# system architecture overview

## design philosophy

infra pilot follows a distributed microservices architecture with clear separation of concerns, enabling independent scaling, deployment, and development of services.

### core principles

• modularity - each service has a single responsibility
• autonomy - services can be deployed independently
• scalability - horizontal scaling of individual components
• resilience - graceful degradation and fault tolerance
• observability - comprehensive logging, metrics, and tracing

## system components

### 1. management dashboard
language: typescript/react
framework: vite, tailwind css, convex
purpose: web-based operations interface

```
┌─────────────────────────┐
│   React Components      │
├─────────────────────────┤
│  - Server Provisioning  │
│  - Status Dashboard     │
│  - User Management      │
│  - Configuration UI     │
└────────────┬────────────┘
             ▼
     ┌───────────────┐
     │ Convex RPC    │
     │ Backend       │
     └───────┬───────┘
             ▼
    Orchestrator Agent API
```

responsibilities:
• user interface for infrastructure operations
• real-time status updates via websocket
• user authentication and rbac
• audit logging of all operations

### 2. orchestrator agent
language: python 3.9+
frameworks: aiohttp, discord.py
purpose: core provisioning and orchestration engine

```
┌──────────────────────────┐
│  Event Handlers          │
├──────────────────────────┤
│  - Discord events        │
│  - Webhook events        │
│  - API requests          │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  Provisioning Logic      │
├──────────────────────────┤
│  - Resource allocation   │
│  - Configuration gen.    │
│  - Workflow engine       │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  External Integrations   │
├──────────────────────────┤
│  - Pterodactyl API       │
│  - Cloud providers       │
│  - Database ops          │
└──────────────────────────┘
```

responsibilities:
• handle provisioning requests
• orchestrate service interactions
• manage resource allocation
• execute automation workflows
• integrate with external apis

### 3. discord service
language: node.js (javascript)
framework: discord.js
purpose: discord bot interface for operations

```
┌─────────────────────────┐
│  Discord Events         │
│  (messages, reactions)  │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Command Handlers       │
├─────────────────────────┤
│  - /provision           │
│  - /status              │
│  - /configure           │
│  - /billing             │
└────────────┬────────────┘
             ▼
   Orchestrator Agent API
```

responsibilities:
• parse discord commands
• execute infrastructure operations
• post status updates
• handle user interactions
• webhook integration

### 4. service core
language: java 8+
build tool: maven
purpose: game server lifecycle management

```
┌────────────────────────┐
│  Resource Manager      │
├────────────────────────┤
│  - CPU allocation      │
│  - Memory management   │
│  - Storage provisioning│
└────────────┬───────────┘
             ▼
┌────────────────────────┐
│  Server Lifecycle      │
├────────────────────────┤
│  - Startup/shutdown    │
│  - Monitoring          │
│  - Event logging       │
└────────────┬───────────┘
             ▼
┌────────────────────────┐
│  Configuration         │
├────────────────────────┤
│  - Props generation    │
│  - Settings management │
│  - Schema validation   │
└────────────────────────┘
```

responsibilities:
• manage server resources
• handle lifecycle events
• generate configurations
• report status and metrics
• coordinate with orchestrator

## data flow patterns

### provisioning flow
```
User (Discord/Dashboard) 
    ▼
Orchestrator Agent
    ▼
Service Core (validate config)
    ▼
Cloud/Infrastructure APIs
    ▼
Infrastructure State Updated
    ▼
Webhook → Discord Service
    ▼
Notification to User
```

### status update flow
```
Service Core (emits metric)
    ▼
Metrics Store (Prometheus)
    ▼
Dashboard (polls metrics)
    ▼
Real-time UI Update
    ▼
User Sees Status
```

### event-driven flow
```
External System (Pterodactyl)
    ▼
Webhook to Orchestrator
    ▼
Process Event
    ▼
Update State
    ▼
Broadcast to Dashboard
```

## api boundaries

### service-to-service communication

| from | to | protocol | format |
|------|-----|----------|--------|
| dashboard | orchestrator | rest/grpc | json |
| orchestrator | service core | rest | json |
| discord service | orchestrator | rest | json |
| dashboard | service core | rest | json |
| external systems | orchestrator | webhook | json |

### external integrations

• pterodactyl: game server hosting (rest api)
• cloud apis: aws, gcp, azure (rest/sdk)
• discord: bot webhooks and events (rest)
• monitoring: prometheus scrape endpoints (http)

## data model

### core entities

```
┌─────────────────┐
│     Server      │
├─────────────────┤
│ - id            │
│ - name          │
│ - type          │
│ - status        │
│ - resources     │
│ - config        │
└─────────────────┘

┌─────────────────┐
│     User        │
├─────────────────┤
│ - id            │
│ - email         │
│ - role          │
│ - permissions   │
└─────────────────┘

┌─────────────────┐
│  Deployment     │
├─────────────────┤
│ - id            │
│ - server_id     │
│ - status        │
│ - timestamp     │
│ - error_msg     │
└─────────────────┘
```

## security architecture

### authentication & authorization

```
User Login
    ▼
Dashboard → Convex Auth
    ▼
JWT Token Generated
    ▼
Token Passed to API Requests
    ▼
Orchestrator Validates
    ▼
RBAC Rules Applied
    ▼
Operation Allowed/Denied
```

### layers

• transport layer: tls/ssl for all connections
• authentication: jwt tokens, oauth2 support
• authorization: rbac with granular permissions
• audit logging: all operations logged
• secrets management: encrypted config storage

## deployment architecture

### development
```
Docker Compose
├── Management Dashboard (5173)
├── Orchestrator Agent (8000)
├── Discord Service (-)
├── Service Core (8080)
├── PostgreSQL
└── Redis
```

### production
```
Kubernetes Cluster
├── Deployment: dashboard
├── Deployment: orchestrator
├── Deployment: discord
├── Deployment: service-core
├── StatefulSet: PostgreSQL
├── StatefulSet: Redis
├── Service: LoadBalancer (ingress)
└── PVC: persistent storage
```

## scalability considerations

### horizontal scaling

stateless services (can scale freely)
• management dashboard
• orchestrator agent
• discord service

stateful services (require special handling)
• service core (may cache state)
• databases (replication/clustering)

### load distribution

```
Ingress/LB
    ▼
├── Dashboard pods (N replicas)
├── Orchestrator pods (N replicas)
├── Discord pods (N replicas)
└── Core Service pods (N replicas)

Database Layer (Primary + Replicas)
Cache Layer (Cluster)
```

## monitoring & observability

### metrics exposed

• application metrics (prometheus format)
• business metrics (deployments, resources used)
• infrastructure metrics (cpu, memory, network)

### logging strategy

• service logs → centralized logging (elk/loki)
• audit logs → secure storage
• error tracking → sentry integration

### tracing

• distributed tracing via opentelemetry
• service-to-service correlation ids
• performance analysis and bottleneck identification

## high availability

### resilience patterns

• circuit breaker - fail fast on external failures
• retry logic - exponential backoff
• health checks - readiness/liveness probes
• graceful degradation - partial functionality on component failure

### recovery

• automatic pod restart (kubernetes)
• database replication
• state recovery from logs
• backup and restore procedures

## related documentation

• [service specifications](architecture/)
• [data flow details](architecture/data-flow.md)
• [integration patterns](architecture/integration-patterns.md)
• [deployment guide](../operations/deployment-guide.md)

last updated: april 2026
