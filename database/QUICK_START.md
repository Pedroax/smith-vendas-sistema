# ⚡ Quick Start - Configurar Banco de Dados

**Tempo estimado:** 5 minutos

---

## 🎯 Checklist

- [ ] Executar `01_create_tables.sql` no Supabase
- [ ] Executar `02_seed_data.sql` no Supabase
- [ ] Copiar credenciais do Supabase
- [ ] Configurar `backend/.env`
- [ ] Testar conexão

---

## 📝 Passo a Passo

### 1️⃣ Criar Projeto no Supabase

1. Acesse: https://supabase.com
2. Clique em **"New Project"**
3. Preencha:
   - **Name:** `smith-vendas` (ou qualquer nome)
   - **Database Password:** Escolha uma senha forte
   - **Region:** `South America (São Paulo)` (mais próximo)
4. Clique em **"Create new project"**
5. ⏳ Aguarde ~2 minutos enquanto provisiona

---

### 2️⃣ Executar Script de Criação

1. No menu lateral, clique em **SQL Editor**
2. Clique em **"+ New query"**
3. Abra o arquivo `01_create_tables.sql` deste diretório
4. **Copie TODO o conteúdo**
5. **Cole** no editor do Supabase
6. Clique em **"Run"** (ou pressione `Ctrl+Enter`)
7. Aguarde a execução (~10 segundos)
8. Verifique se apareceu: ✅ **"Schema criado com sucesso!"**

---

### 3️⃣ Inserir Dados de Teste

1. Clique em **"+ New query"** novamente
2. Abra o arquivo `02_seed_data.sql`
3. **Copie TODO o conteúdo**
4. **Cole** no editor do Supabase
5. Clique em **"Run"**
6. Aguarde a execução (~5 segundos)
7. Verifique se apareceu: ✅ **"Dados de exemplo inseridos com sucesso!"**

---

### 4️⃣ Verificar Tabelas

1. No menu lateral, clique em **Table Editor**
2. Verifique se existem as tabelas:
   - ✅ `leads` (10 registros)
   - ✅ `conversation_messages` (23 registros)
3. Clique em `leads` e visualize os dados

---

### 5️⃣ Copiar Credenciais

1. No menu lateral, clique em **Settings** (engrenagem)
2. Clique em **API**
3. Copie as seguintes informações:

**Project URL:**
```
https://seu-projeto-id.supabase.co
```

**API Keys → anon / public:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**API Keys → service_role (clique em "Reveal"):**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

4. Clique em **Database** (no menu de Settings)
5. Role até **Connection string**
6. Selecione **"URI"** e copie:

```
postgresql://postgres.seu-projeto:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
```

⚠️ **Importante:** Substitua `[SUA-SENHA]` pela senha que você criou no Passo 1.

---

### 6️⃣ Configurar Backend

1. Abra o arquivo `backend/.env` (crie se não existir)
2. Cole as credenciais:

```bash
# ===================================
# SUPABASE
# ===================================

SUPABASE_URL=https://seu-projeto-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ===================================
# DATABASE
# ===================================

DATABASE_URL=postgresql://postgres.seu-projeto:SUA-SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres

# ===================================
# OPENAI (já deve estar configurado)
# ===================================

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
```

3. Salve o arquivo

---

### 7️⃣ Testar Conexão

#### Opção 1: Python direto

```bash
cd backend
python
```

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

# Testar query
result = supabase.table("leads").select("*").limit(5).execute()
print(f"✅ Sucesso! {len(result.data)} leads encontrados")
print(result.data[0]['nome'])  # Deve mostrar "João Silva"
```

Se funcionar, você verá:
```
✅ Sucesso! 5 leads encontrados
João Silva
```

#### Opção 2: Via API

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Abra: http://localhost:8000/api/leads

Deve retornar JSON com os 10 leads.

---

## ✅ Pronto!

Agora você tem:

- ✅ Banco de dados PostgreSQL no Supabase
- ✅ Tabelas `leads` e `conversation_messages` criadas
- ✅ 10 leads de exemplo + 23 mensagens
- ✅ Índices otimizados
- ✅ Triggers automáticos
- ✅ Funções úteis (search, stats)
- ✅ Backend conectado ao banco

---

## 🔧 Próximos Passos

Agora que o banco está configurado:

1. **Atualizar Backend:**
   - Substituir `LEADS_DB` (dict in-memory) por queries Supabase
   - Criar `database.py` com client Supabase
   - Criar `repository/leads_repository.py` para queries

2. **Testar Frontend:**
   - Iniciar backend: `cd backend && uvicorn app.main:app --reload`
   - Iniciar frontend: `cd frontend && npm run dev`
   - Abrir: http://localhost:3000
   - Verificar se os 10 leads aparecem no Kanban

3. **Implementar Features:**
   - Webhook WhatsApp real
   - Google Calendar OAuth
   - Follow-ups automáticos

---

## 🆘 Problemas Comuns

### ❌ "permission denied for table leads"

**Solução:** Volte ao SQL Editor e execute:

```sql
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
```

### ❌ "relation leads does not exist"

**Solução:** Você pulou o Passo 2. Execute `01_create_tables.sql`.

### ❌ "duplicate key value violates unique constraint"

**Solução:** Dados de teste já existem. Execute:

```sql
TRUNCATE conversation_messages CASCADE;
TRUNCATE leads CASCADE;
```

Depois execute `02_seed_data.sql` novamente.

### ❌ Backend não conecta ao Supabase

**Verifique:**
1. `.env` está no diretório correto (`backend/.env`)
2. URL e keys estão corretas (sem espaços extras)
3. Senha do DATABASE_URL está correta

**Teste:**
```python
print(os.getenv("SUPABASE_URL"))  # Deve mostrar a URL
```

---

## 📚 Arquivos de Referência

- `01_create_tables.sql` - Schema completo
- `02_seed_data.sql` - Dados de exemplo
- `03_useful_queries.sql` - Queries úteis para administração
- `README.md` - Documentação completa
- `QUICK_START.md` - Este arquivo

---

**Banco configurado e pronto para uso! 🚀**
