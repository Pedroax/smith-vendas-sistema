"""
API de Agendamentos/Compromissos
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.appointment import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentType,
    AppointmentStatus
)
from app.repository.appointment_repository import get_appointment_repository

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", response_model=Appointment)
async def create_appointment(data: AppointmentCreate):
    """Criar novo agendamento"""
    repo = get_appointment_repository()
    appointment = await repo.create_appointment(data)

    if not appointment:
        raise HTTPException(status_code=500, detail="Erro ao criar agendamento")

    return appointment


@router.get("/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    """Buscar agendamento por ID"""
    repo = get_appointment_repository()
    appointment = await repo.get_appointment(appointment_id)

    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return appointment


@router.get("/lead/{lead_id}", response_model=List[Appointment])
async def list_appointments_by_lead(
    lead_id: str,
    include_past: bool = Query(default=False)
):
    """Listar agendamentos de um lead específico"""
    repo = get_appointment_repository()
    appointments = await repo.list_appointments_by_lead(lead_id, include_past)
    return appointments


@router.get("", response_model=List[Appointment])
async def list_appointments(
    start_date: Optional[str] = Query(default=None, description="Data início (ISO format)"),
    end_date: Optional[str] = Query(default=None, description="Data fim (ISO format)"),
    status: Optional[AppointmentStatus] = Query(default=None),
    tipo: Optional[AppointmentType] = Query(default=None),
    upcoming_days: Optional[int] = Query(default=None, description="Próximos N dias"),
    today_only: bool = Query(default=False, description="Apenas hoje")
):
    """
    Listar agendamentos com filtros

    - Por período: usar start_date e end_date
    - Próximos dias: usar upcoming_days (ex: 7 para próxima semana)
    - Apenas hoje: usar today_only=true
    - Filtrar por status ou tipo
    """
    repo = get_appointment_repository()

    # Apenas hoje
    if today_only:
        appointments = await repo.list_today_appointments()
        return appointments

    # Próximos dias
    if upcoming_days is not None:
        appointments = await repo.list_upcoming_appointments(days_ahead=upcoming_days)
        return appointments

    # Por período
    if start_date and end_date:
        appointments = await repo.list_appointments_by_date_range(
            start_date=start_date,
            end_date=end_date,
            status_filter=status,
            tipo_filter=tipo
        )
        return appointments

    # Se nenhum filtro, retorna próximos 7 dias
    appointments = await repo.list_upcoming_appointments(days_ahead=7)
    return appointments


@router.put("/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, data: AppointmentUpdate):
    """Atualizar agendamento"""
    repo = get_appointment_repository()
    appointment = await repo.update_appointment(appointment_id, data)

    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return appointment


@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """Deletar agendamento"""
    repo = get_appointment_repository()
    success = await repo.delete_appointment(appointment_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return {"success": True, "message": "Agendamento deletado com sucesso"}


@router.post("/{appointment_id}/complete", response_model=Appointment)
async def mark_appointment_completed(appointment_id: str):
    """Marcar agendamento como concluído"""
    repo = get_appointment_repository()
    appointment = await repo.mark_as_completed(appointment_id)

    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return appointment


@router.post("/{appointment_id}/reminder-sent")
async def mark_reminder_sent(appointment_id: str):
    """Marcar lembrete como enviado"""
    repo = get_appointment_repository()
    success = await repo.mark_reminder_sent(appointment_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return {"success": True, "message": "Lembrete marcado como enviado"}
