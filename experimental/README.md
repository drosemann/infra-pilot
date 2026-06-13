# Experimental — Extended Features

This directory contains functionality that was refactored out of the core MVP scope to reduce system complexity and maintain focus on the vision: **"developer-first alternative to Pterodactyl with modern DevEx tooling."**

These features are preserved for reference and future iterations. They are NOT part of the core product.

## Contents

| Directory | Original Location | Description |
|-----------|------------------|-------------|
| `integration-service/` | `services/integration-service/` | Central API gateway with 2000+ routes (auth, compliance, SOC, CDN, AI, etc.) |
| `orchestrator-cogs/` | `services/orchestrator-agent/cogs/` | 76 expanded Discord bot cogs (AI, edge, IoT, cellular, marketplace, etc.) |
| `discord-modules/` | `services/discord-service/modules/` | 30 expanded Discord modules (economy, gaming, code review, etc.) |
| `management-panel-expanded/` | `services/management-panel/` | V3/V4 API routes, billing, knowledge base, dashboard builder, plugin marketplace, terminal, change management, and 25 expanded frontend pages (finops, networking, compliance, marketplace, BI, geo) |
| `mobile/` | Root `mobile/` | React Native (Expo) mobile app |
| `service-core/` | `services/service-core/` | Java BungeeCord Minecraft server plugin |
| `terraform-provider/` | `infra/terraform/` | Custom Go Terraform provider |
| `infra-edge-iot/` | `infra/edge/`, `infra/green/` | Edge computing, IoT provisioning, green computing |
| `cli-commands/` | `cli/ipilot/commands/` | Expanded CLI command modules (AIops, compliance, data platform, emerging tech, finops, platform engineering, resiliency, SOC) |
| `desktop/` | `services/management-panel/` | Tauri v2 and Zig/zero-native desktop wrappers |
| `branding/` | Root `branding/` | Logo assets and brand guidelines |
| `tests/` | Root `tests/` | Test suites for expanded feature domains |

## Re-enabling Features

If a feature is needed later:
1. Move the directory back to its original location
2. Re-register any routes in the appropriate server file
3. Add back any frontend imports/components
4. Restore the docker-compose service if applicable

## Note

These modules are preserved as-is with no active maintenance. They serve as a reference for the original design intent and may contain useful patterns for future development.
