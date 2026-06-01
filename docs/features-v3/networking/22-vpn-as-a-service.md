# Feature 22: VPN as a Service

## Overview
One-click WireGuard/OpenVPN server deployment with client configuration generation, QR codes for mobile, usage statistics, and certificate expiry management.

## Components

### Integration Service: `networking/vpn_service.py`
- `VPNServiceManager` - Core VPN management
  - WireGuard server deployment and management
  - OpenVPN server deployment and management
  - Client configuration generation (conf files, QR codes)
  - Certificate management (CA, server, client certs)
  - Usage statistics (bandwidth, connected clients)
  - Expiry management for client access

### Orchestrator Agent: `cogs/vpn_manager.py`
- Discord commands:
  - `/vpn create` - Create a VPN server
  - `/vpn list` - List VPN servers
  - `/vpn status` - Show VPN server status
  - `/vpn client add` - Add a client
  - `/vpn client remove` - Remove a client
  - `/vpn client config` - Get client config
  - `/vpn restart` - Restart VPN server

### Management Panel: `pages/networking/VPNPage.tsx`
- VPN server deployment wizard
- Client management table
- Configuration download and QR display
- Usage statistics dashboard
- Certificate management

### Mobile: `app/networking/vpn.tsx`
- VPN server status
- Client configuration import
- QR code scanner for config
- Connection status

### CLI Commands
- `ipilot vpn create --type wireguard|openvpn`
- `ipilot vpn list`
- `ipilot vpn client add <vpn_id> <name>`
- `ipilot vpn client config <vpn_id> <client_id>`

## API Endpoints
- `GET /api/networking/vpn/servers` - List VPN servers
- `POST /api/networking/vpn/servers` - Create VPN server
- `GET /api/networking/vpn/servers/{id}` - Get VPN server details
- `DELETE /api/networking/vpn/servers/{id}` - Delete VPN server
- `POST /api/networking/vpn/servers/{id}/start` - Start VPN server
- `POST /api/networking/vpn/servers/{id}/stop` - Stop VPN server
- `GET /api/networking/vpn/servers/{id}/clients` - List clients
- `POST /api/networking/vpn/servers/{id}/clients` - Add client
- `DELETE /api/networking/vpn/servers/{id}/clients/{client_id}` - Remove client
- `GET /api/networking/vpn/servers/{id}/clients/{client_id}/config` - Get client config
- `GET /api/networking/vpn/servers/{id}/usage` - Get usage statistics
- `POST /api/networking/vpn/servers/{id}/restart` - Restart VPN server

## Data Models

### VPNServer
- id, name, type (wireguard/openvpn), status (running/stopped/error)
- port, protocol (udp/tcp), interface_name
- public_ip, public_key, private_key (encrypted)
- dns_servers, allowed_ips, mtu
- created_at, expires_at

### VPNClient
- id, server_id, name, enabled
- public_key (wg), private_key (encrypted)
- assigned_ip, allowed_ips
- dns_servers, persistent_keepalive
- bytes_sent, bytes_received
- connected, last_handshake
- created_at, expires_at

## Implementation Details
- WireGuard via wg-quick/wg utility
- OpenVPN via easy-rsa for certificate management
- QR codes via qrcode Python library
- Config templates stored in database
- Usage tracking via iptables counters
- Auto-renewal for expiring certificates
- Rate limiting per client

## Testing
- Unit tests for config generation
- Integration tests for server lifecycle
- Certificate management tests
- Client connection simulation
- QR code generation tests
