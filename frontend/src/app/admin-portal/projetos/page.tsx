'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  FolderKanban, Search, Plus, Loader2, X, CheckCircle2,
  Calendar, Users, ArrowRight
} from 'lucide-react';

import { adminFetch } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Client {
  id: string;
  nome: string;
  email: string;
  empresa?: string;
}

interface Project {
  id: string;
  nome: string;
  descricao?: string;
  tipo: string;
  status: string;
  progresso: number;
  client_id: string;
  valor_total: number;
  data_inicio?: string;
  data_previsao?: string;
  created_at: string;
}

interface Template {
  id: string;
  nome: string;
  etapas: number;
  entregas: number;
}

export default function AdminProjectsPage() {
  const searchParams = useSearchParams();
  const clientFilter = searchParams.get('client');

  const [projects, setProjects] = useState<Project[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [form, setForm] = useState({
    nome: '', descricao: '', tipo: 'site_institucional',
    valor_total: '', client_id: clientFilter || '',
    data_inicio: '', data_previsao: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, clientsRes, templatesRes] = await Promise.all([
        adminFetch(`${API_URL}/api/portal/admin/projects`),
        adminFetch(`${API_URL}/api/portal/admin/clients`),
        adminFetch(`${API_URL}/api/portal/templates`),
      ]);
      if (projectsRes.ok) setProjects(await projectsRes.json());
      if (clientsRes.ok) setClients(await clientsRes.json());
      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setTemplates(data.templates || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    setCreating(true);
    try {
      const url = selectedTemplate
        ? `${API_URL}/api/portal/admin/projects?template=${selectedTemplate}`
        : `${API_URL}/api/portal/admin/projects`;

      const res = await adminFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: form.nome,
          descricao: form.descricao || null,
          tipo: form.tipo,
          valor_total: parseFloat(form.valor_total) || 0,
          client_id: form.client_id,
          data_inicio: form.data_inicio || null,
          data_previsao: form.data_previsao || null,
        }),
      });
      if (res.ok) {
        const newProject: Project = await res.json();
        setProjects((prev) => [newProject, ...prev]);
        setCreated(true);
        setTimeout(() => {
          setCreated(false);
          setModalOpen(false);
          setForm({ nome: '', descricao: '', tipo: 'site_institucional', valor_total: '', client_id: clientFilter || '', data_inicio: '', data_previsao: '' });
          setSelectedTemplate('');
        }, 1500);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
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
      briefing: 'Briefing', aguardando_materiais: 'Aguardando Materiais',
      em_desenvolvimento: 'Em Desenvolvimento', revisao: 'Revisão',
      aprovacao: 'Aguardando Aprovação', concluido: 'Concluído',
      pausado: 'Pausado', cancelado: 'Cancelado',
    };
    return labels[status] || status;
  };

  const getClientName = (clientId: string) =>
    clients.find((c) => c.id === clientId)?.nome || 'Cliente desconhecido';

  const filtered = projects.filter((p) => {
    const matchSearch = p.nome.toLowerCase().includes(search.toLowerCase()) ||
      p.tipo.toLowerCase().includes(search.toLowerCase()) ||
      getClientName(p.client_id).toLowerCase().includes(search.toLowerCase());
    const matchStatus = !statusFilter || p.status === statusFilter;
    const matchClient = !clientFilter || p.client_id === clientFilter;
    return matchSearch && matchStatus && matchClient;
  });

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
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Projetos</h1>
          <p className="text-gray-500 mt-1">
            {clientFilter
              ? `Projetos de ${getClientName(clientFilter)}`
              : `${projects.length} projeto${projects.length !== 1 ? 's' : ''} no total`}
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> Novo Projeto
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar projetos ou clientes..."
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
          <option value="pausado">Pausado</option>
          <option value="cancelado">Cancelado</option>
        </select>
        {clientFilter && (
          <Link href="/admin-portal/projetos" className="px-4 py-3 bg-gray-100 text-gray-600 rounded-xl hover:bg-gray-200 transition-colors text-sm font-medium">
            Limpar filtro
          </Link>
        )}
      </div>

      {/* Projects Grid */}
      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <FolderKanban className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum projeto encontrado</h3>
          <p className="text-gray-500">Tente ajustar os filtros ou crie um novo projeto</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((project) => (
            <Link
              key={project.id}
              href={`/admin-portal/projetos/${project.id}`}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all p-5 group"
            >
              <div className="flex items-start justify-between mb-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                  {getStatusLabel(project.status)}
                </span>
                <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-purple-500 transition-colors" />
              </div>

              <h3 className="font-semibold text-gray-900 group-hover:text-purple-600 transition-colors truncate">
                {project.nome}
              </h3>
              <p className="text-sm text-gray-500 mt-0.5">{project.tipo}</p>

              {/* Progress bar */}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Progresso</span>
                  <span>{project.progresso}%</span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full"
                    style={{ width: `${project.progresso}%` }}
                  />
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Users className="w-3.5 h-3.5" />
                  <span>{getClientName(project.client_id)}</span>
                </div>
                {project.data_previsao && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Previsão: {new Date(project.data_previsao).toLocaleDateString('pt-BR')}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-900">
                    {project.valor_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setModalOpen(false)} />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-bold text-gray-900 text-lg">Novo Projeto</h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {created ? (
              <div className="p-10 text-center">
                <CheckCircle2 className="w-14 h-14 text-green-500 mx-auto mb-3" />
                <p className="font-semibold text-gray-900">Projeto criado com sucesso!</p>
              </div>
            ) : (
              <div className="p-6 space-y-4">
                {/* Template selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Template (opcional)</label>
                  <div className="grid grid-cols-2 gap-2">
                    {templates.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => {
                          setSelectedTemplate(selectedTemplate === t.id ? '' : t.id);
                          setForm((f) => ({ ...f, tipo: t.id }));
                        }}
                        className={`text-left p-3 border rounded-xl transition-colors ${
                          selectedTemplate === t.id
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <p className="text-sm font-medium text-gray-900">{t.nome}</p>
                        <p className="text-xs text-gray-500">{t.etapas} etapas · {t.entregas} entregas</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Nome do Projeto</label>
                  <input
                    type="text"
                    value={form.nome}
                    onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                    placeholder="Website corporativo"
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Descrição</label>
                  <textarea
                    value={form.descricao}
                    onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
                    placeholder="Descreva o projeto..."
                    rows={2}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Cliente</label>
                  <select
                    value={form.client_id}
                    onChange={(e) => setForm((f) => ({ ...f, client_id: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 bg-white"
                  >
                    <option value="">Selecione um cliente</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>{c.nome} — {c.empresa || c.email}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Valor Total (R$)</label>
                    <input
                      type="number"
                      value={form.valor_total}
                      onChange={(e) => setForm((f) => ({ ...f, valor_total: e.target.value }))}
                      placeholder="5000"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Data de Previsão</label>
                    <input
                      type="date"
                      value={form.data_previsao}
                      onChange={(e) => setForm((f) => ({ ...f, data_previsao: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500"
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={createProject}
                    disabled={creating || !form.nome || !form.client_id}
                    className="flex-1 py-3 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
                  >
                    {creating ? 'Criando...' : 'Criar Projeto'}
                  </button>
                  <button
                    onClick={() => setModalOpen(false)}
                    className="px-5 py-3 bg-gray-100 text-gray-600 font-medium rounded-xl hover:bg-gray-200 transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
