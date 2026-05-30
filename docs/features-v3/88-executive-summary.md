# Feature 88: Executive Summary Generator

## Overview
Automated narrative report generation for weekly/monthly infrastructure summaries with structured data ingestion and formatted output.

## Report Types
- Weekly Summary: uptime, incidents, costs, performance
- Monthly Summary: trends, capacity, budget comparison
- Custom templates with configurable sections

## Components
- Narrative generation engine with template system
- Data aggregation from multiple sources
- Markdown and HTML output formats
- Scheduling via cron expressions
- Delivery to email, webhook, or Discord

## Backend API
- `POST /api/v1/summary/generate` - generate a summary
- `GET /api/v1/summary/templates` - list templates
- `POST /api/v1/summary/schedule` - schedule generation
- `GET /api/v1/summary/history` - past summaries
