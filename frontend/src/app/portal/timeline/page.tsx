'use client';

import { useEffect, useState } from 'react';
import {
  Clock, FolderKanban, TrendingUp, FileCheck, MessageSquare,
  CheckCircle2, Bell, Loader2, AlertCircle, CreditCard
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Project {
  id: string;
  nome: string;
}

interface TimelineEvent {
  id: string;
  project_id: string;
  tipo: string;
  titulo: string;
  descricao?: string;
  is_client_action: boolean;
  created_at: string;
}

export default function TimelinePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<string>('');

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchEvents(selectedProject);
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const res = await fetch(`${API_URL}/api/portal/projects`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0) {
          setSelectedProject(data[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvents = async (projectId: string) => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const res = await fetch(`${API_URL}/api/portal/projects/${projectId}/timeline`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        setEvents(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getEventIcon = (tipo: string) => {
    const icons: Record<string, any> = {
      projeto_criado: FolderKanban,
      etapa_avancada: TrendingUp,
      material_solicitado: AlertCircle,
      material_enviado: FileCheck,
      material_aprovado: CheckCircle2,
      aprovacao_solicitada: MessageSquare,
      aprovado: CheckCircle2,
      ajustes_solicitados: AlertCircle,
      comentario: MessageSquare,
      projeto_concluido: CheckCircle2,
      pagamento_recebido: CreditCard,
    };
    return icons[tipo] || Bell;
  };

  const getEventColor = (evento: TimelineEvent) => {
    if (evento.is_client_action) return { bg: 'bg-blue-100', icon: 'text-blue-600', line: 'bg-blue-300' };
    const colors: Record<string, { bg: string; icon: string; line: string }> = {
      projeto_criado: { bg: 'bg-purple-100', icon: 'text-purple-600', line: 'bg-purple-300' },
      etapa_avancada: { bg: 'bg-indigo-100', icon: 'text-indigo-600', line: 'bg-indigo-300' },
      aprovado: { bg: 'bg-green-100', icon: 'text-green-600', line: 'bg-green-300' },
      projeto_concluido: { bg: 'bg-green-100', icon: 'text-green-600', line: 'bg-green-300' },
      ajustes_solicitados: { bg: 'bg-yellow-100', icon: 'text-yellow-600', line: 'bg-yellow-300' },
      pagamento_recebido: { bg: 'bg-emerald-100', icon: 'text-emerald-600', line: 'bg-emerald-300' },
    };
    return colors[evento.tipo] || { bg: 'bg-gray-100', icon: 'text-gray-600', line: 'bg-gray-300' };
  };

  const formatDate = (date: string) =>
    new Date(date).toLocaleDateString('pt-BR', {
      day: '2-digit', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

  const groupByDate = (evts: TimelineEvent[]) => {
    const groups: Record<string, TimelineEvent[]> = {};
    evts.forEach((evt) => {
      const day = new Date(evt.created_at).toLocaleDateString('pt-BR', {
        day: '2-digit', month: 'long', year: 'numeric',
      });
      if (!groups[day]) groups[day] = [];
      groups[day].push(evt);
    });
    return groups;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const grouped = groupByDate(events);

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Timeline</h1>
          <p className="text-gray-500 mt-1">Histórico completo do projeto</p>
        </div>

        {projects.length > 1 && (
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 bg-white"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.nome}</option>
            ))}
          </select>
        )}
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-16">
          <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum projeto encontrado</h3>
          <p className="text-gray-500">A timeline aparecerá quando você tiver projetos ativos</p>
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-16">
          <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Timeline vazia</h3>
          <p className="text-gray-500">Não há eventos registrados ainda para este projeto</p>
        </div>
      ) : (
        <div className="max-w-2xl mx-auto">
          {/* Legend */}
          <div className="flex gap-4 mb-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-400" />
              <span className="text-sm text-gray-600">Suas ações</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-400" />
              <span className="text-sm text-gray-600">Ações da equipe</span>
            </div>
          </div>

          {/* Timeline */}
          {Object.entries(grouped).map(([day, dayEvents]) => (
            <div key={day} className="mb-8">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">{day}</h3>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
                <div className="space-y-4">
                  {dayEvents.map((event, index) => {
                    const Icon = getEventIcon(event.tipo);
                    const colors = getEventColor(event);
                    return (
                      <div key={event.id} className="relative flex gap-4">
                        {/* Icon */}
                        <div className={`relative z-10 w-8 h-8 rounded-full ${colors.bg} flex items-center justify-center flex-shrink-0`}>
                          <Icon className={`w-4 h-4 ${colors.icon}`} />
                        </div>

                        {/* Content */}
                        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex-1">
                          <div className="flex items-start justify-between gap-2">
                            <p className="font-medium text-gray-900">{event.titulo}</p>
                            <span className="text-xs text-gray-400 whitespace-nowrap">
                              {new Date(event.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          {event.descricao && (
                            <p className="text-sm text-gray-500 mt-1">{event.descricao}</p>
                          )}
                          <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full ${event.is_client_action ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'}`}>
                            {event.is_client_action ? 'Você' : 'Equipe'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
