# 🧪 Guia de Teste - Notificações e Busca Global

## ✅ O que foi implementado:

### 1. Sistema de Notificações
- **Backend**: Models, Repository, API completos
- **Frontend**: Sino no header + Dropdown + Página /notificacoes
- **Tipos**: 9 tipos de notificação (lead_quente, agendamento, novo_lead, etc)
- **Prioridades**: low, medium, high, urgent

### 2. Busca Global
- **Backend**: Busca unificada em leads, projetos, interações, agendamentos
- **Frontend**: Campo de busca no header com Ctrl+K
- **UI**: Dropdown com resultados agrupados

### 3. TopBar
- Header fixo em todas as páginas
- Busca global + Notificações + Avatar

---

## 🚀 Como Testar:

### Passo 1: Iniciar Backend
```powershell
cd C:\Users\pedro\Desktop\smith-vendas\backend
python -m uvicorn app.main:app --reload --port 8000
```

Aguarde ver: `Application startup complete.`

### Passo 2: Testar Backend
Execute o script de teste:
```powershell
cd C:\Users\pedro\Desktop\smith-vendas
.\test_backend.bat
```

Você deve ver respostas JSON (não 404).

### Passo 3: Criar Notificações de Teste
```powershell
python test_notifications.py
```

Você deve ver `[OK]` em todas as 7 notificações.

### Passo 4: Testar Frontend
1. Acesse: http://localhost:3004
2. Veja o **sino 🔔** no header (canto direito)
3. Deve ter um **badge vermelho** com número (7)
4. Clique no sino para ver dropdown
5. Acesse: http://localhost:3004/notificacoes

---

## 🔍 Endpoints do Backend:

### Notificações:
- `GET /api/notifications` - Listar todas
- `GET /api/notifications/count/unread` - Contar não lidas
- `POST /api/notifications` - Criar
- `POST /api/notifications/{id}/read` - Marcar como lida
- `DELETE /api/notifications/{id}` - Deletar

### Busca Global:
- `GET /api/search?q=termo` - Busca unificada

### Outros:
- `GET /api/interactions` - Interações
- `GET /api/appointments` - Agendamentos

---

## 📋 Checklist de Teste:

### Backend:
- [ ] Backend iniciou sem erros
- [ ] Health check responde
- [ ] Endpoint /api/notifications/count/unread funciona
- [ ] Script test_notifications.py criou 7 notificações

### Frontend:
- [ ] Header aparece em todas as páginas
- [ ] Campo de busca funciona
- [ ] Sino mostra badge com contador
- [ ] Dropdown de notificações abre
- [ ] Página /notificacoes carrega
- [ ] Busca global retorna resultados
- [ ] Ctrl+K abre o campo de busca

---

## ❌ Troubleshooting:

### Backend retorna 404:
1. Verifique se o backend está realmente rodando
2. Mate todos os processos Python: `taskkill //F //IM python.exe`
3. Reinicie o backend
4. Aguarde 10 segundos antes de testar

### Porta 8000 ocupada:
```powershell
netstat -ano | findstr :8000
taskkill //F //PID <numero_do_pid>
```

### Frontend não mostra notificações:
1. Verifique o console do navegador (F12)
2. Confirme que o backend está rodando
3. Teste a API manualmente: `curl http://localhost:8000/api/notifications/count/unread`

---

## 📸 O que você deve ver:

### No Header:
- Barra de busca grande no centro
- Sino com badge vermelho (7) à direita
- Avatar "PM" no canto direito

### No Dropdown (ao clicar no sino):
- 7 notificações listadas
- Ícones diferentes (🔥 📅 ✨ ⏰ etc)
- Badge "NOVA" nas não lidas
- Botão "Marcar todas como lidas"
- Link "Ver todas notificações"

### Na Página /notificacoes:
- Header com "7 não lidas", "7 total"
- Filtros: "Todas" / "Não Lidas"
- Lista completa com detalhes
- Botão "Marcar Todas como Lidas"
- Ações: Marcar lida / Deletar

---

**Pronto para teste!** 🎯

Se encontrar problemas, me avise e eu ajudo a resolver.
