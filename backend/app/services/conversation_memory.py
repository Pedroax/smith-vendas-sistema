"""
Conversation Memory Service - Memória persistente de conversas com Supabase
Integra com LangChain para histórico de mensagens
"""
from typing import List, Optional
from datetime import datetime
from loguru import logger
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.database import get_supabase


class SupabaseChatMemory:
    """
    Memória de chat persistente usando Supabase

    Gerencia histórico de conversas armazenadas no banco de dados,
    com limite de mensagens para evitar contexto muito grande.
    """

    def __init__(self, lead_id: str, max_messages: int = 20):
        """
        Inicializa memória de chat

        Args:
            lead_id: ID do lead (string ou int)
            max_messages: Número máximo de mensagens a carregar (padrão: 20)
                         20 mensagens = ~10 trocas (perguntas + respostas)
        """
        self.lead_id = str(lead_id)  # Garantir que é string
        self.max_messages = max_messages
        self.supabase = get_supabase()

    async def get_messages(self) -> List[BaseMessage]:
        """
        Carrega últimas N mensagens do banco de dados

        Returns:
            Lista de mensagens LangChain (HumanMessage, AIMessage)
        """
        try:
            # Buscar últimas N mensagens ordenadas por timestamp
            response = (
                self.supabase.table("conversation_messages")
                .select("role, content, timestamp")
                .eq("lead_id", self.lead_id)
                .order("timestamp", desc=True)
                .limit(self.max_messages)
                .execute()
            )

            if not response.data:
                logger.info(f"📭 Nenhuma mensagem anterior para lead {self.lead_id}")
                return []

            # Reverter ordem (mais antiga primeiro)
            messages_data = list(reversed(response.data))

            # Converter para mensagens LangChain
            messages = []
            for msg_data in messages_data:
                role = msg_data["role"]
                content = msg_data["content"]

                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))

            logger.info(
                f"📚 Carregadas {len(messages)} mensagens do histórico "
                f"(lead {self.lead_id})"
            )

            return messages

        except Exception as e:
            logger.error(
                f"❌ Erro ao carregar mensagens do lead {self.lead_id}: {e}",
                exc_info=True
            )
            return []  # Retornar lista vazia em caso de erro

    async def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Adiciona mensagem ao histórico no banco

        Args:
            role: "user", "assistant" ou "system"
            content: Conteúdo da mensagem
            metadata: Metadados opcionais (tokens, modelo, etc)

        Returns:
            True se sucesso, False se erro
        """
        try:
            message_data = {
                "lead_id": self.lead_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }

            response = (
                self.supabase.table("conversation_messages")
                .insert(message_data)
                .execute()
            )

            logger.debug(f"✅ Mensagem salva: {role} ({len(content)} chars)")
            return True

        except Exception as e:
            logger.error(
                f"❌ Erro ao salvar mensagem (lead {self.lead_id}): {e}",
                exc_info=True
            )
            return False

    async def clear_history(self) -> bool:
        """
        Limpa todo histórico de conversas do lead

        Returns:
            True se sucesso, False se erro
        """
        try:
            response = (
                self.supabase.table("conversation_messages")
                .delete()
                .eq("lead_id", self.lead_id)
                .execute()
            )
            total = len(response.data) if response.data else 0
            logger.warning(f"🗑️ Histórico limpo para lead {self.lead_id} ({total} registros)")
            return True

        except Exception as e:
            logger.error(
                f"❌ Erro ao limpar histórico (lead {self.lead_id}): {e}",
                exc_info=True
            )
            return False

    async def get_message_count(self) -> int:
        """
        Retorna quantidade total de mensagens do lead

        Returns:
            Número de mensagens
        """
        try:
            response = (
                self.supabase.table("conversation_messages")
                .select("id", count="exact")
                .eq("lead_id", self.lead_id)
                .execute()
            )

            return response.count or 0

        except Exception as e:
            logger.error(
                f"❌ Erro ao contar mensagens (lead {self.lead_id}): {e}"
            )
            return 0


async def load_conversation_history(
    lead_id: str,
    max_messages: int = 20
) -> List[BaseMessage]:
    """
    Helper function para carregar histórico de conversa

    Args:
        lead_id: ID do lead
        max_messages: Número máximo de mensagens a carregar

    Returns:
        Lista de mensagens LangChain
    """
    memory = SupabaseChatMemory(lead_id=lead_id, max_messages=max_messages)
    return await memory.get_messages()


async def save_conversation_message(
    lead_id: str,
    role: str,
    content: str,
    metadata: Optional[dict] = None
) -> bool:
    """
    Helper function para salvar mensagem no histórico

    Args:
        lead_id: ID do lead
        role: "user", "assistant" ou "system"
        content: Conteúdo da mensagem
        metadata: Metadados opcionais

    Returns:
        True se sucesso
    """
    memory = SupabaseChatMemory(lead_id=lead_id)
    return await memory.add_message(role, content, metadata)
