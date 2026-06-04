# Feature 15: Template Registry

## Overview
Versioned blueprint and template library with parameter validation, usage tracking, and categorization for infrastructure and application patterns.

## Components
- `template_registry.py` - Template registry manager with versioning
- `template_registry_cog.py` - Discord bot commands

## Data Models
- `Template` - Blueprint template with metadata
- `TemplateVersion` - Versioned template definition
- `ParameterSchema` - Parameter validation rules

## Features
- Versioning with automatic increment
- Usage tracking per template
- Parameter schema validation
- Category-based organization

## CLI Commands
- `ipilot template-registry list` - List templates
- `ipilot template-registry create` - Create template
- `ipilot template-registry get` - Get template
- `ipilot template-registry use` - Record usage
- `ipilot template-registry summary` - Summary stats
