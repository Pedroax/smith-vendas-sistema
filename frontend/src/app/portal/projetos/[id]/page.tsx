'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, Clock, FileCheck, MessageSquare, CreditCard,
  CheckCircle2, Loader2, AlertCircle, Upload, ChevronRight,
  Calendar, ExternalLink, Send, Paperclip, X, Check,
  FolderKanban, TrendingUp, Bell, User
} from 'lucide-react';
import { FileUpload } from '@/components/FileUpload';
import { useToast } from '@/contexts/ToastContext';
import { authStorage } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Stage {
  id: string;
  nome: string;
  descricao?: string;
  ordem: number;
  cor: string;
  concluida: boolean;
  data_conclusao?: string;
}

interface DeliveryItem {
  id: string;
  nome: string;
  descricao?: string;
  obrigatorio: boolean;
  status: string;
  arquivo_url?: string;
  enviado_em?: string;
}

interface ApprovalItem {
  id: string;
  titulo: string;
  descricao?: string;
  tipo: string;
  status: string;
  arquivo_url?: string;
  link_externo?: string;
  versao: number;
  enviado_em: string;
}

interface TimelineEvent {
  id: string;
  tipo: string;
  titulo: string;
  descricao?: string;
  created_at: string;
  is_client_action: boolean;
  metadata?: Record<string, any>;
}

interface Payment {
  id: string;
  descricao: string;
  valor: number;
  status: string;
  data_vencimento: string;
  data_pagamento?: string;
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
  data_inicio?: string;
  data_previsao?: string;
  access_token: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { showToast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryItem[]>([]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'timeline' | 'entregas' | 'aprovacoes' | 'pagamentos'>('timeline');
  const [updating, setUpdating] = useState<string | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState('');

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      const token = authStorage.getAccessToken();
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };

      // Buscar todos os dados em paralelo
      const [projectRes, stagesRes, deliveriesRes, approvalsRes, timelineRes, paymentsRes] = await Promise.all([
        fetch(`${API_URL}/api/portal/projects/${projectId}`, { headers }),
        fetch(`${API_URL}/api/portal/projects/${projectId}/stages`, { headers }),
        fetch(`${API_URL}/api/portal/projects/${projectId}/deliveries`, { headers }),
        fetch(`${API_URL}/api/portal/projects/${projectId}/approvals`, { headers }),
        fetch(`${API_URL}/api/portal/projects/${projectId}/timeline?limit=30`, { headers }),
        fetch(`${API_URL}/api/portal/projects/${projectId}/payments`, { headers }),
      ]);

      if (projectRes.ok) {
        const data = await projectRes.json();
        setProject(data);
      } else {
        throw new Error('Projeto não encontrado');
      }

      if (stagesRes.ok) setStages(await stagesRes.json());
      if (deliveriesRes.ok) setDeliveries(await deliveriesRes.json());
      if (approvalsRes.ok) setApprovals(await approvalsRes.json());
      if (timelineRes.ok) setTimeline(await timelineRes.json());
      if (paymentsRes.ok) setPayments(await paymentsRes.json());

    } catch (err: any) {
      setError(err.message || 'Erro ao carregar projeto');
    } finally {
      setLoading(false);
    }
  };

  const handleDeliveryUpload = async (itemId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const token = authStorage.getAccessToken();

    const res = await fetch(`${API_URL}/api/portal/deliveries/${itemId}/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Erro no upload' }));
      throw new Error(error.detail || 'Erro ao enviar arquivo');
    }

    const data = await res.json();

    // Atualizar a lista de entregas
    setDeliveries(prev => prev.map(d => d.id === itemId ? data.item : d));

    // Recarregar dados do projeto para atualizar timeline
    await fetchProjectData();

    showToast('Arquivo enviado com sucesso!', 'success');
  };

  const respondApproval = async (itemId: string, status: string) => {
    setUpdating(itemId);
    try {
      const token = authStorage.getAccessToken();
      const body: Record<string, any> = { status };
      if (status === 'ajustes_solicitados' && feedbackText.trim()) {
        body.feedback_cliente = feedbackText.trim();
      }
      const res = await fetch(`${API_URL}/api/portal/approvals/${itemId}/respond`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setApprovals(prev => prev.map(a => a.id === itemId ? { ...a, status } : a));
        setFeedbackOpen(null);
        setFeedbackText('');
        showToast('Resposta enviada com sucesso!', 'success');
        await fetchProjectData();
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao enviar resposta', 'error');
    } finally {
      setUpdating(null);
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
      cancelado: 'bg-red-500',
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
      cancelado: 'Cancelado',
    };
    return labels[status] || status;
  };

  const getEventIcon = (tipo: string) => {
    const icons: Record<string, any> = {
      projeto_criado: FolderKanban,
      etapa_avancada: TrendingUp,
      material_solicitado: FileCheck,
      material_enviado: Upload,
      material_aprovado: CheckCircle2,
      entrega_parcial: FileCheck,
      aprovacao_solicitada: MessageSquare,
      aprovado: CheckCircle2,
      ajustes_solicitados: AlertCircle,
      comentario: MessageSquare,
      projeto_concluido: CheckCircle2,
      pagamento_recebido: CreditCard,
      reuniao_agendada: Calendar,
    };
    return icons[tipo] || Bell;
  };

  const getEventColor = (tipo: string, isClient: boolean) => {
    if (isClient) return 'bg-blue-100 text-blue-600';

    const colors: Record<string, string> = {
      projeto_criado: 'bg-purple-100 text-purple-600',
      etapa_avancada: 'bg-green-100 text-green-600',
      material_enviado: 'bg-blue-100 text-blue-600',
      aprovado: 'bg-green-100 text-green-600',
      ajustes_solicitados: 'bg-yellow-100 text-yellow-600',
      projeto_concluido: 'bg-green-100 text-green-600',
      pagamento_recebido: 'bg-green-100 text-green-600',
    };
    return colors[tipo] || 'bg-purple-100 text-purple-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Erro</h2>
          <p className="text-gray-500 mb-4">{error || 'Projeto não encontrado'}</p>
          <Link href="/portal/projetos" className="text-purple-500 hover:text-purple-600">
            ← Voltar aos projetos
          </Link>
        </div>
      </div>
    );
  }

  const pendingDeliveries = deliveries.filter(d => d.status === 'pendente');
  const pendingApprovals = approvals.filter(a => a.status === 'aguardando');

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/portal/projetos"
          className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar aos projetos
        </Link>

        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">{project.nome}</h1>
            <p className="text-gray-500 mt-1">{project.tipo}</p>
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-4 py-2 rounded-full text-sm font-medium text-white ${getStatusColor(project.status)}`}>
              {getStatusLabel(project.status)}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Section */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Progresso do Projeto</h2>
          <span className="text-2xl font-bold text-purple-500">{project.progresso}%</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-3 bg-gray-100 rounded-full mb-6 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-fuchsia-500 rounded-full transition-all duration-500"
            style={{ width: `${project.progresso}%` }}
          />
        </div>

        {/* Stages Timeline */}
        <div className="relative">
          <div className="flex items-center justify-between">
            {stages.map((stage, index) => (
              <div
                key={stage.id}
                className={`flex flex-col items-center ${index === 0 ? '' : 'flex-1'}`}
              >
                {/* Connector Line */}
                {index > 0 && (
                  <div className="absolute h-1 top-4 -z-10" style={{
                    left: `${((index - 1) / (stages.length - 1)) * 100}%`,
                    width: `${100 / (stages.length - 1)}%`,
                    backgroundColor: stage.concluida || index <= project.etapa_atual ? stage.cor : '#e5e7eb'
                  }} />
                )}

                {/* Stage Circle */}
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center font-medium text-sm
                    transition-all duration-300 relative z-10
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
                  {stage.concluida ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    index + 1
                  )}
                </div>

                {/* Stage Label */}
                <span className={`
                  mt-2 text-xs font-medium text-center max-w-[80px] truncate
                  ${index === project.etapa_atual ? 'text-gray-900' : 'text-gray-500'}
                `}>
                  {stage.nome}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex border-b border-gray-100">
          {[
            { id: 'timeline', label: 'Timeline', icon: Clock },
            { id: 'entregas', label: 'Entregas', icon: FileCheck, badge: pendingDeliveries.length },
            { id: 'aprovacoes', label: 'Aprovações', icon: MessageSquare, badge: pendingApprovals.length },
            { id: 'pagamentos', label: 'Pagamentos', icon: CreditCard },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex-1 px-4 py-4 flex items-center justify-center gap-2 font-medium text-sm
                  transition-colors relative
                  ${activeTab === tab.id
                    ? 'text-purple-600 bg-purple-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.badge && tab.badge > 0 && (
                  <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
                    {tab.badge}
                  </span>
                )}
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500" />
                )}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Timeline Tab */}
          {activeTab === 'timeline' && (
            <div className="space-y-4">
              {timeline.length === 0 ? (
                <div className="text-center py-12">
                  <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Nenhum evento na timeline ainda</p>
                </div>
              ) : (
                <div className="relative">
                  {/* Timeline Line */}
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

                  {timeline.map((event, index) => {
                    const Icon = getEventIcon(event.tipo);
                    const colorClass = getEventColor(event.tipo, event.is_client_action);

                    return (
                      <div key={event.id} className="relative pl-12 pb-6">
                        {/* Event Icon */}
                        <div className={`absolute left-0 w-8 h-8 rounded-full flex items-center justify-center ${colorClass}`}>
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
          )}

          {/* Entregas Tab */}
          {activeTab === 'entregas' && (
            <div className="space-y-4">
              {deliveries.length === 0 ? (
                <div className="text-center py-12">
                  <FileCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Nenhuma entrega pendente</p>
                </div>
              ) : (
                deliveries.map((item) => (
                  <div
                    key={item.id}
                    className={`
                      p-4 rounded-xl border-2 transition-colors
                      ${item.status === 'pendente'
                        ? 'border-yellow-200 bg-yellow-50'
                        : item.status === 'enviado'
                          ? 'border-blue-200 bg-blue-50'
                          : 'border-green-200 bg-green-50'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900">{item.nome}</h4>
                          {item.obrigatorio && (
                            <span className="text-xs text-red-500">*Obrigatório</span>
                          )}
                        </div>
                        {item.descricao && (
                          <p className="text-sm text-gray-600 mt-1">{item.descricao}</p>
                        )}
                      </div>

                      {item.status === 'pendente' ? (
                        <FileUpload
                          onUpload={(file) => handleDeliveryUpload(item.id, file)}
                          accept="image/*,.pdf,.doc,.docx,.zip,.rar"
                          maxSizeMB={50}
                          label="Enviar Material"
                        />
                      ) : item.status === 'enviado' ? (
                        <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                          Aguardando análise
                        </span>
                      ) : (
                        <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-sm font-medium flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" />
                          Aprovado
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Aprovações Tab */}
          {activeTab === 'aprovacoes' && (
            <div className="space-y-4">
              {approvals.length === 0 ? (
                <div className="text-center py-12">
                  <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Nenhuma aprovação pendente</p>
                </div>
              ) : (
                approvals.map((item) => (
                  <div
                    key={item.id}
                    className={`
                      p-4 rounded-xl border-2 transition-colors
                      ${item.status === 'aguardando'
                        ? 'border-pink-200 bg-pink-50'
                        : item.status === 'aprovado'
                          ? 'border-green-200 bg-green-50'
                          : 'border-yellow-200 bg-yellow-50'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900">{item.titulo}</h4>
                          <span className="text-xs text-gray-500">v{item.versao}</span>
                        </div>
                        {item.descricao && (
                          <p className="text-sm text-gray-600 mt-1">{item.descricao}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-2">
                          Enviado em {new Date(item.enviado_em).toLocaleDateString('pt-BR')}
                        </p>
                      </div>

                      {item.status === 'aguardando' ? (
                        <div className="flex gap-2">
                          {item.arquivo_url && (
                            <a
                              href={item.arquivo_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          )}
                          <button
                            onClick={() => respondApproval(item.id, 'aprovado')}
                            disabled={updating === item.id}
                            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 transition-colors flex items-center gap-2"
                          >
                            {updating === item.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                            Aprovar
                          </button>
                          {feedbackOpen === item.id ? (
                            <div className="flex flex-col gap-2 w-64">
                              <textarea
                                value={feedbackText}
                                onChange={(e) => setFeedbackText(e.target.value)}
                                placeholder="Descreva os ajustes necessários..."
                                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500/50 resize-none"
                                rows={3}
                                autoFocus
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => respondApproval(item.id, 'ajustes_solicitados')}
                                  disabled={updating === item.id || !feedbackText.trim()}
                                  className="flex-1 px-3 py-1.5 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 transition-colors text-sm"
                                >
                                  Enviar
                                </button>
                                <button
                                  onClick={() => { setFeedbackOpen(null); setFeedbackText(''); }}
                                  className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                                >
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              onClick={() => setFeedbackOpen(item.id)}
                              className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
                            >
                              Pedir Ajustes
                            </button>
                          )}
                        </div>
                      ) : item.status === 'aprovado' ? (
                        <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-sm font-medium flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" />
                          Aprovado
                        </span>
                      ) : (
                        <span className="px-3 py-1.5 bg-yellow-100 text-yellow-700 rounded-lg text-sm font-medium">
                          Ajustes solicitados
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Pagamentos Tab */}
          {activeTab === 'pagamentos' && (
            <div className="space-y-4">
              {payments.length === 0 ? (
                <div className="text-center py-12">
                  <CreditCard className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Nenhum pagamento registrado</p>
                </div>
              ) : (
                payments.map((payment) => (
                  <div
                    key={payment.id}
                    className={`
                      p-4 rounded-xl border-2 transition-colors
                      ${payment.status === 'pendente'
                        ? 'border-yellow-200 bg-yellow-50'
                        : payment.status === 'pago'
                          ? 'border-green-200 bg-green-50'
                          : payment.status === 'atrasado'
                            ? 'border-red-200 bg-red-50'
                            : 'border-gray-200 bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h4 className="font-medium text-gray-900">{payment.descricao}</h4>
                        <p className="text-sm text-gray-500 mt-1">
                          Vencimento: {new Date(payment.data_vencimento).toLocaleDateString('pt-BR')}
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900">
                          R$ {payment.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </p>
                        {payment.status === 'pendente' ? (
                          <button className="mt-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors text-sm">
                            Pagar
                          </button>
                        ) : payment.status === 'pago' ? (
                          <span className="text-sm text-green-600 font-medium">
                            Pago em {new Date(payment.data_pagamento!).toLocaleDateString('pt-BR')}
                          </span>
                        ) : payment.status === 'atrasado' ? (
                          <span className="text-sm text-red-600 font-medium">Atrasado</span>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ))
              )}

              {/* Total */}
              {payments.length > 0 && (
                <div className="p-4 bg-gray-100 rounded-xl mt-4">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-700">Valor Total do Projeto</span>
                    <span className="text-xl font-bold text-gray-900">
                      R$ {project.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
