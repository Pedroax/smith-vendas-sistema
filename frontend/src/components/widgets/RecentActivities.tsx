'use client';

import { Lead } from '@/types/lead';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  UserPlus, MessageCircle, TrendingUp, Calendar, Clock, ArrowRight
} from 'lucide-react';

interface RecentActivitiesProps {
  leads: Lead[];
}

type Activity = {
  id: string;
  type: 'lead_created' | 'status_changed' | 'message_received' | 'message_sent' | 'meeting_scheduled';
  leadId: string;
  leadName: string;
  timestamp: Date;
  description: string;
  icon: React.ReactNode;
  color: string;
};

export function RecentActivities({ leads }: RecentActivitiesProps) {
  // Gerar lista de atividades
  const activities: Activity[] = [];

  leads.forEach(lead => {
    // Atividade de criação do lead
    activities.push({
      id: `created-${lead.id}`,
      type: 'lead_created',
      leadId: lead.id,
      leadName: lead.nome,
      timestamp: new Date(lead.created_at),
      description: `Novo lead criado via ${lead.origem}`,
      icon: <UserPlus className="w-4 h-4" />,
      color: 'bg-blue-500',
    });

    // Atividade de última interação
    if (lead.ultima_interacao) {
      activities.push({
        id: `interaction-${lead.id}`,
        type: 'message_received',
        leadId: lead.id,
        leadName: lead.nome,
        timestamp: new Date(lead.ultima_interacao),
        description: 'Última interação registrada',
        icon: <MessageCircle className="w-4 h-4" />,
        color: 'bg-purple-500',
      });
    }

    // Atividade de reunião agendada
    if (lead.meeting_scheduled_at) {
      activities.push({
        id: `meeting-${lead.id}`,
        type: 'meeting_scheduled',
        leadId: lead.id,
        leadName: lead.nome,
        timestamp: new Date(lead.meeting_scheduled_at),
        description: 'Reunião agendada',
        icon: <Calendar className="w-4 h-4" />,
        color: 'bg-green-500',
      });
    }

    // Atividades de mensagens do histórico
    lead.conversation_history.forEach((message, index) => {
      activities.push({
        id: `message-${lead.id}-${message.id}`,
        type: message.role === 'user' ? 'message_received' : 'message_sent',
        leadId: lead.id,
        leadName: lead.nome,
        timestamp: new Date(message.timestamp),
        description: message.role === 'user'
          ? `Mensagem recebida: "${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}"`
          : `Mensagem enviada: "${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}"`
        ,
        icon: <MessageCircle className="w-4 h-4" />,
        color: message.role === 'user' ? 'bg-purple-500' : 'bg-pink-500',
      });
    });
  });

  // Ordenar por timestamp (mais recente primeiro) e pegar apenas os 10 mais recentes
  const recentActivities = activities
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 10);

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900">Atividades Recentes</h3>
          <p className="text-sm text-gray-500">Últimas 10 atividades</p>
        </div>
        <div className="p-2 bg-purple-100 rounded-lg">
          <Clock className="w-5 h-5 text-purple-600" />
        </div>
      </div>

      <div className="space-y-4">
        {recentActivities.length === 0 ? (
          <div className="text-center py-8">
            <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">Nenhuma atividade recente</p>
          </div>
        ) : (
          recentActivities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer group"
            >
              {/* Icon */}
              <div className={`p-2 ${activity.color} rounded-lg text-white flex-shrink-0`}>
                {activity.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm truncate">
                      {activity.leadName}
                    </p>
                    <p className="text-xs text-gray-600 mt-0.5">
                      {activity.description}
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                </div>
                <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {format(activity.timestamp, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {recentActivities.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button className="w-full text-sm text-purple-600 hover:text-purple-700 font-medium transition-colors">
            Ver todas as atividades
          </button>
        </div>
      )}
    </div>
  );
}
