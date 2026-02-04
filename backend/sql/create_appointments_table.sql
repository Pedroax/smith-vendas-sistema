-- Tabela de Agendamentos/Compromissos
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id TEXT NOT NULL,
    lead_nome TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN ('reuniao', 'ligacao', 'follow_up', 'demo', 'apresentacao', 'outro')),
    titulo TEXT NOT NULL,
    descricao TEXT,
    data_hora TIMESTAMPTZ NOT NULL,
    duracao_minutos INTEGER NOT NULL DEFAULT 60,
    status TEXT NOT NULL DEFAULT 'agendado' CHECK (status IN ('agendado', 'confirmado', 'concluido', 'cancelado', 'remarcado')),
    user_nome TEXT NOT NULL DEFAULT 'Sistema',
    location TEXT,
    meeting_url TEXT,
    observacoes TEXT,
    lembrete_enviado BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_appointments_lead_id ON appointments(lead_id);
CREATE INDEX IF NOT EXISTS idx_appointments_data_hora ON appointments(data_hora);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_tipo ON appointments(tipo);
CREATE INDEX IF NOT EXISTS idx_appointments_created_at ON appointments(created_at DESC);

-- Índice composto para queries de período + status
CREATE INDEX IF NOT EXISTS idx_appointments_date_status ON appointments(data_hora, status);

-- Comentários
COMMENT ON TABLE appointments IS 'Agendamentos e compromissos com leads';
COMMENT ON COLUMN appointments.tipo IS 'Tipo de agendamento: reuniao, ligacao, follow_up, demo, apresentacao, outro';
COMMENT ON COLUMN appointments.status IS 'Status: agendado, confirmado, concluido, cancelado, remarcado';
COMMENT ON COLUMN appointments.data_hora IS 'Data e hora do agendamento';
COMMENT ON COLUMN appointments.duracao_minutos IS 'Duração estimada em minutos';
COMMENT ON COLUMN appointments.location IS 'Local para reuniões presenciais';
COMMENT ON COLUMN appointments.meeting_url IS 'URL para reuniões online (Google Meet, Zoom, etc)';
COMMENT ON COLUMN appointments.lembrete_enviado IS 'Controle de envio de lembretes';
COMMENT ON COLUMN appointments.metadata IS 'Dados adicionais em JSON (participantes, anexos, etc)';
