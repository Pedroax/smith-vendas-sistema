'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Clock, FileCheck, MessageSquare, CreditCard,
  CheckCircle2, Loader2, AlertCircle, Upload, ChevronRight,
  ExternalLink, Check, FolderKanban, TrendingUp, Bell, User,
  ArrowRight, Lock
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Stage {
  id: string;
  nome: string;
  descricao?: string;
  ordem: number;
  cor: string;
  concluida: boolean;
}

interface TimelineEvent {
  id: string;
  tipo: string;
  titulo: string;
  descricao?: string;
  created_at: string;
  is_client_action: boolean;
}

interface Project {
  id: string;
  nome: string;
  descricao?: string;
  tipo: string;
  status: string;
  progresso: number;
  etapa_atual: number;
  valor_total: number;
  data_previsao?: string;
}

export default function PublicProjectPage() {
  const params = useParams();
  const token = params.token as string;

  const [project, setProject] = useState<Project | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [pendingDeliveries, setPendingDeliveries] = useState(0);
  const [pendingApprovals, setPendingApprovals] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProjectData();
  }, [token]);

  const fetchProjectData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/portal/projects/token/${token}`);

      if (!response.ok) {
        throw new Error('Projeto não encontrado ou link expirado');
      }

      const data = await response.json();
      setProject(data.project);
      setStages(data.stages || []);
      setTimeline(data.timeline || []);
      setPendingDeliveries(data.pending_deliveries || 0);
      setPendingApprovals(data.pending_approvals || 0);

    } catch (err: any) {
      setError(err.message || 'Erro ao carregar projeto');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      briefing: 'bg-purple-500',
      aguardando_materiais: 'bg-yellow-500',
      em_desenvolvimento: 'bg-blue-500',
      revisao: 'bg-purple-500',
      aprovacao: 'bg-pink-500',
      concluido: 'bg-green-500',
      pausado: 'bg-gray-500',
    };
    return colors[status] || 'bg-gray-500';
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
    };
    return labels[status] || status;
  };

  const getEventIcon = (tipo: string) => {
    const icons: Record<string, any> = {
      projeto_criado: FolderKanban,
      etapa_avancada: TrendingUp,
      material_enviado: Upload,
      aprovado: CheckCircle2,
      ajustes_solicitados: AlertCircle,
      comentario: MessageSquare,
      projeto_concluido: CheckCircle2,
    };
    return icons[tipo] || Bell;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Carregando projeto...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Projeto não encontrado</h2>
          <p className="text-gray-500 mb-6">
            {error || 'O link pode estar incorreto ou ter expirado.'}
          </p>
          <Link
            href="/portal/login"
            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-500 text-white rounded-xl hover:bg-purple-600 transition-colors"
          >
            Fazer login
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <div>
                <h1 className="font-bold text-gray-900">Ax ai</h1>
                <p className="text-xs text-gray-500">Portal do Cliente</p>
              </div>
            </div>

            <Link
              href="/portal/login"
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Lock className="w-4 h-4" />
              Entrar
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Project Header */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{project.nome}</h1>
              <p className="text-gray-500 mt-1">{project.tipo}</p>
            </div>

            <span className={`px-4 py-2 rounded-full text-sm font-medium text-white ${getStatusColor(project.status)} self-start`}>
              {getStatusLabel(project.status)}
            </span>
          </div>

          {/* Progress */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Progresso do Projeto</span>
              <span className="text-lg font-bold text-purple-500">{project.progresso}%</span>
            </div>
            <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-fuchsia-500 rounded-full transition-all duration-500"
                style={{ width: `${project.progresso}%` }}
              />
            </div>
          </div>

          {/* Stages */}
          <div className="flex items-center justify-between overflow-x-auto pb-2">
            {stages.map((stage, index) => (
              <div
                key={stage.id}
                className={`flex flex-col items-center min-w-[80px] ${index === 0 ? '' : 'flex-1'}`}
              >
                {/* Connector Line */}
                {index > 0 && (
                  <div
                    className="absolute h-1 -z-10"
                    style={{
                      left: `${((index - 1) / (stages.length - 1)) * 100}%`,
                      width: `${100 / (stages.length - 1)}%`,
                      backgroundColor: stage.concluida || index <= project.etapa_atual ? stage.cor : '#e5e7eb'
                    }}
                  />
                )}

                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center font-medium text-sm
                    ${stage.concluida
                      ? 'text-white'
                      : index === project.etapa_atual
                        ? 'text-white ring-4 ring-offset-2'
                        : 'bg-gray-100 text-gray-400'
                    }
                  `}
                  style={{
                    backgroundColor: stage.concluida || index === project.etapa_atual ? stage.cor : undefined,
                  }}
                >
                  {stage.concluida ? <Check className="w-4 h-4" /> : index + 1}
                </div>

                <span className={`
                  mt-2 text-xs font-medium text-center
                  ${index === project.etapa_atual ? 'text-gray-900' : 'text-gray-500'}
                `}>
                  {stage.nome}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Required Alert */}
        {(pendingDeliveries > 0 || pendingApprovals > 0) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-5 mb-6 flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-yellow-900">Ações Pendentes</h3>
              <p className="text-sm text-yellow-700 mt-1">
                {pendingDeliveries > 0 && (
                  <span>Você tem {pendingDeliveries} material(is) para enviar. </span>
                )}
                {pendingApprovals > 0 && (
                  <span>Você tem {pendingApprovals} item(ns) aguardando sua aprovação.</span>
                )}
              </p>
              <p className="text-sm text-yellow-700 mt-2">
                <Link href="/portal/login" className="font-medium underline">
                  Faça login
                </Link> para realizar essas ações.
              </p>
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-gray-400" />
              Linha do Tempo
            </h2>
          </div>

          <div className="p-6">
            {timeline.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Nenhum evento na timeline ainda</p>
              </div>
            ) : (
              <div className="relative">
                {/* Timeline Line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

                {timeline.map((event) => {
                  const Icon = getEventIcon(event.tipo);

                  return (
                    <div key={event.id} className="relative pl-12 pb-6 last:pb-0">
                      {/* Event Icon */}
                      <div className={`
                        absolute left-0 w-8 h-8 rounded-full flex items-center justify-center
                        ${event.is_client_action ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-purple-600'}
                      `}>
                        <Icon className="w-4 h-4" />
                      </div>

                      {/* Event Content */}
                      <div className="bg-gray-50 rounded-xl p-4">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h4 className="font-medium text-gray-900">{event.titulo}</h4>
                            {event.descricao && (
                              <p className="text-sm text-gray-600 mt-1">{event.descricao}</p>
                            )}
                          </div>
                          <span className="text-xs text-gray-500 whitespace-nowrap">
                            {new Date(event.created_at).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                        {event.is_client_action && (
                          <span className="inline-flex items-center gap-1 mt-2 text-xs text-blue-600">
                            <User className="w-3 h-3" />
                            Sua ação
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* CTA - Login */}
        <div className="bg-gradient-to-br from-purple-500 to-fuchsia-500 rounded-2xl p-6 mt-6 text-white text-center">
          <h3 className="text-xl font-bold mb-2">Acesso Completo</h3>
          <p className="text-white/80 mb-4">
            Faça login para enviar arquivos, aprovar entregas e ver mais detalhes do projeto.
          </p>
          <Link
            href="/portal/login"
            className="inline-flex items-center gap-2 px-6 py-3 bg-white text-purple-600 rounded-xl font-medium hover:bg-gray-100 transition-colors"
          >
            Entrar no Portal
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Powered by <span className="font-medium text-gray-700">Ax ai</span></p>
        </div>
      </div>
    </div>
  );
}
