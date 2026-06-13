"""Advanced green computing calculators and reporting."""

import pytest
from calculators import (
    CarbonCalculator, EnergyCostCalculator, PUECalculator,
    OffsetCalculator, SustainabilityScore, GreenReporter
)


class TestCarbonCalculator:
    def test_calculate_basic(self):
        calc = CarbonCalculator("us-east")
        result = calc.calculate(1000, renewable_pct=0)
        assert result.total_co2_kg > 0
        assert result.total_energy_kwh == 1000

    def test_calculate_with_renewables(self):
        calc = CarbonCalculator("us-east")
        result = calc.calculate(1000, renewable_pct=50)
        grid_part = result.scope_2_kg / 0.294 / 1000
        assert grid_part < 1000

    def test_carbon_neutral_with_offsets(self):
        calc = CarbonCalculator("us-east")
        result = calc.calculate(1000, offsets_kg=500)
        assert result.net_co2_kg >= 0

    def test_with_region(self):
        calc = CarbonCalculator("us-east")
        calc2 = calc.with_region("eu-central")
        assert calc2.intensity != calc.intensity

    def test_regional_intensities(self):
        for region in ["us-east", "us-west", "eu-central", "ap-southeast"]:
            calc = CarbonCalculator(region)
            result = calc.calculate(1, renewable_pct=0)
            assert result.total_co2_kg > 0


class TestEnergyCostCalculator:
    def test_calculate_cost(self):
        calc = EnergyCostCalculator("us-east")
        cost = calc.calculate_cost(1000)
        assert cost == 120.0

    def test_calculate_monthly(self):
        calc = EnergyCostCalculator("us-east")
        result = calc.calculate_monthly(100)
        assert result["monthly_kwh"] == 3000
        assert result["monthly_cost"] > 0

    def test_project_savings(self):
        calc = EnergyCostCalculator("us-east")
        result = calc.project_savings(1000, 800)
        assert result["savings_kwh"] == 200
        assert result["savings_usd"] == 24.0


class TestPUECalculator:
    def test_calculate_pue(self):
        calc = PUECalculator()
        pue = calc.calculate_pue(500, 400)
        assert pue == 1.25

    def test_pue_zero_it_load(self):
        calc = PUECalculator()
        pue = calc.calculate_pue(500, 0)
        assert pue == 0.0

    def test_cooling_load(self):
        calc = PUECalculator()
        cooling = calc.calculate_cooling_load(500, 400)
        assert cooling == 100.0

    def test_efficiency_score(self):
        calc = PUECalculator()
        score = calc.calculate_efficiency_score(1.2)
        assert 80 <= score <= 85

    def test_estimate_savings(self):
        calc = PUECalculator()
        savings = calc.estimate_savings(1.4, 1.2, 500)
        assert savings["savings_kw"] > 0

    def test_efficiency_rating(self):
        calc = PUECalculator()
        assert calc.get_efficiency_rating(1.05) == "excellent"
        assert calc.get_efficiency_rating(1.5) == "poor"
        assert calc.get_efficiency_rating(2.0) == "critical"


class TestOffsetCalculator:
    def test_calculate_required(self):
        calc = OffsetCalculator()
        result = calc.calculate_required_offsets(10000)
        assert result["required_offsets_tonnes"] == 10.0
        assert result["trees_required"] > 0

    def test_calculate_project_impact(self):
        calc = OffsetCalculator()
        result = calc.calculate_project_impact("reforestation", 100)
        assert "annual_cost" in result

    def test_different_project_types(self):
        calc = OffsetCalculator()
        for ptype in ["reforestation", "renewable_energy", "methane_capture", "direct_air_capture"]:
            result = calc.calculate_project_impact(ptype, 50)
            assert result["effective_co2_reduction"] > 0


class TestSustainabilityScore:
    def test_compute(self):
        ss = SustainabilityScore()
        result = ss.compute(pue=1.2, renewable_pct=50, carbon_intensity=0.3)
        assert 60 <= result["overall_score"] <= 80

    def test_ratings(self):
        ss = SustainabilityScore()
        assert ss._get_rating(95) == "platinum"
        assert ss._get_rating(80) == "gold"
        assert ss._get_rating(65) == "silver"
        assert ss._get_rating(45) == "bronze"
        assert ss._get_rating(20) == "standard"

    def test_compare(self):
        ss = SustainabilityScore()
        scores = [{"name": "A", "overall": 80}, {"name": "B", "overall": 90}]
        ranked = ss.compare(scores)
        assert ranked[0]["name"] == "B"
        assert ranked[0]["rank"] == 1


class TestGreenReporter:
    def test_sustainability_report(self):
        gr = GreenReporter()
        facilities = [
            {"name": "DC-1", "total_power_kw": 500, "it_load_kw": 400},
            {"name": "DC-2", "total_power_kw": 300, "it_load_kw": 250},
        ]
        report = gr.generate_sustainability_report(facilities, 30)
        assert report["facilities"] == 2
        assert report["avg_pue"] > 0

    def test_comparison(self):
        gr = GreenReporter()
        result = gr.generate_comparison({"emissions": 100}, {"emissions": 120})
        assert result["changes_pct"]["emissions"] == -16.7
