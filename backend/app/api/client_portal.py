"""
API do Portal do Cliente
Endpoints para gerenciamento de clientes e projetos
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

from loguru import logger

from app.config import settings
from app.models.client_portal import (
    Client, ClientCreate, ClientUpdate,
    Project, ProjectCreate, ProjectUpdate, ProjectStatus, ProjectWithDetails,
    Stage, StageCreate, StageUpdate,
    DeliveryItem, DeliveryItemCreate, DeliveryItemUpdate, DeliveryStatus,
    ApprovalItem, ApprovalItemCreate, ApprovalItemUpdate, ApprovalStatus,
    TimelineEvent, TimelineEventCreate,
    Comment, CommentCreate,
    Payment, PaymentCreate, PaymentUpdate,
    PROJECT_TEMPLATES
)
from app.repository.client_portal_repository import get_client_portal_repository
from app.middleware.auth import (
    create_access_token as create_jwt_access_token,
    create_refresh_token as create_jwt_refresh_token,
    verify_token as verify_admin_token,
    get_current_admin
)
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/api/portal", tags=["Portal do Cliente"])

security = HTTPBearer(auto_error=False)


# ============================================
# AUTENTICAÇÃO
# ============================================

class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    client: Client


class TokenData(BaseModel):
    client_id: str
    email: str
    exp: datetime


def create_access_token(client: Client) -> str:
    """Criar token JWT"""
    payload = {
        "client_id": str(client.id),
        "email": client.email,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_portal_token(token: str) -> Optional[TokenData]:
    """Verificar token JWT do portal"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Client:
    """Dependency para pegar cliente autenticado"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token_data = verify_portal_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    repo = get_client_portal_repository()
    client = await repo.get_client_by_id(UUID(token_data.client_id))

    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return client


async def get_optional_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Client]:
    """Dependency opcional para cliente autenticado"""
    if not credentials:
        return None

    try:
        return await get_current_client(credentials)
    except HTTPException:
        return None


# ============================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    """Login do cliente"""
    repo = get_client_portal_repository()
    client = await repo.authenticate_client(data.email, data.senha)

    if not client:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not client.ativo:
        raise HTTPException(status_code=403, detail="Conta desativada")

    access_token = create_jwt_access_token(str(client.id))
    refresh_token = create_jwt_refresh_token(str(client.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        client=client
    )


@router.post("/auth/register", response_model=LoginResponse)
async def register(data: ClientCreate):
    """Registrar novo cliente"""
    repo = get_client_portal_repository()

    # Verificar se email já existe
    existing = await repo.get_client_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    client = await repo.create_client(data)
    if not client:
        raise HTTPException(status_code=500, detail="Erro ao criar conta")

    access_token = create_jwt_access_token(str(client.id))
    refresh_token = create_jwt_refresh_token(str(client.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        client=client
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/auth/refresh", response_model=LoginResponse)
async def refresh_token_endpoint(data: RefreshTokenRequest):
    """Renovar access token usando refresh token"""
    try:
        # Verify refresh token
        payload = verify_token(data.refresh_token, "refresh")
        client_id = payload.get("sub")

        # Get client from database
        repo = get_client_portal_repository()
        client = await repo.get_client_by_id(UUID(client_id))

        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        if not client.ativo:
            raise HTTPException(status_code=403, detail="Conta desativada")

        # Generate new tokens
        access_token = create_jwt_access_token(str(client.id))
        refresh_token = create_jwt_refresh_token(str(client.id))

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            client=client
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.get("/auth/me", response_model=Client)
async def get_me(client: Client = Depends(get_current_client)):
    """Retorna dados do cliente logado"""
    return client


@router.put("/auth/me", response_model=Client)
async def update_me(data: ClientUpdate, client: Client = Depends(get_current_client)):
    """Atualizar dados do cliente logado"""
    repo = get_client_portal_repository()
    updated = await repo.update_client(client.id, data)

    if not updated:
        raise HTTPException(status_code=500, detail="Erro ao atualizar")

    return updated


# ============================================
# ENDPOINTS DE CLIENTES (ADMIN)
# ============================================

@router.get("/admin/clients", response_model=List[Client])
async def list_clients(only_active: bool = True, _admin=Depends(get_current_admin)):
    """Listar todos os clientes (admin)"""
    repo = get_client_portal_repository()
    return await repo.list_clients(only_active=only_active)


@router.get("/admin/clients/{client_id}", response_model=Client)
async def get_client(client_id: UUID, _admin=Depends(get_current_admin)):
    """Buscar cliente por ID (admin)"""
    repo = get_client_portal_repository()
    client = await repo.get_client_by_id(client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return client


@router.post("/admin/clients", response_model=Client)
async def create_client(data: ClientCreate, _admin=Depends(get_current_admin)):
    """Criar cliente (admin)"""
    repo = get_client_portal_repository()

    existing = await repo.get_client_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    client = await repo.create_client(data)
    if not client:
        raise HTTPException(status_code=500, detail="Erro ao criar cliente")

    return client


@router.put("/admin/clients/{client_id}", response_model=Client)
async def update_client(client_id: UUID, data: ClientUpdate, _admin=Depends(get_current_admin)):
    """Atualizar cliente (admin)"""
    repo = get_client_portal_repository()
    client = await repo.update_client(client_id, data)

    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return client


# ============================================
# ENDPOINTS DE PROJETOS
# ============================================

@router.get("/projects", response_model=List[Project])
async def list_my_projects(
    status: Optional[str] = None,
    client: Client = Depends(get_current_client)
):
    """Listar projetos do cliente logado"""
    repo = get_client_portal_repository()
    return await repo.list_client_projects(client.id, status=status)


@router.get("/projects/{project_id}", response_model=ProjectWithDetails)
async def get_project(
    project_id: UUID,
    client: Client = Depends(get_current_client)
):
    """Buscar projeto com detalhes"""
    repo = get_client_portal_repository()
    project = await repo.get_project_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Verificar se pertence ao cliente
    if project.client_id != client.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Carregar detalhes
    stages = await repo.list_project_stages(project_id)
    deliveries = await repo.list_delivery_items(project_id, status=DeliveryStatus.PENDENTE.value)
    approvals = await repo.list_approval_items(project_id, status=ApprovalStatus.AGUARDANDO.value)
    timeline = await repo.get_project_timeline(project_id, limit=10)
    payments = await repo.list_project_payments(project_id)

    return ProjectWithDetails(
        **project.model_dump(),
        etapas=stages,
        entregas_pendentes=len(deliveries),
        aprovacoes_pendentes=len(approvals),
        timeline_recente=timeline,
        proximos_pagamentos=[p for p in payments if p.status == PaymentStatus.PENDENTE]
    )


@router.get("/projects/token/{access_token}")
async def get_project_by_token(access_token: str):
    """Acesso direto ao projeto via token (sem login)"""
    repo = get_client_portal_repository()
    project = await repo.get_project_by_token(access_token)

    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Carregar detalhes
    stages = await repo.list_project_stages(project.id)
    deliveries = await repo.list_delivery_items(project.id, status=DeliveryStatus.PENDENTE.value)
    approvals = await repo.list_approval_items(project.id, status=ApprovalStatus.AGUARDANDO.value)
    timeline = await repo.get_project_timeline(project.id, limit=20)

    return {
        "project": project,
        "stages": stages,
        "pending_deliveries": len(deliveries),
        "pending_approvals": len(approvals),
        "timeline": timeline
    }


# Admin endpoints para projetos
@router.get("/admin/projects", response_model=List[Project])
async def list_all_projects(status: Optional[str] = None, _admin=Depends(get_current_admin)):
    """Listar todos os projetos (admin)"""
    repo = get_client_portal_repository()
    return await repo.list_all_projects(status=status)


@router.post("/admin/projects", response_model=Project)
async def create_project(data: ProjectCreate, template: Optional[str] = None, _admin=Depends(get_current_admin)):
    """Criar projeto (admin)"""
    repo = get_client_portal_repository()
    project = await repo.create_project(data, template=template)

    if not project:
        raise HTTPException(status_code=500, detail="Erro ao criar projeto")

    return project


@router.put("/admin/projects/{project_id}", response_model=Project)
async def update_project(project_id: UUID, data: ProjectUpdate, _admin=Depends(get_current_admin)):
    """Atualizar projeto (admin)"""
    repo = get_client_portal_repository()
    project = await repo.update_project(project_id, data)

    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return project


@router.delete("/admin/projects/{project_id}")
async def delete_project(project_id: UUID, _admin=Depends(get_current_admin)):
    """Deletar projeto (admin)"""
    logger.info(f"🗑️ Tentando deletar projeto: {project_id}")

    repo = get_client_portal_repository()

    # Verificar se projeto existe primeiro
    existing_project = await repo.get_project_by_id(project_id)
    if not existing_project:
        logger.warning(f"❌ Projeto {project_id} não encontrado no banco")
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    logger.info(f"✅ Projeto encontrado: {existing_project.nome}")

    success = await repo.delete_project(project_id)
    logger.info(f"📊 Resultado da deleção: {success}")

    if not success:
        logger.error(f"❌ Falha ao deletar projeto {project_id}")
        raise HTTPException(status_code=500, detail="Erro ao deletar projeto")

    logger.info(f"✅ Projeto {project_id} deletado com sucesso")
    return {"message": "Projeto deletado com sucesso"}


@router.post("/admin/projects/{project_id}/advance")
async def advance_project_stage(project_id: UUID, _admin=Depends(get_current_admin)):
    """Avançar etapa do projeto (admin)"""
    repo = get_client_portal_repository()
    project = await repo.advance_project_stage(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return {"message": "Etapa avançada", "project": project}


# ============================================
# ENDPOINTS DE ETAPAS
# ============================================

@router.get("/projects/{project_id}/stages", response_model=List[Stage])
async def list_project_stages(
    project_id: UUID,
    client: Optional[Client] = Depends(get_optional_client)
):
    """Listar etapas do projeto"""
    repo = get_client_portal_repository()
    return await repo.list_project_stages(project_id)


@router.post("/admin/projects/{project_id}/stages", response_model=Stage)
async def create_stage(project_id: UUID, data: StageCreate, _admin=Depends(get_current_admin)):
    """Criar etapa (admin)"""
    repo = get_client_portal_repository()

    # Ajustar project_id
    data.project_id = project_id

    stage = await repo.create_stage(data)
    if not stage:
        raise HTTPException(status_code=500, detail="Erro ao criar etapa")

    return stage


@router.put("/admin/stages/{stage_id}", response_model=Stage)
async def update_stage(stage_id: UUID, data: StageUpdate, _admin=Depends(get_current_admin)):
    """Atualizar etapa (admin)"""
    repo = get_client_portal_repository()
    stage = await repo.update_stage(stage_id, data)

    if not stage:
        raise HTTPException(status_code=404, detail="Etapa não encontrada")

    return stage


# ============================================
# ENDPOINTS DE ENTREGAS (Cliente -> Empresa)
# ============================================

@router.get("/projects/{project_id}/deliveries", response_model=List[DeliveryItem])
async def list_deliveries(
    project_id: UUID,
    status: Optional[str] = None,
    client: Optional[Client] = Depends(get_optional_client)
):
    """Listar entregas pendentes"""
    repo = get_client_portal_repository()
    return await repo.list_delivery_items(project_id, status=status)


@router.post("/admin/projects/{project_id}/deliveries", response_model=DeliveryItem)
async def create_delivery_item(project_id: UUID, data: DeliveryItemCreate, _admin=Depends(get_current_admin)):
    """Criar item de entrega (admin)"""
    repo = get_client_portal_repository()

    data.project_id = project_id

    item = await repo.create_delivery_item(data)
    if not item:
        raise HTTPException(status_code=500, detail="Erro ao criar item")

    return item


@router.put("/deliveries/{item_id}", response_model=DeliveryItem)
async def update_delivery(
    item_id: UUID,
    data: DeliveryItemUpdate,
    client: Client = Depends(get_current_client)
):
    """Cliente atualiza entrega (envia arquivo)"""
    repo = get_client_portal_repository()
    item = await repo.update_delivery_item(item_id, data, is_client=True)

    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    return item


@router.put("/admin/deliveries/{item_id}", response_model=DeliveryItem)
async def admin_update_delivery(item_id: UUID, data: DeliveryItemUpdate, _admin=Depends(get_current_admin)):
    """Admin atualiza entrega (aprova/rejeita)"""
    repo = get_client_portal_repository()
    item = await repo.update_delivery_item(item_id, data, is_client=False)

    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    return item


@router.post("/deliveries/{item_id}/upload")
async def upload_delivery_file(
    item_id: UUID,
    file: UploadFile = File(...),
    client: Client = Depends(get_current_client)
):
    """Cliente faz upload de arquivo para entrega"""
    repo = get_client_portal_repository()
    storage = get_storage_service()

    # Buscar item de entrega
    item = await repo.get_delivery_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de entrega não encontrado")

    # Verificar se o cliente tem acesso ao projeto
    project = await repo.get_project_by_id(item.project_id)
    if not project or project.client_id != client.id:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este item")

    # Upload do arquivo
    file_data = await storage.upload_file(
        bucket="project-deliveries",
        file=file,
        project_id=item.project_id,
        item_id=item_id,
        allowed_types=['image', 'document', 'video', 'archive']
    )

    # Atualizar item com URL do arquivo e marcar como enviado
    update_data = DeliveryItemUpdate(
        arquivo_url=file_data['url'],
        arquivo_nome=file_data['filename'],
        status='enviado'
    )
    updated_item = await repo.update_delivery_item(item_id, update_data, is_client=True)

    return {
        "success": True,
        "message": "Arquivo enviado com sucesso",
        "item": updated_item,
        "file": file_data
    }


# ============================================
# ENDPOINTS DE APROVAÇÕES (Empresa -> Cliente)
# ============================================

@router.get("/projects/{project_id}/approvals", response_model=List[ApprovalItem])
async def list_approvals(
    project_id: UUID,
    status: Optional[str] = None,
    client: Optional[Client] = Depends(get_optional_client)
):
    """Listar itens para aprovação"""
    repo = get_client_portal_repository()
    return await repo.list_approval_items(project_id, status=status)


@router.post("/admin/projects/{project_id}/approvals", response_model=ApprovalItem)
async def create_approval_item(project_id: UUID, data: ApprovalItemCreate, _admin=Depends(get_current_admin)):
    """Criar item para aprovação (admin)"""
    repo = get_client_portal_repository()

    data.project_id = project_id

    item = await repo.create_approval_item(data)
    if not item:
        raise HTTPException(status_code=500, detail="Erro ao criar item")

    return item


@router.put("/approvals/{item_id}/respond", response_model=ApprovalItem)
async def respond_to_approval(
    item_id: UUID,
    data: ApprovalItemUpdate,
    client: Client = Depends(get_current_client)
):
    """Cliente responde a aprovação"""
    repo = get_client_portal_repository()
    item = await repo.respond_to_approval(item_id, data, is_client=True)

    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    return item


@router.post("/admin/approvals/{item_id}/upload")
async def upload_approval_file(
    item_id: UUID,
    file: UploadFile = File(...),
    _admin=Depends(get_current_admin)
):
    """Admin faz upload de arquivo para aprovação"""
    repo = get_client_portal_repository()
    storage = get_storage_service()

    # Buscar item de aprovação
    item = await repo.get_approval_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de aprovação não encontrado")

    # Upload do arquivo
    file_data = await storage.upload_file(
        bucket="project-approvals",
        file=file,
        project_id=item.project_id,
        item_id=item_id,
        allowed_types=['image', 'document', 'video']
    )

    # Atualizar item com URL do arquivo
    update_data = ApprovalItemUpdate(
        arquivo_url=file_data['url'],
        arquivo_nome=file_data['filename']
    )
    updated_item = await repo.update_approval_item(item_id, update_data)

    return {
        "success": True,
        "message": "Arquivo enviado com sucesso",
        "item": updated_item,
        "file": file_data
    }


# ============================================
# ENDPOINTS DE TIMELINE
# ============================================

@router.get("/projects/{project_id}/timeline", response_model=List[TimelineEvent])
async def get_project_timeline(
    project_id: UUID,
    limit: int = Query(default=50, le=100),
    client: Optional[Client] = Depends(get_optional_client)
):
    """Buscar timeline do projeto"""
    repo = get_client_portal_repository()
    return await repo.get_project_timeline(project_id, limit=limit)


# ============================================
# ENDPOINTS DE COMENTÁRIOS
# ============================================

@router.get("/projects/{project_id}/comments", response_model=List[Comment])
async def list_comments(
    project_id: UUID,
    client: Optional[Client] = Depends(get_optional_client)
):
    """Listar comentários do projeto"""
    repo = get_client_portal_repository()
    return await repo.list_project_comments(project_id)


@router.post("/projects/{project_id}/comments", response_model=Comment)
async def add_comment(
    project_id: UUID,
    data: CommentCreate,
    client: Client = Depends(get_current_client)
):
    """Cliente adiciona comentário"""
    repo = get_client_portal_repository()

    data.project_id = project_id
    data.is_client = True

    comment = await repo.add_comment(data, user_nome=client.nome)
    if not comment:
        raise HTTPException(status_code=500, detail="Erro ao adicionar comentário")

    return comment


@router.post("/admin/projects/{project_id}/comments", response_model=Comment)
async def admin_add_comment(project_id: UUID, data: CommentCreate, user_nome: str = "Equipe", _admin=Depends(get_current_admin)):
    """Admin adiciona comentário"""
    repo = get_client_portal_repository()

    data.project_id = project_id
    data.is_client = False

    comment = await repo.add_comment(data, user_nome=user_nome)
    if not comment:
        raise HTTPException(status_code=500, detail="Erro ao adicionar comentário")

    return comment


# ============================================
# ENDPOINTS DE PAGAMENTOS
# ============================================

@router.get("/projects/{project_id}/payments", response_model=List[Payment])
async def list_payments(
    project_id: UUID,
    client: Optional[Client] = Depends(get_optional_client)
):
    """Listar pagamentos do projeto"""
    repo = get_client_portal_repository()
    return await repo.list_project_payments(project_id)


@router.post("/admin/projects/{project_id}/payments", response_model=Payment)
async def create_payment(project_id: UUID, data: PaymentCreate, _admin=Depends(get_current_admin)):
    """Criar pagamento (admin)"""
    repo = get_client_portal_repository()

    data.project_id = project_id

    payment = await repo.create_payment(data)
    if not payment:
        raise HTTPException(status_code=500, detail="Erro ao criar pagamento")

    return payment


@router.put("/admin/payments/{payment_id}", response_model=Payment)
async def update_payment(payment_id: UUID, data: PaymentUpdate, _admin=Depends(get_current_admin)):
    """Atualizar pagamento (admin)"""
    repo = get_client_portal_repository()
    payment = await repo.update_payment(payment_id, data)

    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    return payment


@router.post("/payments/{payment_id}/upload-proof")
async def upload_payment_proof(
    payment_id: UUID,
    file: UploadFile = File(...),
    client: Client = Depends(get_current_client)
):
    """Cliente faz upload de comprovante de pagamento"""
    repo = get_client_portal_repository()
    storage = get_storage_service()

    # Buscar pagamento
    payment = await repo.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    # Verificar se o cliente tem acesso ao projeto
    project = await repo.get_project_by_id(payment.project_id)
    if not project or project.client_id != client.id:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este pagamento")

    # Upload do comprovante
    file_data = await storage.upload_file(
        bucket="payment-proofs",
        file=file,
        project_id=payment.project_id,
        item_id=payment_id,
        allowed_types=['image', 'document']
    )

    # Atualizar pagamento com URL do comprovante
    update_data = PaymentUpdate(
        comprovante_url=file_data['url']
    )
    updated_payment = await repo.update_payment(payment_id, update_data)

    return {
        "success": True,
        "message": "Comprovante enviado com sucesso",
        "payment": updated_payment,
        "file": file_data
    }


# ============================================
# ENDPOINTS DE ESTATÍSTICAS
# ============================================

@router.get("/stats")
async def get_my_stats(client: Client = Depends(get_current_client)):
    """Estatísticas do cliente logado"""
    repo = get_client_portal_repository()
    return await repo.get_client_stats(client.id)


@router.get("/admin/stats")
async def get_admin_stats(_admin=Depends(get_current_admin)):
    """Estatísticas gerais (admin)"""
    repo = get_client_portal_repository()
    return await repo.get_admin_stats()


# ============================================
# ENDPOINTS AUXILIARES
# ============================================

@router.get("/templates")
async def list_project_templates():
    """Listar templates de projeto disponíveis"""
    return [
        {
            "id": key,
            "nome": value["nome"],
            "descricao": value.get("descricao", ""),
            "etapas": value["etapas"],
            "entregas": value.get("entregas", [])
        }
        for key, value in PROJECT_TEMPLATES.items()
    ]


@router.get("/templates/{template_id}")
async def get_project_template(template_id: str):
    """Buscar detalhes de um template"""
    if template_id not in PROJECT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    template = PROJECT_TEMPLATES[template_id]
    return {
        "id": template_id,
        "nome": template["nome"],
        "descricao": template.get("descricao", ""),
        "etapas": template["etapas"],
        "entregas": template.get("entregas", [])
    }


class TemplateCreate(BaseModel):
    nome: str
    descricao: str = ""
    etapas: List[str]
    entregas: List[dict] = []


@router.post("/templates")
async def create_template(data: TemplateCreate, _admin=Depends(get_current_admin)):
    """Criar novo template (admin)"""
    # Gerar ID único
    template_id = data.nome.lower().replace(" ", "_")

    # Garantir que o ID é único
    counter = 1
    original_id = template_id
    while template_id in PROJECT_TEMPLATES:
        template_id = f"{original_id}_{counter}"
        counter += 1

    # Adicionar template ao dicionário
    PROJECT_TEMPLATES[template_id] = {
        "nome": data.nome,
        "descricao": data.descricao,
        "etapas": data.etapas,
        "entregas": data.entregas
    }

    return {
        "id": template_id,
        "nome": data.nome,
        "descricao": data.descricao,
        "etapas": data.etapas,
        "entregas": data.entregas
    }


@router.put("/templates/{template_id}")
async def update_template(template_id: str, data: TemplateCreate, _admin=Depends(get_current_admin)):
    """Atualizar template existente (admin)"""
    if template_id not in PROJECT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    # Atualizar template
    PROJECT_TEMPLATES[template_id] = {
        "nome": data.nome,
        "descricao": data.descricao,
        "etapas": data.etapas,
        "entregas": data.entregas
    }

    return {
        "id": template_id,
        "nome": data.nome,
        "descricao": data.descricao,
        "etapas": data.etapas,
        "entregas": data.entregas
    }


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, _admin=Depends(get_current_admin)):
    """Deletar template (admin)"""
    if template_id not in PROJECT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    # Não permitir deletar templates padrão
    default_templates = ["site_institucional", "identidade_visual", "landing_page", "ecommerce"]
    if template_id in default_templates:
        raise HTTPException(
            status_code=400,
            detail="Não é possível deletar templates padrão do sistema"
        )

    del PROJECT_TEMPLATES[template_id]

    return {"success": True, "message": "Template deletado com sucesso"}
