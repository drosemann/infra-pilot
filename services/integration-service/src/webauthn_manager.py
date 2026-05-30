import json
import uuid
import base64
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AuthenticatorDevice:
    credential_id: str
    public_key: str
    sign_count: int
    user_id: str
    device_name: str
    authenticator_type: str
    created_at: datetime
    last_used: datetime
    backed_up: bool
    transports: List[str] = field(default_factory=lambda: ["internal", "usb", "nfc", "ble"])


class WebAuthnManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rp_name = config.get("rp_name", "Infra Pilot")
        self.rp_id = config.get("rp_id", "infrapilot.local")
        self.origin = config.get("origin", "https://infrapilot.local")
        self.timeout = config.get("timeout", 60000)
        self.attestation_preference = config.get("attestation_preference", "none")
        self._devices: Dict[str, List[AuthenticatorDevice]] = {}
        self._challenges: Dict[str, Dict[str, Any]] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info(f"WebAuthnManager initialized for RP: {self.rp_id}")

    async def close(self) -> None:
        self._devices.clear()
        self._challenges.clear()
        logger.info("WebAuthnManager closed")

    def add_user(self, user_id: str, name: str, display_name: str) -> None:
        self._users[user_id] = {
            "id": user_id,
            "name": name,
            "display_name": display_name,
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def generate_registration_options(self, user_id: str, user_name: str,
                                      user_display_name: str) -> Dict[str, Any]:
        challenge = base64.urlsafe_b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).rstrip('=').decode()
        user_handle = base64.urlsafe_b64encode(user_id.encode()).rstrip('=').decode()

        self._challenges[challenge] = {
            "user_id": user_id,
            "type": "registration",
            "created_at": datetime.utcnow().isoformat(),
        }

        options = {
            "publicKey": {
                "rp": {"name": self.rp_name, "id": self.rp_id},
                "user": {
                    "id": user_handle,
                    "name": user_name,
                    "displayName": user_display_name,
                },
                "challenge": challenge,
                "pubKeyCredParams": [
                    {"type": "public-key", "alg": -7},
                    {"type": "public-key", "alg": -257},
                    {"type": "public-key", "alg": -8},
                    {"type": "public-key", "alg": -35},
                    {"type": "public-key", "alg": -36},
                    {"type": "public-key", "alg": -258},
                    {"type": "public-key", "alg": -259},
                ],
                "timeout": self.timeout,
                "excludeCredentials": self._get_excluded_credentials(user_id),
                "authenticatorSelection": {
                    "authenticatorAttachment": "platform",
                    "residentKey": "preferred",
                    "userVerification": "preferred",
                },
                "attestation": self.attestation_preference,
                "extensions": {
                    "credProps": True,
                    "hmacCreateSecret": True,
                },
            }
        }
        return options

    def _get_excluded_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        devices = self._devices.get(user_id, [])
        excluded = []
        for dev in devices:
            excluded.append({
                "type": "public-key",
                "id": dev.credential_id,
                "transports": dev.transports,
            })
        return excluded

    def verify_registration(self, user_id: str, challenge: str,
                            credential_id: str, public_key: str,
                            device_name: str, authenticator_type: str,
                            backed_up: bool, sign_count: int) -> bool:
        stored_challenge = self._challenges.get(challenge)
        if not stored_challenge or stored_challenge["user_id"] != user_id:
            logger.warning(f"Invalid challenge for user {user_id}")
            return False
        if stored_challenge["type"] != "registration":
            logger.warning(f"Challenge type mismatch for user {user_id}")
            return False

        device = AuthenticatorDevice(
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            user_id=user_id,
            device_name=device_name,
            authenticator_type=authenticator_type,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            backed_up=backed_up,
        )

        if user_id not in self._devices:
            self._devices[user_id] = []
        self._devices[user_id].append(device)
        del self._challenges[challenge]
        logger.info(f"Registered authenticator '{device_name}' for user {user_id}")
        return True

    def generate_authentication_options(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        challenge = base64.urlsafe_b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).rstrip('=').decode()

        self._challenges[challenge] = {
            "user_id": user_id,
            "type": "authentication",
            "created_at": datetime.utcnow().isoformat(),
        }

        options = {
            "publicKey": {
                "challenge": challenge,
                "timeout": self.timeout,
                "rpId": self.rp_id,
                "allowCredentials": self._get_allowed_credentials(user_id) if user_id else [],
                "userVerification": "preferred",
                "extensions": {
                    "credProps": True,
                },
            }
        }
        return options

    def _get_allowed_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        devices = self._devices.get(user_id, [])
        allowed = []
        for dev in devices:
            allowed.append({
                "type": "public-key",
                "id": dev.credential_id,
                "transports": dev.transports,
            })
        return allowed

    def verify_authentication(self, user_id: str, challenge: str,
                              credential_id: str, sign_count: int) -> bool:
        stored_challenge = self._challenges.get(challenge)
        if not stored_challenge:
            logger.warning(f"Challenge not found")
            return False

        challenge_user_id = stored_challenge["user_id"]
        if challenge_user_id and challenge_user_id != user_id:
            logger.warning(f"User ID mismatch in challenge")
            return False

        if stored_challenge["type"] != "authentication":
            logger.warning(f"Challenge type mismatch")
            return False

        devices = self._devices.get(user_id, [])
        device = None
        for dev in devices:
            if dev.credential_id == credential_id:
                device = dev
                break

        if not device:
            logger.warning(f"Credential {credential_id} not found for user {user_id}")
            return False

        if sign_count > 0 and sign_count <= device.sign_count:
            logger.warning(f"Sign count reuse detected for credential {credential_id}")
            return False

        device.sign_count = max(sign_count, device.sign_count + 1)
        device.last_used = datetime.utcnow()
        del self._challenges[challenge]
        logger.info(f"Authentication verified for user {user_id} with credential {credential_id}")
        return True

    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        devices = self._devices.get(user_id, [])
        return [
            {
                "credential_id": d.credential_id,
                "device_name": d.device_name,
                "authenticator_type": d.authenticator_type,
                "created_at": d.created_at.isoformat(),
                "last_used": d.last_used.isoformat(),
                "backed_up": d.backed_up,
                "transports": d.transports,
                "sign_count": d.sign_count,
            }
            for d in devices
        ]

    def remove_credential(self, user_id: str, credential_id: str) -> bool:
        devices = self._devices.get(user_id, [])
        for i, dev in enumerate(devices):
            if dev.credential_id == credential_id:
                self._devices[user_id].pop(i)
                logger.info(f"Removed credential {credential_id} for user {user_id}")
                return True
        return False

    def get_credential_count(self, user_id: str) -> int:
        return len(self._devices.get(user_id, []))

    def get_statistics(self) -> Dict[str, Any]:
        total_devices = sum(len(devices) for devices in self._devices.values())
        total_users = len(self._devices)
        platform_devices = sum(
            1 for devices in self._devices.values()
            for d in devices if d.authenticator_type == "platform"
        )
        cross_platform_devices = total_devices - platform_devices
        return {
            "total_users_registered": total_users,
            "total_devices": total_devices,
            "platform_devices": platform_devices,
            "cross_platform_devices": cross_platform_devices,
            "backed_up_devices": sum(
                1 for devices in self._devices.values()
                for d in devices if d.backed_up
            ),
        }

    def generate_passkey_registration_qr(self, user_id: str, user_name: str) -> Dict[str, Any]:
        options = self.generate_registration_options(user_id, user_name, user_name)
        qr_payload = json.dumps({
            "type": "passkey_registration",
            "rp_id": self.rp_id,
            "rp_name": self.rp_name,
            "user_id": user_id,
            "user_name": user_name,
            "challenge": options["publicKey"]["challenge"],
        })
        return {
            "qr_payload": qr_payload,
            "options": options,
            "expires_in": self.timeout // 1000,
        }
