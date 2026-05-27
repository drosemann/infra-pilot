# feature 27: collaborative terminal

| metadata | value |
|----------|-------|
| feature id | 27 |
| feature name | collaborative terminal |
| primary service | management panel |
| effort estimate | large (7-10 pt) |
| dependencies | websocket gateway, tmux, auth service |
| priority | high |

## 1. overview

the collaborative terminal enables multiple users to share a single terminal session in real time. users can invite peers via a shareable url, observe peer cursors, and communicate via an embedded chat panel -- all within a tmux-backed session managed by the management panel.

### 1.1 goals

- allow ad-hoc pair debugging and collaborative troubleshooting
- provide shared terminal access without granting ssh credentials
- support read-only and read-write participation modes
- include in-session chat to reduce context-switching
- persist session history for post-session review

### 1.2 non-goals

- replace ssh or full remote desktop solutions
- support concurrent shell job isolation (all participants share one tmux session)
- file transfer (handled by separate feature)
- recording/playback of keystrokes (future enhancement)

## 2. architecture

### 2.1 high-level diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (User A)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Collaborative Terminal UI (React)                        │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │ Terminal    │  │ Peer Cursor   │  │ Chat Panel      │  │  │
│  │  │ (xterm.js)  │  │ Overlay       │  │ (WebSocket)     │  │  │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘  │  │
│  └─────────┼───────────────┼───────────────────┼─────────────┘  │
└────────────┼───────────────┼───────────────────┼────────────────┘
             │               │                   │
             │   WebSocket   │   WebSocket       │   WebSocket
             │   (/ws/term)  │   (/ws/cursor)    │   (/ws/chat)
             ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Management Panel Backend                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  WebSocket Multiplexer                                   │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │ Terminal    │  │ Cursor Sync  │  │ Chat Broker     │  │  │
│  │  │ Manager     │  │ Engine       │  │                 │  │  │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘  │  │
│  └─────────┼────────────────┼───────────────────┼─────────────┘  │
│            │                │                   │                │
│            ▼                ▼                   ▼                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Session Manager                                          │  │
│  │  - Create/destroy sessions                                │  │
│  │  - Auth & permissions                                     │  │
│  │  - Share URL generation                                   │  │
│  │  - Session history                                        │  │
│  └──────────────────────────┬────────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────┐
              │  tmux (on target host)       │
              │  - Session: collab-<uuid>    │
              │  - Control mode: -CC         │
              │  - Pipe I/O via stdio        │
              └─────────────────────────────┘
```

### 2.2 component descriptions

| component | role | technology |
|-----------|------|------------|
| terminal ui | renders terminal emulator in browser | xterm.js |
| peer cursor overlay | shows other users' cursor positions | canvas overlay |
| chat panel | real-time chat alongside terminal | react + websocket |
| websocket multiplexer | routes messages between clients and tmux | go / node.js |
| session manager | crud for collaborative sessions | management panel |
| tmux | terminal multiplexer on target host | tmux 3.x |

### 2.3 data flow

• **host** clicks "share terminal" to management panel creates a tmux session on the target host
• panel generates a shareable url: `https://panel.example.com/collab/<session-id>?token=<jwt>`
• **guest** opens url to websocket connection established to `/ws/term/<session-id>`
• all keystrokes are forwarded to the tmux session via its control mode (`-cc`)
• tmux output is broadcast to all connected clients
• cursor positions are synchronized via separate websocket channel
• chat messages are brokered through the chat broker and persisted to db

## 3. implementation plan

### phase 1: foundation (pt 2-3)

| task | description |
|------|-------------|
| 1.1 | implement tmux control-mode wrapper: spawn, attach, pipe i/o |
| 1.2 | build websocket endpoint `/ws/term/:sessionId` with jwt auth |
| 1.3 | integrate xterm.js with websocket feed (single-user test) |
| 1.4 | session crud api (create, get, delete) |

### phase 2: multi-user (pt 3-4)

| task | description |
|------|-------------|
| 2.1 | implement message fan-out: broadcast output to all peers |
| 2.2 | input locking: only one writer at a time (request/grant model) |
| 2.3 | peer cursor synchronization over websocket |
| 2.4 | share link generation with expiring jwt tokens |
| 2.5 | read-only vs. read-write permission enforcement |

### phase 3: chat & polish (pt 2-3)

| task | description |
|------|-------------|
| 3.1 | in-terminal chat panel ui + websocket broker |
| 3.2 | session history recording (log all output to db) |
| 3.3 | session replay viewer (read-only playback of history) |
| 3.4 | disconnect handling, reconnection, session heartbeat |
| 3.5 | admin controls: force-remove participant, terminate session |

## 4. api design

### 4.1 rest endpoints

```
POST   /api/v2/collab/sessions                Create session
GET    /api/v2/collab/sessions                 List user's sessions
GET    /api/v2/collab/sessions/:id             Get session details
DELETE /api/v2/collab/sessions/:id             Terminate session
POST   /api/v2/collab/sessions/:id/invite     Generate share link
GET    /api/v2/collab/sessions/:id/history    Get session log
```

### 4.2 websocket endpoints

```
/ws/v2/collab/term/:sessionId       Terminal I/O stream
/ws/v2/collab/cursor/:sessionId     Cursor position sync
/ws/v2/collab/chat/:sessionId       Chat message broker
```

### 4.3 request/response examples

**create session:**
```json
POST /api/v2/collab/sessions
{
  "host_id": "srv-prod-01",
  "user": "ssh-user",
  "initial_command": "/bin/bash",
  "session_name": "debug-session-20260527"
}

Response 201:
{
  "id": "cs_abc123",
  "ws_url": "wss://panel.example.com/ws/v2/collab/term/cs_abc123",
  "share_url": "https://panel.example.com/collab/cs_abc123?token=eyJhbGci...",
  "tmux_session": "collab-cs_abc123",
  "created_at": "2026-05-27T12:00:00Z",
  "participants": []
}
```

**invite:**
```json
POST /api/v2/collab/sessions/cs_abc123/invite
{
  "permission": "read_write",   // "read_only" | "read_write"
  "expires_in_minutes": 60
}

Response 200:
{
  "share_url": "https://panel.example.com/collab/cs_abc123?token=eyJhbGci...",
  "expires_at": "2026-05-27T13:00:00Z"
}
```

**websocket message (terminal i/o):**
```json
// Client → Server (keystroke)
{ "type": "input", "data": "ls -la\r", "seq": 42 }

// Server → Client (output)
{ "type": "output", "data": "\u001b[01;32mtotal 128\n...", "seq": 42 }

// Server → Client (participant update)
{ "type": "participant_join", "user_id": "u_456", "cursor": {"row": 12, "col": 5} }
```

**websocket message (cursor):**
```json
// Client → Server
{ "type": "cursor_move", "row": 24, "col": 15 }

// Server → Client (broadcast)
{ "type": "cursor_update", "user_id": "u_456", "display_name": "Alice", "row": 24, "col": 15 }
```

**websocket message (chat):**
```json
// Client → Server
{ "type": "chat_message", "text": "Run apt-get update first" }

// Server → Client (broadcast)
{ "type": "chat_message", "user_id": "u_456", "display_name": "Alice", "text": "Run apt-get update first", "ts": "2026-05-27T12:05:00Z" }
```

## 5. data model

### 5.1 `collab_sessions`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | unique session identifier |
| host_id | varchar(64) | target server/vm identifier |
| ssh_user | varchar(64) | ssh user on target |
| initial_command | text | default shell/command |
| tmux_session_name | varchar(128) | tmux session identifier on host |
| status | enum | `active`, `terminated`, `expired` |
| created_by | uuid (fk to users) | session creator |
| created_at | timestamptz | creation timestamp |
| terminated_at | timestamptz | when session ended |
| max_participants | int | default: 10 |

### 5.2 `collab_participants`

| column | type | description |
|--------|------|-------------|
| id | uuid (pk) | unique participant id |
| session_id | uuid (fk) | associated session |
| user_id | uuid (fk to users) | participant |
| permission | enum | `read_only`, `read_write` |
| connected_at | timestamptz | join timestamp |
| disconnected_at | timestamptz | leave timestamp (nullable) |
| is_currently_connected | boolean | live presence flag |

### 5.3 `collab_chat_messages`

| column | type | description |
|--------|------|-------------|
| id | bigserial (pk) | auto-increment |
| session_id | uuid (fk) | associated session |
| user_id | uuid (fk to users) | sender |
| message | text | message content |
| created_at | timestamptz | timestamp |

### 5.4 `collab_session_logs`

| column | type | description |
|--------|------|-------------|
| id | bigserial (pk) | auto-increment |
| session_id | uuid (fk) | associated session |
| log_entry | text | raw terminal output at interval |
| offset_bytes | bigint | byte offset in stream |
| captured_at | timestamptz | timestamp |

## 6. service assignments

| service | responsibilities |
|---------|-----------------|
| **management panel** (primary) | websocket multiplexer, session crud, tmux wrapper, chat broker, history storage |
| **auth service** | jwt generation for share links, permission validation |
| **target host** | tmux installation, ssh access, session isolation |
| **database** | session metadata, participant tracking, chat history, logs |

## 7. security & permissions

| aspect | implementation |
|--------|---------------|
| share link expiry | jwt with `exp` claim, default 60 min |
| session isolation | each session runs in its own tmux instance |
| read-only enforcement | server refuses `input` messages from read-only participants |
| host access control | only users with `server:ssh` permission can create sessions |
| invite control | only session host can generate share links |
| rate limiting | max 5 concurrent sessions per user |

## 8. effort estimate

| phase | person-days |
|-------|-------------|
| phase 1: foundation | 2-3 pt |
| phase 2: multi-user | 3-4 pt |
| phase 3: chat & polish | 2-3 pt |
| **total** | **7-10 pt** |

## 9. future enhancements

- session recording with playback scrubber
- encrypted terminal i/o (e2ee)
- multi-tab sessions (multiple tmux windows)
- file drag-and-drop into terminal
- integration with runbook automation
