"""
API de Analytics
Endpoints para métricas e dashboards
"""
from fastapi import APIRouter, Query
from typing import Dict, Any
from app.services.analytics_service import analytics_service
from app.repository.leads_repository import LeadsRepository
from loguru import logger

router = APIRouter(prefix="/analytics", tags=["Analytics"])
leads_repository = LeadsRepository()


@router.get("/dashboard")
async def get_dashboard_metrics(
    periodo_dias: int = Query(default=30, ge=1, le=365, description="Período em dias para análise")
) -> Dict[str, Any]:
    """
    Retorna métricas do dashboard em tempo real

    Args:
        periodo_dias: Número de dias para análise (1-365)

    Returns:
        Métricas completas do dashboard:
        - Resumo geral (total leads, pipeline value, crescimento)
        - Funil de conversão por etapa
        - Distribuição por temperatura
        - Tempo médio em cada estágio
        - Motivos de perda
        - Timeline de evolução
        - Taxas de conversão
    """
    try:
        logger.info(f"📊 Calculando métricas do dashboard (período: {periodo_dias} dias)")
        metrics = await analytics_service.get_dashboard_metrics(periodo_dias)
        return metrics

    except Exception as e:
        logger.error(f"Erro ao buscar métricas do dashboard: {e}")
        raise


@router.get("/funil")
async def get_funil_conversao(
    periodo_dias: int = Query(default=30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Retorna dados do funil de conversão

    Args:
        periodo_dias: Período em dias

    Returns:
        Dados do funil com contagem e percentual por etapa
    """
    try:
        metrics = await analytics_service.get_dashboard_metrics(periodo_dias)
        return {
            "funil": metrics["funil"],
            "taxa_conversao": metrics["taxa_conversao"],
        }

    except Exception as e:
        logger.error(f"Erro ao buscar dados do funil: {e}")
        raise


@router.get("/temperatura")
async def get_distribuicao_temperatura() -> Dict[str, Any]:
    """
    Retorna distribuição de leads por temperatura

    Returns:
        Contagem e percentual de leads quentes/mornos/frios
    """
    try:
        metrics = await analytics_service.get_dashboard_metrics(30)
        return metrics["temperatura"]

    except Exception as e:
        logger.error(f"Erro ao buscar distribuição de temperatura: {e}")
        raise


@router.get("/timeline")
async def get_timeline(
    periodo_dias: int = Query(default=30, ge=7, le=90)
) -> Dict[str, Any]:
    """
    Retorna timeline de evolução de leads

    Args:
        periodo_dias: Período em dias (7-90)

    Returns:
        Série temporal com novos leads, qualificados e perdidos por dia
    """
    try:
        metrics = await analytics_service.get_dashboard_metrics(periodo_dias)
        return {"timeline": metrics["timeline"]}

    except Exception as e:
        logger.error(f"Erro ao buscar timeline: {e}")
        raise


@router.get("/motivos-perda")
async def get_motivos_perda(
    periodo_dias: int = Query(default=30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Retorna principais motivos de perda de leads

    Args:
        periodo_dias: Período em dias

    Returns:
        Lista de motivos com contagem e percentual
    """
    try:
        metrics = await analytics_service.get_dashboard_metrics(periodo_dias)
        return {"motivos_perda": metrics["motivos_perda"]}

    except Exception as e:
        logger.error(f"Erro ao buscar motivos de perda: {e}")
        raise


@router.get("/metricas-integracao")
async def get_metricas_integracao() -> Dict[str, Any]:
    """
    Retorna métricas de leads atendidos vs integrados ao CRM

    Endpoint para BI dos Orientadores - disponibiliza dados de:
    - Total de interações (leads atendidos pelo bot)
    - Total de leads integrados ao CRM
    - Taxa de integração
    - Leads por origem

    Returns:
        Métricas de integração CRM/WhatsApp
    """
    try:
        # Buscar todos os leads
        all_leads = await leads_repository.list_all(limit=10000)

        # Total de leads integrados ao CRM
        total_leads_crm = len(all_leads)

        # Leads que tiveram interação pelo WhatsApp
        leads_whatsapp = [l for l in all_leads if l.origem == "whatsapp"]
        total_interacoes_whatsapp = len(leads_whatsapp)

        # Calcular contagem de mensagens por lead
        total_mensagens = 0
        leads_com_conversas = 0

        for lead in all_leads:
            num_mensagens = len(lead.conversation_history) if lead.conversation_history else 0
            if num_mensagens > 0:
                leads_com_conversas += 1
                total_mensagens += num_mensagens

        # Taxa de integração
        taxa_integracao = (total_leads_crm / total_interacoes_whatsapp * 100) if total_interacoes_whatsapp > 0 else 0

        # Média de mensagens por lead
        media_mensagens = total_mensagens / total_leads_crm if total_leads_crm > 0 else 0

        # Distribuição por origem
        origens = {}
        for lead in all_leads:
            origem = str(lead.origem)
            origens[origem] = origens.get(origem, 0) + 1

        return {
            "total_interacoes_whatsapp": total_interacoes_whatsapp,
            "total_leads_integrados_crm": total_leads_crm,
            "taxa_integracao_percentual": round(taxa_integracao, 2),
            "leads_com_conversas_ativas": leads_com_conversas,
            "total_mensagens_trocadas": total_mensagens,
            "media_mensagens_por_lead": round(media_mensagens, 2),
            "distribuicao_por_origem": origens,
            "resumo": {
                "descricao": "Métricas de integração WhatsApp -> CRM",
                "periodo": "Todos os tempos",
                "atualizado_em": "tempo_real"
            }
        }

    except Exception as e:
        logger.error(f"Erro ao buscar métricas de integração: {e}")
        raise
