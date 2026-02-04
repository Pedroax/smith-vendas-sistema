"""
Modelo de Agendamento
Representa reuniões agendadas com leads
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class AgendamentoStatus(str, Enum):
    """Status do agendamento"""
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    REALIZADO = "realizado"
    NAO_COMPARECEU = "nao_compareceu"


class Agendamento(BaseModel):
    """Modelo de agendamento de reunião"""

    id: str = Field(..., description="ID único do agendamento")
    lead_id: str = Field(..., description="ID do lead")

    # Dados da reunião
    data_hora: datetime = Field(..., description="Data e hora da reunião")
    duracao_minutos: int = Field(default=30, description="Duração em minutos")

    # Integração com Google Calendar
    google_event_id: Optional[str] = Field(None, description="ID do evento no Google Calendar")
    google_meet_link: Optional[str] = Field(None, description="Link do Google Meet")
    google_event_link: Optional[str] = Field(None, description="Link do evento no Google Calendar")

    # Status
    status: AgendamentoStatus = Field(default=AgendamentoStatus.AGENDADO, description="Status do agendamento")

    # Confirmação
    confirmado_em: Optional[datetime] = Field(None, description="Data/hora da confirmação")
    confirmado_via: Optional[str] = Field(None, description="Canal de confirmação (whatsapp, email)")

    # Lembretes
    lembrete_24h_enviado: bool = Field(default=False, description="Lembrete 24h enviado")
    lembrete_3h_enviado: bool = Field(default=False, description="Lembrete 3h enviado")
    lembrete_30min_enviado: bool = Field(default=False, description="Lembrete 30min enviado")

    # Observações
    observacoes: Optional[str] = Field(None, description="Observações sobre a reunião")
    motivo_cancelamento: Optional[str] = Field(None, description="Motivo do cancelamento")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    updated_at: datetime = Field(default_factory=datetime.now, description="Última atualização")

    class Config:
        """Configuração do modelo"""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "lead_id": "550e8400-e29b-41d4-a716-446655440001",
                "data_hora": "2025-01-15T14:00:00-03:00",
                "duracao_minutos": 30,
                "google_event_id": "abc123xyz",
                "google_meet_link": "https://meet.google.com/abc-defg-hij",
                "status": "agendado",
                "lembrete_24h_enviado": False,
                "lembrete_3h_enviado": False,
                "lembrete_30min_enviado": False,
            }
        }
