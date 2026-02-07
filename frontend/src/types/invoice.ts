/**
 * Types para sistema de Faturas (Invoices)
 */

export enum InvoiceStatus {
  PENDENTE = 'pendente',
  AGUARDANDO_CONF = 'aguardando_conf',
  PAGO = 'pago',
  ATRASADO = 'atrasado',
  CANCELADO = 'cancelado',
}

export enum MetodoPagamento {
  PIX = 'pix',
  TRANSFERENCIA = 'transferencia',
  BOLETO = 'boleto',
  CARTAO = 'cartao',
  DINHEIRO = 'dinheiro',
  OUTRO = 'outro',
}

export interface Invoice {
  id: string;
  project_id: number;
  numero_fatura: string;
  descricao: string;

  // Valores
  valor: number;
  desconto: number;
  valor_final: number;

  // Datas
  data_emissao: string; // ISO date
  data_vencimento: string; // ISO date
  data_pagamento?: string; // ISO date

  // Status
  status: InvoiceStatus;

  // Documentos
  nota_fiscal_url?: string;
  comprovante_url?: string;
  comprovante_enviado_em?: string; // ISO timestamp

  // Confirmação admin
  confirmado_por?: string;
  confirmado_em?: string; // ISO timestamp
  notas_admin?: string;

  // Método
  metodo_pagamento?: MetodoPagamento;

  // Metadata
  created_at: string;
  updated_at: string;

  // Joins
  project_nome?: string;
  client_nome?: string;

  // Computed fields
  esta_atrasado?: boolean;
  dias_ate_vencimento?: number;
}

export interface InvoiceCreate {
  project_id: number;
  descricao: string;
  valor: number;
  desconto?: number;
  data_vencimento: string; // ISO date
  data_emissao?: string; // ISO date
  metodo_pagamento?: MetodoPagamento;
  notas_admin?: string;
}

export interface InvoiceUpdate {
  descricao?: string;
  valor?: number;
  desconto?: number;
  data_vencimento?: string;
  metodo_pagamento?: MetodoPagamento;
  status?: InvoiceStatus;
  notas_admin?: string;
}

export interface InvoiceStats {
  total_faturado: number;
  total_pendente: number;
  total_atrasado: number;
  total_pago: number;

  quantidade_pendente: number;
  quantidade_atrasado: number;
  quantidade_pago: number;
  quantidade_aguardando_conf: number;

  proximos_vencimentos: Invoice[];
}

export const STATUS_LABELS: Record<InvoiceStatus, string> = {
  [InvoiceStatus.PENDENTE]: 'Pendente',
  [InvoiceStatus.AGUARDANDO_CONF]: 'Aguardando Confirmação',
  [InvoiceStatus.PAGO]: 'Pago',
  [InvoiceStatus.ATRASADO]: 'Atrasado',
  [InvoiceStatus.CANCELADO]: 'Cancelado',
};

export const STATUS_COLORS: Record<InvoiceStatus, string> = {
  [InvoiceStatus.PENDENTE]: 'bg-yellow-100 text-yellow-700',
  [InvoiceStatus.AGUARDANDO_CONF]: 'bg-blue-100 text-blue-700',
  [InvoiceStatus.PAGO]: 'bg-green-100 text-green-700',
  [InvoiceStatus.ATRASADO]: 'bg-red-100 text-red-700',
  [InvoiceStatus.CANCELADO]: 'bg-gray-100 text-gray-700',
};

export const METODO_LABELS: Record<MetodoPagamento, string> = {
  [MetodoPagamento.PIX]: 'PIX',
  [MetodoPagamento.TRANSFERENCIA]: 'Transferência',
  [MetodoPagamento.BOLETO]: 'Boleto',
  [MetodoPagamento.CARTAO]: 'Cartão',
  [MetodoPagamento.DINHEIRO]: 'Dinheiro',
  [MetodoPagamento.OUTRO]: 'Outro',
};
