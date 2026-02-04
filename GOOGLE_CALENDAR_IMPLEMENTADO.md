# ✅ Google Calendar Integrado ao Smith!

## O que foi implementado:

### 1. Integração com Google Calendar API ✅
- Serviço completo para criar reuniões automaticamente
- Criação de eventos com Google Meet integrado
- Envio automático de convites por email
- Lembretes configurados (24h, 1h, 10min antes)

### 2. Modelo de Agendamento no Banco ✅
- Tabela `agendamentos` criada (SQL migration em `backend/migrations/003_create_agendamentos.sql`)
- Model Pydantic completo
- Repository para gerenciar agendamentos

### 3. Smith Modificado ✅
- **ANTES:** Enviava link do Calendly
- **AGORA:** Coleta disponibilidade do lead e agenda DIRETO no Google Calendar

### 4. Processamento Inteligente de Horários ✅
- Extrai data/hora de mensagens naturais ("terça 14h", "amanhã 10h")
- Valida horário comercial (9h-18h, dias úteis)
- Sugere horários alternativos se inválido

## Novo Fluxo:

```
Lead qualificado
  ↓
Smith: "Que dia e horário funciona melhor? (Ex: terça 14h, quinta 10h...)"
  ↓
Lead: "Quinta 14h"
  ↓
Sistema extrai data/hora automaticamente
  ↓
Cria evento no Google Calendar
  ↓
Salva agendamento no banco
  ↓
Smith: "Agendado! Quinta-feira, 02/01 às 14h 📅
Você vai receber um email com o convite do Google Calendar + link do Meet.
Te vejo lá! 🚀"
  ↓
Lead recebe email automaticamente com:
- Convite do Google Calendar
- Link do Google Meet
- Lembretes configurados
```

## Próximos passos para VOCÊ:

### Passo 1: Executar Migration SQL no Supabase

1. Acesse seu painel do Supabase: https://supabase.com/dashboard
2. Vá em **SQL Editor**
3. Clique em **New Query**
4. Cole o conteúdo do arquivo: `backend/migrations/003_create_agendamentos.sql`
5. Clique em **Run** (ou F5)
6. Verifique se a tabela `agendamentos` foi criada em **Table Editor**

### Passo 2: Configurar Google Calendar API

Siga o guia completo em: [`SETUP_GOOGLE_CALENDAR.md`](./SETUP_GOOGLE_CALENDAR.md)

**Resumo:**
1. Criar projeto no Google Cloud
2. Ativar Google Calendar API
3. Criar Service Account
4. Baixar credenciais JSON
5. Salvar em `backend/credentials/service_account.json`
6. Compartilhar seu calendário com o email da Service Account
7. Configurar variáveis no `.env`:
   ```env
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
   GOOGLE_CALENDAR_ID=primary
   ```

### Passo 3: Reiniciar Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Você deve ver no log:
```
✅ Autenticado com Google Calendar API
```

Se ver:
```
⚠️ Google Calendar desabilitado. Configure as credenciais para habilitar.
```

Significa que precisa configurar as credenciais (Passo 2).

### Passo 4: Testar o Fluxo Completo

1. Vá em http://localhost:3000/landing
2. Inicie conversa com Smith
3. Preencha os dados:
   - Nome
   - Email (use um email real seu)
   - Empresa
   - Setor
   - Faturamento: "1M" ou mais
   - Decisor: "Sim"
4. Aguarde mensagem de qualificação
5. Responda com horário: "amanhã 14h" ou "quinta 15h"
6. Smith vai confirmar o agendamento
7. **Verifique seu email** - você deve receber:
   - Convite do Google Calendar
   - Link do Google Meet
8. **Verifique seu Google Calendar** - evento deve aparecer

## Arquivos Criados/Modificados:

### Criados:
- ✅ `backend/app/services/google_calendar_service.py` - Integração Google Calendar
- ✅ `backend/app/services/appointment_processor.py` - Processa horários
- ✅ `backend/app/models/agendamento.py` - Model de Agendamento
- ✅ `backend/app/repository/agendamentos_repository.py` - Repository
- ✅ `backend/migrations/003_create_agendamentos.sql` - SQL migration
- ✅ `SETUP_GOOGLE_CALENDAR.md` - Guia de configuração
- ✅ `GOOGLE_CALENDAR_IMPLEMENTADO.md` - Este arquivo

### Modificados:
- ✅ `backend/app/agent/smith_agent.py` - Prompts atualizados
- ✅ `backend/app/api/webhook.py` - Processamento de agendamentos
- ✅ `backend/.env.example` - Variáveis do Google Calendar
- ✅ `backend/requirements.txt` - Dependências instaladas

## Como Funciona por Trás dos Panos:

### 1. Extração de Data/Hora
Quando o lead responde com horário (ex: "quinta 14h"):
- LLM extrai data/hora da mensagem em linguagem natural
- Valida se é futuro, dia útil, horário comercial
- Se inválido, sugere 3 horários alternativos automaticamente

### 2. Criação no Google Calendar
Quando horário é válido:
- Cria evento no Google Calendar via API
- Gera link do Google Meet automaticamente
- Configura lembretes (24h, 1h, 10min antes)
- Envia convite para o email do lead

### 3. Persistência
- Salva agendamento no Supabase com:
  - `google_event_id` - para cancelar/atualizar depois
  - `google_meet_link` - link da reunião
  - `status` - agendado, confirmado, cancelado, etc.
  - Flags de lembretes enviados

## Vantagens vs Calendly:

✅ **Lead sai com reunião JÁ AGENDADA** - Sem fricção de clicar em link
✅ **Experiência 100% no WhatsApp** - Sem sair da conversa
✅ **Personalizado** - Usa SEU calendário direto
✅ **Sem custos extras** - Calendly custa $12+/mês
✅ **Controle total** - Você gerencia tudo pelo código
✅ **Prova do produto** - Lead vê a IA funcionando na prática

## Próximas Melhorias (TODO):

- [ ] Sistema de lembretes via WhatsApp (24h, 3h, 30min antes)
- [ ] Webhook do Google Calendar para capturar cancelamentos
- [ ] Reagendamento via WhatsApp
- [ ] Dashboard de agendamentos no frontend
- [ ] Confirmação de presença 1h antes

## Observações Importantes:

⚠️ **Google Calendar API é GRATUITO** até 1 milhão de requisições/dia (mais que suficiente)

⚠️ **Email do lead precisa ser REAL** - senão não recebe o convite

⚠️ **Service Account precisa ter acesso ao calendário** - compartilhe antes de testar

⚠️ **Backend precisa rodar no servidor 24/7** para processar mensagens do WhatsApp

## Testes Recomendados:

1. ✅ Horário válido: "amanhã 14h"
2. ✅ Horário inválido (final de semana): "sábado 10h" → deve sugerir alternativas
3. ✅ Horário inválido (fora comercial): "hoje 20h" → deve sugerir alternativas
4. ✅ Horário inválido (passado): "ontem 14h" → deve sugerir alternativas
5. ✅ Formato variado: "quinta às 15h", "15/01 10h30", "dia 20 14h"

## Dúvidas?

Se tiver problemas:
1. Verifique os logs do backend (uvicorn mostra tudo)
2. Confira se credenciais Google estão corretas
3. Verifique se tabela `agendamentos` existe no Supabase
4. Reveja [`SETUP_GOOGLE_CALENDAR.md`](./SETUP_GOOGLE_CALENDAR.md)

---

**Resumo:** Google Calendar está 100% integrado. Você só precisa:
1. Executar SQL no Supabase
2. Configurar credenciais Google
3. Testar! 🚀
