"""
Repository para Notificações
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from loguru import logger

from app.config import settings
from app.models.notification import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationType,
    NotificationPriority
)


class NotificationRepository:
    """Repository para gerenciar notificações"""

    def __init__(self):
        self.supabase = settings.supabase

    async def create_notification(self, data: NotificationCreate) -> Optional[Notification]:
        """Criar nova notificação"""
        try:
            # Get lead name if lead_id is provided
            lead_nome = None
            if data.lead_id:
                lead_result = self.supabase.table("leads").select("nome").eq("id", data.lead_id).execute()
                lead_nome = lead_result.data[0]["nome"] if lead_result.data else None

            notification_data = {
                "id": str(uuid4()),
                "user_id": data.user_id,
                "tipo": data.tipo.value if isinstance(data.tipo, NotificationType) else data.tipo,
                "prioridade": data.prioridade.value if isinstance(data.prioridade, NotificationPriority) else data.prioridade,
                "titulo": data.titulo,
                "mensagem": data.mensagem,
                "link": data.link,
                "lida": False,
                "lead_id": data.lead_id,
                "lead_nome": lead_nome,
                "metadata": data.metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "read_at": None
            }

            result = self.supabase.table("notifications").insert(notification_data).execute()

            if result.data:
                return Notification(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {e}")
            return None

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Buscar notificação por ID"""
        try:
            result = self.supabase.table("notifications").select("*").eq("id", notification_id).execute()

            if result.data:
                return Notification(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar notificação: {e}")
            return None

    async def list_notifications(
        self,
        user_id: Optional[str] = None,
        unread_only: bool = False,
        tipo_filter: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Listar notificações com filtros"""
        try:
            query = self.supabase.table("notifications").select("*")

            # Filter by user (including global notifications)
            if user_id:
                query = query.or_(f"user_id.eq.{user_id},user_id.is.null")
            else:
                query = query.is_("user_id", "null")

            # Filter unread only
            if unread_only:
                query = query.eq("lida", False)

            # Filter by type
            if tipo_filter:
                tipo_value = tipo_filter.value if isinstance(tipo_filter, NotificationType) else tipo_filter
                query = query.eq("tipo", tipo_value)

            result = query.order("created_at", desc=True).limit(limit).offset(offset).execute()

            if result.data:
                return [Notification(**item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Erro ao listar notificações: {e}")
            return []

    async def count_unread(self, user_id: Optional[str] = None) -> int:
        """Contar notificações não lidas"""
        try:
            query = self.supabase.table("notifications").select("id", count="exact").eq("lida", False)

            if user_id:
                query = query.or_(f"user_id.eq.{user_id},user_id.is.null")
            else:
                query = query.is_("user_id", "null")

            result = query.execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Erro ao contar notificações não lidas: {e}")
            return 0

    async def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Marcar notificação como lida"""
        try:
            update_data = {
                "lida": True,
                "read_at": datetime.utcnow().isoformat()
            }

            result = (
                self.supabase.table("notifications")
                .update(update_data)
                .eq("id", notification_id)
                .execute()
            )

            if result.data:
                return Notification(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao marcar notificação como lida: {e}")
            return None

    async def mark_all_as_read(self, user_id: Optional[str] = None) -> bool:
        """Marcar todas notificações como lidas"""
        try:
            update_data = {
                "lida": True,
                "read_at": datetime.utcnow().isoformat()
            }

            query = self.supabase.table("notifications").update(update_data).eq("lida", False)

            if user_id:
                query = query.or_(f"user_id.eq.{user_id},user_id.is.null")
            else:
                query = query.is_("user_id", "null")

            query.execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao marcar todas notificações como lidas: {e}")
            return False

    async def delete_notification(self, notification_id: str) -> bool:
        """Deletar notificação"""
        try:
            self.supabase.table("notifications").delete().eq("id", notification_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar notificação: {e}")
            return False

    async def delete_old_notifications(self, days: int = 30) -> int:
        """Deletar notificações antigas (lidas)"""
        try:
            cutoff_date = datetime.utcnow()
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=days)

            result = (
                self.supabase.table("notifications")
                .delete()
                .eq("lida", True)
                .lt("created_at", cutoff_date.isoformat())
                .execute()
            )

            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Erro ao deletar notificações antigas: {e}")
            return 0


# Instância global do repository
_notification_repository: Optional[NotificationRepository] = None


def get_notification_repository() -> NotificationRepository:
    """Retorna instância do NotificationRepository"""
    global _notification_repository
    if _notification_repository is None:
        _notification_repository = NotificationRepository()
    return _notification_repository
