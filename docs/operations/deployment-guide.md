# how to deploy infra pilot

simple, beautiful, repeatable: so deployest du alle infra pilot services auf einem host.

diese anleitung nutzt docker compose als standardweg. sie startet den kompletten stack, hält daten in named volumes und erklärt einen ruhigen update- und rollback-flow.

## was deployed wird

| service | port | aufgabe |
|---------|------|---------|
| management panel | `5173` | web ui, live logs, config, backups, alerts |
| orchestrator agent | `8000` | provisioning, docker/vps automation, discord cogs |
| integration service | `9000` | auth, users, notifications, metrics, modpacks, shared api |
| service core | `8080` | java core service und player-server-logik |
| discord service | intern | discord bot und pterodactyl/provisioning bridge |
| postgres | `5432` | persistente app-daten |
| redis | `6379` | cache, sessions, coordination |
| prometheus | `9090` | optionale metrics |
| grafana | `3000` | optionale dashboards |

## bevor du startest

nimm zuerst einen kleinen linux host. keep it boring.

empfohlenes minimum:

• ubuntu 22.04 oder neuer
• 2 cpu cores
• 4 gb ram
• 30 gb disk
• docker + docker compose plugin
• eine domain mit dns auf den host
• ssh zugang

öffne nur, was wirklich öffentlich sein muss:

• `80` und `443` für app / reverse proxy
• `22` für ssh, am besten eingeschränkt
• interne service ports nur beim debugging

## 1. server vorbereiten

```bash
ssh user@your-server
sudo apt-get update
sudo apt-get install -y ca-certificates curl git openssl
```

docker installieren:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
```

runtime prüfen:

```bash
docker --version
docker compose version
```

## 2. infra pilot klonen

```bash
sudo mkdir -p /opt/infra-pilot
sudo chown "$USER":"$USER" /opt/infra-pilot
git clone https://github.com/DaaanielTV/infra-pilot.git /opt/infra-pilot
cd /opt/infra-pilot
```

wenn das repo schon existiert:

```bash
cd /opt/infra-pilot
git fetch origin
git status
```

## 3. environment konfigurieren

runtime env aus dem template erstellen:

```bash
cp .env.example .env
nano .env
```

minimum values, die du ändern solltest:

```env
NODE_ENV=production
POSTGRES_PASSWORD=replace-with-a-long-secret
JWT_SECRET=replace-with-a-long-secret
DISCORD_TOKEN=your-discord-bot-token
PTERODACTYL_API_URL=https://your-panel.example.com/api
PTERODACTYL_API_KEY=your-pterodactyl-api-key
VITE_API_URL=https://api.your-domain.example
DASHBOARD_URL=https://your-domain.example
ORCHESTRATOR_URL=http://orchestrator-agent:8000
SERVICE_CORE_URL=http://service-core:8080
INTEGRATION_API_URL=http://integration-service:9000
```

starke secrets generieren:

```bash
openssl rand -base64 32
```

`.env` bleibt privat. niemals committen.

## 4. alles bauen und starten

core stack starten:

```bash
docker compose up -d --build
```

mit monitoring starten:

```bash
docker compose --profile monitoring up -d --build
```

rollout beobachten:

```bash
docker compose ps
docker compose logs -f --tail=100
```

## 5. deployment verifizieren

container prüfen:

```bash
docker compose ps
```

service endpoints prüfen:

```bash
curl -f http://localhost:9000/health
curl -f http://localhost:5173
```

data services prüfen:

```bash
docker compose exec postgres pg_isready -U "${POSTGRES_USER:-infra_pilot}"
docker compose exec redis redis-cli ping
```

optional monitoring:

```bash
curl -f http://localhost:9090/-/healthy
curl -f http://localhost:3000/api/health
```

wenn diese checks grün sind, läuft infra pilot.

## 6. reverse proxy davor setzen

in production nicht jeden container-port öffentlich exposen. nutze nginx, caddy, traefik oder einen cloud load balancer.

einfaches routing model:

| public url | target |
|------------|--------|
| `https://your-domain.example` | `management-panel:5173` |
| `https://api.your-domain.example` | `integration-service:9000` |
| `https://orchestrator.your-domain.example` | `orchestrator-agent:8000` nur wenn nötig |

postgres, redis, service core und discord service bleiben privat.

## update flow

updates sollen ruhig sein: backup, pull, build, rollout, verify.

### 1. backup zuerst

```bash
cd /opt/infra-pilot
mkdir -p backups
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-infra_pilot}" \
  "${POSTGRES_DB:-infra_pilot}" > "backups/infra-pilot-$(date +%Y%m%d-%H%M%S).sql"
```

optionaler volume snapshot:

```bash
docker run --rm \
  -v infra-pilot_postgres_data:/data:ro \
  -v "$PWD/backups:/backup" \
  alpine tar czf /backup/postgres-volume-$(date +%Y%m%d-%H%M%S).tgz -C /data .
```

### 2. neue version holen

```bash
git fetch origin
git pull --ff-only
```

wenn du tagged releases deployest:

```bash
git fetch --tags
git checkout vX.Y.Z
```

### 3. rebuild und rollout

```bash
docker compose up -d --build
```

mit monitoring:

```bash
docker compose --profile monitoring up -d --build
```

compose ersetzt geänderte container und behält named volumes.

### 4. nach dem update prüfen

```bash
docker compose ps
curl -f http://localhost:9000/health
curl -f http://localhost:5173
docker compose logs --tail=100 integration-service management-panel orchestrator-agent
```

## rollback flow

rollback ist auch nur ein deploy, aber auf die letzte gute revision.

### 1. letzte gute revision finden

```bash
git log --oneline -10
```

### 2. zurück wechseln

```bash
git checkout <good-commit-or-tag>
docker compose up -d --build
```

### 3. datenbank nur bei bedarf zurückspielen

restore nur machen, wenn eine migration oder ein fehlerhaftes release production daten verändert hat.

```bash
cat backups/infra-pilot-YYYYMMDD-HHMMSS.sql | \
  docker compose exec -T postgres psql \
  -U "${POSTGRES_USER:-infra_pilot}" \
  "${POSTGRES_DB:-infra_pilot}"
```

## service operations

### einen service neu starten

```bash
docker compose restart integration-service
```

beispiele:

```bash
docker compose restart management-panel
docker compose restart orchestrator-agent
docker compose restart discord-service
```

### einen service rebuilden

```bash
docker compose up -d --build management-panel
```

### logs ansehen

```bash
docker compose logs -f integration-service
```

alle services:

```bash
docker compose logs -f --tail=200
```

### alles stoppen

```bash
docker compose down
```

stoppen und lokale daten-volumes löschen, nur wenn du es wirklich meinst:

```bash
docker compose down -v
```

## production checklist

• `.env` nutzt production secrets
• `POSTGRES_PASSWORD` und `JWT_SECRET` sind unique und lang
• discord und pterodactyl tokens sind gültig
• reverse proxy terminiert tls
• nur public routes sind exposed
• postgres und redis sind privat
• backups sind getestet, nicht nur erstellt
• monitoring ist für long-running hosts aktiv
• update- und rollback-kommandos sind im team bekannt

## troubleshooting

### container wird nicht healthy

```bash
docker compose ps
docker compose logs --tail=200 <service-name>
```

### datenbank ist nicht ready

```bash
docker compose logs postgres
docker compose exec postgres pg_isready -U "${POSTGRES_USER:-infra_pilot}"
```

### redis ist nicht ready

```bash
docker compose logs redis
docker compose exec redis redis-cli ping
```

### frontend erreicht die api nicht

prüfe diese werte in `.env`:

```env
VITE_API_URL=https://api.your-domain.example
DASHBOARD_URL=https://your-domain.example
INTEGRATION_API_URL=http://integration-service:9000
```

danach panel neu bauen:

```bash
docker compose up -d --build management-panel
```

### discord bot startet nicht

```bash
docker compose logs -f discord-service
```

prüfe:

• `DISCORD_TOKEN`
• bot intents im discord developer portal
• `PTERODACTYL_API_URL`
• `PTERODACTYL_API_KEY`

## kubernetes path

nutze kubernetes, wenn ein host nicht mehr reicht.

das deployment model bleibt gleich:

• ein deployment pro service
• postgres und redis wenn möglich als managed services
• secrets über kubernetes secrets oder external secrets
• ingress für public routes
• rolling updates mit `maxUnavailable: 0`

basic rollout shape:

```bash
kubectl create namespace infra-pilot
kubectl apply -n infra-pilot -f infrastructure/kubernetes/
kubectl rollout status -n infra-pilot deployment/management-panel
```

für jetzt ist docker compose die reference deployment path. kubernetes manifests sollten mit der service-liste oben aligned bleiben.

## related docs

• [local development](../setup/local-development.md)
• [ci architecture](../development/ci-architecture.md)
• [testing](../testing/running_tests.md)
• [security review](../security/security-review-2026-05-04.md)

last updated: may 2026
