# Sistema de Lembretes de Marcos de Projetos

Sistema automático de lembretes via WhatsApp para prazos de etapas de projetos.

## 📋 O Que Foi Implementado

### 1. Banco de Dados (Migration 008)

**Arquivo**: `backend/migrations/008_create_project_milestones.sql`

Tabelas criadas:
- `project_milestones` - Marcos/etapas dos projetos com prazos
- `scheduled_reminders` - Lembretes agendados

Triggers automáticos:
- ✅ Criação automática de lembretes ao criar/atualizar marco
- ✅ Marcação automática de marcos atrasados
- ✅ Atualização de `updated_at` em mudanças

### 2. Backend API

**Arquivos criados:**
- `app/models/milestone.py` - Modelos Pydantic
- `app/repository/milestone_repository.py` - Acesso ao banco
- `app/services/milestone_reminder_service.py` - Lógica de envio
- `app/api/milestones.py` - Endpoints REST
- `app/cron/daily_reminders.py` - Job diário

**Configuração:**
- `app/config.py` - Adicionado `admin_whatsapp` (5561998112622)

### 3. Endpoints Disponíveis

```
POST   /api/milestones/                    - Criar marco
GET    /api/milestones/{id}                - Buscar marco
GET    /api/milestones/project/{project_id} - Listar marcos do projeto
PUT    /api/milestones/{id}                - Atualizar marco
DELETE /api/milestones/{id}                - Deletar marco

POST   /api/milestones/project/{id}/bulk   - Criar múltiplos marcos
GET    /api/milestones/{id}/reminders      - Listar lembretes

POST   /api/milestones/send-reminders      - Enviar lembretes (cron)
POST   /api/milestones/check-overdue       - Marcar atrasados (cron)
```

## 🚀 Como Configurar

### Passo 1: Rodar Migration no Supabase

1. Acesse o Supabase Dashboard
2. Vá em **SQL Editor**
3. Abra o arquivo `backend/migrations/008_create_project_milestones.sql`
4. Execute o SQL completo
5. Verifique se as tabelas foram criadas:
   ```sql
   SELECT * FROM project_milestones LIMIT 1;
   SELECT * FROM scheduled_reminders LIMIT 1;
   ```

### Passo 2: Configurar WhatsApp Admin

No arquivo `.env` do backend, adicione (ou verifique):

```bash
# WhatsApp do admin para receber lembretes
ADMIN_WHATSAPP=5561998112622

# Evolution API (já deve estar configurado)
EVOLUTION_API_URL=https://...
EVOLUTION_API_KEY=...
EVOLUTION_INSTANCE_NAME=smith
```

### Passo 3: Configurar Cron Job Diário

#### Opção A: Railway (Recomendado)

1. Instale o Railway CLI: `npm install -g @railway/cli`
2. Configure Railway Cron:
   ```bash
   railway cron add "daily-reminders" "0 8 * * *" "cd backend && python -m app.cron.daily_reminders"
   ```
   - Executa todo dia às 8h da manhã
   - Horário em UTC (8h UTC = 5h BRT)

#### Opção B: Endpoint Externo (Alternativa)

Use um serviço de cron externo (cron-job.org, EasyCron) para chamar:

```bash
curl -X POST https://seu-backend.railway.app/api/milestones/send-reminders
```

Configure para rodar diariamente às 8h.

#### Opção C: Sistema Linux/Mac (Local/VPS)

Adicione ao crontab:
```bash
crontab -e
```

```
# Lembretes diários às 8h
0 8 * * * cd /path/to/smith-vendas/backend && /usr/bin/python3 -m app.cron.daily_reminders >> /var/log/smith_reminders.log 2>&1
```

## 📱 Como Usar

### 1. Criar Marco ao Criar Projeto

```python
# Exemplo de criação de projeto com marcos
import requests

# Criar projeto
project_data = {
    "nome": "Site Institucional - Empresa XYZ",
    "client_id": "uuid-do-cliente",
    # ... outros campos
}
project = requests.post(f"{API_URL}/api/projects/", json=project_data).json()

# Criar marcos do projeto
milestones = [
    {
        "project_id": project["id"],
        "nome": "Briefing e Aprovação de Escopo",
        "descricao": "Reunião inicial e definição de requisitos",
        "ordem": 1,
        "data_limite": "2026-02-20",
        "notificacao_whatsapp": True
    },
    {
        "project_id": project["id"],
        "nome": "Design e Mockups",
        "descricao": "Criação de layouts e protótipos",
        "ordem": 2,
        "data_limite": "2026-03-05",
        "notificacao_whatsapp": True
    },
    {
        "project_id": project["id"],
        "nome": "Desenvolvimento",
        "descricao": "Implementação do site",
        "ordem": 3,
        "data_limite": "2026-03-25",
        "notificacao_whatsapp": True
    },
    {
        "project_id": project["id"],
        "nome": "Testes e Ajustes Finais",
        "descricao": "QA e correções",
        "ordem": 4,
        "data_limite": "2026-04-05",
        "notificacao_whatsapp": True
    },
    {
        "project_id": project["id"],
        "nome": "Deploy e Entrega",
        "descricao": "Publicação do site",
        "ordem": 5,
        "data_limite": "2026-04-10",
        "notificacao_whatsapp": True
    }
]

# Criar todos de uma vez (envia resumo por WhatsApp)
response = requests.post(
    f"{API_URL}/api/milestones/project/{project['id']}/bulk",
    json=milestones
)
```

### 2. Mensagem Automática Enviada

Ao criar os marcos, você receberá uma mensagem no WhatsApp:

```
✅ NOVO PROJETO CRIADO

🎯 Projeto: Site Institucional - Empresa XYZ
🔢 ID: #123
📋 Etapas: 5

📅 Cronograma de Entregas:

1. Briefing e Aprovação de Escopo
   📅 Prazo: 20/02/2026
   📝 Reunião inicial e definição de requisitos

2. Design e Mockups
   📅 Prazo: 05/03/2026
   📝 Criação de layouts e protótipos

[...]

🔔 Você receberá lembretes automáticos:
• 10, 7, 3 e 1 dias antes de cada prazo
• No dia do vencimento

---
Smith 2.0 - Gerenciamento de Projetos
```

### 3. Lembretes Automáticos

Você receberá lembretes nos seguintes momentos:

**10 dias antes:**
```
📅 LEMBRETE DE PRAZO

📋 Etapa: Design e Mockups
🎯 Projeto: Site Institucional - Empresa XYZ
📅 Vencimento: 05/03/2026
⏰ Faltam: 10 dias

📝 Detalhes: Criação de layouts e protótipos

---
Smith 2.0 - Gerenciamento de Projetos
```

**No dia:**
```
⏳ LEMBRETE: PRAZO HOJE!

📋 Etapa: Design e Mockups
🎯 Projeto: Site Institucional - Empresa XYZ
📅 Vencimento: 05/03/2026

⚡ A entrega desta etapa é hoje!

---
Smith 2.0 - Gerenciamento de Projetos
```

**Se atrasar:**
```
🔴 ALERTA: ETAPA ATRASADA!

📋 Etapa: Design e Mockups
🎯 Projeto: Site Institucional - Empresa XYZ
📅 Venceu em: 05/03/2026
⏱️ Atraso: 3 dias

⚠️ Esta etapa está atrasada!

---
Smith 2.0 - Gerenciamento de Projetos
```

## 🔧 Gerenciar Marcos

### Atualizar Status

```bash
# Marcar marco como concluído
curl -X PUT https://seu-backend.railway.app/api/milestones/{milestone_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "concluido",
    "data_conclusao": "2026-03-03"
  }'
```

### Alterar Data Limite

```bash
# Remarcar prazo (lembretes são recriados automaticamente)
curl -X PUT https://seu-backend.railway.app/api/milestones/{milestone_id} \
  -H "Content-Type: application/json" \
  -d '{
    "data_limite": "2026-03-10"
  }'
```

### Deletar Marco

```bash
curl -X DELETE https://seu-backend.railway.app/api/milestones/{milestone_id}
```

## 📊 Status de Marcos

- **pendente** - Ainda não iniciado
- **em_progresso** - Trabalhando na etapa
- **concluido** - Finalizado (não recebe mais lembretes)
- **atrasado** - Passou do prazo (marcado automaticamente)
- **cancelado** - Cancelado (não recebe mais lembretes)

## 🐛 Troubleshooting

### Lembretes não estão sendo enviados

1. Verifique se o cron está configurado e rodando
2. Teste manualmente:
   ```bash
   cd backend
   python -m app.cron.daily_reminders
   ```
3. Verifique logs:
   ```bash
   railway logs
   ```
4. Confirme que Evolution API está conectada:
   ```bash
   curl {EVOLUTION_API_URL}/instance/connectionState/{EVOLUTION_INSTANCE_NAME} \
     -H "apikey: {EVOLUTION_API_KEY}"
   ```

### Lembretes duplicados

- Trigger do banco cria lembretes automaticamente
- NÃO crie lembretes manualmente na tabela `scheduled_reminders`

### Alterar horário dos lembretes

Edite o cron para outro horário:
```bash
# 10h da manhã (7h UTC)
0 7 * * * ...

# 18h (15h UTC)
0 15 * * * ...
```

## 📝 Próximos Passos (Opcional)

### Frontend - Interface de Marcos

Criar tela em `frontend/src/app/portal/projetos/[id]/milestones/page.tsx`:

- Timeline visual das etapas
- Edição de marcos
- Visualização de status
- Histórico de lembretes enviados

### Melhorias Futuras

- [ ] Lembretes por email (além de WhatsApp)
- [ ] Notificações push no frontend
- [ ] Relatórios de atrasos
- [ ] Integração com Google Calendar
- [ ] Templates de marcos por tipo de projeto

## 🎯 Resumo

✅ **O que está funcionando:**
- Criação automática de lembretes ao criar marcos
- Triggers de banco para gerenciar lembretes
- Envio automático via WhatsApp
- Marcação automática de marcos atrasados
- API completa de gerenciamento

⏳ **O que precisa configurar:**
1. Rodar migration 008 no Supabase
2. Configurar cron job diário
3. Verificar ADMIN_WHATSAPP no .env

🚀 **Como testar:**
1. Criar projeto com marcos via API
2. Verificar mensagem de resumo no WhatsApp
3. Aguardar cron job ou executar manualmente
4. Receber lembretes nos prazos configurados

---

**Desenvolvido para Smith 2.0** 🤖
