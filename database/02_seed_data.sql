-- =====================================================
-- SMITH 2.0 - DADOS DE EXEMPLO (SEED)
-- Popula banco com leads de teste
-- Data: 25/12/2024
-- =====================================================

-- Limpar dados existentes (CUIDADO EM PRODUÇÃO!)
TRUNCATE conversation_messages CASCADE;
TRUNCATE leads CASCADE;

-- =====================================================
-- INSERIR LEADS DE EXEMPLO
-- =====================================================

-- Lead 1: Qualificado - Score Alto
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, roi_analysis, valor_estimado, notas, tags,
  ai_summary, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'João Silva',
  'Tech Solutions Ltda',
  '+5511987654321',
  'joao@techsolutions.com',
  'qualificado',
  'instagram',
  'quente',
  85,
  '{
    "budget": 3000,
    "authority": true,
    "need": "Estamos perdendo muitos leads por falta de atendimento 24/7",
    "timing": "Urgente, preciso implementar essa semana",
    "atendimentos_por_dia": 80,
    "tempo_por_atendimento": 15,
    "ticket_medio": 500,
    "funcionarios_atendimento": 2
  }'::jsonb,
  '{
    "tempo_economizado_mes": 180,
    "valor_economizado_ano": 129600,
    "roi_percentual": 360,
    "payback_meses": 3,
    "pdf_url": "/pdfs/roi-lead-001.pdf",
    "generated_at": "2024-12-25T10:30:00Z"
  }'::jsonb,
  25000,
  'Cliente muito interessado, tem urgência real',
  ARRAY['vip', 'hot', 'prioridade'],
  'Lead qualificado com score 85/100. Budget adequado, é decisor, necessidade clara.',
  NOW() - INTERVAL '2 hours',
  NOW() - INTERVAL '1 day'
);

-- Lead 2: Novo - Acabou de entrar
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000002'::uuid,
  'Maria Costa',
  'Marketing Digital Pro',
  '+5521998765432',
  'maria@marketingpro.com',
  'novo',
  'whatsapp',
  'morno',
  0,
  'Primeira interação via WhatsApp',
  ARRAY['novo'],
  NOW() - INTERVAL '30 minutes',
  NOW() - INTERVAL '30 minutes'
);

-- Lead 3: Contato Inicial
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000003'::uuid,
  'Pedro Santos',
  'E-commerce Plus',
  '+5511912345678',
  'pedro@ecommerceplus.com',
  'contato_inicial',
  'site',
  'morno',
  45,
  '{
    "need": "Quero automatizar atendimento da loja virtual",
    "atendimentos_por_dia": 30
  }'::jsonb,
  'Respondeu bem no primeiro contato',
  ARRAY['ecommerce'],
  NOW() - INTERVAL '3 hours',
  NOW() - INTERVAL '5 hours'
);

-- Lead 4: Qualificando
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, valor_estimado, notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000004'::uuid,
  'Ana Oliveira',
  'Clínica Saúde+',
  '+5521988887777',
  'ana@clinicasaude.com',
  'qualificando',
  'indicacao',
  'quente',
  62,
  '{
    "budget": 2000,
    "authority": true,
    "need": "Muitos pacientes ligam fora do horário",
    "atendimentos_por_dia": 40,
    "tempo_por_atendimento": 10
  }'::jsonb,
  12000,
  'Em processo de qualificação, respondendo perguntas BANT',
  ARRAY['saude', 'em-qualificacao'],
  NOW() - INTERVAL '1 hour',
  NOW() - INTERVAL '6 hours'
);

-- Lead 5: Agendamento Marcado
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, roi_analysis, valor_estimado, meeting_scheduled_at,
  meeting_google_event_id, notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000005'::uuid,
  'Carlos Mendes',
  'Indústria ABC',
  '+5511977776666',
  'carlos@industriaabc.com',
  'agendamento_marcado',
  'instagram',
  'quente',
  90,
  '{
    "budget": 5000,
    "authority": true,
    "need": "Crítico - estamos perdendo vendas",
    "timing": "Imediato",
    "atendimentos_por_dia": 150,
    "tempo_por_atendimento": 20,
    "ticket_medio": 800
  }'::jsonb,
  '{
    "tempo_economizado_mes": 300,
    "valor_economizado_ano": 216000,
    "roi_percentual": 450,
    "payback_meses": 2,
    "pdf_url": "/pdfs/roi-lead-005.pdf",
    "generated_at": "2024-12-24T15:00:00Z"
  }'::jsonb,
  35000,
  NOW() + INTERVAL '2 days',
  'evt_abc123xyz',
  'Reunião agendada para quinta-feira 14h com Pedro',
  ARRAY['vip', 'high-ticket', 'reuniao-agendada'],
  NOW() - INTERVAL '30 minutes',
  NOW() - INTERVAL '2 days'
);

-- Lead 6: Ganho (Fechado)
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, valor_estimado, won_at, notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000006'::uuid,
  'Fernanda Lima',
  'Consultoria FGL',
  '+5521999998888',
  'fernanda@consultoriafgl.com',
  'ganho',
  'indicacao',
  'quente',
  95,
  '{
    "budget": 4000,
    "authority": true,
    "need": "Preciso escalar atendimento",
    "timing": "Urgente"
  }'::jsonb,
  28000,
  NOW() - INTERVAL '1 day',
  'Cliente fechado! Implementação inicia semana que vem',
  ARRAY['cliente', 'fechado', 'vip'],
  NOW() - INTERVAL '1 day',
  NOW() - INTERVAL '10 days'
);

-- Lead 7: Perdido (Não qualificado)
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, lost_at, notas, tags, ai_summary, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000007'::uuid,
  'Roberto Alves',
  'Startup XYZ',
  '+5511966665555',
  'roberto@startupxyz.com',
  'perdido',
  'site',
  'frio',
  25,
  '{
    "budget": 300,
    "authority": false,
    "need": "Só curiosidade",
    "timing": "Talvez ano que vem",
    "atendimentos_por_dia": 5
  }'::jsonb,
  NOW() - INTERVAL '3 days',
  'Não qualificado - orçamento muito baixo e sem urgência',
  ARRAY['nao-qualificado', 'budget-baixo'],
  'Lead não qualificado. Motivo: Orçamento insuficiente E volume operacional baixo. Score: 25/100',
  NOW() - INTERVAL '3 days',
  NOW() - INTERVAL '5 days'
);

-- Lead 8: Qualificado - Pronto para ROI
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, valor_estimado, notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000008'::uuid,
  'Juliana Ferreira',
  'Imobiliária Prime',
  '+5521977778888',
  'juliana@imobiliariaprime.com',
  'qualificado',
  'whatsapp',
  'quente',
  78,
  '{
    "budget": 2500,
    "authority": true,
    "need": "Muitos leads não são atendidos rapidamente",
    "timing": "Próximo mês",
    "atendimentos_por_dia": 60,
    "tempo_por_atendimento": 12,
    "ticket_medio": 1200
  }'::jsonb,
  18000,
  'Lead engajado, respondeu todas as perguntas',
  ARRAY['imobiliaria', 'hot'],
  NOW() - INTERVAL '4 hours',
  NOW() - INTERVAL '1 day'
);

-- Lead 9: Novo - Recente
INSERT INTO leads (
  id, nome, empresa, telefone, status, origem, temperatura, lead_score,
  ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000009'::uuid,
  'Ricardo Gomes',
  'Tech Startup',
  '+5511955554444',
  'novo',
  'instagram',
  'morno',
  0,
  NOW() - INTERVAL '10 minutes',
  NOW() - INTERVAL '10 minutes'
);

-- Lead 10: Qualificando - Meio do funil
INSERT INTO leads (
  id, nome, empresa, telefone, email, status, origem, temperatura, lead_score,
  qualification_data, valor_estimado, notas, tags, ultima_interacao, created_at
) VALUES (
  '00000000-0000-0000-0000-000000000010'::uuid,
  'Patrícia Souza',
  'Escola de Idiomas ABC',
  '+5521966667777',
  'patricia@escolaabc.com',
  'qualificando',
  'site',
  'morno',
  55,
  '{
    "budget": 1500,
    "need": "Atendimento de matrículas está caótico",
    "atendimentos_por_dia": 35,
    "tempo_por_atendimento": 18
  }'::jsonb,
  10000,
  'Interessada mas ainda coletando informações',
  ARRAY['educacao'],
  NOW() - INTERVAL '2 hours',
  NOW() - INTERVAL '8 hours'
);

-- =====================================================
-- INSERIR CONVERSAS DE EXEMPLO
-- =====================================================

-- Conversa do Lead 1 (João Silva - Qualificado)
INSERT INTO conversation_messages (lead_id, role, content, timestamp) VALUES
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Olá, vi o anúncio de vocês no Instagram sobre automação de atendimento', NOW() - INTERVAL '1 day'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'Olá João! Que bom ter você por aqui! 😊 Vi que você tem a Tech Solutions. Me conta, o que te chamou atenção na automação?', NOW() - INTERVAL '23 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Estamos perdendo muitos leads porque não conseguimos atender 24/7', NOW() - INTERVAL '22 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'Entendo perfeitamente! Quantos atendimentos vocês fazem por dia em média?', NOW() - INTERVAL '22 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Cerca de 80 por dia, mas fora do horário comercial perdemos uns 30-40', NOW() - INTERVAL '21 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'Isso é bastante! E quanto tempo em média vocês gastam em cada atendimento?', NOW() - INTERVAL '21 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Uns 15 minutos em média', NOW() - INTERVAL '20 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'Perfeito! E vocês já têm um orçamento pensado para essa automação?', NOW() - INTERVAL '20 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Sim, posso investir até R$ 3.000 por mês', NOW() - INTERVAL '19 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'Ótimo! Você é quem decide sobre ferramentas na empresa?', NOW() - INTERVAL '19 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Sim, sou sócio e responsável pela área comercial', NOW() - INTERVAL '18 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'Perfeito! Deixa eu fazer uma análise completa baseada no que você me passou...', NOW() - INTERVAL '18 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'assistant', 'João, acabei de fazer uma análise personalizada para a Tech Solutions! 📊\n\nVocês estão perdendo R$ 10.800 por mês em oportunidades. Com nossa solução, o ROI é de 360% ao ano.\n\nEnviei um PDF completo com a análise. Vale muito a pena conversarmos sobre isso!', NOW() - INTERVAL '17 hours'),
  ('00000000-0000-0000-0000-000000000001'::uuid, 'user', 'Nossa, não imaginava que estava perdendo tanto! Quero saber mais', NOW() - INTERVAL '2 hours');

-- Conversa do Lead 2 (Maria Costa - Novo)
INSERT INTO conversation_messages (lead_id, role, content, timestamp) VALUES
  ('00000000-0000-0000-0000-000000000002'::uuid, 'user', 'Oi, vim pelo WhatsApp', NOW() - INTERVAL '30 minutes'),
  ('00000000-0000-0000-0000-000000000002'::uuid, 'assistant', 'Olá Maria! Bem-vinda! 😊 Vi que você tem a Marketing Digital Pro. Me conta, o que posso te ajudar hoje?', NOW() - INTERVAL '29 minutes');

-- Conversa do Lead 3 (Pedro Santos - Contato Inicial)
INSERT INTO conversation_messages (lead_id, role, content, timestamp) VALUES
  ('00000000-0000-0000-0000-000000000003'::uuid, 'user', 'Olá, gostaria de saber sobre automação para e-commerce', NOW() - INTERVAL '5 hours'),
  ('00000000-0000-0000-0000-000000000003'::uuid, 'assistant', 'Olá Pedro! Ótimo ter você aqui! Vi que você tem o E-commerce Plus. Que tipo de automação você está buscando?', NOW() - INTERVAL '4 hours 55 minutes'),
  ('00000000-0000-0000-0000-000000000003'::uuid, 'user', 'Quero automatizar o atendimento da loja virtual', NOW() - INTERVAL '4 hours 50 minutes'),
  ('00000000-0000-0000-0000-000000000003'::uuid, 'assistant', 'Perfeito! E quantos atendimentos vocês fazem por dia em média?', NOW() - INTERVAL '4 hours 45 minutes'),
  ('00000000-0000-0000-0000-000000000003'::uuid, 'user', 'Uns 30 por dia', NOW() - INTERVAL '3 hours');

-- Conversa do Lead 5 (Carlos Mendes - Agendamento Marcado)
INSERT INTO conversation_messages (lead_id, role, content, timestamp) VALUES
  ('00000000-0000-0000-0000-000000000005'::uuid, 'user', 'Preciso de uma solução URGENTE para automação', NOW() - INTERVAL '2 days'),
  ('00000000-0000-0000-0000-000000000005'::uuid, 'assistant', 'Olá Carlos! Entendo a urgência. Me conta mais sobre sua situação atual.', NOW() - INTERVAL '2 days'),
  ('00000000-0000-0000-0000-000000000005'::uuid, 'user', 'Fazemos 150 atendimentos por dia e estamos perdendo muitas vendas', NOW() - INTERVAL '2 days'),
  ('00000000-0000-0000-0000-000000000005'::uuid, 'assistant', 'Perfeito Carlos! Vou agendar uma reunião para quinta-feira às 14h. Confirma pra mim?', NOW() - INTERVAL '1 day'),
  ('00000000-0000-0000-0000-000000000005'::uuid, 'user', 'Confirmado!', NOW() - INTERVAL '1 day');

-- =====================================================
-- VERIFICAÇÕES
-- =====================================================

-- Contar leads inseridos
SELECT 'Leads inseridos:' AS info, COUNT(*) AS total FROM leads;

-- Contar mensagens inseridas
SELECT 'Mensagens inseridas:' AS info, COUNT(*) AS total FROM conversation_messages;

-- Mostrar distribuição por status
SELECT status, COUNT(*) AS quantidade
FROM leads
GROUP BY status
ORDER BY quantidade DESC;

-- Mostrar estatísticas gerais
SELECT get_leads_stats() AS estatisticas;

SELECT '✅ Dados de exemplo inseridos com sucesso!' AS status;
