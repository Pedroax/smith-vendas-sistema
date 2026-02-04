'use client';

import { useEffect } from 'react';
import { TrendingUp, DollarSign, Users, Calendar, ArrowUpRight, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useLeadsStore } from '@/store/useLeadsStore';

export default function Home() {
  const { leads, fetchLeads, fetchStats } = useLeadsStore();

  // Buscar leads ao montar componente
  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  const stats = {
    totalLeads: leads.length,
    leadsHoje: leads.filter(l => {
      const today = new Date().toDateString();
      return new Date(l.created_at).toDateString() === today;
    }).length,
    valorPipeline: leads.reduce((sum, lead) => sum + lead.valor_estimado, 0),
    taxaConversao: Math.round((leads.filter(l => l.status === 'agendamento_marcado').length / Math.max(leads.length, 1)) * 100),
    leadsGanhos: leads.filter(l => l.status === 'agendamento_marcado').length,
    emNegociacao: leads.filter(l => ['negociacao', 'proposta'].includes(l.status)).length,
  };

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Bem-vindo de volta, Pedro! 👋
              </h1>
              <p className="text-gray-500 mt-1">
                Aqui está o resumo do seu funil de vendas hoje
              </p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-700">Smith Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-8 py-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Leads */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                +{stats.leadsHoje} hoje
              </span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">{stats.totalLeads}</div>
            <div className="text-sm text-gray-500">Total de Leads</div>
            <Link href="/crm" className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-3 inline-flex items-center gap-1">
              Ver pipeline <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          {/* Valor Pipeline */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">
              R$ {(stats.valorPipeline / 1000).toFixed(0)}k
            </div>
            <div className="text-sm text-gray-500">Valor no Pipeline</div>
            <div className="text-xs text-green-600 font-medium mt-3">
              {stats.emNegociacao} leads em negociação
            </div>
          </div>

          {/* Taxa de Conversão */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
              <CheckCircle2 className="w-5 h-5 text-purple-500" />
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">{stats.taxaConversao}%</div>
            <div className="text-sm text-gray-500">Taxa de Conversão</div>
            <div className="text-xs text-purple-600 font-medium mt-3">
              {stats.leadsGanhos} leads convertidos
            </div>
          </div>

          {/* Agendamentos */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-100 rounded-lg">
                <Calendar className="w-6 h-6 text-orange-600" />
              </div>
              <Clock className="w-5 h-5 text-orange-500" />
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">0</div>
            <div className="text-sm text-gray-500">Agendamentos Hoje</div>
            <Link href="/agendamentos" className="text-xs text-orange-600 hover:text-orange-700 font-medium mt-3 inline-flex items-center gap-1">
              Ver calendário <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2 bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Atividade Recente</h2>
              <Link href="/conversas" className="text-sm text-purple-600 hover:text-purple-700 font-medium">
                Ver todas
              </Link>
            </div>
            <div className="space-y-4">
              {leads.slice(0, 5).map((lead) => (
                <div key={lead.id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold">
                    {lead.nome.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{lead.nome}</p>
                    <p className="text-sm text-gray-500">{lead.empresa} • {lead.telefone}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-xs font-semibold px-3 py-1 rounded-full ${
                      lead.status === 'qualificado' ? 'bg-purple-100 text-purple-700' :
                      lead.status === 'agendamento_marcado' ? 'bg-green-100 text-green-700' :
                      lead.status === 'perdido' ? 'bg-red-100 text-red-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {lead.status === 'qualificado' ? 'Qualificado' :
                       lead.status === 'qualificando' ? 'Qualificando' :
                       lead.status === 'agendamento_marcado' ? 'Agendado' :
                       lead.status === 'perdido' ? 'Perdido' :
                       lead.status === 'contato_inicial' ? 'Contato Inicial' :
                       'Novo'}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      R$ {(lead.valor_estimado / 1000).toFixed(0)}k
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Status do Sistema</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">Backend API</p>
                  <p className="text-xs text-gray-500">Operacional</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">Smith IA</p>
                  <p className="text-xs text-gray-500">Online</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-yellow-100 flex items-center justify-center">
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">WhatsApp</p>
                  <p className="text-xs text-gray-500">Aguardando config</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-yellow-100 flex items-center justify-center">
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">Google Calendar</p>
                  <p className="text-xs text-gray-500">Aguardando config</p>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <Link
                  href="/integracoes"
                  className="block w-full text-center px-4 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all font-medium"
                >
                  Configurar Integrações
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
