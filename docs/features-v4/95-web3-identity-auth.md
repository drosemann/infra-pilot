# Feature 95: Web3 Identity & Authentication

## Overview
Wallet-based authentication using MetaMask, WalletConnect, and other Web3 wallets. Includes SIWE (Sign-In with Ethereum), session management, and token-gated access to infrastructure.

## Capabilities
- Wallet-based authentication (MetaMask, WalletConnect, Coinbase Wallet)
- SIWE (EIP-4361) challenge-response authentication
- Web3 session management with expiry
- Token-gated access rules for infrastructure
- Multi-chain wallet support
- Session revocation and audit logging

## Architecture
1. **Integration Module** (`services/integration-service/src/emerging_tech/web3_auth.py`): Core authentication operations
2. **Orchestrator Cog** (`services/orchestrator-agent/cogs/emerging_tech/web3_auth.py`): Discord commands for Web3 auth
3. **Management Panel** (`services/management-panel/src/pages/emerging-tech/Web3Auth.tsx`): Auth management dashboard
4. **CLI Commands** (`cli/ipilot/commands/emerging_tech/web3_auth.py`): Terminal-based auth operations

## Data Model
- `Web3User`: user_id, wallet_address, chain, provider, label, created_at, last_login
- `SessionToken`: session_id, user_id, token, expires_at, created_at, revoked, ip_address
- `TokenGateRule`: gate_id, name, description, required_tokens, min_balance, chain, allowed_contracts

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/web3/users | List Web3 users |
| POST | /api/v1/web3/register | Register Web3 user |
| POST | /api/v1/web3/siwe/challenge | Generate SIWE challenge |
| POST | /api/v1/web3/siwe/verify | Verify SIWE signature |
| GET | /api/v1/web3/sessions/{id} | List user sessions |
| GET | /api/v1/web3/gates | List token gates |
| POST | /api/v1/web3/gates/check | Check access against gate |

## Security
- SIWE prevents replay attacks via nonces
- Session tokens signed with server-side secret
- Token gates verified on every access
- Rate limiting on SIWE challenge generation
