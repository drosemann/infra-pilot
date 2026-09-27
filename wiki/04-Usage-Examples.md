# Usage Examples

## GitOps: Infrastructure as Code

```bash
# Export current infrastructure to YAML
infra-passenger gitops export -o production.yaml

# Plan changes before applying
infra-passenger gitops plan -f production.yaml

# Apply with dry-run first
infra-passenger gitops apply -f production.yaml --dry-run
infra-passenger gitops apply -f production.yaml -y

# Scan for configuration drift
infra-passenger gitops drift --scan
```

## SSH Session Management

```bash
# Connect to a server via jump host
infra-passenger ssh connect web-01 -u admin -j bastion.corp.com

# Manage jump hosts
infra-passenger ssh jump-hosts --create bastion --host bastion.corp.com --user admin

# Add SSH key
infra-passenger ssh keys --add ~/.ssh/id_ed25519.pub --name laptop

# List active sessions
infra-passenger ssh list --status active

# View session recording
infra-passenger ssh record <session-id>

# Save a host for quick access
infra-passenger ssh saved --add prod@web-01.example.com:2222
```

## Server Inventory

```bash
# List all production servers with tags
infra-passenger inventory list --tag production

# Filter by environment and region
infra-passenger inventory list --environment staging --region eu-west

# Filter by owner and provider
infra-passenger inventory list --owner alice --provider aws

# Update server metadata
infra-passenger inventory update web-01 \
  --owner "Platform Team" \
  --environment production \
  --region us-east-1 \
  --provider aws \
  --os "Ubuntu 22.04 LTS" \
  --cost 123.50 \
  --tags "frontend,api,critical"

# Tag management
infra-passenger inventory tags --add web-01:frontend
infra-passenger inventory tags --add web-01:api
infra-passenger inventory tags --remove web-01:deprecated
infra-passenger inventory tags --list
```

## Secret Management

```bash
# Store a database URL
infra-passenger secrets set DATABASE_URL "postgresql://user:pass@host:5432/db" \
  --rotate --rotation-days 90

# Store an API key
infra-passenger secrets set STRIPE_API_KEY "sk_live_..." --rotation-days 30

# Retrieve a secret (latest version)
infra-passenger secrets get DATABASE_URL

# Retrieve a specific version
infra-passenger secrets get DATABASE_URL --version 2

# List all secrets
infra-passenger secrets list

# View version history
infra-passenger secrets versions DATABASE_URL

# Rotate a specific secret
infra-passenger secrets rotate --key DATABASE_URL

# Rotate all secrets due for rotation
infra-passenger secrets rotate --all

# RBAC: grant/revoke access
infra-passenger secrets roles DATABASE_URL --grant developer
infra-passenger secrets roles DATABASE_URL --revoke viewer
infra-passenger secrets roles DATABASE_URL
```

## Deployment Templates

```bash
# List all templates
infra-passenger templates list

# Filter by type
infra-passenger templates list --type node
infra-passenger templates list --type python

# Deploy a Node.js app
infra-passenger templates deploy nodejs my-api --server web-01

# Deploy PostgreSQL
infra-passenger templates deploy postgresql my-db

# Deploy Traefik reverse proxy
infra-passenger templates deploy traefik ingress

# Initialize a local project from template
infra-passenger templates init nodejs my-api-project -o ./apps

# Deploy with custom variables
infra-passenger templates deploy nodejs my-api \
  --server web-01 \
  --vars '{"environment_vars":{"PORT":"4000"},"ports":[{"hostPort":4000,"containerPort":4000}]}'

# Dry-run a template deployment
infra-passenger templates deploy redis cache --dry-run
```

## Webhooks

```bash
# Create a webhook for deployments
infra-passenger webhooks create deploy-notify https://hooks.example.com/deploy \
  --events deploy,backup,alert \
  --secret whsec_abc123

# List webhooks
infra-passenger webhooks list

# Test a webhook
infra-passenger webhooks test --id <id> --event deploy

# View delivery logs
infra-passenger webhooks logs
infra-passenger webhooks logs --id <id>
```

## API Keys

```bash
# Create a read-only key for CI/CD
infra-passenger apikeys create github-actions --role readonly --expire 365

# Create an admin key
infra-passenger apikeys create admin-key --role admin

# List keys
infra-passenger apikeys list

# Revoke a compromised key
infra-passenger apikeys revoke <key-id>
```

## Plugin Management

```bash
# List available plugins
infra-passenger plugins list

# Show only installed
infra-passenger plugins list --installed

# Install plugins
infra-passenger plugins install kubernetes
infra-passenger plugins install aws
infra-passenger plugins install cloudflare

# Update all plugins
infra-passenger plugins update --all

# Check for updates
infra-passenger plugins update

# Plugin info
infra-passenger plugins info docker

# Uninstall
infra-passenger plugins uninstall proxmox
```

## Developer Tools

```bash
# Run diagnostics
infra-passenger doctor doctor

# Auto-fix issues
infra-passenger doctor doctor --fix

# Verbose diagnostics
infra-passenger doctor doctor --verbose

# Benchmark local system
infra-passenger benchmark

# Benchmark a remote server
infra-passenger benchmark --server web-01

# Diagnose connectivity issues
infra-passenger diagnose --issue connectivity

# Diagnose specific server performance
infra-passenger diagnose --server web-01 --issue performance

# Disk diagnosis
infra-passenger diagnose --issue disk

# TUI dashboard
infra-passenger tui dashboard

# TUI monitor
infra-passenger tui monitor web-01

# TUI logs
infra-passenger tui logs web-01
```

## Rollback & Undo

```bash
# List recent changes
infra-passenger rollback list --limit 10

# Preview an undo
infra-passenger rollback undo <change-id> --dry-run

# Execute undo
infra-passenger rollback undo <change-id>

# Rollback a server config
infra-passenger rollback rollback server web-01 --version "2024-01-15T10:00:00Z"

# View change history for a specific resource
infra-passenger rollback history --resource server --id web-01
```

## Create a Server and View Logs

```bash
infra-passenger server create web-prod --image nginx:latest --memory 4096
infra-passenger logs fetch <id> --lines 50
```

## Backups

```bash
# Create a backup
infra-passenger backup create <id>

# Create with S3 target
infra-passenger backup create <id> --s3 my-bucket:/backups

# Schedule automated backups
infra-passenger backup schedule <id> --interval daily --retention 30

# Schedule with S3 offsite storage
infra-passenger backup schedule <id> --interval hourly --s3 my-bucket:/db-dumps

# List backups
infra-passenger backup list

# Manage snapshots
infra-passenger backup snapshots <id>
infra-passenger backup snapshots <id> --create
infra-passenger backup snapshots <id> --restore <snapshot-id>

# Restore
infra-passenger backup restore <backup-id>

# Configure S3 storage
infra-passenger backup config \
  --s3-bucket my-backups \
  --s3-key ACCESS_KEY \
  --s3-secret SECRET_KEY \
  --s3-endpoint https://s3.us-east-1.amazonaws.com
```

## Global Search

```bash
# Available via API:
# GET /api/global-search?q=<query>
# Searches across: apps, servers, backups, runbooks, secrets, hosts
```

---

*See [CLI Reference](05-CLI-Reference) for all available commands.*
