# Feature 18: API Catalog

## Overview
Centralized API registry with OpenAPI specification ingestion, endpoint discovery, and breaking change detection between versions.

## Components
- `api_catalog.py` - API catalog manager with spec parsing
- `api_catalog_cog.py` - Discord bot commands for API catalog

## Data Models
- `APIDefinition` - API metadata with OpenAPI spec
- `APIEndpoint` - Parsed endpoint definition
- `BreakingChange` - Detected breaking change record

## Features
- OpenAPI 3.x spec ingestion and validation
- Automatic endpoint extraction
- Version comparison with breaking change detection
- Endpoint search by path, method, or tag

## CLI Commands
- `ipilot api-catalog list` - List APIs
- `ipilot api-catalog register` - Register from spec file
- `ipilot api-catalog get` - Get API details
- `ipilot api-catalog summary` - Catalog statistics
