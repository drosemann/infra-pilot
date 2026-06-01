# Feature 30: 5G/LTE Integration

## Overview
Manage cellular modems, APN configuration, signal monitoring, data usage caps, and automatic fallback routing when primary links fail.

## Components

### Integration Service: `networking/cellular_manager.py`
- `CellularManager` - Core cellular management
  - Modem discovery and management (qmi, mbim, serial)
  - APN configuration management
  - Signal quality monitoring (RSRP, RSRQ, SINR, RSSI)
  - Data usage tracking and capping
  - SMS send/receive
  - Automatic failover routing
  - Carrier aggregation status
  - Band configuration

### Orchestrator Agent: `cogs/cellular_manager.py`
- Discord commands:
  - `/cellular status` - Modem status
  - `/cellular signal` - Signal strength info
  - `/cellular apn set` - Set APN configuration
  - `/cellular usage` - Data usage
  - `/cellular sms` - Send SMS
  - `/cellular failover` - Failover settings

### Management Panel: `pages/networking/CellularPage.tsx`
- Modem dashboard with signal quality
- APN configuration
- Data usage graphs
- SMS interface
- Failover routing configuration
- Carrier/band information

### CLI Commands
- `ipilot cellular status`
- `ipilot cellular signal`
- `ipilot cellular apn list`
- `ipilot cellular usage --period current`

## API Endpoints
- `GET /api/networking/cellular/modems` - List modems
- `GET /api/networking/cellular/modems/{id}` - Modem details
- `GET /api/networking/cellular/modems/{id}/signal` - Signal info
- `GET /api/networking/cellular/modems/{id}/usage` - Data usage
- `POST /api/networking/cellular/modems/{id}/apn` - Set APN
- `GET /api/networking/cellular/modems/{id}/apn` - Get APN config
- `POST /api/networking/cellular/modems/{id}/sms` - Send SMS
- `GET /api/networking/cellular/modems/{id}/sms` - List SMS
- `POST /api/networking/cellular/modems/{id}/reset` - Reset modem
- `GET /api/networking/cellular/failover` - Failover status
- `PUT /api/networking/cellular/failover` - Update failover config

## Data Models

### CellularModem
- id, name, manufacturer, model, firmware_version
- interface_name (wwan0, eth2, etc.), protocol (qmi/mbim/serial)
- imei, imsi, iccid, operator_name
- connection_status (connected/disconnected/error)
- rssi_dbm, rsrp_dbm, rsrq_db, sinr_db
- cell_id, tac, band, carrier_aggregation
- ipv4_address, ipv6_address
- data_used_gb, data_cap_gb
- temperature_celsius

### APNConfig
- id, modem_id, apn, username, password (encrypted)
- authentication (pap/chap/none)
- ip_type (ipv4/ipv6/ipv4v6)
- roaming_enabled, is_primary

### FailoverConfig
- id, primary_uplink_id, cellular_uplink_id
- failover_threshold_latency_ms
- failover_threshold_loss_pct
- auto_failback, failback_after_seconds
- data_saver_mode (low/medium/high/off)

## Implementation Details
- ModemManager (mmcli) for modem control
- qmicli for Qualcomm modems
- mbimcli for Microsoft MBIM modems
- AT command interface for serial modems
- Signal metrics polling every 10 seconds
- Data usage tracking via kernel counters
- Failover via policy routing and NAT
- SMS via AT+CMGS or mbim/qmi SMS interfaces
- Carrier aggregation via modem-specific AT commands
- 5G NR-specific metrics (SS-RSRP, SS-SINR)

## Testing
- Modem discovery and enumeration
- Signal quality metric collection
- APN configuration push
- SMS send/receive
- Data usage tracking accuracy
- Failover trigger and recovery
- Connection state machine
