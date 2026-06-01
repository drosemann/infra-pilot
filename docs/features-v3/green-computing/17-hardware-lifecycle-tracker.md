# Feature 17: Hardware Lifecycle Tracker

## Overview
Track server hardware age, warranty status, and e-waste disposition. Alert when hardware exceeds recommended lifespan. Integrate with recycling partners.

## Capabilities
- Hardware inventory management (server, storage, network, GPU)
- Warranty tracking with expiry alerts
- Hardware age tracking with lifespan estimates
- E-waste disposition tracking and reporting
- Recycling partner integration
- Maintenance schedule tracking
- Component replacement history
- Hardware cost tracking (purchase, maintenance, power)
- Depreciation calculation
- End-of-life (EOL) alerts from manufacturer data
- Compliance with WEEE directive

## Hardware Data Model

```python
@dataclass
class HardwareAsset:
    asset_id: str
    asset_type: HardwareType  # server, storage, network, gpu, ups, etc.
    manufacturer: str
    model: str
    serial_number: str
    purchase_date: date
    purchase_price: float
    warranty_months: int
    warranty_expiry: date
    expected_lifespan_months: int
    end_of_life_date: Optional[date]  # manufacturer EOL
    
    # Location
    location: str  # datacenter, rack, U position
    owner: str  # team or project
    
    # Status
    status: AssetStatus  # active, maintenance, decommissioned, disposed
    decommission_date: Optional[date]
    disposal_method: Optional[str]  # recycled, resold, scrapped
    recycling_partner: Optional[str]
    
    # Maintenance
    last_maintenance_date: Optional[date]
    next_maintenance_date: Optional[date]
    maintenance_interval_days: int = 180
    
    # Financial
    depreciation_method: str = "straight_line"
    salvage_value: float = 0.0
    current_value: float  # computed
```

## Lifecycle Stages

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Procure  │───▶│  Active  │───▶│  End of  │───▶│Decomm-   │───▶│ Disposal │
│          │    │          │    │  Life    │    │ission    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                      │               │               │
                      ▼               ▼               ▼
                Scheduled         Replacement     Recycling
                Maintenance       Alert           Certificate
```

## Alert Triggers

| Event | Trigger | Alert Method |
|-------|---------|-------------|
| Warranty Expiry | 30 days before | Email, Dashboard |
| EOL Date | 90 days before | Email, Dashboard |
| Lifespan Exceeded | > expected_lifespan | Urgent notification |
| Maintenance Due | 7 days before | Email |
| Overheating | Temperature > threshold | Alert |
| Disk Failure Predicted | SMART attributes | Critical alert |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/hardware/assets | List all assets |
| POST | /api/v1/hardware/assets | Add new asset |
| GET | /api/v1/hardware/assets/{id} | Get asset details |
| PUT | /api/v1/hardware/assets/{id} | Update asset |
| DELETE | /api/v1/hardware/assets/{id} | Remove asset |
| GET | /api/v1/hardware/warranty-expiring | Warranty alerts |
| GET | /api/v1/hardware/eol | End-of-life alerts |
| GET | /api/v1/hardware/report | Lifecycle report |

## Implementation
- Primary service: Integration Service
- Module: `services/integration-service/src/hardware_lifecycle_tracker.py`
- CLI commands for asset management
- Management panel for hardware dashboard
