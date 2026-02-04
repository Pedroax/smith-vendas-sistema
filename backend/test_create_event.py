"""
Script de teste para criar evento no Google Calendar
"""
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.google_calendar_service import google_calendar_service

async def test_create_event():
    print("=" * 60)
    print("TESTE DE CRIACAO DE EVENTO - GOOGLE CALENDAR")
    print("=" * 60)
    print()

    # Verificar se serviço está disponível
    if not google_calendar_service.is_available():
        print("ERRO: Google Calendar NAO esta disponivel!")
        return

    print("OK: Google Calendar conectado!")
    print()

    # Definir data/hora do evento (amanhã às 10:00)
    SP_TZ = ZoneInfo('America/Sao_Paulo')
    tomorrow = datetime.now(SP_TZ) + timedelta(days=1)
    meeting_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

    print(f"Criando evento de TESTE para: {meeting_time.strftime('%d/%m/%Y as %H:%M')}")
    print()

    # Criar evento
    result = await google_calendar_service.create_meeting(
        lead_name="Lead de Teste - Smith",
        lead_email="teste@smith.com",
        lead_phone="11999999999",
        meeting_datetime=meeting_time,
        duration_minutes=60,
        empresa="Empresa Teste S/A"
    )

    if result:
        print("=" * 60)
        print("SUCESSO! Evento criado no Google Calendar")
        print("=" * 60)
        print()
        print(f"Event ID: {result['event_id']}")
        print(f"Link do Calendar: {result.get('event_link', 'N/A')}")
        print(f"Link do Google Meet: {result.get('meet_link', 'N/A')}")
        print(f"Horario: {meeting_time.strftime('%d/%m/%Y as %H:%M')}")
        print(f"Duracao: 60 minutos")
        print()
        print("Verifique sua agenda do Google Calendar!")
        print()
    else:
        print("ERRO: Falha ao criar evento")
        print()

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_create_event())
