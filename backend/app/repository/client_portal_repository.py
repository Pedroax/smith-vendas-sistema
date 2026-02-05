"""
Repository do Portal do Cliente
Operações de banco de dados para clientes e projetos
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import hashlib
import secrets

from loguru import logger

from app.database import get_supabase
from app.models.client_portal import (
    Client, ClientCreate, ClientUpdate,
    Project, ProjectCreate, ProjectUpdate, ProjectStatus,
    Stage, StageCreate, StageUpdate,
    DeliveryItem, DeliveryItemCreate, DeliveryItemUpdate, DeliveryStatus,
    ApprovalItem, ApprovalItemCreate, ApprovalItemUpdate, ApprovalStatus,
    TimelineEvent, TimelineEventCreate, TimelineEventType,
    Comment, CommentCreate,
    Payment, PaymentCreate, PaymentUpdate, PaymentStatus,
    PROJECT_TEMPLATES
)


class ClientPortalRepository:
    """Repository para operações do Portal do Cliente"""

    def __init__(self):
        self.supabase = get_supabase()

    # ============================================
    # CLIENTES
    # ============================================

    def _hash_password(self, password: str) -> str:
        """Hash de senha simples (em produção use bcrypt)"""
        salt = "mity_portal_salt_"
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verificar senha"""
        return self._hash_password(password) == hashed

    async def create_client(self, data: ClientCreate) -> Optional[Client]:
        """Criar novo cliente"""
        try:
            client_data = {
                "id": str(uuid4()),
                "nome": data.nome,
                "email": data.email,
                "telefone": data.telefone,
                "empresa": data.empresa,
                "documento": data.documento,
                "avatar_url": data.avatar_url,
                "senha_hash": self._hash_password(data.senha),
                "ativo": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("clients").insert(client_data).execute()

            if result.data:
                logger.success(f"Cliente criado: {data.email}")
                return Client(**result.data[0])

            return None

        except Exception as e:
            logger.error(f"Erro ao criar cliente: {e}")
            return None

    async def get_client_by_id(self, client_id: UUID) -> Optional[Client]:
        """Buscar cliente por ID"""
        try:
            result = self.supabase.table("clients").select("*").eq("id", str(client_id)).single().execute()
            if result.data:
                return Client(**result.data)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {e}")
            return None

    async def get_client_by_email(self, email: str) -> Optional[Dict]:
        """Buscar cliente por email (para login)"""
        try:
            result = self.supabase.table("clients").select("*").eq("email", email).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Erro ao buscar cliente por email: {e}")
            return None

    async def authenticate_client(self, email: str, password: str) -> Optional[Client]:
        """Autenticar cliente"""
        try:
            client_data = await self.get_client_by_email(email)
            if client_data and self._verify_password(password, client_data.get("senha_hash", "")):
                # Atualizar último acesso
                self.supabase.table("clients").update({
                    "ultimo_acesso": datetime.utcnow().isoformat()
                }).eq("id", client_data["id"]).execute()

                return Client(**client_data)
            return None
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None

    async def update_client(self, client_id: UUID, data: ClientUpdate) -> Optional[Client]:
        """Atualizar cliente"""
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = self.supabase.table("clients").update(update_data).eq("id", str(client_id)).execute()

            if result.data:
                return Client(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente: {e}")
            return None

    async def list_clients(self, only_active: bool = True) -> List[Client]:
        """Listar todos os clientes"""
        try:
            query = self.supabase.table("clients").select("*")
            if only_active:
                query = query.eq("ativo", True)

            result = query.order("nome").execute()
            return [Client(**c) for c in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar clientes: {e}")
            return []

    # ============================================
    # PROJETOS
    # ============================================

    async def create_project(self, data: ProjectCreate, template: str = None) -> Optional[Project]:
        """Criar novo projeto"""
        try:
            access_token = secrets.token_hex(6)  # 12 caracteres

            project_data = {
                "id": str(uuid4()),
                "client_id": str(data.client_id),
                "nome": data.nome,
                "descricao": data.descricao,
                "tipo": data.tipo,
                "status": ProjectStatus.BRIEFING.value,
                "etapa_atual": 0,
                "progresso": 0,
                "valor_total": data.valor_total,
                "data_inicio": data.data_inicio.isoformat() if data.data_inicio else None,
                "data_previsao": data.data_previsao.isoformat() if data.data_previsao else None,
                "access_token": access_token,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("client_projects").insert(project_data).execute()

            if result.data:
                project = Project(**result.data[0])

                # Criar etapas baseado no template ou customizado
                etapas = []
                if template and template in PROJECT_TEMPLATES:
                    etapas = PROJECT_TEMPLATES[template]["etapas"]
                elif data.etapas:
                    etapas = [{"nome": e, "descricao": "", "cor": "#6366f1"} for e in data.etapas]
                else:
                    # Etapas padrão
                    etapas = [
                        {"nome": "Briefing", "descricao": "Entendimento do projeto", "cor": "#8b5cf6"},
                        {"nome": "Em Desenvolvimento", "descricao": "Execução do projeto", "cor": "#3b82f6"},
                        {"nome": "Revisão", "descricao": "Ajustes e correções", "cor": "#f97316"},
                        {"nome": "Entrega", "descricao": "Projeto finalizado", "cor": "#10b981"},
                    ]

                # Criar as etapas no banco
                for i, etapa in enumerate(etapas):
                    await self.create_stage(StageCreate(
                        project_id=project.id,
                        nome=etapa["nome"],
                        descricao=etapa.get("descricao", ""),
                        ordem=i
                    ), cor=etapa.get("cor", "#6366f1"))

                # Criar entregas se template
                if template and template in PROJECT_TEMPLATES:
                    for entrega in PROJECT_TEMPLATES[template].get("entregas", []):
                        await self.create_delivery_item(DeliveryItemCreate(
                            project_id=project.id,
                            nome=entrega["nome"],
                            obrigatorio=entrega.get("obrigatorio", True)
                        ))

                # Adicionar evento na timeline
                await self.add_timeline_event(TimelineEventCreate(
                    project_id=project.id,
                    tipo=TimelineEventType.PROJETO_CRIADO,
                    titulo="Projeto criado",
                    descricao=f"Projeto '{data.nome}' foi criado"
                ))

                logger.success(f"Projeto criado: {data.nome}")
                return project

            return None

        except Exception as e:
            logger.error(f"Erro ao criar projeto: {e}")
            return None

    async def get_project_by_id(self, project_id: UUID) -> Optional[Project]:
        """Buscar projeto por ID"""
        try:
            result = self.supabase.table("client_projects").select("*").eq("id", str(project_id)).single().execute()
            if result.data:
                return Project(**result.data)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar projeto: {e}")
            return None

    async def get_project_by_token(self, access_token: str) -> Optional[Project]:
        """Buscar projeto por token de acesso (link direto)"""
        try:
            result = self.supabase.table("client_projects").select("*").eq("access_token", access_token).single().execute()
            if result.data:
                return Project(**result.data)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar projeto por token: {e}")
            return None

    async def list_client_projects(self, client_id: UUID, status: str = None) -> List[Project]:
        """Listar projetos de um cliente"""
        try:
            query = self.supabase.table("client_projects").select("*").eq("client_id", str(client_id))

            if status:
                query = query.eq("status", status)

            result = query.order("created_at", desc=True).execute()
            return [Project(**p) for p in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar projetos: {e}")
            return []

    async def list_all_projects(self, status: str = None) -> List[Project]:
        """Listar todos os projetos (admin)"""
        try:
            query = self.supabase.table("client_projects").select("*")

            if status:
                query = query.eq("status", status)

            result = query.order("created_at", desc=True).execute()
            return [Project(**p) for p in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar projetos: {e}")
            return []

    async def update_project(self, project_id: UUID, data) -> Optional[Project]:
        """Atualizar projeto"""
        try:
            # Aceitar dict ou ProjectUpdate
            if isinstance(data, dict):
                update_data = {k: v for k, v in data.items() if v is not None}
            else:
                update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "status" in update_data:
                update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = self.supabase.table("client_projects").update(update_data).eq("id", str(project_id)).execute()

            if result.data:
                return Project(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar projeto: {e}")
            return None

    async def delete_project(self, project_id: UUID) -> bool:
        """Deletar projeto e todos os dados relacionados"""
        try:
            # Deletar em cascata: stages, deliveries, approvals, timeline, comments, payments
            await self.supabase.table("client_project_stages").delete().eq("project_id", str(project_id)).execute()
            await self.supabase.table("client_delivery_items").delete().eq("project_id", str(project_id)).execute()
            await self.supabase.table("client_approval_items").delete().eq("project_id", str(project_id)).execute()
            await self.supabase.table("client_timeline_events").delete().eq("project_id", str(project_id)).execute()
            await self.supabase.table("client_comments").delete().eq("project_id", str(project_id)).execute()
            await self.supabase.table("client_payments").delete().eq("project_id", str(project_id)).execute()

            # Deletar o projeto
            result = self.supabase.table("client_projects").delete().eq("id", str(project_id)).execute()

            return result.data is not None and len(result.data) > 0
        except Exception as e:
            logger.error(f"Erro ao deletar projeto: {e}")
            return False

    async def advance_project_stage(self, project_id: UUID) -> Optional[Project]:
        """Avançar etapa do projeto"""
        try:
            project = await self.get_project_by_id(project_id)
            if not project:
                return None

            # Pegar etapas
            stages = await self.list_project_stages(project_id)
            current_index = project.etapa_atual

            if current_index < len(stages):
                # Marcar etapa atual como concluída
                current_stage = stages[current_index]
                await self.update_stage(current_stage.id, StageUpdate(
                    concluida=True,
                    data_conclusao=datetime.utcnow()
                ))

                # Adicionar evento na timeline
                await self.add_timeline_event(TimelineEventCreate(
                    project_id=project_id,
                    tipo=TimelineEventType.ETAPA_AVANCADA,
                    titulo=f"Etapa concluída: {current_stage.nome}",
                    descricao=f"A etapa '{current_stage.nome}' foi finalizada",
                    metadata={"stage_id": str(current_stage.id), "stage_name": current_stage.nome}
                ))

                # Se ainda há próxima etapa
                if current_index + 1 < len(stages):
                    next_stage = stages[current_index + 1]
                    await self.update_stage(next_stage.id, StageUpdate(
                        data_inicio=datetime.utcnow()
                    ))

            return await self.get_project_by_id(project_id)

        except Exception as e:
            logger.error(f"Erro ao avançar etapa: {e}")
            return None

    # ============================================
    # ETAPAS
    # ============================================

    async def create_stage(self, data: StageCreate, cor: str = "#6366f1") -> Optional[Stage]:
        """Criar etapa"""
        try:
            stage_data = {
                "id": str(uuid4()),
                "project_id": str(data.project_id),
                "nome": data.nome,
                "descricao": data.descricao,
                "ordem": data.ordem,
                "cor": cor,
                "concluida": False,
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("project_stages").insert(stage_data).execute()

            if result.data:
                return Stage(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao criar etapa: {e}")
            return None

    async def list_project_stages(self, project_id: UUID) -> List[Stage]:
        """Listar etapas de um projeto"""
        try:
            result = self.supabase.table("project_stages").select("*").eq("project_id", str(project_id)).order("ordem").execute()
            return [Stage(**s) for s in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar etapas: {e}")
            return []

    async def update_stage(self, stage_id: UUID, data) -> Optional[Stage]:
        """Atualizar etapa"""
        try:
            # Aceitar dict ou StageUpdate
            if isinstance(data, dict):
                update_data = {k: v for k, v in data.items() if v is not None}
            else:
                update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "data_conclusao" in update_data and update_data["data_conclusao"]:
                update_data["data_conclusao"] = update_data["data_conclusao"].isoformat()

            result = self.supabase.table("project_stages").update(update_data).eq("id", str(stage_id)).execute()

            if result.data:
                return Stage(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar etapa: {e}")
            return None

    # ============================================
    # ENTREGAS (Cliente -> Empresa)
    # ============================================

    async def create_delivery_item(self, data: DeliveryItemCreate) -> Optional[DeliveryItem]:
        """Criar item de entrega"""
        try:
            item_data = {
                "id": str(uuid4()),
                "project_id": str(data.project_id),
                "stage_id": str(data.stage_id) if data.stage_id else None,
                "nome": data.nome,
                "descricao": data.descricao,
                "obrigatorio": data.obrigatorio,
                "status": DeliveryStatus.PENDENTE.value,
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("delivery_items").insert(item_data).execute()

            if result.data:
                return DeliveryItem(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao criar item de entrega: {e}")
            return None

    async def list_delivery_items(self, project_id: UUID, status: str = None) -> List[DeliveryItem]:
        """Listar itens de entrega de um projeto"""
        try:
            query = self.supabase.table("delivery_items").select("*").eq("project_id", str(project_id))

            if status:
                query = query.eq("status", status)

            result = query.order("created_at").execute()
            return [DeliveryItem(**i) for i in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar entregas: {e}")
            return []

    async def update_delivery_item(self, item_id: UUID, data: DeliveryItemUpdate, is_client: bool = False) -> Optional[DeliveryItem]:
        """Atualizar item de entrega"""
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "status" in update_data:
                update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

                # Marcar timestamp apropriado
                if update_data["status"] == DeliveryStatus.ENVIADO.value:
                    update_data["enviado_em"] = datetime.utcnow().isoformat()
                elif update_data["status"] == DeliveryStatus.APROVADO.value:
                    update_data["aprovado_em"] = datetime.utcnow().isoformat()

            result = self.supabase.table("delivery_items").update(update_data).eq("id", str(item_id)).execute()

            if result.data:
                item = DeliveryItem(**result.data[0])

                # Eventos na timeline por status
                if is_client and data.status == DeliveryStatus.ENVIADO:
                    await self.add_timeline_event(TimelineEventCreate(
                        project_id=item.project_id,
                        tipo=TimelineEventType.MATERIAL_ENVIADO,
                        titulo=f"Material enviado: {item.nome}",
                        is_client_action=True,
                        metadata={"item_id": str(item_id), "item_name": item.nome}
                    ))
                elif not is_client and data.status == DeliveryStatus.APROVADO:
                    await self.add_timeline_event(TimelineEventCreate(
                        project_id=item.project_id,
                        tipo=TimelineEventType.MATERIAL_APROVADO,
                        titulo=f"Material aprovado: {item.nome}",
                        metadata={"item_id": str(item_id), "item_name": item.nome}
                    ))
                elif not is_client and data.status == DeliveryStatus.REJEITADO:
                    await self.add_timeline_event(TimelineEventCreate(
                        project_id=item.project_id,
                        tipo=TimelineEventType.AJUSTES_SOLICITADOS,
                        titulo=f"Ajustes solicitados: {item.nome}",
                        metadata={"item_id": str(item_id), "item_name": item.nome}
                    ))

                return item
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar item de entrega: {e}")
            return None

    async def get_delivery_item(self, item_id: UUID) -> Optional[DeliveryItem]:
        """Buscar item de entrega por ID"""
        try:
            result = self.supabase.table("delivery_items").select("*").eq("id", str(item_id)).execute()
            if result.data:
                return DeliveryItem(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar item de entrega: {e}")
            return None

    # ============================================
    # APROVAÇÕES (Empresa -> Cliente)
    # ============================================

    async def create_approval_item(self, data: ApprovalItemCreate) -> Optional[ApprovalItem]:
        """Criar item para aprovação"""
        try:
            item_data = {
                "id": str(uuid4()),
                "project_id": str(data.project_id),
                "stage_id": str(data.stage_id) if data.stage_id else None,
                "titulo": data.titulo,
                "descricao": data.descricao,
                "tipo": data.tipo,
                "status": ApprovalStatus.AGUARDANDO.value,
                "arquivo_url": data.arquivo_url,
                "link_externo": data.link_externo,
                "versao": 1,
                "enviado_em": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("approval_items").insert(item_data).execute()

            if result.data:
                item = ApprovalItem(**result.data[0])

                # Adicionar evento na timeline
                await self.add_timeline_event(TimelineEventCreate(
                    project_id=data.project_id,
                    tipo=TimelineEventType.APROVACAO_SOLICITADA,
                    titulo=f"Aprovação solicitada: {data.titulo}",
                    metadata={"approval_id": str(item.id), "titulo": data.titulo}
                ))

                return item
            return None
        except Exception as e:
            logger.error(f"Erro ao criar item de aprovação: {e}")
            return None

    async def list_approval_items(self, project_id: UUID, status: str = None) -> List[ApprovalItem]:
        """Listar itens de aprovação de um projeto"""
        try:
            query = self.supabase.table("approval_items").select("*").eq("project_id", str(project_id))

            if status:
                query = query.eq("status", status)

            result = query.order("created_at", desc=True).execute()
            return [ApprovalItem(**i) for i in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar aprovações: {e}")
            return []

    async def respond_to_approval(self, item_id: UUID, data: ApprovalItemUpdate, is_client: bool = True) -> Optional[ApprovalItem]:
        """Responder a item de aprovação"""
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "status" in update_data:
                update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

            update_data["respondido_em"] = datetime.utcnow().isoformat()

            result = self.supabase.table("approval_items").update(update_data).eq("id", str(item_id)).execute()

            if result.data:
                item = ApprovalItem(**result.data[0])

                # Adicionar evento na timeline
                event_type = TimelineEventType.APROVADO if data.status == ApprovalStatus.APROVADO else TimelineEventType.AJUSTES_SOLICITADOS
                titulo = f"Aprovado: {item.titulo}" if data.status == ApprovalStatus.APROVADO else f"Ajustes solicitados: {item.titulo}"

                await self.add_timeline_event(TimelineEventCreate(
                    project_id=item.project_id,
                    tipo=event_type,
                    titulo=titulo,
                    descricao=data.feedback_cliente,
                    is_client_action=is_client,
                    metadata={"approval_id": str(item_id), "titulo": item.titulo}
                ))

                return item
            return None
        except Exception as e:
            logger.error(f"Erro ao responder aprovação: {e}")
            return None

    async def get_approval_item(self, item_id: UUID) -> Optional[ApprovalItem]:
        """Buscar item de aprovação por ID"""
        try:
            result = self.supabase.table("approval_items").select("*").eq("id", str(item_id)).execute()
            if result.data:
                return ApprovalItem(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar item de aprovação: {e}")
            return None

    async def update_approval_item(self, item_id: UUID, data: ApprovalItemUpdate) -> Optional[ApprovalItem]:
        """Atualizar item de aprovação"""
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "status" in update_data:
                update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

            result = self.supabase.table("approval_items").update(update_data).eq("id", str(item_id)).execute()

            if result.data:
                item = ApprovalItem(**result.data[0])

                # Eventos na timeline por status
                if data.status == ApprovalStatus.APROVADO:
                    await self.add_timeline_event(TimelineEventCreate(
                        project_id=item.project_id,
                        tipo=TimelineEventType.APROVADO,
                        titulo=f"Aprovado pelo cliente: {item.nome}",
                        is_client_action=True,
                        metadata={"item_id": str(item_id), "item_name": item.nome}
                    ))
                elif data.status == ApprovalStatus.AJUSTES_SOLICITADOS:
                    await self.add_timeline_event(TimelineEventCreate(
                        project_id=item.project_id,
                        tipo=TimelineEventType.AJUSTES_SOLICITADOS,
                        titulo=f"Ajustes solicitados pelo cliente: {item.nome}",
                        is_client_action=True,
                        metadata={"item_id": str(item_id), "item_name": item.nome}
                    ))

                return item
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar item de aprovação: {e}")
            return None

    # ============================================
    # TIMELINE
    # ============================================

    async def add_timeline_event(self, data: TimelineEventCreate) -> Optional[TimelineEvent]:
        """Adicionar evento na timeline"""
        try:
            event_data = {
                "id": str(uuid4()),
                "project_id": str(data.project_id),
                "tipo": data.tipo.value if hasattr(data.tipo, "value") else data.tipo,
                "titulo": data.titulo,
                "descricao": data.descricao,
                "user_id": str(data.user_id) if data.user_id else None,
                "is_client_action": data.is_client_action,
                "metadata": data.metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("project_timeline").insert(event_data).execute()

            if result.data:
                return TimelineEvent(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao adicionar evento: {e}")
            return None

    async def get_project_timeline(self, project_id: UUID, limit: int = 50) -> List[TimelineEvent]:
        """Buscar timeline de um projeto"""
        try:
            result = self.supabase.table("project_timeline").select("*").eq("project_id", str(project_id)).order("created_at", desc=True).limit(limit).execute()
            return [TimelineEvent(**e) for e in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao buscar timeline: {e}")
            return []

    # ============================================
    # COMENTÁRIOS
    # ============================================

    async def add_comment(self, data: CommentCreate, user_nome: str = "Sistema") -> Optional[Comment]:
        """Adicionar comentário"""
        try:
            comment_data = {
                "id": str(uuid4()),
                "project_id": str(data.project_id),
                "stage_id": str(data.stage_id) if data.stage_id else None,
                "approval_id": str(data.approval_id) if data.approval_id else None,
                "user_nome": user_nome,
                "is_client": data.is_client,
                "conteudo": data.conteudo,
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("project_comments").insert(comment_data).execute()

            if result.data:
                comment = Comment(**result.data[0])

                # Adicionar evento na timeline
                await self.add_timeline_event(TimelineEventCreate(
                    project_id=data.project_id,
                    tipo=TimelineEventType.COMENTARIO,
                    titulo=f"Novo comentário de {user_nome}",
                    descricao=data.conteudo[:100] + "..." if len(data.conteudo) > 100 else data.conteudo,
                    is_client_action=data.is_client
                ))

                return comment
            return None
        except Exception as e:
            logger.error(f"Erro ao adicionar comentário: {e}")
            return None

    async def list_project_comments(self, project_id: UUID) -> List[Comment]:
        """Listar comentários de um projeto"""
        try:
            result = self.supabase.table("project_comments").select("*").eq("project_id", str(project_id)).order("created_at", desc=True).execute()
            return [Comment(**c) for c in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar comentários: {e}")
            return []

    # ============================================
    # PAGAMENTOS
    # ============================================

    async def create_payment(self, data: PaymentCreate) -> Optional[Payment]:
        """Criar pagamento"""
        try:
            payment_data = {
                "id": str(uuid4()),
                "project_id": str(data.project_id),
                "descricao": data.descricao,
                "valor": float(data.valor),
                "status": PaymentStatus.PENDENTE.value,
                "data_vencimento": data.data_vencimento.isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("project_payments").insert(payment_data).execute()

            if result.data:
                return Payment(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao criar pagamento: {e}")
            return None

    async def list_project_payments(self, project_id: UUID) -> List[Payment]:
        """Listar pagamentos de um projeto"""
        try:
            result = self.supabase.table("project_payments").select("*").eq("project_id", str(project_id)).order("data_vencimento").execute()
            return [Payment(**p) for p in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Erro ao listar pagamentos: {e}")
            return []

    async def update_payment(self, payment_id: UUID, data) -> Optional[Payment]:
        """Atualizar pagamento"""
        try:
            # Aceitar dict ou PaymentUpdate
            if isinstance(data, dict):
                update_data = {k: v for k, v in data.items() if v is not None}
            else:
                update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "status" in update_data:
                update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

            if "data_pagamento" in update_data and update_data["data_pagamento"]:
                update_data["data_pagamento"] = update_data["data_pagamento"].isoformat()

            result = self.supabase.table("project_payments").update(update_data).eq("id", str(payment_id)).execute()

            if result.data:
                payment = Payment(**result.data[0])

                # Adicionar evento se foi pago
                if data.status == PaymentStatus.PAGO:
                    await self.add_timeline_event(TimelineEventCreate(
                        project_id=payment.project_id,
                        tipo=TimelineEventType.PAGAMENTO_RECEBIDO,
                        titulo=f"Pagamento recebido: {payment.descricao}",
                        metadata={"payment_id": str(payment_id), "valor": float(payment.valor)}
                    ))

                return payment
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar pagamento: {e}")
            return None

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        """Buscar pagamento por ID"""
        try:
            result = self.supabase.table("project_payments").select("*").eq("id", str(payment_id)).execute()
            if result.data:
                return Payment(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar pagamento: {e}")
            return None

    # ============================================
    # ESTATÍSTICAS
    # ============================================

    async def get_client_stats(self, client_id: UUID) -> Dict[str, Any]:
        """Estatísticas do cliente"""
        try:
            projects = await self.list_client_projects(client_id)

            total = len(projects)
            ativos = len([p for p in projects if p.status not in [ProjectStatus.CONCLUIDO, ProjectStatus.CANCELADO]])
            concluidos = len([p for p in projects if p.status == ProjectStatus.CONCLUIDO])

            # Entregas pendentes
            entregas_pendentes = 0
            aprovacoes_pendentes = 0
            for project in projects:
                entregas = await self.list_delivery_items(project.id, status=DeliveryStatus.PENDENTE.value)
                entregas_pendentes += len(entregas)
                aprovacoes = await self.list_approval_items(project.id, status=ApprovalStatus.AGUARDANDO.value)
                aprovacoes_pendentes += len(aprovacoes)

            return {
                "total_projetos": total,
                "projetos_ativos": ativos,
                "projetos_concluidos": concluidos,
                "entregas_pendentes": entregas_pendentes,
                "aprovacoes_pendentes": aprovacoes_pendentes
            }
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {}

    async def get_admin_stats(self) -> Dict[str, Any]:
        """Estatísticas gerais (admin)"""
        try:
            clients = await self.list_clients()
            projects = await self.list_all_projects()

            return {
                "total_clientes": len(clients),
                "total_projetos": len(projects),
                "projetos_ativos": len([p for p in projects if p.status not in [ProjectStatus.CONCLUIDO, ProjectStatus.CANCELADO]]),
                "projetos_concluidos": len([p for p in projects if p.status == ProjectStatus.CONCLUIDO]),
                "aguardando_materiais": len([p for p in projects if p.status == ProjectStatus.AGUARDANDO_MATERIAIS]),
                "em_desenvolvimento": len([p for p in projects if p.status == ProjectStatus.EM_DESENVOLVIMENTO]),
                "aguardando_aprovacao": len([p for p in projects if p.status == ProjectStatus.APROVACAO]),
            }
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas admin: {e}")
            return {}


# Singleton
_repository = None

def get_client_portal_repository() -> ClientPortalRepository:
    global _repository
    if _repository is None:
        _repository = ClientPortalRepository()
    return _repository
