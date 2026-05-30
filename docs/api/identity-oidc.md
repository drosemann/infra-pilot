# SSO / OIDC Provider API Reference

## Overview
The SSO/OIDC provider implements OpenID Connect Discovery, Authorization Code flow, Client Credentials grant, and SAML 2.0 assertion generation. It supports RS256 signed tokens, dynamic client registration, and token revocation.

## Base URL
`/api/v1/identity/oidc`

## Endpoints

### GET /.well-known/openid-configuration
Returns the OpenID Connect Discovery document.

**Response:**
```json
{
  "issuer": "https://auth.infra-pilot.io",
  "authorization_endpoint": "https://auth.infra-pilot.io/api/v1/identity/oidc/authorize",
  "token_endpoint": "https://auth.infra-pilot.io/api/v1/identity/oidc/token",
  "userinfo_endpoint": "https://auth.infra-pilot.io/api/v1/identity/oidc/userinfo",
  "jwks_uri": "https://auth.infra-pilot.io/api/v1/identity/oidc/jwks",
  "registration_endpoint": "https://auth.infra-pilot.io/api/v1/identity/oidc/register",
  "scopes_supported": ["openid", "profile", "email", "offline_access"],
  "response_types_supported": ["code", "token", "id_token"],
  "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email", "picture"]
}
```

### POST /clients
Register a new OIDC client.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| client_name | string | yes | Human-readable client name |
| redirect_uris | string[] | yes | Allowed redirect URIs |
| grant_types | string[] | no | Default: ["authorization_code"] |
| client_type | string | no | "confidential" (default) or "public" |
| post_logout_redirect_uris | string[] | no | Post-logout redirect URIs |

### GET /clients
List all registered OIDC clients.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| per_page | int | Items per page (default: 20) |

### GET /clients/{client_id}
Get details of a specific OIDC client.

### DELETE /clients/{client_id}
Delete an OIDC client registration.

### POST /clients/{client_id}/rotate-secret
Rotate the client secret. Optionally expire the old secret immediately.

**Request Body:**
| Field | Type | Description |
|-------|------|-------------|
| expire_old | boolean | Immediately expire old secret (default: false) |

### GET /authorize
Authorization endpoint for the OIDC Authorization Code flow.

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| client_id | yes | Client identifier |
| redirect_uri | yes | Must match registered URI |
| response_type | yes | Must be "code" |
| scope | yes | Space-separated scope values |
| state | no | Opaque state value for CSRF protection |
| nonce | no | Nonce for id_token |

### POST /token
Token endpoint for exchanging authorization codes and refreshing tokens.

**Request Body (code exchange):**
| Field | Required | Description |
|-------|----------|-------------|
| grant_type | yes | "authorization_code" |
| code | yes | Authorization code |
| client_id | yes | Client identifier |
| client_secret | conditional | Required for confidential clients |
| redirect_uri | yes | Must match original |

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def456...",
  "id_token": "eyJhbGci..."
}
```

### POST /token (refresh)
**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| grant_type | yes | "refresh_token" |
| refresh_token | yes | Refresh token |
| client_id | yes | Client identifier |
| client_secret | conditional | Required for confidential clients |

### POST /token (client_credentials)
**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| grant_type | yes | "client_credentials" |
| client_id | yes | Client identifier |
| client_secret | yes | Client secret |
| scope | no | Requested scopes |

### POST /revoke
Revoke a token (access or refresh).

**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| token | yes | The token to revoke |
| token_type_hint | no | "access_token" or "refresh_token" |
| client_id | yes | Client identifier |
| client_secret | conditional | Required for confidential clients |

### GET /userinfo
Get user claims based on the access token.

**Headers:** Authorization: Bearer <access_token>

**Response:**
```json
{
  "sub": "user-123",
  "name": "John Doe",
  "email": "john@example.com",
  "picture": "https://auth.example.com/avatars/123.png"
}
```

### POST /saml/assertion
Generate a SAML 2.0 assertion for service provider integration.

**Request Body:**
| Field | Required | Description |
|-------|----------|-------------|
| user_id | yes | The user to authenticate |
| issuer | yes | SAML issuer entity ID |
| audience | yes | Service provider ACS URL |

## Token Claims

### ID Token Claims
| Claim | Description |
|-------|-------------|
| sub | Subject identifier (user ID) |
| iss | Issuer URL |
| aud | Audience (client_id) |
| exp | Expiration timestamp |
| iat | Issued-at timestamp |
| auth_time | Authentication timestamp |
| nonce | Nonce value if provided |
| azp | Authorized party |

### Access Token Claims
| Claim | Description |
|-------|-------------|
| sub | Subject identifier |
| iss | Issuer URL |
| aud | Audience (client_id or API identifier) |
| exp | Expiration timestamp |
| iat | Issued-at timestamp |
| scope | Granted scopes |
| client_id | Client identifier |

## Error Codes
| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | invalid_request | Missing or invalid parameters |
| 401 | invalid_client | Client authentication failed |
| 401 | invalid_token | Token is expired or invalid |
| 403 | insufficient_scope | Token lacks required scopes |
| 404 | not_found | Resource not found |
| 409 | conflict | Resource already exists |
| 429 | rate_limited | Too many requests |

## Security Considerations
1. Always use HTTPS in production
2. Rotate client secrets periodically
3. Set appropriate token TTLs (default: 3600s for access, 86400s for refresh)
4. Validate redirect URIs strictly against registered values
5. Use PKCE for public clients (mobile/SPA)
6. Monitor failed authentication attempts
7. Implement rate limiting on token endpoints
8. Store client secrets using strong hashing
9. Use the nonce parameter to prevent replay attacks
10. Validate all cryptographic signatures using JWKS
