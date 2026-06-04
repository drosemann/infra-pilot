# Change Risk Analysis

feature id: 58
category: AIOps & Autonomous Operations
primary service: integration service
effort estimate: medium (4-6 pt)

## Overview

Analyzes planned changes against historical data to predict risk. Computes similarity to past changes, evaluates risk factors (change type, blast radius, historical failure rate, time of day, data integrity), and generates actionable recommendations.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              Change Request                            │
│  Type │ Target │ Components │ Metadata │ Schedule      │
└──────────────────────┬───────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────┐
│           Change Risk Analyzer                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  Similarity Engine                             │   │
│  │  • Type similarity (30%)                       │   │
│  │  • Service similarity (30%)                    │   │
│  │  • Component overlap (20%)                     │   │
│  │  • Text similarity (20%)                       │   │
│  └────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────┐   │
│  │  Risk Factor Evaluation                        │   │
│  │  • Change type baseline risk                   │   │
│  │  • Blast radius (component count)              │   │
│  │  • Historical failure rate                     │   │
│  │  • Time of day (off-hours penalty)             │   │
│  │  • Data integrity risk                         │   │
│  │  • Rollback plan (mitigation)                  │   │
│  │  • Pre-testing (mitigation)                    │   │
│  └────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────┐   │
│  │  Risk Classification                           │   │
│  │  • Critical (≥0.9) → Blocking                  │   │
│  │  • High (≥0.7) → Requires senior approval      │   │
│  │  • Medium (≥0.4) → Peer review                 │   │
│  │  • Low (≥0.2) → Standard process              │   │
│  │  • Negligible (<0.2) → Auto-approve           │   │
│  └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Key Features

- Historical similarity matching (90-day lookback)
- 7 risk factors with weighted scoring
- 5-tier risk classification
- Automated recommendations for each risk level
- Similar incident identification
- Rollback plan and pre-testing mitigation credit
