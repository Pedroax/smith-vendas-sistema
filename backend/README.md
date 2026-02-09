# Smith 2.0 - Sistema de Automação de Vendas com IA

Sistema completo de automação de vendas com IA que:
- Recebe leads do Facebook Lead Ads
- Qualifica automaticamente com IA (OpenAI GPT-4)
- Insere leads qualificados no CRM
- Envia mensagens automáticas via WhatsApp
- Agenda reuniões no Google Calendar
- Processa mensagens de texto e áudio (Whisper)

## 🚀 Deploy na Vercel

### Pré-requisitos
- Conta Vercel
- Conta Supabase (PostgreSQL)
- API OpenAI
- Evolution API (WhatsApp)
- Google Calendar API

### Passos

1. **Fork/Clone este repositório**

2. **Configure as variáveis de ambiente na Vercel:**
   - Vá em Settings → Environment Variables
   - Adicione todas as variáveis do arquivo `.env.example`

3. **Deploy:**
   - Conecte seu repositório GitHub na Vercel
   - A Vercel vai detectar automaticamente como FastAPI
   - Deploy será automático

4. **Configure o Webhook do Facebook:**
   - Após deploy, copie a URL da Vercel (ex: `https://seu-app.vercel.app`)
   - No Facebook Developer:
     - Vá em Webhooks
     - Configure: `https://seu-app.vercel.app/webhook/facebook`
     - Verify Token: `smith_webhook_2026`
     - Subscribe: `leadgen`

## 📋 Variáveis de Ambiente Necessárias

Veja `.env.example` para lista completa.

**Críticas:**
- `OPENAI_API_KEY`
- `EVOLUTION_API_URL` e `EVOLUTION_API_KEY`
- `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`
- `FACEBOOK_APP_SECRET` (para segurança)
- `GOOGLE_CREDENTIALS_PATH` e credenciais

## 🔧 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env com suas chaves

# Rodar servidor
uvicorn app.main:app --reload --port 8000
```

## 📱 Funcionalidades

### 1. Recebimento de Leads (Facebook)
- Webhook `/webhook/facebook` recebe leads
- Qualificação automática com IA
- Score de 0-100 baseado em BANT

### 2. Qualificação Inteligente
- Analisa faturamento, cargo, urgência
- Só leads qualificados entram no CRM
- Notificações automáticas

### 3. WhatsApp Automático
- Mensagens via Evolution API
- Suporte a texto e áudio (Whisper)
- Agendamento de reuniões

### 4. Google Calendar
- Busca horários disponíveis
- Cria eventos automaticamente
- Envia convites por email

## 🗂️ Estrutura do Projeto

```
backend/
├── app/
│   ├── api/              # Endpoints (webhooks, leads, etc)
│   ├── models/           # Modelos Pydantic
│   ├── repository/       # Acesso ao banco de dados
│   ├── services/         # Lógica de negócio
│   └── main.py          # FastAPI app
├── .env.example         # Template de configuração
├── requirements.txt     # Dependências Python
└── README.md           # Este arquivo
```

## 🛠️ Stack Tecnológica

- **Backend:** FastAPI + Python 3.14
- **IA:** OpenAI GPT-4 + Whisper
- **Banco:** Supabase (PostgreSQL)
- **WhatsApp:** Evolution API
- **Deploy:** Vercel
- **Agenda:** Google Calendar API

## 📞 Suporte

Para dúvidas, abra uma issue no GitHub.
# Railway deploy fix
