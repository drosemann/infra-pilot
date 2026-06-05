# Feature 60: Game Server Dashboard

## Overview
Live status overview of all game servers: players online, TPS, memory, uptime. Embedded mini-map/live player list.

## Components
- **Management Panel Page**: `gaming/GameServerDashboard.tsx` - Main dashboard
- **Management Panel Component**: `gaming/GameServerCard.tsx` - Server card component
- **Orchestrator Agent Cog**: `gaming/game_server_stats.py` - Stats collection

## Features
- Live player count per server
- TPS (ticks per second) monitoring
- Memory and CPU usage
- Uptime tracking
- Embedded mini-map
- Live player list
- Server version tracking
- Performance history
- Alert thresholds
- Quick actions (restart, command, backup)
