"""
Webhook para receber leads do formulário da Landing Page (Lovable).
Qualifica automaticamente e dispara primeira mensagem via Smith/WhatsApp.
"""
import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.models.lead import (
    Lead, LeadStatus, LeadOrigin, LeadTemperature,
    QualificationData, FollowUpConfig,
)
from app.repository.leads_repository import LeadsRepository
from app.services.uazapi_service import get_uazapi_service

router = APIRouter()
repository = LeadsRepository()
uazapi_service = get_uazapi_service()

# Cargos que indicam poder de decisão
CARGOS_QUALIFICADOS = {
    "ceo", "diretor", "diretora", "socio", "sócia", "sócio",
    "fundador", "fundadora", "co-fundador", "co-fundadora",
    "cofundador", "cofundadora", "cfo", "coo", "cto", "presidente",
    "proprietario", "proprietária", "proprietário", "dono", "dona",
    "partner", "managing director", "md",
}

FATURAMENTO_MINIMO = 50_000.0


class FormLeadPayload(BaseModel):
    nome: str
    empresa: str
    segmento: str
    faturamento_mensal: float
    cargo: str
    telefone: str


def normalizar_telefone(tel: str) -> str:
    """Garante formato 55XXXXXXXXXXX."""
    digits = re.sub(r'\D', '', tel)
    if not digits.startswith('55'):
        digits = '55' + digits
    return digits


def is_qualificado(cargo: str, faturamento_mensal: float) -> bool:
    """Verifica se o lead passa nos critérios de qualificação."""
    cargo_lower = cargo.lower().strip()
    cargo_ok = any(q in cargo_lower for q in CARGOS_QUALIFICADOS)
    fat_ok = faturamento_mensal >= FATURAMENTO_MINIMO
    return cargo_ok and fat_ok


@router.post("/form")
async def webhook_form(payload: FormLeadPayload):
    """
    Recebe lead do formulário da LP, qualifica e registra no CRM.
    Se qualificado, envia primeira mensagem via WhatsApp.
    """
    logger.info(f"📋 Lead do formulário recebido: {payload.nome} | {payload.empresa} | {payload.cargo} | R${payload.faturamento_mensal:,.0f}/mês")

    tel = normalizar_telefone(payload.telefone)
    qualificado = is_qualificado(payload.cargo, payload.faturamento_mensal)

    logger.info(f"{'✅ QUALIFICADO' if qualificado else '❌ NÃO QUALIFICADO'}: cargo={payload.cargo}, faturamento=R${payload.faturamento_mensal:,.0f}")

    if qualificado:
        lead = Lead(
            id=str(uuid.uuid4()),
            nome=payload.nome,
            telefone=tel,
            empresa=payload.empresa,
            status=LeadStatus.CONTATO_INICIAL,
            origem=LeadOrigin.SITE,
            temperatura=LeadTemperature.QUENTE,
            lead_score=70,
            qualification_data=QualificationData(
                cargo=payload.cargo,
                setor=payload.segmento,
                faturamento_anual=payload.faturamento_mensal * 12,
                site_perguntado=False,
            ),
            followup_config=FollowUpConfig(
                tentativas_realizadas=0,
                intervalo_horas=[24, 72, 168],
            ),
            tags=["formulario_lp"],
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await repository.create(lead)
        logger.info(f"Lead qualificado salvo: {lead.id}")

        # Montar e enviar primeira mensagem
        nome_curto = payload.nome.split()[0]
        mensagem = (
            f"Oi {nome_curto}! Vi aqui o formulário que você preencheu — "
            f"a {payload.empresa} tem exatamente o perfil que a gente atende.\n\n"
            f"Me conta uma coisa: qual é o maior desafio de atendimento que vocês enfrentam hoje? "
            f"Perda de leads, demora pra responder, processos manuais?"
        )

        sucesso = uazapi_service.send_text_message(tel, mensagem)

        if sucesso:
            await repository.add_conversation_message(lead.id, "assistant", mensagem)
            logger.success(f"✅ Mensagem enviada para {tel} ({payload.nome})")
        else:
            logger.error(f"❌ Falha ao enviar WhatsApp para {tel}")

        return {
            "success": True,
            "qualificado": True,
            "lead_id": lead.id,
            "mensagem_enviada": sucesso,
        }

    else:
        # Salvar como não qualificado — sem WhatsApp
        lead = Lead(
            id=str(uuid.uuid4()),
            nome=payload.nome,
            telefone=tel,
            empresa=payload.empresa,
            status=LeadStatus.PERDIDO,
            origem=LeadOrigin.SITE,
            temperatura=LeadTemperature.FRIO,
            lead_score=10,
            qualification_data=QualificationData(
                cargo=payload.cargo,
                setor=payload.segmento,
                faturamento_anual=payload.faturamento_mensal * 12,
            ),
            followup_config=FollowUpConfig(
                tentativas_realizadas=0,
                intervalo_horas=[24, 72, 168],
            ),
            tags=["formulario_lp", "nao_qualificado"],
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await repository.create(lead)
        logger.info(f"Lead não qualificado salvo: {lead.id} ({payload.nome})")

        return {
            "success": True,
            "qualificado": False,
            "lead_id": lead.id,
        }
