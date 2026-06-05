# Feature 12: Carbon Footprint Dashboard

## Overview
Display CO2 equivalent emissions based on energy data and regional grid carbon intensity API. Show historical trends and offset suggestions.

## Capabilities
- Real-time CO2 emission display
- Historical trends (daily, weekly, monthly, yearly)
- Per-server, per-user, per-container carbon breakdown
- Grid carbon intensity integration (WattTime, ElectricityMap, CarbonIntensity API)
- Regional carbon intensity data with auto-detection
- Avoided emissions vs. on-premises baseline
- Carbon offset suggestions with cost estimates
- Export carbon reports (PDF, CSV)
- Comparison with industry benchmarks
- CO2 saved by green scheduling and autoshutdown

## Carbon Calculation

```
CO2_grams = energy_kWh × grid_carbon_intensity_g_per_kWh

Where:
- energy_kWh is measured or estimated by energy tracker
- grid_carbon_intensity varies by:
  - Geographic region (auto-detected from server location)
  - Time of day (renewable availability)
  - Grid mix (coal, gas, nuclear, renewables)
```

## Dashboard Widgets

### Overview Widget
```tsx
<CarbonOverviewCard>
  <Metric label="Total CO2 (This Month)" value="1,234 kg" trend="down 12%" />
  <Metric label="Per Server Avg" value="45.2 kg" trend="stable" />
  <Metric label="Grid Intensity" value="285 gCO2/kWh" trend="down 5%" />
  <Metric label="Trees Equivalent" value="57 trees/month" />
</CarbonOverviewCard>
```

### Trend Chart
- Stacked bar chart: CO2 per server per day
- Line overlay: grid carbon intensity
- 30/60/90 day views
- Anomaly highlighting (spikes)

### Comparison Card
```
┌──────────────────────────────────────┐
│  Your Carbon vs. Industry Average    │
│                                      │
│  Your Infrastructure ████████░░ 78% │
│  Industry Avg      ██████████░ 92% │
│  Best in Class     ██████░░░░░ 62% │
│                                      │
│  You save: 14% below industry avg   │
└──────────────────────────────────────┘
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/carbon/current | Current CO2 output |
| GET | /api/v1/carbon/history | Historical CO2 data |
| GET | /api/v1/carbon/servers/{id} | Per-server carbon |
| GET | /api/v1/carbon/intensity | Grid intensity data |
| GET | /api/v1/carbon/benchmarks | Industry benchmarks |
| GET | /api/v1/carbon/report | Generate carbon report |

## Implementation
- Primary service: Management Panel (React)
- Data source: Integration Service energy tracker + carbon intensity API
- Module: `services/management-panel/src/pages/GreenComputing/CarbonDashboard.tsx`
- Charts: recharts or chart.js for trend visualization
