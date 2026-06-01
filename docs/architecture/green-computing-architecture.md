# Green Computing Architecture

## Overview
The Green Computing architecture provides sustainability monitoring, optimization, and reporting capabilities to reduce the environmental impact of infrastructure operations.

## Components

### 11. Energy Consumption Tracker
- **Purpose**: Monitor and track energy usage across all infrastructure
- **Key Features**: Real-time power readings, source breakdown, efficiency ratings, threshold alerts
- **Backend**: `services/integration-service/src/energy_consumption_tracker.py`
- **Sources**: Grid, Solar, Wind, Battery

### 12. Carbon Footprint Dashboard
- **Purpose**: Visualize carbon emissions from infrastructure operations
- **Key Features**: CO₂ emission tracking, carbon intensity monitoring, trend analysis
- **Frontend**: `services/management-panel/src/pages/GreenComputing/CarbonDashboard.tsx`
- **Metrics**: Scope 1, 2, and 3 emissions

### 13. Green Scheduling
- **Purpose**: Schedule compute jobs during low-carbon periods
- **Key Features**: Carbon-aware scheduling, best-window optimization, forecast integration
- **Backend**: `services/orchestrator-agent/cogs/green_scheduling.py`
- **Integration**: Carbon intensity APIs, weather-based renewable forecasts

### 14. Idle Resource Reclamation
- **Purpose**: Identify and reclaim underutilized infrastructure resources
- **Key Features**: Idle detection, automated reclamation, savings projection, policy engine
- **Backend**: `services/orchestrator-agent/cogs/idle_resource_reclamation.py`
- **Resource Types**: Compute, Memory, Storage, GPU, Network

### 15. Efficiency Scorecards
- **Purpose**: Score and rank infrastructure efficiency across multiple dimensions
- **Key Features**: PUE scoring, cooling efficiency, renewable mix, carbon footprint
- **Frontend**: `services/management-panel/src/pages/GreenComputing/EfficiencyScorecards.tsx`
- **Scoring**: 0-100 per category, weighted overall score

### 16. Auto Shutdown Policies
- **Purpose**: Automatically shut down or hibernate idle resources
- **Key Features**: Time-based schedules, idle detection, policy simulation, compliance tracking
- **Backend**: `services/orchestrator-agent/cogs/auto_shutdown_policies.py`
- **Actions**: Shutdown, Hibernate, Sleep, Stop

### 17. Hardware Lifecycle Tracker
- **Purpose**: Track hardware assets through their lifecycle
- **Key Features**: Asset registration, maintenance records, EOL forecasting, warranty tracking
- **Backend**: `services/integration-service/src/hardware_lifecycle_tracker.py`
- **Types**: Server, Switch, Router, Storage, GPU, Network

### 18. PUE/DCIM Integration
- **Purpose**: Monitor Power Usage Effectiveness and data center infrastructure
- **Key Features**: PUE tracking, facility management, cooling unit monitoring, PDU management
- **Backend**: `services/integration-service/src/pue_dcim_integration.py`
- **Optimization**: Cooling efficiency, power distribution, airflow management

### 19. Sustainable Provider Ranking
- **Purpose**: Rank cloud and infrastructure providers by sustainability metrics
- **Key Features**: Multi-dimensional scoring, certification tracking, badge system
- **Frontend**: `services/management-panel/src/pages/GreenComputing/SustainableProviderRanking.tsx`
- **Dimensions**: Sustainability, Efficiency, Transparency, Innovation

### 20. CO₂ Offset Integration
- **Purpose**: Purchase and manage carbon offsets to achieve neutrality
- **Key Features**: Offset purchasing, project registration, portfolio management, retirement
- **Backend**: `services/integration-service/src/co2_offset_integration.py`
- **Standards**: VCS, Gold Standard, CAR, CDM

## Data Flow
```
Energy Meters → Energy Tracker → Carbon Dashboard → Offset Integration
     ↓                                                    ↓
Green Scheduling ← Carbon Forecasts            Sustainable Rankings
     ↓                                                    ↓
Idle Reclamation → Auto Shutdown → Efficiency Scorecards
     ↓
Hardware Lifecycle → PUE/DCIM → Optimization Recommendations
```

## Key Metrics
- **PUE (Power Usage Effectiveness)**: Total facility energy / IT equipment energy
- **CUE (Carbon Usage Effectiveness)**: Total CO₂ emissions / IT equipment energy
- **WUE (Water Usage Effectiveness)**: Total water usage / IT equipment energy
- **ERE (Energy Reuse Effectiveness)**: (Total energy - Reused energy) / IT equipment energy

## CO₂ Calculation
```
CO₂ (kg) = Energy (kWh) × Carbon Intensity (kgCO₂/kWh)
```

## Savings Models
- **Idle Resource Reclamation**: Savings = Reclaimed Watts × Hours × Electricity Rate
- **Green Scheduling**: Savings = (Carbon Intensity at peak - Carbon Intensity at off-peak) × kWh
- **Auto Shutdown**: Savings = Hours shutdown × Average Power Draw × Electricity Rate

## API Endpoints
- `GET /api/v1/green/metrics` - All green metrics
- `GET /api/v1/green/energy/{device_id}` - Device energy data
- `POST /api/v1/green/offsets` - Purchase offsets
- `GET /api/v1/green/carbon` - Carbon footprint data
- `GET /api/v1/green/ranking` - Provider rankings
