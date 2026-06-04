import pytest


class TestDeviceSpec:
    def test_get_device_spec_known(self):
        from infra.edge import get_device_spec
        spec = get_device_spec("raspberry_pi_5")
        assert spec["ram_gb"] == 8
        assert spec["cpu"] == "BCM2712"
        assert spec["arch"] == "arm64"

    def test_get_device_spec_unknown(self):
        from infra.edge import get_device_spec
        assert get_device_spec("unknown_device") is None

    def test_get_device_spec_all_known(self):
        from infra.edge import EDGE_DEVICE_PROVIDER_MAP, get_device_spec
        for device in EDGE_DEVICE_PROVIDER_MAP:
            spec = get_device_spec(device)
            assert "cpu" in spec and "ram_gb" in spec and "arch" in spec


class TestModelSpec:
    def test_get_model_spec_known(self):
        from infra.edge import get_model_spec
        spec = get_model_spec("mobilenet_v2")
        assert spec["format"] == "tflite"
        assert spec["size_mb"] == 14

    def test_get_model_spec_unknown(self):
        from infra.edge import get_model_spec
        assert get_model_spec("unknown_model") is None


class TestFirmwareVersions:
    def test_get_firmware_versions_known(self):
        from infra.edge import get_firmware_versions
        versions = get_firmware_versions("raspberry_pi")
        assert "2.0.0" in versions
        assert "1.0.0" in versions

    def test_get_firmware_versions_unknown(self):
        from infra.edge import get_firmware_versions
        assert get_firmware_versions("unknown_device") == []


class TestFrequencyPlan:
    def test_get_frequency_plan_known(self):
        from infra.edge import get_frequency_plan
        plan = get_frequency_plan("EU868")
        assert plan["bandwidth_khz"] == 125
        assert plan["duty_cycle_pct"] == 1.0
        assert len(plan["frequencies_mhz"]) == 8

    def test_get_frequency_plan_unknown(self):
        from infra.edge import get_frequency_plan
        assert get_frequency_plan("UNKNOWN") is None


class TestMeshDefaults:
    def test_get_mesh_defaults_wireguard(self):
        from infra.edge import get_mesh_defaults
        cfg = get_mesh_defaults("wireguard")
        assert cfg["port"] == 51820
        assert cfg["mtu"] == 1420

    def test_get_mesh_defaults_tinc(self):
        from infra.edge import get_mesh_defaults
        cfg = get_mesh_defaults("tinc")
        assert cfg["port"] == 655
        assert cfg["cipher"] == "aes-256-cbc"

    def test_get_mesh_defaults_unknown(self):
        from infra.edge import get_mesh_defaults
        assert get_mesh_defaults("unknown") == {}


class TestValidateDeviceFingerprint:
    def test_valid_fingerprint(self):
        from infra.edge import validate_device_fingerprint
        assert validate_device_fingerprint("fp_abcdef1234567890") is True

    def test_invalid_fingerprint_too_short(self):
        from infra.edge import validate_device_fingerprint
        assert validate_device_fingerprint("fp_short") is False

    def test_invalid_fingerprint_wrong_prefix(self):
        from infra.edge import validate_device_fingerprint
        assert validate_device_fingerprint("ab_abcdef1234567890") is False

    def test_invalid_fingerprint_empty(self):
        from infra.edge import validate_device_fingerprint
        assert validate_device_fingerprint("") is False
        assert validate_device_fingerprint(None) is False


class TestCalculateCacheSize:
    def test_calculate_cache_size_gb(self):
        from infra.edge import calculate_cache_size_gb
        result = calculate_cache_size_gb(1024, 5)
        assert result == 5.0

    def test_calculate_cache_size_default_size(self):
        from infra.edge import calculate_cache_size_gb
        result = calculate_cache_size_gb(2048)
        assert result == 10.0

    def test_calculate_cache_size_zero(self):
        from infra.edge import calculate_cache_size_gb
        assert calculate_cache_size_gb(0) == 0.0


class TestEstimatePower:
    def test_estimate_power_from_utilization(self):
        from infra.edge import estimate_power_from_utilization
        result = estimate_power_from_utilization(50, 8, 1000)
        cpu_power = 10 + (50 / 100) * 80
        ram_power = 0.5 * 8
        disk_power = 0.01 * 1000
        assert result["cpu_watts"] == round(cpu_power, 2)
        assert result["ram_watts"] == round(ram_power, 2)
        assert result["disk_watts"] == round(disk_power, 2)
        assert result["total_watts"] == round(cpu_power + ram_power + disk_power, 2)

    def test_estimate_power_zero_util(self):
        from infra.edge import estimate_power_from_utilization
        result = estimate_power_from_utilization(0, 0, 0)
        assert result["total_watts"] == 10.0  # idle cpu power


class TestCalculateCO2:
    def test_calculate_co2_default(self):
        from infra.edge import calculate_co2
        result = calculate_co2(100)
        assert result["energy_kwh"] == 100.0
        assert result["co2_grams"] == 100 * 285
        assert result["co2_kg"] == 100 * 285 / 1000

    def test_calculate_co2_custom_intensity(self):
        from infra.edge import calculate_co2
        result = calculate_co2(100, grid_intensity=100)
        assert result["co2_grams"] == 10000
        assert result["co2_kg"] == 10.0


class TestPUEClassification:
    def test_pue_classification_excellent(self):
        from infra.edge import pue_classification
        assert pue_classification(1.1) == "Excellent"

    def test_pue_classification_good(self):
        from infra.edge import pue_classification
        assert pue_classification(1.3) == "Good"

    def test_pue_classification_average(self):
        from infra.edge import pue_classification
        assert pue_classification(1.5) == "Average"

    def test_pue_classification_poor(self):
        from infra.edge import pue_classification
        assert pue_classification(1.8) == "Poor"

    def test_pue_classification_very_poor(self):
        from infra.edge import pue_classification
        assert pue_classification(2.5) == "Very Poor"


class TestEstimateOffsetCost:
    def test_estimate_offset_cost_reforestation(self):
        from infra.edge import estimate_offset_cost
        result = estimate_offset_cost(1000, "reforestation")
        assert result["co2_kg"] == 1000
        assert result["co2_tons"] == 1.0
        assert result["price_per_ton"] == 15.0
        assert result["total_cost"] == 15.0

    def test_estimate_offset_cost_renewable(self):
        from infra.edge import estimate_offset_cost
        result = estimate_offset_cost(2000, "renewable_energy")
        assert result["total_cost"] == 24.0

    def test_estimate_offset_cost_direct_air_capture(self):
        from infra.edge import estimate_offset_cost
        result = estimate_offset_cost(1000, "direct_air_capture")
        assert result["total_cost"] == 150.0

    def test_estimate_offset_cost_unknown_type(self):
        from infra.edge import estimate_offset_cost
        result = estimate_offset_cost(1000, "unknown")
        assert result["total_cost"] == 15.0

    def test_estimate_offset_cost_default_type(self):
        from infra.edge import estimate_offset_cost
        result = estimate_offset_cost(500)
        assert result["project_type"] == "reforestation"
