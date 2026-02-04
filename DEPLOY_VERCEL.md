# Deploy na Vercel - Smith 2.0

## Passo 1: Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. Nome do repositório: `smith-vendas`
3. Visibilidade: **Private**
4. NÃO marque "Initialize with README"
5. Clique em "Create repository"

## Passo 2: Fazer Push do Código

Depois de criar o repositório, execute:

```bash
cd c:\Users\pedro\Desktop\smith-vendas

# Inicializar git (se ainda não foi)
git init

# Adicionar remote (substitua USERNAME pelo seu usuário do GitHub)
git remote add origin https://github.com/USERNAME/smith-vendas.git

# Adicionar todos os arquivos
git add .

# Commit
git commit -m "Initial commit - Smith 2.0 production ready"

# Push
git push -u origin main
```

## Passo 3: Deploy Frontend na Vercel

### 3.1 Criar conta/Login
1. Acesse: https://vercel.com/signup
2. Faça login com GitHub

### 3.2 Importar Projeto
1. Clique em "Add New..." > "Project"
2. Selecione o repositório `smith-vendas`
3. Clique em "Import"

### 3.3 Configurar Projeto
**Root Directory**: `frontend`

**Build Settings** (deve detectar automaticamente):
- Framework Preset: `Next.js`
- Build Command: `npm run build`
- Output Directory: `.next`

### 3.4 Variáveis de Ambiente

Adicione as seguintes variáveis:

```
NEXT_PUBLIC_API_URL=https://seu-backend.railway.app
```

*Nota: A URL do backend você vai obter no Passo 4*

### 3.5 Deploy
Clique em "Deploy" e aguarde ~2 minutos

## Passo 4: Deploy Backend no Railway

### 4.1 Criar conta
1. Acesse: https://railway.app/
2. Faça login com GitHub

### 4.2 Novo Projeto
1. Clique em "New Project"
2. Selecione "Deploy from GitHub repo"
3. Escolha `smith-vendas`
4. Clique em "Deploy Now"

### 4.3 Configurar
1. Vá em "Settings"
2. **Root Directory**: `/backend`
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Build Command**: `pip install -r requirements.txt`

### 4.4 Variáveis de Ambiente

Adicione TODAS estas variáveis (copie do .env):

```env
# Aplicação
APP_NAME=Smith 2.0
DEBUG=false
LOG_LEVEL=INFO
PORT=8000

# OpenAI
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

# Evolution API
EVOLUTION_API_URL=https://evolutionv2.dev.automatexia.com.br
EVOLUTION_API_KEY=sua_chave
EVOLUTION_INSTANCE_NAME=automatex

# Supabase
SUPABASE_URL=https://byseoksffurotygitfvy.supabase.co
SUPABASE_SERVICE_KEY=sua_chave_service
SUPABASE_ANON_KEY=sua_chave_anon
SUPABASE_DB_PASSWORD=sua_senha

# JWT (IMPORTANTE: use o secret forte gerado)
JWT_SECRET_KEY=Ii_xKyvmvLXDzkv95tDRv3V-JCCDXhI8dOmZeNd2xzK9XKnhZvb2PI984NDpA8Uf71IQYbopWeBdBCL0xhaZ7Q
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS (ATUALIZAR com URL do frontend da Vercel)
CORS_ORIGINS=https://seu-frontend.vercel.app

# Admin
ADMIN_EMAIL=pedro@automatex.com.br
ADMIN_PASSWORD=Smith2026!

# Notificações
NOTIFICATION_WHATSAPP_ENABLED=true
NOTIFICATION_WHATSAPP_NUMBER=5561998112622
NOTIFICATION_EMAIL_ENABLED=false

# Google Calendar
GOOGLE_CALENDAR_ID=pedrohfmachado0194@gmail.com
CALENDAR_TIMEZONE=America/Sao_Paulo
CALENDAR_WORK_START_HOUR=09:00
CALENDAR_WORK_END_HOUR=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5
CALENDAR_MEETING_DURATION=60

# Redis (opcional)
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=false

# Configurações
DEBOUNCE_SECONDS=5.0
MAX_MESSAGE_LENGTH=2000
DEFAULT_TIMEZONE=America/Sao_Paulo
AUTO_APPROVE_THRESHOLD=80
REVIEW_THRESHOLD=50
NUMERO_PEDRO=5521999999999

# Facebook (opcional)
FACEBOOK_VERIFY_TOKEN=smith_webhook_2026
FACEBOOK_APP_SECRET=
FACEBOOK_ACCESS_TOKEN=
```

### 4.5 Deploy
Railway vai fazer deploy automático. Aguarde ~3 minutos.

## Passo 5: Atualizar URLs Cruzadas

### 5.1 Após backend fazer deploy no Railway:
1. Copie a URL do backend (ex: `https://smith-vendas-production.up.railway.app`)
2. Volte na Vercel (frontend)
3. Vá em "Settings" > "Environment Variables"
4. Atualize `NEXT_PUBLIC_API_URL` com a URL do Railway
5. Faça "Redeploy" do frontend

### 5.2 Atualizar CORS no Railway:
1. Copie a URL do frontend (ex: `https://smith-portal.vercel.app`)
2. No Railway, atualize a variável `CORS_ORIGINS`
3. Faça redeploy

## Passo 6: Testar em Produção

### 6.1 Verificar Backend
```bash
curl https://seu-backend.railway.app/health
```

Deve retornar: `{"status":"healthy"}`

### 6.2 Testar Frontend
1. Acesse a URL da Vercel
2. Faça login: `pedro@automatex.com.br` / `Smith2026!`
3. Verifique se dashboard carrega

### 6.3 Testar PWA no Celular
1. Acesse a URL no celular
2. Aguarde 30s
3. Banner de instalação deve aparecer
4. Instale o app

## Passo 7: Configurar Domínio (Opcional)

### Frontend (Vercel)
1. Vá em "Settings" > "Domains"
2. Adicione seu domínio (ex: `portal.automatex.com.br`)
3. Configure DNS conforme instruções

### Backend (Railway)
1. Vá em "Settings" > "Domains"
2. Adicione domínio (ex: `api.automatex.com.br`)
3. Configure DNS

## 🎯 Checklist Final

- [ ] Código no GitHub
- [ ] Frontend na Vercel
- [ ] Backend no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] URLs cruzadas atualizadas
- [ ] Login funcionando
- [ ] PWA instalável no celular
- [ ] Upload de arquivos funcionando

## 🐛 Troubleshooting

### Erro: "Failed to fetch"
- Verificar CORS no backend
- Verificar NEXT_PUBLIC_API_URL no frontend

### Erro 500 no backend
- Verificar logs no Railway
- Verificar variáveis de ambiente

### PWA não instala
- Certificar que está usando HTTPS
- Verificar se manifest.json está acessível
- Limpar cache do navegador

## 📞 Suporte

Se algo der errado, verifique:
1. Logs do Railway: `railway logs`
2. Logs da Vercel: Na dashboard, aba "Logs"
3. Console do navegador (F12)

---

✨ **Depois do deploy, seu sistema estará rodando 24/7 na nuvem!**
