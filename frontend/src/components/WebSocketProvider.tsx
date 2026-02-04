'use client';

import { useCallback, useRef } from 'react';
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket';
import { useLeadsStore } from '@/store/useLeadsStore';
import { Lead } from '@/types/lead';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const store = useLeadsStore();
  const storeRef = useRef(store);
  storeRef.current = store;

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'lead_created':
        storeRef.current.handleLeadCreated(message.data as Lead);
        showNotification('Novo Lead!', `${message.data.nome} foi adicionado`, 'success');
        break;

      case 'lead_updated':
        storeRef.current.handleLeadUpdated(message.data as Lead);
        showNotification('Lead Atualizado', `${message.data.nome} foi atualizado`, 'info');
        break;

      case 'lead_deleted':
        storeRef.current.handleLeadDeleted(message.data.id);
        showNotification('Lead Removido', 'Um lead foi removido', 'warning');
        break;

      case 'lead_status_changed':
        console.log('[WebSocket] Status changed:', message.data);
        break;

      default:
        console.log('[WebSocket] Unknown message type:', message.type);
    }
  }, []);

  const handleConnect = useCallback(() => {
    console.log('[WebSocket] Connected successfully');
  }, []);

  const handleDisconnect = useCallback(() => {
    console.log('[WebSocket] Disconnected');
  }, []);

  const handleError = useCallback((error: Event) => {
    console.error('[WebSocket] Error:', error);
  }, []);

  const { status, reconnectCount } = useWebSocket({
    url: WS_URL,
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
  });

  return <>{children}</>;
}

// Helper para mostrar notificações
function showNotification(
  title: string,
  message: string,
  type: 'success' | 'info' | 'warning' | 'error'
) {
  // Por enquanto, apenas console.log
  // TODO: Integrar com biblioteca de notificações (toast)
  console.log(`[Notification ${type.toUpperCase()}] ${title}: ${message}`);

  // Se o navegador suportar notificações e o usuário permitir
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, {
      body: message,
      icon: '/icon.png',
      badge: '/badge.png',
    });
  }
}
