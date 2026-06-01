# Contributing to Infra-pilot

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- pnpm or npm
- Discord bot token (for orchestrator agent)
- Access to edge/IoT infrastructure (optional)

### Repository Structure
```
infra-pilot/
├── services/
│   ├── orchestrator-agent/    # Discord bot for orchestration
│   │   ├── cogs/              # Command cog modules
│   │   ├── tests/             # Cog test suites
│   │   └── main.py           # Entry point
│   ├── integration-service/   # REST API service
│   │   ├── src/               # Source modules
│   │   │   ├── analytics/     # Analytics engine
│   │   │   ├── fleet/         # Fleet manager
│   │   │   └── ...            # Other modules
│   │   └── tests/             # Integration tests
│   └── management-panel/      # React dashboard
│       ├── src/pages/         # Page components
│       └── ...
├── cli/ipilot/                # CLI tool
├── infra/                     # Infrastructure helpers
│   ├── edge/                  # Edge computing helpers
│   └── green/                 # Green computing helpers
├── mobile/                    # React Native app
│   └── app/screens/           # Mobile screens
└── docs/                      # Documentation
```

### Setting Up Development Environment

#### Backend (Python)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### Frontend (Management Panel)
```bash
cd services/management-panel
pnpm install
pnpm run dev
```

#### Mobile App
```bash
cd mobile
pnpm install
npx expo start
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest services/integration-service/tests/ -v

# Run with coverage
pytest --cov=services --cov-report=html

# Run management panel tests
cd services/management-panel
pnpm run test
```

## Development Workflow

### 1. Feature Development Process
1. Create feature branch from `main`
2. Implement changes following coding standards
3. Write/update tests for all changes
4. Run lint and type checks
5. Submit pull request with description
6. Request code review from at least one team member
7. Address review feedback
8. Merge after approval and CI passes

### 2. Commit Guidelines
- Use conventional commits format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep commits focused on single logical change
- Write descriptive commit messages

### 3. Branch Naming Convention
- `feat/<feature-name>` for new features
- `fix/<bug-description>` for bug fixes
- `docs/<documentation-topic>` for documentation
- `refactor/<component>` for refactoring
- `test/<test-description>` for test additions

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use async/await for I/O operations
- Use dataclasses for data containers
- Document public APIs with docstrings

#### Python Example
```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceResult:
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class DeviceService:
    async def get_device(self, device_id: str) -> ServiceResult:
        device = await self.repository.find_by_id(device_id)
        if not device:
            return ServiceResult(success=False, error="Device not found")
        return ServiceResult(success=True, data=device.to_dict())
```

### TypeScript/React
- Use functional components with hooks
- Define TypeScript interfaces for props
- Use Tailwind CSS classes for styling
- Follow shadcn/ui component patterns
- Use proper React key props for lists

#### TypeScript Example
```typescript
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface DeviceCardProps {
  deviceId: string;
  name: string;
  status: 'online' | 'offline' | 'degraded';
  onStatusChange: (id: string, newStatus: string) => void;
}

export function DeviceCard({ deviceId, name, status, onStatusChange }: DeviceCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleToggle = async () => {
    setIsLoading(true);
    await onStatusChange(deviceId, status === 'online' ? 'offline' : 'online');
    setIsLoading(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">Status: {status}</p>
        <Button onClick={handleToggle} disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Toggle Status'}
        </Button>
      </CardContent>
    </Card>
  );
}
```

### React Native
- Use StyleSheet.create for styles
- Follow React Native performance best practices
- Use SafeAreaView for safe area handling
- Use FlatList for long lists
- Implement pull-to-refresh where applicable

### Testing Standards
- Unit tests for all service modules
- Integration tests for API endpoints
- Component tests for UI elements
- Aim for > 80% code coverage
- Use pytest fixtures for test setup
- Mock external dependencies

### Documentation Standards
- Document all public APIs
- Include usage examples in docstrings
- Keep README up-to-date with features
- Document configuration options
- Include troubleshooting guides

## Architecture Decisions

### Service Layer Pattern
All backend modules follow the service layer pattern:
1. **Models**: Data structures and types
2. **Services**: Business logic and operations
3. **Handlers**: Request/response handling
4. **Routes**: HTTP endpoint definitions

### Data Flow
```
External → API Routes → Handlers → Services → Data Stores
                  ↑                        ↓
              Discord Cog ←→ Orchestrator ←─┘
```

### State Management
- In-memory stores for development
- PostgreSQL for production persistence
- Redis for caching and session management
- Kafka for event streaming (IoT pipeline)

## Deployment

### Development
- Local docker-compose for services
- Hot-reload for backend and frontend
- Local PostgreSQL and Redis instances

### Staging
- Docker containers on staging cluster
- Managed PostgreSQL and Redis
- Feature flags for gradual rollout

### Production
- Kubernetes deployment with Helm
- Horizontal pod autoscaling
- Blue-green deployment strategy
- Database migration automation

## Monitoring and Observability

### Logging
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing
- Centralized log aggregation (ELK stack)

### Metrics
- Prometheus metrics endpoint
- Custom business metrics
- Grafana dashboards for visualization
- Alert thresholds for anomalies

### Tracing
- OpenTelemetry integration
- Distributed tracing across services
- Performance bottleneck identification
- Latency breakdown per component

## Security Guidelines

### Authentication
- JWT-based authentication for API
- OAuth 2.0 for third-party integrations
- API keys for service-to-service communication
- Session management with refresh tokens

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Audit logging for sensitive actions
- Principle of least privilege

### Data Protection
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Secrets management via vault
- PII data masking in logs

### Security Checklist
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection for web UI
- [ ] CSRF tokens for state-changing requests
- [ ] Rate limiting on public endpoints
- [ ] Dependency vulnerability scanning
- [ ] Regular security audits
- [ ] Incident response plan documented

## Performance Optimization

### Backend
- Use async/await for non-blocking I/O
- Implement caching for frequent queries
- Use database connection pooling
- Batch processing for bulk operations
- Pagination for list endpoints

### Frontend
- Code splitting and lazy loading
- Image optimization and CDN
- Debounced search inputs
- Virtual scrolling for long lists
- Memoization of expensive computations

### Mobile
- Image caching with FastImage
- State management optimization
- Lazy loading screens
- Background task optimization
- Network request batching

## Troubleshooting Common Issues

### Backend
**Issue**: Module import errors
- Check PYTHONPATH is set correctly
- Verify all dependencies are installed
- Check for circular imports

**Issue**: Database connection failures
- Verify database service is running
- Check connection string in environment
- Review network/firewall settings

**Issue**: Async task not executing
- Ensure event loop is running
- Check for unhandled exceptions
- Verify task is properly awaited

### Frontend
**Issue**: Component not rendering
- Check console for errors
- Verify props are being passed correctly
- Review state initialization

**Issue**: API calls failing
- Check network tab for request details
- Verify API endpoint URLs
- Review CORS configuration

**Issue**: Styling not applying
- Check Tailwind class names
- Verify CSS specificity
- Review component structure

### Mobile
**Issue**: App crashes on startup
- Check Metro bundler output
- Verify native module linking
- Review device compatibility

**Issue**: Poor scroll performance
- Implement FlatList/VirtualizedList
- Optimize image sizes
- Reduce re-renders

## Release Process

### Versioning
- Semantic versioning (MAJOR.MINOR.PATCH)
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

### Release Checklist
- [ ] All tests passing
- [ ] Code coverage maintained
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Migration scripts prepared
- [ ] Release candidate deployed to staging
- [ ] Smoke tests passed
- [ ] Performance benchmark verified
- [ ] Security scan completed
- [ ] Release approved by team lead

### Release Steps
1. Create release branch `release/v{major}.{minor}.{patch}`
2. Run full test suite
3. Update version numbers
4. Generate changelog
5. Create GitHub release with tag
6. Deploy to production
7. Monitor for issues (24h)
8. Announce release to team

## Community

### Communication
- GitHub Issues for bug reports and feature requests
- Pull Requests for code contributions
- Discord for real-time discussion
- Wiki for documentation

### Code of Conduct
- Be respectful and inclusive
- Provide constructive feedback
- Focus on the problem, not the person
- Follow the project's coding standards

### Getting Help
- Check existing documentation
- Search GitHub issues
- Ask in Discord #dev channel
- Tag maintainers for urgent issues

---

*Thank you for contributing to Infra-pilot!*
