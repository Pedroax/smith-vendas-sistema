import { useEffect, useRef, useCallback, useState } from 'react';

export type WebSocketMessage = {
  type: 'lead_created' | 'lead_updated' | 'lead_deleted' | 'lead_status_changed';
  data: any;
};

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
}: UseWebSocketOptions) {
  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const [reconnectCount, setReconnectCount] = useState(0);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  // Função para enviar heartbeat
  const sendHeartbeat = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send('ping');
    }
  }, []);

  // Usar ref para reconnectCount para evitar recriar connect
  const reconnectCountRef = useRef(0);

  // Função para conectar ao WebSocket
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return; // Já está conectado
    }

    console.log('[WebSocket] Connecting to:', url);
    setStatus('connecting');

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('[WebSocket] Connected');
        setStatus('connected');
        reconnectCountRef.current = 0;
        setReconnectCount(0);

        // Iniciar heartbeat
        heartbeatIntervalRef.current = setInterval(sendHeartbeat, 30000); // 30s

        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        // Ignorar pong de heartbeat
        if (event.data === 'pong') {
          return;
        }

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('[WebSocket] Message received:', message.type);
          onMessage?.(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setStatus('error');
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setStatus('disconnected');

        // Limpar heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        onDisconnect?.();

        // Tentar reconectar se ainda estiver montado
        if (
          shouldReconnect.current &&
          reconnectCountRef.current < maxReconnectAttempts
        ) {
          console.log(`[WebSocket] Reconnecting in ${reconnectInterval}ms... (attempt ${reconnectCountRef.current + 1}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectCountRef.current += 1;
            setReconnectCount(reconnectCountRef.current);
            connect();
          }, reconnectInterval);
        } else if (reconnectCountRef.current >= maxReconnectAttempts) {
          console.error('[WebSocket] Max reconnect attempts reached');
        }
      };
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      setStatus('error');
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectInterval, maxReconnectAttempts, sendHeartbeat]);

  // Função para desconectar manualmente
  const disconnect = useCallback(() => {
    shouldReconnect.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setStatus('disconnected');
  }, []);

  // Conectar ao montar (DESABILITADO - Vercel não suporta WebSocket)
  useEffect(() => {
    // WEBSOCKET DESABILITADO TEMPORARIAMENTE
    console.log('[WebSocket] Disabled - Using polling instead');
    setStatus('disconnected');

    // connect();

    // Cleanup ao desmontar
    return () => {
      shouldReconnect.current = false;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }

      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    status,
    reconnectCount,
    disconnect,
    reconnect: connect,
  };
}
