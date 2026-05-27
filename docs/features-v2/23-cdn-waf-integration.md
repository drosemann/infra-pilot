# feature 23: cdn & waf integration

| metadata | value |
|----------|-------|
| feature id | 23 |
| feature name | cdn & waf integration |
| primary service | integration service |
| effort estimate | medium (4-6 pt) |
| status | planned |

## 1. overview

one-click cloudflare / bunny cdn provisioning and waf management directly from the panel. users select a provider, choose a plan, and the system automatically provisions the cdn, configures caching rules, applies waf security policies, enables ddos mitigation, and manages ssl/tls certificates.

### goals

- eliminate manual cdn setup friction with a fully automated workflow
- provide a unified interface across multiple cdn providers
- enforce security baseline via waf rules and ddos protection
- enable per-environment cache rule management (dev / staging / prod)
- support ssl/tls certificate provisioning and renewal

## 2. architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Panel (UI)                           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ CDN Setup    │  │ Cache Rules  │  │ WAF / DDoS Config│  │
│  │ Wizard       │  │ Manager      │  │ Manager           │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬──────────┘  │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Integration Service                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CDN Provider Abstraction Layer          │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│  │  │ Cloudflare  │  │ Bunny CDN    │  │ (Future:   │  │   │
│  │  │ Adapter     │  │ Adapter      │  │  Fastly…)  │  │   │
│  │  └──────┬──────┘  └──────┬───────┘  └──────┬─────┘  │   │
│  └─────────┼─────────────────┼─────────────────┼────────┘   │
│            │                 │                               │
│  ┌─────────▼─────────────────▼─────────────────────────┐    │
│  │           Rule Engine / Orchestrator                 │    │
│  │  ┌──────────┐ ┌───────────┐ ┌───────────────────┐   │    │
│  │  │Cache Rule│ │ WAF Rule  │ │ DDoS / Security   │   │    │
│  │  │Manager   │ │ Manager   │ │ Profile Manager   │   │    │
│  │  └──────────┘ └───────────┘ └───────────────────┘   │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌──────────┐        ┌──────────┐        ┌──────────────┐
│Cloudflare│        │Bunny CDN │        │ Let's Encrypt │
│  API     │        │  API     │        │ / ACME        │
└──────────┘        └──────────┘        └──────────────┘
```

### component responsibilities

| component | role |
|-----------|------|
| panel | ui forms, wizards, dashboards for cdn/waf management |
| integration service | provider abstraction, orchestration, rule management |
| cdn provider adapter | type-safe api client for each provider |
| rule engine | compiles panel config into provider-specific api calls |
| acme client | automatic ssl/tls certificate issuance and renewal |

## 3. data model

### `cdn_providers`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| name | varchar | e.g. "cloudflare", "bunny" |
| display_name | varchar | e.g. "cloudflare" |
| enabled | boolean | whether the provider is available |
| config_schema | jsonb | json schema for provider-specific config |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `cdn_zones`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| environment_id | uuid | fk → environments.id |
| provider_id | uuid | fk → cdn_providers.id |
| provider_zone_id | varchar | id returned by the provider |
| domain | varchar | the domain being proxied |
| plan | varchar | e.g. "free", "pro", "business" |
| status | enum | provisioning, active, failed, suspended |
| config | jsonb | provider-specific zone config |
| ssl_status | enum | pending, active, expired |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `cache_rules`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| zone_id | uuid | fk → cdn_zones.id |
| name | varchar | human-readable rule name |
| description | text | |
| priority | int | rule evaluation order |
| criteria | jsonb | match conditions (path, query, header, cookie) |
| actions | jsonb | ttl, cache-key, bypass, edge-cache |
| enabled | boolean | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `waf_rules`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| zone_id | uuid | fk → cdn_zones.id |
| name | varchar | |
| description | text | |
| severity | enum | critical, high, medium, low |
| action | enum | block, challenge, js_challenge, log, allow |
| filter | jsonb | filter expression (ip, ua, path, rate) |
| enabled | boolean | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `security_profiles`

| field | type | description |
|-------|------|-------------|
| id | uuid | primary key |
| zone_id | uuid | fk → cdn_zones.id |
| name | varchar | e.g. "strict", "moderate", "custom" |
| ddos_protection | boolean | |
| rate_limiting | jsonb | requests per second / ip |
| bot_management | jsonb | bot fight mode settings |
| tls_min_version | varchar | e.g. "1.2", "1.3" |
| always_use_https | boolean | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## 4. api design

### cdn zone management

```
POST   /api/v2/cdn/zones                     — Provision a new CDN zone
GET    /api/v2/cdn/zones                      — List all CDN zones
GET    /api/v2/cdn/zones/:id                  — Get zone details
PUT    /api/v2/cdn/zones/:id                  — Update zone configuration
DELETE /api/v2/cdn/zones/:id                  — Delete / suspend a zone
POST   /api/v2/cdn/zones/:id/purge            — Purge cache (by URL, tag, or all)
POST   /api/v2/cdn/zones/:id/ssl             — Trigger SSL certificate issuance
```

### cache rules

```
GET    /api/v2/cdn/zones/:id/cache-rules       — List cache rules
POST   /api/v2/cdn/zones/:id/cache-rules       — Create cache rule
PUT    /api/v2/cdn/zones/:id/cache-rules/:rid  — Update cache rule
DELETE /api/v2/cdn/zones/:id/cache-rules/:rid  — Delete cache rule
PATCH  /api/v2/cdn/zones/:id/cache-rules/reorder — Reorder rule priority
```

### waf rules

```
GET    /api/v2/cdn/zones/:id/waf-rules         — List WAF rules
POST   /api/v2/cdn/zones/:id/waf-rules         — Create WAF rule
PUT    /api/v2/cdn/zones/:id/waf-rules/:rid    — Update WAF rule
DELETE /api/v2/cdn/zones/:id/waf-rules/:rid    — Delete WAF rule
POST   /api/v2/cdn/zones/:id/waf-rules/simulate — Test a rule against sample traffic
```

### security profiles

```
GET    /api/v2/cdn/zones/:id/security-profile  — Get current security profile
PUT    /api/v2/cdn/zones/:id/security-profile  — Update security profile
POST   /api/v2/cdn/zones/:id/security-profile/apply — Apply profile to zone
```

## 5. implementation plan

### phase 1 -- provider abstraction & one-click provisioning (2 pt)

• define `cdnprovideradapter` interface (go interface or typescript abstract class)
• implement cloudflare adapter (zones, dns, ssl via cloudflare api v4)
• implement bunny cdn adapter (pull zones, ssl via bunny api)
• build provisioning workflow in integration service (create zone → configure dns → issue ssl)
• add `cdn_zones` crud endpoints

### phase 2 -- cache rules engine (1 pt)

• implement `cacherulemanager` -- normalizes rules across providers
• build cache rule crud api
• add cache purge endpoint with tag / url / wildcard support
• ui for drag-and-drop rule reordering

### phase 3 -- waf & security (1.5 pt)

• implement `wafrulemanager` -- translates panel waf rules to provider-specific format
• build waf rule crud api
• implement `securityprofilemanager` -- presets and custom profiles
• add ddos protection toggle and rate-limiting config
• build waf simulation / dry-run endpoint

### phase 4 -- ssl/tls & polish (0.5-1 pt)

• acme / let's encrypt integration for custom certificate management
• ssl status monitoring and autorenewal alerts
• dashboard widgets: cache hit ratio, threats blocked, bandwidth saved
• audit logging for all cdn/waf configuration changes

## 6. provider adapter interface (pseudo-code)

```typescript
interface CDNProviderAdapter {
  // Zone lifecycle
  createZone(params: CreateZoneParams): Promise<Zone>;
  getZone(zoneId: string): Promise<Zone>;
  updateZone(zoneId: string, params: Partial<Zone>): Promise<Zone>;
  deleteZone(zoneId: string): Promise<void>;
  suspendZone(zoneId: string): Promise<void>;
  activateZone(zoneId: string): Promise<void>;

  // SSL
  issueSSL(zoneId: string, method: 'acme' | 'provider'): Promise<SSLStatus>;
  renewSSL(zoneId: string): Promise<SSLStatus>;

  // Cache
  purgeCache(zoneId: string, params: PurgeParams): Promise<void>;
  createCacheRule(zoneId: string, rule: CacheRule): Promise<CacheRule>;
  updateCacheRule(zoneId: string, ruleId: string, rule: Partial<CacheRule>): Promise<CacheRule>;
  deleteCacheRule(zoneId: string, ruleId: string): Promise<void>;

  // WAF
  createWafRule(zoneId: string, rule: WafRule): Promise<WafRule>;
  updateWafRule(zoneId: string, ruleId: string, rule: Partial<WafRule>): Promise<WafRule>;
  deleteWafRule(zoneId: string, ruleId: string): Promise<void>;

  // Security
  getSecurityProfile(zoneId: string): Promise<SecurityProfile>;
  updateSecurityProfile(zoneId: string, profile: SecurityProfile): Promise<SecurityProfile>;
}
```

## 7. configuration examples

### one-click cloudflare setup (post /api/v2/cdn/zones)

```json
{
  "provider": "cloudflare",
  "domain": "app.example.com",
  "plan": "pro",
  "config": {
    "origin_server": "origin.app.example.com",
    "ipv6": true,
    "http2": true,
    "http3": true,
    "min_tls_version": "1.2",
    "always_use_https": true,
    "ssl": "full"
  },
  "security_profile": "moderate"
}
```

### cache rule example

```json
{
  "name": "Static Assets — Long TTL",
  "description": "Cache JS, CSS, and images for 30 days",
  "priority": 10,
  "criteria": {
    "path_glob": ["/assets/**", "/static/**"],
    "file_extension": [".js", ".css", ".png", ".jpg", ".svg", ".woff2"]
  },
  "actions": {
    "ttl": 2592000,
    "cache_key": {
      "include_query": false,
      "include_host": true
    },
    "edge_cache_ttl": 604800,
    "browser_cache_ttl": 2592000
  },
  "enabled": true
}
```

### waf rule example

```json
{
  "name": "Block Admin Access from Non-VPN IPs",
  "description": "Only allow /admin from approved IP ranges",
  "severity": "critical",
  "action": "block",
  "filter": {
    "path_prefix": "/admin",
    "not_ip_in": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
  },
  "enabled": true
}
```

## 8. service assignments

| service | responsibilities |
|---------|------------------|
| **panel** | cdn setup wizard, cache rule form, waf rule editor, security dashboard, ssl status |
| **integration service** | provider abstraction layer, rule engine, ssl management, audit logging |
| **orchestrator agent** | cross-service coordination (if multi-region cdn) |
| **database** | stores zones, rules, profiles, audit logs |

## 9. effort breakdown

| task | pt | dependencies |
|------|----|-------------|
| provider adapter interface & cloudflare adapter | 1.0 | -- |
| bunny cdn adapter | 0.5 | -- |
| zone provisioning workflow | 0.5 | adapters |
| cache rules crud + engine | 1.0 | zone endpoints |
| cache purge logic | 0.5 | cache engine |
| waf rules crud + engine | 1.0 | zone endpoints |
| security profile manager | 0.5 | -- |
| ddos mitigation toggle | 0.25 | -- |
| ssl/tls acme integration | 0.5 | -- |
| dashboard widgets & monitoring | 0.5 | all endpoints |
| ui screens (wizard, editor, dashboard) | 1.0 | all apis |
| documentation & tests | 0.5 | -- |

## 10. risks & mitigations

| risk | impact | mitigation |
|------|--------|------------|
| provider api rate limits | delayed provisioning | implement queue with exponential backoff |
| provider api breaking changes | integration failure | version-pin adapters, integration tests run nightly |
| ssl certificate race conditions | partial downtime | use acme with retry logic + status polling |
| waf rule conflicts across providers | inconsistent behavior | normalize rules via abstract syntax tree before translation |
