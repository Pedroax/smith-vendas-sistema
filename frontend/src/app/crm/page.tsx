'use client';

import { useEffect } from 'react';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { useLeadsStore } from '@/store/useLeadsStore';
import { TrendingUp, DollarSign, Users, Target, Plus, Search, Filter, Loader2 } from 'lucide-react';

export default function CRMPage() {
  const { leads, isLoading, error, fetchLeads, fetchStats, clearError } = useLeadsStore();

  // Buscar leads ao montar componente
  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  const stats = {
    totalLeads: leads.length,
    valorTotal: leads.reduce((sum, lead) => sum + lead.valor_estimado, 0),
    leadsQualificados: leads.filter(l => ['qualificado', 'agendamento_marcado'].includes(l.status)).length,
    taxaConversao: Math.round((leads.filter(l => l.status === 'ganho').length / Math.max(leads.length, 1)) * 100),
  };

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">
                Pipeline de Vendas
              </h1>
              <p className="text-gray-500">
                Gerencie seus leads e acompanhe o funil de conversão
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar leads..."
                  className="pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent w-64"
                />
              </div>

              {/* Filter */}
              <button className="p-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Filter className="w-5 h-5 text-gray-600" />
              </button>

              {/* Add Lead */}
              <button className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all">
                <Plus className="w-5 h-5" />
                <span className="font-medium">Novo Lead</span>
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            {/* Total Leads */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-blue-600 bg-blue-200 px-2 py-1 rounded-full">
                  Total
                </span>
              </div>
              <div className="text-2xl font-bold text-blue-900">{stats.totalLeads}</div>
              <div className="text-xs text-blue-600 font-medium">Leads Ativos</div>
            </div>

            {/* Valor Total */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-green-500 rounded-lg">
                  <DollarSign className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-green-600 bg-green-200 px-2 py-1 rounded-full">
                  Pipeline
                </span>
              </div>
              <div className="text-2xl font-bold text-green-900">
                R$ {(stats.valorTotal / 1000).toFixed(0)}k
              </div>
              <div className="text-xs text-green-600 font-medium">Valor Total</div>
            </div>

            {/* Leads Qualificados */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <Target className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-purple-600 bg-purple-200 px-2 py-1 rounded-full">
                  Qualificados
                </span>
              </div>
              <div className="text-2xl font-bold text-purple-900">{stats.leadsQualificados}</div>
              <div className="text-xs text-purple-600 font-medium">Em Negociação</div>
            </div>

            {/* Taxa de Conversão */}
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4 border border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-orange-500 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-orange-600 bg-orange-200 px-2 py-1 rounded-full">
                  Conversão
                </span>
              </div>
              <div className="text-2xl font-bold text-orange-900">{stats.taxaConversao}%</div>
              <div className="text-xs text-orange-600 font-medium">Taxa de Sucesso</div>
            </div>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mx-8 mt-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-1 bg-red-500 rounded-full">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-red-900">Erro ao carregar dados</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && leads.length === 0 ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
            <p className="text-gray-600 font-medium">Carregando leads...</p>
          </div>
        </div>
      ) : (
        /* Kanban Board */
        <div className="py-6">
          <KanbanBoard />
        </div>
      )}
    </div>
  );
}
