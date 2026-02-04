"""
Modelo de Conversação e Estado do Lead
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from enum import Enum
from app.database import Base


class ConversationState(str, Enum):
    """Estados possíveis da conversa com o lead"""
    INICIAL = "inicial"                           # Primeira interação
    AGUARDANDO_EMPRESA = "aguardando_empresa"     # Perguntou nome da empresa
    AGUARDANDO_SITE = "aguardando_site"           # Perguntou site da empresa
    PESQUISANDO_SITE = "pesquisando_site"         # Pesquisando informações do site
    QUALIFICANDO = "qualificando"                 # Qualificando o lead (3-4 trocas)
    AGENDAMENTO_ENVIADO = "agendamento_enviado"   # Enviou horários, aguardando resposta
    TIRANDO_DUVIDAS = "tirando_duvidas"           # Lead fazendo perguntas
    AGUARDANDO_CONFIRMACAO = "aguardando_confirmacao"  # Lead escolheu horário, aguardando confirmação
    AGENDADO = "agendado"                         # Reunião confirmada
    FINALIZADO = "finalizado"                     # Conversa encerrada


class MessageType(str, Enum):
    """Tipos de mensagem"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class MessageDirection(str, Enum):
    """Direção da mensagem"""
    INBOUND = "inbound"   # Lead enviou
    OUTBOUND = "outbound"  # Smith enviou


class Conversation(Base):
    """
    Gerencia o estado e histórico da conversa com o lead
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)  # FK para leads
    phone_number = Column(String(20), nullable=False, index=True)

    # Estado da conversa
    state = Column(SQLEnum(ConversationState), default=ConversationState.INICIAL, nullable=False)

    # Contexto
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    agendamento_message_sent = Column(DateTime(timezone=True), nullable=True)  # Quando enviou mensagem de agendamento
    selected_slot_index = Column(Integer, nullable=True)  # Qual horário o lead escolheu (1, 2, 3)

    # Coleta de informações
    qualification_message_count = Column(Integer, default=0, nullable=False)  # Contador de mensagens na qualificação
    website_researched = Column(String(500), nullable=True)  # URL do site pesquisado

    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Message(Base):
    """
    Histórico de mensagens trocadas
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, nullable=False, index=True)  # FK para conversations

    # Conteúdo
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=False)

    # Metadados Evolution API
    evolution_message_id = Column(String(100), nullable=True, unique=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
