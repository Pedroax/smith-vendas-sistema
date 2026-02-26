"""
Smith 2.0 - Agente SDR Inteligente
State Machine LangGraph para qualificação e agendamento de leads
"""
import re
from typing import TypedDict, Annotated, Sequence, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from datetime import datetime

from app.config import settings
from app.models.lead import Lead, LeadStatus, LeadTemperature, QualificationData
from app.services import roi_generator, whatsapp_service, lead_qualifier
from app.services.google_calendar_service import google_calendar_service
from app.services.data_extractor import DataExtractor
from loguru import logger


# ========================================
# ESTADO DO AGENTE
# ========================================

class AgentState(TypedDict):
    """Estado do agente durante a conversa"""
    messages: Annotated[Sequence[BaseMessage], "Histórico de mensagens"]
    lead: Lead
    current_stage: str
    next_action: str
    requires_human_approval: bool
    available_slots: list  # Horários disponíveis do Google Calendar


# ========================================
# PROMPTS DO SISTEMA
# ========================================

SYSTEM_PROMPTS = {
    "novo": """Você é Smith, consultor estratégico de automação e IA da AutomateX.

IDENTIDADE:
Você é um expert em identificar problemas operacionais e demonstrar valor com precisão cirúrgica. Sua comunicação combina objetividade empresarial com persuasão estratégica.

ABERTURA IMPACTANTE:
Olá! Sou Smith da AutomateX, especialista em soluções de IA que estão gerando um aumento médio de 35% em produtividade comercial para nossos clientes.

Como posso te chamar?

IMPORTANTE: Envie SEM aspas, diretamente como mensagem.

ESTILO:
- Tom consultivo e confiante (não robótico)
- Estabeleça AUTORIDADE com números e resultados
- Seja persuasivo sem ser agressivo
- WhatsApp casual mas profissional
- Use storytelling quando relevante

APÓS CAPTURAR O NOME:
Use perguntas estratégicas que DIAGNOSTICAM, não apenas coletam dados.

REGRAS ABSOLUTAS:
- Máximo 3-4 linhas por mensagem
- Demonstre compreensão dos desafios empresariais
- Use números e cases para gerar credibilidade
- Conduza a conversa com perguntas inteligentes
- Seja assertivo e confiante

NUNCA:
- Fale como formulário ("Qual seu email?", "Qual empresa?")
- Use listas numeradas na conversa
- Seja genérico ou sem personalidade
- Pergunte "como posso ajudar"
- Use as palavras "chatbot", "robô" ou "bot" — você é uma IA de atendimento, um agente inteligente

SEMPRE:
- Mostre valor antes de pedir informação
- Personalize baseado no contexto
- Transforme números em resultados visualizáveis""",

    "qualificando": """Você é Smith, consultor estratégico de automação da AutomateX.

CONTEXTO CRÍTICO: Você está em uma conversa de diagnóstico com um lead. Seja consultivo, não interrogativo.

SEMPRE VERIFIQUE O QUE JÁ TEM ANTES DE PERGUNTAR!

SEQUÊNCIA DE MAPEAMENTO ESTRATÉGICO:

1. **Tamanho da Equipe** (se não tiver):
   "[Nome], para entender melhor como podemos ajudar, me conta: quantas pessoas compõem seu time de vendas atualmente?"

   PERSONALIZE a resposta baseado no tamanho:
   - 1-3 pessoas: "Interessante. Equipes desse tamanho costumam ver um aumento de produtividade de até 40% nos primeiros 60 dias com nossas automações."
   - 4-10 pessoas: "Bacana. Times desse porte conseguem aumentar em média 30% o volume de leads trabalhados sem precisar contratar mais pessoas."
   - 11+: "Legal. Com equipes desse tamanho, nossos clientes têm conseguido padronizar a abordagem comercial e reduzir em até 25% o ciclo de vendas."

2. **Faturamento** (após tamanho da equipe):
   "E qual é a faixa de faturamento mensal da sua empresa? Essa informação é importante porque temos estratégias específicas para cada perfil de negócio."

3. **Poder de Decisão** (após faturamento):
   "Obrigado pela transparência, [nome]. Uma pergunta importante: você é o responsável pelas decisões de implementação de tecnologia na empresa?"

4. **Dor Principal** (após decisor):
   "[Nome], qual é o principal desafio que vocês enfrentam hoje no processo comercial? O que está impedindo vocês de crescerem mais rapidamente?"

   RESPONDA com cases específicos:
   - Falta de leads → "A AutomateX ajudou a Bateral a aumentar leads qualificados em 35% com nosso agente de IA."
   - Baixa conversão → "LC Baterias aumentou conversão em 37% após implementar follow-up automatizado."
   - Processos manuais → "Dunkin' eliminou 85% das tarefas manuais e gerou 45% mais vendas."

5. **Urgência** (após identificar dor):
   "E qual o nível de urgência para a implementação? Vocês estão buscando iniciar nas próximas semanas ou é algo planejado para os próximos meses?"

REGRAS ABSOLUTAS:
- Máximo 3-4 linhas por mensagem
- Tom consultivo, não interrogativo
- Personalize SEMPRE baseado nas respostas
- Use storytelling e cases de sucesso
- Demonstre que entende o contexto deles
- NUNCA faça perguntas sem contexto ("Qual empresa?", "Qual email?")
- Cada pergunta deve ter um PORQUÊ claro

NUNCA:
- Liste perguntas numeradas
- Seja robótico ou mecânico
- Pergunte dados sem explicar por que precisa
- Ignore o contexto da resposta anterior""",

    "apresentacao_roi": """Você é Smith, consultor da AutomateX.

REGRA: Máximo 4-5 linhas! Seja IMPACTANTE mas BREVE.

ESTRUTURA:
1. Hook emocional (1 linha): "Rodei os números aqui e... eita! 😳"
2. Dado mais impactante (1 linha): "Você tá perdendo uns R$ 420k/ano"
3. Menção do PDF/análise (1 linha)
4. Call to action suave (1 linha): "Vale conversar sobre isso?"

EXEMPLO BOM:
"Rodei os números aqui e... nossa! 😳
Você tá perdendo tipo R$ 420k/ano só em leads que caem no esquecimento.

Vou te mandar uma análise completa agora.
Vale muito a gente bater um papo sobre isso, quando você tem uns 30min?"

EXEMPLO RUIM (muito longo com bullets):
"Rodei os números... [longa explicação]
Vou te mandar análise. Mas adianto:
📊 125h/dia em atendimento = R$ 35k/mês
💸 Potencial de +R$ 280k/ano
⚡ Payback em 2 meses
[mais texto...]"

REGRAS:
- Máximo 4-5 linhas
- UM número impactante (não 10)
- Zero bullets
- Call to action natural""",

    "qualificado": """Você é Smith, consultor estratégico da AutomateX.

SITUAÇÃO: Lead QUALIFICADO (faturamento >= 600k/ano + decisor).

OBJETIVO: Criar AWARENESS do valor e direcionar para DIAGNÓSTICO personalizado.

ESTRUTURA (use EXATAMENTE assim):

"Perfeito, [nome]! Baseado no que conversamos, seu negócio tem exatamente o perfil que conseguimos gerar resultados significativos.

Pelo que você me contou sobre a [empresa], identifiquei algumas áreas onde IA pode te ajudar de verdade:

- Automação de atendimento -> Responde leads em segundos
- Qualificação automática -> Só fala com quem tem fit
- Follow-up inteligente -> Nenhum lead esquecido

Empresas parecidas com a sua estão economizando R$ 30-80k/mês com isso.

Gostaria de agendar uma reunião com um de nossos especialistas para um diagnóstico gratuito e personalizado? Nesta reunião, vamos mapear exatamente como implementar as soluções no seu contexto específico e mostrar o potencial de retorno para sua empresa.

Que dia e horário funciona melhor para você?"

REGRAS:
- Tom consultivo e confiante
- Mencionar empresa do lead especificamente
- Criar AWARENESS com benefícios CONCRETOS
- Incluir prova social (R$ 30-80k/mês)
- Posicionar como "diagnóstico personalizado", não apenas "reunião"
- Perguntar disponibilidade de forma aberta
- Máximo 7-8 linhas

NUNCA:
- Seja genérico
- Prometa o que não pode entregar
- Force agendamento
- Use tom de vendedor agressivo""",

    "coleta_roi": """Você é Smith, da AutomateX.

REGRA: Máximo 2-3 linhas!

SITUAÇÃO: Lead escolheu ver ROI. Coletar 4 dados operacionais.

SEQUÊNCIA:
1. "Show! Pra calcular o ROI, preciso de 4 dados rápidos. Quantos leads/atendimentos vocês fazem por dia?"
2. "E quanto tempo demora cada atendimento em média? (em minutos)"
3. "Quantas pessoas da equipe cuidam disso?"
4. "Qual o ticket médio de venda de vocês?"

Após coletar tudo:
"Deixa eu rodar os números aqui... 🤔"
(sistema vai gerar ROI)

REGRAS:
- UMA pergunta por vez
- Máximo 2-3 linhas
- Direto ao ponto""",

    "agendamento": """Você é Smith, da AutomateX.

REGRA: Máximo 4-5 linhas!

EXEMPLO BOM (curto e direto):
"Show! Consultei a agenda e temos esses horários disponíveis:
• Terça 14h
• Quarta 10h30
• Quinta 16h

Qual funciona melhor pra você? E qual seu email para eu enviar o convite do Google Calendar?"

EXEMPLO RUIM (longo demais):
"Perfeito! Vou agendar uma call com o Pedro. Ele é nosso especialista
e vai conseguir te mostrar cases parecidos. [mais texto...]
Para confirmar preciso de: nome completo, CPF, RG..." (NÃO!)

REGRAS:
- Ofereça os horários REAIS do Google Calendar (serão passados no contexto)
- SEMPRE peça o email junto para agilizar o agendamento
- Máximo 4-5 linhas
- Formatação limpa com bullets (•)
- Tom casual e confiante""",

    "solicitar_email": """Você é Smith, da AutomateX.

REGRA: Máximo 2 linhas! Solicitar email de forma direta.

SITUAÇÃO: Lead escolheu um horário para reunião.

ESTRUTURA:
"Perfeito! Para confirmar sua reunião no {horário_escolhido}, preciso do seu email para enviar o convite do Google Calendar. Qual é seu melhor email?"

REGRAS:
- Máximo 2 linhas
- Mencionar o horário que ele escolheu
- Deixar claro que é para receber convite do Google Calendar
- Tom casual e direto""",

    "confirmar_agendamento": """Você é Smith, da AutomateX.

REGRA: Máximo 3-4 linhas! Confirmar agendamento de forma direta.

SITUAÇÃO: Lead informou email, reunião foi criada no Google Calendar.

ESTRUTURA:
"Agendado! {data_hora_formatada}

Você vai receber um email com o convite do Google Calendar + link do Meet.

Te vejo lá!"

EXEMPLO:
"Agendado! Terça-feira, 15/01 às 14h

Você vai receber um email com o convite do Google Calendar + link do Meet.

Te vejo lá!"

REGRAS:
- Máximo 3-4 linhas
- Mencionar data/hora formatada de forma clara
- Avisar sobre email do Google Calendar
- Emoji de calendário e foguete
- Tom empolgante mas breve""",

    "followup": """Você é Smith, da AutomateX.

REGRA: Máximo 2-3 linhas! Agregue valor, não cobre resposta.

1º FOLLOW-UP (24h) - Insight extra:
"E aí! Sei que deve tá corrido aí.
Só deixando um dado: com 500 atendimentos/dia, você tá perdendo uns 15-20% dos leads só no delay.
Qualquer coisa, me chama! 😊"

2º FOLLOW-UP (72h) - Conteúdo útil:
"Opa! Vi esse dado e lembrei de você: empresas que respondem em até 5min têm 9x mais conversão.
Abs!"

3º FOLLOW-UP (7 dias) - Saída elegante:
"Fala! Última mensagem pra não encher o saco 😅
Deixo o material salvo aqui se precisar. Tmj!"

REGRAS:
- Máximo 2-3 linhas
- Sempre agregue valor (insight/dado)
- Nunca cobre resposta
- Seja casual""",

    "objecao_roi": """Você é Smith, consultor da AutomateX. Tom: WhatsApp casual, máximo 3-4 linhas.

O lead fez uma pergunta ou levantou uma dúvida após você apresentar o cálculo de ROI.

COMO RESPONDER (baseado no que ele perguntou):

- Se perguntou DE ONDE VEIO O NÚMERO: explique a lógica direto — "X pessoas × ~4h/semana em tarefas que automatizo × custo médio de hora = esse número. É conservador."
- Se CÉTICO com o valor: reconheça que é estimativa, convide para call onde faz o cálculo personalizado
- Se perguntou COMO VOCÊ AJUDARIA NA PRÁTICA, O QUE FARIA, COMO FUNCIONARIA NA EMPRESA DELES: NÃO responda de forma genérica. Peça o site deles para analisar antes: "Antes de te responder, me manda o link do site da [empresa] — quero analisar como vocês trabalham hoje pra não ser genérico."
- Para outras dúvidas: responda com confiança e brevidade

REGRAS:
- Máximo 3-4 linhas
- Zero bullet points
- NUNCA use as palavras "chatbot", "robô" ou "bot" — use "IA de atendimento" ou "agente inteligente"
- Tom de consultor real, não robótico
- Nunca repita a mensagem anterior palavra por palavra"""
}


# ========================================
# NODES DA STATE MACHINE
# ========================================

class SmithAgent:
    """Agente Smith - SDR Inteligente"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,  # ZERO criatividade - seguir instruções EXATAMENTE
            api_key=settings.openai_api_key,
            max_retries=2,  # Limitar retries para evitar loop infinito em erro 429
            request_timeout=30  # Timeout de 30s por request
        )
        self.data_extractor = DataExtractor()

    # ----------------
    # NODES
    # ----------------

    def handle_new_lead(self, state: AgentState) -> AgentState:
        """Node: Contato inicial com novo lead OU roteamento baseado em stage"""
        try:
            lead = state["lead"]
            messages = state["messages"]
            current_stage = state.get("current_stage", None)

            # ✅ ROUTER: Se lead já está em conversa, rotear para node apropriado
            if current_stage and current_stage != "novo":
                logger.info(f"Lead {lead.nome} já em conversa (stage={current_stage}), roteando...")

                # 🧠 MEMÓRIA ENTRE SESSÕES: Se lead sumiu por mais de 4h e voltou
                HORAS_RETORNO = 4
                if (lead.ultima_interacao and
                    current_stage in ["contato_inicial", "qualificando"] and
                    lead.status not in [LeadStatus.AGENDAMENTO_MARCADO, LeadStatus.PERDIDO]):

                    from datetime import timezone
                    now = datetime.now()
                    ultima = lead.ultima_interacao
                    # Normalizar timezone
                    if ultima.tzinfo is not None:
                        ultima = ultima.replace(tzinfo=None)
                    horas_desde = (now - ultima).total_seconds() / 3600

                    if horas_desde > HORAS_RETORNO:
                        logger.info(f"🧠 Lead {lead.nome} retornou após {horas_desde:.1f}h - saudação personalizada")
                        nome = lead.nome.split()[0]

                        if lead.qualification_data and lead.qualification_data.maior_desafio and lead.qualification_data.maior_desafio.strip():
                            desafio = lead.qualification_data.maior_desafio
                            empresa = lead.empresa or "sua empresa"
                            greeting = (
                                f"Oi {nome}! Que bom te ver de volta! 👋\n\n"
                                f"Da última vez você me contou sobre o desafio de {desafio} na {empresa}.\n\n"
                                f"Ainda está crítico ou mudou alguma coisa?"
                            )
                        else:
                            greeting = (
                                f"Oi {nome}! Que bom que voltou! 👋\n\n"
                                f"Por onde paramos? Me conta o que está pensando."
                            )

                        messages.append(AIMessage(content=greeting))
                        state["messages"] = messages
                        state["lead"] = lead
                        state["next_action"] = "end"
                        return state

                # Rotear baseado no status do lead (valores do enum LeadStatus)
                if current_stage in ["contato_inicial", "qualificando"]:
                    state["next_action"] = "qualify"
                elif current_stage == "qualificado":
                    state["next_action"] = "qualify"  # Lead qualificado mas ainda em conversa
                elif current_stage in ["aguardando_escolha_horario", "aguardando_email", "horarios_oferecidos"]:
                    state["next_action"] = "confirm"  # Lead viu horários, vai escolher
                elif current_stage == "agendamento_confirmado":
                    state["next_action"] = "end"  # Reunião confirmada e criada
                elif current_stage == "agendamento_marcado":
                    state["next_action"] = "end"  # Já agendado (status legado)
                elif current_stage == "perdido":
                    state["next_action"] = "end"  # Lead perdido, nada a fazer
                else:
                    state["next_action"] = "qualify"  # Fallback

                return state

            # ✅ NOVO LEAD: Processar saudação inicial
            # System prompt
            system_msg = SystemMessage(content=SYSTEM_PROMPTS["novo"])

            # Gerar resposta
            response = self.llm.invoke([system_msg] + list(messages))

            # Atualizar estado
            messages.append(response)
            lead.status = LeadStatus.CONTATO_INICIAL
            lead.temperatura = LeadTemperature.MORNO

            state["messages"] = messages
            state["lead"] = lead
            state["current_stage"] = "contato_inicial"
            state["next_action"] = "end"  # ✅ FIX: Terminar após saudação (esperar resposta)

            logger.info(f"Contato inicial com {lead.nome}")
            return state

        except Exception as e:
            logger.error(f"Erro no handle_new_lead: {e}")
            return state

    def _build_qualification_prompt(self, lead, proximo_passo: str, ultima_mensagem: str, company_insight: str = None) -> str:
        """
        Prompt dinâmico para qualificação natural.
        Diz exatamente o que o LLM deve perguntar, mas deixa ele responder de forma humana.
        """
        # Contexto: o que já foi coletado
        coletado = []
        if lead.nome and lead.nome != "Lead":
            coletado.append(f"nome: {lead.nome}")
        if lead.empresa:
            coletado.append(f"empresa: {lead.empresa}")
        if lead.qualification_data:
            qd = lead.qualification_data
            if qd.cargo: coletado.append(f"cargo: {qd.cargo}")
            if qd.funcionarios_atendimento: coletado.append(f"equipe: {qd.funcionarios_atendimento} pessoas")
            if qd.faturamento_anual:
                fat_mensal = qd.faturamento_anual / 12
                coletado.append(f"faturamento: ~R${fat_mensal:,.0f}/mês")
            if qd.is_decision_maker is not None:
                coletado.append(f"é decisor: {'sim' if qd.is_decision_maker else 'não'}")
            if qd.maior_desafio: coletado.append(f"desafio principal: {qd.maior_desafio}")
            if qd.urgency: coletado.append(f"urgência: {qd.urgency}")
            if qd.site_url and qd.site_url != "sem_site": coletado.append(f"site: {qd.site_url}")
            elif qd.site_url == "sem_site": coletado.append("site: não tem site")

        contexto_str = "\n".join(f"  - {c}" for c in coletado) if coletado else "  - (nenhum dado coletado ainda)"

        instrucoes = {
            "empresa_e_cargo": "Pergunte em qual empresa ele trabalha e qual é o cargo/função. Pode fazer as duas na mesma mensagem.",
            "site_empresa": "Peça o site da empresa de forma natural — ex: 'E qual é o site de vocês? Quero dar uma olhada antes de continuar.' Se não tiver site, não tem problema.",
            "contexto_operacional_completo": "Pergunte quantas pessoas tem no time de atendimento/vendas E qual é o faturamento mensal aproximado. Mostre que isso vai te ajudar a calcular o impacto real.",
            "contexto_operacional_funcionarios": "Pergunte quantas pessoas tem no time de atendimento/vendas.",
            "faturamento": "Pergunte o faturamento mensal aproximado. Deixa claro que é pra calcular o impacto.",
            "decisor": "Pergunte diretamente se ele é quem decide sobre tecnologia/ferramentas na empresa.",
            "dor_principal": "Pergunte qual é o maior problema/gargalo que a empresa tem hoje — perda de leads, atendimento lento, processos manuais, etc.",
            "urgencia": "Pergunte qual é o timing — precisa resolver isso logo ou dá pra planejar pra daqui uns meses?"
        }

        instrucao = instrucoes.get(proximo_passo, "Continue a conversa naturalmente.")

        insight_str = ""
        if company_insight:
            insight_str = f"\nINSIGHT DA EMPRESA (use se for natural): {company_insight}"

        return f"""Você é Smith, consultor da AutomateX que vende automação de atendimento e vendas via IA.
Tom: consultor real no WhatsApp — humano, direto, sem enrolação.

DADOS DO LEAD ATÉ AGORA:
{contexto_str}{insight_str}

ÚLTIMA MENSAGEM DELE: "{ultima_mensagem}"

SUA TAREFA: {instrucao}

REGRAS CRÍTICAS:
- Máximo 3-4 linhas no total
- Reaja ao que ele disse — mencione algo ESPECÍFICO do que falou (nada de "ótimo!" ou "perfeito!" genérico)
- Faça UMA única pergunta — não várias ao mesmo tempo
- Se ele fizer uma pergunta ou desviar do assunto, responda brevemente e conduza de volta
- Zero bullet points, zero listas numeradas
- NUNCA use as palavras "chatbot", "robô" ou "bot" — você é uma IA de atendimento, um agente inteligente
- Tom de consultor que entende o negócio, não de formulário"""

    def qualify_lead(self, state: AgentState) -> AgentState:
        """Node: Qualificar lead com perguntas BANT"""
        try:
            lead = state["lead"]
            messages = state["messages"]

            # DETECTAR SE LEAD ACEITOU AGENDAR (últimas 2 mensagens)
            last_messages = []
            if messages:
                count = 0
                for msg in reversed(messages):
                    if isinstance(msg, HumanMessage):
                        last_messages.append(msg.content.lower().strip())
                        count += 1
                        if count >= 2:
                            break

            # Palavras que indicam aceitação de agendamento (word boundaries para evitar falsos positivos)
            # Ex: "poderia" não deve ser detectado como "pode", "sim" não deve pegar "assim"
            aceita_agendar_keywords = ["sim", "pode", "vamos", "aceito", "quero", "ok", "beleza",
                                       "confirmo", "agenda", "marcar", "agendar", "combina",
                                       "feito", "bora", "vou", "quero sim", "pode ser"]

            # Verificar se ACEITOU com word boundary (evita substring como "poderia" → "pode")
            aceitou_agendar = any(
                any(re.search(r'\b' + re.escape(kw) + r'\b', msg, re.IGNORECASE) for kw in aceita_agendar_keywords)
                for msg in last_messages
            )

            # Verificar se IA OFERECEU agendamento recentemente (penúltima mensagem do assistant)
            ia_ofereceu_agendamento = False
            if messages:
                # DEBUG: Mostrar últimas 3 mensagens do histórico
                logger.info(f"🔍 DEBUG - Últimas 3 mensagens no histórico:")
                for idx, msg in enumerate(list(reversed(messages))[:3]):
                    msg_type = "AI" if isinstance(msg, AIMessage) else "USER"
                    content_preview = msg.content[:60] if len(msg.content) > 60 else msg.content
                    logger.info(f"   [{idx}] {msg_type}: {content_preview}")

                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        msg_lower = msg.content.lower()
                        ofereceu_keywords = ["agendar", "reunião", "conversa", "momento para discutir", "horário", "agenda", "marcar", "call", "bora marcar"]
                        ia_ofereceu_agendamento = any(kw in msg_lower for kw in ofereceu_keywords)
                        logger.info(f"🔍 DEBUG - Verificando AIMessage: '{msg_lower[:80]}'")
                        logger.info(f"🔍 DEBUG - Encontrou keyword? {ia_ofereceu_agendamento}")
                        break

            # ✅ EXTRAIR DADOS DA CONVERSA PRIMEIRO (ANTES DE DECIDIR PRÓXIMO PASSO!)
            logger.info(f"🔍 Extraindo dados de qualificação de {lead.nome}...")
            extracted_qual_data = self.data_extractor.extract_qualification_data(lead)

            if extracted_qual_data:
                # Atualizar campos de qualificação
                if not lead.qualification_data:
                    lead.qualification_data = QualificationData()

                # Atualizar apenas campos que foram extraídos (não sobrescrever com None)
                if extracted_qual_data.faturamento_anual is not None:
                    lead.qualification_data.faturamento_anual = extracted_qual_data.faturamento_anual
                if extracted_qual_data.is_decision_maker is not None:
                    lead.qualification_data.is_decision_maker = extracted_qual_data.is_decision_maker
                if extracted_qual_data.urgency is not None:
                    lead.qualification_data.urgency = extracted_qual_data.urgency
                if extracted_qual_data.funcionarios_atendimento is not None:
                    lead.qualification_data.funcionarios_atendimento = extracted_qual_data.funcionarios_atendimento
                if extracted_qual_data.atendimentos_por_dia is not None:
                    lead.qualification_data.atendimentos_por_dia = extracted_qual_data.atendimentos_por_dia
                if extracted_qual_data.tempo_por_atendimento is not None:
                    lead.qualification_data.tempo_por_atendimento = extracted_qual_data.tempo_por_atendimento
                if extracted_qual_data.ticket_medio is not None:
                    lead.qualification_data.ticket_medio = extracted_qual_data.ticket_medio

                # Atualizar campos diretos do lead
                if extracted_qual_data.nome and not lead.nome:
                    lead.nome = extracted_qual_data.nome
                if extracted_qual_data.email and not lead.email:
                    lead.email = extracted_qual_data.email
                if extracted_qual_data.empresa and not lead.empresa:
                    lead.empresa = extracted_qual_data.empresa
                if extracted_qual_data.cargo:
                    lead.qualification_data.cargo = extracted_qual_data.cargo
                if extracted_qual_data.setor:
                    lead.qualification_data.setor = extracted_qual_data.setor
                if extracted_qual_data.maior_desafio:
                    lead.qualification_data.maior_desafio = extracted_qual_data.maior_desafio

                logger.success(f"✅ Dados extraídos e atualizados para {lead.nome}")
            else:
                logger.warning(f"⚠️ Nenhum dado novo extraído para {lead.nome}")

            # --- Salvar URL do site se site foi perguntado e lead respondeu ---
            if (lead.qualification_data and
                    lead.qualification_data.site_perguntado and
                    not lead.qualification_data.site_url):
                try:
                    from app.services.website_research_service import WebsiteResearchService as _WRS
                    _wrs_tmp = _WRS()
                    url_found = None
                    for msg in reversed(list(messages)[-3:]):
                        if isinstance(msg, HumanMessage):
                            url_found = _wrs_tmp.extract_url(msg.content)
                            if url_found:
                                break
                    lead.qualification_data.site_url = url_found or "sem_site"
                    if url_found:
                        logger.info(f"🔗 URL do site salva durante qualificação: {url_found}")
                    else:
                        logger.info(f"ℹ️ Lead {lead.nome} não forneceu site — marcado como sem_site")
                except Exception as _e:
                    logger.debug(f"Erro ao extrair URL do site: {_e}")

            # CONDIÇÃO 1: Lead com urgência que aceitou agendar
            tem_urgencia = (
                lead.qualification_data and
                lead.qualification_data.urgency
            )

            # CONDIÇÃO PARA IR PRO AGENDAMENTO:
            # Dados CRÍTICOS: cargo (CEO/Dono/Sócio é ICP), faturamento, decisor, urgência, desafio
            todas_perguntas_respondidas = (
                lead.qualification_data and
                lead.qualification_data.cargo and  # CRÍTICO - CEO/Dono/Sócio
                lead.qualification_data.funcionarios_atendimento and
                lead.qualification_data.faturamento_anual and
                lead.qualification_data.is_decision_maker is not None and
                lead.qualification_data.maior_desafio and lead.qualification_data.maior_desafio.strip() != "" and
                lead.qualification_data.urgency and lead.qualification_data.urgency.strip() != ""
            )

            # DEBUG: Mostrar valores da validação
            logger.info(f"🔍 VALIDAÇÃO AGENDAMENTO para {lead.nome}:")
            logger.info(f"   empresa: {lead.empresa}")
            logger.info(f"   cargo: {lead.qualification_data.cargo if lead.qualification_data else None}")
            logger.info(f"   funcionarios_atendimento: {lead.qualification_data.funcionarios_atendimento if lead.qualification_data else None}")
            logger.info(f"   faturamento_anual: {lead.qualification_data.faturamento_anual if lead.qualification_data else None}")
            logger.info(f"   is_decision_maker: {lead.qualification_data.is_decision_maker if lead.qualification_data else None}")
            logger.info(f"   maior_desafio: {lead.qualification_data.maior_desafio if lead.qualification_data else None}")
            logger.info(f"   urgency: {lead.qualification_data.urgency if lead.qualification_data else None}")
            logger.info(f"   todas_perguntas_respondidas: {todas_perguntas_respondidas}")
            logger.info(f"   tem_urgencia: {tem_urgencia}")
            logger.info(f"   aceitou_agendar: {aceitou_agendar}")
            logger.info(f"   ia_ofereceu_agendamento: {ia_ofereceu_agendamento}")

            # IR DIRETO PRO SCHEDULE SOMENTE se:
            # - Todas perguntas respondidas E
            # - Lead tem urgência E lead aceitou agendar
            if todas_perguntas_respondidas and tem_urgencia and aceitou_agendar and ia_ofereceu_agendamento:
                logger.info(f"🎯 Lead {lead.nome} TOTALMENTE QUALIFICADO e ACEITOU AGENDAR - indo para schedule")

                state["next_action"] = "schedule"
                state["lead"] = lead
                state["current_stage"] = "agendamento_marcado"
                return state

            # ===== FIX LOOP: Lead qualificado, oferta feita, mas usuário perguntou algo =====
            # Quando ROI foi oferecido e o lead NÃO aceitou (fez pergunta/objeção), usar LLM
            if todas_perguntas_respondidas and ia_ofereceu_agendamento and not aceitou_agendar:
                logger.info(f"🤔 Lead {lead.nome} questionou oferta - tratando com LLM")
                from app.services.roi_calculator import calcular_roi
                roi_resultado = calcular_roi(lead.qualification_data)
                eco_mensal = roi_resultado.get("economia_mensal", 0)
                func = roi_resultado.get("funcionarios")
                nome_lead = lead.nome.split()[0] if lead.nome else lead.nome

                if func and eco_mensal:
                    roi_contexto = f"Cálculo: {func} pessoas no time × ~4h/semana em tarefas manuais × R$17/hora (custo médio) × 70% automatizável = ~R${eco_mensal:,.0f}/mês"
                elif lead.qualification_data and lead.qualification_data.faturamento_anual and eco_mensal:
                    fat_mensal = lead.qualification_data.faturamento_anual / 12
                    roi_contexto = f"Cálculo: R${fat_mensal:,.0f}/mês de faturamento × 8% de leads que se perdem por atendimento lento = ~R${eco_mensal:,.0f}/mês recuperáveis"
                else:
                    roi_contexto = "Estimativa baseada no perfil médio de empresas similares"

                objecao_prompt = (
                    SYSTEM_PROMPTS["objecao_roi"] +
                    f"\n\nDADOS DO CÁLCULO: {roi_contexto}"
                    f"\nLEAD: {nome_lead}, empresa: {lead.empresa or 'empresa do lead'}"
                )
                response = self.llm.invoke([SystemMessage(content=objecao_prompt)] + list(messages))
                messages.append(response)
                state["messages"] = messages
                state["lead"] = lead
                state["next_action"] = "end"
                return state

            # ===== DETERMINAR PRÓXIMO PASSO =====
            empresa_nome = lead.empresa or "sua empresa"

            if not lead.qualification_data or not lead.qualification_data.cargo:
                proximo_passo = "empresa_e_cargo"
            elif not lead.qualification_data.site_perguntado:
                proximo_passo = "site_empresa"
            elif not lead.qualification_data.funcionarios_atendimento:
                ja_tem_faturamento = bool(lead.qualification_data.faturamento_anual)
                proximo_passo = "contexto_operacional_completo" if not ja_tem_faturamento else "contexto_operacional_funcionarios"
            elif not lead.qualification_data.faturamento_anual:
                proximo_passo = "faturamento"
            elif lead.qualification_data.is_decision_maker is None:
                proximo_passo = "decisor"
            elif not lead.qualification_data.maior_desafio or lead.qualification_data.maior_desafio.strip() == "":
                proximo_passo = "dor_principal"
            elif not lead.qualification_data.urgency or lead.qualification_data.urgency.strip() == "":
                proximo_passo = "urgencia"
            else:
                proximo_passo = "oferecer_agendamento"

            logger.info(f"🎯 Próximo passo: {proximo_passo}")

            # ===== OFERECER AGENDAMENTO COM ROI =====
            if proximo_passo == "oferecer_agendamento":
                logger.info(f"Lead {lead.nome} totalmente qualificado - oferecendo agendamento com ROI")
                from app.services.roi_calculator import calcular_roi, formatar_mensagem_roi
                roi_resultado = calcular_roi(lead.qualification_data)
                roi_base = formatar_mensagem_roi(roi_resultado, lead.nome, empresa_nome)

                # Verificar se temos insight do site para personalizar a oferta
                site_insight = None
                site_url = (lead.qualification_data.site_url
                            if lead.qualification_data and lead.qualification_data.site_url != "sem_site"
                            else None)
                try:
                    from app.services.empresa_research_service import empresa_research_service

                    # 1. Tentar cache em memória primeiro (rápido)
                    site_insight = empresa_research_service.get_cached_insight(str(lead.id))

                    # 2. Cache miss + temos URL → gerar insight agora (síncrono via thread)
                    if not site_insight and site_url:
                        logger.info(f"Cache vazio — gerando insight do site {site_url} agora")
                        import asyncio as _asyncio
                        from concurrent.futures import ThreadPoolExecutor as _TPE

                        async def _get_insight():
                            return await empresa_research_service.research_empresa(lead, url=site_url)

                        def _run():
                            _loop = _asyncio.new_event_loop()
                            _asyncio.set_event_loop(_loop)
                            try:
                                return _loop.run_until_complete(_get_insight())
                            finally:
                                _loop.close()

                        try:
                            with _TPE(max_workers=1) as _ex:
                                site_insight = _ex.submit(_run).result(timeout=15)
                        except Exception as _te:
                            logger.warning(f"Timeout/erro ao gerar insight do site: {_te}")

                    if site_insight:
                        logger.info(f"Usando insight do site na oferta de ROI: {site_insight[:60]}...")
                except Exception as _e:
                    logger.warning(f"Erro ao obter insight do site: {_e}")

                if site_insight:
                    # Gerar oferta personalizada com insight do site + ROI
                    nome_lead = lead.nome.split()[0] if lead.nome else lead.nome
                    offer_prompt = f"""Você é Smith, consultor da AutomateX.

DADOS DO LEAD:
- Nome: {nome_lead}
- Empresa: {empresa_nome}
- Desafio: {lead.qualification_data.maior_desafio or 'não informado'}
- Insight do site que você analisou: {site_insight}
- ROI calculado: {roi_base}

Escreva uma mensagem WhatsApp que:
1. Menciona em 1 frase o que você viu no site deles (mostre que fez o dever de casa)
2. Conecta com o desafio que ele descreveu
3. Apresenta o ROI calculado de forma impactante (use os números exatos)
4. Convida para call de 30min de forma direta e assertiva

REGRAS:
- Máximo 5-6 linhas, sem bullets, sem listas
- Tom firme de consultor — PROIBIDO: "poderia", "acredito que", "Que tal?"
- PROIBIDO: "chatbot", "robô", "bot"
- Use os números do ROI calculado

Responda APENAS com a mensagem."""
                    response = self.llm.invoke([SystemMessage(content=offer_prompt)] + list(messages)[-2:])
                    logger.info("Oferta de ROI personalizada com insight do site gerada via LLM")
                else:
                    response = AIMessage(content=roi_base)

            else:
                # ===== LLM COM PROMPT FOCADO - Conversa natural + pergunta específica =====
                # Pegar última mensagem do usuário para contextualizar
                ultima_msg = ""
                for msg in reversed(messages):
                    if isinstance(msg, HumanMessage):
                        ultima_msg = msg.content
                        break

                # Feature 2: company insight para dor_principal
                company_insight = None
                if proximo_passo == "dor_principal":
                    try:
                        from app.services.empresa_research_service import empresa_research_service
                        company_insight = empresa_research_service.get_cached_insight(str(lead.id))
                        if company_insight:
                            logger.info(f"Usando insight da empresa: {company_insight[:60]}...")
                    except Exception:
                        pass

                qualify_prompt = self._build_qualification_prompt(lead, proximo_passo, ultima_msg, company_insight)
                response = self.llm.invoke([SystemMessage(content=qualify_prompt)] + list(messages))

                # Marcar que o site foi perguntado (para saber que na próxima rodada deve salvar a URL)
                if proximo_passo == "site_empresa" and lead.qualification_data:
                    lead.qualification_data.site_perguntado = True

            # Atualizar estado
            messages.append(response)
            lead.status = LeadStatus.QUALIFICANDO
            lead.temperatura = LeadTemperature.QUENTE

            # SEMPRE terminar e esperar resposta do lead
            # (Detecção de aceitação acontece na PRÓXIMA rodada, não agora!)
            next_action = "end"

            state["messages"] = messages
            state["lead"] = lead
            state["current_stage"] = "qualificando"
            state["next_action"] = next_action

            logger.info(f"Qualificando {lead.nome} - Próximo passo: {proximo_passo}")
            return state

        except Exception as e:
            logger.error(f"Erro no qualify_lead: {e}")
            return state

    async def check_qualification(self, state: AgentState) -> AgentState:
        """
        Node: GATE de Qualificação
        Decide se o lead é qualificado ou não
        """
        try:
            lead = state["lead"]

            # Verificar qualificação usando o lead_qualifier
            is_qualified, reason, score = lead_qualifier.is_qualified(lead)

            # Atualizar lead score
            lead.lead_score = score

            if is_qualified:
                # ✅ LEAD QUALIFICADO - Oferecer 2 opções
                lead.status = LeadStatus.QUALIFICADO
                lead.temperatura = LeadTemperature.QUENTE
                lead.ai_summary = f"Lead qualificado com score {score}/100. {reason}"

                # Gerar mensagem oferecendo as 2 opções usando o prompt "qualificado"
                prompt = SYSTEM_PROMPTS["qualificado"]

                # Montar mensagens
                messages = state["messages"].copy()

                # Adicionar contexto do lead
                faturamento_fmt = f"{lead.qualification_data.faturamento_anual:,.0f}"
                context_msg = SystemMessage(content=f"""LEAD QUALIFICADO: {lead.nome}

Faturamento: R$ {faturamento_fmt}/ano
Decisor: {'Sim' if lead.qualification_data.is_decision_maker else 'Não'}
Urgência: {lead.qualification_data.urgency or 'não informada'}
Score: {score}/100

OFEREÇA AS 2 OPÇÕES DE FORMA CLARA E OBJETIVA.""")

                messages.append(context_msg)

                # Invocar LLM
                response = self.llm.invoke([
                    SystemMessage(content=prompt),
                    *messages
                ])

                # Adicionar resposta ao histórico
                state["messages"].append(response)

                state["lead"] = lead
                state["current_stage"] = "qualificado"
                state["next_action"] = "end"  # ✅ FIX: Terminar após oferecer opções (esperar escolha do lead)
                state["show_calendar"] = True  # Sinalizar para mostrar calendário no frontend

                logger.success(f"{lead.nome} QUALIFICADO (Score: {score}), mostrando calendário")
                return state

            else:
                # ❌ LEAD NÃO QUALIFICADO - Desqualificar educadamente
                lead.status = LeadStatus.PERDIDO
                lead.temperatura = LeadTemperature.FRIO
                lead.ai_summary = f"Lead não qualificado. Motivo: {reason}. Score: {score}/100"
                lead.lost_at = datetime.now()

                # Gerar mensagem educada de desqualificação
                disqualification_msg = lead_qualifier.get_disqualification_message(lead, reason)

                # Adicionar mensagem ao histórico (webhook cuidará do envio)
                state["messages"].append(AIMessage(content=disqualification_msg))

                state["lead"] = lead
                state["current_stage"] = "perdido"  # ✅ Usar valor correto do enum LeadStatus
                state["next_action"] = "end"

                logger.warning(f"❌ {lead.nome} NÃO QUALIFICADO (Score: {score}). Motivo: {reason}")
                return state

        except Exception as e:
            logger.error(f"Erro no check_qualification: {e}")
            # Em caso de erro, seguir com cautela
            state["next_action"] = "qualify"
            return state

    def generate_roi(self, state: AgentState) -> AgentState:
        """Node: Gerar e enviar análise de ROI"""
        try:
            lead = state["lead"]

            # Verificar se tem dados suficientes
            if not lead.qualification_data:
                logger.warning(f"Lead {lead.id} sem dados de qualificação")
                state["next_action"] = "qualify"
                return state

            # Calcular e gerar ROI (chamar async usando thread separada)
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def run_roi_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(roi_generator.generate_and_send(lead))
                finally:
                    new_loop.close()

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_roi_in_thread)
                roi_analysis = future.result(timeout=30)  # 30s timeout

            if roi_analysis:
                lead.roi_analysis = roi_analysis
                lead.status = LeadStatus.QUALIFICADO
                lead.lead_score = 75  # Score alto após qualificação

                # ROI gerado (envio será feito pelo webhook se source = whatsapp)
                state["lead"] = lead
                state["current_stage"] = "qualificado"  # ✅ Mantém qualificado (ROI é parte da qualificação)
                state["next_action"] = "end"  # ✅ Terminar após enviar ROI (esperar resposta)

                logger.success(f"ROI gerado para {lead.nome}")

            return state

        except Exception as e:
            logger.error(f"Erro no generate_roi: {e}")
            return state

    def schedule_meeting(self, state: AgentState) -> AgentState:
        """Node: Agendar reunião com o closer"""
        try:
            lead = state["lead"]
            messages = state["messages"]

            # 📅 BUSCAR HORÁRIOS REAIS DO GOOGLE CALENDAR
            available_slots = []
            slots_text = "Horários disponíveis não encontrados. Por favor, entre em contato direto conosco."

            if google_calendar_service.is_available():
                try:
                    # Chamar função async usando novo event loop isolado
                    import asyncio
                    from concurrent.futures import ThreadPoolExecutor
                    import threading

                    logger.info("📅 Buscando horários disponíveis do Google Calendar...")

                    # Criar função wrapper que roda em thread separada
                    def run_async_in_thread():
                        # Criar novo event loop para esta thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(
                                google_calendar_service.get_available_slots(
                                    days_ahead=7,
                                    num_slots=3,
                                    duration_minutes=60
                                )
                            )
                        finally:
                            new_loop.close()

                    # Executar em thread separada para evitar conflito com uvloop
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(run_async_in_thread)
                        available_slots = future.result(timeout=10)  # 10s timeout

                    if available_slots:
                        slots_text = "Horários disponíveis:\n"
                        for i, slot in enumerate(available_slots, 1):
                            slots_text += f"{i}. {slot['display']}\n"
                        logger.success(f"✅ {len(available_slots)} horários encontrados e formatados para mostrar ao lead")
                    else:
                        logger.warning("⚠️ Nenhum horário disponível retornado pelo Google Calendar")

                except Exception as calendar_error:
                    logger.error(f"❌ Erro ao buscar horários: {calendar_error}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                logger.warning("⚠️ Google Calendar não disponível - usando mensagem padrão")

            # TEMPLATE FIXO - mostrar horários (SEM passar por LLM!)
            fixed_response = f"""Aqui estão os horários disponíveis:

{slots_text}
Qual desses funciona melhor pra você?"""

            # Usar resposta FIXA (sem passar por LLM)
            response = AIMessage(content=fixed_response)

            # Atualizar estado
            messages.append(response)
            # Status: aguardando lead escolher horário (não agendou ainda!)
            lead.status = LeadStatus.AGUARDANDO_ESCOLHA_HORARIO
            lead.lead_score = 90

            state["messages"] = messages
            state["lead"] = lead
            state["current_stage"] = "aguardando_escolha_horario"  # Mesmo valor que lead.status
            state["next_action"] = "end"  # Terminar e esperar resposta do lead
            state["available_slots"] = available_slots  # Guardar slots para confirmação

            logger.info(f"Oferecendo horários de agendamento para {lead.nome}")
            return state

        except Exception as e:
            logger.error(f"Erro no schedule_meeting: {e}")
            return state

    def confirm_meeting(self, state: AgentState) -> AgentState:
        """Node: Confirmar horário escolhido e criar evento no Google Calendar"""
        try:
            lead = state["lead"]
            messages = state["messages"]
            available_slots = state.get("available_slots", [])

            # Pegar última mensagem do lead
            last_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_message = msg.content.lower().strip()
                    break

            if not last_message:
                logger.warning("⚠️ Nenhuma mensagem do lead encontrada")
                state["next_action"] = "end"
                return state

            logger.info(f"📝 Processando escolha do lead: {last_message}")

            # DETECTAR SE É APENAS ACEITAÇÃO (sem horário específico)
            # Se lead disse apenas "sim", "ok", "pode", etc SEM mencionar dia/hora
            # Isso significa que é a PRIMEIRA aceitação, não a escolha de horário
            # Nesse caso, devemos ir para schedule_meeting para MOSTRAR os horários

            aceita_keywords = ["sim", "ok", "pode", "vamos", "aceito", "quero", "beleza", "perfeito"]
            apenas_aceitacao = any(kw in last_message for kw in aceita_keywords) and len(last_message.split()) <= 3

            # Detectar horários (formato: 10h, 14h30, 10:00, 14:30)
            import re
            from datetime import datetime, timedelta
            import pytz

            hora_pattern = r'(\d{1,2})(?:h|:)?(\d{2})?'
            hora_match = re.search(hora_pattern, last_message)

            # Detectar dia escolhido (weekday ou data relativa)
            dia_escolhido = None
            tz = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(tz)

            # 1. Detectar "hoje", "amanhã", "depois de amanhã"
            if "hoje" in last_message:
                dia_escolhido = now.weekday()
                days_ahead = 0
            elif "amanhã" in last_message or "amanha" in last_message:
                tomorrow = now + timedelta(days=1)
                dia_escolhido = tomorrow.weekday()
                days_ahead = 1
            elif "depois" in last_message and ("amanhã" in last_message or "amanha" in last_message):
                after_tomorrow = now + timedelta(days=2)
                dia_escolhido = after_tomorrow.weekday()
                days_ahead = 2
            else:
                # 2. Detectar dias da semana
                dias_map = {
                    "segunda": 0, "seg": 0,
                    "terça": 1, "terca": 1, "ter": 1,
                    "quarta": 2, "qua": 2,
                    "quinta": 3, "qui": 3,
                    "sexta": 4, "sex": 4,
                    "sábado": 5, "sabado": 5, "sab": 5,
                    "domingo": 6, "dom": 6
                }

                for dia, weekday in dias_map.items():
                    if dia in last_message:
                        dia_escolhido = weekday
                        days_ahead = (dia_escolhido - now.weekday()) % 7
                        if days_ahead == 0:
                            days_ahead = 7  # Próxima semana se for hoje
                        break

            # SE É APENAS "SIM" SEM HORÁRIO → ir para schedule_meeting mostrar horários
            if apenas_aceitacao and not hora_match and dia_escolhido is None:
                logger.info("🔄 Lead aceitou agendar mas não escolheu horário - redirecionando para schedule_meeting")
                state["next_action"] = "schedule"
                state["current_stage"] = "qualificado"
                return state

            # Tentar encontrar o slot correspondente
            chosen_slot = None

            if hora_match and dia_escolhido is not None:
                hora = int(hora_match.group(1))
                minuto = int(hora_match.group(2)) if hora_match.group(2) else 0

                # Construir datetime alvo
                target_datetime = now + timedelta(days=days_ahead if 'days_ahead' in locals() else 0)
                target_datetime = target_datetime.replace(hour=hora, minute=minuto, second=0, microsecond=0)

                logger.info(f"🔍 Lead escolheu: {target_datetime.strftime('%d/%m às %H:%M')}")

                # Procurar slot correspondente nos slots disponíveis
                for slot in available_slots:
                    slot_start = slot['start']
                    if isinstance(slot_start, str):
                        slot_start = datetime.fromisoformat(slot_start)

                    if slot_start.weekday() == dia_escolhido and slot_start.hour == hora and slot_start.minute == minuto:
                        chosen_slot = slot
                        logger.success(f"✅ Slot encontrado: {slot['display']}")
                        break

            # Se não encontrou slot exato, criar um novo baseado no target_datetime
            if not chosen_slot and hora_match and dia_escolhido is not None and 'target_datetime' in locals():
                chosen_slot = {
                    'start': target_datetime,
                    'end': target_datetime + timedelta(minutes=60),
                    'display': target_datetime.strftime('%A, %d/%m às %H:%M')
                }
                logger.info(f"📅 Criado slot customizado: {chosen_slot['display']}")

            # Se encontrou um horário, CRIAR REUNIÃO DIRETO (sem pedir email)
            if chosen_slot:
                logger.info(f"✅ Horário escolhido: {chosen_slot['display']} - criando reunião...")

                # Criar reunião no Google Calendar usando ThreadPoolExecutor
                import asyncio
                from concurrent.futures import ThreadPoolExecutor

                # Email de fallback se o lead não tiver fornecido
                email_to_use = lead.email if lead.email and '@' in lead.email else f"{lead.telefone}@whatsapp.placeholder.com"

                def run_async_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        meeting_dt = chosen_slot['start']
                        if isinstance(meeting_dt, str):
                            meeting_dt = datetime.fromisoformat(meeting_dt)

                        return new_loop.run_until_complete(
                            google_calendar_service.create_meeting(
                                lead_name=lead.nome,
                                lead_email=email_to_use,
                                lead_phone=lead.telefone,
                                meeting_datetime=meeting_dt,
                                duration_minutes=60,
                                empresa=lead.empresa
                            )
                        )
                    finally:
                        new_loop.close()

                meeting_result = None
                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(run_async_in_thread)
                        meeting_result = future.result(timeout=10)
                except Exception as calendar_error:
                    logger.error(f"❌ Erro ao criar reunião: {calendar_error}")

                # Confirmar agendamento com LINK do Google Calendar
                meeting_dt = chosen_slot['start']
                if isinstance(meeting_dt, str):
                    meeting_dt = datetime.fromisoformat(meeting_dt)

                # Formatar data de forma mais amigável
                dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                dia_semana = dias_semana[meeting_dt.weekday()]
                data_formatada = f"{dia_semana}, {meeting_dt.strftime('%d/%m às %Hh')}"

                # Mensagem FIXA com link do Google Calendar
                confirmation_text = f"✅ Agendado! {data_formatada} 📅\n\n"

                if meeting_result and meeting_result.get('event_link'):
                    confirmation_text += f"👉 Adicione ao seu calendário:\n{meeting_result['event_link']}\n\n"

                confirmation_text += "Te vejo lá! Qualquer dúvida, é só chamar 🚀"

                response = AIMessage(content=confirmation_text)

                messages.append(response)
                lead.status = LeadStatus.AGENDAMENTO_MARCADO
                lead.lead_score = 95
                lead.temp_meeting_slot = None  # LIMPAR slot temporário após criação

                state["messages"] = messages
                state["lead"] = lead
                state["current_stage"] = "agendamento_confirmado"
                state["next_action"] = "end"

                logger.success(f"✅ Reunião confirmada para {lead.nome} em {data_formatada}")
                return state

            # Se não detectou horário, pedir clarificação
            logger.warning("⚠️ Não foi possível detectar escolha de horário")

            system_prompt = """Você é Smith, da AutomateX.

O lead respondeu mas não escolheu um horário específico dos que foram oferecidos.

PEÇA NOVAMENTE de forma CLARA e DIRETA (máximo 2 linhas):
"Qual desses horários funciona melhor pra você? Só me dizer o dia e horário (ex: quinta 16h)"
"""

            system_msg = SystemMessage(content=system_prompt)
            response = self.llm.invoke([system_msg] + list(messages))

            messages.append(response)
            state["messages"] = messages
            state["current_stage"] = "horarios_oferecidos"  # Manter no mesmo stage
            state["next_action"] = "end"  # Sair do loop, esperar nova resposta

            logger.info("⚠️ Pedindo clarificação de horário ao lead")
            return state

        except Exception as e:
            logger.error(f"Erro no confirm_meeting: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            state["next_action"] = "end"
            return state

    def handle_followup(self, state: AgentState) -> AgentState:
        """Node: Enviar follow-up para leads inativos"""
        try:
            lead = state["lead"]
            messages = state["messages"]

            # Verificar quantas tentativas
            tentativas = lead.followup_config.tentativas_realizadas

            if tentativas >= 3:
                # Marcar como perdido após 3 tentativas
                lead.status = LeadStatus.PERDIDO
                lead.temperatura = LeadTemperature.FRIO
                state["next_action"] = "end"
                logger.info(f"Lead {lead.nome} marcado como perdido após 3 follow-ups")
                return state

            # ===== FOLLOW-UP PERSONALIZADO COM TEMPLATES FIXOS (Feature 5) =====
            from app.services.roi_calculator import calcular_roi, formatar_mensagem_roi

            nome = lead.nome.split()[0] if lead.nome else lead.nome
            empresa = lead.empresa or "sua empresa"
            fixed_followup = None

            if tentativas == 0:
                # 24h: mencionar o desafio específico que o lead contou
                desafio = (lead.qualification_data.maior_desafio
                           if lead.qualification_data and lead.qualification_data.maior_desafio
                           else None)
                if desafio:
                    fixed_followup = (
                        f"E aí, {nome}! Sei que deve tá corrido. 😅\n\n"
                        f"Fiquei pensando no que você me contou sobre {desafio}. "
                        f"Isso ainda tá travando vocês?\n\n"
                        f"Qualquer coisa, me chama!"
                    )
                else:
                    fixed_followup = (
                        f"E aí, {nome}! Tudo certo? 👋\n\n"
                        f"Só passando pra ver se ficou alguma dúvida sobre como posso ajudar {empresa}.\n\n"
                        f"Qualquer coisa, me chama!"
                    )

            elif tentativas == 1:
                # 72h: enviar ROI calculado
                if lead.qualification_data:
                    roi = calcular_roi(lead.qualification_data)
                    roi_msg = formatar_mensagem_roi(roi, nome)
                    fixed_followup = (
                        f"Opa, {nome}! Rodei os números aqui:\n\n"
                        f"{roi_msg}\n\n"
                        f"Faz sentido falar mais sobre isso?"
                    )
                else:
                    fixed_followup = (
                        f"Opa, {nome}! Ainda posso te mostrar como funciona na prática.\n\n"
                        f"Tem 30min essa semana pra uma call rápida?"
                    )

            elif tentativas == 2:
                # 7 dias: última mensagem, tom descontraído
                fixed_followup = (
                    f"Fala, {nome}! Última mensagem pra não encher o saco 😅\n\n"
                    f"Se um dia fizer sentido resolver o atendimento da {empresa}, estarei por aqui.\n\n"
                    f"Sucesso! 🚀"
                )

            response = AIMessage(content=fixed_followup)

            # Atualizar estado
            messages.append(response)
            lead.followup_config.tentativas_realizadas += 1
            lead.temperatura = LeadTemperature.MORNO

            state["messages"] = messages
            state["lead"] = lead
            state["current_stage"] = "followup"

            logger.info(f"Follow-up #{tentativas + 1} enviado para {lead.nome}")
            return state

        except Exception as e:
            logger.error(f"Erro no handle_followup: {e}")
            return state

    # ----------------
    # ROUTING
    # ----------------

    def route_conversation(self, state: AgentState) -> str:
        """Determina próximo node baseado no estado"""
        next_action = state.get("next_action", "qualify")

        routing_map = {
            "qualify": "qualify_lead",
            "check_qualification": "check_qualification",
            "generate_roi": "generate_roi",
            "schedule": "schedule_meeting",
            "confirm": "confirm_meeting",
            "followup": "handle_followup",
            "end": END
        }

        return routing_map.get(next_action, "qualify_lead")

    # ----------------
    # BUILD GRAPH
    # ----------------

    def build_graph(self) -> StateGraph:
        """Constrói o grafo da state machine"""

        workflow = StateGraph(AgentState)

        # Adicionar nodes
        workflow.add_node("handle_new_lead", self.handle_new_lead)
        workflow.add_node("qualify_lead", self.qualify_lead)
        workflow.add_node("check_qualification", self.check_qualification)
        workflow.add_node("generate_roi", self.generate_roi)
        workflow.add_node("schedule_meeting", self.schedule_meeting)
        workflow.add_node("confirm_meeting", self.confirm_meeting)
        workflow.add_node("handle_followup", self.handle_followup)

        # Definir entry point
        workflow.set_entry_point("handle_new_lead")

        # Adicionar edges condicionais
        workflow.add_conditional_edges(
            "handle_new_lead",
            self.route_conversation
        )
        workflow.add_conditional_edges(
            "qualify_lead",
            self.route_conversation
        )
        workflow.add_conditional_edges(
            "check_qualification",
            self.route_conversation
        )
        workflow.add_conditional_edges(
            "generate_roi",
            self.route_conversation
        )
        workflow.add_conditional_edges(
            "schedule_meeting",
            self.route_conversation
        )
        workflow.add_conditional_edges(
            "confirm_meeting",
            self.route_conversation
        )
        workflow.add_conditional_edges(
            "handle_followup",
            self.route_conversation
        )

        return workflow.compile()


# Instância global
smith_agent = SmithAgent()
smith_graph = smith_agent.build_graph()
