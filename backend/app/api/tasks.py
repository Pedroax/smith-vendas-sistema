"""
API de Tarefas
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.task import Task, TaskCreate, TaskUpdate, TaskStatus
from app.repository.task_repository import get_task_repository

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("/counts")
async def get_task_counts():
    """Contar tarefas por status"""
    repo = get_task_repository()
    counts = await repo.get_counts()
    return counts


@router.post("", response_model=Task)
async def create_task(data: TaskCreate):
    """Criar nova tarefa"""
    repo = get_task_repository()
    task = await repo.create_task(data)
    if not task:
        raise HTTPException(status_code=500, detail="Erro ao criar tarefa")
    return task


@router.get("", response_model=List[Task])
async def list_tasks(
    status: Optional[TaskStatus] = Query(default=None),
    prioridade: Optional[str] = Query(default=None),
    lead_id: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    include_feito: bool = Query(default=True),
    limit: int = Query(default=100, le=200)
):
    """Listar tarefas com filtros"""
    repo = get_task_repository()
    tasks = await repo.list_tasks(
        status=status,
        prioridade=prioridade,
        lead_id=lead_id,
        project_id=project_id,
        include_feito=include_feito,
        limit=limit
    )
    return tasks


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Buscar tarefa por ID"""
    repo = get_task_repository()
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, data: TaskUpdate):
    """Atualizar tarefa"""
    repo = get_task_repository()
    task = await repo.update_task(task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Deletar tarefa"""
    repo = get_task_repository()
    success = await repo.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"success": True, "message": "Tarefa deletada"}
