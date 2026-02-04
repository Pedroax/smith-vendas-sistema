import { create } from 'zustand';
import { Lead, LeadStatus, LeadOrigin, LeadTemperature } from '@/types/lead';
import { apiClient, CreateLeadData, UpdateLeadData, LeadFilters, LeadStats } from '@/lib/api';

interface LeadsStore {
  // Estado
  leads: Lead[];
  stats: LeadStats | null;
  isLoading: boolean;
  error: string | null;

  // Ações de fetch
  fetchLeads: (filters?: LeadFilters) => Promise<void>;
  fetchLead: (leadId: string) => Promise<Lead | null>;
  fetchStats: () => Promise<void>;
  refreshLeads: () => Promise<void>;

  // Ações de CRUD
  createLead: (data: CreateLeadData) => Promise<Lead | null>;
  updateLeadStatus: (leadId: string, newStatus: LeadStatus) => Promise<void>;
  updateLead: (leadId: string, data: UpdateLeadData) => Promise<void>;
  deleteLead: (leadId: string) => Promise<void>;
  qualifyLead: (leadId: string) => Promise<void>;

  // Helpers
  clearError: () => void;
  setLoading: (loading: boolean) => void;

  // WebSocket handlers
  handleLeadCreated: (lead: Lead) => void;
  handleLeadUpdated: (lead: Lead) => void;
  handleLeadDeleted: (leadId: string) => void;
}

export const useLeadsStore = create<LeadsStore>((set, get) => ({
  // Estado inicial
  leads: [],
  stats: null,
  isLoading: false,
  error: null,

  // ==================== FETCH ====================

  fetchLeads: async (filters?: LeadFilters) => {
    set({ isLoading: true, error: null });
    try {
      const leads = await apiClient.getLeads(filters);
      set({ leads, isLoading: false });
    } catch (error) {
      console.error('Erro ao buscar leads:', error);
      set({
        error: error instanceof Error ? error.message : 'Erro ao buscar leads',
        isLoading: false,
      });
    }
  },

  fetchLead: async (leadId: string) => {
    try {
      const lead = await apiClient.getLead(leadId);

      // Atualizar lead no estado local
      set((state) => ({
        leads: state.leads.map((l) => (l.id === leadId ? lead : l)),
      }));

      return lead;
    } catch (error) {
      console.error('Erro ao buscar lead:', error);
      set({
        error: error instanceof Error ? error.message : 'Erro ao buscar lead',
      });
      return null;
    }
  },

  fetchStats: async () => {
    try {
      const stats = await apiClient.getStats();
      set({ stats });
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error);
    }
  },

  refreshLeads: async () => {
    const { fetchLeads, fetchStats } = get();
    await Promise.all([fetchLeads(), fetchStats()]);
  },

  // ==================== CRUD ====================

  createLead: async (data: CreateLeadData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.createLead(data);

      // Adicionar lead ao estado local
      set((state) => ({
        leads: [...state.leads, response.lead],
        isLoading: false,
      }));

      // Atualizar estatísticas
      get().fetchStats();

      return response.lead;
    } catch (error) {
      console.error('Erro ao criar lead:', error);
      set({
        error: error instanceof Error ? error.message : 'Erro ao criar lead',
        isLoading: false,
      });
      return null;
    }
  },

  updateLeadStatus: async (leadId: string, newStatus: LeadStatus) => {
    // Atualização otimista
    const previousLeads = get().leads;
    set((state) => ({
      leads: state.leads.map((lead) =>
        lead.id === leadId
          ? { ...lead, status: newStatus, updated_at: new Date().toISOString() }
          : lead
      ),
    }));

    try {
      await apiClient.updateLead(leadId, { status: newStatus });

      // Atualizar estatísticas
      get().fetchStats();
    } catch (error) {
      console.error('Erro ao atualizar status:', error);

      // Reverter em caso de erro
      set({ leads: previousLeads });
      set({
        error: error instanceof Error ? error.message : 'Erro ao atualizar status',
      });
    }
  },

  updateLead: async (leadId: string, data: UpdateLeadData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.updateLead(leadId, data);

      // Atualizar lead no estado local
      set((state) => ({
        leads: state.leads.map((lead) =>
          lead.id === leadId ? response.lead : lead
        ),
        isLoading: false,
      }));

      // Atualizar estatísticas se mudou status/temperatura
      if (data.status || data.temperatura) {
        get().fetchStats();
      }
    } catch (error) {
      console.error('Erro ao atualizar lead:', error);
      set({
        error: error instanceof Error ? error.message : 'Erro ao atualizar lead',
        isLoading: false,
      });
    }
  },

  deleteLead: async (leadId: string) => {
    // Atualização otimista
    const previousLeads = get().leads;
    set((state) => ({
      leads: state.leads.filter((lead) => lead.id !== leadId),
    }));

    try {
      await apiClient.deleteLead(leadId);

      // Atualizar estatísticas
      get().fetchStats();
    } catch (error) {
      console.error('Erro ao deletar lead:', error);

      // Reverter em caso de erro
      set({ leads: previousLeads });
      set({
        error: error instanceof Error ? error.message : 'Erro ao deletar lead',
      });
    }
  },

  qualifyLead: async (leadId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.qualifyLead(leadId);

      // Atualizar lead no estado local
      set((state) => ({
        leads: state.leads.map((lead) =>
          lead.id === leadId ? response.lead : lead
        ),
        isLoading: false,
      }));

      // Atualizar estatísticas
      get().fetchStats();
    } catch (error) {
      console.error('Erro ao qualificar lead:', error);
      set({
        error: error instanceof Error ? error.message : 'Erro ao qualificar lead',
        isLoading: false,
      });
    }
  },

  // ==================== HELPERS ====================

  clearError: () => set({ error: null }),

  setLoading: (loading: boolean) => set({ isLoading: loading }),

  // ==================== WEBSOCKET HANDLERS ====================

  handleLeadCreated: (lead: Lead) => {
    console.log('[Store] Lead created via WebSocket:', lead.id);
    set((state) => {
      // Verificar se lead já existe
      const exists = state.leads.some((l) => l.id === lead.id);
      if (exists) return state;

      return {
        leads: [...state.leads, lead],
      };
    });

    // Atualizar estatísticas
    get().fetchStats();
  },

  handleLeadUpdated: (lead: Lead) => {
    console.log('[Store] Lead updated via WebSocket:', lead.id);
    set((state) => ({
      leads: state.leads.map((l) => (l.id === lead.id ? lead : l)),
    }));

    // Atualizar estatísticas
    get().fetchStats();
  },

  handleLeadDeleted: (leadId: string) => {
    console.log('[Store] Lead deleted via WebSocket:', leadId);
    set((state) => ({
      leads: state.leads.filter((l) => l.id !== leadId),
    }));

    // Atualizar estatísticas
    get().fetchStats();
  },
}));
