"""
API de Interações/Conversas
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.interaction import (
    Interaction,
    InteractionCreate,
    InteractionUpdate,
    InteractionType
)
from app.repository.interaction_repository import get_interaction_repository

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.post("", response_model=Interaction)
async def create_interaction(data: InteractionCreate):
    """Criar nova interação com lead"""
    repo = get_interaction_repository()
    interaction = await repo.create_interaction(data)

    if not interaction:
        raise HTTPException(status_code=500, detail="Erro ao criar interação")

    return interaction


@router.get("/{interaction_id}", response_model=Interaction)
async def get_interaction(interaction_id: str):
    """Buscar interação por ID"""
    repo = get_interaction_repository()
    interaction = await repo.get_interaction(interaction_id)

    if not interaction:
        raise HTTPException(status_code=404, detail="Interação não encontrada")

    return interaction


@router.get("/lead/{lead_id}", response_model=List[Interaction])
async def list_interactions_by_lead(
    lead_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Listar interações de um lead específico"""
    repo = get_interaction_repository()
    interactions = await repo.list_interactions_by_lead(lead_id, limit, offset)
    return interactions


@router.get("", response_model=List[Interaction])
async def list_recent_interactions(
    limit: int = Query(default=50, le=100),
    tipo: Optional[InteractionType] = None
):
    """Listar interações recentes (todas ou por tipo)"""
    repo = get_interaction_repository()
    interactions = await repo.list_recent_interactions(limit, tipo)
    return interactions


@router.put("/{interaction_id}", response_model=Interaction)
async def update_interaction(interaction_id: str, data: InteractionUpdate):
    """Atualizar interação"""
    repo = get_interaction_repository()
    interaction = await repo.update_interaction(interaction_id, data)

    if not interaction:
        raise HTTPException(status_code=404, detail="Interação não encontrada")

    return interaction


@router.delete("/{interaction_id}")
async def delete_interaction(interaction_id: str):
    """Deletar interação"""
    repo = get_interaction_repository()
    success = await repo.delete_interaction(interaction_id)

    if not success:
        raise HTTPException(status_code=404, detail="Interação não encontrada")

    return {"success": True, "message": "Interação deletada com sucesso"}
