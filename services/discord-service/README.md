# Discord Server Creator Bot

Create and provision Pterodactyl servers from Discord workflows.

## Current status

The bot now ships with a `package.json` declaring all dependencies.

## Features

- **Server provisioning** — Pterodactyl integration with multiple templates (Minecraft, Node.js, TeamSpeak, Database, Python), user registration, and automated server creation.
- **Ticket system** — Basic and advanced multi-category tickets with priority levels, staff assignment, and close with rating/feedback.
- **Economy system** — In-server currency with balance, payments, and leaderboard.
- **Moderation** — Warning system, message filtering (bad words, spam, domain whitelist), and channel cleanup (bulk purge).
- **Verification** — Captcha-based member verification with configurable roles, plus account/guild age verification levels.
- **Welcome messages** — Configurable join messages in channels and DMs with template placeholders.
- **Voice management** — Manual voice channel creation with limit/lock/unlock, plus temporary voice channels via "Join to Create" with auto-cleanup and ownership transfer.
- **Activity tracking** — Tracks messages and voice sessions with activity leaderboards and personal stats.
- **Event scheduling** — Create, list, and remind about events with optional recurring intervals.
- **Polls** — Multi-option polls with anonymous mode, timed voting, and reaction-based voting.
- **Role management** — Role creation, editing, deletion, hierarchy display, and reaction role menus.
- **Custom commands** — Per-server custom text/embed commands.
- **Custom prefixes** — Per-server configurable command prefix.
- **Message scheduling** — Schedule one-time or recurring (cron) messages.
- **Message logging** — Log message edits and deletions to configurable channels.
- **Message archival** — Export channel messages to JSON, CSV, or TXT.
- **Channel categories** — Create and manage channel categories with permission syncing.
- **Topic rotation** — Scheduled rotating channel topics.
- **Server status widgets** — Live system info (CPU, RAM, uptime) with auto-refresh.
- **Stats graphs** — Visual server statistics with generated charts.
- **Dashboard** — Interactive system dashboard with refresh support.

## Prerequisites

- Node.js 18+
- A Discord bot application
- A reachable Pterodactyl panel

## Branding

- Cosmic Infra branding is applied across the Infra Pilot UI. Tokens: Primary #6C5CE7, Secondary #EC4899, Accent #22D3EE.
- Logo variants are available, with a simple selector implemented in the management panel to switch between default and alt IP lockup designs.
- UI elements reuse the branding tokens for consistency (buttons, inputs, cards).

## Installation

```bash
npm install
```

## Configuration

```bash
cp .env.example .env
```

Update `.env` with your credentials and IDs.

Environment variables include:

- `DISCORD_TOKEN`
- `PTERODACTYL_API_URL`
- `PTERODACTYL_API_KEY`
- `SERVER_CREATION_CHANNEL_ID`
- `SERVER_CREATOR_ROLE_ID`
- `MAX_SERVERS_PER_USER`
- `MINECRAFT_EGG_ID`, `NODEJS_EGG_ID`, `TEAMSPEAK_EGG_ID`, `DATABASE_EGG_ID`, `PYTHON_EGG_ID`
- `LOCATION_ID`

## Modules

The bot ships with 20+ modular systems in `modules/`:

| Module | Description |
|--------|-------------|
| `welcomeMessages` | Configurable join messages in channels and DMs |
| `verificationSystem` | Captcha-based member verification with role assignment |
| `verificationLevels` | Account/guild age and role-based verification tiers |
| `advancedTicketSystem` | Multi-category tickets with priority, rating, and feedback |
| `serverStatus` | Live CPU/RAM/uptime status widget with auto-refresh |
| `eventScheduler` | Event creation, reminders, and recurring support |
| `pollCreator` | Multi-option polls with anonymous mode and timed voting |
| `roleHierarchy` | Role CRUD, hierarchy display, and reaction role menus |
| `customCommands` | Per-server custom text/embed commands |
| `prefixSettings` | Per-server custom command prefix |
| `warningSystem` | User warning management with history and removal |
| `messageFilter` | Bad word, spam, and domain whitelist filtering |
| `messageLogger` | Message edit/delete logging |
| `messageScheduler` | Schedule one-time or recurring messages (cron) |
| `activityTracker` | Message and voice activity tracking with leaderboards |
| `voiceManager` | Manual voice channel management (create, lock, limit) |
| `tempVoiceChannels` | Temporary voice channels via "Join to Create" |
| `channelCleanup` | Bulk message purge by user, bot, or all |
| `messageArchive` | Channel message export to JSON/CSV/TXT |
| `categoryManager` | Channel category creation, management, permission sync |
| `topicRotation` | Scheduled rotating channel topics |
| `statsGraphs` | Server statistics visualization with charts |

Pre-existing modules: `ticketSystem`, `ticketCommands`, `statsCommands`, `roleManager`, `economyCommands`, `dashboard`.

## Syntax check

```bash
node --check index.js
```

## Usage after dependencies are installed

```bash
node index.js
```

Then run `/server create` in your configured channel.

## License

This module is distributed under the repository MIT License. See [LICENSE](../../LICENSE).
