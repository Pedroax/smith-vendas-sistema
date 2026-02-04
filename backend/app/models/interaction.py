"""
Modelos para Interações/Conversas com Leads
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    """Tipo de interação"""
    NOTA = "nota"
    LIGACAO = "ligacao"
    REUNIAO = "reuniao"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PROPOSTA = "proposta"
    FOLLOW_UP = "follow_up"
    OUTRO = "outro"


class Interaction(BaseModel):
    """Modelo de interação com lead"""
    id: str
    lead_id: str
    tipo: InteractionType
    assunto: Optional[str] = None
    conteudo: str
    user_id: Optional[str] = None
    user_nome: str = "Sistema"
    created_at: str
    metadata: dict = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class InteractionCreate(BaseModel):
    """Dados para criar interação"""
    lead_id: str
    tipo: InteractionType
    assunto: Optional[str] = None
    conteudo: str
    user_nome: str = "Sistema"
    metadata: dict = Field(default_factory=dict)


class InteractionUpdate(BaseModel):
    """Dados para atualizar interação"""
    assunto: Optional[str] = None
    conteudo: Optional[str] = None
    tipo: Optional[InteractionType] = None
