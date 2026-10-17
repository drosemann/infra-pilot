/**
 * Public surface of the authenticated WebSocket gateway.
 *
 * `server/index.ts` imports from this barrel: config loading, the ticket
 * service, the audit logger, the gateway factory, and the token router.
 */
export { loadWsConfig, resolveWsTicketSecret, DEFAULT_WS_CONFIG } from './config.ts';
export { TicketService } from './auth.ts';
export { WsAuditLogger, WS_AUDIT_ACTIONS } from './audit.ts';
export { AclService, normalizeAppId } from './acl.ts';
export { SessionRegistry, sessionRegistryOptionsFromConfig } from './sessions.ts';
export { WsRateLimiter } from './rate-limit.ts';
export { createWsGateway, sanitizeDisplayName } from './gateway.ts';
export type { SocketLike, ChildProcessLike, SpawnFn, WsGatewayOptions } from './gateway.ts';
export { createWsTokenRouter } from './routes.ts';
export type { WsTokenRouterOptions } from './routes.ts';
export { WS_CLOSE_CODES, wsError } from './types.ts';
export type {
  WsAction,
  WsConfig,
  WsSession,
  WsErrorMessage,
  WsCloseCode,
  TicketClaims,
  MintedTicket,
  VerifyResult,
  TicketDenyReason,
  ResolveAppAccess,
  ResolveContainerId,
  ExecCommand,
  ExecResult,
  LogAudit,
  Clock,
} from './types.ts';
