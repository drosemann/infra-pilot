# Feature 1: Edge Device Manager

## Overview
Register, monitor, and manage Raspberry Pi, Jetson Nano, RockPi, and other ARM/x86 devices as edge nodes in the Infra Pilot platform.

## Capabilities
- Device registration with hardware fingerprinting
- Remote firmware/OS updates via OTA mechanism
- Health pings with automatic alerting on failure
- Geolocation tagging for physical device tracking
- Resource monitoring (CPU, RAM, disk, temperature)
- Remote command execution and script deployment
- Device grouping and tagging for organization

## Architecture
The Edge Device Manager consists of:

1. **Orchestrator Cog** (`services/orchestrator-agent/cogs/edge_device_manager.py`): Core Discord bot integration for device management
2. **Integration Module** (`services/integration-service/src/edge_device_manager.py`): REST API for device CRUD and monitoring
3. **Agent Daemon** deployed on each edge node for heartbeats and command execution
4. **Management Panel** UI for visual device management
5. **CLI Commands** for device operations

## Data Model

```
EdgeDevice {
  id: UUID
  name: string
  device_type: enum(raspberry_pi, jetson_nano, rockpi, generic_arm, generic_x86)
  hardware_id: string (unique, from CPU serial / MAC)
  fingerprint: string (SHA256 of hardware composite)
  geolocation: { lat: float, lng: float, label: string }
  tags: string[]
  firmware_version: string
  agent_version: string
  status: enum(online, offline, degraded, provisioning)
  last_heartbeat: datetime
  created_at: datetime
  updated_at: datetime
  metadata: dict
  
  resources: {
    cpu_cores: int
    cpu_usage: float (%)
    memory_total_mb: int
    memory_used_mb: int
    disk_total_gb: int
    disk_used_gb: int
    temperature_celsius: float
    uptime_seconds: int
  }
}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/edge/devices | List all devices |
| POST | /api/v1/edge/devices | Register new device |
| GET | /api/v1/edge/devices/{id} | Get device details |
| PUT | /api/v1/edge/devices/{id} | Update device |
| DELETE | /api/v1/edge/devices/{id} | Remove device |
| POST | /api/v1/edge/devices/{id}/heartbeat | Receive heartbeat |
| GET | /api/v1/edge/devices/{id}/metrics | Get metrics history |
| POST | /api/v1/edge/devices/{id}/command | Execute command |
| POST | /api/v1/edge/devices/{id}/firmware | Trigger firmware update |
| GET | /api/v1/edge/devices/groups | List device groups |
| POST | /api/v1/edge/devices/groups | Create device group |

## Security
- All communications over mTLS
- Device identity verified via hardware fingerprint
- Signed heartbeats prevent spoofing
- Role-based access control for management operations

## Implementation Plan

1. Create data models and database schema
2. Implement device registration and heartbeat handling
3. Build remote command execution framework
4. Implement firmware update mechanism
5. Create monitoring dashboard in management panel
6. Add CLI commands for device management
7. Write comprehensive tests
8. Create agent installer script for edge devices
