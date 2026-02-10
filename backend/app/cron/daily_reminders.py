"""
Cron Job para Lembretes Diários de Marcos
Executa diariamente para enviar lembretes de prazos
"""
import asyncio
from datetime import date
from loguru import logger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repository.milestone_repository import MilestoneRepository
from app.services.milestone_reminder_service import (
    MilestoneReminderService,
    get_milestone_reminder_service
)
from app.services.uazapi_service import get_uazapi_service


async def run_daily_reminders():
    """
    Executa verificação e envio de lembretes diários

    Esta função deve ser chamada diariamente (ex: 8h da manhã)
    """
    logger.info(f"🔔 Iniciando verificação de lembretes - {date.today()}")

    db = SessionLocal()
    try:
        # Criar repository e service
        milestone_repo = MilestoneRepository(db)
        uazapi_service = get_uazapi_service()
        reminder_service = get_milestone_reminder_service(
            milestone_repo,
            uazapi_service
        )

        # Executar envio de lembretes
        result = await reminder_service.send_daily_reminders()

        logger.info(
            f"✅ Execução concluída:\n"
            f"   📬 Enviados: {result['reminders_sent']}\n"
            f"   ❌ Falhas: {result['reminders_failed']}\n"
            f"   ⚠️  Atrasados: {result['overdue_marked']}"
        )

        return result

    except Exception as e:
        logger.error(f"❌ Erro ao executar lembretes diários: {e}")
        raise

    finally:
        db.close()


def main():
    """Entry point para execução do cron"""
    try:
        result = asyncio.run(run_daily_reminders())
        exit_code = 0 if result['reminders_failed'] == 0 else 1
        exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Falha crítica no cron: {e}")
        exit(1)


if __name__ == "__main__":
    main()
