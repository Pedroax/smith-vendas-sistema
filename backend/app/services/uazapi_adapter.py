"""
Adaptador UAZAPI → Evolution API Format
Converte webhooks da UAZAPI para o formato Evolution API que o sistema já conhece
"""
from loguru import logger
from typing import Dict, Any


def is_uazapi_webhook(payload: Dict[str, Any]) -> bool:
    """
    Detecta se o webhook veio da UAZAPI

    Args:
        payload: Payload recebido no webhook

    Returns:
        True se for UAZAPI, False se for Evolution ou outro formato
    """
    # UAZAPI tem 'EventType' e 'BaseUrl'
    # Evolution tem 'event' e 'instance'
    is_uazapi = 'EventType' in payload and 'BaseUrl' in payload

    if is_uazapi:
        logger.info("🔵 Webhook UAZAPI detectado")
    else:
        logger.info("🟢 Webhook Evolution (ou outro formato) detectado")

    return is_uazapi


def adapt_uazapi_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payload UAZAPI para formato Evolution API

    ESTRUTURA UAZAPI (INPUT):
    {
        "EventType": "messages",
        "BaseUrl": "https://api-ax.uazapi.com",
        "instanceName": "paula",
        "owner": "5521970295930",
        "chat": {
            "phone": "+55 21 99121-6065",
            "name": "Hugo Godinho",
            "wa_chatid": "5521991216065@s.whatsapp.net",
            ...
        },
        "message": {
            "id": "5521970295930:ABC123",
            "chatid": "5521991216065@s.whatsapp.net",
            "content": "Olá, quero agendar",
            "messageTimestamp": 1770653549000,
            "fromMe": false,
            "sender": "5521991216065@s.whatsapp.net",
            "senderName": "Hugo Godinho",
            ...
        }
    }

    ESTRUTURA EVOLUTION (OUTPUT):
    {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": "5521991216065@s.whatsapp.net",
                "fromMe": false,
                "id": "5521970295930:ABC123"
            },
            "message": {
                "conversation": "Olá, quero agendar"
            },
            "pushName": "Hugo Godinho",
            "messageTimestamp": 1770653549000
        }
    }

    Args:
        payload: Payload UAZAPI original

    Returns:
        Payload convertido para formato Evolution API

    Raises:
        Exception: Se falhar ao adaptar o payload
    """
    try:
        # Extrair dados do payload UAZAPI
        message_data = payload.get('message', {})
        chat_data = payload.get('chat', {})

        # Extrair campos essenciais
        remote_jid = message_data.get('chatid') or chat_data.get('wa_chatid')
        message_id = message_data.get('id') or message_data.get('messageid')

        # Extrair texto da mensagem (pode ser string ou dict com campo 'text')
        content = message_data.get('content', {})
        if isinstance(content, dict):
            message_text = content.get('text', '')
        else:
            message_text = content or message_data.get('text', '')

        from_me = message_data.get('fromMe', False)
        sender_name = message_data.get('senderName') or chat_data.get('name', '')
        timestamp = message_data.get('messageTimestamp', 0)

        # Verificar campos obrigatórios
        if not remote_jid:
            raise ValueError("Campo 'remoteJid' não encontrado no payload UAZAPI")

        # Garantir que message_text é string
        message_text = str(message_text) if message_text else ''

        if not message_text:
            logger.warning("⚠️ Mensagem vazia recebida da UAZAPI")

        # Montar payload no formato Evolution
        evolution_payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": remote_jid,
                    "fromMe": from_me,
                    "id": message_id or "unknown"
                },
                "message": {
                    "conversation": message_text
                },
                "pushName": sender_name,
                "messageTimestamp": timestamp
            }
        }

        logger.info(
            f"✅ Payload UAZAPI adaptado: {remote_jid} - "
            f"'{message_text[:50]}{'...' if len(message_text) > 50 else ''}'"
        )

        return evolution_payload

    except Exception as e:
        logger.error(f"💥 Erro ao adaptar payload UAZAPI: {str(e)}")
        logger.error(f"📋 Payload original: {payload}")
        raise


def extract_phone_from_jid(remote_jid: str) -> str:
    """
    Extrai número de telefone do JID do WhatsApp

    Args:
        remote_jid: JID completo (ex: 5521999999999@s.whatsapp.net)

    Returns:
        Número de telefone limpo (ex: 5521999999999)
    """
    return remote_jid.replace('@s.whatsapp.net', '').replace('@c.us', '')


def format_jid(phone: str) -> str:
    """
    Formata número de telefone para JID do WhatsApp

    Args:
        phone: Número de telefone (ex: 5521999999999)

    Returns:
        JID completo (ex: 5521999999999@s.whatsapp.net)
    """
    phone_clean = phone.replace('@s.whatsapp.net', '').replace('@c.us', '')
    return f"{phone_clean}@s.whatsapp.net"
