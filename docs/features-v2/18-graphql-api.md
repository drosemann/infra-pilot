# feature 18: graphql api

- feature #: 18
- category: developer ecosystem & api
- primary service: integration service
- supporting services: orchestrator agent, management panel
- effort: medium (4-6 pt)
- dependencies: feature #14 (api gateway & rate limiting), feature #17 (opentelemetry export)

## 1. overview

the graphql api provides an optional graphql layer alongside the existing rest api. it enables clients to query exactly the data they need, receive real-time updates via subscriptions (websocket), and interact with the full infra pilot resource model through a single endpoint. the layer includes n+1 query prevention via dataloader, authentication middleware, and support for schema stitching to compose multiple service schemas.

### goals

- single `/graphql` endpoint for all queries and mutations
- real-time subscriptions for server events, logs, and metrics
- dataloader-based batching to prevent n+1 query problems
- jwt-based auth middleware with field-level permission checking
- schema stitching to compose schemas from integration service, orchestrator agent, and service core
- backward compatible -- existing rest api unchanged; graphql is additive

### non-goals

- replacing rest api entirely (rest remains primary, graphql is optional)
- automatic schema generation from rest endpoints (hand-written schema with resolvers)
- federated graphql (apollo federation) in v1 -- schema stitching is simpler
- graphql as a bff (backend for frontend) -- the schema is general-purpose

## 2. architecture

### high-level component diagram

```
┌──────────────────┐       ┌──────────────────────────────────────────┐
│   Client         │       │        Integration Service                │
│   (GraphQL)      │       │                                          │
│                  │       │  ┌──────────────────────────────────────┐ │
│  Queries         │──────►│  │        GraphQL Server (Yoga)         │ │
│  Mutations       │       │  │                                      │ │
│  Subscriptions   │◄──────┤  │  ┌──────────┐  ┌──────────────────┐  │ │
│                  │       │  │  │ Schema   │  │ Auth Middleware   │  │ │
└──────────────────┘       │  │  │ (Stitched)│  │ (JWT + RBAC)     │  │ │
                            │  │  └────┬─────┘  └──────────────────┘  │ │
                            │  │       │                               │ │
                            │  │       ▼                               │ │
                            │  │  ┌──────────────────────────────────┐ │ │
                            │  │  │      Resolvers                   │ │ │
                            │  │  │  ┌────────┐  ┌───────────────┐  │ │ │
                            │  │  │  │ Query  │  │ Mutation      │  │ │ │
                            │  │  │  │ ────── │  │ ────────────  │  │ │ │
                            │  │  │  │ servers│  │ createServer  │  │ │ │
                            │  │  │  │ server │  │ deleteServer  │  │ │ │
                            │  │  │  │ logs   │  │ updateConfig  │  │ │ │
                            │  │  │  │ metrics│  │ deployBackup  │  │ │ │
                            │  │  │  └───┬────┘  └───────┬───────┘  │ │ │
                            │  │  │      │               │           │ │ │
                            │  │  │      ▼               ▼           │ │ │
                            │  │  │  ┌─────────────────────────┐     │ │ │
                            │  │  │  │     DataLoader Cache     │     │ │ │
                            │  │  │  │  (batches + caches per  │     │ │ │
                            │  │  │  │   request context)      │     │ │ │
                            │  │  │  └────────┬────────────────┘     │ │ │
                            │  │  │           │                       │ │ │
                            │  │  └───────────┼───────────────────────┘ │ │
                            │  └──────────────┼─────────────────────────┘ │
                            │                 │                           │
                            └─────────────────┼───────────────────────────┘
                                              │
                ┌─────────────────────────────┼─────────────────────────────┐
                │              ┌──────────────┴──────────────┐              │
                │              ▼              ▼              ▼              │
                │     ┌────────────┐  ┌──────────────┐  ┌──────────┐       │
                │     │REST API    │  │Orchestrator  │  │Service   │       │
                │     │(Integration│  │Agent (Python)│  │Core(Java)│       │
                │     │ Service)   │  │              │  │          │       │
                │     └────────────┘  └──────────────┘  └──────────┘       │
                │                                                          │
                └──────────────────────────────────────────────────────────┘
```

### request lifecycle

```
1. Client sends GraphQL query to POST /graphql (or WebSocket for subscriptions)
2. Auth middleware extracts JWT, attaches user + permissions to context
3. GraphQL engine parses query, validates against schema
4. Resolvers execute, batching via DataLoader where applicable
5. For stitched schemas, delegation to downstream services
6. Response assembled and returned (JSON for queries, stream for subscriptions)
```

### subscription transport

```
WebSocket Connection (graphql-ws protocol)
       │
       ▼
Client sends connection_init (with auth token)
       │
       ▼
Server validates → acknowledge
       │
       ▼
Client subscribes:
  subscription {
    serverEvents(serverId: "srv_web_01") {
      type
      message
      timestamp
    }
  }
       │
       ▼
Server registers subscription → publishes events via
Integration Service event bus (Redis Pub/Sub)
       │
       ▼
Event occurs → GraphQL server pushes to subscribed clients
       │
       ▼
Client receives:
  {
    "data": {
      "serverEvents": {
        "type": "STATUS_CHANGE",
        "message": "Server web-01 is now running",
        "timestamp": "2026-05-20T12:00:00Z"
      }
    }
  }
```

## 3. data model

### graphql schema (core)

```graphql
# ============================================================
# Types
# ============================================================

type Server {
  id: ID!
  name: String!
  provider: Provider!
  region: String!
  plan: String!
  status: ServerStatus!
  cpuCores: Int!
  memoryMb: Int!
  diskGb: Int!
  image: String
  ipAddress: String
  tags: [String!]!
  firewall: [FirewallRule!]
  backups: [Backup!]
  metrics: ServerMetrics
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Backup {
  id: ID!
  serverId: ID!
  status: BackupStatus!
  sizeBytes: Int
  type: BackupType!
  createdAt: DateTime!
  completedAt: DateTime
}

type ServerMetrics {
  cpuUsage: Float
  memoryUsage: Float
  diskUsage: Float
  networkIn: Int
  networkOut: Int
  uptime: Int
  sampledAt: DateTime
}

type FirewallRule {
  protocol: String!
  port: Int
  source: String!
  action: FirewallAction!
}

type DnsRecord {
  id: ID!
  zone: String!
  name: String!
  type: DnsRecordType!
  value: String!
  ttl: Int!
  proxied: Boolean!
}

type Deployment {
  id: ID!
  serverId: ID!
  status: DeploymentStatus!
  type: String!
  errorMessage: String
  startedAt: DateTime!
  completedAt: DateTime
}

type LogEntry {
  timestamp: DateTime!
  level: LogLevel!
  message: String!
  service: String
  traceId: String
}

type User {
  id: ID!
  email: String!
  name: String!
  role: UserRole!
  permissions: [String!]!
  createdAt: DateTime!
}

# ============================================================
# Enums
# ============================================================

enum ServerStatus { PROVISIONING RUNNING STOPPED ERROR SUSPENDED TERMINATED }
enum BackupStatus { PENDING RUNNING COMPLETED FAILED }
enum BackupType { FULL INCREMENTAL SNAPSHOT }
enum FirewallAction { ALLOW DENY }
enum DnsRecordType { A AAAA CNAME MX TXT SRV }
enum DeploymentStatus { PENDING RUNNING SUCCEEDED FAILED ROLLED_BACK }
enum LogLevel { DEBUG INFO WARN ERROR FATAL }
enum UserRole { ADMIN OPERATOR DEVELOPER VIEWER }

# ============================================================
# Input Types
# ============================================================

input CreateServerInput {
  name: String!
  provider: Provider!
  region: String!
  plan: String!
  cpuCores: Int
  memoryMb: Int
  diskGb: Int
  image: String
  tags: [String!]
  firewall: [FirewallRuleInput!]
}

input FirewallRuleInput {
  protocol: String!
  port: Int
  source: String!
  action: FirewallAction!
}

input ServerFilter {
  status: ServerStatus
  provider: Provider
  tag: String
  search: String
}

input PaginationInput {
  page: Int = 1
  perPage: Int = 20
}

# ============================================================
# Query
# ============================================================

type Query {
  # Server queries
  servers(filter: ServerFilter, pagination: PaginationInput): ServerConnection!
  server(id: ID!): Server
  serverByName(name: String!): Server

  # Backup queries
  backups(serverId: ID!, pagination: PaginationInput): BackupConnection!
  backup(id: ID!): Backup

  # DNS queries
  dnsRecords(zone: String, pagination: PaginationInput): DnsRecordConnection!
  dnsRecord(id: ID!): DnsRecord

  # Deployment queries
  deployments(serverId: ID, pagination: PaginationInput): DeploymentConnection!
  deployment(id: ID!): Deployment

  # Log queries
  logs(
    serverId: ID!,
    level: LogLevel,
    from: DateTime,
    to: DateTime,
    search: String,
    pagination: PaginationInput
  ): LogConnection!

  # Metrics queries
  metrics(
    serverId: ID!,
    from: DateTime!,
    to: DateTime!,
    interval: String!
  ): [ServerMetrics!]!

  # User queries
  me: User!
  users(pagination: PaginationInput): UserConnection!

  # Health
  health: HealthStatus!
}

# ============================================================
# Mutations
# ============================================================

type Mutation {
  # Server mutations
  createServer(input: CreateServerInput!): ServerPayload!
  updateServer(id: ID!, input: UpdateServerInput!): ServerPayload!
  deleteServer(id: ID!): DeletePayload!
  startServer(id: ID!): ServerPayload!
  stopServer(id: ID!): ServerPayload!
  restartServer(id: ID!): ServerPayload!

  # Backup mutations
  createBackup(serverId: ID!, type: BackupType!): BackupPayload!
  restoreBackup(id: ID!): BackupPayload!
  deleteBackup(id: ID!): DeletePayload!

  # DNS mutations
  createDnsRecord(input: CreateDnsRecordInput!): DnsRecordPayload!
  updateDnsRecord(id: ID!, input: UpdateDnsRecordInput!): DnsRecordPayload!
  deleteDnsRecord(id: ID!): DeletePayload!

  # Deployment mutations
  triggerDeployment(serverId: ID!, type: String!, config: JSON): DeploymentPayload!
  rollbackDeployment(id: ID!): DeploymentPayload!
}

# ============================================================
# Subscriptions
# ============================================================

type Subscription {
  # Real-time server events
  serverEvents(serverId: ID): ServerEvent!
  serverLogs(serverId: ID!, level: LogLevel): LogEntry!
  serverMetrics(serverId: ID!, interval: String!): ServerMetrics!

  # Global events
  deploymentEvents: DeploymentEvent!
  alertEvents: AlertEvent!
}

# ============================================================
# Event Types (for subscriptions)
# ============================================================

type ServerEvent {
  type: ServerEventType!
  serverId: ID!
  message: String!
  timestamp: DateTime!
  data: JSON
}

enum ServerEventType {
  STATUS_CHANGE
  RESOURCE_UPDATE
  BACKUP_COMPLETE
  ERROR
  ALERT
}

type DeploymentEvent {
  type: DeploymentEventType!
  deploymentId: ID!
  serverId: ID!
  status: DeploymentStatus!
  message: String
  timestamp: DateTime!
}

type AlertEvent {
  id: ID!
  severity: String!
  title: String!
  message: String!
  resourceType: String
  resourceId: String
  timestamp: DateTime!
}

# ============================================================
# Connection Types (pagination wrappers)
# ============================================================

type ServerConnection { edges: [ServerEdge!]! pageInfo: PageInfo! totalCount: Int! }
type ServerEdge { node: Server! cursor: String! }
type BackupConnection { edges: [BackupEdge!]! pageInfo: PageInfo! totalCount: Int! }
type BackupEdge { node: Backup! cursor: String! }
type DnsRecordConnection { edges: [DnsRecordEdge!]! pageInfo: PageInfo! totalCount: Int! }
type DnsRecordEdge { node: DnsRecord! cursor: String! }
type DeploymentConnection { edges: [DeploymentEdge!]! pageInfo: PageInfo! totalCount: Int! }
type DeploymentEdge { node: Deployment! cursor: String! }
type LogConnection { edges: [LogEdge!]! pageInfo: PageInfo! totalCount: Int! }
type LogEntryEdge { node: LogEntry! cursor: String! }
type UserConnection { edges: [UserEdge!]! pageInfo: PageInfo! totalCount: Int! }
type UserEdge { node: User! cursor: String! }

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# ============================================================
# Payloads
# ============================================================

type ServerPayload { server: Server! success: Boolean! errors: [Error!] }
type BackupPayload { backup: Backup! success: Boolean! errors: [Error!] }
type DnsRecordPayload { dnsRecord: DnsRecord! success: Boolean! errors: [Error!] }
type DeploymentPayload { deployment: Deployment! success: Boolean! errors: [Error!] }
type DeletePayload { success: Boolean! errors: [Error!] }

type Error { field: String message: String! code: String! }

type HealthStatus {
  status: String!
  version: String!
  uptime: Int!
  services: [ServiceStatus!]!
}

type ServiceStatus { name: String! status: String! latency: Int! }

# ============================================================
# Scalars
# ============================================================

scalar DateTime
scalar JSON
scalar Provider
```

## 4. api design

### endpoints

| endpoint | protocol | description |
|----------|----------|-------------|
| `POST /api/v2/graphql` | http | graphql queries and mutations |
| `GET /api/v2/graphql` | http | graphiql ide (development mode) |
| `ws://host/api/v2/graphql` | websocket | graphql subscriptions (graphql-ws) |

### authentication

the auth middleware extracts the jwt from the `authorization` header (http) or connection params (websocket):

```json
// HTTP Request
POST /api/v2/graphql
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "query": "query { servers { id name status } }",
  "variables": {}
}

// WebSocket connection_init
{
  "type": "connection_init",
  "payload": {
    "token": "<jwt_token>"
  }
}
```

### query examples

**get servers with nested backups and metrics:**

```graphql
query GetServers {
  servers(filter: { status: RUNNING }, pagination: { page: 1, perPage: 10 }) {
    totalCount
    edges {
      node {
        id
        name
        status
        cpuCores
        memoryMb
        tags
        metrics {
          cpuUsage
          memoryUsage
        }
        backups(pagination: { page: 1, perPage: 3 }) {
          edges {
            node {
              id
              status
              createdAt
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**single server with logs:**

```graphql
query GetServerWithLogs($id: ID!) {
  server(id: $id) {
    id
    name
    status
    ipAddress
    firewall { protocol port source action }
  }
  logs(serverId: $id, level: ERROR, from: "2026-05-20T00:00:00Z", to: "2026-05-20T23:59:59Z") {
    edges {
      node {
        timestamp
        level
        message
        traceId
      }
    }
  }
}
```

**create server mutation:**

```graphql
mutation CreateServer($input: CreateServerInput!) {
  createServer(input: $input) {
    server {
      id
      name
      status
      provider
      ipAddress
    }
    errors {
      field
      message
    }
  }
}
```

### subscription examples

**listen to all server events:**

```graphql
subscription WatchServerEvents {
  serverEvents {
    type
    serverId
    message
    timestamp
    data
  }
}
```

**listen to error logs for a specific server:**

```graphql
subscription WatchServerErrors($serverId: ID!) {
  serverLogs(serverId: $serverId, level: ERROR) {
    timestamp
    message
    traceId
  }
}
```

**listen to real-time metrics stream:**

```graphql
subscription WatchMetrics($serverId: ID!) {
  serverMetrics(serverId: $serverId, interval: "1m") {
    cpuUsage
    memoryUsage
    diskUsage
    sampledAt
  }
}
```

## 5. implementation plan

### phase 1: graphql server setup & schema (week 1, 2 pt)

| task | service | description |
|------|---------|-------------|
| 1.1 | integration service | install graphql yoga (or apollo server), configure http + websocket |
| 1.2 | integration service | define core graphql schema (type definitions + resolvers) |
| 1.3 | integration service | implement auth middleware (jwt extraction, rbac context) |
| 1.4 | integration service | set up graphiql ide (development only) |
| 1.5 | integration service | configure rate limiting per query complexity |

**deliverables:** graphql endpoint operational with core schema and auth.

### phase 2: resolvers & dataloader (weeks 1-2, 1.5 pt)

| task | service | description |
|------|---------|-------------|
| 2.1 | integration service | implement query resolvers (servers, backups, logs, metrics, dns, deployments) |
| 2.2 | integration service | implement mutation resolvers (crud for all resource types) |
| 2.3 | integration service | create dataloader instances for n+1 prevention (server → backups, server → metrics, etc.) |
| 2.4 | integration service | add field-level permission checks in resolvers |
| 2.5 | integration service | add query complexity analysis and depth limiting |

**deliverables:** all queries and mutations functional with dataloader batching.

### phase 3: subscriptions (week 2-3, 1.5 pt)

| task | service | description |
|------|---------|-------------|
| 3.1 | integration service | implement websocket transport (graphql-ws) |
| 3.2 | integration service | create pubsub adapter backed by redis |
| 3.3 | integration service | implement subscription resolvers (serverevents, serverlogs, servermetrics, deploymenteventsevents) |
| 3.4 | integration service | add websocket auth (connection_init token validation) |
| 3.5 | integration service | implement subscription filtering (per-server, per-level) |
| 3.6 | management panel | demo: live-updating dashboard via subscriptions |

**deliverables:** real-time subscriptions operational for events, logs, and metrics.

### phase 4: schema stitching (week 3, 1 pt)

| task | service | description |
|------|---------|-------------|
| 4.1 | orchestrator agent | expose internal graphql schema (or rest → gql schema mapping) |
| 4.2 | service core | expose internal graphql schema (or rest → gql schema mapping) |
| 4.3 | integration service | implement schema stitching (merge schemas from multiple services) |
| 4.4 | integration service | add delegation resolvers for remote schemas |

**deliverables:** stitched schema combining data from integration service, orchestrator agent, and service core.

### phase 5: testing & documentation (week 4, 0.5 pt)

| task | service | description |
|------|---------|-------------|
| 5.1 | all | integration tests for all query/mutation/subscription paths |
| 5.2 | integration service | query performance testing (n+1 prevention verification) |
| 5.3 | integration service | load testing (concurrent subscriptions, high-frequency metrics) |
| 5.4 | shared | api documentation (graphql schema docs, example queries) |

**deliverables:** tested and documented graphql api.

## 6. dataloader strategy

### batch loading patterns

```
Without DataLoader (N+1 problem):
  Query: servers { backups { id } }
  DB calls:
    1. SELECT * FROM servers                  (1 query)
    10. SELECT * FROM backups WHERE server_id = 'srv_01'  (10 queries!)
    11. SELECT * FROM backups WHERE server_id = 'srv_02'
    ...

With DataLoader:
  DB calls:
    1. SELECT * FROM servers                  (1 query)
    2. SELECT * FROM backups WHERE server_id IN ('srv_01', 'srv_02', ...)  (1 query)
```

### dataloader instances

| loader | key | batch function | cache scope |
|--------|-----|----------------|-------------|
| `serverLoader` | `server.id` | `SELECT * FROM servers WHERE id IN ($keys)` | per-request |
| `backupLoader` | `server.id` | `SELECT * FROM backups WHERE server_id IN ($keys)` | per-request |
| `dnsLoader` | `dns.id` | `SELECT * FROM dns_records WHERE id IN ($keys)` | per-request |
| `deploymentLoader` | `server.id` | `SELECT * FROM deployments WHERE server_id IN ($keys)` | per-request |
| `userLoader` | `user.id` | `SELECT * FROM users WHERE id IN ($keys)` | per-request |
| `metricsLoader` | `server.id` | batch fetch from prometheus/influxdb | per-request |

## 7. service assignments

| service | responsibilities |
|---------|-----------------|
| **integration service** | graphql server (yoga/apollo), schema definition, resolver implementation, dataloader batching, websocket subscriptions, auth middleware, query complexity analysis, schema stitching orchestrator |
| **orchestrator agent** | expose internal graphql schema (or rest endpoints consumed by resolvers), publish events for subscription topics |
| **management panel** | graphql client integration (apollo client or urql), subscription hooks for live-updating ui, demo dashboards |
| **service core** | expose internal graphql schema for game-server-specific types |

## 8. configuration example

**infrapilot.yaml** (graphql configuration):

```yaml
graphql:
  enabled: true
  path: /api/v2/graphql
  playground: false  # GraphiQL IDE — enable only in dev
  auth:
    required: true
    jwt_secret_env: JWT_SECRET
  subscriptions:
    enabled: true
    path: /api/v2/graphql
    protocol: graphql-ws
    keepalive_interval_secs: 10
    max_subscriptions_per_connection: 50
  query:
    max_depth: 8
    max_complexity: 1000
    max_batch_size: 25
  dataloader:
    cache: true
    cache_ttl_ms: 5000  # per-request cache, not shared
  stitching:
    enabled: true
    services:
      - name: orchestrator
        url: http://orchestrator:8000/graphql
      - name: service-core
        url: http://service-core:8080/graphql
  rate_limiting:
    queries_per_minute: 120
    mutations_per_minute: 30
    complexity_per_minute: 5000
```

## 9. effort estimate

| phase | pt | dependencies |
|-------|----|-------------|
| phase 1: graphql server setup & schema | 2.0 | feature #14 (api gateway & rate limiting) |
| phase 2: resolvers & dataloader | 1.5 | phase 1 |
| phase 3: subscriptions | 1.5 | phase 1, redis |
| phase 4: schema stitching | 1.0 | phase 1, orchestrator agent gql schema |
| phase 5: testing & documentation | 0.5 | phases 1-4 |
| **buffer (15%)** | **0.9** | -- |
| **total** | **~7.4 pt** | -- |

### risk factors

- **subscription scaling:** each websocket connection consumes memory; long-lived subscriptions for 1000+ concurrent users need horizontal scaling with sticky sessions or a shared pubsub
- **schema stitching complexity:** type conflicts across service schemas (e.g., different `server` types) require manual merge configuration
- **performance:** deeply nested queries without dataloader can cause cascading db load; complexity analysis must be strict
- **websocket proxy:** load balancers (nginx, haproxy) must be configured for websocket upgrade and long-lived connections

## 10. security & compliance

- jwt required for all queries, mutations, and subscriptions
- field-level authorization: users can only query resources they have permission for
- query complexity limits prevent abusive queries (malicious or accidental)
- subscription rate limiting: max n subscriptions per connection, throttled event delivery
- input validation: all mutation inputs sanitized and validated against schema
- depth limiting prevents deeply nested recursive queries
- tls required in production for both http and websocket transports
- audit logging for all mutations (who performed what action)
