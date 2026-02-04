# 📊 Diagrama do Schema - Smith 2.0

Visualização da estrutura do banco de dados.

---

## 🗂️ Tabelas e Relacionamentos

```
┌─────────────────────────────────────────────────────────────┐
│                          LEADS                              │
├─────────────────────────────────────────────────────────────┤
│ PK  id                    UUID                              │
│     nome                  VARCHAR(255)        NOT NULL      │
│     empresa               VARCHAR(255)                      │
│     telefone              VARCHAR(50)         UNIQUE        │
│     email                 VARCHAR(255)                      │
│     avatar                TEXT                              │
├─────────────────────────────────────────────────────────────┤
│     status                lead_status         NOT NULL      │
│     origem                lead_origin         NOT NULL      │
│     temperatura           lead_temperature    NOT NULL      │
│     lead_score            INTEGER (0-100)                   │
├─────────────────────────────────────────────────────────────┤
│     qualification_data    JSONB              DEFAULT '{}'   │
│     roi_analysis          JSONB              DEFAULT '{}'   │
│     valor_estimado        DECIMAL(10,2)      DEFAULT 0.0    │
├─────────────────────────────────────────────────────────────┤
│     meeting_scheduled_at  TIMESTAMPTZ                       │
│     meeting_google_event_id VARCHAR(255)                    │
├─────────────────────────────────────────────────────────────┤
│     followup_config       JSONB              DEFAULT {...}  │
│     ultima_interacao      TIMESTAMPTZ                       │
│     ultima_mensagem_ia    TEXT                              │
├─────────────────────────────────────────────────────────────┤
│     notas                 TEXT                              │
│     tags                  TEXT[]             DEFAULT []     │
├─────────────────────────────────────────────────────────────┤
│     ai_summary            TEXT                              │
│     ai_next_action        VARCHAR(100)                      │
│     requires_human_approval BOOLEAN          DEFAULT false  │
├─────────────────────────────────────────────────────────────┤
│     created_at            TIMESTAMPTZ        NOT NULL       │
│     updated_at            TIMESTAMPTZ        NOT NULL       │
│     lost_at               TIMESTAMPTZ                       │
│     won_at                TIMESTAMPTZ                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  CONVERSATION_MESSAGES                      │
├─────────────────────────────────────────────────────────────┤
│ PK  id                    UUID                              │
│ FK  lead_id               UUID          → leads.id          │
│     role                  VARCHAR(20)        NOT NULL       │
│     content               TEXT               NOT NULL       │
│     metadata              JSONB              DEFAULT '{}'   │
│     timestamp             TIMESTAMPTZ        NOT NULL       │
│     created_at            TIMESTAMPTZ        NOT NULL       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏷️ ENUMs

### lead_status

```
┌─────────────────────────┐
│   LEAD STATUS           │
├─────────────────────────┤
│ • novo                  │
│ • contato_inicial       │
│ • qualificando          │
│ • qualificado           │
│ • agendamento_marcado   │
│ • ganho                 │
│ • perdido               │
└─────────────────────────┘
```

### lead_origin

```
┌─────────────────────────┐
│   LEAD ORIGIN           │
├─────────────────────────┤
│ • instagram             │
│ • whatsapp              │
│ • site                  │
│ • indicacao             │
│ • outro                 │
└─────────────────────────┘
```

### lead_temperature

```
┌─────────────────────────┐
│  LEAD TEMPERATURE       │
├─────────────────────────┤
│ • quente                │
│ • morno                 │
│ • frio                  │
└─────────────────────────┘
```

---

## 📦 JSONB Structures

### qualification_data

```json
{
  "budget": 3000,
  "authority": true,
  "need": "Estamos perdendo muitos leads",
  "timing": "Urgente",
  "atendimentos_por_dia": 80,
  "tempo_por_atendimento": 15,
  "ticket_medio": 500,
  "funcionarios_atendimento": 2,
  "ferramentas_atuais": ["WhatsApp Business", "Planilha"],
  "maior_desafio": "Atendimento 24/7",
  "expectativa_roi": "Reduzir custos em 40%"
}
```

### roi_analysis

```json
{
  "tempo_economizado_mes": 180,
  "valor_economizado_ano": 129600,
  "roi_percentual": 360,
  "payback_meses": 3,
  "pdf_url": "/pdfs/roi-lead-001.pdf",
  "generated_at": "2024-12-25T10:30:00Z"
}
```

### followup_config

```json
{
  "tentativas_realizadas": 0,
  "proxima_tentativa": "2024-12-26T10:00:00Z",
  "intervalo_horas": [24, 72, 168],
  "mensagem_template": "Oi {nome}, tudo bem? Vi que..."
}
```

### conversation_messages.metadata

```json
{
  "sentiment": "positive",
  "intent": "qualificacao",
  "confidence": 0.95,
  "entities": ["budget", "timing"],
  "platform": "whatsapp"
}
```

---

## 🔍 Índices

### Índices Simples

```
leads:
  ├─ idx_leads_status           ON status
  ├─ idx_leads_origem           ON origem
  ├─ idx_leads_temperatura      ON temperatura
  ├─ idx_leads_telefone         ON telefone (UNIQUE)
  ├─ idx_leads_created_at       ON created_at DESC
  └─ idx_leads_lead_score       ON lead_score DESC

conversation_messages:
  ├─ idx_messages_lead_id       ON lead_id
  ├─ idx_messages_timestamp     ON timestamp DESC
  └─ idx_messages_lead_timestamp ON (lead_id, timestamp DESC)
```

### Índices GIN (Full-Text e Arrays)

```
leads:
  ├─ idx_leads_tags             ON tags (GIN)
  └─ idx_leads_search           ON to_tsvector(nome || empresa) (GIN)
```

### Índices JSONB

```
leads:
  ├─ idx_leads_qualification_budget  ON (qualification_data->>'budget')
  └─ idx_leads_roi_pdf_url           ON (roi_analysis->>'pdf_url')
```

---

## ⚡ Triggers

### update_leads_updated_at

```
BEFORE UPDATE ON leads
  ↓
  SET updated_at = NOW()
```

### update_lead_on_new_message

```
AFTER INSERT ON conversation_messages
  ↓
  UPDATE leads SET:
    - ultima_interacao = NEW.timestamp
    - ultima_mensagem_ia = NEW.content (if role = 'assistant')
```

---

## 🔧 Funções

### search_leads(search_term TEXT)

Busca full-text em leads por nome/empresa.

**Input:** `'tech solutions'`

**Output:**
```sql
id, nome, empresa, telefone, status, lead_score, rank
```

### get_leads_stats()

Retorna estatísticas agregadas em JSON.

**Output:**
```json
{
  "total_leads": 10,
  "por_status": {"novo": 2, "qualificado": 3, ...},
  "por_origem": {"instagram": 4, ...},
  "score_medio": 58.5,
  "valor_total_pipeline": 128000,
  "taxa_qualificacao": 70.0,
  "taxa_conversao": 10.0
}
```

---

## 📊 Views

### leads_with_last_message

```sql
SELECT
  l.*,
  last_message,
  last_message_at,
  total_messages
FROM leads l
```

### leads_qualificados

```sql
SELECT *
FROM leads
WHERE lead_score >= 60
  AND status IN ('qualificado', 'agendamento_marcado', 'ganho')
```

### pipeline_ativo

```sql
SELECT *
FROM leads
WHERE status NOT IN ('ganho', 'perdido')
ORDER BY lead_score DESC
```

---

## 🔄 Fluxo de Dados

### 1. Lead entra via WhatsApp

```
WhatsApp → Webhook → Backend
                        ↓
              INSERT INTO leads
              (status = 'novo')
                        ↓
              INSERT INTO conversation_messages
              (role = 'user', content = '...')
                        ↓
              🔥 TRIGGER: update_lead_on_new_message
                        ↓
              UPDATE leads.ultima_interacao
```

### 2. Agente qualifica o lead

```
Backend (LangGraph) → Qualification Node
                        ↓
              UPDATE leads SET:
                - qualification_data = {...}
                - lead_score = 85
                - status = 'qualificado'
                        ↓
              🔥 TRIGGER: update_updated_at
```

### 3. Gera ROI e envia PDF

```
Backend → ROI Generator
           ↓
    UPDATE leads SET:
      - roi_analysis = {...}
      - status = 'qualificado'
           ↓
    INSERT INTO conversation_messages
    (role = 'assistant', content = 'Enviei o PDF...')
           ↓
    🔥 TRIGGER: update_lead_on_new_message
```

### 4. Agenda reunião

```
Backend → Google Calendar API
           ↓
    UPDATE leads SET:
      - meeting_scheduled_at = '2024-12-28 14:00'
      - meeting_google_event_id = 'evt_abc123'
      - status = 'agendamento_marcado'
```

### 5. Lead é ganho

```
Backend → Manual/Automatic
           ↓
    UPDATE leads SET:
      - status = 'ganho'
      - won_at = NOW()
      - temperatura = 'quente'
```

---

## 📈 Exemplo de Query Flow

### Buscar leads qualificados com última mensagem

```sql
SELECT
  l.nome,
  l.empresa,
  l.lead_score,
  l.valor_estimado,
  (SELECT content
   FROM conversation_messages
   WHERE lead_id = l.id
   ORDER BY timestamp DESC
   LIMIT 1
  ) as ultima_mensagem
FROM leads l
WHERE l.status = 'qualificado'
  AND l.lead_score >= 60
ORDER BY l.lead_score DESC;
```

**Índices usados:**
- `idx_leads_status` (filtro)
- `idx_leads_lead_score` (ordenação)
- `idx_messages_lead_timestamp` (subquery)

---

## 🎯 Design Decisions

### Por que JSONB e não colunas separadas?

**qualification_data e roi_analysis são JSONB porque:**

✅ Flexibilidade - Dados podem evoluir sem migrations
✅ Performance - JSONB é indexável e rápido
✅ Integração fácil com Python/JavaScript
✅ Queries diretas: `qualification_data->>'budget'`

### Por que tabela separada para conversation_messages?

✅ Normalização - Uma conversa pode ter centenas de mensagens
✅ Performance - Queries em leads não carregam histórico todo
✅ Escalabilidade - Fácil adicionar índices/partições
✅ Auditoria - Histórico completo preservado

### Por que ENUMs?

✅ Validação - Banco garante valores válidos
✅ Performance - Mais eficiente que VARCHAR com CHECK
✅ Documentação - Schema é auto-documentado
✅ Integridade - Impossível inserir status inválido

---

**Schema otimizado para performance e escalabilidade! 🚀**
