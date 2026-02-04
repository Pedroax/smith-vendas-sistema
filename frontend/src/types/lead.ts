export type LeadStatus = 'novo' | 'contato_inicial' | 'qualificando' | 'qualificado' | 'agendamento_marcado' | 'ganho' | 'perdido';
export type LeadOrigin = 'instagram' | 'whatsapp' | 'site' | 'indicacao' | 'outro';
export type LeadTemperature = 'quente' | 'morno' | 'frio';

export interface QualificationData {
  // BANT Framework
  budget?: number;
  authority?: boolean;
  need?: string;
  timing?: string;

  // Dados operacionais para ROI
  atendimentos_por_dia?: number;
  tempo_por_atendimento?: number; // minutos
  ticket_medio?: number;
  funcionarios_atendimento?: number;

  // Informações adicionais
  ferramentas_atuais?: string[];
  maior_desafio?: string;
  expectativa_roi?: string;
}

export interface ROIAnalysis {
  tempo_economizado_mes?: number; // horas
  valor_economizado_ano?: number; // R$
  roi_percentual?: number; // %
  payback_meses?: number;
  pdf_url?: string;
  generated_at?: string;
}

export interface FollowUpConfig {
  tentativas_realizadas: number;
  proxima_tentativa?: string;
  intervalo_horas: number[];
  mensagem_template?: string;
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Lead {
  // Identificação
  id: string;
  nome: string;
  empresa?: string;
  telefone: string;
  email?: string;

  // Status e origem
  status: LeadStatus;
  origem: LeadOrigin;
  temperatura: LeadTemperature;

  // Qualificação
  qualification_data?: QualificationData;
  lead_score: number; // 0-100

  // ROI
  roi_analysis?: ROIAnalysis;
  valor_estimado: number;

  // Agendamento
  meeting_scheduled_at?: string;
  meeting_google_event_id?: string;

  // Follow-up
  followup_config: FollowUpConfig;

  // Histórico
  conversation_history: ConversationMessage[];
  ultima_interacao?: string;
  ultima_mensagem_ia?: string;

  // Notas e observações
  notas?: string;
  tags: string[];

  // IA metadata
  ai_summary?: string;
  ai_next_action?: string;
  requires_human_approval: boolean;

  // Timestamps
  created_at: string;
  updated_at: string;
  lost_at?: string;
  won_at?: string;

  // Avatar
  avatar?: string;
}

export interface KanbanColumn {
  id: LeadStatus;
  title: string;
  color: string;
  leads: Lead[];
}
