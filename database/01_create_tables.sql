-- =====================================================
-- SMITH 2.0 - DATABASE SCHEMA
-- Supabase PostgreSQL
-- Data: 25/12/2024
-- =====================================================

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para busca de texto

-- =====================================================
-- ENUMS
-- =====================================================

-- Status do lead no funil
CREATE TYPE lead_status AS ENUM (
  'novo',
  'contato_inicial',
  'qualificando',
  'qualificado',
  'agendamento_marcado',
  'ganho',
  'perdido'
);

-- Origem do lead
CREATE TYPE lead_origin AS ENUM (
  'instagram',
  'whatsapp',
  'site',
  'indicacao',
  'outro'
);

-- Temperatura do lead
CREATE TYPE lead_temperature AS ENUM (
  'quente',
  'morno',
  'frio'
);

-- =====================================================
-- TABELA: leads
-- =====================================================

CREATE TABLE leads (
  -- Identificação
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome VARCHAR(255) NOT NULL,
  empresa VARCHAR(255),
  telefone VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255),
  avatar TEXT,

  -- Status e classificação
  status lead_status NOT NULL DEFAULT 'novo',
  origem lead_origin NOT NULL,
  temperatura lead_temperature NOT NULL DEFAULT 'morno',
  lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),

  -- Dados de qualificação (BANT + operacionais)
  qualification_data JSONB DEFAULT '{}'::jsonb,

  -- Análise de ROI
  roi_analysis JSONB DEFAULT '{}'::jsonb,
  valor_estimado DECIMAL(10, 2) DEFAULT 0.0,

  -- Agendamento
  meeting_scheduled_at TIMESTAMPTZ,
  meeting_google_event_id VARCHAR(255),

  -- Follow-up
  followup_config JSONB DEFAULT '{"tentativas_realizadas": 0, "intervalo_horas": [24, 72, 168]}'::jsonb,

  -- Histórico e interações
  ultima_interacao TIMESTAMPTZ,
  ultima_mensagem_ia TEXT,

  -- Notas e observações
  notas TEXT,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],

  -- Inteligência Artificial
  ai_summary TEXT,
  ai_next_action VARCHAR(100),
  requires_human_approval BOOLEAN DEFAULT false,

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  lost_at TIMESTAMPTZ,
  won_at TIMESTAMPTZ,

  -- Constraints
  CONSTRAINT valid_phone CHECK (telefone ~ '^\+?[0-9]{10,15}$'),
  CONSTRAINT valid_email CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Comentários
COMMENT ON TABLE leads IS 'Tabela principal de leads do sistema Smith 2.0';
COMMENT ON COLUMN leads.qualification_data IS 'Dados BANT (Budget, Authority, Need, Timing) + dados operacionais';
COMMENT ON COLUMN leads.roi_analysis IS 'Análise de ROI calculada pelo sistema';
COMMENT ON COLUMN leads.followup_config IS 'Configuração de follow-ups automáticos';
COMMENT ON COLUMN leads.lead_score IS 'Score de qualificação (0-100 pontos)';

-- =====================================================
-- TABELA: conversation_messages
-- =====================================================

CREATE TABLE conversation_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

  -- Conteúdo da mensagem
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,

  -- Timestamp
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Índice para ordenação
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE conversation_messages IS 'Histórico completo de conversas entre leads e o agente Smith';
COMMENT ON COLUMN conversation_messages.role IS 'user = lead, assistant = Smith IA';
COMMENT ON COLUMN conversation_messages.metadata IS 'Dados adicionais (sentiment, intent, etc)';

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices na tabela leads
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_origem ON leads(origem);
CREATE INDEX idx_leads_temperatura ON leads(temperatura);
CREATE INDEX idx_leads_telefone ON leads(telefone);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_lead_score ON leads(lead_score DESC);
CREATE INDEX idx_leads_tags ON leads USING GIN(tags);

-- Índice para busca de texto (nome, empresa)
CREATE INDEX idx_leads_search ON leads USING GIN(
  to_tsvector('portuguese', COALESCE(nome, '') || ' ' || COALESCE(empresa, ''))
);

-- Índices JSONB para queries rápidas
CREATE INDEX idx_leads_qualification_budget ON leads((qualification_data->>'budget'));
CREATE INDEX idx_leads_roi_pdf_url ON leads((roi_analysis->>'pdf_url'));

-- Índices na tabela conversation_messages
CREATE INDEX idx_messages_lead_id ON conversation_messages(lead_id);
CREATE INDEX idx_messages_timestamp ON conversation_messages(timestamp DESC);
CREATE INDEX idx_messages_lead_timestamp ON conversation_messages(lead_id, timestamp DESC);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para leads
CREATE TRIGGER update_leads_updated_at
  BEFORE UPDATE ON leads
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Função para atualizar ultima_interacao quando há nova mensagem
CREATE OR REPLACE FUNCTION update_lead_ultima_interacao()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE leads
  SET ultima_interacao = NEW.timestamp,
      ultima_mensagem_ia = CASE
        WHEN NEW.role = 'assistant' THEN NEW.content
        ELSE ultima_mensagem_ia
      END
  WHERE id = NEW.lead_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para conversation_messages
CREATE TRIGGER update_lead_on_new_message
  AFTER INSERT ON conversation_messages
  FOR EACH ROW
  EXECUTE FUNCTION update_lead_ultima_interacao();

-- =====================================================
-- RLS (Row Level Security) - OPCIONAL
-- =====================================================

-- Descomente se quiser habilitar RLS para multi-tenant

-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

-- -- Policy: Usuários autenticados podem ver todos os leads
-- CREATE POLICY "Usuários podem ver todos os leads"
--   ON leads
--   FOR SELECT
--   USING (auth.role() = 'authenticated');

-- -- Policy: Usuários autenticados podem inserir leads
-- CREATE POLICY "Usuários podem criar leads"
--   ON leads
--   FOR INSERT
--   WITH CHECK (auth.role() = 'authenticated');

-- -- Policy: Usuários autenticados podem atualizar leads
-- CREATE POLICY "Usuários podem atualizar leads"
--   ON leads
--   FOR UPDATE
--   USING (auth.role() = 'authenticated');

-- =====================================================
-- FUNÇÕES ÚTEIS
-- =====================================================

-- Função para buscar leads por texto
CREATE OR REPLACE FUNCTION search_leads(search_term TEXT)
RETURNS TABLE (
  id UUID,
  nome VARCHAR,
  empresa VARCHAR,
  telefone VARCHAR,
  status lead_status,
  lead_score INTEGER,
  rank REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    l.id,
    l.nome,
    l.empresa,
    l.telefone,
    l.status,
    l.lead_score,
    ts_rank(
      to_tsvector('portuguese', COALESCE(l.nome, '') || ' ' || COALESCE(l.empresa, '')),
      plainto_tsquery('portuguese', search_term)
    ) AS rank
  FROM leads l
  WHERE
    to_tsvector('portuguese', COALESCE(l.nome, '') || ' ' || COALESCE(l.empresa, ''))
    @@ plainto_tsquery('portuguese', search_term)
  ORDER BY rank DESC;
END;
$$ LANGUAGE plpgsql;

-- Função para obter estatísticas agregadas
CREATE OR REPLACE FUNCTION get_leads_stats()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_leads', COUNT(*),
    'por_status', (
      SELECT json_object_agg(status, count)
      FROM (
        SELECT status, COUNT(*) as count
        FROM leads
        GROUP BY status
      ) s
    ),
    'por_origem', (
      SELECT json_object_agg(origem, count)
      FROM (
        SELECT origem, COUNT(*) as count
        FROM leads
        GROUP BY origem
      ) o
    ),
    'por_temperatura', (
      SELECT json_object_agg(temperatura, count)
      FROM (
        SELECT temperatura, COUNT(*) as count
        FROM leads
        GROUP BY temperatura
      ) t
    ),
    'score_medio', ROUND(AVG(lead_score), 2),
    'valor_total_pipeline', SUM(valor_estimado),
    'taxa_qualificacao', ROUND(
      (COUNT(*) FILTER (WHERE status IN ('qualificado', 'agendamento_marcado', 'ganho'))::NUMERIC /
       NULLIF(COUNT(*), 0) * 100), 2
    ),
    'taxa_conversao', ROUND(
      (COUNT(*) FILTER (WHERE status = 'ganho')::NUMERIC /
       NULLIF(COUNT(*), 0) * 100), 2
    )
  ) INTO result
  FROM leads;

  RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View: Leads com última mensagem
CREATE OR REPLACE VIEW leads_with_last_message AS
SELECT
  l.*,
  (
    SELECT content
    FROM conversation_messages
    WHERE lead_id = l.id
    ORDER BY timestamp DESC
    LIMIT 1
  ) AS last_message,
  (
    SELECT timestamp
    FROM conversation_messages
    WHERE lead_id = l.id
    ORDER BY timestamp DESC
    LIMIT 1
  ) AS last_message_at,
  (
    SELECT COUNT(*)
    FROM conversation_messages
    WHERE lead_id = l.id
  ) AS total_messages
FROM leads l;

-- View: Leads qualificados (score >= 60)
CREATE OR REPLACE VIEW leads_qualificados AS
SELECT *
FROM leads
WHERE lead_score >= 60
  AND status IN ('qualificado', 'agendamento_marcado', 'ganho');

-- View: Pipeline ativo (excluindo ganhos e perdidos)
CREATE OR REPLACE VIEW pipeline_ativo AS
SELECT *
FROM leads
WHERE status NOT IN ('ganho', 'perdido')
ORDER BY lead_score DESC, created_at DESC;

-- =====================================================
-- GRANTS (Permissões)
-- =====================================================

-- Se estiver usando service_role
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres, service_role;

-- Se estiver usando autenticação
GRANT SELECT, INSERT, UPDATE, DELETE ON leads TO authenticated;
GRANT SELECT, INSERT ON conversation_messages TO authenticated;
GRANT EXECUTE ON FUNCTION search_leads(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_leads_stats() TO authenticated;

-- =====================================================
-- FIM DO SCHEMA
-- =====================================================

-- Para verificar se tudo foi criado:
SELECT 'Schema criado com sucesso!' AS status;
