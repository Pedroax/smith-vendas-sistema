"""
Serviço de integração com WhatsApp via Evolution API
Gerencia envio e recebimento de mensagens
"""
import httpx
from typing import Optional, Dict, Any
from pathlib import Path

from app.config import settings
from loguru import logger


class WhatsAppService:
    """Serviço de integração com WhatsApp via Evolution API"""

    def __init__(self):
        self.base_url = settings.evolution_api_url.rstrip('/')
        self.api_key = settings.evolution_api_key
        self.instance_name = settings.evolution_instance_name

        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    async def send_text_message(self, phone: str, message: str) -> bool:
        """
        Envia mensagem de texto para um número

        Args:
            phone: Número de telefone (formato: 5521999999999)
            message: Texto da mensagem

        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            url = f"{self.base_url}/message/sendText/{self.instance_name}"

            payload = {
                "number": phone,
                "text": message
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)

                if response.status_code == 200 or response.status_code == 201:
                    logger.success(f"✅ Mensagem enviada para {phone}")
                    return True
                else:
                    logger.error(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem via WhatsApp: {e}")
            return False

    async def send_file(self, phone: str, file_path: str, caption: Optional[str] = None) -> bool:
        """
        Envia arquivo (PDF, imagem, etc) para um número

        Args:
            phone: Número de telefone
            file_path: Caminho do arquivo
            caption: Legenda opcional

        Returns:
            True se enviado com sucesso
        """
        try:
            url = f"{self.base_url}/message/sendMedia/{self.instance_name}"

            # Ler arquivo e converter para base64
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                return False

            with open(file_path, 'rb') as f:
                import base64
                file_data = base64.b64encode(f.read()).decode('utf-8')

            payload = {
                "number": phone,
                "mediatype": "document",
                "mimetype": "application/pdf",
                "caption": caption or "",
                "media": file_data,
                "fileName": file_path_obj.name
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)

                if response.status_code == 200 or response.status_code == 201:
                    logger.success(f"✅ Arquivo enviado para {phone}")
                    return True
                else:
                    logger.error(f"❌ Erro ao enviar arquivo: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ Erro ao enviar arquivo via WhatsApp: {e}")
            return False

    async def send_roi_analysis(self, phone: str, pdf_path: str, lead_name: str) -> bool:
        """
        Envia análise de ROI personalizada

        Args:
            phone: Número do lead
            pdf_path: Caminho do PDF gerado
            lead_name: Nome do lead

        Returns:
            True se enviado com sucesso
        """
        try:
            # Mensagem de acompanhamento
            intro_message = f"""Oi {lead_name}! 📊

Acabei de preparar uma análise personalizada baseada nas informações que você me passou.

Vou te enviar agora um estudo mostrando o potencial de economia e retorno que a automação com IA pode trazer para sua empresa.

Dá uma olhada com calma! 👇"""

            # Enviar mensagem introdutória
            await self.send_text_message(phone, intro_message)

            # Aguardar 2 segundos
            import asyncio
            await asyncio.sleep(2)

            # Enviar PDF
            caption = f"📊 Análise de ROI Personalizada - {lead_name}"
            success = await self.send_file(phone, pdf_path, caption)

            if success:
                # Mensagem de fechamento
                closing_message = """Com base nessa análise, vale muito a pena conversarmos!

Que tal agendar uma reunião rápida de 30 minutos para eu te mostrar na prática como funciona?

Tenho horários disponíveis essa semana. Qual dia funciona melhor para você? 📅"""

                await asyncio.sleep(2)
                await self.send_text_message(phone, closing_message)

            return success

        except Exception as e:
            logger.error(f"❌ Erro ao enviar análise de ROI: {e}")
            return False

    async def get_instance_status(self) -> Dict[str, Any]:
        """
        Verifica status da instância do WhatsApp

        Returns:
            Dicionário com status da conexão
        """
        try:
            url = f"{self.base_url}/instance/connectionState/{self.instance_name}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Status da instância: {data}")
                    return data
                else:
                    logger.error(f"Erro ao verificar status: {response.status_code}")
                    return {"state": "error", "status_code": response.status_code}

        except Exception as e:
            logger.error(f"Erro ao verificar status da instância: {e}")
            return {"state": "error", "error": str(e)}

    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Processa dados do webhook e extrai informações da mensagem

        Args:
            webhook_data: Dados recebidos no webhook

        Returns:
            Dicionário com phone, message, name ou None
        """
        try:
            event = webhook_data.get("event")

            # Processar apenas mensagens recebidas
            if event != "messages.upsert":
                return None

            data = webhook_data.get("data", {})
            key = data.get("key", {})
            message_data = data.get("message", {})

            # Ignorar mensagens enviadas por nós
            if key.get("fromMe"):
                return None

            # Extrair informações
            phone = key.get("remoteJid", "").replace("@s.whatsapp.net", "")

            # Extrair texto da mensagem
            message = None
            if "conversation" in message_data:
                message = message_data["conversation"]
            elif "extendedTextMessage" in message_data:
                message = message_data["extendedTextMessage"].get("text")

            if not message:
                return None

            # Extrair nome (pushName)
            push_name = data.get("pushName", "Cliente")

            return {
                "phone": phone,
                "message": message,
                "name": push_name
            }

        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return None


# Instância global
whatsapp_service = WhatsAppService()
