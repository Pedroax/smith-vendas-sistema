'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Lead } from '@/types/lead';
import { Building2, Phone, Mail, DollarSign, Clock, Instagram, MessageCircle, Globe, Users, Facebook, HelpCircle } from 'lucide-react';

interface LeadCardProps {
  lead: Lead;
}

const origemIcons: Record<string, any> = {
  instagram: Instagram,
  whatsapp: MessageCircle,
  site: Globe,
  indicacao: Users,
  facebook_ads: Facebook,
  teste: HelpCircle,
  outro: HelpCircle,
};

const origemColors: Record<string, string> = {
  instagram: 'bg-pink-500/10 text-pink-600',
  whatsapp: 'bg-green-500/10 text-green-600',
  site: 'bg-blue-500/10 text-blue-600',
  indicacao: 'bg-purple-500/10 text-purple-600',
  facebook_ads: 'bg-blue-500/10 text-blue-600',
  teste: 'bg-gray-500/10 text-gray-600',
  outro: 'bg-gray-500/10 text-gray-600',
};

export function LeadCard({ lead }: LeadCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: lead.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const OrigemIcon = origemIcons[lead.origem] || HelpCircle;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`
        bg-white rounded-xl border border-gray-200 p-4 cursor-grab active:cursor-grabbing
        hover:shadow-lg transition-all duration-200
        ${isDragging ? 'opacity-50 shadow-2xl scale-105' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 text-sm mb-1">
            {lead.nome}
          </h3>
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Building2 className="w-3 h-3" />
            <span>{lead.empresa}</span>
          </div>
        </div>

        {/* Origem Badge */}
        <div className={`p-1.5 rounded-lg ${origemColors[lead.origem] || 'bg-gray-500/10 text-gray-600'}`}>
          <OrigemIcon className="w-3.5 h-3.5" />
        </div>
      </div>

      {/* Valor Estimado */}
      <div className="mb-3 p-2.5 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-green-500 rounded-md">
            <DollarSign className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <div className="text-[10px] text-green-600 font-medium uppercase tracking-wide">
              Valor Estimado
            </div>
            <div className="text-sm font-bold text-green-700">
              R$ {lead.valor_estimado.toLocaleString('pt-BR')}
            </div>
          </div>
        </div>
      </div>

      {/* Contato */}
      <div className="space-y-1.5 mb-3">
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <Phone className="w-3 h-3" />
          <span>{lead.telefone}</span>
        </div>
        {lead.email && (
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <Mail className="w-3 h-3" />
            <span className="truncate">{lead.email}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{lead.ultima_interacao || 'Sem interação'}</span>
        </div>

        {/* Avatar ou Iniciais */}
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
          <span className="text-[10px] font-bold text-white">
            {lead.nome.split(' ').map(n => n[0]).join('').slice(0, 2)}
          </span>
        </div>
      </div>

      {/* Notas (se houver) */}
      {lead.notas && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <p className="text-[11px] text-gray-500 line-clamp-2 italic">
            "{lead.notas}"
          </p>
        </div>
      )}
    </div>
  );
}
