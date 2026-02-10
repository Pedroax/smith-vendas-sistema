"""
API de Marcos de Projetos (Milestones)
Gerenciamento de etapas e lembretes de projetos
"""
from datetime import date
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.milestone import (
    Milestone, MilestoneCreate, MilestoneUpdate,
    MilestoneWithReminders, ScheduledReminder
)
from app.repository.milestone_repository import MilestoneRepository
from app.services.milestone_reminder_service import (
    MilestoneReminderService,
    get_milestone_reminder_service
)
from app.services.evolution_service import get_evolution_service


router = APIRouter(prefix="/api/milestones", tags=["milestones"])


def get_milestone_repository(db: Session = Depends(get_db)) -> MilestoneRepository:
    """Dependency para obter repository de milestones"""
    return MilestoneRepository(db)


def get_reminder_service(
    db: Session = Depends(get_db)
) -> MilestoneReminderService:
    """Dependency para obter serviço de lembretes"""
    milestone_repo = MilestoneRepository(db)
    evolution_service = get_evolution_service()
    return get_milestone_reminder_service(milestone_repo, evolution_service)


@router.post("/", response_model=Milestone, status_code=201)
async def create_milestone(
    milestone_data: MilestoneCreate,
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """
    Cria um novo marco de projeto

    Lembretes são criados automaticamente pelo trigger do banco
    """
    try:
        milestone = await repo.create_milestone(milestone_data)
        logger.info(f"✅ Marco criado: {milestone.nome} (Projeto #{milestone.project_id})")
        return milestone
    except Exception as e:
        logger.error(f"❌ Erro ao criar marco: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{milestone_id}", response_model=MilestoneWithReminders)
async def get_milestone(
    milestone_id: UUID,
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """Busca um marco específico com seus lembretes"""
    milestone = await repo.get_milestone(milestone_id)

    if not milestone:
        raise HTTPException(status_code=404, detail="Marco não encontrado")

    # Buscar lembretes
    reminders = await repo.get_milestone_reminders(milestone_id)

    return MilestoneWithReminders(**milestone.model_dump(), lembretes=reminders)


@router.get("/project/{project_id}", response_model=List[Milestone])
async def list_project_milestones(
    project_id: int,
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """Lista todos os marcos de um projeto"""
    milestones = await repo.get_project_milestones(project_id)
    return milestones


@router.put("/{milestone_id}", response_model=Milestone)
async def update_milestone(
    milestone_id: UUID,
    milestone_data: MilestoneUpdate,
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """
    Atualiza um marco existente

    Se data_limite for alterada, lembretes são recriados automaticamente
    """
    milestone = await repo.update_milestone(milestone_id, milestone_data)

    if not milestone:
        raise HTTPException(status_code=404, detail="Marco não encontrado")

    logger.info(f"✅ Marco atualizado: {milestone.nome}")
    return milestone


@router.delete("/{milestone_id}", status_code=204)
async def delete_milestone(
    milestone_id: UUID,
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """Deleta um marco (e seus lembretes em cascata)"""
    success = await repo.delete_milestone(milestone_id)

    if not success:
        raise HTTPException(status_code=404, detail="Marco não encontrado")

    logger.info(f"✅ Marco deletado: {milestone_id}")


@router.post("/project/{project_id}/bulk", response_model=List[Milestone])
async def bulk_create_milestones(
    project_id: int,
    milestones_data: List[MilestoneCreate],
    repo: MilestoneRepository = Depends(get_milestone_repository),
    reminder_service: MilestoneReminderService = Depends(get_reminder_service)
):
    """
    Cria múltiplos marcos de uma vez (útil ao criar projeto)

    Envia resumo via WhatsApp após criação
    """
    try:
        # Validar que todos os milestones são do mesmo projeto
        for milestone_data in milestones_data:
            if milestone_data.project_id != project_id:
                raise HTTPException(
                    status_code=400,
                    detail="Todos os marcos devem ser do mesmo projeto"
                )

        # Criar todos os marcos
        milestones = []
        for milestone_data in milestones_data:
            milestone = await repo.create_milestone(milestone_data)
            milestones.append(milestone)

        logger.info(
            f"✅ {len(milestones)} marcos criados para Projeto #{project_id}"
        )

        # Enviar resumo via WhatsApp (não bloqueia se falhar)
        try:
            await reminder_service.send_project_created_summary(
                project_id=project_id,
                project_name=f"Projeto #{project_id}",  # Pode buscar nome real
                milestones=milestones
            )
        except Exception as e:
            logger.warning(f"⚠️  Falha ao enviar resumo por WhatsApp: {e}")

        return milestones

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao criar marcos em lote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{milestone_id}/reminders", response_model=List[ScheduledReminder])
async def get_milestone_reminders(
    milestone_id: UUID,
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """Lista todos os lembretes de um marco"""
    reminders = await repo.get_milestone_reminders(milestone_id)
    return reminders


@router.post("/send-reminders", response_model=dict)
async def send_daily_reminders(
    reminder_service: MilestoneReminderService = Depends(get_reminder_service)
):
    """
    Verifica e envia lembretes pendentes do dia

    Endpoint para ser chamado por cron job diário
    """
    try:
        result = await reminder_service.send_daily_reminders()
        return result
    except Exception as e:
        logger.error(f"❌ Erro ao enviar lembretes diários: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-overdue", response_model=dict)
async def check_overdue_milestones(
    repo: MilestoneRepository = Depends(get_milestone_repository)
):
    """
    Marca marcos como atrasados

    Endpoint para ser chamado por cron job diário
    """
    try:
        count = await repo.mark_overdue_milestones()
        return {
            "overdue_count": count,
            "message": f"{count} marcos marcados como atrasados"
        }
    except Exception as e:
        logger.error(f"❌ Erro ao marcar marcos atrasados: {e}")
        raise HTTPException(status_code=500, detail=str(e))
