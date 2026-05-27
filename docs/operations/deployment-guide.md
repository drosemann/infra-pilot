# production deployment guide

deploy infra pilot to production environments with confidence.

## deployment options

### option 1: docker compose (suitable for small-to-medium deployments)

pros: simple, all-in-one
cons: single point of failure, harder to scale

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### option 2: kubernetes (recommended for production)

pros: high availability, auto-scaling, self-healing
cons: higher complexity

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/deployments/
kubectl apply -f infrastructure/kubernetes/services/
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

### option 3: terraform + cloud provider

pros: infrastructure as code, repeatable, multi-region
cons: cloud provider knowledge required

```bash
cd infrastructure/terraform/aws
terraform init
terraform plan
terraform apply
```

## pre-deployment checklist

• [ ] all tests passing in ci/cd
• [ ] code reviewed and approved
• [ ] secrets configured (api keys, tokens)
• [ ] database backed up
• [ ] ssl/tls certificates configured
• [ ] monitoring and alerting set up
• [ ] rollback plan documented
• [ ] change logged and approved

## docker compose production deployment

### prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### deployment steps

#### prepare server

```bash
# SSH into production server
ssh user@production-server.com

# Create project directory
mkdir -p /opt/gemini
cd /opt/gemini

# Clone repository
git clone https://github.com/DaaanielTV/infra-pilot.git .
```

#### configure environment

```bash
# Copy and edit production environment
cp .env.example .env.prod

# Edit configuration
nano .env.prod
```

production `.env.prod` example:
```env
NODE_ENV=production
DEBUG=false

# Services
DASHBOARD_URL=https://your-domain.com
ORCHESTRATOR_URL=https://api.your-domain.com
SERVICE_CORE_URL=https://core.your-domain.com

# Database (use managed service if possible)
DATABASE_URL=postgresql://user:password@db.your-domain.com:5432/gemini
DATABASE_POOL_SIZE=20
DATABASE_SSL=true

# Redis cluster
REDIS_URL=redis://redis-cluster.your-domain.com:6379

# Secrets
JWT_SECRET=generate-strong-random-key
CONVEX_DEPLOYMENT=production

# External Services
PTERODACTYL_API_KEY=your-key
DISCORD_BOT_TOKEN=your-token
SENTRY_DSN=https://your-sentry-dsn

# Security
ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com
SSL_CERT_PATH=/etc/ssl/certs/your-cert.crt
SSL_KEY_PATH=/etc/ssl/private/your-key.key
```

#### start services

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml ps
```

#### verify deployment

```bash
# Check service health
curl https://your-domain.com/health
curl https://api.your-domain.com/health

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check resource usage
docker stats
```

## kubernetes deployment

### prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Access to Kubernetes cluster (AWS EKS, GCP GKE, Azure AKS, etc)
```

### deployment steps

#### create namespace

```bash
kubectl create namespace gemini
kubectl label namespace gemini environment=production
```

#### create secrets

```bash
# Database credentials
kubectl create secret generic db-credentials \
  --from-literal=username=gemini \
  --from-literal=password=$(openssl rand -base64 32) \
  -n gemini

# API keys and tokens
kubectl create secret generic api-keys \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  --from-literal=discord-token=your-token \
  --from-literal=pterodactyl-key=your-key \
  -n gemini

# TLS certificates (if not using cert-manager)
kubectl create secret tls tls-secret \
  --cert=path/to/cert.crt \
  --key=path/to/key.key \
  -n gemini
```

#### deploy services

```bash
# Apply all manifests
kubectl apply -f infrastructure/kubernetes/

# Wait for deployments
kubectl rollout status deployment -n gemini

# Check pod status
kubectl get pods -n gemini
```

#### set up ingress

```bash
# If using Nginx Ingress
kubectl apply -f infrastructure/kubernetes/ingress.yaml

# Get LoadBalancer IP
kubectl get svc -n gemini
```

## multi-region deployment

### strategy

```
┌─────────────────┐     ┌─────────────────┐
│   Region 1      │     │   Region 2      │
│  (us-east-1)    │     │  (eu-west-1)    │
│   Cluster 1     │     │   Cluster 2     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
           ┌─────────────────┐
           │  Global LB      │
           │  (DNS failover) │
           └─────────────────┘
```

### implementation

```bash
# Deploy to region 1
export KUBECONFIG=~/.kube/config-region1
kubectl apply -f infrastructure/kubernetes/

# Deploy to region 2
export KUBECONFIG=~/.kube/config-region2
kubectl apply -f infrastructure/kubernetes/

# Configure global load balancer (AWS Route53, Azure Traffic Manager, etc)
# Set up DNS failover policies
```

## monitoring deployment

### prometheus

```bash
# Check metrics
kubectl port-forward -n gemini svc/prometheus 9090:9090
# Navigate to http://localhost:9090
```

### grafana

```bash
# Access Grafana
kubectl port-forward -n gemini svc/grafana 3000:3000
# Navigate to http://localhost:3000
# Default credentials: admin/admin
```

### logs

```bash
# View service logs
kubectl logs -n gemini deployment/orchestrator-agent -f

# View all logs
kubectl logs -n gemini --all-containers=true -f
```

## updates & rollbacks

### rolling update

```bash
# Update image
kubectl set image deployment/orchestrator-agent \
  orchestrator-agent=your-registry/orchestrator:v1.1.0 \
  -n gemini

# Monitor rollout
kubectl rollout status deployment/orchestrator-agent -n gemini

# View history
kubectl rollout history deployment/orchestrator-agent -n gemini
```

### rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/orchestrator-agent -n gemini

# Rollback to specific revision
kubectl rollout undo deployment/orchestrator-agent --to-revision=3 -n gemini
```

### zero-downtime deployment

set in deployment manifest:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

## security hardening

### network policies

```bash
kubectl apply -f infrastructure/kubernetes/network-policies/
```

### pod security policies

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'MustRunAs'
  fsGroup:
    rule: 'MustRunAs'
  readOnlyRootFilesystem: false
```

### resource limits

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

## troubleshooting deployment

### service won't start

```bash
# Check pod status
kubectl describe pod <pod-name> -n gemini

# Check logs
kubectl logs <pod-name> -n gemini

# Check events
kubectl get events -n gemini --sort-by='.lastTimestamp'
```

### connectivity issues

```bash
# Test DNS
kubectl run -it --image=busybox:1.28 --restart=Never --rm debug -- nslookup kubernetes.default

# Test network policies
kubectl port-forward service/orchestrator-agent 8000:8000 -n gemini
```

### database connectivity

```bash
# Test connection from pod
kubectl run -it --image=postgres:15 --restart=Never --rm -- \
  psql postgresql://user:password@db-host:5432/gemini -c "SELECT 1;"
```

## performance tuning

### database connection pooling

```env
DATABASE_POOL_SIZE=20
DATABASE_POOL_IDLE_TIMEOUT=300
DATABASE_MAX_LIFETIME=1800
```

### cache configuration

```env
REDIS_POOL_SIZE=10
REDIS_TIMEOUT=5000
```

### service replicas

```yaml
replicas: 3  # Increase for higher load
```

## related documentation

• [kubernetes setup](../setup/kubernetes-deploy.md)
• [monitoring & observability](monitoring-observability.md)
• [scaling strategy](scaling-strategy.md)
• [troubleshooting](troubleshooting.md)

last updated: april 2026
