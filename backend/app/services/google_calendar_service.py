"""
Serviço de integração com Google Calendar API
Gerencia criação de eventos e agendamentos
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional, Dict, Any, List
import os
import json
from zoneinfo import ZoneInfo

from app.config import settings

# Configurações
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Timezone São Paulo
SP_TZ = ZoneInfo('America/Sao_Paulo')


class GoogleCalendarService:
    """Serviço para integração com Google Calendar"""

    def __init__(self):
        """Inicializa o serviço com autenticação"""
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Autentica com Google Calendar API usando Service Account"""
        try:
            credentials = None

            # OPÇÃO 1: Tentar carregar da variável de ambiente (PRODUÇÃO - Railway)
            if settings.google_credentials_json:
                logger.info("🔑 Carregando credenciais do Google Calendar da variável de ambiente...")
                try:
                    credentials_dict = json.loads(settings.google_credentials_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict,
                        scopes=SCOPES
                    )
                    logger.success("✅ Credenciais carregadas da variável de ambiente")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON inválido em GOOGLE_CREDENTIALS_JSON: {str(e)}")
                except Exception as e:
                    logger.error(f"❌ Erro ao processar credenciais da env var: {str(e)}")

            # OPÇÃO 2: Tentar carregar do arquivo (DESENVOLVIMENTO - Local)
            if not credentials:
                credentials_path = settings.google_credentials_path

                if os.path.exists(credentials_path):
                    logger.info(f"🔑 Carregando credenciais do arquivo: {credentials_path}")
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_path,
                        scopes=SCOPES
                    )
                    logger.success("✅ Credenciais carregadas do arquivo local")
                else:
                    logger.warning(f"⚠️ Arquivo de credenciais não encontrado: {credentials_path}")

            # Verificar se conseguiu carregar credenciais
            if not credentials:
                logger.warning("⚠️ Google Calendar desabilitado. Configure GOOGLE_CREDENTIALS_JSON (Railway) ou google_credentials.json (local)")
                return

            # Construir serviço
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.success("✅ Google Calendar API autenticado e disponível")

        except Exception as e:
            logger.error(f"❌ Erro ao autenticar com Google Calendar: {str(e)}")
            logger.warning("⚠️ Google Calendar desabilitado")

    def is_available(self) -> bool:
        """Verifica se o serviço está disponível"""
        return self.service is not None

    async def create_meeting(
        self,
        lead_name: str,
        lead_email: str,
        lead_phone: str,
        meeting_datetime: datetime,
        duration_minutes: int = 30,
        empresa: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cria uma reunião no Google Calendar

        Args:
            lead_name: Nome do lead
            lead_email: Email do lead
            lead_phone: Telefone do lead
            meeting_datetime: Data e hora da reunião
            duration_minutes: Duração em minutos (padrão 30)
            empresa: Nome da empresa (opcional)

        Returns:
            Dicionário com dados do evento criado ou None em caso de erro
        """
        if not self.is_available():
            logger.error("❌ Google Calendar não está disponível")
            return None

        try:
            # Garantir que datetime tem timezone
            if meeting_datetime.tzinfo is None:
                meeting_datetime = meeting_datetime.replace(tzinfo=SP_TZ)

            # Calcular fim da reunião
            end_datetime = meeting_datetime + timedelta(minutes=duration_minutes)

            # ===== VERIFICAR CONFLITOS =====
            # Buscar eventos existentes no período
            events_result = self.service.events().list(
                calendarId=settings.google_calendar_id,
                timeMin=meeting_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            existing_events = events_result.get('items', [])

            # Verificar se há conflito
            for event in existing_events:
                event_start_raw = event['start'].get('dateTime', event['start'].get('date'))
                event_end_raw = event['end'].get('dateTime', event['end'].get('date'))

                event_start = datetime.fromisoformat(event_start_raw.replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event_end_raw.replace('Z', '+00:00'))

                # Converter para SP_TZ se necessário
                if event_start.tzinfo != SP_TZ:
                    event_start = event_start.astimezone(SP_TZ)
                if event_end.tzinfo != SP_TZ:
                    event_end = event_end.astimezone(SP_TZ)

                # Verificar conflito (qualquer sobreposição)
                if (meeting_datetime < event_end and end_datetime > event_start):
                    logger.warning(f"⚠️ Conflito detectado: {meeting_datetime.strftime('%d/%m %H:%M')} com evento existente {event.get('summary', 'Sem título')}")
                    return None  # Retorna None = horário ocupado

            # Criar descrição
            description_parts = [
                f"Reunião de qualificação com {lead_name}",
                f"Telefone: {lead_phone}",
            ]
            if empresa:
                description_parts.insert(1, f"Empresa: {empresa}")

            description = "\n".join(description_parts)

            # Criar evento
            # Nota: Google Meet não pode ser criado automaticamente via service account
            # O usuário pode adicionar o Meet manualmente no calendário depois
            event = {
                'summary': f'Reunião - {lead_name}' + (f' ({empresa})' if empresa else ''),
                'description': description + "\n\n💡 Dica: Clique em 'Adicionar Google Meet' ao abrir o evento no calendário",
                'start': {
                    'dateTime': meeting_datetime.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                # Não adicionar attendees quando usar service account
                # Service accounts precisam de Domain-Wide Delegation para isso
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},        # 1 hora antes
                        {'method': 'popup', 'minutes': 10},        # 10 min antes
                    ],
                },
            }

            # Inserir evento no calendário
            created_event = self.service.events().insert(
                calendarId=settings.google_calendar_id,
                body=event,
                sendUpdates='none'  # Não enviar emails (service account)
            ).execute()

            logger.success(f"✅ Reunião criada no Google Calendar para {lead_name}")
            logger.info(f"📅 Data/Hora: {meeting_datetime.strftime('%d/%m/%Y às %H:%M')}")

            # Extrair informações importantes
            result = {
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'meet_link': created_event.get('hangoutLink'),
                'start_time': meeting_datetime.isoformat(),
                'end_time': end_datetime.isoformat(),
                'calendar_id': settings.google_calendar_id,
            }

            return result

        except Exception as e:
            logger.error(f"❌ Erro ao criar reunião no Google Calendar: {str(e)}")
            return None

    def _round_to_next_hour(self, dt: datetime) -> datetime:
        """
        Arredonda datetime para a próxima hora cheia
        Ex: 16:22 -> 17:00, 16:00 -> 16:00
        """
        if dt.minute == 0 and dt.second == 0:
            return dt  # Já está na hora cheia

        # Arredondar para a próxima hora
        return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    async def get_available_slots(
        self,
        days_ahead: int = 7,
        num_slots: int = 3,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Retorna horários disponíveis nos próximos dias

        Args:
            days_ahead: Quantos dias no futuro buscar (padrão: 7 dias)
            num_slots: Quantos horários retornar (padrão: 3)
            duration_minutes: Duração da reunião (padrão: 60 minutos)

        Returns:
            Lista de dicionários com horários disponíveis:
            [
                {
                    "start": datetime,
                    "end": datetime,
                    "display": "Amanhã às 10h",
                    "day_name": "Terça-feira"
                },
                ...
            ]
        """
        if not self.is_available():
            logger.error("❌ Google Calendar não está disponível")
            return []

        try:
            logger.info(f"🔍 Buscando {num_slots} horários disponíveis nos próximos {days_ahead} dias")

            # Configurações de horário de trabalho
            work_start = settings.calendar_work_start_hour  # Ex: "09:00"
            work_end = settings.calendar_work_end_hour  # Ex: "18:00"
            work_days = [int(d) for d in settings.calendar_work_days.split(",")]  # Ex: [1,2,3,4,5]

            work_start_hour = int(work_start.split(":")[0])
            work_start_minute = int(work_start.split(":")[1])
            work_end_hour = int(work_end.split(":")[0])
            work_end_minute = int(work_end.split(":")[1])

            # Data de início e fim da busca
            now = datetime.now(SP_TZ)
            search_start = now + timedelta(hours=1)  # Começa daqui 1 hora

            # ===== ARREDONDAR PARA HORA CHEIA (XX:00) =====
            search_start = self._round_to_next_hour(search_start)

            search_end = now + timedelta(days=days_ahead)

            # Buscar eventos existentes no Google Calendar
            logger.info(f"🔍 Buscando eventos no calendário: {settings.google_calendar_id}")
            logger.info(f"🔍 Período: {search_start.isoformat()} até {search_end.isoformat()}")

            events_result = self.service.events().list(
                calendarId=settings.google_calendar_id,
                timeMin=search_start.isoformat(),
                timeMax=search_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            existing_events = events_result.get('items', [])
            logger.info(f"📅 Encontrados {len(existing_events)} eventos já agendados")

            # LOG DETALHADO: Mostrar eventos encontrados
            if existing_events:
                logger.info("📋 EVENTOS ENCONTRADOS:")
                for evt in existing_events:
                    evt_start = evt.get('start', {}).get('dateTime', evt.get('start', {}).get('date'))
                    evt_summary = evt.get('summary', 'Sem título')
                    logger.info(f"   - {evt_summary} em {evt_start}")
            else:
                logger.warning("⚠️ NENHUM evento retornado pela API do Google Calendar")
                logger.warning(f"⚠️ Verifique se o calendário {settings.google_calendar_id} está compartilhado com a service account")
                logger.warning(f"⚠️ Service account: smith-calendar-service@gen-lang-client-0661934225.iam.gserviceaccount.com")

            # Gerar slots candidatos
            available_slots = []
            current_date = search_start.date()

            while len(available_slots) < num_slots and current_date <= search_end.date():
                # Verificar se é dia de trabalho
                weekday = current_date.isoweekday()  # 1=segunda, 7=domingo

                if weekday not in work_days:
                    current_date += timedelta(days=1)
                    continue

                # Gerar slots para este dia
                current_time = datetime.combine(
                    current_date,
                    datetime.min.time(),
                    tzinfo=SP_TZ
                ).replace(hour=work_start_hour, minute=work_start_minute)

                # ===== GARANTIR QUE SLOTS SEJAM APENAS EM HORA CHEIA (XX:00) =====
                current_time = self._round_to_next_hour(current_time)

                end_of_day = current_time.replace(hour=work_end_hour, minute=work_end_minute)

                # Se for hoje, começar a partir de agora + 1 hora (já arredondado)
                if current_date == search_start.date():
                    current_time = max(current_time, search_start)

                while current_time + timedelta(minutes=duration_minutes) <= end_of_day:
                    slot_end = current_time + timedelta(minutes=duration_minutes)

                    # Verificar se não conflita com eventos existentes
                    is_available = True
                    for event in existing_events:
                        event_start_raw = event['start'].get('dateTime', event['start'].get('date'))
                        event_end_raw = event['end'].get('dateTime', event['end'].get('date'))

                        event_start = datetime.fromisoformat(event_start_raw.replace('Z', '+00:00'))
                        event_end = datetime.fromisoformat(event_end_raw.replace('Z', '+00:00'))

                        # Converter para SP_TZ se necessário
                        if event_start.tzinfo != SP_TZ:
                            event_start = event_start.astimezone(SP_TZ)
                        if event_end.tzinfo != SP_TZ:
                            event_end = event_end.astimezone(SP_TZ)

                        # Verificar conflito
                        if (current_time < event_end and slot_end > event_start):
                            is_available = False
                            break

                    if is_available:
                        available_slots.append({
                            "start": current_time,
                            "end": slot_end,
                            "display": self._format_slot_display(current_time),
                            "day_name": self._get_day_name(current_time)
                        })

                        if len(available_slots) >= num_slots:
                            break

                    # Próximo slot (a cada 60 minutos)
                    current_time += timedelta(minutes=60)

                current_date += timedelta(days=1)

            logger.success(f"✅ {len(available_slots)} horários disponíveis encontrados")
            return available_slots[:num_slots]

        except Exception as e:
            logger.error(f"❌ Erro ao buscar slots disponíveis: {str(e)}")
            return []

    def _format_slot_display(self, dt: datetime) -> str:
        """
        Formata data/hora para exibição
        Ex: "Amanhã às 10h", "Quinta-feira às 14h"
        """
        now = datetime.now(SP_TZ)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        if dt.date() == today:
            return f"Hoje às {dt.strftime('%H:%M')}"
        elif dt.date() == tomorrow:
            return f"Amanhã às {dt.strftime('%H:%M')}"
        else:
            day_name = self._get_day_name(dt)
            return f"{day_name} às {dt.strftime('%H:%M')}"

    def _get_day_name(self, dt: datetime) -> str:
        """Retorna nome do dia em português"""
        days = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo"
        }
        return days[dt.weekday()]

    async def cancel_meeting(self, event_id: str) -> bool:
        """
        Cancela uma reunião

        Args:
            event_id: ID do evento

        Returns:
            True se cancelado com sucesso, False caso contrário
        """
        if not self.is_available():
            logger.error("❌ Google Calendar não está disponível")
            return False

        try:
            self.service.events().delete(
                calendarId=settings.google_calendar_id,
                eventId=event_id,
                sendUpdates='none'  # Não notificar (service account)
            ).execute()

            logger.success(f"✅ Reunião cancelada: {event_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao cancelar reunião: {str(e)}")
            return False


# Instância global do serviço
google_calendar_service = GoogleCalendarService()
