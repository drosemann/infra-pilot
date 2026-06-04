# Feature 43: Data Quality Framework

## Overview
Automated data quality monitoring with configurable rules, scheduled validations, violation tracking, and dataset scorecards.

## Components
- `data_quality.py` - Quality rule management with validation execution
- `cog_data_quality.py` - Discord bot commands for quality operations

## Data Models
- QualityRule - Rule with name, dataset, column, check type (null/unique/range/regex/custom), threshold, severity
- Violation - Violation record with rule reference, dataset, timestamp, actual value, severity
- Scorecard - Dataset quality score with passing/failing counts

## API Endpoints
- `GET /api/v4/data/quality/rules` - List rules
- `POST /api/v4/data/quality/rules` - Create rule
- `POST /api/v4/data/quality/run` - Execute validation
- `GET /api/v4/data/quality/violations` - List violations
- `GET /api/v4/data/quality/scorecard/:dataset` - Dataset scorecard

## Metrics
- Total rules defined
- Pass rate percentage
- Open violations by severity

## Discord Commands
- `/quality list-rules` - List quality rules
- `/quality create-rule` - Create new rule
- `/quality run` - Execute validation
- `/quality violations` - View violations
- `/quality scorecard` - Dataset scorecard
