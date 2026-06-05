# Feature 62: Passkey/WebAuthn Authentication

## Overview
Passwordless authentication using WebAuthn standard, supporting platform authenticators (fingerprint, Face ID, Windows Hello) and roaming authenticators (YubiKey, security keys).

## Components
- `webauthn_manager.py` - Core WebAuthn logic
- `authenticator_store.py` - Authenticator device storage
- `passkey_routes.py` - API endpoints for registration and authentication
- Mobile: `biometric-auth.ts` - React Native biometric integration

## Registration Flow
1. User initiates passkey registration
2. Server generates registration options (challenge, RP info)
3. Client creates credential via WebAuthn API
4. Client sends public key and credential ID to server
5. Server stores credential associated with user account

## Authentication Flow
1. User initiates passkey login
2. Server generates authentication options
3. Client signs challenge with private key
4. Server verifies signature using stored public key
5. Session is created upon successful verification

## API Endpoints
- `POST /auth/webauthn/register/begin` - Start registration
- `POST /auth/webauthn/register/complete` - Complete registration
- `POST /auth/webauthn/login/begin` - Start authentication
- `POST /auth/webauthn/login/complete` - Complete authentication
- `GET /auth/webauthn/credentials` - List registered credentials
- `DELETE /auth/webauthn/credentials/{id}` - Remove credential

## Supported Authenticator Types
- Platform: Windows Hello, Apple Touch ID/Face ID, Android biometric
- Cross-platform: YubiKey, Google Titan, SoloKey
- Phone-as-passkey via QR code
