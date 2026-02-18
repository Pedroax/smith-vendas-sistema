"""
API de Leads - CRUD e operações
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from datetime import datetime
import uuid

from app.models.lead import (
    Lead,
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadStatus,
    LeadOrigin,
    LeadTemperature,
    FollowUpConfig,
)
from app.repository.leads_repository import LeadsRepository
from app.websocket import manager

router = APIRouter()

# Repository para acesso ao banco de dados
repository = LeadsRepository()


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(lead_data: LeadCreate):
    """
    Cria um novo lead

    Args:
        lead_data: Dados do lead a criar

    Returns:
        Lead criado com ID
    """
    try:
        # Gerar ID único
        lead_id = str(uuid.uuid4())

        # Criar lead
        lead = Lead(
            id=lead_id,
            nome=lead_data.nome,
            telefone=lead_data.telefone,
            empresa=lead_data.empresa,
            email=lead_data.email,
            origem=lead_data.origem,
            status=LeadStatus.NOVO,
            temperatura=LeadTemperature.MORNO,
            lead_score=0,
            valor_estimado=0,
            followup_config=FollowUpConfig(
                tentativas_realizadas=0,
                intervalo_horas=[24, 72, 168]
            ),
            conversation_history=[],
            tags=[],
            requires_human_approval=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            notas=lead_data.notas
        )

        # Salvar no banco via repository
        created_lead = await repository.create(lead)

        logger.info(f"Lead criado: {created_lead.nome} ({created_lead.id})")

        # Broadcast para clientes WebSocket
        await manager.broadcast_lead_created(created_lead.model_dump(mode='json'))

        return LeadResponse(
            success=True,
            lead=created_lead,
            message="Lead criado com sucesso"
        )

    except Exception as e:
        logger.error(f"Erro ao criar lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Lead])
async def list_leads(
    status: Optional[LeadStatus] = None,
    origem: Optional[LeadOrigin] = None,
    temperatura: Optional[LeadTemperature] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Lista leads com filtros opcionais

    Args:
        status: Filtrar por status
        origem: Filtrar por origem
        temperatura: Filtrar por temperatura
        limit: Número máximo de resultados
        offset: Offset para paginação

    Returns:
        Lista de leads
    """
    try:
        # Buscar leads do banco via repository
        leads = await repository.list_all(
            status=status,
            origem=origem,
            temperatura=temperatura,
            limit=limit,
            offset=offset
        )

        logger.info(f"Listando {len(leads)} leads")

        return leads

    except Exception as e:
        logger.error(f"Erro ao listar leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_stats():
    """
    Retorna estatísticas gerais dos leads
    Usa a função get_leads_stats() do PostgreSQL

    Returns:
        Estatísticas agregadas
    """
    try:
        # Buscar estatísticas do banco (função PostgreSQL)
        stats = await repository.get_stats()

        logger.info(f"Estatísticas calculadas: {stats.get('total_leads', 0)} leads")

        return stats

    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    """
    Busca um lead por ID

    Args:
        lead_id: ID do lead

    Returns:
        Lead encontrado
    """
    try:
        lead = await repository.get_by_id(lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")

        logger.info(f"Lead recuperado: {lead.nome} ({lead_id})")

        return lead

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, lead_data: LeadUpdate):
    """
    Atualiza um lead existente

    Args:
        lead_id: ID do lead
        lead_data: Dados a atualizar

    Returns:
        Lead atualizado
    """
    try:
        # Verificar se lead existe
        existing_lead = await repository.get_by_id(lead_id)
        if not existing_lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")

        # Preparar dados de atualização
        update_data = lead_data.model_dump(exclude_unset=True)

        # Converter Pydantic models para dict se necessário
        if "qualification_data" in update_data and update_data["qualification_data"]:
            update_data["qualificacao_detalhes"] = update_data["qualification_data"].model_dump()
            del update_data["qualification_data"]  # Remove a chave antiga

        if "roi_analysis" in update_data and update_data["roi_analysis"]:
            roi_dict = update_data["roi_analysis"].model_dump()
            # Converter datetime para ISO string
            if roi_dict.get("generated_at"):
                roi_dict["generated_at"] = roi_dict["generated_at"].isoformat()
            update_data["roi_analysis"] = roi_dict

        # Converter enums para valores
        if "status" in update_data:
            update_data["status"] = update_data["status"].value
        if "temperatura" in update_data:
            update_data["temperatura"] = update_data["temperatura"].value

        # Atualizar timestamps especiais baseado no status
        if lead_data.status == LeadStatus.GANHO and not existing_lead.won_at:
            update_data["won_at"] = datetime.now().isoformat()
        elif lead_data.status == LeadStatus.PERDIDO and not existing_lead.lost_at:
            update_data["lost_at"] = datetime.now().isoformat()

        # Atualizar no banco
        updated_lead = await repository.update(lead_id, update_data)

        logger.info(f"Lead atualizado: {updated_lead.nome} ({lead_id})")

        # Broadcast para clientes WebSocket
        await manager.broadcast_lead_updated(updated_lead.model_dump(mode='json'))

        # Se o status mudou, broadcast específico
        if lead_data.status and str(lead_data.status.value) != str(existing_lead.status):
            # existing_lead.status vem do banco como string
            # lead_data.status é um enum LeadStatus
            old_status = str(existing_lead.status)
            new_status = lead_data.status.value
            await manager.broadcast_lead_status_changed(
                lead_id,
                old_status,
                new_status
            )

        return LeadResponse(
            success=True,
            lead=updated_lead,
            message="Lead atualizado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lead_id}", response_model=LeadResponse)
async def delete_lead(lead_id: str):
    """
    Deleta um lead

    Args:
        lead_id: ID do lead

    Returns:
        Confirmação de deleção
    """
    try:
        # Verificar se lead existe
        lead = await repository.get_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")

        # Deletar do banco
        await repository.delete(lead_id)

        logger.warning(f"Lead deletado: {lead.nome} ({lead_id})")

        # Broadcast para clientes WebSocket
        await manager.broadcast_lead_deleted(lead_id)

        return LeadResponse(
            success=True,
            lead=None,
            message=f"Lead {lead.nome} deletado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/qualify", response_model=LeadResponse)
async def force_qualification(lead_id: str):
    """
    Força re-qualificação de um lead

    Args:
        lead_id: ID do lead

    Returns:
        Lead com novo score
    """
    try:
        # Buscar lead do banco
        lead = await repository.get_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")

        # Importar lead_qualifier
        from app.services import lead_qualifier

        # Re-qualificar
        is_qualified, reason, score = lead_qualifier.is_qualified(lead)

        # Preparar atualização
        update_data = {
            "lead_score": score,
            "ai_summary": reason,
        }

        if is_qualified:
            update_data["status"] = LeadStatus.QUALIFICADO.value
            update_data["temperatura"] = LeadTemperature.QUENTE.value
        else:
            update_data["status"] = LeadStatus.PERDIDO.value
            update_data["temperatura"] = LeadTemperature.FRIO.value
            update_data["lost_at"] = datetime.now().isoformat()

        # Atualizar no banco
        updated_lead = await repository.update(lead_id, update_data)

        logger.info(f"Lead re-qualificado: {updated_lead.nome} - Score: {score} - Qualificado: {is_qualified}")

        return LeadResponse(
            success=True,
            lead=updated_lead,
            message=f"Lead {'qualificado' if is_qualified else 'não qualificado'} com score {score}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao re-qualificar lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Função auxiliar para popular banco com leads de exemplo
def seed_mock_leads():
    """Popula banco com leads de exemplo para testes"""
    if LEADS_DB:
        return  # Já tem dados

    from app.models.lead import QualificationData, ROIAnalysis

    mock_leads = [
        Lead(
            id="1",
            nome="Carlos Silva",
            empresa="TechCorp",
            telefone="5511999998888",
            email="carlos@techcorp.com",
            status=LeadStatus.QUALIFICADO,
            origem=LeadOrigin.INSTAGRAM,
            temperatura=LeadTemperature.QUENTE,
            valor_estimado=15000,
            lead_score=85,
            qualification_data=QualificationData(
                budget=3000,
                authority=True,
                need="Preciso automatizar atendimento urgentemente",
                timing="Este mês",
                atendimentos_por_dia=80,
                tempo_por_atendimento=12,
                ticket_medio=450
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            followup_config=FollowUpConfig(tentativas_realizadas=0, intervalo_horas=[24, 72, 168]),
            conversation_history=[],
            tags=["alta-prioridade"],
            requires_human_approval=False
        ),
        # Adicionar mais leads mock aqui...
    ]

    for lead in mock_leads:
        LEADS_DB[lead.id] = lead

    logger.info(f"Banco populado com {len(mock_leads)} leads de exemplo")
