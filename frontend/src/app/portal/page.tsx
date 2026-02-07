'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FolderKanban, Clock, FileCheck, MessageSquare, CreditCard,
  ChevronRight, AlertCircle, CheckCircle2, Loader2, TrendingUp,
  Calendar, Bell
} from 'lucide-react';

import { API_URL } from '@/lib/api-config';

interface Project {
  id: string;
  nome: string;
  tipo: string;
  status: string;
  progresso: number;
  etapa_atual: number;
  data_previsao?: string;
  access_token: string;
}

interface Stats {
  total_projetos: number;
  projetos_ativos: number;
  projetos_concluidos: number;
  entregas_pendentes: number;
  aprovacoes_pendentes: number;
}

interface TimelineEvent {
  id: string;
  tipo: string;
  titulo: string;
  descricao?: string;
  created_at: string;
  is_client_action: boolean;
}

export default function PortalDashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentEvents, setRecentEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };

      // Buscar projetos, stats e eventos em paralelo
      const [projectsRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/api/portal/projects`, { headers }),
        fetch(`${API_URL}/api/portal/stats`, { headers }),
      ]);

      if (projectsRes.ok) {
        const projectsData = await projectsRes.json();
        setProjects(projectsData);

        // Buscar eventos do primeiro projeto ativo
        const activeProject = projectsData.find((p: Project) =>
          !['concluido', 'cancelado'].includes(p.status)
        );
        if (activeProject) {
          const eventsRes = await fetch(
            `${API_URL}/api/portal/projects/${activeProject.id}/timeline?limit=5`,
            { headers }
          );
          if (eventsRes.ok) {
            setRecentEvents(await eventsRes.json());
          }
        }
      }

      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
    } catch (err) {
      setError('Erro ao carregar dados');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      briefing: 'bg-purple-100 text-purple-700',
      aguardando_materiais: 'bg-yellow-100 text-yellow-700',
      em_desenvolvimento: 'bg-blue-100 text-blue-700',
      revisao: 'bg-purple-100 text-orange-700',
      aprovacao: 'bg-pink-100 text-pink-700',
      concluido: 'bg-green-100 text-green-700',
      pausado: 'bg-gray-100 text-gray-700',
      cancelado: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      briefing: 'Briefing',
      aguardando_materiais: 'Aguardando Materiais',
      em_desenvolvimento: 'Em Desenvolvimento',
      revisao: 'Revisão',
      aprovacao: 'Aguardando Aprovação',
      concluido: 'Concluído',
      pausado: 'Pausado',
      cancelado: 'Cancelado',
    };
    return labels[status] || status;
  };

  const getEventIcon = (tipo: string) => {
    const icons: Record<string, any> = {
      projeto_criado: FolderKanban,
      etapa_avancada: TrendingUp,
      material_enviado: FileCheck,
      aprovacao_solicitada: MessageSquare,
      aprovado: CheckCircle2,
      comentario: MessageSquare,
    };
    return icons[tipo] || Bell;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const clientData = typeof window !== 'undefined'
    ? JSON.parse(localStorage.getItem('portal_client') || '{}')
    : {};

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">
          Olá, {clientData.nome?.split(' ')[0] || 'Cliente'}! 👋
        </h1>
        <p className="text-gray-500 mt-1">
          Acompanhe o progresso dos seus projetos
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <FolderKanban className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats?.projetos_ativos || 0}</p>
          <p className="text-sm text-gray-500">Projetos Ativos</p>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
              <FileCheck className="w-5 h-5 text-yellow-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats?.entregas_pendentes || 0}</p>
          <p className="text-sm text-gray-500">Entregas Pendentes</p>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-pink-100 rounded-xl flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-pink-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats?.aprovacoes_pendentes || 0}</p>
          <p className="text-sm text-gray-500">Para Aprovar</p>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats?.projetos_concluidos || 0}</p>
          <p className="text-sm text-gray-500">Concluídos</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Projects List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Meus Projetos</h2>
              <Link
                href="/portal/projetos"
                className="text-sm text-purple-500 hover:text-purple-600 flex items-center gap-1"
              >
                Ver todos <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="divide-y divide-gray-100">
              {projects.length === 0 ? (
                <div className="p-8 text-center">
                  <FolderKanban className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Nenhum projeto encontrado</p>
                </div>
              ) : (
                projects.slice(0, 5).map((project) => (
                  <Link
                    key={project.id}
                    href={`/portal/projetos/${project.id}`}
                    className="p-5 flex items-center gap-4 hover:bg-gray-50 transition-colors"
                  >
                    {/* Progress Circle */}
                    <div className="relative w-12 h-12 flex-shrink-0">
                      <svg className="w-12 h-12 -rotate-90">
                        <circle
                          cx="24"
                          cy="24"
                          r="20"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                          className="text-gray-100"
                        />
                        <circle
                          cx="24"
                          cy="24"
                          r="20"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                          strokeDasharray={`${project.progresso * 1.256} 125.6`}
                          className="text-purple-500"
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-700">
                        {project.progresso}%
                      </span>
                    </div>

                    {/* Project Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">{project.nome}</h3>
                      <p className="text-sm text-gray-500 truncate">{project.tipo}</p>
                    </div>

                    {/* Status Badge */}
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                      {getStatusLabel(project.status)}
                    </span>

                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="p-5 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Atividade Recente</h2>
            </div>

            <div className="p-5">
              {recentEvents.length === 0 ? (
                <div className="text-center py-6">
                  <Clock className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Nenhuma atividade recente</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentEvents.map((event, index) => {
                    const Icon = getEventIcon(event.tipo);
                    return (
                      <div key={event.id} className="flex gap-3">
                        <div className={`
                          w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                          ${event.is_client_action ? 'bg-blue-100' : 'bg-purple-100'}
                        `}>
                          <Icon className={`w-4 h-4 ${event.is_client_action ? 'text-blue-600' : 'text-purple-600'}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {event.titulo}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(event.created_at).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-2xl p-6 mt-6 text-white">
            <h3 className="font-semibold mb-2">Precisa de ajuda?</h3>
            <p className="text-sm text-white/80 mb-4">
              Entre em contato com nossa equipe para tirar dúvidas sobre seus projetos.
            </p>
            <button className="w-full py-2.5 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-colors">
              Falar com Suporte
            </button>
          </div>
        </div>
      </div>

      {/* Pending Actions Alert */}
      {stats && (stats.entregas_pendentes > 0 || stats.aprovacoes_pendentes > 0) && (
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-2xl p-5 flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-yellow-900">Ações Pendentes</h3>
            <p className="text-sm text-yellow-700 mt-1">
              {stats.entregas_pendentes > 0 && (
                <span>Você tem {stats.entregas_pendentes} material(is) para enviar. </span>
              )}
              {stats.aprovacoes_pendentes > 0 && (
                <span>Você tem {stats.aprovacoes_pendentes} item(ns) aguardando sua aprovação.</span>
              )}
            </p>
            <div className="flex gap-3 mt-3">
              {stats.entregas_pendentes > 0 && (
                <Link
                  href="/portal/entregas"
                  className="text-sm font-medium text-yellow-700 hover:text-yellow-900"
                >
                  Ver Entregas →
                </Link>
              )}
              {stats.aprovacoes_pendentes > 0 && (
                <Link
                  href="/portal/aprovacoes"
                  className="text-sm font-medium text-yellow-700 hover:text-yellow-900"
                >
                  Ver Aprovações →
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
