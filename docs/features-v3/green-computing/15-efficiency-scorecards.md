# Feature 15: Efficiency Scorecards

## Overview
Per-server efficiency rating based on utilization vs. capacity. Recommendations for consolidation or rightsizing, gamified as a "Green Score".

## Capabilities
- Per-server efficiency scoring (0-100)
- Utilization analysis (CPU, RAM, disk, network)
- Rightsizing recommendations (over-provisioned vs. under-provisioned)
- Consolidation suggestions (merge low-utilization servers)
- Green Score gamification with badges
- Historical efficiency trends
- Server fleet comparison
- Recommendations with estimated savings
- Export reports for management

## Efficiency Score Calculation

```
Efficiency Score = weighted_avg of:
  CPU Efficiency:     min(avg_utilization / target_utilization, 1.0) * 100
  Memory Efficiency:  min(avg_utilization / target_utilization, 1.0) * 100
  Disk Efficiency:    min(avg_utilization / target_utilization, 1.0) * 100
  Network Efficiency: min(avg_utilization / target_utilization, 1.0) * 100

Target utilization: CPU=70%, RAM=75%, Disk=80%, Network=50%
Weights: CPU=40%, RAM=30%, Disk=20%, Network=10%

Penalties:
- Over-provisioned (>20% headroom): -10 points
- Under-provisioned (<10% headroom): -5 points
- Idle (<5% utilization for >12h/day): -15 points
- Power usage effectiveness impact: -5 to +5
```

## Green Score Badges

| Score Range | Badge | Color |
|-------------|-------|-------|
| 90-100 | 🌟 Energy Star | Gold |
| 75-89 | ✅ Efficient | Green |
| 50-74 | ⚠️ Average | Yellow |
| 25-49 | 🔧 Needs Optimization | Orange |
| 0-24 | 🚨 Inefficient | Red |

## Recommendations

```python
class EfficiencyRecommendation:
    def generate(self, server: ServerMetrics) -> list[Recommendation]:
        recs = []
        
        # CPU over-provisioned
        if server.cpu_avg_utilization < 20:
            savings = self.estimate_savings("cpu", server.cpu_cores, 
                                            server.cpu_cores // 2)
            recs.append(Recommendation(
                type="rightsize_cpu",
                title="CPU is over-provisioned",
                detail=f"Avg CPU utilization is {server.cpu_avg_utilization:.0f}%."
                       f" Consider reducing from {server.cpu_cores} to "
                       f"{max(1, server.cpu_cores // 2)} cores.",
                savings=savings,
                effort="medium",
                impact="high"
            ))
        
        # Consolidation opportunity
        if server.efficiency_score < 30:
            recs.append(Recommendation(
                type="consolidate",
                title="Candidate for consolidation",
                detail="This server has very low efficiency. Consider "
                       "migrating workloads to another server and "
                       "decommissioning.",
                savings=self.estimate_consolidation_savings(server),
                effort="high",
                impact="very_high"
            ))
        
        return recs
```

## Implementation
- Primary service: Management Panel (React)
- Module: `services/management-panel/src/pages/GreenComputing/EfficiencyScorecards.tsx`
- Data from integration service resource tracker
- Charts for efficiency trends
