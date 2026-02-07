/**
 * API Client para comunicação com backend
 */

import { Lead, LeadStatus, LeadOrigin, LeadTemperature } from '@/types/lead';
import { APIError, handleAPIError } from './errors';
import { API_URL as API_BASE_URL } from './api-config';

export interface CreateLeadData {
  nome: string;
  telefone: string;
  empresa?: string;
  email?: string;
  origem: LeadOrigin;
  notas?: string;
}

export interface UpdateLeadData {
  nome?: string;
  empresa?: string;
  email?: string;
  status?: LeadStatus;
  temperatura?: LeadTemperature;
  valor_estimado?: number;
  notas?: string;
  tags?: string[];
}

export interface LeadFilters {
  status?: LeadStatus;
  origem?: LeadOrigin;
  temperatura?: LeadTemperature;
  limit?: number;
  offset?: number;
}

export interface LeadStats {
  total_leads: number;
  por_status: Record<LeadStatus, number>;
  por_origem: Record<string, number>;
  por_temperatura: Record<LeadTemperature, number>;
  score_medio: number;
  valor_total_pipeline: number;
  taxa_qualificacao: number;
  taxa_conversao: number;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw handleAPIError({
          response: {
            status: response.status,
            data: error
          }
        });
      }

      return response.json();
    } catch (error) {
      // If it's already an APIError, rethrow it
      if (error instanceof APIError) {
        throw error;
      }
      // Otherwise, handle it as a network error
      throw handleAPIError(error);
    }
  }

  // ==================== LEADS ====================

  /**
   * Lista todos os leads com filtros opcionais
   */
  async getLeads(filters?: LeadFilters): Promise<Lead[]> {
    const params = new URLSearchParams();

    if (filters?.status) params.append('status', filters.status);
    if (filters?.origem) params.append('origem', filters.origem);
    if (filters?.temperatura) params.append('temperatura', filters.temperatura);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());

    const query = params.toString();
    const endpoint = `/api/leads/${query ? `?${query}` : ''}`;

    return this.request<Lead[]>(endpoint);
  }

  /**
   * Busca um lead específico por ID
   */
  async getLead(leadId: string): Promise<Lead> {
    return this.request<Lead>(`/api/leads/${leadId}`);
  }

  /**
   * Cria um novo lead
   */
  async createLead(data: CreateLeadData): Promise<{ success: boolean; lead: Lead; message: string }> {
    return this.request(`/api/leads/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Atualiza um lead existente
   */
  async updateLead(
    leadId: string,
    data: UpdateLeadData
  ): Promise<{ success: boolean; lead: Lead; message: string }> {
    return this.request(`/api/leads/${leadId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Deleta um lead
   */
  async deleteLead(leadId: string): Promise<{ success: boolean; lead: null; message: string }> {
    return this.request(`/api/leads/${leadId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Força re-qualificação de um lead
   */
  async qualifyLead(leadId: string): Promise<{ success: boolean; lead: Lead; message: string }> {
    return this.request(`/api/leads/${leadId}/qualify`, {
      method: 'POST',
    });
  }

  /**
   * Busca estatísticas agregadas
   */
  async getStats(): Promise<LeadStats> {
    return this.request<LeadStats>('/api/leads/stats/summary');
  }

  // ==================== WEBHOOK ====================

  /**
   * Verifica status do webhook e conexão WhatsApp
   */
  async getWebhookStatus(): Promise<{
    webhook: string;
    whatsapp_connection: string;
    total_leads: number;
    timestamp: string;
  }> {
    return this.request('/webhook/whatsapp/status');
  }
}

// Instância global do cliente
export const apiClient = new APIClient(API_BASE_URL);
