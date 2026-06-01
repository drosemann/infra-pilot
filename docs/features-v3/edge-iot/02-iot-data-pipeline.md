# Feature 2: IoT Data Pipeline

## Overview
Ingest MQTT, CoAP, and HTTP sensor data from IoT devices. Transform, filter, and route data to storage or triggers. Rule engine for threshold-based alerts.

## Capabilities
- MQTT broker integration (Mosquitto, EMQX, HiveMQ)
- CoAP server for constrained devices
- HTTP ingestion endpoint for RESTful sensor reporting
- Data transformation pipeline (JSON normalization, unit conversion, aggregation)
- Rule engine for threshold alerts and triggers
- Multiple output sinks (PostgreSQL, InfluxDB, MQTT topics, webhooks)
- Data retention policies and auto-archival

## Architecture

```
IoT Devices → [MQTT/CoAP/HTTP] → Pipeline Controller → Transform Chain → Router → Sinks
                                           ↓
                                      Rule Engine → Alerts
```

## Protocol Adapters

### MQTT Adapter
- Connects to any MQTT broker (v3.1.1, v5.0)
- Subscribe to topics with wildcards
- QoS 0, 1, 2 support
- TLS client certificate authentication
- Automatic reconnection with exponential backoff

### CoAP Adapter  
- CoAP server on port 5683
- DTLS for secure connections
- Observe mode for streaming sensor data
- Block-wise transfer for large payloads

### HTTP Adapter
- POST endpoint for JSON sensor data
- API key authentication
- Rate limiting per device
- Batch upload support

## Rule Engine

Rules are evaluated in order. Each rule has:
- **Condition**: Expression using sensor values (e.g., `temperature > 85`)
- **Action**: One of: alert, store, forward, transform, drop
- **Target**: Where to send or store the result

Example rules:
```
IF temperature > 85 AND humidity < 20 THEN alert("fire_risk")
IF vibration > 5.0 THEN store(influxdb, priority=high) AND forward(webhook)
IF battery < 10 THEN alert("battery_critical") AND store(postgresql)
```

## Data Sinks

| Sink | Protocol | Configuration |
|------|----------|--------------|
| PostgreSQL | SQL | Connection string, table mapping |
| InfluxDB | HTTP API | Org, bucket, token, measurement |
| MQTT | Pub | Broker, topic template, QoS |
| Webhook | HTTP POST | URL, headers, retry policy |
| Kafka | Pub | Brokers, topic, acks |

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/iot_data_pipeline.py`
- Full test suite with simulated MQTT/CoAP traffic
- CLI commands for pipeline management
