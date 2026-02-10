# Configuração UAZAPI - Smith 2.0

## 🚀 Migração Evolution API → UAZAPI

Sistema agora usa **UAZAPI** para envio e recebimento de mensagens WhatsApp.

---

## 📋 O Que Foi Implementado

### 1. **Cliente UAZAPI** (`app/services/uazapi_service.py`)
   - ✅ `send_text_message()` - Envio de texto
   - ✅ `send_audio()` - Envio de áudio
   - ✅ `send_image()` - Envio de imagem
   - ✅ `send_document()` - Envio de documento/PDF

### 2. **Adaptador de Webhook** (`app/services/uazapi_adapter.py`)
   - ✅ `is_uazapi_webhook()` - Detecta formato UAZAPI
   - ✅ `adapt_uazapi_webhook()` - Converte UAZAPI → Evolution API
   - Mantém compatibilidade com código existente

### 3. **Webhook UAZAPI** (`app/api/webhook_uazapi.py`)
   - ✅ Recebe mensagens da UAZAPI
   - ✅ **Integrado com LangGraph** (smith_agent)
   - ✅ **Qualificação automática** de leads
   - ✅ **Cálculo de score** automático
   - ✅ **Agendamento automático** no Google Calendar
   - ✅ Envia respostas via UAZAPI

---

## ⚙️ Configuração (.env)

Adicione no arquivo `.env` do backend:

```bash
# UAZAPI (WhatsApp) - NOVO
UAZAPI_BASE_URL=https://api-ax.uazapi.com
UAZAPI_INSTANCE_ID=smith
UAZAPI_TOKEN=seu-token-aqui
```

### Como Obter as Credenciais:

1. **UAZAPI_BASE_URL**: Já está correto (`https://api-ax.uazapi.com`)
2. **UAZAPI_INSTANCE_ID**: Nome da instância que você criar (ex: "smith", "vendas")
3. **UAZAPI_TOKEN**: Token gerado na criação da instância

---

## 📱 Criar Nova Instância UAZAPI

### Passo 1: Acessar Painel
- URL: https://uazapi.dev/interno?p=conecte
- Login com sua conta

### Passo 2: Criar Instância
1. Clique em **"Nova Instância"** (botão azul)
2. **Nome**: smith (ou outro nome)
3. **Salvar**

### Passo 3: Conectar WhatsApp
1. Abra WhatsApp no celular
2. Vá em **Configurações → Aparelhos Conectados → Conectar Aparelho**
3. Escaneie o QR Code que aparece no painel UAZAPI
4. Aguarde status ficar **"online"** (verde)

### Passo 4: Copiar Token
1. No painel, clique no ícone do **olho 👁️** ao lado de "Admin Token"
2. Copie o token completo
3. Cole no `.env` em `UAZAPI_TOKEN`

---

## 🔗 Configurar Webhook na UAZAPI

Depois de subir seu backend, configure o webhook:

### Opção A: Painel UAZAPI
1. No painel da instância, clique em **"Webhook Global"**
2. **URL**: `https://seu-backend.railway.app/webhook/uazapi`
3. **Eventos**: Selecione **"messages"**
4. **Salvar**

### Opção B: Via API
```bash
curl -X POST "https://api-ax.uazapi.com/v1/webhook" \
  -H "Authorization: Bearer {SEU_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "instance": "smith",
    "webhook": "https://seu-backend.railway.app/webhook/uazapi",
    "events": ["messages"]
  }'
```

---

## 🧪 Testar Integração

### 1. Verificar se Backend Está Recebendo

Envie uma mensagem para o número conectado na UAZAPI e verifique os logs:

```bash
# Local
tail -f logs/smith.log | grep "UAZAPI"

# Railway
railway logs --tail
```

Você deve ver:
```
📨 RAW WEBHOOK BODY (UAZAPI): {...}
🔵 Webhook UAZAPI detectado
🔄 Payload adaptado para formato Evolution
💬 Mensagem de João (5521999999999): Oi, quero agendar...
🤖 Processando com smith_agent (LangGraph): stage=novo
✅ Agente processou: status=qualificando, score=0
📤 Enviando via UAZAPI para 55219999...
✅ Mensagem enviada para 5521999999999
```

### 2. Testar Fluxo Completo

**Simular conversa de qualificação:**

1. Envie: `"Oi, me chamo João"`
   - Agente: Pergunta empresa
2. Envie: `"Minha empresa é ACME Corp"`
   - Agente: Pergunta faturamento
3. Envie: `"Faturamos R$ 100k por mês"`
   - Agente: Pergunta se é decisor
4. Envie: `"Sim, sou o dono"`
   - Agente: **QUALIFICA** e oferece 2 opções (ROI ou Agendamento)
5. Envie: `"Quero agendar"`
   - Agente: Mostra horários disponíveis do Google Calendar
6. Envie: `"Opção 1"`
   - Agente: **AGENDA AUTOMATICAMENTE** e confirma

### 3. Verificar no Banco

```sql
-- Ver leads criados
SELECT nome, telefone, status, lead_score FROM leads ORDER BY created_at DESC LIMIT 5;

-- Ver conversas
SELECT * FROM conversation_messages WHERE lead_id = 'uuid-do-lead' ORDER BY timestamp;
```

---

## 🔄 Diferenças Evolution vs UAZAPI

| Aspecto | Evolution API | UAZAPI |
|---------|--------------|---------|
| **Webhook Format** | `event`, `data.key.remoteJid` | `EventType`, `chat.wa_chatid` |
| **Envio de Mensagem** | `/message/sendText/{instance}` | `/v1/chats/send-text` |
| **Auth** | `apikey` header | `Authorization: Bearer` |
| **Estabilidade** | ⚠️ Instável | ✅ Estável |
| **Custo** | Variável | R$ 79-138/mês |

---

## 📊 Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/webhook/uazapi` | POST | Recebe mensagens da UAZAPI |
| `/webhook/whatsapp` | POST | Webhook antigo (Evolution) |
| `/webhook/evolution` | POST | Webhook Evolution (DEPRECATED) |

---

## 🐛 Troubleshooting

### Problema: Webhook não está sendo chamado

**Causas:**
- URL do webhook incorreta
- Instância não está conectada
- Eventos não configurados

**Solução:**
1. Verificar URL: `https://seu-backend.railway.app/webhook/uazapi`
2. Verificar se instância está **online** (verde)
3. Reconfigurar webhook no painel

### Problema: Mensagens não são enviadas

**Causas:**
- Token inválido
- Instância desconectada
- Formato do telefone incorreto

**Solução:**
1. Verificar `UAZAPI_TOKEN` no `.env`
2. Reconectar WhatsApp (escanear QR Code novamente)
3. Telefone deve ser sem `@s.whatsapp.net` (ex: `5521999999999`)

### Problema: Agente não qualifica leads

**Causa:**
- LangGraph não está sendo chamado

**Solução:**
- Verificar logs: `Processando com smith_agent (LangGraph)`
- Se não aparecer, há erro no `smith_graph.invoke()`
- Verificar se OpenAI API Key está configurada

### Problema: Payload não é adaptado

**Erro:** `Invalid UAZAPI payload`

**Solução:**
- Verificar formato do payload nos logs
- Comparar com estrutura esperada no `uazapi_adapter.py`
- Pode ser evento diferente de `"messages"` (ex: `"status"`)

---

## 📝 Próximos Passos

Após configurar:

1. ✅ Criar instância UAZAPI
2. ✅ Configurar `.env` com token
3. ✅ Deploy backend (Railway)
4. ✅ Configurar webhook na UAZAPI
5. ✅ Testar com 1 lead
6. ✅ Ativar para os 10 leads pendentes

---

## 🎯 Resumo Rápido

```bash
# 1. Criar instância "smith" na UAZAPI
# 2. Copiar token

# 3. Adicionar ao .env
echo "UAZAPI_TOKEN=seu-token-aqui" >> .env

# 4. Deploy
git push railway master

# 5. Configurar webhook
URL: https://seu-backend.railway.app/webhook/uazapi

# 6. Testar!
# Envie "Oi" para o número conectado
```

---

**Sistema 100% pronto para atender leads automaticamente com qualificação via LangGraph!** 🚀
