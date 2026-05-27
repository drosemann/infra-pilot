# infra pilot - orchestrator agent

## features

### core vps management
- create, start, stop, restart, delete vps instances via docker sdk
- resource monitoring with mysql persistence
- pricing and billing system with player_economy integration
- monthly billing cycle with grace periods

### vps bot features

#### resource management
- resource usage graphs - `/vpsgraph` - time-series graphs (cpu, ram, disk, network) using matplotlib
- server health checks - `/health`, `/healthcreate` - ping, port, process, api health monitoring with alerts
- auto scaling - `/scalerule`, `/scaleset` - automatic resource scaling based on usage thresholds
- backup rotation - `/backup`, `/backuplist`, `/restore` - configurable retention (daily/weekly/monthly)
- snapshots - `/snapshotcreate`, `/snapshotlist`, `/snapshotrestore` - point-in-time snapshots
- clone system - `/clone` - clone vps with os + data via docker commit
- server migration - `/migrate` - migrate vps between hosts (live/cold)

#### advanced features
- cost prediction - `/costpredict` - analyze usage trends, predict next month costs
- performance optimizer - `/optimize`, `/optimizeapply` - suggest cpu/ram/disk tuning
- resource pools - `/resourcepoolcreate/delete/list/add` - track oversubscription ratios
- network monitoring - `/networkstats`, `/networklatency` - bandwidth tracking, latency monitoring
- server templates - `/templatecreate/apply/list` - define vps templates with versioning

#### monitoring & alerts
- resource alerts - `/alertcreate`, `/alertlist` - configurable alert channels (dm/webhook)
- performance benchmarking - `/benchmark` - cpu, disk, network benchmarks
- recovery system - `/recoveryplaybookcreate/list`, `/recoveryrun`, `/recoverystatus` - automated recovery playbooks
- troubleshooting - `/troubleshoot` - common issue diagnosis

#### admin & cleanup
- security audit - `/securityaudit` - ssh config, open ports, capabilities, privileges
- update management - `/updatecheck`, `/updateapply` - os package update check/apply
- resource cleanup - `/cleanupdryrun`, `/cleanuprun` - clean docker images, volumes, logs
- quota enforcement - `/quotaset`, `/quotaget` - per-user cpu/ram/disk/bandwidth limits

#### networking & dns
- load balancing - `/lbcreate/add/remove/list` - lb pools with health check integration
- dns management - `/dnsadd/remove/list` - dns record crud with docker ip resolution
- ssl certificates - `/sslrequest/status/renew` - let's encrypt auto-renewal tracking
- cost optimization - `/costoptimize` - analyze usage vs allocation, suggest savings
- traffic analysis - `/traffic` - bandwidth breakdown, peak analysis

#### database management
- mysql provisioning - `/database create/list/delete/info` - on-demand mysql container provisioning with automatic configuration

#### git deployment
- git deployment - `/deploy create/list/delete/toggle/logs` - automated deployments from github webhooks
- webhook server - listens on port 8500 for github push events, triggers auto-deploy

#### task scheduler
- cron scheduler - `/cron` - cron-based scheduled task execution (restart/command/backup) with 30s check interval

#### modpack installer
- modpack search - `/modpack search` - search modpacks from curseforge and modrinth
- modpack install - `/modpack install` - one-click modpack installation with dependency resolution

#### prepaid billing
- balance check - `/balance` - view current credit balance
- balance top-up - `/balance add` - add credits to user balance
- transaction history - `/balance history` - view transaction history
- cost estimation - `/balance cost` - calculate estimated costs for a server configuration
- hourly billing loop - background task that deducts usage costs every hour

## quick start

```bash
pip install -r requirements.txt
docker build -t ubuntu-22.04-with-tmate .
python main.py
```

## configuration

all configurable values are in `config.py` (loaded via environment variables):
- `discord_bot_token` - discord bot token
- `db_host/user/password/name` - mysql connection
- `whitelist_ids` - admin user ids (comma-separated)
- `cuttly_api_key` - url shortening api key
- `public_ip` - server public ip
- `ssl_email` - email for let's encrypt
- `discord_token_validation` - enable/disable discord token validation on startup

## architecture

- `main.py` - unified entry point loading all cogs
- `config.py` - central configuration
- `vps_manager.py` - docker sdk-based vps management
- `integration.py` - mysql and rest integration helpers
- `resource_monitor.py` - system/container stats collection
- `cogs/*.py` - discord command cogs (35 total)

## database tables

the system uses mysql with tables for: player_economy, economy_transactions, vps_statistics, vps_peak_statistics, vps_containers, health_checks, health_check_results, backup_rotation, snapshots, dns_records, ssl_certificates, scaling_rules, resource_quotas, load_balancer_pools, lb_pool_members, recovery_playbooks, recovery_executions, templates, alerts.
