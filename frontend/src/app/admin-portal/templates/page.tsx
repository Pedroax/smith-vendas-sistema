'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Edit2, Trash2, Copy, Loader2, FileText, CheckCircle2, Package } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { adminFetch } from '@/lib/auth';

import { API_URL } from '@/lib/api-config';

interface Etapa {
  nome: string;
  descricao: string;
  cor: string;
}

interface Entrega {
  nome: string;
  descricao?: string;
  obrigatorio: boolean;
}

interface Template {
  id: string;
  nome: string;
  descricao: string;
  etapas: Etapa[];
  entregas: Entrega[];
}

export default function TemplatesPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
    etapas: [{ nome: '', descricao: '', cor: '#8b5cf6' }] as Etapa[],
    entregas: [{ nome: '', descricao: '', obrigatorio: true }] as Entrega[],
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await adminFetch(`${API_URL}/api/portal/templates`);
      if (res.ok) {
        const data = await res.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar templates', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddEtapa = () => {
    setFormData((prev) => ({
      ...prev,
      etapas: [...prev.etapas, { nome: '', descricao: '', cor: '#8b5cf6' }],
    }));
  };

  const handleRemoveEtapa = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      etapas: prev.etapas.filter((_, i) => i !== index),
    }));
  };

  const handleEtapaChange = (index: number, field: 'nome' | 'descricao', value: string) => {
    setFormData((prev) => ({
      ...prev,
      etapas: prev.etapas.map((e, i) => (i === index ? { ...e, [field]: value } : e)),
    }));
  };

  const handleAddEntrega = () => {
    setFormData((prev) => ({
      ...prev,
      entregas: [...prev.entregas, { nome: '', descricao: '', obrigatorio: true }],
    }));
  };

  const handleRemoveEntrega = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      entregas: prev.entregas.filter((_, i) => i !== index),
    }));
  };

  const handleEntregaChange = (
    index: number,
    field: 'nome' | 'descricao' | 'obrigatorio',
    value: string | boolean
  ) => {
    setFormData((prev) => ({
      ...prev,
      entregas: prev.entregas.map((e, i) =>
        i === index ? { ...e, [field]: value } : e
      ),
    }));
  };

  const handleOpenModal = (template?: Template) => {
    if (template) {
      setEditingTemplate(template);
      setFormData({
        nome: template.nome,
        descricao: template.descricao,
        etapas: template.etapas,
        entregas: template.entregas,
      });
    } else {
      setEditingTemplate(null);
      setFormData({
        nome: '',
        descricao: '',
        etapas: [{ nome: '', descricao: '', cor: '#8b5cf6' }],
        entregas: [{ nome: '', descricao: '', obrigatorio: true }],
      });
    }
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingTemplate(null);
    setFormData({
      nome: '',
      descricao: '',
      etapas: [{ nome: '', descricao: '', cor: '#8b5cf6' }],
      entregas: [{ nome: '', descricao: '', obrigatorio: true }],
    });
  };

  const handleSubmit = async () => {
    // Validação básica
    if (!formData.nome.trim()) {
      showToast('Nome é obrigatório', 'error');
      return;
    }

    const validEtapas = formData.etapas.filter((e) => e.nome.trim());
    if (validEtapas.length === 0) {
      showToast('Adicione pelo menos uma etapa', 'error');
      return;
    }

    setSubmitting(true);

    try {
      const payload = {
        ...formData,
        etapas: validEtapas,
        entregas: formData.entregas.filter((e) => e.nome.trim()),
      };

      const url = editingTemplate
        ? `${API_URL}/api/portal/templates/${editingTemplate.id}`
        : `${API_URL}/api/portal/templates`;

      const method = editingTemplate ? 'PUT' : 'POST';

      const res = await adminFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        showToast(
          editingTemplate ? 'Template atualizado!' : 'Template criado!',
          'success'
        );
        handleCloseModal();
        await fetchTemplates();
      } else {
        const error = await res.json().catch(() => ({ detail: 'Erro ao salvar' }));
        showToast(error.detail || 'Erro ao salvar template', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao salvar template', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDuplicate = (template: Template) => {
    handleOpenModal({
      ...template,
      id: '',
      nome: `${template.nome} (Cópia)`,
    } as Template);
  };

  const handleDelete = async (templateId: string) => {
    if (!confirm('Tem certeza que deseja excluir este template?')) return;

    try {
      const res = await adminFetch(`${API_URL}/api/portal/templates/${templateId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        showToast('Template excluído!', 'success');
        await fetchTemplates();
      } else {
        showToast('Erro ao excluir template', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao excluir template', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Templates de Projetos</h1>
          <p className="text-gray-600 mt-1">Gerencie templates para criação de novos projetos</p>
        </div>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          Novo Template
        </button>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div
            key={template.id}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                  <Package className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">{template.nome}</h3>
                  <p className="text-sm text-gray-500">{template.descricao}</p>
                </div>
              </div>
            </div>

            <div className="space-y-3 mb-4">
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Etapas ({template.etapas.length})</p>
                <div className="flex flex-wrap gap-1">
                  {template.etapas.slice(0, 3).map((etapa, i) => (
                    <span
                      key={i}
                      className="text-xs px-2 py-1 rounded-lg"
                      style={{ backgroundColor: etapa.cor + '20', color: etapa.cor }}
                    >
                      {etapa.nome}
                    </span>
                  ))}
                  {template.etapas.length > 3 && (
                    <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-lg">
                      +{template.etapas.length - 3}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Entregas ({template.entregas.length})</p>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <FileText className="w-3 h-3" />
                  {template.entregas.filter((e) => e.obrigatorio).length} obrigatórias
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-4 border-t border-gray-100">
              <button
                onClick={() => handleOpenModal(template)}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                <Edit2 className="w-4 h-4" />
                Editar
              </button>
              <button
                onClick={() => handleDuplicate(template)}
                className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                <Copy className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDelete(template.id)}
                className="flex items-center justify-center gap-2 px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors text-sm"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="text-center py-16">
          <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Nenhum template ainda</h3>
          <p className="text-gray-600 mb-6">Crie seu primeiro template para agilizar a criação de projetos</p>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors font-medium"
          >
            <Plus className="w-5 h-5" />
            Criar Template
          </button>
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="absolute inset-0 bg-black/40" onClick={handleCloseModal} />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl my-8">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900">
                {editingTemplate ? 'Editar Template' : 'Novo Template'}
              </h2>
            </div>

            <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nome do Template *
                </label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData((prev) => ({ ...prev, nome: e.target.value }))}
                  placeholder="Site Institucional"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                />
              </div>

              {/* Descrição */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Descrição
                </label>
                <textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData((prev) => ({ ...prev, descricao: e.target.value }))}
                  placeholder="Desenvolvimento de site institucional completo"
                  rows={2}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                />
              </div>

              {/* Etapas */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">Etapas *</label>
                  <button
                    type="button"
                    onClick={handleAddEtapa}
                    className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                  >
                    + Adicionar Etapa
                  </button>
                </div>
                <div className="space-y-2">
                  {formData.etapas.map((etapa, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={etapa.nome}
                        onChange={(e) => handleEtapaChange(index, 'nome', e.target.value)}
                        placeholder={`Nome da etapa ${index + 1}`}
                        className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                      />
                      <input
                        type="text"
                        value={etapa.descricao}
                        onChange={(e) => handleEtapaChange(index, 'descricao', e.target.value)}
                        placeholder="Descrição"
                        className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                      />
                      {formData.etapas.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveEtapa(index)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Entregas */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">Entregas</label>
                  <button
                    type="button"
                    onClick={handleAddEntrega}
                    className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                  >
                    + Adicionar Entrega
                  </button>
                </div>
                <div className="space-y-3">
                  {formData.entregas.map((entrega, index) => (
                    <div key={index} className="p-3 border border-gray-200 rounded-lg space-y-2">
                      <div className="flex items-start gap-2">
                        <input
                          type="text"
                          value={entrega.nome}
                          onChange={(e) => handleEntregaChange(index, 'nome', e.target.value)}
                          placeholder="Nome da entrega"
                          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-sm"
                        />
                        <button
                          type="button"
                          onClick={() => handleRemoveEntrega(index)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <input
                        type="text"
                        value={entrega.descricao}
                        onChange={(e) => handleEntregaChange(index, 'descricao', e.target.value)}
                        placeholder="Descrição (opcional)"
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-sm"
                      />
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={entrega.obrigatorio}
                          onChange={(e) =>
                            handleEntregaChange(index, 'obrigatorio', e.target.checked)
                          }
                          className="w-4 h-4 accent-purple-600"
                        />
                        <span className="text-sm text-gray-700">Obrigatório</span>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-100 flex items-center gap-3">
              <button
                onClick={handleCloseModal}
                disabled={submitting}
                className="flex-1 px-4 py-3 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || !formData.nome.trim()}
                className="flex-1 px-4 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    {editingTemplate ? 'Atualizar' : 'Criar Template'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
