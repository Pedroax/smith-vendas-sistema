# 🤖 Smith - Sistema Conversacional COMPLETO

## 🎯 O Que Foi Implementado

### 1. Sistema de Estados da Conversa ✅

Agora o Smith **SABE** exatamente em que etapa está cada lead:

```
INICIAL → AGENDAMENTO_ENVIADO → TIRANDO_DUVIDAS ⟷ AGUARDANDO_CONFIRMACAO → AGENDADO
```

**Estados:**
- `INICIAL`: Primeira interação
- `AGENDAMENTO_ENVIADO`: Já enviou horários, aguardando resposta
- `TIRANDO_DUVIDAS`: Lead está conversando/perguntando
- `AGUARDANDO_CONFIRMACAO`: Lead escolheu horário, confirming
- `AGENDADO`: Reunião marcada
- `FINALIZADO`: Conversa encerrada

###  2. Webhook Evolution API ✅

**Endpoint**: `POST /webhook/evolution`

Recebe TODAS as mensagens do WhatsApp e:
- Identifica quem enviou (lead)
- Evita processar duplicatas
- Salva no histórico
- Roteia para o handler correto

### 3. IA Conversacional (Smith AI) ✅

**GPT-4o** treinado para:
- ✅ Responder dúvidas sobre o produto
- ✅ Explicar funcionalidades
- ✅ Tirar dúvidas sobre preço
- ✅ Comparar com concorrentes
- ✅ Conduzir naturalmente ao agendamento
- ✅ Detectar quando lead quer agendar
- ✅ Manter contexto da conversa

**Personalidade:**
- Profissional mas amigável
- Direto e objetivo
- Usa emojis com moderação
- Honesto sobre limitações

### 4. Sistema de Roteamento Inteligente ✅

O Smith decide automaticamente:

```python
if estado == AGENDAMENTO_ENVIADO:
    if mensagem é "1", "2" ou "3":
        → Processar escolha de horário
    else:
        → Lead está tirando dúvida
        → Mudar para TIRANDO_DUVIDAS
        → Processar com IA

if estado == TIRANDO_DUVIDAS:
    → Processar com IA
    → Se detectar intenção de agendar:
        → Voltar para AGENDAMENTO_ENVIADO
```

### 5. Histórico Completo ✅

Todas as mensagens são salvas em `messages`:
- Direção (lead → Smith ou Smith → lead)
- Conteúdo
- Tipo (texto, imagem, áudio, etc)
- Timestamp
- ID da Evolution API (evita duplicatas)

### 6. Detecção de Intenções ✅

Smith detecta automaticamente quando lead:
- Quer agendar reunião
- Está tirando dúvida
- Escolheu horário (1, 2, 3)
- Quer outro horário

##  📁 Arquivos Criados

```
backend/
├── app/
│   ├── models/
│   │   └── conversation.py          # Modelos de conversa e mensagens
│   ├── repositories/
│   │   └── conversation_repository.py  # CRUD de conversas
│   ├── services/
│   │   ├── conversation_service.py    # Orquestrador principal
│   │   ├── smith_ai_service.py        # IA conversacional
│   │   └── evolution_service.py       # Cliente Evolution API
│   └── api/
│       └── webhook_evolution.py      # Webhook WhatsApp
└── create_conversation_tables.py    # Script criação tabelas
```

## 🚀 Como Usar

### 1. Criar Tabelas no Banco

```bash
cd backend
python create_conversation_tables.py
```

### 2. Reiniciar Backend

```bash
python -m uvicorn app.main:app --reload
```

### 3. Configurar Webhook na Evolution API

Configure o webhook para apontar para:
```
https://seu-dominio.com/webhook/evolution
```

Ou use ngrok para testar local:
```bash
ngrok http 8000
```

Webhook URL: `https://xxx.ngrok.io/webhook/evolution`

### 4. Testar Fluxo Completo

1. **Lead qualificado recebe mensagem de agendamento** ✅
   - Conversa criada com estado `AGENDAMENTO_ENVIADO`

2. **Lead responde "Tenho uma dúvida"**
   - Smith detecta que NÃO é escolha de horário
   - Muda estado para `TIRANDO_DUVIDAS`
   - IA responde a dúvida

3. **Lead continua conversando**
   - IA mantém contexto
   - Responde naturalmente
   - Conduz ao agendamento quando apropriado

4. **Lead diz "Ok, vamos agendar então"**
   - IA detecta intenção
   - Volta ao estado `AGENDAMENTO_ENVIADO`
   - Reexibe opções de horário

5. **Lead responde "1"**
   - Detecta escolha de horário
   - Cria evento no Google Calendar
   - Marca conversa como `AGENDADO`
   - Notifica você

## 🔥 Fluxo de Exemplo Real

```
[Sistema] Lead qualificado! Enviando agendamento...
[Smith → Lead] "Olá João! 👋 Vi que você se interessou..."
[Estado: AGENDAMENTO_ENVIADO]

[Lead → Smith] "Quanto custa?"
[Sistema] Não é escolha de horário, tirando dúvida
[Estado: TIRANDO_DUVIDAS]
[Smith → Lead] "O investimento é de R$ 6-7 mil..."

[Lead → Smith] "E tem integração com Instagram?"
[Smith → Lead] "Sim! Temos integração completa..."

[Lead → Smith] "Legal! Vamos marcar então"
[Sistema] Detectou intenção de agendamento!
[Estado: AGENDAMENTO_ENVIADO]
[Smith → Lead] "Perfeito! Esses horários funcionam para você?..."

[Lead → Smith] "2"
[Sistema] Lead escolheu horário 2
[Sistema] Criando evento no Google Calendar...
[Estado: AGENDADO]
[Smith → Lead] "✅ Pronto! Sua reunião está agendada!"
[Sistema] Notificando Pedro...
```

## 💪 Benefícios

### Antes (SEM Sistema Conversacional)
- ❌ Enviava horários e esperava resposta numérica
- ❌ Se lead perguntasse algo, ficaria sem resposta
- ❌ Não conseguia tirar dúvidas
- ❌ Perdia oportunidades de engajamento

### Agora (COM Sistema Conversacional)
- ✅ Responde QUALQUER dúvida do lead
- ✅ Conduz naturalmente ao agendamento
- ✅ Mantém lead engajado
- ✅ Aumenta taxa de conversão
- ✅ Constrói confiança antes da reunião
- ✅ Qualifica ainda mais durante conversa

## 🎨 Customizações Possíveis

### Personalidade da IA
Edite `smith_ai_service.py` → `self.system_prompt` para mudar:
- Tom de voz
- Nível de formalidade
- Emojis
- Estilo de resposta

### Detecção de Intenções
Edite `smith_ai_service.py` → `detected_scheduling_intent()` para adicionar mais keywords

### Fluxo de Estados
Edite `conversation_service.py` → `process_incoming_message()` para customizar lógica

## 🐛 Debug

Ver logs em tempo real:
```bash
tail -f logs/smith.log
```

Testar webhook manualmente:
```bash
curl -X POST http://localhost:8000/webhook/evolution \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "data": {
      "key": {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "test123"
      },
      "message": {
        "conversation": "Oi, tenho uma dúvida"
      }
    }
  }'
```

## 🎯 Próximos Passos

1. ✅ **Sistema funcionando** - Recebe e responde mensagens
2. ⏳ **Testar com Evolution API** - Configurar webhook real
3. ⏳ **Ajustar prompts da IA** - Refinar personalidade
4. ⏳ **Adicionar mais intenções** - Detectar mais casos
5. ⏳ **Dashboard de conversas** - Ver histórico no CRM

## 🚨 Importante

- **Estado é tudo**: O sistema sabe EXATAMENTE onde cada lead está
- **IA é inteligente**: Não só responde, mas CONDUZ ao agendamento
- **Contexto preservado**: Mantém histórico completo
- **Não repete mensagens**: Sabe que já enviou agendamento
- **Flexível**: Lead pode perguntar o que quiser

---

**SMITH ESTÁ PRONTO PARA CONVERSAR! 🤖🚀**
