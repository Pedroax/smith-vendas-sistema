"""
API de Webhook - UAZAPI (WhatsApp)
Processa mensagens recebidas via UAZAPI e aciona o agente Smith com LangGraph

Este webhook:
1. Recebe payload UAZAPI
2. Converte para formato Evolution API (compatibilidade)
3. Adiciona mensagem ao buffer (debouncer)
4. Retorna 200 OK imediatamente
5. Processa em background após X segundos de silêncio
6. Envia resposta via UAZAPI
"""
from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from datetime import datetime
import uuid
import asyncio

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
from app.services.message_debouncer import get_message_debouncer
from app.services.conversation_memory import load_conversation_history
from app.agent import smith_agent, smith_graph, AgentState
from langchain_core.messages import HumanMessage, AIMessage
from app.repository.leads_repository import LeadsRepository

router = APIRouter()

# Instanciar serviços
repository = LeadsRepository()
uazapi_service = get_uazapi_service()
message_debouncer = get_message_debouncer(wait_seconds=2.5)


@router.post("/uazapi")
async def webhook_uazapi(request: Request):
    """
    Webhook para receber mensagens do WhatsApp via UAZAPI

    Fluxo:
    1. Recebe webhook UAZAPI
    2. Converte para formato Evolution (adaptador)
    3. Extrai dados (phone, message, name)
    4. Adiciona mensagem ao buffer (debouncer)
    5. Retorna 200 OK IMEDIATAMENTE
    6. Processamento acontece em background após X segundos de silêncio
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

        # 🧪 COMANDO DE TESTE: /delete - Resetar memória completamente
        if message_text.strip().lower() == "/delete":
            logger.warning(f"🗑️ Comando /delete recebido de {push_name} ({phone})")
            logger.info(f"🔍 DEBUG: Criando task para handle_delete_command")
            task = asyncio.create_task(
                handle_delete_command(phone, push_name)
            )
            logger.info(f"🔍 DEBUG: Task criada: {task}")
            return {
                "status": "command_executed",
                "command": "delete",
                "phone": phone
            }

        # 🔥 ADICIONAR AO BUFFER (não aguarda processamento)
        # O debouncer processará após 2.5s de silêncio
        asyncio.create_task(
            message_debouncer.add_message(
                phone=phone,
                message=message_text,
                callback=process_buffered_message,
                push_name=push_name
            )
        )

        # ✅ RETORNAR IMEDIATAMENTE (não bloqueia webhook)
        return {
            "status": "buffered",
            "phone": phone,
            "message_length": len(message_text),
            "buffer_wait_seconds": message_debouncer.wait_seconds
        }

    except HTTPException:
        raise
    except Exception as e:
        # ✅ Use str(e) para evitar KeyError quando e é um dict
        logger.error(f"❌ Erro no webhook UAZAPI: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def process_buffered_message(phone: str, combined_message: str, push_name: str):
    """
    Processa mensagem(ns) combinada(s) após buffer

    Esta função é chamada pelo debouncer após X segundos de silêncio.
    Recebe todas as mensagens enviadas pelo usuário combinadas com \\n

    Args:
        phone: Telefone do usuário (sem @s.whatsapp.net)
        combined_message: Mensagens combinadas separadas por \\n
        push_name: Nome do contato
    """
    try:
        logger.info(f"🔄 Processando mensagem buffered de {push_name} ({phone[:12]}...)")

        # Buscar ou criar lead
        lead = await get_or_create_lead(phone, push_name)

        # Adicionar mensagem combinada ao banco
        await repository.add_conversation_message(
            lead_id=lead.id,
            role="user",
            content=combined_message
        )

        # Adicionar mensagem ao histórico (em memória para o agente processar)
        user_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=combined_message,
            timestamp=datetime.now()
        )
        lead.conversation_history.append(user_message)
        lead.ultima_interacao = datetime.now()

        # 🤖 PROCESSAR COM O AGENTE SMITH (LangGraph)
        response_text, show_calendar = await process_with_agent(lead, combined_message)

        # Adicionar resposta da IA ao histórico
        ai_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=response_text,
            timestamp=datetime.now()
        )
        lead.conversation_history.append(ai_message)
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
            "empresa": lead.empresa,
            "email": lead.email,
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

        # 📤 ENVIAR RESPOSTA VIA UAZAPI
        success = uazapi_service.send_text_message(phone, response_text)

        if success:
            logger.success(f"✅ Resposta enviada via UAZAPI para {push_name}")
            if show_calendar:
                logger.info(f"📅 Lead qualificado - calendário disponível")
        else:
            logger.error(f"❌ Falha ao enviar resposta via UAZAPI")

    except Exception as e:
        logger.error(
            f"❌ Erro ao processar mensagem buffered de {phone[:12]}...: {str(e)}",
            exc_info=True
        )


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


async def handle_delete_command(phone: str, push_name: str):
    """
    Processa comando /delete - Reseta memória e dados do lead

    Este comando é útil para testes e permite recomeçar
    uma conversa do zero, limpando todo histórico.

    Args:
        phone: Telefone do lead (sem @s.whatsapp.net)
        push_name: Nome do contato
    """
    logger.warning(f"🔍 DEBUG: handle_delete_command INICIADA para {phone}")
    try:
        logger.info(f"🗑️ Executando comando /delete para {push_name} ({phone})")

        # Buscar lead existente
        existing_lead = await repository.get_by_telefone(phone)

        if not existing_lead:
            # Lead não existe, apenas enviar mensagem de "já está limpo"
            confirmation_msg = (
                "✅ SEM DADOS PARA LIMPAR!\n\n"
                "🆕 Você ainda não tem histórico conosco.\n"
                "Pode começar uma conversa nova agora!"
            )
            uazapi_service.send_text_message(phone, confirmation_msg)
            logger.info(f"⚪ Lead {phone} não existe - nada para deletar")
            return

        lead_id = existing_lead.id
        lead_nome = existing_lead.nome

        logger.info(f"🔍 Lead encontrado: {lead_nome} (ID: {lead_id})")

        # 🧹 LIMPAR HISTÓRICO DE CONVERSAS (conversation_messages)
        from app.services.conversation_memory import SupabaseChatMemory

        memory = SupabaseChatMemory(lead_id=lead_id)
        message_count = await memory.get_message_count()

        await memory.clear_history()
        logger.success(f"🗑️ {message_count} mensagens deletadas do histórico")

        # 🔄 RESETAR DADOS DO LEAD (RESET COMPLETO - LIMPAR TUDO!)
        # NOMES EXATOS DAS COLUNAS CONFIRMADOS NO SUPABASE DASHBOARD
        reset_data = {
            # Status básico
            "status": LeadStatus.NOVO.value,
            "temperatura": LeadTemperature.FRIO.value,
            "lead_score": 0,

            # Limpar informações de contato/empresa
            "empresa": None,
            "email": None,
            "cargo": None,
            "faturamento_anual": None,

            # Limpar qualificação (JSONB)
            "qualificacao_detalhes": None,

            # Limpar agendamento
            "meeting_scheduled_at": None,
            "meeting_google_event_id": None,

            # Limpar notas e tags
            "observacoes": None,
            "tags": [],
        }

        try:
            await repository.update(lead_id, reset_data)
            logger.success(f"♻️ Lead {lead_nome} resetado para estado inicial")
        except Exception as update_error:
            logger.warning(f"⚠️ Não foi possível resetar dados do lead: {str(update_error)}")
            # Continuar mesmo se falhar - o histórico já foi limpo

        # 📤 ENVIAR MENSAGEM DE CONFIRMAÇÃO
        confirmation_msg = (
            "✅ MEMÓRIA RESETADA COMPLETAMENTE!\n\n"
            "🧹 Todo seu histórico foi limpo:\n"
            f"   • {message_count} conversas anteriores\n"
            "   • Mensagens\n"
            "   • Agendamentos\n"
            "   • Dados salvos\n\n"
            "🆕 Podemos começar uma nova conversa do zero!"
        )

        logger.warning(f"🔍 DEBUG: Enviando confirmação para {phone}")
        logger.warning(f"🔍 DEBUG: Mensagem: {confirmation_msg[:100]}...")
        success = uazapi_service.send_text_message(phone, confirmation_msg)
        logger.warning(f"🔍 DEBUG: Resultado do envio: {success}")

        if success:
            logger.success(
                f"✅ Comando /delete executado com sucesso para {lead_nome} "
                f"({message_count} mensagens deletadas)"
            )
        else:
            logger.error(f"❌ Falha ao enviar confirmação do /delete")

    except Exception as e:
        logger.error(
            f"❌ Erro ao processar comando /delete para {phone}: {str(e)}",
            exc_info=True
        )

        # Enviar mensagem de erro
        error_msg = (
            "❌ Erro ao limpar memória.\n\n"
            "Por favor, tente novamente em alguns instantes."
        )
        uazapi_service.send_text_message(phone, error_msg)


@router.get("/uazapi/buffer/stats")
async def get_buffer_stats():
    """
    Retorna estatísticas do buffer de mensagens

    Útil para debug e monitoramento
    """
    stats = message_debouncer.get_stats()
    return {
        "status": "ok",
        "debouncer": {
            "wait_seconds": message_debouncer.wait_seconds,
            "active_timers": stats["active_timers"],
            "pending_messages": stats["pending_messages"],
            "phones_waiting": stats["phones_waiting"]
        }
    }


async def process_with_agent(lead: Lead, message: str) -> tuple[str, bool]:
    """
    Processa mensagem com o agente Smith (LangGraph)

    Este método usa o LangGraph completo com:
    - Memória persistente (Supabase) - últimas 20 mensagens
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
        # 🧠 CARREGAR HISTÓRICO DO BANCO (últimas 20 mensagens)
        logger.info(f"📚 Carregando histórico de conversas para lead {lead.id}")
        messages = await load_conversation_history(
            lead_id=lead.id,
            max_messages=20  # Últimas 20 mensagens (10 trocas)
        )

        # Adicionar mensagem atual ao histórico (já foi salva no banco)
        messages.append(HumanMessage(content=message))

        logger.info(
            f"🔄 Processando com {len(messages)} mensagens de contexto "
            f"(lead: {lead.nome})"
        )

        # Montar estado inicial para o LangGraph
        initial_state = AgentState(
            messages=messages,
            lead=lead,
            current_stage=lead.status.value if hasattr(lead.status, 'value') else lead.status,
            next_action="continue",
            requires_human_approval=False,
            available_slots=[]
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
        if result.get("next_action") == "schedule":
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
