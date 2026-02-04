"""
Serviço de Qualificação de Leads com IA
Usa o Agente Smith para analisar e qualificar leads automaticamente
"""
from typing import Dict, Any
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import re


class LeadQualificationService:
    """
    Serviço que usa IA para qualificar leads automaticamente
    Critérios: Faturamento + Cargo + Contexto

    PRODUTO: Sistema de automação de atendimento
    - Implementação: R$ 6-7k
    - Recorrência: R$ 800/mês
    - Custo 1º ano: ~R$ 16.600
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=settings.openai_api_key
        )

        # Prompt de qualificação focado em faturamento + cargo
        self.qualification_prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um especialista em qualificação de leads B2B para um sistema de automação de atendimento.

**CONTEXTO DO PRODUTO:**
- Implementação: R$ 6-7 mil
- Recorrência: R$ 800/mês
- Custo 1º ano: ~R$ 16.600

**CRITÉRIOS DE QUALIFICAÇÃO:**

1. **FATURAMENTO ANUAL (peso 70%):**
   - Menos de R$ 300k/ano = ❌ REJEITAR (score 0-20)
     Razão: Investimento de R$ 16k seria 5%+ do faturamento, inviável

   - R$ 300k a R$ 500k/ano = ⚠️ BORDERLINE (score 40-60)
     Razão: Investimento é 3-5% do faturamento, apertado mas possível
     ATENÇÃO: Só qualifica se cargo for CEO/Diretor/Sócio

   - R$ 500k a R$ 1M/ano = ✅ BOM (score 70-85)
     Razão: Investimento é 1,6-3,3% do faturamento, saudável

   - Acima de R$ 1M/ano = 🔥 EXCELENTE (score 90-100)
     Razão: Investimento é <1,6% do faturamento, decisão fácil

2. **CARGO (peso 30%):**
   - CEO, Fundador, Sócio, Dono = ✅ Tomador de decisão (+20 pts)
   - Diretor = ✅ Alta influência (+15 pts)
   - Gerente = ⚠️ Média influência (+10 pts)
   - Coordenador = ⚠️ Baixa influência (+5 pts)
   - Analista, Assistente = ❌ Sem poder (-10 pts)

**REGRAS CRÍTICAS:**
- Faturamento < R$ 300k = SEMPRE rejeitar, independente do cargo
- Faturamento R$ 300-500k SEM cargo CEO/Diretor/Sócio = REJEITAR
- Faturamento > R$ 500k com cargo decisor = SEMPRE qualificar
- Sem informação de faturamento = Usar análise contextual (empresa, mensagem)

**ANÁLISE CONTEXTUAL (se faturamento não informado):**
- Empresa grande/conhecida = Assumir > R$ 1M
- Clínica/consultório médico = Assumir R$ 500k-1M
- Microempresa/MEI/autônomo = Assumir < R$ 300k

Retorne APENAS um JSON válido no formato:
{{
    "is_qualified": true/false,
    "score": 0-100,
    "reasoning": "Explicação objetiva: Por que qualificou/rejeitou baseado em faturamento + cargo",
    "next_action": "Ação específica (ex: 'Ligar imediatamente', 'Enviar proposta', 'Descartado')",
    "faturamento_estimado": "Faixa estimada se não informado explicitamente"
}}"""),
            ("user", """Analise este lead:

Nome: {nome}
Email: {email}
Telefone: {telefone}
Empresa: {empresa}
Cargo: {cargo}
Faturamento Anual: {faturamento}
Mensagem/Contexto: {mensagem}

Retorne o JSON de qualificação.""")
        ])

    async def qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualifica um lead usando IA

        Args:
            lead_data: Dicionário com dados do lead
                - nome, email, telefone, empresa, cargo, mensagem
                - faturamento: "Menos de R$ 300k", "R$ 300k-500k", "R$ 500k-1M", "Acima de R$ 1M"

        Returns:
            Dict com is_qualified, score, reasoning, next_action, faturamento_estimado
        """
        try:
            logger.info(f"🤖 Qualificando lead: {lead_data.get('nome')}")

            # Preparar dados (garantir que não tem None)
            prepared_data = {
                "nome": lead_data.get("nome", "Não informado"),
                "email": lead_data.get("email", "Não informado"),
                "telefone": lead_data.get("telefone", "Não informado"),
                "empresa": lead_data.get("empresa", "Não informado"),
                "cargo": lead_data.get("cargo", "Não informado"),
                "faturamento": lead_data.get("faturamento", "Não informado"),
                "mensagem": lead_data.get("mensagem", "Não informado"),
            }

            # Criar chain
            chain = self.qualification_prompt | self.llm

            # Executar qualificação
            response = chain.invoke(prepared_data)

            # Parse resposta
            import json
            result_text = response.content.strip()

            # Limpar markdown se vier com ```json
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()

            result = json.loads(result_text)

            is_qualified = result.get("is_qualified", False)
            score = result.get("score", 0)

            logger.success(f"✅ Lead qualificado: {'APROVADO' if is_qualified else 'REJEITADO'} - Score {score}/100")

            return result

        except Exception as e:
            logger.error(f"❌ Erro ao qualificar lead: {e}")
            # Em caso de erro, tenta qualificação manual (sem IA)
            manual_result = self.qualify_lead_manual(lead_data)
            return manual_result

    def qualify_lead_manual(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualificação manual baseada em regras (fallback se IA falhar)
        """
        score = 0
        reasoning_parts = []

        faturamento_str = lead_data.get("faturamento", "").lower()
        cargo_str = lead_data.get("cargo", "").lower()

        # SCORE POR FATURAMENTO (70% do score)
        if "menos" in faturamento_str or "300" in faturamento_str and "menos" in faturamento_str:
            score += 10
            reasoning_parts.append("❌ Faturamento < R$ 300k (inviável)")
            is_qualified = False
        elif "300" in faturamento_str and "500" in faturamento_str:
            score += 50
            reasoning_parts.append("⚠️ Faturamento R$ 300-500k (borderline)")
            is_qualified = False  # Só qualifica se tiver cargo alto
        elif "500" in faturamento_str or ("500k" in faturamento_str and "1m" in faturamento_str):
            score += 75
            reasoning_parts.append("✅ Faturamento R$ 500k-1M (bom)")
            is_qualified = True
        elif "acima" in faturamento_str or "milhão" in faturamento_str or "milhões" in faturamento_str:
            score += 90
            reasoning_parts.append("🔥 Faturamento > R$ 1M (excelente)")
            is_qualified = True
        else:
            score += 30
            reasoning_parts.append("⚠️ Faturamento não informado")
            is_qualified = False

        # SCORE POR CARGO (30% do score)
        decision_makers = ["ceo", "fundador", "sócio", "socio", "dono", "proprietário", "proprietario", "owner"]
        directors = ["diretor", "diretora", "director"]
        managers = ["gerente"]

        if any(dm in cargo_str for dm in decision_makers):
            score += 20
            reasoning_parts.append("✅ Cargo: Tomador de decisão")
            # Se borderline + decisor = qualifica
            if "borderline" in reasoning_parts[0]:
                is_qualified = True
        elif any(d in cargo_str for d in directors):
            score += 15
            reasoning_parts.append("✅ Cargo: Diretor")
            if "borderline" in reasoning_parts[0]:
                is_qualified = True
        elif any(m in cargo_str for m in managers):
            score += 10
            reasoning_parts.append("⚠️ Cargo: Gerente")
        else:
            score += 0
            reasoning_parts.append("❌ Cargo sem poder de decisão")

        # Score final limitado a 100
        score = min(score, 100)

        return {
            "is_qualified": is_qualified,
            "score": score,
            "reasoning": " | ".join(reasoning_parts) + " (Qualificação manual - IA indisponível)",
            "next_action": "Ligar imediatamente" if score >= 80 else ("Enviar proposta" if is_qualified else "Descartado"),
            "faturamento_estimado": lead_data.get("faturamento", "Não informado")
        }

    async def batch_qualify_leads(self, leads_data: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Qualifica múltiplos leads de uma vez
        """
        results = []
        for lead_data in leads_data:
            result = await self.qualify_lead(lead_data)
            results.append({
                "lead": lead_data,
                "qualification": result
            })

        return results

    def calculate_manual_score(self, lead_data: Dict[str, Any]) -> int:
        """
        Cálculo de score manual sem IA (fallback)
        """
        score = 0

        # Email corporativo (+20)
        email = lead_data.get("email", "").lower()
        if email and "@" in email:
            domain = email.split("@")[1]
            if domain not in ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]:
                score += 20

        # Tem empresa (+20)
        if lead_data.get("empresa") and lead_data.get("empresa") != "Não informado":
            score += 20

        # Cargo de decisão (+30)
        cargo = lead_data.get("cargo", "").lower()
        decision_keywords = ["ceo", "diretor", "gerente", "dono", "proprietário", "sócio", "founder"]
        if any(keyword in cargo for keyword in decision_keywords):
            score += 30

        # Tem telefone (+10)
        if lead_data.get("telefone") and lead_data.get("telefone") != "Não informado":
            score += 10

        # Tem mensagem (+20)
        if lead_data.get("mensagem") and lead_data.get("mensagem") != "Não informado":
            score += 20

        return min(score, 100)
