'use client';

import { Lead, LeadStatus } from '@/types/lead';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface PipelineChartProps {
  leads: Lead[];
}

const statusOrder: LeadStatus[] = [
  'novo',
  'contato_inicial',
  'qualificando',
  'qualificado',
  'agendamento_marcado',
  'ganho',
  'perdido'
];

const statusLabels: Record<LeadStatus, string> = {
  novo: 'Novo',
  contato_inicial: 'Contato',
  qualificando: 'Qualificando',
  qualificado: 'Qualificado',
  agendamento_marcado: 'Agendado',
  ganho: 'Ganho',
  perdido: 'Perdido',
};

const statusColors: Record<LeadStatus, string> = {
  novo: '#3b82f6',
  contato_inicial: '#eab308',
  qualificando: '#6366f1',
  qualificado: '#a855f7',
  agendamento_marcado: '#ec4899',
  ganho: '#22c55e',
  perdido: '#ef4444',
};

export function PipelineChart({ leads }: PipelineChartProps) {
  const data = statusOrder.map(status => {
    const count = leads.filter(l => l.status === status).length;
    const valor = leads
      .filter(l => l.status === status)
      .reduce((sum, l) => sum + l.valor_estimado, 0);

    return {
      status: statusLabels[status],
      count,
      valor,
      color: statusColors[status],
    };
  });

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-gray-900">Pipeline de Vendas</h3>
        <p className="text-sm text-gray-500">Distribuição de leads por estágio</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="status"
            tick={{ fontSize: 12 }}
            tickLine={false}
          />
          <YAxis tick={{ fontSize: 12 }} tickLine={false} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                    <div className="font-semibold text-gray-900 mb-1">{data.status}</div>
                    <div className="text-sm text-gray-600">
                      <div>Leads: {data.count}</div>
                      <div>Valor: R$ {data.valor.toLocaleString('pt-BR')}</div>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legenda */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        {data.map((item) => (
          <div key={item.status} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <div className="text-xs">
              <div className="font-semibold text-gray-700">{item.status}</div>
              <div className="text-gray-500">{item.count} leads</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
