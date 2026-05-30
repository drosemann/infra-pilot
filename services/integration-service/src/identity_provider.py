import json
import uuid
import time
import hashlib
import base64
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

logger = logging.getLogger(__name__)


class OIDCClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uris: List[str],
                 grant_types: List[str], scopes: List[str], token_endpoint_auth_method: str = "client_secret_basic"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uris = redirect_uris
        self.grant_types = grant_types
        self.scopes = scopes
        self.token_endpoint_auth_method = token_endpoint_auth_method
        self.created_at = datetime.utcnow()
        self.is_confidential = client_secret is not None


class OIDCAuthorizationCode:
    def __init__(self, code: str, client_id: str, redirect_uri: str, scopes: List[str],
                 user_id: str, nonce: Optional[str] = None):
        self.code = code
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.user_id = user_id
        self.nonce = nonce
        self.created_at = datetime.utcnow()
        self.used = False


class OIDCAccessToken:
    def __init__(self, token: str, client_id: str, user_id: str, scopes: List[str],
                 expires_in: int = 3600, token_type: str = "Bearer"):
        self.token = token
        self.client_id = client_id
        self.user_id = user_id
        self.scopes = scopes
        self.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        self.token_type = token_type
        self.created_at = datetime.utcnow()
        self.revoked = False


class OIDCRefreshToken:
    def __init__(self, token: str, client_id: str, user_id: str, scopes: List[str],
                 expires_in: int = 86400):
        self.token = token
        self.client_id = client_id
        self.user_id = user_id
        self.scopes = scopes
        self.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        self.created_at = datetime.utcnow()
        self.used = False


class SAMLServiceProvider:
    def __init__(self, entity_id: str, acs_url: str, metadata_url: str,
                 certificate: Optional[str] = None, name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"):
        self.entity_id = entity_id
        self.acs_url = acs_url
        self.metadata_url = metadata_url
        self.certificate = certificate
        self.name_id_format = name_id_format
        self.created_at = datetime.utcnow()


class IdentityProviderManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.issuer = config.get("issuer", "https://auth.infrapilot.local")
        self.oidc_enabled = config.get("oidc", {}).get("enabled", True)
        self.saml_enabled = config.get("saml", {}).get("enabled", True)
        self.access_token_ttl = config.get("oidc", {}).get("access_token_ttl", 3600)
        self.refresh_token_ttl = config.get("oidc", {}).get("refresh_token_ttl", 86400)
        self.id_token_ttl = config.get("oidc", {}).get("id_token_ttl", 3600)
        self.signing_alg = config.get("oidc", {}).get("signing_alg", "RS256")
        self.saml_entity_id = config.get("saml", {}).get("entity_id", "https://infrapilot.local")
        self.saml_assertion_ttl = config.get("saml", {}).get("assertion_ttl", 300)
        self._clients: Dict[str, OIDCClient] = {}
        self._auth_codes: Dict[str, OIDCAuthorizationCode] = {}
        self._access_tokens: Dict[str, OIDCAccessToken] = {}
        self._refresh_tokens: Dict[str, OIDCRefreshToken] = {}
        self._sp_metadata: Dict[str, SAMLServiceProvider] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._private_key = None
        self._public_key = None
        self._initialized = False

    async def initialize(self) -> None:
        self._generate_keys()
        self._initialized = True
        logger.info(f"IdentityProviderManager initialized at {self.issuer}")

    async def close(self) -> None:
        self._clients.clear()
        self._auth_codes.clear()
        self._access_tokens.clear()
        self._refresh_tokens.clear()
        self._sp_metadata.clear()
        logger.info("IdentityProviderManager closed")

    def _generate_keys(self) -> None:
        self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._public_key = self._private_key.public_key()

    def get_public_key_pem(self) -> str:
        return self._public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()

    def get_private_key_pem(self) -> str:
        return self._private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()

    def get_jwks(self) -> Dict[str, Any]:
        pub_key = self._public_key
        pub_numbers = pub_key.public_numbers()
        n = base64.urlsafe_b64encode(pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, 'big')).rstrip('=').decode()
        e = base64.urlsafe_b64encode(pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, 'big')).rstrip('=').decode()
        return {
            "keys": [{
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "infrapilot-1",
                "n": n,
                "e": e
            }]
        }

    def get_openid_configuration(self, base_url: str) -> Dict[str, Any]:
        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{base_url}/auth/oidc/authorize",
            "token_endpoint": f"{base_url}/auth/oidc/token",
            "userinfo_endpoint": f"{base_url}/auth/oidc/userinfo",
            "jwks_uri": f"{base_url}/auth/oidc/jwks",
            "registration_endpoint": f"{base_url}/auth/oidc/register",
            "scopes_supported": ["openid", "profile", "email", "groups", "offline_access"],
            "response_types_supported": ["code", "id_token", "token id_token", "code id_token", "code token", "code id_token token"],
            "grant_types_supported": ["authorization_code", "implicit", "refresh_token", "client_credentials"],
            "acr_values_supported": ["urn:mace:incommon:iap:silver", "urn:mace:incommon:iap:bronze"],
            "subject_types_supported": ["public", "pairwise"],
            "id_token_signing_alg_values_supported": ["RS256", "ES256"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email", "groups"],
        }

    def register_client(self, redirect_uris: List[str], grant_types: List[str],
                        scopes: List[str], client_name: str) -> Dict[str, Any]:
        client_id = str(uuid.uuid4())
        client_secret = base64.urlsafe_b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).rstrip('=').decode()
        client = OIDCClient(client_id, client_secret, redirect_uris, grant_types, scopes)
        self._clients[client_id] = client
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "grant_types": grant_types,
            "scopes": scopes,
            "token_endpoint_auth_method": "client_secret_basic",
        }

    def authenticate_client(self, client_id: str, client_secret: str) -> bool:
        client = self._clients.get(client_id)
        if not client:
            return False
        return client.client_secret == client_secret

    def get_client(self, client_id: str) -> Optional[OIDCClient]:
        return self._clients.get(client_id)

    def create_authorization_code(self, client_id: str, redirect_uri: str,
                                  scopes: List[str], user_id: str,
                                  nonce: Optional[str] = None) -> str:
        code = base64.urlsafe_b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).rstrip('=').decode()
        auth_code = OIDCAuthorizationCode(code, client_id, redirect_uri, scopes, user_id, nonce)
        self._auth_codes[code] = auth_code
        return code

    def validate_authorization_code(self, code: str, client_id: str, redirect_uri: str) -> Optional[OIDCAuthorizationCode]:
        auth_code = self._auth_codes.get(code)
        if not auth_code or auth_code.used or auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri:
            return None
        code_age = (datetime.utcnow() - auth_code.created_at).total_seconds()
        if code_age > 600:
            return None
        auth_code.used = True
        return auth_code

    def create_token_pair(self, client_id: str, user_id: str, scopes: List[str]) -> Dict[str, Any]:
        access_token = str(uuid.uuid4())
        refresh_token = str(uuid.uuid4())
        at = OIDCAccessToken(access_token, client_id, user_id, scopes, self.access_token_ttl)
        rt = OIDCRefreshToken(refresh_token, client_id, user_id, scopes, self.refresh_token_ttl)
        self._access_tokens[access_token] = at
        self._refresh_tokens[refresh_token] = rt

        id_token_claims = {
            "iss": self.issuer,
            "sub": user_id,
            "aud": client_id,
            "exp": int((datetime.utcnow() + timedelta(seconds=self.id_token_ttl)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "nonce": None,
        }
        user = self._users.get(user_id, {})
        if "email" in scopes and user.get("email"):
            id_token_claims["email"] = user["email"]
        if "profile" in scopes:
            if user.get("name"):
                id_token_claims["name"] = user["name"]
            if user.get("preferred_username"):
                id_token_claims["preferred_username"] = user["preferred_username"]

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl,
            "refresh_token": refresh_token,
            "id_token": self._sign_jwt(id_token_claims),
        }

    def validate_access_token(self, token: str) -> Optional[OIDCAccessToken]:
        at = self._access_tokens.get(token)
        if not at or at.revoked or datetime.utcnow() > at.expires_at:
            return None
        return at

    def revoke_access_token(self, token: str) -> bool:
        at = self._access_tokens.get(token)
        if not at:
            return False
        at.revoked = True
        return True

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        rt = self._refresh_tokens.get(refresh_token)
        if not rt or rt.used or datetime.utcnow() > rt.expires_at:
            return None
        rt.used = True
        return self.create_token_pair(rt.client_id, rt.user_id, rt.scopes)

    def add_user(self, user_id: str, claims: Dict[str, Any]) -> None:
        self._users[user_id] = claims

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def _sign_jwt(self, claims: Dict[str, Any]) -> str:
        header = {"alg": "RS256", "kid": "infrapilot-1", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip('=').decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip('=').decode()
        message = f"{header_b64}.{payload_b64}".encode()
        signature = self._private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip('=').decode()
        return f"{header_b64}.{payload_b64}.{sig_b64}"

    # SAML methods
    def register_service_provider(self, entity_id: str, acs_url: str, metadata_url: str,
                                  certificate: Optional[str] = None) -> SAMLServiceProvider:
        sp = SAMLServiceProvider(entity_id, acs_url, metadata_url, certificate)
        self._sp_metadata[entity_id] = sp
        return sp

    def get_service_provider(self, entity_id: str) -> Optional[SAMLServiceProvider]:
        return self._sp_metadata.get(entity_id)

    def create_saml_assertion(self, user_id: str, sp_entity_id: str) -> str:
        sp = self._sp_metadata.get(sp_entity_id)
        if not sp:
            raise ValueError(f"Unknown SP: {sp_entity_id}")
        now = datetime.utcnow()
        assertion_id = f"_assertion_{uuid.uuid4().hex}"
        assertion = {
            "id": assertion_id,
            "issuer": self.saml_entity_id,
            "issue_instant": now.isoformat(),
            "subject": {
                "name_id": user_id,
                "format": sp.name_id_format,
            },
            "conditions": {
                "not_before": now.isoformat(),
                "not_on_or_after": (now + timedelta(seconds=self.saml_assertion_ttl)).isoformat(),
                "audience_restriction": [sp_entity_id],
            },
            "authn_statement": {
                "authn_instant": now.isoformat(),
                "authn_context_class_ref": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            },
            "attribute_statement": {},
        }
        user = self._users.get(user_id, {})
        if user.get("email"):
            assertion["attribute_statement"]["email"] = user["email"]
        if user.get("name"):
            assertion["attribute_statement"]["name"] = user["name"]
        if user.get("groups"):
            assertion["attribute_statement"]["groups"] = user["groups"]
        return json.dumps(assertion)

    def generate_saml_response(self, user_id: str, sp_entity_id: str, acs_url: str) -> str:
        assertion_json = self.create_saml_assertion(user_id, sp_entity_id)
        assertion_b64 = base64.b64encode(assertion_json.encode()).decode()
        saml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="_response_{uuid.uuid4().hex}"
                Version="2.0"
                IssueInstant="{datetime.utcnow().isoformat()}"
                Destination="{acs_url}">
  <saml:Issuer>{self.saml_entity_id}</saml:Issuer>
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
  </samlp:Status>
  <saml:Assertion>{assertion_b64}</saml:Assertion>
</samlp:Response>"""
        return saml_response

    def generate_saml_metadata(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  entityID="{self.saml_entity_id}">
  <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
        <X509Data>
          <X509Certificate>{base64.b64encode(self.get_public_key_pem().encode()).decode()}</X509Certificate>
        </X509Data>
      </KeyInfo>
    </KeyDescriptor>
    <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                         Location="https://{self.issuer}/auth/saml/sso"/>
    <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                         Location="https://{self.issuer}/auth/saml/slo"/>
  </IDPSSODescriptor>
</EntityDescriptor>"""
