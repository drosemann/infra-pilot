# Feature 24: BGP Route Manager

## Overview
BGP session management for bring-your-own-IP (BYOIP) scenarios. Prefix announcements, AS-path prepend, community tagging, and integration with BIRD/FRR routing daemons.

## Components

### Integration Service: `networking/bgp_manager.py`
- `BGPRouteManager` - Core BGP management
  - BGP session CRUD (eBGP, iBGP, route reflector)
  - Prefix announcement management
  - AS-path prepend configuration
  - Community tagging (standard, large, extended)
  - Route map / prefix list management
  - BIRD/FRR configuration generation
  - Session state monitoring
  - RPKI/ROA validation

### Orchestrator Agent: `cogs/bgp_manager.py`
- Discord commands:
  - `/bgp session create` - Create BGP session
  - `/bgp session list` - List BGP sessions
  - `/bgp session status` - Show session status
  - `/bgp prefix announce` - Announce prefix
  - `/bgp prefix withdraw` - Withdraw prefix
  - `/bgp prefix list` - List announced prefixes
  - `/bgp community` - Show community tags

### Management Panel: `pages/networking/BGPPage.tsx`
- BGP session management table
- Prefix announcement dashboard
- Route map visual editor
- BGP status monitoring
- AS-path analysis tool
- RPKI/ROA validation overview

### Mobile: `app/networking/bgp.tsx`
- BGP session status overview
- Alert notifications for BGP changes
- Prefix list view

### CLI Commands
- `ipilot bgp session create --asn <asn> --neighbor <ip>`
- `ipilot bgp session list`
- `ipilot bgp prefix announce --prefix <cidr>`
- `ipilot bgp prefix withdraw --prefix <cidr>`

## API Endpoints
- `GET /api/networking/bgp/sessions` - List BGP sessions
- `POST /api/networking/bgp/sessions` - Create BGP session
- `GET /api/networking/bgp/sessions/{id}` - Get session details
- `PUT /api/networking/bgp/sessions/{id}` - Update session
- `DELETE /api/networking/bgp/sessions/{id}` - Delete session
- `POST /api/networking/bgp/sessions/{id}/reset` - Reset session
- `GET /api/networking/bgp/prefixes` - List announced prefixes
- `POST /api/networking/bgp/prefixes` - Announce prefix
- `DELETE /api/networking/bgp/prefixes/{id}` - Withdraw prefix
- `GET /api/networking/bgp/communities` - List community tags
- `POST /api/networking/bgp/communities` - Create community tag
- `GET /api/networking/bgp/routes` - BGP routing table viewer

## Data Models

### BGPSession
- id, name, local_asn, remote_asn, neighbor_ip
- type (ebgp/ibgp/rr-client), multihop_ttl
- source_interface, source_ip, password (encrypted)
- hold_time, keepalive_interval
- status (idle/connect/active/opensent/openconfirm/established)
- address_families (ipv4, ipv6, l2vpn)
- error_count, last_error

### BGPAnnouncement
- id, session_id, prefix (CIDR), description
- as_path_prepend (list of ASNs)
- communities list, large_communities list
- rpki_status (valid/invalid/unknown)
- enabled, created_at

### CommunityTag
- id, name, community (standard: "ASN:VAL")
- description, type (standard/large/extended)
- session_ids (list of associated sessions)

## Implementation Details
- BIRD/FRR daemon control via Unix sockets
- Configuration file generation from templates
- Session state machine monitoring
- Route advertisement with BGP attributes
- RPKI validation via Routinator/Cloudflare API
- Graceful shutdown (graceful-restart capability)
- Prefix limit / max-prefix configuration
- BGP community-based policy tagging
- AS-path prepend for traffic engineering
- BGP-LS (link-state) for traffic engineering

## Testing
- Session state machine transitions
- Configuration generation verification
- Prefix announcement/withdrawal lifecycle
- RPKI validation scenarios
- Community tag enforcement
- Route flap damping
