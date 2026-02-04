'use client';

import { useEffect, useState } from 'react';
import {
  MessageSquare, Phone, Video, Mail, FileText, Calendar as CalendarIcon,
  Send, Loader2, Search, Clock, User, Plus, CheckCircle2
} from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { apiClient } from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Lead {
  id: string;
  nome: string;
  telefone: string;
  email?: string;
  empresa?: string;
  status: string;
}

interface Interaction {
  id: string;
  lead_id: string;
  tipo: string;
  assunto?: string;
  conteudo: string;
  user_nome: string;
  created_at: string;
  metadata?: any;
}

const interactionTypes = [
  { value: 'nota', label: 'Nota', icon: MessageSquare, color: 'text-blue-600 bg-blue-50' },
  { value: 'ligacao', label: 'Ligação', icon: Phone, color: 'text-green-600 bg-green-50' },
  { value: 'reuniao', label: 'Reunião', icon: Video, color: 'text-purple-600 bg-purple-50' },
  { value: 'email', label: 'E-mail', icon: Mail, color: 'text-orange-600 bg-orange-50' },
  { value: 'proposta', label: 'Proposta', icon: FileText, color: 'text-pink-600 bg-pink-50' },
  { value: 'follow_up', label: 'Follow-up', icon: CalendarIcon, color: 'text-yellow-600 bg-yellow-50' },
  { value: 'outro', label: 'Outro', icon: CheckCircle2, color: 'text-gray-600 bg-gray-50' },
];

export default function ConversasPage() {
  const { showToast } = useToast();

  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingInteractions, setLoadingInteractions] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    tipo: 'nota',
    assunto: '',
    conteudo: '',
    user_nome: 'Pedro Machado'
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchLeads();
  }, []);

  useEffect(() => {
    if (selectedLead) {
      fetchInteractions(selectedLead.id);
    }
  }, [selectedLead]);

  const fetchLeads = async () => {
    try {
      const data = await apiClient.getLeads();
      setLeads(data);
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar leads', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchInteractions = async (leadId: string) => {
    setLoadingInteractions(true);
    try {
      const res = await fetch(`${API_URL}/api/interactions/lead/${leadId}`);
      if (res.ok) {
        const data = await res.json();
        setInteractions(data);
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao carregar interações', 'error');
    } finally {
      setLoadingInteractions(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLead || !formData.conteudo.trim()) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_id: selectedLead.id,
          ...formData
        }),
      });

      if (res.ok) {
        const newInteraction = await res.json();
        setInteractions(prev => [newInteraction, ...prev]);
        setFormData({ tipo: 'nota', assunto: '', conteudo: '', user_nome: 'Pedro Machado' });
        setShowForm(false);
        showToast('Interação adicionada!', 'success');
      } else {
        showToast('Erro ao adicionar interação', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro ao adicionar interação', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const getInteractionIcon = (tipo: string) => {
    const config = interactionTypes.find(t => t.value === tipo);
    return config || interactionTypes[0];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 60) return `${minutes}m atrás`;
    if (hours < 24) return `${hours}h atrás`;
    if (days < 7) return `${days}d atrás`;

    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  };

  const filteredLeads = leads.filter(lead =>
    lead.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lead.telefone.includes(searchTerm) ||
    lead.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Lista de Leads */}
      <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900 mb-4">Conversas</h1>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar lead..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-sm"
            />
          </div>
        </div>

        {/* Leads List */}
        <div className="flex-1 overflow-y-auto">
          {filteredLeads.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <MessageSquare className="w-12 h-12 mb-2" />
              <p>Nenhum lead encontrado</p>
            </div>
          ) : (
            filteredLeads.map((lead) => (
              <button
                key={lead.id}
                onClick={() => setSelectedLead(lead)}
                className={`w-full p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors text-left ${
                  selectedLead?.id === lead.id ? 'bg-purple-50 border-l-4 border-l-purple-600' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">{lead.nome}</h3>
                </div>
                <p className="text-sm text-gray-600 truncate">{lead.telefone}</p>
                {lead.empresa && (
                  <p className="text-xs text-gray-500 mt-1">{lead.empresa}</p>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Content - Timeline de Interações */}
      <div className="flex-1 flex flex-col">
        {!selectedLead ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Selecione um lead</p>
              <p className="text-sm mt-1">para ver o histórico de interações</p>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="bg-white border-b border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedLead.nome}</h2>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <Phone className="w-4 h-4" />
                      {selectedLead.telefone}
                    </span>
                    {selectedLead.email && (
                      <span className="flex items-center gap-1">
                        <Mail className="w-4 h-4" />
                        {selectedLead.email}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setShowForm(!showForm)}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Nova Interação
                </button>
              </div>
            </div>

            {/* Form */}
            {showForm && (
              <div className="bg-white border-b border-gray-200 p-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tipo
                      </label>
                      <select
                        value={formData.tipo}
                        onChange={(e) => setFormData(prev => ({ ...prev, tipo: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                      >
                        {interactionTypes.map(type => (
                          <option key={type.value} value={type.value}>{type.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Assunto (opcional)
                      </label>
                      <input
                        type="text"
                        value={formData.assunto}
                        onChange={(e) => setFormData(prev => ({ ...prev, assunto: e.target.value }))}
                        placeholder="Assunto da interação"
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Conteúdo *
                    </label>
                    <textarea
                      value={formData.conteudo}
                      onChange={(e) => setFormData(prev => ({ ...prev, conteudo: e.target.value }))}
                      placeholder="Descreva a interação..."
                      rows={3}
                      required
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={submitting || !formData.conteudo.trim()}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                    >
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      Adicionar
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowForm(false)}
                      className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Timeline */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingInteractions ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
                </div>
              ) : interactions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                  <MessageSquare className="w-12 h-12 mb-2 text-gray-300" />
                  <p>Nenhuma interação ainda</p>
                  <p className="text-sm mt-1">Adicione a primeira interação com este lead</p>
                </div>
              ) : (
                <div className="space-y-4 max-w-3xl">
                  {interactions.map((interaction) => {
                    const config = getInteractionIcon(interaction.tipo);
                    const Icon = config.icon;

                    return (
                      <div key={interaction.id} className="flex gap-4">
                        <div className={`flex-shrink-0 w-10 h-10 rounded-full ${config.color} flex items-center justify-center`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 bg-white rounded-xl border border-gray-200 p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <span className="font-semibold text-gray-900">{config.label}</span>
                              {interaction.assunto && (
                                <span className="text-gray-600"> • {interaction.assunto}</span>
                              )}
                            </div>
                            <span className="text-sm text-gray-500 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatDate(interaction.created_at)}
                            </span>
                          </div>
                          <p className="text-gray-700 whitespace-pre-wrap">{interaction.conteudo}</p>
                          <div className="flex items-center gap-2 mt-3 text-sm text-gray-500">
                            <User className="w-3 h-3" />
                            {interaction.user_nome}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
