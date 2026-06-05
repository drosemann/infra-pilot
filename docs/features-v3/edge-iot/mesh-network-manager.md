# Feature 4: Mesh Network Manager

## Overview
Manage WireGuard and Tinc mesh VPNs across edge nodes. Automatic routing, peer discovery, encrypted tunnels, and visual topology map.

## Capabilities
- WireGuard mesh VPN management
- Tinc mesh VPN with automatic routing
- Automatic peer discovery and key exchange
- Encrypted tunnels with perfect forward secrecy
- Visual topology map with connection status
- Bandwidth monitoring per tunnel
- Automatic failover and route optimization
- Network segmentation (subnets per mesh)
- Dynamic IP assignment
- NAT traversal support

## Mesh Types

### WireGuard Mesh
- Full mesh topology (every node connects to every other)
- Peer configuration generation
- Automatic key pair generation and distribution
- PersistentKeepalive for NAT traversal
- MTU optimization per link

### Tinc Mesh
- Self-healing mesh with automatic route calculation
- Spanning tree protocol for loop prevention
- Meta-connections for control, raw UDP for data
- Public/private key authentication
- Host files managed centrally

## Configuration Model

```yaml
mesh_network:
  name: "production-edge"
  type: wireguard  # or tinc
  subnet: "10.100.0.0/16"
  mtu: 1420
  peers:
    - node_id: "node-001"
      address: "10.100.0.1"
      endpoint: "203.0.113.10:51820"
      public_key: "xTIBAQ..." 
      allowed_ips: ["10.100.0.0/24"]
    - node_id: "node-002"
      address: "10.100.0.2"
      endpoint: "203.0.113.20:51820"
      public_key: "yUJCBQ..."
      allowed_ips: ["10.100.0.0/24"]
  routing:
    type: full_mesh  # or hub_and_spoke, partial
    metrics:
      - latency
      - bandwidth
      - packet_loss
  monitoring:
    check_interval: 30
    alert_on_disconnect: true
    metrics_retention_days: 90
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/mesh/networks | List mesh networks |
| POST | /api/v1/mesh/networks | Create mesh network |
| GET | /api/v1/mesh/networks/{id} | Get network details |
| PUT | /api/v1/mesh/networks/{id} | Update network config |
| DELETE | /api/v1/mesh/networks/{id} | Delete network |
| POST | /api/v1/mesh/networks/{id}/peers | Add peer |
| DELETE | /api/v1/mesh/networks/{id}/peers/{peer_id} | Remove peer |
| GET | /api/v1/mesh/networks/{id}/topology | Get topology data |
| GET | /api/v1/mesh/networks/{id}/metrics | Get tunnel metrics |
| POST | /api/v1/mesh/networks/{id}/restart | Restart mesh |

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/mesh_network_manager.py`
- Test with simulated WireGuard/Tinc configurations
- CLI commands for mesh management
