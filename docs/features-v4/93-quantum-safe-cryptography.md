# Feature 93: Quantum-Safe Cryptography

## Overview
Post-quantum cryptography support using Kyber (KEM) and Dilithium (signing) algorithms for TLS, VPN, and code signing. Includes hybrid certificates and PQ migration assessment.

## Capabilities
- Post-quantum key generation (Kyber, Dilithium, Falcon)
- Hybrid certificate management (PQ + traditional)
- TLS configuration with PQ key exchange
- Migration assessment and roadmap generation
- Algorithm agility for future NIST standards
- Key rotation and revocation

## Architecture
1. **Integration Module** (`services/integration-service/src/emerging_tech/quantum_crypto.py`): Core PQ crypto operations
2. **Orchestrator Cog** (`services/orchestrator-agent/cogs/emerging_tech/quantum_crypto.py`): Discord commands for crypto ops
3. **Management Panel** (`services/management-panel/src/pages/emerging-tech/QuantumCrypto.tsx`): Crypto management dashboard
4. **CLI Commands** (`cli/ipilot/commands/emerging_tech/quantum_crypto.py`): Terminal-based crypto operations

## Data Model
- `PQKeyPair`: key_id, algorithm, key_type, strength, public_key, status, created_at, expires_at
- `MigrationAssessment`: assessment_id, system_id, crypto_inventory, pq_readiness_score, recommendations, timeline
- `TLSConfig`: config_id, hybrid_mode, pq_algorithms, certificate_authority, ocsp_stapling

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/quantum/keys | List PQ keys |
| POST | /api/v1/quantum/keys | Generate PQ key |
| GET | /api/v1/quantum/keys/{id} | Get key details |
| DELETE | /api/v1/quantum/keys/{id} | Revoke key |
| POST | /api/v1/quantum/keys/{id}/rotate | Rotate key |

## Security
- Keys stored encrypted with hardware-backed keystore
- Algorithm negotiation prevents downgrade attacks
- Migration assessment does not expose private key material
