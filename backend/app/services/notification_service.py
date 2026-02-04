"""
Serviço de Notificações
Envia notificações sobre eventos importantes (novos leads, etc)
"""
from typing import Dict, Any
from loguru import logger
import httpx
from datetime import datetime

from app.models.lead import Lead
from app.config import settings


class NotificationService:
    """
    Serviço para enviar notificações multi-canal
    Suporta: WhatsApp, Email, Webhook
    """

    async def notify_new_qualified_lead(
        self,
        lead: Lead,
        qualification: Dict[str, Any]
    ):
        """
        Notifica sobre novo lead qualificado

        Args:
            lead: Lead que foi qualificado
            qualification: Resultado da qualificação (score, reasoning, etc)
        """
        logger.info(f"📢 Enviando notificações para lead: {lead.nome}")

        # Preparar mensagem
        message = self._format_lead_notification(lead, qualification)

        # Enviar via WhatsApp (se configurado)
        if settings.notification_whatsapp_enabled:
            await self._send_whatsapp_notification(message, lead)

        # Enviar via Email (se configurado)
        if settings.notification_email_enabled:
            await self._send_email_notification(message, lead, qualification)

        # Enviar via Webhook (se configurado)
        if settings.notification_webhook_url:
            await self._send_webhook_notification(lead, qualification)

        logger.success(f"✅ Notificações enviadas!")

    def _format_lead_notification(
        self,
        lead: Lead,
        qualification: Dict[str, Any]
    ) -> str:
        """
        Formata mensagem de notificação
        """
        score = qualification.get("score", 0)
        reasoning = qualification.get("reasoning", "")
        next_action = qualification.get("next_action", "Entrar em contato")

        # Emoji baseado no score
        if score >= 80:
            emoji = "🔥"
        elif score >= 60:
            emoji = "⭐"
        else:
            emoji = "✅"

        message = f"""
{emoji} **NOVO LEAD QUALIFICADO!** {emoji}

👤 **Nome:** {lead.nome}
🏢 **Empresa:** {lead.empresa or 'Não informado'}
📧 **Email:** {lead.email}
📱 **Telefone:** {lead.telefone or 'Não informado'}

🎯 **Score de Qualificação:** {score}/100

💭 **Análise da IA:**
{reasoning}

🎬 **Próxima ação sugerida:**
{next_action}

📊 **Fonte:** {lead.fonte}
🕐 **Recebido em:** {lead.created_at.strftime('%d/%m/%Y às %H:%M')}

🔗 **Ver no CRM:** http://localhost:3000/crm/{lead.id}
""".strip()

        return message

    async def _send_whatsapp_notification(self, message: str, lead: Lead):
        """
        Envia notificação via WhatsApp
        """
        try:
            # Formatar mensagem para WhatsApp (sem markdown)
            whatsapp_message = message.replace("**", "").replace("*", "")

            # Número do vendedor/gestor que deve receber notificação
            notification_number = settings.notification_whatsapp_number

            if not notification_number:
                logger.warning("⚠️ Número do WhatsApp para notificação não configurado")
                return

            # Aqui você usaria a API do WhatsApp Business
            # Por exemplo, usando Evolution API, Baileys, ou WhatsApp Business API oficial

            # Exemplo com Evolution API (se você tiver)
            """
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.whatsapp_api_url}/message/sendText/{settings.whatsapp_instance}",
                    headers={
                        "apikey": settings.whatsapp_api_key
                    },
                    json={
                        "number": notification_number,
                        "text": whatsapp_message
                    }
                )
                response.raise_for_status()
            """

            logger.info(f"📱 Notificação WhatsApp enviada para {notification_number}")

        except Exception as e:
            logger.error(f"❌ Erro ao enviar WhatsApp: {e}")

    async def _send_email_notification(
        self,
        message: str,
        lead: Lead,
        qualification: Dict[str, Any]
    ):
        """
        Envia notificação via Email
        """
        try:
            notification_email = settings.notification_email_to

            if not notification_email:
                logger.warning("⚠️ Email para notificação não configurado")
                return

            # Aqui você usaria um serviço de email (SendGrid, Resend, etc)
            # Por exemplo, usando Resend:

            """
            import resend
            resend.api_key = settings.resend_api_key

            params = {
                "from": "Smith <notificacoes@seudominio.com>",
                "to": [notification_email],
                "subject": f"🔥 Novo Lead Qualificado: {lead.nome}",
                "html": f"<pre>{message}</pre>"
            }

            email = resend.Emails.send(params)
            """

            logger.info(f"📧 Notificação Email enviada para {notification_email}")

        except Exception as e:
            logger.error(f"❌ Erro ao enviar Email: {e}")

    async def _send_webhook_notification(
        self,
        lead: Lead,
        qualification: Dict[str, Any]
    ):
        """
        Envia notificação via Webhook (para integração com outros sistemas)
        """
        try:
            webhook_url = settings.notification_webhook_url

            if not webhook_url:
                return

            # Preparar payload
            payload = {
                "event": "lead.qualified",
                "timestamp": datetime.now().isoformat(),
                "lead": {
                    "id": lead.id,
                    "nome": lead.nome,
                    "email": lead.email,
                    "telefone": lead.telefone,
                    "empresa": lead.empresa,
                    "origem": lead.origem,
                },
                "qualification": qualification
            }

            # Enviar webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info(f"🔗 Webhook enviado para {webhook_url}")

        except Exception as e:
            logger.error(f"❌ Erro ao enviar Webhook: {e}")

    async def notify_lead_status_change(self, lead: Lead, old_status: str, new_status: str):
        """
        Notifica sobre mudança de status de lead
        """
        message = f"""
📊 **LEAD MUDOU DE STATUS**

👤 **Lead:** {lead.nome}
🏢 **Empresa:** {lead.empresa or 'N/A'}

🔄 **Status:**
De: {old_status}
Para: {new_status}

🔗 **Ver no CRM:** http://localhost:3000/crm/{lead.id}
""".strip()

        logger.info(message)
        # Aqui você pode escolher se envia notificação ou não
