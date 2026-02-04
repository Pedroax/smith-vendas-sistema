'use client';

import { useState, Fragment } from 'react';
import { Lead, LeadStatus, LeadTemperature } from '@/types/lead';
import {
  Building2, Phone, Mail, Calendar, TrendingUp, TrendingDown, Minus,
  ChevronDown, ChevronUp, Eye, Edit2, Trash2, MoreVertical
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface LeadsTableProps {
  leads: Lead[];
  onViewLead?: (lead: Lead) => void;
  onEditLead?: (lead: Lead) => void;
  onDeleteLead?: (lead: Lead) => void;
}

type SortField = 'nome' | 'empresa' | 'status' | 'lead_score' | 'valor_estimado' | 'created_at';
type SortOrder = 'asc' | 'desc';

const statusLabels: Record<LeadStatus, string> = {
  novo: 'Novo',
  contato_inicial: 'Contato Inicial',
  qualificando: 'Qualificando',
  qualificado: 'Qualificado',
  agendamento_marcado: 'Reunião Agendada',
  ganho: 'Ganho',
  perdido: 'Perdido',
};

const statusColors: Record<LeadStatus, string> = {
  novo: 'bg-blue-100 text-blue-700',
  contato_inicial: 'bg-yellow-100 text-yellow-700',
  qualificando: 'bg-indigo-100 text-indigo-700',
  qualificado: 'bg-purple-100 text-purple-700',
  agendamento_marcado: 'bg-pink-100 text-pink-700',
  ganho: 'bg-green-100 text-green-700',
  perdido: 'bg-red-100 text-red-700',
};

const temperaturaIcons: Record<LeadTemperature, React.JSX.Element> = {
  quente: <TrendingUp className="w-4 h-4 text-green-500" />,
  morno: <Minus className="w-4 h-4 text-yellow-500" />,
  frio: <TrendingDown className="w-4 h-4 text-red-500" />,
};

export function LeadsTable({ leads, onViewLead, onEditLead, onDeleteLead }: LeadsTableProps) {
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const sortedLeads = [...leads].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];

    if (sortField === 'created_at') {
      aValue = new Date(aValue as string).getTime();
      bValue = new Date(bValue as string).getTime();
    }

    if (typeof aValue === 'string') {
      return sortOrder === 'asc'
        ? aValue.localeCompare(bValue as string)
        : (bValue as string).localeCompare(aValue);
    }

    if (typeof aValue === 'number') {
      return sortOrder === 'asc' ? aValue - (bValue as number) : (bValue as number) - aValue;
    }

    return 0;
  });

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortOrder === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('nome')}
                  className="flex items-center gap-2 text-xs font-semibold text-gray-700 uppercase tracking-wider hover:text-gray-900 transition-colors"
                >
                  Nome / Empresa
                  <SortIcon field="nome" />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Contato
                </div>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('status')}
                  className="flex items-center gap-2 text-xs font-semibold text-gray-700 uppercase tracking-wider hover:text-gray-900 transition-colors"
                >
                  Status
                  <SortIcon field="status" />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('lead_score')}
                  className="flex items-center gap-2 text-xs font-semibold text-gray-700 uppercase tracking-wider hover:text-gray-900 transition-colors"
                >
                  Score
                  <SortIcon field="lead_score" />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('valor_estimado')}
                  className="flex items-center gap-2 text-xs font-semibold text-gray-700 uppercase tracking-wider hover:text-gray-900 transition-colors"
                >
                  Valor
                  <SortIcon field="valor_estimado" />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('created_at')}
                  className="flex items-center gap-2 text-xs font-semibold text-gray-700 uppercase tracking-wider hover:text-gray-900 transition-colors"
                >
                  Criado em
                  <SortIcon field="created_at" />
                </button>
              </th>
              <th className="px-6 py-3 text-right">
                <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Ações
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedLeads.map((lead) => (
              <Fragment key={lead.id}>
                <tr
                  className="hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => setExpandedRow(expandedRow === lead.id ? null : lead.id)}
                >
                  {/* Nome / Empresa */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                        {lead.nome.split(' ').map(n => n[0]).join('').slice(0, 2)}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{lead.nome}</div>
                        {lead.empresa && (
                          <div className="text-sm text-gray-500 flex items-center gap-1">
                            <Building2 className="w-3 h-3" />
                            {lead.empresa}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Contato */}
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="text-sm text-gray-900 flex items-center gap-2">
                        <Phone className="w-3 h-3 text-gray-400" />
                        {lead.telefone}
                      </div>
                      {lead.email && (
                        <div className="text-sm text-gray-500 flex items-center gap-2">
                          <Mail className="w-3 h-3 text-gray-400" />
                          {lead.email}
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Status */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColors[lead.status]}`}>
                        {statusLabels[lead.status]}
                      </span>
                      {temperaturaIcons[lead.temperatura]}
                    </div>
                  </td>

                  {/* Score */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[80px]">
                        <div
                          className={`h-2 rounded-full ${
                            lead.lead_score >= 70 ? 'bg-green-500' :
                            lead.lead_score >= 40 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${lead.lead_score}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-gray-900 w-8 text-right">
                        {lead.lead_score}
                      </span>
                    </div>
                  </td>

                  {/* Valor */}
                  <td className="px-6 py-4">
                    <div className="font-semibold text-gray-900">
                      R$ {lead.valor_estimado.toLocaleString('pt-BR')}
                    </div>
                  </td>

                  {/* Data */}
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500 flex items-center gap-2">
                      <Calendar className="w-3 h-3" />
                      {format(new Date(lead.created_at), 'dd/MM/yyyy', { locale: ptBR })}
                    </div>
                  </td>

                  {/* Ações */}
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      {onViewLead && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onViewLead(lead);
                          }}
                          className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                          title="Visualizar"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      {onEditLead && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onEditLead(lead);
                          }}
                          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                      {onDeleteLead && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteLead(lead);
                          }}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Deletar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>

                {/* Linha expandida com detalhes */}
                {expandedRow === lead.id && (
                  <tr className="bg-gray-50">
                    <td colSpan={7} className="px-6 py-4">
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-500 font-medium mb-1">Tags</div>
                          <div className="flex flex-wrap gap-1">
                            {lead.tags.length > 0 ? (
                              lead.tags.map((tag, i) => (
                                <span key={i} className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs">
                                  {tag}
                                </span>
                              ))
                            ) : (
                              <span className="text-gray-400 text-xs">Sem tags</span>
                            )}
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-500 font-medium mb-1">Última Interação</div>
                          <div className="text-gray-700">
                            {lead.ultima_interacao
                              ? format(new Date(lead.ultima_interacao), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })
                              : 'Nunca'}
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-500 font-medium mb-1">Origem</div>
                          <div className="text-gray-700 capitalize">{lead.origem}</div>
                        </div>
                        {lead.notas && (
                          <div className="col-span-3">
                            <div className="text-gray-500 font-medium mb-1">Notas</div>
                            <div className="text-gray-700 bg-white p-3 rounded-lg border border-gray-200">
                              {lead.notas}
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>

        {sortedLeads.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">Nenhum lead encontrado</div>
            <div className="text-gray-500 text-sm">
              Tente ajustar os filtros ou criar um novo lead
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
