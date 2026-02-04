'use client';

import { Lead, LeadStatus } from '@/types/lead';
import { format, isPast, isFuture, differenceInDays, addDays } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  Calendar, AlertCircle, Clock, Phone, TrendingUp, CheckCircle2
} from 'lucide-react';

interface UpcomingFollowUpsProps {
  leads: Lead[];
}

type FollowUp = {
  id: string;
  leadId: string;
  leadName: string;
  leadStatus: LeadStatus;
  type: 'scheduled_meeting' | 'overdue_interaction' | 'needs_followup';
  priority: 'high' | 'medium' | 'low';
  date: Date;
  description: string;
  daysUntil: number;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
};

export function UpcomingFollowUps({ leads }: UpcomingFollowUpsProps) {
  const followUps: FollowUp[] = [];
  const now = new Date();

  leads.forEach(lead => {
    // Skip leads que já foram ganhos ou perdidos
    if (lead.status === 'ganho' || lead.status === 'perdido') return;

    // 1. Reuniões agendadas
    if (lead.meeting_scheduled_at) {
      const meetingDate = new Date(lead.meeting_scheduled_at);
      const daysUntil = differenceInDays(meetingDate, now);

      followUps.push({
        id: `meeting-${lead.id}`,
        leadId: lead.id,
        leadName: lead.nome,
        leadStatus: lead.status,
        type: 'scheduled_meeting',
        priority: daysUntil < 0 ? 'high' : daysUntil <= 2 ? 'medium' : 'low',
        date: meetingDate,
        description: isPast(meetingDate)
          ? `Reunião atrasada (${Math.abs(daysUntil)} dias atrás)`
          : `Reunião agendada`,
        daysUntil,
        icon: <Calendar className="w-4 h-4" />,
        color: daysUntil < 0 ? 'text-red-600' : 'text-green-600',
        bgColor: daysUntil < 0 ? 'bg-red-50' : 'bg-green-50',
      });
    }

    // 2. Leads sem interação há muito tempo
    if (lead.ultima_interacao) {
      const lastInteraction = new Date(lead.ultima_interacao);
      const daysSinceInteraction = differenceInDays(now, lastInteraction);

      // Se não teve interação há mais de 3 dias e está em status ativo
      if (daysSinceInteraction > 3 && ['contato_inicial', 'qualificando', 'qualificado'].includes(lead.status)) {
        followUps.push({
          id: `overdue-${lead.id}`,
          leadId: lead.id,
          leadName: lead.nome,
          leadStatus: lead.status,
          type: 'overdue_interaction',
          priority: daysSinceInteraction > 7 ? 'high' : 'medium',
          date: lastInteraction,
          description: `Sem contato há ${daysSinceInteraction} dias`,
          daysUntil: -daysSinceInteraction,
          icon: <AlertCircle className="w-4 h-4" />,
          color: daysSinceInteraction > 7 ? 'text-red-600' : 'text-orange-600',
          bgColor: daysSinceInteraction > 7 ? 'bg-red-50' : 'bg-orange-50',
        });
      }
    }

    // 3. Leads quentes que precisam de atenção
    if (lead.temperatura === 'quente' && lead.status === 'qualificado') {
      const lastInteraction = lead.ultima_interacao ? new Date(lead.ultima_interacao) : new Date(lead.created_at);
      const daysSinceInteraction = differenceInDays(now, lastInteraction);

      if (daysSinceInteraction > 1) {
        followUps.push({
          id: `hot-lead-${lead.id}`,
          leadId: lead.id,
          leadName: lead.nome,
          leadStatus: lead.status,
          type: 'needs_followup',
          priority: 'high',
          date: lastInteraction,
          description: `Lead quente precisa de atenção! (${daysSinceInteraction} dias)`,
          daysUntil: -daysSinceInteraction,
          icon: <TrendingUp className="w-4 h-4" />,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
        });
      }
    }

    // 4. Leads novos que precisam de primeiro contato
    if (lead.status === 'novo') {
      const createdDate = new Date(lead.created_at);
      const daysSinceCreation = differenceInDays(now, createdDate);

      if (daysSinceCreation > 0) {
        followUps.push({
          id: `new-lead-${lead.id}`,
          leadId: lead.id,
          leadName: lead.nome,
          leadStatus: lead.status,
          type: 'needs_followup',
          priority: daysSinceCreation > 2 ? 'high' : 'medium',
          date: createdDate,
          description: `Aguardando primeiro contato (${daysSinceCreation} dias)`,
          daysUntil: -daysSinceCreation,
          icon: <Phone className="w-4 h-4" />,
          color: daysSinceCreation > 2 ? 'text-red-600' : 'text-yellow-600',
          bgColor: daysSinceCreation > 2 ? 'bg-red-50' : 'bg-yellow-50',
        });
      }
    }
  });

  // Ordenar por prioridade e data
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  const sortedFollowUps = followUps
    .sort((a, b) => {
      // Primeiro por prioridade
      if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }
      // Depois por data (mais urgente primeiro)
      return a.date.getTime() - b.date.getTime();
    })
    .slice(0, 10);

  const highPriorityCount = sortedFollowUps.filter(f => f.priority === 'high').length;

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900">Próximos Follow-ups</h3>
          <p className="text-sm text-gray-500">
            {highPriorityCount > 0 ? (
              <span className="text-red-600 font-semibold">
                {highPriorityCount} urgente{highPriorityCount > 1 ? 's' : ''}
              </span>
            ) : (
              'Nenhum follow-up urgente'
            )}
          </p>
        </div>
        <div className="p-2 bg-orange-100 rounded-lg">
          <Calendar className="w-5 h-5 text-orange-600" />
        </div>
      </div>

      <div className="space-y-3">
        {sortedFollowUps.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <p className="text-gray-900 font-semibold">Tudo em dia!</p>
            <p className="text-sm text-gray-500 mt-1">Nenhum follow-up pendente</p>
          </div>
        ) : (
          sortedFollowUps.map((followUp) => (
            <div
              key={followUp.id}
              className={`p-4 rounded-lg border-l-4 ${
                followUp.priority === 'high'
                  ? 'border-red-500 bg-red-50'
                  : followUp.priority === 'medium'
                  ? 'border-orange-500 bg-orange-50'
                  : 'border-green-500 bg-green-50'
              } hover:shadow-md transition-shadow cursor-pointer`}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className={`p-2 ${followUp.color} ${followUp.bgColor} rounded-lg flex-shrink-0`}>
                  {followUp.icon}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 text-sm truncate">
                        {followUp.leadName}
                      </p>
                      <p className={`text-xs font-medium mt-0.5 ${followUp.color}`}>
                        {followUp.description}
                      </p>
                    </div>
                    {followUp.priority === 'high' && (
                      <span className="px-2 py-0.5 bg-red-500 text-white text-xs font-bold rounded-full flex-shrink-0">
                        URGENTE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {format(followUp.date, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {sortedFollowUps.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Alta prioridade</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <span>Média prioridade</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Baixa prioridade</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
