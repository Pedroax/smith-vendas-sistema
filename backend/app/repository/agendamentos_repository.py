"""
Repository para gerenciar agendamentos no Supabase
"""
from supabase import create_client, Client
from loguru import logger
from typing import Optional, List
from datetime import datetime
import os

from app.models.agendamento import Agendamento, AgendamentoStatus


class AgendamentosRepository:
    """Repository para operações de agendamentos no banco"""

    def __init__(self):
        """Inicializa conexão com Supabase"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados")

        self.client: Client = create_client(url, key)
        self.table = "agendamentos"

    async def create(self, agendamento: Agendamento) -> Agendamento:
        """
        Cria um novo agendamento

        Args:
            agendamento: Objeto Agendamento

        Returns:
            Agendamento criado
        """
        try:
            data = agendamento.model_dump(mode='json')

            # Converter datetime para ISO string
            if isinstance(data.get('data_hora'), datetime):
                data['data_hora'] = data['data_hora'].isoformat()
            if isinstance(data.get('created_at'), datetime):
                data['created_at'] = data['created_at'].isoformat()
            if isinstance(data.get('updated_at'), datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            if data.get('confirmado_em') and isinstance(data['confirmado_em'], datetime):
                data['confirmado_em'] = data['confirmado_em'].isoformat()

            # Converter enum para string
            if isinstance(data.get('status'), AgendamentoStatus):
                data['status'] = data['status'].value

            result = self.client.table(self.table).insert(data).execute()

            logger.success(f"✅ Agendamento criado: {agendamento.id}")

            return Agendamento(**result.data[0])

        except Exception as e:
            logger.error(f"❌ Erro ao criar agendamento: {e}", exc_info=True)
            raise

    async def get_by_id(self, agendamento_id: str) -> Optional[Agendamento]:
        """
        Busca agendamento por ID

        Args:
            agendamento_id: ID do agendamento

        Returns:
            Agendamento ou None se não encontrado
        """
        try:
            result = self.client.table(self.table).select("*").eq("id", agendamento_id).execute()

            if result.data:
                return Agendamento(**result.data[0])

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar agendamento {agendamento_id}: {e}")
            return None

    async def get_by_lead_id(self, lead_id: str) -> List[Agendamento]:
        """
        Busca todos os agendamentos de um lead

        Args:
            lead_id: ID do lead

        Returns:
            Lista de agendamentos
        """
        try:
            result = self.client.table(self.table).select("*").eq("lead_id", lead_id).order("data_hora", desc=True).execute()

            return [Agendamento(**item) for item in result.data]

        except Exception as e:
            logger.error(f"❌ Erro ao buscar agendamentos do lead {lead_id}: {e}")
            return []

    async def get_proximos_agendamentos(self, horas: int = 24) -> List[Agendamento]:
        """
        Busca agendamentos nas próximas X horas

        Args:
            horas: Número de horas à frente

        Returns:
            Lista de agendamentos
        """
        try:
            from datetime import timedelta

            agora = datetime.now()
            limite = agora + timedelta(hours=horas)

            result = (
                self.client.table(self.table)
                .select("*")
                .gte("data_hora", agora.isoformat())
                .lte("data_hora", limite.isoformat())
                .eq("status", AgendamentoStatus.AGENDADO.value)
                .order("data_hora")
                .execute()
            )

            return [Agendamento(**item) for item in result.data]

        except Exception as e:
            logger.error(f"❌ Erro ao buscar próximos agendamentos: {e}")
            return []

    async def update(self, agendamento_id: str, data: dict) -> Optional[Agendamento]:
        """
        Atualiza um agendamento

        Args:
            agendamento_id: ID do agendamento
            data: Dados a atualizar

        Returns:
            Agendamento atualizado ou None em caso de erro
        """
        try:
            # Converter datetime para ISO string
            if 'data_hora' in data and isinstance(data['data_hora'], datetime):
                data['data_hora'] = data['data_hora'].isoformat()
            if 'confirmado_em' in data and isinstance(data['confirmado_em'], datetime):
                data['confirmado_em'] = data['confirmado_em'].isoformat()

            # Converter enum para string
            if 'status' in data and isinstance(data['status'], AgendamentoStatus):
                data['status'] = data['status'].value

            # Atualizar timestamp
            data['updated_at'] = datetime.now().isoformat()

            result = (
                self.client.table(self.table)
                .update(data)
                .eq("id", agendamento_id)
                .execute()
            )

            if result.data:
                logger.success(f"✅ Agendamento atualizado: {agendamento_id}")
                return Agendamento(**result.data[0])

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar agendamento {agendamento_id}: {e}", exc_info=True)
            return None

    async def marcar_lembrete_enviado(
        self,
        agendamento_id: str,
        tipo_lembrete: str  # "24h", "3h", "30min"
    ) -> bool:
        """
        Marca que um lembrete foi enviado

        Args:
            agendamento_id: ID do agendamento
            tipo_lembrete: Tipo do lembrete ("24h", "3h", "30min")

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            campo = f"lembrete_{tipo_lembrete}_enviado"

            result = await self.update(agendamento_id, {campo: True})

            return result is not None

        except Exception as e:
            logger.error(f"❌ Erro ao marcar lembrete: {e}")
            return False

    async def cancelar(
        self,
        agendamento_id: str,
        motivo: Optional[str] = None
    ) -> Optional[Agendamento]:
        """
        Cancela um agendamento

        Args:
            agendamento_id: ID do agendamento
            motivo: Motivo do cancelamento

        Returns:
            Agendamento cancelado ou None em caso de erro
        """
        data = {
            "status": AgendamentoStatus.CANCELADO.value,
        }

        if motivo:
            data["motivo_cancelamento"] = motivo

        return await self.update(agendamento_id, data)

    async def confirmar(
        self,
        agendamento_id: str,
        via: str = "whatsapp"
    ) -> Optional[Agendamento]:
        """
        Confirma um agendamento

        Args:
            agendamento_id: ID do agendamento
            via: Canal de confirmação

        Returns:
            Agendamento confirmado ou None em caso de erro
        """
        return await self.update(agendamento_id, {
            "status": AgendamentoStatus.CONFIRMADO.value,
            "confirmado_em": datetime.now(),
            "confirmado_via": via
        })
