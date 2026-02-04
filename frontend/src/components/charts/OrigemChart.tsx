'use client';

import { Lead, LeadOrigin } from '@/types/lead';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Instagram, MessageCircle, Globe, Users, Shuffle } from 'lucide-react';

interface OrigemChartProps {
  leads: Lead[];
}

const origemLabels: Record<LeadOrigin, string> = {
  instagram: 'Instagram',
  whatsapp: 'WhatsApp',
  site: 'Site',
  indicacao: 'Indicação',
  outro: 'Outro',
};

const origemColors: Record<LeadOrigin, string> = {
  instagram: '#ec4899',
  whatsapp: '#22c55e',
  site: '#3b82f6',
  indicacao: '#a855f7',
  outro: '#64748b',
};

const origemIcons = {
  instagram: Instagram,
  whatsapp: MessageCircle,
  site: Globe,
  indicacao: Users,
  outro: Shuffle,
};

export function OrigemChart({ leads }: OrigemChartProps) {
  const origens: LeadOrigin[] = ['instagram', 'whatsapp', 'site', 'indicacao', 'outro'];

  const data = origens.map(origem => {
    const count = leads.filter(l => l.origem === origem).length;
    const percentage = leads.length > 0 ? (count / leads.length) * 100 : 0;

    return {
      name: origemLabels[origem],
      value: count,
      percentage: percentage.toFixed(1),
      color: origemColors[origem],
      origem,
    };
  }).filter(item => item.value > 0);

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-gray-900">Origem dos Leads</h3>
        <p className="text-sm text-gray-500">De onde vêm seus leads</p>
      </div>

      {data.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                        <div className="font-semibold text-gray-900">{data.name}</div>
                        <div className="text-sm text-gray-600">
                          <div>{data.value} leads ({data.percentage}%)</div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Estatísticas */}
          <div className="mt-6 space-y-3">
            {data.map((item) => {
              const Icon = origemIcons[item.origem];
              return (
                <div key={item.origem} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${item.color}20` }}
                    >
                      <Icon className="w-4 h-4" style={{ color: item.color }} />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900 text-sm">{item.name}</div>
                      <div className="text-xs text-gray-500">{item.percentage}% do total</div>
                    </div>
                  </div>
                  <div className="font-bold text-gray-900">{item.value}</div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-400 text-sm">Nenhum dado disponível</div>
        </div>
      )}
    </div>
  );
}
