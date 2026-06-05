# Feature 93: Low-Code Connector Builder

## Overview
Visual pipeline builder for creating integrations without code. Supports HTTP requests, data transforms, conditionals, and authentication nodes.

## Node Types
- HTTP Request: GET/POST/PUT/DELETE with headers and body
- Transform: JSONata/JQ expression mapping
- Conditional: if/else branching logic
- Auth: OAuth2, API key, Basic Auth credential injection

## Features
- Topological pipeline execution engine
- Visual node editor with drag-and-drop
- 3 starter templates: webhook relay, data sync, alert routing
- Execution logs and error handling
- Test mode with sample data

## Backend API
- `POST /api/v1/connectors/execute` - run a pipeline
- `GET /api/v1/connectors/templates` - list starter templates
- `POST /api/v1/connectors/validate` - validate pipeline config
- `GET /api/v1/connectors/logs/:executionId` - execution logs
