-- Criar tabela de documentos do projeto
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
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_project_documents_project_id ON project_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_project_documents_tipo ON project_documents(tipo);

-- Comentários
COMMENT ON TABLE project_documents IS 'Documentos anexados aos projetos (contratos, termos, etc)';
COMMENT ON COLUMN project_documents.tipo IS 'Tipo de documento: contrato, termo_entrega, outro';
