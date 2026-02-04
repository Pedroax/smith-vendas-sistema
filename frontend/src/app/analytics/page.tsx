'use client';

import { useEffect, useState } from 'react';
import { useLeadsStore } from '@/store/useLeadsStore';
import { PipelineChart } from '@/components/charts/PipelineChart';
import { OrigemChart } from '@/components/charts/OrigemChart';
import { ConversaoChart } from '@/components/charts/ConversaoChart';
import {
  TrendingUp, TrendingDown, Users, DollarSign, Target, Calendar,
  Phone, MessageCircle, Clock, Award, Download, Filter, Loader2
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { format, subDays, eachDayOfInterval } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function AnalyticsPage() {
  const { leads, isLoading, fetchLeads, fetchStats } = useLeadsStore();
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  // Calcular métricas
  const totalLeads = leads.length;
  const leadsGanhos = leads.filter(l => l.status === 'ganho').length;
  const leadsPerdidos = leads.filter(l => l.status === 'perdido').length;
  const valorTotal = leads.reduce((sum, l) => sum + l.valor_estimado, 0);
  const valorGanho = leads.filter(l => l.status === 'ganho').reduce((sum, l) => sum + l.valor_estimado, 0);
  const taxaConversao = totalLeads > 0 ? (leadsGanhos / totalLeads) * 100 : 0;
  const ticketMedio = leadsGanhos > 0 ? valorGanho / leadsGanhos : 0;
  const scoreMedia = totalLeads > 0 ? leads.reduce((sum, l) => sum + l.lead_score, 0) / totalLeads : 0;

  // Tendências (comparação com período anterior)
  const getDayRange = () => {
    switch (timeRange) {
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
    }
  };

  const days = getDayRange();
  const currentPeriodStart = subDays(new Date(), days);
  const previousPeriodStart = subDays(currentPeriodStart, days);

  const currentPeriodLeads = leads.filter(l =>
    new Date(l.created_at) >= currentPeriodStart
  ).length;

  const previousPeriodLeads = leads.filter(l =>
    new Date(l.created_at) >= previousPeriodStart &&
    new Date(l.created_at) < currentPeriodStart
  ).length;

  const leadsTrend = previousPeriodLeads > 0
    ? ((currentPeriodLeads - previousPeriodLeads) / previousPeriodLeads) * 100
    : 0;

  // Dados para gráfico de evolução diária
  const last30Days = eachDayOfInterval({
    start: subDays(new Date(), 29),
    end: new Date(),
  });

  const evolutionData = last30Days.map(day => {
    const dayString = day.toDateString();
    const created = leads.filter(l =>
      new Date(l.created_at).toDateString() === dayString
    ).length;
    const won = leads.filter(l =>
      l.won_at && new Date(l.won_at).toDateString() === dayString
    ).length;

    return {
      date: format(day, 'dd/MM', { locale: ptBR }),
      criados: created,
      ganhos: won,
    };
  });

  // Dados por origem
  const origemData = ['whatsapp', 'instagram', 'site', 'indicacao', 'outro'].map(origem => ({
    origem,
    quantidade: leads.filter(l => l.origem === origem).length,
    valor: leads.filter(l => l.origem === origem).reduce((sum, l) => sum + l.valor_estimado, 0),
  }));

  // Dados por temperatura
  const tempData = [
    { temp: 'Quente', value: leads.filter(l => l.temperatura === 'quente').length, color: '#ef4444' },
    { temp: 'Morno', value: leads.filter(l => l.temperatura === 'morno').length, color: '#f59e0b' },
    { temp: 'Frio', value: leads.filter(l => l.temperatura === 'frio').length, color: '#3b82f6' },
  ];

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                Analytics Avançado
              </h1>
              <p className="text-gray-500">
                Análise detalhada do desempenho do seu funil de vendas
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Time Range Selector */}
              <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setTimeRange('7d')}
                  className={`px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    timeRange === '7d'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  7 dias
                </button>
                <button
                  onClick={() => setTimeRange('30d')}
                  className={`px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    timeRange === '30d'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  30 dias
                </button>
                <button
                  onClick={() => setTimeRange('90d')}
                  className={`px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    timeRange === '90d'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  90 dias
                </button>
              </div>

              <button className="flex items-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Download className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-700">Exportar Relatório</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8 space-y-6">
        {isLoading && leads.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
              <p className="text-gray-600 font-medium">Carregando analytics...</p>
            </div>
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-6">
              {/* Total Leads */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className={`flex items-center gap-1 text-sm font-semibold ${
                    leadsTrend >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {leadsTrend >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {Math.abs(leadsTrend).toFixed(1)}%
                  </div>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">{totalLeads}</div>
                <div className="text-sm text-gray-600">Total de Leads</div>
              </div>

              {/* Taxa de Conversão */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <Target className="w-6 h-6 text-green-600" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">{taxaConversao.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Taxa de Conversão</div>
              </div>

              {/* Ticket Médio */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  R$ {(ticketMedio / 1000).toFixed(1)}k
                </div>
                <div className="text-sm text-gray-600">Ticket Médio</div>
              </div>

              {/* Score Médio */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-orange-100 rounded-lg">
                    <Award className="w-6 h-6 text-orange-600" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">{scoreMedia.toFixed(0)}</div>
                <div className="text-sm text-gray-600">Score Médio</div>
              </div>
            </div>

            {/* Evolução Temporal */}
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="text-lg font-bold text-gray-900 mb-6">Evolução de Leads</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={evolutionData}>
                  <defs>
                    <linearGradient id="colorCriados" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorGanhos" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="criados"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    fill="url(#colorCriados)"
                    name="Leads Criados"
                  />
                  <Area
                    type="monotone"
                    dataKey="ganhos"
                    stroke="#10b981"
                    strokeWidth={2}
                    fill="url(#colorGanhos)"
                    name="Leads Ganhos"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Performance por Origem e Temperatura */}
            <div className="grid grid-cols-2 gap-6">
              {/* Por Origem */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-6">Performance por Origem</h3>
                <div className="space-y-4">
                  {origemData.map((item) => (
                    <div key={item.origem}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 capitalize">{item.origem}</span>
                        <span className="text-sm font-bold text-gray-900">{item.quantidade} leads</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                          style={{ width: `${(item.quantidade / totalLeads) * 100}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        R$ {(item.valor / 1000).toFixed(1)}k em pipeline
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Por Temperatura */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-6">Distribuição por Temperatura</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={tempData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="temp" tick={{ fontSize: 11 }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {tempData.map((entry, index) => (
                        <Bar key={index} dataKey="value" fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Gráficos Principais */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="lg:col-span-2">
                <PipelineChart leads={leads} />
              </div>
              <OrigemChart leads={leads} />
              <ConversaoChart leads={leads} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
