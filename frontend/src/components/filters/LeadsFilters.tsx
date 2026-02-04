'use client';

import { useState } from 'react';
import { LeadStatus, LeadOrigin, LeadTemperature } from '@/types/lead';
import { Search, Filter, X, SlidersHorizontal } from 'lucide-react';

export interface FilterValues {
  search: string;
  status: LeadStatus | 'all';
  origem: LeadOrigin | 'all';
  temperatura: LeadTemperature | 'all';
  scoreMin: number;
  scoreMax: number;
  valorMin: number;
  valorMax: number;
}

interface LeadsFiltersProps {
  filters: FilterValues;
  onFilterChange: (filters: FilterValues) => void;
  onReset: () => void;
}

const statusOptions: { value: LeadStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Todos os Status' },
  { value: 'novo', label: 'Novo' },
  { value: 'contato_inicial', label: 'Contato Inicial' },
  { value: 'qualificando', label: 'Qualificando' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'agendamento_marcado', label: 'Reunião Agendada' },
  { value: 'ganho', label: 'Ganho' },
  { value: 'perdido', label: 'Perdido' },
];

const origemOptions: { value: LeadOrigin | 'all'; label: string }[] = [
  { value: 'all', label: 'Todas as Origens' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'site', label: 'Site' },
  { value: 'indicacao', label: 'Indicação' },
  { value: 'outro', label: 'Outro' },
];

const temperaturaOptions: { value: LeadTemperature | 'all'; label: string }[] = [
  { value: 'all', label: 'Todas as Temperaturas' },
  { value: 'quente', label: 'Quente 🔥' },
  { value: 'morno', label: 'Morno 🟡' },
  { value: 'frio', label: 'Frio ❄️' },
];

export function LeadsFilters({ filters, onFilterChange, onReset }: LeadsFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleChange = (key: keyof FilterValues, value: any) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const hasActiveFilters =
    filters.search ||
    filters.status !== 'all' ||
    filters.origem !== 'all' ||
    filters.temperatura !== 'all' ||
    filters.scoreMin > 0 ||
    filters.scoreMax < 100 ||
    filters.valorMin > 0 ||
    filters.valorMax < 1000000;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      {/* Busca */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={filters.search}
          onChange={(e) => handleChange('search', e.target.value)}
          placeholder="Buscar por nome, empresa, telefone ou email..."
          className="w-full pl-11 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
        />
      </div>

      {/* Filtros Rápidos */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <select
            value={filters.status}
            onChange={(e) => handleChange('status', e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Origem</label>
          <select
            value={filters.origem}
            onChange={(e) => handleChange('origem', e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
          >
            {origemOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Temperatura</label>
          <select
            value={filters.temperatura}
            onChange={(e) => handleChange('temperatura', e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
          >
            {temperaturaOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Toggle Filtros Avançados */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700 font-medium transition-colors"
      >
        <SlidersHorizontal className="w-4 h-4" />
        {showAdvanced ? 'Ocultar' : 'Mostrar'} Filtros Avançados
      </button>

      {/* Filtros Avançados */}
      {showAdvanced && (
        <div className="grid grid-cols-2 gap-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          {/* Score Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Lead Score: {filters.scoreMin} - {filters.scoreMax}
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="0"
                max="100"
                value={filters.scoreMin}
                onChange={(e) => handleChange('scoreMin', parseInt(e.target.value))}
                className="w-full"
              />
              <input
                type="range"
                min="0"
                max="100"
                value={filters.scoreMax}
                onChange={(e) => handleChange('scoreMax', parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          {/* Valor Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Valor Estimado: R$ {filters.valorMin.toLocaleString('pt-BR')} - R$ {filters.valorMax.toLocaleString('pt-BR')}
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="0"
                max="1000000"
                step="1000"
                value={filters.valorMin}
                onChange={(e) => handleChange('valorMin', parseInt(e.target.value))}
                className="w-full"
              />
              <input
                type="range"
                min="0"
                max="1000000"
                step="1000"
                value={filters.valorMax}
                onChange={(e) => handleChange('valorMax', parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <span className="text-sm text-gray-600">
            Filtros ativos
          </span>
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors font-medium"
          >
            <X className="w-4 h-4" />
            Limpar Filtros
          </button>
        </div>
      )}
    </div>
  );
}
