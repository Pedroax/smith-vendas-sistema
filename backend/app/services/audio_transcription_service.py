"""
Serviço de transcrição de áudio usando OpenAI Whisper
"""
import tempfile
import os
import asyncio
from typing import Optional
from openai import OpenAI
from loguru import logger

from app.config import settings


class AudioTranscriptionService:
    """Serviço para transcrever áudios usando Whisper API"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def transcribe_audio(self, audio_data: bytes, audio_format: str = "ogg") -> Optional[str]:
        """
        Transcreve áudio usando Whisper API

        Args:
            audio_data: Bytes do arquivo de áudio
            audio_format: Formato do áudio (ogg, mp3, wav, etc)

        Returns:
            Texto transcrito ou None em caso de erro
        """
        try:
            logger.info(f"🎤 Transcrevendo áudio ({len(audio_data)} bytes, formato original: {audio_format})")

            # WhatsApp usa Opus dentro de OGG, mas Whisper prefere MP3/M4A/WAV
            # Vamos tentar primeiro como está e deixar o Whisper lidar com o formato
            # Se falhar, podemos adicionar conversão depois

            # Criar arquivo temporário com o formato original
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name

            try:
                # Transcrever com Whisper (executar em thread separada para não bloquear)
                def _transcribe():
                    with open(tmp_file_path, "rb") as audio_file:
                        # Não especificar language deixa o Whisper detectar automaticamente
                        # Isso pode funcionar melhor para áudios com ruído ou qualidade baixa
                        transcript = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text"  # Retornar apenas texto
                        )
                    return transcript if isinstance(transcript, str) else transcript.text

                transcribed_text = await asyncio.to_thread(_transcribe)

                if transcribed_text and transcribed_text.strip():
                    logger.success(f"✅ Áudio transcrito ({len(transcribed_text)} chars): {transcribed_text[:100]}...")
                    return transcribed_text.strip()
                else:
                    logger.warning("⚠️ Whisper retornou texto vazio")
                    return None

            finally:
                # Limpar arquivo temporário
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        except Exception as e:
            logger.error(f"❌ Erro ao transcrever áudio: {str(e)}")
            # Log do erro completo para debug
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return None

    async def text_to_speech(self, text: str, voice: str = "ash") -> Optional[bytes]:
        """
        Gera áudio a partir de texto usando a TTS da OpenAI (voz masculina grave e confiante)

        Args:
            text: Texto a ser sintetizado
            voice: Voz da OpenAI (padrão "ash" — voz masculina grave)

        Returns:
            Bytes do áudio em formato Ogg/Opus (compatível com nota de voz do WhatsApp) ou None em caso de erro
        """
        try:
            logger.info(f"🔊 Gerando resposta em áudio ({len(text)} chars, voz={voice})...")

            def _synthesize():
                response = self.client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice=voice,
                    input=text,
                    instructions=(
                        "Fale em português do Brasil com voz grave, confiante e direta — "
                        "tom de consultor de vendas experiente, natural e sem soar robótico."
                    ),
                    response_format="opus"
                )
                return response.content

            audio_bytes = await asyncio.to_thread(_synthesize)

            logger.success(f"✅ Áudio TTS gerado ({len(audio_bytes)} bytes)")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio TTS: {str(e)}")
            return None


# Instância global
audio_transcription_service = AudioTranscriptionService()
