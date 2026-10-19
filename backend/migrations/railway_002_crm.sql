-- ============================================================
-- SMITH 2.0 - RAILWAY POSTGRES: CRM, PORTAL, FINANCEIRO
-- ============================================================
-- Complementa railway_001_core.sql. Montado a partir dos
-- repositories e models (não dos .sql antigos do Supabase):
-- - sem políticas RLS (usavam auth.role(), exclusivo do Supabase)
-- - sem CHECK em colunas de enum (o Pydantic já valida)
-- - ids gerados com gen_random_uuid() (nativo desde o PG13)
-- Aplicado automaticamente no startup por app/database.py.
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- LEADS: colunas que a API escreve e não estavam no schema core
-- ============================================================
ALTER TABLE leads ADD COLUMN IF NOT EXISTS valor_estimado DECIMAL(15, 2) DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_summary TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ultima_mensagem_ia TEXT;

-- conversation_memory.add_message insere sem id
ALTER TABLE conversation_messages ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Estatísticas usadas por GET /api/leads/stats/summary
CREATE OR REPLACE FUNCTION get_leads_stats()
RETURNS JSON AS $$
    SELECT json_build_object(
        'total_leads', COUNT(*),
        'por_status', COALESCE((
            SELECT json_object_agg(status, total)
            FROM (SELECT status, COUNT(*) AS total FROM leads GROUP BY status) s
        ), '{}'::json),
        'por_origem', COALESCE((
            SELECT json_object_agg(origem, total)
            FROM (SELECT origem, COUNT(*) AS total FROM leads GROUP BY origem) o
        ), '{}'::json),
        'por_temperatura', COALESCE((
            SELECT json_object_agg(temperatura, total)
            FROM (
                SELECT temperatura, COUNT(*) AS total FROM leads
                WHERE temperatura IS NOT NULL GROUP BY temperatura
            ) t
        ), '{}'::json),
        'score_medio', COALESCE(ROUND(AVG(lead_score), 2), 0),
        'valor_total_pipeline', COALESCE(SUM(valor_estimado), 0),
        'taxa_qualificacao', COALESCE(ROUND(
            COUNT(*) FILTER (WHERE status IN ('qualificado', 'agendamento_marcado', 'ganho'))::NUMERIC
            / NULLIF(COUNT(*), 0) * 100, 2), 0),
        'taxa_conversao', COALESCE(ROUND(
            COUNT(*) FILTER (WHERE status = 'ganho')::NUMERIC
            / NULLIF(COUNT(*), 0) * 100, 2), 0)
    )
    FROM leads;
$$ LANGUAGE sql STABLE;

-- ============================================================
-- USUÁRIOS DO SISTEMA INTERNO (login admin/marketing)
-- ============================================================
CREATE TABLE IF NOT EXISTS sm_usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'marketing',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SUBMISSÕES DO FORMULÁRIO DA LANDING PAGE
-- ============================================================
CREATE TABLE IF NOT EXISTS sm_lp_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT,
    empresa TEXT,
    segmento TEXT,
    cargo TEXT,
    telefone TEXT,
    faturamento_mensal DECIMAL(15, 2),
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_term TEXT,
    utm_content TEXT,
    qualificado BOOLEAN,
    lead_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lp_submissions_created_at ON sm_lp_submissions(created_at DESC);

-- ============================================================
-- NOTIFICAÇÕES
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,  -- NULL = notificação global
    tipo TEXT NOT NULL,
    prioridade TEXT NOT NULL DEFAULT 'medium',
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    link TEXT,
    lida BOOLEAN NOT NULL DEFAULT FALSE,
    lead_id TEXT,
    lead_nome TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, lida, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_lead_id ON notifications(lead_id);

-- ============================================================
-- TAREFAS
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'hoje',
    prioridade TEXT NOT NULL DEFAULT 'media',
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
CREATE INDEX IF NOT EXISTS idx_tasks_lead_id ON tasks(lead_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);

-- ============================================================
-- INTERAÇÕES (notas, ligações, reuniões com leads)
-- ============================================================
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id TEXT NOT NULL,
    lead_nome TEXT,
    tipo TEXT NOT NULL,
    assunto TEXT,
    conteudo TEXT NOT NULL,
    user_id TEXT,
    user_nome TEXT NOT NULL DEFAULT 'Sistema',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON interactions(lead_id, created_at DESC);

-- ============================================================
-- AGENDAMENTOS (agenda do CRM)
-- ============================================================
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id TEXT NOT NULL,
    lead_nome TEXT,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT,
    data_hora TIMESTAMPTZ NOT NULL,
    duracao_minutos INTEGER NOT NULL DEFAULT 60,
    status TEXT NOT NULL DEFAULT 'agendado',
    user_nome TEXT NOT NULL DEFAULT 'Sistema',
    location TEXT,
    meeting_url TEXT,
    observacoes TEXT,
    lembrete_enviado BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_appointments_data_hora ON appointments(data_hora, status);
CREATE INDEX IF NOT EXISTS idx_appointments_lead_id ON appointments(lead_id);

-- ============================================================
-- REUNIÕES MARCADAS PELO AGENTE (webhook /webhook/whatsapp)
-- ============================================================
CREATE TABLE IF NOT EXISTS agendamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    data_hora TIMESTAMPTZ NOT NULL,
    duracao_minutos INTEGER NOT NULL DEFAULT 30,
    google_event_id TEXT,
    google_meet_link TEXT,
    google_event_link TEXT,
    status TEXT NOT NULL DEFAULT 'agendado',
    confirmado_em TIMESTAMPTZ,
    confirmado_via TEXT,
    lembrete_24h_enviado BOOLEAN NOT NULL DEFAULT FALSE,
    lembrete_3h_enviado BOOLEAN NOT NULL DEFAULT FALSE,
    lembrete_30min_enviado BOOLEAN NOT NULL DEFAULT FALSE,
    observacoes TEXT,
    motivo_cancelamento TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agendamentos_lead_id ON agendamentos(lead_id);
CREATE INDEX IF NOT EXISTS idx_agendamentos_data_hora ON agendamentos(data_hora, status);

-- ============================================================
-- PROJETOS (pipeline kanban de implementações)
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    cliente_id TEXT,  -- id do lead (opcional)
    cliente_nome VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'backlog',
    prioridade VARCHAR(30) NOT NULL DEFAULT 'media',
    prazo TIMESTAMPTZ,
    valor DECIMAL(12, 2),
    responsavel VARCHAR(255),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    notas TEXT,
    progresso_percentual INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- PORTAL DO CLIENTE
-- ============================================================
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    empresa VARCHAR(100),
    documento VARCHAR(20),
    avatar_url TEXT,
    senha_hash VARCHAR(255) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_acesso TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS client_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'briefing',
    etapa_atual INTEGER NOT NULL DEFAULT 0,
    progresso INTEGER NOT NULL DEFAULT 0,
    valor_total DECIMAL(12, 2) NOT NULL DEFAULT 0,
    data_inicio TIMESTAMPTZ,
    data_previsao TIMESTAMPTZ,
    concluido_em TIMESTAMPTZ,
    access_token VARCHAR(32) UNIQUE NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_client_projects_client ON client_projects(client_id);

CREATE TABLE IF NOT EXISTS project_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ordem INTEGER NOT NULL,
    cor VARCHAR(10) NOT NULL DEFAULT '#6366f1',
    concluida BOOLEAN NOT NULL DEFAULT FALSE,
    data_inicio TIMESTAMPTZ,
    data_conclusao TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_stages_project ON project_stages(project_id, ordem);

CREATE TABLE IF NOT EXISTS delivery_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE SET NULL,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    obrigatorio BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    arquivo_url TEXT,
    arquivo_nome VARCHAR(255),
    comentario_cliente TEXT,
    enviado_em TIMESTAMPTZ,
    aprovado_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_delivery_items_project ON delivery_items(project_id);

CREATE TABLE IF NOT EXISTS approval_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'arquivo',
    status VARCHAR(30) NOT NULL DEFAULT 'aguardando',
    arquivo_url TEXT,
    link_externo TEXT,
    feedback_cliente TEXT,
    versao INTEGER NOT NULL DEFAULT 1,
    enviado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    respondido_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approval_items_project ON approval_items(project_id);

CREATE TABLE IF NOT EXISTS project_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    user_id UUID,
    is_client_action BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_timeline_project ON project_timeline(project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS project_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE SET NULL,
    approval_id UUID REFERENCES approval_items(id) ON DELETE SET NULL,
    user_id UUID,
    user_nome VARCHAR(100) NOT NULL DEFAULT 'Sistema',
    is_client BOOLEAN NOT NULL DEFAULT FALSE,
    conteudo TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_comments_project ON project_comments(project_id);

CREATE TABLE IF NOT EXISTS project_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    descricao VARCHAR(200) NOT NULL,
    valor DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    data_vencimento TIMESTAMPTZ NOT NULL,
    data_pagamento TIMESTAMPTZ,
    comprovante_url TEXT,
    parcela INTEGER NOT NULL DEFAULT 1,
    total_parcelas INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_payments_project ON project_payments(project_id);

CREATE TABLE IF NOT EXISTS project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'outro',
    descricao TEXT,
    arquivo_url TEXT NOT NULL,
    arquivo_nome VARCHAR(255) NOT NULL,
    arquivo_tamanho INTEGER,
    uploaded_by VARCHAR(50) DEFAULT 'admin',
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_documents_project ON project_documents(project_id);

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_client_projects_updated_at ON client_projects;
CREATE TRIGGER update_client_projects_updated_at
    BEFORE UPDATE ON client_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Recalcula progresso do projeto quando uma etapa é concluída
CREATE OR REPLACE FUNCTION calculate_project_progress()
RETURNS TRIGGER AS $$
DECLARE
    total_stages INTEGER;
    completed_stages INTEGER;
BEGIN
    SELECT COUNT(*), COUNT(*) FILTER (WHERE concluida)
    INTO total_stages, completed_stages
    FROM project_stages
    WHERE project_id = NEW.project_id;

    UPDATE client_projects
    SET progresso = CASE WHEN total_stages > 0 THEN (completed_stages * 100) / total_stages ELSE 0 END,
        etapa_atual = completed_stages
    WHERE id = NEW.project_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_project_progress ON project_stages;
CREATE TRIGGER update_project_progress
    AFTER UPDATE OF concluida ON project_stages
    FOR EACH ROW EXECUTE FUNCTION calculate_project_progress();

-- ============================================================
-- FATURAS
-- ============================================================
-- project_id é INTEGER porque é o que o model/frontend usam hoje
-- (sem FK: ainda não existe tabela de projetos com id inteiro).
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER,
    numero_fatura TEXT UNIQUE NOT NULL,
    descricao TEXT NOT NULL,
    valor DECIMAL(12, 2) NOT NULL,
    desconto DECIMAL(12, 2) NOT NULL DEFAULT 0,
    valor_final DECIMAL(12, 2) NOT NULL,
    data_emissao DATE NOT NULL DEFAULT CURRENT_DATE,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status TEXT NOT NULL DEFAULT 'pendente',
    nota_fiscal_url TEXT,
    comprovante_url TEXT,
    comprovante_enviado_em TIMESTAMPTZ,
    confirmado_por TEXT,
    confirmado_em TIMESTAMPTZ,
    notas_admin TEXT,
    metodo_pagamento TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_project ON invoices(project_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status, data_vencimento);

DROP TRIGGER IF EXISTS update_invoices_updated_at ON invoices;
CREATE TRIGGER update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Fatura pendente com vencimento passado vira 'atrasado'
CREATE OR REPLACE FUNCTION check_invoice_overdue()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'pendente' AND NEW.data_vencimento < CURRENT_DATE THEN
        NEW.status = 'atrasado';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_check_invoice_overdue ON invoices;
CREATE TRIGGER trigger_check_invoice_overdue
    BEFORE INSERT OR UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION check_invoice_overdue();

-- ============================================================
-- MARCOS DE PROJETO E LEMBRETES
-- ============================================================
CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    descricao TEXT,
    ordem INTEGER NOT NULL DEFAULT 0,
    data_limite DATE NOT NULL,
    data_conclusao DATE,
    status TEXT NOT NULL DEFAULT 'pendente',
    notificacao_whatsapp BOOLEAN NOT NULL DEFAULT TRUE,
    notificacao_email BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scheduled_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    milestone_id UUID NOT NULL REFERENCES project_milestones(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,
    data_envio DATE NOT NULL,
    enviado BOOLEAN NOT NULL DEFAULT FALSE,
    enviado_em TIMESTAMPTZ,
    erro_envio TEXT,
    metodo TEXT NOT NULL DEFAULT 'whatsapp',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestones_project ON project_milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_reminders_pendentes ON scheduled_reminders(enviado, data_envio);

DROP TRIGGER IF EXISTS update_milestones_updated_at ON project_milestones;
CREATE TRIGGER update_milestones_updated_at
    BEFORE UPDATE ON project_milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION mark_overdue_milestones()
RETURNS void AS $$
    UPDATE project_milestones
    SET status = 'atrasado'
    WHERE status = 'pendente'
      AND data_limite < CURRENT_DATE
      AND data_conclusao IS NULL;
$$ LANGUAGE sql;

-- Cria os lembretes (10, 7, 3, 1 dia antes e no dia) ao criar/alterar um marco
CREATE OR REPLACE FUNCTION create_milestone_reminders()
RETURNS TRIGGER AS $$
DECLARE
    metodo_envio TEXT;
    antecedencia RECORD;
BEGIN
    IF NOT NEW.notificacao_whatsapp AND NOT NEW.notificacao_email THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' AND NEW.status IN ('concluido', 'cancelado') THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        DELETE FROM scheduled_reminders WHERE milestone_id = NEW.id AND enviado = FALSE;
    END IF;

    metodo_envio := CASE WHEN NEW.notificacao_whatsapp THEN 'whatsapp' ELSE 'email' END;

    FOR antecedencia IN
        SELECT * FROM (VALUES ('10_dias', 10), ('7_dias', 7), ('3_dias', 3), ('1_dia', 1), ('no_dia', 0)) AS t(tipo, dias)
    LOOP
        IF NEW.data_limite - antecedencia.dias >= CURRENT_DATE THEN
            INSERT INTO scheduled_reminders (milestone_id, tipo, data_envio, metodo)
            VALUES (NEW.id, antecedencia.tipo, NEW.data_limite - antecedencia.dias, metodo_envio);
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_create_milestone_reminders ON project_milestones;
CREATE TRIGGER trigger_create_milestone_reminders
    AFTER INSERT OR UPDATE OF data_limite, notificacao_whatsapp, notificacao_email
    ON project_milestones
    FOR EACH ROW EXECUTE FUNCTION create_milestone_reminders();
