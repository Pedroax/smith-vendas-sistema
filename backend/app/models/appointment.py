"""
Modelos para Agendamentos/Compromissos
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AppointmentType(str, Enum):
    """Tipo de agendamento"""
    REUNIAO = "reuniao"
    LIGACAO = "ligacao"
    FOLLOW_UP = "follow_up"
    DEMO = "demo"
    APRESENTACAO = "apresentacao"
    OUTRO = "outro"


class AppointmentStatus(str, Enum):
    """Status do agendamento"""
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"
    REMARCADO = "remarcado"


class Appointment(BaseModel):
    """Modelo de agendamento"""
    id: str
    lead_id: str
    lead_nome: Optional[str] = None  # Denormalized for easier display
    tipo: AppointmentType
    titulo: str
    descricao: Optional[str] = None
    data_hora: str  # ISO format datetime
    duracao_minutos: int = 60
    status: AppointmentStatus = AppointmentStatus.AGENDADO
    user_nome: str = "Sistema"
    location: Optional[str] = None  # Para reuniões presenciais
    meeting_url: Optional[str] = None  # Para reuniões online
    observacoes: Optional[str] = None
    lembrete_enviado: bool = False
    created_at: str
    updated_at: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class AppointmentCreate(BaseModel):
    """Dados para criar agendamento"""
    lead_id: str
    tipo: AppointmentType
    titulo: str
    descricao: Optional[str] = None
    data_hora: str  # ISO format datetime
    duracao_minutos: int = 60
    user_nome: str = "Sistema"
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    observacoes: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class AppointmentUpdate(BaseModel):
    """Dados para atualizar agendamento"""
    tipo: Optional[AppointmentType] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_hora: Optional[str] = None
    duracao_minutos: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    observacoes: Optional[str] = None
    lembrete_enviado: Optional[bool] = None
