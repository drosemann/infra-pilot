# Feature 79: NPS & Survey Engine

## Overview
Automated NPS survey engine that sends surveys at key lifecycle moments. Customizable survey builder with response analytics, trend tracking, and closed-loop feedback.

## Components
- `nps_surveys.py` - NPS survey engine
- `cx_cogs.py` - NPSSurveysCog Discord commands

## Data Models
- `Survey` - Survey definition with questions and triggers
- `SurveyResponse` - Individual survey response
- `NPSMetric` - Aggregated NPS score and trend

## API Endpoints
- `POST /api/v1/cx/nps/surveys` - Create survey
- `GET /api/v1/cx/nps/surveys` - List surveys
- `GET /api/v1/cx/nps/surveys/{id}` - Get survey
- `POST /api/v1/cx/nps/send/{survey_id}` - Send survey
- `POST /api/v1/cx/nps/respond/{response_id}` - Submit response
- `GET /api/v1/cx/nps/score` - Get NPS score
- `GET /api/v1/cx/nps/trend` - NPS trend
- `GET /api/v1/cx/nps/detractors` - Detractor feedback
- `GET /api/v1/cx/nps/stats` - NPS statistics

## Metrics
- NPS score, response rate, promoter/passive/detractor distribution
