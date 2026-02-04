# Setup Google Calendar API

## Passo 1: Criar Projeto no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em "Novo Projeto"
3. Nome do projeto: `smith-vendas` (ou outro nome)
4. Clique em "Criar"

## Passo 2: Habilitar Google Calendar API

1. No menu lateral, vá em **APIs e Serviços** → **Biblioteca**
2. Busque por "Google Calendar API"
3. Clique em "Ativar"

## Passo 3: Criar Service Account

1. No menu lateral, vá em **APIs e Serviços** → **Credenciais**
2. Clique em **Criar credenciais** → **Conta de serviço**
3. Preencha:
   - Nome da conta de serviço: `smith-calendar-bot`
   - ID da conta de serviço: `smith-calendar-bot` (auto-gerado)
   - Descrição: "Bot para criar reuniões automaticamente"
4. Clique em "Criar e continuar"
5. Pule as permissões (clique em "Continuar")
6. Clique em "Concluir"

## Passo 4: Gerar Chave JSON

1. Na lista de contas de serviço, clique na conta que você criou (`smith-calendar-bot`)
2. Vá na aba **Chaves**
3. Clique em **Adicionar chave** → **Criar nova chave**
4. Escolha tipo **JSON**
5. Clique em "Criar"
6. Um arquivo JSON será baixado automaticamente

## Passo 5: Configurar no Projeto

1. Crie uma pasta `credentials` dentro de `backend/`:
   ```bash
   mkdir backend/credentials
   ```

2. Mova o arquivo JSON baixado para `backend/credentials/service_account.json`

3. Adicione ao `.gitignore`:
   ```
   backend/credentials/
   *.json
   ```

## Passo 6: Compartilhar Calendário com Service Account

⚠️ **IMPORTANTE**: O Service Account precisa ter acesso ao seu Google Calendar!

1. Abra [Google Calendar](https://calendar.google.com)
2. No lado esquerdo, encontre seu calendário
3. Clique nos 3 pontos ao lado do calendário → **Configurações e compartilhamento**
4. Role até **Compartilhar com pessoas específicas**
5. Clique em **Adicionar pessoas**
6. Cole o email da Service Account:
   - Você encontra no arquivo JSON: campo `client_email`
   - Exemplo: `smith-calendar-bot@smith-vendas.iam.gserviceaccount.com`
7. Permissão: **Fazer alterações em eventos**
8. Clique em "Enviar"

## Passo 7: Configurar Variáveis de Ambiente

Adicione ao arquivo `.env`:

```env
# Google Calendar API
GOOGLE_CALENDAR_ID=primary
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
```

Se quiser usar um calendário específico (não o principal):
1. Vá em [Google Calendar](https://calendar.google.com)
2. Clique nos 3 pontos do calendário → **Configurações e compartilhamento**
3. Role até **Integrar calendário**
4. Copie o **ID do calendário** (ex: `abc123@group.calendar.google.com`)
5. Use no `.env`: `GOOGLE_CALENDAR_ID=abc123@group.calendar.google.com`

## Passo 8: Testar

Reinicie o backend:

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
⚠️ Arquivo de credenciais não encontrado: credentials/service_account.json
⚠️ Google Calendar desabilitado. Configure as credenciais para habilitar.
```

Significa que o arquivo não está no lugar certo ou o caminho no `.env` está errado.

## Estrutura de Arquivos

```
smith-vendas/
├── backend/
│   ├── credentials/
│   │   └── service_account.json  ← Arquivo JSON da Service Account
│   ├── app/
│   │   ├── services/
│   │   │   └── google_calendar_service.py
│   │   └── ...
│   └── .env  ← Variáveis de ambiente
└── ...
```

## Troubleshooting

### Erro: "Calendar not found"
- Verifique se compartilhou o calendário com o email da Service Account
- Verifique se o GOOGLE_CALENDAR_ID está correto

### Erro: "Permission denied"
- Verifique se deu permissão "Fazer alterações em eventos" ao compartilhar
- Aguarde alguns minutos após compartilhar (pode demorar para propagar)

### Erro: "Service account file not found"
- Verifique se o arquivo está em `backend/credentials/service_account.json`
- Verifique se o caminho no `.env` está correto

### Reuniões não aparecem no calendário
- Verifique se o email do lead está correto
- Verifique se o `sendUpdates='all'` está habilitado no código
- Confira a caixa de spam do lead

## Observações

- O Google Calendar API tem limites de uso: 1.000.000 requisições/dia (mais que suficiente)
- As reuniões criadas incluem automaticamente um link do Google Meet
- O lead recebe email de convite automaticamente
- Lembretes são configurados automaticamente (24h, 1h, 10min antes)

## Próximos Passos

Após configurar:

1. ✅ Testar criação de reunião manualmente
2. ✅ Testar fluxo completo WhatsApp → Qualificação → Agendamento
3. ✅ Configurar sistema de lembretes via WhatsApp (TODO)
