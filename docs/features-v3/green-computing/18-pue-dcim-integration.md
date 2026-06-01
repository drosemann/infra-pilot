# Feature 18: PUE / DCIM Integration

## Overview
Integrate with Data Center Infrastructure Management (DCIM) systems for Power Usage Effectiveness (PUE) data. Combine facility-level metrics with server-level metrics for comprehensive efficiency analysis.

## Capabilities
- DCIM integration (Nlyte, Sunbird DCIM, Device42, openDCIM)
- PUE data collection and monitoring
- Facility power and cooling metrics
- Per-rack power distribution tracking
- Temperature and humidity monitoring
- Cooling system efficiency (CWUE, WUE)
- Combined IT + facility energy analysis
- PUE trend analysis and anomaly detection
- PUE contribution by cooling type, rack, row
- Integration with building management systems (BACnet, Modbus)

## PUE Calculation

```
PUE = Total Facility Energy / IT Equipment Energy

Where:
- Total Facility Energy = IT + Cooling + Power Distribution + Lighting + Other
- IT Equipment Energy = Sum of all server, storage, network equipment power

Tier classification:
- PUE < 1.2: Excellent
- PUE 1.2-1.4: Good
- PUE 1.4-1.6: Average
- PUE 1.6-2.0: Poor
- PUE > 2.0: Very Poor
```

## DCIM Connectors

| DCIM System | Protocol | Features |
|-------------|----------|----------|
| Nlyte | REST API | Asset, power, cooling, PUE |
| Sunbird DCIM | REST API | Power chain, temperature, capacity |
| Device42 | REST API | Asset, power, network, PDU |
| openDCIM | REST API | Power, cooling, PUE, capacity |
| BACnet | BACnet/IP | BMS integration, temperature, humidity |
| Modbus | TCP/RTU | PDU, UPS, temperature sensors |
| SNMP | v2c/v3 | UPS, PDU, environmental sensors |

## Data Collection

```python
class DCIMConnector:
    """Base connector for DCIM integration."""
    
    async def collect_metrics(self) -> DCIMMetrics:
        """Collect facility metrics from DCIM system."""
        return DCIMMetrics(
            timestamp=datetime.utcnow(),
            facility_power_kw=await self._get_facility_power(),
            it_power_kw=await self._get_it_power(),
            cooling_power_kw=await self._get_cooling_power(),
            pue=self._calculate_pue(
                facility_power, it_power
            ),
            temperature_celsius=await self._get_avg_temperature(),
            humidity_pct=await self._get_avg_humidity(),
            cooling_efficiency=await self._get_cooling_efficiency(),
            power_distribution_losses=await self._get_pdu_losses(),
            rack_power_distribution=await self._get_rack_power()
        )
    
    async def _get_rack_power(self) -> dict[str, float]:
        """Get power per rack."""
        racks = {}
        for pdu in await self._get_pdus():
            for outlet in pdu.outlets:
                rack_name = outlet.rack_name
                racks[rack_name] = racks.get(rack_name, 0) + outlet.power_watts
        return racks
```

## Dashboard Integration

```
┌─────────────────────────────────────────────────────┐
│  Data Center Efficiency Overview                    │
│  ─────────────────────────────                       │
│                                                      │
│  PUE: 1.35  (Good)        ┃  IT Power: 245.6 kW     │
│  ─────────────             ┃  ─────────────           │
│  Facility Power: 331.6 kW ┃  Cooling: 62.3 kW       │
│                          ┃  Losses: 23.7 kW         │
│                                                      │
│  ┌──────────────────────────────────────┐           │
│  │  PUE Trend - Last 30 Days           │           │
│  │  ╱╲    ╱╲  ╱╲                       │           │
│  │ ╱  ╲  ╱  ╲╱  ╲___╱╲                │           │
│  │╱    ╲╱              ╲╱╲             │           │
│  └──────────────────────────────────────┘           │
│                                                      │
│  Top Cooling Consumers:                              │
│  │ CRAC-01: 18.2 kW (29%)                           │
│  │ CRAC-02: 15.7 kW (25%)                           │
│  │ CRAH-01: 12.1 kW (19%)                           │
│  │ Chiller:  10.3 kW (17%)                          │
│  │ Pumps:     6.0 kW (10%)                          │
└─────────────────────────────────────────────────────┘
```

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/pue_dcim_integration.py`
- Connectors for major DCIM systems
- Dashboard widgets for management panel
