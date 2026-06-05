# Feature 90: Discord Report Bot

## Overview
Scheduled report delivery bot for Discord. Supports 6 report types with cron-based scheduling and interactive button controls.

## Commands
- `/report send` - send a report to the channel immediately
- `/report digest` - send infrastructure digest (daily/weekly/monthly)
- `/report schedule` - create a scheduled report
- `/report list` - list active schedules
- `/report delete` - remove a schedule

## Report Types
- Executive Summary: high-level infrastructure overview
- Cost Report: spending breakdown and trends
- Performance Report: system performance metrics
- Incident Report: recent incidents and resolution
- Anomaly Digest: detected anomalies in time series
- Capacity Forecast: resource prediction

## Buttons
- Refresh: regenerate the report
- Export: download as file (JSON/CSV)
- View: show full details in thread

## Data Model
Schedule: { id, guildId, channelId, type, cron, enabled, createdAt }
