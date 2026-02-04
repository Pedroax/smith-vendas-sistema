'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Users, FolderKanban, TrendingUp, CheckCircle2, Clock,
  AlertCircle, Loader2, ArrowRight, Plus
} from 'lucide-react';

import { adminFetch } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AdminStats {
  total_clientes: number;
  total_projetos: number;
  projetos_ativos: number;
  projetos_concluidos: number;
  aguardando_materiais: number;
  em_desenvolvimento: number;
  aguardando_aprovacao: number;
}

interface Project {
  id: string;
  nome: string;
  tipo: string;
  status: string;
  progresso: number;
  client_id: string;
  created_at: string;
}

export default function AdminPortalDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, projectsRes] = await Promise.all([
        adminFetch(`${API_URL}/api/portal/admin/stats`),
        adminFetch(`${API_URL}/api/portal/admin/projects`),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (projectsRes.ok) {
        const projects: Project[] = await projectsRes.json();
        setRecentProjects(projects.slice(0, 6));
      }
    } catch (err) {
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
      revisao: 'bg-orange-100 text-orange-700',
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const statCards = [
    { label: 'Clientes', value: stats?.total_clientes || 0, icon: Users, color: 'bg-blue-100 text-blue-600', href: '/admin-portal/clientes' },
    { label: 'Projetos Ativos', value: stats?.projetos_ativos || 0, icon: FolderKanban, color: 'bg-purple-100 text-purple-600', href: '/admin-portal/projetos' },
    { label: 'Em Desenvolvimento', value: stats?.em_desenvolvimento || 0, icon: TrendingUp, color: 'bg-indigo-100 text-indigo-600', href: null },
    { label: 'Aguardando Aprovação', value: stats?.aguardando_aprovacao || 0, icon: AlertCircle, color: 'bg-yellow-100 text-yellow-600', href: null },
    { label: 'Aguardando Materiais', value: stats?.aguardando_materiais || 0, icon: Clock, color: 'bg-orange-100 text-orange-600', href: null },
    { label: 'Concluídos', value: stats?.projetos_concluidos || 0, icon: CheckCircle2, color: 'bg-green-100 text-green-600', href: null },
  ];

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Portal — Admin</h1>
          <p className="text-gray-500 mt-1">Gerenciar clientes e projetos do portal</p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/admin-portal/clientes"
            className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
          >
            <Users className="w-4 h-4" /> Clientes
          </Link>
          <Link
            href="/admin-portal/projetos"
            className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 transition-colors"
          >
            <Plus className="w-4 h-4" /> Novo Projeto
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {statCards.map((card) => {
          const Icon = card.icon;
          const content = (
            <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 ${card.color} rounded-xl flex items-center justify-center`}>
                  <Icon className="w-5 h-5" />
                </div>
                {card.href && <ArrowRight className="w-4 h-4 text-gray-400" />}
              </div>
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              <p className="text-sm text-gray-500">{card.label}</p>
            </div>
          );

          return card.href ? (
            <Link key={card.label} href={card.href}>{content}</Link>
          ) : (
            <div key={card.label}>{content}</div>
          );
        })}
      </div>

      {/* Recent Projects */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Projetos Recentes</h2>
          <Link href="/admin-portal/projetos" className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1">
            Ver todos <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {recentProjects.length === 0 ? (
          <div className="p-10 text-center">
            <FolderKanban className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">Nenhum projeto ainda</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentProjects.map((project) => (
              <Link
                key={project.id}
                href={`/admin-portal/projetos/${project.id}`}
                className="p-5 flex items-center gap-4 hover:bg-gray-50 transition-colors"
              >
                <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                  <FolderKanban className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">{project.nome}</h3>
                  <p className="text-sm text-gray-500">{project.tipo}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                  {getStatusLabel(project.status)}
                </span>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
