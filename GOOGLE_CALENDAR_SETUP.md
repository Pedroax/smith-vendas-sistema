# Configuração do Google Calendar no Railway

## Problema
O arquivo `google_credentials.json` está no `.gitignore` e não vai pro Railway quando você faz deploy. Por isso o Google Calendar fica desabilitado em produção.

## Solução
Usar variável de ambiente `GOOGLE_CREDENTIALS_JSON` no Railway.

---

## Passo a Passo

### 1. Copiar o conteúdo do arquivo JSON

No seu computador LOCAL, abra o arquivo `backend/google_credentials.json` e copie TODO o conteúdo.

**IMPORTANTE:** O arquivo é uma ÚNICA linha de JSON compactado (sem quebras de linha). Copie exatamente como está no arquivo.

### 2. Configurar no Railway

1. Acesse o Railway: https://railway.app
2. Entre no projeto do Smith
3. Vá em **Variables** (tab de variáveis de ambiente)
4. Clique em **+ New Variable**
5. Nome: `GOOGLE_CREDENTIALS_JSON`
6. Valor: **Cole todo o JSON que você copiou** (1 linha só, sem espaços extras)
7. Clique em **Add**

### 3. Redeploy

Depois de adicionar a variável, o Railway vai fazer redeploy automaticamente.

### 4. Verificar nos Logs

Após o deploy, procure nos logs do Railway:

✅ **Se funcionou:**
```
🔑 Carregando credenciais do Google Calendar da variável de ambiente...
✅ Credenciais carregadas da variável de ambiente
✅ Google Calendar API autenticado e disponível
```

❌ **Se ainda estiver com erro:**
```
⚠️ Google Calendar desabilitado. Configure GOOGLE_CREDENTIALS_JSON
```

---

## Como Funciona

O código agora tenta carregar credenciais de **DUAS formas**:

1. **Variável de ambiente** `GOOGLE_CREDENTIALS_JSON` (prioridade - para Railway)
2. **Arquivo** `google_credentials.json` (fallback - para desenvolvimento local)

Se você configurou a variável no Railway, o Google Calendar vai funcionar automaticamente.

---

## Testando Localmente

Localmente, você NÃO precisa fazer nada. O arquivo `google_credentials.json` já está na pasta `backend/` e é carregado automaticamente.

---

## Fluxo de Agendamento (quando tudo estiver funcionando)

Quando um lead qualificado aceitar agendar reunião:

1. **Lead diz "sim", "pode", "vamos", etc.**
2. **IA detecta aceitação** (`aceitou_agendar = True`)
3. **Chama Google Calendar API** (`get_available_slots()`)
4. **Mostra 3 horários reais** disponíveis no WhatsApp
5. **Lead escolhe horário**
6. **IA cria evento no Google Calendar** (`create_meeting()`)

---

## Próximos Passos

Depois de configurar a variável no Railway:

1. Aguardar o redeploy automático
2. Verificar os logs para confirmar autenticação
3. Testar o fluxo completo de agendamento
4. Qualificar um lead de teste
5. Aceitar agendamento ("sim")
6. Verificar se mostra os 3 horários disponíveis

---

**Importante:** Não compartilhe o JSON das credenciais publicamente. Ele dá acesso ao Google Calendar configurado.
