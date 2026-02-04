# 🚀 Deploy Smith 2.0 - PRONTO PARA USAR!

## ✅ Código no GitHub
**Repositório**: https://github.com/Pedroax/smith-vendas-sistema

**Status**: Código enviado com sucesso! 207 arquivos, 54.910 linhas.

---

## 🎯 DEPLOY FRONTEND (Vercel) - 5 minutos

### Passo 1: Login na Vercel
1. Acesse: **https://vercel.com/signup**
2. Clique em **"Continue with GitHub"**
3. Faça login com sua conta GitHub

### Passo 2: Importar Projeto
1. No dashboard da Vercel, clique em **"Add New..."**
2. Selecione **"Project"**
3. Na lista de repositórios, procure por **"smith-vendas-sistema"**
4. Clique em **"Import"**

### Passo 3: Configurar Build
**IMPORTANTE**: Configure exatamente assim:

- **Framework Preset**: Next.js ✅ (detecta automaticamente)
- **Root Directory**: Digite `frontend` e clique em "Edit"
- **Build Command**: `npm run build` (automático)
- **Output Directory**: `.next` (automático)
- **Install Command**: `npm install` (automático)

### Passo 4: Variáveis de Ambiente
Clique em **"Environment Variables"** e adicione:

**Name**: `NEXT_PUBLIC_API_URL`
**Value**: `http://localhost:8000` (temporário - vamos atualizar depois)

### Passo 5: Deploy
1. Clique em **"Deploy"**
2. Aguarde 2-3 minutos ⏳
3. Quando terminar, você verá: **"Congratulations! 🎉"**
4. **COPIE A URL** (algo como: `https://smith-vendas-sistema.vercel.app`)

---

## 🚂 DEPLOY BACKEND (Railway) - 8 minutos

### Passo 1: Login no Railway
1. Acesse: **https://railway.app**
2. Clique em **"Login"**
3. Selecione **"Login with GitHub"**

### Passo 2: Criar Projeto
1. Clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Procure por **"smith-vendas-sistema"**
4. Clique em **"Deploy Now"**

### Passo 3: Aguardar Deploy Inicial
Aguarde ~2 minutos. Vai falhar inicialmente (é normal - falta configuração).

### Passo 4: Configurar Backend
1. Clique no card do projeto
2. Vá em **"Settings"** (ícone de engrenagem)
3. Role até **"Service"**
4. Em **"Root Directory"**, clique em "Configure" e digite: `backend`
5. Clique em "Update"

### Passo 5: Configurar Start Command
1. Ainda em "Settings"
2. Vá até **"Deploy"**
3. Em **"Custom Start Command"**, digite:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Salve

### Passo 6: Adicionar Variáveis de Ambiente

Vá em **"Variables"** e adicione UMA POR UMA (cole do seu arquivo .env):

```
APP_NAME=Smith 2.0
DEBUG=false
LOG_LEVEL=INFO

OPENAI_API_KEY=<sua_chave_openai>
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

EVOLUTION_API_URL=https://evolutionv2.dev.automatexia.com.br
EVOLUTION_API_KEY=<sua_chave_evolution>
EVOLUTION_INSTANCE_NAME=automatex

SUPABASE_URL=https://byseoksffurotygitfvy.supabase.co
SUPABASE_SERVICE_KEY=<sua_service_key>
SUPABASE_ANON_KEY=<sua_anon_key>
SUPABASE_DB_PASSWORD=<sua_senha_db>

JWT_SECRET_KEY=Ii_xKyvmvLXDzkv95tDRv3V-JCCDXhI8dOmZeNd2xzK9XKnhZvb2PI984NDpA8Uf71IQYbopWeBdBCL0xhaZ7Q
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

CORS_ORIGINS=http://localhost:3004
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

**⚠️ IMPORTANTE**: Substitua os valores `<sua_chave_...>` pelos valores reais do arquivo `.env`

### Passo 7: Verificar Deploy
1. Railway vai fazer redeploy automaticamente
2. Aguarde ~3-5 minutos
3. Vá em **"Deployments"** e veja se ficou verde ✅
4. Clique em **"Settings"** → **"Networking"**
5. Clique em **"Generate Domain"**
6. **COPIE A URL** (algo como: `smith-vendas-sistema-production.up.railway.app`)

---

## 🔗 CONECTAR FRONTEND E BACKEND

### Etapa 1: Atualizar Frontend com URL do Backend

1. Volte na **Vercel**
2. Vá no seu projeto → **"Settings"**
3. Clique em **"Environment Variables"**
4. Encontre `NEXT_PUBLIC_API_URL`
5. Clique em **"Edit"**
6. Mude o valor para: `https://SUA-URL-RAILWAY.up.railway.app` (URL que você copiou)
7. Marque **Production**, **Preview** e **Development**
8. Clique em **"Save"**
9. Vá em **"Deployments"**
10. No último deploy, clique nos **3 pontinhos** → **"Redeploy"** → **"Redeploy"**

### Etapa 2: Atualizar Backend com URL do Frontend

1. Volte no **Railway**
2. Vá em **"Variables"**
3. Encontre `CORS_ORIGINS`
4. Clique para editar
5. Mude o valor para: `https://SUA-URL-VERCEL.vercel.app` (URL que você copiou da Vercel)
6. Adicione também localhost: `https://SUA-URL-VERCEL.vercel.app,http://localhost:3004`
7. Salve (Railway redeploya automaticamente)

---

## ✅ TESTAR SISTEMA

### Teste 1: Backend funcionando
Abra no navegador:
```
https://SUA-URL-RAILWAY.up.railway.app/health
```

Deve retornar:
```json
{"status":"healthy"}
```

### Teste 2: Frontend + Login
1. Acesse: `https://SUA-URL-VERCEL.vercel.app`
2. Faça login:
   - **Email**: `pedro@automatex.com.br`
   - **Senha**: `Smith2026!`
3. Deve carregar o dashboard! 🎉

### Teste 3: PWA no Celular
1. Acesse a URL da Vercel no celular
2. Aguarde 30 segundos navegando
3. Banner "Instalar Smith Portal" deve aparecer
4. Clique em **"Instalar"**
5. App será adicionado à tela inicial! 📱

---

## 📋 Resumo das URLs

Anote aqui depois do deploy:

- **GitHub**: https://github.com/Pedroax/smith-vendas-sistema
- **Frontend (Vercel)**: https://_____.vercel.app
- **Backend (Railway)**: https://_____.up.railway.app

---

## 🐛 Se Algo Der Errado

### Backend não sobe no Railway
1. Vá em **"Deployments"** → clique no deploy
2. Veja os **logs** (tab "Deploy Logs")
3. Geralmente é variável de ambiente faltando ou com valor errado
4. Verifique se `Root Directory` está como `backend`
5. Verifique se o Start Command está correto

### Frontend dá erro 500
1. Vercel → **"Deployments"** → clique no deploy
2. Veja os **logs** (tab "Functions")
3. Geralmente é `NEXT_PUBLIC_API_URL` errada
4. Certifique que a URL do Railway está correta (com `https://`)

### Login não funciona
1. Verifique se `CORS_ORIGINS` no Railway tem a URL da Vercel
2. Abra DevTools (F12) → aba Console
3. Veja se tem erro de CORS
4. Se sim, adicione a URL correta no `CORS_ORIGINS`

### Upload não funciona
1. Verifique se executou o SQL de políticas RLS no Supabase
2. Vá em Supabase Dashboard → SQL Editor
3. Copie o conteúdo de `backend/storage_policies.sql`
4. Execute

---

## 💰 Custos

- **Vercel**: Gratuito (100GB/mês bandwidth)
- **Railway**: $5/mês após $5 de crédito gratuito
- **Supabase**: Gratuito (até 500MB DB)
- **GitHub**: Gratuito (repo privado)

**Total**: ~$5/mês após trial

---

## 🎯 Pronto!

Depois de seguir esses passos, seu sistema estará:
- ✅ Rodando 24/7 na nuvem
- ✅ Acessível de qualquer lugar
- ✅ Instalável como app no celular
- ✅ Com HTTPS seguro
- ✅ Escalável automaticamente

**Qualquer dúvida, me avise!** 🚀
