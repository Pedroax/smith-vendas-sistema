# 🗄️ Database Setup - Smith 2.0

Instruções para configurar o banco de dados no Supabase.

---

## 📋 Arquivos SQL

| Arquivo | Descrição | Ordem |
|---------|-----------|-------|
| `01_create_tables.sql` | Cria tabelas, índices, triggers, funções | **1º** |
| `02_seed_data.sql` | Insere dados de exemplo (10 leads + conversas) | **2º** |

---

## 🚀 Como Executar no Supabase

### Passo 1: Acessar SQL Editor

1. Entre no [Supabase](https://supabase.com)
2. Abra seu projeto (ou crie um novo)
3. No menu lateral, clique em **SQL Editor**

### Passo 2: Executar Scripts

#### Script 1: Criar Schema

1. Clique em **New Query**
2. Copie todo o conteúdo de `01_create_tables.sql`
3. Cole no editor
4. Clique em **Run** (ou `Ctrl+Enter`)
5. Aguarde mensagem de sucesso ✅

**Output esperado:**
```
Schema criado com sucesso!
```

#### Script 2: Inserir Dados de Teste

1. Clique em **New Query** novamente
2. Copie todo o conteúdo de `02_seed_data.sql`
3. Cole no editor
4. Clique em **Run**
5. Aguarde mensagem de sucesso ✅

**Output esperado:**
```
✅ Dados de exemplo inseridos com sucesso!
Leads inseridos: 10
Mensagens inseridas: 23
```

### Passo 3: Verificar Tabelas

No menu lateral, clique em **Table Editor** e verifique:
- ✅ Tabela `leads` com 10 registros
- ✅ Tabela `conversation_messages` com 23 registros

---

## 📊 Estrutura do Banco

### Tabela: `leads`

**Colunas principais:**

```sql
id                        UUID (PK)
nome                      VARCHAR(255)
empresa                   VARCHAR(255)
telefone                  VARCHAR(50) UNIQUE
email                     VARCHAR(255)
status                    ENUM (novo, contato_inicial, qualificando, ...)
origem                    ENUM (instagram, whatsapp, site, ...)
temperatura               ENUM (quente, morno, frio)
lead_score                INTEGER (0-100)
qualification_data        JSONB
roi_analysis              JSONB
valor_estimado            DECIMAL(10,2)
meeting_scheduled_at      TIMESTAMPTZ
meeting_google_event_id   VARCHAR(255)
followup_config           JSONB
ultima_interacao          TIMESTAMPTZ
ultima_mensagem_ia        TEXT
notas                     TEXT
tags                      TEXT[]
ai_summary                TEXT
ai_next_action            VARCHAR(100)
requires_human_approval   BOOLEAN
created_at                TIMESTAMPTZ
updated_at                TIMESTAMPTZ
lost_at                   TIMESTAMPTZ
won_at                    TIMESTAMPTZ
```

### Tabela: `conversation_messages`

**Colunas:**

```sql
id          UUID (PK)
lead_id     UUID (FK → leads.id)
role        VARCHAR(20) ('user' | 'assistant')
content     TEXT
metadata    JSONB
timestamp   TIMESTAMPTZ
created_at  TIMESTAMPTZ
```

---

## 🔍 Índices Criados

Performance otimizada para queries comuns:

- `idx_leads_status` - Filtrar por status
- `idx_leads_origem` - Filtrar por origem
- `idx_leads_temperatura` - Filtrar por temperatura
- `idx_leads_telefone` - Busca por telefone (único)
- `idx_leads_created_at` - Ordenação por data
- `idx_leads_lead_score` - Ordenação por score
- `idx_leads_tags` - Busca em tags (GIN)
- `idx_leads_search` - Busca full-text em nome/empresa
- `idx_messages_lead_id` - Buscar mensagens de um lead
- `idx_messages_timestamp` - Ordenação de mensagens

---

## ⚙️ Triggers Automáticos

### 1. **Atualizar `updated_at`**

Sempre que um lead é atualizado, `updated_at` é automaticamente setado para `NOW()`.

```sql
CREATE TRIGGER update_leads_updated_at
  BEFORE UPDATE ON leads
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

### 2. **Atualizar `ultima_interacao`**

Quando uma nova mensagem é inserida, atualiza automaticamente:
- `ultima_interacao` do lead
- `ultima_mensagem_ia` (se mensagem for do assistant)

```sql
CREATE TRIGGER update_lead_on_new_message
  AFTER INSERT ON conversation_messages
  FOR EACH ROW
  EXECUTE FUNCTION update_lead_ultima_interacao();
```

---

## 🛠️ Funções Úteis

### 1. **Buscar Leads por Texto**

Busca full-text em nome e empresa (português):

```sql
SELECT * FROM search_leads('tech');
```

**Retorna:** Leads que contêm "tech" ordenados por relevância.

### 2. **Estatísticas Agregadas**

Retorna JSON com todas as estatísticas:

```sql
SELECT get_leads_stats();
```

**Retorna:**
```json
{
  "total_leads": 10,
  "por_status": {
    "novo": 2,
    "qualificado": 3,
    "ganho": 1,
    ...
  },
  "por_origem": {
    "instagram": 4,
    "whatsapp": 2,
    ...
  },
  "score_medio": 58.5,
  "valor_total_pipeline": 128000,
  "taxa_qualificacao": 70.0,
  "taxa_conversao": 10.0
}
```

---

## 📌 Views Criadas

### 1. **`leads_with_last_message`**

Leads com última mensagem e contagem total:

```sql
SELECT * FROM leads_with_last_message;
```

**Colunas extras:**
- `last_message` - Conteúdo da última mensagem
- `last_message_at` - Timestamp da última mensagem
- `total_messages` - Total de mensagens na conversa

### 2. **`leads_qualificados`**

Somente leads qualificados (score >= 60):

```sql
SELECT * FROM leads_qualificados;
```

### 3. **`pipeline_ativo`**

Leads ativos (excluindo ganhos e perdidos):

```sql
SELECT * FROM pipeline_ativo;
```

---

## 🔐 Permissões (RLS)

Row Level Security está **desabilitado** por padrão para desenvolvimento.

Para habilitar em produção, descomente no `01_create_tables.sql`:

```sql
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários podem ver todos os leads"
  ON leads FOR SELECT
  USING (auth.role() = 'authenticated');
```

---

## 🧪 Dados de Teste Inseridos

### Leads de Exemplo:

1. **João Silva** (Tech Solutions) - Qualificado, Score 85, VIP
2. **Maria Costa** (Marketing Pro) - Novo, acabou de entrar
3. **Pedro Santos** (E-commerce Plus) - Contato inicial
4. **Ana Oliveira** (Clínica Saúde+) - Qualificando
5. **Carlos Mendes** (Indústria ABC) - Agendamento marcado, Score 90
6. **Fernanda Lima** (Consultoria FGL) - **Ganho** (fechado!)
7. **Roberto Alves** (Startup XYZ) - **Perdido** (não qualificado)
8. **Juliana Ferreira** (Imobiliária Prime) - Qualificado, Score 78
9. **Ricardo Gomes** (Tech Startup) - Novo recente
10. **Patrícia Souza** (Escola ABC) - Qualificando

### Conversas:

- Lead 1 (João): Conversa completa de qualificação até envio de ROI
- Lead 2 (Maria): Primeira mensagem apenas
- Lead 3 (Pedro): Início de qualificação
- Lead 5 (Carlos): Conversa até agendamento confirmado

---

## 🔗 Conectar ao Backend

Após criar o banco, configure as credenciais no backend:

### 1. Pegar credenciais do Supabase

No Supabase:
1. Vá em **Settings** → **Database**
2. Copie as informações de conexão

### 2. Configurar `.env` do backend

```bash
# backend/.env

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-anon-key-aqui
SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key-aqui

# Database URL (PostgreSQL)
DATABASE_URL=postgresql://postgres:senha@db.seu-projeto.supabase.co:5432/postgres
```

### 3. Testar conexão

```bash
cd backend
python -c "from app.database import supabase; print(supabase.table('leads').select('*').execute())"
```

Se retornar os 10 leads, está funcionando! ✅

---

## 🐛 Troubleshooting

### Erro: "permission denied for table leads"

**Solução:** Execute os GRANTS no final do `01_create_tables.sql`:

```sql
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
```

### Erro: "relation leads already exists"

**Solução:** Tabelas já existem. Para recriar:

```sql
DROP TABLE IF EXISTS conversation_messages CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
-- Depois execute 01_create_tables.sql novamente
```

### Erro: "duplicate key value violates unique constraint"

**Solução:** IDs dos leads de teste já existem. Execute:

```sql
TRUNCATE conversation_messages CASCADE;
TRUNCATE leads CASCADE;
-- Depois execute 02_seed_data.sql novamente
```

---

## 📈 Próximos Passos

Após configurar o banco:

1. ✅ Criar tabelas e índices (`01_create_tables.sql`)
2. ✅ Inserir dados de teste (`02_seed_data.sql`)
3. 🔄 Configurar backend com credenciais Supabase
4. 🔄 Testar API endpoints com dados reais
5. 🔄 Conectar frontend ao backend
6. 🔄 Testar fluxo completo end-to-end

---

## 📝 Notas Importantes

- **Dados de teste:** Os dados inseridos são apenas para desenvolvimento. Apague antes de produção.
- **Backup:** Sempre faça backup antes de executar scripts em produção.
- **RLS:** Em produção, habilite Row Level Security para multi-tenant.
- **Índices:** Os índices foram otimizados para queries comuns. Ajuste conforme seu uso.

---

**Database configurado e pronto para uso! 🎉**
