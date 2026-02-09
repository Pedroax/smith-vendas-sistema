'use client';

import { useEffect, useState } from 'react';
import { Plus, FileText, Download, Check, X, AlertCircle, DollarSign, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import { API_URL } from '@/lib/api-config';
import { Invoice, InvoiceStats, InvoiceStatus, STATUS_LABELS, STATUS_COLORS, METODO_LABELS, MetodoPagamento } from '@/types/invoice';
import { useToast } from '@/contexts/ToastContext';

export default function FinanceiroPage() {
  const { showToast } = useToast();

  const [stats, setStats] = useState<InvoiceStats | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedStatus, setSelectedStatus] = useState<InvoiceStatus | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    fetchAll();
    fetchProjects();
  }, [selectedStatus]);

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_URL}/api/projects/`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (err) {
      console.error('Erro ao carregar projetos:', err);
    }
  };

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [statsRes, invoicesRes] = await Promise.all([
        fetch(`${API_URL}/api/invoices/stats`),
        fetch(`${API_URL}/api/invoices${selectedStatus !== 'all' ? `?status=${selectedStatus}` : ''}`),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (invoicesRes.ok) setInvoices(await invoicesRes.json());
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar financeiro', 'error');
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

  const handleConfirmarPagamento = async (invoiceId: string) => {
    if (!confirm('Confirmar pagamento desta fatura?')) return;

    try {
      const res = await fetch(`${API_URL}/api/invoices/${invoiceId}/confirmar-pagamento`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_pagamento: new Date().toISOString().split('T')[0],
        }),
      });

      if (res.ok) {
        showToast('Pagamento confirmado!', 'success');
        fetchAll();
      } else {
        throw new Error('Erro ao confirmar pagamento');
      }
    } catch (err) {
      showToast('Erro ao confirmar pagamento', 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-gray-500">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Financeiro</h1>
            <p className="text-gray-600 mt-1">Gerenciamento de faturas e pagamentos</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Nova Fatura
          </button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Pago</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.total_pago)}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500">{stats.quantidade_pago} faturas</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Pendente</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.total_pendente)}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500">{stats.quantidade_pendente} faturas</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Atrasado</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.total_atrasado)}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500">{stats.quantidade_atrasado} faturas</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Aguardando Conf.</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.quantidade_aguardando_conf}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500">Comprovantes enviados</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setSelectedStatus('all')}
              className={`px-4 py-2 rounded-lg ${selectedStatus === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}
            >
              Todas
            </button>
            {Object.entries(STATUS_LABELS).map(([status, label]) => (
              <button
                key={status}
                onClick={() => setSelectedStatus(status as InvoiceStatus)}
                className={`px-4 py-2 rounded-lg ${selectedStatus === status ? STATUS_COLORS[status as InvoiceStatus] : 'bg-gray-100 text-gray-700'}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Invoices Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fatura</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente/Projeto</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vencimento</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{invoice.numero_fatura}</p>
                        <p className="text-sm text-gray-500">{invoice.descricao}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{invoice.client_nome || 'N/A'}</p>
                        <p className="text-sm text-gray-500">{invoice.project_nome || 'N/A'}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-gray-900">{formatCurrency(invoice.valor_final)}</p>
                      {invoice.desconto > 0 && (
                        <p className="text-xs text-green-600">-{formatCurrency(invoice.desconto)} desc.</p>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-900">{formatDate(invoice.data_vencimento)}</p>
                      {invoice.dias_ate_vencimento !== undefined && invoice.dias_ate_vencimento < 0 && (
                        <p className="text-xs text-red-600">{Math.abs(invoice.dias_ate_vencimento)} dias atraso</p>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[invoice.status]}`}>
                        {STATUS_LABELS[invoice.status]}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {invoice.status === InvoiceStatus.AGUARDANDO_CONF && (
                          <button
                            onClick={() => handleConfirmarPagamento(invoice.id)}
                            className="text-green-600 hover:text-green-700"
                            title="Confirmar pagamento"
                          >
                            <Check className="w-5 h-5" />
                          </button>
                        )}
                        {invoice.comprovante_url && (
                          <a
                            href={invoice.comprovante_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700"
                            title="Ver comprovante"
                          >
                            <FileText className="w-5 h-5" />
                          </a>
                        )}
                        <button
                          onClick={() => setSelectedInvoice(invoice)}
                          className="text-gray-600 hover:text-gray-700"
                          title="Ver detalhes"
                        >
                          <FileText className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {invoices.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              Nenhuma fatura encontrada
            </div>
          )}
        </div>
      </div>

      {/* Modal: Criar Nova Fatura */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">Nova Fatura</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);

                const payload = {
                  project_id: parseInt(formData.get('project_id') as string),
                  descricao: formData.get('descricao') as string,
                  valor: parseFloat(formData.get('valor') as string),
                  desconto: parseFloat(formData.get('desconto') as string) || 0,
                  data_vencimento: formData.get('data_vencimento') as string,
                  metodo_pagamento: formData.get('metodo_pagamento') as string || null,
                };

                try {
                  const res = await fetch(`${API_URL}/api/invoices/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                  });

                  if (res.ok) {
                    showToast('Fatura criada com sucesso!', 'success');
                    setShowCreateModal(false);
                    fetchAll();
                  } else {
                    const error = await res.json();
                    throw new Error(error.detail || 'Erro ao criar fatura');
                  }
                } catch (err: any) {
                  showToast(err.message || 'Erro ao criar fatura', 'error');
                }
              }}
              className="p-6 space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Projeto <span className="text-red-500">*</span>
                </label>
                <select
                  name="project_id"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Selecione o projeto...</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.nome} - {project.client_nome || 'Sem cliente'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="descricao"
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: Desenvolvimento do Site - Fase 1"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valor (R$) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="valor"
                    required
                    step="0.01"
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="5000.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Desconto (R$)
                  </label>
                  <input
                    type="number"
                    name="desconto"
                    step="0.01"
                    min="0"
                    defaultValue="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Vencimento <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    name="data_vencimento"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Método de Pagamento
                  </label>
                  <select
                    name="metodo_pagamento"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Selecione...</option>
                    {Object.entries(METODO_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Plus className="w-5 h-5" />
                  Criar Fatura
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
