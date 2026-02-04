"""
Repository para Agendamentos
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4
from loguru import logger

from app.config import settings
from app.models.appointment import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentType,
    AppointmentStatus
)


class AppointmentRepository:
    """Repository para gerenciar agendamentos"""

    def __init__(self):
        self.supabase = settings.supabase

    async def create_appointment(self, data: AppointmentCreate) -> Optional[Appointment]:
        """Criar novo agendamento"""
        try:
            # Get lead name for denormalization
            lead_result = self.supabase.table("leads").select("nome").eq("id", data.lead_id).execute()
            lead_nome = lead_result.data[0]["nome"] if lead_result.data else None

            appointment_data = {
                "id": str(uuid4()),
                "lead_id": data.lead_id,
                "lead_nome": lead_nome,
                "tipo": data.tipo.value if isinstance(data.tipo, AppointmentType) else data.tipo,
                "titulo": data.titulo,
                "descricao": data.descricao,
                "data_hora": data.data_hora,
                "duracao_minutos": data.duracao_minutos,
                "status": AppointmentStatus.AGENDADO.value,
                "user_nome": data.user_nome,
                "location": data.location,
                "meeting_url": data.meeting_url,
                "observacoes": data.observacoes,
                "lembrete_enviado": False,
                "metadata": data.metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = self.supabase.table("appointments").insert(appointment_data).execute()

            if result.data:
                return Appointment(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {e}")
            return None

    async def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Buscar agendamento por ID"""
        try:
            result = self.supabase.table("appointments").select("*").eq("id", appointment_id).execute()

            if result.data:
                return Appointment(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar agendamento: {e}")
            return None

    async def list_appointments_by_lead(
        self,
        lead_id: str,
        include_past: bool = False
    ) -> List[Appointment]:
        """Listar agendamentos de um lead"""
        try:
            query = (
                self.supabase.table("appointments")
                .select("*")
                .eq("lead_id", lead_id)
            )

            if not include_past:
                now = datetime.utcnow().isoformat()
                query = query.gte("data_hora", now)

            result = query.order("data_hora", desc=False).execute()

            if result.data:
                return [Appointment(**item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Erro ao listar agendamentos do lead: {e}")
            return []

    async def list_appointments_by_date_range(
        self,
        start_date: str,
        end_date: str,
        status_filter: Optional[AppointmentStatus] = None,
        tipo_filter: Optional[AppointmentType] = None
    ) -> List[Appointment]:
        """Listar agendamentos por período"""
        try:
            query = (
                self.supabase.table("appointments")
                .select("*")
                .gte("data_hora", start_date)
                .lte("data_hora", end_date)
            )

            if status_filter:
                status_value = status_filter.value if isinstance(status_filter, AppointmentStatus) else status_filter
                query = query.eq("status", status_value)

            if tipo_filter:
                tipo_value = tipo_filter.value if isinstance(tipo_filter, AppointmentType) else tipo_filter
                query = query.eq("tipo", tipo_value)

            result = query.order("data_hora", desc=False).execute()

            if result.data:
                return [Appointment(**item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Erro ao listar agendamentos por período: {e}")
            return []

    async def list_upcoming_appointments(
        self,
        days_ahead: int = 7,
        limit: int = 50
    ) -> List[Appointment]:
        """Listar próximos agendamentos"""
        try:
            now = datetime.utcnow()
            end_date = now + timedelta(days=days_ahead)

            result = (
                self.supabase.table("appointments")
                .select("*")
                .gte("data_hora", now.isoformat())
                .lte("data_hora", end_date.isoformat())
                .neq("status", AppointmentStatus.CANCELADO.value)
                .order("data_hora", desc=False)
                .limit(limit)
                .execute()
            )

            if result.data:
                return [Appointment(**item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Erro ao listar próximos agendamentos: {e}")
            return []

    async def list_today_appointments(self) -> List[Appointment]:
        """Listar agendamentos de hoje"""
        try:
            today = datetime.utcnow().date()
            start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
            end_of_day = datetime.combine(today, datetime.max.time()).isoformat()

            return await self.list_appointments_by_date_range(start_of_day, end_of_day)
        except Exception as e:
            logger.error(f"Erro ao listar agendamentos de hoje: {e}")
            return []

    async def update_appointment(
        self,
        appointment_id: str,
        data: AppointmentUpdate
    ) -> Optional[Appointment]:
        """Atualizar agendamento"""
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}

            if "tipo" in update_data:
                update_data["tipo"] = update_data["tipo"].value if hasattr(update_data["tipo"], "value") else update_data["tipo"]

            if "status" in update_data:
                update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = (
                self.supabase.table("appointments")
                .update(update_data)
                .eq("id", appointment_id)
                .execute()
            )

            if result.data:
                return Appointment(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar agendamento: {e}")
            return None

    async def delete_appointment(self, appointment_id: str) -> bool:
        """Deletar agendamento"""
        try:
            self.supabase.table("appointments").delete().eq("id", appointment_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar agendamento: {e}")
            return False

    async def mark_as_completed(self, appointment_id: str) -> Optional[Appointment]:
        """Marcar agendamento como concluído"""
        try:
            update_data = {
                "status": AppointmentStatus.CONCLUIDO.value,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = (
                self.supabase.table("appointments")
                .update(update_data)
                .eq("id", appointment_id)
                .execute()
            )

            if result.data:
                return Appointment(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao marcar agendamento como concluído: {e}")
            return None

    async def mark_reminder_sent(self, appointment_id: str) -> bool:
        """Marcar lembrete como enviado"""
        try:
            update_data = {
                "lembrete_enviado": True,
                "updated_at": datetime.utcnow().isoformat()
            }

            self.supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao marcar lembrete: {e}")
            return False


# Instância global do repository
_appointment_repository: Optional[AppointmentRepository] = None


def get_appointment_repository() -> AppointmentRepository:
    """Retorna instância do AppointmentRepository"""
    global _appointment_repository
    if _appointment_repository is None:
        _appointment_repository = AppointmentRepository()
    return _appointment_repository
