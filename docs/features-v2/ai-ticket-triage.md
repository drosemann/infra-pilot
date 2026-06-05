# ai ticket triage

| field | value |
|-------|-------|
| id | f-009 |
| name | ai ticket triage |
| category | ai & intelligence |
| primary service | integration service |
| effort | medium (4-6 pt) |
| dependencies | feature 13 (webhook event bus), knowledge base (feature 32) |
| phase | phase 1 |

## overview

the ai ticket triage system automatically classifies incoming support tickets by urgency, category, and affected service. it searches the knowledge base for matching solutions, scores confidence levels, and routes the ticket to the appropriate team -- all before a human ever reads it. over time, the system learns from human feedback to improve classification accuracy.

### goals

- classify 90%+ of incoming tickets within 5 seconds
- auto-suggest solutions from knowledge base with >=80% match rate
- route tickets to correct team with 95%+ accuracy
- reduce first-response time from hours to seconds

### non-goals

- not a full ticketing system (integrates with existing platforms)
- does not auto-close or auto-resolve tickets (human-in-the-loop)
- not a chatbot -- does not engage in conversational support
- does not replace tier-1 support for complex issues

## architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Ticket Sources (External)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ Zendesk  │  │ Freshdesk│  │ Discord  │  │ Email    │  │ Panel │ │
│  │ Webhook  │  │ Webhook  │  │ Ticket   │  │ Intake   │  │ Form  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬───┘ │
└───────┼──────────────┼─────────────┼──────────────┼────────────┼─────┘
        │              │             │              │            │
        ▼              ▼             ▼              ▼            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Integration Service (Primary)                    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    Ticket Ingestion Pipeline                   │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │      │
│  │  │ Normalize│  │ Dedupe   │  │ Enrich   │  │ Queue      │ │      │
│  │  │ Adapter  │  │ Check    │  │ (user +  │  │ (RabbitMQ/ │ │      │
│  │  │          │  │          │  │  server) │  │  Redis)    │ │      │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │      │
│  └────────────────────────────────────────────────────────────┘      │
│                              │                                        │
│                              ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    Classification Pipeline                     │      │
│  │                                                              │      │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │      │
│  │  │ Category         │  │ Urgency Score    │  │ Affected   │ │      │
│  │  │ Classifier       │  │ Calculator       │  │ Service    │ │      │
│  │  │                  │  │                  │  │ Detector   │ │      │
│  │  │ - Text model     │  │ - Keywords       │  │ - Entity   │ │      │
│  │  │ - Embedding      │  │ - Sentiment      │  │   extract  │ │      │
│  │  │   similarity     │  │ - Customer tier  │  │ - Config   │ │      │
│  │  │ - LLM few-shot   │  │ - Repetition     │  │   refs     │ │      │
│  │  └────────┬─────────┘  │ - Escalation     │  │ - Log refs │ │      │
│  │           │            │   history        │  └────────────┘ │      │
│  │           │            └────────┬─────────┘                  │      │
│  │           ▼                    ▼                             │      │
│  │  ┌──────────────────────────────────────────────────────┐   │      │
│  │  │           Knowledge Base Matcher                      │   │      │
│  │  │  ┌────────────────┐  ┌────────────────┐  ┌─────────┐ │   │      │
│  │  │  │ Semantic       │  │ Solution       │  │ Keyword │ │   │      │
│  │  │  │ Search         │  │ Confidence     │  │ Match   │ │   │      │
│  │  │  │ (vector)       │  │ Scorer         │  │ (BM25)  │ │   │      │
│  │  │  └────────────────┘  └────────────────┘  └─────────┘ │   │      │
│  │  └──────────────────────────────────────────────────────┘   │      │
│  └────────────────────────────────────────────────────────────┘      │
│                              │                                        │
│                              ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                    Routing & Action Engine                     │      │
│  │                                                              │      │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │      │
│  │  │ Team Router      │  │ Escalation       │  │ Auto-Reply │ │      │
│  │  │                  │  │ Engine           │  │ Generator  │ │      │
│  │  │ - Skill-based    │  │ - SLA timeline   │  │ - Solution  │ │      │
│  │  │ - Round-robin    │  │ - Severity map   │  │   snippet  │ │      │
│  │  │ - Capacity-aware │  │ - Paging rules   │  │ - KB link  │ │      │
│  │  └────────┬─────────┘  └────────┬─────────┘  └──────┬─────┘ │      │
│  └───────────┼─────────────────────┼────────────────────┼────────┘      │
│              │                     │                    │               │
└──────────────┼─────────────────────┼────────────────────┼───────────────┘
               │                     │                    │
               ▼                     ▼                    ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ Ticket Platform  │  │ Discord / Slack      │  │ Management Panel     │
│ (updated with    │  │ (team notification)  │  │ (Ticket dashboard)   │
│  classification)  │  │                      │  │                      │
└──────────────────┘  └──────────────────────┘  └──────────────────────┘
```

### processing flow

```
New Ticket ──► Normalize to unified schema
                  │
                  ▼
             Deduplication check
                  │
                  ├──► Exact/close match found -> Link to existing ticket
                  │
                  ▼
             Enrich (fetch user tier, server info, recent activity)
                  │
                  ▼
             Classification Pipeline (parallel)
                  │
                  ├──► Category -> "performance", "security", "billing", etc.
                  ├──► Urgency -> 1-10 score
                  ├──► Affected service -> "minecraft", "proxy", "backup", etc.
                  │
                  ▼
             Knowledge Base Search
                  │
                  ├──► Top 3 KB articles with relevance scores
                  │
                  ▼
             Routing Decision
                  │
                  ├──► Team assignment
                  ├──► Auto-reply with KB links (if confidence >0.85)
                  ├──► Escalation if urgency >= 8
                  │
                  ▼
             Update external ticket system + notify team
```

## implementation plan

### phase 1: ingestion & normalization (week 1, 1.0 pt)

1. **unified ticket schema**
   - normalize fields from zendesk, freshdesk, discord, email, panel form
   - store: subject, body, attachments, user info, metadata, custom fields

2. **ingestion adapters**
   - webhook receiver for each platform
   - email ingestion via imap/pop3
   - discord bot command (`/ticket` -> creates ticket via webhook)

3. **deduplication engine**
   - exact body hash matching
   - near-duplicate detection via text similarity (cosine >0.9)
   - customer + subject + timeframe grouping

4. **enrichment layer**
   - fetch customer tier, server assignments, recent changes
   - pull recent alerts/incidents for affected servers
   - check open tickets from same customer

### phase 2: classification pipeline (week 1-2, 2.0 pt)

1. **category classifier**
   - ml model (fine-tuned bert or distilbert)
   - 12 default categories (expandable):
     - performance / lag
     - server crash
     - connection issue
     - plugin / mod problem
     - billing / invoice
     - account / authentication
     - backup / restore
     - security / compromise
     - configuration help
     - world / data issue
     - feature request
     - other
   - confidence threshold: 0.70 for auto-classify, else queue for manual

2. **urgency score calculator**
   - weighted scoring algorithm:

   | Factor | Weight | Description |
   |--------|--------|-------------|
   | Keywords | 0.30 | "crash", "down", "emergency", "lost data" -> +3 |
   | Sentiment | 0.15 | Negative sentiment -> +1 to +3 |
   | Customer tier | 0.15 | Enterprise tier -> +1, VIP -> +2 |
   | Repetition | 0.10 | Same issue 3+ times -> +2 |
   | Escalation history | 0.10 | Previously escalated -> +1 |
   | Affected scope | 0.10 | "all players" vs "my" -> +0 to +2 |
   | Server status | 0.10 | Server currently down -> +3 |

   - score 1-10: 1-3 (low), 4-6 (medium), 7-8 (high), 9-10 (critical)

3. **affected service detector**
   - entity extraction from ticket text
   - server name patterns, service keywords
   - model fine-tuned on minecraft server terminology

### phase 3: knowledge base matching & routing (week 2-3, 1.5 pt)

1. **knowledge base matcher**
   - dual retrieval: bm25 (keyword) + vector (semantic)
   - re-ranking with cross-encoder model
   - 3 result tiers:
     - tier 1: score >=0.90 -> direct match, auto-suggest
     - tier 2: score >=0.70 -> suggest with confidence note
     - tier 3: score <0.70 -> no auto-suggestion

2. **auto-reply generator**
   - if kb match confidence >=0.85:
     - generate reply with kb article title, link, and relevant excerpt
     - add "did this solve your problem?" buttons
   - if urgency >=8: skip auto-reply, immediately escalate

3. **routing engine**
   - skills-based routing matrix:

   | Category | Primary Team | Secondary Team |
   |----------|-------------|----------------|
   | Performance | Infrastructure | Game Ops |
   | Server Crash | Game Ops | Infrastructure |
   | Connection | Network | Infrastructure |
   | Plugin | Game Ops | Dev Support |
   | Billing | Finance | Customer Success |
   | Account | Customer Success | Security |
   | Backup | Infrastructure | Game Ops |
   | Security | Security | Infrastructure |
   | Configuration | Game Ops | Customer Success |
   | World/Data | Game Ops | Infrastructure |

   - round-robin within team
   - capacity-aware routing (avoid overloaded agents)

### phase 4: feedback loop & analytics (week 3-4, 1.0 pt)

1. **human feedback collection**
   - "was this classification correct?" buttons in panel
   - agent re-classification audit trail
   - weekly accuracy reports

2. **model retraining pipeline**
   - weekly fine-tuning on corrected classifications
   - a/b testing for model versions
   - drift detection (accuracy drop >5% triggers retrain)

3. **analytics dashboard**
   - classification accuracy over time
   - auto-suggestion acceptance rate
   - average time-to-classify
   - backlog by category/urgency
   - team workload distribution

## api design

### endpoints

all endpoints are prefixed with `/api/v2/ticket-triage`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tickets` | Ingest a new ticket from any source |
| `GET`  | `/tickets/{ticketId}` | Get ticket with classification |
| `PATCH`| `/tickets/{ticketId}` | Update ticket (reclassify, reassign) |
| `POST` | `/tickets/{ticketId}/feedback` | Submit classification feedback |
| `POST` | `/tickets/{ticketId}/reclassify` | Force re-classification |
| `GET`  | `/tickets/{ticketId}/suggestions` | Get KB suggestions for ticket |
| `GET`  | `/categories` | List available categories |
| `POST` | `/train` | Trigger model retraining |
| `GET`  | `/stats` | Classification accuracy & performance stats |
| `GET`  | `/routing/matrix` | Get current routing matrix |

### request/response examples

**POST /api/v2/ticket-triage/tickets**

```json
{
  "source": "zendesk",
  "external_id": "zd-123456",
  "subject": "Server keeps crashing after latest update",
  "body": "After updating to Paper 1.21.3, my server crashes every 10-15 minutes. The error mentions 'java.lang.OutOfMemoryError'. I have 8GB RAM allocated but it still crashes. This affects all 50+ players on my network.\n\nServer: mc.myhosting.com\nPrevious version: 1.20.6 (stable)\nPlugins: 24 installed\nPlayers: 50-80 concurrent",
  "attachments": [
    "https://example.zendesk.com/attachments/crash-report-123.log"
  ],
  "customer": {
    "id": "cust_abc123",
    "email": "admin@example.com",
    "tier": "enterprise",
    "server_ids": ["srv-mc-42", "srv-mc-43"]
  },
  "metadata": {
    "submitted_via": "web_form",
    "priority": "high"
  }
}
```

**response**

```json
{
  "ticket_id": "tkt-20260527-xyz789",
  "external_id": "zd-123456",
  "status": "processed",
  "classification": {
    "category": {
      "primary": "server_crash",
      "secondary": "performance",
      "confidence": 0.94,
      "model_version": "bert-ticket-v2.3"
    },
    "urgency": {
      "score": 8.2,
      "level": "high",
      "factors": {
        "keywords": 3,
        "affected_scope": 2,
        "customer_tier": 1,
        "sentiment": 1.2,
        "repetition": 1
      }
    },
    "affected_service": {
      "primary": "minecraft",
      "confidence": 0.97
    },
    "language": "en",
    "processed_at": "2026-05-27T14:30:00.123Z",
    "processing_time_ms": 3400
  },
  "kb_suggestions": [
    {
      "article_id": "kb-042",
      "title": "Paper 1.21 OutOfMemoryError: Fixes & Workarounds",
      "url": "https://docs.infrapilot.dev/kb/paper-oom-fixes",
      "relevance_score": 0.92,
      "excerpt": "After upgrading to Paper 1.21, many servers experience OOM errors due to increased memory pressure. Recommended: increase -Xmx by 25%, enable Aikar's flags, and disable unused world generation features.",
      "match_type": "semantic"
    },
    {
      "article_id": "kb-031",
      "title": "JVM Flags Optimization for Minecraft Servers",
      "url": "https://docs.infrapilot.dev/kb/jvm-flags",
      "relevance_score": 0.78,
      "excerpt": "Proper JVM flags can reduce memory pressure significantly. Aikar's recommended flags: -Xms -Xmx -XX:+UseG1GC -XX:+ParallelRefProcEnabled...",
      "match_type": "keyword"
    }
  ],
  "routing": {
    "assigned_team": "game_ops",
    "assigned_agent": "agent_sarah",
    "routing_reason": "primary_category",
    "sla_deadline": "2026-05-27T16:30:00Z"
  },
  "auto_reply": {
    "sent": true,
    "content": "Hello,\n\nThank you for your report. Based on the error description, this appears to be a known issue with Paper 1.21 memory allocation.\n\n**Suggested Solution:**\nPlease review this article: Paper 1.21 OutOfMemoryError: Fixes & Workarounds\nhttps://docs.infrapilot.dev/kb/paper-oom-fixes\n\nIf this does not resolve your issue, our Game Operations team has been notified and will follow up within 2 hours.\n\nBest,\nInfra Pilot AI Support",
    "confidence": 0.92
  }
}
```

## data model

```yaml
Ticket:
  id: string (UUID)
  source: string
  external_id: string
  subject: string
  body: string
  body_clean: string
  attachments: Attachment[]
  customer: Customer
  metadata: dict
  status: "new" | "processing" | "classified" | "routed" | "resolved" | "closed"
  classification: Classification | null
  routing: Routing | null
  auto_reply: AutoReply | null
  feedback: Feedback | null
  created_at: datetime
  processed_at: datetime | null
  resolved_at: datetime | null

Classification:
  category: CategoryAssignment
  urgency: UrgencyScore
  affected_service: ServiceAssignment
  language: string
  model_version: string
  processing_time_ms: integer

CategoryAssignment:
  primary: string
  secondary: string | null
  confidence: float

UrgencyScore:
  score: float
  level: "low" | "medium" | "high" | "critical"
  factors: dict

ServiceAssignment:
  primary: string
  confidence: float

Routing:
  assigned_team: string
  assigned_agent: string | null
  routing_reason: string
  sla_deadline: datetime

AutoReply:
  sent: boolean
  content: string
  confidence: float
  kb_articles: string[]

Feedback:
  correct: boolean | null
  corrected_category: string | null
  corrected_urgency: integer | null
  rated_by: string
  rated_at: datetime
  notes: string | null

KBArticle:
  id: string
  title: string
  body: string
  url: string
  category: string
  tags: string[]
  embedding: float[]
  keywords: string[]
  embedding_model: string
  last_updated: datetime

CategoryModel:
  id: string
  name: string
  parent: string | null
  keywords: string[]
  routing_team: string
  routing_secondary: string | null
  sla_minutes: integer
  is_active: boolean
```

## service assignments

| Service | Responsibility |
|---------|---------------|
| integration service | primary: ingestion, classification pipeline, kb matching, routing, auto-reply |
| management panel | secondary: ticket dashboard, feedback ui, analytics, routing configuration |
| discord service | secondary: discord ticket intake, team notifications |
| service core | none directly; authentication, customer lookup, server info enrichment |

## effort estimate

| Phase | Task | PT | Owner |
|-------|------|----|-------|
| P1 | Unified ticket schema + ingestion adapters | 0.5 | Backend |
| P1 | Deduplication engine | 0.25 | Backend |
| P1 | Enrichment layer | 0.25 | Backend |
| P2 | Category classifier (ML model + training) | 1.0 | ML/Backend |
| P2 | Urgency scoring engine | 0.5 | Backend |
| P2 | Affected service detector | 0.5 | ML/Backend |
| P3 | KB matcher (BM25 + vector search) | 0.75 | Backend |
| P3 | Routing engine + SLA tracking | 0.5 | Backend |
| P3 | Auto-reply generator | 0.25 | Backend |
| P4 | Feedback collection + analytics dashboard | 0.5 | Frontend+Backend |
| P4 | Model retraining pipeline | 0.25 | ML |
| total | | 5.25 pt | |

## risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low accuracy on novel/unseen issues | medium | fallback to manual classification; confidence threshold with human-in-the-loop |
| pii/sensitive data in tickets | high | strip emails, ips, passwords before ml processing; data retention controls |
| integration platform api changes | medium | adapter pattern with versioned schemas; webhook health monitoring |
| bias in urgency scoring (vip vs standard) | medium | transparent scoring factors; audit trail; regular bias testing |
| kb depends on feature 32 (knowledge base) | medium | v1 ships with bundled kb articles; integration with external kb in v2 |
| multi-language support | medium | v1 english-only; language detection for routing to bilingual agents |

## category taxonomy (v1)

```
ticket_category:
  - performance:
      keywords: [lag, tps, mspt, tick, slow, stutter, freeze, latency, ping]
  - server_crash:
      keywords: [crash, oom, outofmemory, segfault, panic, restart loop, kernel]
  - connection:
      keywords: [cant connect, timeout, refused, dns, firewall, port, auth fail]
  - plugin_mod:
      keywords: [plugin, mod, datapack, incompatible, error, conflict, version]
  - billing:
      keywords: [invoice, payment, refund, upgrade, downgrade, coupon, credit]
  - account:
      keywords: [login, password, 2fa, mfa, reset, locked, suspended, verify]
  - backup:
      keywords: [backup, restore, rollback, snapshot, corrupted, missing data]
  - security:
      keywords: [hacked, griefed, exploit, vulnerability, breach, unauthorized]
  - configuration:
      keywords: [config, setup, settings, properties, yml, yaml, env, options]
  - world_data:
      keywords: [world, map, chunk, region, schematic, schematica, worldedit]
  - feature_request:
      keywords: [suggestion, feature, request, roadmap, idea, would like]
  - other:
      keywords: []
```

## future enhancements

- v2.0: multi-language ticket classification
- v2.1: agent assist -- real-time suggestions while typing reply
- v2.2: sentiment trend analysis across customer lifecycle
- v2.3: integration with jira, linear, github issues
- v2.4: automated solution execution (kb article -> runbook -> fix)
- v2.5: customer satisfaction prediction and proactive outreach
