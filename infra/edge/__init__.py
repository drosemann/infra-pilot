"""Infra edge module - provider maps and helpers for edge computing features."""

from typing import Any, Optional

EDGE_DEVICE_PROVIDER_MAP = {
    "raspberry_pi_4": {"cpu": "BCM2711", "ram_gb": 4, "arch": "arm64", "gpu": "VideoCore VI"},
    "raspberry_pi_5": {"cpu": "BCM2712", "ram_gb": 8, "arch": "arm64", "gpu": "VideoCore VII"},
    "jetson_nano": {"cpu": "ARM Cortex-A57", "ram_gb": 4, "arch": "arm64", "gpu": "128-core Maxwell"},
    "jetson_orin": {"cpu": "ARM Cortex-A78", "ram_gb": 8, "arch": "arm64", "gpu": "Ampere 2048-core"},
    "rockpi_5": {"cpu": "RK3588", "ram_gb": 16, "arch": "arm64", "gpu": "Mali-G610"},
    "generic_arm": {"cpu": "generic", "ram_gb": 4, "arch": "arm64", "gpu": "generic"},
    "generic_x86": {"cpu": "generic", "ram_gb": 8, "arch": "amd64", "gpu": "generic"},
}

EDGE_MODEL_MAP = {
    "mobilenet_v2": {"format": "tflite", "input": [1, 224, 224, 3], "size_mb": 14},
    "yolo_v5": {"format": "onnx", "input": [1, 3, 640, 640], "size_mb": 28},
    "anomaly_detector": {"format": "onnx", "input": [1, 128], "size_mb": 2},
    "vibration_cnn": {"format": "tflite", "input": [1, 64, 3], "size_mb": 1},
    "keyword_spotter": {"format": "tflite", "input": [1, 49, 10], "size_mb": 0.5},
    "defect_detector": {"format": "onnx", "input": [1, 512, 512, 3], "size_mb": 45},
}

EDGE_FIRMWARE_MAP = {
    "raspberry_pi": ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"],
    "jetson_nano": ["1.0.0", "1.1.0", "2.0.0"],
    "rockpi": ["1.0.0", "1.1.0"],
}

LORAWAN_FREQUENCY_PLANS = {
    "EU868": {
        "frequencies_mhz": [868.1, 868.3, 868.5, 867.1, 867.3, 867.5, 867.7, 867.9],
        "bandwidth_khz": 125,
        "duty_cycle_pct": 1.0,
        "max_eirp_dbm": 16,
    },
    "US915": {
        "frequencies_mhz": [902.3, 902.5, 902.7, 902.9, 903.1, 903.3, 903.5, 903.7],
        "bandwidth_khz": 125,
        "duty_cycle_pct": 10.0,
        "max_eirp_dbm": 30,
    },
    "AU915": {
        "frequencies_mhz": [915.2, 915.4, 915.6, 915.8, 916.0, 916.2, 916.4, 916.6],
        "bandwidth_khz": 125,
        "duty_cycle_pct": 1.0,
        "max_eirp_dbm": 30,
    },
    "AS923": {
        "frequencies_mhz": [923.2, 923.4, 923.6, 923.8, 924.0, 924.2, 924.4, 924.6],
        "bandwidth_khz": 125,
        "duty_cycle_pct": 1.0,
        "max_eirp_dbm": 16,
    },
    "CN470": {
        "frequencies_mhz": [470.3, 470.5, 470.7, 470.9, 471.1, 471.3, 471.5, 471.7],
        "bandwidth_khz": 125,
        "duty_cycle_pct": 1.0,
        "max_eirp_dbm": 16,
    },
}

MESH_PROTOCOL_DEFAULTS = {
    "wireguard": {
        "port": 51820,
        "mtu": 1420,
        "keepalive": 25,
        "allowed_ips": ["0.0.0.0/0"],
    },
    "tinc": {
        "port": 655,
        "mtu": 1500,
        "compression": 9,
        "cipher": "aes-256-cbc",
    },
}


def get_device_spec(device_type: str) -> Optional[dict]:
    return EDGE_DEVICE_PROVIDER_MAP.get(device_type)


def get_model_spec(model_name: str) -> Optional[dict]:
    return EDGE_MODEL_MAP.get(model_name)


def get_firmware_versions(device_type: str) -> list:
    return EDGE_FIRMWARE_MAP.get(device_type, [])


def get_frequency_plan(region: str) -> Optional[dict]:
    return LORAWAN_FREQUENCY_PLANS.get(region)


def get_mesh_defaults(protocol: str) -> dict:
    return MESH_PROTOCOL_DEFAULTS.get(protocol, {})


def validate_device_fingerprint(fingerprint: str) -> bool:
    if not fingerprint or len(fingerprint) < 16:
        return False
    return fingerprint.startswith("fp_")


def calculate_cache_size_gb(objects_count: int, avg_size_mb: float = 5.0) -> float:
    return round(objects_count * avg_size_mb / 1024, 2)


def estimate_power_from_utilization(cpu_pct: float, ram_gb: float,
                                     disk_iops: int = 0) -> dict:
    cpu_power = 10 + (cpu_pct / 100) * 80
    ram_power = 0.5 * ram_gb
    disk_power = 0.01 * disk_iops
    return {
        "cpu_watts": round(cpu_power, 2),
        "ram_watts": round(ram_power, 2),
        "disk_watts": round(disk_power, 2),
        "total_watts": round(cpu_power + ram_power + disk_power, 2),
    }


def calculate_co2(energy_kwh: float, grid_intensity: float = 285.0) -> dict:
    co2_grams = energy_kwh * grid_intensity
    return {
        "energy_kwh": round(energy_kwh, 3),
        "grid_intensity": grid_intensity,
        "co2_grams": round(co2_grams, 2),
        "co2_kg": round(co2_grams / 1000, 4),
    }


def pue_classification(pue: float) -> str:
    if pue < 1.2:
        return "Excellent"
    elif pue < 1.4:
        return "Good"
    elif pue < 1.6:
        return "Average"
    elif pue < 2.0:
        return "Poor"
    return "Very Poor"


def estimate_offset_cost(co2_kg: float, project_type: str = "reforestation") -> dict:
    prices = {
        "reforestation": 15.0,
        "renewable_energy": 12.0,
        "direct_air_capture": 150.0,
        "methane_capture": 8.0,
        "blue_carbon": 25.0,
        "soil_carbon": 20.0,
    }
    price = prices.get(project_type, 15.0)
    total = co2_kg / 1000 * price
    return {
        "co2_kg": co2_kg,
        "co2_tons": round(co2_kg / 1000, 3),
        "price_per_ton": price,
        "total_cost": round(total, 2),
        "project_type": project_type,
    }
