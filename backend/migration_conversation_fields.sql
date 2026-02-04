-- ============================================
-- MIGRAÇÃO: Adicionar campos de qualificação
-- ============================================
-- Execute no SQL Editor do Supabase
-- ============================================

-- Adicionar campo para contador de mensagens na qualificação
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS qualification_message_count INTEGER DEFAULT 0 NOT NULL;

-- Adicionar campo para armazenar URL do site pesquisado
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS website_researched VARCHAR(500);

-- ============================================
-- ✅ Migração concluída!
-- ============================================
-- Novos campos adicionados:
-- ✓ qualification_message_count - Conta mensagens na fase de qualificação
-- ✓ website_researched - Armazena URL do site pesquisado
-- ============================================

SELECT 'Migração completa! Novos campos adicionados à tabela conversations.' as status;
