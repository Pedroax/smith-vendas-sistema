"""
Modelos do Portal do Cliente
Sistema de acompanhamento de projetos com linha do tempo
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


# ============================================
# ENUMS
# ============================================

class ProjectStatus(str, Enum):
    """Status do projeto"""
    BRIEFING = "briefing"
    AGUARDANDO_MATERIAIS = "aguardando_materiais"
    EM_DESENVOLVIMENTO = "em_desenvolvimento"
    REVISAO = "revisao"
    APROVACAO = "aprovacao"
    CONCLUIDO = "concluido"
    PAUSADO = "pausado"
    CANCELADO = "cancelado"


class DeliveryStatus(str, Enum):
    """Status de uma entrega (cliente -> empresa)"""
    PENDENTE = "pendente"
    ENVIADO = "enviado"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class ApprovalStatus(str, Enum):
    """Status de aprovação (empresa -> cliente)"""
    AGUARDANDO = "aguardando"
    APROVADO = "aprovado"
    AJUSTES_SOLICITADOS = "ajustes_solicitados"


class TimelineEventType(str, Enum):
    """Tipos de eventos na timeline"""
    PROJETO_CRIADO = "projeto_criado"
    ETAPA_AVANCADA = "etapa_avancada"
    MATERIAL_SOLICITADO = "material_solicitado"
    MATERIAL_ENVIADO = "material_enviado"
    MATERIAL_APROVADO = "material_aprovado"
    ENTREGA_PARCIAL = "entrega_parcial"
    APROVACAO_SOLICITADA = "aprovacao_solicitada"
    APROVADO = "aprovado"
    AJUSTES_SOLICITADOS = "ajustes_solicitados"
    COMENTARIO = "comentario"
    PROJETO_CONCLUIDO = "projeto_concluido"
    PAGAMENTO_RECEBIDO = "pagamento_recebido"
    REUNIAO_AGENDADA = "reuniao_agendada"


class PaymentStatus(str, Enum):
    """Status de pagamento"""
    PENDENTE = "pendente"
    PAGO = "pago"
    ATRASADO = "atrasado"
    CANCELADO = "cancelado"


# ============================================
# MODELOS DE CLIENTE
# ============================================

class ClientBase(BaseModel):
    """Base do cliente"""
    nome: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)
    empresa: Optional[str] = Field(None, max_length=100)
    documento: Optional[str] = Field(None, max_length=20)  # CPF ou CNPJ
    avatar_url: Optional[str] = None


class ClientCreate(ClientBase):
    """Criar cliente"""
    senha: str = Field(..., min_length=6)


class ClientUpdate(BaseModel):
    """Atualizar cliente"""
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    empresa: Optional[str] = None
    documento: Optional[str] = None
    avatar_url: Optional[str] = None


class Client(ClientBase):
    """Cliente completo"""
    id: UUID = Field(default_factory=uuid4)
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ultimo_acesso: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE PROJETO
# ============================================

class ProjectStageTemplate(BaseModel):
    """Template de etapa de projeto"""
    nome: str
    descricao: str
    ordem: int
    cor: str = "#6366f1"  # Indigo padrão


class ProjectBase(BaseModel):
    """Base do projeto"""
    nome: str = Field(..., min_length=2, max_length=200)
    descricao: Optional[str] = None
    tipo: str = Field(..., max_length=50)  # site, identidade_visual, video, etc
    valor_total: float = Field(default=0, ge=0)
    data_inicio: Optional[datetime] = None
    data_previsao: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    """Criar projeto"""
    client_id: UUID
    etapas: Optional[List[str]] = None  # Lista de nomes de etapas personalizadas


class ProjectUpdate(BaseModel):
    """Atualizar projeto"""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[ProjectStatus] = None
    valor_total: Optional[float] = None
    data_previsao: Optional[datetime] = None
    etapa_atual: Optional[int] = None


class Project(ProjectBase):
    """Projeto completo"""
    id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    status: ProjectStatus = ProjectStatus.BRIEFING
    etapa_atual: int = 0  # Índice da etapa atual
    progresso: int = 0  # 0-100%
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    concluido_em: Optional[datetime] = None

    # Link único para acesso direto
    access_token: str = Field(default_factory=lambda: uuid4().hex[:12])

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE ETAPA
# ============================================

class StageBase(BaseModel):
    """Base da etapa"""
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: Optional[str] = None
    ordem: int = Field(..., ge=0)


class StageCreate(StageBase):
    """Criar etapa"""
    project_id: UUID


class StageUpdate(BaseModel):
    """Atualizar etapa"""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    concluida: Optional[bool] = None
    data_conclusao: Optional[datetime] = None


class Stage(StageBase):
    """Etapa completa"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    concluida: bool = False
    data_inicio: Optional[datetime] = None
    data_conclusao: Optional[datetime] = None
    cor: str = "#6366f1"

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE ENTREGA (Cliente -> Empresa)
# ============================================

class DeliveryItemBase(BaseModel):
    """Item que o cliente precisa entregar"""
    nome: str = Field(..., min_length=2, max_length=200)
    descricao: Optional[str] = None
    obrigatorio: bool = True


class DeliveryItemCreate(DeliveryItemBase):
    """Criar item de entrega"""
    project_id: UUID
    stage_id: Optional[UUID] = None  # Pode ser associado a uma etapa específica


class DeliveryItemUpdate(BaseModel):
    """Atualizar item de entrega"""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[DeliveryStatus] = None
    arquivo_url: Optional[str] = None
    comentario_cliente: Optional[str] = None


class DeliveryItem(DeliveryItemBase):
    """Item de entrega completo"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    stage_id: Optional[UUID] = None
    status: DeliveryStatus = DeliveryStatus.PENDENTE
    arquivo_url: Optional[str] = None
    arquivo_nome: Optional[str] = None
    comentario_cliente: Optional[str] = None
    enviado_em: Optional[datetime] = None
    aprovado_em: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE APROVAÇÃO (Empresa -> Cliente)
# ============================================

class ApprovalItemBase(BaseModel):
    """Item para aprovação do cliente"""
    titulo: str = Field(..., min_length=2, max_length=200)
    descricao: Optional[str] = None
    tipo: str = "arquivo"  # arquivo, link, texto


class ApprovalItemCreate(ApprovalItemBase):
    """Criar item para aprovação"""
    project_id: UUID
    stage_id: Optional[UUID] = None
    arquivo_url: Optional[str] = None
    link_externo: Optional[str] = None


class ApprovalItemUpdate(BaseModel):
    """Atualizar aprovação"""
    status: Optional[ApprovalStatus] = None
    feedback_cliente: Optional[str] = None


class ApprovalItem(ApprovalItemBase):
    """Item de aprovação completo"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    stage_id: Optional[UUID] = None
    status: ApprovalStatus = ApprovalStatus.AGUARDANDO
    arquivo_url: Optional[str] = None
    link_externo: Optional[str] = None
    feedback_cliente: Optional[str] = None
    versao: int = 1
    enviado_em: datetime = Field(default_factory=datetime.utcnow)
    respondido_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE TIMELINE
# ============================================

class TimelineEventBase(BaseModel):
    """Evento da timeline"""
    tipo: TimelineEventType
    titulo: str
    descricao: Optional[str] = None
    metadata: Optional[dict] = None  # Dados extras (ex: de qual etapa, qual arquivo, etc)


class TimelineEventCreate(TimelineEventBase):
    """Criar evento"""
    project_id: UUID
    user_id: Optional[UUID] = None  # Quem fez a ação (cliente ou admin)
    is_client_action: bool = False


class TimelineEvent(TimelineEventBase):
    """Evento completo"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    user_id: Optional[UUID] = None
    is_client_action: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE COMENTÁRIO
# ============================================

class CommentBase(BaseModel):
    """Comentário no projeto"""
    conteudo: str = Field(..., min_length=1, max_length=2000)


class CommentCreate(CommentBase):
    """Criar comentário"""
    project_id: UUID
    stage_id: Optional[UUID] = None
    approval_id: Optional[UUID] = None  # Se for comentário em uma aprovação
    is_client: bool = False


class Comment(CommentBase):
    """Comentário completo"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    stage_id: Optional[UUID] = None
    approval_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    user_nome: str = "Sistema"
    is_client: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# MODELOS DE PAGAMENTO
# ============================================

class PaymentBase(BaseModel):
    """Pagamento do projeto"""
    descricao: str = Field(..., min_length=2, max_length=200)
    valor: float = Field(..., gt=0)
    data_vencimento: datetime


class PaymentCreate(PaymentBase):
    """Criar pagamento"""
    project_id: UUID


class PaymentUpdate(BaseModel):
    """Atualizar pagamento"""
    status: Optional[PaymentStatus] = None
    data_pagamento: Optional[datetime] = None
    comprovante_url: Optional[str] = None


class Payment(PaymentBase):
    """Pagamento completo"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    status: PaymentStatus = PaymentStatus.PENDENTE
    data_pagamento: Optional[datetime] = None
    comprovante_url: Optional[str] = None
    parcela: int = 1
    total_parcelas: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================
# MODELOS COMPOSTOS (Para respostas da API)
# ============================================

class ProjectWithDetails(Project):
    """Projeto com todos os detalhes"""
    client: Optional[Client] = None
    etapas: List[Stage] = []
    entregas_pendentes: int = 0
    aprovacoes_pendentes: int = 0
    timeline_recente: List[TimelineEvent] = []
    proximos_pagamentos: List[Payment] = []


class ClientPortalDashboard(BaseModel):
    """Dashboard do cliente"""
    client: Client
    projetos_ativos: List[ProjectWithDetails] = []
    entregas_pendentes_total: int = 0
    aprovacoes_pendentes_total: int = 0
    notificacoes: List[dict] = []


class ProjectTimeline(BaseModel):
    """Timeline completa do projeto"""
    project: Project
    eventos: List[TimelineEvent] = []
    etapas: List[Stage] = []


# ============================================
# TEMPLATES DE PROJETO
# ============================================

PROJECT_TEMPLATES = {
    "site_institucional": {
        "nome": "Site Institucional",
        "etapas": [
            {"nome": "Briefing", "descricao": "Entender necessidades e objetivos", "cor": "#8b5cf6"},
            {"nome": "Wireframe", "descricao": "Estrutura e layout das páginas", "cor": "#6366f1"},
            {"nome": "Design", "descricao": "Visual completo do site", "cor": "#3b82f6"},
            {"nome": "Desenvolvimento", "descricao": "Programação do site", "cor": "#0ea5e9"},
            {"nome": "Conteúdo", "descricao": "Inserção de textos e imagens", "cor": "#14b8a6"},
            {"nome": "Testes", "descricao": "Verificação de funcionamento", "cor": "#22c55e"},
            {"nome": "Entrega", "descricao": "Site no ar!", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Logo em PNG (fundo transparente)", "obrigatorio": True},
            {"nome": "Textos das páginas", "obrigatorio": True},
            {"nome": "Fotos da empresa/equipe", "obrigatorio": False},
            {"nome": "Dados de contato", "obrigatorio": True},
            {"nome": "Acesso ao domínio", "obrigatorio": True},
            {"nome": "Acesso à hospedagem", "obrigatorio": True},
        ]
    },
    "identidade_visual": {
        "nome": "Identidade Visual",
        "etapas": [
            {"nome": "Briefing", "descricao": "Entender a marca e público", "cor": "#8b5cf6"},
            {"nome": "Pesquisa", "descricao": "Análise de mercado e referências", "cor": "#6366f1"},
            {"nome": "Conceitos", "descricao": "Primeiras propostas de logo", "cor": "#3b82f6"},
            {"nome": "Refinamento", "descricao": "Ajustes no conceito escolhido", "cor": "#0ea5e9"},
            {"nome": "Aplicações", "descricao": "Papelaria, redes sociais, etc", "cor": "#14b8a6"},
            {"nome": "Entrega", "descricao": "Manual de marca completo", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Referências visuais (marcas que gosta)", "obrigatorio": False},
            {"nome": "Cores preferidas", "obrigatorio": False},
            {"nome": "Descrição do público-alvo", "obrigatorio": True},
            {"nome": "Valores da empresa", "obrigatorio": True},
        ]
    },
    "sistema_web": {
        "nome": "Sistema Web",
        "etapas": [
            {"nome": "Briefing", "descricao": "Levantamento de requisitos", "cor": "#8b5cf6"},
            {"nome": "Arquitetura", "descricao": "Definição técnica", "cor": "#6366f1"},
            {"nome": "Protótipo", "descricao": "Wireframes e fluxos", "cor": "#3b82f6"},
            {"nome": "Design UI", "descricao": "Interface visual", "cor": "#0ea5e9"},
            {"nome": "Backend", "descricao": "Lógica e banco de dados", "cor": "#14b8a6"},
            {"nome": "Frontend", "descricao": "Interface do usuário", "cor": "#22c55e"},
            {"nome": "Integração", "descricao": "Conectar tudo", "cor": "#eab308"},
            {"nome": "Testes", "descricao": "QA e correções", "cor": "#f97316"},
            {"nome": "Deploy", "descricao": "Sistema no ar!", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Documento de requisitos", "obrigatorio": True},
            {"nome": "Fluxos de processo", "obrigatorio": True},
            {"nome": "Acessos a sistemas existentes", "obrigatorio": False},
            {"nome": "Dados para importação", "obrigatorio": False},
        ]
    },
    "video_institucional": {
        "nome": "Vídeo Institucional",
        "etapas": [
            {"nome": "Briefing", "descricao": "Objetivos e mensagem", "cor": "#8b5cf6"},
            {"nome": "Roteiro", "descricao": "Texto e storyboard", "cor": "#6366f1"},
            {"nome": "Pré-produção", "descricao": "Planejamento de gravação", "cor": "#3b82f6"},
            {"nome": "Gravação", "descricao": "Captação de imagens", "cor": "#0ea5e9"},
            {"nome": "Edição", "descricao": "Montagem e efeitos", "cor": "#14b8a6"},
            {"nome": "Revisão", "descricao": "Ajustes finais", "cor": "#22c55e"},
            {"nome": "Entrega", "descricao": "Vídeo finalizado", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Logo em alta resolução", "obrigatorio": True},
            {"nome": "Materiais de apoio (fotos, vídeos)", "obrigatorio": False},
            {"nome": "Texto para locução", "obrigatorio": False},
            {"nome": "Músicas preferidas", "obrigatorio": False},
        ]
    }
}
