"""Extended WebAuthn/Passkey management with FIDO2, attestation, and multi-device support."""
import json
import uuid
import base64
import hashlib
import hmac
import logging
import secrets
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AuthenticatorInfo:
    credential_id: str
    public_key_cose: bytes
    sign_count: int
    user_id: str
    device_name: str
    authenticator_attachment: str
    credential_type: str
    created_at: datetime
    last_used: datetime
    backed_up: bool
    backup_eligible: bool
    transports: List[str]
    aaguid: str
    attestation_type: str
    rp_id: str
    user_handle: str
    user_verified: bool
    uv_initialized: bool
    extensions: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "credential_id": self.credential_id,
            "sign_count": self.sign_count,
            "user_id": self.user_id,
            "device_name": self.device_name,
            "authenticator_attachment": self.authenticator_attachment,
            "credential_type": self.credential_type,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "backed_up": self.backed_up,
            "backup_eligible": self.backup_eligible,
            "transports": self.transports,
            "aaguid": self.aaguid,
            "attestation_type": self.attestation_type,
            "rp_id": self.rp_id,
            "user_verified": self.user_verified,
            "uv_initialized": self.uv_initialized,
            "extensions": self.extensions,
        }


class FIDO2MetadataRegistry:
    AAGUID_METADATA = {
        "00000000-0000-0000-0000-000000000000": {
            "name": "Unknown Authenticator",
            "icon": "unknown",
            "device_type_flags": ["none"],
            "key_protection": ["software"],
            "matcher_protection": ["software"],
            "attestation_types": ["none"],
            "user_verification_methods": ["none"],
            "is_user_present_required": True,
            "is_user_verification_required": False,
        },
        "adce0002-35bc-c60a-648b-0b25f1f05503": {
            "name": "Chrome on Mac",
            "icon": "chrome",
            "device_type_flags": ["internal"],
            "key_protection": ["software", "tpm"],
            "matcher_protection": ["software"],
            "attestation_types": ["none"],
            "user_verification_methods": ["internal"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "089ac58d-8980-46e0-a49d-54a5b3a7f26c": {
            "name": "Windows Hello",
            "icon": "windows_hello",
            "device_type_flags": ["internal"],
            "key_protection": ["tpm"],
            "matcher_protection": ["tpm"],
            "attestation_types": ["platform_attestation"],
            "user_verification_methods": ["fingerprint", "face", "pin"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "6028b017-b1d4-4c02-b4b3-afcdafc96bb2": {
            "name": "Windows Hello Software Authenticator",
            "icon": "windows_hello",
            "device_type_flags": ["internal"],
            "key_protection": ["software"],
            "matcher_protection": ["software"],
            "attestation_types": ["none"],
            "user_verification_methods": ["fingerprint", "face", "pin"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "f3809540-7f14-49c1-8db3-1d2e1f2b9c56": {
            "name": "YubiKey 5 Series",
            "icon": "yubikey",
            "device_type_flags": ["internal", "usb", "nfc"],
            "key_protection": ["hardware", "secure_element"],
            "matcher_protection": ["on_chip"],
            "attestation_types": ["basic", "ecdaa"],
            "user_verification_methods": ["pin"],
            "is_user_present_required": True,
            "is_user_verification_required": False,
        },
        "73bbcd3d-0ae9-4d4d-b7a0-0c7f8a1c7b2a": {
            "name": "YubiKey 5 FIPS Series",
            "icon": "yubikey",
            "device_type_flags": ["internal", "usb", "nfc"],
            "key_protection": ["hardware", "secure_element"],
            "matcher_protection": ["on_chip"],
            "attestation_types": ["basic"],
            "user_verification_methods": ["pin"],
            "is_user_present_required": True,
            "is_user_verification_required": False,
        },
        "ee882879-721c-4d4b-9b0f-9e6c3c6f0b3a": {
            "name": "YubiKey Bio Series",
            "icon": "yubikey",
            "device_type_flags": ["internal", "usb", "nfc"],
            "key_protection": ["hardware", "secure_element"],
            "matcher_protection": ["on_chip"],
            "attestation_types": ["basic"],
            "user_verification_methods": ["fingerprint", "pin"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "12f43a1e-1e3c-4e2a-b0b3-2b8b7e8aa4f0": {
            "name": "Apple Touch ID",
            "icon": "touchid",
            "device_type_flags": ["internal"],
            "key_protection": ["secure_enclave"],
            "matcher_protection": ["on_chip"],
            "attestation_types": ["apple_attestation"],
            "user_verification_methods": ["fingerprint"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "3e078ffd-2c2d-4c5e-8f3a-1f7c9a2e8d4b": {
            "name": "Apple Face ID",
            "icon": "faceid",
            "device_type_flags": ["internal"],
            "key_protection": ["secure_enclave"],
            "matcher_protection": ["on_chip"],
            "attestation_types": ["apple_attestation"],
            "user_verification_methods": ["face"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "952e6d8f-5c6e-4b9a-b3e7-2d8f1a4c7e6b": {
            "name": "Android KeyStore",
            "icon": "android",
            "device_type_flags": ["internal"],
            "key_protection": ["tee", "hardware"],
            "matcher_protection": ["tee"],
            "attestation_types": ["android_key_attestation"],
            "user_verification_methods": ["fingerprint", "face", "pin", "pattern"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "b5397666-7c6e-4d6c-9e8a-1f5c3a7d4e2b": {
            "name": "Android SafetyNet",
            "icon": "android",
            "device_type_flags": ["internal"],
            "key_protection": ["tee"],
            "matcher_protection": ["tee"],
            "attestation_types": ["safetynet"],
            "user_verification_methods": ["fingerprint", "face", "pin"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "7e3f8a1b-2c4d-5e6f-8a9b-0c1d2e3f4a5b": {
            "name": "Google Password Manager",
            "icon": "google",
            "device_type_flags": ["internal"],
            "key_protection": ["software"],
            "matcher_protection": ["software"],
            "attestation_types": ["none"],
            "user_verification_methods": ["screen_lock"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "9f0d6c8b-4a5e-3c7d-2b1a-8e9f0c6d7e5a": {
            "name": "iCloud Keychain",
            "icon": "icloud",
            "device_type_flags": ["internal"],
            "key_protection": ["secure_enclave"],
            "matcher_protection": ["on_chip"],
            "attestation_types": ["none"],
            "user_verification_methods": ["face", "fingerprint", "pin"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
        "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d": {
            "name": "Microsoft Authenticator",
            "icon": "microsoft",
            "device_type_flags": ["internal"],
            "key_protection": ["software", "tee"],
            "matcher_protection": ["software"],
            "attestation_types": ["none"],
            "user_verification_methods": ["biometric", "pin"],
            "is_user_present_required": True,
            "is_user_verification_required": True,
        },
    }

    @staticmethod
    def lookup_aaguid(aaguid: str) -> Dict[str, Any]:
        return FIDO2MetadataRegistry.AAGUID_METADATA.get(
            aaguid, FIDO2MetadataRegistry.AAGUID_METADATA["00000000-0000-0000-0000-000000000000"]
        )

    @staticmethod
    def get_authenticator_brand(aaguid: str) -> str:
        metadata = FIDO2MetadataRegistry.lookup_aaguid(aaguid)
        name = metadata["name"]
        if "YubiKey" in name:
            return "Yubico"
        if "Apple" in name:
            return "Apple"
        if "Windows Hello" in name:
            return "Microsoft"
        if "Android" in name:
            return "Google"
        if "Chrome" in name:
            return "Google"
        if "iCloud" in name:
            return "Apple"
        return "Unknown"


class PasskeyChallengeManager:
    def __init__(self):
        self._challenges: Dict[str, Dict[str, Any]] = {}
        self._cleanup_interval = 300

    def create_challenge(self, user_id: str, challenge_type: str,
                         timeout: int = 60000,
                         extensions: Optional[Dict[str, Any]] = None) -> str:
        challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip("=").decode()
        self._challenges[challenge] = {
            "user_id": user_id,
            "type": challenge_type,
            "timeout": timeout,
            "extensions": extensions or {},
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "max_attempts": 5,
            "consumed": False,
        }
        return challenge

    def validate_challenge(self, challenge: str, user_id: str,
                           expected_type: str) -> bool:
        stored = self._challenges.get(challenge)
        if not stored:
            return False
        if stored["consumed"]:
            return False
        if stored["user_id"] != user_id:
            return False
        if stored["type"] != expected_type:
            return False
        elapsed = (datetime.utcnow() - datetime.fromisoformat(stored["created_at"])).total_seconds() * 1000
        if elapsed > stored["timeout"]:
            return False
        if stored["attempts"] >= stored["max_attempts"]:
            return False
        stored["attempts"] += 1
        return True

    def consume_challenge(self, challenge: str) -> bool:
        stored = self._challenges.get(challenge)
        if not stored:
            return False
        stored["consumed"] = True
        return True

    def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        expired = []
        for ch, data in self._challenges.items():
            elapsed = (now - datetime.fromisoformat(data["created_at"])).total_seconds() * 1000
            if elapsed > data["timeout"] or data["consumed"]:
                expired.append(ch)
        for ch in expired:
            del self._challenges[ch]
        return len(expired)


class WebAuthnManagerExtended:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rp_name = config.get("rp_name", "Infra Pilot")
        self.rp_id = config.get("rp_id", "infrapilot.local")
        self.origin = config.get("origin", "https://infrapilot.local")
        self.timeout = config.get("timeout", 60000)
        self.attestation_preference = config.get("attestation_preference", "none")
        self.user_verification = config.get("user_verification", "preferred")
        self.resident_key = config.get("resident_key", "preferred")
        self._devices: Dict[str, List[AuthenticatorInfo]] = {}
        self._credential_map: Dict[str, str] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._passkey_challenge_mgr = PasskeyChallengeManager()
        self._registration_options_cache: Dict[str, Dict[str, Any]] = {}
        self._authentication_options_cache: Dict[str, Dict[str, Any]] = {}
        self._passkeys: Dict[str, Dict[str, Any]] = {}
        self._fido2_credentials: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info(f"WebAuthnManagerExtended initialized for RP: {self.rp_id}")

    async def close(self) -> None:
        self._devices.clear()
        self._credential_map.clear()
        self._passkeys.clear()
        self._fido2_credentials.clear()
        self._registration_options_cache.clear()
        self._authentication_options_cache.clear()
        logger.info("WebAuthnManagerExtended closed")

    def register_user(self, user_id: str, name: str, display_name: str,
                      icon: Optional[str] = None) -> Dict[str, Any]:
        user = {
            "id": user_id,
            "name": name,
            "display_name": display_name,
            "icon": icon,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "credential_count": 0,
            "passkey_count": 0,
        }
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = self._users.get(user_id)
        if not user:
            return None
        user.update(updates)
        user["updated_at"] = datetime.utcnow().isoformat()
        return user

    def delete_user(self, user_id: str) -> bool:
        if user_id not in self._users:
            return False
        self._devices.pop(user_id, None)
        credential_ids = [cid for cid, uid in self._credential_map.items() if uid == user_id]
        for cid in credential_ids:
            del self._credential_map[cid]
        del self._users[user_id]
        return True

    def list_users(self) -> List[Dict[str, Any]]:
        return list(self._users.values())

    def get_credential_ids_for_user(self, user_id: str) -> List[str]:
        return [info.credential_id for info in self._devices.get(user_id, [])]

    def generate_registration_options_ext(self, user_id: str, user_name: str,
                                          user_display_name: str,
                                          authenticator_attachment: Optional[str] = None,
                                          resident_key: Optional[str] = None,
                                          user_verification: Optional[str] = None,
                                          attestation_preference: Optional[str] = None,
                                          hints: Optional[List[str]] = None,
                                          extensions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip("=").decode()
        user_handle = base64.urlsafe_b64encode(user_id.encode()).rstrip("=").decode()
        self._passkey_challenge_mgr.create_challenge(user_id, "registration", self.timeout)
        pub_key_cred_params = [
            {"type": "public-key", "alg": -7},
            {"type": "public-key", "alg": -257},
            {"type": "public-key", "alg": -8},
            {"type": "public-key", "alg": -35},
            {"type": "public-key", "alg": -36},
            {"type": "public-key", "alg": -258},
            {"type": "public-key", "alg": -259},
            {"type": "public-key", "alg": -37},
            {"type": "public-key", "alg": -38},
            {"type": "public-key", "alg": -39},
            {"type": "public-key", "alg": -65535},
        ]
        authenticator_selection = {
            "residentKey": resident_key or self.resident_key,
            "userVerification": user_verification or self.user_verification,
        }
        if authenticator_attachment:
            authenticator_selection["authenticatorAttachment"] = authenticator_attachment
        options = {
            "publicKey": {
                "rp": {"name": self.rp_name, "id": self.rp_id},
                "user": {
                    "id": user_handle,
                    "name": user_name,
                    "displayName": user_display_name,
                },
                "challenge": challenge,
                "pubKeyCredParams": pub_key_cred_params,
                "timeout": self.timeout,
                "excludeCredentials": self._get_excluded_creds(user_id),
                "authenticatorSelection": authenticator_selection,
                "attestation": attestation_preference or self.attestation_preference,
                "extensions": extensions or {
                    "credProps": True,
                    "hmacCreateSecret": True,
                    "minPinLength": True,
                    "credBlob": True,
                    "largeBlob": {"support": "preferred"},
                    "uvm": True,
                },
            }
        }
        if hints:
            options["publicKey"]["hints"] = hints
        self._registration_options_cache[challenge] = {
            "user_id": user_id,
            "options": options,
            "created_at": datetime.utcnow().isoformat(),
        }
        return options

    def _get_excluded_creds(self, user_id: str) -> List[Dict[str, Any]]:
        devices = self._devices.get(user_id, [])
        return [
            {
                "type": "public-key",
                "id": d.credential_id,
                "transports": d.transports,
            }
            for d in devices
        ]

    def verify_registration_ext(self, user_id: str, challenge: str,
                                credential_id: str, public_key_cose: bytes,
                                device_name: str, authenticator_attachment: str,
                                credential_type: str, backed_up: bool,
                                backup_eligible: bool, sign_count: int,
                                transports: Optional[List[str]] = None,
                                aaguid: Optional[str] = None,
                                attestation_type: Optional[str] = None,
                                user_verified: bool = False,
                                uv_initialized: bool = False,
                                extensions: Optional[Dict[str, Any]] = None) -> bool:
        if not self._passkey_challenge_mgr.validate_challenge(challenge, user_id, "registration"):
            logger.warning(f"Invalid challenge for user {user_id}")
            return False
        cached = self._registration_options_cache.pop(challenge, None)
        if not cached or cached["user_id"] != user_id:
            return False
        aaguid = aaguid or "00000000-0000-0000-0000-000000000000"
        user_handle = base64.urlsafe_b64encode(user_id.encode()).rstrip("=").decode()
        device = AuthenticatorInfo(
            credential_id=credential_id,
            public_key_cose=public_key_cose,
            sign_count=sign_count,
            user_id=user_id,
            device_name=device_name,
            authenticator_attachment=authenticator_attachment or "platform",
            credential_type=credential_type or "public-key",
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            backed_up=backed_up,
            backup_eligible=backup_eligible,
            transports=transports or ["internal"],
            aaguid=aaguid,
            attestation_type=attestation_type or "none",
            rp_id=self.rp_id,
            user_handle=user_handle,
            user_verified=user_verified,
            uv_initialized=uv_initialized,
            extensions=extensions or {},
            metadata=FIDO2MetadataRegistry.lookup_aaguid(aaguid),
        )
        if user_id not in self._devices:
            self._devices[user_id] = []
        self._devices[user_id].append(device)
        self._credential_map[credential_id] = user_id
        self._passkey_challenge_mgr.consume_challenge(challenge)
        if user_id in self._users:
            self._users[user_id]["credential_count"] = len(self._devices[user_id])
        logger.info(f"Registered credential '{device_name}' for user {user_id} (AAGUID: {aaguid})")
        return True

    def generate_authentication_options_ext(self, user_id: Optional[str] = None,
                                            user_verification: Optional[str] = None,
                                            hints: Optional[List[str]] = None,
                                            extensions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip("=").decode()
        self._passkey_challenge_mgr.create_challenge(user_id or "anonymous", "authentication", self.timeout)
        options = {
            "publicKey": {
                "challenge": challenge,
                "timeout": self.timeout,
                "rpId": self.rp_id,
                "allowCredentials": self._get_allowed_creds(user_id) if user_id else [],
                "userVerification": user_verification or self.user_verification,
                "extensions": extensions or {
                    "credProps": True,
                    "uvm": True,
                    "largeBlob": {"read": True},
                },
            }
        }
        if hints:
            options["publicKey"]["hints"] = hints
        self._authentication_options_cache[challenge] = {
            "user_id": user_id,
            "options": options,
            "created_at": datetime.utcnow().isoformat(),
        }
        return options

    def _get_allowed_creds(self, user_id: str) -> List[Dict[str, Any]]:
        devices = self._devices.get(user_id, [])
        return [
            {
                "type": "public-key",
                "id": d.credential_id,
                "transports": d.transports,
            }
            for d in devices
        ]

    def verify_authentication_ext(self, user_id: str, challenge: str,
                                  credential_id: str, sign_count: int,
                                  user_verified: bool = False,
                                  extensions: Optional[Dict[str, Any]] = None) -> bool:
        if not self._passkey_challenge_mgr.validate_challenge(challenge, user_id, "authentication"):
            logger.warning("Invalid authentication challenge")
            return False
        cached = self._authentication_options_cache.pop(challenge, None)
        if not cached:
            return False
        cached_uid = cached["user_id"]
        if cached_uid and cached_uid != user_id:
            return False
        actual_user_id = self._credential_map.get(credential_id)
        if not actual_user_id or actual_user_id != user_id:
            logger.warning(f"Credential {credential_id[:16]}... not owned by user {user_id}")
            return False
        devices = self._devices.get(user_id, [])
        device = None
        for d in devices:
            if d.credential_id == credential_id:
                device = d
                break
        if not device:
            return False
        if sign_count > 0 and sign_count <= device.sign_count:
            logger.warning(f"Sign count reuse for credential {credential_id[:16]}...")
            return False
        device.sign_count = max(sign_count, device.sign_count + 1)
        device.last_used = datetime.utcnow()
        self._passkey_challenge_mgr.consume_challenge(challenge)
        logger.info(f"Authentication verified for user {user_id} with credential {credential_id[:16]}...")
        return True

    def get_user_devices_ext(self, user_id: str) -> List[Dict[str, Any]]:
        devices = self._devices.get(user_id, [])
        result = []
        for d in devices:
            info = d.to_dict()
            info["authenticator_brand"] = FIDO2MetadataRegistry.get_authenticator_brand(d.aaguid)
            info["rp_id"] = d.rp_id
            result.append(info)
        return sorted(result, key=lambda x: x["created_at"], reverse=True)

    def get_all_devices(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        all_devices = []
        for uid, devices in self._devices.items():
            for d in devices:
                info = d.to_dict()
                info["user_id"] = uid
                info["user_name"] = self._users.get(uid, {}).get("name", "unknown")
                info["authenticator_brand"] = FIDO2MetadataRegistry.get_authenticator_brand(d.aaguid)
                all_devices.append(info)
        all_devices.sort(key=lambda x: x["last_used"], reverse=True)
        total = len(all_devices)
        start = (page - 1) * page_size
        end = start + page_size
        return {"devices": all_devices[start:end], "total": total, "page": page, "page_size": page_size}

    def remove_credential_ext(self, user_id: str, credential_id: str) -> bool:
        devices = self._devices.get(user_id, [])
        for i, d in enumerate(devices):
            if d.credential_id == credential_id:
                self._devices[user_id].pop(i)
                self._credential_map.pop(credential_id, None)
                if user_id in self._users:
                    self._users[user_id]["credential_count"] = len(devices) - 1
                logger.info(f"Removed credential {credential_id[:16]}... for user {user_id}")
                return True
        return False

    def get_credential_count(self, user_id: str) -> int:
        return len(self._devices.get(user_id, []))

    def create_passkey_credential(self, user_id: str, rp_id: str,
                                  user_name: str, credential_id: str,
                                  private_key: str, sign_count: int = 0) -> Dict[str, Any]:
        passkey = {
            "credential_id": credential_id,
            "rp_id": rp_id,
            "user_id": user_id,
            "user_name": user_name,
            "private_key": private_key,
            "sign_count": sign_count,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "backed_up": True,
        }
        if user_id not in self._passkeys:
            self._passkeys[user_id] = []
        self._passkeys[user_id].append(passkey)
        if user_id in self._users:
            self._users[user_id]["passkey_count"] = len(self._passkeys[user_id])
        return passkey

    def list_passkeys(self, user_id: str) -> List[Dict[str, Any]]:
        return self._passkeys.get(user_id, [])

    def delete_passkey(self, user_id: str, credential_id: str) -> bool:
        passkeys = self._passkeys.get(user_id, [])
        for i, pk in enumerate(passkeys):
            if pk["credential_id"] == credential_id:
                self._passkeys[user_id].pop(i)
                if user_id in self._users:
                    self._users[user_id]["passkey_count"] = len(passkeys) - 1
                return True
        return False

    def get_passkey_count(self, user_id: str) -> int:
        return len(self._passkeys.get(user_id, []))

    def get_authenticator_metadata(self, aaguid: str) -> Dict[str, Any]:
        return FIDO2MetadataRegistry.lookup_aaguid(aaguid)

    def list_known_authenticators(self) -> List[Dict[str, Any]]:
        result = []
        for aaguid, metadata in FIDO2MetadataRegistry.AAGUID_METADATA.items():
            if aaguid != "00000000-0000-0000-0000-000000000000":
                entry = dict(metadata)
                entry["aaguid"] = aaguid
                result.append(entry)
        return sorted(result, key=lambda x: x["name"])

    def get_statistics_ext(self) -> Dict[str, Any]:
        total_devices = sum(len(devices) for devices in self._devices.values())
        total_users = len(self._devices)
        platform_devices = sum(
            1 for devices in self._devices.values()
            for d in devices if d.authenticator_attachment == "platform"
        )
        cross_platform_devices = total_devices - platform_devices
        passkey_count = sum(len(pks) for pks in self._passkeys.values())
        user_verified_count = sum(
            1 for devices in self._devices.values()
            for d in devices if d.user_verified
        )
        uv_initialized_count = sum(
            1 for devices in self._devices.values()
            for d in devices if d.uv_initialized
        )
        aaguid_stats = {}
        for devices in self._devices.values():
            for d in devices:
                brand = FIDO2MetadataRegistry.get_authenticator_brand(d.aaguid)
                aaguid_stats[brand] = aaguid_stats.get(brand, 0) + 1
        return {
            "total_users_registered": total_users,
            "total_devices": total_devices,
            "platform_devices": platform_devices,
            "cross_platform_devices": cross_platform_devices,
            "backed_up_devices": sum(
                1 for devices in self._devices.values()
                for d in devices if d.backed_up
            ),
            "backup_eligible_devices": sum(
                1 for devices in self._devices.values()
                for d in devices if d.backup_eligible
            ),
            "user_verified_devices": user_verified_count,
            "uv_initialized_devices": uv_initialized_count,
            "total_passkeys": passkey_count,
            "authenticators_by_brand": aaguid_stats,
            "total_users": len(self._users),
            "rp_id": self.rp_id,
        }

    def get_user_verification_methods(self, user_id: str) -> List[str]:
        methods = set()
        devices = self._devices.get(user_id, [])
        for d in devices:
            metadata = FIDO2MetadataRegistry.lookup_aaguid(d.aaguid)
            methods.update(metadata.get("user_verification_methods", []))
        return sorted(methods)

    def check_passkey_supported(self, user_id: str) -> Dict[str, Any]:
        devices = self._devices.get(user_id, [])
        has_platform = any(d.authenticator_attachment == "platform" for d in devices)
        has_uv = any(d.user_verified for d in devices)
        return {
            "passkey_supported": has_platform or has_uv,
            "has_platform_authenticator": has_platform,
            "has_user_verifying_authenticator": has_uv,
            "registered_credentials": len(devices),
            "recommendation": "register" if not devices else "use_existing",
        }

    def generate_passkey_registration_qr_ext(self, user_id: str,
                                              user_name: str) -> Dict[str, Any]:
        options = self.generate_registration_options_ext(user_id, user_name, user_name)
        qr_payload = {
            "type": "passkey_registration",
            "rp_id": self.rp_id,
            "rp_name": self.rp_name,
            "user_id": user_id,
            "user_name": user_name,
            "challenge": options["publicKey"]["challenge"],
            "origin": self.origin,
        }
        return {
            "qr_payload": base64.urlsafe_b64encode(json.dumps(qr_payload).encode()).decode(),
            "options": options,
            "expires_in": self.timeout // 1000,
        }

    def validate_origin(self, origin: str) -> bool:
        allowed_origins = self.config.get("allowed_origins", [self.origin])
        if origin in allowed_origins:
            return True
        for allowed in allowed_origins:
            if allowed.endswith("/*") and origin.startswith(allowed[:-1]):
                return True
        return False

    def validate_rp_id(self, rp_id: str) -> bool:
        allowed_rp_ids = self.config.get("allowed_rp_ids", [self.rp_id])
        return rp_id in allowed_rp_ids

    def export_credentials(self, user_id: str) -> Dict[str, Any]:
        devices = self._devices.get(user_id, [])
        return {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "credentials": [
                {
                    "credential_id": d.credential_id,
                    "device_name": d.device_name,
                    "authenticator_attachment": d.authenticator_attachment,
                    "aaguid": d.aaguid,
                    "created_at": d.created_at.isoformat(),
                    "transports": d.transports,
                }
                for d in devices
            ],
        }

    def import_credentials(self, user_id: str, credentials_data: List[Dict[str, Any]]) -> int:
        imported = 0
        for cred in credentials_data:
            existing = self._devices.get(user_id, [])
            if any(d.credential_id == cred["credential_id"] for d in existing):
                continue
            device = AuthenticatorInfo(
                credential_id=cred["credential_id"],
                public_key_cose=cred.get("public_key_cose", b""),
                sign_count=cred.get("sign_count", 0),
                user_id=user_id,
                device_name=cred.get("device_name", "Imported"),
                authenticator_attachment=cred.get("authenticator_attachment", "cross-platform"),
                credential_type=cred.get("credential_type", "public-key"),
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                backed_up=cred.get("backed_up", False),
                backup_eligible=cred.get("backup_eligible", False),
                transports=cred.get("transports", ["usb"]),
                aaguid=cred.get("aaguid", "00000000-0000-0000-0000-000000000000"),
                attestation_type=cred.get("attestation_type", "none"),
                rp_id=cred.get("rp_id", self.rp_id),
                user_handle=base64.urlsafe_b64encode(user_id.encode()).rstrip("=").decode(),
                user_verified=cred.get("user_verified", False),
                uv_initialized=cred.get("uv_initialized", False),
                extensions=cred.get("extensions", {}),
                metadata=FIDO2MetadataRegistry.lookup_aaguid(cred.get("aaguid", "00000000-0000-0000-0000-000000000000")),
            )
            if user_id not in self._devices:
                self._devices[user_id] = []
            self._devices[user_id].append(device)
            self._credential_map[cred["credential_id"]] = user_id
            imported += 1
        if user_id in self._users:
            self._users[user_id]["credential_count"] = len(self._devices.get(user_id, []))
        return imported

    def cleanup(self) -> Dict[str, int]:
        expired_challenges = self._passkey_challenge_mgr.cleanup_expired()
        return {
            "expired_challenges_removed": expired_challenges,
            "total_users": len(self._users),
            "total_devices": sum(len(d) for d in self._devices.values()),
        }
