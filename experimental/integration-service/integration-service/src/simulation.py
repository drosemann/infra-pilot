"""Edge & IoT simulation and testing utilities.

This module provides simulation tools for testing edge devices, IoT data pipelines,
and network topologies without requiring physical hardware.
"""

import random
import json
import math
import time
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SimulatedSensor:
    device_id: str
    sensor_type: str
    location: str
    base_value: float
    noise_std: float
    drift_per_hour: float
    failure_probability: float
    battery_max: float
    battery_current: float
    firmware_version: str
    is_online: bool = True
    last_reading_time: datetime = field(default_factory=datetime.utcnow)
    readings_sent: int = 0


class SensorSimulator:
    """Simulates IoT sensor data streams."""

    def __init__(self):
        self.sensors: Dict[str, SimulatedSensor] = {}
        self.presets = self._create_presets()

    def _create_presets(self) -> Dict[str, Dict[str, Any]]:
        return {
            "temperature": {
                "base_value": 22.0, "noise_std": 2.0, "drift_per_hour": 0.1,
                "battery_max": 3000, "failure_probability": 0.001
            },
            "humidity": {
                "base_value": 55.0, "noise_std": 5.0, "drift_per_hour": -0.2,
                "battery_max": 2500, "failure_probability": 0.0005
            },
            "pressure": {
                "base_value": 1013.25, "noise_std": 10.0, "drift_per_hour": 0.05,
                "battery_max": 3500, "failure_probability": 0.002
            },
            "light": {
                "base_value": 500.0, "noise_std": 100.0, "drift_per_hour": -5.0,
                "battery_max": 2000, "failure_probability": 0.001
            },
            "vibration": {
                "base_value": 0.5, "noise_std": 0.3, "drift_per_hour": 0.01,
                "battery_max": 4000, "failure_probability": 0.003
            },
            "power": {
                "base_value": 150.0, "noise_std": 25.0, "drift_per_hour": 0.5,
                "battery_max": 50000, "failure_probability": 0.0001
            },
            "current": {
                "base_value": 1.2, "noise_std": 0.3, "drift_per_hour": 0.01,
                "battery_max": 0, "failure_probability": 0.0005
            },
            "voltage": {
                "base_value": 230.0, "noise_std": 5.0, "drift_per_hour": -0.1,
                "battery_max": 0, "failure_probability": 0.0005
            },
            "co2": {
                "base_value": 400.0, "noise_std": 50.0, "drift_per_hour": 2.0,
                "battery_max": 5000, "failure_probability": 0.002
            },
            "airflow": {
                "base_value": 2.5, "noise_std": 0.5, "drift_per_hour": -0.05,
                "battery_max": 3000, "failure_probability": 0.001
            },
        }

    def add_sensor(self, device_id: str, sensor_type: str = "temperature",
                   location: str = "unknown") -> SimulatedSensor:
        preset = self.presets.get(sensor_type, self.presets["temperature"])
        sensor = SimulatedSensor(
            device_id=device_id,
            sensor_type=sensor_type,
            location=location,
            base_value=preset["base_value"],
            noise_std=preset["noise_std"],
            drift_per_hour=preset["drift_per_hour"],
            failure_probability=preset["failure_probability"],
            battery_max=preset["battery_max"],
            battery_current=preset["battery_max"],
            firmware_version=f"FW-{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,99)}"
        )
        self.sensors[device_id] = sensor
        return sensor

    def generate_batch(self, count: int = 10, sensor_type: str = "temperature",
                       location_prefix: str = "DC-1") -> List[SimulatedSensor]:
        sensors = []
        for i in range(count):
            device_id = f"sim-{sensor_type}-{i+1:04d}"
            location = f"{location_prefix}-Rack-{random.choice('ABCDEF')}{random.randint(1,42)}"
            sensor = self.add_sensor(device_id, sensor_type, location)
            sensors.append(sensor)
        return sensors

    def read_sensor(self, device_id: str, hours_elapsed: float = 0) -> Optional[Dict[str, Any]]:
        sensor = self.sensors.get(device_id)
        if not sensor:
            return None
        if not sensor.is_online:
            return {"device_id": device_id, "error": "device_offline"}
        if random.random() < sensor.failure_probability:
            sensor.is_online = False
            return {"device_id": device_id, "error": "sensor_failure"}
        drift = sensor.drift_per_hour * hours_elapsed
        noise = random.gauss(0, sensor.noise_std)
        value = sensor.base_value + drift + noise
        if sensor.battery_max > 0:
            drain = random.uniform(0.5, 2.0)
            sensor.battery_current = max(0, sensor.battery_current - drain)
        sensor.readings_sent += 1
        sensor.last_reading_time = datetime.utcnow()
        reading = {
            "device_id": device_id,
            "sensor_type": sensor.sensor_type,
            "location": sensor.location,
            "value": round(value, 2),
            "unit": self._get_unit(sensor.sensor_type),
            "battery_pct": round((sensor.battery_current / sensor.battery_max) * 100, 1) if sensor.battery_max > 0 else 100,
            "firmware": sensor.firmware_version,
            "timestamp": datetime.utcnow().isoformat(),
            "rssi_dbm": random.randint(-90, -30),
            "snr_db": round(random.uniform(5, 25), 1),
        }
        return reading

    def _get_unit(self, sensor_type: str) -> str:
        units = {
            "temperature": "celsius", "humidity": "pct", "pressure": "hpa",
            "light": "lux", "vibration": "mm/s", "power": "watts",
            "current": "amps", "voltage": "volts", "co2": "ppm",
            "airflow": "m/s"
        }
        return units.get(sensor_type, "unknown")

    def read_all(self, hours_elapsed: float = 0) -> List[Dict[str, Any]]:
        readings = []
        for device_id in list(self.sensors.keys()):
            reading = self.read_sensor(device_id, hours_elapsed)
            if reading:
                readings.append(reading)
        return readings

    def get_stats(self) -> Dict[str, Any]:
        online = sum(1 for s in self.sensors.values() if s.is_online)
        total_readings = sum(s.readings_sent for s in self.sensors.values())
        avg_battery = statistics.mean(
            [s.battery_current / s.battery_max * 100 for s in self.sensors.values() if s.battery_max > 0]
        ) if any(s.battery_max > 0 for s in self.sensors.values()) else 100.0
        return {
            "total_sensors": len(self.sensors),
            "online": online,
            "offline": len(self.sensors) - online,
            "total_readings": total_readings,
            "avg_battery_pct": round(avg_battery, 1),
            "sensor_types": list(set(s.sensor_type for s in self.sensors.values()))
        }


class TopologySimulator:
    """Simulates mesh network topologies for testing."""

    def __init__(self, num_nodes: int = 10):
        self.num_nodes = num_nodes
        self.nodes: List[Dict[str, Any]] = []
        self.links: List[Dict[str, Any]] = []
        self._generate_topology()

    def _generate_topology(self):
        for i in range(self.num_nodes):
            node = {
                "node_id": f"mesh-node-{i+1:04d}",
                "ip_address": f"10.0.{random.randint(0,255)}.{random.randint(1,254)}",
                "role": random.choice(["gateway", "relay", "leaf", "relay", "relay"]),
                "x": random.uniform(0, 100),
                "y": random.uniform(0, 100),
                "rssi_base": random.randint(-85, -45),
                "is_online": True,
                "uptime_hours": random.uniform(0, 720),
                "firmware": f"mesh-fw-{random.randint(1,3)}.{random.randint(0,9)}",
                "neighbors": [],
            }
            self.nodes.append(node)
        for i in range(self.num_nodes):
            for j in range(i + 1, self.num_nodes):
                if random.random() < 0.3:
                    dist = math.sqrt(
                        (self.nodes[i]["x"] - self.nodes[j]["x"]) ** 2 +
                        (self.nodes[i]["y"] - self.nodes[j]["y"]) ** 2
                    )
                    if dist < 60:
                        signal = self.nodes[i]["rssi_base"] + random.randint(-10, 10)
                        link = {
                            "source": self.nodes[i]["node_id"],
                            "target": self.nodes[j]["node_id"],
                            "signal_dbm": signal,
                            "latency_ms": round(random.uniform(1, 50), 1),
                            "bandwidth_mbps": random.randint(10, 1000),
                            "is_active": signal > -80,
                        }
                        self.links.append(link)
                        self.nodes[i]["neighbors"].append(self.nodes[j]["node_id"])
                        self.nodes[j]["neighbors"].append(self.nodes[i]["node_id"])

    def get_topology(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "links": self.links,
            "node_count": len(self.nodes),
            "link_count": len(self.links),
            "avg_degree": round(sum(len(n["neighbors"]) for n in self.nodes) / len(self.nodes), 1),
            "is_connected": self._is_connected()
        }

    def _is_connected(self) -> bool:
        if not self.nodes:
            return False
        visited = set()
        stack = [self.nodes[0]["node_id"]]
        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            node = next((n for n in self.nodes if n["node_id"] == node_id), None)
            if node:
                stack.extend(n for n in node["neighbors"] if n not in visited)
        return len(visited) == len(self.nodes)

    def simulate_link_failure(self, probability: float = 0.1):
        for link in self.links:
            if random.random() < probability:
                link["is_active"] = False
                link["signal_dbm"] = -120

    def simulate_node_failure(self, probability: float = 0.05):
        for node in self.nodes:
            if random.random() < probability:
                node["is_online"] = False
                for link in self.links:
                    if link["source"] == node["node_id"] or link["target"] == node["node_id"]:
                        link["is_active"] = False

    def find_route(self, source_id: str, target_id: str) -> Optional[List[str]]:
        if source_id == target_id:
            return [source_id]
        visited = set()
        queue = [[source_id]]
        while queue:
            path = queue.pop(0)
            node_id = path[-1]
            if node_id in visited:
                continue
            visited.add(node_id)
            node = next((n for n in self.nodes if n["node_id"] == node_id), None)
            if not node:
                continue
            for neighbor_id in node["neighbors"]:
                link = next(
                    (l for l in self.links
                     if ((l["source"] == node_id and l["target"] == neighbor_id) or
                         (l["source"] == neighbor_id and l["target"] == node_id)) and
                     l["is_active"]),
                    None
                )
                if link and neighbor_id not in visited:
                    new_path = path + [neighbor_id]
                    if neighbor_id == target_id:
                        return new_path
                    queue.append(new_path)
        return None


import statistics

class LoadSimulator:
    """Simulates compute load patterns for green scheduling testing."""

    def __init__(self):
        self.load_patterns: Dict[str, List[float]] = {}

    def create_daily_pattern(self, name: str = "default",
                             base_load: float = 50.0,
                             peak_load: float = 100.0,
                             peak_hours: List[int] = [9, 10, 11, 14, 15, 16]) -> List[float]:
        pattern = []
        for hour in range(24):
            if hour in peak_hours:
                load = peak_load
            elif hour < 6 or hour > 22:
                load = base_load * 0.3
            else:
                load = base_load * random.uniform(0.5, 0.8)
            noise = random.gauss(0, load * 0.05)
            pattern.append(round(load + noise, 1))
        self.load_patterns[name] = pattern
        return pattern

    def get_load_at_hour(self, pattern_name: str, hour: int) -> float:
        pattern = self.load_patterns.get(pattern_name, self.load_patterns.get("default", []))
        if not pattern:
            return 0
        return pattern[hour % 24]

    def estimate_energy(self, pattern_name: str, hours: List[int]) -> float:
        total = 0
        for hour in hours:
            total += self.get_load_at_hour(pattern_name, hour)
        return total


class CarbonIntensitySimulator:
    """Simulates carbon intensity data for testing green scheduling."""

    def __init__(self):
        self.base_intensity = 300
        self.daily_pattern: List[float] = []

    def generate_daily_forecast(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        self.daily_pattern = []
        for hour in range(24):
            time_of_day_factor = math.sin((hour - 6) * math.pi / 12)
            base = self.base_intensity + time_of_day_factor * 150
            solar_factor = max(0, math.sin((hour - 7) * math.pi / 10))
            renewable_contribution = solar_factor * 100 + random.uniform(0, 50)
            intensity = max(50, base - renewable_contribution + random.gauss(0, 20))
            self.daily_pattern.append(round(intensity, 1))
        forecast = [
            {"hour": h, "intensity_g_per_kwh": self.daily_pattern[h],
             "renewable_pct": round(random.uniform(20, 80), 1),
             "source": random.choice(["grid", "solar", "wind", "mix"])}
            for h in range(24)
        ]
        return forecast

    def get_best_window(self, duration_hours: int = 2) -> Dict[str, Any]:
        if not self.daily_pattern:
            self.generate_daily_forecast()
        best_start = 0
        lowest_avg = float("inf")
        for start_hour in range(24 - duration_hours + 1):
            window = self.daily_pattern[start_hour:start_hour + duration_hours]
            avg = sum(window) / len(window)
            if avg < lowest_avg:
                lowest_avg = avg
                best_start = start_hour
        return {
            "start_hour": best_start,
            "end_hour": best_start + duration_hours,
            "avg_intensity": round(lowest_avg, 1),
            "savings_vs_peak_pct": round((1 - lowest_avg / max(self.daily_pattern)) * 100, 1)
        }


class EdgeSimulationSuite:
    """Complete simulation suite for Edge & IoT and Green Computing testing."""

    def __init__(self):
        self.sensors = SensorSimulator()
        self.topology = TopologySimulator(num_nodes=15)
        self.load = LoadSimulator()
        self.carbon = CarbonIntensitySimulator()
        self.simulation_running = False

    def initialize(self, num_sensors: int = 20):
        types = ["temperature", "humidity", "pressure", "power", "co2", "vibration", "light", "airflow"]
        for i in range(num_sensors):
            sensor_type = types[i % len(types)]
            self.sensors.add_sensor(
                f"sim-{sensor_type}-{i+1:04d}",
                sensor_type,
                f"DC-1-Rack-{random.choice('ABCDEFGH')}{i % 42 + 1}"
            )
        self.load.create_daily_pattern("default", base_load=50, peak_load=100)
        self.carbon.generate_daily_forecast()

    async def run_simulation(self, duration_seconds: int = 60, interval_seconds: float = 1.0,
                             on_reading: Optional[Callable] = None):
        self.simulation_running = True
        start_time = time.time()
        hours_per_tick = interval_seconds / 3600.0
        elapsed_hours = 0
        tick = 0
        while self.simulation_running and (time.time() - start_time) < duration_seconds:
            tick += 1
            elapsed_hours += hours_per_tick
            readings = self.sensors.read_all(elapsed_hours)
            if on_reading:
                await on_reading(readings, tick)
            if tick % 10 == 0:
                self.topology.simulate_link_failure(0.05)
                self.topology.simulate_node_failure(0.02)
            await asyncio.sleep(interval_seconds)
        self.simulation_running = False

    def stop_simulation(self):
        self.simulation_running = False

    def get_report(self) -> Dict[str, Any]:
        return {
            "sensors": self.sensors.get_stats(),
            "topology": self.topology.get_topology(),
            "carbon_forecast": self.carbon.daily_pattern[:6],
            "load_patterns": {k: v[:6] for k, v in self.load.load_patterns.items()},
        }
