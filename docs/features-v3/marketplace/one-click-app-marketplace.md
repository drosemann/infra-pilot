# Feature 32: One-Click App Marketplace

## Overview
Curated marketplace with 100+ applications (WordPress, Nextcloud, Minecraft, GitLab, Jellyfin, etc.). Automated deployment via Docker Compose, configuration wizards, one-click updates.

## Components

### Integration Service: `marketplace/app_marketplace.py`
- `AppMarketplaceManager` - Core app marketplace
  - App catalog management (versioning, categories)
  - App deployment engine (Docker Compose generator)
  - Configuration wizard framework
  - Update management (one-click updates)
  - Resource requirement estimation
  - App dependency resolution
  - Backup/recovery for apps

### Management Panel: `pages/marketplace/MarketplacePage.tsx` (enhance existing)
- App catalog browser with categories
- App detail view with screenshots
- One-click deploy button
- Configuration wizard
- My installed apps dashboard
- Update notifications
- Resource usage per app

### CLI Commands
- `ipilot app search <query>`
- `ipilot app install <app_name>`
- `ipilot app list`
- `ipilot app update <app_id>`
- `ipilot app remove <app_id>`

## API Endpoints
- `GET /api/marketplace/apps` - List apps
- `GET /api/marketplace/apps/{id}` - App details
- `POST /api/marketplace/apps/{id}/deploy` - Deploy app
- `GET /api/marketplace/apps/{id}/config` - Get config schema
- `POST /api/marketplace/apps/{id}/validate` - Validate config
- `GET /api/marketplace/installed` - List installed apps
- `GET /api/marketplace/installed/{id}` - Installed app details
- `PUT /api/marketplace/installed/{id}/update` - Update app
- `DELETE /api/marketplace/installed/{id}` - Uninstall app
- `GET /api/marketplace/categories` - List categories

## Data Models

### MarketplaceApp
- id, name, slug, description, summary
- version, app_type (docker/compose/helm)
- categories list, tags list
- icon_url, screenshots list
- website_url, source_url, docs_url
- min_cpu, min_ram_mb, min_disk_gb
- ports list (container ports)
- dependencies list (app IDs)
- config_schema (JSON Schema)
- docker_compose_template, env_template
- is_verified, downloads_count, rating

### InstalledApp
- id, user_id, app_id, app_name
- status (deploying/running/stopped/updating/error)
- version_installed, version_available
- config (JSON of user's config)
- resource_usage (cpu/ram/disk)
- url (access URL)
- deployed_at, updated_at

## Implementation Details
- Docker Compose generation from templates
- Jinja2 templating for config substitution
- Environment variable management
- Port allocation (avoiding conflicts)
- Volume management for persistence
- Health check after deployment
- Version tracking and update mechanism
- Dependency resolution (install prerequisites first)
- Resource requirement calculation
- App uninstall with data cleanup option
- Backup before update

## Testing
- App catalog CRUD
- Deployment generation for each app type
- Configuration validation against schema
- Update mechanism
- Dependency resolution
- Resource estimation accuracy
- Install/uninstall lifecycle
