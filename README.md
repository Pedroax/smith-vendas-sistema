# 🤖 Smith 2.0 - Agente de Vendas Inteligente

**Agente de IA revolucionário para qualificação de leads e agendamento automático via WhatsApp**

## 🎯 Visão Geral

Smith 2.0 é um agente de vendas baseado em IA que:
- ✅ Atende leads do Instagram Ads 24/7 via WhatsApp
- ✅ Qualifica automaticamente com inteligência contextual
- ✅ Agenda reuniões direto no Google Calendar
- ✅ Gera propostas personalizadas em PDF
- ✅ Calcula ROI em tempo real
- ✅ Aprende e melhora continuamente

## 🏗️ Arquitetura

```
Instagram Ads → WhatsApp → Smith 2.0 (IA) → Qualificação → Agendamento
                              ↓
                      Dashboard (Monitoramento)
```

### Stack Técnica

**Backend (Python)**
- FastAPI - Framework web async
- LangGraph - State machine para IA
- OpenAI GPT-4o - Motor de IA
- Supabase - Banco de dados
- Redis - Cache e sessões
- Evolution API - Integração WhatsApp

**Frontend (Next.js 14)**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- Zustand - Estado global
- Supabase Realtime - Atualizações em tempo real

## 📦 Estrutura do Projeto

```
smith-vendas/
├── backend/          # API Python (FastAPI + LangGraph)
│   ├── app/
│   │   ├── agent/       # Smith Agent (LangGraph)
│   │   ├── services/    # WhatsApp, Calendar, etc
│   │   ├── models/      # Modelos de dados
│   │   ├── utils/       # Utilitários
│   │   └── api/         # Rotas da API
│   └── requirements.txt
│
├── frontend/         # Dashboard (Next.js 14)
│   ├── src/
│   │   ├── app/         # Páginas (App Router)
│   │   ├── components/  # Componentes React
│   │   ├── lib/         # Utilitários
│   │   └── types/       # TypeScript types
│   └── package.json
│
├── database/         # Schemas SQL
└── docs/            # Documentação

```

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- Conta Supabase
- Conta OpenAI
- Instância Evolution API

### Instalação

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # Configure suas variáveis
python -m app.main
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local  # Configure suas variáveis
npm run dev
```

## 🎯 Roadmap de Desenvolvimento

### ✅ Fase 1 - MVP (Semana 1-2)
- [x] Estrutura do projeto
- [ ] Integração WhatsApp (Evolution API)
- [ ] State Machine LangGraph (7 estados)
- [ ] Intelligent Controller
- [ ] Google Calendar
- [ ] Dashboard básico

### 🔄 Fase 2 - Inteligência (Semana 3)
- [ ] Sentiment Analysis
- [ ] Conversion Score (ML)
- [ ] ROI Calculator visual
- [ ] Geração de Proposta PDF
- [ ] Web Intelligence (Browserbase)
- [ ] Modo Copilot

### 🚀 Fase 3 - Otimizações (Semana 4+)
- [ ] Follow-up Preditivo
- [ ] Learning System
- [ ] Analytics avançado
- [ ] A/B Testing
- [ ] LinkedIn Intelligence

## 📄 Licença

Propriedade da AutomateX - Todos os direitos reservados

## 👨‍💻 Autor

Pedro Machado - AutomateX
https://automatexia.com.br
