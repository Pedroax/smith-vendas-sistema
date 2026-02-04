"""
Repository para Interações
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from loguru import logger

from app.config import settings
from app.models.interaction import Interaction, InteractionCreate, InteractionUpdate, InteractionType


class InteractionRepository:
    """Repository para gerenciar interações"""

    def __init__(self):
        self.supabase = settings.supabase

    async def create_interaction(self, data: InteractionCreate) -> Optional[Interaction]:
        """Criar nova interação"""
        try:
            interaction_data = {
                "id": str(uuid4()),
                "lead_id": data.lead_id,
                "tipo": data.tipo.value if isinstance(data.tipo, InteractionType) else data.tipo,
                "assunto": data.assunto,
                "conteudo": data.conteudo,
                "user_nome": data.user_nome,
                "metadata": data.metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("interactions").insert(interaction_data).execute()

            if result.data:
                return Interaction(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao criar interação: {e}")
            return None

    async def get_interaction(self, interaction_id: str) -> Optional[Interaction]:
        """Buscar interação por ID"""
        try:
            result = self.supabase.table("interactions").select("*").eq("id", interaction_id).execute()

            if result.data:
                return Interaction(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar interação: {e}")
            return None

    async def list_interactions_by_lead(
        self,
        lead_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Interaction]:
        """Listar interações de um lead"""
        try:
            result = (
                self.supabase.table("interactions")
                .select("*")
                .eq("lead_id", lead_id)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            if result.data:
                return [Interaction(**item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Erro ao listar interações do lead: {e}")
            return []

    async def list_recent_interactions(
        self,
        limit: int = 50,
        tipo: Optional[InteractionType] = None
    ) -> List[Interaction]:
        """Listar interações recentes"""
        try:
            query = self.supabase.table("interactions").select("*")

            if tipo:
                tipo_value = tipo.value if isinstance(tipo, InteractionType) else tipo
                query = query.eq("tipo", tipo_value)

            result = query.order("created_at", desc=True).limit(limit).execute()

            if result.data:
                return [Interaction(**item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Erro ao listar interações recentes: {e}")
            return []

    async def update_interaction(
        self,
        interaction_id: str,
        data: InteractionUpdate
    ) -> Optional[Interaction]:
        """Atualizar interação"""
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "tipo" in update_data:
                update_data["tipo"] = update_data["tipo"].value if hasattr(update_data["tipo"], "value") else update_data["tipo"]

            result = (
                self.supabase.table("interactions")
                .update(update_data)
                .eq("id", interaction_id)
                .execute()
            )

            if result.data:
                return Interaction(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar interação: {e}")
            return None

    async def delete_interaction(self, interaction_id: str) -> bool:
        """Deletar interação"""
        try:
            self.supabase.table("interactions").delete().eq("id", interaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar interação: {e}")
            return False

    async def get_last_interaction_by_lead(self, lead_id: str) -> Optional[Interaction]:
        """Buscar última interação de um lead"""
        try:
            result = (
                self.supabase.table("interactions")
                .select("*")
                .eq("lead_id", lead_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return Interaction(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar última interação: {e}")
            return None


# Instância global do repository
_interaction_repository: Optional[InteractionRepository] = None


def get_interaction_repository() -> InteractionRepository:
    """Retorna instância do InteractionRepository"""
    global _interaction_repository
    if _interaction_repository is None:
        _interaction_repository = InteractionRepository()
    return _interaction_repository
