# Edge & IoT Architecture

## Overview
The Edge & IoT architecture enables distributed computing at the network edge, connecting IoT devices to cloud infrastructure through low-latency gateways and protocols.

## Components

### 1. Edge Device Manager
- **Purpose**: Register, monitor, and manage edge computing nodes
- **Key Features**: Device enrollment, health monitoring, firmware updates, remote access
- **Backend**: `services/orchestrator-agent/cogs/edge_device_manager.py`
- **CLI**: `ipilot edge device` commands

### 2. IoT Data Pipeline
- **Purpose**: Ingest, process, and route IoT telemetry data
- **Key Features**: MQTT ingestion, protocol translation, data enrichment, stream routing
- **Backend**: `services/integration-service/src/iot_data_pipeline.py`
- **Integration**: Kafka, MQTT broker, time-series databases

### 3. Edge Function Runtime
- **Purpose**: Execute lightweight functions at edge nodes
- **Key Features**: Function deployment, version management, sandboxed execution, scaling
- **Backend**: `services/orchestrator-agent/cogs/edge_function_runtime.py`
- **Supported Runtimes**: WASM, Lua, JavaScript, Python

### 4. Mesh Network Manager
- **Purpose**: Manage peer-to-peer mesh networks for edge devices
- **Key Features**: Node registration, link management, routing optimization, topology visualization
- **Backend**: `services/integration-service/src/mesh_network_manager.py`
- **Protocols**: OSPF, BATMAN, HWMP

### 5. Edge ML Inference
- **Purpose**: Deploy and run ML models at edge nodes
- **Key Features**: Model deployment, quantized inference, hardware acceleration, batch jobs
- **Backend**: `services/orchestrator-agent/cogs/edge_ml_inference.py`
- **Formats**: TFLite, ONNX, CoreML, OpenVINO

### 6. IoT Device Provisioning
- **Purpose**: Secure enrollment of IoT devices with certificates
- **Key Features**: Claim codes, X.509 certificates, device shadows, profiles
- **Backend**: `services/orchestrator-agent/cogs/iot_device_provisioning.py`
- **Security**: TPM, ATECC608A secure elements

### 7. LoRaWAN Gateway Manager
- **Purpose**: Manage LoRaWAN gateways and end-devices
- **Key Features**: Gateway registration, device management, data rate optimization, coverage mapping
- **Backend**: `services/integration-service/src/lorawan_gateway_manager.py`
- **Frequency Plans**: US915, EU868, AS923, AU915

### 8. Edge CDN
- **Purpose**: Content caching and delivery at edge locations
- **Key Features**: Cache policies, origin shields, content pre-warming, cache invalidation
- **Backend**: `services/orchestrator-agent/cogs/edge_cdn.py`
- **Strategies**: LRU, LFU, TTL-based eviction

### 9. Digital Twin Viewer
- **Purpose**: Real-time digital representations of physical edge devices
- **Key Features**: Device state mirroring, telemetry visualization, historical playback
- **Frontend**: `services/management-panel/src/pages/EdgeIoT/DigitalTwinViewer.tsx`
- **Mobile**: `mobile/app/screens/EdgeIoT/EdgeDevicesScreen.tsx`

### 10. Edge Backup & Restore
- **Purpose**: Backup and recovery for edge node configurations and data
- **Key Features**: Full/incremental backups, scheduled backups, point-in-time restore
- **Backend**: `services/orchestrator-agent/cogs/edge_backup_restore.py`
- **Targets**: S3, NFS, local storage

## Data Flow
```
IoT Devices → LoRaWAN Gateways → IoT Data Pipeline → Edge Functions → ML Inference → Cloud
     ↓                                                                ↓
Mesh Network ← → Edge Device Manager                     Digital Twin Viewer
     ↓                                                                ↓
Edge Backup & Restore ← → Edge CDN ← → End Users
```

## API Endpoints
All Edge & IoT features expose REST APIs via:
- `GET /api/v1/edge/{resource}` - List resources
- `POST /api/v1/edge/{resource}` - Create resource
- `GET /api/v1/edge/{resource}/{id}` - Get resource details
- `PUT /api/v1/edge/{resource}/{id}` - Update resource
- `DELETE /api/v1/edge/{resource}/{id}` - Delete resource

## Security Model
- Device authentication via X.509 certificates
- Claim codes for zero-touch provisioning
- TLS 1.3 for all communication
- Secure element integration for hardware root of trust
- Role-based access control (RBAC) for management
