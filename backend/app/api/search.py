"""
API de Busca Global
Busca unificada em leads, projetos, interações, agendamentos
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Query
from loguru import logger

from app.config import settings

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(default=20, le=50)
):
    """
    Busca global no sistema

    Busca em:
    - Leads (nome, email, telefone, empresa)
    - Projetos (nome, cliente_nome)
    - Interações (assunto, conteúdo, lead_nome)
    - Agendamentos (titulo, lead_nome)
    """
    supabase = settings.supabase
    results: Dict[str, List[Dict[str, Any]]] = {
        "leads": [],
        "projects": [],
        "interactions": [],
        "appointments": []
    }

    search_term = f"%{q.lower()}%"

    try:
        # Search Leads
        leads_result = (
            supabase.table("leads")
            .select("id, nome, email, telefone, empresa, status, temperatura")
            .or_(f"nome.ilike.{search_term},email.ilike.{search_term},telefone.ilike.{search_term},empresa.ilike.{search_term}")
            .limit(limit)
            .execute()
        )

        if leads_result.data:
            results["leads"] = [
                {
                    **lead,
                    "type": "lead",
                    "title": lead["nome"],
                    "subtitle": " • ".join(filter(None, [lead.get('empresa'), lead.get('email')])),
                    "link": f"/crm?lead={lead['id']}"
                }
                for lead in leads_result.data
            ]

        # Search Projects
        try:
            projects_result = (
                supabase.table("portal_projects")
                .select("id, nome, cliente_id, cliente_nome, status, valor_total")
                .or_(f"nome.ilike.{search_term},cliente_nome.ilike.{search_term}")
                .limit(limit)
                .execute()
            )

            if projects_result.data:
                results["projects"] = [
                    {
                        **project,
                        "type": "project",
                        "title": project["nome"],
                        "subtitle": f"Cliente: {project.get('cliente_nome', 'N/A')} • Status: {project.get('status', 'N/A')}",
                        "link": f"/admin-portal/projects/{project['id']}"
                    }
                    for project in projects_result.data
                ]
        except Exception as e:
            logger.warning(f"Erro ao buscar projetos: {e}")

        # Search Interactions
        try:
            interactions_result = (
                supabase.table("interactions")
                .select("id, lead_id, lead_nome, tipo, assunto, conteudo, created_at")
                .or_(f"assunto.ilike.{search_term},conteudo.ilike.{search_term},lead_nome.ilike.{search_term}")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            if interactions_result.data:
                results["interactions"] = [
                    {
                        **interaction,
                        "type": "interaction",
                        "title": interaction.get("assunto") or f"Interação ({interaction['tipo']})",
                        "subtitle": f"Lead: {interaction.get('lead_nome', 'N/A')} • {interaction.get('tipo', '')}",
                        "link": f"/conversas?lead={interaction['lead_id']}"
                    }
                    for interaction in interactions_result.data
                ]
        except Exception as e:
            logger.warning(f"Erro ao buscar interações: {e}")

        # Search Appointments
        try:
            appointments_result = (
                supabase.table("appointments")
                .select("id, lead_id, lead_nome, tipo, titulo, data_hora, status")
                .or_(f"titulo.ilike.{search_term},lead_nome.ilike.{search_term}")
                .order("data_hora", desc=False)
                .limit(limit)
                .execute()
            )

            if appointments_result.data:
                results["appointments"] = [
                    {
                        **appointment,
                        "type": "appointment",
                        "title": appointment["titulo"],
                        "subtitle": f"Lead: {appointment.get('lead_nome', 'N/A')} • {appointment.get('tipo', '')}",
                        "link": f"/agendamentos?appointment={appointment['id']}"
                    }
                    for appointment in appointments_result.data
                ]
        except Exception as e:
            logger.warning(f"Erro ao buscar agendamentos: {e}")

        # Calculate total count
        total_count = sum(len(results[key]) for key in results)

        return {
            "query": q,
            "total": total_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"Erro na busca global: {e}")
        return {
            "query": q,
            "total": 0,
            "results": results,
            "error": str(e)
        }
