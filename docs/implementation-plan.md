# Infra Pilot - Full Feature Implementation Plan

## Overview

This plan covers ~120 features across 4 domains (Minecraft Plugin, VPS Bot, Discord Bot, Integrations), organized into 5 implementation phases over ~12-16 weeks. Each phase builds on the previous one.

**Current state:** ~60% of the "Minecraft features" code exists but is not wired up. Discord bot has complete modules that are not imported. Integration service is most complete. Orchestrator has legacy/modern split.

---

## Phase 0: Foundation & Wiring (Week 1-2)

**Goal:** Activate existing dead code, establish shared infrastructure, resolve technical debt.

### Minecraft Plugin (service-core)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M0.1 | **Wire up existing features** | 2d | Register `EconomyManager`, `ActivityRewardListener`, `PlayerStatistics`, `ResourceWorldManager` in `PlayerServerPlugin.onEnable()`. Load config sections. |
| M0.2 | **Resolve dual-codebase** | 1d | Choose between `com.playerservers.PlayerServerPlugin` and `PlayerServerManager`. Merge the better parts (PlayerServerManager has better command/permissions, main has cleaner structure). |
| M0.3 | **Implement InactivityShutdown** | 1d | Fill empty `run()` method: track last activity per server, add configurable timeout, graceful stop with player notification. |
| M0.4 | **Fix ServerManager start script** | 1d | Implement `createStartScript()` - write actual shell/batch file, wire output reader in `startServer()`. |

### Discord Bot (discord-service)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| D0.1 | **Wire all modules into index.js** | 2d | Import and register: `ticketSystem.js`, `ticketCommands.js`, `statsCommands.js`, `roleManager.js`, `economyCommands.js`, `dashboard.js`. Add event handlers for each. Create `package.json`. |
| D0.2 | **Add command registration** | 1d | Register all slash commands from modules in the client ready handler. |

### Orchestrator Agent (orchestrator-agent)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O0.1 | **Unify legacy and modern bots** | 2d | Either consolidate `bot.py` commands into cogs, or make `bot.py` import the cog-based system. Ensure single entry point. All cogs loading from single `main.py`. |
| O0.2 | **Fix security issues in bot.py** | 1d | Replace `subprocess.run(shell=True)` with Docker SDK calls. Replace flat-file `database.txt` with JSON/vps_instances.json. Persist credit system to DB. |

### Integration Service (integration-service)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| I0.1 | **Add authentication to API** | 1d | Add API key validation or JWT auth to all endpoints. Currently unprotected. |

### Infrastructure
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X0.1 | **Shared database schema** | 2d | Create unified migration script(s) for all tables across services. Establish naming conventions. Add migration tooling (Flyway/Liquibase for Java, Alembic for Python). |
| X0.2 | **Shared config management** | 1d | Centralize env var conventions. `.env.example` exists but isn't synchronized across services. |

---

## Phase 1: Core Minecraft & Economy (Week 3-4)

**Goal:** Complete service-core as a functional Minecraft plugin with full economy, statistics, and world management.

### Resource World Auto-Regeneration (M1)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M1.1 | **Wire ResourceWorldManager** | 0.5d | Already coded - register from main plugin, add config section, test with actual server. |
| M1.2 | **Multi-world support** | 2d | Extend to manage multiple resource worlds with independent schedules. Config-driven world list. |
| M1.3 | **Regeneration commands** | 1d | `/resworld create <name>`, `/resworld schedule <name> <interval>`, `/resworld force <name>`, `/resworld list` with permissions. |

### Custom World Border Expansion (M2)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M2.1 | **World border manager** | 2d | Configurable starting size, max size, expansion rate (blocks/day), expansion intervals. Track current border per world. |
| M2.2 | **Border expansion scheduler** | 1d | Bukkit scheduler that expands border incrementally at set intervals. Player notification on expansion. |
| M2.3 | **Commands & hooks** | 1d | `/border set <size>`, `/border pause`, `/border status`. Hook into resource world regen to reset border. |

### Economy & Shop System (M3)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M3.1 | **Wire economy existing code** | 0.5d | `EconomyManager`, `EconomyCommands`, `ActivityRewardListener` are fully coded - register them. |
| M3.2 | **Player shop tax system** | 2d | Configurable tax rate (default 5%). Shop sale transaction hook. Tax revenue tracking. `/shoptax rate < %>`, `/shoptax revenue`. Ledger for tax collected. |
| M3.3 | **Currency exchange system** | 3d | Configurable exchange rates between currency types. Exchange fees. `/exchange rates`, `/exchange <from> <to> <amount>`. Transaction limits. Rate fluctuation over time (optional). |
| M3.4 | **Player-created markets** | 3d | Player shop chests (click chest to set up shop). Item listing with prices. Search/browse GUI. Market fee on listing. Expiration system. |

### Statistics & Achievements (M4)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M4.1 | **Wire PlayerStatistics** | 0.5d | Already coded - register from main plugin. |
| M4.2 | **Player statistics tracking** | 1d | Already partially done. Add tracking: blocks broken/placed, mobs killed, items crafted, distance traveled, join count. Store in `player_statistics` table. |
| M4.3 | **Player achievement system** | 3d | Achievement definitions in config (YAML). Types: reach level, collect items, kill mobs, explore biomes, playtime milestones. Auto-award with broadcast. `/achievements`, `/achievements <player>`. GUI viewer. |

### Custom Items & Crafting (M5)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M5.1 | **Custom item durability** | 2d | Custom item registry with configurable durability. Durability tracking per item stack. Repair mechanics (anvil, combine). Unbreaking enchant integration. |
| M5.2 | **Custom item crafting system** | 3d | Recipe definitions in config (shaped, shapeless, furnace). Custom ingredients. Permission-locked recipes. Discovery system (learn recipe on first ingredient). |
| M5.3 | **Resource gathering multipliers** | 2d | Per-player multiplier tracking. Boost types: blocks, ores, farming, fishing, mob drops. Multiplier sources: vote rewards, playtime, perks, events. Stacking rules (additive/multiplicative). |

---

## Phase 2: Servers, Performance & Anti-Cheat (Week 5-7)

**Goal:** Server management tools, anti-cheat, performance monitoring, permissions.

### Server Management (M6)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M6.1 | **Server maintenance mode** | 2d | Toggle maintenance mode. Kick message customization. Permission bypass. Scheduled maintenance window. `/maintenance on/off`, `/maintenance schedule <time>`. |
| M6.2 | **Server resource management** | 2d | Per-server resource limits (max players, max entities, max chunks loaded). Resource usage tracking. Auto-disable laggy redstone/chunk loaders. |
| M6.3 | **Server resource limits** | 1d | Global caps: max RAM per player, max loaded chunks, max entities per chunk. Enforce limits with warnings. Configurable thresholds. |

### Anti-Cheat Integration (M7)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M7.1 | **Advanced anti-cheat integration** | 3d | Abstract AC interface (supports AAC, Vulcan, Matrix, Grim). Detection alert aggregation (rate-limit alerts to staff). Auto-flag for review. False positive reporting. |
| M7.2 | **Custom command cooldowns** | 2d | Configurable per-command cooldowns per group/permission. Cooldown bypass permissions. `/cooldown set <command> <seconds>`, `/cooldown reset <player>`. |
| M7.3 | **Custom death penalties** | 2d | Configurable penalty types: currency loss, item drop %, XP loss, respawn timer. Per-world penalties. Keep-inventory exemption items/permissions. `/deathpenalty set <world> <type> <value>`. |

### Player Features (M8)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M8.1 | **Player-specific time/weather** | 2d | Per-player time (`/ptime <day/night/reset>`). Per-player weather (`/pweather <sun/rain/reset>`). Persistent across sessions. Synced on world rejoin. |
| M8.2 | **Player playtime rewards** | 2d | Tiered rewards at configurable intervals (30min, 1hr, 2hr, 5hr, etc.). Reward types: currency, items, commands, perks. `/playtime`, `/playtime rewards`. Auto-claim GUI. |
| M8.3 | **Vote rewards** | 2d | Vote party system (global goals). Per-vote rewards. Vote streak bonuses. `/vote`, `/vote party`, `/vote top`. Integration with Votifier. |
| M8.4 | **Player referral rewards** | 2d | Referral code per player. `/refer create`, `/refer redeem <code>`. Rewards for both referrer and referee. Referral leaderboard. Configurable reward tiers. |

### Permissions (M9)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| M9.1 | **Advanced permission management** | 3d | Group/track-based permission system. Temporary permissions (timed). Permission inheritance. World-specific permissions. `/permissions group add/remove`, `.permissions user set/check`. |
| M9.2 | **VIP server perks management** | 2d | Rank tiers defined in config. Per-perk flags (fly, feed, heal, nick, color chat, join effects). Perk durations (lifetime/timed). `/vip perks`, `/vip give <player> <rank> <duration>`. |

---

## Phase 3: Discord Bot & VPS Features (Week 8-10)

**Goal:** Complete Discord bot functionality, VPS management, and monitoring.

### Discord Bot - Core Features (D1)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| D1.1 | **Advanced ticket system** | 2d | Already coded in `ticketSystem.js`/`ticketCommands.js` - wire into index.js. Add: priority levels, ticket categories, response templates, satisfaction rating after close. |
| D1.2 | **Server status widgets** | 1d | Live embed showing: server count, online players, TPS, uptime. Auto-refresh (30s interval). `/status`, `/status widget create`. Webhook-based updates. |
| D1.3 | **Event scheduling system** | 2d | `/event create <name> <time> <description>`, `/event list`, `/event remind <id>`. Auto-role ping on event start. Recurring events (daily/weekly). Calendar view. |
| D1.4 | **Server poll creator** | 1d | `/poll create <question> <options>`, `/poll vote`, `/poll results`. Anonymous mode. Duration limit. Role-restricted polls. |

### Discord Bot - Management (D2)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| D2.1 | **Role hierarchy manager** | 2d | Role tree visualization. `/role create/delete/edit <name> <permissions>`. Role permission flags (kick, ban, mute, etc.). Role sorting by weight. |
| D2.2 | **Role reaction manager** | 1d | Already coded in `roleManager.js` - wire in. Add: multi-role selectors, temporary roles (timed), role request approval flow. |
| D2.3 | **Custom command creator** | 2d | `/command create <trigger> <response>`, `/command delete`, `/command list`. Embed responses, multi-line, dynamic placeholders (%user%, %server%, etc.). Category organization. |
| D2.4 | **Custom prefix settings** | 1d | Per-server customizable command prefix. `/prefix set <prefix>`. Prefix reset. |

### Discord Bot - Moderation & Logging (D3)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| D3.1 | **User warning system** | 2d | `/warn <user> <reason>`, `/warnings <user>`, `/warn remove <id>`. Warning tiers with auto-action (3 warns = mute, 5 = kick, 7 = ban). Warning expiry. |
| D3.2 | **User verification system** | 2d | Captcha verification on join (reaction/image). Role on verify. Timeout for unverified users. Configurable required age. `/verify`, `/verify config`. |
| D3.3 | **Message filter system** | 2d | Bad word list (configurable). Spam detection (message rate limit). Link whitelist/blacklist. Caps filter. Auto-delete + warn + log. `/filter config`. |
| D3.4 | **Message deletion logs** | 1d | Log deleted messages to `deleted-messages` channel. Author, content, channel, timestamp. Bulk delete summary. Edit history tracking. |
| D3.5 | **User activity tracking** | 2d | Track: messages sent, voice minutes, reactions given, joins/leaves. Activity score algorithm. `/activity <user>`, `/activity leaderboard`. |

### Discord Bot - Utility (D4)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| D4.1 | **Custom welcome messages** | 1d | Configurable join/leave messages. Embed support, placeholders. `/welcome set <type>`, `/welcome preview`. Image/DM welcome option. |
| D4.2 | **Voice channel manager** | 2d | Temporary voice channels (create on join, delete on leave). Voice channel limits (user cap, bitrate). `/voice create`, `/voice limit`, `/voice lock`. |
| D4.3 | **Temporary voice channels** | 1d | Users join a "create VC" to spawn their own temporary channel. Auto-delete when empty. Channel name customization. |
| D4.4 | **Message scheduling** | 2d | `/schedule message <channel> <time> <content>`. Recurring messages. Queue view. Cancel pending. Announcement channel integration. |
| D4.5 | **Channel cleanup tools** | 1d | `/purge <count>`, `/purge user <user> <count>`. Filter options (bots, attachments, links). Confirmation prompt. Audit log. |

### Discord Bot - Archiving & Stats (D5)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| D5.1 | **Message archival system** | 2d | Archive channels by age threshold. Export to JSON/CSV. `/archive channel <channel>`, `/archive server`. Auto-archive schedule. Download link. |
| D5.2 | **Channel category manager** | 2d | Category templates. `/category create <name>`, `/category add <channel>`, `/category permissions`. Bulk channel operations within category. |
| D5.3 | **Channel topic rotation** | 1d | Rotate channel topics from a list on schedule. `/topic rotation set <channel> <list>`, `/topic rotation on/off`. |
| D5.4 | **Server statistics graphs** | 2d | Member growth chart. Message volume over time. Voice activity chart. Channel activity heatmap. `/server graph <type> <period>`. |
| D5.5 | **User verification levels** | 1d | Required account age, must be in server X days, must have role. `/verify level set <level>`. Stacking rules. |

### VPS Bot - Core (O1)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O1.1 | **Resource usage graphs** | 2d | Already partially done in `monitoring.py`. Generate time-series graphs (CPU, RAM, disk, network). `/vps graph <id> <metric> <period>`. Support multiple graph libraries (matplotlib exists). |
| O1.2 | **Server health checks** | 2d | Periodic health check: ping test, port check, process check, API response check. `/health <vps_id>`, `/health check create <type>`. Alert on failure. |
| O1.3 | **Automated scaling system** | 3d | Define scale-up/down rules (CPU > 80% for 5min = scale up). Resource pool management. Cooldown period between scales. `/scale set <vps_id> <cpu|memory> <limit>`. |
| O1.4 | **Backup rotation system** | 2d | Already partially supported in `vps_manager.py`. Configurable retention policy (daily/weekly/monthly). Backup scheduling. `/backup list`, `/backup restore <id>`. |

### VPS Bot - Advanced (O2)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O2.1 | **Cost prediction calculator** | 2d | Based on current usage trends, predict next month cost. `/cost predict <vps_id>`. Factors: CPU trend, bandwidth trend, storage growth. |
| O2.2 | **Performance optimization suggestions** | 2d | Analyze resource usage and suggest: RAM allocation, CPU pinning, disk I/O tuning. `/optimize <vps_id>`. Auto-apply with confirmation. |
| O2.3 | **Resource allocation manager** | 2d | Oversubscription ratio config. Fair scheduling between VPS instances. Resource pool partitioning. `/resource pool create/delete/list`. |
| O2.4 | **Network monitoring** | 2d | Bandwidth tracking (in/out/total per VPS). Latency monitoring to multiple endpoints. Packet loss detection. `/network stats <vps_id>`. |

### VPS Bot - Operations (O3)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O3.1 | **Server template manager** | 2d | Define VPS templates (OS, software stack, resource defaults). `/template create/apply/list`. Template versioning. |
| O3.2 | **Server migration tool** | 3d | Migrate VPS between hosts. Live migration (shared storage) vs cold migration (data transfer). `/migrate <vps_id> <target_host>`. Progress tracking. |
| O3.3 | **Server cloning system** | 2d | Clone entire VPS (OS + data). `/clone <vps_id> <new_name>`. Clone with resource overrides. Snapshot-based cloning. |
| O3.4 | **Server snapshot system** | 2d | Create point-in-time snapshots before changes. `/snapshot create <vps_id>`, `/snapshot list`, `/snapshot restore <id>`. Automatic pre-update snapshots. |

### VPS Bot - Monitoring (O4)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O4.1 | **Resource usage alerts** | 1d | Already partially done in `monitoring.py`. Add configurable alert channels (Discord DM, webhook, email). `/alert create <type> <threshold>`, `/alert list`. |
| O4.2 | **Performance benchmarking** | 2d | CPU benchmark (Geekbench-style calculation), disk benchmark (seq/rnd RW), network benchmark (speedtest). `/benchmark <vps_id> <type>`. |
| O4.3 | **Automated recovery system** | 3d | Define recovery playbooks (service restart -> host reboot -> reimage). Health check triggers. `/recovery playbook create/list`, `/recovery status`. |
| O4.4 | **Automated troubleshooting** | 2d | Common issue diagnosis: service not starting, high CPU, disk full, network down. `/troubleshoot <vps_id> <issue>`. Suggested fix steps. |

### VPS Bot - Admin & Cleanup (O5)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O5.1 | **Security audit system** | 2d | SSH config audit, open port scan, user account audit, software version check. `/security audit <vps_id>`, `/security report`. |
| O5.2 | **Update management** | 2d | OS package update check. `/update check <vps_id>`, `/update apply <vps_id>`. Maintenance window scheduling. Reboot required detection. |
| O5.3 | **Resource cleanup tools** | 2d | Clean Docker images, orphaned volumes, package cache, old logs. `/cleanup dry-run <vps_id>`, `/cleanup run <vps_id>`. Scheduled cleanup. |
| O5.4 | **Resource quota enforcement** | 1d | Enforce per-user CPU/RAM/disk/bandwidth limits. Quota exceeded actions (throttle, warn, suspend). `/quota set <user> <type> <limit>`. |

### VPS Bot - Misc (O6)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| O6.1 | **Load balancing configuration** | 2d | Define load balancer pools. Health check integration. `/lb create <name>`, `/lb add <vps>`, `/lb remove <vps>`. Round-robin/least-connections. |
| O6.2 | **DNS management system** | 2d | DNS record CRUD. `/dns add <domain> <type> <value>`, `/dns remove`, `/dns list`. Integration with Docker IP assignment. |
| O6.3 | **SSL certificate manager** | 2d | Let's Encrypt auto-renewal. Certificate status dashboard. `/ssl request <domain>`, `/ssl status`, `/ssl renew <domain>`. Wildcard support. |
| O6.4 | **Cost optimization suggestions** | 2d | Analyze usage vs allocation. Suggest downsizing underutilized VPS, reserved instances. `/cost optimize <vps_id>`. Savings estimate. |
| O6.5 | **Traffic analysis tools** | 2d | Bandwidth usage breakdown by protocol/service. Peak traffic analysis. `/traffic <vps_id> <period>`. Top talkers/ listeners. |

---

## Phase 4: Management Panel & VPS Dashboard (Week 11-12)

**Goal:** Build out the management panel dashboard with VPS-specific features.

### Server Performance Dashboard (P1)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| P1.1 | **Server performance monitoring dashboard** | 3d | Real-time TPS graph (last 5min/30min/1hr). Memory/CPU usage chart. Player count over time. World size tracking. Lag spike detection. Widget: `/dashboard` embed on Discord. |
| P1.2 | **Server metrics dashboard** | 2d | Aggregate all metrics in one view. Server count, total players, resource usage summary. Export metrics to Prometheus endpoint. |

### VPS Dashboard (P2)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| P2.1 | **Server access logs** | 1d | SSH login attempts, console access, file access. `/logs access <vps_id>`. Integration with auth.log. |
| P2.2 | **Server resource monitoring** | 2d | Real-time resource dashboard in management panel. CPU/memory/disk/network gauges. Historical trend charts. Export to Grafana via Prometheus. |
| P2.3 | **Resource usage reports** | 2d | Scheduled reports (daily/weekly/monthly). PDF/CSV export. `/report generate <type> <period>`. Auto-send to email/Discord. |

### Templates & Config (P3)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| P3.1 | **Configuration version control** | 2d | Track config file changes. `/config history`, `/config diff <version>`, `/config rollback <version>`. Git-backed storage. |
| P3.2 | **Server maintenance scheduler** | 2d | Schedule maintenance windows. Auto-apply updates at scheduled time. `/maintenance schedule <vps_id> <time>`. Notify users. |
| P3.3 | **Database backup automation** | 2d | MySQL/PostgreSQL dump automation. Schedule: hourly/daily/weekly. Retention policy. `/db backup create`, `/db backup list`, `/db backup restore <id>`. |

### Alerts & Updates (P4)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| P4.1 | **Server backup notifications** | 1d | Notify on backup completion/failure. Include: size, duration, location. Channel: Discord DM, webhook, email. |
| P4.2 | **Resource usage alerts** | 1d | Already partially done. Add management panel alert configuration UI. `/alert test <type>`. Alert history log. |
| P4.3 | **Server health checks** (Dashboard) | 1d | Health check visualization. Uptime percentage over time. `/health dashboard`. Incident timeline. |

---

## Phase 5: Integration & Cross-Platform (Week 13-16)

**Goal:** Connect all services into a unified platform with cross-platform features.

### Authentication & Users (X1)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X1.1 | **Cross-platform authentication** | 3d | Single sign-on across Dashboard, Discord, and Minecraft. OAuth2 flow. Link Minecraft UUID with Discord ID. `/link account`. JWT token exchange. |
| X1.2 | **Shared user management** | 2d | Already partially done in `UnifiedUserManager`. Add: profile sync on login, role sync across platforms, user search API. |
| X1.3 | **Shared user profiles** | 2d | Unified profile: Discord name, Minecraft UUID, stats, balance, achievements. `/profile <user>`. Bio, social links, vanity URL. |

### Messaging & Notifications (X2)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X2.1 | **Cross-platform messaging** | 2d | Message bridge: Discord <-> Minecraft chat. Bidirectional. Format conversion (Discord markdown -> Minecraft colors). Webhook-based. |
| X2.2 | **Cross-platform notifications** | 2d | Already partially done in `CrossPlatformNotifier`. Add: notification preferences per user, priority levels, digest mode (daily summary). |
| X2.3 | **Cross-platform commands** | 3d | Execute commands from any platform. `/execute discord <command>` on Minecraft, `/execute mc <command>` on Discord. Permission-checked. Audit logged. |
| X2.4 | **Cross-platform events** | 2d | Server events broadcast across platforms. Player join/leave, achievement unlock, vote received. Custom event hooks. |
| X2.5 | **Cross-platform alerts** | 2d | Unified alert system. Alert types: resource threshold, security, maintenance. Delivery channels: Discord, in-game, email, SMS (webhook). |
| X2.6 | **Server announcement scheduler** | 2d | Schedule announcements across platforms. `/announce create <message> <time> <platforms>`. Recurring announcements. Template support. |

### Logging & Monitoring (X3)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X3.1 | **Unified logging system** | 2d | Already partially done in `UnifiedLogger`. Add: centralized log aggregation, log level filtering, search API, log retention. |
| X3.2 | **Cross-platform logging** | 1d | Log all cross-platform events in one place. `/logs cross-platform <filter>`. Export to external SIEM. |
| X3.3 | **Unified reporting system** | 2d | Generate reports spanning all services. `/report unified <type> <period>`. Usage, billing, security, performance reports. |
| X3.4 | **Server logs integration** | 2d | Minecraft server logs -> Discord channel. Filter by log level. `/logs tail <server>`, `/logs search <query>`. |
| X3.5 | **Server backup logs** | 1d | Centralized backup status across all services. Backup success/failure rate. `/backup logs <period>`. |

### Resource & Configuration (X4)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X4.1 | **Unified permission system** | 3d | Central permission store. Permission inheritance across platforms. `/permission set <user> <platform> <permission>`. Cache with Redis. |
| X4.2 | **Shared configuration management** | 2d | Already partially done in `SharedConfigManager`. Add: config versioning, diff view, rollback, bulk update. |
| X4.3 | **Shared configuration system** | 1d | Central config repository. Environment-specific overlays. `/config set/get/list`. Validation on update. |
| X4.4 | **Shared resource pools** | 2d | Pool resources (CPU, RAM, storage) across VPS instances. Fair scheduling. Pool size adjustment. `/pool create/delete/resize`. |

### Backups & Resources (X5)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X5.1 | **Integrated backup system** | 3d | Already partially done in `BackupManager`. Add: cross-service backup coordination, atomic multi-service restore, backup verification. |
| X5.2 | **Unified backup management** | 2d | Single view of all backups. Retention policy engine (per-service + global). `/backup unified list`. Restore from unified interface. |
| X5.3 | **Cross-platform backups** | 1d | Backup that spans services (Minecraft world + Discord config + VPS data). Coordinated restore. |
| X5.4 | **Resource synchronization** | 2d | Sync resource allocations across services. Resource pool updates propagate to all VPS. `/resource sync`. |
| X5.5 | **Resource allocation management** | 2d | Unified view of resource allocation vs usage. Rebalance suggestion. `/resource rebalance`. |

### Metrics & Coordination (X6)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X6.1 | **Resource usage tracking** | 2d | Already partially done in `UnifiedResourceTracker`. Add: cost allocation, trend analysis, forecasting. |
| X6.2 | **Unified metrics system** | 2d | Prometheus metric exports from all services. Grafana dashboards. `/metrics unified <period>`. Metric annotations for events. |
| X6.3 | **Cross-platform statistics** | 2d | Aggregate stats across all platforms. `/stats unified <user>`. Player stats + Discord activity + VPS usage in one view. |
| X6.4 | **Resource scheduling coordination** | 2d | Coordinate maintenance windows, backups, scaling events. Conflict detection. `/schedule resource <type> <time>`. |
| X6.5 | **Resource optimization coordination** | 2d | Cross-service optimization. Identify idle resources, recommend consolidation. `/optimize cross-platform`. |

### Integration Features (X7)
| # | Feature | Effort | Details |
|---|---------|--------|---------|
| X7.1 | **Integrated monitoring system** | 2d | Single monitoring view: all services, all metrics. Alert correlation. Root cause analysis suggestions. |
| X7.2 | **Integrated maintenance system** | 2d | Cross-service maintenance windows. Dependency-aware ordering. `/maintenance create <services> <window>`. |
| X7.3 | **Integrated security system** | 2d | Centralized security monitoring. Cross-platform suspicious activity detection. `/security report unified`. |
| X7.4 | **Integrated resource management** | 2d | Unified dashboard for all resource allocation. Cost tracking. `/resources dashboard`. |

---

## Summary Statistics

| Phase | Features | Effort (person-days) |
|-------|----------|---------------------|
| Phase 0: Foundation & Wiring | 9 | 13 |
| Phase 1: Core Minecraft & Economy | 16 | 28 |
| Phase 2: Servers, Performance & Anti-Cheat | 13 | 24 |
| Phase 3: Discord Bot & VPS Features | 40 | 67 |
| Phase 4: Management Panel & VPS Dashboard | 10 | 17 |
| Phase 5: Integration & Cross-Platform | 30 | 52 |
| **Total** | **~118** | **~201** |

## Architecture Decisions

1. **Integration Service as Hub**: All cross-platform features go through the integration service (port 9000). It becomes the central nervous system.
2. **Shared Database**: A shared PostgreSQL database (already in docker-compose) used for cross-service data. Individual services keep their own MySQL/JSON for service-specific data.
3. **Message Queue**: Consider adding Redis pub/sub (already in docker-compose) for real-time cross-platform events instead of polling.
4. **Single Entry Per Service**: Each service should have ONE main entry point that loads all modules. Currently both service-core and orchestrator-agent have split entry points.

## Immediate Next Steps

1. Complete Phase 0 - wiring existing code is the highest ROI (features are already written)
2. Establish CI/CD tests for the newly wired features
3. Then proceed with Phase 1 features based on priority
