"""Edge & IoT and Green Computing API Reference."""

# Edge & IoT API Reference

## Base URL
`/api/v1/edge`

## Authentication
All API requests require a valid API key in the `Authorization` header:
```
Authorization: Bearer <api_key>
```

## Endpoints

### Devices

#### List All Edge Devices
```
GET /api/v1/edge/devices
```
Returns a list of all registered edge devices.

**Response:**
```json
{
  "devices": [
    {
      "device_id": "dev-001",
      "name": "Temp Sensor A1",
      "status": "online",
      "type": "sensor",
      "firmware": "2.1.3",
      "last_seen": "2026-05-29T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### Get Edge Device
```
GET /api/v1/edge/devices/{device_id}
```

#### Register Edge Device
```
POST /api/v1/edge/devices
```
**Body:**
```json
{
  "device_id": "dev-001",
  "name": "Temp Sensor A1",
  "device_type": "sensor",
  "location": "DC-1-Rack-A3"
}
```

#### Delete Edge Device
```
DELETE /api/v1/edge/devices/{device_id}
```

### IoT Pipelines

#### List Pipelines
```
GET /api/v1/iot/pipelines
```

#### Create Pipeline
```
POST /api/v1/iot/pipelines
```

#### Ingest IoT Data
```
POST /api/v1/iot/ingest
```
**Body:**
```json
{
  "device_id": "dev-001",
  "payload": {
    "temperature": 25.0,
    "humidity": 55
  }
}
```

### Mesh Network

#### List Mesh Nodes
```
GET /api/v1/mesh/nodes
```

#### Register Mesh Node
```
POST /api/v1/mesh/nodes
```

#### Get Mesh Topology
```
GET /api/v1/mesh/topology
```

#### Get Node Routes
```
GET /api/v1/mesh/routes/{node_id}
```

### LoRaWAN

#### List Gateways
```
GET /api/v1/lorawan/gateways
```

#### Register Gateway
```
POST /api/v1/lorawan/gateways
```

#### List Devices
```
GET /api/v1/lorawan/devices
```

#### Register Device
```
POST /api/v1/lorawan/devices
```

### IoT Provisioning

#### List Provisioned Devices
```
GET /api/v1/iot/provisioning/devices
```

#### Claim Device
```
POST /api/v1/iot/provisioning/claim
```

#### Enroll Device
```
POST /api/v1/iot/provisioning/enroll
```

# Green Computing API Reference

## Base URL
`/api/v1/green`

## Endpoints

### Energy

#### Get Device Energy Data
```
GET /api/v1/green/energy/{device_id}
```

#### Get All Energy Metrics
```
GET /api/v1/green/energy/metrics
```

#### Record Energy Reading
```
POST /api/v1/green/energy/reading
```

### Hardware Lifecycle

#### List Hardware Assets
```
GET /api/v1/green/hardware/assets
```

#### Register Hardware Asset
```
POST /api/v1/green/hardware/assets
```

#### Get Hardware Asset
```
GET /api/v1/green/hardware/assets/{asset_id}
```

#### Add Maintenance Record
```
POST /api/v1/green/hardware/maintenance
```

### PUE/DCIM

#### List Facilities
```
GET /api/v1/green/pue/facilities
```

#### Get Facility PUE Metrics
```
GET /api/v1/green/pue/metrics/{facility_id}
```

#### Record PUE Reading
```
POST /api/v1/green/pue/reading
```

### Carbon Offsets

#### List Offsets
```
GET /api/v1/green/offsets
```

#### Purchase Offset
```
POST /api/v1/green/offsets
```

#### Get Offset Summary
```
GET /api/v1/green/offsets/summary
```

#### Get Carbon Neutrality Status
```
GET /api/v1/green/carbon/status
```

### Scheduling

#### List Schedule Jobs
```
GET /api/v1/green/schedule/jobs
```

#### Create Schedule Job
```
POST /api/v1/green/schedule/jobs
```

#### Optimize Schedule
```
GET /api/v1/green/schedule/optimize/{device_id}
```

### Comprehensive Metrics

#### All Green Metrics
```
GET /api/v1/green/metrics
```

#### All Edge Metrics
```
GET /api/v1/edge/metrics
```

# CLI Reference

## Edge Device Commands

```bash
# List edge devices
ipilot edge device list

# Get device details
ipilot edge device get <device_id>

# Register a new device
ipilot edge device register --name "Device Name" --type sensor

# Delete a device
ipilot edge device delete <device_id>
```

## IoT Pipeline Commands

```bash
# List pipelines
ipilot iot pipeline list

# Create pipeline
ipilot iot pipeline create --name "Pipeline Name" --type mqtt
```

## Mesh Network Commands

```bash
# List mesh nodes
ipilot mesh node list

# Get topology
ipilot mesh topology

# Show routing table
ipilot mesh routes <node_id>
```

## LoRaWAN Commands

```bash
# List gateways
ipilot lorawan gateway list

# Register gateway
ipilot lorawan gateway register --name "GW-1" --region us915

# List devices
ipilot lorawan device list
```

## Energy Commands

```bash
# Get device energy data
ipilot green energy get <device_id>

# Record energy reading
ipilot green energy record --device-id <id> --watts 150

# Show energy metrics
ipilot green energy metrics
```

## Carbon Commands

```bash
# Get carbon footprint
ipilot green carbon footprint <device_id>

# View carbon dashboard
ipilot green carbon dashboard

# Purchase carbon offset
ipilot green offset purchase --tonnes 10 --provider provider-1
```

## Hardware Lifecycle Commands

```bash
# List hardware assets
ipilot green hardware list

# Register hardware asset
ipilot green hardware register --name "Server-1" --type server

# Get asset details
ipilot green hardware get <asset_id>
```

## PUE Commands

```bash
# List facilities
ipilot green pue list

# Get facility metrics
ipilot green pue metrics <facility_id>

# Record PUE reading
ipilot green pue record --facility <id> --total 500 --it 400
```

## Scheduling Commands

```bash
# List scheduled jobs
ipilot green schedule list

# Optimize schedule for device
ipilot green schedule optimize <device_id>
```

## Auto Shutdown Commands

```bash
# List shutdown policies
ipilot green shutdown list

# Create shutdown policy
ipilot green shutdown create --name "Night Shutdown" --action hibernate

# Delete policy
ipilot green shutdown delete <policy_id>
```

## Provider Ranking Commands

```bash
# View provider rankings
ipilot green provider list
```

## Offset Commands

```bash
# List offset projects
ipilot green offset project list

# Get offset summary
ipilot green offset summary
```
