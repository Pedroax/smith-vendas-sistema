-- Migration: Criar tabela de agendamentos
-- Data: 2025-12-29
-- Descrição: Tabela para armazenar reuniões agendadas com leads

-- Criar tabela de agendamentos
CREATE TABLE IF NOT EXISTS agendamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Dados da reunião
    data_hora TIMESTAMPTZ NOT NULL,
    duracao_minutos INTEGER DEFAULT 30,

    -- Integração Google Calendar
    google_event_id TEXT,
    google_meet_link TEXT,
    google_event_link TEXT,

    -- Status
    status TEXT NOT NULL DEFAULT 'agendado' CHECK (status IN ('agendado', 'confirmado', 'cancelado', 'realizado', 'nao_compareceu')),

    -- Confirmação
    confirmado_em TIMESTAMPTZ,
    confirmado_via TEXT,

    -- Lembretes
    lembrete_24h_enviado BOOLEAN DEFAULT FALSE,
    lembrete_3h_enviado BOOLEAN DEFAULT FALSE,
    lembrete_30min_enviado BOOLEAN DEFAULT FALSE,

    -- Observações
    observacoes TEXT,
    motivo_cancelamento TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_agendamentos_lead_id ON agendamentos(lead_id);
CREATE INDEX IF NOT EXISTS idx_agendamentos_data_hora ON agendamentos(data_hora);
CREATE INDEX IF NOT EXISTS idx_agendamentos_status ON agendamentos(status);
CREATE INDEX IF NOT EXISTS idx_agendamentos_google_event_id ON agendamentos(google_event_id);

-- Índice composto para buscar agendamentos próximos
CREATE INDEX IF NOT EXISTS idx_agendamentos_data_status ON agendamentos(data_hora, status);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_agendamentos_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agendamentos_updated_at
    BEFORE UPDATE ON agendamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_agendamentos_updated_at();

-- Comentários nas colunas
COMMENT ON TABLE agendamentos IS 'Armazena reuniões agendadas com leads';
COMMENT ON COLUMN agendamentos.lead_id IS 'Referência ao lead que agendou';
COMMENT ON COLUMN agendamentos.data_hora IS 'Data e hora da reunião (com timezone)';
COMMENT ON COLUMN agendamentos.duracao_minutos IS 'Duração da reunião em minutos';
COMMENT ON COLUMN agendamentos.google_event_id IS 'ID do evento no Google Calendar';
COMMENT ON COLUMN agendamentos.google_meet_link IS 'Link do Google Meet gerado automaticamente';
COMMENT ON COLUMN agendamentos.status IS 'Status: agendado, confirmado, cancelado, realizado, nao_compareceu';
COMMENT ON COLUMN agendamentos.lembrete_24h_enviado IS 'Indica se o lembrete de 24h foi enviado';
COMMENT ON COLUMN agendamentos.lembrete_3h_enviado IS 'Indica se o lembrete de 3h foi enviado';
COMMENT ON COLUMN agendamentos.lembrete_30min_enviado IS 'Indica se o lembrete de 30min foi enviado';
