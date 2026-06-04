# Conversational Ops Assistant

feature id: 57
category: AIOps & Autonomous Operations
primary service: orchestrator agent
effort estimate: medium (4-6 pt)

## Overview

Natural language interface for operations that understands intents like status checks, deployments, restarts, scaling, log viewing, and more. Supports Slack/Discord/Web UI channels with session management and conversation history.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 User Interfaces                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Web UI  │  │  Discord │  │  Slack   │  ...       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
└───────┼──────────────┼────────────┼───────────────────┘
        ▼              ▼            ▼
┌──────────────────────────────────────────────────────┐
│          Conversational Ops Assistant                  │
│  ┌────────────────────────────────────────────────┐   │
│  │  NLP Intent Engine                             │   │
│  │  • Regex-based intent extraction               │   │
│  │  • Parameter extraction (resource, version,    │   │
│  │    target, replicas)                           │   │
│  │  • Confidence scoring (high/medium/low)        │   │
│  └────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────┐   │
│  │  Intent Handlers                               │   │
│  │  • status_check → query service status         │   │
│  │  • deploy → deploy version to environment      │   │
│  │  • restart → restart service                   │   │
│  │  • scale → adjust replicas                     │   │
│  │  • logs → fetch service logs                   │   │
│  │  • metrics → show resource metrics             │   │
│  │  • backup → create backup                      │   │
│  │  • config → show configuration                 │   │
│  │  • list_resources → enumerate services         │   │
│  └────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────┐   │
│  │  Session Manager                               │   │
│  │  • Per-user conversation state                 │   │
│  │  • Context retention across messages           │   │
│  │  • Session timeout (configurable)              │   │
│  └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Key Features

- 10 supported intent types with regex extraction
- Multi-channel support (Web, Discord, Slack)
- Session management with context retention
- Confidence-based response quality
- Conversation history for audit
- Quick-reply suggestions
