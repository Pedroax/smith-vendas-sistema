# 🔌 API Documentation - Smith 2.0

**Base URL**: `http://localhost:8000`
**Documentação Interativa**: `http://localhost:8000/docs`

---

## 📋 Endpoints de Leads

### **POST** `/api/leads`
Cria um novo lead.

**Request Body:**
```json
{
  "nome": "João Silva",
  "telefone": "5521999999999",
  "empresa": "Tech Corp",
  "email": "joao@techcorp.com",
  "origem": "instagram",
  "notas": "Veio do anúncio de automação"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "lead": { ... },
  "message": "Lead criado com sucesso"
}
```

---

### **GET** `/api/leads`
Lista leads com filtros opcionais.

**Query Parameters:**
- `status` (opcional): `novo`, `contato_inicial`, `qualificando`, `qualificado`, `agendamento_marcado`, `ganho`, `perdido`
- `origem` (opcional): `instagram`, `whatsapp`, `site`, `indicacao`, `outro`
- `temperatura` (opcional): `quente`, `morno`, `frio`
- `limit` (opcional): Máximo de resultados (default: 100, max: 1000)
- `offset` (opcional): Offset para paginação (default: 0)

**Exemplos:**
```bash
GET /api/leads?status=qualificado
GET /api/leads?origem=instagram&temperatura=quente
GET /api/leads?limit=50&offset=100
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid-123",
    "nome": "João Silva",
    "status": "qualificado",
    "lead_score": 85,
    ...
  }
]
```

---

### **GET** `/api/leads/{lead_id}`
Busca um lead específico por ID.

**Response:** `200 OK`
```json
{
  "id": "uuid-123",
  "nome": "João Silva",
  "empresa": "Tech Corp",
  "telefone": "5521999999999",
  "status": "qualificado",
  "lead_score": 85,
  "qualification_data": {
    "budget": 3000,
    "authority": true,
    "need": "Preciso automatizar",
    ...
  },
  "roi_analysis": {
    "tempo_economizado_mes": 120,
    "valor_economizado_ano": 86400,
    "roi_percentual": 360,
    ...
  }
}
```

**Error:** `404 Not Found`

---

### **PUT** `/api/leads/{lead_id}`
Atualiza um lead existente.

**Request Body:**
```json
{
  "nome": "João Silva Jr.",
  "status": "ganho",
  "valor_estimado": 5000,
  "notas": "Fechou na reunião!",
  "tags": ["vip", "prioridade"]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "lead": { ... },
  "message": "Lead atualizado com sucesso"
}
```

---

### **DELETE** `/api/leads/{lead_id}`
Deleta um lead.

**Response:** `200 OK`
```json
{
  "success": true,
  "lead": null,
  "message": "Lead João Silva deletado com sucesso"
}
```

---

### **POST** `/api/leads/{lead_id}/qualify`
Força re-qualificação de um lead (recalcula score).

**Response:** `200 OK`
```json
{
  "success": true,
  "lead": {
    "id": "uuid-123",
    "lead_score": 72,
    "status": "qualificado",
    ...
  },
  "message": "Lead qualificado com score 72"
}
```

---

### **GET** `/api/leads/stats/summary`
Retorna estatísticas agregadas de todos os leads.

**Response:** `200 OK`
```json
{
  "total_leads": 156,
  "por_status": {
    "novo": 12,
    "contato_inicial": 8,
    "qualificando": 15,
    "qualificado": 45,
    "agendamento_marcado": 20,
    "ganho": 40,
    "perdido": 16
  },
  "por_origem": {
    "instagram": 80,
    "whatsapp": 45,
    "site": 20,
    "indicacao": 11
  },
  "por_temperatura": {
    "quente": 65,
    "morno": 70,
    "frio": 21
  },
  "score_medio": 68.5,
  "valor_total_pipeline": 450000,
  "taxa_qualificacao": 72.5,
  "taxa_conversao": 25.6
}
```

---

## 📱 Endpoints de Webhook (WhatsApp)

### **POST** `/webhook/whatsapp`
Recebe mensagens do WhatsApp via Evolution API.

**⚠️ Este endpoint é chamado automaticamente pela Evolution API.**

**Request Body:** (formato Evolution API)
```json
{
  "event": "messages.upsert",
  "data": {
    "key": {
      "remoteJid": "5521999999999@s.whatsapp.net",
      "fromMe": false
    },
    "pushName": "João",
    "message": {
      "conversation": "Olá, gostaria de saber sobre automação"
    }
  }
}
```

**Fluxo Automático:**
1. ✅ Recebe mensagem
2. ✅ Cria/atualiza lead no banco
3. ✅ Processa com agente Smith
4. ✅ Agente responde automaticamente
5. ✅ Envia resposta via WhatsApp

**Response:** `200 OK`
```json
{
  "status": "processed",
  "lead_id": "uuid-123",
  "lead_status": "qualificando",
  "lead_score": 45
}
```

---

### **GET** `/webhook/whatsapp/status`
Verifica status do webhook e conexão WhatsApp.

**Response:** `200 OK`
```json
{
  "webhook": "active",
  "whatsapp_connection": "open",
  "total_leads": 156,
  "timestamp": "2024-12-25T12:30:00"
}
```

---

### **POST** `/webhook/test`
Endpoint de teste para simular mensagem do WhatsApp.

**Response:** `200 OK`
```json
{
  "test": "completed",
  "result": {
    "status": "processed",
    "lead_id": "test-uuid",
    "lead_status": "novo"
  }
}
```

---

## 🔍 Exemplos de Uso

### Criar Lead e Processar Mensagem

```python
import requests

# Criar lead
response = requests.post(
    "http://localhost:8000/api/leads",
    json={
        "nome": "Carlos Silva",
        "telefone": "5511988887777",
        "origem": "instagram"
    }
)
lead = response.json()["lead"]

# Simular mensagem do WhatsApp
requests.post(
    "http://localhost:8000/webhook/whatsapp",
    json={
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": "5511988887777@s.whatsapp.net",
                "fromMe": False
            },
            "pushName": "Carlos Silva",
            "message": {
                "conversation": "Tenho interesse em automação com IA"
            }
        }
    }
)
```

---

### Buscar Leads Qualificados

```bash
curl "http://localhost:8000/api/leads?status=qualificado&temperatura=quente"
```

---

### Ver Estatísticas

```bash
curl "http://localhost:8000/api/leads/stats/summary"
```

---

## 🎯 Fluxo Completo de Lead

```
1. Mensagem chega no WhatsApp
   ↓
2. Evolution API → POST /webhook/whatsapp
   ↓
3. Sistema cria/atualiza lead
   ↓
4. Agente Smith processa (qualifica, calcula ROI, etc)
   ↓
5. Resposta automática enviada
   ↓
6. Lead atualizado no CRM (GET /api/leads)
   ↓
7. Frontend atualiza em tempo real
```

---

## 🔐 Autenticação

**Atualmente:** Sem autenticação (desenvolvimento)

**Produção (futuro):**
- JWT tokens
- API keys
- Rate limiting

---

## 📊 Status Codes

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

---

## 🧪 Testando a API

### Via Swagger UI
Acesse: `http://localhost:8000/docs`

### Via cURL

```bash
# Listar leads
curl http://localhost:8000/api/leads

# Criar lead
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"nome":"Test","telefone":"5521999999999","origem":"whatsapp"}'

# Ver estatísticas
curl http://localhost:8000/api/leads/stats/summary
```

### Via Python

```python
import httpx

async with httpx.AsyncClient() as client:
    # Listar leads
    response = await client.get("http://localhost:8000/api/leads")
    leads = response.json()

    # Criar lead
    response = await client.post(
        "http://localhost:8000/api/leads",
        json={
            "nome": "Test Lead",
            "telefone": "5521999999999",
            "origem": "whatsapp"
        }
    )
    new_lead = response.json()
```

---

## 🚀 Próximas Rotas (TODO)

- [ ] `/api/conversations` - Histórico de conversas
- [ ] `/api/analytics` - Analytics e métricas
- [ ] `/api/calendar` - Google Calendar integration
- [ ] `/api/agent/config` - Configuração do agente
- [ ] `/api/agent/approve` - Aprovação manual de mensagens

---

**Documentação atualizada**: 25/12/2024
**Versão da API**: 2.0.0
