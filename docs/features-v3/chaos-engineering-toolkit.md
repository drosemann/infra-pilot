# Feature 79: Chaos Engineering Toolkit

## Overview
Controlled fault injection toolkit for testing system resilience using chaos engineering principles with support for multiple fault types, blast radius control, and experiment management.

## Components
- `chaos_engine.py` - Core chaos experiment engine
- `fault_injector.py` - Fault injection implementations
- `experiment_manager.py` - Experiment lifecycle management
- `chaos_routes.py` - API endpoints
- `ChaosManager` - Manager class

## Supported Fault Types
- **Infrastructure**: CPU stress, Memory fill, Disk fill, Network latency, Packet loss, DNS failure
- **Container**: Kill container, Stop container, Resource limit, Image pull failure
- **Network**: Latency, Packet loss, Bandwidth limit, Port blockage, DNS failure
- **Cloud**: Instance stop, Volume detach, Security group change
- **Application**: HTTP error, Slow response, Exception injection
- **Database**: Connection pool exhaustion, Slow query, Table lock

## Experiment Definition
```json
{
  "id": "uuid",
  "name": "Test payment service resilience",
  "target": {
    "type": "container",
    "selector": {"service": "payment-api", "environment": "staging"}
  },
  "faults": [
    {"type": "network_latency", "duration": 60, "config": {"latency_ms": 2000, "jitter_ms": 500}},
    {"type": "cpu_stress", "duration": 30, "config": {"cores": 1, "load_percent": 80}}
  ],
  "steady_state": {
    "metrics": [
      {"metric": "http.latency.p99", "threshold": 500},
      {"metric": "error.rate", "threshold": 0.01}
    ]
  },
  "rollback_on_failure": true,
  "blast_radius": {"namespaces": ["staging"], "services": ["payment-*"]}
}
```

## API Endpoints
- `GET /api/v1/chaos/experiments` - List experiments
- `POST /api/v1/chaos/experiments` - Create experiment
- `GET /api/v1/chaos/experiments/{id}` - Get experiment
- `PUT /api/v1/chaos/experiments/{id}` - Update experiment
- `DELETE /api/v1/chaos/experiments/{id}` - Delete experiment
- `POST /api/v1/chaos/experiments/{id}/run` - Run experiment
- `POST /api/v1/chaos/experiments/{id}/stop` - Stop experiment
- `GET /api/v1/chaos/experiments/{id}/results` - Experiment results
- `GET /api/v1/chaos/fault-types` - Available fault types
- `GET /api/v1/chaos/history` - Experiment history

## Safety Mechanisms
- Blast radius limits (namespace, service, instance selectors)
- Automatic rollback on failure
- Scheduled experiment end time
- Kill switch to stop all active experiments
- Steady state validation before/during/after
