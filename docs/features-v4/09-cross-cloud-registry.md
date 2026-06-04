# Feature 9: Cross-Cloud Container Registry

## Overview
Replicate container images across all cloud registries simultaneously. Pull-through cache per region. Vulnerability scan across all copies.

## Components
- `registry_replication.py` — Image replicator, pull-through cache
- `RegistryReplicationCog` — Discord commands for registry
- `ContainerRegistry.tsx` — React registry replication viewer
- CLI commands in `cli/ipilot/commands/hybrid_cloud/registry_replication.py`

## API Endpoints
- `GET /api/registry/images` — List images
- `POST /api/registry/images` — Register image
- `POST /api/registry/images/:id/scan` — Scan for vulnerabilities
- `POST /api/registry/images/:id/replicate` — Replicate image
- `GET /api/registry/rules` — List replication rules
- `POST /api/registry/rules` — Create rule
- `GET /api/registry/registries` — List registries

## Supported Registries
AWS ECR, Azure ACR, GCP GCR, GCP Artifact Registry, Docker Hub, GHCR, GitLab, Hetzner, OVH, DigitalOcean
