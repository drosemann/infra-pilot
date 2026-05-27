# infra pilot - full feature implementation plan

## overview

this plan covers ~120 features across 4 domains (minecraft plugin, vps bot, discord bot, integrations), organized into 5 implementation phases over ~12-16 weeks. each phase builds on the previous one.

current state: ~60% of the "minecraft features" code exists but is not wired up. discord bot has complete modules that are not imported. integration service is most complete. orchestrator has legacy/modern split.

## phase 0: foundation & wiring (week 1-2)

goal: activate existing dead code, establish shared infrastructure, resolve technical debt.

### minecraft plugin (service-core)
| # | feature | effort | details |
|---|---------|--------|---------|
| m0.1 | wire up existing features | 2d | register `economymanager`, `activityrewardlistener`, `playerstatistics`, `resourceworldmanager` in `playerserverplugin.onenable()`. load config sections. |
| m0.2 | resolve dual-codebase | 1d | choose between `com.playerservers.playerserverplugin` and `playerservermanager`. merge the better parts (playerservermanager has better command/permissions, main has cleaner structure). |
| m0.3 | implement in activityshutdown | 1d | fill empty `run()` method: track last activity per server, add configurable timeout, graceful stop with player notification. |
| m0.4 | fix servermanager start script | 1d | implement `createstartscript()` - write actual shell/batch file, wire output reader in `startserver()`. |

### discord bot (discord-service)
| # | feature | effort | details |
|---|---------|--------|---------|
| d0.1 | wire all modules into index.js | 2d | import and register: `ticketsystem.js`, `ticketcommands.js`, `statscommands.js`, `rolemanager.js`, `economycommands.js`, `dashboard.js`. add event handlers for each. create `package.json`. |
| d0.2 | add command registration | 1d | register all slash commands from modules in the client ready handler. |

### orchestrator agent (orchestrator-agent)
| # | feature | effort | details |
|---|---------|--------|---------|
| o0.1 | unify legacy and modern bots | 2d | either consolidate `bot.py` commands into cogs, or make `bot.py` import the cog-based system. ensure single entry point. all cogs loading from single `main.py`. |
| o0.2 | fix security issues in bot.py | 1d | replace `subprocess.run(shell=true)` with docker sdk calls. replace flat-file `database.txt` with json/vps_instances.json. persist credit system to db. |

### integration service (integration-service)
| # | feature | effort | details |
|---|---------|--------|---------|
| i0.1 | add authentication to api | 1d | add api key validation or jwt auth to all endpoints. currently unprotected. |

### infrastructure
| # | feature | effort | details |
|---|---------|--------|---------|
| x0.1 | shared database schema | 2d | create unified migration script(s) for all tables across services. establish naming conventions. add migration tooling (flyway/liquibase for java, alembic for python). |
| x0.2 | shared config management | 1d | centralize env var conventions. `.env.example` exists but isn't synchronized across services. |

## phase 1: core minecraft & economy (week 3-4)

goal: complete service-core as a functional minecraft plugin with full economy, statistics, and world management.

### resource world auto-regeneration (m1)
| # | feature | effort | details |
|---|---------|--------|---------|
| m1.1 | wire resourceworldmanager | 0.5d | already coded - register from main plugin, add config section, test with actual server. |
| m1.2 | multi-world support | 2d | extend to manage multiple resource worlds with independent schedules. config-driven world list. |
| m1.3 | regeneration commands | 1d | `/resworld create <name>`, `/resworld schedule <name> <interval>`, `/resworld force <name>`, `/resworld list` with permissions. |

### custom world border expansion (m2)
| # | feature | effort | details |
|---|---------|--------|---------|
| m2.1 | world border manager | 2d | configurable starting size, max size, expansion rate (blocks/day), expansion intervals. track current border per world. |
| m2.2 | border expansion scheduler | 1d | bukkit scheduler that expands border incrementally at set intervals. player notification on expansion. |
| m2.3 | commands & hooks | 1d | `/border set <size>`, `/border pause`, `/border status`. hook into resource world regen to reset border. |

### economy & shop system (m3)
| # | feature | effort | details |
|---|---------|--------|---------|
| m3.1 | wire economy existing code | 0.5d | `economymanager`, `economycommands`, `activityrewardlistener` are fully coded - register them. |
| m3.2 | player shop tax system | 2d | configurable tax rate (default 5%). shop sale transaction hook. tax revenue tracking. `/shoptax rate < %>`, `/shoptax revenue`. ledger for tax collected. |
| m3.3 | currency exchange system | 3d | configurable exchange rates between currency types. exchange fees. `/exchange rates`, `/exchange <from> <to> <amount>`. transaction limits. rate fluctuation over time (optional). |
| m3.4 | player-created markets | 3d | player shop chests (click chest to set up shop). item listing with prices. search/browse gui. market fee on listing. expiration system. |

### statistics & achievements (m4)
| # | feature | effort | details |
|---|---------|--------|---------|
| m4.1 | wire playerstatistics | 0.5d | already coded - register from main plugin. |
| m4.2 | player statistics tracking | 1d | already partially done. add tracking: blocks broken/placed, mobs killed, items crafted, distance traveled, join count. store in `player_statistics` table. |
| m4.3 | player achievement system | 3d | achievement definitions in config (yaml). types: reach level, collect items, kill mobs, explore biomes, playtime milestones. auto-award with broadcast. `/achievements`, `/achievements <player>`. gui viewer. |

### custom items & crafting (m5)
| # | feature | effort | details |
|---|---------|--------|---------|
| m5.1 | custom item durability | 2d | custom item registry with configurable durability. durability tracking per item stack. repair mechanics (anvil, combine). unbreaking enchant integration. |
| m5.2 | custom item crafting system | 3d | recipe definitions in config (shaped, shapeless, furnace). custom ingredients. permission-locked recipes. discovery system (learn recipe on first ingredient). |
| m5.3 | resource gathering multipliers | 2d | per-player multiplier tracking. boost types: blocks, ores, farming, fishing, mob drops. multiplier sources: vote rewards, playtime, perks, events. stacking rules (additive/multiplicative). |

## phase 2: servers, performance & anti-cheat (week 5-7)

goal: server management tools, anti-cheat, performance monitoring, permissions.

### server management (m6)
| # | feature | effort | details |
|---|---------|--------|---------|
| m6.1 | server maintenance mode | 2d | toggle maintenance mode. kick message customization. permission bypass. scheduled maintenance window. `/maintenance on/off`, `/maintenance schedule <time>`. |
| m6.2 | server resource management | 2d | per-server resource limits (max players, max entities, max chunks loaded). resource usage tracking. auto-disable laggy redstone/chunk loaders. |
| m6.3 | server resource limits | 1d | global caps: max ram per player, max loaded chunks, max entities per chunk. enforce limits with warnings. configurable thresholds. |

### anti-cheat integration (m7)
| # | feature | effort | details |
|---|---------|--------|---------|
| m7.1 | advanced anti-cheat integration | 3d | abstract ac interface (supports aac, vulcan, matrix, grim). detection alert aggregation (rate-limit alerts to staff). auto-flag for review. false positive reporting. |
| m7.2 | custom command cooldowns | 2d | configurable per-command cooldowns per group/permission. cooldown bypass permissions. `/cooldown set <command> <seconds>`, `/cooldown reset <player>`. |
| m7.3 | custom death penalties | 2d | configurable penalty types: currency loss, item drop %, xp loss, respawn timer. per-world penalties. keep-inventory exemption items/permissions. `/deathpenalty set <world> <type> <value>`. |

### player features (m8)
| # | feature | effort | details |
|---|---------|--------|---------|
| m8.1 | player-specific time/weather | 2d | per-player time (`/ptime <day/night/reset>`). per-player weather (`/pweather <sun/rain/reset>`). persistent across sessions. synced on world rejoin. |
| m8.2 | player playtime rewards | 2d | tiered rewards at configurable intervals (30min, 1hr, 2hr, 5hr, etc.). reward types: currency, items, commands, perks. `/playtime`, `/playtime rewards`. auto-claim gui. |
| m8.3 | vote rewards | 2d | vote party system (global goals). per-vote rewards. vote streak bonuses. `/vote`, `/vote party`, `/vote top`. integration with votifier. |
| m8.4 | player referral rewards | 2d | referral code per player. `/refer create`, `/refer redeem <code>`. rewards for both referrer and referee. referral leaderboard. configurable reward tiers. |

### permissions (m9)
| # | feature | effort | details |
|---|---------|--------|---------|
| m9.1 | advanced permission management | 3d | group/track-based permission system. temporary permissions (timed). permission inheritance. world-specific permissions. `/permissions group add/remove`, `.permissions user set/check`. |
| m9.2 | vip server perks management | 2d | rank tiers defined in config. per-perk flags (fly, feed, heal, nick, color chat, join effects). perk durations (lifetime/timed). `/vip perks`, `/vip give <player> <rank> <duration>`. |

## phase 3: discord bot & vps features (week 8-10)

goal: complete discord bot functionality, vps management, and monitoring.

### discord bot - core features (d1)
| # | feature | effort | details |
|---|---------|--------|---------|
| d1.1 | advanced ticket system | 2d | already coded in `ticketsystem.js`/`ticketcommands.js` - wire into index.js. add: priority levels, ticket categories, response templates, satisfaction rating after close. |
| d1.2 | server status widgets | 1d | live embed showing: server count, online players, tps, uptime. auto-refresh (30s interval). `/status`, `/status widget create`. webhook-based updates. |
| d1.3 | event scheduling system | 2d | `/event create <name> <time> <description>`, `/event list`, `/event remind <id>`. auto-role ping on event start. recurring events (daily/weekly). calendar view. |
| d1.4 | server poll creator | 1d | `/poll create <question> <options>`, `/poll vote`, `/poll results`. anonymous mode. duration limit. role-restricted polls. |

### discord bot - management (d2)
| # | feature | effort | details |
|---|---------|--------|---------|
| d2.1 | role hierarchy manager | 2d | role tree visualization. `/role create/delete/edit <name> <permissions>`. role permission flags (kick, ban, mute, etc.). role sorting by weight. |
| d2.2 | role reaction manager | 1d | already coded in `rolemanager.js` - wire in. add: multi-role selectors, temporary roles (timed), role request approval flow. |
| d2.3 | custom command creator | 2d | `/command create <trigger> <response>`, `/command delete`, `/command list`. embed responses, multi-line, dynamic placeholders (%user%, %server%, etc.). category organization. |
| d2.4 | custom prefix settings | 1d | per-server customizable command prefix. `/prefix set <prefix>`. prefix reset. |

### discord bot - moderation & logging (d3)
| # | feature | effort | details |
|---|---------|--------|---------|
| d3.1 | user warning system | 2d | `/warn <user> <reason>`, `/warnings <user>`, `/warn remove <id>`. warning tiers with auto-action (3 warns = mute, 5 = kick, 7 = ban). warning expiry. |
| d3.2 | user verification system | 2d | captcha verification on join (reaction/image). role on verify. timeout for unverified users. configurable required age. `/verify`, `/verify config`. |
| d3.3 | message filter system | 2d | bad word list (configurable). spam detection (message rate limit). link whitelist/blacklist. caps filter. auto-delete + warn + log. `/filter config`. |
| d3.4 | message deletion logs | 1d | log deleted messages to `deleted-messages` channel. author, content, channel, timestamp. bulk delete summary. edit history tracking. |
| d3.5 | user activity tracking | 2d | track: messages sent, voice minutes, reactions given, joins/leaves. activity score algorithm. `/activity <user>`, `/activity leaderboard`. |

### discord bot - utility (d4)
| # | feature | effort | details |
|---|---------|--------|---------|
| d4.1 | custom welcome messages | 1d | configurable join/leave messages. embed support, placeholders. `/welcome set <type>`, `/welcome preview`. image/dm welcome option. |
| d4.2 | voice channel manager | 2d | temporary voice channels (create on join, delete on leave). voice channel limits (user cap, bitrate). `/voice create`, `/voice limit`, `/voice lock`. |
| d4.3 | temporary voice channels | 1d | users join a "create vc" to spawn their own temporary channel. auto-delete when empty. channel name customization. |
| d4.4 | message scheduling | 2d | `/schedule message <channel> <time> <content>`. recurring messages. queue view. cancel pending. announcement channel integration. |
| d4.5 | channel cleanup tools | 1d | `/purge <count>`, `/purge user <user> <count>`. filter options (bots, attachments, links). confirmation prompt. audit log. |

### discord bot - archiving & stats (d5)
| # | feature | effort | details |
|---|---------|--------|---------|
| d5.1 | message archival system | 2d | archive channels by age threshold. export to json/csv. `/archive channel <channel>`, `/archive server`. auto-archive schedule. download link. |
| d5.2 | channel category manager | 2d | category templates. `/category create <name>`, `/category add <channel>`, `/category permissions`. bulk channel operations within category. |
| d5.3 | channel topic rotation | 1d | rotate channel topics from a list on schedule. `/topic rotation set <channel> <list>`, `/topic rotation on/off`. |
| d5.4 | server statistics graphs | 2d | member growth chart. message volume over time. voice activity chart. channel activity heatmap. `/server graph <type> <period>`. |
| d5.5 | user verification levels | 1d | required account age, must be in server x days, must have role. `/verify level set <level>`. stacking rules. |

### vps bot - core (o1)
| # | feature | effort | details |
|---|---------|--------|---------|
| o1.1 | resource usage graphs | 2d | already partially done in `monitoring.py`. generate time-series graphs (cpu, ram, disk, network). `/vps graph <id> <metric> <period>`. support multiple graph libraries (matplotlib exists). |
| o1.2 | server health checks | 2d | periodic health check: ping test, port check, process check, api response check. `/health <vps_id>`, `/health check create <type>`. alert on failure. |
| o1.3 | automated scaling system | 3d | define scale-up/down rules (cpu > 80% for 5min = scale up). resource pool management. cooldown period between scales. `/scale set <vps_id> <cpu|memory> <limit>`. |
| o1.4 | backup rotation system | 2d | already partially supported in `vps_manager.py`. configurable retention policy (daily/weekly/monthly). backup scheduling. `/backup list`, `/backup restore <id>`. |

### vps bot - advanced (o2)
| # | feature | effort | details |
|---|---------|--------|---------|
| o2.1 | cost prediction calculator | 2d | based on current usage trends, predict next month cost. `/cost predict <vps_id>`. factors: cpu trend, bandwidth trend, storage growth. |
| o2.2 | performance optimization suggestions | 2d | analyze resource usage and suggest: ram allocation, cpu pinning, disk i/o tuning. `/optimize <vps_id>`. auto-apply with confirmation. |
| o2.3 | resource allocation manager | 2d | oversubscription ratio config. fair scheduling between vps instances. resource pool partitioning. `/resource pool create/delete/list`. |
| o2.4 | network monitoring | 2d | bandwidth tracking (in/out/total per vps). latency monitoring to multiple endpoints. packet loss detection. `/network stats <vps_id>`. |

### vps bot - operations (o3)
| # | feature | effort | details |
|---|---------|--------|---------|
| o3.1 | server template manager | 2d | define vps templates (os, software stack, resource defaults). `/template create/apply/list`. template versioning. |
| o3.2 | server migration tool | 3d | migrate vps between hosts. live migration (shared storage) vs cold migration (data transfer). `/migrate <vps_id> <target_host>`. progress tracking. |
| o3.3 | server cloning system | 2d | clone entire vps (os + data). `/clone <vps_id> <new_name>`. clone with resource overrides. snapshot-based cloning. |
| o3.4 | server snapshot system | 2d | create point-in-time snapshots before changes. `/snapshot create <vps_id>`, `/snapshot list`, `/snapshot restore <id>`. automatic pre-update snapshots. |

### vps bot - monitoring (o4)
| # | feature | effort | details |
|---|---------|--------|---------|
| o4.1 | resource usage alerts | 1d | already partially done in `monitoring.py`. add configurable alert channels (discord dm, webhook, email). `/alert create <type> <threshold>`, `/alert list`. |
| o4.2 | performance benchmarking | 2d | cpu benchmark (geekbench-style calculation), disk benchmark (seq/rnd rw), network benchmark (speedtest). `/benchmark <vps_id> <type>`. |
| o4.3 | automated recovery system | 3d | define recovery playbooks (service restart -> host reboot -> reimage). health check triggers. `/recovery playbook create/list`, `/recovery status`. |
| o4.4 | automated troubleshooting | 2d | common issue diagnosis: service not starting, high cpu, disk full, network down. `/troubleshoot <vps_id> <issue>`. suggested fix steps. |

### vps bot - admin & cleanup (o5)
| # | feature | effort | details |
|---|---------|--------|---------|
| o5.1 | security audit system | 2d | ssh config audit, open port scan, user account audit, software version check. `/security audit <vps_id>`, `/security report`. |
| o5.2 | update management | 2d | os package update check. `/update check <vps_id>`, `/update apply <vps_id>`. maintenance window scheduling. reboot required detection. |
| o5.3 | resource cleanup tools | 2d | clean docker images, orphaned volumes, package cache, old logs. `/cleanup dry-run <vps_id>`, `/cleanup run <vps_id>`. scheduled cleanup. |
| o5.4 | resource quota enforcement | 1d | enforce per-user cpu/ram/disk/bandwidth limits. quota exceeded actions (throttle, warn, suspend). `/quota set <user> <type> <limit>`. |

### vps bot - misc (o6)
| # | feature | effort | details |
|---|---------|--------|---------|
| o6.1 | load balancing configuration | 2d | define load balancer pools. health check integration. `/lb create <name>`, `/lb add <vps>`, `/lb remove <vps>`. round-robin/least-connections. |
| o6.2 | dns management system | 2d | dns record crud. `/dns add <domain> <type> <value>`, `/dns remove`, `/dns list`. integration with docker ip assignment. |
| o6.3 | ssl certificate manager | 2d | let's encrypt auto-renewal. certificate status dashboard. `/ssl request <domain>`, `/ssl status`, `/ssl renew <domain>`. wildcard support. |
| o6.4 | cost optimization suggestions | 2d | analyze usage vs allocation. suggest downsizing underutilized vps, reserved instances. `/cost optimize <vps_id>`. savings estimate. |
| o6.5 | traffic analysis tools | 2d | bandwidth usage breakdown by protocol/service. peak traffic analysis. `/traffic <vps_id> <period>`. top talkers/ listeners. |

## phase 4: management panel & vps dashboard (week 11-12)

goal: build out the management panel dashboard with vps-specific features.

### server performance dashboard (p1)
| # | feature | effort | details |
|---|---------|--------|---------|
| p1.1 | server performance monitoring dashboard | 3d | real-time tps graph (last 5min/30min/1hr). memory/cpu usage chart. player count over time. world size tracking. lag spike detection. widget: `/dashboard` embed on discord. |
| p1.2 | server metrics dashboard | 2d | aggregate all metrics in one view. server count, total players, resource usage summary. export metrics to prometheus endpoint. |

### vps dashboard (p2)
| # | feature | effort | details |
|---|---------|--------|---------|
| p2.1 | server access logs | 1d | ssh login attempts, console access, file access. `/logs access <vps_id>`. integration with auth.log. |
| p2.2 | server resource monitoring | 2d | real-time resource dashboard in management panel. cpu/memory/disk/network gauges. historical trend charts. export to grafana via prometheus. |
| p2.3 | resource usage reports | 2d | scheduled reports (daily/weekly/monthly). pdf/csv export. `/report generate <type> <period>`. auto-send to email/discord. |

### templates & config (p3)
| # | feature | effort | details |
|---|---------|--------|---------|
| p3.1 | configuration version control | 2d | track config file changes. `/config history`, `/config diff <version>`, `/config rollback <version>`. git-backed storage. |
| p3.2 | server maintenance scheduler | 2d | schedule maintenance windows. auto-apply updates at scheduled time. `/maintenance schedule <vps_id> <time>`. notify users. |
| p3.3 | database backup automation | 2d | mysql/postgresql dump automation. schedule: hourly/daily/weekly. retention policy. `/db backup create`, `/db backup list`, `/db backup restore <id>`. |

### alerts & updates (p4)
| # | feature | effort | details |
|---|---------|--------|---------|
| p4.1 | server backup notifications | 1d | notify on backup completion/failure. include: size, duration, location. channel: discord dm, webhook, email. |
| p4.2 | resource usage alerts | 1d | already partially done. add management panel alert configuration ui. `/alert test <type>`. alert history log. |
| p4.3 | server health checks (dashboard) | 1d | health check visualization. uptime percentage over time. `/health dashboard`. incident timeline. |

## phase 5: integration & cross-platform (week 13-16)

goal: connect all services into a unified platform with cross-platform features.

### authentication & users (x1)
| # | feature | effort | details |
|---|---------|--------|---------|
| x1.1 | cross-platform authentication | 3d | single sign-on across dashboard, discord, and minecraft. oauth2 flow. link minecraft uuid with discord id. `/link account`. jwt token exchange. |
| x1.2 | shared user management | 2d | already partially done in `unifiedusermanager`. add: profile sync on login, role sync across platforms, user search api. |
| x1.3 | shared user profiles | 2d | unified profile: discord name, minecraft uuid, stats, balance, achievements. `/profile <user>`. bio, social links, vanity url. |

### messaging & notifications (x2)
| # | feature | effort | details |
|---|---------|--------|---------|
| x2.1 | cross-platform messaging | 2d | message bridge: discord <-> minecraft chat. bidirectional. format conversion (discord markdown -> minecraft colors). webhook-based. |
| x2.2 | cross-platform notifications | 2d | already partially done in `crossplatformnotifier`. add: notification preferences per user, priority levels, digest mode (daily summary). |
| x2.3 | cross-platform commands | 3d | execute commands from any platform. `/execute discord <command>` on minecraft, `/execute mc <command>` on discord. permission-checked. audit logged. |
| x2.4 | cross-platform events | 2d | server events broadcast across platforms. player join/leave, achievement unlock, vote received. custom event hooks. |
| x2.5 | cross-platform alerts | 2d | unified alert system. alert types: resource threshold, security, maintenance. delivery channels: discord, in-game, email, sms (webhook). |
| x2.6 | server announcement scheduler | 2d | schedule announcements across platforms. `/announce create <message> <time> <platforms>`. recurring announcements. template support. |

### logging & monitoring (x3)
| # | feature | effort | details |
|---|---------|--------|---------|
| x3.1 | unified logging system | 2d | already partially done in `unifiedlogger`. add: centralized log aggregation, log level filtering, search api, log retention. |
| x3.2 | cross-platform logging | 1d | log all cross-platform events in one place. `/logs cross-platform <filter>`. export to external siem. |
| x3.3 | unified reporting system | 2d | generate reports spanning all services. `/report unified <type> <period>`. usage, billing, security, performance reports. |
| x3.4 | server logs integration | 2d | minecraft server logs -> discord channel. filter by log level. `/logs tail <server>`, `/logs search <query>`. |
| x3.5 | server backup logs | 1d | centralized backup status across all services. backup success/failure rate. `/backup logs <period>`. |

### resource & configuration (x4)
| # | feature | effort | details |
|---|---------|--------|---------|
| x4.1 | unified permission system | 3d | central permission store. permission inheritance across platforms. `/permission set <user> <platform> <permission>`. cache with redis. |
| x4.2 | shared configuration management | 2d | already partially done in `sharedconfigmanager`. add: config versioning, diff view, rollback, bulk update. |
| x4.3 | shared configuration system | 1d | central config repository. environment-specific overlays. `/config set/get/list`. validation on update. |
| x4.4 | shared resource pools | 2d | pool resources (cpu, ram, storage) across vps instances. fair scheduling. pool size adjustment. `/pool create/delete/resize`. |

### backups & resources (x5)
| # | feature | effort | details |
|---|---------|--------|---------|
| x5.1 | integrated backup system | 3d | already partially done in `backupmanager`. add: cross-service backup coordination, atomic multi-service restore, backup verification. |
| x5.2 | unified backup management | 2d | single view of all backups. retention policy engine (per-service + global). `/backup unified list`. restore from unified interface. |
| x5.3 | cross-platform backups | 1d | backup that spans services (minecraft world + discord config + vps data). coordinated restore. |
| x5.4 | resource synchronization | 2d | sync resource allocations across services. resource pool updates propagate to all vps. `/resource sync`. |
| x5.5 | resource allocation management | 2d | unified view of resource allocation vs usage. rebalance suggestion. `/resource rebalance`. |

### metrics & coordination (x6)
| # | feature | effort | details |
|---|---------|--------|---------|
| x6.1 | resource usage tracking | 2d | already partially done in `unifiedresourcetracker`. add: cost allocation, trend analysis, forecasting. |
| x6.2 | unified metrics system | 2d | prometheus metric exports from all services. grafana dashboards. `/metrics unified <period>`. metric annotations for events. |
| x6.3 | cross-platform statistics | 2d | aggregate stats across all platforms. `/stats unified <user>`. player stats + discord activity + vps usage in one view. |
| x6.4 | resource scheduling coordination | 2d | coordinate maintenance windows, backups, scaling events. conflict detection. `/schedule resource <type> <time>`. |
| x6.5 | resource optimization coordination | 2d | cross-service optimization. identify idle resources, recommend consolidation. `/optimize cross-platform`. |

### integration features (x7)
| # | feature | effort | details |
|---|---------|--------|---------|
| x7.1 | integrated monitoring system | 2d | single monitoring view: all services, all metrics. alert correlation. root cause analysis suggestions. |
| x7.2 | integrated maintenance system | 2d | cross-service maintenance windows. dependency-aware ordering. `/maintenance create <services> <window>`. |
| x7.3 | integrated security system | 2d | centralized security monitoring. cross-platform suspicious activity detection. `/security report unified`. |
| x7.4 | integrated resource management | 2d | unified dashboard for all resource allocation. cost tracking. `/resources dashboard`. |

## summary statistics

| phase | features | effort (person-days) |
|-------|----------|---------------------|
| phase 0: foundation & wiring | 9 | 13 |
| phase 1: core minecraft & economy | 16 | 28 |
| phase 2: servers, performance & anti-cheat | 13 | 24 |
| phase 3: discord bot & vps features | 40 | 67 |
| phase 4: management panel & vps dashboard | 10 | 17 |
| phase 5: integration & cross-platform | 30 | 52 |
| total | ~118 | ~201 |

## architecture decisions

- integration service as hub: all cross-platform features go through the integration service (port 9000). it becomes the central nervous system.
- shared database: a shared postgresql database (already in docker-compose) used for cross-service data. individual services keep their own mysql/json for service-specific data.
- message queue: consider adding redis pub/sub (already in docker-compose) for real-time cross-platform events instead of polling.
- single entry per service: each service should have one main entry point that loads all modules. currently both service-core and orchestrator-agent have split entry points.

## immediate next steps

- complete phase 0 - wiring existing code is the highest roi (features are already written)
- establish ci/cd tests for the newly wired features
- then proceed with phase 1 features based on priority
