"""
Repository para operações de banco de dados com Leads
Gerencia leads e conversation_messages no Supabase
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from postgrest.exceptions import APIError

from app.database import get_supabase
from app.models.lead import (
    Lead,
    LeadStatus,
    LeadOrigin,
    LeadTemperature,
    ConversationMessage,
    QualificationData,
    ROIAnalysis,
    FollowUpConfig,
)


class LeadsRepository:
    """Repository para gerenciar leads no Supabase"""

    def __init__(self):
        self.supabase = get_supabase()

    def _convert_db_to_lead(self, db_lead: Dict[str, Any]) -> Lead:
        """
        Converte registro do banco para objeto Lead

        Args:
            db_lead: Registro do banco de dados

        Returns:
            Objeto Lead
        """
        # Converter JSONB para Pydantic models (qualificacao_detalhes -> qualification_data)
        qualification_data = None
        if db_lead.get("qualificacao_detalhes"):
            qualification_data = QualificationData(**db_lead["qualificacao_detalhes"])

        roi_analysis = None
        if db_lead.get("roi_analysis"):
            roi_data = db_lead["roi_analysis"].copy()
            # Converter string ISO para datetime se existir
            if roi_data.get("generated_at"):
                roi_data["generated_at"] = datetime.fromisoformat(
                    roi_data["generated_at"].replace("Z", "+00:00")
                )
            roi_analysis = ROIAnalysis(**roi_data)

        followup_config = FollowUpConfig()
        if db_lead.get("followup_config"):
            followup_data = db_lead["followup_config"].copy()
            # Converter string ISO para datetime se existir
            if followup_data.get("proxima_tentativa"):
                followup_data["proxima_tentativa"] = datetime.fromisoformat(
                    followup_data["proxima_tentativa"].replace("Z", "+00:00")
                )
            followup_config = FollowUpConfig(**followup_data)

        # Converter timestamps
        created_at = datetime.fromisoformat(db_lead["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(db_lead["updated_at"].replace("Z", "+00:00"))

        ultima_interacao = None
        if db_lead.get("ultima_interacao"):
            ultima_interacao = datetime.fromisoformat(
                db_lead["ultima_interacao"].replace("Z", "+00:00")
            )

        meeting_scheduled_at = None
        if db_lead.get("meeting_scheduled_at"):
            meeting_scheduled_at = datetime.fromisoformat(
                db_lead["meeting_scheduled_at"].replace("Z", "+00:00")
            )

        won_at = None
        if db_lead.get("won_at"):
            won_at = datetime.fromisoformat(db_lead["won_at"].replace("Z", "+00:00"))

        lost_at = None
        if db_lead.get("lost_at"):
            lost_at = datetime.fromisoformat(db_lead["lost_at"].replace("Z", "+00:00"))

        # Conversation history será carregado separadamente se necessário
        # Por padrão, deixar vazio para performance
        conversation_history = []

        return Lead(
            id=str(db_lead["id"]),  # Converter int para str
            nome=db_lead["nome"],
            empresa=db_lead.get("empresa"),
            telefone=db_lead["telefone"],
            email=db_lead.get("email"),
            avatar=None,  # Campo não existe no banco
            status=LeadStatus(db_lead["status"]),
            origem=LeadOrigin(db_lead["origem"]),
            temperatura=LeadTemperature(db_lead["temperatura"]) if db_lead.get("temperatura") else None,
            lead_score=db_lead.get("lead_score", 0),
            qualification_data=qualification_data,
            roi_analysis=roi_analysis,
            valor_estimado=0.0,  # Campo não existe no banco
            meeting_scheduled_at=meeting_scheduled_at,
            meeting_google_event_id=db_lead.get("meeting_google_event_id"),
            temp_meeting_slot=db_lead.get("temp_meeting_slot"),  # Slot temporário de agendamento
            followup_config=followup_config,
            conversation_history=conversation_history,
            ultima_interacao=ultima_interacao,
            ultima_mensagem_ia=None,  # Campo não existe no banco
            notas=db_lead.get("observacoes"),  # observacoes -> notas
            tags=db_lead.get("tags") or [],  # Se None, usar lista vazia
            ai_summary=None,  # Campo não existe no banco
            ai_next_action=None,  # Campo não existe no banco
            requires_human_approval=False,  # Campo não existe no banco
            created_at=created_at,
            updated_at=updated_at,
            lost_at=lost_at,
            won_at=won_at,
        )

    def _convert_lead_to_db(self, lead: Lead) -> Dict[str, Any]:
        """
        Converte objeto Lead para formato do banco

        Args:
            lead: Objeto Lead

        Returns:
            Dicionário para inserção/atualização no banco
        """
        # Mapear apenas campos que EXISTEM no banco de dados
        db_data = {
            "nome": lead.nome,
            "empresa": lead.empresa,
            "telefone": lead.telefone,
            "email": lead.email,
            "cargo": getattr(lead.qualification_data, "setor", None) if lead.qualification_data else None,
            "status": lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
            "origem": lead.origem.value if isinstance(lead.origem, LeadOrigin) else lead.origem,
            "temperatura": lead.temperatura.value if isinstance(lead.temperatura, LeadTemperature) else lead.temperatura if lead.temperatura else None,
            "lead_score": lead.lead_score,
            "observacoes": lead.notas,  # notas -> observacoes no banco
            "tags": lead.tags,
            "meeting_scheduled_at": lead.meeting_scheduled_at.isoformat() if lead.meeting_scheduled_at else None,
            "meeting_google_event_id": lead.meeting_google_event_id,
            "temp_meeting_slot": lead.temp_meeting_slot,  # Slot temporário de agendamento (JSONB)
        }

        # Converter qualification_data para qualificacao_detalhes (JSONB)
        if lead.qualification_data:
            db_data["qualificacao_detalhes"] = lead.qualification_data.model_dump()
            # Extrair faturamento_anual para coluna específica
            if lead.qualification_data.faturamento_anual:
                db_data["faturamento_anual"] = lead.qualification_data.faturamento_anual

        return db_data

    async def create(self, lead: Lead) -> Lead:
        """
        Cria um novo lead no banco

        Args:
            lead: Lead a criar

        Returns:
            Lead criado com ID do banco
        """
        try:
            db_data = self._convert_lead_to_db(lead)
            # Não enviar ID - deixar o banco gerar automaticamente (serial)

            response = self.supabase.table("leads").insert(db_data).execute()

            if not response.data:
                raise Exception("Erro ao criar lead: resposta vazia do banco")

            logger.info(f"Lead criado no banco: {lead.nome} ({lead.id})")

            return self._convert_db_to_lead(response.data[0])

        except APIError as e:
            logger.error(f"Erro API ao criar lead: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar lead: {e}")
            raise

    async def get_by_id(self, lead_id: str) -> Optional[Lead]:
        """
        Busca lead por ID

        Args:
            lead_id: ID do lead

        Returns:
            Lead encontrado ou None
        """
        try:
            response = self.supabase.table("leads").select("*").eq("id", lead_id).execute()

            if not response.data:
                return None

            return self._convert_db_to_lead(response.data[0])

        except Exception as e:
            logger.error(f"Erro ao buscar lead {lead_id}: {e}")
            raise

    async def get_by_telefone(self, telefone: str) -> Optional[Lead]:
        """
        Busca lead por telefone

        Args:
            telefone: Telefone do lead

        Returns:
            Lead encontrado ou None
        """
        try:
            response = self.supabase.table("leads").select("*").eq("telefone", telefone).execute()

            if not response.data:
                return None

            return self._convert_db_to_lead(response.data[0])

        except Exception as e:
            logger.error(f"Erro ao buscar lead por telefone {telefone}: {e}")
            raise

    async def list_all(
        self,
        status: Optional[LeadStatus] = None,
        origem: Optional[LeadOrigin] = None,
        temperatura: Optional[LeadTemperature] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Lead]:
        """
        Lista leads com filtros opcionais

        Args:
            status: Filtrar por status
            origem: Filtrar por origem
            temperatura: Filtrar por temperatura
            limit: Número máximo de resultados
            offset: Offset para paginação

        Returns:
            Lista de leads
        """
        try:
            query = self.supabase.table("leads").select("*")

            # Aplicar filtros
            if status:
                query = query.eq("status", status.value)

            if origem:
                query = query.eq("origem", origem.value)

            if temperatura:
                query = query.eq("temperatura", temperatura.value)

            # Ordenar por created_at decrescente
            query = query.order("created_at", desc=True)

            # Aplicar paginação
            query = query.range(offset, offset + limit - 1)

            response = query.execute()

            if not response.data:
                return []

            return [self._convert_db_to_lead(lead) for lead in response.data]

        except Exception as e:
            logger.error(f"Erro ao listar leads: {e}")
            raise

    async def update(self, lead_id: str, updates: Dict[str, Any]) -> Lead:
        """
        Atualiza um lead existente

        Args:
            lead_id: ID do lead
            updates: Dicionário com campos a atualizar

        Returns:
            Lead atualizado
        """
        try:
            # Atualizar updated_at automaticamente (trigger do banco fará isso, mas garantir)
            updates["updated_at"] = datetime.now().isoformat()

            response = self.supabase.table("leads").update(updates).eq("id", lead_id).execute()

            if not response.data:
                raise Exception(f"Lead {lead_id} não encontrado para atualização")

            logger.info(f"Lead atualizado: {lead_id}")

            return self._convert_db_to_lead(response.data[0])

        except Exception as e:
            logger.error(f"Erro ao atualizar lead {lead_id}: {e}")
            raise

    async def update_empresa(self, lead_id: str, empresa: str) -> bool:
        """
        Atualiza o nome da empresa do lead

        Args:
            lead_id: ID do lead
            empresa: Nome da empresa

        Returns:
            True se atualizou com sucesso
        """
        try:
            response = self.supabase.table("leads")\
                .update({"empresa": empresa})\
                .eq("id", lead_id)\
                .execute()

            if response.data:
                logger.info(f"Empresa atualizada para lead {lead_id}: {empresa}")
                return True
            return False

        except Exception as e:
            logger.error(f"Erro ao atualizar empresa do lead {lead_id}: {e}")
            return False

    async def delete(self, lead_id: str) -> bool:
        """
        Deleta um lead

        Args:
            lead_id: ID do lead

        Returns:
            True se deletado com sucesso
        """
        try:
            # Deletar mensagens primeiro (CASCADE deve fazer isso automaticamente, mas garantir)
            self.supabase.table("conversation_messages").delete().eq("lead_id", lead_id).execute()

            # Deletar lead
            response = self.supabase.table("leads").delete().eq("id", lead_id).execute()

            logger.warning(f"Lead deletado: {lead_id}")

            return True

        except Exception as e:
            logger.error(f"Erro ao deletar lead {lead_id}: {e}")
            raise

    async def get_conversation_messages(self, lead_id: str) -> List[ConversationMessage]:
        """
        Busca todas as mensagens de conversação de um lead

        Args:
            lead_id: ID do lead

        Returns:
            Lista de mensagens ordenadas por timestamp
        """
        try:
            response = (
                self.supabase.table("conversation_messages")
                .select("*")
                .eq("lead_id", lead_id)
                .order("timestamp", desc=False)
                .execute()
            )
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens do lead {lead_id}: {e}")
            # Se tabela não existir, retornar lista vazia (não crashar)
            return []

        try:

            if not response.data:
                return []

            messages = []
            for msg in response.data:
                messages.append(
                    ConversationMessage(
                        id=msg["id"],
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00")),
                        metadata=msg.get("metadata"),
                    )
                )

            return messages

        except Exception as e:
            logger.error(f"Erro ao buscar mensagens do lead {lead_id}: {e}")
            raise

    async def add_conversation_message(
        self, lead_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Adiciona uma mensagem à conversação de um lead

        Args:
            lead_id: ID do lead
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
            metadata: Metadados opcionais

        Returns:
            Mensagem criada
        """
        try:
            import uuid

            # Garantir que lead_id é int para consistência no banco
            lead_id_int = int(lead_id) if lead_id else None

            message_data = {
                "id": str(uuid.uuid4()),
                "lead_id": lead_id_int,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
            }

            try:
                response = self.supabase.table("conversation_messages").insert(message_data).execute()
            except Exception as insert_error:
                logger.error(f"Erro ao adicionar mensagem ao lead {lead_id}: {insert_error}")
                # Se tabela não existir, retornar mensagem fictícia (não crashar)
                return ConversationMessage(
                    id=message_data["id"],
                    role=role,
                    content=content,
                    timestamp=datetime.now()
                )

            if not response.data:
                raise Exception("Erro ao adicionar mensagem: resposta vazia")

            msg = response.data[0]

            logger.info(f"Mensagem adicionada ao lead {lead_id}: {role}")

            return ConversationMessage(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00")),
                metadata=msg.get("metadata"),
            )

        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem ao lead {lead_id}: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas agregadas dos leads
        Usa a função get_leads_stats() do banco

        Returns:
            Dicionário com estatísticas
        """
        try:
            # Chamar função RPC do Supabase
            response = self.supabase.rpc("get_leads_stats").execute()

            if not response.data:
                return {
                    "total_leads": 0,
                    "por_status": {},
                    "por_origem": {},
                    "score_medio": 0,
                    "valor_total_pipeline": 0,
                    "taxa_qualificacao": 0,
                    "taxa_conversao": 0,
                }

            return response.data

        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            # Retornar estatísticas vazias em caso de erro
            return {
                "total_leads": 0,
                "por_status": {},
                "por_origem": {},
                "score_medio": 0,
                "valor_total_pipeline": 0,
                "taxa_qualificacao": 0,
                "taxa_conversao": 0,
            }
