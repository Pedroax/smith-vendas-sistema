'use client';

import { useEffect, useState } from 'react';
import {
  TrendingUp, TrendingDown, Users, Target, DollarSign, Clock,
  AlertCircle, RefreshCw, Calendar, Zap, Activity, Filter
} from 'lucide-react';

interface DashboardMetrics {
  resumo: {
    total_leads: number;
    leads_ativos: number;
    novos_ultimos_30d: number;
    qualificados_ultimos_30d: number;
    valor_pipeline: number;
    crescimento_percentual: number;
  };
  funil: Record<string, { count: number; percentual: number }>;
  temperatura: {
    quente: { count: number; percentual: number };
    morno: { count: number; percentual: number };
    frio: { count: number; percentual: number };
  };
  tempo_medio: Record<string, number>;
  motivos_perda: Array<{ motivo: string; count: number; percentual: number }>;
  timeline: Array<{ data: string; novos: number; qualificados: number; perdidos: number }>;
  taxa_conversao: {
    lead_para_contato: number;
    contato_para_qualificacao: number;
    qualificacao_para_qualificado: number;
    geral: number;
  };
}

export default function AnalyticsDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodo, setPeriodo] = useState(30);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setIsLoading(true);
        setError(null);

        console.log('Buscando métricas...', `http://localhost:8000/api/analytics/dashboard?periodo_dias=${periodo}`);
        const response = await fetch(`http://localhost:8000/api/analytics/dashboard?periodo_dias=${periodo}`);

        if (!response.ok) {
          throw new Error('Erro ao buscar métricas');
        }

        const data = await response.json();
        console.log('Métricas recebidas:', data);
        setMetrics(data);
      } catch (err) {
        console.error('Erro ao buscar métricas:', err);
        setError(err instanceof Error ? err.message : 'Erro desconhecido');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();
  }, [periodo, refreshKey]);

  if (isLoading && !metrics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Carregando analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 text-center mb-2">
            Erro ao carregar dados
          </h3>
          <p className="text-sm text-red-700 text-center mb-4">{error}</p>
          <button
            onClick={() => setRefreshKey(k => k + 1)}
            className="w-full py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const { resumo, temperatura, taxa_conversao, motivos_perda } = metrics;

  // Valores padrão para evitar erros quando a API retorna dados incompletos
  const temperaturaSegura = temperatura || {
    quente: { count: 0, percentual: 0 },
    morno: { count: 0, percentual: 0 },
    frio: { count: 0, percentual: 0 }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                Analytics em Tempo Real
              </h1>
              <p className="text-gray-500">
                Insights e métricas do seu funil de vendas
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Período */}
              <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
                {[7, 30, 90].map((dias) => (
                  <button
                    key={dias}
                    onClick={() => setPeriodo(dias)}
                    className={`px-4 py-2 rounded-md font-medium text-sm transition-all ${
                      periodo === dias
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {dias}d
                  </button>
                ))}
              </div>

              {/* Refresh */}
              <button
                onClick={() => setRefreshKey(k => k + 1)}
                disabled={isLoading}
                className="p-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                title="Atualizar"
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* KPI Cards Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
            {/* Total Leads */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Users className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-blue-900">{resumo.total_leads}</div>
              <div className="text-xs text-blue-600 font-medium">Total Leads</div>
            </div>

            {/* Leads Ativos */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-green-500 rounded-lg">
                  <Activity className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-green-900">{resumo.leads_ativos}</div>
              <div className="text-xs text-green-600 font-medium">Leads Ativos</div>
            </div>

            {/* Novos (Período) */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <Zap className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-purple-900">{resumo.novos_ultimos_30d}</div>
              <div className="text-xs text-purple-600 font-medium">Novos ({periodo}d)</div>
            </div>

            {/* Qualificados */}
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl p-4 border border-yellow-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-yellow-500 rounded-lg">
                  <Target className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-yellow-900">{resumo.qualificados_ultimos_30d}</div>
              <div className="text-xs text-yellow-600 font-medium">Qualificados ({periodo}d)</div>
            </div>

            {/* Pipeline Value */}
            <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-4 border border-emerald-200">
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-emerald-500 rounded-lg">
                  <DollarSign className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="text-2xl font-bold text-emerald-900">
                R$ {(resumo.valor_pipeline / 1000).toFixed(0)}k
              </div>
              <div className="text-xs text-emerald-600 font-medium">Pipeline Value</div>
            </div>

            {/* Crescimento */}
            <div className={`bg-gradient-to-br ${
              resumo.crescimento_percentual >= 0
                ? 'from-teal-50 to-teal-100 border-teal-200'
                : 'from-red-50 to-red-100 border-red-200'
            } rounded-xl p-4 border`}>
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${
                  resumo.crescimento_percentual >= 0 ? 'bg-teal-500' : 'bg-red-500'
                }`}>
                  {resumo.crescimento_percentual >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-white" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-white" />
                  )}
                </div>
              </div>
              <div className={`text-2xl font-bold ${
                resumo.crescimento_percentual >= 0 ? 'text-teal-900' : 'text-red-900'
              }`}>
                {resumo.crescimento_percentual >= 0 ? '+' : ''}{resumo.crescimento_percentual.toFixed(1)}%
              </div>
              <div className={`text-xs font-medium ${
                resumo.crescimento_percentual >= 0 ? 'text-teal-600' : 'text-red-600'
              }`}>
                Crescimento
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Temperatura Distribution */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Distribuição por Temperatura
            </h3>
            <div className="space-y-4">
              {/* Quente */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">🔥 Quente</span>
                  <span className="text-sm font-bold text-red-600">
                    {temperaturaSegura.quente.count} ({temperaturaSegura.quente.percentual}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-red-500 to-orange-500 h-2 rounded-full transition-all"
                    style={{ width: `${temperaturaSegura.quente.percentual}%` }}
                  />
                </div>
              </div>

              {/* Morno */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">🌤️ Morno</span>
                  <span className="text-sm font-bold text-yellow-600">
                    {temperaturaSegura.morno.count} ({temperaturaSegura.morno.percentual}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-yellow-400 to-orange-400 h-2 rounded-full transition-all"
                    style={{ width: `${temperaturaSegura.morno.percentual}%` }}
                  />
                </div>
              </div>

              {/* Frio */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">❄️ Frio</span>
                  <span className="text-sm font-bold text-blue-600">
                    {temperaturaSegura.frio.count} ({temperaturaSegura.frio.percentual}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-400 to-cyan-400 h-2 rounded-full transition-all"
                    style={{ width: `${temperaturaSegura.frio.percentual}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Taxa de Conversão */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Taxa de Conversão
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Lead → Contato</span>
                <span className="text-lg font-bold text-blue-600">
                  {taxa_conversao.lead_para_contato}%
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Contato → Qualificação</span>
                <span className="text-lg font-bold text-purple-600">
                  {taxa_conversao.contato_para_qualificacao}%
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Qualificação → Qualificado</span>
                <span className="text-lg font-bold text-green-600">
                  {taxa_conversao.qualificacao_para_qualificado}%
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg border-2 border-purple-300">
                <span className="text-sm font-bold text-gray-900">Taxa Geral</span>
                <span className="text-2xl font-bold text-purple-600">
                  {taxa_conversao.geral}%
                </span>
              </div>
            </div>
          </div>

          {/* Motivos de Perda */}
          {motivos_perda.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6 lg:col-span-2">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Principais Motivos de Perda
              </h3>
              <div className="space-y-3">
                {motivos_perda.slice(0, 5).map((motivo, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        {index + 1}. {motivo.motivo}
                      </span>
                      <span className="text-sm font-bold text-red-600">
                        {motivo.count} leads ({motivo.percentual}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-red-500 to-pink-500 h-2 rounded-full transition-all"
                        style={{ width: `${motivo.percentual}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
