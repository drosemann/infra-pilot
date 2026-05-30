# WebAuthn / Passkey Authentication API Reference

## Overview
WebAuthn allows passwordless authentication using platform authenticators (Touch ID, Windows Hello, YubiKey) and roaming authenticators. The API follows the W3C WebAuthn Level 2 specification.

## Base URL
`/api/v1/identity/webauthn`

## Endpoints

### POST /register/options
Generate registration options for the `navigator.credentials.create()` call.

**Request Body:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| user_id | yes | string | User identifier |
| display_name | no | string | Human-readable display name |
| authenticator_type | no | string | "platform", "cross-platform", or "both" |
| require_resident_key | no | boolean | Require discoverable credential |

**Response:**
```json
{
  "rp": {
    "name": "Infra Pilot",
    "id": "auth.infra-pilot.io"
  },
  "user": {
    "id": "base64userid",
    "name": "user@example.com",
    "displayName": "John Doe"
  },
  "challenge": "base64challenge",
  "pubKeyCredParams": [
    {"type": "public-key", "alg": -7},
    {"type": "public-key", "alg": -257}
  ],
  "timeout": 60000,
  "excludeCredentials": [],
  "authenticatorSelection": {
    "authenticatorAttachment": "platform",
    "residentKey": "preferred",
    "userVerification": "preferred"
  },
  "attestation": "none"
}
```

### POST /register/verify
Verify the authenticator attestation response.

**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| id | yes | Credential ID (base64) |
| rawId | yes | Raw credential ID (base64) |
| response.attestationObject | yes | Attestation object (base64) |
| response.clientDataJSON | yes | Client data (base64 JSON) |
| type | yes | Must be "public-key" |
| clientExtensionResults | no | Extension results |

**Response:**
```json
{
  "verified": true,
  "credential_id": "base64credentialid",
  "device_name": "MacBook Touch ID",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### POST /login/options
Generate authentication options for `navigator.credentials.get()`.

**Request Body:**
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| user_id | yes | string | User identifier |
| mediation | no | string | "conditional", "optional", "required", "silent" |

**Response:**
```json
{
  "challenge": "base64challenge",
  "timeout": 60000,
  "rpId": "auth.infra-pilot.io",
  "allowCredentials": [
    {
      "type": "public-key",
      "id": "base64credentialid",
      "transports": ["internal", "usb", "nfc", "ble"]
    }
  ],
  "userVerification": "preferred"
}
```

### POST /login/verify
Verify the authenticator assertion response.

**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| id | yes | Credential ID (base64) |
| rawId | yes | Raw credential ID |
| response.authenticatorData | yes | Authenticator data (base64) |
| response.clientDataJSON | yes | Client data (base64 JSON) |
| response.signature | yes | Signature (base64) |
| response.userHandle | no | User handle for discoverable credentials |
| type | yes | Must be "public-key" |

### GET /credentials
List all credentials for a user.

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| user_id | yes | User identifier |

### DELETE /credentials/{credential_id}
Remove a WebAuthn credential.

### PUT /credentials/{credential_id}/rename
Rename a credential.

**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| device_name | yes | New device name |

### POST /passkey/register/options
Generate passkey registration options (same as WebAuthn but with residentKey required).

### POST /passkey/register/verify
Verify passkey registration.

### POST /passkey/login/options
Generate passkey login options (conditional UI mediation).

### POST /passkey/login/verify
Verify passkey login.

## Error Codes
| HTTP Status | Error | Description |
|-------------|-------|-------------|
| 400 | invalid_challenge | Challenge expired or invalid |
| 400 | bad_origin | Origin does not match registered origin |
| 400 | bad_assertion | Invalid assertion data |
| 404 | credential_not_found | Credential ID not found |
| 409 | credential_exists | Credential already registered |

## Security Best Practices
1. Always verify the origin matches your application origin
2. Validate the challenge to prevent replay attacks
3. Use attestation verification in high-security environments
4. Implement rate limiting per user for registration and login
5. Store credential public keys securely
6. Monitor for credential cloning via signature counters
7. Support user verification for sensitive operations
8. Implement fallback authentication methods
9. Use conditional mediation for seamless reauthentication
