"""
Serviço de integração com Evolution API (WhatsApp)
"""
import httpx
from loguru import logger
from app.config import settings


class EvolutionService:
    """
    Serviço para enviar mensagens via Evolution API
    """

    def __init__(self):
        self.api_url = settings.evolution_api_url
        self.api_key = settings.evolution_api_key
        self.instance_name = settings.evolution_instance_name

    async def send_text_message(self, phone: str, message: str) -> bool:
        """
        Envia mensagem de texto via WhatsApp

        Args:
            phone: Número do telefone (ex: 5511999999999)
            message: Texto da mensagem

        Returns:
            True se enviado com sucesso
        """
        try:
            # Limpar número de telefone
            clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

            # Garantir que tem código do país (Brasil = 55)
            if not clean_phone.startswith("55"):
                clean_phone = f"55{clean_phone}"

            # API da Evolution
            url = f"{self.api_url}/message/sendText/{self.instance_name}"

            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "number": clean_phone,
                "text": message
            }

            # Enviar requisição
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

            logger.success(f"✅ Mensagem WhatsApp enviada para {clean_phone}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Erro HTTP ao enviar WhatsApp: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar WhatsApp: {e}")
            return False

    async def download_media(self, message_id: str, media_type: str = "audio") -> bytes:
        """
        Baixa mídia (áudio, imagem, vídeo) da Evolution API

        Args:
            message_id: ID da mensagem
            media_type: Tipo da mídia (audio, image, video)

        Returns:
            Bytes do arquivo ou None em caso de erro
        """
        try:
            logger.info(f"📥 Baixando {media_type} da Evolution API...")

            # Endpoint para baixar mídia
            url = f"{self.api_url}/chat/getBase64FromMediaMessage/{self.instance_name}"

            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "message": {
                    "key": {
                        "id": message_id
                    }
                },
                "convertToMp4": False  # Não converter
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                # Evolution retorna base64
                if "base64" in data:
                    import base64
                    media_bytes = base64.b64decode(data["base64"])
                    logger.success(f"✅ {media_type} baixado: {len(media_bytes)} bytes")
                    return media_bytes
                else:
                    logger.error(f"❌ Resposta não contém base64: {data}")
                    return None

        except Exception as e:
            logger.error(f"❌ Erro ao baixar {media_type}: {str(e)}")
            return None


# Instância global
evolution_service = EvolutionService()
