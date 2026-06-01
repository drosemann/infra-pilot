# Feature 7: LoRaWAN Gateway Management

## Overview
Manage LoRaWAN gateways and concentrators. Configure packet forwarders, plan channels, integrate with join servers, and monitor gateway health.

## Capabilities
- Gateway registration and configuration
- Packet forwarder management (Semtech UDP, BasicStation)
- Channel planning and frequency configuration
- Join Server integration (ChirpStack, TTN, AWS IoT Core for LoRaWAN)
- Gateway health monitoring (GPS, temperature, packet statistics)
- Firmware update management
- Spectrum analysis and interference detection
- Downlink queue management
- Gateway group management for load balancing

## Gateway Configuration

```json
{
  "gateway_id": "gw-008c",
  "name": "factory-floor-gw-1",
  "model": "RAK7258",
  "concentrator": "SX1302",
  "frequency_plan": "EU868",
  "antenna": {
    "type": "omnidirectional",
    "gain_dbi": 5.5,
    "height_meters": 15.0
  },
  "location": {
    "latitude": 52.5200,
    "longitude": 13.4050,
    "altitude_meters": 34.0
  },
  "packet_forwarder": {
    "type": "semtech_udp",
    "server_address": "eu1.cloud.thethings.network",
    "server_port_up": 1700,
    "server_port_down": 1700,
    "served_gateway_id": "eui-a84041ff...",
    "served_gateway_key": "NNSXS..."
  },
  "channels": {
    "enabled": [0, 1, 2, 3, 4, 5, 6, 7],
    "custom": [],
    "lbt_enabled": false
  },
  "status": "active"
}
```

## Packet Forwarder Types

| Type | Protocol | Use Case |
|------|----------|----------|
| Semtech UDP | UDP JSON | Legacy gateways, simple setup |
| BasicStation | WebSocket LNS | TTN v3+, secure, bidirectional |
| ChirpStack Gateway Bridge | MQTT | ChirpStack ecosystem |
| AWS IoT Core for LoRaWAN | MQTT | AWS integration |

## Channel Planning

The channel planner recommends optimal frequency channels based on:
- Regulatory region (EU868, US915, AU915, AS923, etc.)
- Gateways in range (co-channel interference avoidance)
- Device types (Class A/B/C requirements)
- Duty cycle restrictions
- LBT (Listen Before Talk) requirements

## Monitoring Metrics

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| RSSI (avg) | Gateway | < -120 dBm |
| SNR (avg) | Gateway | < -10 dB |
| Packets Forwarded | Counter | 0 for 5 min |
| GPS Fix | GPS module | Lost for > 10 min |
| Temperature | Sensor | > 70°C |
| Gateway Uptime | System | < 90% in 24h |

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/lorawan_gateway_manager.py`
- Test with Semtech UDP and BasicStation protocol mocks
- CLI commands for gateway management
