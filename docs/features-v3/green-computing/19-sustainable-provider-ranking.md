# Feature 19: Sustainable Provider Ranking

## Overview
Rank cloud providers by carbon intensity, water usage, renewable energy percentage, and other sustainability metrics. Guide green provider selection at provisioning time.

## Capabilities
- Provider sustainability scoring (0-100)
- Carbon intensity ranking per region
- Renewable energy percentage per provider
- Water usage efficiency (WUE) data
- Electronic waste recycling programs
- Green certifications (ISO 14001, LEED, Energy Star)
- Provisioning-time recommendation
- Provider comparison tool
- Historical sustainability trends
- Custom weighting of sustainability factors

## Sustainability Data Sources

| Provider | Data Source | Metrics | Update Frequency |
|----------|-------------|---------|-----------------|
| AWS | Sustainability Pillar, Carbon Footprint | Carbon intensity, renewable %, WUE | Quarterly |
| Azure | Sustainability Dashboard, Emissions API | Carbon intensity, renewable %, water | Monthly |
| GCP | Carbon Footprint, Region PUE | Carbon intensity, PUE, water | Monthly |
| Hetzner | ESG Report, Website | Carbon intensity, renewable % | Annual |
| DigitalOcean | Sustainability Report | Carbon intensity, renewable % | Annual |
| OVHcloud | ESG Report | Carbon intensity, PUE, recycling | Annual |
| Scaleway | Sustainability Page | Carbon intensity, PUE | Annual |

## Scoring Model

```python
SUSTAINABILITY_WEIGHTS = {
    "carbon_intensity": 0.35,    # gCO2/kWh
    "renewable_energy_pct": 0.25,  # 0-100
    "water_usage_efficiency": 0.15,  # L/kWh
    "pue": 0.10,  # Power Usage Effectiveness
    "e_waste_recycling": 0.05,  # 0-100
    "green_certifications": 0.05,  # Count
    "transparency_score": 0.05,  # 0-100
}

def calculate_provider_score(provider_data: ProviderSustainability) -> float:
    scores = {}
    
    # Carbon intensity (lower is better)
    ci = provider_data.carbon_intensity_g_per_kwh
    scores["carbon_intensity"] = max(0, 100 - (ci / 10))
    
    # Renewable energy (higher is better)
    scores["renewable_energy_pct"] = provider_data.renewable_energy_pct
    
    # Water usage (lower is better)
    wue = provider_data.water_usage_l_per_kwh
    scores["water_usage_efficiency"] = max(0, 100 - (wue * 20))
    
    # PUE (lower is better)
    pue = provider_data.pue
    scores["pue"] = max(0, 100 - ((pue - 1.0) * 100))
    
    # Composite score
    total = sum(
        scores[key] * SUSTAINABILITY_WEIGHTS[key]
        for key in SUSTAINABILITY_WEIGHTS
    )
    
    return round(total, 1)
```

## Provider Comparison View

```tsx
<ProviderComparisonTable>
  <ProviderRow 
    name="Google Cloud" 
    score={92} 
    carbonIntensity={48} 
    renewablePct={100}
    wue={0.5}
    pue={1.10}
    certifications={["ISO 14001", "LEED Gold"]}
  />
  <ProviderRow 
    name="Azure" 
    score={78} 
    carbonIntensity={145} 
    renewablePct={65}
    wue={1.2}
    pue={1.18}
    certifications={["ISO 14001"]}
  />
  <ProviderRow 
    name="AWS" 
    score={74} 
    carbonIntensity={162} 
    renewablePct={55}
    wue={1.5}
    pue={1.20}
    certifications={["ISO 14001"]}
  />
</ProviderComparisonTable>
```

## Implementation
- Primary service: Management Panel (React)
- Module: `services/management-panel/src/pages/GreenComputing/ProviderRanking.tsx`
- Backend data: Integration Service
- Integration with provisioning workflow
