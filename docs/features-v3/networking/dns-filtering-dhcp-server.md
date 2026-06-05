# Feature 28: DNS Filtering / DHCP Server

## Overview
Pi-hole/AdGuard Home integration for DNS-based content filtering. DHCP server management with per-client policy configuration, blocklist management, and analytics dashboard.

## Components

### Integration Service: `networking/dns_filtering.py`
- `DNSFilterManager` - Core DNS filtering management
  - Pi-hole/AdGuard Home instance management
  - DNS blocklist/allowlist management
  - DHCP server configuration
  - Per-client policy assignment
  - Filtering statistics and analytics
  - Upstream DNS configuration
  - Conditional forwarding
  - CNAME cloaking protection
  - Query log viewer and search

### Orchestrator Agent: `cogs/dns_filter.py`
- Discord commands:
  - `/dnsfilter status` - DNS filtering status
  - `/dnsfilter blocklist add` - Add domain to blocklist
  - `/dnsfilter blocklist remove` - Remove domain from blocklist
  - `/dnsfilter allowlist add` - Add to allowlist
  - `/dnsfilter stats` - Query statistics
  - `/dnsfilter client policy` - Set client policy
  - `/dnsfilter dhcp leases` - List DHCP leases
  - `/dnsfilter disable` - Temporarily disable filtering

### Management Panel: `pages/networking/DNSFilterPage.tsx`
- Filtering dashboard with query stats
- Blocklist/allowlist management
- DHCP server configuration
- Client policy matrix
- Query log with filters
- Top blocked domains
- Network overview with filtering status
- Upstream DNS configuration

### CLI Commands
- `ipilot dnsfilter status`
- `ipilot dnsfilter blocklist add <domain>`
- `ipilot dnsfilter blocklist list`
- `ipilot dnsfilter stats --period 24h`

## API Endpoints
- `GET /api/networking/dnsfilter/status` - Filtering status
- `GET /api/networking/dnsfilter/stats` - Query statistics
- `GET /api/networking/dnsfilter/querylog` - Query log
- `GET /api/networking/dnsfilter/blocklist` - Get blocklist
- `POST /api/networking/dnsfilter/blocklist` - Add to blocklist
- `DELETE /api/networking/dnsfilter/blocklist/{id}` - Remove from blocklist
- `GET /api/networking/dnsfilter/allowlist` - Get allowlist
- `POST /api/networking/dnsfilter/allowlist` - Add to allowlist
- `DELETE /api/networking/dnsfilter/allowlist/{id}` - Remove from allowlist
- `GET /api/networking/dnsfilter/dhcp/config` - DHCP configuration
- `PUT /api/networking/dnsfilter/dhcp/config` - Update DHCP config
- `GET /api/networking/dnsfilter/dhcp/leases` - DHCP leases
- `GET /api/networking/dnsfilter/clients` - Client list
- `PUT /api/networking/dnsfilter/clients/{ip}/policy` - Set client policy

## Data Models

### FilterInstance
- id, type (pihole/adguard), status (running/stopped/error)
- version, port, web_port
- dns_upstream (list of DNS servers)
- blocking_enabled, blocklist_count
- queries_today, blocked_today, percentage_blocked
- dhcp_enabled, dhcp_range_start, dhcp_range_end

### BlocklistEntry
- id, domain, type (blocked/allowed)
- source (manual/gravity/adlist), list_name
- enabled, created_at, comment
- hit_count, last_hit

### DHCPLease
- id, mac_address, ip_address, hostname
- expires_at, state (active/static/expired)
- vendor_class, client_id

### ClientPolicy
- mac_address, ip_address, client_name
- filtering_enabled, blocking_mode (default/strict/disabled)
- rate_limit, query_log_enabled
- groups list

## Implementation Details
- Pi-hole API integration (v6)
- AdGuard Home API integration
- DNS query log storage and indexing
- Blocklist management via gravity/adlist
- DHCP via dnsmasq integration
- Per-client rate limiting
- Regex domain blocking
- CNAME cloaking detection
- Top clients/domains analytics
- Periodic blocklist updates

## Testing
- Blocklist/allowlist operations
- Query log indexing accuracy
- DHCP lease management
- Client policy enforcement
- Upstream DNS failover
- Blocklist update process
- API compatibility with Pi-hole/AdGuard
