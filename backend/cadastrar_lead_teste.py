"""
Script para cadastrar lead de teste
"""
import asyncio
from app.database import init_supabase, get_supabase
from loguru import logger

async def main():
    # Inicializar Supabase
    init_supabase()
    supabase = get_supabase()

    logger.info(f"🔍 Verificando se lead já existe...")

    # Buscar por telefone
    result = supabase.table("leads").select("*").eq("telefone", "556182563956").execute()

    if result.data:
        existing = result.data[0]
        logger.warning(f"⚠️ Lead já existe: {existing['nome']} (ID: {existing['id']})")
        logger.info(f"Telefone: {existing['telefone']}")
        logger.info(f"Email: {existing.get('email')}")
        logger.info(f"Status: {existing['status']}")
    else:
        logger.info(f"✅ Lead não existe, criando...")

        # Dados do lead
        lead_data = {
            "nome": "Pedro Machado",
            "telefone": "556182563956",
            "email": "pedro@teste.com",
            "empresa": "Teste LTDA",
            "cargo": "CEO",
            "status": "qualificado",
            "origem": "whatsapp",
            "lead_score": 85
        }

        # Inserir no banco
        result = supabase.table("leads").insert(lead_data).execute()

        if result.data:
            created = result.data[0]
            logger.success(f"✅ Lead criado: {created['nome']} (ID: {created['id']})")
            logger.success(f"Telefone: {created['telefone']}")
        else:
            logger.error("❌ Erro ao criar lead")

if __name__ == "__main__":
    asyncio.run(main())
