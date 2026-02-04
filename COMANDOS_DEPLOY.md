# Comandos para Deploy - Smith 2.0

## ✅ Git Commit já feito!

207 arquivos commitados com sucesso.

---

## 📦 PASSO 1: Criar Repositório no GitHub

1. **Acesse**: https://github.com/new

2. **Preencha**:
   - Repository name: `smith-vendas`
   - Description: `Smith 2.0 - Sistema de vendas com IA`
   - Visibility: **Private** (recomendado)
   - ❌ **NÃO** marque "Initialize with README"

3. **Clique em** "Create repository"

4. **Copie a URL** que aparecerá (algo como: `https://github.com/SEU-USUARIO/smith-vendas.git`)

---

## 📤 PASSO 2: Fazer Push para GitHub

Execute estes comandos no terminal:

```bash
cd c:\Users\pedro\Desktop\smith-vendas

# Adicionar remote (SUBSTITUA SEU-USUARIO pelo seu usuário do GitHub)
git remote add origin https://github.com/SEU-USUARIO/smith-vendas.git

# Fazer push
git push -u origin master
```

**Pronto!** Código está no GitHub.

---

## 🚀 PASSO 3: Deploy do Frontend na Vercel

### 3.1 Criar conta/Login
1. Acesse: https://vercel.com/signup
2. Clique em "Continue with GitHub"
3. Faça login com sua conta GitHub

### 3.2 Importar Projeto
1. Na dashboard da Vercel, clique em **"Add New..."** → **"Project"**
2. Procure pelo repositório `smith-vendas`
3. Clique em **"Import"**

### 3.3 Configurar Build
**Root Directory**: Digite `frontend` (IMPORTANTE!)

As configurações devem aparecer automaticamente:
- Framework Preset: `Next.js`
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

### 3.4 Adicionar Variáveis de Ambiente

Clique em "Environment Variables" e adicione:

**Nome**: `NEXT_PUBLIC_API_URL`
**Valor**: `http://localhost:8000` (temporário - vamos atualizar depois)

### 3.5 Deploy
1. Clique em **"Deploy"**
2. Aguarde ~2-3 minutos
3. **Copie a URL** que aparecer (ex: `https://smith-vendas.vercel.app`)

---

## 🚂 PASSO 4: Deploy do Backend no Railway

### 4.1 Criar conta
1. Acesse: https://railway.app
2. Clique em "Login"
3. Escolha "Login with GitHub"

### 4.2 Novo Projeto
1. Clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Escolha o repositório `smith-vendas`
4. Clique em **"Deploy Now"**

### 4.3 Configurar Backend
1. Depois que deployar, clique no projeto
2. Vá em **"Settings"**
3. Em **"Service"** → **"Root Directory"**, digite: `backend`
4. Em **"Deploy"**:
   - **Build Command**: deixe vazio
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4.4 Adicionar TODAS as Variáveis de Ambiente

Vá em **"Variables"** e adicione uma por uma:

```env
APP_NAME=Smith 2.0
DEBUG=false
LOG_LEVEL=INFO

OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

EVOLUTION_API_URL=https://evolutionv2.dev.automatexia.com.br
EVOLUTION_API_KEY=sua_chave_aqui
EVOLUTION_INSTANCE_NAME=automatex

SUPABASE_URL=https://byseoksffurotygitfvy.supabase.co
SUPABASE_SERVICE_KEY=sua_chave_service
SUPABASE_ANON_KEY=sua_chave_anon
SUPABASE_DB_PASSWORD=sua_senha

JWT_SECRET_KEY=Ii_xKyvmvLXDzkv95tDRv3V-JCCDXhI8dOmZeNd2xzK9XKnhZvb2PI984NDpA8Uf71IQYbopWeBdBCL0xhaZ7Q
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

CORS_ORIGINS=https://smith-vendas.vercel.app
ADMIN_EMAIL=pedro@automatex.com.br
ADMIN_PASSWORD=Smith2026!

NOTIFICATION_WHATSAPP_ENABLED=true
NOTIFICATION_WHATSAPP_NUMBER=5561998112622
NOTIFICATION_EMAIL_ENABLED=false

GOOGLE_CALENDAR_ID=pedrohfmachado0194@gmail.com
CALENDAR_TIMEZONE=America/Sao_Paulo
CALENDAR_WORK_START_HOUR=09:00
CALENDAR_WORK_END_HOUR=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5
CALENDAR_MEETING_DURATION=60

REDIS_ENABLED=false
DEBOUNCE_SECONDS=5.0
MAX_MESSAGE_LENGTH=2000
DEFAULT_TIMEZONE=America/Sao_Paulo
AUTO_APPROVE_THRESHOLD=80
REVIEW_THRESHOLD=50
```

**IMPORTANTE**: Substitua os valores com as chaves reais do arquivo `.env`

### 4.5 Verificar Deploy
1. Aguarde ~3-5 minutos
2. Railway mostrará uma URL (ex: `https://smith-vendas-production.up.railway.app`)
3. **Copie essa URL**

---

## 🔄 PASSO 5: Atualizar URLs Cruzadas

### 5.1 Atualizar Frontend com URL do Backend
1. Volte na **Vercel**
2. Vá em **"Settings"** → **"Environment Variables"**
3. Edite `NEXT_PUBLIC_API_URL`
4. Mude para a URL do Railway (ex: `https://smith-vendas-production.up.railway.app`)
5. Clique em **"Save"**
6. Vá em **"Deployments"**
7. Clique nos 3 pontinhos no último deploy → **"Redeploy"**

### 5.2 Atualizar Backend com URL do Frontend
1. Volte no **Railway**
2. Vá em **"Variables"**
3. Edite a variável `CORS_ORIGINS`
4. Mude para a URL da Vercel (ex: `https://smith-vendas.vercel.app`)
5. Salve (o Railway redeploya automaticamente)

---

## ✅ PASSO 6: Testar

### 6.1 Testar Backend
Abra no navegador:
```
https://SUA-URL-RAILWAY.up.railway.app/health
```

Deve retornar: `{"status":"healthy"}`

### 6.2 Testar Frontend
1. Acesse a URL da Vercel
2. Faça login:
   - Email: `pedro@automatex.com.br`
   - Senha: `Smith2026!`
3. Deve carregar o dashboard!

### 6.3 Testar PWA no Celular
1. Acesse a URL da Vercel no celular
2. Aguarde 30 segundos
3. Banner de instalação deve aparecer
4. Instale o app!

---

## 🎯 Resumo das URLs

Depois do deploy, você terá:

- **Frontend**: `https://smith-vendas.vercel.app`
- **Backend**: `https://smith-vendas-production.up.railway.app`
- **GitHub**: `https://github.com/SEU-USUARIO/smith-vendas`

---

## 🐛 Se algo der errado

### Backend não sobe:
1. Railway → Aba "Deployments" → Clique no deploy
2. Veja os logs
3. Geralmente é variável de ambiente faltando

### Frontend não conecta ao backend:
1. Verificar se `NEXT_PUBLIC_API_URL` está correto
2. Verificar se `CORS_ORIGINS` no backend inclui a URL do frontend
3. Fazer redeploy do frontend

### Upload não funciona:
1. Verificar se executou o SQL de políticas RLS no Supabase
2. Verificar se as credenciais do Supabase estão corretas

---

## 🎉 Pronto!

Seu sistema estará rodando 24/7 na nuvem, acessível de qualquer lugar!

**Custos**:
- Vercel: Gratuito (até 100GB bandwidth)
- Railway: $5/mês após trial gratuito
- Supabase: Gratuito (até 500MB DB)
