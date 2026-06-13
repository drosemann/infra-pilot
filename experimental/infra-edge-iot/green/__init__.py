"""Infra green module - helpers for green/sustainable computing features."""

from typing import Any, Optional

CARBON_INTENSITY_MAP = {
    "us-east": {"region": "US-East", "intensity_g_per_kwh": 285, "renewable_pct": 25},
    "us-west": {"region": "US-West", "intensity_g_per_kwh": 180, "renewable_pct": 45},
    "eu-central": {"region": "EU-Central", "intensity_g_per_kwh": 240, "renewable_pct": 40},
    "eu-west": {"region": "EU-West", "intensity_g_per_kwh": 200, "renewable_pct": 55},
    "eu-north": {"region": "EU-North", "intensity_g_per_kwh": 50, "renewable_pct": 90},
    "asia-east": {"region": "Asia-East", "intensity_g_per_kwh": 350, "renewable_pct": 15},
    "asia-south": {"region": "Asia-South", "intensity_g_per_kwh": 450, "renewable_pct": 10},
    "australia": {"region": "Australia", "intensity_g_per_kwh": 380, "renewable_pct": 20},
    "south-america": {"region": "South America", "intensity_g_per_kwh": 150, "renewable_pct": 60},
    "africa": {"region": "Africa", "intensity_g_per_kwh": 320, "renewable_pct": 18},
}

PROVIDER_SUSTAINABILITY_RANKINGS = {
    "google_cloud": {
        "score": 92,
        "carbon_intensity": 48,
        "renewable_pct": 100,
        "wue_l_per_kwh": 0.5,
        "pue": 1.10,
        "certifications": ["ISO 14001", "LEED Gold"],
    },
    "microsoft_azure": {
        "score": 78,
        "carbon_intensity": 145,
        "renewable_pct": 65,
        "wue_l_per_kwh": 1.2,
        "pue": 1.18,
        "certifications": ["ISO 14001"],
    },
    "amazon_aws": {
        "score": 74,
        "carbon_intensity": 162,
        "renewable_pct": 55,
        "wue_l_per_kwh": 1.5,
        "pue": 1.20,
        "certifications": ["ISO 14001"],
    },
    "hetzner": {
        "score": 88,
        "carbon_intensity": 60,
        "renewable_pct": 100,
        "wue_l_per_kwh": 0.8,
        "pue": 1.12,
        "certifications": ["ISO 14001"],
    },
    "digitalocean": {
        "score": 65,
        "carbon_intensity": 200,
        "renewable_pct": 40,
        "wue_l_per_kwh": 1.8,
        "pue": 1.25,
        "certifications": [],
    },
    "ovhcloud": {
        "score": 82,
        "carbon_intensity": 80,
        "renewable_pct": 80,
        "wue_l_per_kwh": 1.0,
        "pue": 1.15,
        "certifications": ["ISO 14001"],
    },
    "scaleway": {
        "score": 85,
        "carbon_intensity": 55,
        "renewable_pct": 95,
        "wue_l_per_kwh": 0.7,
        "pue": 1.11,
        "certifications": ["ISO 14001"],
    },
}

HARDWARE_LIFESPAN_GUIDE = {
    "server": {"min_months": 36, "max_months": 72, "typical_months": 60},
    "storage": {"min_months": 36, "max_months": 60, "typical_months": 48},
    "network": {"min_months": 60, "max_months": 96, "typical_months": 84},
    "gpu": {"min_months": 36, "max_months": 60, "typical_months": 48},
    "ups": {"min_months": 24, "max_months": 48, "typical_months": 36},
}

ENERGY_STAR_RATINGS = {
    90: "Energy Star",
    75: "Efficient",
    50: "Average",
    25: "Needs Optimization",
    0: "Inefficient",
}


def get_carbon_intensity(region: str) -> Optional[dict]:
    return CARBON_INTENSITY_MAP.get(region)


def get_provider_sustainability(provider: str) -> Optional[dict]:
    return PROVIDER_SUSTAINABILITY_RANKINGS.get(provider)


def get_all_provider_rankings() -> dict:
    return dict(sorted(
        PROVIDER_SUSTAINABILITY_RANKINGS.items(),
        key=lambda x: x[1]["score"],
        reverse=True,
    ))


def calculate_efficiency_score(cpu_util: float, ram_util: float,
                                disk_util: float, net_util: float) -> dict:
    cpu_score = min(cpu_util / 70.0, 1.0) * 100
    ram_score = min(ram_util / 75.0, 1.0) * 100
    disk_score = min(disk_util / 80.0, 1.0) * 100
    net_score = min(net_util / 50.0, 1.0) * 100
    overall = (cpu_score * 0.40 + ram_score * 0.30 +
               disk_score * 0.20 + net_score * 0.10)
    penalty = 0
    if cpu_util < 5 and disk_util < 5:
        penalty = -15
    elif cpu_util > 95:
        penalty = -5
    overall = max(0, overall + penalty)
    badge = "Inefficient"
    for threshold, label in sorted(ENERGY_STAR_RATINGS.items(), reverse=True):
        if overall >= threshold:
            badge = label
            break
    return {
        "overall_score": round(overall, 1),
        "cpu_score": round(cpu_score, 1),
        "ram_score": round(ram_score, 1),
        "disk_score": round(disk_score, 1),
        "net_score": round(net_score, 1),
        "badge": badge,
        "penalty": penalty,
    }


def calculate_depreciation(purchase_price: float, salvage_value: float,
                            lifespan_months: int, age_months: float,
                            method: str = "straight_line") -> float:
    if method == "straight_line":
        monthly = (purchase_price - salvage_value) / max(lifespan_months, 1)
        age = min(age_months, lifespan_months)
        return max(salvage_value, purchase_price - monthly * age)
    elif method == "declining_balance":
        rate = 2.0 / max(lifespan_months, 1)
        value = purchase_price
        for _ in range(int(min(age_months, lifespan_months))):
            value -= value * rate
        return max(salvage_value, value)
    return purchase_price


def estimate_shutdown_savings(containers_count: int, cpu_cores: int,
                               memory_gb: int, off_hours_per_week: int) -> dict:
    cost_per_hour = containers_count * 0.02 + cpu_cores * 0.04 + memory_gb * 0.01
    weekly_savings = cost_per_hour * off_hours_per_week
    monthly_savings = weekly_savings * 4.33
    annual_savings = monthly_savings * 12
    return {
        "cost_per_hour": round(cost_per_hour, 2),
        "off_hours_per_week": off_hours_per_week,
        "weekly_savings": round(weekly_savings, 2),
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
    }


def energy_star_label(score: float) -> str:
    for threshold, label in sorted(ENERGY_STAR_RATINGS.items(), reverse=True):
        if score >= threshold:
            return label
    return "Inefficient"


def get_green_energy_sources() -> list[dict]:
    return [
        {"source": "Solar", "pct": 35, "trend": "up"},
        {"source": "Wind", "pct": 30, "trend": "up"},
        {"source": "Hydroelectric", "pct": 15, "trend": "stable"},
        {"source": "Nuclear", "pct": 10, "trend": "stable"},
        {"source": "Biomass", "pct": 5, "trend": "stable"},
        {"source": "Geothermal", "pct": 5, "trend": "up"},
    ]
