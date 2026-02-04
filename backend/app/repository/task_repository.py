"""
Repository para Tarefas
"""

import uuid
from datetime import datetime
from typing import List, Optional
from loguru import logger

from app.config import settings
from app.models.task import Task, TaskCreate, TaskUpdate, TaskStatus


class TaskRepository:
    def __init__(self):
        self.supabase = settings.supabase
        self.table = "tasks"

    async def create_task(self, data: TaskCreate) -> Optional[Task]:
        now = datetime.utcnow().isoformat()

        lead_nome = None
        project_nome = None

        if data.lead_id:
            try:
                lead = self.supabase.table("leads").select("nome").eq("id", data.lead_id).execute()
                if lead.data:
                    lead_nome = lead.data[0]["nome"]
            except Exception as e:
                logger.warning(f"Erro ao buscar nome do lead: {e}")

        if data.project_id:
            try:
                project = self.supabase.table("portal_projects").select("nome").eq("id", data.project_id).execute()
                if project.data:
                    project_nome = project.data[0]["nome"]
            except Exception as e:
                logger.warning(f"Erro ao buscar nome do projeto: {e}")

        task_data = {
            "id": str(uuid.uuid4()),
            "titulo": data.titulo,
            "descricao": data.descricao,
            "status": data.status if isinstance(data.status, str) else data.status.value,
            "prioridade": data.prioridade if isinstance(data.prioridade, str) else data.prioridade.value,
            "prazo": data.prazo,
            "lead_id": data.lead_id,
            "lead_nome": lead_nome,
            "project_id": data.project_id,
            "project_nome": project_nome,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }

        result = self.supabase.table(self.table).insert(task_data).execute()

        if result.data:
            return Task(**result.data[0])
        return None

    async def get_task(self, task_id: str) -> Optional[Task]:
        result = self.supabase.table(self.table).select("*").eq("id", task_id).execute()
        if result.data:
            return Task(**result.data[0])
        return None

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        prioridade: Optional[str] = None,
        lead_id: Optional[str] = None,
        project_id: Optional[str] = None,
        include_feito: bool = True,
        limit: int = 100
    ) -> List[Task]:
        query = self.supabase.table(self.table).select("*")

        if status:
            status_val = status if isinstance(status, str) else status.value
            query = query.eq("status", status_val)

        if not include_feito and not status:
            query = query.neq("status", "feito")

        if prioridade:
            query = query.eq("prioridade", prioridade)

        if lead_id:
            query = query.eq("lead_id", lead_id)

        if project_id:
            query = query.eq("project_id", project_id)

        query = query.order("created_at", desc=True).limit(limit)
        result = query.execute()

        return [Task(**task) for task in result.data] if result.data else []

    async def update_task(self, task_id: str, data: TaskUpdate) -> Optional[Task]:
        now = datetime.utcnow().isoformat()
        update_data = {"updated_at": now}

        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.descricao is not None:
            update_data["descricao"] = data.descricao
        if data.status is not None:
            status_val = data.status if isinstance(data.status, str) else data.status.value
            update_data["status"] = status_val
            if status_val == "feito":
                update_data["completed_at"] = now
            else:
                update_data["completed_at"] = None
        if data.prioridade is not None:
            update_data["prioridade"] = data.prioridade if isinstance(data.prioridade, str) else data.prioridade.value
        if data.prazo is not None:
            update_data["prazo"] = data.prazo if data.prazo else None

        if data.lead_id is not None:
            update_data["lead_id"] = data.lead_id if data.lead_id else None
            if data.lead_id:
                try:
                    lead = self.supabase.table("leads").select("nome").eq("id", data.lead_id).execute()
                    if lead.data:
                        update_data["lead_nome"] = lead.data[0]["nome"]
                except Exception:
                    pass
            else:
                update_data["lead_nome"] = None

        if data.project_id is not None:
            update_data["project_id"] = data.project_id if data.project_id else None
            if data.project_id:
                try:
                    project = self.supabase.table("portal_projects").select("nome").eq("id", data.project_id).execute()
                    if project.data:
                        update_data["project_nome"] = project.data[0]["nome"]
                except Exception:
                    pass
            else:
                update_data["project_nome"] = None

        result = self.supabase.table(self.table).update(update_data).eq("id", task_id).execute()

        if result.data:
            return Task(**result.data[0])
        return None

    async def delete_task(self, task_id: str) -> bool:
        result = self.supabase.table(self.table).delete().eq("id", task_id).execute()
        return bool(result.data)

    async def get_counts(self) -> dict:
        counts = {"hoje": 0, "esta_semana": 0, "depois": 0, "feito": 0}
        for status in counts.keys():
            result = self.supabase.table(self.table).select("id").eq("status", status).execute()
            counts[status] = len(result.data) if result.data else 0
        return counts


def get_task_repository() -> TaskRepository:
    return TaskRepository()
