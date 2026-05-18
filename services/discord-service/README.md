# Discord Server Creator Bot

Create and provision Pterodactyl servers from Discord workflows.

## Current status

This directory currently contains the bot source (`index.js`, `integration.js`) and `.env.example`, but no service-local `package.json`. Before running the bot in a fresh checkout, add a dependency manifest or provide the required packages from your runtime environment.

Expected runtime dependencies:

- Node.js 18+
- `discord.js`
- `axios`
- `dotenv`

## Features

- Multiple server templates (Minecraft, Node.js, TeamSpeak, Database, Python).
- User registration and validation flow.
- Automated Pterodactyl user/server creation.
- Optional role assignment after provisioning.
- Configurable per-user server limits.

## Prerequisites

- Node.js 18+
- A Discord bot application
- A reachable Pterodactyl panel
- Installed/provided Node dependencies listed above

## Branding

- Cosmic Infra branding is applied across the Infra Pilot UI. Tokens: Primary #6C5CE7, Secondary #EC4899, Accent #22D3EE.
- Logo variants are available, with a simple selector implemented in the management panel to switch between default and alt IP lockup designs.
- UI elements reuse the branding tokens for consistency (buttons, inputs, cards).

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
