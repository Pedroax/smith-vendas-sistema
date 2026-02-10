"""
Repository para gerenciar marcos de projetos e lembretes
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from app.models.milestone import (
    Milestone, MilestoneCreate, MilestoneUpdate,
    ScheduledReminder, MilestoneStatus, ReminderType
)


class MilestoneRepository:
    """Repository para operações de marcos e lembretes"""

    def __init__(self, db: Session):
        self.db = db

    async def create_milestone(self, milestone_data: MilestoneCreate) -> Milestone:
        """
        Cria um novo marco de projeto

        Os lembretes são criados automaticamente pelo trigger do banco
        """
        query = text("""
            INSERT INTO project_milestones (
                project_id, nome, descricao, ordem, data_limite,
                notificacao_whatsapp, notificacao_email
            )
            VALUES (
                :project_id, :nome, :descricao, :ordem, :data_limite,
                :notificacao_whatsapp, :notificacao_email
            )
            RETURNING *
        """)

        result = self.db.execute(query, {
            "project_id": milestone_data.project_id,
            "nome": milestone_data.nome,
            "descricao": milestone_data.descricao,
            "ordem": milestone_data.ordem,
            "data_limite": milestone_data.data_limite,
            "notificacao_whatsapp": milestone_data.notificacao_whatsapp,
            "notificacao_email": milestone_data.notificacao_email,
        }).fetchone()

        self.db.commit()

        return self._row_to_milestone(result)

    async def get_milestone(self, milestone_id: UUID) -> Optional[Milestone]:
        """Busca um marco pelo ID"""
        query = text("""
            SELECT * FROM project_milestones
            WHERE id = :milestone_id
        """)

        result = self.db.execute(query, {"milestone_id": str(milestone_id)}).fetchone()

        if not result:
            return None

        return self._row_to_milestone(result)

    async def get_project_milestones(self, project_id: int) -> List[Milestone]:
        """Lista todos os marcos de um projeto (ordenados por ordem)"""
        query = text("""
            SELECT * FROM project_milestones
            WHERE project_id = :project_id
            ORDER BY ordem ASC, data_limite ASC
        """)

        results = self.db.execute(query, {"project_id": project_id}).fetchall()

        return [self._row_to_milestone(row) for row in results]

    async def update_milestone(
        self,
        milestone_id: UUID,
        milestone_data: MilestoneUpdate
    ) -> Optional[Milestone]:
        """Atualiza um marco existente"""
        # Construir query dinamicamente apenas com campos fornecidos
        updates = []
        params = {"milestone_id": str(milestone_id)}

        if milestone_data.nome is not None:
            updates.append("nome = :nome")
            params["nome"] = milestone_data.nome

        if milestone_data.descricao is not None:
            updates.append("descricao = :descricao")
            params["descricao"] = milestone_data.descricao

        if milestone_data.ordem is not None:
            updates.append("ordem = :ordem")
            params["ordem"] = milestone_data.ordem

        if milestone_data.data_limite is not None:
            updates.append("data_limite = :data_limite")
            params["data_limite"] = milestone_data.data_limite

        if milestone_data.status is not None:
            updates.append("status = :status")
            params["status"] = milestone_data.status.value

        if milestone_data.data_conclusao is not None:
            updates.append("data_conclusao = :data_conclusao")
            params["data_conclusao"] = milestone_data.data_conclusao

        if milestone_data.notificacao_whatsapp is not None:
            updates.append("notificacao_whatsapp = :notificacao_whatsapp")
            params["notificacao_whatsapp"] = milestone_data.notificacao_whatsapp

        if milestone_data.notificacao_email is not None:
            updates.append("notificacao_email = :notificacao_email")
            params["notificacao_email"] = milestone_data.notificacao_email

        if not updates:
            # Nada para atualizar
            return await self.get_milestone(milestone_id)

        query = text(f"""
            UPDATE project_milestones
            SET {', '.join(updates)}
            WHERE id = :milestone_id
            RETURNING *
        """)

        result = self.db.execute(query, params).fetchone()
        self.db.commit()

        if not result:
            return None

        return self._row_to_milestone(result)

    async def delete_milestone(self, milestone_id: UUID) -> bool:
        """Deleta um marco (e seus lembretes em cascata)"""
        query = text("""
            DELETE FROM project_milestones
            WHERE id = :milestone_id
        """)

        result = self.db.execute(query, {"milestone_id": str(milestone_id)})
        self.db.commit()

        return result.rowcount > 0

    async def get_milestone_reminders(self, milestone_id: UUID) -> List[ScheduledReminder]:
        """Lista todos os lembretes de um marco"""
        query = text("""
            SELECT * FROM scheduled_reminders
            WHERE milestone_id = :milestone_id
            ORDER BY data_envio ASC
        """)

        results = self.db.execute(query, {"milestone_id": str(milestone_id)}).fetchall()

        return [self._row_to_reminder(row) for row in results]

    async def get_pending_reminders(self, target_date: date) -> List[tuple[ScheduledReminder, Milestone]]:
        """
        Busca lembretes pendentes para uma data específica

        Retorna tuplas de (reminder, milestone) para facilitar envio
        """
        query = text("""
            SELECT
                sr.*,
                pm.id as milestone_id,
                pm.project_id,
                pm.nome as milestone_nome,
                pm.descricao as milestone_descricao,
                pm.data_limite,
                pm.status
            FROM scheduled_reminders sr
            JOIN project_milestones pm ON sr.milestone_id = pm.id
            WHERE sr.data_envio = :target_date
              AND sr.enviado = false
              AND pm.status NOT IN ('concluido', 'cancelado')
            ORDER BY pm.data_limite ASC
        """)

        results = self.db.execute(query, {"target_date": target_date}).fetchall()

        reminders_with_milestones = []
        for row in results:
            reminder = ScheduledReminder(
                id=row.id,
                milestone_id=row.milestone_id,
                tipo=ReminderType(row.tipo),
                data_envio=row.data_envio,
                enviado=row.enviado,
                enviado_em=row.enviado_em,
                erro_envio=row.erro_envio,
                metodo=row.metodo,
                created_at=row.created_at
            )

            milestone = Milestone(
                id=row.milestone_id,
                project_id=row.project_id,
                nome=row.milestone_nome,
                descricao=row.milestone_descricao,
                ordem=0,  # Não usado neste contexto
                data_limite=row.data_limite,
                data_conclusao=None,
                status=MilestoneStatus(row.status),
                notificacao_whatsapp=True,
                notificacao_email=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            reminders_with_milestones.append((reminder, milestone))

        return reminders_with_milestones

    async def mark_reminder_sent(
        self,
        reminder_id: UUID,
        success: bool,
        error_message: Optional[str] = None
    ) -> bool:
        """Marca um lembrete como enviado (ou com erro)"""
        if success:
            query = text("""
                UPDATE scheduled_reminders
                SET enviado = true, enviado_em = NOW()
                WHERE id = :reminder_id
            """)
            params = {"reminder_id": str(reminder_id)}
        else:
            query = text("""
                UPDATE scheduled_reminders
                SET erro_envio = :erro_envio
                WHERE id = :reminder_id
            """)
            params = {"reminder_id": str(reminder_id), "erro_envio": error_message}

        result = self.db.execute(query, params)
        self.db.commit()

        return result.rowcount > 0

    async def mark_overdue_milestones(self) -> int:
        """
        Marca marcos como atrasados (chama função do banco)

        Retorna número de marcos atualizados
        """
        query = text("SELECT mark_overdue_milestones()")
        self.db.execute(query)
        self.db.commit()

        # Contar quantos foram atualizados
        count_query = text("""
            SELECT COUNT(*) FROM project_milestones
            WHERE status = 'atrasado'
              AND data_limite < CURRENT_DATE
              AND data_conclusao IS NULL
        """)
        result = self.db.execute(count_query).fetchone()

        return result[0] if result else 0

    def _row_to_milestone(self, row) -> Milestone:
        """Converte row do banco para modelo Milestone"""
        milestone = Milestone(
            id=row.id,
            project_id=row.project_id,
            nome=row.nome,
            descricao=row.descricao,
            ordem=row.ordem,
            data_limite=row.data_limite,
            data_conclusao=row.data_conclusao,
            status=MilestoneStatus(row.status),
            notificacao_whatsapp=row.notificacao_whatsapp,
            notificacao_email=row.notificacao_email,
            created_at=row.created_at,
            updated_at=row.updated_at
        )

        # Calcular dias até limite
        hoje = date.today()
        if row.data_limite:
            dias = (row.data_limite - hoje).days
            milestone.dias_ate_limite = dias
            milestone.atrasado = dias < 0 and row.status != MilestoneStatus.CONCLUIDO

        return milestone

    def _row_to_reminder(self, row) -> ScheduledReminder:
        """Converte row do banco para modelo ScheduledReminder"""
        return ScheduledReminder(
            id=row.id,
            milestone_id=row.milestone_id,
            tipo=ReminderType(row.tipo),
            data_envio=row.data_envio,
            enviado=row.enviado,
            enviado_em=row.enviado_em,
            erro_envio=row.erro_envio,
            metodo=row.metodo,
            created_at=row.created_at
        )
