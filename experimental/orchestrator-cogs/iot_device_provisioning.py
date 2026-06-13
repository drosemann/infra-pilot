"""IoT Device Provisioning Cog - Zero-touch device onboarding with claim codes and certificates."""

import asyncio
import json
import logging
import re
import secrets
import string
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ProvisioningStatus(Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    ENROLLING = "enrolling"
    ACTIVE = "active"
    FAILED = "failed"
    EXPIRED = "expired"


class SecureElementType(Enum):
    TPM = "tpm"
    ATECC608A = "atecc608a"
    SOFT = "software"


class ClaimCode:
    """Represents a device claim code for zero-touch onboarding."""

    def __init__(self, code: str, batch_id: str):
        self.code = code
        self.batch_id = batch_id
        self.status = ProvisioningStatus.PENDING
        self.device_id: Optional[str] = None
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
        self.claimed_at: Optional[datetime] = None
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "batch_id": self.batch_id,
            "status": self.status.value,
            "device_id": self.device_id,
            "expires_at": self.expires_at.isoformat(),
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "metadata": self.metadata,
        }

    @property
    def is_valid(self) -> bool:
        return (self.status == ProvisioningStatus.PENDING
                and datetime.utcnow() < self.expires_at)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class DeviceCertificate:
    """X.509 certificate for a provisioned IoT device."""

    def __init__(self, serial: str, device_id: str, common_name: str):
        self.serial = serial
        self.device_id = device_id
        self.common_name = common_name
        self.issuer = "Infra Pilot IoT CA"
        self.not_before = datetime.utcnow()
        self.not_after = datetime.utcnow() + timedelta(days=3650)
        self.certificate_pem: str = ""
        self.ca_chain_pem: str = ""
        self.signature_algorithm = "SHA256-ECDSA"
        self.revoked = False
        self.revoked_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "serial": self.serial,
            "device_id": self.device_id,
            "common_name": self.common_name,
            "issuer": self.issuer,
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
            "signature_algorithm": self.signature_algorithm,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }


class DeviceShadow:
    """Device shadow state that synchronizes with the cloud."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.reported: dict[str, Any] = {
            "state": "initializing",
            "firmware_version": "1.0.0",
            "connected": False,
            "last_seen": None,
        }
        self.desired: dict[str, Any] = {
            "target_firmware": "1.0.0",
            "config_version": 1,
            "log_level": "info",
        }
        self.version: int = 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "reported": self.reported,
            "desired": self.desired,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
        }


class DeviceProfile:
    """Provisioning profile for a device model/type."""

    def __init__(self, profile_id: str, name: str, device_type: str):
        self.profile_id = profile_id
        self.name = name
        self.device_type = device_type
        self.default_config: dict[str, Any] = {
            "mqtt_endpoint": "mqtt.infra-pilot.dev:8883",
            "update_interval_seconds": 60,
            "log_level": "info",
            "enable_telemetry": True,
        }
        self.initial_firmware: str = "1.0.0"
        self.certificate_validity_days: int = 3650
        self.claim_code_ttl_hours: int = 24
        self.required_attestation: bool = True
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "device_type": self.device_type,
            "default_config": self.default_config,
            "initial_firmware": self.initial_firmware,
            "certificate_validity_days": self.certificate_validity_days,
            "claim_code_ttl_hours": self.claim_code_ttl_hours,
            "required_attestation": self.required_attestation,
            "metadata": self.metadata,
        }


class IoTDeviceProvisioning:
    """Manager for IoT device provisioning with zero-touch onboarding."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.claim_codes: dict[str, ClaimCode] = {}
        self.certificates: dict[str, DeviceCertificate] = {}
        self.shadows: dict[str, DeviceShadow] = {}
        self.profiles: dict[str, DeviceProfile] = {}
        self._seed_data()

    def _seed_data(self):
        self.profiles["profile-default-iot"] = DeviceProfile(
            "profile-default-iot", "Default IoT Profile", "generic_iot"
        )
        self.profiles["profile-sensor"] = DeviceProfile(
            "profile-sensor", "Sensor Node Profile", "sensor"
        )
        self.profiles["profile-gateway"] = DeviceProfile(
            "profile-gateway", "Gateway Profile", "gateway"
        )
        batch_id = "batch-manufacturing-2026-001"
        for i in range(10):
            code = self._generate_claim_code()
            cc = ClaimCode(code, batch_id)
            self.claim_codes[code] = cc

    def _generate_claim_code(self) -> str:
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace("0", "").replace("O", "").replace("I", "").replace("L", "")
        parts = [
            "IP",
            "".join(secrets.choice(chars) for _ in range(5)),
            "".join(secrets.choice(chars) for _ in range(5)),
            "".join(secrets.choice(chars) for _ in range(5)),
        ]
        return "-".join(parts)

    async def initialize(self):
        logger.info("IoTDeviceProvisioning initialized")

    async def close(self):
        logger.info("IoTDeviceProvisioning closed")

    def generate_claim_codes(self, count: int = 10,
                              ttl_hours: int = 24,
                              batch_id: Optional[str] = None) -> list[ClaimCode]:
        batch = batch_id or f"batch-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        codes = []
        for _ in range(count):
            code_str = self._generate_claim_code()
            cc = ClaimCode(code_str, batch)
            cc.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            self.claim_codes[code_str] = cc
            codes.append(cc)
        logger.info("Generated %d claim codes in batch %s", count, batch)
        return codes

    def validate_claim_code(self, code: str) -> tuple[bool, str]:
        cc = self.claim_codes.get(code)
        if not cc:
            return False, "Invalid claim code"
        if not cc.is_valid:
            if cc.is_expired:
                cc.status = ProvisioningStatus.EXPIRED
                return False, "Claim code has expired"
            return False, f"Claim code status: {cc.status.value}"
        return True, "Claim code is valid"

    def claim_device(self, code: str, device_id: str,
                     hardware_fingerprint: str) -> tuple[bool, str]:
        valid, msg = self.validate_claim_code(code)
        if not valid:
            return False, msg
        cc = self.claim_codes[code]
        cc.status = ProvisioningStatus.CLAIMED
        cc.device_id = device_id
        cc.claimed_at = datetime.utcnow()
        logger.info("Device %s claimed with code %s", device_id, code)
        return True, "Device claimed successfully"

    async def enroll_device(self, device_id: str, csr_pem: str,
                             secure_element: SecureElementType = SecureElementType.SOFT,
                             profile_id: Optional[str] = None) -> Optional[DeviceCertificate]:
        profile = self.profiles.get(profile_id or "profile-default-iot")
        serial = f"IP-{uuid.uuid4().hex[:16].upper()}"
        cert = DeviceCertificate(serial, device_id, f"device-{device_id}")
        cert.certificate_pem = (
            f"-----BEGIN CERTIFICATE-----\n"
            f"MIIB{secrets.token_hex(16)}\n"
            f"{secrets.token_hex(64)}\n"
            f"{secrets.token_hex(64)}\n"
            f"-----END CERTIFICATE-----\n"
        )
        cert.ca_chain_pem = (
            f"-----BEGIN CERTIFICATE-----\n"
            f"MIIB{secrets.token_hex(16)}\n"
            f"-----END CERTIFICATE-----\n"
        )
        self.certificates[serial] = cert
        shadow = DeviceShadow(device_id)
        shadow.reported.update({
            "state": "enrolled",
            "secure_element": secure_element.value,
            "provisioned_at": datetime.utcnow().isoformat(),
        })
        self.shadows[device_id] = shadow
        logger.info("Device %s enrolled with cert %s", device_id, serial)
        return cert

    def get_certificate(self, serial: str) -> Optional[DeviceCertificate]:
        return self.certificates.get(serial)

    def revoke_certificate(self, serial: str) -> bool:
        cert = self.certificates.get(serial)
        if not cert:
            return False
        cert.revoked = True
        cert.revoked_at = datetime.utcnow()
        return True

    def get_shadow(self, device_id: str) -> Optional[DeviceShadow]:
        return self.shadows.get(device_id)

    def update_shadow(self, device_id: str,
                       reported: Optional[dict] = None,
                       desired: Optional[dict] = None) -> Optional[DeviceShadow]:
        shadow = self.shadows.get(device_id)
        if not shadow:
            return None
        if reported:
            shadow.reported.update(reported)
        if desired:
            shadow.desired.update(desired)
        shadow.version += 1
        shadow.updated_at = datetime.utcnow()
        return shadow

    def create_profile(self, name: str, device_type: str,
                       config: Optional[dict] = None) -> DeviceProfile:
        profile_id = f"profile-{uuid.uuid4().hex[:8]}"
        profile = DeviceProfile(profile_id, name, device_type)
        if config:
            profile.default_config.update(config)
        self.profiles[profile_id] = profile
        return profile

    def list_profiles(self) -> list[DeviceProfile]:
        return list(self.profiles.values())

    def get_profile(self, profile_id: str) -> Optional[DeviceProfile]:
        return self.profiles.get(profile_id)

    def list_claim_codes(self, status: Optional[str] = None,
                          batch_id: Optional[str] = None) -> list[ClaimCode]:
        result = list(self.claim_codes.values())
        if status:
            result = [c for c in result if c.status.value == status]
        if batch_id:
            result = [c for c in result if c.batch_id == batch_id]
        return result

    def get_provisioning_summary(self) -> dict[str, Any]:
        total_codes = len(self.claim_codes)
        used_codes = sum(1 for c in self.claim_codes.values()
                         if c.status == ProvisioningStatus.CLAIMED)
        active_devices = len(self.shadows)
        return {
            "total_claim_codes": total_codes,
            "used_codes": used_codes,
            "available_codes": total_codes - used_codes,
            "active_devices": active_devices,
            "active_certificates": sum(1 for c in self.certificates.values() if not c.revoked),
            "profiles": len(self.profiles),
        }


class IoTDeviceProvisioningCog(commands.Cog):
    """Discord cog for IoT device provisioning."""

    def __init__(self, bot):
        self.bot = bot
        self.provisioning = IoTDeviceProvisioning({})

    async def cog_load(self):
        await self.provisioning.initialize()

    async def cog_unload(self):
        await self.provisioning.close()

    @discord.app_commands.command(name="iot_codes", description="Generate claim codes")
    async def iot_codes(self, interaction: discord.Interaction,
                        count: int = 10, ttl_hours: int = 24):
        codes = self.provisioning.generate_claim_codes(count, ttl_hours)
        embed = discord.Embed(
            title=f"Claim Codes Generated ({len(codes)})",
            description=f"TTL: {ttl_hours}h\nBatch: {codes[0].batch_id}",
            color=discord.Color.green()
        )
        code_list = "\n".join(c.code for c in codes[:20])
        embed.add_field(name="Codes", value=f"```\n{code_list}\n```", inline=False)
        embed.set_footer(text=f"Expires: {codes[0].expires_at.strftime('%Y-%m-%d %H:%M UTC')}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="iot_status", description="Get provisioning status")
    async def iot_status(self, interaction: discord.Interaction, code: Optional[str] = None):
        if code:
            valid, msg = self.provisioning.validate_claim_code(code)
            cc = self.provisioning.claim_codes.get(code)
            embed = discord.Embed(title=f"Claim Code: {code}", color=discord.Color.green() if valid else discord.Color.red())
            embed.add_field(name="Status", value=msg, inline=True)
            if cc:
                embed.add_field(name="Batch", value=cc.batch_id, inline=True)
                embed.add_field(name="Expires", value=cc.expires_at.strftime("%Y-%m-%d %H:%M"), inline=True)
                if cc.device_id:
                    embed.add_field(name="Claimed By", value=cc.device_id, inline=True)
                    embed.add_field(name="Claimed At", value=cc.claimed_at.strftime("%Y-%m-%d %H:%M"), inline=True)
        else:
            summary = self.provisioning.get_provisioning_summary()
            embed = discord.Embed(title="Provisioning Summary", color=discord.Color.blue())
            for k, v in summary.items():
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="iot_enroll", description="Enroll a device")
    async def iot_enroll(self, interaction: discord.Interaction,
                         code: str, device_id: str):
        claimed, msg = self.provisioning.claim_device(code, device_id, "simulated-fp")
        if not claimed:
            await interaction.response.send_message(f"Claim failed: {msg}", ephemeral=True)
            return
        cert = await self.provisioning.enroll_device(device_id, "csr-placeholder")
        embed = discord.Embed(title="Device Enrolled", color=discord.Color.green())
        embed.add_field(name="Device ID", value=device_id, inline=True)
        embed.add_field(name="Certificate", value=cert.serial if cert else "N/A", inline=True)
        embed.add_field(name="Valid Until", value=cert.not_after.strftime("%Y-%m-%d") if cert else "N/A", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="iot_profiles", description="List provisioning profiles")
    async def iot_profiles(self, interaction: discord.Interaction):
        profiles = self.provisioning.list_profiles()
        embed = discord.Embed(title="Provisioning Profiles", color=discord.Color.blue())
        for p in profiles:
            embed.add_field(
                name=p.name,
                value=f"Type: {p.device_type}\n"
                     f"Config items: {len(p.default_config)}\n"
                     f"Attestation: {p.required_attestation}",
                inline=True
            )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(IoTDeviceProvisioningCog(bot))
