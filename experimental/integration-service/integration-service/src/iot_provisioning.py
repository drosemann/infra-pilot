"""IoT Device Provisioning API - Zero-touch onboarding integration module."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class IoTProvisioningAPI:
    """API-level integration for IoT device provisioning with certificate management."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.enrolled_devices: dict[str, dict] = {}
        self.pending_enrollments: dict[str, dict] = {}
        self._seed_data()

    def _seed_data(self):
        for i in range(10):
            dev_id = f"enrolled-device-{i:04d}"
            self.enrolled_devices[dev_id] = {
                "device_id": dev_id,
                "name": f"Demo Sensor {i}",
                "certificate_serial": f"IP-{uuid.uuid4().hex[:16].upper()}",
                "enrolled_at": (datetime.utcnow() - timedelta(days=hash(str(i)) % 90)).isoformat(),
                "firmware_version": "2.0.0",
                "status": "active",
                "secure_element": "atecc608a",
            }

    async def initialize(self):
        logger.info("IoTProvisioningAPI initialized")

    async def close(self):
        logger.info("IoTProvisioningAPI closed")

    def create_enrollment(self, device_id: str, csr_pem: str,
                          claim_code: str) -> dict[str, Any]:
        if device_id in self.enrolled_devices:
            return {"success": False, "error": "Device already enrolled"}
        serial = f"IP-{uuid.uuid4().hex[:16].upper()}"
        enrollment = {
            "device_id": device_id,
            "serial": serial,
            "status": "pending",
            "claim_code": claim_code,
            "csr": csr_pem[:50] + "...",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.pending_enrollments[device_id] = enrollment
        return {
            "success": True,
            "serial": serial,
            "status": "pending_approval",
            "enrollment_id": f"enr-{uuid.uuid4().hex[:8]}",
        }

    def approve_enrollment(self, device_id: str) -> dict[str, Any]:
        enrollment = self.pending_enrollments.get(device_id)
        if not enrollment:
            return {"success": False, "error": "No pending enrollment"}
        certificate = {
            "device_id": device_id,
            "serial": enrollment["serial"],
            "certificate_pem": f"-----BEGIN CERTIFICATE-----\nMIIB{enrollment['serial']}\n-----END CERTIFICATE-----",
            "ca_chain_pem": "-----BEGIN CERTIFICATE-----\nMIIBCA==\n-----END CERTIFICATE-----",
            "not_before": datetime.utcnow().isoformat(),
            "not_after": (datetime.utcnow() + timedelta(days=3650)).isoformat(),
        }
        self.enrolled_devices[device_id] = {
            "device_id": device_id,
            "name": device_id,
            "certificate_serial": enrollment["serial"],
            "enrolled_at": datetime.utcnow().isoformat(),
            "firmware_version": "1.0.0",
            "status": "active",
        }
        del self.pending_enrollments[device_id]
        return {"success": True, "certificate": certificate}

    def get_device_certificate(self, device_id: str) -> Optional[dict]:
        device = self.enrolled_devices.get(device_id)
        if not device:
            return None
        return {
            "serial": device["certificate_serial"],
            "device_id": device_id,
            "status": device["status"],
            "enrolled_at": device["enrolled_at"],
        }

    def revoke_device_certificate(self, device_id: str) -> dict[str, Any]:
        device = self.enrolled_devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}
        device["status"] = "revoked"
        return {"success": True, "serial": device["certificate_serial"], "revoked_at": datetime.utcnow().isoformat()}

    def get_device_shadow(self, device_id: str) -> dict[str, Any]:
        return {
            "device_id": device_id,
            "reported": {
                "state": "running",
                "firmware": "2.0.0",
                "temperature": 42.5,
                "humidity": 65.0,
                "last_seen": datetime.utcnow().isoformat(),
            },
            "desired": {
                "target_firmware": "2.1.0",
                "log_level": "debug",
                "sample_interval_seconds": 30,
            },
            "version": 5,
        }

    def update_device_shadow(self, device_id: str, desired: dict) -> dict[str, Any]:
        return {
            "success": True,
            "device_id": device_id,
            "version": 6,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def list_enrolled_devices(self, status: Optional[str] = None) -> list[dict]:
        devices = list(self.enrolled_devices.values())
        if status:
            devices = [d for d in devices if d.get("status") == status]
        return devices

    def get_statistics(self) -> dict[str, Any]:
        total = len(self.enrolled_devices)
        active = sum(1 for d in self.enrolled_devices.values() if d.get("status") == "active")
        revoked = sum(1 for d in self.enrolled_devices.values() if d.get("status") == "revoked")
        return {
            "total_enrolled": total,
            "active_devices": active,
            "revoked_devices": revoked,
            "pending_enrollments": len(self.pending_enrollments),
        }
