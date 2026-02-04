'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Lead, LeadStatus, ConversationMessage } from '@/types/lead';
import { apiClient } from '@/lib/api';
import {
  ArrowLeft, Building2, Phone, Mail, Calendar, MessageCircle,
  TrendingUp, DollarSign, Clock, Tag, Edit2, Trash2, User,
  CheckCircle, XCircle, AlertCircle, Loader2, Send
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const statusColors: Record<LeadStatus, string> = {
  novo: 'bg-blue-100 text-blue-700 border-blue-200',
  contato_inicial: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  qualificando: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  qualificado: 'bg-purple-100 text-purple-700 border-purple-200',
  agendamento_marcado: 'bg-pink-100 text-pink-700 border-pink-200',
  ganho: 'bg-green-100 text-green-700 border-green-200',
  perdido: 'bg-red-100 text-red-700 border-red-200',
};

const statusLabels: Record<LeadStatus, string> = {
  novo: 'Novo',
  contato_inicial: 'Contato Inicial',
  qualificando: 'Qualificando',
  qualificado: 'Qualificado',
  agendamento_marcado: 'Reunião Agendada',
  ganho: 'Ganho',
  perdido: 'Perdido',
};

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [lead, setLead] = useState<Lead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => {
    loadLead();
  }, [params.id]);

  const loadLead = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getLead(params.id as string);
      setLead(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar lead');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = () => {
    if (!newMessage.trim()) return;
    // TODO: Implementar envio de mensagem
    console.log('Enviar mensagem:', newMessage);
    setNewMessage('');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Carregando lead...</p>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Erro ao carregar lead</h2>
          <p className="text-gray-600 mb-4">{error || 'Lead não encontrado'}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
          >
            Voltar ao Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{lead.nome}</h1>
              <p className="text-gray-500">Detalhes do lead</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Edit2 className="w-5 h-5 text-gray-600" />
              </button>
              <button className="p-2.5 border border-gray-300 rounded-lg hover:bg-red-50 hover:border-red-300 transition-colors">
                <Trash2 className="w-5 h-5 text-gray-600 hover:text-red-600" />
              </button>
            </div>
          </div>

          {/* Status Badge */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border font-semibold ${statusColors[lead.status]}`}>
            {statusLabels[lead.status]}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Sidebar - Informações */}
          <div className="space-y-6">
            {/* Informações de Contato */}
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-purple-500" />
                Informações de Contato
              </h3>
              <div className="space-y-4">
                {lead.empresa && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-1">Empresa</div>
                    <div className="flex items-center gap-2 text-gray-900">
                      <Building2 className="w-4 h-4 text-gray-400" />
                      {lead.empresa}
                    </div>
                  </div>
                )}
                <div>
                  <div className="text-xs text-gray-500 font-medium mb-1">Telefone</div>
                  <div className="flex items-center gap-2 text-gray-900">
                    <Phone className="w-4 h-4 text-gray-400" />
                    {lead.telefone}
                  </div>
                </div>
                {lead.email && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-1">Email</div>
                    <div className="flex items-center gap-2 text-gray-900">
                      <Mail className="w-4 h-4 text-gray-400" />
                      {lead.email}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Qualificação */}
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-500" />
                Qualificação
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Lead Score</span>
                    <span className="font-bold text-gray-900">{lead.lead_score}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        lead.lead_score >= 70 ? 'bg-green-500' :
                        lead.lead_score >= 40 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${lead.lead_score}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 font-medium mb-1">Temperatura</div>
                  <div className="flex items-center gap-2">
                    {lead.temperatura === 'quente' && <TrendingUp className="w-4 h-4 text-green-500" />}
                    {lead.temperatura === 'morno' && <AlertCircle className="w-4 h-4 text-yellow-500" />}
                    {lead.temperatura === 'frio' && <XCircle className="w-4 h-4 text-red-500" />}
                    <span className="capitalize text-gray-900">{lead.temperatura}</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 font-medium mb-1">Valor Estimado</div>
                  <div className="flex items-center gap-2 text-lg font-bold text-green-600">
                    <DollarSign className="w-5 h-5" />
                    R$ {lead.valor_estimado.toLocaleString('pt-BR')}
                  </div>
                </div>
              </div>
            </div>

            {/* Datas Importantes */}
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-purple-500" />
                Datas Importantes
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-gray-500 font-medium mb-1">Criado em</div>
                  <div className="text-sm text-gray-900">
                    {format(new Date(lead.created_at), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                  </div>
                </div>
                {lead.ultima_interacao && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-1">Última Interação</div>
                    <div className="text-sm text-gray-900">
                      {format(new Date(lead.ultima_interacao), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                    </div>
                  </div>
                )}
                {lead.meeting_scheduled_at && (
                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-1">Reunião Agendada</div>
                    <div className="text-sm text-green-600 font-semibold">
                      {format(new Date(lead.meeting_scheduled_at), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Tags */}
            {lead.tags.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Tag className="w-5 h-5 text-purple-500" />
                  Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                  {lead.tags.map((tag, i) => (
                    <span key={i} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Notas */}
            {lead.notas && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-3">Notas</h3>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{lead.notas}</p>
              </div>
            )}
          </div>

          {/* Main Content - Histórico de Conversas */}
          <div className="col-span-2">
            <div className="bg-white rounded-xl border border-gray-200 h-[calc(100vh-250px)] flex flex-col">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-bold text-gray-900 flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-purple-500" />
                  Histórico de Conversas
                  <span className="ml-auto text-sm font-normal text-gray-500">
                    {lead.conversation_history.length} mensagens
                  </span>
                </h3>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {lead.conversation_history.length === 0 ? (
                  <div className="text-center py-12">
                    <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Nenhuma conversa ainda</p>
                    <p className="text-sm text-gray-400 mt-1">
                      As mensagens do WhatsApp aparecerão aqui
                    </p>
                  </div>
                ) : (
                  lead.conversation_history.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-start' : 'justify-end'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                          message.role === 'user'
                            ? 'bg-gray-100 text-gray-900'
                            : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <div
                          className={`text-xs mt-2 flex items-center gap-1 ${
                            message.role === 'user' ? 'text-gray-500' : 'text-white/70'
                          }`}
                        >
                          <Clock className="w-3 h-3" />
                          {format(new Date(message.timestamp), "HH:mm", { locale: ptBR })}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Input (placeholder) */}
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Digite uma mensagem (em breve via WhatsApp)..."
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    disabled
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled
                    className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  💡 As mensagens são enviadas automaticamente via WhatsApp pelo Smith
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
