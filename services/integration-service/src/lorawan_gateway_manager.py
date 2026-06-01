"""LoRaWAN Gateway Manager - Manage gateways, packet forwarders, channel planning."""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ForwarderType(Enum):
    SEMTECH_UDP = "semtech_udp"
    BASIC_STATION = "basic_station"
    CHIRPSTACK = "chirpstack"
    AWS_IOT = "aws_iot"


class GatewayStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PROVISIONING = "provisioning"


class FrequencyPlan(Enum):
    EU868 = "EU868"
    US915 = "US915"
    AU915 = "AU915"
    AS923 = "AS923"
    CN470 = "CN470"
    KR920 = "KR920"
    IN865 = "IN865"


class LoRaWANGateway:
    """Represents a LoRaWAN gateway."""

    def __init__(self, gateway_id: str, name: str, model: str):
        self.gateway_id = gateway_id
        self.name = name
        self.model = model
        self.concentrator: str = "SX1302"
        self.frequency_plan: FrequencyPlan = FrequencyPlan.EU868
        self.antenna: dict[str, Any] = {
            "type": "omnidirectional",
            "gain_dbi": 5.5,
            "height_meters": 15.0,
        }
        self.location: dict[str, Any] = {
            "latitude": 0.0,
            "longitude": 0.0,
            "altitude_meters": 0.0,
        }
        self.packet_forwarder: dict[str, Any] = {
            "type": ForwarderType.SEMTECH_UDP.value,
            "server_address": "",
            "server_port_up": 1700,
            "server_port_down": 1700,
        }
        self.channels: dict[str, Any] = {
            "enabled": list(range(8)),
            "custom": [],
            "lbt_enabled": False,
        }
        self.status: GatewayStatus = GatewayStatus.PROVISIONING
        self.firmware_version: str = "2.1.0"
        self.last_seen: Optional[datetime] = None
        self.uptime_seconds: int = 0
        self.packets_forwarded: int = 0
        self.packets_received: int = 0
        self.avg_rssi: float = -100.0
        self.avg_snr: float = 5.0
        self.gps_fix: bool = False
        self.temperature_celsius: float = 35.0
        self.tags: list[str] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "gateway_id": self.gateway_id,
            "name": self.name,
            "model": self.model,
            "concentrator": self.concentrator,
            "frequency_plan": self.frequency_plan.value,
            "antenna": self.antenna,
            "location": self.location,
            "packet_forwarder": self.packet_forwarder,
            "channels": self.channels,
            "status": self.status.value,
            "firmware_version": self.firmware_version,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "uptime_seconds": self.uptime_seconds,
            "packets_forwarded": self.packets_forwarded,
            "packets_received": self.packets_received,
            "avg_rssi": self.avg_rssi,
            "avg_snr": self.avg_snr,
            "gps_fix": self.gps_fix,
            "temperature_celsius": self.temperature_celsius,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class GatewayGroup:
    """A group of gateways for load balancing and management."""

    def __init__(self, group_id: str, name: str):
        self.group_id = group_id
        self.name = name
        self.gateway_ids: list[str] = []
        self.description: str = ""
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "name": self.name,
            "gateway_count": len(self.gateway_ids),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


class ChannelPlan:
    """Channel plan recommendation for a region."""

    def __init__(self, plan_id: str, frequency_plan: FrequencyPlan):
        self.plan_id = plan_id
        self.frequency_plan = frequency_plan
        self.channels: list[dict] = []
        self._generate_channels()

    def _generate_channels(self):
        if self.frequency_plan == FrequencyPlan.EU868:
            base_freq = 868.1
            for i in range(8):
                self.channels.append({
                    "index": i,
                    "frequency_mhz": round(base_freq + i * 0.2, 1),
                    "bandwidth_khz": 125,
                    "datarate": "SF7-BW125" if i < 3 else "SF12-BW125",
                    "duty_cycle_pct": 1.0,
                })
        elif self.frequency_plan == FrequencyPlan.US915:
            for i in range(72):
                freq = 902.3 + i * 0.2 if i < 64 else 903.0 + (i - 64) * 0.2
                self.channels.append({
                    "index": i,
                    "frequency_mhz": round(freq, 1),
                    "bandwidth_khz": 125 if i < 64 else 500,
                    "datarate": "SF7-BW125" if i < 64 else "SF12-BW500",
                })
        else:
            for i in range(8):
                self.channels.append({
                    "index": i,
                    "frequency_mhz": round(865.0 + i * 0.2, 1),
                    "bandwidth_khz": 125,
                    "datarate": "SF7-BW125",
                })

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "frequency_plan": self.frequency_plan.value,
            "channels": self.channels,
        }


class LoRaWANGatewayManager:
    """Manager for LoRaWAN gateways."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.gateways: dict[str, LoRaWANGateway] = {}
        self.groups: dict[str, GatewayGroup] = {}
        self.channel_plans: dict[str, ChannelPlan] = {}
        self._seed_data()

    def _seed_data(self):
        demo_gateways = [
            ("gw-001", "factory-floor-gw-1", "RAK7258", 52.52, 13.405,
             ForwarderType.SEMTECH_UDP, FrequencyPlan.EU868),
            ("gw-002", "warehouse-gw-2", "RAK7249", 52.53, 13.410,
             ForwarderType.BASIC_STATION, FrequencyPlan.EU868),
            ("gw-003", "office-building-gw", "Kerlink iBTS", 52.51, 13.400,
             ForwarderType.SEMTECH_UDP, FrequencyPlan.EU868),
            ("gw-004", "outdoor-pole-gw-1", "Multitech Multiconnect", 52.54, 13.415,
             ForwarderType.CHIRPSTACK, FrequencyPlan.EU868),
            ("gw-005", "rooftop-gw-main", "RAK7258", 52.50, 13.395,
             ForwarderType.SEMTECH_UDP, FrequencyPlan.EU868),
        ]
        for gid, name, model, lat, lng, fwd_type, fplan in demo_gateways:
            gw = LoRaWANGateway(gid, name, model)
            gw.location = {"latitude": lat, "longitude": lng, "altitude_meters": 25.0}
            gw.packet_forwarder["type"] = fwd_type.value
            gw.packet_forwarder["server_address"] = "eu1.cloud.thethings.network"
            gw.frequency_plan = fplan
            gw.status = GatewayStatus.ACTIVE
            gw.last_seen = datetime.utcnow() - timedelta(seconds=hash(gid) % 300)
            gw.uptime_seconds = int(86400 * (hash(gid) % 90))
            gw.packets_forwarded = hash(gid) % 100000
            gw.packets_received = hash(gid) % 200000
            gw.avg_rssi = round(-80 - (hash(gid) % 30), 1)
            gw.avg_snr = round(5 + (hash(gid) % 10), 1)
            gw.gps_fix = True
            gw.temperature_celsius = round(30 + (hash(gid) % 15), 1)
            self.gateways[gid] = gw

        self.channel_plans["plan-eu868"] = ChannelPlan("plan-eu868", FrequencyPlan.EU868)
        self.channel_plans["plan-us915"] = ChannelPlan("plan-us915", FrequencyPlan.US915)

    async def initialize(self):
        logger.info("LoRaWANGatewayManager initialized with %d gateways", len(self.gateways))

    async def close(self):
        logger.info("LoRaWANGatewayManager closed")

    def register_gateway(self, name: str, model: str, frequency_plan: str,
                         latitude: float, longitude: float,
                         forwarder_type: str = "semtech_udp") -> LoRaWANGateway:
        gateway_id = f"gw-{uuid.uuid4().hex[:8]}"
        gw = LoRaWANGateway(gateway_id, name, model)
        try:
            gw.frequency_plan = FrequencyPlan(frequency_plan)
        except ValueError:
            gw.frequency_plan = FrequencyPlan.EU868
        gw.location = {"latitude": latitude, "longitude": longitude, "altitude_meters": 0.0}
        gw.packet_forwarder["type"] = forwarder_type
        self.gateways[gateway_id] = gw
        return gw

    def get_gateway(self, gateway_id: str) -> Optional[LoRaWANGateway]:
        return self.gateways.get(gateway_id)

    def list_gateways(self, status: Optional[str] = None,
                      frequency_plan: Optional[str] = None) -> list[LoRaWANGateway]:
        result = list(self.gateways.values())
        if status:
            result = [g for g in result if g.status.value == status]
        if frequency_plan:
            result = [g for g in result if g.frequency_plan.value == frequency_plan]
        return result

    def update_gateway(self, gateway_id: str, updates: dict) -> Optional[LoRaWANGateway]:
        gw = self.gateways.get(gateway_id)
        if not gw:
            return None
        if "location" in updates:
            gw.location.update(updates["location"])
        if "antenna" in updates:
            gw.antenna.update(updates["antenna"])
        if "channels" in updates:
            gw.channels.update(updates["channels"])
        if "packet_forwarder" in updates:
            gw.packet_forwarder.update(updates["packet_forwarder"])
        if "tags" in updates:
            gw.tags = updates["tags"]
        gw.updated_at = datetime.utcnow()
        return gw

    def delete_gateway(self, gateway_id: str) -> bool:
        if gateway_id in self.gateways:
            del self.gateways[gateway_id]
            return True
        return False

    def update_gateway_status(self, gateway_id: str, status: str,
                               metrics: Optional[dict] = None) -> bool:
        gw = self.gateways.get(gateway_id)
        if not gw:
            return False
        try:
            gw.status = GatewayStatus(status)
        except ValueError:
            return False
        gw.last_seen = datetime.utcnow()
        if metrics:
            if "packets_forwarded" in metrics:
                gw.packets_forwarded = metrics["packets_forwarded"]
            if "packets_received" in metrics:
                gw.packets_received = metrics["packets_received"]
            if "avg_rssi" in metrics:
                gw.avg_rssi = metrics["avg_rssi"]
            if "avg_snr" in metrics:
                gw.avg_snr = metrics["avg_snr"]
            if "temperature_celsius" in metrics:
                gw.temperature_celsius = metrics["temperature_celsius"]
            if "gps_fix" in metrics:
                gw.gps_fix = metrics["gps_fix"]
            if "uptime_seconds" in metrics:
                gw.uptime_seconds = metrics["uptime_seconds"]
        return True

    def create_group(self, name: str, description: str = "") -> GatewayGroup:
        group_id = f"grp-{uuid.uuid4().hex[:8]}"
        group = GatewayGroup(group_id, name)
        group.description = description
        self.groups[group_id] = group
        return group

    def add_gateway_to_group(self, group_id: str, gateway_id: str) -> bool:
        group = self.groups.get(group_id)
        if not group or gateway_id not in self.gateways:
            return False
        if gateway_id not in group.gateway_ids:
            group.gateway_ids.append(gateway_id)
        return True

    def list_groups(self) -> list[GatewayGroup]:
        return list(self.groups.values())

    def get_channel_plan(self, frequency_plan: str) -> Optional[ChannelPlan]:
        for plan in self.channel_plans.values():
            if plan.frequency_plan.value == frequency_plan:
                return plan
        return None

    def get_statistics(self) -> dict[str, Any]:
        gateways = list(self.gateways.values())
        total = len(gateways)
        active = sum(1 for g in gateways if g.status == GatewayStatus.ACTIVE)
        total_packets_fwd = sum(g.packets_forwarded for g in gateways)
        total_packets_rcv = sum(g.packets_received for g in gateways)
        avg_rssi = sum(g.avg_rssi for g in gateways) / max(total, 1)
        avg_snr = sum(g.avg_snr for g in gateways) / max(total, 1)
        return {
            "total_gateways": total,
            "active_gateways": active,
            "inactive_gateways": total - active,
            "total_packets_forwarded": total_packets_fwd,
            "total_packets_received": total_packets_rcv,
            "avg_rssi": round(avg_rssi, 1),
            "avg_snr": round(avg_snr, 1),
            "groups_count": len(self.groups),
            "frequency_plans": list(set(g.frequency_plan.value for g in gateways)),
        }
