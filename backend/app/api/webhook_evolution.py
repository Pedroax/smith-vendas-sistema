"""
Webhook para receber mensagens do WhatsApp via Evolution API
"""
from fastapi import APIRouter, Request, HTTPException
from loguru import logger
from typing import Dict, Any, Set, List

from app.repository.leads_repository import LeadsRepository
from app.services.smith_ai_service import SmithAIService
from app.services.evolution_service import evolution_service
from app.services.google_calendar_service import google_calendar_service
from app.services.conversation_storage_service import conversation_storage

router = APIRouter()

# Cache de mensagens já processadas (evitar duplicatas)
_processed_messages: Set[str] = set()


@router.post("/webhook/evolution")
async def evolution_webhook(request: Request):
    """
    Webhook para receber mensagens do WhatsApp via Evolution API

    A Evolution API envia eventos quando:
    - Mensagem recebida
    - Mensagem enviada
    - Status de mensagem atualizado
    - Etc
    """
    try:
        payload = await request.json()
        logger.info(f"📨 Webhook Evolution recebido: {payload.get('event', 'unknown')}")

        # Verificar tipo de evento
        event_type = payload.get("event")

        if event_type == "messages.upsert":
            # Mensagem recebida
            await _process_incoming_message(payload)
        elif event_type == "messages.update":
            # Status de mensagem atualizado (lido, entregue, etc)
            logger.debug(f"Status atualizado: {payload}")
        else:
            logger.debug(f"Evento não processado: {event_type}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook Evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_incoming_message(payload: Dict[str, Any]):
    """
    Processa mensagem recebida do lead
    """
    try:
        # Inicializar variável de resposta como string vazia
        response = ""

        data = payload.get("data", {})

        # Extrair informações da mensagem
        message_data = data.get("message", {})
        key = data.get("key", {})

        # ID da mensagem (para evitar duplicados)
        message_id = key.get("id")

        # Verificar se já processamos esta mensagem
        if message_id in _processed_messages:
            logger.debug(f"⏭️ Mensagem {message_id} já processada, ignorando")
            return

        # Marcar como processada
        _processed_messages.add(message_id)

        # Limpar cache se ficar muito grande (manter apenas últimas 1000)
        if len(_processed_messages) > 1000:
            _processed_messages.clear()

        # Verificar se mensagem é do lead (não é nossa)
        from_me = key.get("fromMe", False)
        if from_me:
            logger.debug("Mensagem enviada por nós, ignorando")
            return

        # Extrair telefone (remoteJid)
        phone_raw = key.get("remoteJid", "")
        phone = phone_raw.split("@")[0]  # Remove @s.whatsapp.net

        # Extrair conteúdo
        message_type_raw = message_data.get("messageType", "conversation")
        conversation_text = message_data.get("conversation", "")
        extended_text = message_data.get("extendedTextMessage", {}).get("text", "")

        message_content = ""

        # ===== PROCESSAR ÁUDIO =====
        # Verificar múltiplas formas de detectar áudio
        is_audio = (
            message_type_raw == "audioMessage" or
            "audioMessage" in message_data or
            message_data.get("messageType") == "audioMessage"
        )

        if is_audio:
            logger.info(f"🎤 Áudio recebido de {phone}")

            # Importar serviços de áudio
            from app.services.audio_transcription_service import audio_transcription_service

            try:
                # Baixar áudio da Evolution API
                logger.info(f"📥 Iniciando download do áudio (message_id={message_id})...")
                audio_data = await evolution_service.download_media(
                    message_id=message_id,
                    media_type="audio"
                )

                if audio_data:
                    logger.success(f"✅ Áudio baixado com sucesso ({len(audio_data)} bytes)")
                else:
                    logger.error("❌ Não consegui baixar o áudio da Evolution API")
                    await evolution_service.send_text_message(
                        phone,
                        "Desculpe, não consegui processar seu áudio. Pode tentar enviar novamente ou escrever uma mensagem de texto?"
                    )
                    return

                # Transcrever áudio
                logger.info("🔄 Iniciando transcrição com Whisper...")
                transcribed_text = await audio_transcription_service.transcribe_audio(
                    audio_data=audio_data,
                    audio_format="ogg"
                )

                if not transcribed_text:
                    logger.error("❌ Whisper não conseguiu transcrever o áudio")
                    await evolution_service.send_text_message(
                        phone,
                        "Desculpe, não consegui entender seu áudio. Pode tentar enviar novamente ou escrever uma mensagem de texto?"
                    )
                    return

                # Áudio transcrito com sucesso
                message_content = transcribed_text
                logger.success(f"✅ Áudio transcrito com sucesso: '{message_content[:50]}...'")

            except Exception as e:
                logger.error(f"❌ Erro ao processar áudio: {str(e)}")
                await evolution_service.send_text_message(
                    phone,
                    "Desculpe, tive um problema ao processar seu áudio. Pode tentar enviar novamente ou escrever uma mensagem de texto?"
                )
                return

        # ===== PROCESSAR TEXTO =====
        else:
            message_content = conversation_text or extended_text or "[Mensagem não suportada]"

        logger.info(f"📱 Mensagem recebida de {phone}: {message_content[:50]}...")

        # Buscar lead por telefone
        lead_repo = LeadsRepository()
        lead = await lead_repo.get_by_telefone(phone)

        if not lead:
            logger.warning(f"⚠️ Lead não encontrado para telefone {phone}")
            # Responder gentilmente
            await evolution_service.send_text_message(
                phone,
                "Olá! Para melhor atendê-lo, preciso que você se cadastre primeiro. Entre em contato conosco!"
            )
            return

        # Processar com IA
        ai_service = SmithAIService()

        # Detectar se lead está confirmando/escolhendo um horário
        async def detect_time_selection(message: str):
            """Detecta se mensagem contém escolha de horário com dia + hora"""
            import re
            from datetime import datetime, timedelta
            import pytz

            SP_TZ = pytz.timezone('America/Sao_Paulo')
            message_lower = message.lower()

            # Detectar HORA
            hour_match = re.search(r'(\d{1,2}):?(\d{2})?(?:h|:)?', message_lower)
            if not hour_match:
                return None

            hour = int(hour_match.group(1))
            minute = int(hour_match.group(2)) if hour_match.group(2) else 0

            # Detectar DIA DA SEMANA
            dias_semana = {
                'segunda': 0, 'seg': 0,
                'terça': 1, 'terca': 1, 'ter': 1,
                'quarta': 2, 'qua': 2,
                'quinta': 3, 'qui': 3,
                'sexta': 4, 'sex': 4,
                'sábado': 5, 'sabado': 5, 'sab': 5,
                'domingo': 6, 'dom': 6
            }

            target_weekday = None
            for dia_nome, weekday in dias_semana.items():
                if dia_nome in message_lower:
                    target_weekday = weekday
                    break

            # Calcular data target
            now = datetime.now(SP_TZ)
            current_weekday = now.weekday()

            if target_weekday is not None:
                # Calcular próxima ocorrência do dia da semana
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Próxima semana
                target_date = now.date() + timedelta(days=days_ahead)
            else:
                # Sem dia específico, assume próximo dia útil
                target_date = now.date() + timedelta(days=1)

            # Criar datetime target
            target_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=SP_TZ)
            target_dt = target_dt.replace(hour=hour, minute=minute)

            logger.info(f"🎯 Horário detectado: {target_dt.strftime('%A, %d/%m às %H:%M')}")

            return {"target_datetime": target_dt}

        # Verificar se é escolha natural de horário (ex: "segunda às 13h", "pode ser terça 14h")
        selected_slot_natural = await detect_time_selection(message_content)

        if selected_slot_natural:
            logger.info(f"📅 Lead escolheu horário naturalmente: {message_content[:50]}")

            target_dt = selected_slot_natural['target_datetime']

            # Tentar criar evento no Google Calendar
            event = await google_calendar_service.create_meeting(
                lead_name=lead.nome,
                lead_email=lead.email or f"{phone}@whatsapp.temp",
                lead_phone=phone,
                meeting_datetime=target_dt,
                duration_minutes=60,
                empresa=lead.empresa
            )

            if event:
                horario_formatado = google_calendar_service._format_slot_display(target_dt)

                response = f"""✅ Perfeito, {lead.nome.split()[0]}!

Sua reunião está confirmada para *{horario_formatado}*.

Vou te enviar um lembrete antes. Até lá! 🚀"""

                logger.success(f"✅ Reunião criada no Google Calendar: {event.get('id')}")
            else:
                # Evento não criado (provavelmente conflito)
                response = f"""Ops, {lead.nome.split()[0]}! 😅

O horário que você sugeriu ({target_dt.strftime('%d/%m às %H:%M')}) já está ocupado na agenda.

Me deixa ver os horários que tenho livres?"""

                # Buscar e enviar horários disponíveis
                available_slots = await google_calendar_service.get_available_slots(days_ahead=7)
                if available_slots:
                    if len(available_slots) == 1:
                        horarios_text = f"*{available_slots[0]['display']}*"
                    elif len(available_slots) == 2:
                        horarios_text = f"*{available_slots[0]['display']}* ou *{available_slots[1]['display']}*"
                    else:
                        horarios_parts = [f"*{slot['display']}*" for slot in available_slots[:-1]]
                        horarios_text = ", ".join(horarios_parts) + f" ou *{available_slots[-1]['display']}*"

                    response += f"\n\nTenho disponibilidade em:\n{horarios_text}\n\nQual funciona melhor?"

            await evolution_service.send_text_message(phone, response)
            logger.success(f"✅ Resposta enviada para {lead.nome}")
            return

        # Verificar se é escolha de horário (1, 2 ou 3)
        message_stripped = message_content.strip()
        if message_stripped in ["1", "2", "3"]:
            logger.info(f"📅 Lead escolheu horário {message_stripped}")

            # Buscar horários disponíveis
            available_slots = await google_calendar_service.get_available_slots(days_ahead=7)

            if available_slots:
                try:
                    slot_index = int(message_stripped) - 1
                    selected_slot = available_slots[slot_index]

                    # Extrair datetime do slot (pode ser dict ou datetime)
                    if isinstance(selected_slot, dict):
                        slot_dt = selected_slot['start']
                    else:
                        slot_dt = selected_slot

                    # Criar evento no Google Calendar
                    event = await google_calendar_service.create_meeting(
                        lead_name=lead.nome,
                        lead_email=lead.email or f"{phone}@whatsapp.temp",
                        lead_phone=phone,
                        meeting_datetime=slot_dt,
                        duration_minutes=60,
                        empresa=lead.empresa
                    )

                    if event:
                        # Usar o display formatado em português do slot original
                        horario_formatado = selected_slot.get('display') if isinstance(selected_slot, dict) else google_calendar_service._format_slot_display(slot_dt)

                        response = f"""✅ Perfeito, {lead.nome.split()[0]}!

Sua reunião está confirmada para *{horario_formatado}*.

Vou te enviar um lembrete mais perto da data. Até lá! 🚀"""

                        logger.success(f"✅ Reunião criada no Google Calendar: {event.get('id')}")
                    else:
                        response = "Ops! Houve um problema ao agendar. Pode tentar outro horário?"

                except (IndexError, ValueError):
                    response = "Por favor, escolha um número válido (1, 2 ou 3) 😊"
            else:
                response = "Desculpe, não encontrei horários disponíveis no momento. Pode aguardar um momento?"

            # Enviar resposta
            await evolution_service.send_text_message(phone, response)
            logger.success(f"✅ Resposta enviada para {lead.nome}")
            return

        # Detectar se lead quer agendar
        wants_to_schedule = ai_service.detected_scheduling_intent(message_content)

        if wants_to_schedule:
            logger.info("🗓️ Lead quer agendar! Buscando horários disponíveis...")

            # Buscar horários reais do Google Calendar
            available_slots = await google_calendar_service.get_available_slots(days_ahead=7)

            if available_slots:
                # Formatar horários de forma natural usando o 'display' já formatado em português
                if len(available_slots) == 1:
                    horarios_text = f"*{available_slots[0]['display']}*"
                elif len(available_slots) == 2:
                    horarios_text = f"*{available_slots[0]['display']}* ou *{available_slots[1]['display']}*"
                else:
                    horarios_parts = [f"*{slot['display']}*" for slot in available_slots[:-1]]
                    horarios_text = ", ".join(horarios_parts) + f" ou *{available_slots[-1]['display']}*"

                response = f"""Ótimo, {lead.nome.split()[0]}! 😊

Acabei de verificar a agenda e tenho disponibilidade em:

{horarios_text}

Qual desses funciona melhor pra você? Se preferir outro horário, é só me avisar!"""
            else:
                response = f"Opa, {lead.nome}! No momento não tenho horários disponíveis na agenda. Deixa eu verificar com a equipe e te aviso em breve! 😊"

        else:
            # ===== FLUXO DE QUALIFICAÇÃO COM ESTADOS =====

            # 1. Buscar ou criar conversa no Supabase
            conversation_id = await conversation_storage.get_or_create_conversation(
                phone=phone,
                lead_id=int(lead.id)
            )

            if not conversation_id:
                logger.error("Erro ao criar conversa, usando fallback")
                response = "Desculpe, tive um problema técnico. Pode tentar novamente em alguns segundos?"
                await evolution_service.send_text_message(phone, response)
                return

            # 2. Buscar estado atual da conversa
            conv_state = await conversation_storage.get_conversation_state(conversation_id)
            current_state = conv_state.get("state", "inicial") if conv_state else "inicial"
            qualification_count = conv_state.get("qualification_message_count", 0) if conv_state else 0
            website_researched = conv_state.get("website_researched") if conv_state else None

            logger.info(f"📊 Estado atual: {current_state} | Mensagens: {qualification_count}")

            # 3. Recuperar histórico do Supabase (últimas 10 mensagens)
            history = await conversation_storage.get_conversation_history(
                conversation_id=conversation_id,
                limit=10
            )

            # 4. Salvar mensagem do lead no Supabase
            await conversation_storage.save_message(
                conversation_id=conversation_id,
                direction="inbound",
                content=message_content,
                evolution_message_id=message_id
            )

            # ===== FLUXO CONVERSACIONAL NATURAL =====

            from app.services.website_research_service import website_research_service

            # 1. DETECÇÃO AUTOMÁTICA DE EMPRESA (se ainda não tem ou é valor de teste)
            empresa_invalida = (
                not lead.empresa or
                any(termo in lead.empresa.lower() for termo in ["teste", "test", "exemplo", "example"])
            )

            if empresa_invalida:
                # Tentar detectar nome da empresa na mensagem
                # Palavras-chave que indicam menção de empresa
                empresa_keywords = ["trabalho na", "trabalho no", "sou da", "sou do", "empresa", "minha empresa é"]
                message_lower = message_content.lower()

                for keyword in empresa_keywords:
                    if keyword in message_lower:
                        # Extrair nome após keyword
                        parts = message_lower.split(keyword)
                        if len(parts) > 1:
                            empresa_candidata = parts[1].split()[0:3]  # Pegar até 3 palavras
                            empresa_nome = " ".join(empresa_candidata).strip('.,!?')
                            if len(empresa_nome) > 2:
                                await lead_repo.update_empresa(lead_id=lead.id, empresa=empresa_nome.title())
                                logger.info(f"🏢 Empresa detectada automaticamente: {empresa_nome}")
                                # Recarregar lead
                                lead = await lead_repo.get_by_telefone(phone)
                                break

            # 2. DETECÇÃO AUTOMÁTICA DE URL (pesquisa oportunista)
            url_detected = website_research_service.extract_url(message_content)

            if url_detected and not website_researched:
                logger.info(f"🔗 URL detectada automaticamente: {url_detected}")

                # Enviar mensagem de "digitando..."
                await evolution_service.send_text_message(
                    phone,
                    "Deixa eu dar uma olhada... ⏳"
                )

                # Pesquisar website
                research = await website_research_service.research_website(url_detected)

                # Salvar URL pesquisada
                await conversation_storage.set_website_researched(
                    conversation_id=conversation_id,
                    website_url=url_detected
                )

                # Gerar resposta personalizada
                if research["success"]:
                    company_name = research["company_name"]
                    summary = research["summary"]
                    insight = research["insights"][0] if research["insights"] else ""

                    response = f"Visitei o site! 👀\n\n"

                    if summary:
                        response += f"{summary}\n\n"

                    if insight:
                        response += f"{insight}\n\n"
                    else:
                        response += f"Muitos clientes nossos nesse segmento tinham desafio de perder leads por demora no atendimento.\n\n"

                    response += "Isso faz sentido pro cenário de vocês?"

                    # Atualizar estado para QUALIFICANDO
                    if current_state == "inicial":
                        await conversation_storage.update_conversation_state(
                            conversation_id=conversation_id,
                            state="qualificando"
                        )
                else:
                    # Falhou a pesquisa - continuar com IA normalmente
                    response = ""

            # 3. CONVERSA COM IA (padrão para qualquer mensagem)
            if not response:
                logger.info(f"💬 Processando com IA - Estado: {current_state} | Count: {qualification_count}")

                # Incrementar contador de mensagens
                await conversation_storage.increment_qualification_count(conversation_id)

                # Atualizar estado para qualificando se ainda está em inicial
                if current_state == "inicial":
                    await conversation_storage.update_conversation_state(
                        conversation_id=conversation_id,
                        state="qualificando"
                    )

                # Processar com IA
                response = await ai_service.process_message(
                    message=message_content,
                    lead=lead,
                    conversation_state=None,
                    message_history=history
                )

                # Após 3-4 mensagens, sugerir agendamento
                if qualification_count >= 2:
                    logger.info("📅 Hora de oferecer agendamento")

                    # Adicionar convite ao agendamento
                    response += f"\n\nFaz sentido a gente marcar uma conversa de 1h pra eu te mostrar como funciona na prática?"

                    # Atualizar estado
                    await conversation_storage.update_conversation_state(
                        conversation_id=conversation_id,
                        state="agendamento_enviado"
                    )

            # 5. Salvar resposta da IA no Supabase
            if response:
                await conversation_storage.save_message(
                    conversation_id=conversation_id,
                    direction="outbound",
                    content=response
                )

        # Enviar resposta
        await evolution_service.send_text_message(phone, response)

        logger.success(f"✅ Resposta enviada para {lead.nome}")

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {str(e)}")
        raise
