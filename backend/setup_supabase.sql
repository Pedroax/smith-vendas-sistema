-- ============================================
-- SMITH 2.0 - SETUP COMPLETO DO SUPABASE
-- ============================================
-- Execute este SQL no SQL Editor do Supabase
-- para criar todas as tabelas necessárias
-- ============================================

-- ============================================
-- 1. TABELA DE LEADS (CRM Principal)
-- ============================================
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telefone VARCHAR(20) NOT NULL UNIQUE,
    empresa VARCHAR(255),
    cargo VARCHAR(100),
    faturamento_anual DECIMAL(15, 2),

    -- Status e temperatura
    status VARCHAR(50) NOT NULL DEFAULT 'novo',
    temperatura VARCHAR(20),
    origem VARCHAR(50) DEFAULT 'outro',

    -- Qualificação
    lead_score INTEGER DEFAULT 0,
    qualificacao_detalhes JSONB,

    -- Agendamento
    meeting_scheduled_at TIMESTAMPTZ,
    meeting_google_event_id VARCHAR(255),

    -- Metadados
    observacoes TEXT,
    tags TEXT[],

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para leads
CREATE INDEX IF NOT EXISTS idx_leads_telefone ON leads(telefone);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_temperatura ON leads(temperatura);
CREATE INDEX IF NOT EXISTS idx_leads_origem ON leads(origem);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

-- ============================================
-- 2. TABELA DE PROJETOS
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',

    -- Metadados
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ============================================
-- 3. TABELA DE CONVERSAS (Sistema Conversacional)
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    phone_number VARCHAR(20) NOT NULL,

    -- Estado da conversa
    state VARCHAR(50) NOT NULL DEFAULT 'inicial',

    -- Contexto
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    agendamento_message_sent TIMESTAMPTZ,
    selected_slot_index INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para conversations
CREATE INDEX IF NOT EXISTS idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversations_state ON conversations(state);

-- ============================================
-- 4. TABELA DE MENSAGENS (Histórico Completo)
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,

    -- Conteúdo
    direction VARCHAR(20) NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    content TEXT NOT NULL,

    -- Metadados Evolution API
    evolution_message_id VARCHAR(100) UNIQUE,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_evolution_id ON messages(evolution_message_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- ============================================
-- 5. TRIGGERS PARA ATUALIZAR updated_at
-- ============================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para leads
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para projects
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para conversations
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. POLÍTICAS RLS (Row Level Security)
-- ============================================
-- IMPORTANTE: Por padrão, desabilitado para simplificar
-- Habilite se precisar de segurança avançada

-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 7. VIEWS ÚTEIS (Opcional)
-- ============================================

-- View de leads qualificados
CREATE OR REPLACE VIEW leads_qualificados AS
SELECT
    l.*,
    c.state as conversation_state,
    c.last_message_at,
    COUNT(m.id) as total_messages
FROM leads l
LEFT JOIN conversations c ON l.id = c.lead_id
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE l.status IN ('qualificado', 'agendamento_marcado')
GROUP BY l.id, c.id, c.state, c.last_message_at;

-- View de conversas ativas
CREATE OR REPLACE VIEW conversas_ativas AS
SELECT
    c.*,
    l.nome,
    l.empresa,
    l.lead_score,
    COUNT(m.id) as total_messages,
    MAX(m.created_at) as ultima_mensagem
FROM conversations c
JOIN leads l ON c.lead_id = l.id
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE c.state IN ('agendamento_enviado', 'tirando_duvidas', 'aguardando_confirmacao')
GROUP BY c.id, l.nome, l.empresa, l.lead_score;

-- ============================================
-- 8. DADOS DE EXEMPLO (Opcional - Comentado)
-- ============================================
/*
-- Inserir lead de teste
INSERT INTO leads (nome, email, telefone, empresa, cargo, faturamento_anual, status, origem, lead_score)
VALUES
('João Silva', 'joao@empresa.com.br', '11999999999', 'Empresa Teste', 'CEO', 1000000.00, 'qualificado', 'facebook_ads', 85);

-- Inserir projeto de teste
INSERT INTO projects (name, description, status)
VALUES
('Smith CRM', 'Sistema de gestão de leads', 'active');
*/

-- ============================================
-- ✅ SETUP COMPLETO!
-- ============================================
-- Tabelas criadas:
-- ✓ leads - CRM completo
-- ✓ projects - Gestão de projetos
-- ✓ conversations - Sistema conversacional
-- ✓ messages - Histórico de mensagens
--
-- Triggers configurados:
-- ✓ updated_at automático
--
-- Views criadas:
-- ✓ leads_qualificados
-- ✓ conversas_ativas
-- ============================================

SELECT 'Setup completo! Todas as tabelas foram criadas.' as status;
