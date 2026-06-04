# Feature 14: Scorecards & DORA Metrics

## Overview
Engineering scorecard system tracking DORA metrics (Deploy Frequency, Lead Time, MTTR, Change Failure Rate) and custom scoring rubrics for team performance evaluation.

## Components
- `scorecards.py` - Scorecard and DORA metrics engine
- `scorecards_cog.py` - Discord bot commands

## Data Models
- `Scorecard` - Scorecard definition with metrics
- `DORAMetrics` - Deploy frequency, lead time, MTTR, change failure rate
- `ScoreEntry` - Individual scoring entry

## DORA Metrics
- **Deploy Frequency** - How often deployments occur
- **Lead Time** - Time from commit to production
- **MTTR** - Mean time to recover from failures
- **Change Failure Rate** - Percentage of changes causing failures

## CLI Commands
- `ipilot scorecards list` - List scorecards
- `ipilot scorecards create` - Create scorecard
- `ipilot scorecards get` - Get details with DORA metrics
- `ipilot scorecards update` - Update a metric value
- `ipilot scorecards summary` - Aggregate summary
