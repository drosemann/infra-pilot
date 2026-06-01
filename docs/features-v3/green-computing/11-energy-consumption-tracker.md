# Feature 11: Energy Consumption Tracker

## Overview
Measure per-container energy usage via RAPL (Running Average Power Limit), Intel PCM, or estimated from CPU/RAM/disk utilization. Provide kWh breakdown per server, per user, per container.

## Capabilities
- RAPL-based power measurement for Intel/AMD CPUs
- Intel PCM (Performance Counter Monitor) integration
- Estimated power from CPU/RAM/disk utilization (when RAPL unavailable)
- Per-container energy attribution
- Per-server and per-user energy aggregation
- Real-time and historical energy data
- Energy cost calculation based on local electricity rates
- Export to Prometheus for Grafana dashboards
- API for third-party integration

## Measurement Methods

| Method | Accuracy | Requirements | Coverage |
|--------|----------|-------------|----------|
| RAPL | High (±5%) | Intel Sandy Bridge+, AMD Zen+ | CPU package + DRAM |
| Intel PCM | High (±8%) | Intel specific | CPU, uncore, memory |
| Estimated | Medium (±20%) | CPU/RAM/disk metrics | Any server |
| BMC/IPMI | High (±3%) | Server BMC | Whole server |

## Per-Container Attribution

Energy is attributed to containers using cgroup statistics:
- CPU usage (user + system time) → proportional to package power
- Memory usage → proportional to DRAM power  
- Disk I/O → proportional to storage power (estimated)

Formula:
```
container_energy_joules = 
    (container_cpu_time / total_cpu_time) * cpu_package_energy +
    (container_memory_bytes / total_memory_bytes) * dram_energy +
    container_disk_energy_estimate
```

## Data Model

```python
@dataclass
class EnergyMeasurement:
    server_id: str
    container_id: Optional[str]
    user_id: Optional[str]
    timestamp: datetime
    measurement_method: str  # "rapl", "pcm", "estimated"
    
    # Energy in joules (since last measurement)
    cpu_energy_joules: float
    dram_energy_joules: float
    disk_energy_joules: float
    total_energy_joules: float
    
    # Power in watts
    cpu_power_watts: float
    dram_power_watts: float
    disk_power_watts: float
    total_power_watts: float
    
    # Cost (computed)
    energy_cost_kwh: float  # total_energy_joules / 3_600_000 * rate
    co2_grams: float  # energy_kwh * grid_intensity
    
    # Utilization
    cpu_utilization_pct: float
    memory_utilization_pct: float
    disk_utilization_pct: float
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/energy/current | Current energy usage snapshot |
| GET | /api/v1/energy/history | Historical energy data |
| GET | /api/v1/energy/servers/{id} | Per-server breakdown |
| GET | /api/v1/energy/containers/{id} | Per-container breakdown |
| GET | /api/v1/energy/users/{id} | Per-user aggregation |
| GET | /api/v1/energy/cost-summary | Cost summary (daily/weekly/monthly) |
| POST | /api/v1/energy/rate | Set electricity rate |

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/energy_consumption_tracker.py`
- Test with RAPL simulation and cgroup mocks
- Prometheus metrics export
