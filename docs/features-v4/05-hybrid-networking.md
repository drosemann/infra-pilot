# Feature 5: Hybrid Networking Mesh

## Overview
Automatic VPN/GRE tunnel mesh between on-prem, edge, and cloud VPCs. BGP route propagation, bandwidth aggregation, latency-based routing.

## Components
- `hybrid_networking.py` — Mesh tunnel manager, BGP route propagation
- `HybridNetworkingCog` — Discord commands for mesh network
- `HybridNetworking.tsx` — React mesh network topology page
- CLI commands in `cli/ipilot/commands/hybrid_cloud/hybrid_networking.py`

## API Endpoints
- `GET /api/mesh/peers` — List mesh peers
- `POST /api/mesh/peers` — Register new peer
- `GET /api/mesh/tunnels` — List tunnels
- `POST /api/mesh/tunnels` — Create tunnel
- `GET /api/mesh/topology` — Get mesh topology
- `POST /api/mesh/routes` — Add BGP route

## Supported Tunnel Types
VPN, GRE, VXLAN, WireGuard, IPSec
