-- Tabela de Notificações
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,  -- NULL = notificação global (para todos)
    tipo TEXT NOT NULL CHECK (tipo IN ('lead_quente', 'agendamento', 'lead_parado', 'proposta_vencendo', 'novo_lead', 'lead_movido', 'follow_up', 'sistema', 'outro')),
    prioridade TEXT NOT NULL DEFAULT 'medium' CHECK (prioridade IN ('low', 'medium', 'high', 'urgent')),
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    link TEXT,  -- URL para navegar ao clicar
    lida BOOLEAN DEFAULT FALSE,
    lead_id TEXT,
    lead_nome TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_lida ON notifications(lida);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_tipo ON notifications(tipo);
CREATE INDEX IF NOT EXISTS idx_notifications_prioridade ON notifications(prioridade);
CREATE INDEX IF NOT EXISTS idx_notifications_lead_id ON notifications(lead_id);

-- Índice composto para queries comuns (usuário + não lidas)
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, lida, created_at DESC);

-- Comentários
COMMENT ON TABLE notifications IS 'Sistema de notificações in-app';
COMMENT ON COLUMN notifications.user_id IS 'ID do usuário (NULL = notificação global)';
COMMENT ON COLUMN notifications.tipo IS 'Tipo de notificação: lead_quente, agendamento, lead_parado, proposta_vencendo, novo_lead, lead_movido, follow_up, sistema, outro';
COMMENT ON COLUMN notifications.prioridade IS 'Prioridade: low, medium, high, urgent';
COMMENT ON COLUMN notifications.link IS 'URL para navegar ao clicar na notificação';
COMMENT ON COLUMN notifications.lida IS 'Se a notificação foi lida';
COMMENT ON COLUMN notifications.lead_id IS 'ID do lead relacionado (opcional)';
COMMENT ON COLUMN notifications.metadata IS 'Dados adicionais em JSON';
