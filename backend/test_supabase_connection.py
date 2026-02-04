"""
Script de teste para verificar conexão com Supabase
Execute: python test_supabase_connection.py
"""
import sys
import asyncio
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_supabase
from app.repository.leads_repository import LeadsRepository
from loguru import logger


async def test_connection():
    """Testa conexão com Supabase e lista leads"""

    logger.info("🧪 Testando conexão com Supabase...")

    try:
        # 1. Inicializar Supabase
        supabase = init_supabase()
        logger.success("✅ Supabase conectado!")

        # 2. Criar repository
        repository = LeadsRepository()
        logger.success("✅ Repository criado!")

        # 3. Listar todos os leads
        logger.info("📊 Buscando leads do banco...")
        leads = await repository.list_all(limit=100)

        if not leads:
            logger.warning("⚠️  Nenhum lead encontrado no banco")
            logger.info("💡 Execute os scripts SQL no Supabase para popular o banco:")
            logger.info("   1. database/01_create_tables.sql")
            logger.info("   2. database/02_seed_data.sql")
            return

        # 4. Exibir leads
        logger.success(f"✅ {len(leads)} leads encontrados!")
        logger.info("\n" + "=" * 80)
        logger.info("LEADS NO BANCO:")
        logger.info("=" * 80)

        for i, lead in enumerate(leads, 1):
            logger.info(f"\n{i}. {lead.nome} ({lead.empresa or 'Sem empresa'})")
            logger.info(f"   📞 {lead.telefone}")
            # Status e temperatura já são strings por causa de use_enum_values=True
            logger.info(f"   📊 Status: {lead.status} | Temperatura: {lead.temperatura}")
            logger.info(f"   ⭐ Score: {lead.lead_score}")
            logger.info(f"   💰 Valor estimado: R$ {lead.valor_estimado:,.2f}")
            logger.info(f"   🏷️  Tags: {', '.join(lead.tags) if lead.tags else 'Nenhuma'}")

        logger.info("\n" + "=" * 80)

        # 5. Testar estatísticas
        logger.info("\n📈 Buscando estatísticas...")
        stats = await repository.get_stats()

        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS:")
        logger.info("=" * 80)
        logger.info(f"Total de leads: {stats.get('total_leads', 0)}")
        logger.info(f"Score médio: {stats.get('score_medio', 0)}")
        logger.info(f"Valor total pipeline: R$ {stats.get('valor_total_pipeline', 0):,.2f}")
        logger.info(f"Taxa de qualificação: {stats.get('taxa_qualificacao', 0)}%")
        logger.info(f"Taxa de conversão: {stats.get('taxa_conversao', 0)}%")

        if stats.get('por_status'):
            logger.info("\nPor status:")
            for status, count in stats['por_status'].items():
                logger.info(f"  - {status}: {count}")

        logger.info("\n" + "=" * 80)

        logger.success("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        logger.info("🚀 Você pode iniciar o backend agora: uvicorn app.main:app --reload")

    except Exception as e:
        logger.error(f"\n❌ ERRO NO TESTE: {e}")
        logger.error("\n🔧 Verifique:")
        logger.error("   1. As credenciais no arquivo backend/.env estão corretas")
        logger.error("   2. Os scripts SQL foram executados no Supabase")
        logger.error("   3. O Supabase está acessível")
        raise


if __name__ == "__main__":
    # Executar teste
    asyncio.run(test_connection())
