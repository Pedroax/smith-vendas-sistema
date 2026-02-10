"""
Modelos Pydantic para Marcos de Projetos e Lembretes
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class MilestoneStatus(str, Enum):
    """Status de um marco do projeto"""
    PENDENTE = "pendente"
    EM_PROGRESSO = "em_progresso"
    CONCLUIDO = "concluido"
    ATRASADO = "atrasado"
    CANCELADO = "cancelado"


class ReminderType(str, Enum):
    """Tipo de lembrete (quando enviar)"""
    DEZ_DIAS = "10_dias"
    SETE_DIAS = "7_dias"
    TRES_DIAS = "3_dias"
    UM_DIA = "1_dia"
    NO_DIA = "no_dia"
    ATRASADO = "atrasado"


class ReminderMethod(str, Enum):
    """Método de envio do lembrete"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"


# Schemas de Request (para criar/atualizar)

class MilestoneCreate(BaseModel):
    """Schema para criar um novo marco"""
    project_id: int
    nome: str = Field(..., min_length=1, max_length=200)
    descricao: Optional[str] = None
    ordem: int = Field(default=0, ge=0)
    data_limite: date
    notificacao_whatsapp: bool = True
    notificacao_email: bool = False


class MilestoneUpdate(BaseModel):
    """Schema para atualizar um marco existente"""
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    descricao: Optional[str] = None
    ordem: Optional[int] = Field(None, ge=0)
    data_limite: Optional[date] = None
    status: Optional[MilestoneStatus] = None
    data_conclusao: Optional[date] = None
    notificacao_whatsapp: Optional[bool] = None
    notificacao_email: Optional[bool] = None


# Schemas de Response (o que retornar)

class Milestone(BaseModel):
    """Marco de projeto completo"""
    id: UUID
    project_id: int
    nome: str
    descricao: Optional[str]
    ordem: int
    data_limite: date
    data_conclusao: Optional[date]
    status: MilestoneStatus
    notificacao_whatsapp: bool
    notificacao_email: bool
    created_at: datetime
    updated_at: datetime

    # Campos calculados
    dias_ate_limite: Optional[int] = None
    atrasado: bool = False

    class Config:
        from_attributes = True


class ScheduledReminder(BaseModel):
    """Lembrete agendado"""
    id: UUID
    milestone_id: UUID
    tipo: ReminderType
    data_envio: date
    enviado: bool
    enviado_em: Optional[datetime]
    erro_envio: Optional[str]
    metodo: ReminderMethod
    created_at: datetime

    class Config:
        from_attributes = True


class MilestoneWithReminders(Milestone):
    """Marco com lista de lembretes agendados"""
    lembretes: list[ScheduledReminder] = []


# Schema para bulk creation (criar vários marcos de uma vez)

class BulkMilestoneCreate(BaseModel):
    """Criar múltiplos marcos de uma vez (ao criar projeto)"""
    project_id: int
    milestones: list[MilestoneCreate]
