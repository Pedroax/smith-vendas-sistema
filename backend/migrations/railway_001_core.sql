-- ============================================================
-- SMITH 2.0 - SCHEMA MÍNIMO PARA RAILWAY POSTGRES
-- ============================================================
-- Este script recria APENAS as tabelas essenciais pro agente
-- Smith (WhatsApp) voltar a funcionar: leads + histórico de
-- conversas. Foi montado lendo o código real (repository/*.py,
-- models/lead.py) em vez de confiar nos .sql antigos do repo,
-- que estavam desatualizados/contraditórios entre si (alguns
-- tratavam leads.id como UUID, outros como SERIAL — o código
-- real usa SERIAL).
--
-- NÃO inclui ainda: portal do cliente, invoices, projetos
-- (kanban), tasks, notifications, interactions, appointments,
-- sm_usuarios, sm_lp_submissions. Essas são features do painel
-- administrativo e ficam pra uma segunda etapa.
-- ============================================================

-- ============================================================
-- TABELA: leads
-- ============================================================
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telefone VARCHAR(50) NOT NULL UNIQUE,
    empresa VARCHAR(255),
    cargo VARCHAR(100),
    faturamento_anual DECIMAL(15, 2),

    -- Status e temperatura (VARCHAR, não ENUM nativo — o Python
    -- já valida via Pydantic e os valores mudam com frequência)
    status VARCHAR(50) NOT NULL DEFAULT 'novo',
    origem VARCHAR(50) NOT NULL DEFAULT 'outro',
    temperatura VARCHAR(20),

    -- Qualificação (JSONB)
    lead_score INTEGER DEFAULT 0,
    qualificacao_detalhes JSONB DEFAULT '{}'::jsonb,

    -- ROI
    roi_analysis JSONB DEFAULT '{}'::jsonb,

    -- Agendamento
    meeting_scheduled_at TIMESTAMPTZ,
    meeting_google_event_id VARCHAR(255),
    temp_meeting_slot JSONB,

    -- Follow-up
    followup_config JSONB DEFAULT '{"tentativas_realizadas": 0, "intervalo_horas": [24, 72, 168]}'::jsonb,

    -- Histórico e interações
    ultima_interacao TIMESTAMPTZ,

    -- Notas e observações
    observacoes TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    lost_at TIMESTAMPTZ,
    won_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_leads_telefone ON leads(telefone);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_temperatura ON leads(temperatura);
CREATE INDEX IF NOT EXISTS idx_leads_origem ON leads(origem);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_lead_score ON leads(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_tags ON leads USING GIN(tags);

-- ============================================================
-- TABELA: conversation_messages
-- ============================================================
-- id é gerado no Python (uuid4), não pelo banco.
-- lead_id é INTEGER (não UUID!) porque leads.id é SERIAL.
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_messages_lead_id ON conversation_messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_conv_messages_timestamp ON conversation_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conv_messages_lead_timestamp ON conversation_messages(lead_id, timestamp DESC);

-- ============================================================
-- TRIGGER: updated_at automático em leads
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Confirmação
-- ============================================================
SELECT 'Schema mínimo (leads + conversation_messages) criado com sucesso!' AS status;
