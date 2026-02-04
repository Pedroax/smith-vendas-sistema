"""
Processador de agendamentos
Extrai data/hora de mensagens naturais e valida
"""
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from zoneinfo import ZoneInfo

from app.config import settings

# Timezone São Paulo
SP_TZ = ZoneInfo('America/Sao_Paulo')


class ExtractedDateTime(BaseModel):
    """Data/hora extraída da mensagem"""
    datetime: datetime = Field(..., description="Data e hora da reunião")
    confidence: float = Field(..., description="Confiança da extração (0-1)")
    original_text: str = Field(..., description="Texto original que foi interpretado")


class AppointmentProcessor:
    """Processa e valida agendamentos"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Baixa temperatura para extração precisa
            api_key=settings.openai_api_key
        )

    async def extract_datetime_from_message(
        self,
        message: str,
        lead_timezone: str = "America/Sao_Paulo"
    ) -> Optional[ExtractedDateTime]:
        """
        Extrai data e hora de uma mensagem em linguagem natural

        Args:
            message: Mensagem do lead (ex: "terça 14h", "amanhã às 10h")
            lead_timezone: Timezone do lead

        Returns:
            ExtractedDateTime ou None se não conseguir extrair
        """
        try:
            # Obter data/hora atual no timezone do lead
            now = datetime.now(ZoneInfo(lead_timezone))

            # Prompt para extração
            extraction_prompt = f"""Você é um assistente que extrai data e hora de mensagens.

DATA/HORA ATUAL: {now.strftime('%A, %d/%m/%Y %H:%M')} (timezone: {lead_timezone})

MENSAGEM DO USUÁRIO: "{message}"

INSTRUÇÕES:
1. Extraia a data e hora que o usuário está sugerindo
2. Considere que:
   - "terça" = próxima terça-feira
   - "amanhã" = dia seguinte ao atual
   - "hoje" = dia atual
   - Se não especificar data, assumir próximo dia útil
   - Se não especificar horário, assumir 14h
   - Horário comercial: 9h-18h
3. Retorne no formato ISO 8601 com timezone
4. Indique confiança (0.0-1.0) baseado na clareza da mensagem

EXEMPLOS:
- "terça 14h" → próxima terça às 14h, confiança 0.9
- "amanhã 10h30" → amanhã às 10h30, confiança 0.95
- "quinta" → próxima quinta às 14h (padrão), confiança 0.7
- "14h" → próximo dia útil às 14h, confiança 0.6

Se não conseguir extrair data/hora com confiança >= 0.5, retorne None."""

            # Usar structured output
            structured_llm = self.llm.with_structured_output(ExtractedDateTime)

            # Invocar LLM
            result = structured_llm.invoke(extraction_prompt)

            if result and result.confidence >= 0.5:
                # Validar que é futuro
                if result.datetime <= now:
                    logger.warning(f"Data/hora extraída está no passado: {result.datetime}")
                    return None

                # Validar horário comercial (9h-18h)
                if result.datetime.hour < 9 or result.datetime.hour >= 18:
                    logger.warning(f"Horário fora do comercial: {result.datetime.hour}h")
                    # Ajustar para 14h se fora do horário
                    result.datetime = result.datetime.replace(hour=14, minute=0)

                logger.success(f"✅ Data/hora extraída: {result.datetime.strftime('%d/%m/%Y %H:%M')} (confiança: {result.confidence:.0%})")
                return result

            logger.warning(f"Não consegui extrair data/hora com confiança suficiente da mensagem: {message}")
            return None

        except Exception as e:
            logger.error(f"❌ Erro ao extrair data/hora: {e}", exc_info=True)
            return None

    def is_valid_meeting_time(self, dt: datetime) -> tuple[bool, Optional[str]]:
        """
        Valida se o horário é adequado para reunião

        Args:
            dt: Data/hora a validar

        Returns:
            Tupla (is_valid, reason_if_invalid)
        """
        now = datetime.now(SP_TZ)

        # Verificar se é futuro
        if dt <= now:
            return False, "Data/hora no passado"

        # Verificar se é muito distante (máximo 60 dias)
        if (dt - now).days > 60:
            return False, "Data muito distante (máximo 60 dias)"

        # Verificar se é muito próximo (mínimo 2 horas)
        if (dt - now).total_seconds() < 7200:  # 2 horas
            return False, "Horário muito próximo (mínimo 2 horas de antecedência)"

        # Verificar se é final de semana
        if dt.weekday() >= 5:  # Sábado=5, Domingo=6
            return False, "Final de semana (apenas dias úteis)"

        # Verificar horário comercial (9h-18h)
        if dt.hour < 9 or dt.hour >= 18:
            return False, "Fora do horário comercial (9h-18h)"

        return True, None

    async def suggest_alternative_times(
        self,
        base_date: Optional[datetime] = None
    ) -> list[datetime]:
        """
        Sugere 3 horários alternativos

        Args:
            base_date: Data base (padrão: amanhã)

        Returns:
            Lista com 3 horários sugeridos
        """
        if not base_date:
            base_date = datetime.now(SP_TZ) + timedelta(days=1)

        suggestions = []
        current = base_date

        # Encontrar próximos 3 dias úteis
        while len(suggestions) < 3:
            # Pular finais de semana
            if current.weekday() < 5:  # Segunda a Sexta
                # Horários: 10h, 14h, 16h
                for hour in [10, 14, 16]:
                    if len(suggestions) < 3:
                        suggestion = current.replace(hour=hour, minute=0, second=0, microsecond=0)
                        suggestions.append(suggestion)

            current += timedelta(days=1)

        return suggestions[:3]


# Instância global
appointment_processor = AppointmentProcessor()
