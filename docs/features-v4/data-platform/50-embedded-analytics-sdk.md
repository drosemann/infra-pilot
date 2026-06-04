# Feature 50: Embedded Analytics SDK

## Overview
White-label analytics embedding platform with iframe/widget SDKs, customer management, API key authentication, and usage tracking for multi-tenant deployments.

## Components
- `embedded_analytics.py` - Customer and embed management with SDK code generation
- `cog_embedded_analytics.py` - Discord bot commands for embed operations

## Data Models
- EmbedCustomer - Customer with name, domain, api_key, active status, embed count
- EmbedConfig - Embed config with type (dashboard/report/widget), customer reference, filters, theme
- EmbedCode - Generated SDK snippet (iframe/React/Vanilla JS)
- EmbedStats - Aggregate stats on customers, embeds, and usage

## API Endpoints
- `GET /api/v4/data/embed/customers` - List customers
- `POST /api/v4/data/embed/customers` - Create customer
- `POST /api/v4/data/embed/customers/:id/rotate-key` - Rotate API key
- `GET /api/v4/data/embed/embeds` - List embeds
- `POST /api/v4/data/embed/embeds` - Create embed
- `GET /api/v4/data/embed/embeds/:id/code` - Get embed code
- `DELETE /api/v4/data/embed/embeds/:id` - Delete embed
- `GET /api/v4/data/embed/stats` - Embed statistics
- `DELETE /api/v4/data/embed/customers/:id` - Delete customer

## Metrics
- Total customers and embeds
- Active vs inactive customers
- SDK code generation requests

## Discord Commands
- `/embed list-customers` - List embed customers
- `/embed create-customer` - Register customer
- `/embed rotate-key` - Rotate API key
- `/embed list-embeds` - List embeds
- `/embed create-embed` - Create embed
- `/embed get-code` - Get embed code
- `/embed stats` - Embed statistics
