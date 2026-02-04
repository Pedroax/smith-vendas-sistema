"""
Serviço de Analytics em Tempo Real
Calcula métricas e KPIs do funil de vendas
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from app.models.lead import Lead, LeadStatus, LeadTemperature
from app.repository.leads_repository import LeadsRepository
from loguru import logger


class AnalyticsService:
    """Serviço para análise de dados e métricas do CRM"""

    def __init__(self):
        self.repository = LeadsRepository()

    async def get_dashboard_metrics(self, periodo_dias: int = 30) -> Dict[str, Any]:
        """
        Retorna métricas principais do dashboard

        Args:
            periodo_dias: Número de dias para análise (default: 30)

        Returns:
            Dict com todas as métricas do dashboard
        """
        try:
            # Data de corte (timezone-aware)
            data_corte = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

            # Buscar todos os leads
            all_leads = await self.repository.list_all(limit=1000)

            # Filtrar por período
            leads_periodo = [
                lead for lead in all_leads
                if lead.created_at and lead.created_at >= data_corte
            ]

            # Calcular métricas
            metricas = {
                "resumo": await self._calcular_resumo(all_leads, leads_periodo),
                "funil": await self._calcular_funil(leads_periodo),
                "temperatura": await self._calcular_temperatura(all_leads),
                "tempo_medio": await self._calcular_tempo_medio(leads_periodo),
                "motivos_perda": await self._calcular_motivos_perda(leads_periodo),
                "timeline": await self._calcular_timeline(periodo_dias),
                "taxa_conversao": await self._calcular_taxa_conversao(leads_periodo),
            }

            logger.info(f"✅ Dashboard metrics calculadas para {len(leads_periodo)} leads")
            return metricas

        except Exception as e:
            logger.error(f"Erro ao calcular métricas do dashboard: {e}")
            return self._get_empty_metrics()

    async def _calcular_resumo(self, all_leads: List[Lead], leads_periodo: List[Lead]) -> Dict[str, Any]:
        """Calcula resumo geral de leads"""
        total_leads = len(all_leads)
        novos_periodo = len(leads_periodo)

        # Leads ativos (não perdidos)
        leads_ativos = [l for l in all_leads if str(l.status) != LeadStatus.PERDIDO.value]

        # Leads qualificados no período
        qualificados_periodo = [
            l for l in leads_periodo
            if str(l.status) in [LeadStatus.QUALIFICADO.value, LeadStatus.AGENDAMENTO_MARCADO.value, "qualificado", "agendamento_marcado"]
        ]

        # Valor total do pipeline (leads ativos)
        valor_pipeline = sum(l.valor_estimado or 0 for l in leads_ativos)

        # Crescimento vs período anterior
        if novos_periodo > 0:
            periodo_anterior_inicio = datetime.now(timezone.utc) - timedelta(days=60)
            periodo_anterior_fim = datetime.now(timezone.utc) - timedelta(days=30)
            leads_periodo_anterior = [
                l for l in all_leads
                if l.created_at and periodo_anterior_inicio <= l.created_at < periodo_anterior_fim
            ]
            crescimento = ((novos_periodo - len(leads_periodo_anterior)) / len(leads_periodo_anterior) * 100) if len(leads_periodo_anterior) > 0 else 100
        else:
            crescimento = 0

        return {
            "total_leads": total_leads,
            "leads_ativos": len(leads_ativos),
            "novos_ultimos_30d": novos_periodo,
            "qualificados_ultimos_30d": len(qualificados_periodo),
            "valor_pipeline": valor_pipeline,
            "crescimento_percentual": round(crescimento, 1),
        }

    async def _calcular_funil(self, leads: List[Lead]) -> Dict[str, Any]:
        """Calcula métricas do funil de conversão"""
        total = len(leads)
        if total == 0:
            return {
                "novo": {"count": 0, "percentual": 0},
                "contato_inicial": {"count": 0, "percentual": 0},
                "qualificando": {"count": 0, "percentual": 0},
                "qualificado": {"count": 0, "percentual": 0},
                "agendamento_marcado": {"count": 0, "percentual": 0},
                "perdido": {"count": 0, "percentual": 0},
            }

        # Contar por status
        status_count = {}
        for status in LeadStatus:
            count = len([l for l in leads if str(l.status) == status.value or str(l.status) == status.value.lower()])
            status_count[status.value] = {
                "count": count,
                "percentual": round((count / total) * 100, 1)
            }

        return status_count

    async def _calcular_temperatura(self, leads: List[Lead]) -> Dict[str, Any]:
        """Calcula distribuição por temperatura"""
        total = len([l for l in leads if str(l.status) != LeadStatus.PERDIDO.value])

        if total == 0:
            return {
                "quente": {"count": 0, "percentual": 0},
                "morno": {"count": 0, "percentual": 0},
                "frio": {"count": 0, "percentual": 0},
            }

        quente = len([l for l in leads if str(l.temperatura) == LeadTemperature.QUENTE.value and str(l.status) != LeadStatus.PERDIDO.value])
        morno = len([l for l in leads if str(l.temperatura) == LeadTemperature.MORNO.value and str(l.status) != LeadStatus.PERDIDO.value])
        frio = len([l for l in leads if str(l.temperatura) == LeadTemperature.FRIO.value and str(l.status) != LeadStatus.PERDIDO.value])

        return {
            "quente": {"count": quente, "percentual": round((quente / total) * 100, 1)},
            "morno": {"count": morno, "percentual": round((morno / total) * 100, 1)},
            "frio": {"count": frio, "percentual": round((frio / total) * 100, 1)},
        }

    async def _calcular_tempo_medio(self, leads: List[Lead]) -> Dict[str, float]:
        """Calcula tempo médio em cada estágio (em horas)"""
        # Por enquanto retorna valores estimados
        # TODO: Implementar tracking real de tempo por estágio
        return {
            "novo_para_contato": 0.5,  # 30min
            "contato_para_qualificacao": 2.0,  # 2h
            "qualificacao_completa": 4.0,  # 4h
            "qualificado_para_agendamento": 24.0,  # 24h
        }

    async def _calcular_motivos_perda(self, leads: List[Lead]) -> List[Dict[str, Any]]:
        """Agrupa e conta motivos de perda"""
        leads_perdidos = [l for l in leads if str(l.status) == LeadStatus.PERDIDO.value]

        if not leads_perdidos:
            return []

        # Agrupar por motivo (extrair do ai_summary se houver)
        motivos = {}
        sem_motivo = 0

        for lead in leads_perdidos:
            if lead.ai_summary:
                # Tentar extrair motivo do summary
                summary_lower = lead.ai_summary.lower()

                if "faturamento" in summary_lower or "receita" in summary_lower:
                    motivo = "Faturamento insuficiente"
                elif "decisor" in summary_lower or "decisão" in summary_lower:
                    motivo = "Não é decisor"
                elif "preço" in summary_lower or "caro" in summary_lower:
                    motivo = "Preço elevado"
                elif "timing" in summary_lower or "momento" in summary_lower:
                    motivo = "Timing inadequado"
                else:
                    motivo = "Não qualificado"
            else:
                sem_motivo += 1
                continue

            motivos[motivo] = motivos.get(motivo, 0) + 1

        if sem_motivo > 0:
            motivos["Sem motivo especificado"] = sem_motivo

        # Converter para lista ordenada
        resultado = [
            {"motivo": motivo, "count": count, "percentual": round((count / len(leads_perdidos)) * 100, 1)}
            for motivo, count in sorted(motivos.items(), key=lambda x: x[1], reverse=True)
        ]

        return resultado

    async def _calcular_timeline(self, periodo_dias: int) -> List[Dict[str, Any]]:
        """Calcula evolução de leads ao longo do tempo"""
        all_leads = await self.repository.list_all(limit=1000)
        data_inicio = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

        # Agrupar por dia
        timeline = {}

        for lead in all_leads:
            if not lead.created_at or lead.created_at < data_inicio:
                continue

            data_str = lead.created_at.strftime("%Y-%m-%d")

            if data_str not in timeline:
                timeline[data_str] = {
                    "data": data_str,
                    "novos": 0,
                    "qualificados": 0,
                    "perdidos": 0,
                }

            timeline[data_str]["novos"] += 1

            if str(lead.status) in [LeadStatus.QUALIFICADO.value, "qualificado"]:
                timeline[data_str]["qualificados"] += 1
            elif str(lead.status) == LeadStatus.PERDIDO.value:
                timeline[data_str]["perdidos"] += 1

        # Ordenar por data
        resultado = sorted(timeline.values(), key=lambda x: x["data"])

        return resultado

    async def _calcular_taxa_conversao(self, leads: List[Lead]) -> Dict[str, float]:
        """Calcula taxas de conversão entre etapas"""
        total = len(leads)
        if total == 0:
            return {
                "lead_para_contato": 0,
                "contato_para_qualificacao": 0,
                "qualificacao_para_qualificado": 0,
                "geral": 0,
            }

        # Contar leads em cada etapa
        com_contato = len([l for l in leads if str(l.status) not in [LeadStatus.NOVO.value, "novo"]])
        qualificando = len([l for l in leads if str(l.status) in [LeadStatus.QUALIFICANDO.value, "qualificando"]])
        qualificados = len([l for l in leads if str(l.status) in [LeadStatus.QUALIFICADO.value, LeadStatus.AGENDAMENTO_MARCADO.value, "qualificado", "agendamento_marcado"]])

        return {
            "lead_para_contato": round((com_contato / total) * 100, 1) if total > 0 else 0,
            "contato_para_qualificacao": round((qualificando / com_contato) * 100, 1) if com_contato > 0 else 0,
            "qualificacao_para_qualificado": round((qualificados / qualificando) * 100, 1) if qualificando > 0 else 0,
            "geral": round((qualificados / total) * 100, 1) if total > 0 else 0,
        }

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Retorna estrutura vazia de métricas em caso de erro"""
        return {
            "resumo": {
                "total_leads": 0,
                "leads_ativos": 0,
                "novos_ultimos_30d": 0,
                "qualificados_ultimos_30d": 0,
                "valor_pipeline": 0,
                "crescimento_percentual": 0,
            },
            "funil": {},
            "temperatura": {},
            "tempo_medio": {},
            "motivos_perda": [],
            "timeline": [],
            "taxa_conversao": {},
        }


# Instância global
analytics_service = AnalyticsService()
