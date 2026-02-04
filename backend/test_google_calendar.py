"""
Script de teste para Google Calendar
Verifica conexão e mostra horários disponíveis/ocupados
"""
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.google_calendar_service import google_calendar_service

async def test_calendar():
    print("=" * 60)
    print("TESTE DE CONEXAO - GOOGLE CALENDAR")
    print("=" * 60)

    # Verificar se serviço está disponível
    if not google_calendar_service.is_available():
        print("ERRO: Google Calendar NAO esta disponivel!")
        print("Verifique as credenciais em google_credentials.json")
        return

    print("OK: Google Calendar conectado com sucesso!")
    print()

    # Buscar horários disponíveis
    print("Buscando horarios disponiveis nos proximos 7 dias...")
    print()

    available_slots = await google_calendar_service.get_available_slots(
        days_ahead=7,
        num_slots=5,  # Buscar 5 horários
        duration_minutes=60
    )

    if available_slots:
        print(f"OK: {len(available_slots)} horarios DISPONIVEIS encontrados:")
        print()
        for i, slot in enumerate(available_slots, 1):
            start = slot['start']
            day_name = slot['day_name']
            display = slot['display']
            print(f"   {i}. {display} ({day_name})")
            print(f"      Horario exato: {start.strftime('%d/%m/%Y as %H:%M')}")
        print()
    else:
        print("AVISO: Nenhum horario disponivel encontrado")
        print()

    # Buscar eventos já agendados para amanhã
    print("=" * 60)
    print("EVENTOS AGENDADOS PARA AMANHA")
    print("=" * 60)

    SP_TZ = ZoneInfo('America/Sao_Paulo')
    tomorrow = datetime.now(SP_TZ) + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

    try:
        from app.config import settings

        events_result = google_calendar_service.service.events().list(
            calendarId=settings.google_calendar_id,
            timeMin=tomorrow_start.isoformat(),
            timeMax=tomorrow_end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if events:
            print(f"EVENTOS: {len(events)} evento(s) agendado(s) para amanha:")
            print()
            for event in events:
                summary = event.get('summary', 'Sem titulo')
                start_raw = event['start'].get('dateTime', event['start'].get('date'))
                end_raw = event['end'].get('dateTime', event['end'].get('date'))

                start_dt = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))

                # Converter para timezone local
                if start_dt.tzinfo != SP_TZ:
                    start_dt = start_dt.astimezone(SP_TZ)
                if end_dt.tzinfo != SP_TZ:
                    end_dt = end_dt.astimezone(SP_TZ)

                print(f"   - {summary}")
                print(f"     Horario: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
                print()
        else:
            print("OK: Nenhum evento agendado para amanha - agenda totalmente livre!")
            print()

    except Exception as e:
        print(f"ERRO ao buscar eventos: {e}")
        print()

    print("=" * 60)
    print("OK: Teste concluido!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_calendar())
