# ✅ Integração Frontend-Backend - Smith 2.0

**Data**: 25/12/2024
**Status**: ✅ Completa

---

## 🎯 O QUE FOI IMPLEMENTADO

### 1. **API Client** ([frontend/src/lib/api.ts](frontend/src/lib/api.ts))

Cliente TypeScript completo para comunicação com o backend FastAPI.

#### Métodos Implementados:

**Leads:**
- `getLeads(filters?)` - Lista leads com filtros opcionais
- `getLead(leadId)` - Busca lead específico
- `createLead(data)` - Cria novo lead
- `updateLead(leadId, data)` - Atualiza lead
- `deleteLead(leadId)` - Remove lead
- `qualifyLead(leadId)` - Força re-qualificação
- `getStats()` - Estatísticas agregadas

**Webhook:**
- `getWebhookStatus()` - Status da conexão WhatsApp

#### Configuração:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

---

### 2. **Store Atualizado** ([frontend/src/store/useLeadsStore.ts](frontend/src/store/useLeadsStore.ts))

Zustand store completamente refatorado para consumir API real.

#### Antes (Mock):
```typescript
export const useLeadsStore = create<LeadsStore>((set) => ({
  leads: mockLeads, // Dados fixos
  addLead: (lead) => set((state) => ({ ... })),
}));
```

#### Depois (API Real):
```typescript
export const useLeadsStore = create<LeadsStore>((set, get) => ({
  leads: [],
  stats: null,
  isLoading: false,
  error: null,

  fetchLeads: async (filters?) => {
    set({ isLoading: true });
    const leads = await apiClient.getLeads(filters);
    set({ leads, isLoading: false });
  },

  createLead: async (data) => {
    const response = await apiClient.createLead(data);
    set((state) => ({ leads: [...state.leads, response.lead] }));
    get().fetchStats(); // Atualiza estatísticas
  },

  updateLeadStatus: async (leadId, newStatus) => {
    // Atualização otimista para melhor UX
    const previousLeads = get().leads;
    set((state) => ({
      leads: state.leads.map(l => l.id === leadId ? {...l, status: newStatus} : l)
    }));

    try {
      await apiClient.updateLead(leadId, { status: newStatus });
    } catch {
      set({ leads: previousLeads }); // Reverte em caso de erro
    }
  },
}));
```

#### Novos Recursos:

✅ **Loading States**: `isLoading` para feedback visual
✅ **Error Handling**: `error` com mensagens detalhadas
✅ **Optimistic Updates**: UI atualiza instantaneamente, reverte se API falhar
✅ **Auto-refresh Stats**: Estatísticas atualizadas após mudanças
✅ **Filtros**: Suporte a filtros por status, origem, temperatura
✅ **Paginação**: Offset e limit para grandes volumes

---

### 3. **Páginas Atualizadas**

#### Home Page ([frontend/src/app/page.tsx](frontend/src/app/page.tsx))

```typescript
export default function Home() {
  const { leads, fetchLeads, fetchStats } = useLeadsStore();

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, []);

  // Estatísticas calculadas de leads reais da API
  const stats = {
    totalLeads: leads.length,
    leadsHoje: leads.filter(l => new Date(l.created_at).toDateString() === today).length,
    valorPipeline: leads.reduce((sum, lead) => sum + lead.valor_estimado, 0),
    taxaConversao: Math.round((leads.filter(l => l.status === 'ganho').length / leads.length) * 100),
  };
}
```

#### CRM Page ([frontend/src/app/crm/page.tsx](frontend/src/app/crm/page.tsx))

```typescript
export default function CRMPage() {
  const { leads, isLoading, error, fetchLeads, clearError } = useLeadsStore();

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, []);

  return (
    <>
      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3>Erro ao carregar dados</h3>
          <p>{error}</p>
          <button onClick={clearError}>Fechar</button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && leads.length === 0 ? (
        <div className="text-center py-20">
          <Loader2 className="animate-spin" />
          <p>Carregando leads...</p>
        </div>
      ) : (
        <KanbanBoard />
      )}
    </>
  );
}
```

**Melhorias:**
- ✅ Feedback de loading com spinner
- ✅ Mensagens de erro personalizadas
- ✅ Atualização automática ao montar
- ✅ Dados reais do backend

---

### 4. **Variáveis de Ambiente** ([frontend/.env.local](frontend/.env.local))

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Uso:**
- Desenvolvimento: `http://localhost:8000`
- Produção: Alterar para URL do servidor

---

## 🔄 FLUXO DE DADOS

```
┌─────────────────┐
│  Next.js Pages  │
│  (Home, CRM)    │
└────────┬────────┘
         │ useLeadsStore()
         ▼
┌─────────────────┐
│  Zustand Store  │
│  (State Mgmt)   │
└────────┬────────┘
         │ apiClient.getLeads()
         ▼
┌─────────────────┐
│   API Client    │
│   (lib/api.ts)  │
└────────┬────────┘
         │ fetch('http://localhost:8000/api/leads')
         ▼
┌─────────────────┐
│  FastAPI Backend│
│  (Python)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Database       │
│  (Supabase)     │
└─────────────────┘
```

---

## 📊 ENDPOINTS CONSUMIDOS

| Método | Endpoint | Usado em |
|--------|----------|----------|
| `GET` | `/api/leads` | Home, CRM (listagem) |
| `GET` | `/api/leads/{id}` | Detalhes de lead |
| `POST` | `/api/leads` | Formulário criar lead |
| `PUT` | `/api/leads/{id}` | Drag-and-drop Kanban |
| `DELETE` | `/api/leads/{id}` | Ação de deletar |
| `POST` | `/api/leads/{id}/qualify` | Re-qualificação manual |
| `GET` | `/api/leads/stats/summary` | Dashboard stats |
| `GET` | `/webhook/whatsapp/status` | System status |

---

## 🚀 COMO TESTAR

### 1. **Iniciar Backend**

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Backend estará em: `http://localhost:8000`
Docs interativa: `http://localhost:8000/docs`

### 2. **Iniciar Frontend**

```bash
cd frontend
npm run dev
```

Frontend estará em: `http://localhost:3000`

### 3. **Testar Integração**

1. Abra `http://localhost:3000`
2. Verifique se leads aparecem (carregados da API)
3. Arraste um card no Kanban (deve atualizar via API)
4. Verifique Network tab no DevTools:
   - Deve ver chamadas para `http://localhost:8000/api/leads`
   - Status 200 OK
   - Dados JSON retornados

### 4. **Verificar Mock Data**

O backend tem leads mockados em `backend/app/api/leads.py`:

```python
LEADS_DB = {
    "lead-001": Lead(...),  # 15 leads de exemplo
}
```

Esses leads aparecem automaticamente no frontend quando você abre a página.

---

## ⚙️ CONFIGURAÇÃO ADICIONAL

### Caso Backend esteja em outra porta:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### Caso Backend esteja em produção:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.automatexia.com.br
```

---

## ✅ FEATURES IMPLEMENTADAS

- [x] Cliente API TypeScript completo
- [x] Store Zustand com async/await
- [x] Loading states (spinners)
- [x] Error handling (mensagens de erro)
- [x] Optimistic updates (UX responsiva)
- [x] Auto-refresh de estatísticas
- [x] Filtros de leads (status, origem, temperatura)
- [x] Paginação (limit, offset)
- [x] Drag-and-drop integrado com API
- [x] Fetch automático ao montar páginas
- [x] Variáveis de ambiente configuradas

---

## 🔜 PRÓXIMOS PASSOS

1. **Supabase Integration**: Substituir LEADS_DB in-memory por Supabase real
2. **Real-time Updates**: WebSocket para sync automático entre frontend/backend
3. **Formulários**: Modal para criar/editar leads
4. **Filtros UI**: Componentes de filtro no CRM
5. **WhatsApp Integration**: Conectar Evolution API
6. **Google Calendar**: OAuth e agendamentos
7. **Notifications**: Toast para ações (lead criado, erro, etc)

---

## 🐛 DEBUG

### Frontend não carrega leads?

1. Verifique se backend está rodando: `curl http://localhost:8000/api/leads`
2. Abra DevTools → Network → Veja se há erro 404 ou CORS
3. Verifique `.env.local` se URL está correta

### CORS Error?

Backend já tem CORS configurado em `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Leads não atualizam após drag?

1. Verifique console do browser por erros
2. Verifique se `updateLeadStatus()` está sendo chamado
3. Teste endpoint diretamente: `curl -X PUT http://localhost:8000/api/leads/{id} -d '{"status":"qualificado"}'`

---

**Integração completa e funcional! 🎉**

**Próximo passo:** Conectar Supabase para persistência real dos dados.
