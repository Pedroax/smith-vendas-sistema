"""
Script para iniciar conversa de teste - simula lead qualificado do Facebook
"""
import asyncio
from app.database import init_supabase
from app.services.whatsapp_followup_service import WhatsAppFollowUpService
from app.repository.leads_repository import LeadsRepository
from loguru import logger

async def main():
    # Inicializar
    init_supabase()

    # Buscar lead
    lead_repo = LeadsRepository()
    lead = await lead_repo.get_by_telefone("556182563956")

    if not lead:
        logger.error("❌ Lead não encontrado!")
        return

    logger.info(f"✅ Lead encontrado: {lead.nome}")
    logger.info(f"📱 Telefone: {lead.telefone}")

    # Enviar mensagem de follow-up com horários REAIS do Google Calendar
    logger.info("🚀 Enviando mensagem de agendamento com horários reais...")

    followup_service = WhatsAppFollowUpService()
    success = await followup_service.send_scheduling_message(lead)

    if success:
        logger.success("✅ Mensagem enviada! Agora converse pelo WhatsApp normalmente.")
        logger.info("💬 O Smith vai responder qualquer mensagem que você enviar!")
    else:
        logger.error("❌ Erro ao enviar mensagem")

if __name__ == "__main__":
    asyncio.run(main())
