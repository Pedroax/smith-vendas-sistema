'use client';

import { Lead } from '@/types/lead';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { format, subDays, eachDayOfInterval } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface ConversaoChartProps {
  leads: Lead[];
}

export function ConversaoChart({ leads }: ConversaoChartProps) {
  // Últimos 30 dias
  const last30Days = eachDayOfInterval({
    start: subDays(new Date(), 29),
    end: new Date(),
  });

  const data = last30Days.map(day => {
    const dayString = day.toDateString();

    // Leads criados nesse dia
    const leadsCreated = leads.filter(l => {
      return new Date(l.created_at).toDateString() === dayString;
    }).length;

    // Leads ganhos nesse dia
    const leadsWon = leads.filter(l => {
      return l.won_at && new Date(l.won_at).toDateString() === dayString;
    }).length;

    // Taxa de conversão acumulada até esse dia
    const totalLeadsUntilDay = leads.filter(l => {
      return new Date(l.created_at) <= day;
    }).length;

    const totalWonUntilDay = leads.filter(l => {
      return l.won_at && new Date(l.won_at) <= day;
    }).length;

    const conversionRate = totalLeadsUntilDay > 0
      ? (totalWonUntilDay / totalLeadsUntilDay) * 100
      : 0;

    return {
      date: format(day, 'dd/MM', { locale: ptBR }),
      fullDate: format(day, 'dd/MM/yyyy', { locale: ptBR }),
      leadsCreated,
      leadsWon,
      conversionRate: parseFloat(conversionRate.toFixed(1)),
    };
  });

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-gray-900">Taxa de Conversão</h3>
        <p className="text-sm text-gray-500">Últimos 30 dias</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorConversion" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickLine={false}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                    <div className="font-semibold text-gray-900 mb-2">{data.fullDate}</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-gray-600">Leads criados:</span>
                        <span className="font-semibold text-blue-600">{data.leadsCreated}</span>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-gray-600">Leads ganhos:</span>
                        <span className="font-semibold text-green-600">{data.leadsWon}</span>
                      </div>
                      <div className="flex items-center justify-between gap-4 pt-1 border-t">
                        <span className="text-gray-600">Taxa:</span>
                        <span className="font-semibold text-purple-600">{data.conversionRate}%</span>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Area
            type="monotone"
            dataKey="conversionRate"
            stroke="#8b5cf6"
            strokeWidth={2}
            fill="url(#colorConversion)"
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Resumo */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-100">
          <div className="text-2xl font-bold text-blue-600">
            {data.reduce((sum, d) => sum + d.leadsCreated, 0)}
          </div>
          <div className="text-xs text-blue-600 font-medium mt-1">Leads Criados</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg border border-green-100">
          <div className="text-2xl font-bold text-green-600">
            {data.reduce((sum, d) => sum + d.leadsWon, 0)}
          </div>
          <div className="text-xs text-green-600 font-medium mt-1">Leads Ganhos</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg border border-purple-100">
          <div className="text-2xl font-bold text-purple-600">
            {data[data.length - 1].conversionRate}%
          </div>
          <div className="text-xs text-purple-600 font-medium mt-1">Taxa Atual</div>
        </div>
      </div>
    </div>
  );
}
