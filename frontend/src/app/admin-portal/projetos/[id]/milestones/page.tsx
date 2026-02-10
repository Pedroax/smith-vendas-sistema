'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Calendar, Plus, Edit2, Trash2, CheckCircle, Clock,
  AlertCircle, XCircle, ChevronLeft, Bell, BellOff
} from 'lucide-react';
import { API_URL } from '@/lib/api-config';
import { useToast } from '@/contexts/ToastContext';

interface Milestone {
  id: string;
  project_id: number;
  nome: string;
  descricao?: string;
  ordem: number;
  data_limite: string;
  data_conclusao?: string;
  status: 'pendente' | 'em_progresso' | 'concluido' | 'atrasado' | 'cancelado';
  notificacao_whatsapp: boolean;
  notificacao_email: boolean;
  dias_ate_limite?: number;
  atrasado: boolean;
  created_at: string;
  updated_at: string;
}

const STATUS_LABELS = {
  pendente: 'Pendente',
  em_progresso: 'Em Progresso',
  concluido: 'Concluído',
  atrasado: 'Atrasado',
  cancelado: 'Cancelado'
};

const STATUS_COLORS = {
  pendente: 'bg-gray-100 text-gray-700',
  em_progresso: 'bg-blue-100 text-blue-700',
  concluido: 'bg-green-100 text-green-700',
  atrasado: 'bg-red-100 text-red-700',
  cancelado: 'bg-gray-100 text-gray-500'
};

const STATUS_ICONS = {
  pendente: Clock,
  em_progresso: Calendar,
  concluido: CheckCircle,
  atrasado: AlertCircle,
  cancelado: XCircle
};

export default function ProjectMilestonesPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const projectId = params?.id as string;

  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingMilestone, setEditingMilestone] = useState<Milestone | null>(null);

  useEffect(() => {
    fetchMilestones();
  }, [projectId]);

  const fetchMilestones = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/milestones/project/${projectId}`);
      if (res.ok) {
        const data = await res.json();
        setMilestones(data);
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar marcos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    const data = {
      project_id: parseInt(projectId),
      nome: formData.get('nome') as string,
      descricao: formData.get('descricao') as string,
      ordem: parseInt(formData.get('ordem') as string),
      data_limite: formData.get('data_limite') as string,
      notificacao_whatsapp: formData.get('notificacao_whatsapp') === 'on',
      notificacao_email: formData.get('notificacao_email') === 'on',
      ...(editingMilestone && {
        status: formData.get('status') as string,
        data_conclusao: formData.get('data_conclusao') as string || null
      })
    };

    try {
      const url = editingMilestone
        ? `${API_URL}/api/milestones/${editingMilestone.id}`
        : `${API_URL}/api/milestones/`;

      const res = await fetch(url, {
        method: editingMilestone ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        showToast(
          editingMilestone ? 'Marco atualizado!' : 'Marco criado!',
          'success'
        );
        setShowModal(false);
        setEditingMilestone(null);
        fetchMilestones();
      } else {
        throw new Error('Erro ao salvar marco');
      }
    } catch (err: any) {
      showToast(err.message || 'Erro ao salvar marco', 'error');
    }
  };

  const handleDelete = async (milestoneId: string) => {
    if (!confirm('Tem certeza que deseja deletar este marco?')) return;

    try {
      const res = await fetch(`${API_URL}/api/milestones/${milestoneId}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        showToast('Marco deletado!', 'success');
        fetchMilestones();
      }
    } catch (err) {
      showToast('Erro ao deletar marco', 'error');
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-gray-500">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Marcos do Projeto
              </h1>
              <p className="text-gray-600 mt-1">
                Gerencie as etapas e prazos do projeto
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setEditingMilestone(null);
              setShowModal(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Novo Marco
          </button>
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          {milestones.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Nenhum marco cadastrado ainda</p>
              <button
                onClick={() => setShowModal(true)}
                className="mt-4 text-blue-600 hover:text-blue-700"
              >
                Criar primeiro marco
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {milestones.map((milestone) => {
                const StatusIcon = STATUS_ICONS[milestone.status];
                return (
                  <div
                    key={milestone.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <StatusIcon className="w-5 h-5 text-gray-400" />
                          <h3 className="font-semibold text-gray-900">
                            {milestone.nome}
                          </h3>
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[milestone.status]}`}
                          >
                            {STATUS_LABELS[milestone.status]}
                          </span>
                          {milestone.notificacao_whatsapp && (
                            <Bell className="w-4 h-4 text-green-600" />
                          )}
                          {!milestone.notificacao_whatsapp && (
                            <BellOff className="w-4 h-4 text-gray-400" />
                          )}
                        </div>

                        {milestone.descricao && (
                          <p className="text-sm text-gray-600 mb-3">
                            {milestone.descricao}
                          </p>
                        )}

                        <div className="flex items-center gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Prazo: </span>
                            <span className="font-medium text-gray-900">
                              {formatDate(milestone.data_limite)}
                            </span>
                          </div>

                          {milestone.dias_ate_limite !== undefined && (
                            <div>
                              {milestone.dias_ate_limite > 0 ? (
                                <span className="text-blue-600">
                                  Faltam {milestone.dias_ate_limite} dias
                                </span>
                              ) : milestone.dias_ate_limite === 0 ? (
                                <span className="text-orange-600 font-medium">
                                  Vence hoje!
                                </span>
                              ) : (
                                <span className="text-red-600 font-medium">
                                  {Math.abs(milestone.dias_ate_limite)} dias de
                                  atraso
                                </span>
                              )}
                            </div>
                          )}

                          {milestone.data_conclusao && (
                            <div>
                              <span className="text-gray-500">
                                Concluído em:{' '}
                              </span>
                              <span className="font-medium text-green-600">
                                {formatDate(milestone.data_conclusao)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => {
                            setEditingMilestone(milestone);
                            setShowModal(true);
                          }}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <Edit2 className="w-4 h-4 text-gray-600" />
                        </button>
                        <button
                          onClick={() => handleDelete(milestone.id)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                {editingMilestone ? 'Editar Marco' : 'Novo Marco'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome da Etapa *
                </label>
                <input
                  type="text"
                  name="nome"
                  required
                  defaultValue={editingMilestone?.nome}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: Briefing e Aprovação de Escopo"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <textarea
                  name="descricao"
                  rows={3}
                  defaultValue={editingMilestone?.descricao}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Detalhes da etapa..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ordem *
                  </label>
                  <input
                    type="number"
                    name="ordem"
                    required
                    min="0"
                    defaultValue={editingMilestone?.ordem ?? milestones.length}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data Limite *
                  </label>
                  <input
                    type="date"
                    name="data_limite"
                    required
                    defaultValue={editingMilestone?.data_limite}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {editingMilestone && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      name="status"
                      defaultValue={editingMilestone.status}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="pendente">Pendente</option>
                      <option value="em_progresso">Em Progresso</option>
                      <option value="concluido">Concluído</option>
                      <option value="cancelado">Cancelado</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Conclusão
                    </label>
                    <input
                      type="date"
                      name="data_conclusao"
                      defaultValue={editingMilestone.data_conclusao}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    name="notificacao_whatsapp"
                    defaultChecked={
                      editingMilestone?.notificacao_whatsapp ?? true
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Notificação por WhatsApp
                  </span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    name="notificacao_email"
                    defaultChecked={editingMilestone?.notificacao_email}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Notificação por Email
                  </span>
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingMilestone(null);
                  }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {editingMilestone ? 'Atualizar' : 'Criar Marco'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
