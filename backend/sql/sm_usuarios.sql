-- Tabela de usuários do sistema interno Smith
-- Executar no Supabase SQL Editor

CREATE TABLE IF NOT EXISTS sm_usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'marketing' CHECK (role IN ('admin', 'marketing')),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index para login rápido por email
CREATE INDEX IF NOT EXISTS sm_usuarios_email_idx ON sm_usuarios (email);
