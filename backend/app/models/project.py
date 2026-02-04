"""
Modelos de dados para Projetos
Sistema de Pipeline Kanban para gerenciamento de implementações
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ProjectStatus(str, Enum):
    """Status do projeto no pipeline Kanban"""
    BACKLOG = "backlog"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"


class ProjectPriority(str, Enum):
    """Prioridade do projeto"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class Project(BaseModel):
    """Modelo completo de Projeto"""
    # Identificação
    id: str
    nome: str
    descricao: Optional[str] = None

    # Cliente (pode estar linkado a um lead)
    cliente_id: Optional[str] = None  # ID do lead/cliente
    cliente_nome: Optional[str] = None  # Nome do cliente para exibição

    # Status e prioridade
    status: ProjectStatus = ProjectStatus.BACKLOG
    prioridade: ProjectPriority = ProjectPriority.MEDIA

    # Detalhes do projeto
    prazo: Optional[datetime] = None
    valor: Optional[float] = None  # Valor do projeto em R$
    responsavel: Optional[str] = None  # Nome do responsável

    # Organização
    tags: List[str] = []

    # Notas e observações
    notas: Optional[str] = None

    # Progresso
    progresso_percentual: int = 0  # 0-100

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None  # Quando movido para "em_andamento"
    completed_at: Optional[datetime] = None  # Quando movido para "concluido"

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectCreate(BaseModel):
    """Payload para criar um projeto"""
    nome: str
    descricao: Optional[str] = None
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    prioridade: Optional[ProjectPriority] = ProjectPriority.MEDIA
    prazo: Optional[datetime] = None
    valor: Optional[float] = None
    responsavel: Optional[str] = None
    tags: Optional[List[str]] = []
    notas: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Payload para atualizar um projeto"""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = None
    status: Optional[ProjectStatus] = None
    prioridade: Optional[ProjectPriority] = None
    prazo: Optional[datetime] = None
    valor: Optional[float] = None
    responsavel: Optional[str] = None
    tags: Optional[List[str]] = None
    notas: Optional[str] = None
    progresso_percentual: Optional[int] = None


class ProjectResponse(BaseModel):
    """Response padrão de Project"""
    success: bool
    project: Optional[Project] = None
    message: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Response para listagem de projetos"""
    success: bool
    projects: List[Project] = []
    total: int = 0
    message: Optional[str] = None
