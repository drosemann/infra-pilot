import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OIDCClientType(Enum):
    CONFIDENTIAL = "confidential"
    PUBLIC = "public"

class OIDCClientStatus(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    REVOKED = "revoked"

IDP_PROVIDERS = [
    {"provider_id": "oidc_generic", "name": "Generic OIDC", "protocol": "oidc",
     "description": "Generic OpenID Connect provider", "config_schema": {
         "properties": {
             "issuer_url": {"type": "string", "description": "OIDC issuer URL"},
             "client_id": {"type": "string"}, "client_secret": {"type": "string"},
             "scopes": {"type": "array", "items": {"type": "string"}, "default": ["openid", "profile", "email"]},
         }, "required": ["issuer_url", "client_id", "client_secret"],
     }},
    {"provider_id": "saml_generic", "name": "Generic SAML 2.0", "protocol": "saml",
     "description": "Generic SAML 2.0 Identity Provider", "config_schema": {
         "properties": {
             "entity_id": {"type": "string"}, "sso_url": {"type": "string"},
             "certificate": {"type": "string", "description": "Base64-encoded X.509 cert"},
             "nameid_format": {"type": "string", "enum": ["email", "transient", "persistent", "unspecified"]},
         }, "required": ["entity_id", "sso_url", "certificate"],
     }},
    {"provider_id": "azure_ad", "name": "Azure AD / Entra ID", "protocol": "oidc",
     "description": "Microsoft Entra ID (formerly Azure AD)", "config_schema": {
         "properties": {
             "tenant_id": {"type": "string"}, "client_id": {"type": "string"},
             "client_secret": {"type": "string"},
         }, "required": ["tenant_id", "client_id", "client_secret"],
     }},
    {"provider_id": "okta", "name": "Okta", "protocol": "oidc",
     "description": "Okta identity cloud", "config_schema": {
         "properties": {
             "domain": {"type": "string", "description": "Okta domain (e.g. dev-123.okta.com)"},
             "client_id": {"type": "string"}, "client_secret": {"type": "string"},
         }, "required": ["domain", "client_id", "client_secret"],
     }},
    {"provider_id": "google", "name": "Google Workspace", "protocol": "oidc",
     "description": "Google Workspace / G Suite", "config_schema": {
         "properties": {
             "client_id": {"type": "string"}, "client_secret": {"type": "string"},
         }, "required": ["client_id", "client_secret"],
     }},
    {"provider_id": "keycloak", "name": "Keycloak", "protocol": "oidc",
     "description": "Keycloak identity provider", "config_schema": {
         "properties": {
             "base_url": {"type": "string"}, "realm": {"type": "string"},
             "client_id": {"type": "string"}, "client_secret": {"type": "string"},
         }, "required": ["base_url", "realm", "client_id", "client_secret"],
     }},
]

DATA_FILE = "data/identity_providers.json"


class OIDCClient:
    def __init__(self, client_id: str, client_name: str, client_type: OIDCClientType,
                 redirect_uris: List[str], status: OIDCClientStatus = OIDCClientStatus.ACTIVE,
                 allowed_scopes: Optional[List[str]] = None):
        self.client_id = client_id
        self.client_name = client_name
        self.client_type = client_type
        self.redirect_uris = redirect_uris
        self.status = status
        self.allowed_scopes = allowed_scopes or ["openid", "profile", "email"]
        self.client_secret = uuid.uuid4().hex + uuid.uuid4().hex
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {"client_id": self.client_id, "client_name": self.client_name,
                "client_type": self.client_type.value, "redirect_uris": self.redirect_uris,
                "status": self.status.value, "allowed_scopes": self.allowed_scopes,
                "client_secret": self.client_secret, "created_at": self.created_at,
                "updated_at": self.updated_at}


class IdentityProviderManager:
    def __init__(self):
        self._clients: Dict[str, OIDCClient] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"clients": [], "provider_configs": []}
        for c in data.get("clients", []):
            client = OIDCClient(c["client_id"], c["client_name"],
                                OIDCClientType(c.get("client_type", "confidential")),
                                c["redirect_uris"], OIDCClientStatus(c.get("status", "active")),
                                c.get("allowed_scopes"))
            client.client_secret = c.get("client_secret", client.client_secret)
            client.created_at = c.get("created_at", client.created_at)
            client.updated_at = c.get("updated_at", client.updated_at)
            self._clients[c["client_id"]] = client
        for pc in data.get("provider_configs", []):
            self._provider_configs[pc["provider_id"]] = pc
        self._initialized = True
        logger.info(f"IdentityProviderManager initialized with {len(self._clients)} clients, {len(self._provider_configs)} providers")

    async def close(self):
        await self._save_data()

    async def _save_data(self):
        data = {"clients": [c.to_dict() for c in self._clients.values()],
                "provider_configs": list(self._provider_configs.values())}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def list_providers(self) -> List[Dict[str, Any]]:
        return IDP_PROVIDERS

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        for p in IDP_PROVIDERS:
            if p["provider_id"] == provider_id:
                return p
        return None

    def configure_provider(self, provider_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_id}")
        entry = {"provider_id": provider_id, "name": provider["name"], "config": config,
                 "enabled": True, "configured_at": datetime.utcnow().isoformat()}
        self._provider_configs[provider_id] = entry
        return entry

    def get_configured_providers(self) -> List[Dict[str, Any]]:
        return [p for p in self._provider_configs.values() if p.get("enabled")]

    def remove_provider_config(self, provider_id: str) -> bool:
        if provider_id in self._provider_configs:
            del self._provider_configs[provider_id]
            return True
        return False

    def list_clients(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._clients.values()]

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        c = self._clients.get(client_id)
        return c.to_dict() if c else None

    def register_client(self, client_name: str, redirect_uris: List[str],
                        client_type: str = "confidential",
                        allowed_scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        cid = uuid.uuid4().hex[:16]
        ct = OIDCClientType.CONFIDENTIAL if client_type == "confidential" else OIDCClientType.PUBLIC
        client = OIDCClient(cid, client_name, ct, redirect_uris,
                            allowed_scopes=allowed_scopes)
        self._clients[cid] = client
        return client.to_dict()

    def delete_client(self, client_id: str) -> bool:
        if client_id in self._clients:
            del self._clients[client_id]
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        return {"total_clients": len(self._clients),
                "active_clients": sum(1 for c in self._clients.values() if c.status == OIDCClientStatus.ACTIVE),
                "configured_providers": len(self._provider_configs),
                "supported_providers": len(IDP_PROVIDERS)}

    def get_protocols(self) -> List[Dict[str, Any]]:
        return [{"protocol": "oidc", "name": "OpenID Connect", "version": "1.0",
                 "flows": ["authorization_code", "client_credentials", "refresh_token"]},
                {"protocol": "saml", "name": "Security Assertion Markup Language", "version": "2.0",
                 "bindings": ["http_redirect", "http_post", "http_artifact"]}]
