# 🚀 Getting Started - Smith 2.0

## ✅ Parte 1: Estrutura Base CRIADA!

A estrutura do projeto está completa:
- ✅ Backend (Python/FastAPI/LangGraph)
- ✅ Frontend (Next.js 14/TypeScript/Tailwind)
- ✅ Configurações de ambiente
- ✅ Arquivos base

---

## 🧪 TESTE 1: Verificar Instalação do Backend

### Passo 1: Criar ambiente virtual Python

```bash
cd backend
python -m venv venv
```

### Passo 2: Ativar ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Passo 3: Instalar dependências

```bash
pip install -r requirements.txt
```

**Tempo estimado:** 2-3 minutos

### Passo 4: Criar arquivo .env

```bash
cp .env.example .env
```

**IMPORTANTE:** Edite o arquivo `.env` e configure ao menos:
- `OPENAI_API_KEY` - Sua chave da OpenAI
- `EVOLUTION_API_URL` - URL da Evolution API
- `EVOLUTION_API_KEY` - Chave da Evolution API
- `SUPABASE_URL` - URL do Supabase
- `SUPABASE_SERVICE_KEY` - Service key do Supabase
- `NUMERO_PEDRO` - Seu número de WhatsApp
- `JWT_SECRET_KEY` - Uma string secreta qualquer

### Passo 5: Testar backend (SEM configurar tudo ainda)

**ATENÇÃO:** O backend vai dar erro de validação se não configurar as variáveis.
Mas isso é esperado! Vamos testar apenas se o Python funciona:

```bash
python -c "from app.config import settings; print('✅ Imports OK')"
```

Se funcionar, você verá: `✅ Imports OK`

---

## 🧪 TESTE 2: Verificar Instalação do Frontend

### Passo 1: Instalar dependências

```bash
cd frontend
npm install
```

**Tempo estimado:** 3-5 minutos

### Passo 2: Criar arquivo .env.local

```bash
cp .env.local.example .env.local
```

Edite e configure:
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `NEXT_PUBLIC_SUPABASE_URL` - URL do Supabase
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Anon key do Supabase

### Passo 3: Rodar servidor de desenvolvimento

```bash
npm run dev
```

Abra: http://localhost:3000

**Você deve ver:** Tela roxa bonita com "🤖 Smith 2.0"

---

## ✅ Se chegou aqui: PARABÉNS!

A estrutura base está **100% funcional**!

Próximos passos:
1. ⏳ Integração WhatsApp (Evolution API)
2. ⏳ State Machine LangGraph
3. ⏳ Intelligent Controller
4. ⏳ Google Calendar
5. ⏳ Dashboard completo

---

## 🆘 Problemas Comuns

### Backend não inicia

**Erro:** `ValidationError: OPENAI_API_KEY não configurada`
**Solução:** Configure o arquivo `.env` com suas chaves reais

### Frontend não inicia

**Erro:** `Module not found`
**Solução:** Rode `npm install` novamente

### Porta já em uso

**Backend (porta 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (porta 3000):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

---

## 📝 Próximo Checkpoint

Quando terminar os testes acima, me confirme:
- [ ] Backend instalou sem erros
- [ ] Frontend rodando em localhost:3000
- [ ] Consegue ver a tela roxa do Smith 2.0

Aí vamos para a **Parte 2: Integração WhatsApp**! 🚀
