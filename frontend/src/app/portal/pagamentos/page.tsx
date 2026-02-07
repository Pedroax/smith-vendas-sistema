'use client';

import { useEffect, useState } from 'react';
import {
  CreditCard, Loader2, CheckCircle2, AlertCircle, Clock,
  FolderKanban, ChevronDown, ChevronUp, DollarSign
} from 'lucide-react';

import { API_URL } from '@/lib/api-config';

interface Project {
  id: string;
  nome: string;
  valor_total: number;
}

interface Payment {
  id: string;
  project_id: string;
  descricao: string;
  valor: number;
  status: 'pendente' | 'pago' | 'atrasado' | 'cancelado';
  data_vencimento: string;
  data_pagamento?: string;
  comprovante_url?: string;
  parcela: number;
  total_parcelas: number;
  created_at: string;
}

export default function PagamentosPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [payments, setPayments] = useState<Record<string, Payment[]>>({});
  const [loading, setLoading] = useState(true);
  const [expandedProject, setExpandedProject] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const projectsRes = await fetch(`${API_URL}/api/portal/projects`, { headers });
      if (projectsRes.ok) {
        const projectsData: Project[] = await projectsRes.json();
        setProjects(projectsData);

        const results = await Promise.all(
          projectsData.map(async (p) => {
            const res = await fetch(`${API_URL}/api/portal/projects/${p.id}/payments`, { headers });
            return { id: p.id, data: res.ok ? await res.json().catch(() => []) : [] };
          })
        );

        const map: Record<string, Payment[]> = {};
        results.forEach((r) => { map[r.id] = r.data; });
        setPayments(map);

        const first = results.find((r) => r.data.some((p: Payment) => p.status === 'pendente' || p.status === 'atrasado'));
        if (first) setExpandedProject(first.id);
        else if (projectsData.length > 0) setExpandedProject(projectsData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { label: string; bg: string; text: string; icon: any }> = {
      pendente: { label: 'Pendente', bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock },
      pago: { label: 'Pago', bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle2 },
      atrasado: { label: 'Atrasado', bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle },
      cancelado: { label: 'Cancelado', bg: 'bg-gray-100', text: 'text-gray-600', icon: AlertCircle },
    };
    return configs[status] || configs.pendente;
  };

  const formatCurrency = (value: number) =>
    value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const isOverdue = (vencimento: string, status: string) => {
    if (status !== 'pendente') return false;
    return new Date(vencimento) < new Date();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const allPayments = Object.values(payments).flat();
  const totalDevido = allPayments.filter((p) => p.status === 'pendente' || p.status === 'atrasado').reduce((s, p) => s + p.valor, 0);
  const totalPago = allPayments.filter((p) => p.status === 'pago').reduce((s, p) => s + p.valor, 0);
  const totalAtrasado = allPayments.filter((p) => p.status === 'atrasado').reduce((s, p) => s + p.valor, 0);

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Pagamentos</h1>
        <p className="text-gray-500 mt-1">Acompanhe os pagamentos dos seus projetos</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-yellow-100 rounded-xl flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-yellow-600" />
            </div>
          </div>
          <p className="text-xl font-bold text-gray-900">{formatCurrency(totalDevido)}</p>
          <p className="text-sm text-gray-500">Para pagar</p>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-green-100 rounded-xl flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <p className="text-xl font-bold text-gray-900">{formatCurrency(totalPago)}</p>
          <p className="text-sm text-gray-500">Já pago</p>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-red-100 rounded-xl flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
          </div>
          <p className="text-xl font-bold text-gray-900">{formatCurrency(totalAtrasado)}</p>
          <p className="text-sm text-gray-500">Atrasados</p>
        </div>
      </div>

      {/* Projects with Payments */}
      {projects.length === 0 ? (
        <div className="text-center py-16">
          <CreditCard className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum pagamento</h3>
          <p className="text-gray-500">Não há pagamentos registrados</p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => {
            const items = payments[project.id] || [];
            if (items.length === 0) return null;
            const isExpanded = expandedProject === project.id;
            const atrasados = items.filter((p) => p.status === 'atrasado').length;
            const pendentes = items.filter((p) => p.status === 'pendente').length;
            const totalProject = items.reduce((s, p) => s + p.valor, 0);
            const pagoProjeto = items.filter((p) => p.status === 'pago').reduce((s, p) => s + p.valor, 0);
            const progressPercent = totalProject > 0 ? Math.round((pagoProjeto / totalProject) * 100) : 0;

            return (
              <div key={project.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpandedProject(isExpanded ? null : project.id)}
                  className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                      <FolderKanban className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-gray-900">{project.nome}</h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500 rounded-full"
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{progressPercent}% pago</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {atrasados > 0 && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        {atrasados} atrasado{atrasados !== 1 ? 's' : ''}
                      </span>
                    )}
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-gray-100">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gray-50 text-left">
                          <th className="px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Descrição</th>
                          <th className="px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Parcela</th>
                          <th className="px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Valor</th>
                          <th className="px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Vencimento</th>
                          <th className="px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {items.map((payment) => {
                          const config = getStatusConfig(payment.status);
                          const StatusIcon = config.icon;
                          const overdue = isOverdue(payment.data_vencimento, payment.status);

                          return (
                            <tr key={payment.id} className={overdue ? 'bg-red-50' : ''}>
                              <td className="px-5 py-4">
                                <p className="text-sm font-medium text-gray-900">{payment.descricao}</p>
                                {payment.comprovante_url && (
                                  <a
                                    href={payment.comprovante_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-purple-600 hover:text-purple-700"
                                  >
                                    Ver comprovante
                                  </a>
                                )}
                              </td>
                              <td className="px-5 py-4 text-sm text-gray-600">
                                {payment.parcela}/{payment.total_parcelas}
                              </td>
                              <td className="px-5 py-4 text-sm font-semibold text-gray-900">
                                {formatCurrency(payment.valor)}
                              </td>
                              <td className="px-5 py-4">
                                <p className={`text-sm ${overdue ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                                  {new Date(payment.data_vencimento).toLocaleDateString('pt-BR')}
                                </p>
                                {payment.data_pagamento && (
                                  <p className="text-xs text-gray-400">
                                    Pago em {new Date(payment.data_pagamento).toLocaleDateString('pt-BR')}
                                  </p>
                                )}
                              </td>
                              <td className="px-5 py-4">
                                <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
                                  <StatusIcon className="w-3.5 h-3.5" />
                                  {config.label}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
