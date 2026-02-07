'use client';

import { useEffect, useState } from 'react';
import {
  MessageSquare, Loader2, CheckCircle2, AlertCircle, Clock,
  FolderKanban, ChevronDown, ChevronUp, ExternalLink, Image
} from 'lucide-react';

import { API_URL } from '@/lib/api-config';

interface Project {
  id: string;
  nome: string;
}

interface ApprovalItem {
  id: string;
  project_id: string;
  titulo: string;
  descricao?: string;
  tipo: string;
  status: 'aguardando' | 'aprovado' | 'ajustes_solicitados';
  arquivo_url?: string;
  link_externo?: string;
  feedback_cliente?: string;
  versao: number;
  enviado_em: string;
  respondido_em?: string;
}

export default function AprovacoesPag() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [approvals, setApprovals] = useState<Record<string, ApprovalItem[]>>({});
  const [loading, setLoading] = useState(true);
  const [expandedProject, setExpandedProject] = useState<string | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('portal_access_token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const projectsRes = await fetch(`${API_URL}/api/portal/projects`, { headers });
      if (projectsRes.ok) {
        const projectsData: Project[] = await projectsRes.json();
        setProjects(projectsData);

        const results = await Promise.all(
          projectsData.map(async (p) => {
            const res = await fetch(`${API_URL}/api/portal/projects/${p.id}/approvals`, { headers });
            return { id: p.id, data: res.ok ? await res.json().catch(() => []) : [] };
          })
        );

        const map: Record<string, ApprovalItem[]> = {};
        results.forEach((r) => { map[r.id] = r.data; });
        setApprovals(map);

        const first = results.find((r) => r.data.some((a: ApprovalItem) => a.status === 'aguardando'));
        if (first) setExpandedProject(first.id);
        else if (projectsData.length > 0) setExpandedProject(projectsData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const respondApproval = async (itemId: string, status: 'aprovado' | 'ajustes_solicitados') => {
    setUpdating(itemId);
    try {
      const token = localStorage.getItem('portal_access_token');
      const res = await fetch(`${API_URL}/api/portal/approvals/${itemId}/respond`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status,
          feedback_cliente: status === 'ajustes_solicitados' ? feedbackText : undefined,
        }),
      });
      if (res.ok) {
        setApprovals((prev) => {
          const updated = { ...prev };
          Object.keys(updated).forEach((pid) => {
            updated[pid] = updated[pid].map((a) =>
              a.id === itemId
                ? { ...a, status, feedback_cliente: feedbackText || a.feedback_cliente, respondido_em: new Date().toISOString() }
                : a
            );
          });
          return updated;
        });
        setFeedbackOpen(null);
        setFeedbackText('');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUpdating(null);
    }
  };

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { label: string; bg: string; text: string; icon: any }> = {
      aguardando: { label: 'Aguardando', bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock },
      aprovado: { label: 'Aprovado', bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle2 },
      ajustes_solicitados: { label: 'Ajustes Solicitados', bg: 'bg-orange-100', text: 'text-orange-700', icon: AlertCircle },
    };
    return configs[status] || configs.aguardando;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const totalAguardando = Object.values(approvals).flat().filter((a) => a.status === 'aguardando').length;
  const totalAprovados = Object.values(approvals).flat().filter((a) => a.status === 'aprovado').length;
  const totalAjustes = Object.values(approvals).flat().filter((a) => a.status === 'ajustes_solicitados').length;

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Aprovações</h1>
        <p className="text-gray-500 mt-1">Itens que precisam da sua aprovação</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-yellow-100 rounded-xl flex items-center justify-center">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalAguardando}</p>
          <p className="text-sm text-gray-500">Aguardando</p>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-green-100 rounded-xl flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalAprovados}</p>
          <p className="text-sm text-gray-500">Aprovados</p>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-orange-100 rounded-xl flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-orange-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalAjustes}</p>
          <p className="text-sm text-gray-500">Com Ajustes</p>
        </div>
      </div>

      {/* Projects with Approvals */}
      {projects.length === 0 ? (
        <div className="text-center py-16">
          <MessageSquare className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma aprovação</h3>
          <p className="text-gray-500">Não há itens aguardando aprovação</p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => {
            const items = approvals[project.id] || [];
            if (items.length === 0) return null;
            const isExpanded = expandedProject === project.id;
            const aguardando = items.filter((a) => a.status === 'aguardando').length;

            return (
              <div key={project.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpandedProject(isExpanded ? null : project.id)}
                  className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                      <FolderKanban className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-gray-900">{project.nome}</h3>
                      <p className="text-sm text-gray-500">{items.length} item{items.length !== 1 ? 's' : ''}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {aguardando > 0 && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
                        {aguardando} aguardando
                      </span>
                    )}
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-gray-100 divide-y divide-gray-100">
                    {items.map((item) => {
                      const config = getStatusConfig(item.status);
                      const StatusIcon = config.icon;
                      const isFeedbackOpen = feedbackOpen === item.id;

                      return (
                        <div key={item.id} className="p-5">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-medium text-gray-900">{item.titulo}</h4>
                                <span className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
                                  <StatusIcon className="w-3 h-3" />
                                  {config.label}
                                </span>
                                {item.versao > 1 && (
                                  <span className="text-xs text-gray-400">v{item.versao}</span>
                                )}
                              </div>
                              {item.descricao && (
                                <p className="text-sm text-gray-500 mt-1">{item.descricao}</p>
                              )}
                              {item.feedback_cliente && (
                                <p className="text-sm text-orange-600 mt-1 italic">Seu feedback: "{item.feedback_cliente}"</p>
                              )}
                              <p className="text-xs text-gray-400 mt-1">
                                Enviado em {new Date(item.enviado_em).toLocaleDateString('pt-BR')}
                                {item.respondido_em && ` · Respondido em ${new Date(item.respondido_em).toLocaleDateString('pt-BR')}`}
                              </p>
                            </div>

                            <div className="flex-shrink-0">
                              {/* Links to view content */}
                              <div className="flex gap-2 mb-3">
                                {item.arquivo_url && (
                                  <a
                                    href={item.arquivo_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
                                  >
                                    <Image className="w-4 h-4" /> Ver arquivo
                                  </a>
                                )}
                                {item.link_externo && (
                                  <a
                                    href={item.link_externo}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
                                  >
                                    <ExternalLink className="w-4 h-4" /> Abrir link
                                  </a>
                                )}
                              </div>

                              {/* Action buttons */}
                              {item.status === 'aguardando' && !isFeedbackOpen && (
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => respondApproval(item.id, 'aprovado')}
                                    disabled={updating === item.id}
                                    className="px-4 py-1.5 bg-green-600 text-white text-sm font-medium rounded-xl hover:bg-green-700 disabled:opacity-50 transition-colors"
                                  >
                                    Aprovar
                                  </button>
                                  <button
                                    onClick={() => setFeedbackOpen(item.id)}
                                    className="px-4 py-1.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-xl hover:bg-gray-200 transition-colors"
                                  >
                                    Pedir Ajustes
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Feedback input */}
                          {isFeedbackOpen && (
                            <div className="mt-4 pt-4 border-t border-gray-100">
                              <label className="text-sm font-medium text-gray-700 block mb-2">
                                Descreva os ajustes necessários:
                              </label>
                              <textarea
                                value={feedbackText}
                                onChange={(e) => setFeedbackText(e.target.value)}
                                rows={3}
                                placeholder="Ex: A cor do título precisa ser mais escura..."
                                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 text-sm resize-none"
                              />
                              <div className="flex gap-2 mt-3">
                                <button
                                  onClick={() => respondApproval(item.id, 'ajustes_solicitados')}
                                  disabled={updating === item.id || !feedbackText.trim()}
                                  className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-xl hover:bg-orange-700 disabled:opacity-50 transition-colors"
                                >
                                  Enviar Feedback
                                </button>
                                <button
                                  onClick={() => { setFeedbackOpen(null); setFeedbackText(''); }}
                                  className="px-4 py-2 bg-gray-100 text-gray-600 text-sm font-medium rounded-xl hover:bg-gray-200 transition-colors"
                                >
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
