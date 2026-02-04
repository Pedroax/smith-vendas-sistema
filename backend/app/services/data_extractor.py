"""
Serviço de Extração de Dados de Qualificação
Usa GPT-4 para extrair dados estruturados do histórico de conversa
"""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from loguru import logger

from app.config import settings
from app.models.lead import Lead, QualificationData


class ExtractedData(BaseModel):
    """Dados extraídos da conversa"""
    # CONTATO (prioridade máxima - coletar PRIMEIRO)
    nome: Optional[str] = Field(None, description="Nome completo do lead (não apelido). Ex: 'Pedro Silva', 'João'")
    email: Optional[str] = Field(None, description="Email do lead")
    empresa: Optional[str] = Field(None, description="Nome da empresa")
    setor: Optional[str] = Field(None, description="Setor/nicho do negócio (e-commerce, SaaS, educação, etc)")

    # QUALIFICAÇÃO DIRETA (coletar DEPOIS do contato)
    faturamento_anual: Optional[float] = Field(None, description="Faturamento anual da empresa em R$. Ex: '2M' = 2000000, '700k' = 700000")
    is_decision_maker: Optional[bool] = Field(None, description="Se é tomador de decisão de compras/tecnologia")
    urgency: Optional[str] = Field(None, description="Urgência para implementar: 'imediato', '1-3_meses', '3-6_meses', 'sem_urgencia'")

    # ESCOLHA DO LEAD (após qualificado)
    wants_roi: Optional[bool] = Field(None, description="Lead escolheu ver análise de ROI (opção 2)")
    wants_meeting: Optional[bool] = Field(None, description="Lead escolheu agendar reunião (opção 1)")

    # DADOS OPERACIONAIS PARA ROI (só coletar se wants_roi = True)
    atendimentos_por_dia: Optional[int] = Field(None, description="Número de leads/atendimentos por dia")
    tempo_por_atendimento: Optional[int] = Field(None, description="Tempo médio por atendimento em minutos")
    funcionarios_atendimento: Optional[int] = Field(None, description="Número de funcionários na equipe de atendimento/vendas")
    ticket_medio: Optional[float] = Field(None, description="Ticket médio de venda em R$")


class DataExtractor:
    """Extrator de dados de qualificação usando LLM"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Baixa temperatura para extração precisa
            api_key=settings.openai_api_key
        )

    def extract_qualification_data(self, lead: Lead) -> Optional[QualificationData]:
        """
        Extrai dados de qualificação do histórico de conversa

        Args:
            lead: Lead com histórico de mensagens

        Returns:
            QualificationData ou None se não conseguir extrair
        """
        if not lead.conversation_history or len(lead.conversation_history) < 2:
            logger.debug(f"Histórico muito curto para {lead.nome}, pulando extração")
            return None

        try:
            # Construir histórico formatado
            conversation_text = self._format_conversation(lead)

            # System prompt para extração
            system_prompt = """Você é um extrator de dados. Analise a conversa e extraia APENAS os dados EXPLICITAMENTE mencionados pelo lead.

REGRAS CRÍTICAS:
- Se o lead NÃO mencionou um dado, retorne null (não invente)
- Extraia APENAS números e informações CLARAS
- Não faça suposições ou estimativas
- Converta valores para números quando necessário

EXEMPLOS DE CONTATO (PRIORIDADE):

Lead: "pedro" ou "Me chamo João Silva" ou "Meu nome é Maria"
→ nome: "pedro" ou "João Silva" ou "Maria"

Lead: "Meu email é pedro@empresa.com" ou "pode mandar no contato@acme.com.br"
→ email: "pedro@empresa.com" ou "contato@acme.com.br"

Lead: "Trabalho na Acme Corp" ou "Sou da TechStart"
→ empresa: "Acme Corp" ou "TechStart"

Lead: "Somos do varejo" ou "Trabalho com e-commerce" ou "SaaS B2B"
→ setor: "varejo" ou "e-commerce" ou "SaaS B2B"

EXEMPLOS DE QUALIFICAÇÃO DIRETA:

Lead: "Faturamos 2M por ano" ou "uns 700k" ou "R$ 1.5 milhão/ano"
→ faturamento_anual: 2000000.0 ou 700000.0 ou 1500000.0
(SEMPRE converter para número: M = 1.000.000, k = 1.000)

Lead: "Sim, sou eu quem decide" ou "Eu sou o dono" ou "Sou o decisor"
→ is_decision_maker: true

Lead: "Não, preciso falar com meu sócio" ou "Participo da decisão mas não sou o único"
→ is_decision_maker: false

Lead: "Já, tá urgente" ou "Esse mês" ou "Imediato"
→ urgency: "imediato"

Lead: "Daqui 2-3 meses" ou "Em uns 60 dias"
→ urgency: "1-3_meses"

Lead: "Talvez semestre que vem" ou "Daqui uns 4-5 meses"
→ urgency: "3-6_meses"

Lead: "Sem pressa" ou "Só quero ver"
→ urgency: "sem_urgencia"

EXEMPLOS DE ESCOLHA:

Lead: "1" ou "opção 1" ou "quero agendar reunião"
→ wants_meeting: true

Lead: "2" ou "opção 2" ou "quero ver o ROI"
→ wants_roi: true

EXEMPLOS DE DADOS OPERACIONAIS (PARA ROI):

Lead: "Recebo uns 50 leads por dia" ou "200 atendimentos/dia"
→ atendimentos_por_dia: 50 ou 200

Lead: "Demoro tipo 2 horas pra responder" ou "20 minutos por atendimento"
→ tempo_por_atendimento: 120 ou 20 (SEMPRE em minutos)

Lead: "Somos 3 na equipe" ou "20 pessoas" ou "Tenho 10 funcionários"
→ funcionarios_atendimento: 3 ou 20 ou 10

Lead: "Ticket médio de R$ 500" ou "Cada venda é 7k" ou "6k"
→ ticket_medio: 500.0 ou 7000.0 ou 6000.0

Se NÃO mencionou, retorne null."""

            # Mensagem com a conversa
            user_prompt = f"""Analise esta conversa e extraia os dados:

{conversation_text}

Retorne APENAS os dados que foram EXPLICITAMENTE mencionados. Se não foi mencionado, retorne null."""

            # Invocar LLM com structured output
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Usar with_structured_output para forçar formato Pydantic
            structured_llm = self.llm.with_structured_output(ExtractedData)
            extracted = structured_llm.invoke(messages)

            # DEBUG: Mostrar o que foi extraído
            logger.info(f"🔍 EXTRAÇÃO DEBUG para {lead.nome}:")
            logger.info(f"   Nome extraído: {extracted.nome}")
            logger.info(f"   Email extraído: {extracted.email}")
            logger.info(f"   Empresa extraída: {extracted.empresa}")
            logger.info(f"   Setor extraído: {extracted.setor}")

            # Converter para QualificationData
            qual_data = QualificationData(
                # Qualificação direta
                faturamento_anual=extracted.faturamento_anual,
                is_decision_maker=extracted.is_decision_maker,
                urgency=extracted.urgency,
                setor=extracted.setor,
                # Escolha
                wants_roi=extracted.wants_roi,
                wants_meeting=extracted.wants_meeting,
                # Dados operacionais para ROI
                atendimentos_por_dia=extracted.atendimentos_por_dia,
                tempo_por_atendimento=extracted.tempo_por_atendimento,
                funcionarios_atendimento=extracted.funcionarios_atendimento,
                ticket_medio=extracted.ticket_medio
            )

            # Atualizar nome, empresa, email e setor no lead se extraiu
            if extracted.nome and (not lead.nome or lead.nome.lower() in ['lead landing', 'lead', 'landing']):
                lead.nome = extracted.nome
                logger.info(f"📝 Nome do lead atualizado para: {extracted.nome}")

            if extracted.empresa and not lead.empresa:
                lead.empresa = extracted.empresa

            if extracted.email and not lead.email:
                lead.email = extracted.email

            # Log dos dados extraídos
            dados_qualificacao = sum([
                1 for field in ['faturamento_anual', 'is_decision_maker', 'urgency']
                if getattr(qual_data, field) is not None
            ])

            dados_roi = sum([
                1 for field in ['atendimentos_por_dia', 'tempo_por_atendimento', 'funcionarios_atendimento', 'ticket_medio']
                if getattr(qual_data, field) is not None
            ])

            logger.info(f"📊 Extraídos de {lead.nome}: {dados_qualificacao}/3 qualif, {dados_roi}/4 ROI")

            return qual_data

        except Exception as e:
            logger.error(f"Erro ao extrair dados de {lead.nome}: {e}")
            return None

    def _format_conversation(self, lead: Lead) -> str:
        """Formata histórico de conversa para análise"""
        lines = []
        for msg in lead.conversation_history:
            role = "Lead" if msg.role == "user" else "Smith"
            lines.append(f"{role}: {msg.content}")

        return "\n".join(lines)

    def has_qualification_data(self, qual_data: Optional[QualificationData]) -> bool:
        """
        Verifica se tem dados mínimos para qualificar o lead

        Critério: faturamento_anual E is_decision_maker

        Args:
            qual_data: Dados de qualificação

        Returns:
            True se pode qualificar
        """
        if not qual_data:
            return False

        return (qual_data.faturamento_anual is not None and
                qual_data.is_decision_maker is not None)

    def has_minimum_data(self, qual_data: Optional[QualificationData]) -> bool:
        """
        Verifica se tem dados mínimos para gerar ROI

        Critério: Pelo menos 3 dos 4 dados principais
        - atendimentos_por_dia
        - tempo_por_atendimento
        - funcionarios_atendimento
        - ticket_medio

        Args:
            qual_data: Dados de qualificação

        Returns:
            True se tem dados suficientes para ROI
        """
        if not qual_data:
            return False

        dados_principais = [
            qual_data.atendimentos_por_dia,
            qual_data.tempo_por_atendimento,
            qual_data.funcionarios_atendimento,
            qual_data.ticket_medio
        ]

        dados_preenchidos = sum(1 for dado in dados_principais if dado is not None)

        return dados_preenchidos >= 3


# Instância global
data_extractor = DataExtractor()
