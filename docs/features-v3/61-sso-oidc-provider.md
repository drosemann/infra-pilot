# Feature 61: SSO/OIDC Provider

## Overview
Built-in OpenID Connect (OIDC) and SAML identity provider for centralized authentication across all Infra Pilot services.

## Components
- `identity_provider.py` - Core OIDC/SAML provider logic
- `oidc_routes.py` - OIDC protocol endpoints (authorization, token, userinfo, jwks)
- `saml_routes.py` - SAML 2.0 protocol endpoints (SSO, SLO, metadata)
- `IdentityProviderManager` - Manager class for identity operations
- `identity_store.py` - Database layer for user/identity storage

## OIDC Endpoints
- `GET /auth/oidc/.well-known/openid-configuration` - Discovery
- `GET /auth/oidc/authorize` - Authorization endpoint
- `POST /auth/oidc/token` - Token endpoint
- `GET /auth/oidc/userinfo` - UserInfo endpoint
- `GET /auth/oidc/jwks` - JWKS endpoint
- `GET /auth/oidc/logout` - RP-initiated logout

## SAML Endpoints
- `GET /auth/saml/metadata` - SP metadata
- `POST /auth/saml/acs` - Assertion Consumer Service
- `GET /auth/saml/sso` - SSO initiation
- `GET /auth/saml/slo` - Single Logout

## Configuration
```yaml
identity_provider:
  issuer: https://auth.infrapilot.local
  oidc:
    enabled: true
    access_token_ttl: 3600
    refresh_token_ttl: 86400
    id_token_ttl: 3600
    signing_alg: RS256
  saml:
    enabled: true
    entity_id: https://infrapilot.local
    assertion_ttl: 300
  storage:
    type: postgresql
    connection_string: postgresql://user:pass@localhost:5432/infrapilot
```

## Client Registration
Clients are registered via the management panel and stored with:
- `client_id` - Unique identifier
- `client_secret` - Secret for confidential clients
- `redirect_uris` - Allowed redirect URIs
- `grant_types` - Allowed grant types
- `scopes` - Requested scopes
- `token_endpoint_auth_method` - client_secret_basic, client_secret_post, none
