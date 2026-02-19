-- ============================================
-- MIGRAÇÃO: Adicionar campo temp_meeting_slot
-- ============================================
-- Execute no SQL Editor do Supabase
-- ============================================

-- Adicionar campo para armazenar slot temporário de agendamento
-- Este campo armazena o horário escolhido pelo lead enquanto aguardamos o email
-- Formato JSONB: {"start": "ISO datetime", "end": "ISO datetime", "display": "texto"}
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS temp_meeting_slot JSONB DEFAULT NULL;

-- Adicionar comentário explicativo
COMMENT ON COLUMN leads.temp_meeting_slot IS 'Slot temporário de agendamento (JSONB). Armazena horário escolhido enquanto aguarda email. Limpo após criação do evento.';

-- ============================================
-- ✅ Migração concluída!
-- ============================================
-- Novo campo adicionado:
-- ✓ temp_meeting_slot (JSONB) - Armazena slot escolhido temporariamente
--   durante o processo de agendamento (entre escolha do horário e fornecimento do email)
-- ============================================

SELECT 'Migração completa! Campo temp_meeting_slot adicionado à tabela leads.' as status;
