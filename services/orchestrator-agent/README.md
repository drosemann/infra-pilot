# Infra Pilot - Orchestrator Agent

## Features

### Core VPS Management
- Create, start, stop, restart, delete VPS instances via Docker SDK
- Resource monitoring with MySQL persistence
- Pricing and billing system with player_economy integration
- Monthly billing cycle with grace periods

### VPS Bot Features

#### Resource Management
- **Resource usage graphs** - `/vpsgraph` - Time-series graphs (CPU, RAM, disk, network) using matplotlib
- **Server health checks** - `/health`, `/healthcreate` - Ping, port, process, API health monitoring with alerts
- **Auto scaling** - `/scalerule`, `/scaleset` - Automatic resource scaling based on usage thresholds
- **Backup rotation** - `/backup`, `/backuplist`, `/restore` - Configurable retention (daily/weekly/monthly)
- **Snapshots** - `/snapshotcreate`, `/snapshotlist`, `/snapshotrestore` - Point-in-time snapshots
- **Clone system** - `/clone` - Clone VPS with OS + data via Docker commit
- **Server migration** - `/migrate` - Migrate VPS between hosts (live/cold)

#### Advanced Features
- **Cost prediction** - `/costpredict` - Analyze usage trends, predict next month costs
- **Performance optimizer** - `/optimize`, `/optimizeapply` - Suggest CPU/RAM/disk tuning
- **Resource pools** - `/resourcepoolcreate/delete/list/add` - Track oversubscription ratios
- **Network monitoring** - `/networkstats`, `/networklatency` - Bandwidth tracking, latency monitoring
- **Server templates** - `/templatecreate/apply/list` - Define VPS templates with versioning

#### Monitoring & Alerts
- **Resource alerts** - `/alertcreate`, `/alertlist` - Configurable alert channels (DM/webhook)
- **Performance benchmarking** - `/benchmark` - CPU, disk, network benchmarks
- **Recovery system** - `/recoveryplaybookcreate/list`, `/recoveryrun`, `/recoverystatus` - Automated recovery playbooks
- **Troubleshooting** - `/troubleshoot` - Common issue diagnosis

#### Admin & Cleanup
- **Security audit** - `/securityaudit` - SSH config, open ports, capabilities, privileges
- **Update management** - `/updatecheck`, `/updateapply` - OS package update check/apply
- **Resource cleanup** - `/cleanupdryrun`, `/cleanuprun` - Clean Docker images, volumes, logs
- **Quota enforcement** - `/quotaset`, `/quotaget` - Per-user CPU/RAM/disk/bandwidth limits

#### Networking & DNS
- **Load balancing** - `/lbcreate/add/remove/list` - LB pools with health check integration
- **DNS management** - `/dnsadd/remove/list` - DNS record CRUD with Docker IP resolution
- **SSL certificates** - `/sslrequest/status/renew` - Let's Encrypt auto-renewal tracking
- **Cost optimization** - `/costoptimize` - Analyze usage vs allocation, suggest savings
- **Traffic analysis** - `/traffic` - Bandwidth breakdown, peak analysis

## Quick Start

```bash
pip install -r requirements.txt
docker build -t ubuntu-22.04-with-tmate .
python main.py
```

## Configuration

All configurable values are in `config.py` (loaded via environment variables):
- `DISCORD_BOT_TOKEN` - Discord bot token
- `DB_HOST/USER/PASSWORD/NAME` - MySQL connection
- `WHITELIST_IDS` - Admin user IDs (comma-separated)
- `CUTTLY_API_KEY` - URL shortening API key
- `PUBLIC_IP` - Server public IP
- `SSL_EMAIL` - Email for Let's Encrypt

## Architecture

- `main.py` - Unified entry point loading all cogs
- `config.py` - Central configuration
- `vps_manager.py` - Docker SDK-based VPS management
- `integration.py` - MySQL and REST integration helpers
- `resource_monitor.py` - System/container stats collection
- `cogs/*.py` - Discord command cogs (28 total)

## Database Tables

The system uses MySQL with tables for: player_economy, economy_transactions, vps_statistics, vps_peak_statistics, vps_containers, health_checks, health_check_results, backup_rotation, snapshots, dns_records, ssl_certificates, scaling_rules, resource_quotas, load_balancer_pools, lb_pool_members, recovery_playbooks, recovery_executions, templates, alerts.
