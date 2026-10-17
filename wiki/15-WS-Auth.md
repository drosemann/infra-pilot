# WebSocket Gateway Protocol

The management panel's realtime gateway (`services/management-panel/server/ws/`)
replaces the former unauthenticated `WebSocketServer` with an authenticated,
per-app authorized connection lifecycle. This page is the wire-protocol
reference: handshake, message schemas, close codes, and limits.

Companion docs: [Security](08-Security.md), the panel
[README](../services/management-panel/README.md), and
[Auth Matrix](11-Auth-Matrix.md).

## Trust model

- The WebSocket upgrade itself is unauthenticated; every connection must
  present a ticket within the auth window before any feature message is
  honored. Feature messages sent earlier are refused.
- A ticket is a single-use bearer credential for at most five minutes,
  HMAC-SHA256 signed with `WS_TICKET_SECRET`, bound to one user (`uid`) and
  optionally one app (`aid`). Tickets are never logged or audited; only the
  ticket id (`jti`) is recorded.
- Authorization is deny-by-default. The host application resolves
  `userId × appId × action` (ownership plus role assignments); the ticket
  scope can only narrow this further, never widen it.
- Docker commands (`docker logs`, `docker stats`, `docker exec`) run only
  after the matching ACL decision succeeds.

## Obtaining a ticket

```http
POST /api/ws-token
Authorization: Bearer <supabase-jwt-or-api-key>
Content-Type: application/json

{ "appId": "optional-app-scope" }
```

```json
{ "ticket": "wst1.<claims>.<signature>", "expiresIn": 300, "appScope": null }
```

- `appId` is optional; when present the caller must own the app or hold a
  role assignment for it (403 otherwise). A blank `appId` is treated as
  unscoped.
- Revocation: `POST /api/ws-token/revoke` with `{ "ticket": "..." }` for one
  ticket (ownership checked) or `{ "all": true }` for every ticket the caller
  holds. Live sessions authenticated with a revoked ticket are closed with
  4003; `sessionsClosed` reports how many.

## Handshake

Two equivalent ways to authenticate after upgrading:

```text
1. Query parameter (used by the panel frontend):
   ws://host:3001/?ticket=<ticket>&appId=<id>&sessionId=<roomId>&displayName=<name>
   -> server: { "type": "ready", ... }

2. Challenge/response:
   ws://host:3001/
   -> server: { "type": "auth_challenge", "authTimeoutMs": 5000, "serverTime": "..." }
   <- client: { "type": "auth", "ticket": "<ticket>" }
   -> server: { "type": "ready", ... }
```

If no valid ticket arrives within `WS_AUTH_TIMEOUT_MS` (default 5000 ms) the
server sends an `auth_failed` error and closes with 4002. A ticket already
used on another connection (replay) is refused with 4003. The `ready` frame
is the only signal that feature messages are accepted:

```json
{ "type": "ready", "sessionId": "uuid", "userId": "user-1",
  "appScope": "app-1-or-null", "mode": "viewer" | "terminal" }
```

## Client-to-server messages

All frames are JSON objects with a `type` field. Anything else is a protocol
violation (`bad_message` / `unknown_type`); repeated violations close the
connection with 4009.

| Type | Payload | Action checked | Notes |
| --- | --- | --- | --- |
| `auth` | `ticket` | — | Only before authentication. |
| `ping` | — | — | Application-level ping; answered with `pong`. |
| `pong` | — | — | Answers the server's application ping. |
| `subscribe` | `appId` | `logs:read` | Starts `docker logs --tail 100 -f`. |
| `unsubscribe` | `appId` | — | Kills the log stream. |
| `subscribe:metrics` | `appId` | `metrics:read` | Starts `docker stats` polling (2 s). |
| `unsubscribe:metrics` | `appId` | — | Stops the poll loop. |
| `join` | `appId`, `roomId`, `displayName?` | `terminal:write` | Joins a collaborative room; returns `history`. |
| `leave` | `roomId` | — | Leaves the room. |
| `terminal-input` | `appId`, `roomId`, `text` | `terminal:write` | Requires room membership. |
| `cursor` | `appId`, `roomId`, `cursor` | `terminal:write` | Relayed to others only. |
| `chat` | `appId`, `roomId`, `text` | `terminal:write` | Relayed to the whole room. |
| `exec` | `appId?`, `command`, `roomId?` | `terminal:exec` | Runs `docker exec <container> sh -c <command>`; replies `exec_result`. |

`appId` may fall back to the `?appId=` connection parameter. App ids are
validated (trim, 1-128 chars, no control characters) before any lookup.
Commands are limited to 2000 characters; oversized frames (> `WS_MAX_MESSAGE_BYTES`,
default 64 KiB) are rejected by the WebSocket layer with 1009.

## Server-to-client messages

| Type | Payload | Meaning |
| --- | --- | --- |
| `auth_challenge` | `authTimeoutMs`, `serverTime` | Send an `auth` message. |
| `ready` | `sessionId`, `userId`, `appScope`, `mode` | Handshake complete. |
| `subscribed` | `appId`, `channel` (`logs`/`metrics`) | Subscription started. |
| `unsubscribed` | `appId`, `channel` | Subscription stopped. |
| `log` | `appId`, `data` | Log chunk. |
| `log_end` | `appId` | Log stream ended. |
| `metrics` | `appId`, `data` | Parsed `docker stats` snapshot. |
| `history` | `lines[]` | Buffered room output on join. |
| `terminal-output` | `line`, `userId`, `displayName` | Room command echo/output. |
| `user-joined` / `user-left` | `userId`, `displayName`, `users[]` | Room membership changes. |
| `cursor-update` | `userId`, `displayName`, `cursor` | Peer cursor position. |
| `chat-message` | `userId`, `displayName`, `text`, `timestamp` | Room chat. |
| `exec_result` | `appId`, `command`, `ok`, `output`, `error?`, `exitCode?` | Exec outcome. |
| `pong` | — | Answers an application `ping`. |
| `error` | `code`, `message`, `appId?`, `action?`, `scope?`, `retryAfterMs?` | Structured error. |

## Close codes

Application close codes live in the 4000-4999 range reserved by RFC 6455
(1009 is the standard "message too big").

| Code | Name | When |
| --- | --- | --- |
| 4001 | `AUTH_FAILED` | Ticket missing, malformed, or signature invalid. |
| 4002 | `AUTH_TIMEOUT` | No `auth` message / `?ticket=` within the auth window. |
| 4003 | `TICKET_INVALID` | Ticket expired, replayed, or revoked. |
| 4004 | `NOT_AUTHORIZED` | Repeated per-app ACL denials; or ticket scope vs `?appId=` mismatch. |
| 4008 | `RATE_LIMITED` | Rate-limit strikes exhausted. |
| 4009 | `POLICY_VIOLATION` | Repeated malformed/unknown messages. |
| 1009 | `MESSAGE_TOO_BIG` | Frame exceeded `WS_MAX_MESSAGE_BYTES`. |
| 4013 | `IDLE_TIMEOUT` | No activity within `WS_IDLE_TIMEOUT_SECONDS`; also used for missed heartbeats. |
| 4014 | `SESSION_LIMIT` | Per-user session cap reached (`reject`) or the session was replaced (`kick-oldest`). |

Clients must treat 4001-4004, 4008, 4009, and 4014 as terminal: minting a
fresh ticket (on 4003) or reconnecting blindly cannot succeed. The panel
frontend hook (`src/hooks/useWebSocket.ts`) implements this policy plus
capped exponential backoff for transient closes.

## Sessions, heartbeats, and rate limits

- Sessions are registered per connection: user id, ticket `jti`, app scope,
  room membership, last-activity timestamp.
- The server pings at `WS_HEARTBEAT_INTERVAL_SECONDS`; a missed pong for a
  full interval terminates the connection (4013). Application-level
  `ping`/`pong` frames also reset the idle timer.
- Idle sessions are swept every minute and closed with 4013 after
  `WS_IDLE_TIMEOUT_SECONDS` (default 1800).
- Each user may hold `WS_MAX_SESSIONS_PER_USER` sessions (default 10). Under
  `kick-oldest` (default) the oldest socket is closed with 4014; under
  `reject` new connections are refused with 4014.
- Token buckets enforce `WS_MAX_MESSAGES_PER_MINUTE` per connection and
  `WS_MAX_SUBSCRIBES_PER_MINUTE` per user. Denied attempts receive
  `{ "type": "error", "code": "rate_limited", "scope": "...", "retryAfterMs": n }`
  and accumulate strikes; exhausting `WS_MAX_RATE_STRIKES` closes with 4008.

## Configuration

All knobs are validated at startup (non-numeric values fail fast, ranges are
clamped). See `services/management-panel/.env.example` for the full list:
`WS_TICKET_SECRET`, `WS_TICKET_TTL_SECONDS` (max 300),
`WS_TICKET_SKEW_SECONDS`, `WS_AUTH_TIMEOUT_MS`, `WS_IDLE_TIMEOUT_SECONDS`,
`WS_HEARTBEAT_INTERVAL_SECONDS`, `WS_MAX_SESSIONS_PER_USER`,
`WS_SESSION_LIMIT_POLICY`, `WS_MAX_MESSAGES_PER_MINUTE`,
`WS_MAX_SUBSCRIBES_PER_MINUTE`, `WS_MAX_RATE_STRIKES`, `WS_MAX_VIOLATIONS`,
`WS_MAX_MESSAGE_BYTES`.

Without `WS_TICKET_SECRET` the server generates an ephemeral per-process
secret: tickets then die with the process (bounded by the TTL) and do not
validate across replicas. Production deployments should set it.

## Audit events

The gateway writes `ws:*` actions through the panel audit log:
`ws:ticket:issue`, `ws:ticket:reject`, `ws:ticket:revoke`, `ws:connect`,
`ws:disconnect`, `ws:auth:failed`, `ws:subscribe`, `ws:subscribe:denied`,
`ws:terminal`, `ws:terminal:denied`, `ws:rate-limit`. Ticket strings,
nonces, and signatures never appear in audit rows or logs; pre-authentication
failures without a known user are emitted as structured console warnings
keyed by reason and IP.
