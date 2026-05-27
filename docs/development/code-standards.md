# code standards & best practices

maintain consistency and quality across infra pilot services.

## python standards (orchestrator agent)

### pep 8 compliance

```python
# ✅ Good
async def provision_server(server_id: str, config: Dict[str, Any]) -> bool:
    """Provision a cloud server with given configuration.
    
    Args:
        server_id: Unique server identifier
        config: Server configuration dictionary
        
    Returns:
        True if provisioning succeeded, False otherwise
        
    Raises:
        ProvisioningError: If provisioning fails
    """
    try:
        await validate_config(config)
        result = await cloud_api.create_server(server_id, config)
        return result.success
    except Exception as e:
        logger.error(f"Provisioning failed: {e}")
        raise ProvisioningError(f"Failed to provision {server_id}") from e

# ❌ Avoid
def provision(id,conf):
    try:
        return api.create(id,conf)
    except:
        return False
```

### code style

• line length: 120 characters maximum
• indentation: 4 spaces
• imports: `black`, `isort` for formatting
• type hints: required for all functions

### naming conventions

```python
# Classes: PascalCase
class ServerOrchestrator:
    pass

# Functions/methods: snake_case
def get_server_status():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_SERVERS = 100
DATABASE_TIMEOUT = 30

# Private: leading underscore
def _internal_method():
    pass
```

### testing

```python
# tests/test_provisioning.py
import pytest
from services.provisioning import ServerOrchestrator

@pytest.fixture
def orchestrator():
    return ServerOrchestrator()

@pytest.mark.asyncio
async def test_provision_server_success(orchestrator):
    """Test successful server provisioning."""
    result = await orchestrator.provision_server("srv-001", {})
    assert result.success
    assert result.server_id == "srv-001"

@pytest.mark.asyncio
async def test_provision_server_invalid_config(orchestrator):
    """Test provisioning with invalid configuration."""
    with pytest.raises(ConfigError):
        await orchestrator.provision_server("srv-002", {})
```

### async/await

```python
# ✅ Good - Use async context managers
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# ✅ Good - Use async comprehensions
results = [await process(item) async for item in items]

# ✅ Good - Proper error handling
try:
    await client.connect()
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
```

## typescript/react standards (dashboard)

### type safety

```typescript
// ✅ Good: Strict typing
interface Server {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'provisioning';
  resources: {
    cpu: number;
    memory: number;
    storage: number;
  };
}

const getServer = async (id: string): Promise<Server> => {
  const response = await fetch(`/api/servers/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch server: ${response.statusText}`);
  }
  return response.json();
};

// ❌ Avoid: Using `any`
const getServer = async (id: any): Promise<any> => {
  const response = await fetch(`/api/servers/${id}`);
  return response.json();
};
```

### react components

```typescript
// ✅ Good: Functional component with hooks
import React, { useState, useEffect } from 'react';

interface ServerListProps {
  onSelect: (server: Server) => void;
  filter?: 'running' | 'all';
}

export const ServerList: React.FC<ServerListProps> = ({ onSelect, filter = 'all' }) => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchServers = async () => {
      try {
        setLoading(true);
        const data = await getServers();
        const filtered = filter === 'running' 
          ? data.filter(s => s.status === 'running')
          : data;
        setServers(filtered);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchServers();
  }, [filter]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <ul>
      {servers.map(server => (
        <li key={server.id} onClick={() => onSelect(server)}>
          {server.name}
        </li>
      ))}
    </ul>
  );
};
```

### styling

```typescript
// ✅ Good: Tailwind CSS with clsx
import clsx from 'clsx';

const Button: React.FC<ButtonProps> = ({ variant, disabled, children }) => {
  return (
    <button
      className={clsx(
        'px-4 py-2 rounded font-medium transition-colors',
        {
          'bg-blue-500 text-white hover:bg-blue-600': variant === 'primary',
          'bg-gray-200 text-gray-800 hover:bg-gray-300': variant === 'secondary',
          'opacity-50 cursor-not-allowed': disabled,
        }
      )}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

## java standards (service core)

### code style

```java
// ✅ Good: Clear class structure
public class ServerManager {
    private final ServerRepository repository;
    private final Logger logger = LoggerFactory.getLogger(ServerManager.class);
    
    public ServerManager(ServerRepository repository) {
        this.repository = repository;
    }
    
    public Server getServer(String id) throws ServerNotFoundException {
        return repository.findById(id)
            .orElseThrow(() -> new ServerNotFoundException("Server not found: " + id));
    }
    
    public void startServer(String id) throws ServerNotFoundException {
        Server server = getServer(id);
        server.setStatus(ServerStatus.STARTING);
        repository.save(server);
        logger.info("Starting server: {}", id);
    }
}

// ❌ Avoid: Poor structure
public class ServerManager {
    public static void main(String[] args) {
        // Don't mix concerns
    }
    
    public void startServer(String id) {
        // No error handling
        Server s = db.get(id);
        s.status = "STARTING";
    }
}
```

### maven build

```xml
<!-- Use established frameworks -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- Keep dependencies updated -->
<!-- Use dependabot or similar for updates -->
```

## commit message format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### types

• `feat`: new feature
• `fix`: bug fix
• `docs`: documentation
• `style`: code style
• `refactor`: refactoring
• `perf`: performance
• `test`: tests
• `chore`: build, deps

### example

```
feat(orchestrator): add auto-scaling policy

Implement monitoring-based auto-scaling that provisions/deprovisions
servers based on CPU and memory metrics.

- Add MetricsCollector for real-time data
- Implement ScalingPolicy engine
- Add scaling rules configuration

Closes #789
```

## documentation standards

### readme sections

• what is it?
• quick start
• architecture overview
• api endpoints
• development setup
• testing
• contributing

### code comments

```python
# ✅ Good: Explains WHY, not WHAT
async def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff.
    
    Uses exponential backoff (2^attempt seconds) to avoid overwhelming
    the API when it's temporarily unavailable.
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except TemporaryError:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            await asyncio.sleep(wait)

# ❌ Avoid: Commenting obvious code
x = x + 1  # Increment x
if condition:  # Check condition
    do_something()  # Do something
```

## testing coverage

### minimum coverage

• python: 80%
• typescript: 70%
• java: 75%

### test organization

```python
# tests/
#   ├── __init__.py
#   ├── conftest.py           # Fixtures
#   ├── test_provisioning.py
#   ├── test_billing.py
#   └── integration/
#       └── test_api.py
```

## security best practices

• no hardcoded secrets (use environment variables)
• validate all user input
• use parameterized queries
• always hash passwords
• use https only
• implement rate limiting
• log security events (without sensitive data)
• keep dependencies updated

## pull request checklist

• [ ] code follows style guide
• [ ] tests added/updated
• [ ] documentation updated
• [ ] no console errors/warnings
• [ ] commits are clean
• [ ] feature branches created properly
• [ ] no hardcoded secrets

last updated: april 2026
