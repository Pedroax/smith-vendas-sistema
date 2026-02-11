"""
Cliente UAZAPI para envio de mensagens WhatsApp
Baseado na implementação da instância Paula
"""
import requests
from typing import Optional
from loguru import logger

from app.config import settings


class UazapiService:
    """Cliente para interação com UAZAPI"""

    def __init__(self):
        """Inicializa cliente UAZAPI"""
        self.base_url = settings.uazapi_base_url  # Ex: https://api-ax.uazapi.com
        self.instance_id = settings.uazapi_instance_id  # Nome da instância
        self.token = settings.uazapi_token  # Token de autenticação

        logger.info(
            f"🔵 UAZAPI Service inicializado: "
            f"{self.base_url} | Instância: {self.instance_id}"
        )

    def send_text_message(self, phone_number: str, message: str) -> bool:
        """
        Envia mensagem de texto via UAZAPI

        Args:
            phone_number: Telefone no formato 5521999999999 (sem @s.whatsapp.net)
            message: Texto da mensagem

        Returns:
            True se sucesso, False se erro
        """
        try:
            # Normalizar telefone (remover @s.whatsapp.net se vier)
            phone_clean = phone_number.replace('@s.whatsapp.net', '')

            # Endpoint da UAZAPI para enviar mensagem
            # Formato padrão de APIs WhatsApp (similar a Evolution API)
            url = f"{self.base_url}/message/sendText/{self.instance_id}"

            # Headers com autenticação
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            # Payload no formato padrão de APIs WhatsApp
            payload = {
                "number": phone_clean,
                "text": message
            }

            logger.info(f"📤 Enviando via UAZAPI para {phone_clean[:8]}...")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.success(f"✅ Mensagem enviada para {phone_clean}")
                return True
            else:
                logger.error(
                    f"❌ Erro UAZAPI: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"💥 Erro ao enviar via UAZAPI: {str(e)}")
            return False

    def send_audio(self, phone_number: str, audio_url: str) -> bool:
        """
        Envia áudio via UAZAPI

        Args:
            phone_number: Telefone no formato 5521999999999
            audio_url: URL do áudio

        Returns:
            True se sucesso, False se erro
        """
        try:
            phone_clean = phone_number.replace('@s.whatsapp.net', '')

            url = f"{self.base_url}/message/sendAudio/{self.instance_id}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            payload = {
                "number": phone_clean,
                "audio": audio_url
            }

            logger.info(f"🎵 Enviando áudio via UAZAPI para {phone_clean[:8]}...")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.success(f"✅ Áudio enviado para {phone_clean}")
                return True
            else:
                logger.error(
                    f"❌ Erro ao enviar áudio: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"💥 Erro ao enviar áudio via UAZAPI: {str(e)}")
            return False

    def send_document(
        self,
        phone_number: str,
        document_url: str,
        filename: Optional[str] = None
    ) -> bool:
        """
        Envia documento via UAZAPI

        Args:
            phone_number: Telefone no formato 5521999999999
            document_url: URL do documento
            filename: Nome do arquivo (opcional)

        Returns:
            True se sucesso, False se erro
        """
        try:
            phone_clean = phone_number.replace('@s.whatsapp.net', '')

            url = f"{self.base_url}/message/sendMedia/{self.instance_id}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            payload = {
                "number": phone_clean,
                "mediaUrl": document_url,
                "mediatype": "document"
            }

            if filename:
                payload["filename"] = filename

            logger.info(f"📄 Enviando documento via UAZAPI para {phone_clean[:8]}...")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.success(f"✅ Documento enviado para {phone_clean}")
                return True
            else:
                logger.error(
                    f"❌ Erro ao enviar documento: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"💥 Erro ao enviar documento via UAZAPI: {str(e)}")
            return False

    def send_image(self, phone_number: str, image_url: str, caption: Optional[str] = None) -> bool:
        """
        Envia imagem via UAZAPI

        Args:
            phone_number: Telefone no formato 5521999999999
            image_url: URL da imagem
            caption: Legenda da imagem (opcional)

        Returns:
            True se sucesso, False se erro
        """
        try:
            phone_clean = phone_number.replace('@s.whatsapp.net', '')

            url = f"{self.base_url}/message/sendMedia/{self.instance_id}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            payload = {
                "number": phone_clean,
                "mediaUrl": image_url,
                "mediatype": "image"
            }

            if caption:
                payload["caption"] = caption

            logger.info(f"🖼️ Enviando imagem via UAZAPI para {phone_clean[:8]}...")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.success(f"✅ Imagem enviada para {phone_clean}")
                return True
            else:
                logger.error(
                    f"❌ Erro ao enviar imagem: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"💥 Erro ao enviar imagem via UAZAPI: {str(e)}")
            return False


# Instância global do serviço
_uazapi_service: Optional[UazapiService] = None


def get_uazapi_service() -> UazapiService:
    """Retorna instância global do UAZAPI Service"""
    global _uazapi_service
    if _uazapi_service is None:
        _uazapi_service = UazapiService()
    return _uazapi_service
