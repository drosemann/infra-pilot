# AI Root Cause Analysis

feature id: 51
category: AIOps & Autonomous Operations
primary service: integration service
effort estimate: large (7-10 pt)

## Overview

ML-powered correlation of metrics, logs, traces, and events to automatically identify the root cause of incidents. Uses multiple correlation methods (time proximity, metric correlation, log pattern analysis, graph propagation, ML classifier) to rank potential root causes by confidence.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Event Sources                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Metrics │  │  Logs   │  │ Traces  │  │ Alerts  │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │
└───────┼────────────┼────────────┼─────────────┼────────┘
        ▼            ▼            ▼             ▼
┌──────────────────────────────────────────────────────┐
│           Root Cause Analyzer                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  Correlation Pipeline                          │   │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────────┐  │   │
│  │  │  Time    │ │  Metric   │ │  ML          │  │   │
│  │  │ Proximity│ │ Correlation│ │  Classifier  │  │   │
│  │  └──────────┘ └───────────┘ └──────────────┘  │   │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────────┐  │   │
│  │  │  Log     │ │  Graph    │ │  Service     │  │   │
│  │  │  Pattern │ │ Propagation│ │  Dependency  │  │   │
│  │  └──────────┘ └───────────┘ └──────────────┘  │   │
│  └────────────────────────────────────────────────┘   │
│              │                                         │
│              ▼                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  Ranked Root Causes with Confidence Scores     │   │
│  └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Key Features

- Multi-source event ingestion (metrics, logs, traces, alerts, config changes, deployments)
- Five correlation algorithms with ensemble scoring
- Service dependency graph for blast radius analysis
- Natural language explanation of findings
- Historical learning from past incidents

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/aiops/rca/events | Ingest an event |
| POST | /api/v1/aiops/rca/analyze | Analyze an incident |
| GET | /api/v1/aiops/rca/incidents | List incidents |
| GET | /api/v1/aiops/rca/incidents/{id} | Get incident details |
| POST | /api/v1/aiops/rca/dependencies | Set service dependencies |
| GET | /api/v1/aiops/rca/dependencies | Get dependency graph |

## Implementation Files

- `services/integration-service/src/aiops/root_cause_analysis.py` — Core analyzer
- `services/orchestrator-agent/cogs/aiops/root_cause_analysis.py` — Discord cog
- `services/management-panel/src/pages/aiops/RootCauseAnalysisPage.tsx` — UI page
