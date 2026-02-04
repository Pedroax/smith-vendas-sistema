'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLeadsStore } from '@/store/useLeadsStore';
import { LeadsTable } from '@/components/leads/LeadsTable';
import { PipelineChart } from '@/components/charts/PipelineChart';
import { OrigemChart } from '@/components/charts/OrigemChart';
import { ConversaoChart } from '@/components/charts/ConversaoChart';
import { LeadModal } from '@/components/modals/LeadModal';
import { LeadsFilters, FilterValues } from '@/components/filters/LeadsFilters';
import { RecentActivities } from '@/components/widgets/RecentActivities';
import { UpcomingFollowUps } from '@/components/widgets/UpcomingFollowUps';
import { Lead } from '@/types/lead';
import {
  TrendingUp, DollarSign, Users, Target, Plus, Download,
  LayoutGrid, Table, BarChart3, Loader2, RefreshCw
} from 'lucide-react';

type ViewMode = 'table' | 'charts';

const defaultFilters: FilterValues = {
  search: '',
  status: 'all',
  origem: 'all',
  temperatura: 'all',
  scoreMin: 0,
  scoreMax: 100,
  valorMin: 0,
  valorMax: 1000000,
};

export default function DashboardPage() {
  const router = useRouter();
  const { leads, stats, isLoading, error, fetchLeads, fetchStats, clearError, deleteLead } = useLeadsStore();
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [filters, setFilters] = useState<FilterValues>(defaultFilters);

  // Filtrar leads
  const filteredLeads = leads.filter((lead) => {
    // Busca por texto
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      const matchesSearch =
        lead.nome.toLowerCase().includes(searchLower) ||
        lead.empresa?.toLowerCase().includes(searchLower) ||
        lead.telefone.includes(searchLower) ||
        lead.email?.toLowerCase().includes(searchLower);

      if (!matchesSearch) return false;
    }

    // Filtro de status
    if (filters.status !== 'all' && lead.status !== filters.status) return false;

    // Filtro de origem
    if (filters.origem !== 'all' && lead.origem !== filters.origem) return false;

    // Filtro de temperatura
    if (filters.temperatura !== 'all' && lead.temperatura !== filters.temperatura) return false;

    // Filtro de score
    if (lead.lead_score < filters.scoreMin || lead.lead_score > filters.scoreMax) return false;

    // Filtro de valor
    if (lead.valor_estimado < filters.valorMin || lead.valor_estimado > filters.valorMax) return false;

    return true;
  });

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  const handleRefresh = async () => {
    await Promise.all([fetchLeads(), fetchStats()]);
  };

  const handleExport = () => {
    // Criar CSV
    const headers = ['Nome', 'Empresa', 'Telefone', 'Email', 'Status', 'Score', 'Valor', 'Origem', 'Criado em'];
    const rows = leads.map(lead => [
      lead.nome,
      lead.empresa || '',
      lead.telefone,
      lead.email || '',
      lead.status,
      lead.lead_score,
      lead.valor_estimado,
      lead.origem,
      new Date(lead.created_at).toLocaleDateString('pt-BR'),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `leads_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleViewLead = (lead: Lead) => {
    router.push(`/leads/${lead.id}`);
  };

  const handleEditLead = (lead: Lead) => {
    setSelectedLead(lead);
    setIsModalOpen(true);
  };

  const handleDeleteLead = async (lead: Lead) => {
    if (confirm(`Tem certeza que deseja deletar o lead ${lead.nome}?`)) {
      await deleteLead(lead.id);
    }
  };

  const handleCreateLead = () => {
    setSelectedLead(null);
    setIsModalOpen(true);
  };

  const displayStats = {
    total_leads: filteredLeads.length,
    score_medio: filteredLeads.reduce((sum, l) => sum + l.lead_score, 0) / (filteredLeads.length || 1),
    valor_total_pipeline: filteredLeads.reduce((sum, l) => sum + l.valor_estimado, 0),
    taxa_conversao: (filteredLeads.filter(l => l.status === 'ganho').length / (filteredLeads.length || 1)) * 100,
  };

  const handleResetFilters = () => {
    setFilters(defaultFilters);
  };

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                Dashboard Completo
              </h1>
              <p className="text-gray-500">
                Visão completa do seu pipeline de vendas
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Refresh */}
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="p-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                title="Atualizar"
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${isLoading ? 'animate-spin' : ''}`} />
              </button>

              {/* Export */}
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Download className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-700">Exportar CSV</span>
              </button>

              {/* Add Lead */}
              <button
                onClick={handleCreateLead}
                className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all"
              >
                <Plus className="w-5 h-5" />
                <span className="font-medium">Novo Lead</span>
              </button>
            </div>
          </div>

          {/* Stats Cards */}
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
              <div className="text-2xl font-bold text-blue-900">{displayStats.total_leads}</div>
              <div className="text-xs text-blue-600 font-medium">Leads Ativos</div>
            </div>

            {/* Score Médio */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <Target className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-purple-600 bg-purple-200 px-2 py-1 rounded-full">
                  Qualidade
                </span>
              </div>
              <div className="text-2xl font-bold text-purple-900">
                {displayStats.score_medio.toFixed(0)}
              </div>
              <div className="text-xs text-purple-600 font-medium">Score Médio</div>
            </div>

            {/* Valor Pipeline */}
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
                R$ {(displayStats.valor_total_pipeline / 1000).toFixed(0)}k
              </div>
              <div className="text-xs text-green-600 font-medium">Valor Total</div>
            </div>

            {/* Taxa Conversão */}
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4 border border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-orange-500 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-orange-600 bg-orange-200 px-2 py-1 rounded-full">
                  Conversão
                </span>
              </div>
              <div className="text-2xl font-bold text-orange-900">
                {displayStats.taxa_conversao.toFixed(0)}%
              </div>
              <div className="text-xs text-orange-600 font-medium">Taxa de Sucesso</div>
            </div>
          </div>

          {/* View Toggle */}
          <div className="mt-6 flex items-center gap-2 bg-gray-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => {
                console.log('Mudando para tabela');
                setViewMode('table');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                viewMode === 'table'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Table className="w-4 h-4" />
              Tabela
            </button>
            <button
              onClick={() => {
                console.log('Mudando para gráficos');
                setViewMode('charts');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                viewMode === 'charts'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Gráficos
            </button>
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

      {/* Content */}
      <div className="p-8">
        {/* Filters */}
        <div className="mb-6">
          <LeadsFilters
            filters={filters}
            onFilterChange={setFilters}
            onReset={handleResetFilters}
          />
        </div>

        {/* Widgets */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <RecentActivities leads={leads} />
          <UpcomingFollowUps leads={leads} />
        </div>

        {isLoading && leads.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
              <p className="text-gray-600 font-medium">Carregando dados...</p>
            </div>
          </div>
        ) : viewMode === 'table' ? (
          <LeadsTable
            leads={filteredLeads}
            onViewLead={handleViewLead}
            onEditLead={handleEditLead}
            onDeleteLead={handleDeleteLead}
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="lg:col-span-2">
              <PipelineChart leads={filteredLeads} />
            </div>
            <OrigemChart leads={filteredLeads} />
            <ConversaoChart leads={filteredLeads} />
          </div>
        )}
      </div>

      {/* Modal */}
      <LeadModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedLead(null);
        }}
        lead={selectedLead}
      />
    </div>
  );
}
