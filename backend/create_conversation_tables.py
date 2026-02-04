"""
Script para criar tabelas de conversação no Supabase
"""
import asyncio
from app.database import engine
from app.models.conversation import Conversation, Message
from loguru import logger


async def create_tables():
    """Cria as tabelas de conversação"""
    try:
        logger.info("🔧 Criando tabelas de conversação...")

        # Importar Base do modelo
        from app.database import Base

        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)

        logger.success("✅ Tabelas criadas com sucesso!")
        logger.info("""
Tabelas criadas:
- conversations: Gerencia estado da conversa com cada lead
- messages: Histórico de mensagens trocadas

Estados da conversa:
- inicial: Primeira interação
- agendamento_enviado: Enviou horários, aguardando resposta
- tirando_duvidas: Lead fazendo perguntas
- aguardando_confirmacao: Lead escolheu horário
- agendado: Reunião confirmada
- finalizado: Conversa encerrada
""")

    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_tables())
