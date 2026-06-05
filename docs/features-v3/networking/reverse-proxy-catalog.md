# Feature 25: Reverse Proxy Catalog

## Overview
Centralized reverse proxy management supporting Nginx, Caddy, and Traefik. Auto-SSL via Let's Encrypt, upstream health checks, rate limiting, and access log viewer.

## Components

### Integration Service: `networking/reverse_proxy.py`
- `ReverseProxyManager` - Core reverse proxy management
  - Proxy instance CRUD (nginx/caddy/traefik)
  - Virtual host/server block management
  - Upstream server pools with health checks
  - SSL certificate management (auto via Let's Encrypt)
  - Rate limiting configuration
  - Access log aggregation and viewer
  - Configuration validation and diff
  - Template-based config generation

### Orchestrator Agent: `cogs/proxy_manager.py`
- Discord commands:
  - `/proxy create` - Create reverse proxy instance
  - `/proxy list` - List proxy instances
  - `/proxy status` - Show proxy status
  - `/proxy host add` - Add virtual host
  - `/proxy host remove` - Remove virtual host
  - `/proxy ssl renew` - Renew SSL certificates
  - `/proxy restart` - Restart proxy

### Management Panel: `pages/networking/ProxyPage.tsx`
- Proxy instance dashboard
- Virtual host management table
- Upstream pool visual editor
- SSL certificate status
- Access log viewer with search
- Rate limit configuration
- Config editor with preview

### Mobile: `app/networking/proxy.tsx`
- Proxy instance status
- SSL certificate expiry warnings
- Basic upstream management

### CLI Commands
- `ipilot proxy create --type nginx|caddy|traefik`
- `ipilot proxy list`
- `ipilot proxy host add <proxy_id> --domain <domain> --upstream <url>`
- `ipilot proxy ssl list`

## API Endpoints
- `GET /api/networking/proxy/instances` - List proxy instances
- `POST /api/networking/proxy/instances` - Create proxy instance
- `GET /api/networking/proxy/instances/{id}` - Get instance details
- `PUT /api/networking/proxy/instances/{id}` - Update instance
- `DELETE /api/networking/proxy/instances/{id}` - Delete instance
- `POST /api/networking/proxy/instances/{id}/restart` - Restart proxy
- `GET /api/networking/proxy/instances/{id}/hosts` - List virtual hosts
- `POST /api/networking/proxy/instances/{id}/hosts` - Add virtual host
- `PUT /api/networking/proxy/instances/{id}/hosts/{host_id}` - Update host
- `DELETE /api/networking/proxy/instances/{id}/hosts/{host_id}` - Remove host
- `GET /api/networking/proxy/instances/{id}/ssl` - SSL certificate status
- `POST /api/networking/proxy/instances/{id}/ssl/renew` - Renew SSL certs
- `GET /api/networking/proxy/instances/{id}/logs` - Access logs
- `GET /api/networking/proxy/instances/{id}/upstreams` - Upstream pools

## Data Models

### ProxyInstance
- id, name, type (nginx/caddy/traefik), version
- status (running/stopped/error), port, admin_port
- config_path, ssl_cert_path, ssl_key_path
- container_id (if containerized)
- access_log_path, error_log_path

### VirtualHost
- id, proxy_id, domain, aliases list
- upstream_url, upstream_pool_id
- ssl_enabled, ssl_status (active/expiring/expired)
- ssl_expires_at, ssl_issuer
- rate_limit_rps, rate_limit_burst
- custom_config (JSON for advanced directives)
- enabled, created_at

### UpstreamPool
- id, proxy_id, name, method (round_robin/least_conn/ip_hash)
- servers (list of url + weight + max_fails)
- health_check_path, health_check_interval
- health_check_timeout, healthy_threshold

## Implementation Details
- Nginx: config file generation + reload via signal
- Caddy: Caddyfile generation + API admin interface
- Traefik: dynamic config via file provider or API
- SSL via acme.sh / certbot / Caddy built-in ACME
- Docker container deployment for each proxy type
- Configuration validation before apply
- Zero-downtime reload for nginx (USR2)
- Rate limiting via nginx limit_req / Caddy rate_limit
- Access log parsing and indexing
- Health checks with configurable thresholds
- Configuration templating with Jinja2

## Testing
- Config generation for each proxy type
- SSL certificate lifecycle
- Virtual host CRUD operations
- Health check state transitions
- Rate limiting enforcement
- Access log parsing
- Configuration validation
- Reload/restart operations
