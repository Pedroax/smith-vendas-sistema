-- =====================================================
-- SMITH 2.0 - QUERIES ÚTEIS
-- Comandos SQL para gerenciar e consultar dados
-- =====================================================

-- =====================================================
-- CONSULTAS BÁSICAS
-- =====================================================

-- Listar todos os leads
SELECT * FROM leads ORDER BY created_at DESC;

-- Listar apenas leads ativos (pipeline)
SELECT * FROM pipeline_ativo;

-- Listar leads qualificados
SELECT * FROM leads_qualificados;

-- Contar leads por status
SELECT status, COUNT(*) as quantidade
FROM leads
GROUP BY status
ORDER BY quantidade DESC;

-- Contar leads por origem
SELECT origem, COUNT(*) as quantidade
FROM leads
GROUP BY origem
ORDER BY quantidade DESC;

-- Contar leads por temperatura
SELECT temperatura, COUNT(*) as quantidade
FROM leads
GROUP BY temperatura
ORDER BY quantidade DESC;

-- =====================================================
-- BUSCA E FILTROS
-- =====================================================

-- Buscar lead por telefone
SELECT * FROM leads WHERE telefone = '+5511987654321';

-- Buscar lead por ID
SELECT * FROM leads WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Buscar leads por nome (case-insensitive)
SELECT * FROM leads WHERE LOWER(nome) LIKE '%joão%';

-- Buscar leads por empresa
SELECT * FROM leads WHERE LOWER(empresa) LIKE '%tech%';

-- Busca full-text (nome + empresa)
SELECT * FROM search_leads('tech solutions');

-- Filtrar por status
SELECT * FROM leads WHERE status = 'qualificado';

-- Filtrar por origem
SELECT * FROM leads WHERE origem = 'instagram';

-- Filtrar por temperatura
SELECT * FROM leads WHERE temperatura = 'quente';

-- Filtrar por score mínimo
SELECT * FROM leads WHERE lead_score >= 60;

-- Filtrar por tags
SELECT * FROM leads WHERE 'vip' = ANY(tags);

-- Filtrar leads criados hoje
SELECT * FROM leads
WHERE created_at >= CURRENT_DATE
ORDER BY created_at DESC;

-- Filtrar leads da última semana
SELECT * FROM leads
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Filtrar leads com agendamento futuro
SELECT * FROM leads
WHERE meeting_scheduled_at IS NOT NULL
  AND meeting_scheduled_at > NOW()
ORDER BY meeting_scheduled_at ASC;

-- =====================================================
-- ESTATÍSTICAS E AGREGAÇÕES
-- =====================================================

-- Estatísticas completas (usando função)
SELECT get_leads_stats();

-- Score médio por origem
SELECT origem, ROUND(AVG(lead_score), 2) as score_medio
FROM leads
GROUP BY origem
ORDER BY score_medio DESC;

-- Valor total por status
SELECT status, SUM(valor_estimado) as valor_total
FROM leads
GROUP BY status
ORDER BY valor_total DESC;

-- Taxa de conversão por origem
SELECT
  origem,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status = 'ganho') as ganhos,
  ROUND(
    (COUNT(*) FILTER (WHERE status = 'ganho')::NUMERIC / NULLIF(COUNT(*), 0) * 100),
    2
  ) as taxa_conversao
FROM leads
GROUP BY origem
ORDER BY taxa_conversao DESC;

-- Top 10 leads por score
SELECT nome, empresa, status, lead_score, valor_estimado
FROM leads
ORDER BY lead_score DESC
LIMIT 10;

-- Leads com maior valor estimado
SELECT nome, empresa, status, valor_estimado
FROM leads
WHERE valor_estimado > 0
ORDER BY valor_estimado DESC
LIMIT 10;

-- Resumo diário de leads criados (últimos 7 dias)
SELECT
  DATE(created_at) as data,
  COUNT(*) as total_leads,
  COUNT(*) FILTER (WHERE status = 'qualificado') as qualificados,
  COUNT(*) FILTER (WHERE status = 'ganho') as ganhos
FROM leads
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY data DESC;

-- =====================================================
-- CONVERSAS E MENSAGENS
-- =====================================================

-- Ver todas as mensagens de um lead
SELECT
  cm.timestamp,
  cm.role,
  cm.content
FROM conversation_messages cm
WHERE cm.lead_id = '00000000-0000-0000-0000-000000000001'::uuid
ORDER BY cm.timestamp ASC;

-- Contar mensagens por lead
SELECT
  l.nome,
  l.empresa,
  COUNT(cm.id) as total_mensagens
FROM leads l
LEFT JOIN conversation_messages cm ON cm.lead_id = l.id
GROUP BY l.id, l.nome, l.empresa
ORDER BY total_mensagens DESC;

-- Leads com conversas ativas (última mensagem < 24h)
SELECT
  l.nome,
  l.empresa,
  l.status,
  MAX(cm.timestamp) as ultima_mensagem
FROM leads l
JOIN conversation_messages cm ON cm.lead_id = l.id
GROUP BY l.id, l.nome, l.empresa, l.status
HAVING MAX(cm.timestamp) > NOW() - INTERVAL '24 hours'
ORDER BY ultima_mensagem DESC;

-- Últimas 10 mensagens de todos os leads
SELECT
  l.nome,
  cm.role,
  LEFT(cm.content, 50) || '...' as preview,
  cm.timestamp
FROM conversation_messages cm
JOIN leads l ON l.id = cm.lead_id
ORDER BY cm.timestamp DESC
LIMIT 10;

-- =====================================================
-- DADOS DE QUALIFICAÇÃO (JSONB)
-- =====================================================

-- Leads com budget maior que R$ 2000
SELECT nome, empresa, qualification_data->>'budget' as budget
FROM leads
WHERE (qualification_data->>'budget')::INTEGER > 2000
ORDER BY (qualification_data->>'budget')::INTEGER DESC;

-- Leads que são decisores
SELECT nome, empresa, status
FROM leads
WHERE (qualification_data->>'authority')::BOOLEAN = true;

-- Leads com ROI gerado (tem PDF)
SELECT nome, empresa, roi_analysis->>'pdf_url' as pdf_url
FROM leads
WHERE roi_analysis->>'pdf_url' IS NOT NULL;

-- Leads com timing urgente
SELECT nome, empresa, qualification_data->>'timing' as timing
FROM leads
WHERE LOWER(qualification_data->>'timing') LIKE '%urgente%'
   OR LOWER(qualification_data->>'timing') LIKE '%agora%';

-- =====================================================
-- ANÁLISES AVANÇADAS
-- =====================================================

-- Funil de conversão (percentuais)
WITH funil AS (
  SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status IN ('qualificado', 'agendamento_marcado', 'ganho', 'perdido')) as qualificados,
    COUNT(*) FILTER (WHERE status = 'agendamento_marcado' OR status = 'ganho') as agendamentos,
    COUNT(*) FILTER (WHERE status = 'ganho') as ganhos
  FROM leads
)
SELECT
  total,
  qualificados,
  ROUND((qualificados::NUMERIC / total * 100), 2) || '%' as taxa_qualificacao,
  agendamentos,
  ROUND((agendamentos::NUMERIC / NULLIF(qualificados, 0) * 100), 2) || '%' as taxa_agendamento,
  ganhos,
  ROUND((ganhos::NUMERIC / NULLIF(agendamentos, 0) * 100), 2) || '%' as taxa_fechamento
FROM funil;

-- Tempo médio de conversão (do novo ao ganho)
SELECT
  AVG(won_at - created_at) as tempo_medio_conversao
FROM leads
WHERE status = 'ganho';

-- Leads que precisam follow-up (sem interação há mais de 24h)
SELECT
  nome,
  empresa,
  status,
  ultima_interacao,
  NOW() - ultima_interacao as tempo_sem_interacao
FROM leads
WHERE status NOT IN ('ganho', 'perdido')
  AND ultima_interacao < NOW() - INTERVAL '24 hours'
ORDER BY ultima_interacao ASC;

-- Performance por dia da semana
SELECT
  TO_CHAR(created_at, 'Day') as dia_semana,
  COUNT(*) as total_leads,
  COUNT(*) FILTER (WHERE status = 'ganho') as ganhos,
  ROUND(
    (COUNT(*) FILTER (WHERE status = 'ganho')::NUMERIC / NULLIF(COUNT(*), 0) * 100),
    2
  ) as taxa_conversao
FROM leads
GROUP BY TO_CHAR(created_at, 'Day'), EXTRACT(DOW FROM created_at)
ORDER BY EXTRACT(DOW FROM created_at);

-- =====================================================
-- ATUALIZAÇÕES E MANUTENÇÃO
-- =====================================================

-- Atualizar status de um lead
UPDATE leads
SET status = 'qualificado'
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Atualizar temperatura
UPDATE leads
SET temperatura = 'quente'
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Adicionar tag a um lead
UPDATE leads
SET tags = array_append(tags, 'vip')
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Remover tag de um lead
UPDATE leads
SET tags = array_remove(tags, 'vip')
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Atualizar valor estimado
UPDATE leads
SET valor_estimado = 15000
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Marcar lead como ganho
UPDATE leads
SET status = 'ganho',
    temperatura = 'quente',
    won_at = NOW()
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Marcar lead como perdido
UPDATE leads
SET status = 'perdido',
    temperatura = 'frio',
    lost_at = NOW()
WHERE id = '00000000-0000-0000-0000-000000000001'::uuid;

-- Limpar dados de teste (CUIDADO!)
-- DELETE FROM conversation_messages;
-- DELETE FROM leads;

-- =====================================================
-- BACKUP E EXPORT
-- =====================================================

-- Exportar leads qualificados (CSV)
COPY (
  SELECT
    nome,
    empresa,
    telefone,
    email,
    status,
    lead_score,
    valor_estimado,
    created_at
  FROM leads
  WHERE status = 'qualificado'
  ORDER BY lead_score DESC
) TO '/tmp/leads_qualificados.csv' WITH CSV HEADER;

-- Exportar estatísticas
COPY (
  SELECT * FROM get_leads_stats()
) TO '/tmp/stats.json';

-- =====================================================
-- DEBUGGING E LOGS
-- =====================================================

-- Ver últimas atualizações
SELECT
  nome,
  status,
  updated_at,
  NOW() - updated_at as tempo_desde_update
FROM leads
ORDER BY updated_at DESC
LIMIT 20;

-- Leads com dados inconsistentes
SELECT * FROM leads
WHERE status = 'qualificado' AND lead_score < 60;

-- Leads sem conversas
SELECT l.*
FROM leads l
LEFT JOIN conversation_messages cm ON cm.lead_id = l.id
WHERE cm.id IS NULL;

-- Leads com muitas mensagens mas sem qualificação
SELECT
  l.nome,
  l.status,
  COUNT(cm.id) as total_mensagens
FROM leads l
JOIN conversation_messages cm ON cm.lead_id = l.id
WHERE l.status = 'novo'
GROUP BY l.id, l.nome, l.status
HAVING COUNT(cm.id) > 5
ORDER BY total_mensagens DESC;

-- =====================================================
-- PERFORMANCE E OTIMIZAÇÃO
-- =====================================================

-- Ver tamanho das tabelas
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Ver índices em uso
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Analisar query plan (exemplo)
EXPLAIN ANALYZE
SELECT * FROM leads
WHERE status = 'qualificado'
  AND lead_score >= 60
ORDER BY created_at DESC;

-- =====================================================
-- FIM
-- =====================================================

SELECT '✅ Queries úteis carregadas!' AS status;
