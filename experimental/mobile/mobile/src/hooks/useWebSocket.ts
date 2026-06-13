import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuth } from './useAuth';

type MessageHandler = (data: any) => void;

interface UseWebSocketOptions {
  url?: string;
  onMessage?: MessageHandler;
  onLog?: (line: string) => void;
  onMetric?: (metrics: any) => void;
  onStatus?: (status: string) => void;
  autoReconnect?: boolean;
}

export function useWebSocket({
  url: customUrl,
  onMessage,
  autoReconnect = true,
}: UseWebSocketOptions = {}) {
  const { state } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    const token = state.token;
    if (!token) return;

    const baseUrl = customUrl || process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:3001';
    const url = `${baseUrl}?token=${token}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => setIsConnected(true);

      ws.onclose = () => {
        setIsConnected(false);
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch {
          // ignore parse errors
        }
      };
    } catch {
      if (autoReconnect) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      }
    }
  }, [state.token, customUrl, onMessage, autoReconnect]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, send };
}
