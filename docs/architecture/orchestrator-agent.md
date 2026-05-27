# orchestrator agent architecture

## purpose

the orchestrator agent is the core provisioning and orchestration engine, handling all infrastructure provisioning requests, workflow execution, and service coordination.

## component structure

```
orchestrator-agent/
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── cogs/
│   ├── provisioning.py     # Server provisioning workflows
│   ├── billing.py          # Billing and cost tracking
│   ├── monitoring.py       # Health checks and metrics
│   ├── webhooks.py         # Discord webhook handlers
│   └── api.py              # REST API endpoints
├── services/
│   ├── cloud.py            # Cloud API integrations
│   ├── pterodactyl.py      # Pterodactyl API client
│   ├── database.py         # Database operations
│   └── email.py            # Email notifications
├── models/
│   ├── server.py           # Server data model
│   ├── deployment.py       # Deployment tracking
│   └── transaction.py      # Billing transactions
└── tests/
    ├── test_provisioning.py
    ├── test_api.py
    └── conftest.py
```

## api endpoints

### servers

#### get servers
```
GET /api/servers?filter=running&limit=50
```

response:
```json
{
  "servers": [
    {
      "id": "srv-001",
      "name": "my-gameserver",
      "type": "gameserver",
      "status": "running",
      "region": "us-east-1",
      "resources": {
        "cpu": 4,
        "memory": 8,
        "storage": 100
      }
    }
  ],
  "total": 1
}
```

#### provision server
```
POST /api/servers/provision
```

request:
```json
{
  "name": "new-server-01",
  "type": "gameserver",
  "game": "minecraft",
  "region": "eu-west-1",
  "resources": {
    "cpu": 4,
    "memory": 8,
    "storage": 100
  }
}
```

response:
```json
{
  "deployment_id": "dep-12345",
  "status": "provisioning",
  "estimated_time": 300
}
```

#### get server details
```
GET /api/servers/{server_id}
```

#### update server
```
PATCH /api/servers/{server_id}
```

#### delete server
```
DELETE /api/servers/{server_id}
```

### deployments

#### get deployment status
```
GET /api/deployments/{deployment_id}
```

response:
```json
{
  "id": "dep-12345",
  "server_id": "srv-001",
  "status": "completed",
  "progress": 100,
  "stages": [
    { "name": "resource-allocation", "status": "completed", "duration": 30 },
    { "name": "configuration", "status": "completed", "duration": 45 },
    { "name": "initialization", "status": "completed", "duration": 120 }
  ]
}
```

### metrics

#### get server metrics
```
GET /api/servers/{server_id}/metrics?window=24h
```

## provisioning workflow

```
User Request
    ▼
Validate Input
    ▼
Check Quota & Resources
    ▼
Create Deployment Record
    ▼
Allocate Resources
    ├─ Reserve CPU
    ├─ Allocate Memory
    └─ Configure Storage
    ▼
Generate Configuration
    ├─ server.properties
    ├─ admin.conf
    └─ network.conf
    ▼
Create Server Instance
    ├─ Cloud API Call
    ├─ Network Setup
    └─ Security Groups
    ▼
Initialize Application
    ├─ Install Runtime
    ├─ Deploy Binary
    └─ Configure Services
    ▼
Health Check
    ├─ Connectivity Test
    ├─ Service Check
    └─ Metrics Verification
    ▼
Update Status → Running
    ▼
Notify User
```

## event handlers

### discord events

```python
# Handle /provision command
@orchestrator.event("discord:command:provision")
async def handle_provision_command(interaction: discord.Interaction, params: dict):
    deployment_id = await orchestrator.provision_server(params)
    await interaction.response.send_message(
        f"Provisioning started: {deployment_id}"
    )
```

### webhook events

```python
# Handle remote system updates
@orchestrator.event("webhook:pterodactyl:server_installed")
async def handle_pterodactyl_installed(webhook_data: dict):
    server_id = webhook_data['server_id']
    await orchestrator.mark_as_running(server_id)
```

### api events

```python
# Handle REST API calls
@app.post("/api/servers/provision")
async def provision_via_api(request: ProvisionRequest) -> ProvisionResponse:
    deployment_id = await orchestrator.provision_server(request.dict())
    return ProvisionResponse(deployment_id=deployment_id)
```

## error handling

```python
class ProvisioningError(Exception):
    """Base provisioning error."""
    pass

class InsufficientResourcesError(ProvisioningError):
    """Raised when cluster lacks resources."""
    pass

class InvalidConfigurationError(ProvisioningError):
    """Raised when configuration is invalid."""
    pass

# Retry logic
@retry(max_attempts=3, backoff=2)
async def provision_with_retry(config: ServerConfig):
    try:
        return await cloud_api.create_server(config)
    except TemporaryError:
        raise  # Will trigger retry
    except PermanentError as e:
        logger.error(f"Permanent error: {e}")
        skip_retry()  # Don't retry
```

## state management

```python
# Server lifecycle states
class ServerStatus(Enum):
    PROVISIONING = "provisioning"    # Being created
    RUNNING = "running"              # Active
    STOPPING = "stopping"            # Being stopped
    STOPPED = "stopped"              # Inactive
    UPDATING = "updating"            # Configuration update
    ERROR = "error"                  # Failed state
    DELETING = "deleting"            # Being deleted

# State transitions
valid_transitions = {
    ServerStatus.PROVISIONING: [ServerStatus.RUNNING, ServerStatus.ERROR],
    ServerStatus.RUNNING: [ServerStatus.STOPPING, ServerStatus.UPDATING, ServerStatus.ERROR],
    ServerStatus.STOPPING: [ServerStatus.STOPPED, ServerStatus.ERROR],
    ServerStatus.STOPPED: [ServerStatus.RUNNING, ServerStatus.DELETING, ServerStatus.ERROR],
}
```

## external integrations

### pterodactyl api

```python
class PterodactylClient:
    """Pterodactyl game server panel integration."""
    
    async def create_server(self, config: dict) -> dict:
        """Create server in Pterodactyl panel."""
        # Implementation
        pass
    
    async def start_server(self, server_id: str) -> bool:
        """Start server instance."""
        # Implementation
        pass
    
    async def get_resources(self) -> dict:
        """Get available resources."""
        # Implementation
        pass
```

### cloud providers

```python
class CloudProviderFactory:
    @staticmethod
    def get_provider(cloud_type: str) -> CloudProvider:
        providers = {
            'aws': AWSProvider(),
            'gcp': GCPProvider(),
            'azure': AzureProvider(),
        }
        return providers[cloud_type]

class CloudProvider(ABC):
    @abstractmethod
    async def create_instance(self, config: dict) -> str:
        """Create compute instance, return instance ID."""
        pass
    
    @abstractmethod
    async def terminate_instance(self, instance_id: str) -> bool:
        """Terminate instance."""
        pass
```

## monitoring & logging

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Counters
provisions_total = Counter('provisions_total', 'Total provisions', ['status'])
deployments_failed = Counter('deployments_failed', 'Failed deployments')

# Gauges
active_servers = Gauge('active_servers', 'Active servers')
resource_utilization = Gauge('resource_utilization', 'CPU/Memory usage', ['resource'])

# Histograms
provision_duration = Histogram('provision_duration_seconds', 'Provisioning duration')

# Logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"Server provisioned: {server_id}")
logger.error(f"Provisioning failed: {error}", exc_info=True)
```

## security considerations

• validate all inputs against schema
• use asyncio locks for concurrent operations
• implement rate limiting
• log all operations (without sensitive data)
• use secrets manager for credentials
• implement rbac for api access

last updated: april 2026
