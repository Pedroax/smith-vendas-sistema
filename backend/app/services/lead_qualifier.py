"""
Serviço de Qualificação de Leads
Sistema de scoring e decisão de qualificação (GATE)
"""
from typing import Tuple
from app.models.lead import Lead, QualificationData, LeadStatus
from loguru import logger


class LeadQualifier:
    """
    Qualificador de leads usando qualificação direta

    CRITÉRIOS DE QUALIFICAÇÃO (SIMPLIFICADOS):
    - Faturamento anual >= R$ 600.000/ano (R$ 50K/mês)
    - É tomador de decisão (is_decision_maker = True)

    Critérios opcionais para scoring:
    - Urgência (imediato é melhor)
    """

    def __init__(self):
        # Threshold de qualificação CRÍTICO
        self.min_faturamento_anual = 600000  # R$ 600.000/ano (50K × 12 meses)

    def calculate_lead_score(self, qualification_data: QualificationData) -> int:
        """
        Calcula score de 0-100 baseado nos dados de qualificação direta

        DISTRIBUIÇÃO DE PONTOS:
        - Faturamento anual (50 pontos): >= 600K = qualificado
        - É decisor (30 pontos): True = qualificado
        - Urgência (20 pontos): Imediato = melhor

        Args:
            qualification_data: Dados coletados

        Returns:
            Score de 0 a 100
        """
        score = 0

        # 1. FATURAMENTO ANUAL (50 pontos)
        if qualification_data.faturamento_anual:
            if qualification_data.faturamento_anual >= 5000000:  # >= 5M
                score += 50
            elif qualification_data.faturamento_anual >= 2000000:  # >= 2M
                score += 45
            elif qualification_data.faturamento_anual >= 1000000:  # >= 1M
                score += 40
            elif qualification_data.faturamento_anual >= 600000:  # >= 600K (mínimo)
                score += 35
            else:
                score += 10  # Abaixo do mínimo

        # 2. É DECISOR (30 pontos)
        if qualification_data.is_decision_maker is not None:
            if qualification_data.is_decision_maker:
                score += 30  # É decisor
            else:
                score += 5  # Não é decisor (mas pode influenciar)

        # 3. URGÊNCIA (20 pontos)
        if qualification_data.urgency:
            urgency = qualification_data.urgency.lower()
            if urgency == "imediato":
                score += 20
            elif urgency == "1-3_meses":
                score += 15
            elif urgency == "3-6_meses":
                score += 10
            else:  # sem_urgencia
                score += 3

        return min(score, 100)  # Cap em 100

    def calculate_annual_revenue(self, qualification_data: QualificationData) -> float:
        """
        Calcula receita anual estimada baseada nos dados operacionais

        Fórmula:
        Receita Anual = atendimentos_por_dia × ticket_medio × taxa_conversao × dias_uteis_ano

        Args:
            qualification_data: Dados coletados

        Returns:
            Receita anual estimada em R$
        """
        if not qualification_data.atendimentos_por_dia or not qualification_data.ticket_medio:
            return 0.0

        # Assumir taxa de conversão conservadora de 20%
        taxa_conversao = 0.20

        # 252 dias úteis por ano (aproximadamente)
        dias_uteis_ano = 252

        receita_anual = (
            qualification_data.atendimentos_por_dia
            * qualification_data.ticket_medio
            * taxa_conversao
            * dias_uteis_ano
        )

        logger.info(
            f"💰 Receita anual calculada: R$ {receita_anual:,.2f} "
            f"({qualification_data.atendimentos_por_dia} leads/dia × "
            f"R$ {qualification_data.ticket_medio:,.2f} ticket × "
            f"{taxa_conversao*100}% conversão × {dias_uteis_ano} dias)"
        )

        return receita_anual

    def is_qualified(self, lead: Lead) -> Tuple[bool, str, int]:
        """
        Decide se o lead é qualificado (GATE)

        CRITÉRIOS MÍNIMOS (SIMPLIFICADOS):
        - Faturamento anual >= R$ 600.000/ano (R$ 50K/mês)
        - É tomador de decisão (is_decision_maker = True)

        Args:
            lead: Lead com dados de qualificação

        Returns:
            Tupla (qualificado: bool, motivo: str, score: int)
        """
        if not lead.qualification_data:
            return False, "Dados de qualificação incompletos", 0

        qual_data = lead.qualification_data

        # Calcular score
        score = self.calculate_lead_score(qual_data)

        # Verificar critérios mínimos
        reasons_disqualified = []

        # CRITÉRIO 1: FATURAMENTO MÍNIMO (CRÍTICO)
        if not qual_data.faturamento_anual:
            reasons_disqualified.append("Faturamento anual não informado")
        elif qual_data.faturamento_anual < self.min_faturamento_anual:
            faturamento_mensal = qual_data.faturamento_anual / 12
            reasons_disqualified.append(
                f"Faturamento anual (R$ {qual_data.faturamento_anual:,.0f}/ano = R$ {faturamento_mensal:,.0f}/mês) "
                f"abaixo do mínimo (R$ {self.min_faturamento_anual:,.0f}/ano = R$ 50.000/mês)"
            )

        # CRITÉRIO 2: É DECISOR (CRÍTICO)
        if qual_data.is_decision_maker is None:
            reasons_disqualified.append("Não informou se é decisor")
        elif not qual_data.is_decision_maker:
            reasons_disqualified.append("Não é tomador de decisão")

        # Decisão final
        if reasons_disqualified:
            reason = "; ".join(reasons_disqualified)
            logger.warning(f"❌ Lead {lead.nome} NÃO qualificado: {reason} (Score: {score})")
            return False, reason, score
        else:
            faturamento_mensal = qual_data.faturamento_anual / 12
            urgency_text = qual_data.urgency or "não informada"
            reason = (
                f"Lead qualificado com score {score}/100, "
                f"faturamento R$ {qual_data.faturamento_anual:,.0f}/ano (R$ {faturamento_mensal:,.0f}/mês), "
                f"é decisor, urgência: {urgency_text}"
            )
            logger.success(f"✅ Lead {lead.nome} QUALIFICADO! Score: {score}, Faturamento: R$ {faturamento_mensal:,.0f}/mês")
            return True, reason, score

    def get_disqualification_message(self, lead: Lead, reason: str) -> str:
        """
        Gera mensagem educada de desqualificação

        Args:
            lead: Lead desqualificado
            reason: Motivo da desqualificação

        Returns:
            Mensagem para enviar ao lead
        """
        messages = {
            "faturamento": f"""Oi {lead.nome}!

Muito obrigado pela conversa e pelas informações que compartilhou!

Analisando o faturamento atual da {lead.empresa or 'sua empresa'}, nossa solução ainda não seria o melhor investimento neste momento.

A gente trabalha melhor com empresas que já faturam a partir de R$ 600mil/ano (R$ 50k/mês), onde o ROI da automação compensa mais rápido.

Mas fica tranquilo! Vou guardar seu contato aqui. Quando vocês crescerem e escalar, a gente retoma essa conversa! 😊

Sucesso aí! 🚀""",

            "budget": f"""Olá {lead.nome}!

Agradeço muito o seu tempo em conversar comigo.

Pela nossa conversa, percebi que neste momento nossa solução pode não ser a mais adequada para o estágio atual da {lead.empresa or 'sua empresa'}.

Nossa plataforma é desenhada para operações que já têm um volume considerável de atendimentos e estão buscando escalar ainda mais.

Mas fique tranquilo! Vou deixar seu contato aqui. Quando sua operação crescer, a gente retoma essa conversa! 😊

Sucesso aí! 🚀""",

            "volume": f"""Oi {lead.nome}!

Foi ótimo conhecer mais sobre a {lead.empresa or 'sua empresa'}!

Pelo que você me passou, vejo que vocês ainda estão em uma fase onde o atendimento manual consegue dar conta tranquilamente.

Nossa solução tem melhor custo-benefício para empresas que já têm um volume maior de conversas diárias.

Mas vou guardar seu contato aqui! Quando vocês crescerem e sentirem necessidade de automação, é só me chamar!

Sucesso! 💪""",

            "timing": f"""Oi {lead.nome}!

Entendi que vocês não têm urgência para implementar uma solução agora, certo?

Tudo bem! Respeito totalmente o timing de vocês.

Vou deixar aqui nosso contato caso precisem no futuro:
📱 WhatsApp: {lead.telefone}
🌐 automatexia.com.br

Quando estiverem prontos, é só chamar! Estaremos aqui. 😊""",

            "default": f"""Olá {lead.nome}!

Muito obrigado pelo seu tempo e pelas informações que compartilhou comigo!

Analisando o momento atual da {lead.empresa or 'sua empresa'}, acredito que nossa solução ainda não seria o melhor fit neste momento.

Mas isso pode mudar! Vou deixar seu contato guardado e, se fizer sentido no futuro, a gente retoma essa conversa.

Desejo muito sucesso para vocês! 🚀

Abs,
Smith"""
        }

        # Escolher mensagem baseada no motivo
        if "faturamento" in reason.lower():
            return messages["faturamento"]
        elif "decisor" in reason.lower() or "decisão" in reason.lower():
            return messages["default"]
        elif "orçamento" in reason.lower() or "budget" in reason.lower():
            return messages["budget"]
        elif "volume" in reason.lower():
            return messages["volume"]
        elif "timing" in reason.lower():
            return messages["timing"]
        else:
            return messages["default"]


# Instância global
lead_qualifier = LeadQualifier()
