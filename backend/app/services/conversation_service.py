"""
Serviço de gerenciamento de conversas
Orquestra o fluxo conversacional do Smith
"""
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime
from typing import Optional

from app.models.conversation import Conversation, ConversationState
from app.models.lead import Lead
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from app.services.smith_ai_service import SmithAIService
from app.services.evolution_service import evolution_service


class ConversationService:
    """
    Gerencia o fluxo conversacional com o lead
    """

    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.ai_service = SmithAIService()

    async def process_incoming_message(
        self,
        conversation: Conversation,
        message_content: str,
        lead: Lead
    ):
        """
        Processa mensagem recebida do lead e decide o que fazer

        Fluxo:
        1. Analisa estado atual da conversa
        2. Determina intenção da mensagem
        3. Roteia para o handler apropriado
        """
        try:
            logger.info(f"🤖 Processando mensagem no estado: {conversation.state}")

            # Rotear baseado no estado atual
            if conversation.state == ConversationState.AGENDAMENTO_ENVIADO:
                # Lead pode estar escolhendo horário OU tirando dúvidas
                await self._handle_agendamento_response(conversation, message_content, lead)

            elif conversation.state == ConversationState.TIRANDO_DUVIDAS:
                # Lead está conversando com o Smith
                await self._handle_conversation(conversation, message_content, lead)

            elif conversation.state == ConversationState.AGUARDANDO_CONFIRMACAO:
                # Lead confirmando horário escolhido
                await self._handle_confirmation(conversation, message_content, lead)

            elif conversation.state == ConversationState.INICIAL:
                # Primeira interação do lead após qualificação
                # Normalmente não chega aqui pois enviamos mensagem primeiro
                await self._handle_first_interaction(conversation, message_content, lead)

            else:
                logger.warning(f"⚠️ Estado não tratado: {conversation.state}")

        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {str(e)}")
            # Enviar mensagem de erro genérica
            await self._send_error_message(lead.telefone)

    async def _handle_agendamento_response(
        self,
        conversation: Conversation,
        message: str,
        lead: Lead
    ):
        """
        Lead respondeu à mensagem de agendamento
        Pode ser: escolhendo horário (1, 2, 3) OU fazendo pergunta
        """
        logger.info("📅 Analisando resposta de agendamento")

        # Detectar se é escolha de horário
        slot_choice = self._extract_slot_choice(message)

        if slot_choice:
            # Lead escolheu um horário
            logger.info(f"✅ Lead escolheu horário: {slot_choice}")
            await self._process_slot_selection(conversation, slot_choice, lead)

        else:
            # Lead está fazendo uma pergunta
            logger.info("💬 Lead está tirando dúvida")
            # Mudar estado para TIRANDO_DUVIDAS
            self.conversation_repo.update_state(
                conversation.id,
                ConversationState.TIRANDO_DUVIDAS
            )
            # Processar como conversa normal
            await self._handle_conversation(conversation, message, lead)

    async def _handle_conversation(
        self,
        conversation: Conversation,
        message: str,
        lead: Lead
    ):
        """
        Lead está conversando / tirando dúvidas
        """
        logger.info("💬 Processando conversa com IA")

        # Buscar histórico recente
        history = self.message_repo.get_history(conversation.id, limit=10)

        # Processar com IA
        response = await self.ai_service.process_message(
            message=message,
            lead=lead,
            conversation_state=conversation.state,
            message_history=history
        )

        # Enviar resposta
        await evolution_service.send_text_message(
            phone=lead.telefone,
            message=response
        )

        # Salvar resposta no histórico
        from app.models.conversation import MessageDirection, MessageType
        self.message_repo.create(
            conversation_id=conversation.id,
            direction=MessageDirection.OUTBOUND,
            content=response,
            message_type=MessageType.TEXT
        )

        # Verificar se IA detectou que lead quer agendar
        if self.ai_service.detected_scheduling_intent(message):
            logger.info("📅 IA detectou intenção de agendamento")
            # Voltar para estado de agendamento
            self.conversation_repo.update_state(
                conversation.id,
                ConversationState.AGENDAMENTO_ENVIADO
            )

    async def _process_slot_selection(
        self,
        conversation: Conversation,
        slot_index: int,
        lead: Lead
    ):
        """
        Lead escolheu um horário específico (1, 2 ou 3)
        """
        logger.info(f"✅ Processando escolha de horário: {slot_index}")

        # Marcar slot selecionado
        self.conversation_repo.set_selected_slot(conversation.id, slot_index)

        # Enviar mensagem de confirmação
        confirmation_message = f"""Perfeito! Vou agendar a reunião na opção {slot_index} para você.

Confirmando esse horário na sua agenda! Um momento... ⏰"""

        await evolution_service.send_text_message(
            phone=lead.telefone,
            message=confirmation_message
        )

        # Salvar no histórico
        from app.models.conversation import MessageDirection, MessageType
        self.message_repo.create(
            conversation_id=conversation.id,
            direction=MessageDirection.OUTBOUND,
            content=confirmation_message,
            message_type=MessageType.TEXT
        )

        # Criar evento no Google Calendar
        # TODO: Implementar criação real do evento baseado no slot escolhido
        logger.info("📅 Criando evento no Google Calendar...")

        # Confirmar agendamento
        success_message = """✅ Pronto! Sua reunião está agendada!

Você vai receber uma notificação antes do horário.

Nos vemos em breve! 🚀"""

        await evolution_service.send_text_message(
            phone=lead.telefone,
            message=success_message
        )

        # Atualizar estado para AGENDADO
        self.conversation_repo.update_state(
            conversation.id,
            ConversationState.AGENDADO
        )

    async def _handle_confirmation(
        self,
        conversation: Conversation,
        message: str,
        lead: Lead
    ):
        """
        Lead confirmando/cancelando agendamento
        """
        # TODO: Implementar lógica de confirmação
        pass

    async def _handle_first_interaction(
        self,
        conversation: Conversation,
        message: str,
        lead: Lead
    ):
        """
        Primeira interação do lead
        """
        # Normalmente não deve chegar aqui pois enviamos mensagem primeiro
        logger.info("👋 Primeira interação do lead")
        await self._handle_conversation(conversation, message, lead)

    async def _send_error_message(self, phone: str):
        """Envia mensagem de erro genérica"""
        error_msg = "Desculpe, tive um problema técnico. Pode repetir sua mensagem? 🤖"
        await evolution_service.send_text_message(phone, error_msg)

    def _extract_slot_choice(self, message: str) -> Optional[int]:
        """
        Extrai escolha de horário da mensagem (1, 2, 3, 4)
        """
        message_clean = message.strip().lower()

        # Detectar números
        if message_clean in ["1", "2", "3", "4"]:
            return int(message_clean)

        # Detectar palavras
        if "primeiro" in message_clean or "1º" in message_clean or "opção 1" in message_clean:
            return 1
        if "segundo" in message_clean or "2º" in message_clean or "opção 2" in message_clean:
            return 2
        if "terceiro" in message_clean or "3º" in message_clean or "opção 3" in message_clean:
            return 3
        if "quarto" in message_clean or "4º" in message_clean or "outro" in message_clean or "opção 4" in message_clean:
            return 4

        return None
