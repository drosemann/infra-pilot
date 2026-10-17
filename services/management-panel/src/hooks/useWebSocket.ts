/**
 * @file useWebSocket — authenticated WebSocket client hook.
 *
 * Fetches a short-lived ticket from `POST /api/ws-token`, opens the socket,
 * completes the handshake, and keeps the connection alive with an application
 * ping. Reconnects with capped exponential backoff on transient failures, but
 * stops on terminal auth/policy close codes (`4001`-`4004`, `4008`, `4009`,
 * `4014`) because replaying a used or revoked ticket cannot succeed.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '../lib/api.ts';

export type WebSocketStatus = 'idle' | 'connecting' | 'authenticating' | 'open' | 'closed' | 'error';

export interface WsServerMessage {
  type: string;
  [key: string]: unknown;
}

export interface UseWebSocketOptions {
  /** App to scope the ticket to and pass as `?appId=` (optional). */
  appId?: string;
  /** Collaborative room id sent as `?sessionId=` (optional). */
  sessionId?: string;
  /** Friendly name sent as `?displayName=` (optional). */
  displayName?: string;
  /** Feature mode, sent as `?mode=` (optional, informational). */
  mode?: 'logs' | 'metrics' | 'terminal' | 'viewer';
  /** Set false to keep the socket closed (e.g. until a container exists). */
  enabled?: boolean;
  /** Subscribe to logs for `appId` as soon as the session is ready. */
  autoSubscribeLogs?: boolean;
  /** Subscribe to metrics for `appId` as soon as the session is ready. */
  autoSubscribeMetrics?: boolean;
  /** Join the collaborative room for `sessionId || appId` as soon as ready. */
  autoJoinRoom?: boolean;
  /** Maximum reconnect attempts before giving up (default 5). */
  maxRetries?: number;
  /** Called for every server message (parsed JSON). */
  onMessage?: (message: WsServerMessage) => void;
  /** Called when the session becomes ready. */
  onReady?: (info: { sessionId: string; userId: string; appScope: string | null }) => void;
  /** Called when the socket closes; receives the close code and reason. */
  onClose?: (info: { code: number; reason: string; willRetry: boolean }) => void;
}

export interface UseWebSocketResult {
  status: WebSocketStatus;
  error: string | null;
  sessionId: string | null;
  /** Send a message; returns false when the socket is not open. */
  send: (message: Record<string, unknown>) => boolean;
  /** Force a reconnect now (fetches a fresh ticket). */
  reconnect: () => void;
}

/** Close codes that must not be retried (replaying the ticket cannot help). */
const TERMINAL_CLOSE_CODES = new Set([4001, 4002, 4003, 4004, 4008, 4009, 4014]);
const PING_INTERVAL_MS = 25000;

function describeClose(code: number, reason: string): string {
  switch (code) {
    case 4001:
      return 'Authentication failed';
    case 4002:
      return 'Authentication timed out';
    case 4003:
      return 'Session ticket expired or was revoked';
    case 4004:
      return 'Not authorized for this app';
    case 4008:
      return 'Rate limit exceeded';
    case 4009:
      return 'Connection closed after protocol errors';
    case 4013:
      return 'Closed after inactivity';
    case 4014:
      return 'Too many active sessions';
    default:
      return reason || `Connection closed (${code})`;
  }
}

function buildSocketUrl(params: Record<string, string | undefined>): string {
  const env = (import.meta as { env?: Record<string, string | undefined> }).env ?? {};
  const base = env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:3001`;
  const url = new URL(base);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') url.searchParams.set(key, value);
  }
  return url.toString();
}

/**
 * Authenticated WebSocket hook. See the file header for behavior details.
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketResult {
  const {
    appId,
    sessionId: roomSessionId,
    displayName,
    mode,
    enabled = true,
    autoSubscribeLogs = false,
    autoSubscribeMetrics = false,
    autoJoinRoom = false,
    maxRetries = 5,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const send = useCallback((message: Record<string, unknown>): boolean => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify(message));
    return true;
  }, []);

  const connect = useCallback(async () => {
    setError(null);
    setStatus('connecting');

    let ticket: string;
    try {
      const token = await apiClient.createWsToken(appId);
      ticket = token.ticket;
    } catch {
      setStatus('error');
      setError('Could not obtain a session ticket');
      return;
    }

    const url = buildSocketUrl({
      ticket,
      appId,
      sessionId: roomSessionId,
      displayName,
      mode,
    });
    const socket = new WebSocket(url);
    socketRef.current = socket;

    let pingTimer: ReturnType<typeof setInterval> | null = null;
    const stopPing = () => {
      if (pingTimer) clearInterval(pingTimer);
      pingTimer = null;
    };
    const startPing = () => {
      stopPing();
      pingTimer = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
      }, PING_INTERVAL_MS);
    };

    socket.onopen = () => {
      setStatus('authenticating');
    };

    socket.onmessage = (event) => {
      let message: WsServerMessage;
      try {
        message = JSON.parse(String(event.data)) as WsServerMessage;
      } catch {
        return;
      }
      if (message.type === 'auth_challenge') {
        socket.send(JSON.stringify({ type: 'auth', ticket }));
        return;
      }
      if (message.type === 'ready') {
        const sid = typeof message.sessionId === 'string' ? message.sessionId : null;
        setSessionId(sid);
        setStatus('open');
        retriesRef.current = 0;
        startPing();
        if (optionsRef.current.autoSubscribeLogs && appId) {
          socket.send(JSON.stringify({ type: 'subscribe', appId }));
        }
        if (optionsRef.current.autoSubscribeMetrics && appId) {
          socket.send(JSON.stringify({ type: 'subscribe:metrics', appId }));
        }
        if (optionsRef.current.autoJoinRoom) {
          socket.send(
            JSON.stringify({
              type: 'join',
              appId,
              roomId: roomSessionId || appId,
              displayName,
            }),
          );
        }
        optionsRef.current.onReady?.({
          sessionId: sid ?? '',
          userId: typeof message.userId === 'string' ? message.userId : '',
          appScope: typeof message.appScope === 'string' ? message.appScope : null,
        });
        return;
      }
      if (message.type === 'pong') return;
      if (message.type === 'ping') {
        socket.send(JSON.stringify({ type: 'pong' }));
        return;
      }
      optionsRef.current.onMessage?.(message);
    };

    socket.onerror = () => {
      setStatus('error');
    };

    socket.onclose = (event) => {
      stopPing();
      if (socketRef.current === socket) socketRef.current = null;
      setSessionId(null);

      const terminal = TERMINAL_CLOSE_CODES.has(event.code);
      const canRetry = !terminal && retriesRef.current < maxRetries;
      setError(describeClose(event.code, event.reason));
      setStatus(terminal ? 'error' : 'closed');
      optionsRef.current.onClose?.({ code: event.code, reason: event.reason, willRetry: canRetry });

      if (canRetry) {
        const attempt = retriesRef.current;
        retriesRef.current = attempt + 1;
        const delay = Math.min(30000, 1000 * Math.pow(2, attempt)) + Math.floor(Math.random() * 250);
        setTimeout(() => {
          void connect();
        }, delay);
      }
    };
  }, [appId, roomSessionId, displayName, mode, maxRetries]);

  const reconnect = useCallback(() => {
    retriesRef.current = 0;
    const socket = socketRef.current;
    if (socket) {
      socket.onclose = null;
      socket.close();
    }
    socketRef.current = null;
    void connect();
  }, [connect]);

  useEffect(() => {
    if (!enabled) {
      setStatus('idle');
      return;
    }
    void connect();
    return () => {
      const socket = socketRef.current;
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
      socketRef.current = null;
      setStatus('idle');
    };
    // Reconnect whenever the connection identity changes.
  }, [enabled, connect]);

  return { status, error, sessionId, send, reconnect };
}
