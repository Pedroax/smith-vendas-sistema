-- ============================================
-- MIGRAÇÃO: Portal do Cliente
-- Sistema de acompanhamento de projetos
-- ============================================

-- ============================================
-- TABELA: clients (Clientes do portal)
-- ============================================
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    empresa VARCHAR(100),
    documento VARCHAR(20), -- CPF ou CNPJ
    avatar_url TEXT,
    senha_hash VARCHAR(255) NOT NULL,
    ativo BOOLEAN DEFAULT true,
    ultimo_acesso TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_ativo ON clients(ativo);

-- ============================================
-- TABELA: client_projects (Projetos do cliente)
-- ============================================
CREATE TABLE IF NOT EXISTS client_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL, -- site, identidade_visual, video, sistema, etc
    status VARCHAR(30) DEFAULT 'briefing',
    etapa_atual INTEGER DEFAULT 0,
    progresso INTEGER DEFAULT 0, -- 0-100
    valor_total DECIMAL(12, 2) DEFAULT 0,
    data_inicio TIMESTAMP WITH TIME ZONE,
    data_previsao TIMESTAMP WITH TIME ZONE,
    concluido_em TIMESTAMP WITH TIME ZONE,
    access_token VARCHAR(20) UNIQUE NOT NULL, -- Link único para acesso direto
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_client_projects_client ON client_projects(client_id);
CREATE INDEX idx_client_projects_status ON client_projects(status);
CREATE INDEX idx_client_projects_token ON client_projects(access_token);

-- ============================================
-- TABELA: project_stages (Etapas do projeto)
-- ============================================
CREATE TABLE IF NOT EXISTS project_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ordem INTEGER NOT NULL,
    cor VARCHAR(10) DEFAULT '#6366f1',
    concluida BOOLEAN DEFAULT false,
    data_inicio TIMESTAMP WITH TIME ZONE,
    data_conclusao TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_project_stages_project ON project_stages(project_id);
CREATE INDEX idx_project_stages_ordem ON project_stages(ordem);

-- ============================================
-- TABELA: delivery_items (O que o cliente precisa entregar)
-- ============================================
CREATE TABLE IF NOT EXISTS delivery_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE SET NULL,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    obrigatorio BOOLEAN DEFAULT true,
    status VARCHAR(20) DEFAULT 'pendente', -- pendente, enviado, aprovado, rejeitado
    arquivo_url TEXT,
    arquivo_nome VARCHAR(255),
    comentario_cliente TEXT,
    enviado_em TIMESTAMP WITH TIME ZONE,
    aprovado_em TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_delivery_items_project ON delivery_items(project_id);
CREATE INDEX idx_delivery_items_status ON delivery_items(status);

-- ============================================
-- TABELA: approval_items (Entregas para aprovação do cliente)
-- ============================================
CREATE TABLE IF NOT EXISTS approval_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(20) DEFAULT 'arquivo', -- arquivo, link, texto
    status VARCHAR(30) DEFAULT 'aguardando', -- aguardando, aprovado, ajustes_solicitados
    arquivo_url TEXT,
    link_externo TEXT,
    feedback_cliente TEXT,
    versao INTEGER DEFAULT 1,
    enviado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    respondido_em TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_approval_items_project ON approval_items(project_id);
CREATE INDEX idx_approval_items_status ON approval_items(status);

-- ============================================
-- TABELA: project_timeline (Linha do tempo)
-- ============================================
CREATE TABLE IF NOT EXISTS project_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    user_id UUID, -- Quem fez a ação
    is_client_action BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_project_timeline_project ON project_timeline(project_id);
CREATE INDEX idx_project_timeline_created ON project_timeline(created_at DESC);

-- ============================================
-- TABELA: project_comments (Comentários)
-- ============================================
CREATE TABLE IF NOT EXISTS project_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE SET NULL,
    approval_id UUID REFERENCES approval_items(id) ON DELETE SET NULL,
    user_id UUID,
    user_nome VARCHAR(100) DEFAULT 'Sistema',
    is_client BOOLEAN DEFAULT false,
    conteudo TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_project_comments_project ON project_comments(project_id);
CREATE INDEX idx_project_comments_approval ON project_comments(approval_id);

-- ============================================
-- TABELA: project_payments (Pagamentos)
-- ============================================
CREATE TABLE IF NOT EXISTS project_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES client_projects(id) ON DELETE CASCADE,
    descricao VARCHAR(200) NOT NULL,
    valor DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente', -- pendente, pago, atrasado, cancelado
    data_vencimento TIMESTAMP WITH TIME ZONE NOT NULL,
    data_pagamento TIMESTAMP WITH TIME ZONE,
    comprovante_url TEXT,
    parcela INTEGER DEFAULT 1,
    total_parcelas INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_project_payments_project ON project_payments(project_id);
CREATE INDEX idx_project_payments_status ON project_payments(status);
CREATE INDEX idx_project_payments_vencimento ON project_payments(data_vencimento);

-- ============================================
-- TABELA: client_notifications (Notificações)
-- ============================================
CREATE TABLE IF NOT EXISTS client_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES client_projects(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensagem TEXT,
    lida BOOLEAN DEFAULT false,
    link VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_client_notifications_client ON client_notifications(client_id);
CREATE INDEX idx_client_notifications_lida ON client_notifications(lida);

-- ============================================
-- FUNÇÕES E TRIGGERS
-- ============================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_client_projects_updated_at
    BEFORE UPDATE ON client_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Função para calcular progresso do projeto automaticamente
CREATE OR REPLACE FUNCTION calculate_project_progress()
RETURNS TRIGGER AS $$
DECLARE
    total_stages INTEGER;
    completed_stages INTEGER;
    new_progress INTEGER;
BEGIN
    -- Contar etapas
    SELECT COUNT(*), COUNT(*) FILTER (WHERE concluida = true)
    INTO total_stages, completed_stages
    FROM project_stages
    WHERE project_id = NEW.project_id;

    -- Calcular progresso
    IF total_stages > 0 THEN
        new_progress := (completed_stages * 100) / total_stages;
    ELSE
        new_progress := 0;
    END IF;

    -- Atualizar projeto
    UPDATE client_projects
    SET progresso = new_progress,
        etapa_atual = completed_stages
    WHERE id = NEW.project_id;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para atualizar progresso quando etapa é concluída
CREATE TRIGGER update_project_progress
    AFTER UPDATE OF concluida ON project_stages
    FOR EACH ROW
    EXECUTE FUNCTION calculate_project_progress();

-- ============================================
-- POLÍTICAS RLS (Row Level Security)
-- ============================================

-- Habilitar RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE delivery_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_notifications ENABLE ROW LEVEL SECURITY;

-- Políticas para service_role (acesso total via backend)
CREATE POLICY "Service role has full access to clients"
    ON clients FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to client_projects"
    ON client_projects FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to project_stages"
    ON project_stages FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to delivery_items"
    ON delivery_items FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to approval_items"
    ON approval_items FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to project_timeline"
    ON project_timeline FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to project_comments"
    ON project_comments FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to project_payments"
    ON project_payments FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to client_notifications"
    ON client_notifications FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================
-- DADOS INICIAIS (Opcional)
-- ============================================

-- Inserir cliente de exemplo
-- INSERT INTO clients (nome, email, telefone, empresa, senha_hash)
-- VALUES ('Cliente Exemplo', 'cliente@exemplo.com', '11999999999', 'Empresa Exemplo', 'hash_here');
