"""
Script para limpar conversas e simular novo lead entrando no sistema
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_supabase, get_supabase
from app.services.evolution_service import evolution_service
from app.services.google_calendar_service import google_calendar_service


async def limpar_e_iniciar_atendimento():
    """Limpa conversas antigas e inicia novo atendimento"""

    # Inicializar Supabase
    init_supabase()
    supabase = get_supabase()

    phone = "5561982563956"

    print("="*60)
    print("LIMPANDO E INICIANDO NOVO ATENDIMENTO")
    print("="*60)

    # 1. Buscar lead
    print("\n1. Buscando lead...")
    result = supabase.table("leads").select("*").eq("telefone", phone).execute()

    if not result.data:
        print(f"   Lead não existe, criando...")
        # Criar lead básico
        new_lead = {
            "nome": "Pedro Machado",
            "telefone": phone,
            "email": "pedro@teste.com",
            "empresa": "Automatexia",
            "origem": "whatsapp",
            "status": "novo"
        }
        result = supabase.table("leads").insert(new_lead).execute()
        lead_data = result.data[0]
        print(f"   Lead criado: {lead_data['nome']}")
    else:
        lead_data = result.data[0]
        print(f"   Lead encontrado: {lead_data['nome']}")

    # 2. Limpar conversas antigas
    print("\n2. Limpando conversas antigas...")
    try:
        # Deletar conversações antigas
        supabase.table("conversations").delete().eq("phone_number", phone).execute()
        print("   Conversas limpas!")
    except Exception as e:
        print(f"   Aviso: {e}")

    # 3. Buscar horários disponíveis
    print("\n3. Buscando horários disponíveis...")
    try:
        slots = await google_calendar_service.get_available_slots(days_ahead=7, slots_per_day=3)

        if not slots:
            print("   AVISO: Nenhum horário disponível!")
            horarios_texto = "Infelizmente não tenho horários disponíveis no momento."
        else:
            print(f"   Encontrados {len(slots)} horários")
            # Pegar primeiros 3 slots
            slots_texto = []
            for slot in slots[:3]:
                slot_formatado = google_calendar_service._format_slot_display(slot)
                slots_texto.append(slot_formatado)

            horarios_texto = ", ".join(slots_texto)
            print(f"   Horários: {horarios_texto}")
    except Exception as e:
        print(f"   Erro ao buscar horários: {e}")
        horarios_texto = "Amanhã às 09:00, Amanhã às 10:00 ou Amanhã às 11:00"

    # 4. Enviar mensagem inicial
    print("\n4. Enviando mensagem de qualificação...")

    mensagem = f"""Olá {lead_data['nome'].split()[0]}! 👋

Vi que você demonstrou interesse no nosso sistema de automação com IA para gestão de leads.

Acabei de verificar a agenda aqui e tenho disponibilidade para uma conversa em:

{horarios_texto}

Algum desses horários funciona pra você? Se preferir outro dia ou horário, é só me avisar que a gente se ajusta! 😊

Ah, e pode me fazer qualquer pergunta sobre o sistema, estou aqui pra te ajudar."""

    try:
        await evolution_service.send_text_message(
            phone=phone,
            message=mensagem
        )
        print("   Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"   ERRO ao enviar mensagem: {e}")
        return

    print("\n" + "="*60)
    print("PRONTO! Agora você pode responder no WhatsApp")
    print("Pode enviar TEXTO ou ÁUDIO para testar!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(limpar_e_iniciar_atendimento())
