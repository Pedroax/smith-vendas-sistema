-- Tabela de Interações/Conversas com Leads
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('nota', 'ligacao', 'reuniao', 'email', 'whatsapp', 'proposta', 'follow_up', 'outro')),
    assunto TEXT,
    conteudo TEXT NOT NULL,
    user_id TEXT,
    user_nome TEXT NOT NULL DEFAULT 'Sistema',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON interactions(lead_id);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON interactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_tipo ON interactions(tipo);

-- Comentários
COMMENT ON TABLE interactions IS 'Interações e conversas com leads';
COMMENT ON COLUMN interactions.tipo IS 'Tipo de interação: nota, ligacao, reuniao, email, whatsapp, proposta, follow_up, outro';
COMMENT ON COLUMN interactions.conteudo IS 'Conteúdo da interação/nota';
COMMENT ON COLUMN interactions.metadata IS 'Dados adicionais em JSON (duração, anexos, etc)';
