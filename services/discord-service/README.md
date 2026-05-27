# discord server creator bot

create and provision pterodactyl servers from discord workflows.

## current status

the bot now ships with a `package.json` declaring all dependencies.

## features

- server provisioning — pterodactyl integration with multiple templates (minecraft, node.js, teamspeak, database, python), user registration, and automated server creation.
- ticket system — basic and advanced multi-category tickets with priority levels, staff assignment, and close with rating/feedback.
- economy system — in-server currency with balance, payments, and leaderboard.
- moderation — warning system, message filtering (bad words, spam, domain whitelist), and channel cleanup (bulk purge).
- verification — captcha-based member verification with configurable roles, plus account/guild age verification levels.
- welcome messages — configurable join messages in channels and dms with template placeholders.
- voice management — manual voice channel creation with limit/lock/unlock, plus temporary voice channels via "join to create" with auto-cleanup and ownership transfer.
- activity tracking — tracks messages and voice sessions with activity leaderboards and personal stats.
- event scheduling — create, list, and remind about events with optional recurring intervals.
- polls — multi-option polls with anonymous mode, timed voting, and reaction-based voting.
- role management — role creation, editing, deletion, hierarchy display, and reaction role menus.
- custom commands — per-server custom text/embed commands.
- custom prefixes — per-server configurable command prefix.
- message scheduling — schedule one-time or recurring (cron) messages.
- message logging — log message edits and deletions to configurable channels.
- message archival — export channel messages to json, csv, or txt.
- channel categories — create and manage channel categories with permission syncing.
- topic rotation — scheduled rotating channel topics.
- server status widgets — live system info (cpu, ram, uptime) with auto-refresh.
- stats graphs — visual server statistics with generated charts.
- dashboard — interactive system dashboard with refresh support.
- token validation — validates `discord_token` via management panel endpoint before container start to prevent silent runtime failures.
- git push notifications — receives deployment webhook events from the orchestrator and posts status updates (deploy started, completed, failed) to discord channels.

## prerequisites

- node.js 18+
- a discord bot application
- a reachable pterodactyl panel

## branding

- cosmic infra branding is applied across the infra pilot ui. tokens: primary #6c5ce7, secondary #ec4899, accent #22d3ee.
- logo variants are available, with a simple selector implemented in the management panel to switch between default and alt ip lockup designs.
- ui elements reuse the branding tokens for consistency (buttons, inputs, cards).

## installation

```bash
npm install
```

## configuration

```bash
cp .env.example .env
```

update `.env` with your credentials and ids.

environment variables include:

- `discord_token`
- `pterodactyl_api_url`
- `pterodactyl_api_key`
- `server_creation_channel_id`
- `server_creator_role_id`
- `max_servers_per_user`
- `minecraft_egg_id`, `nodejs_egg_id`, `teamspeak_egg_id`, `database_egg_id`, `python_egg_id`
- `location_id`

## modules

the bot ships with 20+ modular systems in `modules/`:

| module | description |
|--------|-------------|
| `welcomeMessages` | configurable join messages in channels and dms |
| `verificationSystem` | captcha-based member verification with role assignment |
| `verificationLevels` | account/guild age and role-based verification tiers |
| `advancedTicketSystem` | multi-category tickets with priority, rating, and feedback |
| `serverStatus` | live cpu/ram/uptime status widget with auto-refresh |
| `eventScheduler` | event creation, reminders, and recurring support |
| `pollCreator` | multi-option polls with anonymous mode and timed voting |
| `roleHierarchy` | role crud, hierarchy display, and reaction role menus |
| `customCommands` | per-server custom text/embed commands |
| `prefixSettings` | per-server custom command prefix |
| `warningSystem` | user warning management with history and removal |
| `messageFilter` | bad word, spam, and domain whitelist filtering |
| `messageLogger` | message edit/delete logging |
| `messageScheduler` | schedule one-time or recurring messages (cron) |
| `activityTracker` | message and voice activity tracking with leaderboards |
| `voiceManager` | manual voice channel management (create, lock, limit) |
| `tempVoiceChannels` | temporary voice channels via "join to create" |
| `channelCleanup` | bulk message purge by user, bot, or all |
| `messageArchive` | channel message export to json/csv/txt |
| `categoryManager` | channel category creation, management, permission sync |
| `topicRotation` | scheduled rotating channel topics |
| `statsGraphs` | server statistics visualization with charts |

pre-existing modules: `ticketSystem`, `ticketCommands`, `statsCommands`, `roleManager`, `economyCommands`, `dashboard`.

## syntax check

```bash
node --check index.js
```

## usage after dependencies are installed

```bash
node index.js
```

then run `/server create` in your configured channel.

## license

this module is distributed under the repository mit license. see [license](../../license).
