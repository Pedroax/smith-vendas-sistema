-- Migration 007: Create invoices table
-- Criado em: 2026-02-07
-- Descrição: Tabela de faturas/pagamentos para controle financeiro

-- Criar tabela de faturas
CREATE TABLE IF NOT EXISTS invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,

  -- Identificação
  numero_fatura TEXT UNIQUE NOT NULL,  -- INV-2026-001
  descricao TEXT NOT NULL,

  -- Valores
  valor DECIMAL(10,2) NOT NULL CHECK (valor > 0),
  desconto DECIMAL(10,2) DEFAULT 0 CHECK (desconto >= 0),
  valor_final DECIMAL(10,2) NOT NULL CHECK (valor_final > 0),

  -- Datas
  data_emissao DATE NOT NULL DEFAULT CURRENT_DATE,
  data_vencimento DATE NOT NULL,
  data_pagamento DATE,

  -- Status
  status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN (
    'pendente',           -- Aguardando pagamento
    'aguardando_conf',    -- Cliente enviou comprovante
    'pago',               -- Admin confirmou pagamento
    'atrasado',           -- Venceu e não foi pago
    'cancelado'           -- Cancelado pelo admin
  )),

  -- Documentos (URLs do Supabase Storage)
  nota_fiscal_url TEXT,           -- Upload feito pelo admin
  comprovante_url TEXT,           -- Upload feito pelo cliente
  comprovante_enviado_em TIMESTAMP,

  -- Confirmação do pagamento (admin)
  confirmado_por UUID,            -- ID do admin que confirmou
  confirmado_em TIMESTAMP,
  notas_admin TEXT,               -- Observações internas do admin

  -- Método de pagamento
  metodo_pagamento TEXT CHECK (metodo_pagamento IN (
    'pix', 'transferencia', 'boleto', 'cartao', 'dinheiro', 'outro'
  )),

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Índices para otimização de queries
CREATE INDEX idx_invoices_project ON invoices(project_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_vencimento ON invoices(data_vencimento);
CREATE INDEX idx_invoices_numero ON invoices(numero_fatura);
CREATE INDEX idx_invoices_created ON invoices(created_at DESC);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_invoices_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_invoices_updated_at
  BEFORE UPDATE ON invoices
  FOR EACH ROW
  EXECUTE FUNCTION update_invoices_updated_at();

-- Trigger para atualizar status automaticamente para 'atrasado'
CREATE OR REPLACE FUNCTION check_invoice_overdue()
RETURNS TRIGGER AS $$
BEGIN
  -- Se a fatura está pendente e a data de vencimento passou
  IF NEW.status = 'pendente' AND NEW.data_vencimento < CURRENT_DATE THEN
    NEW.status = 'atrasado';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_invoice_overdue
  BEFORE INSERT OR UPDATE ON invoices
  FOR EACH ROW
  EXECUTE FUNCTION check_invoice_overdue();

-- Comentários para documentação
COMMENT ON TABLE invoices IS 'Faturas e pagamentos dos projetos';
COMMENT ON COLUMN invoices.numero_fatura IS 'Número único da fatura (ex: INV-2026-001)';
COMMENT ON COLUMN invoices.status IS 'Status: pendente, aguardando_conf, pago, atrasado, cancelado';
COMMENT ON COLUMN invoices.valor_final IS 'Valor final após descontos';
COMMENT ON COLUMN invoices.comprovante_url IS 'URL do comprovante enviado pelo cliente';
COMMENT ON COLUMN invoices.nota_fiscal_url IS 'URL da nota fiscal enviada pelo admin';
