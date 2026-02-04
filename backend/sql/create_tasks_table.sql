-- Tabela de Tarefas (Centro de Trabalho)
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'hoje' CHECK (status IN ('hoje', 'esta_semana', 'depois', 'feito')),
    prioridade TEXT NOT NULL DEFAULT 'media' CHECK (prioridade IN ('alta', 'media', 'baixa')),
    prazo DATE,
    lead_id TEXT,
    lead_nome TEXT,
    project_id TEXT,
    project_nome TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_prioridade ON tasks(prioridade);
CREATE INDEX IF NOT EXISTS idx_tasks_lead_id ON tasks(lead_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_prazo ON tasks(prazo);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
