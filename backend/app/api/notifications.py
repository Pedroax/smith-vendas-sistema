"""
API de Notificações
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.notification import (
    Notification,
    NotificationCreate,
    NotificationType
)
from app.repository.notification_repository import get_notification_repository

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("", response_model=Notification)
async def create_notification(data: NotificationCreate):
    """Criar nova notificação"""
    repo = get_notification_repository()
    notification = await repo.create_notification(data)

    if not notification:
        raise HTTPException(status_code=500, detail="Erro ao criar notificação")

    return notification


@router.get("/{notification_id}", response_model=Notification)
async def get_notification(notification_id: str):
    """Buscar notificação por ID"""
    repo = get_notification_repository()
    notification = await repo.get_notification(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    return notification


@router.get("", response_model=List[Notification])
async def list_notifications(
    user_id: Optional[str] = Query(default=None),
    unread_only: bool = Query(default=False),
    tipo: Optional[NotificationType] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Listar notificações

    - user_id: Filtrar por usuário (None = notificações globais)
    - unread_only: Apenas não lidas
    - tipo: Filtrar por tipo
    - limit/offset: Paginação
    """
    repo = get_notification_repository()
    notifications = await repo.list_notifications(
        user_id=user_id,
        unread_only=unread_only,
        tipo_filter=tipo,
        limit=limit,
        offset=offset
    )
    return notifications


@router.get("/count/unread")
async def count_unread_notifications(
    user_id: Optional[str] = Query(default=None)
):
    """Contar notificações não lidas"""
    repo = get_notification_repository()
    count = await repo.count_unread(user_id)
    return {"count": count}


@router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(notification_id: str):
    """Marcar notificação como lida"""
    repo = get_notification_repository()
    notification = await repo.mark_as_read(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    return notification


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    user_id: Optional[str] = Query(default=None)
):
    """Marcar todas notificações como lidas"""
    repo = get_notification_repository()
    success = await repo.mark_all_as_read(user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao marcar notificações como lidas")

    return {"success": True, "message": "Todas notificações marcadas como lidas"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Deletar notificação"""
    repo = get_notification_repository()
    success = await repo.delete_notification(notification_id)

    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    return {"success": True, "message": "Notificação deletada com sucesso"}


@router.delete("/cleanup/old")
async def cleanup_old_notifications(
    days: int = Query(default=30, description="Deletar notificações lidas com mais de N dias")
):
    """Deletar notificações antigas (lidas)"""
    repo = get_notification_repository()
    deleted_count = await repo.delete_old_notifications(days)

    return {
        "success": True,
        "message": f"{deleted_count} notificações antigas deletadas",
        "count": deleted_count
    }
