"""Extended OIDC/SAML Identity Provider with federation, token management, and discovery."""
import json
import uuid
import time
import hashlib
import hmac
import base64
import binascii
import logging
import secrets
import urllib.parse
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class GrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICIT = "implicit"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    PASSWORD = "password"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"
    TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
    JWT_BEARER = "urn:ietf:params:oauth:grant-type:jwt-bearer"


class ResponseType(str, Enum):
    CODE = "code"
    TOKEN = "token"
    ID_TOKEN = "id_token"
    CODE_ID_TOKEN = "code id_token"
    CODE_TOKEN = "code token"
    ID_TOKEN_TOKEN = "id_token token"
    NONE = "none"


class TokenTypeHint(str, Enum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"


class SubjectType(str, Enum):
    PUBLIC = "public"
    PAIRWISE = "pairwise"


@dataclass
class OIDCClientRegistration:
    client_id: str
    client_secret: str
    client_id_issued_at: int
    client_secret_expires_at: int
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: str
    client_name: str
    client_uri: Optional[str]
    logo_uri: Optional[str]
    contacts: List[str]
    tos_uri: Optional[str]
    policy_uri: Optional[str]
    jwks_uri: Optional[str]
    software_id: Optional[str]
    software_version: Optional[str]
    scopes: List[str]
    post_logout_redirect_uris: List[str]
    require_auth_time: bool
    default_max_age: Optional[int]
    subject_type: str
    sector_identifier_uri: Optional[str]
    id_token_signed_response_alg: str
    userinfo_signed_response_alg: Optional[str]
    request_object_signing_alg: Optional[str]
    application_type: str
    initiated_login_uri: Optional[str]
    authentication_method_refs: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    enabled: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "client_id_issued_at": self.client_id_issued_at,
            "client_secret_expires_at": self.client_secret_expires_at,
            "redirect_uris": self.redirect_uris,
            "grant_types": self.grant_types,
            "response_types": self.response_types,
            "token_endpoint_auth_method": self.token_endpoint_auth_method,
            "client_name": self.client_name,
            "client_uri": self.client_uri,
            "logo_uri": self.logo_uri,
            "contacts": self.contacts,
            "tos_uri": self.tos_uri,
            "policy_uri": self.policy_uri,
            "jwks_uri": self.jwks_uri,
            "software_id": self.software_id,
            "software_version": self.software_version,
            "scopes": self.scopes,
            "post_logout_redirect_uris": self.post_logout_redirect_uris,
            "require_auth_time": self.require_auth_time,
            "default_max_age": self.default_max_age,
            "subject_type": self.subject_type,
            "sector_identifier_uri": self.sector_identifier_uri,
            "id_token_signed_response_alg": self.id_token_signed_response_alg,
            "userinfo_signed_response_alg": self.userinfo_signed_response_alg,
            "request_object_signing_alg": self.request_object_signing_alg,
            "application_type": self.application_type,
            "initiated_login_uri": self.initiated_login_uri,
            "enabled": self.enabled,
        }


@dataclass
class OIDCToken:
    token_id: str
    token_type: str
    client_id: str
    user_id: Optional[str]
    scopes: List[str]
    claims: Dict[str, Any]
    issued_at: datetime
    expires_at: datetime
    revoked: bool
    replaced_by: Optional[str]
    metadata: Dict[str, Any]

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "token_type": self.token_type,
            "client_id": self.client_id,
            "user_id": self.user_id,
            "scopes": self.scopes,
            "claims": self.claims,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked": self.revoked,
            "replaced_by": self.replaced_by,
        }


@dataclass
class AuthorizationRequest:
    request_id: str
    client_id: str
    redirect_uri: str
    response_type: str
    scopes: List[str]
    state: Optional[str]
    nonce: Optional[str]
    user_id: Optional[str]
    acr_values: Optional[List[str]]
    max_age: Optional[int]
    prompt: Optional[str]
    display: Optional[str]
    login_hint: Optional[str]
    id_token_hint: Optional[str]
    claims_locales: Optional[str]
    request_uri: Optional[str]
    resource: Optional[str]
    code_challenge: Optional[str]
    code_challenge_method: Optional[str]
    authorization_details: Optional[List[Dict[str, Any]]]
    created_at: datetime
    expired: bool
    used: bool

    def is_expired(self) -> bool:
        return self.expired or (datetime.utcnow() - self.created_at).total_seconds() > 600


@dataclass
class DeviceCode:
    device_code: str
    user_code: str
    client_id: str
    scopes: List[str]
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int
    user_id: Optional[str]
    status: str
    created_at: datetime
    last_poll: Optional[datetime]

    def is_expired(self) -> bool:
        return (datetime.utcnow() - self.created_at).total_seconds() > self.expires_in

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_code": self.device_code,
            "user_code": self.user_code,
            "client_id": self.client_id,
            "scopes": self.scopes,
            "verification_uri": self.verification_uri,
            "verification_uri_complete": self.verification_uri_complete,
            "expires_in": self.expires_in,
            "interval": self.interval,
            "user_id": self.user_id,
            "status": self.status,
        }


@dataclass
class SAMLAttribute:
    name: str
    name_format: str
    values: List[str]
    friendly_name: Optional[str]


@dataclass
class SAMLAssertion:
    assertion_id: str
    issuer: str
    subject: str
    subject_format: str
    audience: str
    conditions_not_before: datetime
    conditions_not_on_or_after: datetime
    authn_instant: datetime
    authn_context_class: str
    attributes: List[SAMLAttribute]
    signature: Optional[str]
    session_index: Optional[str]


class TokenRevocationManager:
    def __init__(self):
        self._revoked_tokens: Dict[str, datetime] = {}
        self._revoked_token_hashes: Dict[str, datetime] = {}

    def revoke_token(self, token_id: str, token: str) -> None:
        self._revoked_tokens[token_id] = datetime.utcnow()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self._revoked_token_hashes[token_hash] = datetime.utcnow()

    def is_revoked(self, token_id: str, token: Optional[str] = None) -> bool:
        if token_id in self._revoked_tokens:
            return True
        if token:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if token_hash in self._revoked_token_hashes:
                return True
        return False

    def cleanup_expired(self, retention_hours: int = 72) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
        before = len(self._revoked_tokens)
        self._revoked_tokens = {k: v for k, v in self._revoked_tokens.items() if v > cutoff}
        self._revoked_token_hashes = {k: v for k, v in self._revoked_token_hashes.items() if v > cutoff}
        return before - len(self._revoked_tokens)


class TokenIntrospectionManager:
    def __init__(self):
        self._introspection_log: List[Dict[str, Any]] = []

    def log_introspection(self, client_id: str, token_type: str, token_hash: str, active: bool) -> None:
        self._introspection_log.append({
            "client_id": client_id,
            "token_type": token_type,
            "token_hash": token_hash[:16],
            "active": active,
            "timestamp": datetime.utcnow().isoformat(),
        })
        if len(self._introspection_log) > 10000:
            self._introspection_log = self._introspection_log[-5000:]

    def get_introspection_history(self, client_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        entries = self._introspection_log
        if client_id:
            entries = [e for e in entries if e["client_id"] == client_id]
        return entries[-limit:]


class IdentityProviderManagerExtended:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.issuer = config.get("issuer", "https://auth.infrapilot.local")
        self.access_token_ttl = config.get("oidc", {}).get("access_token_ttl", 3600)
        self.refresh_token_ttl = config.get("oidc", {}).get("refresh_token_ttl", 86400)
        self.id_token_ttl = config.get("oidc", {}).get("id_token_ttl", 3600)
        self.device_code_ttl = config.get("oidc", {}).get("device_code_ttl", 600)
        self.device_code_interval = config.get("oidc", {}).get("device_code_interval", 5)
        self._registrations: Dict[str, OIDCClientRegistration] = {}
        self._auth_requests: Dict[str, AuthorizationRequest] = {}
        self._tokens: Dict[str, OIDCToken] = {}
        self._tokens_by_user: Dict[str, List[str]] = {}
        self._tokens_by_client: Dict[str, List[str]] = {}
        self._saml_assertions: Dict[str, SAMLAssertion] = {}
        self._saml_sp_registrations: Dict[str, Dict[str, Any]] = {}
        self._device_codes: Dict[str, DeviceCode] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._consent_records: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.revocation_manager = TokenRevocationManager()
        self.introspection_manager = TokenIntrospectionManager()
        self._federation_providers: Dict[str, Dict[str, Any]] = {}
        self._claims_mapping: Dict[str, Dict[str, str]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info(f"IdentityProviderManagerExtended initialized at issuer: {self.issuer}")

    async def close(self) -> None:
        self._registrations.clear()
        self._auth_requests.clear()
        self._tokens.clear()
        self._device_codes.clear()
        self._saml_assertions.clear()
        self._consent_records.clear()
        logger.info("IdentityProviderManagerExtended closed")

    def register_client(self, client_name: str, redirect_uris: List[str],
                        grant_types: Optional[List[str]] = None,
                        response_types: Optional[List[str]] = None,
                        scopes: Optional[List[str]] = None,
                        token_endpoint_auth_method: str = "client_secret_basic",
                        application_type: str = "web",
                        contacts: Optional[List[str]] = None,
                        jwks_uri: Optional[str] = None,
                        software_id: Optional[str] = None,
                        post_logout_redirect_uris: Optional[List[str]] = None,
                        subject_type: str = "public",
                        sector_identifier_uri: Optional[str] = None,
                        id_token_signed_response_alg: str = "RS256",
                        require_auth_time: bool = False,
                        default_max_age: Optional[int] = None) -> Dict[str, Any]:
        client_id = str(uuid.uuid4())
        client_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip("=").decode()
        now = int(time.time())
        if grant_types is None:
            grant_types = ["authorization_code", "refresh_token"]
        if response_types is None:
            response_types = ["code"]
        if scopes is None:
            scopes = ["openid", "profile", "email"]
        registration = OIDCClientRegistration(
            client_id=client_id,
            client_secret=client_secret,
            client_id_issued_at=now,
            client_secret_expires_at=0,
            redirect_uris=redirect_uris,
            grant_types=grant_types,
            response_types=response_types,
            token_endpoint_auth_method=token_endpoint_auth_method,
            client_name=client_name,
            client_uri=None,
            logo_uri=None,
            contacts=contacts or [],
            tos_uri=None,
            policy_uri=None,
            jwks_uri=jwks_uri,
            software_id=software_id,
            software_version=None,
            scopes=scopes,
            post_logout_redirect_uris=post_logout_redirect_uris or [],
            require_auth_time=require_auth_time,
            default_max_age=default_max_age,
            subject_type=subject_type,
            sector_identifier_uri=sector_identifier_uri,
            id_token_signed_response_alg=id_token_signed_response_alg,
            userinfo_signed_response_alg=None,
            request_object_signing_alg=None,
            application_type=application_type,
            initiated_login_uri=None,
            authentication_method_refs={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            enabled=True,
        )
        self._registrations[client_id] = registration
        logger.info(f"Registered OIDC client: {client_id} ({client_name})")
        return registration.to_dict()

    def get_client(self, client_id: str) -> Optional[OIDCClientRegistration]:
        return self._registrations.get(client_id)

    def update_client(self, client_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reg = self._registrations.get(client_id)
        if not reg:
            return None
        allowed_fields = {"client_name", "redirect_uris", "grant_types", "response_types",
                          "token_endpoint_auth_method", "contacts", "jwks_uri", "post_logout_redirect_uris",
                          "require_auth_time", "default_max_age", "subject_type", "application_type",
                          "id_token_signed_response_alg", "scopes", "enabled"}
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(reg, key, value)
        reg.updated_at = datetime.utcnow()
        logger.info(f"Updated OIDC client: {client_id}")
        return reg.to_dict()

    def delete_client(self, client_id: str) -> bool:
        if client_id in self._registrations:
            del self._registrations[client_id]
            logger.info(f"Deleted OIDC client: {client_id}")
            return True
        return False

    def list_clients(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        clients = list(self._registrations.values())
        clients.sort(key=lambda c: c.created_at, reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return [c.to_dict() for c in clients[start:end]]

    def authenticate_client(self, client_id: str, client_secret: str) -> bool:
        client = self._registrations.get(client_id)
        if not client or not client.enabled:
            return False
        if client.token_endpoint_auth_method == "none":
            return True
        return client.client_secret == client_secret

    def create_authorization_request(self, client_id: str, redirect_uri: str,
                                     response_type: str, scopes: List[str],
                                     state: Optional[str] = None,
                                     nonce: Optional[str] = None,
                                     code_challenge: Optional[str] = None,
                                     code_challenge_method: Optional[str] = None,
                                     max_age: Optional[int] = None,
                                     prompt: Optional[str] = None,
                                     login_hint: Optional[str] = None,
                                     resource: Optional[str] = None) -> AuthorizationRequest:
        request_id = str(uuid.uuid4())
        auth_req = AuthorizationRequest(
            request_id=request_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scopes=scopes,
            state=state,
            nonce=nonce,
            user_id=None,
            acr_values=None,
            max_age=max_age,
            prompt=prompt,
            display=None,
            login_hint=login_hint,
            id_token_hint=None,
            claims_locales=None,
            request_uri=None,
            resource=resource,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            authorization_details=None,
            created_at=datetime.utcnow(),
            expired=False,
            used=False,
        )
        self._auth_requests[request_id] = auth_req
        return auth_req

    def validate_authorization_request(self, client_id: str, redirect_uri: str,
                                       request_id: str) -> Optional[AuthorizationRequest]:
        req = self._auth_requests.get(request_id)
        if not req or req.client_id != client_id or req.redirect_uri != redirect_uri:
            return None
        if req.is_expired() or req.used:
            return None
        client = self._registrations.get(client_id)
        if not client or not client.enabled:
            return None
        if redirect_uri not in client.redirect_uris:
            return None
        return req

    def approve_authorization_request(self, request_id: str, user_id: str) -> Optional[str]:
        req = self._auth_requests.get(request_id)
        if not req or req.used or req.is_expired():
            return None
        req.user_id = user_id
        if "code" in req.response_type:
            auth_code = self._generate_authorization_code(req.client_id, user_id, req.scopes, req.nonce, req.code_challenge, req.code_challenge_method)
            req.used = True
            return auth_code
        return None

    def _generate_authorization_code(self, client_id: str, user_id: str, scopes: List[str],
                                     nonce: Optional[str] = None,
                                     code_challenge: Optional[str] = None,
                                     code_challenge_method: Optional[str] = None) -> str:
        code = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip("=").decode()
        code_data = {
            "code": code,
            "client_id": client_id,
            "user_id": user_id,
            "scopes": scopes,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "created_at": datetime.utcnow().isoformat(),
            "used": False,
        }
        self._auth_requests[f"code:{code}"] = type("AuthCodeData", (), code_data)()
        return code

    def exchange_authorization_code(self, code: str, client_id: str, redirect_uri: str,
                                    code_verifier: Optional[str] = None) -> Optional[Dict[str, Any]]:
        code_key = f"code:{code}"
        code_data = self._auth_requests.get(code_key)
        if not code_data or code_data.used or code_data.client_id != client_id:
            return None
        if (datetime.utcnow() - datetime.fromisoformat(code_data.created_at)).total_seconds() > 600:
            return None
        if code_data.code_challenge and code_verifier:
            if code_data.code_challenge_method == "S256":
                verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
                expected_challenge = base64.urlsafe_b64encode(verifier_hash).rstrip("=").decode()
                if expected_challenge != code_data.code_challenge:
                    return None
            elif code_verifier != code_data.code_challenge:
                return None
        code_data.used = True
        return self.create_token_pair(client_id, code_data.user_id, code_data.scopes, nonce=code_data.nonce)

    def create_token_pair(self, client_id: str, user_id: str, scopes: List[str],
                          nonce: Optional[str] = None,
                          extra_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        access_token_str = str(uuid.uuid4())
        refresh_token_str = str(uuid.uuid4())
        now = datetime.utcnow()
        access_token = OIDCToken(
            token_id=access_token_str,
            token_type="access_token",
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            claims={"sub": user_id, "client_id": client_id, "scopes": scopes, **(extra_claims or {})},
            issued_at=now,
            expires_at=now + timedelta(seconds=self.access_token_ttl),
            revoked=False,
            replaced_by=None,
            metadata={"source": "authorization_code"},
        )
        refresh_token = OIDCToken(
            token_id=refresh_token_str,
            token_type="refresh_token",
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            claims={"sub": user_id, "client_id": client_id},
            issued_at=now,
            expires_at=now + timedelta(seconds=self.refresh_token_ttl),
            revoked=False,
            replaced_by=None,
            metadata={"source": "authorization_code"},
        )
        self._store_token(access_token)
        self._store_token(refresh_token)
        id_token_claims = {
            "iss": self.issuer,
            "sub": user_id,
            "aud": client_id,
            "exp": int((now + timedelta(seconds=self.id_token_ttl)).timestamp()),
            "iat": int(now.timestamp()),
            "auth_time": int(now.timestamp()),
            "nonce": nonce,
        }
        user = self._users.get(user_id, {})
        if "email" in scopes and user.get("email"):
            id_token_claims["email"] = user["email"]
            id_token_claims["email_verified"] = user.get("email_verified", False)
        if "profile" in scopes:
            if user.get("name"):
                id_token_claims["name"] = user["name"]
            if user.get("preferred_username"):
                id_token_claims["preferred_username"] = user["preferred_username"]
            if user.get("given_name"):
                id_token_claims["given_name"] = user["given_name"]
            if user.get("family_name"):
                id_token_claims["family_name"] = user["family_name"]
            if user.get("locale"):
                id_token_claims["locale"] = user["locale"]
            if user.get("picture"):
                id_token_claims["picture"] = user["picture"]
        if "groups" in scopes and user.get("groups"):
            id_token_claims["groups"] = user["groups"]
        if "roles" in scopes and user.get("roles"):
            id_token_claims["roles"] = user["roles"]
        if "phone" in scopes and user.get("phone_number"):
            id_token_claims["phone_number"] = user["phone_number"]
            id_token_claims["phone_number_verified"] = user.get("phone_verified", False)
        if "address" in scopes and user.get("address"):
            id_token_claims["address"] = user["address"]
        id_token_claims.update(extra_claims or {})
        _id_token = self._sign_jwt(id_token_claims)
        return {
            "access_token": access_token_str,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl,
            "refresh_token": refresh_token_str,
            "id_token": _id_token,
            "scope": " ".join(scopes),
        }

    def _store_token(self, token: OIDCToken) -> None:
        self._tokens[token.token_id] = token
        if token.user_id:
            if token.user_id not in self._tokens_by_user:
                self._tokens_by_user[token.user_id] = []
            self._tokens_by_user[token.user_id].append(token.token_id)
        if token.client_id not in self._tokens_by_client:
            self._tokens_by_client[token.client_id] = []
        self._tokens_by_client[token.client_id].append(token.token_id)

    def validate_access_token(self, token_str: str) -> Optional[OIDCToken]:
        token = self._tokens.get(token_str)
        if not token or token.token_type != "access_token":
            return None
        if not token.is_valid():
            return None
        if self.revocation_manager.is_revoked(token.token_id, token_str):
            return None
        return token

    def validate_refresh_token(self, token_str: str) -> Optional[OIDCToken]:
        token = self._tokens.get(token_str)
        if not token or token.token_type != "refresh_token":
            return None
        if not token.is_valid():
            return None
        if self.revocation_manager.is_revoked(token.token_id, token_str):
            return None
        return token

    def refresh_access_token(self, refresh_token_str: str,
                             client_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        token = self.validate_refresh_token(refresh_token_str)
        if not token:
            return None
        if client_id and token.client_id != client_id:
            return None
        self.revocation_manager.revoke_token(token.token_id, refresh_token_str)
        token.revoked = True
        result = self.create_token_pair(token.client_id, token.user_id, token.scopes)
        return result

    def exchange_token(self, subject_token: str, subject_token_type: str,
                       client_id: str, scopes: Optional[List[str]] = None,
                       resource: Optional[str] = None,
                       actor_token: Optional[str] = None,
                       actor_token_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if subject_token_type == "urn:ietf:params:oauth:token-type:access_token":
            token = self.validate_access_token(subject_token)
            if not token:
                return None
            user_id = token.user_id
            token_scopes = scopes or token.scopes
        elif subject_token_type == "urn:ietf:params:oauth:token-type:jwt":
            user_id = subject_token
            token_scopes = scopes or ["openid"]
        else:
            return None
        return self.create_token_pair(client_id, user_id, token_scopes,
                                      extra_claims={"resource": resource} if resource else None)

    def revoke_token(self, token_str: str, token_type_hint: Optional[str] = None) -> bool:
        token = self._tokens.get(token_str)
        if token:
            self.revocation_manager.revoke_token(token.token_id, token_str)
            token.revoked = True
            logger.info(f"Revoked token: {token.token_id[:16]}...")
            return True
        return False

    def introspect_token(self, token_str: str, client_id: str,
                         token_type_hint: Optional[str] = None) -> Dict[str, Any]:
        token = self._tokens.get(token_str)
        if not token or not token.is_valid():
            self.introspection_manager.log_introspection(client_id, token_type_hint or "unknown",
                                                         hashlib.sha256(token_str.encode()).hexdigest(), False)
            return {"active": False}
        if self.revocation_manager.is_revoked(token.token_id, token_str):
            return {"active": False}
        self.introspection_manager.log_introspection(client_id, token.token_type,
                                                     hashlib.sha256(token_str.encode()).hexdigest(), True)
        result = {
            "active": True,
            "token_type": token.token_type,
            "client_id": token.client_id,
            "sub": token.user_id,
            "scope": " ".join(token.scopes),
            "iss": self.issuer,
            "exp": int(token.expires_at.timestamp()),
            "iat": int(token.issued_at.timestamp()),
        }
        if token.user_id:
            user = self._users.get(token.user_id, {})
            if "name" in user:
                result["name"] = user["name"]
            if "email" in user:
                result["email"] = user["email"]
        return result

    def get_userinfo(self, access_token_str: str) -> Optional[Dict[str, Any]]:
        token = self.validate_access_token(access_token_str)
        if not token or not token.user_id:
            return None
        user = self._users.get(token.user_id, {})
        if not user:
            return None
        userinfo = {"sub": token.user_id}
        scopes = token.scopes
        if "profile" in scopes:
            for field in ["name", "preferred_username", "given_name", "family_name",
                          "middle_name", "nickname", "picture", "website", "gender",
                          "birthdate", "zoneinfo", "locale", "updated_at"]:
                if field in user:
                    userinfo[field] = user[field]
        if "email" in scopes:
            if "email" in user:
                userinfo["email"] = user["email"]
                userinfo["email_verified"] = user.get("email_verified", False)
        if "phone" in scopes:
            if "phone_number" in user:
                userinfo["phone_number"] = user["phone_number"]
                userinfo["phone_number_verified"] = user.get("phone_verified", False)
        if "address" in scopes and "address" in user:
            userinfo["address"] = user["address"]
        if "groups" in scopes and user.get("groups"):
            userinfo["groups"] = user["groups"]
        if "roles" in scopes and user.get("roles"):
            userinfo["roles"] = user["roles"]
        return userinfo

    def create_device_code(self, client_id: str, scopes: List[str]) -> DeviceCode:
        device_code = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip("=").decode()
        user_code = "-".join([secrets.token_hex(3).upper() for _ in range(2)])
        verification_uri = f"{self.issuer}/device"
        verification_uri_complete = f"{verification_uri}?user_code={user_code}"
        dc = DeviceCode(
            device_code=device_code,
            user_code=user_code,
            client_id=client_id,
            scopes=scopes,
            verification_uri=verification_uri,
            verification_uri_complete=verification_uri_complete,
            expires_in=self.device_code_ttl,
            interval=self.device_code_interval,
            user_id=None,
            status="pending",
            created_at=datetime.utcnow(),
            last_poll=None,
        )
        self._device_codes[user_code] = dc
        self._device_codes[device_code] = dc
        return dc

    def poll_device_code(self, user_code: str) -> Dict[str, Any]:
        dc = self._device_codes.get(user_code)
        if not dc or dc.is_expired():
            return {"error": "expired_token", "error_description": "Device code expired"}
        dc.last_poll = datetime.utcnow()
        if dc.status == "approved":
            if not dc.user_id:
                return {"error": "invalid_request", "error_description": "No user associated"}
            result = self.create_token_pair(dc.client_id, dc.user_id, dc.scopes)
            dc.status = "completed"
            return result
        elif dc.status == "denied":
            return {"error": "access_denied", "error_description": "User denied authorization"}
        return {"error": "authorization_pending", "error_description": "Authorization pending"}

    def approve_device_code(self, user_code: str, user_id: str) -> bool:
        dc = self._device_codes.get(user_code)
        if not dc or dc.status != "pending":
            return False
        dc.status = "approved"
        dc.user_id = user_id
        return True

    def deny_device_code(self, user_code: str) -> bool:
        dc = self._device_codes.get(user_code)
        if not dc:
            return False
        dc.status = "denied"
        return True

    def get_authorization_metadata(self, base_url: str) -> Dict[str, Any]:
        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{base_url}/auth/oidc/authorize",
            "token_endpoint": f"{base_url}/auth/oidc/token",
            "userinfo_endpoint": f"{base_url}/auth/oidc/userinfo",
            "end_session_endpoint": f"{base_url}/auth/oidc/logout",
            "jwks_uri": f"{base_url}/auth/oidc/jwks",
            "registration_endpoint": f"{base_url}/auth/oidc/register",
            "introspection_endpoint": f"{base_url}/auth/oidc/introspect",
            "revocation_endpoint": f"{base_url}/auth/oidc/revoke",
            "device_authorization_endpoint": f"{base_url}/auth/oidc/device_authorization",
            "scopes_supported": ["openid", "profile", "email", "address", "phone", "groups", "roles", "offline_access"],
            "response_types_supported": ["code", "id_token", "token id_token", "code id_token", "code token", "code id_token token", "none"],
            "grant_types_supported": ["authorization_code", "implicit", "refresh_token", "client_credentials", "password", "urn:ietf:params:oauth:grant-type:device_code", "urn:ietf:params:oauth:grant-type:token-exchange"],
            "acr_values_supported": ["urn:mace:incommon:iap:silver", "urn:mace:incommon:iap:bronze", "urn:mace:incommon:iap:gold"],
            "subject_types_supported": ["public", "pairwise"],
            "id_token_signing_alg_values_supported": ["RS256", "ES256", "ES384", "ES512"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "client_secret_jwt", "private_key_jwt", "none"],
            "token_endpoint_auth_signing_alg_values_supported": ["RS256", "ES256"],
            "claims_supported": ["sub", "iss", "aud", "exp", "iat", "auth_time", "nonce", "acr", "name", "email", "email_verified", "given_name", "family_name", "phone_number", "address", "groups", "roles", "picture", "locale"],
            "claims_parameter_supported": True,
            "request_parameter_supported": True,
            "request_uri_parameter_supported": True,
            "require_request_uri_registration": False,
            "code_challenge_methods_supported": ["S256", "plain"],
            "ui_locales_supported": ["en-US", "de-DE", "fr-FR", "ja-JP", "zh-CN"],
            "display_values_supported": ["page", "popup", "touch", "wap"],
            "prompt_values_supported": ["none", "login", "consent", "select_account"],
        }

    def client_credentials_grant(self, client_id: str, scopes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        client = self._registrations.get(client_id)
        if not client or not client.enabled:
            return None
        token_scopes = scopes or client.scopes
        access_token_str = str(uuid.uuid4())
        now = datetime.utcnow()
        access_token = OIDCToken(
            token_id=access_token_str,
            token_type="access_token",
            client_id=client_id,
            user_id=None,
            scopes=token_scopes,
            claims={"sub": client_id, "client_id": client_id, "scopes": token_scopes},
            issued_at=now,
            expires_at=now + timedelta(seconds=self.access_token_ttl),
            revoked=False,
            replaced_by=None,
            metadata={"source": "client_credentials"},
        )
        self._store_token(access_token)
        return {
            "access_token": access_token_str,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl,
            "scope": " ".join(token_scopes),
        }

    def password_grant(self, client_id: str, username: str, password: str,
                       scopes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        client = self._registrations.get(client_id)
        if not client or not client.enabled:
            return None
        user = self._authenticate_user(username, password)
        if not user:
            return None
        token_scopes = scopes or client.scopes
        return self.create_token_pair(client_id, user["id"], token_scopes)

    def _authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        for uid, user in self._users.items():
            if user.get("email") == username or user.get("preferred_username") == username:
                stored_hash = user.get("password_hash")
                if stored_hash and self._verify_password(password, stored_hash):
                    return user
        return None

    def add_user(self, user_id: str, claims: Dict[str, Any],
                 password: Optional[str] = None) -> Dict[str, Any]:
        user_data = dict(claims)
        if password:
            user_data["password_hash"] = self._hash_password(password)
        user_data["id"] = user_id
        user_data["created_at"] = datetime.utcnow().isoformat()
        user_data["updated_at"] = datetime.utcnow().isoformat()
        self._users[user_id] = user_data
        return user_data

    def _hash_password(self, password: str) -> str:
        iterations = 310000
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode('ascii')}${base64.b64encode(dk).decode('ascii')}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iter_str, salt_b64, hash_b64 = stored_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            iterations = int(iter_str)
            salt = base64.b64decode(salt_b64.encode("ascii"))
            expected = base64.b64decode(hash_b64.encode("ascii"))
            candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(candidate, expected)
        except (ValueError, TypeError, binascii.Error):
            return False

    def update_user(self, user_id: str, claims: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = self._users.get(user_id)
        if not user:
            return None
        user.update(claims)
        user["updated_at"] = datetime.utcnow().isoformat()
        return user

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    def list_users(self, page: int = 1, page_size: int = 50,
                   filter_by: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        users = list(self._users.values())
        if filter_by:
            for key, value in filter_by.items():
                users = [u for u in users if u.get(key) == value]
        users.sort(key=lambda u: u.get("created_at", ""), reverse=True)
        total = len(users)
        start = (page - 1) * page_size
        end = start + page_size
        safe_users = []
        for u in users[start:end]:
            safe = dict(u)
            safe.pop("password_hash", None)
            safe_users.append(safe)
        return {"users": safe_users, "total": total, "page": page, "page_size": page_size}

    def save_consent(self, user_id: str, client_id: str, scopes: List[str]) -> Dict[str, Any]:
        key = f"{user_id}:{client_id}"
        consent = {
            "user_id": user_id,
            "client_id": client_id,
            "scopes": scopes,
            "granted_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        }
        self._consent_records[key] = consent
        return consent

    def get_consent(self, user_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        key = f"{user_id}:{client_id}"
        consent = self._consent_records.get(key)
        if consent:
            expiry = datetime.fromisoformat(consent["expires_at"])
            if datetime.utcnow() > expiry:
                del self._consent_records[key]
                return None
        return consent

    def revoke_consent(self, user_id: str, client_id: str) -> bool:
        key = f"{user_id}:{client_id}"
        if key in self._consent_records:
            del self._consent_records[key]
            return True
        return False

    def get_user_tokens(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        token_ids = self._tokens_by_user.get(user_id, [])
        tokens = []
        for tid in token_ids:
            token = self._tokens.get(tid)
            if token:
                if active_only and not token.is_valid():
                    continue
                tokens.append(token.to_dict())
        return sorted(tokens, key=lambda t: t["issued_at"], reverse=True)

    def get_client_tokens(self, client_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        token_ids = self._tokens_by_client.get(client_id, [])
        tokens = []
        for tid in token_ids:
            token = self._tokens.get(tid)
            if token:
                if active_only and not token.is_valid():
                    continue
                tokens.append(token.to_dict())
        return sorted(tokens, key=lambda t: t["issued_at"], reverse=True)

    def register_federation_provider(self, provider_name: str, provider_type: str,
                                     config: Dict[str, Any]) -> Dict[str, Any]:
        provider_id = str(uuid.uuid4())
        provider = {
            "provider_id": provider_id,
            "provider_name": provider_name,
            "provider_type": provider_type,
            "config": config,
            "enabled": True,
            "created_at": datetime.utcnow().isoformat(),
            "user_mappings": {},
        }
        self._federation_providers[provider_id] = provider
        return provider

    def get_federation_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        return self._federation_providers.get(provider_id)

    def list_federation_providers(self) -> List[Dict[str, Any]]:
        return list(self._federation_providers.values())

    def delete_federation_provider(self, provider_id: str) -> bool:
        if provider_id in self._federation_providers:
            del self._federation_providers[provider_id]
            return True
        return False

    def federate_identity(self, provider_id: str, external_claims: Dict[str, Any]) -> Optional[str]:
        provider = self._federation_providers.get(provider_id)
        if not provider or not provider.get("enabled"):
            return None
        mapping = provider.get("config", {}).get("claim_mapping", {})
        local_claims = {}
        for local_field, external_field in mapping.items():
            if external_field in external_claims:
                local_claims[local_field] = external_claims[external_field]
        if not local_claims.get("sub") and not local_claims.get("email"):
            return None
        user_id = local_claims.get("sub") or hashlib.sha256(local_claims.get("email", "").encode()).hexdigest()
        self.add_user(user_id, local_claims)
        return user_id

    def set_claims_mapping(self, mapping_name: str, mapping: Dict[str, str]) -> None:
        self._claims_mapping[mapping_name] = mapping

    def apply_claims_mapping(self, mapping_name: str, claims: Dict[str, Any]) -> Dict[str, Any]:
        mapping = self._claims_mapping.get(mapping_name, {})
        result = {}
        for source_field, target_field in mapping.items():
            if source_field in claims:
                result[target_field] = claims[source_field]
        return result

    def register_saml_service_provider(self, entity_id: str, acs_url: str,
                                       metadata_url: str, certificate: Optional[str] = None,
                                       name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                                       attributes: Optional[List[str]] = None,
                                       assertion_ttl: int = 300) -> Dict[str, Any]:
        sp = {
            "entity_id": entity_id,
            "acs_url": acs_url,
            "metadata_url": metadata_url,
            "certificate": certificate,
            "name_id_format": name_id_format,
            "attributes": attributes or ["email", "name", "groups"],
            "assertion_ttl": assertion_ttl,
            "created_at": datetime.utcnow().isoformat(),
            "enabled": True,
        }
        self._saml_sp_registrations[entity_id] = sp
        return sp

    def get_saml_service_provider(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return self._saml_sp_registrations.get(entity_id)

    def list_saml_service_providers(self) -> List[Dict[str, Any]]:
        return list(self._saml_sp_registrations.values())

    def delete_saml_service_provider(self, entity_id: str) -> bool:
        if entity_id in self._saml_sp_registrations:
            del self._saml_sp_registrations[entity_id]
            return True
        return False

    def generate_saml_response_ext(self, user_id: str, sp_entity_id: str,
                                   acs_url: str, in_response_to: Optional[str] = None) -> Dict[str, Any]:
        sp = self._saml_sp_registrations.get(sp_entity_id)
        if not sp:
            raise ValueError(f"Unknown SP: {sp_entity_id}")
        user = self._users.get(user_id, {})
        now = datetime.utcnow()
        assertion_id = f"_assertion_{uuid.uuid4().hex}"
        response_id = f"_response_{uuid.uuid4().hex}"
        attributes = []
        for attr_name in sp.get("attributes", []):
            if attr_name == "email" and user.get("email"):
                attributes.append(SAMLAttribute(name="urn:oid:0.9.2342.19200300.100.1.3",
                                                name_format="urn:oasis:names:tc:SAML:2.0:attrname-format:uri",
                                                values=[user["email"]],
                                                friendly_name="email"))
            elif attr_name == "name" and user.get("name"):
                attributes.append(SAMLAttribute(name="urn:oid:2.16.840.1.113730.3.1.241",
                                                name_format="urn:oasis:names:tc:SAML:2.0:attrname-format:uri",
                                                values=[user["name"]],
                                                friendly_name="displayName"))
            elif attr_name == "groups" and user.get("groups"):
                attributes.append(SAMLAttribute(name="urn:oid:1.3.6.1.4.1.5923.1.5.1.1",
                                                name_format="urn:oasis:names:tc:SAML:2.0:attrname-format:uri",
                                                values=user["groups"],
                                                friendly_name="groups"))
        assertion = SAMLAssertion(
            assertion_id=assertion_id,
            issuer=self.issuer,
            subject=user_id,
            subject_format=sp["name_id_format"],
            audience=sp_entity_id,
            conditions_not_before=now,
            conditions_not_on_or_after=now + timedelta(seconds=sp["assertion_ttl"]),
            authn_instant=now,
            authn_context_class="urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            attributes=attributes,
            signature=None,
            session_index=f"_session_{uuid.uuid4().hex}",
        )
        self._saml_assertions[assertion_id] = assertion
        return {
            "response_id": response_id,
            "in_response_to": in_response_to,
            "issuer": self.issuer,
            "status": "urn:oasis:names:tc:SAML:2.0:status:Success",
            "assertion_id": assertion_id,
            "subject": user_id,
            "subject_format": sp["name_id_format"],
            "audience": sp_entity_id,
            "attributes": [{"name": a.friendly_name or a.name, "values": a.values} for a in attributes],
            "session_index": assertion.session_index,
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=sp["assertion_ttl"])).isoformat(),
        }

    def create_session(self, user_id: str, client_id: str, auth_method: str = "password",
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "client_id": client_id,
            "auth_method": auth_method,
            "ip_address": ip_address or "unknown",
            "user_agent": user_agent or "unknown",
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "expires_at": (now + timedelta(hours=8)).isoformat(),
            "active": True,
        }
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session or not session["active"]:
            return None
        expiry = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() > expiry:
            session["active"] = False
            return None
        return session

    def list_sessions(self, user_id: Optional[str] = None,
                      client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        sessions = list(self._sessions.values())
        if user_id:
            sessions = [s for s in sessions if s["user_id"] == user_id]
        if client_id:
            sessions = [s for s in sessions if s["client_id"] == client_id]
        sessions = [s for s in sessions if s["active"]]
        return sorted(sessions, key=lambda s: s["last_activity"], reverse=True)

    def terminate_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session["active"] = False
        return True

    def _sign_jwt(self, claims: Dict[str, Any]) -> str:
        header = {"alg": "RS256", "typ": "JWT", "kid": "infrapilot-1"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip("=").decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip("=").decode()
        return f"{header_b64}.{payload_b64}.fake_signature"

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_clients": len(self._registrations),
            "total_users": len(self._users),
            "total_tokens": len(self._tokens),
            "active_tokens": sum(1 for t in self._tokens.values() if t.is_valid()),
            "total_saml_sps": len(self._saml_sp_registrations),
            "total_device_codes": len(self._device_codes),
            "total_consents": len(self._consent_records),
            "total_federation_providers": len(self._federation_providers),
            "total_sessions": len(self._sessions),
            "access_token_ttl": self.access_token_ttl,
            "refresh_token_ttl": self.refresh_token_ttl,
            "id_token_ttl": self.id_token_ttl,
        }

    def cleanup_expired(self) -> Dict[str, int]:
        now = datetime.utcnow()
        expired_clients = 0
        expired_tokens = 0
        expired_requests = 0
        for client_id, client in list(self._registrations.items()):
            if client.client_secret_expires_at > 0 and time.time() > client.client_secret_expires_at:
                client.enabled = False
                expired_clients += 1
        for token_id, token in list(self._tokens.items()):
            if token.is_expired():
                del self._tokens[token_id]
                expired_tokens += 1
        for req_id, req in list(self._auth_requests.items()):
            if req.is_expired():
                del self._auth_requests[req_id]
                expired_requests += 1
        revoked_cleaned = self.revocation_manager.cleanup_expired()
        return {
            "expired_clients_disabled": expired_clients,
            "expired_tokens_removed": expired_tokens,
            "expired_requests_removed": expired_requests,
            "revoked_records_cleaned": revoked_cleaned,
        }
