"""
Repository para operações de banco de dados com Projetos
Gerencia projetos no Supabase
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from loguru import logger
from postgrest.exceptions import APIError

from app.database import get_supabase
from app.models.project import Project, ProjectStatus, ProjectPriority


class ProjectsRepository:
    """Repository para gerenciar projetos no Supabase"""

    def __init__(self):
        self.supabase = get_supabase()

    def _convert_db_to_project(self, db_project: Dict[str, Any]) -> Project:
        """
        Converte registro do banco para objeto Project

        Args:
            db_project: Registro do banco de dados

        Returns:
            Objeto Project
        """
        # Converter timestamps
        created_at = datetime.fromisoformat(db_project["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(db_project["updated_at"].replace("Z", "+00:00"))

        prazo = None
        if db_project.get("prazo"):
            prazo = datetime.fromisoformat(db_project["prazo"].replace("Z", "+00:00"))

        started_at = None
        if db_project.get("started_at"):
            started_at = datetime.fromisoformat(db_project["started_at"].replace("Z", "+00:00"))

        completed_at = None
        if db_project.get("completed_at"):
            completed_at = datetime.fromisoformat(db_project["completed_at"].replace("Z", "+00:00"))

        return Project(
            id=db_project["id"],
            nome=db_project["nome"],
            descricao=db_project.get("descricao"),
            cliente_id=db_project.get("cliente_id"),
            cliente_nome=db_project.get("cliente_nome"),
            status=ProjectStatus(db_project["status"]),
            prioridade=ProjectPriority(db_project["prioridade"]),
            prazo=prazo,
            valor=float(db_project.get("valor", 0)) if db_project.get("valor") else None,
            responsavel=db_project.get("responsavel"),
            tags=db_project.get("tags", []),
            notas=db_project.get("notas"),
            progresso_percentual=db_project.get("progresso_percentual", 0),
            created_at=created_at,
            updated_at=updated_at,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _convert_project_to_db(self, project: Project) -> Dict[str, Any]:
        """
        Converte objeto Project para formato do banco

        Args:
            project: Objeto Project

        Returns:
            Dicionário para inserção/atualização no banco
        """
        db_data = {
            "nome": project.nome,
            "descricao": project.descricao,
            "cliente_id": project.cliente_id,
            "cliente_nome": project.cliente_nome,
            "status": project.status.value if isinstance(project.status, ProjectStatus) else project.status,
            "prioridade": project.prioridade.value if isinstance(project.prioridade, ProjectPriority) else project.prioridade,
            "prazo": project.prazo.isoformat() if project.prazo else None,
            "valor": project.valor,
            "responsavel": project.responsavel,
            "tags": project.tags,
            "notas": project.notas,
            "progresso_percentual": project.progresso_percentual,
        }

        return db_data

    async def create(self, project: Project) -> Project:
        """
        Cria um novo projeto no banco

        Args:
            project: Projeto a criar

        Returns:
            Projeto criado com ID do banco
        """
        try:
            db_data = self._convert_project_to_db(project)
            db_data["id"] = project.id  # Incluir ID na criação

            response = self.supabase.table("projects").insert(db_data).execute()

            if not response.data:
                raise Exception("Erro ao criar projeto: resposta vazia do banco")

            logger.info(f"Projeto criado no banco: {project.nome} ({project.id})")

            return self._convert_db_to_project(response.data[0])

        except APIError as e:
            logger.error(f"Erro API ao criar projeto: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar projeto: {e}")
            raise

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """
        Busca projeto por ID

        Args:
            project_id: ID do projeto

        Returns:
            Projeto encontrado ou None
        """
        try:
            response = self.supabase.table("projects").select("*").eq("id", project_id).execute()

            if not response.data:
                return None

            return self._convert_db_to_project(response.data[0])

        except Exception as e:
            logger.error(f"Erro ao buscar projeto {project_id}: {e}")
            raise

    async def list_all(
        self,
        status: Optional[ProjectStatus] = None,
        prioridade: Optional[ProjectPriority] = None,
        cliente_id: Optional[str] = None,
        responsavel: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        """
        Lista projetos com filtros opcionais

        Args:
            status: Filtrar por status
            prioridade: Filtrar por prioridade
            cliente_id: Filtrar por cliente
            responsavel: Filtrar por responsável
            limit: Número máximo de resultados
            offset: Offset para paginação

        Returns:
            Lista de projetos
        """
        try:
            query = self.supabase.table("projects").select("*")

            # Aplicar filtros
            if status:
                query = query.eq("status", status.value)

            if prioridade:
                query = query.eq("prioridade", prioridade.value)

            if cliente_id:
                query = query.eq("cliente_id", cliente_id)

            if responsavel:
                query = query.eq("responsavel", responsavel)

            # Ordenar por created_at decrescente
            query = query.order("created_at", desc=True)

            # Aplicar paginação
            query = query.range(offset, offset + limit - 1)

            response = query.execute()

            if not response.data:
                return []

            return [self._convert_db_to_project(proj) for proj in response.data]

        except Exception as e:
            logger.error(f"Erro ao listar projetos: {e}")
            raise

    async def update(self, project_id: str, updates: Dict[str, Any]) -> Project:
        """
        Atualiza um projeto existente

        Args:
            project_id: ID do projeto
            updates: Dicionário com campos a atualizar

        Returns:
            Projeto atualizado
        """
        try:
            # Atualizar updated_at automaticamente
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Se mudou para "em_andamento" e não tinha started_at, definir
            if updates.get("status") == ProjectStatus.EM_ANDAMENTO.value:
                existing = await self.get_by_id(project_id)
                if existing and not existing.started_at:
                    updates["started_at"] = datetime.now(timezone.utc).isoformat()

            # Se mudou para "concluido" e não tinha completed_at, definir
            if updates.get("status") == ProjectStatus.CONCLUIDO.value:
                existing = await self.get_by_id(project_id)
                if existing and not existing.completed_at:
                    updates["completed_at"] = datetime.now(timezone.utc).isoformat()

            response = self.supabase.table("projects").update(updates).eq("id", project_id).execute()

            if not response.data:
                raise Exception(f"Projeto {project_id} não encontrado para atualização")

            logger.info(f"Projeto atualizado: {project_id}")

            return self._convert_db_to_project(response.data[0])

        except Exception as e:
            logger.error(f"Erro ao atualizar projeto {project_id}: {e}")
            raise

    async def delete(self, project_id: str) -> bool:
        """
        Deleta um projeto

        Args:
            project_id: ID do projeto

        Returns:
            True se deletado com sucesso
        """
        try:
            response = self.supabase.table("projects").delete().eq("id", project_id).execute()

            logger.warning(f"Projeto deletado: {project_id}")

            return True

        except Exception as e:
            logger.error(f"Erro ao deletar projeto {project_id}: {e}")
            raise

    async def get_stats_by_status(self) -> Dict[str, int]:
        """
        Retorna contagem de projetos por status (para o Kanban)

        Returns:
            Dicionário com contagem por status
        """
        try:
            all_projects = await self.list_all(limit=1000)

            stats = {
                "backlog": 0,
                "em_andamento": 0,
                "concluido": 0,
                "cancelado": 0,
            }

            for project in all_projects:
                stats[project.status.value] += 1

            return stats

        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas de projetos: {e}")
            return {"backlog": 0, "em_andamento": 0, "concluido": 0, "cancelado": 0}
