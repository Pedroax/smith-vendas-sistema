"""
Modelos para Sistema de Notificações
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Tipo de notificação"""
    LEAD_QUENTE = "lead_quente"  # Lead quente sem interação há X dias
    AGENDAMENTO = "agendamento"  # Agendamento próximo
    LEAD_PARADO = "lead_parado"  # Lead parado no estágio há X dias
    PROPOSTA_VENCENDO = "proposta_vencendo"  # Proposta próxima do prazo
    NOVO_LEAD = "novo_lead"  # Novo lead no sistema
    LEAD_MOVIDO = "lead_movido"  # Lead mudou de estágio
    FOLLOW_UP = "follow_up"  # Lembrete de follow-up
    SISTEMA = "sistema"  # Notificação do sistema
    OUTRO = "outro"


class NotificationPriority(str, Enum):
    """Prioridade da notificação"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """Modelo de notificação"""
    id: str
    user_id: Optional[str] = None  # None = todos os usuários
    tipo: NotificationType
    prioridade: NotificationPriority = NotificationPriority.MEDIUM
    titulo: str
    mensagem: str
    link: Optional[str] = None  # Link para navegar ao clicar
    lida: bool = False
    lead_id: Optional[str] = None  # Lead relacionado
    lead_nome: Optional[str] = None
    created_at: str
    read_at: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class NotificationCreate(BaseModel):
    """Dados para criar notificação"""
    user_id: Optional[str] = None
    tipo: NotificationType
    prioridade: NotificationPriority = NotificationPriority.MEDIUM
    titulo: str
    mensagem: str
    link: Optional[str] = None
    lead_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class NotificationUpdate(BaseModel):
    """Dados para atualizar notificação"""
    lida: Optional[bool] = None
