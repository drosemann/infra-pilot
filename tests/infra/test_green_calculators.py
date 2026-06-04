import pytest
from dataclasses import asdict


class TestCarbonCalculator:
    def test_calculate_default_region(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator()
        result = calc.calculate(1000)
        assert result.total_co2_kg > 0
        assert result.carbon_intensity == 0.294
        assert result.total_energy_kwh == 1000

    def test_calculate_with_renewable(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator("eu-west")
        result = calc.calculate(1000, renewable_pct=50)
        scope_2 = (1000 * 0.5) * 0.182
        assert result.scope_2_kg == round(scope_2, 2)

    def test_calculate_with_offsets(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator("us-east")
        result = calc.calculate(1000, offsets_kg=500)
        assert result.net_co2_kg >= 0

    def test_calculate_carbon_neutral(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator()
        result = calc.calculate(1000, offsets_kg=10000)
        assert result.carbon_neutral is True

    def test_calculate_with_scopes(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator("us-east")
        result = calc.calculate(1000, scope_1_kg=50, scope_3_kg=30)
        assert result.scope_1_kg == 50
        assert result.scope_3_kg == 30

    def test_calculate_exhaustive(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator("ap-southeast")
        result = calc.calculate(500, renewable_pct=20, scope_1_kg=10, scope_3_kg=5, offsets_kg=100)
        d = asdict(result)
        assert d["total_energy_kwh"] == 500
        assert d["carbon_intensity"] == 0.408
        assert d["renewable_pct"] == 20
        assert isinstance(d["carbon_neutral"], bool)

    def test_with_region_returns_new_instance(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator("us-east")
        calc2 = calc.with_region("eu-west")
        assert calc2.region == "eu-west"
        assert calc.region == "us-east"
        assert calc is not calc2

    def test_unknown_region_default_intensity(self):
        from infra.green.calculators import CarbonCalculator
        calc = CarbonCalculator("mars")
        assert calc.intensity == 0.3


class TestEnergyCostCalculator:
    def test_calculate_cost(self):
        from infra.green.calculators import EnergyCostCalculator
        calc = EnergyCostCalculator("us-east")
        assert calc.calculate_cost(100) == 12.0

    def test_calculate_monthly(self):
        from infra.green.calculators import EnergyCostCalculator
        calc = EnergyCostCalculator("eu-central")
        result = calc.calculate_monthly(10)
        assert result["monthly_kwh"] == 300
        assert result["monthly_cost"] == round(300 * 0.22, 2)
        assert result["annual_cost"] == round(300 * 12 * 0.22, 2)

    def test_project_savings(self):
        from infra.green.calculators import EnergyCostCalculator
        calc = EnergyCostCalculator("us-east")
        result = calc.project_savings(1000, 800)
        assert result["savings_kwh"] == 200
        assert result["savings_pct"] == 20.0
        assert result["savings_usd"] == 24.0

    def test_project_savings_zero_current(self):
        from infra.green.calculators import EnergyCostCalculator
        calc = EnergyCostCalculator()
        result = calc.project_savings(0, 100)
        assert result["savings_pct"] == 0

    def test_unknown_region_rate(self):
        from infra.green.calculators import EnergyCostCalculator
        calc = EnergyCostCalculator("mars")
        assert calc.rate_per_kwh == 0.12


class TestPUECalculator:
    def test_calculate_pue(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        assert calc.calculate_pue(150, 100) == 1.5

    def test_calculate_pue_zero_it_load(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        assert calc.calculate_pue(100, 0) == 0.0

    def test_calculate_cooling_load(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        assert calc.calculate_cooling_load(150, 100) == 50.0

    def test_efficiency_score_ideal(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        assert calc.calculate_efficiency_score(1.0) == 100.0

    def test_efficiency_score_zero_pue(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        assert calc.calculate_efficiency_score(0) == 0

    def test_estimate_savings(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        result = calc.estimate_savings(1.5, 1.2, 100)
        assert result["savings_kw"] == 30
        assert result["savings_kwh_daily"] == 720

    def test_get_efficiency_rating(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        assert calc.get_efficiency_rating(1.05) == "excellent"
        assert calc.get_efficiency_rating(1.15) == "good"
        assert calc.get_efficiency_rating(1.3) == "average"
        assert calc.get_efficiency_rating(1.5) == "poor"
        assert calc.get_efficiency_rating(2.0) == "critical"

    def test_efficiency_score(self):
        from infra.green.calculators import PUECalculator
        calc = PUECalculator()
        score = calc.calculate_efficiency_score(2.0)
        assert score == 50.0


class TestOffsetCalculator:
    def test_calculate_required_offsets(self):
        from infra.green.calculators import OffsetCalculator
        calc = OffsetCalculator()
        result = calc.calculate_required_offsets(10000)
        assert result["total_co2_tonnes"] == 10.0
        assert result["required_offsets_tonnes"] == 10.0
        assert result["trees_required"] == 450
        assert result["estimated_cost_usd"] == 150.0

    def test_calculate_offsets_partial(self):
        from infra.green.calculators import OffsetCalculator
        calc = OffsetCalculator()
        result = calc.calculate_required_offsets(5000, target_neutral_pct=50)
        assert result["required_offsets_tonnes"] == 2.5

    def test_calculate_project_impact_reforestation(self):
        from infra.green.calculators import OffsetCalculator
        calc = OffsetCalculator()
        result = calc.calculate_project_impact("reforestation", 100)
        assert result["cost_per_tonne"] == 12.0
        assert result["annual_cost"] == 1200.0

    def test_calculate_project_impact_unknown_type(self):
        from infra.green.calculators import OffsetCalculator
        calc = OffsetCalculator()
        result = calc.calculate_project_impact("unknown", 100)
        assert result["project_type"] == "unknown"


class TestSustainabilityScore:
    def test_compute(self):
        from infra.green.calculators import SustainabilityScore
        scorer = SustainabilityScore()
        result = scorer.compute(pue=1.2, renewable_pct=60, carbon_intensity=100)
        assert 0 < result["overall_score"] < 100
        assert "rating" in result
        assert "categories" in result

    def test_compute_perfect_scores(self):
        from infra.green.calculators import SustainabilityScore
        scorer = SustainabilityScore()
        result = scorer.compute(pue=1.0, renewable_pct=100, carbon_intensity=0, water_usage_l_per_kwh=0)
        assert result["overall_score"] > 90

    def test_compute_zero_pue(self):
        from infra.green.calculators import SustainabilityScore
        scorer = SustainabilityScore()
        result = scorer.compute(pue=0, renewable_pct=0, carbon_intensity=500)
        assert result["categories"]["energy_efficiency"] == 0

    def test_get_rating(self):
        from infra.green.calculators import SustainabilityScore
        scorer = SustainabilityScore()
        assert scorer._get_rating(95) == "platinum"
        assert scorer._get_rating(80) == "gold"
        assert scorer._get_rating(65) == "silver"
        assert scorer._get_rating(50) == "bronze"
        assert scorer._get_rating(20) == "standard"

    def test_compare(self):
        from infra.green.calculators import SustainabilityScore
        scorer = SustainabilityScore()
        scores = [
            {"name": "A", "overall": 80},
            {"name": "B", "overall": 95},
            {"name": "C", "overall": 60},
        ]
        ranked = scorer.compare(scores)
        assert ranked[0]["name"] == "B"
        assert ranked[1]["name"] == "A"
        assert ranked[2]["name"] == "C"
        assert ranked[0]["rank"] == 1
        assert ranked[0]["rating"] == "platinum"


class TestGreenReporter:
    def test_generate_sustainability_report(self):
        from infra.green.calculators import GreenReporter
        reporter = GreenReporter()
        facilities = [
            {"total_power_kw": 100, "it_load_kw": 80},
            {"total_power_kw": 200, "it_load_kw": 160},
        ]
        result = reporter.generate_sustainability_report(facilities, 30)
        assert result["facilities"] == 2
        assert result["total_power_kw"] == 300
        assert result["total_it_kw"] == 240
        assert result["avg_pue"] == 1.25

    def test_generate_sustainability_report_empty(self):
        from infra.green.calculators import GreenReporter
        reporter = GreenReporter()
        result = reporter.generate_sustainability_report([])
        assert result["facilities"] == 0
        assert result["avg_pue"] == 0

    def test_generate_comparison(self):
        from infra.green.calculators import GreenReporter
        reporter = GreenReporter()
        current = {"pue": 1.2, "co2": 100}
        baseline = {"pue": 1.5, "co2": 150}
        result = reporter.generate_comparison(current, baseline)
        assert result["changes_pct"]["pue"] == -20.0
        assert result["changes_pct"]["co2"] == -33.3
        assert result["improved"] is True

    def test_generate_comparison_no_improvement(self):
        from infra.green.calculators import GreenReporter
        reporter = GreenReporter()
        current = {"pue": 1.8, "co2": 200}
        baseline = {"pue": 1.5, "co2": 150}
        result = reporter.generate_comparison(current, baseline)
        assert result["improved"] is False
