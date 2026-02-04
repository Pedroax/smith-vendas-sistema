"""
Serviço de Follow-up via WhatsApp
Envia mensagens automáticas após qualificação e agenda reuniões
"""
from typing import Dict, Any, Optional, List
from loguru import logger
import httpx
from datetime import datetime

from app.models.lead import Lead, LeadStatus
from app.repository.leads_repository import LeadsRepository
from app.services.google_calendar_service import google_calendar_service
from app.services.notification_service import NotificationService
from app.config import settings
from app.database import SessionLocal


class WhatsAppFollowUpService:
    """
    Serviço para follow-up automático via WhatsApp
    - Envia mensagem com horários disponíveis
    - Processa resposta do lead
    - Agenda reunião no Google Calendar
    - Atualiza status do lead
    """

    def __init__(self):
        self.leads_repo = LeadsRepository()
        self.notification_service = NotificationService()

    async def send_scheduling_message(self, lead: Lead) -> bool:
        """
        Envia mensagem automática com opções de horário

        Args:
            lead: Lead qualificado

        Returns:
            True se mensagem foi enviada com sucesso
        """
        try:
            logger.info(f"📱 Enviando mensagem de agendamento para {lead.nome}")

            # Buscar horários disponíveis no Google Calendar
            if not google_calendar_service.is_available():
                logger.warning("⚠️ Google Calendar não disponível, não é possível buscar horários")
                return False

            available_slots = await google_calendar_service.get_available_slots(
                days_ahead=7,
                num_slots=3,
                duration_minutes=settings.calendar_meeting_duration
            )

            if not available_slots:
                logger.warning("⚠️ Nenhum horário disponível encontrado")
                return False

            # Formatar mensagem com horários
            message = self._format_scheduling_message(lead, available_slots)

            # Enviar via WhatsApp
            success = await self._send_whatsapp_message(lead.telefone, message)

            if success:
                # Marcar que mensagem de agendamento foi enviada
                self._mark_agendamento_sent(lead)
                logger.success(f"✅ Mensagem de agendamento enviada para {lead.nome}")
                return True
            else:
                logger.error(f"❌ Falha ao enviar mensagem para {lead.nome}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem de agendamento: {e}")
            return False

    def _format_scheduling_message(
        self,
        lead: Lead,
        available_slots: List[Dict[str, Any]]
    ) -> str:
        """
        Formata mensagem com horários disponíveis

        Args:
            lead: Lead qualificado
            available_slots: Lista de horários disponíveis

        Returns:
            Mensagem formatada
        """
        # Obter nome próprio (primeiro nome)
        first_name = lead.nome.split()[0]

        # Construir lista natural de horários
        if len(available_slots) == 1:
            horarios_text = f"*{available_slots[0]['display']}*"
        elif len(available_slots) == 2:
            horarios_text = f"*{available_slots[0]['display']}* ou *{available_slots[1]['display']}*"
        else:
            horarios_parts = [f"*{slot['display']}*" for slot in available_slots[:-1]]
            horarios_text = ", ".join(horarios_parts) + f" ou *{available_slots[-1]['display']}*"

        message = f"""Olá {first_name}! 👋

Vi que você demonstrou interesse no nosso *sistema de automação com IA* para gestão de leads.

Acabei de verificar a agenda aqui e tenho disponibilidade para uma conversa em:

{horarios_text}

Algum desses horários funciona pra você? Se preferir outro dia ou horário, é só me avisar que a gente se ajusta! 😊

_Ah, e pode me fazer qualquer pergunta sobre o sistema, estou aqui pra te ajudar._"""

        return message

    async def _send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        """
        Envia mensagem via Evolution API (WhatsApp)

        Args:
            phone_number: Número do telefone (ex: 11999999999)
            message: Mensagem a enviar

        Returns:
            True se enviado com sucesso
        """
        try:
            # Limpar número de telefone
            clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

            # Garantir que tem código do país (Brasil = 55)
            if not clean_phone.startswith("55"):
                clean_phone = f"55{clean_phone}"

            # API da Evolution
            url = f"{settings.evolution_api_url}/message/sendText/{settings.evolution_instance_name}"

            headers = {
                "apikey": settings.evolution_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "number": clean_phone,
                "text": message
            }

            # Enviar requisição
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

            logger.success(f"✅ Mensagem WhatsApp enviada para {clean_phone}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Erro HTTP ao enviar WhatsApp: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar WhatsApp: {e}")
            return False

    async def process_scheduling_response(
        self,
        lead_id: str,
        message_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Processa resposta do lead sobre horário

        Args:
            lead_id: ID do lead
            message_text: Texto da mensagem recebida

        Returns:
            Dicionário com resultado do agendamento ou None se falhou
        """
        try:
            logger.info(f"📝 Processando resposta de agendamento do lead {lead_id}")

            # Buscar lead
            lead = await self.leads_repo.get_by_id(lead_id)
            if not lead:
                logger.error(f"❌ Lead {lead_id} não encontrado")
                return None

            # Analisar resposta (1, 2, 3 ou texto livre)
            message_lower = message_text.strip().lower()

            # Buscar horários disponíveis novamente (pode ter mudado)
            available_slots = await google_calendar_service.get_available_slots(
                days_ahead=7,
                num_slots=3,
                duration_minutes=settings.calendar_meeting_duration
            )

            if not available_slots:
                logger.warning("⚠️ Nenhum horário disponível")
                return None

            # Identificar escolha
            selected_slot = None

            if "1" in message_lower or "primeiro" in message_lower:
                selected_slot = available_slots[0]
            elif "2" in message_lower or "segundo" in message_lower:
                selected_slot = available_slots[1] if len(available_slots) > 1 else None
            elif "3" in message_lower or "terceiro" in message_lower:
                selected_slot = available_slots[2] if len(available_slots) > 2 else None
            elif "4" in message_lower or "outro" in message_lower:
                # Lead quer outro horário - aqui você pode implementar lógica adicional
                logger.info("Lead solicitou outro horário - implementar lógica customizada")
                return {
                    "status": "needs_custom_scheduling",
                    "message": "Lead solicitou horário customizado"
                }

            if not selected_slot:
                logger.warning("⚠️ Não foi possível identificar horário escolhido")
                return None

            # Criar evento no Google Calendar
            event_id = await google_calendar_service.create_meeting(
                lead_name=lead.nome,
                lead_email=lead.email or "",
                lead_phone=lead.telefone,
                meeting_datetime=selected_slot["start"],
                duration_minutes=settings.calendar_meeting_duration,
                empresa=lead.empresa
            )

            if not event_id:
                logger.error("❌ Falha ao criar evento no Google Calendar")
                return None

            # Atualizar lead no CRM
            lead.status = LeadStatus.AGENDAMENTO_MARCADO
            lead.meeting_scheduled_at = selected_slot["start"]
            lead.meeting_google_event_id = event_id["event_id"]
            lead.updated_at = datetime.now()

            updated_lead = await self.leads_repo.update(lead)

            # Enviar confirmação para o lead
            confirmation_message = f"""✅ *Agendamento confirmado!*

📅 *Data/Hora:* {selected_slot['display']}
⏱️ *Duração:* {settings.calendar_meeting_duration} minutos

🔗 *Link do Google Meet:* {event_id.get('meet_link', 'Será enviado por email')}

Você receberá um email de confirmação com todos os detalhes.

Até lá! 👋
"""
            await self._send_whatsapp_message(lead.telefone, confirmation_message)

            # Notificar Pedro sobre o agendamento
            await self._notify_meeting_scheduled(updated_lead, selected_slot)

            logger.success(f"✅ Agendamento concluído para {lead.nome}")

            return {
                "status": "scheduled",
                "lead_id": lead.id,
                "event_id": event_id["event_id"],
                "meeting_time": selected_slot["display"],
                "meet_link": event_id.get("meet_link")
            }

        except Exception as e:
            logger.error(f"❌ Erro ao processar resposta de agendamento: {e}")
            return None

    async def _notify_meeting_scheduled(
        self,
        lead: Lead,
        slot: Dict[str, Any]
    ):
        """
        Notifica Pedro sobre reunião agendada

        Args:
            lead: Lead com reunião agendada
            slot: Horário agendado
        """
        try:
            notification_message = f"""
📅 *REUNIÃO AGENDADA AUTOMATICAMENTE!*

👤 *Lead:* {lead.nome}
🏢 *Empresa:* {lead.empresa or 'N/A'}
📱 *Telefone:* {lead.telefone}
📧 *Email:* {lead.email or 'N/A'}

⏰ *Horário:* {slot['display']}
🕐 *Duração:* {settings.calendar_meeting_duration} minutos

🎯 *Score:* {lead.lead_score}/100

💬 *Próxima Ação:*
Preparar demonstração personalizada com foco nos pontos de dor do lead.

🔗 *Ver no CRM:* http://localhost:3000/crm/{lead.id}
"""

            # Enviar notificação para Pedro via WhatsApp
            if settings.notification_whatsapp_enabled and settings.notification_whatsapp_number:
                await self._send_whatsapp_message(
                    settings.notification_whatsapp_number,
                    notification_message
                )

            logger.success("✅ Notificação de agendamento enviada")

        except Exception as e:
            logger.error(f"❌ Erro ao notificar agendamento: {e}")

    def _mark_agendamento_sent(self, lead: Lead):
        """
        Marca que mensagem de agendamento foi enviada
        Cria/atualiza conversa no banco
        """
        try:
            from app.repositories.conversation_repository import ConversationRepository, MessageRepository
            from app.models.conversation import MessageDirection, MessageType

            db = SessionLocal()

            try:
                conversation_repo = ConversationRepository(db)
                message_repo = MessageRepository(db)

                # Buscar ou criar conversa
                conversation = conversation_repo.get_by_phone(lead.telefone)
                if not conversation:
                    conversation = conversation_repo.create(
                        lead_id=lead.id,
                        phone_number=lead.telefone
                    )

                # Marcar que enviou mensagem de agendamento
                conversation_repo.mark_agendamento_sent(conversation.id)

                logger.success(f"✅ Conversa marcada como AGENDAMENTO_ENVIADO")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"❌ Erro ao marcar agendamento enviado: {e}")
