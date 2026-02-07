'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Upload, FileText, Download, AlertCircle, CheckCircle, Clock, DollarSign } from 'lucide-react';
import { API_URL } from '@/lib/api-config';
import { Invoice, InvoiceStatus, STATUS_LABELS, STATUS_COLORS } from '@/types/invoice';
import { useToast } from '@/contexts/ToastContext';

export default function PortalFinanceiroPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  const { showToast } = useToast();

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadingInvoiceId, setUploadingInvoiceId] = useState<string | null>(null);

  useEffect(() => {
    fetchInvoices();
  }, [projectId]);

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/invoices?project_id=${parseInt(projectId)}`);
      if (res.ok) {
        const data = await res.json();
        setInvoices(data);
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar faturas', 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  const handleUploadComprovante = async (invoiceId: string, file: File) => {
    // TODO: Upload real para Supabase Storage
    // Por enquanto, apenas simular
    try {
      setUploadingInvoiceId(invoiceId);

      // Simular upload (substituir por upload real no Supabase)
      const fakeUrl = `https://storage.supabase.co/comprovantes/${file.name}`;

      const res = await fetch(`${API_URL}/api/invoices/${invoiceId}/upload-comprovante`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comprovante_url: fakeUrl }),
      });

      if (res.ok) {
        showToast('Comprovante enviado! Aguardando confirmação.', 'success');
        fetchInvoices();
      } else {
        throw new Error('Erro ao enviar comprovante');
      }
    } catch (err) {
      showToast('Erro ao enviar comprovante', 'error');
    } finally {
      setUploadingInvoiceId(null);
    }
  };

  const totalPendente = invoices
    .filter(i => i.status === InvoiceStatus.PENDENTE || i.status === InvoiceStatus.ATRASADO)
    .reduce((sum, i) => sum + i.valor_final, 0);

  const totalPago = invoices
    .filter(i => i.status === InvoiceStatus.PAGO)
    .reduce((sum, i) => sum + i.valor_final, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-gray-500">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Financeiro</h1>
          <p className="text-gray-600 mt-1">Acompanhe suas faturas e pagamentos</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Investido</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalPago + totalPendente)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pago</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalPago)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pendente</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalPendente)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Invoices List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Suas Faturas</h2>
          </div>

          <div className="divide-y divide-gray-200">
            {invoices.map((invoice) => (
              <div key={invoice.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{invoice.numero_fatura}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[invoice.status]}`}>
                        {STATUS_LABELS[invoice.status]}
                      </span>
                    </div>

                    <p className="text-sm text-gray-600 mb-3">{invoice.descricao}</p>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Valor</p>
                        <p className="font-medium text-gray-900">{formatCurrency(invoice.valor_final)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Vencimento</p>
                        <p className="font-medium text-gray-900">{formatDate(invoice.data_vencimento)}</p>
                        {invoice.dias_ate_vencimento !== undefined && invoice.dias_ate_vencimento < 0 && (
                          <p className="text-xs text-red-600">{Math.abs(invoice.dias_ate_vencimento)} dias atraso</p>
                        )}
                      </div>
                      {invoice.data_pagamento && (
                        <div>
                          <p className="text-gray-500">Pago em</p>
                          <p className="font-medium text-gray-900">{formatDate(invoice.data_pagamento)}</p>
                        </div>
                      )}
                      {invoice.metodo_pagamento && (
                        <div>
                          <p className="text-gray-500">Método</p>
                          <p className="font-medium text-gray-900">{invoice.metodo_pagamento.toUpperCase()}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 ml-4">
                    {/* Botão de upload de comprovante */}
                    {(invoice.status === InvoiceStatus.PENDENTE || invoice.status === InvoiceStatus.ATRASADO) && (
                      <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm">
                        <Upload className="w-4 h-4" />
                        Enviar Comprovante
                        <input
                          type="file"
                          className="hidden"
                          accept="image/*,.pdf"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleUploadComprovante(invoice.id, file);
                          }}
                        />
                      </label>
                    )}

                    {/* Status de comprovante enviado */}
                    {invoice.status === InvoiceStatus.AGUARDANDO_CONF && (
                      <div className="bg-blue-100 text-blue-700 px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Aguardando confirmação
                      </div>
                    )}

                    {/* Download de NF */}
                    {invoice.nota_fiscal_url && (
                      <a
                        href={invoice.nota_fiscal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 flex items-center gap-2 text-sm"
                      >
                        <Download className="w-4 h-4" />
                        Nota Fiscal
                      </a>
                    )}

                    {/* Ver comprovante enviado */}
                    {invoice.comprovante_url && (
                      <a
                        href={invoice.comprovante_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 flex items-center gap-2 text-sm"
                      >
                        <FileText className="w-4 h-4" />
                        Ver Comprovante
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {invoices.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              Nenhuma fatura cadastrada ainda
            </div>
          )}
        </div>

        {/* Informações de pagamento */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">Como pagar</h3>
              <p className="text-sm text-blue-700">
                Após realizar o pagamento, faça o upload do comprovante clicando no botão "Enviar Comprovante".
                Confirmaremos o pagamento em até 1 dia útil e enviaremos a nota fiscal.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
