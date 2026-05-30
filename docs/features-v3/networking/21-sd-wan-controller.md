# Feature 21: SD-WAN Controller

## Overview
Software-Defined WAN controller for managing multiple internet uplinks, traffic steering, and failover policies. Provides per-application QoS, latency/loss monitoring, and automatic failover.

## Components

### Integration Service: `networking/sdwan_controller.py`
- `SDWANControllerManager` - Core SD-WAN management
  - Manage uplinks (primary, secondary, LTE, etc.)
  - Traffic steering policies (app-based, IP-based, geo-based)
  - Failover groups with health checks
  - QoS policy management
  - Latency/loss/jitter monitoring
  - Path selection algorithm

### Orchestrator Agent: `cogs/sdwan_manager.py`
- Discord commands:
  - `/sdwan status` - Show SD-WAN status
  - `/sdwan uplinks` - List all uplinks
  - `/sdwan failover test` - Test failover
  - `/sdwan qos` - Show QoS policies
  - `/sdwan steering` - Show traffic steering rules

### Management Panel: `pages/networking/SDWANPage.tsx`
- SD-WAN dashboard with uplink status cards
- Traffic steering rule editor
- QoS policy configuration
- Failover test controls
- Latency/loss graphs

### Mobile: `app/networking/sdwan.tsx`
- Uplink status overview
- Failover notifications
- Basic QoS management

### CLI Commands
- `ipilot sdwan status`
- `ipilot sdwan uplinks`
- `ipilot sdwan failover test`

## API Endpoints
- `GET /api/networking/sdwan/status` - SD-WAN overall status
- `GET /api/networking/sdwan/uplinks` - List uplinks
- `POST /api/networking/sdwan/uplinks` - Add uplink
- `PUT /api/networking/sdwan/uplinks/{id}` - Update uplink
- `DELETE /api/networking/sdwan/uplinks/{id}` - Remove uplink
- `POST /api/networking/sdwan/failover/test` - Test failover
- `GET /api/networking/sdwan/failover/policies` - List failover policies
- `POST /api/networking/sdwan/failover/policies` - Create failover policy
- `GET /api/networking/sdwan/qos` - List QoS policies
- `POST /api/networking/sdwan/qos` - Create QoS policy
- `GET /api/networking/sdwan/steering` - Traffic steering rules
- `POST /api/networking/sdwan/steering` - Create steering rule
- `GET /api/networking/sdwan/metrics` - Latency/loss metrics

## Data Models

### Uplink
- id, name, type (fiber/cable/lte/5g), provider, bandwidth_up, bandwidth_down
- status (active/standby/degraded/down), ip_address, gateway
- latency_ms, packet_loss_pct, jitter_ms
- cost_per_gb, monthly_cap, priority

### FailoverPolicy
- id, name, uplink_ids, condition_type (latency/loss/packet_loss)
- threshold_ms, threshold_loss_pct, fallback_uplink_id
- auto_revert, revert_after_seconds

### QoS Policy
- id, name, application, protocol, port_range
- dscp_tag, bandwidth_limit, priority_queue
- uplink_affinity

### SteeringRule
- id, name, source_ip, destination_ip, app_id
- uplink_id, policy_id, enabled

## Implementation Details
- Health checks via ICMP ping, HTTP(S) probes, DNS queries
- Path selection based on latency, loss, jitter, cost
- Failover detection in < 5 seconds
- Traffic steering via policy-based routing
- QoS via tc (traffic control) on Linux
- Monitoring via Prometheus metrics export

## Testing
- Unit tests for failover logic
- Integration tests for uplink management
- Mock uplink simulator for testing
- Chaos testing with packet loss injection
