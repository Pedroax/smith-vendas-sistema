-- =====================================================
-- SMITH 2.0 - MIGRATION 004: Projects Table
-- Pipeline Kanban para Gerenciamento de Projetos
-- Data: 30/12/2024
-- =====================================================

-- =====================================================
-- ENUMS
-- =====================================================

-- Status do projeto no Pipeline Kanban
CREATE TYPE project_status AS ENUM (
  'backlog',
  'em_andamento',
  'concluido',
  'cancelado'
);

-- Prioridade do projeto
CREATE TYPE project_priority AS ENUM (
  'baixa',
  'media',
  'alta',
  'urgente'
);

-- =====================================================
-- TABELA: projects
-- =====================================================

CREATE TABLE projects (
  -- Identificação
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome VARCHAR(255) NOT NULL,
  descricao TEXT,

  -- Cliente (pode estar linkado a um lead)
  cliente_id UUID REFERENCES leads(id) ON DELETE SET NULL,
  cliente_nome VARCHAR(255),

  -- Status e prioridade
  status project_status NOT NULL DEFAULT 'backlog',
  prioridade project_priority NOT NULL DEFAULT 'media',

  -- Detalhes do projeto
  prazo TIMESTAMPTZ,
  valor DECIMAL(10, 2),
  responsavel VARCHAR(255),

  -- Organização
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  notas TEXT,

  -- Progresso
  progresso_percentual INTEGER DEFAULT 0 CHECK (progresso_percentual >= 0 AND progresso_percentual <= 100),

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,

  -- Constraints
  CONSTRAINT valid_progress CHECK (progresso_percentual >= 0 AND progresso_percentual <= 100)
);

-- Comentários
COMMENT ON TABLE projects IS 'Tabela de projetos para Pipeline Kanban - gerenciamento de implementações';
COMMENT ON COLUMN projects.cliente_id IS 'Referência ao lead/cliente (opcional)';
COMMENT ON COLUMN projects.cliente_nome IS 'Nome do cliente para exibição (pode ser diferente do lead)';
COMMENT ON COLUMN projects.progresso_percentual IS 'Percentual de conclusão do projeto (0-100)';
COMMENT ON COLUMN projects.started_at IS 'Data de início do projeto (quando movido para em_andamento)';
COMMENT ON COLUMN projects.completed_at IS 'Data de conclusão (quando movido para concluido)';

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_prioridade ON projects(prioridade);
CREATE INDEX idx_projects_cliente_id ON projects(cliente_id);
CREATE INDEX idx_projects_responsavel ON projects(responsavel);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_projects_prazo ON projects(prazo);
CREATE INDEX idx_projects_tags ON projects USING GIN(tags);

-- Índice para busca de texto (nome, descricao, cliente)
CREATE INDEX idx_projects_search ON projects USING GIN(
  to_tsvector('portuguese',
    COALESCE(nome, '') || ' ' ||
    COALESCE(descricao, '') || ' ' ||
    COALESCE(cliente_nome, '')
  )
);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger para atualizar updated_at automaticamente
CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Função para atualizar timestamps baseado em mudança de status
CREATE OR REPLACE FUNCTION update_project_status_timestamps()
RETURNS TRIGGER AS $$
BEGIN
  -- Se mudou para "em_andamento" e não tinha started_at, definir
  IF NEW.status = 'em_andamento' AND OLD.status != 'em_andamento' AND NEW.started_at IS NULL THEN
    NEW.started_at = NOW();
  END IF;

  -- Se mudou para "concluido" e não tinha completed_at, definir
  IF NEW.status = 'concluido' AND OLD.status != 'concluido' AND NEW.completed_at IS NULL THEN
    NEW.completed_at = NOW();
    -- Automaticamente marcar como 100% concluído
    NEW.progresso_percentual = 100;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para status timestamps
CREATE TRIGGER update_project_status_timestamps
  BEFORE UPDATE ON projects
  FOR EACH ROW
  EXECUTE FUNCTION update_project_status_timestamps();

-- =====================================================
-- FUNÇÕES ÚTEIS
-- =====================================================

-- Função para buscar projetos por texto
CREATE OR REPLACE FUNCTION search_projects(search_term TEXT)
RETURNS TABLE (
  id UUID,
  nome VARCHAR,
  cliente_nome VARCHAR,
  status project_status,
  prioridade project_priority,
  rank REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.nome,
    p.cliente_nome,
    p.status,
    p.prioridade,
    ts_rank(
      to_tsvector('portuguese',
        COALESCE(p.nome, '') || ' ' ||
        COALESCE(p.descricao, '') || ' ' ||
        COALESCE(p.cliente_nome, '')
      ),
      plainto_tsquery('portuguese', search_term)
    ) AS rank
  FROM projects p
  WHERE
    to_tsvector('portuguese',
      COALESCE(p.nome, '') || ' ' ||
      COALESCE(p.descricao, '') || ' ' ||
      COALESCE(p.cliente_nome, '')
    )
    @@ plainto_tsquery('portuguese', search_term)
  ORDER BY rank DESC;
END;
$$ LANGUAGE plpgsql;

-- Função para obter estatísticas de projetos
CREATE OR REPLACE FUNCTION get_projects_stats()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_projetos', COUNT(*),
    'por_status', (
      SELECT json_object_agg(status, count)
      FROM (
        SELECT status, COUNT(*) as count
        FROM projects
        GROUP BY status
      ) s
    ),
    'por_prioridade', (
      SELECT json_object_agg(prioridade, count)
      FROM (
        SELECT prioridade, COUNT(*) as count
        FROM projects
        GROUP BY prioridade
      ) p
    ),
    'valor_total', SUM(valor),
    'valor_concluido', SUM(CASE WHEN status = 'concluido' THEN valor ELSE 0 END),
    'progresso_medio', ROUND(AVG(progresso_percentual), 2),
    'projetos_atrasados', COUNT(*) FILTER (
      WHERE prazo < NOW() AND status NOT IN ('concluido', 'cancelado')
    )
  ) INTO result
  FROM projects;

  RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View: Projetos ativos (não concluídos nem cancelados)
CREATE OR REPLACE VIEW projects_ativos AS
SELECT *
FROM projects
WHERE status NOT IN ('concluido', 'cancelado')
ORDER BY prioridade DESC, created_at DESC;

-- View: Projetos atrasados
CREATE OR REPLACE VIEW projects_atrasados AS
SELECT *
FROM projects
WHERE prazo < NOW()
  AND status NOT IN ('concluido', 'cancelado')
ORDER BY prazo ASC;

-- View: Projetos por cliente (com dados do lead)
CREATE OR REPLACE VIEW projects_com_cliente AS
SELECT
  p.*,
  l.nome AS lead_nome,
  l.telefone AS lead_telefone,
  l.email AS lead_email,
  l.status AS lead_status
FROM projects p
LEFT JOIN leads l ON p.cliente_id = l.id;

-- =====================================================
-- GRANTS (Permissões)
-- =====================================================

GRANT ALL ON projects TO postgres, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON projects TO authenticated;
GRANT EXECUTE ON FUNCTION search_projects(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_projects_stats() TO authenticated;

-- =====================================================
-- FIM DA MIGRATION
-- =====================================================

SELECT 'Migration 004 (projects) executada com sucesso!' AS status;
