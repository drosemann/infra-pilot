# Chaos Engineering Toolkit API Reference
## Overview
Controlled fault injection for resilience testing with 10 fault types, blast radius control, and automated rollback.

## Base URL: /api/v1/orchestration/chaos

### POST /experiments
Create a chaos experiment.
**Request:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| name | yes | string | Experiment name |
| description | yes | string | Experiment description |
| target | yes | object | Target specification |
| faults | yes | array | Fault definitions |
| blast_radius | no | object | Blast radius limits |
| rollback_on_failure | no | boolean | Auto-rollback on failure |
| schedule | no | object | Scheduled execution |

**Target Schema:**
```json
{
  "type": "container|host|service|namespace|region",
  "selector": "app=web-server",
  "namespace": "production",
  "labels": {"tier": "frontend"}
}
```

**Fault Schema:**
```json
{
  "type": "cpu_stress",
  "parameters": {
    "cores": 4,
    "duration": 60,
    "load_percentage": 80
  }
}
```

**Blast Radius Schema:**
```json
{
  "max_containers": 3,
  "max_hosts": 1,
  "exclude": ["critical-svc", "database-primary"],
  "exclude_namespaces": ["kube-system"],
  "max_faults_per_target": 2
}
```

**Response:**
```json
{
  "experiment_id": "ce_abc123",
  "name": "CPU Spike Test",
  "status": "created",
  "target": {"type": "container", "selector": "app=web"},
  "faults": [...],
  "blast_radius": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /experiments
List experiments. Query: status, target_type

### GET /experiments/{experiment_id}
Get experiment details.

### PUT /experiments/{experiment_id}
Update experiment definition.

### DELETE /experiments/{experiment_id}
Delete experiment.

### POST /experiments/{experiment_id}/run
Start experiment execution.

### POST /experiments/{experiment_id}/stop
Stop experiment immediately and rollback.

### POST /experiments/{experiment_id}/pause
Pause running experiment.

### POST /experiments/{experiment_id}/resume
Resume paused experiment.

### GET /experiments/{experiment_id}/results
Get experiment results with metrics.

### GET /fault-types
List available fault types with parameters.
**Response:**
```json
[
  {
    "id": "cpu_stress",
    "name": "CPU Stress",
    "category": "compute",
    "description": "Stress CPU cores to test autoscaling",
    "parameters": [
      {"name": "cores", "type": "integer", "default": 1, "min": 1, "max": 32},
      {"name": "duration", "type": "integer", "default": 30, "min": 5, "max": 300},
      {"name": "load_percentage", "type": "integer", "default": 100, "min": 10, "max": 100}
    ]
  }
]
```

## Fault Types (10)

### 1. CPU Stress
Stress CPU cores to test autoscaling and throttling.
- Parameters: cores (1-32), duration (5-300s), load_percentage (10-100)
- Use case: Test HPA scaling, CPU limit enforcement

### 2. Memory Hog
Consume memory to test OOM handling and limits.
- Parameters: size_mb (64-8192), duration (5-300s)
- Use case: Test memory limits, OOM kill behavior

### 3. Disk Fill
Fill disk space to test storage monitoring.
- Parameters: size_mb (100-102400), path, fill_speed_mbps
- Use case: Test disk alerts, eviction policies

### 4. Network Delay
Inject network latency.
- Parameters: latency_ms (10-5000), jitter_ms (0-1000), percentage (0-100)
- Use case: Test timeout handling, retry logic

### 5. Network Packet Loss
Drop network packets.
- Parameters: loss_percentage (0.1-50), correlation (0-100)
- Use case: Test network resilience

### 6. Network Partition
Create network partition between services.
- Parameters: target_service, protocol (tcp/udp/all), ports
- Use case: Test service mesh failover

### 7. Container Kill
Kill containers to test rescheduling.
- Parameters: kill_count (1-10), interval_seconds, signal (SIGTERM/SIGKILL)
- Use case: Test Kubernetes pod resilience

### 8. DNS Failure
Block DNS resolution for specific domains.
- Parameters: domains, failure_rate (0-100)
- Use case: Test DNS caching, fallback logic

### 9. IO Stress
High disk I/O to test performance isolation.
- Parameters: workers (1-8), io_type (read/write/rw), block_size, duration
- Use case: Test IOPS limits, disk QoS

### 10. Database Latency
Inject latency into database connections.
- Parameters: db_type (postgres/mysql/mongo), latency_ms, query_pattern
- Use case: Test query timeout, connection pooling

## Self-Healing Infrastructure API Reference
## Base URL: /api/v1/orchestration/healing

### GET /status
Get self-healing system status.
**Response:**
```json
{
  "enabled": true,
  "total_remediations": 156,
  "success_rate": 94.2,
  "patterns_detected": 7,
  "model_learned_actions": 12,
  "auto_remediation_enabled": true,
  "model_version": "v2.3.1",
  "last_trained": "2024-01-14T10:30:00Z",
  "confidence_thresholds": {
    "auto_remediate": 0.85,
    "suggest": 0.65,
    "log_only": 0.40
  }
}
```

### POST /remediate
Trigger remediation for a specific context.
**Request:**
| Field | Required | Description |
|-------|----------|-------------|
| context | yes | Context data describing the issue |

**Example:**
```json
{
  "context": {
    "container": "web-01",
    "restart_count": 6,
    "cpu_percent": 90,
    "memory_percent": 85,
    "health": "unhealthy"
  }
}
```

**Response:**
```json
{
  "pattern": "container_restart",
  "confidence": 0.92,
  "action": "container_restart",
  "remediation": "Restarting container web-01",
  "status": "executed",
  "execution_id": "heal_001"
}
```

### GET /history
List remediation history.
**Query Parameters:** pattern, result, limit, from_date, to_date

### GET /history/{execution_id}
Get specific remediation execution details.

### POST /feedback
Submit feedback on a remediation action (reinforcement learning).
**Request:** { "context_id", "action_taken", "success": true, "notes": "string" }

### POST /retrain
Retrain the healing model with accumulated feedback.

### GET /patterns
List detected patterns with success rates.
**Response:**
```json
[
  {
    "pattern": "container_restart",
    "recommended_action": "restart_container",
    "avg_success_rate": 0.95,
    "detection_count": 87,
    "confidence_threshold": 0.80
  }
]
```

## Detection Patterns (7)
1. **Container Restart Loop** - Container restarting repeatedly >5 times
2. **Memory Leak** - Memory usage increasing over time without release
3. **CPU Spikes** - Sudden CPU utilization >90%
4. **Disk Pressure** - Disk usage >85% or inode exhaustion
5. **OOM Kills** - Out of memory kills detected
6. **Unhealthy Endpoints** - Health check failures
7. **Connection Pool Exhaustion** - Database connection pool depletion

## Learning Loop
1. Pattern detection via event monitoring
2. Confidence calculation using Q-learning model
3. Action selection based on confidence thresholds:
   - >0.85: Auto-remediate
   - 0.65-0.85: Suggest to operator
   - <0.65: Log only
4. Action execution with cooldown enforcement
5. Feedback collection (success/failure)
6. Model retraining with accumulated experience
7. Confidence threshold adjustment per pattern
