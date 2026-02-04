"""
Repository para gerenciar conversações
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime

from app.models.conversation import Conversation, Message, ConversationState, MessageDirection, MessageType


class ConversationRepository:
    """Repository para operações com conversações"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_phone(self, phone_number: str) -> Optional[Conversation]:
        """Busca conversa pelo telefone"""
        return self.db.query(Conversation).filter(
            Conversation.phone_number == phone_number
        ).first()

    def get_by_lead_id(self, lead_id: int) -> Optional[Conversation]:
        """Busca conversa pelo ID do lead"""
        return self.db.query(Conversation).filter(
            Conversation.lead_id == lead_id
        ).first()

    def create(self, lead_id: int, phone_number: str) -> Conversation:
        """Cria nova conversa"""
        conversation = Conversation(
            lead_id=lead_id,
            phone_number=phone_number,
            state=ConversationState.INICIAL
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_state(self, conversation_id: int, new_state: ConversationState) -> Conversation:
        """Atualiza estado da conversa"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation:
            conversation.state = new_state
            conversation.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    def mark_agendamento_sent(self, conversation_id: int):
        """Marca que mensagem de agendamento foi enviada"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation:
            conversation.agendamento_message_sent = datetime.now()
            conversation.state = ConversationState.AGENDAMENTO_ENVIADO
            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    def set_selected_slot(self, conversation_id: int, slot_index: int):
        """Define qual horário o lead escolheu"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation:
            conversation.selected_slot_index = slot_index
            conversation.state = ConversationState.AGUARDANDO_CONFIRMACAO
            self.db.commit()
            self.db.refresh(conversation)

        return conversation


class MessageRepository:
    """Repository para operações com mensagens"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: int,
        direction: MessageDirection,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        evolution_message_id: Optional[str] = None
    ) -> Message:
        """Cria nova mensagem no histórico"""
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            message_type=message_type,
            content=content,
            evolution_message_id=evolution_message_id
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_history(self, conversation_id: int, limit: int = 50) -> List[Message]:
        """Busca histórico de mensagens"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit).all()

    def message_exists(self, evolution_message_id: str) -> bool:
        """Verifica se mensagem já foi processada"""
        return self.db.query(Message).filter(
            Message.evolution_message_id == evolution_message_id
        ).first() is not None
