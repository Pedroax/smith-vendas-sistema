'use client';

import { useState, useEffect } from 'react';
import { Bell, Loader2, Check, CheckCheck, Trash2, Filter } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/contexts/ToastContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Notification {
  id: string;
  tipo: string;
  prioridade: 'low' | 'medium' | 'high' | 'urgent';
  titulo: string;
  mensagem: string;
  link?: string;
  lida: boolean;
  lead_nome?: string;
  created_at: string;
  read_at?: string;
}

const priorityConfig = {
  low: { label: 'Baixa', color: 'text-gray-600 bg-gray-100' },
  medium: { label: 'Média', color: 'text-blue-600 bg-blue-100' },
  high: { label: 'Alta', color: 'text-orange-600 bg-orange-100' },
  urgent: { label: 'Urgente', color: 'text-red-600 bg-red-100' },
};

const typeLabels: Record<string, string> = {
  lead_quente: '🔥 Lead Quente',
  agendamento: '📅 Agendamento',
  lead_parado: '⏸️ Lead Parado',
  proposta_vencendo: '⏰ Proposta Vencendo',
  novo_lead: '✨ Novo Lead',
  lead_movido: '➡️ Lead Movido',
  follow_up: '🔔 Follow-up',
  sistema: 'ℹ️ Sistema',
  outro: '📌 Outro',
};

export default function NotificacoesPage() {
  const { showToast } = useToast();
  const router = useRouter();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const unreadOnly = filter === 'unread';
      const res = await fetch(`${API_URL}/api/notifications?unread_only=${unreadOnly}&limit=100`);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (err) {
      console.error('Erro ao buscar notificações:', err);
      showToast('Erro ao carregar notificações', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/notifications/${notificationId}/read`, {
        method: 'POST',
      });

      if (res.ok) {
        setNotifications(prev =>
          prev.map(n => (n.id === notificationId ? { ...n, lida: true } : n))
        );
        showToast('Notificação marcada como lida', 'success');
      }
    } catch (err) {
      console.error('Erro ao marcar como lida:', err);
      showToast('Erro ao atualizar notificação', 'error');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const res = await fetch(`${API_URL}/api/notifications/mark-all-read`, {
        method: 'POST',
      });

      if (res.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, lida: true })));
        showToast('Todas notificações marcadas como lidas', 'success');
      }
    } catch (err) {
      console.error('Erro ao marcar todas como lidas:', err);
      showToast('Erro ao atualizar notificações', 'error');
    }
  };

  const handleDelete = async (notificationId: string) => {
    if (!confirm('Deseja realmente deletar esta notificação?')) return;

    try {
      const res = await fetch(`${API_URL}/api/notifications/${notificationId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
        showToast('Notificação removida', 'success');
      }
    } catch (err) {
      console.error('Erro ao deletar notificação:', err);
      showToast('Erro ao remover notificação', 'error');
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.lida) {
      await handleMarkAsRead(notification.id);
    }

    if (notification.link) {
      router.push(notification.link);
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const unreadCount = notifications.filter(n => !n.lida).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1 flex items-center gap-3">
                <Bell className="w-8 h-8" />
                Notificações
              </h1>
              <p className="text-gray-500">
                Central de notificações e alertas do sistema
              </p>
            </div>

            <div className="flex items-center gap-3">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <CheckCheck className="w-5 h-5" />
                  <span className="font-medium">Marcar Todas como Lidas</span>
                </button>
              )}
            </div>
          </div>

          {/* Stats & Filters */}
          <div className="flex items-center gap-4">
            {/* Stats */}
            <div className="flex items-center gap-4">
              <div className="px-4 py-2 bg-blue-50 rounded-lg border border-blue-200">
                <span className="text-sm text-blue-600 font-medium">
                  {unreadCount} não lidas
                </span>
              </div>
              <div className="px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-sm text-gray-600 font-medium">
                  {notifications.length} total
                </span>
              </div>
            </div>

            {/* Filters */}
            <div className="flex-1 flex justify-end">
              <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    filter === 'all'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Todas
                </button>
                <button
                  onClick={() => setFilter('unread')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                    filter === 'unread'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Filter className="w-4 h-4" />
                  Não Lidas
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {notifications.length === 0 ? (
            <div className="text-center py-20">
              <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 font-medium mb-2">
                {filter === 'unread' ? 'Nenhuma notificação não lida' : 'Nenhuma notificação'}
              </p>
              <p className="text-sm text-gray-500">
                Você receberá notificações sobre leads, agendamentos e mais
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {notifications.map((notification) => {
                const priorityInfo = priorityConfig[notification.prioridade];

                return (
                  <div
                    key={notification.id}
                    className={`p-6 hover:bg-gray-50 transition-colors ${
                      !notification.lida ? 'bg-blue-50/20 border-l-4 border-l-blue-500' : ''
                    }`}
                  >
                    <div className="flex gap-4">
                      {/* Icon/Type */}
                      <div className="flex-shrink-0 text-3xl">
                        {typeLabels[notification.tipo]?.charAt(0) || '📌'}
                      </div>

                      {/* Content */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div
                            className={`flex-1 ${notification.link ? 'cursor-pointer' : ''}`}
                            onClick={() => handleNotificationClick(notification)}
                          >
                            <div className="flex items-center gap-3 mb-1">
                              <h3 className="text-lg font-bold text-gray-900">
                                {notification.titulo}
                              </h3>
                              {!notification.lida && (
                                <span className="px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded-full">
                                  NOVA
                                </span>
                              )}
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${priorityInfo.color}`}>
                                {priorityInfo.label}
                              </span>
                            </div>
                            <p className="text-gray-700 mb-2">{notification.mensagem}</p>
                            {notification.lead_nome && (
                              <p className="text-sm text-purple-600 font-medium mb-2">
                                Lead: {notification.lead_nome}
                              </p>
                            )}
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span>{typeLabels[notification.tipo] || 'Notificação'}</span>
                              <span>•</span>
                              <span>{formatDateTime(notification.created_at)}</span>
                              {notification.read_at && (
                                <>
                                  <span>•</span>
                                  <span className="text-green-600 font-medium">
                                    Lida em {formatDateTime(notification.read_at)}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-2">
                            {!notification.lida && (
                              <button
                                onClick={() => handleMarkAsRead(notification.id)}
                                className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                title="Marcar como lida"
                              >
                                <Check className="w-5 h-5" />
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(notification.id)}
                              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Remover"
                            >
                              <Trash2 className="w-5 h-5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
