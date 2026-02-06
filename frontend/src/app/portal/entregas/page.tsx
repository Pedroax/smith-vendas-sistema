'use client';

import { useEffect, useState } from 'react';
import {
  FileCheck, Loader2, AlertCircle, CheckCircle2, Clock,
  Upload, FolderKanban, ChevronDown, ChevronUp
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Project {
  id: string;
  nome: string;
}

interface DeliveryItem {
  id: string;
  project_id: string;
  nome: string;
  descricao?: string;
  obrigatorio: boolean;
  status: 'pendente' | 'enviado' | 'aprovado' | 'rejeitado';
  arquivo_url?: string;
  arquivo_nome?: string;
  comentario_cliente?: string;
  enviado_em?: string;
  aprovado_em?: string;
  created_at: string;
}

export default function EntregasPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [deliveries, setDeliveries] = useState<Record<string, DeliveryItem[]>>({});
  const [loading, setLoading] = useState(true);
  const [expandedProject, setExpandedProject] = useState<string | null>(null);
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

        // Buscar entregas de cada projeto em paralelo
        const results = await Promise.all(
          projectsData.map(async (p) => {
            const res = await fetch(`${API_URL}/api/portal/projects/${p.id}/deliveries`, { headers });
            return { id: p.id, data: res.ok ? await res.json().catch(() => []) : [] };
          })
        );

        const map: Record<string, DeliveryItem[]> = {};
        results.forEach((r) => { map[r.id] = r.data; });
        setDeliveries(map);

        // Expand primeiro projeto que tem entregas pendentes
        const first = results.find((r) => r.data.some((d: DeliveryItem) => d.status === 'pendente'));
        if (first) setExpandedProject(first.id);
        else if (projectsData.length > 0) setExpandedProject(projectsData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markAsDelivered = async (itemId: string) => {
    setUpdating(itemId);
    try {
      const token = localStorage.getItem('portal_access_token');
      const res = await fetch(`${API_URL}/api/portal/deliveries/${itemId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: 'enviado' }),
      });
      if (res.ok) {
        // Atualiza estado local
        setDeliveries((prev) => {
          const updated = { ...prev };
          Object.keys(updated).forEach((pid) => {
            updated[pid] = updated[pid].map((d) =>
              d.id === itemId ? { ...d, status: 'enviado', enviado_em: new Date().toISOString() } : d
            );
          });
          return updated;
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUpdating(null);
    }
  };

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { label: string; bg: string; text: string; icon: any }> = {
      pendente: { label: 'Pendente', bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock },
      enviado: { label: 'Enviado', bg: 'bg-blue-100', text: 'text-blue-700', icon: Upload },
      aprovado: { label: 'Aprovado', bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle2 },
      rejeitado: { label: 'Rejeitado', bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle },
    };
    return configs[status] || configs.pendente;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  const totalPendentes = Object.values(deliveries).flat().filter((d) => d.status === 'pendente').length;
  const totalEnviados = Object.values(deliveries).flat().filter((d) => d.status === 'enviado').length;
  const totalAprovados = Object.values(deliveries).flat().filter((d) => d.status === 'aprovado').length;

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Entregas</h1>
        <p className="text-gray-500 mt-1">Materiais que precisam ser enviados para a equipe</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-yellow-100 rounded-xl flex items-center justify-center">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalPendentes}</p>
          <p className="text-sm text-gray-500">Pendentes</p>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-blue-100 rounded-xl flex items-center justify-center">
              <Upload className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalEnviados}</p>
          <p className="text-sm text-gray-500">Enviados</p>
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
      </div>

      {/* Projects with Deliveries */}
      {projects.length === 0 ? (
        <div className="text-center py-16">
          <FileCheck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma entrega</h3>
          <p className="text-gray-500">Não há materiais para entregar no momento</p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => {
            const items = deliveries[project.id] || [];
            if (items.length === 0) return null;
            const isExpanded = expandedProject === project.id;
            const pendentes = items.filter((d) => d.status === 'pendente').length;

            return (
              <div key={project.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {/* Project Header */}
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
                    {pendentes > 0 && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
                        {pendentes} pendente{pendentes !== 1 ? 's' : ''}
                      </span>
                    )}
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                  </div>
                </button>

                {/* Delivery Items */}
                {isExpanded && (
                  <div className="border-t border-gray-100 divide-y divide-gray-100">
                    {items.map((item) => {
                      const config = getStatusConfig(item.status);
                      const StatusIcon = config.icon;
                      return (
                        <div key={item.id} className="p-5">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <h4 className="font-medium text-gray-900">{item.nome}</h4>
                                {item.obrigatorio && (
                                  <span className="text-xs text-red-500 font-medium">Obrigatório</span>
                                )}
                              </div>
                              {item.descricao && (
                                <p className="text-sm text-gray-500 mt-0.5">{item.descricao}</p>
                              )}
                              {item.comentario_cliente && (
                                <p className="text-sm text-blue-600 mt-1 italic">"{item.comentario_cliente}"</p>
                              )}
                              {item.enviado_em && (
                                <p className="text-xs text-gray-400 mt-1">
                                  Enviado em {new Date(item.enviado_em).toLocaleDateString('pt-BR')}
                                </p>
                              )}
                            </div>

                            <div className="flex items-center gap-3 flex-shrink-0">
                              <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
                                <StatusIcon className="w-3.5 h-3.5" />
                                {config.label}
                              </span>

                              {item.status === 'pendente' && (
                                <button
                                  onClick={() => markAsDelivered(item.id)}
                                  disabled={updating === item.id}
                                  className="px-4 py-1.5 bg-purple-600 text-white text-sm font-medium rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
                                >
                                  {updating === item.id ? 'Enviando...' : 'Marcar como Enviado'}
                                </button>
                              )}
                            </div>
                          </div>
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
