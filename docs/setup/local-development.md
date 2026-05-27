# local development setup

get the infra pilot platform running on your local machine in 15 minutes.

## prerequisites

### system requirements

• os: linux, macos, windows (wsl2)
• memory: 4gb minimum (8gb recommended)
• disk: 10gb free space
• network: internet access

### software requirements

| tool | version | purpose |
|------|---------|---------|
| git | 2.30+ | version control |
| docker | 20.10+ | containerization |
| docker compose | 1.29+ | multi-container orchestration |
| node.js | 18 lts | dashboard & discord bot |
| python | 3.9+ | orchestrator agent |
| java | 8+ | service core |
| maven | 3.6+ | java build tool |

### verify installation

```bash
git --version              # Git 2.30+
docker --version           # Docker 20.10+
docker-compose --version   # Docker Compose 1.29+
node --version             # Node.js 18+
python3 --version          # Python 3.9+
java -version              # Java 8+
mvn --version              # Maven 3.6+
```

## quick start (docker compose)

### option a: fastest (recommended)

```bash
# 1. Clone repository
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot

# 2. Start all services
docker-compose up -d

# 3. Wait for services to initialize (30-60 seconds)
sleep 60

# 4. Verify services are running
docker-compose ps

# 5. Access services
open http://localhost:5173  # Management Dashboard
```

### option b: with log viewing

```bash
# Start services and view logs
docker-compose up

# In another terminal, view specific service logs
docker-compose logs -f orchestrator-agent
docker-compose logs -f management-dashboard
```

### access points

| service | url | purpose |
|---------|-----|---------|
| dashboard | http://localhost:5173 | web operations ui |
| orchestrator api | http://localhost:8000 | api endpoint |
| service core | http://localhost:8080 | server management |
| postgresql | localhost:5432 | database |
| redis | localhost:6379 | cache |

## manual setup (local development)

if you prefer running services locally without docker:

### step 1: clone repository

```bash
git clone https://github.com/DaaanielTV/infra-pilot.git
cd infra-pilot
```

### step 2: configure environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (adjust as needed)
nano .env
# or
code .env  # If using VS Code
```

key variables to configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/gemini
REDIS_URL=redis://localhost:6379

# Services
DASHBOARD_PORT=5173
ORCHESTRATOR_PORT=8000
SERVICE_CORE_PORT=8080

# External APIs (optional for development)
PTERODACTYL_API_KEY=your-key
DISCORD_BOT_TOKEN=your-token
```

### step 3: install dependencies

#### management dashboard

```bash
cd services/management-dashboard
npm install
npm run dev
# Opens at http://localhost:5173
```

#### orchestrator agent

```bash
# In new terminal
cd services/orchestrator-agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
# Runs at http://localhost:8000
```

#### discord service

```bash
# In new terminal
cd services/discord-service
npm install
npm start
# Connects to Discord
```

#### service core (java)

```bash
# In new terminal
cd services/service-core
mvn clean install
mvn spring-boot:run
# Runs at http://localhost:8080
```

### step 4: setup databases

```bash
# Option A: Using Docker containers
docker pull postgres:15
docker run -d --name gemini-postgres \
  -e POSTGRES_USER=gemini \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=gemini \
  -p 5432:5432 \
  postgres:15

docker pull redis:7
docker run -d --name gemini-redis \
  -p 6379:6379 \
  redis:7

# Option B: Install locally (macOS)
brew install postgresql redis
brew services start postgresql
brew services start redis
```

## configuration

### environment variables

create `.env` file in root directory:

```env
# Application
NODE_ENV=development
DEBUG=true

# Services
DASHBOARD_URL=http://localhost:5173
ORCHESTRATOR_URL=http://localhost:8000
SERVICE_CORE_URL=http://localhost:8080

# Database
DATABASE_URL=postgresql://gemini:dev@localhost:5432/gemini
DATABASE_POOL_SIZE=10

# Cache
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=dev-secret-key-change-in-production
CONVEX_DEPLOYMENT=dev

# External Services
PTERODACTYL_URL=https://panel.example.com
PTERODACTYL_API_KEY=ptl_xxxxx
DISCORD_BOT_TOKEN=your_token_here
DISCORD_WEBHOOK_SECRET=your_secret

# Monitoring
SENTRY_DSN=optional
LOG_LEVEL=debug
```

### service-specific config

**management dashboard:** `services/management-dashboard/.env`
```env
VITE_API_URL=http://localhost:8000
VITE_CONVEX_URL=http://localhost:3210
```

**orchestrator agent:** `services/orchestrator-agent/.env`
```env
ORCHESTRATOR_PORT=8000
LOG_LEVEL=DEBUG
DATABASE_ECHO=true
```

## running tests

### test all services

```bash
./scripts/test.sh
```

### test individual services

```bash
# Dashboard tests
cd services/management-dashboard
npm run test
npm run test:watch  # Watch mode

# Orchestrator tests
cd services/orchestrator-agent
pytest tests/
pytest tests/ -v --cov  # With coverage

# Discord bot tests
cd services/discord-service
npm run test

# Service Core tests
cd services/service-core
mvn test
mvn test -DskipTests=false -Dtest=TestClass  # Specific test
```

## development workflow

### creating a feature

```bash
# Create feature branch from main
git checkout -b feature/my-feature

# Make changes in appropriate service
cd services/your-service

# Test locally
npm run test  # or pytest, mvn test

# Commit with clear message
git commit -m "feat: add new provisioning flow"

# Push and open PR
git push origin feature/my-feature
```

### debugging

#### docker containers

```bash
# View logs
docker-compose logs orchestrator-agent

# Enter container shell
docker-compose exec orchestrator-agent bash

# Restart service
docker-compose restart management-dashboard
```

#### local services

```bash
# Python debugging
import pdb; pdb.set_trace()

# Node.js debugging
node --inspect-brk=0.0.0.0:9229 main.js
# Connect inspector in Chrome: chrome://inspect

# Java debugging
mvn -Dagentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005 spring-boot:run
# Connect in IDE to localhost:5005
```

#### logs

```bash
# View all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f orchestrator-agent

# Last 50 lines
docker-compose logs --tail=50 management-dashboard

# With timestamps
docker-compose logs -f --timestamps
```

## common tasks

### update dependencies

```bash
# Dashboard
cd services/management-dashboard
npm update
npm audit fix

# Orchestrator
cd services/orchestrator-agent
pip list --outdated
pip install --upgrade package-name

# Service Core
cd services/service-core
mvn dependency:tree
mvn versions:display-dependency-updates
```

### database operations

```bash
# Connect to PostgreSQL
psql -h localhost -U gemini -d gemini
# Password: dev

# View tables
\dt

# Backup database
pg_dump -h localhost -U gemini -d gemini > backup.sql

# Restore database
psql -h localhost -U gemini -d gemini < backup.sql
```

### clear cache & rebuild

```bash
# Stop all services
docker-compose down

# Remove volumes (careful - deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### monitor resource usage

```bash
# Docker stats
docker stats

# System resources
top          # macOS/Linux
Get-Process  # Windows
```

## troubleshooting

### service won't start

```bash
# Check port is available
lsof -i :5173      # Dashboard
lsof -i :8000      # Orchestrator
lsof -i :8080      # Service Core
lsof -i :5432      # Database

# Kill process on port
kill -9 $(lsof -t -i:5173)

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### database connection issues

```bash
# Test connection
psql -h localhost -U gemini -d gemini -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d
```

### memory issues

```bash
# Increase Docker memory
# macOS: Docker > Preferences > Resources > Memory
# Linux: Check available memory: free -h

# Reduce container resource limits in docker-compose.yml
services:
  orchestrator-agent:
    deploy:
      resources:
        limits:
          memory: 1G
```

### api connection issues

```bash
# Test API endpoint
curl http://localhost:8000/health

# Check service is running
docker-compose ps

# View logs
docker-compose logs orchestrator-agent
```

## additional resources

• [docker deployment](docker-setup.md) - production docker setup
• [development workflow](../development/development-workflow.md) - contributing guidelines
• [testing strategy](../development/testing-strategy.md) - testing best practices
• [troubleshooting](../operations/troubleshooting.md) - advanced troubleshooting

## verification checklist

after setup, verify everything works:

• [ ] dashboard loads at http://localhost:5173
• [ ] can login to dashboard
• [ ] orchestrator api responds to `curl http://localhost:8000/health`
• [ ] can view services in dashboard
• [ ] database connection works
• [ ] all tests pass: `./scripts/test.sh`

if all checks pass, you're ready to develop!

last updated: april 2026
