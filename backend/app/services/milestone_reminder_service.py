"""
Serviço de Lembretes de Marcos de Projetos
Envia lembretes automáticos via WhatsApp sobre prazos de projetos
"""
from datetime import date, datetime
from typing import List, Tuple
from uuid import UUID
from loguru import logger

from app.config import settings
from app.models.milestone import (
    Milestone, ScheduledReminder, ReminderType, MilestoneStatus
)
from app.repository.milestone_repository import MilestoneRepository
from app.services.uazapi_service import UazapiService


class MilestoneReminderService:
    """Serviço para envio de lembretes de marcos de projetos"""

    def __init__(
        self,
        milestone_repo: MilestoneRepository,
        uazapi_service: UazapiService
    ):
        self.milestone_repo = milestone_repo
        self.uazapi_service = uazapi_service
        self.admin_whatsapp = settings.admin_whatsapp

    async def send_daily_reminders(self) -> dict:
        """
        Verifica e envia lembretes pendentes do dia

        Chamado diariamente via cron job

        Returns:
            dict com estatísticas de envio
        """
        today = date.today()
        logger.info(f"🔔 Verificando lembretes para {today}")

        # 1. Marcar marcos atrasados
        overdue_count = await self.milestone_repo.mark_overdue_milestones()
        if overdue_count > 0:
            logger.warning(f"⚠️  {overdue_count} marcos marcados como ATRASADOS")

        # 2. Buscar lembretes pendentes do dia
        reminders = await self.milestone_repo.get_pending_reminders(today)

        if not reminders:
            logger.info("✅ Nenhum lembrete pendente para hoje")
            return {
                "date": str(today),
                "reminders_sent": 0,
                "reminders_failed": 0,
                "overdue_marked": overdue_count
            }

        logger.info(f"📬 Encontrados {len(reminders)} lembretes para enviar")

        # 3. Enviar cada lembrete
        sent_count = 0
        failed_count = 0

        for reminder, milestone in reminders:
            success = await self._send_reminder(reminder, milestone)
            if success:
                sent_count += 1
            else:
                failed_count += 1

        logger.info(
            f"✅ Lembretes enviados: {sent_count} | "
            f"❌ Falhas: {failed_count}"
        )

        return {
            "date": str(today),
            "reminders_sent": sent_count,
            "reminders_failed": failed_count,
            "overdue_marked": overdue_count
        }

    async def _send_reminder(
        self,
        reminder: ScheduledReminder,
        milestone: Milestone
    ) -> bool:
        """
        Envia um lembrete individual via WhatsApp

        Args:
            reminder: Lembrete a ser enviado
            milestone: Marco relacionado

        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            # Montar mensagem
            message = self._build_reminder_message(reminder, milestone)

            # Enviar via WhatsApp
            if reminder.metodo == "whatsapp":
                await self.uazapi_service.send_text_message(
                    phone_number=self.admin_whatsapp,
                    message=message
                )
            else:
                # Email não implementado ainda
                logger.warning(f"Método {reminder.metodo} não suportado ainda")
                await self.milestone_repo.mark_reminder_sent(
                    reminder.id,
                    success=False,
                    error_message="Método de envio não suportado"
                )
                return False

            # Marcar como enviado
            await self.milestone_repo.mark_reminder_sent(
                reminder.id,
                success=True
            )

            logger.info(
                f"✅ Lembrete enviado: {milestone.nome} "
                f"({reminder.tipo.value})"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar lembrete {reminder.id}: {e}")

            # Registrar erro no banco
            await self.milestone_repo.mark_reminder_sent(
                reminder.id,
                success=False,
                error_message=str(e)
            )

            return False

    def _build_reminder_message(
        self,
        reminder: ScheduledReminder,
        milestone: Milestone
    ) -> str:
        """
        Monta a mensagem do lembrete baseado no tipo

        Args:
            reminder: Lembrete a ser enviado
            milestone: Marco relacionado

        Returns:
            Mensagem formatada para envio
        """
        # Emojis por tipo de lembrete
        emoji_map = {
            ReminderType.DEZ_DIAS: "📅",
            ReminderType.SETE_DIAS: "⏰",
            ReminderType.TRES_DIAS: "⚠️",
            ReminderType.UM_DIA: "🚨",
            ReminderType.NO_DIA: "⏳",
            ReminderType.ATRASADO: "🔴"
        }

        # Texto do prazo
        prazo_map = {
            ReminderType.DEZ_DIAS: "10 dias",
            ReminderType.SETE_DIAS: "7 dias",
            ReminderType.TRES_DIAS: "3 dias",
            ReminderType.UM_DIA: "1 dia",
            ReminderType.NO_DIA: "HOJE",
            ReminderType.ATRASADO: "ATRASADO"
        }

        emoji = emoji_map.get(reminder.tipo, "📌")
        prazo_texto = prazo_map.get(reminder.tipo, "em breve")

        # Buscar nome do projeto (simplificado - pode buscar do banco)
        project_name = f"Projeto #{milestone.project_id}"

        # Formatar data
        data_limite_fmt = milestone.data_limite.strftime("%d/%m/%Y")

        # Construir mensagem
        if reminder.tipo == ReminderType.NO_DIA:
            message = (
                f"{emoji} *LEMBRETE: PRAZO HOJE!*\n\n"
                f"📋 *Etapa:* {milestone.nome}\n"
                f"🎯 *Projeto:* {project_name}\n"
                f"📅 *Vencimento:* {data_limite_fmt}\n\n"
                f"⚡ A entrega desta etapa é *hoje*!\n\n"
            )
        elif reminder.tipo == ReminderType.ATRASADO:
            dias_atraso = (date.today() - milestone.data_limite).days
            message = (
                f"{emoji} *ALERTA: ETAPA ATRASADA!*\n\n"
                f"📋 *Etapa:* {milestone.nome}\n"
                f"🎯 *Projeto:* {project_name}\n"
                f"📅 *Venceu em:* {data_limite_fmt}\n"
                f"⏱️ *Atraso:* {dias_atraso} dias\n\n"
                f"⚠️ Esta etapa está atrasada!\n\n"
            )
        else:
            message = (
                f"{emoji} *LEMBRETE DE PRAZO*\n\n"
                f"📋 *Etapa:* {milestone.nome}\n"
                f"🎯 *Projeto:* {project_name}\n"
                f"📅 *Vencimento:* {data_limite_fmt}\n"
                f"⏰ *Faltam:* {prazo_texto}\n\n"
            )

        # Adicionar descrição se houver
        if milestone.descricao:
            message += f"📝 *Detalhes:* {milestone.descricao}\n\n"

        # Footer
        message += "---\n_Smith 2.0 - Gerenciamento de Projetos_"

        return message

    async def send_project_created_summary(
        self,
        project_id: int,
        project_name: str,
        milestones: List[Milestone]
    ) -> bool:
        """
        Envia resumo de marcos quando projeto é criado

        Args:
            project_id: ID do projeto
            project_name: Nome do projeto
            milestones: Lista de marcos criados

        Returns:
            True se enviado com sucesso
        """
        try:
            message = self._build_project_summary(
                project_id,
                project_name,
                milestones
            )

            await self.uazapi_service.send_text_message(
                phone_number=self.admin_whatsapp,
                message=message
            )

            logger.info(f"✅ Resumo de marcos enviado: Projeto #{project_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar resumo de projeto: {e}")
            return False

    def _build_project_summary(
        self,
        project_id: int,
        project_name: str,
        milestones: List[Milestone]
    ) -> str:
        """Monta mensagem de resumo de projeto criado"""
        message = (
            f"✅ *NOVO PROJETO CRIADO*\n\n"
            f"🎯 *Projeto:* {project_name}\n"
            f"🔢 *ID:* #{project_id}\n"
            f"📋 *Etapas:* {len(milestones)}\n\n"
        )

        if milestones:
            message += "*📅 Cronograma de Entregas:*\n\n"
            for i, milestone in enumerate(milestones, 1):
                data_fmt = milestone.data_limite.strftime("%d/%m/%Y")
                message += f"{i}. *{milestone.nome}*\n"
                message += f"   📅 Prazo: {data_fmt}\n"
                if milestone.descricao:
                    message += f"   📝 {milestone.descricao}\n"
                message += "\n"

        message += (
            "🔔 Você receberá lembretes automáticos:\n"
            "• 10, 7, 3 e 1 dias antes de cada prazo\n"
            "• No dia do vencimento\n\n"
            "---\n_Smith 2.0 - Gerenciamento de Projetos_"
        )

        return message


def get_milestone_reminder_service(
    milestone_repo: MilestoneRepository,
    uazapi_service: UazapiService
) -> MilestoneReminderService:
    """Factory function para criar instância do serviço"""
    return MilestoneReminderService(milestone_repo, uazapi_service)
