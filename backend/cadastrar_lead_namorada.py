"""
Script para cadastrar lead da namorada e disparar mensagem
"""
import asyncio
from app.database import init_supabase, get_supabase
from app.services.whatsapp_followup_service import WhatsAppFollowUpService
from app.repository.leads_repository import LeadsRepository
from loguru import logger

async def main():
    # Inicializar
    init_supabase()
    supabase = get_supabase()

    telefone = "559199660063"

    logger.info(f"🔍 Verificando se lead já existe...")

    # Buscar por telefone
    result = supabase.table("leads").select("*").eq("telefone", telefone).execute()

    if result.data:
        logger.info(f"✅ Lead já existe, usando existente")
        lead_repo = LeadsRepository()
        lead = await lead_repo.get_by_telefone(telefone)
    else:
        logger.info(f"✅ Lead não existe, criando...")

        # Dados do lead
        lead_data = {
            "nome": "Lead Teste",
            "telefone": telefone,
            "email": "teste@teste.com",
            "empresa": "Empresa Teste",
            "cargo": "Gerente",
            "status": "qualificado",
            "origem": "facebook_ads",
            "lead_score": 80
        }

        # Inserir no banco
        result = supabase.table("leads").insert(lead_data).execute()

        if result.data:
            logger.success(f"✅ Lead criado no banco")
            lead_repo = LeadsRepository()
            lead = await lead_repo.get_by_telefone(telefone)
        else:
            logger.error("❌ Erro ao criar lead")
            return

    logger.info(f"📱 Lead: {lead.nome} - {lead.telefone}")

    # Enviar mensagem de follow-up com horários REAIS do Google Calendar
    logger.info("🚀 Enviando mensagem de agendamento com horários reais...")

    followup_service = WhatsAppFollowUpService()
    success = await followup_service.send_scheduling_message(lead)

    if success:
        logger.success("✅ Mensagem enviada! Ela pode conversar agora pelo WhatsApp.")
        logger.info("💬 O Smith vai responder qualquer mensagem!")
    else:
        logger.error("❌ Erro ao enviar mensagem")

if __name__ == "__main__":
    asyncio.run(main())
