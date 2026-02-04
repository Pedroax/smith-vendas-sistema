"""
Endpoint de teste para simular qualificação de leads
Útil para testar sem precisar do Facebook
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.lead_qualification import LeadQualificationService
from app.repository.leads_repository import LeadsRepository
from app.services.notification_service import NotificationService
from app.services.whatsapp_followup_service import WhatsAppFollowUpService
from app.models.lead import Lead, LeadStatus, LeadOrigin
from datetime import datetime, timezone
import uuid

router = APIRouter()

qualification_service = LeadQualificationService()
leads_repo = LeadsRepository()
notification_service = NotificationService()
whatsapp_followup_service = WhatsAppFollowUpService()


class TestLeadInput(BaseModel):
    """Dados de entrada para teste"""
    nome: str
    email: Optional[str] = ""
    telefone: Optional[str] = ""
    empresa: Optional[str] = ""
    cargo: Optional[str] = ""
    faturamento: Optional[str] = ""
    mensagem: Optional[str] = ""


@router.post("/test-lead-qualification")
async def test_lead_qualification(lead_input: TestLeadInput):
    """
    Testa o fluxo completo de qualificação de lead

    Exemplo de uso:
    ```
    POST /api/test-lead-qualification
    {
        "nome": "João Silva",
        "email": "joao@empresaX.com.br",
        "telefone": "11999999999",
        "empresa": "Empresa X Ltda",
        "cargo": "CEO",
        "faturamento": "Entre R$ 500 mil e R$ 1 milhão/ano",
        "mensagem": "Quero automatizar meu atendimento, estou perdendo muitos clientes"
    }
    ```

    Opções de faturamento:
    - "Menos de R$ 300 mil/ano"
    - "Entre R$ 300 mil e R$ 500 mil/ano"
    - "Entre R$ 500 mil e R$ 1 milhão/ano"
    - "Entre R$ 1 milhão e R$ 3 milhões/ano"
    - "Acima de R$ 3 milhões/ano"
    """
    try:
        # 1. Qualificar com IA
        lead_data = lead_input.dict()
        qualification_result = await qualification_service.qualify_lead(lead_data)

        is_qualified = qualification_result["is_qualified"]
        score = qualification_result["score"]
        reasoning = qualification_result["reasoning"]
        next_action = qualification_result.get("next_action", "Entrar em contato")

        # 2. Se qualificado, inserir no CRM
        created_lead = None
        if is_qualified:
            lead = Lead(
                id=str(uuid.uuid4()),
                nome=lead_input.nome,
                email=lead_input.email if lead_input.email else None,
                telefone=lead_input.telefone if lead_input.telefone else "Não informado",
                empresa=lead_input.empresa if lead_input.empresa else None,
                status=LeadStatus.QUALIFICADO,
                origem=LeadOrigin.SITE,  # Teste via site/API
                lead_score=score,
                notas=f"🧪 LEAD DE TESTE - QUALIFICADO AUTOMATICAMENTE\n\n📊 Score: {score}/100\n💰 Faturamento: {lead_input.faturamento or 'Não informado'}\n\n🤔 Razão da Qualificação:\n{reasoning}\n\n💬 Mensagem:\n{lead_input.mensagem or 'N/A'}\n\n🎯 Próxima Ação:\n{next_action}",
                tags=["teste", "auto_qualified", f"score_{score}"],
                ai_summary=reasoning,
                ai_next_action=next_action,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            created_lead = await leads_repo.create(lead)

            # 3. Notificar
            await notification_service.notify_new_qualified_lead(created_lead, qualification_result)

            # 4. Enviar mensagem de agendamento via WhatsApp
            whatsapp_sent = await whatsapp_followup_service.send_scheduling_message(created_lead)

        return {
            "success": True,
            "qualification": {
                "is_qualified": is_qualified,
                "score": score,
                "reasoning": reasoning,
                "next_action": next_action
            },
            "lead_created": created_lead is not None,
            "lead_id": created_lead.id if created_lead else None,
            "crm_url": f"http://localhost:3000/crm/{created_lead.id}" if created_lead else None,
            "whatsapp_sent": whatsapp_sent if created_lead else False
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
