# Feature 20: Developer Pulse

## Overview
NPS-style developer satisfaction survey engine with configurable questions, anonymous response collection, sentiment analysis, and trend tracking.

## Components
- `developer_pulse.py` - Survey engine with NPS scoring
- `pulse_cog.py` - Discord bot commands for surveys

## Data Models
- `PulseSurvey` - Survey definition with questions
- `PulseResponse` - Individual response with answers
- `PulseTrend` - Sentiment trend tracking over time

## Features
- Configurable survey questions (rating, text, multiple choice)
- NPS scoring with promoter/passive/detractor classification
- Anonymous response support
- Sentiment trend analysis over time

## CLI Commands
- `ipilot pulse list` - List surveys
- `ipilot pulse create` - Create survey
- `ipilot pulse respond` - Submit response
- `ipilot pulse results` - Get survey results
- `ipilot pulse summary` - NPS and response stats
