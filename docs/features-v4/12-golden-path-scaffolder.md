# Feature 12: Golden Path Scaffolder

## Overview
Template-driven project scaffolding tool that guides developers through opinionated "golden path" workflows for creating new services, APIs, libraries, and pipelines.

## Components
- `golden_path_scaffolder.py` - Scaffolding engine with step-based generation
- `scaffolder_cog.py` - Discord bot commands

## Data Models
- `GoldenPathTemplate` - Template definition with steps and parameter schema
- `ScaffoldGeneration` - Generation instance tracking progress
- `ScaffoldStep` - Individual step within a generation

## Built-in Templates
1. **microservice** - Python FastAPI microservice
2. **api-gateway** - API gateway with routing
3. **data-pipeline** - ETL data pipeline
4. **frontend-app** - React frontend application

## CLI Commands
- `ipilot scaffold list` - List templates
- `ipilot scaffold generate` - Generate from template
- `ipilot scaffold status` - Check generation status
- `ipilot scaffold step` - Complete a step

## Discord Commands
- `/scaffold list` - List templates
- `/scaffold generate` - Start generation
- `/scaffold status` - Check progress
