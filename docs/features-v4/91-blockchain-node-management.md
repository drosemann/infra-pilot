# Feature 91: Blockchain Node Management

## Overview
One-click deployment and management of Ethereum, Solana, Polygon, Avalanche, and other blockchain nodes. Includes staking dashboard, validator management, and node health monitoring.

## Capabilities
- One-click node deployment for major blockchains
- Node health monitoring and auto-restart
- Staking and validator management dashboard
- Multi-network support (mainnet, testnet, devnet)
- Node snapshot and backup
- RPC endpoint management
- Validator key management

## Architecture
1. **Integration Module** (`services/integration-service/src/emerging_tech/blockchain_nodes.py`): Core node lifecycle management (deploy, start, stop, delete)
2. **Orchestrator Cog** (`services/orchestrator-agent/cogs/emerging_tech/blockchain_nodes.py`): Discord bot commands for blockchain ops
3. **Management Panel** (`services/management-panel/src/pages/emerging-tech/BlockchainNodes.tsx`): Visual node management dashboard
4. **CLI Commands** (`cli/ipilot/commands/emerging_tech/blockchain_nodes.py`): Terminal-based node operations

## Data Model
- `BlockchainNode`: id, chain, node_type, network, status, label, rpc_url, p2p_port, created_at
- `DeploymentConfig`: chain, node_type, network, port, extra_args, snapshot_url
- `ValidatorInfo`: address, status, stake_amount, commission_rate, rewards_earned

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/blockchain/nodes | List all nodes |
| POST | /api/v1/blockchain/nodes | Deploy new node |
| GET | /api/v1/blockchain/nodes/{id} | Get node details |
| DELETE | /api/v1/blockchain/nodes/{id} | Remove node |
| POST | /api/v1/blockchain/nodes/{id}/start | Start node |
| POST | /api/v1/blockchain/nodes/{id}/stop | Stop node |

## Security
- Validator keys encrypted at rest
- RPC access restricted by IP whitelist
- Rate limiting on staking operations
