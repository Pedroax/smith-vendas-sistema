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
    cor: str = "#6366f1"  # Cor da etapa (hex)


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
# MODELOS DE DOCUMENTO
# ============================================

class DocumentType(str, Enum):
    """Tipo de documento"""
    CONTRATO = "contrato"
    TERMO_ENTREGA = "termo_entrega"
    OUTRO = "outro"


class ProjectDocumentBase(BaseModel):
    """Base do documento"""
    nome: str = Field(..., min_length=2, max_length=200)
    tipo: DocumentType = DocumentType.OUTRO
    descricao: Optional[str] = None


class ProjectDocumentCreate(ProjectDocumentBase):
    """Criar documento"""
    project_id: UUID
    arquivo_url: str = Field(..., min_length=5)
    arquivo_nome: str = Field(..., min_length=1)
    arquivo_tamanho: Optional[int] = None  # Bytes


class ProjectDocumentUpdate(BaseModel):
    """Atualizar documento"""
    nome: Optional[str] = None
    descricao: Optional[str] = None


class ProjectDocument(ProjectDocumentBase):
    """Documento completo"""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    arquivo_url: str
    arquivo_nome: str
    arquivo_tamanho: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = "admin"  # Quem fez upload

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
    "agente_ia_whatsapp": {
        "nome": "🤖 Agente de IA para WhatsApp",
        "etapas": [
            {"nome": "Briefing", "descricao": "Levantamento de requisitos e objetivos", "cor": "#8b5cf6"},
            {"nome": "Treinamento IA", "descricao": "Criação da base de conhecimento", "cor": "#6366f1"},
            {"nome": "Integração WhatsApp", "descricao": "Configuração e conexão", "cor": "#3b82f6"},
            {"nome": "Testes", "descricao": "Simulação de conversas", "cor": "#0ea5e9"},
            {"nome": "Homologação", "descricao": "Validação com cliente", "cor": "#22c55e"},
            {"nome": "Produção", "descricao": "Agente no ar!", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "FAQ e respostas padrão", "obrigatorio": True},
            {"nome": "Fluxos de conversação", "obrigatorio": True},
            {"nome": "Materiais de treinamento (PDFs, docs)", "obrigatorio": False},
            {"nome": "Acesso à conta WhatsApp Business", "obrigatorio": True},
        ]
    },
    "ia_analitica": {
        "nome": "🧠 Sistema de IA Analítica",
        "etapas": [
            {"nome": "Briefing", "descricao": "Definição de métricas e objetivos", "cor": "#8b5cf6"},
            {"nome": "Coleta de Dados", "descricao": "Integração com fontes de dados", "cor": "#6366f1"},
            {"nome": "Modelagem", "descricao": "Criação do modelo de IA", "cor": "#3b82f6"},
            {"nome": "Treinamento", "descricao": "Treinar modelo com dados reais", "cor": "#0ea5e9"},
            {"nome": "Deploy", "descricao": "Colocar modelo em produção", "cor": "#14b8a6"},
            {"nome": "Monitoramento", "descricao": "Ajustes e otimizações", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Base de dados histórica", "obrigatorio": True},
            {"nome": "Definição de KPIs", "obrigatorio": True},
            {"nome": "Acessos a sistemas/APIs", "obrigatorio": False},
        ]
    },
    "ia_rh": {
        "nome": "👔 IA para Recursos Humanos",
        "etapas": [
            {"nome": "Briefing", "descricao": "Mapeamento de processos de RH", "cor": "#8b5cf6"},
            {"nome": "Análise", "descricao": "Identificação de pontos de automação", "cor": "#6366f1"},
            {"nome": "Desenvolvimento", "descricao": "Criação da solução de IA", "cor": "#3b82f6"},
            {"nome": "Treinamento", "descricao": "Treinar com dados de RH", "cor": "#0ea5e9"},
            {"nome": "Validação", "descricao": "Testes com equipe de RH", "cor": "#22c55e"},
            {"nome": "Produção", "descricao": "Sistema em uso", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Processos atuais de RH documentados", "obrigatorio": True},
            {"nome": "Base de dados de candidatos/colaboradores", "obrigatorio": False},
            {"nome": "Integrações necessárias (ATS, etc)", "obrigatorio": False},
        ]
    },
    "automacao_rpa": {
        "nome": "⚙️ Automação RPA",
        "etapas": [
            {"nome": "Mapeamento", "descricao": "Identificar processos repetitivos", "cor": "#8b5cf6"},
            {"nome": "Desenvolvimento", "descricao": "Criar fluxos de automação", "cor": "#3b82f6"},
            {"nome": "Testes", "descricao": "Validar automações", "cor": "#0ea5e9"},
            {"nome": "Homologação", "descricao": "Aprovação do cliente", "cor": "#22c55e"},
            {"nome": "Produção", "descricao": "Robôs em execução", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Documentação do processo atual", "obrigatorio": True},
            {"nome": "Acessos aos sistemas", "obrigatorio": True},
            {"nome": "Credenciais necessárias", "obrigatorio": True},
        ]
    },
    "aplicativo_mobile": {
        "nome": "📱 Aplicativo Mobile",
        "etapas": [
            {"nome": "Briefing", "descricao": "Requisitos e funcionalidades", "cor": "#8b5cf6"},
            {"nome": "Design", "descricao": "Interface e experiência do usuário", "cor": "#6366f1"},
            {"nome": "Desenvolvimento", "descricao": "Programação do app", "cor": "#3b82f6"},
            {"nome": "Testes", "descricao": "QA em dispositivos reais", "cor": "#0ea5e9"},
            {"nome": "Deploy", "descricao": "Publicação nas lojas", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Wireframes/mockups de referência", "obrigatorio": False},
            {"nome": "Logo e identidade visual", "obrigatorio": True},
            {"nome": "Textos e conteúdo", "obrigatorio": True},
            {"nome": "Conta de desenvolvedor (Apple/Google)", "obrigatorio": True},
        ]
    },
    "sistema_empresa": {
        "nome": "💼 Sistema para Empresas",
        "etapas": [
            {"nome": "Briefing", "descricao": "Levantamento de requisitos", "cor": "#8b5cf6"},
            {"nome": "Arquitetura", "descricao": "Definição técnica e escopo", "cor": "#6366f1"},
            {"nome": "Protótipo", "descricao": "Wireframes e fluxos", "cor": "#3b82f6"},
            {"nome": "Desenvolvimento", "descricao": "Backend e Frontend", "cor": "#0ea5e9"},
            {"nome": "Integração", "descricao": "Conectar com sistemas existentes", "cor": "#14b8a6"},
            {"nome": "Testes", "descricao": "QA e correções", "cor": "#f97316"},
            {"nome": "Deploy", "descricao": "Sistema no ar!", "cor": "#10b981"},
        ],
        "entregas": [
            {"nome": "Documento de requisitos", "obrigatorio": True},
            {"nome": "Fluxos de processo", "obrigatorio": True},
            {"nome": "Acessos a sistemas existentes", "obrigatorio": False},
            {"nome": "Dados para migração/importação", "obrigatorio": False},
        ]
    },
    "projeto_ia_generico": {
        "nome": "🎯 Projeto de IA (Genérico)",
        "etapas": [
            {"nome": "Briefing", "descricao": "Levantamento de requisitos", "cor": "#8b5cf6"},
            {"nome": "Planejamento", "descricao": "Arquitetura e escopo técnico", "cor": "#6366f1"},
            {"nome": "Desenvolvimento", "descricao": "Codificação e integração", "cor": "#3b82f6"},
            {"nome": "Treinamento", "descricao": "Treinar IA com dados", "cor": "#0ea5e9"},
            {"nome": "Testes", "descricao": "Validação e ajustes", "cor": "#14b8a6"},
            {"nome": "Homologação", "descricao": "Aprovação do cliente", "cor": "#22c55e"},
            {"nome": "Produção", "descricao": "Deploy e go-live", "cor": "#10b981"},
            {"nome": "Monitoramento", "descricao": "Ajustes e otimização", "cor": "#f59e0b"},
        ],
        "entregas": [
            {"nome": "Especificações do projeto", "obrigatorio": True},
            {"nome": "Dados de treinamento", "obrigatorio": False},
            {"nome": "Acessos e credenciais", "obrigatorio": False},
        ]
    }
}
