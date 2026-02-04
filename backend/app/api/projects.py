"""
API de Projetos - CRUD e operações para Pipeline Kanban
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from datetime import datetime
import uuid

from app.models.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatus,
    ProjectPriority,
)
from app.repository.projects_repository import ProjectsRepository

router = APIRouter()

# Repository para acesso ao banco de dados
repository = ProjectsRepository()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project_data: ProjectCreate):
    """
    Cria um novo projeto

    Args:
        project_data: Dados do projeto a criar

    Returns:
        Projeto criado com ID
    """
    try:
        # Gerar ID único
        project_id = str(uuid.uuid4())

        # Criar projeto
        project = Project(
            id=project_id,
            nome=project_data.nome,
            descricao=project_data.descricao,
            cliente_id=project_data.cliente_id,
            cliente_nome=project_data.cliente_nome,
            status=ProjectStatus.BACKLOG,
            prioridade=project_data.prioridade or ProjectPriority.MEDIA,
            prazo=project_data.prazo,
            valor=project_data.valor,
            responsavel=project_data.responsavel,
            tags=project_data.tags or [],
            notas=project_data.notas,
            progresso_percentual=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Salvar no banco via repository
        created_project = await repository.create(project)

        logger.info(f"Projeto criado: {created_project.nome} ({created_project.id})")

        return ProjectResponse(
            success=True,
            project=created_project,
            message="Projeto criado com sucesso"
        )

    except Exception as e:
        logger.error(f"Erro ao criar projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Project])
async def list_projects(
    status: Optional[ProjectStatus] = None,
    prioridade: Optional[ProjectPriority] = None,
    cliente_id: Optional[str] = None,
    responsavel: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Lista projetos com filtros opcionais

    Args:
        status: Filtrar por status
        prioridade: Filtrar por prioridade
        cliente_id: Filtrar por cliente
        responsavel: Filtrar por responsável
        limit: Número máximo de resultados
        offset: Offset para paginação

    Returns:
        Lista de projetos
    """
    try:
        # Buscar projetos do banco via repository
        projects = await repository.list_all(
            status=status,
            prioridade=prioridade,
            cliente_id=cliente_id,
            responsavel=responsavel,
            limit=limit,
            offset=offset
        )

        logger.info(f"Listando {len(projects)} projetos")

        return projects

    except Exception as e:
        logger.error(f"Erro ao listar projetos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-status")
async def get_stats_by_status():
    """
    Retorna contagem de projetos por status (para Kanban)

    Returns:
        Estatísticas por status
    """
    try:
        stats = await repository.get_stats_by_status()

        logger.info(f"Estatísticas por status: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """
    Busca um projeto por ID

    Args:
        project_id: ID do projeto

    Returns:
        Projeto encontrado
    """
    try:
        project = await repository.get_by_id(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

        logger.info(f"Projeto recuperado: {project.nome} ({project_id})")

        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: ProjectUpdate):
    """
    Atualiza um projeto existente

    Args:
        project_id: ID do projeto
        project_data: Dados a atualizar

    Returns:
        Projeto atualizado
    """
    try:
        # Verificar se projeto existe
        existing_project = await repository.get_by_id(project_id)
        if not existing_project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

        # Preparar dados de atualização
        update_data = project_data.model_dump(exclude_unset=True)

        # Converter enums para valores
        if "status" in update_data:
            update_data["status"] = update_data["status"].value
        if "prioridade" in update_data:
            update_data["prioridade"] = update_data["prioridade"].value

        # Converter prazo para ISO string se presente
        if "prazo" in update_data and update_data["prazo"]:
            update_data["prazo"] = update_data["prazo"].isoformat()

        # Atualizar no banco
        updated_project = await repository.update(project_id, update_data)

        logger.info(f"Projeto atualizado: {updated_project.nome} ({project_id})")

        return ProjectResponse(
            success=True,
            project=updated_project,
            message="Projeto atualizado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", response_model=ProjectResponse)
async def delete_project(project_id: str):
    """
    Deleta um projeto

    Args:
        project_id: ID do projeto

    Returns:
        Confirmação de deleção
    """
    try:
        # Verificar se projeto existe
        project = await repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

        # Deletar do banco
        await repository.delete(project_id)

        logger.warning(f"Projeto deletado: {project.nome} ({project_id})")

        return ProjectResponse(
            success=True,
            project=None,
            message=f"Projeto {project.nome} deletado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))
