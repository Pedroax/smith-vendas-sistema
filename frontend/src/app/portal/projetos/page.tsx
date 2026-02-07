'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FolderKanban, Plus, Search, Filter, ChevronRight,
  Loader2, Calendar, CheckCircle2, Clock, AlertCircle
} from 'lucide-react';

import { API_URL } from '@/lib/api-config';

interface Project {
  id: string;
  nome: string;
  descricao?: string;
  tipo: string;
  status: string;
  progresso: number;
  etapa_atual: number;
  data_inicio?: string;
  data_previsao?: string;
  created_at: string;
}

export default function ProjectsListPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    fetchProjects();
  }, [statusFilter]);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const url = statusFilter
        ? `${API_URL}/api/portal/projects?status=${statusFilter}`
        : `${API_URL}/api/portal/projects`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setProjects(await response.json());
      }
    } catch (err) {
      console.error('Erro ao buscar projetos:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      briefing: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-200' },
      aguardando_materiais: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-200' },
      em_desenvolvimento: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200' },
      revisao: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-200' },
      aprovacao: { bg: 'bg-pink-100', text: 'text-pink-700', border: 'border-pink-200' },
      concluido: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-200' },
      pausado: { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-200' },
      cancelado: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200' },
    };
    return colors[status] || { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-200' };
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

  const getStatusIcon = (status: string) => {
    const icons: Record<string, any> = {
      concluido: CheckCircle2,
      em_desenvolvimento: Clock,
      aguardando_materiais: AlertCircle,
    };
    return icons[status] || FolderKanban;
  };

  const filteredProjects = projects.filter(project =>
    project.nome.toLowerCase().includes(search.toLowerCase()) ||
    project.tipo.toLowerCase().includes(search.toLowerCase())
  );

  const activeProjects = filteredProjects.filter(p => !['concluido', 'cancelado'].includes(p.status));
  const completedProjects = filteredProjects.filter(p => p.status === 'concluido');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Meus Projetos</h1>
          <p className="text-gray-500 mt-1">Acompanhe todos os seus projetos em um só lugar</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar projetos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 bg-white"
        >
          <option value="">Todos os status</option>
          <option value="briefing">Briefing</option>
          <option value="aguardando_materiais">Aguardando Materiais</option>
          <option value="em_desenvolvimento">Em Desenvolvimento</option>
          <option value="revisao">Revisão</option>
          <option value="aprovacao">Aguardando Aprovação</option>
          <option value="concluido">Concluído</option>
        </select>
      </div>

      {/* Active Projects */}
      {activeProjects.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Projetos Ativos ({activeProjects.length})
          </h2>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {activeProjects.map((project) => {
              const statusColors = getStatusColor(project.status);
              const StatusIcon = getStatusIcon(project.status);

              return (
                <Link
                  key={project.id}
                  href={`/portal/projetos/${project.id}`}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all p-5 group"
                >
                  {/* Progress Circle */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="relative w-14 h-14">
                      <svg className="w-14 h-14 -rotate-90">
                        <circle
                          cx="28"
                          cy="28"
                          r="24"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                          className="text-gray-100"
                        />
                        <circle
                          cx="28"
                          cy="28"
                          r="24"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                          strokeDasharray={`${project.progresso * 1.5} 150`}
                          className="text-purple-500"
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-700">
                        {project.progresso}%
                      </span>
                    </div>

                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors.bg} ${statusColors.text}`}>
                      {getStatusLabel(project.status)}
                    </span>
                  </div>

                  {/* Project Info */}
                  <h3 className="font-semibold text-gray-900 group-hover:text-purple-600 transition-colors truncate">
                    {project.nome}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1 truncate">{project.tipo}</p>

                  {/* Footer */}
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                    {project.data_previsao ? (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>Previsão: {new Date(project.data_previsao).toLocaleDateString('pt-BR')}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Criado em {new Date(project.created_at).toLocaleDateString('pt-BR')}</span>
                      </div>
                    )}

                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-purple-500 transition-colors" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Completed Projects */}
      {completedProjects.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Concluídos ({completedProjects.length})
          </h2>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {completedProjects.map((project) => (
              <Link
                key={project.id}
                href={`/portal/projetos/${project.id}`}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all p-5 group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-green-600" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 group-hover:text-purple-600 transition-colors truncate">
                      {project.nome}
                    </h3>
                    <p className="text-sm text-gray-500 truncate">{project.tipo}</p>
                  </div>

                  <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-purple-500 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {filteredProjects.length === 0 && (
        <div className="text-center py-16">
          <FolderKanban className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {search || statusFilter ? 'Nenhum projeto encontrado' : 'Você ainda não tem projetos'}
          </h3>
          <p className="text-gray-500">
            {search || statusFilter
              ? 'Tente ajustar os filtros de busca'
              : 'Quando você iniciar um projeto conosco, ele aparecerá aqui'
            }
          </p>
        </div>
      )}
    </div>
  );
}
