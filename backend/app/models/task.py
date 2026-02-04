"""
Modelos para Sistema de Tarefas
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class TaskStatus(str, Enum):
    HOJE = "hoje"
    ESTA_SEMANA = "esta_semana"
    DEPOIS = "depois"
    FEITO = "feito"


class TaskPriority(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class Task(BaseModel):
    id: str
    titulo: str
    descricao: Optional[str] = None
    status: TaskStatus
    prioridade: TaskPriority = TaskPriority.MEDIA
    prazo: Optional[str] = None
    lead_id: Optional[str] = None
    lead_nome: Optional[str] = None
    project_id: Optional[str] = None
    project_nome: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

    class Config:
        use_enum_values = True


class TaskCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    status: TaskStatus = TaskStatus.HOJE
    prioridade: TaskPriority = TaskPriority.MEDIA
    prazo: Optional[str] = None
    lead_id: Optional[str] = None
    project_id: Optional[str] = None


class TaskUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[TaskStatus] = None
    prioridade: Optional[TaskPriority] = None
    prazo: Optional[str] = None
    lead_id: Optional[str] = None
    project_id: Optional[str] = None
