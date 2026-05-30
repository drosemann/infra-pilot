# Infra Pilot User Guide: Identity & Access Management

## Overview
Infra Pilot provides comprehensive identity and access management including SSO/OIDC, passwordless WebAuthn authentication, session management with device fingerprinting, and just-in-time privileged access.

## Getting Started

### 1. Configure OIDC Provider

The built-in OIDC provider supports the Authorization Code flow for web applications and the Client Credentials flow for service-to-service authentication.

**Step 1: Register a client**
```bash
ipilot oidc register "My Application" "https://app.example.com/callback,https://app.example.com/callback2" --type confidential
```

**Step 2: Configure your application**
Use the returned `client_id` and `client_secret` to configure your application:

```python
# Python example using requests-oauthlib
from requests_oauthlib import OAuth2Session
client = OAuth2Session(client_id, redirect_uri="https://app.example.com/callback")
authorization_url, state = client.authorization_url("https://auth.infra-pilot.io/api/v1/identity/oidc/authorize")
```

**Step 3: Handle the callback**
```python
token = client.fetch_token(
    "https://auth.infra-pilot.io/api/v1/identity/oidc/token",
    authorization_response=request.url,
    client_secret=client_secret
)
```

### 2. Set Up WebAuthn / Passkeys

**Step 1: Register a device**
```bash
# Get registration options for the user
curl -X POST https://api.infra-pilot.io/api/v1/identity/webauthn/register/options \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "display_name": "John Doe"}'
```

**Step 2: Create credential in browser**
```javascript
const options = await response.json();
const credential = await navigator.credentials.create({ publicKey: options });
```

**Step 3: Verify registration**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/identity/webauthn/register/verify \
  -H "Content-Type: application/json" \
  -d '{"id": "...", "response": {"attestationObject": "...", "clientDataJSON": "..."}}'
```

### 3. Manage Sessions

**View active sessions:**
```bash
ipilot session list user-123
```

**Revoke a suspicious session:**
```bash
ipilot session revoke sess_abc123
```

**Configure session policies:**
```yaml
# session_config.yaml
session_ttl: 86400           # 24 hours
max_sessions_per_user: 10    # Max concurrent sessions
anomaly_threshold: 0.7       # Risk score threshold
require_mfa_new_device: true # Require MFA for new devices
geoip_enabled: true          # Enable GeoIP tracking
```

### 4. Request Privileged Access

**Step 1: Create an access request**
```bash
ipilot pam request user-123 prod-db-01 db_admin "Need to fix replication lag" --duration 3600
```

**Step 2: Approve the request (as manager)**
```bash
ipilot pam approve req_abc123 manager-001
```

**Step 3: Activate JIT access**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/identity/pam/requests/req_abc123/jit/activate \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "10.0.0.1"}'
```

**Break-glass emergency access:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/identity/pam/break-glass \
  -H "Content-Type: application/json" \
  -d '{"user_id": "sre-001", "resource": "critical-db-01", "reason": "Production database down"}'
```

### 5. Breach Notification (GDPR)

**Report a breach:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/identity/breaches \
  -H "Content-Type: application/json" \
  -d '{
    "detected_by": "soc-analyst-001",
    "description": "Unauthorized access to customer database",
    "affected_data_types": ["pii", "email", "passwords"],
    "affected_users_count": 5000,
    "suspected_cause": "phishing_attack",
    "systems_affected": ["auth-db-01"]
  }'
```

**Send GDPR notification to authority:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/identity/breaches/br_001234/notify/authority \
  -H "Content-Type: application/json" \
  -d '{
    "authority_name": "DPA Ireland",
    "authority_email": "dpa@dataprotection.ie",
    "notification_body": "We are reporting a personal data breach..."
  }'
```

## Best Practices

### Session Security
1. Always enforce HTTPS
2. Implement device fingerprinting for all sessions
3. Set reasonable session timeouts (24h default)
4. Revoke all sessions on password change
5. Monitor for impossible travel patterns
6. Implement gradual degradation of trust for suspicious sessions

### PAM Security
1. Require business justification for all access requests
2. Implement time-bound access with auto-expiry
3. Enforce the principle of least privilege
4. Record all privileged sessions
5. Set up alerts for break-glass access
6. Regularly audit access request patterns
7. Implement multi-approver for critical systems

### OIDC Configuration
1. Use confidential clients for server-side applications
2. Implement PKCE for mobile and SPA clients
3. Rotate client secrets regularly (90 days)
4. Validate redirect URIs strictly
5. Use the `nonce` parameter for ID tokens
6. Implement token revocation on logout
7. Monitor failed authentication attempts

### WebAuthn Configuration
1. Prefer platform authenticators for better UX
2. Implement conditional mediation for reauthentication
3. Store only credential public keys, never secrets
4. Allow multiple credentials per user
5. Implement account recovery flow
6. Use attestation verification for high-security environments
