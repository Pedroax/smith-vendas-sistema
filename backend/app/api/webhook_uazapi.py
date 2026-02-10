"""
API de Webhook - UAZAPI (WhatsApp)
Processa mensagens recebidas via UAZAPI e aciona o agente Smith com LangGraph

Este webhook:
1. Recebe payload UAZAPI
2. Converte para formato Evolution API (compatibilidade)
3. Processa com smith_agent (LangGraph) - QUALIFICAÇÃO AUTOMÁTICA
4. Envia resposta via UAZAPI
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
from app.services.uazapi_service import get_uazapi_service
from app.services.uazapi_adapter import (
    is_uazapi_webhook,
    adapt_uazapi_webhook,
    extract_phone_from_jid
)
from app.agent import smith_agent, smith_graph, AgentState
from langchain_core.messages import HumanMessage, AIMessage
from app.repository.leads_repository import LeadsRepository

router = APIRouter()

# Instanciar serviços
repository = LeadsRepository()
uazapi_service = get_uazapi_service()


@router.post("/uazapi")
async def webhook_uazapi(request: Request):
    """
    Webhook para receber mensagens do WhatsApp via UAZAPI

    Fluxo:
    1. Recebe webhook UAZAPI
    2. Converte para formato Evolution (adaptador)
    3. Extrai dados (phone, message, name)
    4. Cria/atualiza lead no banco
    5. Processa com smith_agent (LangGraph) - QUALIFICAÇÃO AUTOMÁTICA
    6. Agente responde automaticamente via UAZAPI
    """
    try:
        # Receber payload
        payload = await request.json()

        logger.info("📨 RAW WEBHOOK BODY (UAZAPI): " + str(payload)[:500])

        # 🔍 VERIFICAR SE É UAZAPI
        if not is_uazapi_webhook(payload):
            logger.warning("⚠️ Webhook não é UAZAPI - ignorando")
            return {"status": "ignored", "reason": "not_uazapi_format"}

        # 🔄 CONVERTER UAZAPI → EVOLUTION FORMAT
        try:
            payload_evolution = adapt_uazapi_webhook(payload)
            logger.info("🔄 Payload adaptado para formato Evolution")
        except Exception as e:
            logger.error(f"💥 Erro ao adaptar payload UAZAPI: {e}")
            raise HTTPException(status_code=400, detail="Invalid UAZAPI payload")

        # Extrair dados do payload adaptado (agora no formato Evolution)
        event = payload_evolution.get("event")
        data = payload_evolution.get("data", {})

        if event != "messages.upsert":
            logger.debug(f"Evento ignorado: {event}")
            return {"status": "ignored", "reason": f"event={event}"}

        # Extrair informações da mensagem
        key = data.get("key", {})
        remote_jid = key.get("remoteJid")
        from_me = key.get("fromMe", False)

        if from_me:
            logger.debug("Mensagem enviada por nós - ignorando")
            return {"status": "ignored", "reason": "message from me"}

        # Extrair telefone e mensagem
        phone = extract_phone_from_jid(remote_jid)
        push_name = data.get("pushName", "")
        message_obj = data.get("message", {})
        message_text = message_obj.get("conversation", "")

        if not message_text:
            logger.warning("Mensagem vazia recebida - ignorando")
            return {"status": "ignored", "reason": "empty_message"}

        logger.info(f"💬 Mensagem de {push_name} ({phone}): {message_text[:50]}...")

        # Buscar ou criar lead
        lead = await get_or_create_lead(phone, push_name)

        # Adicionar mensagem do usuário ao banco
        await repository.add_conversation_message(
            lead_id=lead.id,
            role="user",
            content=message_text
        )

        # Adicionar mensagem ao histórico (em memória para o agente processar)
        user_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=message_text,
            timestamp=datetime.now()
        )
        lead.conversation_history.append(user_message)
        lead.ultima_interacao = datetime.now()

        # 🤖 PROCESSAR COM O AGENTE SMITH (LangGraph)
        response_text, show_calendar = await process_with_agent(lead, message_text)

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
            "nome": lead.nome,
            # "ultima_mensagem_ia": response_text,  # ❌ Coluna não existe no Supabase
            "status": lead.status.value if hasattr(lead.status, 'value') else lead.status,
            "temperatura": lead.temperatura.value if hasattr(lead.temperatura, 'value') else lead.temperatura,
            "lead_score": lead.lead_score
        }

        if lead.qualification_data:
            update_data["qualification_data"] = lead.qualification_data.model_dump()

        if lead.roi_analysis:
            roi_dict = lead.roi_analysis.model_dump()
            if roi_dict.get("generated_at"):
                roi_dict["generated_at"] = roi_dict["generated_at"].isoformat()
            update_data["roi_analysis"] = roi_dict

        await repository.update(lead.id, update_data)

        # 📤 ENVIAR RESPOSTA VIA UAZAPI
        success = uazapi_service.send_text_message(phone, response_text)

        if success:
            logger.success(f"✅ Resposta enviada via UAZAPI para {push_name}")
        else:
            logger.error(f"❌ Falha ao enviar resposta via UAZAPI")

        response_data = {
            "status": "processed",
            "lead_id": lead.id,
            "lead_status": lead.status,
            "lead_score": lead.lead_score,
            "send_success": success
        }

        # Adicionar sinalizador de calendário se necessário
        if show_calendar:
            response_data["show_calendar"] = True
            response_data["calendar_url"] = "https://calendly.com/pedrohfmachado/agende-seu-horario"
            logger.info(f"📅 Lead qualificado - pode mostrar calendário")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        # ✅ Use str(e) para evitar KeyError quando e é um dict
        logger.error(f"❌ Erro no webhook UAZAPI: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def get_or_create_lead(phone: str, name: str) -> Lead:
    """
    Busca lead existente pelo telefone ou cria um novo

    Args:
        phone: Telefone do lead (sem @s.whatsapp.net)
        name: Nome do lead (do pushName)

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
        nome=name or "Lead",  # Se nome vazio, usar "Lead"
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

    logger.success(f"✨ Novo lead criado via UAZAPI: {name} ({lead_id})")

    return created_lead


async def process_with_agent(lead: Lead, message: str) -> tuple[str, bool]:
    """
    Processa mensagem com o agente Smith (LangGraph)

    Este método usa o LangGraph completo com:
    - Qualificação automática
    - Cálculo de score
    - Agendamento automático
    - Geração de ROI

    Args:
        lead: Lead que enviou a mensagem
        message: Conteúdo da mensagem

    Returns:
        Tupla (resposta gerada pelo agente, mostrar calendário)
    """
    show_calendar = False
    try:
        # Converter histórico de conversa para mensagens do LangChain
        messages = []
        for msg in lead.conversation_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        # Montar estado inicial para o LangGraph
        initial_state = AgentState(
            messages=messages,
            lead=lead,
            current_stage=lead.status.value if hasattr(lead.status, 'value') else lead.status,
            next_action="continue",
            requires_human_approval=False
        )

        logger.info(f"🤖 Processando com smith_agent (LangGraph): stage={initial_state['current_stage']}")

        # 🚀 EXECUTAR LANGGRAPH (QUALIFICAÇÃO AUTOMÁTICA)
        result = smith_graph.invoke(initial_state)

        # Extrair resposta da última mensagem do agente
        if result["messages"]:
            last_message = result["messages"][-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_text = "Desculpe, não consegui processar sua mensagem no momento."
            logger.warning("⚠️ smith_graph não retornou mensagens")

        # Atualizar lead com resultado do agente
        lead.status = LeadStatus(result["lead"].status) if isinstance(result["lead"].status, str) else result["lead"].status
        lead.lead_score = result["lead"].lead_score
        lead.temperatura = result["lead"].temperatura
        lead.qualification_data = result["lead"].qualification_data
        lead.roi_analysis = result["lead"].roi_analysis

        logger.success(
            f"✅ Agente processou: "
            f"status={lead.status}, "
            f"score={lead.lead_score}, "
            f"next_action={result.get('next_action')}"
        )

        # Verificar se deve mostrar calendário
        # (quando lead foi qualificado e escolheu agendar)
        if result.get("next_action") == "schedule_meeting":
            show_calendar = True

        return response_text, show_calendar

    except Exception as e:
        logger.error(f"💥 Erro ao processar com agente: {e}", exc_info=True)

        # Fallback: resposta genérica
        fallback_response = (
            "Desculpe, estou com dificuldades técnicas no momento. "
            "Pode repetir sua mensagem?"
        )

        return fallback_response, False
