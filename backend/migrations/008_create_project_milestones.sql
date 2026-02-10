-- Migration 008: Sistema de Marcos e Lembretes de Projetos
-- Cria tabelas para gerenciar etapas de projetos e lembretes automáticos

-- Tabela de marcos/etapas dos projetos
CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Informações da etapa
    nome TEXT NOT NULL,
    descricao TEXT,
    ordem INTEGER NOT NULL DEFAULT 0,

    -- Prazo
    data_limite DATE NOT NULL,
    data_conclusao DATE,

    -- Status
    status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN (
        'pendente',     -- Não iniciado
        'em_progresso', -- Em andamento
        'concluido',    -- Finalizado
        'atrasado',     -- Passou do prazo
        'cancelado'     -- Cancelado
    )),

    -- Configurações de notificação
    notificacao_whatsapp BOOLEAN DEFAULT true,
    notificacao_email BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Tabela de lembretes agendados
CREATE TABLE IF NOT EXISTS scheduled_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    milestone_id UUID NOT NULL REFERENCES project_milestones(id) ON DELETE CASCADE,

    -- Tipo de lembrete
    tipo TEXT NOT NULL CHECK (tipo IN (
        '10_dias',  -- 10 dias antes
        '7_dias',   -- 7 dias antes
        '3_dias',   -- 3 dias antes
        '1_dia',    -- 1 dia antes
        'no_dia',   -- No dia do prazo
        'atrasado'  -- Passou do prazo
    )),

    -- Agendamento
    data_envio DATE NOT NULL,

    -- Controle de envio
    enviado BOOLEAN DEFAULT false,
    enviado_em TIMESTAMP WITH TIME ZONE,
    erro_envio TEXT,

    -- Método
    metodo TEXT NOT NULL DEFAULT 'whatsapp' CHECK (metodo IN ('whatsapp', 'email')),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_milestones_project ON project_milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON project_milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_data_limite ON project_milestones(data_limite);

CREATE INDEX IF NOT EXISTS idx_reminders_milestone ON scheduled_reminders(milestone_id);
CREATE INDEX IF NOT EXISTS idx_reminders_data_envio ON scheduled_reminders(data_envio);
CREATE INDEX IF NOT EXISTS idx_reminders_enviado ON scheduled_reminders(enviado);
CREATE INDEX IF NOT EXISTS idx_reminders_pendentes ON scheduled_reminders(enviado, data_envio);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_milestone_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_milestone_updated_at
    BEFORE UPDATE ON project_milestones
    FOR EACH ROW
    EXECUTE FUNCTION update_milestone_updated_at();

-- Trigger para marcar etapas como atrasadas automaticamente
CREATE OR REPLACE FUNCTION mark_overdue_milestones()
RETURNS void AS $$
BEGIN
    UPDATE project_milestones
    SET status = 'atrasado'
    WHERE status = 'pendente'
      AND data_limite < CURRENT_DATE
      AND data_conclusao IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Função para criar lembretes automaticamente ao criar/atualizar marco
CREATE OR REPLACE FUNCTION create_milestone_reminders()
RETURNS TRIGGER AS $$
DECLARE
    reminder_dates DATE[];
    reminder_type TEXT;
    reminder_date DATE;
BEGIN
    -- Apenas criar lembretes se notificação estiver habilitada
    IF NEW.notificacao_whatsapp = false AND NEW.notificacao_email = false THEN
        RETURN NEW;
    END IF;

    -- Se está atualizando e já foi concluído, não criar novos lembretes
    IF TG_OP = 'UPDATE' AND NEW.status IN ('concluido', 'cancelado') THEN
        RETURN NEW;
    END IF;

    -- Deletar lembretes antigos (se estiver atualizando)
    IF TG_OP = 'UPDATE' THEN
        DELETE FROM scheduled_reminders
        WHERE milestone_id = NEW.id
          AND enviado = false;
    END IF;

    -- Criar lembretes para diferentes períodos
    -- 10 dias antes
    IF NEW.data_limite - INTERVAL '10 days' >= CURRENT_DATE THEN
        INSERT INTO scheduled_reminders (milestone_id, tipo, data_envio, metodo)
        VALUES (
            NEW.id,
            '10_dias',
            (NEW.data_limite - INTERVAL '10 days')::DATE,
            CASE WHEN NEW.notificacao_whatsapp THEN 'whatsapp' ELSE 'email' END
        );
    END IF;

    -- 7 dias antes
    IF NEW.data_limite - INTERVAL '7 days' >= CURRENT_DATE THEN
        INSERT INTO scheduled_reminders (milestone_id, tipo, data_envio, metodo)
        VALUES (
            NEW.id,
            '7_dias',
            (NEW.data_limite - INTERVAL '7 days')::DATE,
            CASE WHEN NEW.notificacao_whatsapp THEN 'whatsapp' ELSE 'email' END
        );
    END IF;

    -- 3 dias antes
    IF NEW.data_limite - INTERVAL '3 days' >= CURRENT_DATE THEN
        INSERT INTO scheduled_reminders (milestone_id, tipo, data_envio, metodo)
        VALUES (
            NEW.id,
            '3_dias',
            (NEW.data_limite - INTERVAL '3 days')::DATE,
            CASE WHEN NEW.notificacao_whatsapp THEN 'whatsapp' ELSE 'email' END
        );
    END IF;

    -- 1 dia antes
    IF NEW.data_limite - INTERVAL '1 day' >= CURRENT_DATE THEN
        INSERT INTO scheduled_reminders (milestone_id, tipo, data_envio, metodo)
        VALUES (
            NEW.id,
            '1_dia',
            (NEW.data_limite - INTERVAL '1 day')::DATE,
            CASE WHEN NEW.notificacao_whatsapp THEN 'whatsapp' ELSE 'email' END
        );
    END IF;

    -- No dia
    IF NEW.data_limite >= CURRENT_DATE THEN
        INSERT INTO scheduled_reminders (milestone_id, tipo, data_envio, metodo)
        VALUES (
            NEW.id,
            'no_dia',
            NEW.data_limite,
            CASE WHEN NEW.notificacao_whatsapp THEN 'whatsapp' ELSE 'email' END
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_milestone_reminders
    AFTER INSERT OR UPDATE OF data_limite, notificacao_whatsapp, notificacao_email
    ON project_milestones
    FOR EACH ROW
    EXECUTE FUNCTION create_milestone_reminders();

-- Comentários nas tabelas
COMMENT ON TABLE project_milestones IS 'Etapas/marcos dos projetos com prazos e status';
COMMENT ON TABLE scheduled_reminders IS 'Lembretes agendados para notificar sobre prazos';

COMMENT ON COLUMN project_milestones.ordem IS 'Ordem de execução da etapa no projeto';
COMMENT ON COLUMN project_milestones.data_limite IS 'Data limite para conclusão da etapa';
COMMENT ON COLUMN project_milestones.data_conclusao IS 'Data em que foi concluída';

COMMENT ON COLUMN scheduled_reminders.tipo IS 'Quando enviar: 10_dias, 7_dias, 3_dias, 1_dia, no_dia, atrasado';
COMMENT ON COLUMN scheduled_reminders.data_envio IS 'Data agendada para envio do lembrete';
COMMENT ON COLUMN scheduled_reminders.enviado IS 'Se já foi enviado';
