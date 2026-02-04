from typing import List, Dict
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gerenciador de conexões WebSocket para broadcast de eventos em tempo real"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Aceitar nova conexão WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nova conexão WebSocket. Total de conexões: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remover conexão WebSocket"""
        self.active_connections.remove(websocket)
        logger.info(f"Conexão WebSocket fechada. Total de conexões: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Enviar mensagem para um cliente específico"""
        await websocket.send_text(message)

    async def broadcast(self, message: Dict):
        """Enviar mensagem para todos os clientes conectados"""
        if not self.active_connections:
            logger.debug("Nenhuma conexão ativa para broadcast")
            return

        message_json = json.dumps(message)
        logger.info(f"Broadcasting para {len(self.active_connections)} clientes: {message.get('type')}")

        # Enviar para todas as conexões ativas
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem via WebSocket: {e}")
                disconnected.append(connection)

        # Remover conexões que falharam
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_lead_created(self, lead_data: Dict):
        """Broadcast quando um lead é criado"""
        await self.broadcast({
            "type": "lead_created",
            "data": lead_data
        })

    async def broadcast_lead_updated(self, lead_data: Dict):
        """Broadcast quando um lead é atualizado"""
        await self.broadcast({
            "type": "lead_updated",
            "data": lead_data
        })

    async def broadcast_lead_deleted(self, lead_id: str):
        """Broadcast quando um lead é deletado"""
        await self.broadcast({
            "type": "lead_deleted",
            "data": {"id": lead_id}
        })

    async def broadcast_lead_status_changed(self, lead_id: str, old_status: str, new_status: str):
        """Broadcast quando o status de um lead muda"""
        await self.broadcast({
            "type": "lead_status_changed",
            "data": {
                "id": lead_id,
                "old_status": old_status,
                "new_status": new_status
            }
        })

# Instância global do gerenciador
manager = ConnectionManager()
