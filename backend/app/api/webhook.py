"""
API de Webhook - WhatsApp Evolution API
Processa mensagens recebidas e aciona o agente Smith
"""
from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from datetime import datetime
import uuid

from app.models.lead import (
    Lead,
    LeadStatus,
    LeadOrigin,
    LeadTemperature,
    FollowUpConfig,
    ConversationMessage,
)
from app.services import whatsapp_service
from app.services.data_extractor import data_extractor
from app.agent import smith_agent, smith_graph, AgentState
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter()

# Importar repository para acesso ao banco
from app.repository.leads_repository import LeadsRepository

# Instanciar repository
repository = LeadsRepository()


@router.post("/whatsapp")
async def webhook_whatsapp(request: Request):
    """
    Webhook para receber mensagens do WhatsApp via Evolution API

    Fluxo:
    1. Recebe mensagem do WhatsApp
    2. Processa dados do webhook
    3. Cria/atualiza lead no banco
    4. Passa para o agente Smith processar
    5. Agente responde automaticamente
    """
    try:
        data = await request.json()
        event = data.get("event", "unknown")
        source = data.get("source", "whatsapp")  # "website" ou "whatsapp"

        logger.info(f"📱 Webhook recebido: {event} (source: {source})")

        # Processar apenas mensagens recebidas
        parsed = whatsapp_service.parse_webhook_message(data)

        if not parsed:
            logger.debug("Mensagem ignorada (enviada por nós ou tipo não suportado)")
            return {"status": "ignored"}

        phone = parsed["phone"]
        message = parsed["message"]
        name = parsed["name"]

        logger.info(f"💬 Mensagem de {name} ({phone}): {message[:50]}...")

        # Buscar ou criar lead
        lead = await get_or_create_lead(phone, name)

        # Se é mensagem de inicialização, apenas enviar saudação
        if message == "__INIT__":
            logger.info(f"🎬 Iniciando conversa com {lead.nome}")
            saudacao = """E aí! 👋 Sou o Smith, da AutomateX.

Vou te ajudar a descobrir quanto dinheiro você está perdendo por não usar IA no seu negócio.

Pra começar, qual seu nome?"""

            # Salvar saudação no histórico
            await repository.add_conversation_message(
                lead_id=lead.id,
                role="assistant",
                content=saudacao
            )

            # Atualizar lead
            await repository.update(lead.id, {
                "ultima_mensagem_ia": saudacao,
                "status": "contato_inicial"
            })

            return {
                "status": "processed",
                "lead_id": lead.id,
                "lead_status": "contato_inicial"
            }

        # Adicionar mensagem do usuário ao banco
        await repository.add_conversation_message(
            lead_id=lead.id,
            role="user",
            content=message
        )

        # Adicionar mensagem ao histórico (em memória para o agente processar)
        user_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=message,
            timestamp=datetime.now()
        )
        lead.conversation_history.append(user_message)
        lead.ultima_interacao = datetime.now()

        # Processar com o agente Smith
        response_text, show_calendar = await process_with_agent(lead, message)

        # Adicionar resposta da IA ao histórico
        ai_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=response_text,
            timestamp=datetime.now()
        )
        lead.conversation_history.append(ai_message)
        lead.ultima_mensagem_ia = response_text
        lead.updated_at = datetime.now()

        # Salvar mensagem no banco
        await repository.add_conversation_message(
            lead_id=lead.id,
            role="assistant",
            content=response_text
        )

        # Atualizar lead no banco
        update_data = {
            "nome": lead.nome,  # Atualizar nome se mudou
            "empresa": lead.empresa,
            "email": lead.email,
            "ultima_mensagem_ia": response_text,
            "status": lead.status.value if hasattr(lead.status, 'value') else lead.status,
            "temperatura": lead.temperatura.value if hasattr(lead.temperatura, 'value') else lead.temperatura,
            "lead_score": lead.lead_score
        }

        if lead.qualification_data:
            update_data["qualificacao_detalhes"] = lead.qualification_data.model_dump()

        if lead.roi_analysis:
            roi_dict = lead.roi_analysis.model_dump()
            if roi_dict.get("generated_at"):
                roi_dict["generated_at"] = roi_dict["generated_at"].isoformat()
            update_data["roi_analysis"] = roi_dict

        await repository.update(lead.id, update_data)

        # Enviar resposta via WhatsApp APENAS se source = "whatsapp"
        if source == "whatsapp":
            await whatsapp_service.send_text_message(phone, response_text)
            logger.success(f"✅ Resposta enviada via WhatsApp para {name}")
        else:
            logger.success(f"✅ Resposta processada para {name} (website chat)")

        response_data = {
            "status": "processed",
            "lead_id": lead.id,
            "lead_status": lead.status,
            "lead_score": lead.lead_score
        }

        # Adicionar sinalizador de calendário se necessário
        if show_calendar:
            response_data["show_calendar"] = True
            response_data["calendar_url"] = "https://calendly.com/pedrohfmachado/agende-seu-horario"
            logger.info(f"📅 Incluindo calendário na resposta para {name}")

        return response_data

    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def get_or_create_lead(phone: str, name: str) -> Lead:
    """
    Busca lead existente pelo telefone ou cria um novo

    Args:
        phone: Telefone do lead
        name: Nome do lead

    Returns:
        Lead encontrado ou criado
    """
    # Buscar lead existente pelo telefone
    existing_lead = await repository.get_by_telefone(phone)

    if existing_lead:
        logger.info(f"Lead existente encontrado: {existing_lead.nome} ({existing_lead.id})")
        # Carregar histórico de mensagens
        existing_lead.conversation_history = await repository.get_conversation_messages(existing_lead.id)
        return existing_lead

    # Criar novo lead
    lead_id = str(uuid.uuid4())

    lead = Lead(
        id=lead_id,
        nome=name,
        telefone=phone,
        status=LeadStatus.NOVO,
        origem=LeadOrigin.WHATSAPP,
        temperatura=LeadTemperature.MORNO,
        lead_score=0,
        valor_estimado=0,
        followup_config=FollowUpConfig(
            tentativas_realizadas=0,
            intervalo_horas=[24, 72, 168]
        ),
        conversation_history=[],
        tags=[],
        requires_human_approval=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Salvar no banco
    created_lead = await repository.create(lead)

    logger.success(f"✨ Novo lead criado: {name} ({lead_id})")

    return created_lead


async def process_with_agent(lead: Lead, message: str) -> tuple[str, bool]:
    """
    Processa mensagem com o agente Smith

    Args:
        lead: Lead que enviou a mensagem
        message: Conteúdo da mensagem

    Returns:
        Tupla (resposta gerada pelo agente, mostrar calendário)
    """
    show_calendar = False
    try:
        # Converter TODO o histórico de conversa para mensagens do LangChain
        # O histórico já inclui a mensagem atual do usuário (adicionada antes de chamar esta função)
        messages = []

        if lead.conversation_history:
            for msg in lead.conversation_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # lead.status vem do banco como string, não enum
        current_status = str(lead.status) if isinstance(lead.status, str) else lead.status.value

        state: AgentState = {
            "messages": messages,
            "lead": lead,
            "current_stage": current_status,
            "next_action": "qualify",
            "requires_human_approval": False
        }

        # Determinar qual node chamar baseado no status atual
        # Comparar com string pois lead.status vem do banco como string
        if str(lead.status) == LeadStatus.NOVO.value or str(lead.status) == "novo":
            # Primeiro contato
            state["next_action"] = "new"
            result = smith_agent.handle_new_lead(state)

        elif str(lead.status) in [LeadStatus.CONTATO_INICIAL.value, LeadStatus.QUALIFICANDO.value, "contato_inicial", "qualificando"]:
            # Continuar qualificação
            result = smith_agent.qualify_lead(state)

            # EXTRAIR dados do histórico de conversa (após cada resposta)
            extracted_data = data_extractor.extract_qualification_data(result["lead"])

            if extracted_data:
                # Atualizar qualification_data do lead
                result["lead"].qualification_data = extracted_data
                logger.info(f"📊 Dados atualizados para {result['lead'].nome}")

            # CRITICAL: Respeitar o next_action definido pelo qualify_lead
            # Só chamar check_qualification se qualify_lead definiu isso explicitamente
            if result.get("next_action") == "check_qualification":
                logger.info(f"✅ {result['lead'].nome} - Todas informações coletadas, qualificando...")

                # Tentar qualificar - gera mensagem de awareness + direciona pro calendário
                result = await smith_agent.check_qualification(result)

                # Se qualificou, marcar para mostrar calendário no frontend
                if str(result["lead"].status) == LeadStatus.QUALIFICADO.value:
                    result["show_calendar"] = True
                    logger.success(f"🎯 {result['lead'].nome} QUALIFICADO - Mostrar calendário no frontend")
            else:
                logger.debug(f"⏳ {result['lead'].nome} ainda coletando informações...")

        elif str(lead.status) == LeadStatus.QUALIFICADO.value or str(lead.status) == "qualificado":
            # Lead já qualificado - tentar processar agendamento
            logger.info(f"💬 {lead.nome} já qualificado, verificando se é agendamento...")

            # Tentar extrair data/hora da mensagem
            from app.services.appointment_processor import appointment_processor
            extracted_datetime = await appointment_processor.extract_datetime_from_message(message)

            if extracted_datetime and extracted_datetime.confidence >= 0.6:
                # Lead informou horário - processar agendamento
                logger.info(f"📅 Processando agendamento para {lead.nome}: {extracted_datetime.datetime}")

                # Validar horário
                is_valid, reason = appointment_processor.is_valid_meeting_time(extracted_datetime.datetime)

                if is_valid:
                    # Criar evento no Google Calendar
                    from app.services.google_calendar_service import google_calendar_service
                    from app.repository.agendamentos_repository import AgendamentosRepository
                    from app.models.agendamento import Agendamento, AgendamentoStatus

                    meeting_data = await google_calendar_service.create_meeting(
                        lead_name=lead.nome,
                        lead_email=lead.email,
                        lead_phone=lead.telefone,
                        meeting_datetime=extracted_datetime.datetime,
                        duration_minutes=30,
                        empresa=lead.empresa
                    )

                    if meeting_data:
                        # Salvar agendamento no banco
                        agendamentos_repo = AgendamentosRepository()

                        agendamento = Agendamento(
                            id=str(uuid.uuid4()),
                            lead_id=lead.id,
                            data_hora=extracted_datetime.datetime,
                            duracao_minutos=30,
                            google_event_id=meeting_data.get("event_id"),
                            google_meet_link=meeting_data.get("meet_link"),
                            google_event_link=meeting_data.get("event_link"),
                            status=AgendamentoStatus.AGENDADO,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )

                        await agendamentos_repo.create(agendamento)

                        # Atualizar status do lead
                        lead.status = LeadStatus.AGENDAMENTO_MARCADO
                        lead.lead_score = 95

                        # Gerar mensagem de confirmação
                        from langchain_core.messages import SystemMessage
                        data_formatada = extracted_datetime.datetime.strftime("%A, %d/%m às %H:%M")

                        confirmation_prompt = f"""Você é Smith da AutomateX.

Use o template de confirmação de agendamento substituindo {{data_hora_formatada}} por: {data_formatada}

Template:
"Agendado! {data_formatada} 📅

Você vai receber um email com o convite do Google Calendar + link do Meet.

Te vejo lá! 🚀"

Gere a mensagem de confirmação natural e empolgante."""

                        confirmation_response = smith_agent.llm.invoke([SystemMessage(content=confirmation_prompt)])
                        response_text = confirmation_response.content

                        # Adicionar ao histórico
                        state["messages"].append(HumanMessage(content=message))
                        state["messages"].append(confirmation_response)

                        # Criar result mock para continuar o fluxo
                        result = {
                            "messages": state["messages"],
                            "lead": lead,
                            "current_stage": "agendamento_marcado",
                            "next_action": "end"
                        }

                        logger.success(f"✅ Reunião agendada para {lead.nome}: {data_formatada}")
                    else:
                        logger.error(f"❌ Erro ao criar evento no Google Calendar")
                        # Fallback - continuar conversa normal
                        result = smith_agent.qualify_lead(state)
                else:
                    logger.warning(f"⚠️ Horário inválido sugerido por {lead.nome}: {reason}")
                    # Sugerir horários alternativos
                    alternatives = await appointment_processor.suggest_alternative_times()

                    alt_text = "\n".join([
                        f"- {alt.strftime('%A, %d/%m às %H:%M')}"
                        for alt in alternatives[:3]
                    ])

                    fallback_msg = f"""Hmm, {reason.lower()}.

Que tal um desses horários?
{alt_text}

Qual funciona pra você?"""

                    state["messages"].append(HumanMessage(content=message))
                    state["messages"].append(AIMessage(content=fallback_msg))

                    result = {
                        "messages": state["messages"],
                        "lead": lead,
                        "current_stage": "qualificado",
                        "next_action": "await_scheduling"
                    }
            else:
                # Não conseguiu extrair horário - continuar conversa normal
                logger.debug(f"⏳ Não consegui extrair horário da mensagem de {lead.nome}")
                result = smith_agent.qualify_lead(state)

        else:
            # Estado padrão - continuar conversa
            result = smith_agent.qualify_lead(state)

        # Atualizar lead com resultado do agente
        lead.status = result["lead"].status
        lead.temperatura = result["lead"].temperatura
        lead.lead_score = result["lead"].lead_score

        # Atualizar nome se mudou (importante para quando captura o nome do lead)
        if result["lead"].nome and result["lead"].nome != lead.nome:
            lead.nome = result["lead"].nome

        if result["lead"].qualification_data:
            lead.qualification_data = result["lead"].qualification_data

        if result["lead"].roi_analysis:
            lead.roi_analysis = result["lead"].roi_analysis

        if result["lead"].ai_summary:
            lead.ai_summary = result["lead"].ai_summary

        # Capturar sinalizador de calendário
        if result.get("show_calendar", False):
            show_calendar = True

        # Extrair resposta da IA
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)

        logger.info(f"🤖 Resposta do agente ({lead.status}): {response_text[:100]}...")

        return response_text, show_calendar

    except Exception as e:
        logger.error(f"Erro ao processar com agente: {e}", exc_info=True)
        # Fallback - resposta genérica
        return "Desculpe, tive um problema técnico. Pode repetir sua mensagem?", False


@router.get("/whatsapp/status")
async def webhook_status():
    """
    Status do webhook

    Returns:
        Status atual do webhook
    """
    try:
        # Verificar conexão com WhatsApp
        wa_status = await whatsapp_service.get_instance_status()

        # Buscar estatísticas do banco
        stats = await repository.get_stats()
        total_leads = stats.get("total_leads", 0)

        return {
            "webhook": "active",
            "whatsapp_connection": wa_status.get("state", "unknown"),
            "total_leads": total_leads,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return {
            "webhook": "error",
            "error": str(e)
        }


@router.post("/test")
async def test_webhook():
    """
    Endpoint de teste para simular mensagem

    Returns:
        Resultado do teste
    """
    # Mensagem de teste
    test_data = {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": "5521999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "test123"
            },
            "pushName": "Lead Teste",
            "message": {
                "conversation": "Olá, gostaria de saber mais sobre automação com IA"
            }
        }
    }

    # Criar request fake
    class FakeRequest:
        async def json(self):
            return test_data

    # Processar
    result = await webhook_whatsapp(FakeRequest())

    return {
        "test": "completed",
        "result": result
    }
