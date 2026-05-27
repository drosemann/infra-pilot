# ai assistant (chatbot)

feature id: 3
category: ai & intelligence
primary service: integration service
effort estimate: extra large (11+ pt)
status: planned

## overview

provide a natural-language conversational interface for server management, monitoring, and troubleshooting. users can ask questions, issue commands, and receive contextual responses in plain english. the assistant understands infrastructure concepts, remembers conversation context, and can execute multi-step actions across services.

### example queries

- "show me servers using >80% ram"
- "restart web-01 and notify slack"
- "why did my backup fail last night?"
- "deploy the latest build to staging and run health checks"
- "what's the cpu trend on db-primary over the last 7 days?"
- "create a firewall rule blocking 10.0.0.0/8 on all game servers"

### goals

- reduce the learning curve for server management via natural language
- enable rapid troubleshooting through conversational context
- support multi-turn interactions with memory of previous queries
- execute actions with safety confirmation for destructive operations

## architecture

```
┌──────────────────────────────────────────────────────────┐
│                    User Interfaces                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │  Panel   │  │  Discord │  │  Slack   │  │  CLI     ││
│  │  Widget  │  │   Bot    │  │   App    │  │  ipilot  ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘│
└───────┼──────────────┼────────────┼──────────────┼───────┘
        │              │            │              │
        ▼              ▼            ▼              ▼
┌──────────────────────────────────────────────────────────┐
│              Integration Service                          │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │              NLU Pipeline                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Input    │──│ Intent   │──│ Entity Extraction │ │  │
│  │  │ Parser   │  │ Classifier│  │ (NER)            │ │  │
│  │  └──────────┘  └────┬─────┘  └────────┬─────────┘ │  │
│  │                      │                 │           │  │
│  │                      ▼                 ▼           │  │
│  │  ┌────────────────────────────────────────────┐    │  │
│  │  │         Context Manager                     │    │  │
│  │  │  Session tracking, conversation history,    │    │  │
│  │  │  entity resolution across turns             │    │  │
│  │  └──────────────────┬─────────────────────────┘    │  │
│  └─────────────────────┼──────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │           Action Orchestrator                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Query    │──│ Command  │──│ Confirmation      │ │  │
│  │  │ Resolver │  │ Executor │  │ (destructive ops) │ │  │
│  │  └────┬─────┘  └────┬─────┘  └──────────────────┘ │  │
│  └───────┼──────────────┼─────────────────────────────┘  │
│          │              │                                 │
│          ▼              ▼                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │           Response Generator                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Data     │──│ Template │──│ LLM Rewriting     │ │  │
│  │  │ Formatter│  │ Engine   │  │ (natural language)│ │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Internal Services                            │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────────┐ │
│  │Orchestrator│ │  Database  │ │  External APIs       │ │
│  │ Agent      │ │  (metrics, │ │  (Slack, Discord,    │ │
│  │ (actions)  │ │  logs)     │ │  GitHub, PagerDuty)  │ │
│  └────────────┘ └────────────┘ └──────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1: nlu pipeline (3-4 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 1.1 | intent taxonomy definition | 15-20 intent classes with example utterances |
| 1.2 | intent classifier training | fine-tuned bert or distilbert model |
| 1.3 | entity extraction (ner) | custom spacy ner pipeline for infra entities |
| 1.4 | input normalization & spelling correction | symspell + domain dictionary |
| 1.5 | multi-language support framework | i18n intent mapping (english, german) |

**intent taxonomy:**

```yaml
# config/intent_taxonomy.yaml
intents:
  - name: list_servers
    examples:
      - "show me all servers"
      - "list my servers"
      - "what servers do I have"
      - "zeige alle Server"
    entities: [filter, status, region]
    action_type: query
    scope: read

  - name: get_server_status
    examples:
      - "status of web-01"
      - "is db-primary running"
      - "what's the state of my game server"
    entities: [server_name]
    action_type: query
    scope: read

  - name: restart_server
    examples:
      - "restart web-01"
      - "reboot db-primary"
      - "starte web-01 neu"
    entities: [server_name]
    action_type: command
    scope: write
    requires_confirmation: true

  - name: analyze_performance
    examples:
      - "why is my server slow"
      - "show me CPU usage for web-01"
      - "what's the RAM trend on db-primary"
      - "analyze performance of game-01"
    entities: [server_name, metric, time_range]
    action_type: query
    scope: read

  - name: investigate_backup_failure
    examples:
      - "why did my backup fail"
      - "check last backup status"
      - "was backup successful last night"
    entities: [server_name, time_range]
    action_type: query
    scope: read

  - name: execute_action
    examples:
      - "deploy version 2.1 to staging"
      - "create a firewall rule blocking 10.0.0.0/8"
      - "scale up web pool to 5 instances"
    entities: [action_target, action_params]
    action_type: command
    scope: write
    requires_confirmation: true
```

### phase 2: context & session management (2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 2.1 | session store (redis) | ttl-based session expiry (30min idle, 24h max) |
| 2.2 | entity resolution across turns | track mentioned servers, resolve "it" / "that server" |
| 2.3 | conversation history compression | sliding window of last n exchanges |
| 2.4 | user authorization state | permissions cached per session |

**session data structure:**

```json
{
  "session_id": "sess-abc123",
  "user_id": "usr-456",
  "user_roles": ["admin", "sre"],
  "created_at": "2026-05-27T10:00:00Z",
  "last_active": "2026-05-27T10:15:00Z",
  "context": {
    "active_server": "web-01",
    "mentioned_servers": ["web-01", "db-primary"],
    "last_query_type": "status",
    "pending_confirmation": null,
    "conversation": [
      {"role": "user", "text": "show me servers with high CPU", "intent": "list_servers"},
      {"role": "assistant", "text": "I found 3 servers...", "data": {...}}
    ]
  },
  "auth": {
    "permissions": ["servers.read", "servers.write", "backups.read"],
    "workspace_id": "ws-789"
  }
}
```

### phase 3: action orchestrator (3 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 3.1 | query resolver | maps intent+entities to api calls or db queries |
| 3.2 | command executor | action validation, dry-run, execution |
| 3.3 | confirmation workflow | destructive action guard: "are you sure?" |
| 3.4 | multi-step action planner | decompose complex requests into sequential steps |
| 3.5 | error handling & fallback | graceful degradation when parts fail |

**action resolution flow:**

```python
# pseudocode: action_orchestrator.py
async def resolve_action(intent: str, entities: dict, context: SessionContext) -> ActionResult:
    if intent == "list_servers":
        filters = build_filters(entities, context)
        servers = await orchestrator_client.get_servers(filters)
        return QueryResult(data=servers, format="table")

    elif intent == "restart_server":
        server_name = entities.get("server_name") or context.active_server
        if not server_name:
            return ActionResult.ask("Which server would you like to restart?")

        health_check = await orchestrator_client.pre_restart_check(server_name)
        if not health_check.ok:
            return ActionResult.warn(f"Pre-restart check failed: {health_check.reason}")

        if entities.get("confirmed"):
            result = await orchestrator_client.restart_server(server_name)
            await notifier.send(f"🔄 Server {server_name} restart initiated")
            return ActionResult.success(f"Restarting {server_name}...")

        return ActionResult.ask(
            f"Are you sure you want to restart {server_name}?",
            confirmation_required=True,
            context={"server_name": server_name, "intent": intent}
        )

    elif intent == "investigate_backup_failure":
        server = entities.get("server_name") or context.active_server
        window = entities.get("time_range") or "last 24h"
        backup_logs = await db.query_backup_failures(server, window)
        analysis = await llm_analyzer.analyze(
            f"Explain why backup failed for {server}\n{backup_logs}"
        )
        return QueryResult(data=analysis, format="narrative")
```

### phase 4: response generation & llm integration (2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 4.1 | structured data → narrative transformer | llm prompt for converting json to natural language |
| 4.2 | response templating engine | templates per intent type (table, summary, alert) |
| 4.3 | streaming responses (websocket) | real-time partial response delivery |
| 4.4 | llm provider abstraction | openai / anthropic / local model support |
| 4.5 | prompt security & injection prevention | input sanitization, output validation |

**llm prompt template:**

```
You are an infrastructure assistant for Infra Pilot.
You help users manage servers, diagnose issues, and execute commands.

Current user: {user_name}
Workspace: {workspace_name}
Roles: {user_roles}

Conversation history:
{history}

User query: {query}

Intent detected: {intent}
Entities: {entities}
Data available: {data}

Instructions:
- Be concise and technical.
- If displaying server data, use a markdown table.
- For errors, explain the likely cause and suggest next steps.
- Do NOT fabricate data not present in the "Data available" field.
- If the user asks for a destructive action, ensure confirmation was given.
- Respond in the user's language (detected: {language}).
```

### phase 5: interface integrations (1-2 pt)

| step | description | artifacts |
|------|-------------|-----------|
| 5.1 | panel chat widget (iframe/component) | react chat component with markdown rendering |
| 5.2 | discord bot slash command | `/ask` command with ephemeral response |
| 5.3 | slack app integration | slash command + interactive messages |
| 5.4 | cli chat mode | `ipilot ask "..."` |

## api design

### rest api

#### send query

```
POST /api/v1/assistant/query
```

request:
```json
{
  "query": "Show me servers with more than 80% RAM usage",
  "session_id": "sess-abc123",
  "channel": "panel",
  "context": {
    "workspace_id": "ws-789",
    "current_view": "servers"
  }
}
```

response:
```json
{
  "response": "I found **3 servers** exceeding 80% RAM usage:\n\n| Server | RAM Usage | Total RAM | Status |\n|--------|-----------|-----------|--------|\n| web-01 | 89% | 32 GB | Running |\n| db-primary | 94% | 64 GB | Running |\n| game-02 | 87% | 16 GB | Running |\n\nWould you like me to investigate any of these further?",
  "session_id": "sess-abc123",
  "intent": "list_servers",
  "entities": {
    "metric": "ram",
    "threshold": 80,
    "operator": "greater_than"
  },
  "actions_available": [
    {"label": "Investigate web-01", "query": "Analyze RAM usage on web-01"},
    {"label": "Restart web-01", "query": "Restart web-01", "confirmation_required": true}
  ],
  "data": [...]
}
```

#### stream response (websocket)

```
ws://<host>/ws/v1/assistant
```

request message:
```json
{
  "type": "query",
  "session_id": "sess-abc123",
  "query": "Why did my backup fail last night?"
}
```

streamed response:
```json
{
  "type": "stream_chunk",
  "session_id": "sess-abc123",
  "chunk": "I checked the backup logs for your servers. "
}
{
  "type": "stream_chunk",
  "session_id": "sess-abc123",
  "chunk": "db-primary's backup failed at 02:34 due to a **disk space issue**. "
}
{
  "type": "stream_complete",
  "session_id": "sess-abc123",
  "response": "I checked the backup logs for your servers. db-primary's backup failed at 02:34 due to a **disk space issue**.\n\nThe `/backup` partition had only 2% free space. I recommend:\n1. Run `sudo du -sh /backup/* | sort -rh` to find large files\n2. Clean up old backups with `retention_policy.sh`\n3. Consider increasing the backup volume\n\nWeb-01 backups completed successfully at 03:00.",
  "actions_available": [
    {"label": "Show disk usage", "query": "Show disk usage on db-primary"},
    {"label": "Run backup cleanup", "query": "Run backup retention policy on db-primary", "confirmation_required": true}
  ]
}
```

#### confirm action

```
POST /api/v1/assistant/confirm
```

request:
```json
{
  "session_id": "sess-abc123",
  "confirmation_id": "cnf-456",
  "confirmed": true,
  "context": {
    "server_name": "web-01",
    "action": "restart"
  }
}
```

#### get conversation history

```
GET /api/v1/assistant/sessions/{session_id}/history
```

## data model

```python
# models/assistant.py
@dataclass
class ChatMessage:
    id: str
    session_id: str
    role: str  # user / assistant / system
    content: str
    intent: str | None
    entities: dict | None
    metadata: dict | None
    created_at: datetime

@dataclass
class ChatSession:
    id: str
    user_id: str
    workspace_id: str
    channel: str   # panel / discord / slack / cli
    context: SessionContext
    created_at: datetime
    last_active: datetime
    message_count: int

@dataclass
class SessionContext:
    active_server: str | None
    mentioned_servers: list[str]
    last_query_type: str | None
    pending_confirmation: ConfirmationRequest | None
    conversation: list[ChatMessage]  # last 20 messages

@dataclass
class ConversationSummary:
    summary: str
    key_entities: list[str]
    pending_actions: list[str]

@dataclass
class IntentClassification:
    intent: str
    confidence: float
    entities: dict[str, Any]
    language: str

@dataclass
class ConfirmationRequest:
    id: str
    action_type: str
    description: str
    context: dict
    expires_at: datetime
    confirmed: bool | None
```

**database schema:**

```sql
-- Chat sessions
CREATE TABLE chat_sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    workspace_id    TEXT NOT NULL,
    channel         TEXT NOT NULL,
    context         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_active     TIMESTAMPTZ DEFAULT NOW(),
    message_count   INTEGER DEFAULT 0
);

CREATE INDEX idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_sessions_active ON chat_sessions(last_active);

-- Chat messages
CREATE TABLE chat_messages (
    id              TEXT PRIMARY KEY,
    session_id      TEXT REFERENCES chat_sessions(id),
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    intent          TEXT,
    entities        JSONB,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON chat_messages(session_id, created_at);

-- Action audit log
CREATE TABLE assistant_actions (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT REFERENCES chat_sessions(id),
    user_id         TEXT NOT NULL,
    action_type     TEXT NOT NULL,
    intent          TEXT NOT NULL,
    entities        JSONB,
    query           TEXT,
    result          TEXT,
    confirmed       BOOLEAN,
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## service assignments

| service | responsibility |
|---------|---------------|
| integration service | nlu pipeline (intent classifier, ner), context manager, action orchestrator, response generator, llm integration, session store |
| orchestrator agent | action execution (restart, deploy, config changes), metric query resolution |
| management panel | chat widget ui, conversation history view, suggestion chips |
| discord service | slash command handler, message formatting |
| slack integration | slash command handler, interactive message components |

## configuration reference

```yaml
# config/ai_assistant.yaml
nlu:
  intent_model: "bert-base-multilingual-cased"  # or path to fine-tuned model
  intent_confidence_threshold: 0.6
  ner_model: "spacy"
  supported_languages: ["en", "de"]
  input_max_length: 1000

llm:
  provider: "openai"    # openai | anthropic | local
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 1024
  streaming: true
  timeout_seconds: 30
  prompt_template: "config/prompts/assistant.j2"

session:
  ttl_minutes: 30
  max_duration_hours: 24
  max_history_messages: 20
  store: "redis"

actions:
  require_confirmation:
    - restart_server
    - stop_server
    - delete_server
    - modify_firewall
    - execute_command
  max_concurrent_actions: 5
  dry_run_default: true

channels:
  panel:
    enabled: true
    websocket_path: "/ws/v1/assistant"
  discord:
    enabled: true
    command_name: "ask"
    ephemeral: true
  slack:
    enabled: false
    command_name: "/ipilot-ask"

security:
  input_sanitization: true
  prevent_sql_injection: true
  prevent_prompt_injection: true
  rate_limit_per_user: 20  # queries per minute
  audit_all_actions: true
```

## effort breakdown

| phase | task | pt | dependencies |
|-------|------|----|-------------|
| 1.1 | intent taxonomy design | 0.5 | product spec |
| 1.2 | intent classifier training | 1.5 | labeled dataset |
| 1.3 | entity extraction (ner) | 1 | training data |
| 1.4 | input normalization | 0.5 | nlu pipeline |
| 1.5 | multi-language framework | 0.5 | core nlu |
| 2.1 | session store (redis) | 0.5 | redis instance |
| 2.2 | cross-turn entity resolution | 0.5 | session store |
| 2.3 | history compression | 0.5 | session store |
| 2.4 | authorization integration | 0.5 | auth service |
| 3.1 | query resolver | 1 | api gateway |
| 3.2 | command executor | 1.5 | orchestrator api |
| 3.3 | confirmation workflow | 0.5 | action executor |
| 3.4 | multi-step action planner | 0.5 | command executor |
| 3.5 | error handling | 0.5 | all phases |
| 4.1 | narrative transformer | 0.5 | llm integration |
| 4.2 | response templates | 0.5 | intent definitions |
| 4.3 | streaming responses | 0.5 | websocket infra |
| 4.4 | llm provider abstraction | 0.5 | any llm api key |
| 4.5 | prompt security | 0.5 | security review |
| 5.1 | panel chat widget | 1 | react component library |
| 5.2 | discord bot integration | 0.5 | discord bot sdk |
| 5.3 | slack app integration | 0.5 | slack api |
| 5.4 | cli chat mode | 0.5 | cli framework |
| | total | 14.5 | |

## risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| nlu misclassification | wrong action executed | high confidence threshold (0.6+), confirmation for destructive actions, "did you mean?" disambiguation |
| llm hallucination | fabricated data or actions | strict prompt constraints, data grounding (only use provided data), output validation layer |
| prompt injection attack | unauthorized actions | input sanitization, role-based separation, rate limiting, audit all actions |
| multi-language accuracy gaps | poor experience for non-english | nlu model fine-tuned per language, fallback to english, clear error messages |
| context window overflow | lost conversation memory | sliding window, summary compression for long sessions |

## metrics & kpis

| metric | target | measurement |
|--------|--------|-------------|
| intent classification accuracy | > 95% | correct intent / total queries (eval set) |
| entity extraction f1 score | > 0.90 | precision & recall on entity labels |
| successful action execution | > 99% | successful actions / total attempted |
| user satisfaction (thumbs up/down) | > 85% positive | feedback responses |
| queries resolved without handoff | > 80% | no escalation to manual support |
| average response time | < 3s | time from query to complete response |
