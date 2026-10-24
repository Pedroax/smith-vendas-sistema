'use client';

import { useState, useEffect, useRef } from 'react';
import { Bell, X, Check, CheckCheck, Trash2, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/contexts/ToastContext';
import { API_URL } from '@/lib/api-config';
import { adminFetch } from '@/lib/auth';

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
}

const priorityColors = {
  low: 'text-gray-600 bg-gray-50',
  medium: 'text-blue-600 bg-blue-50',
  high: 'text-orange-600 bg-orange-50',
  urgent: 'text-red-600 bg-red-50',
};

const typeIcons: Record<string, string> = {
  lead_quente: '🔥',
  agendamento: '📅',
  lead_parado: '⏸️',
  proposta_vencendo: '⏰',
  novo_lead: '✨',
  lead_movido: '➡️',
  follow_up: '🔔',
  sistema: 'ℹ️',
  outro: '📌',
};

export default function NotificationBell() {
  const { showToast } = useToast();
  const router = useRouter();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();

    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await adminFetch(`${API_URL}/api/notifications?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (err) {
      console.error('Erro ao buscar notificações:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const res = await adminFetch(`${API_URL}/api/notifications/count/unread`);
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.count);
      }
    } catch (err) {
      console.error('Erro ao buscar contador:', err);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      const res = await adminFetch(`${API_URL}/api/notifications/${notificationId}/read`, {
        method: 'POST',
      });

      if (res.ok) {
        setNotifications(prev =>
          prev.map(n => (n.id === notificationId ? { ...n, lida: true } : n))
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (err) {
      console.error('Erro ao marcar como lida:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const res = await adminFetch(`${API_URL}/api/notifications/mark-all-read`, {
        method: 'POST',
      });

      if (res.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, lida: true })));
        setUnreadCount(0);
        showToast('Todas notificações marcadas como lidas', 'success');
      }
    } catch (err) {
      console.error('Erro ao marcar todas como lidas:', err);
      showToast('Erro ao marcar notificações', 'error');
    }
  };

  const handleDelete = async (notificationId: string) => {
    try {
      const res = await adminFetch(`${API_URL}/api/notifications/${notificationId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        const notification = notifications.find(n => n.id === notificationId);
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
        if (notification && !notification.lida) {
          setUnreadCount(prev => Math.max(0, prev - 1));
        }
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
      setShowDropdown(false);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    if (days < 7) return `${days}d`;
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => {
          setShowDropdown(!showDropdown);
          if (!showDropdown) {
            fetchNotifications();
          }
        }}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-5 h-5 px-1 flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-900">Notificações</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                  title="Marcar todas como lidas"
                >
                  <CheckCheck className="w-3 h-3" />
                  Marcar todas
                </button>
              )}
              <button
                onClick={() => setShowDropdown(false)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 text-purple-600 animate-spin" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="text-center py-12 px-4">
                <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">Nenhuma notificação</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`px-4 py-3 hover:bg-gray-50 transition-colors ${
                      !notification.lida ? 'bg-blue-50/30' : ''
                    }`}
                  >
                    <div className="flex gap-3">
                      {/* Icon/Emoji */}
                      <div className="flex-shrink-0 text-xl">
                        {typeIcons[notification.tipo] || '📌'}
                      </div>

                      {/* Content */}
                      <div
                        className="flex-1 cursor-pointer"
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <h4 className="text-sm font-semibold text-gray-900 leading-tight">
                            {notification.titulo}
                          </h4>
                          <span className="text-xs text-gray-400 whitespace-nowrap">
                            {formatTime(notification.created_at)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 leading-relaxed mb-1">
                          {notification.mensagem}
                        </p>
                        {notification.lead_nome && (
                          <p className="text-xs text-purple-600 font-medium">
                            Lead: {notification.lead_nome}
                          </p>
                        )}
                        {!notification.lida && (
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                              Nova
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex-shrink-0 flex flex-col gap-1">
                        {!notification.lida && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMarkAsRead(notification.id);
                            }}
                            className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                            title="Marcar como lida"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(notification.id);
                          }}
                          className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Remover"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200 text-center">
              <button
                onClick={() => {
                  router.push('/notificacoes');
                  setShowDropdown(false);
                }}
                className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                Ver todas notificações
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
