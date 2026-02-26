"""
Modelos de dados para Leads
Inclui campos para qualificação e ROI
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LeadStatus(str, Enum):
    """Status do lead no funil de vendas"""
    NOVO = "novo"
    CONTATO_INICIAL = "contato_inicial"
    QUALIFICANDO = "qualificando"
    QUALIFICADO = "qualificado"
    AGUARDANDO_ESCOLHA_HORARIO = "aguardando_escolha_horario"  # Viu horários, aguardando escolha
    AGENDAMENTO_MARCADO = "agendamento_marcado"
    GANHO = "ganho"
    PERDIDO = "perdido"


class LeadOrigin(str, Enum):
    """Origem do lead"""
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    SITE = "site"
    INDICACAO = "indicacao"
    FACEBOOK_ADS = "facebook_ads"
    TESTE = "teste"
    OUTRO = "outro"


class LeadTemperature(str, Enum):
    """Temperatura do lead (engajamento)"""
    QUENTE = "quente"  # 🔥 Respondendo rápido, interessado
    MORNO = "morno"    # 🟡 Respondendo devagar, interesse médio
    FRIO = "frio"      # ❄️ Não respondendo, baixo interesse


class QualificationData(BaseModel):
    """Dados de qualificação coletados pela IA"""
    # Qualificação direta (BANT simplificado)
    cargo: Optional[str] = None  # Cargo do lead na empresa
    faturamento_anual: Optional[float] = None  # Faturamento anual da empresa em R$
    is_decision_maker: Optional[bool] = None  # É tomador de decisão?
    urgency: Optional[str] = None  # Urgência/timing: "imediato", "1-3_meses", "3-6_meses", "sem_urgencia"
    setor: Optional[str] = None  # Setor/nicho da empresa

    # Escolha pós-qualificação
    wants_roi: Optional[bool] = None  # Quer ver análise de ROI?
    wants_meeting: Optional[bool] = None  # Quer agendar reunião?

    # Dados operacionais para ROI (só coletados se wants_roi = True)
    atendimentos_por_dia: Optional[int] = None
    tempo_por_atendimento: Optional[int] = None  # minutos
    ticket_medio: Optional[float] = None
    funcionarios_atendimento: Optional[int] = None

    # Informações complementares
    maior_desafio: Optional[str] = None
    ferramentas_atuais: Optional[List[str]] = None

    # Site da empresa (coletado durante qualificação)
    site_url: Optional[str] = None       # URL do site ou "sem_site" se não tiver
    site_perguntado: bool = False        # True depois de perguntar sobre o site


class ROIAnalysis(BaseModel):
    """Análise de ROI calculada"""
    tempo_economizado_mes: Optional[float] = None  # horas
    valor_economizado_ano: Optional[float] = None  # R$
    roi_percentual: Optional[float] = None  # %
    payback_meses: Optional[int] = None
    pdf_url: Optional[str] = None  # URL do PDF gerado
    generated_at: Optional[datetime] = None


class FollowUpConfig(BaseModel):
    """Configuração de follow-ups"""
    tentativas_realizadas: int = 0
    proxima_tentativa: Optional[datetime] = None
    intervalo_horas: List[int] = [24, 72, 168]  # 1 dia, 3 dias, 7 dias
    mensagem_template: Optional[str] = None


class ConversationMessage(BaseModel):
    """Mensagem da conversa"""
    id: str
    role: str  # 'user' ou 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class Lead(BaseModel):
    """Modelo completo de Lead"""
    # Identificação
    id: str
    nome: str
    empresa: Optional[str] = None
    telefone: str
    email: Optional[str] = None

    # Status e origem
    status: LeadStatus = LeadStatus.NOVO
    origem: LeadOrigin
    temperatura: Optional[LeadTemperature] = None

    # Qualificação
    qualification_data: Optional[QualificationData] = None
    lead_score: int = 0  # 0-100

    # ROI
    roi_analysis: Optional[ROIAnalysis] = None
    valor_estimado: float = 0.0  # Valor estimado do negócio

    # Agendamento
    meeting_scheduled_at: Optional[datetime] = None
    meeting_google_event_id: Optional[str] = None
    temp_meeting_slot: Optional[Dict[str, Any]] = None  # Slot temporário durante processo de agendamento

    # Follow-up
    followup_config: FollowUpConfig = Field(default_factory=FollowUpConfig)

    # Histórico
    conversation_history: List[ConversationMessage] = []
    ultima_interacao: Optional[datetime] = None
    ultima_mensagem_ia: Optional[str] = None

    # Notas e observações
    notas: Optional[str] = None
    tags: List[str] = []

    # IA metadata
    ai_summary: Optional[str] = None  # Resumo gerado pela IA
    ai_next_action: Optional[str] = None  # Próxima ação sugerida
    requires_human_approval: bool = False  # Requer aprovação humana?

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    lost_at: Optional[datetime] = None
    won_at: Optional[datetime] = None

    # Avatar (inicial ou URL)
    avatar: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LeadCreate(BaseModel):
    """Payload para criar um lead"""
    nome: str
    telefone: str
    empresa: Optional[str] = None
    email: Optional[str] = None
    origem: LeadOrigin
    notas: Optional[str] = None


class LeadUpdate(BaseModel):
    """Payload para atualizar um lead"""
    nome: Optional[str] = None
    empresa: Optional[str] = None
    email: Optional[str] = None
    status: Optional[LeadStatus] = None
    temperatura: Optional[LeadTemperature] = None
    qualification_data: Optional[QualificationData] = None
    roi_analysis: Optional[ROIAnalysis] = None
    valor_estimado: Optional[float] = None
    notas: Optional[str] = None
    tags: Optional[List[str]] = None
    ai_summary: Optional[str] = None
    requires_human_approval: Optional[bool] = None


class LeadResponse(BaseModel):
    """Response padrão de Lead"""
    success: bool
    lead: Optional[Lead] = None
    message: Optional[str] = None
