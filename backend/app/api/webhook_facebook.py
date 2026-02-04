"""
Webhook para integração com Facebook Lead Ads
Recebe leads, qualifica com IA e insere no CRM
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from typing import Dict, Any, Optional
import hmac
import hashlib
from datetime import datetime, timezone

from app.models.lead import Lead, LeadStatus, LeadOrigin
from app.repository.leads_repository import LeadsRepository
from app.services.lead_qualification import LeadQualificationService
from app.services.notification_service import NotificationService
from app.services.whatsapp_followup_service import WhatsAppFollowUpService
from app.config import settings

router = APIRouter()

# Repositórios e serviços
leads_repo = LeadsRepository()
qualification_service = LeadQualificationService()
notification_service = NotificationService()
whatsapp_followup_service = WhatsAppFollowUpService()


@router.get("/facebook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Verificação do webhook do Facebook
    Facebook envia GET request para verificar o webhook
    """
    logger.info(f"🔍 Verificação de webhook Facebook - Mode: {mode}, Token recebido: {token}")

    # Token de verificação configurado no Facebook
    verify_token = settings.facebook_verify_token

    if mode == "subscribe" and token == verify_token:
        logger.success("✅ Webhook Facebook verificado com sucesso!")
        return PlainTextResponse(content=challenge, status_code=200)

    logger.error("❌ Falha na verificação do webhook Facebook")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/facebook")
async def receive_facebook_lead(request: Request):
    """
    Recebe leads do Facebook Lead Ads
    Processa, qualifica e insere no CRM automaticamente
    """
    try:
        # Pegar body raw para validação de assinatura
        body = await request.body()

        # Validar assinatura do Facebook (segurança)
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not _verify_facebook_signature(body, signature):
            logger.warning("⚠️ Assinatura inválida do Facebook")
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse JSON
        data = await request.json()
        logger.info(f"📨 Webhook Facebook recebido: {data}")

        # Processar cada entrada
        if "entry" not in data:
            return {"status": "ok", "message": "No entries to process"}

        for entry in data["entry"]:
            if "changes" not in entry:
                continue

            for change in entry["changes"]:
                if change.get("field") != "leadgen":
                    continue

                # Extrair dados do lead
                lead_data = change.get("value", {})
                lead_id_fb = lead_data.get("leadgen_id")
                form_id = lead_data.get("form_id")
                page_id = lead_data.get("page_id")

                # Buscar dados completos do lead via API do Facebook
                # (Aqui você precisaria fazer chamada para Graph API)
                # Por enquanto, vamos processar os dados básicos

                logger.info(f"📋 Processando lead FB: {lead_id_fb}")

                # Processar lead (será implementado abaixo)
                await _process_facebook_lead(lead_id_fb, form_id, page_id, lead_data)

        return {"status": "ok", "message": "Leads processados"}

    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook Facebook: {e}")
        # Retorna 200 mesmo com erro para não fazer Facebook retentar infinitamente
        return {"status": "error", "message": str(e)}


async def _process_facebook_lead(
    lead_id_fb: str,
    form_id: str,
    page_id: str,
    lead_data: Dict[str, Any]
):
    """
    Processa um lead individual do Facebook
    1. Extrai dados
    2. Qualifica com IA
    3. Se qualificado, insere no CRM
    4. Notifica
    """
    try:
        # 1. EXTRAIR DADOS DO LEAD
        # Em produção, você faria chamada para Graph API aqui
        # GET /{lead-id}?fields=field_data,created_time

        # Extrair dados do formulário do Facebook
        # O Facebook Lead Ads retorna os dados em field_data como lista
        field_data_list = lead_data.get("field_data", [])

        # Converter lista em dicionário para facilitar acesso
        field_data = {}
        for field in field_data_list:
            field_name = field.get("name", "")
            field_values = field.get("values", [])
            field_value = field_values[0] if field_values else ""
            field_data[field_name] = field_value

        lead_info = {
            "nome": field_data.get("full_name", "Lead sem nome"),
            "email": field_data.get("email", ""),
            "telefone": field_data.get("phone_number", ""),
            "empresa": field_data.get("company_name", ""),
            "cargo": field_data.get("job_title", ""),
            "faturamento": field_data.get("custom_disclaimer", ""),  # Campo customizado de faturamento
            "mensagem": field_data.get("message", ""),
        }

        logger.info(f"👤 Dados extraídos: {lead_info['nome']} - {lead_info['email']}")

        # 2. QUALIFICAR COM IA
        qualification_result = await qualification_service.qualify_lead(lead_info)

        is_qualified = qualification_result["is_qualified"]
        score = qualification_result["score"]
        reasoning = qualification_result["reasoning"]

        logger.info(f"🎯 Qualificação: {'✅ QUALIFICADO' if is_qualified else '❌ NÃO QUALIFICADO'} (Score: {score}/100)")
        logger.info(f"💭 Razão: {reasoning}")

        # 3. INSERIR NO CRM SE QUALIFICADO
        if is_qualified:
            # Criar lead no CRM (apenas campos que existem no banco)
            lead = Lead(
                id=f"fb_{lead_id_fb}",
                nome=lead_info["nome"],
                email=lead_info["email"] if lead_info["email"] else None,
                telefone=lead_info["telefone"] if lead_info["telefone"] else "Não informado",
                empresa=lead_info["empresa"] if lead_info["empresa"] else None,
                status=LeadStatus.QUALIFICADO,
                origem=LeadOrigin.FACEBOOK_ADS,
                lead_score=score,
                notas=f"LEAD QUALIFICADO AUTOMATICAMENTE VIA FACEBOOK ADS\n\nScore: {score}/100\n\nFaturamento: {lead_info.get('faturamento', 'Não informado')}\nCargo: {lead_info.get('cargo', 'N/A')}\n\nRazão da Qualificação:\n{reasoning}\n\nMensagem Original:\n{lead_info['mensagem']}\n\nPróxima Ação:\n{qualification_result.get('next_action', 'Entrar em contato')}",
                tags=["facebook_ads", "auto_qualified", f"score_{score}"]
            )

            # Salvar no banco
            created_lead = await leads_repo.create(lead)
            logger.success(f"✅ Lead inserido no CRM: {created_lead.id}")

            # 4. NOTIFICAR
            await notification_service.notify_new_qualified_lead(created_lead, qualification_result)
            logger.success(f"📢 Notificação enviada sobre lead qualificado!")

            # 5. ENVIAR MENSAGEM DE AGENDAMENTO VIA WHATSAPP
            whatsapp_sent = await whatsapp_followup_service.send_scheduling_message(created_lead)
            if whatsapp_sent:
                logger.success(f"📱 Mensagem de agendamento enviada via WhatsApp")
            else:
                logger.warning(f"⚠️ Não foi possível enviar mensagem de agendamento via WhatsApp")

        else:
            logger.info(f"⏭️ Lead não qualificado, não inserido no CRM")
            # Opcionalmente, você pode salvar leads não qualificados em outra tabela
            # para análise posterior

    except Exception as e:
        logger.error(f"❌ Erro ao processar lead {lead_id_fb}: {e}")
        raise


def _verify_facebook_signature(payload: bytes, signature: str) -> bool:
    """
    Verifica assinatura do Facebook para garantir autenticidade
    """
    # Modo debug: skip validação se app_secret não configurado
    if settings.debug and not settings.facebook_app_secret:
        logger.warning("⚠️ MODO DEBUG: Pulando verificação de assinatura do Facebook")
        return True

    if not signature:
        return False

    try:
        # Facebook envia assinatura no formato: sha256=<hash>
        expected_signature = signature.split("sha256=")[1]

        # Calcular hash usando app secret
        app_secret = settings.facebook_app_secret.encode()
        calculated_hash = hmac.new(
            app_secret,
            payload,
            hashlib.sha256
        ).hexdigest()

        # Comparar de forma segura
        return hmac.compare_digest(calculated_hash, expected_signature)

    except Exception as e:
        logger.error(f"Erro ao verificar assinatura: {e}")
        return False
