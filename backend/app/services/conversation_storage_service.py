"""
Serviço para armazenar conversas no Supabase
Mantém histórico completo e persistente de todas as interações
"""
from typing import List, Dict, Optional, Any
from loguru import logger
from app.database import get_supabase


class ConversationStorageService:
    """Gerencia armazenamento de conversas no Supabase"""

    def __init__(self):
        self.supabase = get_supabase()

    async def get_or_create_conversation(self, phone: str, lead_id: int) -> int:
        """
        Busca ou cria uma conversa para o telefone

        Args:
            phone: Número de telefone
            lead_id: ID do lead

        Returns:
            ID da conversa
        """
        try:
            # Buscar conversa existente
            result = self.supabase.table("conversations")\
                .select("id")\
                .eq("phone_number", phone)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if result.data:
                conversation_id = result.data[0]["id"]
                logger.debug(f"Conversa existente encontrada: {conversation_id}")
                return conversation_id

            # Criar nova conversa
            new_conversation = {
                "lead_id": lead_id,
                "phone_number": phone,
                "state": "inicial",
                "last_message_at": "NOW()"
            }

            result = self.supabase.table("conversations")\
                .insert(new_conversation)\
                .execute()

            if result.data:
                conversation_id = result.data[0]["id"]
                logger.info(f"✅ Nova conversa criada: {conversation_id}")
                return conversation_id
            else:
                logger.error("Erro ao criar conversa")
                return None

        except Exception as e:
            logger.error(f"Erro ao buscar/criar conversa: {e}")
            return None

    async def save_message(
        self,
        conversation_id: int,
        direction: str,
        content: str,
        evolution_message_id: Optional[str] = None
    ) -> bool:
        """
        Salva mensagem no histórico

        Args:
            conversation_id: ID da conversa
            direction: 'inbound' (lead) ou 'outbound' (smith)
            content: Conteúdo da mensagem
            evolution_message_id: ID da mensagem na Evolution API (opcional)

        Returns:
            True se salvou com sucesso
        """
        try:
            message_data = {
                "conversation_id": conversation_id,
                "direction": direction,
                "message_type": "text",
                "content": content,
                "evolution_message_id": evolution_message_id
            }

            result = self.supabase.table("messages")\
                .insert(message_data)\
                .execute()

            if result.data:
                logger.debug(f"Mensagem salva: {direction} - {content[:50]}...")

                # Atualizar last_message_at na conversa
                self.supabase.table("conversations")\
                    .update({"last_message_at": "NOW()"})\
                    .eq("id", conversation_id)\
                    .execute()

                return True
            else:
                logger.error("Erro ao salvar mensagem")
                return False

        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            return False

    async def get_conversation_history(
        self,
        conversation_id: int,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Recupera histórico de mensagens

        Args:
            conversation_id: ID da conversa
            limit: Número máximo de mensagens (padrão 10)

        Returns:
            Lista de mensagens no formato [{"role": "user", "content": "..."}]
        """
        try:
            result = self.supabase.table("messages")\
                .select("direction, content")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()

            if not result.data:
                return []

            # Converter para formato esperado pela IA
            history = []
            for msg in result.data:
                role = "user" if msg["direction"] == "inbound" else "assistant"
                history.append({
                    "role": role,
                    "content": msg["content"]
                })

            logger.debug(f"Histórico recuperado: {len(history)} mensagens")
            return history

        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {e}")
            return []

    async def update_conversation_state(
        self,
        conversation_id: int,
        state: str
    ) -> bool:
        """
        Atualiza estado da conversa

        Args:
            conversation_id: ID da conversa
            state: Novo estado

        Returns:
            True se atualizou com sucesso
        """
        try:
            result = self.supabase.table("conversations")\
                .update({"state": state})\
                .eq("id", conversation_id)\
                .execute()

            if result.data:
                logger.debug(f"Estado atualizado para: {state}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Erro ao atualizar estado: {e}")
            return False

    async def get_conversation_state(
        self,
        conversation_id: int
    ) -> Optional[Dict[str, any]]:
        """
        Busca estado atual da conversa

        Args:
            conversation_id: ID da conversa

        Returns:
            Dicionário com estado da conversa ou None
        """
        try:
            result = self.supabase.table("conversations")\
                .select("state, qualification_message_count, website_researched")\
                .eq("id", conversation_id)\
                .execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar estado da conversa: {e}")
            return None

    async def increment_qualification_count(
        self,
        conversation_id: int
    ) -> bool:
        """
        Incrementa contador de mensagens na qualificação

        Args:
            conversation_id: ID da conversa

        Returns:
            True se incrementou com sucesso
        """
        try:
            # Buscar valor atual
            conv = await self.get_conversation_state(conversation_id)
            if not conv:
                return False

            current_count = conv.get("qualification_message_count", 0)
            new_count = current_count + 1

            # Atualizar
            result = self.supabase.table("conversations")\
                .update({"qualification_message_count": new_count})\
                .eq("id", conversation_id)\
                .execute()

            if result.data:
                logger.debug(f"Contador incrementado para: {new_count}")
                return True
            return False

        except Exception as e:
            logger.error(f"Erro ao incrementar contador: {e}")
            return False

    async def set_website_researched(
        self,
        conversation_id: int,
        website_url: str
    ) -> bool:
        """
        Armazena URL do site pesquisado

        Args:
            conversation_id: ID da conversa
            website_url: URL do site

        Returns:
            True se salvou com sucesso
        """
        try:
            result = self.supabase.table("conversations")\
                .update({"website_researched": website_url})\
                .eq("id", conversation_id)\
                .execute()

            if result.data:
                logger.debug(f"Website armazenado: {website_url}")
                return True
            return False

        except Exception as e:
            logger.error(f"Erro ao salvar website: {e}")
            return False


# Instância global
conversation_storage = ConversationStorageService()
