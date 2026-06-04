import pytest


class TestCarbonIntensity:
    def test_get_carbon_intensity_known(self):
        from infra.green import get_carbon_intensity
        result = get_carbon_intensity("eu-north")
        assert result is not None
        assert result["intensity_g_per_kwh"] == 50
        assert result["renewable_pct"] == 90

    def test_get_carbon_intensity_unknown(self):
        from infra.green import get_carbon_intensity
        assert get_carbon_intensity("mars") is None

    def test_carbon_intensity_map_values(self):
        from infra.green import CARBON_INTENSITY_MAP
        assert "us-east" in CARBON_INTENSITY_MAP
        assert "eu-central" in CARBON_INTENSITY_MAP
        assert "africa" in CARBON_INTENSITY_MAP


class TestProviderSustainability:
    def test_get_provider_sustainability_known(self):
        from infra.green import get_provider_sustainability
        result = get_provider_sustainability("google_cloud")
        assert result["score"] == 92
        assert result["renewable_pct"] == 100

    def test_get_provider_sustainability_unknown(self):
        from infra.green import get_provider_sustainability
        assert get_provider_sustainability("unknown_provider") is None

    def test_get_all_provider_rankings_sorted(self):
        from infra.green import get_all_provider_rankings
        rankings = get_all_provider_rankings()
        scores = [v["score"] for v in rankings.values()]
        assert scores == sorted(scores, reverse=True)
        assert list(rankings.keys())[0] == "google_cloud"


class TestEfficiencyScore:
    def test_calculate_efficiency_score_balanced(self):
        from infra.green import calculate_efficiency_score
        result = calculate_efficiency_score(50, 60, 40, 30)
        assert 0 < result["overall_score"] < 100
        assert "badge" in result
        assert "penalty" in result

    def test_efficiency_score_penalty_low_util(self):
        from infra.green import calculate_efficiency_score
        result = calculate_efficiency_score(2, 50, 2, 10)
        assert result["penalty"] == -15

    def test_efficiency_score_penalty_high_cpu(self):
        from infra.green import calculate_efficiency_score
        result = calculate_efficiency_score(98, 50, 40, 30)
        assert result["penalty"] == -5

    def test_efficiency_score_no_penalty(self):
        from infra.green import calculate_efficiency_score
        result = calculate_efficiency_score(50, 50, 50, 50)
        assert result["penalty"] == 0

    def test_efficiency_score_capped_at_zero(self):
        from infra.green import calculate_efficiency_score
        result = calculate_efficiency_score(0, 0, 0, 0)
        assert result["overall_score"] >= 0

    def test_efficiency_score_badge_assignment(self):
        from infra.green import calculate_efficiency_score
        high = calculate_efficiency_score(70, 75, 80, 50)
        low = calculate_efficiency_score(1, 1, 1, 1)
        assert high["badge"] != "Inefficient"
        assert isinstance(low["badge"], str)


class TestDepreciation:
    def test_straight_line_depreciation(self):
        from infra.green import calculate_depreciation
        value = calculate_depreciation(1000, 200, 36, 12, "straight_line")
        expected = 1000 - ((1000 - 200) / 36) * 12
        assert round(value, 2) == round(expected, 2)

    def test_straight_line_at_salvage(self):
        from infra.green import calculate_depreciation
        value = calculate_depreciation(1000, 200, 36, 60, "straight_line")
        assert value == 200

    def test_declining_balance(self):
        from infra.green import calculate_depreciation
        value = calculate_depreciation(1000, 200, 36, 12, "declining_balance")
        assert value >= 200
        assert value < 1000

    def test_declining_balance_at_salvage(self):
        from infra.green import calculate_depreciation
        value = calculate_depreciation(1000, 200, 2, 10, "declining_balance")
        assert value == 200

    def test_unknown_method(self):
        from infra.green import calculate_depreciation
        value = calculate_depreciation(1000, 200, 36, 12, "unknown")
        assert value == 1000


class TestShutdownSavings:
    def test_estimate_shutdown_savings(self):
        from infra.green import estimate_shutdown_savings
        result = estimate_shutdown_savings(10, 4, 16, 40)
        assert result["off_hours_per_week"] == 40
        assert result["weekly_savings"] > 0
        assert result["monthly_savings"] > result["weekly_savings"]
        assert result["annual_savings"] > result["monthly_savings"]
        assert result["cost_per_hour"] > 0

    def test_shutdown_savings_no_hours(self):
        from infra.green import estimate_shutdown_savings
        result = estimate_shutdown_savings(10, 4, 16, 0)
        assert result["weekly_savings"] == 0


class TestEnergyStarLabel:
    def test_energy_star_label_platinum(self):
        from infra.green import energy_star_label
        assert energy_star_label(95) == "Energy Star"

    def test_energy_star_label_efficient(self):
        from infra.green import energy_star_label
        assert energy_star_label(80) == "Efficient"

    def test_energy_star_label_average(self):
        from infra.green import energy_star_label
        assert energy_star_label(60) == "Average"

    def test_energy_star_label_needs_optimization(self):
        from infra.green import energy_star_label
        assert energy_star_label(30) == "Needs Optimization"

    def test_energy_star_label_inefficient(self):
        from infra.green import energy_star_label
        assert energy_star_label(10) == "Inefficient"


class TestGreenEnergySources:
    def test_get_green_energy_sources(self):
        from infra.green import get_green_energy_sources
        sources = get_green_energy_sources()
        assert len(sources) == 6
        assert sources[0]["source"] == "Solar"
        assert all("source" in s and "pct" in s and "trend" in s for s in sources)
