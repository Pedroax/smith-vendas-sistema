"""
Smith 2.0 - Agente SDR Inteligente
State Machine LangGraph para qualificação e agendamento de leads
"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from datetime import datetime

from app.config import settings
from app.models.lead import Lead, LeadStatus, LeadTemperature, QualificationData
from app.services import roi_generator, whatsapp_service, lead_qualifier
from app.services.google_calendar_service import google_calendar_service
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


# ========================================
# PROMPTS DO SISTEMA
# ========================================

SYSTEM_PROMPTS = {
    "novo": """Você é Smith, consultor estratégico de automação e IA da AutomateX.

IDENTIDADE:
Você é um expert em identificar problemas operacionais e demonstrar valor com precisão cirúrgica. Sua comunicação combina objetividade empresarial com persuasão estratégica.

ABERTURA IMPACTANTE:
Olá! Sou Smith da AutomateX, especialista em soluções de IA que estão gerando um aumento médio de 35% em produtividade comercial para nossos clientes.

Como posso chamá-lo(a)?

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

SEMPRE:
- Mostre valor antes de pedir informação
- Personalize baseado no contexto
- Transforme números em resultados visualizáveis""",

    "qualificando": """Você é Smith, consultor estratégico de automação da AutomateX.

CONTEXTO CRÍTICO: Você está em uma conversa de diagnóstico com um lead. Seja consultivo, não interrogativo.

⚠️ SEMPRE VERIFIQUE O QUE JÁ TEM ANTES DE PERGUNTAR!

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

✅ Automação de atendimento → Responde leads em segundos
✅ Qualificação automática → Só fala com quem tem fit
✅ Follow-up inteligente → Nenhum lead esquecido

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
"Agendado! {data_hora_formatada} 📅

Você vai receber um email com o convite do Google Calendar + link do Meet.

Te vejo lá! 🚀"

EXEMPLO:
"Agendado! Terça-feira, 15/01 às 14h 📅

Você vai receber um email com o convite do Google Calendar + link do Meet.

Te vejo lá! 🚀"

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
- Seja casual"""
}


# ========================================
# NODES DA STATE MACHINE
# ========================================

class SmithAgent:
    """Agente Smith - SDR Inteligente"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key
        )

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

                # Rotear baseado no status do lead (valores do enum LeadStatus)
                if current_stage in ["contato_inicial", "qualificando"]:
                    state["next_action"] = "qualify"
                elif current_stage == "qualificado":
                    state["next_action"] = "qualify"  # Lead qualificado mas ainda em conversa
                elif current_stage == "agendamento_marcado":
                    state["next_action"] = "end"  # Já agendado, nada a fazer
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

    def qualify_lead(self, state: AgentState) -> AgentState:
        """Node: Qualificar lead com perguntas BANT"""
        try:
            lead = state["lead"]
            messages = state["messages"]

            # System prompt
            system_msg = SystemMessage(content=SYSTEM_PROMPTS["qualificando"])

            # Determinar próximo passo estratégico
            proximo_passo = None
            contexto_estrategico = ""

            if not lead.email:
                proximo_passo = "tamanho_equipe"
                contexto_estrategico = f"""SITUAÇÃO ATUAL: Você acabou de capturar o nome ({lead.nome}).

PRÓXIMO PASSO ESTRATÉGICO: Entender o contexto operacional dele para personalizar a conversa e demonstrar valor específico.

PERGUNTE (de forma consultiva, não mecânica): "{lead.nome}, para entender melhor como podemos ajudar, me conta: quantas pessoas compõem seu time de vendas atualmente?"

APÓS A RESPOSTA: Personalize com um insight baseado no tamanho da equipe (1-3, 4-10, ou 11+)."""

            elif not lead.qualification_data or not lead.qualification_data.faturamento_anual:
                proximo_passo = "faturamento"
                contexto_estrategico = f"""SITUAÇÃO ATUAL: Nome capturado ({lead.nome}).

PRÓXIMO PASSO ESTRATÉGICO: Qualificar o porte da empresa para propor a solução mais adequada.

PERGUNTE (de forma consultiva): "E qual é a faixa de faturamento mensal da sua empresa? Essa informação é importante porque temos estratégias específicas para cada perfil de negócio."

IMPORTANTE: Se ele mostrar resistência, explique o PORQUÊ dessa pergunta."""

            elif not lead.qualification_data or lead.qualification_data.is_decision_maker is None:
                proximo_passo = "decisor"
                contexto_estrategico = f"""SITUAÇÃO ATUAL: Nome e faturamento capturados.

PRÓXIMO PASSO ESTRATÉGICO: Identificar se ele pode tomar a decisão ou precisa envolver mais pessoas.

PERGUNTE (de forma consultiva): "Obrigado pela transparência, {lead.nome}. Uma pergunta importante: você é o responsável pelas decisões de implementação de tecnologia na empresa?"

CONTEXTO: Nossa agenda está apertada, então precisamos garantir que a pessoa certa participa da reunião."""

            elif not lead.qualification_data or not lead.qualification_data.maior_desafio:
                proximo_passo = "dor_principal"
                contexto_estrategico = f"""SITUAÇÃO ATUAL: Lead com perfil qualificável (faturamento + decisor OK).

PRÓXIMO PASSO CRÍTICO: MAPEAR A DOR PRINCIPAL antes de qualificar.

PERGUNTE (de forma profunda): "{lead.nome}, qual é o principal desafio que vocês enfrentam hoje no processo comercial? O que está impedindo vocês de crescerem mais rapidamente?"

IMPORTANTE: Essa é a pergunta MAIS IMPORTANTE. A resposta vai determinar todo o pitch.

APÓS A RESPOSTA: Use cases específicos baseados na dor:
- Falta de leads → "A AutomateX ajudou a Bateral a aumentar leads qualificados em 35% com nosso agente de IA para Instagram Direct."
- Baixa conversão → "LC Baterias enfrentava o mesmo problema e aumentou conversão em 37% após implementar follow-up automatizado."
- Processos manuais → "Dunkin' eliminou 85% das tarefas manuais e gerou 45% mais vendas."
- Time sobrecarregado → "Com automação, times conseguem trabalhar 30% mais leads sem contratar."

NÃO QUALIFIQUE AINDA! Primeiro explore a dor."""

            elif not lead.qualification_data or not lead.qualification_data.urgency:
                proximo_passo = "urgencia"
                contexto_estrategico = f"""SITUAÇÃO ATUAL: Dor mapeada, lead engajado.

PRÓXIMO PASSO ESTRATÉGICO: Entender timing para priorizar corretamente.

PERGUNTE: "E qual o nível de urgência para a implementação? Vocês estão buscando iniciar nas próximas semanas ou é algo planejado para os próximos meses?"

APÓS A RESPOSTA: Agora sim você pode qualificar com awareness."""

            else:
                proximo_passo = "completo"
                contexto_estrategico = "Todas as informações coletadas incluindo DOR. Prossiga para qualificação final com awareness."

            # Adicionar contexto do lead
            context_msg = SystemMessage(content=f"""⚠️ DADOS JÁ CAPTURADOS:

Nome: {lead.nome} ✅
Email: {lead.email or 'Não capturado'}
Empresa: {lead.empresa or 'Não capturado'}
Faturamento: {lead.qualification_data.faturamento_anual if lead.qualification_data and lead.qualification_data.faturamento_anual else 'Não capturado'}
Decisor: {'Sim' if lead.qualification_data and lead.qualification_data.is_decision_maker else 'Não' if lead.qualification_data and lead.qualification_data.is_decision_maker is False else 'Não capturado'}

{contexto_estrategico}

⚠️ NUNCA pergunte o nome novamente! Use "{lead.nome}" nas respostas.
⚠️ Seja CONSULTIVO, não mecânico. Cada pergunta deve ter contexto e demonstrar valor.""")

            # Gerar resposta
            response = self.llm.invoke([system_msg, context_msg] + list(messages))

            # Atualizar estado
            messages.append(response)
            lead.status = LeadStatus.QUALIFICANDO
            lead.temperatura = LeadTemperature.QUENTE

            # CRITICAL: Só vai para check_qualification se TODAS as informações foram coletadas
            # Incluindo: faturamento, decisor, maior_desafio, urgency
            if proximo_passo == "completo":
                next_action = "check_qualification"
            else:
                # ✅ FIX: Terminar após gerar pergunta (esperar resposta do usuário)
                next_action = "end"  # Webhook enviará resposta e aguardará próxima mensagem

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
                context_msg = SystemMessage(content=f"""LEAD QUALIFICADO: {lead.nome}

Faturamento: R$ {lead.qualification_data.faturamento_anual:,.0f}/ano
Decisor: {'Sim' if lead.qualification_data.is_decision_maker else 'Não'}
Urgência: {lead.qualification_data.urgency or 'não informada'}
Score: {score}/100

🎯 OFEREÇA AS 2 OPÇÕES DE FORMA CLARA E OBJETIVA.""")

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

                logger.success(f"✅ {lead.nome} QUALIFICADO (Score: {score}), mostrando calendário")
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

    async def generate_roi(self, state: AgentState) -> AgentState:
        """Node: Gerar e enviar análise de ROI"""
        try:
            lead = state["lead"]

            # Verificar se tem dados suficientes
            if not lead.qualification_data:
                logger.warning(f"Lead {lead.id} sem dados de qualificação")
                state["next_action"] = "qualify"
                return state

            # Calcular e gerar ROI
            roi_analysis = await roi_generator.generate_and_send(lead)

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

    async def schedule_meeting(self, state: AgentState) -> AgentState:
        """Node: Agendar reunião com o closer"""
        try:
            lead = state["lead"]
            messages = state["messages"]

            # 📅 BUSCAR HORÁRIOS REAIS DO GOOGLE CALENDAR
            available_slots = []
            slots_text = "Horários disponíveis não encontrados. Por favor, entre em contato direto conosco."

            if google_calendar_service.is_available():
                try:
                    available_slots = await google_calendar_service.get_available_slots(
                        days_ahead=7,
                        num_slots=3,
                        duration_minutes=60
                    )

                    if available_slots:
                        slots_text = "Horários disponíveis:\n"
                        for i, slot in enumerate(available_slots, 1):
                            slots_text += f"{i}. {slot['display']}\n"

                    logger.info(f"📅 {len(available_slots)} horários disponíveis encontrados")
                except Exception as calendar_error:
                    logger.error(f"❌ Erro ao buscar horários: {calendar_error}")
            else:
                logger.warning("⚠️ Google Calendar não disponível - usando horários fictícios")

            # System prompt COM horários reais
            system_prompt = f"""{SYSTEM_PROMPTS["agendamento"]}

IMPORTANTE: Use EXATAMENTE estes horários disponíveis do Google Calendar:
{slots_text}

NÃO invente horários! Use apenas os listados acima."""

            system_msg = SystemMessage(content=system_prompt)

            # Gerar resposta
            response = self.llm.invoke([system_msg] + list(messages))

            # Atualizar estado
            messages.append(response)
            lead.status = LeadStatus.AGENDAMENTO_MARCADO
            lead.lead_score = 90

            state["messages"] = messages
            state["lead"] = lead
            state["current_stage"] = "agendamento_marcado"
            state["next_action"] = "end"

            logger.info(f"Oferecendo horários de agendamento para {lead.nome}")
            return state

        except Exception as e:
            logger.error(f"Erro no schedule_meeting: {e}")
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

            # System prompt
            system_msg = SystemMessage(content=SYSTEM_PROMPTS["followup"])

            # Contexto do follow-up
            context = f"""Follow-up #{tentativas + 1} para {lead.nome}.
Última interação: {lead.ultima_interacao}
Status atual: {lead.status}

Seja prestativo e agregue valor."""

            context_msg = SystemMessage(content=context)

            # Gerar resposta
            response = self.llm.invoke([system_msg, context_msg] + list(messages))

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
            "handle_followup",
            self.route_conversation
        )

        return workflow.compile()


# Instância global
smith_agent = SmithAgent()
smith_graph = smith_agent.build_graph()
