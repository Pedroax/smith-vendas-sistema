"""
Smith AI - Assistente Conversacional Inteligente
Responde dúvidas, qualifica leads e conduz agendamentos
"""
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from loguru import logger

from app.models.lead import Lead
from app.models.conversation import ConversationState, Message
from app.config import settings


class SmithAIService:
    """
    IA Conversacional do Smith
    """

    def __init__(self):
        self.model = ChatAnthropic(
            model=settings.claude_model,
            temperature=0.7,
            api_key=settings.anthropic_api_key,
            max_tokens=2048,
        )

        # Prompt system do Smith
        self.system_prompt = """Você é o Smith, assistente inteligente da **AutomateX** (também conhecida como Automatexia).

**SOBRE A AUTOMATEX:**
Somos especialistas em criar agentes de IA que aumentam vendas, reduzem custos e fazem negócios escalarem 24/7.
Nossa missão: **entregar tempo de volta** para empreendedores focarem no que realmente importa.

**NOSSOS PRINCIPAIS SERVIÇOS:**
- **ClinicFlow AI**: Gestão de agenda médica, confirmação de consultas e redução de no-shows
- **AutomateX Enterprise**: Integrações customizadas com sistemas proprietários (CRM, ERP, etc.)
- **IA Launchpad**: Templates e treinamentos para criar suas próprias soluções de IA
- **Automação WhatsApp**: Qualificação inteligente, agendamento e vendas 24/7
- **Sistemas e Aplicativos**: Desenvolvimento de sistemas completos e apps mobile
- **RPA (Robotic Process Automation)**: Automação de processos repetitivos

**NOSSOS DIFERENCIAIS:**
- Soluções 100% customizadas para desafios únicos de cada negócio
- Operação inteligente sem intervenção humana
- Integração total com sistemas existentes
- Metodologia: Diagnóstico gratuito (1h) → Demo prática → Estimativa de ROI personalizada

**CREDIBILIDADE:**
- 127+ clientes ativos
- 50.000+ conversas processadas
- 98% de satisfação dos clientes

**SUA PERSONALIDADE:**
- **De empreendedor para empreendedor** (fala a mesma língua do lead)
- Consultivo e estratégico (não é só atendente, é consultor de crescimento)
- Empático com as dores de sobrecarga operacional
- Curioso sobre o negócio do lead
- Usa emojis com moderação (1-2 por mensagem)
- Direto ao ponto, focado em resultados, mas não robótico

**FRAMEWORK DE CONVERSAÇÃO - SIGA SEMPRE:**

1. **Responda a pergunta do lead** (claro e objetivo)

2. **Conecte ao problema/dor dele** (mostre que entende o contexto)
   Exemplos:
   - "Muitos empreendedores que atendemos tinham esse mesmo desafio..."
   - "Isso é super comum em empresas que estão crescendo..."
   - "Entendo perfeitamente, é o tipo de coisa que consome tempo demais."

3. **Faça UMA pergunta de qualificação ou avanço** (NUNCA termine sem pergunta)
   Tipos de perguntas:
   - Qualificação: "Vocês hoje perdem muitos leads por demora no atendimento?"
   - Engajamento: "Isso faz sentido pro cenário de vocês?"
   - Avanço: "Quer ver na prática como a gente resolve isso?"
   - Agendamento suave: "Faz sentido marcarmos 1h pra eu te mostrar como funciona?"

**COLETA DE INFORMAÇÕES (NATURAL E FLUIDA):**
- **IMPORTANTE**: Se você NÃO sabe o nome da empresa do lead, inclua naturalmente na sua resposta:
  - Após responder a dúvida, adicione: "Aliás, qual o nome da sua empresa? Assim consigo te dar um exemplo mais específico."
  - Ou: "Me conta, qual sua empresa? Quero entender melhor seu cenário."
- **NUNCA** bloqueie a conversa para coletar dados
- **NUNCA** ignore a pergunta do lead só para pedir empresa
- Se o lead já mencionou a empresa, NÃO pergunte de novo
- Após saber a empresa e SE tiver site, você pode perguntar: "Vocês tem site? Me manda o link se quiser, dou uma olhada rápida"

**CONDUÇÃO AO AGENDAMENTO:**
- Após 2-3 trocas de mensagem, SE o lead demonstrou interesse (fez perguntas, engajou), ofereça diagnóstico gratuito
- Seja natural: "Faz sentido marcarmos 1h? Faço um diagnóstico gratuito do seu cenário e te mostro como podemos ajudar."
- NÃO seja insistente se lead não quer agendar
- Se lead tiver mais dúvidas, continue respondendo mas sempre termine com pergunta
- **IMPORTANTE**: Se lead sugerir dia/horário específico, apenas confirme verbalmente - o sistema cria o evento automaticamente

**REGRAS CRÍTICAS:**
1. ✅ SEMPRE termine sua resposta com uma PERGUNTA (exceto quando lead já agendou)
2. ✅ Seja breve (2-4 linhas no máximo por resposta)
3. ✅ Não liste múltiplas features - foque no benefício pro lead
4. ✅ Use linguagem natural de WhatsApp (não pareça bot)
5. ❌ NUNCA termine com "Estou à disposição" sem fazer pergunta
6. ❌ NUNCA deixe a conversa "morrer" - sempre dê próximo passo

**EXEMPLOS DE RESPOSTAS BOAS:**

Pergunta: "A IA é humanizada?"
❌ Ruim: "Sim, nossa IA é humanizada e eficiente. Qualquer dúvida estou à disposição!"
✅ Bom: "Totalmente! Nossos agentes conversam naturalmente, entendem contexto e até detectam o tom do lead. Não parece robô, sabe? 😊

Me conta, o atendimento de vocês hoje é manual ou já usa alguma automação?"

Pergunta: "Quanto custa?"
❌ Ruim: "Depende do projeto. Varia bastante."
✅ Bom: "Depende da solução, mas te dou exemplos: ClinicFlow AI (clínicas), Automação WhatsApp e AutomateX Enterprise (integrações customizadas) variam de acordo com volume e integrações. A maioria dos clientes recupera o investimento em 3-4 meses pela economia de tempo e aumento de conversão.

Qual o principal gargalo que vocês enfrentam hoje? Perda de leads, sobrecarga da equipe ou dificuldade pra escalar?"

Pergunta: "Vocês atendem meu segmento?"
❌ Ruim: "Sim, atendemos diversos segmentos!"
✅ Bom: "Trabalhamos principalmente com clínicas (ClinicFlow AI) e empresas que precisam de soluções customizadas (AutomateX Enterprise). Também desenvolvemos sistemas, apps e RPA. Já automatizamos de escola a e-commerce. 😄

Qual seu segmento? Te conto se já temos cases parecidos."
"""

    async def process_message(
        self,
        message: str,
        lead: Lead,
        conversation_state: ConversationState,
        message_history: List[Message]
    ) -> str:
        """
        Processa mensagem do lead e gera resposta inteligente

        Args:
            message: Mensagem atual do lead
            lead: Dados do lead
            conversation_state: Estado atual da conversa
            message_history: Histórico de mensagens

        Returns:
            Resposta do Smith
        """
        try:
            logger.info(f"🤖 Processando mensagem com IA: {message[:50]}...")

            # Construir contexto da conversa
            context = self._build_context(lead, conversation_state, message_history)

            # Criar prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("system", f"**CONTEXTO DA CONVERSA:**\n{context}"),
                ("human", message)
            ])

            # Gerar resposta
            chain = prompt | self.model
            response = await chain.ainvoke({})

            response_text = response.content
            logger.success(f"✅ Resposta gerada: {response_text[:100]}...")

            return response_text

        except Exception as e:
            logger.error(f"❌ Erro ao processar com IA: {str(e)}")
            # Fallback para resposta genérica
            return "Desculpe, tive um problema para processar sua mensagem. Pode reformular? 🤔"

    def detected_scheduling_intent(self, message: str) -> bool:
        """
        Detecta se lead quer agendar reunião

        Args:
            message: Mensagem do lead

        Returns:
            True se detectou intenção de agendamento
        """
        message_lower = message.lower()

        # Palavras que indicam hesitação ou que o lead NÃO está pronto para agendar
        negative_keywords = [
            "duvida",
            "dúvida",
            "antes de",
            "mas",
            "porém",
            "porem",
            "ainda não",
            "ainda nao",
            "não sei",
            "nao sei",
            "talvez",
            "primeiro",
            "preciso saber",
            "gostaria de saber",
            "pode explicar",
            "como funciona",
            "quanto custa",
            "qual o preço",
            "qual o preco"
        ]

        # Se tem palavras negativas, NÃO é intenção de agendar
        if any(neg in message_lower for neg in negative_keywords):
            return False

        # Palavras que indicam FORTE intenção de agendamento
        strong_keywords = [
            "quero agendar",
            "quero marcar",
            "vamos agendar",
            "vamos marcar",
            "pode agendar",
            "pode marcar",
            "horários disponíveis",
            "horarios disponiveis",
            "horários livres",
            "horarios livres",
            "agenda livre",
            "quando você pode",
            "quando voce pode",
            "sugere horários",
            "sugere horarios",
            "mostre horários",
            "mostre horarios"
        ]

        # Se tem palavras fortes, É intenção de agendar
        if any(strong in message_lower for strong in strong_keywords):
            return True

        # Se não tem negativas nem fortes, não assume intenção de agendamento
        return False

    def _build_context(
        self,
        lead: Lead,
        conversation_state: ConversationState,
        message_history: List[Message]
    ) -> str:
        """
        Constrói contexto da conversa para a IA
        """
        # Verificar se empresa é válida (não é teste/desconhecida)
        empresa_valida = lead.empresa and not any(
            termo in lead.empresa.lower()
            for termo in ["teste", "test", "exemplo", "example", "ltda.", "s.a.", "me."]
        )

        # Se empresa for só "LTDA", "S.A.", "ME" etc, também considera inválida
        if lead.empresa and lead.empresa.strip() in ["LTDA", "S.A.", "ME", "LTDA.", "S.A.", "ME."]:
            empresa_valida = False

        # Informações do lead
        context_parts = [
            f"Nome do lead: {lead.nome}",
            f"Empresa: {lead.empresa if empresa_valida else 'Não informado - PERGUNTE NATURALMENTE!'}",
            f"Status: {lead.status if isinstance(lead.status, str) else lead.status.value}",
        ]

        if lead.temperatura:
            temp_value = lead.temperatura if isinstance(lead.temperatura, str) else lead.temperatura.value
            context_parts.append(f"Temperatura: {temp_value}")

        # IMPORTANTE: Indicar se precisa coletar empresa
        if not empresa_valida:
            context_parts.append("\n⚠️ ATENÇÃO: Você NÃO sabe o nome da empresa ainda. Inclua a pergunta naturalmente após responder a dúvida do lead.")

        # Estado da conversa
        if conversation_state:
            state_value = conversation_state if isinstance(conversation_state, str) else conversation_state.value
            context_parts.append(f"\nEstado atual: {state_value}")
        elif not message_history:
            # Só diz "primeira interação" se não tem histórico
            context_parts.append(f"\nEstado atual: Primeira interação")

        # Histórico recente (últimas 5 mensagens)
        if message_history:
            context_parts.append("\n**Histórico da conversa:**")
            for msg in message_history[-10:]:  # Últimas 10 mensagens (5 trocas)
                # Suportar tanto objetos Message quanto dicts simples
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    direction = "Lead" if role == "user" else "Smith"
                else:
                    # Objeto Message
                    direction_value = msg.direction if isinstance(msg.direction, str) else msg.direction.value
                    direction = "Lead" if direction_value == "inbound" else "Smith"
                    content = msg.content

                context_parts.append(f"{direction}: {content}")

        return "\n".join(context_parts)
