# Feature 13: Green Scheduling

## Overview
Schedule non-urgent workloads (backups, batch jobs, maintenance) to run when grid carbon intensity is lowest. Extension of cron system with carbon-awareness.

## Capabilities
- Carbon-aware cron: schedule jobs based on carbon forecast
- Grid carbon intensity API integration (WattTime, ElectricityMap)
- Job deferral when carbon is high
- Automatic scheduling for lowest-carbon windows
- Configurable urgency tiers (low, medium, high, critical)
- Previous schedule vs. green schedule comparison
- Carbon savings report per job
- Manual override for urgent jobs
- Integration with existing cron/scheduler system

## Scheduling Algorithm

```
1. Fetch carbon intensity forecast for next 48 hours
2. For each pending job:
   a. Determine urgency tier
   b. Find optimal time window:
      - Urgent: next available slot regardless of carbon
      - Normal: within 6 hours, prefer lowest carbon
      - Low: schedule in lowest carbon period of next 24h
      - Background: defer to weekend / lowest carbon period
   c. Check resource availability at selected time
   d. Schedule job
3. Re-evaluate every 30 minutes or on forecast update
```

## Carbon Intensity Sources

| Source | Regions | Update Frequency | Cost |
|--------|---------|-----------------|------|
| WattTime | US, EU, UK, AU | 5 minutes | Free tier available |
| ElectricityMap | Global (100+) | Real-time | API key required |
| CarbonIntensity API | UK only | 30 minutes | Free |
| National Grid ESO | UK | 30 minutes | Free |

## Job Configuration

```python
@dataclass
class GreenJobConfig:
    name: str
    command: str
    urgency: str  # "critical", "high", "normal", "low", "background"
    max_delay_hours: int  # Maximum delay before forced execution
    carbon_threshold: Optional[float]  # gCO2/kWh, run only below this
    preferred_hours: Optional[tuple[int, int]]  # e.g., (8, 18) for business hours
    allowed_days: Optional[list[int]]  # 0=Mon, 6=Sun
    notify_on_deferral: bool = True
    notify_on_execution: bool = False
```

## Carbon Savings Report

```
Green Scheduling Savings Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Period: May 1-31, 2026
                            
Job                | Original | Green    | CO2 Saved
━━━━━━━━━━━━━━━━━━┼━━━━━━━━━━┼━━━━━━━━━━┼━━━━━━━━━━
nightly_backup     | 1.2 kWh  | 0.8 kWh  | 0.4 kWh (33%)
data_analytics     | 2.5 kWh  | 1.5 kWh  | 1.0 kWh (40%)
model_training     | 8.0 kWh  | 3.2 kWh  | 4.8 kWh (60%)
report_generation  | 0.5 kWh  | 0.3 kWh  | 0.2 kWh (40%)
━━━━━━━━━━━━━━━━━━┼━━━━━━━━━━┼━━━━━━━━━━┼━━━━━━━━━━
Total              | 12.2 kWh | 5.8 kWh  | 6.4 kWh (52%)

CO2 Saved: 1.83 kg CO2 (at 285 gCO2/kWh grid avg)
Cost Saved: $0.90 (at $0.14/kWh)
```

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/green_scheduling.py`
- Integration with existing cron_scheduler cog
- CLI commands for green job management
