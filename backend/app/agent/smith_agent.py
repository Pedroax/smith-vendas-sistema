"""
Smith 2.0 - Agente SDR Inteligente
State Machine LangGraph para qualificação e agendamento de leads
"""
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

            # Palavras que indicam aceitação de agendamento
            aceita_agendar_keywords = ["sim", "pode", "vamos", "aceito", "quero", "podemos", "ok", "beleza", "perfeito", "ótimo", "confirmo", "agenda", "marcar", "próxima", "semana", "agendar", "reunião", "conversar"]

            # Verificar se ACEITOU em qualquer das últimas mensagens
            aceitou_agendar = any(
                any(keyword in msg for keyword in aceita_agendar_keywords)
                for msg in last_messages
            )

            # Verificar se IA OFERECEU agendamento recentemente (penúltima mensagem do assistant)
            ia_ofereceu_agendamento = False
            if messages:
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        msg_lower = msg.content.lower()
                        ofereceu_keywords = ["agendar", "reunião", "conversa", "momento para discutir", "horário", "agenda"]
                        ia_ofereceu_agendamento = any(kw in msg_lower for kw in ofereceu_keywords)
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

            # System prompt
            system_msg = SystemMessage(content=SYSTEM_PROMPTS["qualificando"])

            # Determinar próximo passo estratégico E RESPOSTA PRÉ-DEFINIDA
            proximo_passo = None
            resposta_predefinida = None  # Nova: resposta exata pré-definida

            # ===== USAR TEMPLATES FIXOS (tipo N8N) - SEM LLM =====
            # IA estava inventando respostas, agora usa TEXTO FIXO

            fixed_response = None

            # CARGO É CRÍTICO (CEO/Dono/Sócio é ICP) - perguntar junto com empresa
            if not lead.qualification_data or not lead.qualification_data.cargo:
                proximo_passo = "empresa_e_cargo"
                fixed_response = f"Legal, {lead.nome}! Qual é sua empresa e qual seu cargo lá?"

            elif not lead.qualification_data or not lead.qualification_data.funcionarios_atendimento:
                proximo_passo = "contexto_operacional"

                # Verificar se já tem faturamento para não perguntar de novo
                ja_tem_faturamento = lead.qualification_data and lead.qualification_data.faturamento_anual

                if ja_tem_faturamento:
                    # Se JÁ tem faturamento, perguntar SÓ sobre funcionários
                    fixed_response = f"Entendi, {lead.nome}! E quantas pessoas você tem no time de vendas/atendimento?"
                else:
                    # Se NÃO tem faturamento, perguntar ambos
                    fixed_response = f"Bacana, {lead.nome}! Pra eu calcular o impacto real: quantas pessoas você tem no time de vendas e qual o faturamento mensal aproximado da empresa?"

            elif not lead.qualification_data or not lead.qualification_data.faturamento_anual:
                proximo_passo = "faturamento"
                fixed_response = f"Ótimo, {lead.nome}! E qual o faturamento mensal aproximado? Isso me ajuda a calcular o ROI exato que conseguimos gerar pra vocês."

            elif not lead.qualification_data or lead.qualification_data.is_decision_maker is None:
                proximo_passo = "decisor"
                fixed_response = f"Perfeito! {lead.nome}, você é o responsável por decisões de tecnologia/processos na {lead.empresa or 'empresa'}?"

            elif not lead.qualification_data or not lead.qualification_data.maior_desafio or lead.qualification_data.maior_desafio.strip() == "":
                proximo_passo = "dor_principal"
                fixed_response = f"Show! Me conta: qual o principal problema que tá impedindo vocês de crescer mais rápido? Perda de leads? Atendimento desorganizado? Processos manuais?"

            elif not lead.qualification_data or not lead.qualification_data.urgency or lead.qualification_data.urgency.strip() == "":
                proximo_passo = "urgencia"
                fixed_response = f"Entendi, {lead.nome}! E quanto ao timing: isso é urgente pra vocês ou dá pra deixar pros próximos meses?"

            else:
                # LEAD TOTALMENTE QUALIFICADO - OFERECER AGENDAMENTO!
                proximo_passo = "oferecer_agendamento"
                logger.info(f"Lead {lead.nome} totalmente qualificado - oferecendo agendamento")
                fixed_response = f"Perfeito, {lead.nome}! 🎯\n\nCom base no que você me contou (faturamento, urgência e desafio), consigo te mostrar exatamente como resolver isso.\n\nQue tal agendarmos 30min para eu te apresentar a solução completa?"

            # Usar resposta FIXA (sem passar por LLM)
            response = AIMessage(content=fixed_response)

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

            # TEMPLATE FIXO - mostrar horários e pedir email (SEM passar por LLM!)
            fixed_response = f"""Aqui estão os horários disponíveis:

{slots_text}
Qual funciona melhor pra você? E qual seu email para eu enviar o convite do Google Calendar?"""

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

            # Detectar dias da semana
            dias_map = {
                "segunda": 0, "seg": 0,
                "terça": 1, "terca": 1, "ter": 1,
                "quarta": 2, "qua": 2,
                "quinta": 3, "qui": 3,
                "sexta": 4, "sex": 4,
                "sábado": 5, "sabado": 5, "sab": 5,
                "domingo": 6, "dom": 6
            }

            # Detectar horários (formato: 10h, 14h30, 10:00, 14:30)
            import re
            hora_pattern = r'(\d{1,2})(?:h|:)?(\d{2})?'
            hora_match = re.search(hora_pattern, last_message)

            # Detectar dia da semana
            dia_escolhido = None
            for dia, weekday in dias_map.items():
                if dia in last_message:
                    dia_escolhido = weekday
                    break

            # SE É APENAS "SIM" SEM HORÁRIO → ir para schedule_meeting mostrar horários
            if apenas_aceitacao and not hora_match and dia_escolhido is None:
                logger.info("🔄 Lead aceitou agendar mas não escolheu horário - redirecionando para schedule_meeting")
                state["next_action"] = "schedule"
                state["current_stage"] = "qualificado"
                return state

            # Tentar encontrar o slot correspondente
            from datetime import datetime, timedelta
            import pytz

            chosen_slot = None

            if hora_match and dia_escolhido is not None:
                hora = int(hora_match.group(1))
                minuto = int(hora_match.group(2)) if hora_match.group(2) else 0

                logger.info(f"🔍 Lead escolheu: {list(dias_map.keys())[list(dias_map.values()).index(dia_escolhido)]} {hora}:{minuto:02d}")

                # Procurar slot correspondente nos slots disponíveis
                for slot in available_slots:
                    slot_start = slot['start']
                    if isinstance(slot_start, str):
                        slot_start = datetime.fromisoformat(slot_start)

                    if slot_start.weekday() == dia_escolhido and slot_start.hour == hora and slot_start.minute == minuto:
                        chosen_slot = slot
                        logger.success(f"✅ Slot encontrado: {slot['display']}")
                        break

            # Se não encontrou slot exato, tentar criar um datetime baseado na escolha
            if not chosen_slot and hora_match and dia_escolhido is not None:
                hora = int(hora_match.group(1))
                minuto = int(hora_match.group(2)) if hora_match.group(2) else 0

                # Calcular próxima ocorrência do dia da semana
                tz = pytz.timezone('America/Sao_Paulo')
                now = datetime.now(tz)
                days_ahead = (dia_escolhido - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Próxima semana se for hoje

                target_date = now + timedelta(days=days_ahead)
                meeting_datetime = target_date.replace(hour=hora, minute=minuto, second=0, microsecond=0)

                chosen_slot = {
                    'start': meeting_datetime,
                    'end': meeting_datetime + timedelta(minutes=60),
                    'display': meeting_datetime.strftime('%A, %d/%m às %H:%M')
                }
                logger.info(f"📅 Criado slot customizado: {chosen_slot['display']}")

            # Se encontrou um horário, processar
            if chosen_slot:
                # Verificar se já tem email
                if not lead.email or '@' not in lead.email:
                    # PEDIR EMAIL
                    system_prompt = f"""{SYSTEM_PROMPTS["solicitar_email"]}

HORÁRIO ESCOLHIDO: {chosen_slot['display']}

Sua resposta deve ser CURTA (máximo 2 linhas) e pedir o email para enviar o convite do Google Calendar."""

                    system_msg = SystemMessage(content=system_prompt)
                    response = self.llm.invoke([system_msg] + list(messages))

                    messages.append(response)
                    state["messages"] = messages
                    state["current_stage"] = "aguardando_email"
                    state["next_action"] = "confirm"
                    state["chosen_slot"] = chosen_slot

                    logger.info("📧 Solicitando email do lead para criar reunião")
                    return state

                # SE TEM EMAIL, CRIAR REUNIÃO
                else:
                    logger.info(f"✅ Lead tem email: {lead.email} - criando reunião...")

                    # Criar reunião no Google Calendar usando ThreadPoolExecutor
                    import asyncio
                    from concurrent.futures import ThreadPoolExecutor

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
                                    lead_email=lead.email,
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

                    # Confirmar agendamento
                    meeting_dt = chosen_slot['start']
                    if isinstance(meeting_dt, str):
                        meeting_dt = datetime.fromisoformat(meeting_dt)

                    data_hora_formatada = meeting_dt.strftime('%d/%m/%Y às %H:%M')

                    system_prompt = f"""{SYSTEM_PROMPTS["confirmar_agendamento"]}

DATA/HORA: {data_hora_formatada}
EMAIL DO LEAD: {lead.email}

Confirme o agendamento de forma CURTA (máximo 3-4 linhas)."""

                    system_msg = SystemMessage(content=system_prompt)
                    response = self.llm.invoke([system_msg] + list(messages))

                    messages.append(response)
                    lead.status = LeadStatus.AGENDAMENTO_MARCADO
                    lead.lead_score = 95

                    state["messages"] = messages
                    state["lead"] = lead
                    state["current_stage"] = "agendamento_confirmado"
                    state["next_action"] = "end"

                    logger.success(f"✅ Reunião confirmada para {lead.nome} em {data_hora_formatada}")
                    return state

            # SE NÃO DETECTOU HORÁRIO, verificar se é email
            elif '@' in last_message:
                # LEAD ENVIOU EMAIL
                lead.email = last_message
                logger.info(f"📧 Email capturado: {lead.email}")

                # Recuperar slot escolhido anteriormente
                chosen_slot = state.get("chosen_slot")

                if chosen_slot:
                    # Criar reunião
                    import asyncio
                    from concurrent.futures import ThreadPoolExecutor

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
                                    lead_email=lead.email,
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

                    # Confirmar agendamento
                    meeting_dt = chosen_slot['start']
                    if isinstance(meeting_dt, str):
                        meeting_dt = datetime.fromisoformat(meeting_dt)

                    data_hora_formatada = meeting_dt.strftime('%d/%m/%Y às %H:%M')

                    system_prompt = f"""{SYSTEM_PROMPTS["confirmar_agendamento"]}

DATA/HORA: {data_hora_formatada}
EMAIL DO LEAD: {lead.email}

Confirme o agendamento de forma CURTA (máximo 3-4 linhas)."""

                    system_msg = SystemMessage(content=system_prompt)
                    response = self.llm.invoke([system_msg] + list(messages))

                    messages.append(response)
                    lead.status = LeadStatus.AGENDAMENTO_MARCADO
                    lead.lead_score = 95

                    state["messages"] = messages
                    state["lead"] = lead
                    state["current_stage"] = "agendamento_confirmado"
                    state["next_action"] = "end"

                    logger.success(f"✅ Reunião confirmada para {lead.nome} em {data_hora_formatada}")
                    return state

            # Se não entendeu, pedir clarificação
            logger.warning("⚠️ Não foi possível detectar escolha de horário ou email")

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
