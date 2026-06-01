import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CredentialType(Enum):
    FIDO2 = "fido2"
    U2F = "u2f"
    APPLE_APPATTEST = "apple_appattest"
    ANDROID_TEE = "android_tee"
    TPM = "tpm"

class AttestationType(Enum):
    NONE = "none"
    DIRECT = "direct"
    INDIRECT = "indirect"
    AID = "aid"

class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    REVOKED = "revoked"

DATA_FILE = "data/webauthn_credentials.json"

RP_ENTITY = {
    "rp_id": "infra-pilot.local",
    "rp_name": "Infra Pilot Passkey Auth",
    "rp_origin": "https://infra-pilot.local",
}

AAGUID_REGISTRY = {
    "00000000-0000-0000-0000-000000000000": {"name": "Software / Testing", "icon": "default"},
    "adce0002-35bc-c60a-648b-0b25f1f05503": {"name": "Chrome on Mac", "icon": "chrome"},
    "6028b017-b1d4-4c02-b4b3-afcdafc96bb2": {"name": "Windows Hello", "icon": "windows"},
    "ea9b8d66-4d01-1d21-3ce4-b6b48cb575d4": {"name": "YubiKey 5 Series", "icon": "yubico"},
    "12dea12f-5c97-46bc-8d8e-0c2d0b70d242": {"name": "Apple Touch ID", "icon": "apple"},
    "7312f736-26d5-4eaf-87c7-fb8b2d75d2b6": {"name": "Google Pixel 6+ TEE", "icon": "android"},
}

preference_options = {
    "rp": RP_ENTITY,
    "pub_key_cred_params": [
        {"type": "public-key", "alg": -7},
        {"type": "public-key", "alg": -257},
        {"type": "public-key", "alg": -8},
    ],
    "timeout": 60000,
    "attestation": "direct",
    "authenticator_selection": {
        "authenticator_attachment": "platform",
        "resident_key": "required",
        "user_verification": "preferred",
    },
    "hints": ["cross-platform", "security-key", "client-device", "hybrid"],
}


class WebAuthnCredential:
    def __init__(self, credential_id: str, user_id: str, user_name: str,
                 credential_type: CredentialType = CredentialType.FIDO2,
                 aaguid: str = "00000000-0000-0000-0000-000000000000",
                 device_name: Optional[str] = None):
        self.credential_id = credential_id
        self.user_id = user_id
        self.user_name = user_name
        self.credential_type = credential_type
        self.aaguid = aaguid
        self.device_name = device_name or AAGUID_REGISTRY.get(aaguid, {}).get("name", "Unknown Device")
        self.status = VerificationStatus.VERIFIED
        self.created_at = datetime.utcnow().isoformat()
        self.last_used_at = self.created_at
        self.use_count = 0
        self.public_key = f"MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_{uuid.uuid4().hex}"
        self.sign_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"credential_id": self.credential_id, "user_id": self.user_id,
                "user_name": self.user_name, "credential_type": self.credential_type.value,
                "aaguid": self.aaguid, "device_name": self.device_name,
                "status": self.status.value, "created_at": self.created_at,
                "last_used_at": self.last_used_at, "use_count": self.use_count,
                "sign_count": self.sign_count}


class WebAuthnManager:
    def __init__(self):
        self._credentials: Dict[str, WebAuthnCredential] = {}
        self._initialized = False

    async def initialize(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"credentials": []}
        for c in data.get("credentials", []):
            cred = WebAuthnCredential(c["credential_id"], c["user_id"], c["user_name"],
                                      CredentialType(c.get("credential_type", "fido2")),
                                      c.get("aaguid", "00000000-0000-0000-0000-000000000000"))
            cred.status = VerificationStatus(c.get("status", "verified"))
            cred.created_at = c.get("created_at", cred.created_at)
            cred.last_used_at = c.get("last_used_at", cred.last_used_at)
            cred.use_count = c.get("use_count", 0)
            cred.device_name = c.get("device_name", cred.device_name)
            self._credentials[c["credential_id"]] = cred
        self._initialized = True
        logger.info(f"WebAuthnManager initialized with {len(self._credentials)} credentials")

    async def close(self):
        await self._save_data()

    async def _save_data(self):
        data = {"credentials": [c.to_dict() for c in self._credentials.values()]}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_rp_config(self) -> Dict[str, Any]:
        return RP_ENTITY

    def get_preferences(self) -> Dict[str, Any]:
        return preference_options

    def get_aaguids(self) -> Dict[str, Any]:
        return AAGUID_REGISTRY

    def list_credentials(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        creds = self._credentials.values()
        if user_id:
            creds = [c for c in creds if c.user_id == user_id]
        return [c.to_dict() for c in creds]

    def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        c = self._credentials.get(credential_id)
        return c.to_dict() if c else None

    def register_credential(self, user_id: str, user_name: str,
                            credential_type: str = "fido2",
                            aaguid: str = "00000000-0000-0000-0000-000000000000",
                            device_name: Optional[str] = None) -> Dict[str, Any]:
        cid = uuid.uuid4().hex[:24]
        cred = WebAuthnCredential(cid, user_id, user_name,
                                  CredentialType(credential_type), aaguid, device_name)
        self._credentials[cid] = cred
        return cred.to_dict()

    def record_usage(self, credential_id: str) -> bool:
        c = self._credentials.get(credential_id)
        if not c:
            return False
        c.use_count += 1
        c.sign_count += 1
        c.last_used_at = datetime.utcnow().isoformat()
        return True

    def remove_credential(self, credential_id: str) -> bool:
        if credential_id in self._credentials:
            del self._credentials[credential_id]
            return True
        return False

    def revoke_credential(self, credential_id: str) -> bool:
        c = self._credentials.get(credential_id)
        if not c:
            return False
        c.status = VerificationStatus.REVOKED
        return True

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_credentials": len(self._credentials),
                "active_credentials": sum(1 for c in self._credentials.values() if c.status == VerificationStatus.VERIFIED),
                "unique_users": len(set(c.user_id for c in self._credentials.values())),
                "supported_aaguids": len(AAGUID_REGISTRY)}
