'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft, Loader2, Plus, X, CheckCircle2, Clock,
  AlertCircle, Upload, MessageSquare, CreditCard, FileCheck,
  TrendingUp, Bell, FolderKanban, ChevronRight, Send
} from 'lucide-react';
import { FileUpload } from '@/components/FileUpload';
import { useToast } from '@/contexts/ToastContext';
import { adminFetch } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Types ──────────────────────────────────────────────────────────────────
interface Stage {
  id: string;
  nome: string;
  descricao?: string;
  ordem: number;
  concluida: boolean;
  cor: string;
}

interface DeliveryItem {
  id: string;
  nome: string;
  descricao?: string;
  obrigatorio: boolean;
  status: string;
  arquivo_url?: string;
  comentario_cliente?: string;
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
  feedback_cliente?: string;
  versao: number;
  enviado_em: string;
}

interface Payment {
  id: string;
  descricao: string;
  valor: number;
  status: string;
  data_vencimento: string;
  data_pagamento?: string;
  parcela: number;
  total_parcelas: number;
}

interface Comment {
  id: string;
  conteudo: string;
  user_nome: string;
  is_client: boolean;
  created_at: string;
}

interface TimelineEvent {
  id: string;
  tipo: string;
  titulo: string;
  descricao?: string;
  is_client_action: boolean;
  created_at: string;
}

interface Project {
  id: string;
  nome: string;
  descricao?: string;
  tipo: string;
  status: string;
  progresso: number;
  valor_total: number;
  etapa_atual: number;
  client_id: string;
  data_previsao?: string;
  created_at: string;
}

// ─── Status helpers ─────────────────────────────────────────────────────────
const STATUS_LABELS: Record<string, string> = {
  briefing: 'Briefing', aguardando_materiais: 'Aguardando Materiais',
  em_desenvolvimento: 'Em Desenvolvimento', revisao: 'Revisão',
  aprovacao: 'Aguardando Aprovação', concluido: 'Concluído',
  pausado: 'Pausado', cancelado: 'Cancelado',
};

const STATUS_COLORS: Record<string, string> = {
  briefing: 'bg-purple-100 text-purple-700',
  aguardando_materiais: 'bg-yellow-100 text-yellow-700',
  em_desenvolvimento: 'bg-blue-100 text-blue-700',
  revisao: 'bg-orange-100 text-orange-700',
  aprovacao: 'bg-pink-100 text-pink-700',
  concluido: 'bg-green-100 text-green-700',
  pausado: 'bg-gray-100 text-gray-700',
  cancelado: 'bg-red-100 text-red-700',
};

const TABS = ['Etapas', 'Entregas', 'Aprovações', 'Pagamentos', 'Comentários', 'Timeline'];

// ─── Main page ──────────────────────────────────────────────────────────────
export default function AdminProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { showToast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryItem[]>([]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Etapas');

  // Modal / form states
  const [modalType, setModalType] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [commentText, setCommentText] = useState('');

  // Forms
  const [deliveryForm, setDeliveryForm] = useState({ nome: '', descricao: '', obrigatorio: true });
  const [approvalForm, setApprovalForm] = useState({ titulo: '', descricao: '', tipo: 'arquivo', arquivo_url: '', link_externo: '' });
  const [paymentForm, setPaymentForm] = useState({ descricao: '', valor: '', data_vencimento: '', parcela: '1', total_parcelas: '1' });
  const [selectedApprovalFile, setSelectedApprovalFile] = useState<File | null>(null);

  useEffect(() => {
    fetchAll();
  }, [id]);

  const fetchAll = async () => {
    console.log('📥 Carregando projeto:', id);
    setLoading(true);

    try {
      // Buscar projeto
      console.log('  🔍 Buscando projeto...');
      const allProjects = await adminFetch(`${API_URL}/api/portal/admin/projects`).then((r) => r.json());
      const proj = allProjects.find((p: Project) => p.id === id);

      if (!proj) {
        console.error('❌ Projeto não encontrado:', id);
        showToast('Projeto não encontrado', 'error');
        router.push('/admin-portal/projetos');
        return;
      }

      setProject(proj);
      console.log('  ✅ Projeto carregado:', proj.nome);

      // Buscar dados relacionados (não bloquear se falhar)
      console.log('  📦 Buscando dados relacionados...');

      try {
        const stagesRes = await adminFetch(`${API_URL}/api/portal/projects/${id}/stages`);
        if (stagesRes.ok) {
          setStages(await stagesRes.json());
          console.log('    ✅ Etapas carregadas');
        }
      } catch (err) { console.error('    ❌ Erro ao carregar etapas:', err); }

      try {
        const delivRes = await adminFetch(`${API_URL}/api/portal/projects/${id}/deliveries`);
        if (delivRes.ok) {
          setDeliveries(await delivRes.json());
          console.log('    ✅ Entregas carregadas');
        }
      } catch (err) { console.error('    ❌ Erro ao carregar entregas:', err); }

      try {
        const approvRes = await adminFetch(`${API_URL}/api/portal/projects/${id}/approvals`);
        if (approvRes.ok) {
          setApprovals(await approvRes.json());
          console.log('    ✅ Aprovações carregadas');
        }
      } catch (err) { console.error('    ❌ Erro ao carregar aprovações:', err); }

      try {
        const paymentsRes = await adminFetch(`${API_URL}/api/portal/projects/${id}/payments`);
        if (paymentsRes.ok) {
          setPayments(await paymentsRes.json());
          console.log('    ✅ Pagamentos carregados');
        }
      } catch (err) { console.error('    ❌ Erro ao carregar pagamentos:', err); }

      try {
        const commentsRes = await adminFetch(`${API_URL}/api/portal/projects/${id}/comments`);
        if (commentsRes.ok) {
          setComments(await commentsRes.json());
          console.log('    ✅ Comentários carregados');
        }
      } catch (err) { console.error('    ❌ Erro ao carregar comentários:', err); }

      try {
        const timelineRes = await adminFetch(`${API_URL}/api/portal/projects/${id}/timeline`);
        if (timelineRes.ok) {
          setTimeline(await timelineRes.json());
          console.log('    ✅ Timeline carregada');
        }
      } catch (err) { console.error('    ❌ Erro ao carregar timeline:', err); }

      console.log('✅ Carregamento concluído!');
    } catch (err) {
      console.error('❌ Erro geral ao carregar projeto:', err);
      showToast('Erro ao carregar projeto', 'error');
    } finally {
      setLoading(false);
    }
  };

  // ─── Actions ──────────────────────────────────────────────────────────────
  const advanceStage = async () => {
    setSubmitting(true);
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/projects/${id}/advance`, { method: 'POST' });
      if (res.ok) await fetchAll();
    } finally { setSubmitting(false); }
  };

  const updateProjectStatus = async (status: string) => {
    try {
      await adminFetch(`${API_URL}/api/portal/admin/projects/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      await fetchAll();
    } catch (err) { console.error(err); }
  };

  const createDelivery = async () => {
    setSubmitting(true);
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/projects/${id}/deliveries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(deliveryForm),
      });
      if (res.ok) {
        const newDelivery = await res.json();
        setDeliveries((prev) => [...prev, newDelivery]);
        setDeliveryForm({ nome: '', descricao: '', obrigatorio: true });
        setModalType(null);
        showToast('Item de entrega criado!', 'success');
        await fetchAll();
      } else {
        showToast('Erro ao criar item de entrega', 'error');
      }
    } catch (err) {
      showToast('Erro ao criar item de entrega', 'error');
    } finally { setSubmitting(false); }
  };

  const updateDeliveryStatus = async (itemId: string, status: string) => {
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/deliveries/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        setDeliveries((prev) => prev.map((d) => d.id === itemId ? { ...d, status } : d));
        showToast('Status atualizado!', 'success');
        await fetchAll();
      } else {
        showToast('Erro ao atualizar status', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao atualizar status', 'error');
    }
  };

  const createApproval = async () => {
    setSubmitting(true);
    try {
      // Criar o item de aprovação
      const res = await adminFetch(`${API_URL}/api/portal/admin/projects/${id}/approvals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(approvalForm),
      });

      if (!res.ok) {
        throw new Error('Erro ao criar aprovação');
      }

      const newApproval = await res.json();

      // Se há arquivo selecionado, fazer upload
      if (selectedApprovalFile) {
        const formData = new FormData();
        formData.append('file', selectedApprovalFile);

        const uploadRes = await adminFetch(`${API_URL}/api/portal/admin/approvals/${newApproval.id}/upload`, {
          method: 'POST',
          body: formData,
        });

        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          // Atualizar com dados do upload
          setApprovals((prev) => [...prev, uploadData.item]);
          showToast('Aprovação criada e arquivo enviado!', 'success');
        } else {
          // Aprovação criada mas upload falhou
          setApprovals((prev) => [...prev, newApproval]);
          showToast('Aprovação criada, mas erro no upload do arquivo', 'warning');
        }
      } else {
        setApprovals((prev) => [...prev, newApproval]);
        showToast('Aprovação criada com sucesso!', 'success');
      }

      // Limpar formulário
      setApprovalForm({ titulo: '', descricao: '', tipo: 'arquivo', arquivo_url: '', link_externo: '' });
      setSelectedApprovalFile(null);
      setModalType(null);
      await fetchAll();
    } catch (err) {
      console.error(err);
      showToast('Erro ao criar aprovação', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const createPayment = async () => {
    setSubmitting(true);
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/projects/${id}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          descricao: paymentForm.descricao,
          valor: parseFloat(paymentForm.valor),
          data_vencimento: paymentForm.data_vencimento,
          parcela: parseInt(paymentForm.parcela),
          total_parcelas: parseInt(paymentForm.total_parcelas),
        }),
      });
      if (res.ok) {
        const newPayment = await res.json();
        setPayments((prev) => [...prev, newPayment]);
        setPaymentForm({ descricao: '', valor: '', data_vencimento: '', parcela: '1', total_parcelas: '1' });
        setModalType(null);
        showToast('Pagamento criado!', 'success');
        await fetchAll();
      } else {
        showToast('Erro ao criar pagamento', 'error');
      }
    } catch (err) {
      showToast('Erro ao criar pagamento', 'error');
    } finally { setSubmitting(false); }
  };

  const updatePaymentStatus = async (paymentId: string, status: string) => {
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/payments/${paymentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, data_pagamento: status === 'pago' ? new Date().toISOString() : null }),
      });
      if (res.ok) {
        setPayments((prev) => prev.map((p) => p.id === paymentId ? { ...p, status } : p));
        showToast('Status do pagamento atualizado!', 'success');
        await fetchAll();
      } else {
        showToast('Erro ao atualizar pagamento', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao atualizar pagamento', 'error');
    }
  };

  const addComment = async () => {
    if (!commentText.trim()) return;
    setSubmitting(true);
    try {
      const res = await adminFetch(`${API_URL}/api/portal/admin/projects/${id}/comments?user_nome=Equipe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conteudo: commentText }),
      });
      if (res.ok) {
        const newComment = await res.json();
        setComments((prev) => [newComment, ...prev]);
        setCommentText('');
      }
    } finally { setSubmitting(false); }
  };

  // ─── Render helpers ───────────────────────────────────────────────────────
  const formatCurrency = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const getDeliveryStatusConfig = (status: string) => {
    const map: Record<string, { label: string; bg: string; text: string }> = {
      pendente: { label: 'Pendente', bg: 'bg-yellow-100', text: 'text-yellow-700' },
      enviado: { label: 'Enviado pelo Cliente', bg: 'bg-blue-100', text: 'text-blue-700' },
      aprovado: { label: 'Aprovado', bg: 'bg-green-100', text: 'text-green-700' },
      rejeitado: { label: 'Rejeitado', bg: 'bg-red-100', text: 'text-red-700' },
    };
    return map[status] || map.pendente;
  };

  const getApprovalStatusConfig = (status: string) => {
    const map: Record<string, { label: string; bg: string; text: string }> = {
      aguardando: { label: 'Aguardando Cliente', bg: 'bg-yellow-100', text: 'text-yellow-700' },
      aprovado: { label: 'Aprovado', bg: 'bg-green-100', text: 'text-green-700' },
      ajustes_solicitados: { label: 'Ajustes Solicitados', bg: 'bg-orange-100', text: 'text-orange-700' },
    };
    return map[status] || map.aguardando;
  };

  const getPaymentStatusConfig = (status: string) => {
    const map: Record<string, { label: string; bg: string; text: string }> = {
      pendente: { label: 'Pendente', bg: 'bg-yellow-100', text: 'text-yellow-700' },
      pago: { label: 'Pago', bg: 'bg-green-100', text: 'text-green-700' },
      atrasado: { label: 'Atrasado', bg: 'bg-red-100', text: 'text-red-700' },
      cancelado: { label: 'Cancelado', bg: 'bg-gray-100', text: 'text-gray-600' },
    };
    return map[status] || map.pendente;
  };

  const getEventIcon = (tipo: string) => {
    const icons: Record<string, any> = {
      projeto_criado: FolderKanban, etapa_avancada: TrendingUp,
      material_enviado: FileCheck, aprovacao_solicitada: MessageSquare,
      aprovado: CheckCircle2, comentario: MessageSquare,
      pagamento_recebido: CreditCard, projeto_concluido: CheckCircle2,
    };
    return icons[tipo] || Bell;
  };

  // ─── Loading ──────────────────────────────────────────────────────────────
  if (loading || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  // ─── Tab content renderers ────────────────────────────────────────────────
  const renderEtapas = () => (
    <div>
      {/* Stage pipeline */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {stages.map((stage, i) => (
          <div key={stage.id} className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition-colors ${
              i < project.etapa_atual ? 'bg-green-100 border-green-300 text-green-700'
              : i === project.etapa_atual ? 'bg-purple-100 border-purple-400 text-purple-700 font-semibold'
              : 'bg-gray-50 border-gray-200 text-gray-500'
            }`}>
              {i < project.etapa_atual ? <CheckCircle2 className="w-4 h-4" /> : <span className="w-4 h-4 flex items-center justify-center text-xs">{i + 1}</span>}
              <span className="text-sm">{stage.nome}</span>
            </div>
            {i < stages.length - 1 && <ChevronRight className="w-4 h-4 text-gray-300" />}
          </div>
        ))}
      </div>

      {/* Advance button */}
      <div className="flex items-center gap-3">
        <button
          onClick={advanceStage}
          disabled={submitting || project.etapa_atual >= stages.length - 1}
          className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          <TrendingUp className="w-4 h-4" />
          {submitting ? 'Avançando...' : 'Avançar Etapa'}
        </button>

        <select
          value={project.status}
          onChange={(e) => updateProjectStatus(e.target.value)}
          className="px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white text-sm"
        >
          <option value="briefing">Briefing</option>
          <option value="aguardando_materiais">Aguardando Materiais</option>
          <option value="em_desenvolvimento">Em Desenvolvimento</option>
          <option value="revisao">Revisão</option>
          <option value="aprovacao">Aguardando Aprovação</option>
          <option value="concluido">Concluído</option>
          <option value="pausado">Pausado</option>
          <option value="cancelado">Cancelado</option>
        </select>
      </div>

      {stages.length === 0 && (
        <p className="text-gray-500 text-sm mt-4">Nenhuma etapa definida para este projeto.</p>
      )}
    </div>
  );

  const renderEntregas = () => (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-500">{deliveries.length} item{deliveries.length !== 1 ? 's' : ''}</p>
        <button onClick={() => setModalType('delivery')} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-xl hover:bg-purple-700 transition-colors">
          <Plus className="w-4 h-4" /> Nova Entrega
        </button>
      </div>
      {deliveries.length === 0 ? (
        <div className="text-center py-10"><FileCheck className="w-12 h-12 text-gray-300 mx-auto mb-2" /><p className="text-gray-500">Sem entregas</p></div>
      ) : (
        <div className="space-y-3">
          {deliveries.map((d) => {
            const cfg = getDeliveryStatusConfig(d.status);
            return (
              <div key={d.id} className="bg-gray-50 rounded-xl p-4 flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900">{d.nome}</p>
                    {d.obrigatorio && <span className="text-xs text-red-500 font-medium">Obrigatório</span>}
                  </div>
                  {d.descricao && <p className="text-sm text-gray-500 mt-0.5">{d.descricao}</p>}
                  {d.comentario_cliente && <p className="text-sm text-blue-600 mt-1 italic">Cliente: "{d.comentario_cliente}"</p>}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>{cfg.label}</span>
                  {d.status === 'enviado' && (
                    <>
                      <button onClick={() => updateDeliveryStatus(d.id, 'aprovado')} className="px-3 py-1 bg-green-600 text-white text-xs font-medium rounded-lg hover:bg-green-700">Aprovar</button>
                      <button onClick={() => updateDeliveryStatus(d.id, 'rejeitado')} className="px-3 py-1 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700">Rejeitar</button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  const renderAprovacoes = () => (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-500">{approvals.length} item{approvals.length !== 1 ? 's' : ''}</p>
        <button onClick={() => setModalType('approval')} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-xl hover:bg-purple-700 transition-colors">
          <Plus className="w-4 h-4" /> Nova Aprovação
        </button>
      </div>
      {approvals.length === 0 ? (
        <div className="text-center py-10"><MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-2" /><p className="text-gray-500">Sem aprovações</p></div>
      ) : (
        <div className="space-y-3">
          {approvals.map((a) => {
            const cfg = getApprovalStatusConfig(a.status);
            return (
              <div key={a.id} className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-gray-900">{a.titulo}</p>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>{cfg.label}</span>
                      {a.versao > 1 && <span className="text-xs text-gray-400">v{a.versao}</span>}
                    </div>
                    {a.descricao && <p className="text-sm text-gray-500 mt-0.5">{a.descricao}</p>}
                    {a.feedback_cliente && <p className="text-sm text-orange-600 mt-1 italic">Feedback: "{a.feedback_cliente}"</p>}
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {a.arquivo_url && <a href={a.arquivo_url} target="_blank" rel="noopener noreferrer" className="text-sm text-purple-600 hover:text-purple-700">Ver arquivo</a>}
                    {a.link_externo && <a href={a.link_externo} target="_blank" rel="noopener noreferrer" className="text-sm text-purple-600 hover:text-purple-700">Ver link</a>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  const renderPagamentos = () => (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-500">{payments.length} pagamento{payments.length !== 1 ? 's' : ''}</p>
        <button onClick={() => setModalType('payment')} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-xl hover:bg-purple-700 transition-colors">
          <Plus className="w-4 h-4" /> Novo Pagamento
        </button>
      </div>
      {payments.length === 0 ? (
        <div className="text-center py-10"><CreditCard className="w-12 h-12 text-gray-300 mx-auto mb-2" /><p className="text-gray-500">Sem pagamentos</p></div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead><tr className="bg-gray-50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Descrição</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Parcela</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Valor</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Vencimento</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3" />
            </tr></thead>
            <tbody className="divide-y divide-gray-100">
              {payments.map((p) => {
                const cfg = getPaymentStatusConfig(p.status);
                return (
                  <tr key={p.id}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{p.descricao}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{p.parcela}/{p.total_parcelas}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-900">{formatCurrency(p.valor)}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{new Date(p.data_vencimento).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3"><span className={`px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>{cfg.label}</span></td>
                    <td className="px-4 py-3">
                      {p.status === 'pendente' && (
                        <button onClick={() => updatePaymentStatus(p.id, 'pago')} className="text-xs font-medium text-purple-600 hover:text-purple-700">Marcar Pago</button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderComentarios = () => (
    <div>
      {/* Comment input */}
      <div className="flex gap-3 mb-6">
        <textarea
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="Adicionar comentário para o cliente..."
          rows={2}
          className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 resize-none"
        />
        <button
          onClick={addComment}
          disabled={submitting || !commentText.trim()}
          className="px-4 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      {comments.length === 0 ? (
        <div className="text-center py-10"><MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-2" /><p className="text-gray-500">Sem comentários</p></div>
      ) : (
        <div className="space-y-3">
          {comments.map((c) => (
            <div key={c.id} className={`p-4 rounded-xl ${c.is_client ? 'bg-blue-50 border border-blue-100' : 'bg-purple-50 border border-purple-100'}`}>
              <div className="flex items-center justify-between mb-1">
                <span className={`text-sm font-semibold ${c.is_client ? 'text-blue-700' : 'text-purple-700'}`}>
                  {c.is_client ? 'Cliente' : c.user_nome}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(c.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-sm text-gray-700">{c.conteudo}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderTimeline = () => (
    <div className="max-w-xl">
      {timeline.length === 0 ? (
        <div className="text-center py-10"><Clock className="w-12 h-12 text-gray-300 mx-auto mb-2" /><p className="text-gray-500">Timeline vazia</p></div>
      ) : (
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
          <div className="space-y-4">
            {timeline.map((evt) => {
              const Icon = getEventIcon(evt.tipo);
              const colors = evt.is_client_action
                ? { bg: 'bg-blue-100', icon: 'text-blue-600' }
                : { bg: 'bg-purple-100', icon: 'text-purple-600' };
              return (
                <div key={evt.id} className="relative flex gap-4">
                  <div className={`relative z-10 w-8 h-8 rounded-full ${colors.bg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-4 h-4 ${colors.icon}`} />
                  </div>
                  <div className="bg-white rounded-xl border border-gray-100 p-3 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-gray-900">{evt.titulo}</p>
                      <span className="text-xs text-gray-400 whitespace-nowrap">
                        {new Date(evt.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    {evt.descricao && <p className="text-xs text-gray-500 mt-0.5">{evt.descricao}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );

  const tabContent: Record<string, () => React.JSX.Element> = {
    'Etapas': renderEtapas,
    'Entregas': renderEntregas,
    'Aprovações': renderAprovacoes,
    'Pagamentos': renderPagamentos,
    'Comentários': renderComentarios,
    'Timeline': renderTimeline,
  };

  // ─── Modal ────────────────────────────────────────────────────────────────
  const renderModal = () => {
    if (!modalType) return null;

    const titles: Record<string, string> = {
      delivery: 'Nova Entrega', approval: 'Nova Aprovação', payment: 'Novo Pagamento',
    };

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/40" onClick={() => setModalType(null)} />
        <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-bold text-gray-900">{titles[modalType]}</h2>
            <button onClick={() => setModalType(null)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
          </div>
          <div className="p-6 space-y-4">
            {modalType === 'delivery' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Nome do material</label>
                  <input type="text" value={deliveryForm.nome} onChange={(e) => setDeliveryForm((f) => ({ ...f, nome: e.target.value }))} placeholder="Logo em PNG" className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Descrição</label>
                  <input type="text" value={deliveryForm.descricao} onChange={(e) => setDeliveryForm((f) => ({ ...f, descricao: e.target.value }))} placeholder="Fundo transparente, alta resolução" className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={deliveryForm.obrigatorio} onChange={(e) => setDeliveryForm((f) => ({ ...f, obrigatorio: e.target.checked }))} className="w-4 h-4 accent-purple-600" />
                  <span className="text-sm text-gray-700">Obrigatório</span>
                </label>
                <button onClick={createDelivery} disabled={submitting || !deliveryForm.nome} className="w-full py-3 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors">
                  {submitting ? 'Criando...' : 'Criar'}
                </button>
              </>
            )}

            {modalType === 'approval' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Título</label>
                  <input type="text" value={approvalForm.titulo} onChange={(e) => setApprovalForm((f) => ({ ...f, titulo: e.target.value }))} placeholder="Logo final v1" className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Descrição</label>
                  <input type="text" value={approvalForm.descricao} onChange={(e) => setApprovalForm((f) => ({ ...f, descricao: e.target.value }))} placeholder="Logo principal da marca" className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Tipo</label>
                  <select value={approvalForm.tipo} onChange={(e) => setApprovalForm((f) => ({ ...f, tipo: e.target.value }))} className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white">
                    <option value="arquivo">Arquivo</option>
                    <option value="link">Link</option>
                    <option value="texto">Texto</option>
                  </select>
                </div>
                {approvalForm.tipo === 'arquivo' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Arquivo</label>
                      <div className="border-2 border-dashed border-gray-200 rounded-xl p-4">
                        {selectedApprovalFile ? (
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Upload className="w-4 h-4 text-purple-600" />
                              <span className="text-sm text-gray-700">{selectedApprovalFile.name}</span>
                            </div>
                            <button
                              type="button"
                              onClick={() => setSelectedApprovalFile(null)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <label className="cursor-pointer flex flex-col items-center gap-2 py-2">
                            <Upload className="w-6 h-6 text-gray-400" />
                            <span className="text-sm text-gray-600">Clique para selecionar arquivo</span>
                            <span className="text-xs text-gray-400">(Imagens, PDFs, Vídeos - máx 50MB)</span>
                            <input
                              type="file"
                              onChange={(e) => setSelectedApprovalFile(e.target.files?.[0] || null)}
                              accept="image/*,video/*,.pdf"
                              className="hidden"
                            />
                          </label>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-gray-200" />
                      <span className="text-xs text-gray-400">ou</span>
                      <div className="flex-1 h-px bg-gray-200" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">URL do arquivo</label>
                      <input
                        type="text"
                        value={approvalForm.arquivo_url}
                        onChange={(e) => setApprovalForm((f) => ({ ...f, arquivo_url: e.target.value }))}
                        placeholder="https://..."
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                        disabled={!!selectedApprovalFile}
                      />
                    </div>
                  </div>
                )}
                {approvalForm.tipo === 'link' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Link externo</label>
                    <input type="text" value={approvalForm.link_externo} onChange={(e) => setApprovalForm((f) => ({ ...f, link_externo: e.target.value }))} placeholder="https://drive.google.com/..." className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                  </div>
                )}
                <button onClick={createApproval} disabled={submitting || !approvalForm.titulo} className="w-full py-3 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors">
                  {submitting ? 'Criando...' : 'Criar'}
                </button>
              </>
            )}

            {modalType === 'payment' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Descrição</label>
                  <input type="text" value={paymentForm.descricao} onChange={(e) => setPaymentForm((f) => ({ ...f, descricao: e.target.value }))} placeholder="Entrada" className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Valor (R$)</label>
                    <input type="number" value={paymentForm.valor} onChange={(e) => setPaymentForm((f) => ({ ...f, valor: e.target.value }))} placeholder="2500" className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Vencimento</label>
                    <input type="date" value={paymentForm.data_vencimento} onChange={(e) => setPaymentForm((f) => ({ ...f, data_vencimento: e.target.value }))} className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Parcela</label>
                    <input type="number" value={paymentForm.parcela} onChange={(e) => setPaymentForm((f) => ({ ...f, parcela: e.target.value }))} className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Total de parcelas</label>
                    <input type="number" value={paymentForm.total_parcelas} onChange={(e) => setPaymentForm((f) => ({ ...f, total_parcelas: e.target.value }))} className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500" />
                  </div>
                </div>
                <button onClick={createPayment} disabled={submitting || !paymentForm.descricao || !paymentForm.valor || !paymentForm.data_vencimento} className="w-full py-3 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors">
                  {submitting ? 'Criando...' : 'Criar'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  // ─── Main render ──────────────────────────────────────────────────────────
  return (
    <div className="p-6 lg:p-8">
      {/* Back + Header */}
      <button onClick={() => router.push('/admin-portal/projetos')} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Voltar aos Projetos
      </button>

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">{project.nome}</h1>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[project.status] || 'bg-gray-100 text-gray-700'}`}>
              {STATUS_LABELS[project.status] || project.status}
            </span>
            <span className="text-sm text-gray-500">{project.tipo}</span>
            <span className="text-sm text-gray-500">· {formatCurrency(project.valor_total)}</span>
          </div>
          {project.descricao && <p className="text-gray-500 mt-2">{project.descricao}</p>}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-200 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg whitespace-nowrap transition-colors ${
              activeTab === tab
                ? 'border-b-2 border-purple-600 text-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="mt-2">
        {tabContent[activeTab]?.()}
      </div>

      {/* Modal */}
      {renderModal()}
    </div>
  );
}
