# Feature 6: IoT Device Provisioning

## Overview
Zero-touch device onboarding system. Supports claim codes, certificate enrollment, secure element integration, and device shadow state synchronization.

## Capabilities
- Zero-touch onboarding via QR code claim codes
- X.509 certificate enrollment (EST/ACME protocol)
- Secure element integration (TPM, ATECC608A)
- Device shadow state with cloud synchronization
- Bulk provisioning via CSV/JSON import
- Provisioning workflow with approval gates
- Device identity binding (hardware fingerprint + certificate)
- Secure boot attestation verification

## Provisioning Flow

```
1. Device Manufacture
   └── Inject secure element keypair
   └── Burn unique device ID (UID)
   
2. Device Power-on (First Boot)
   └── Generate CSR using secure element
   └── Connect to provisioning endpoint
   └── Present claim code (from sticker/QR)
   
3. Cloud Validation
   └── Verify claim code is valid and unassigned
   └── Sign certificate via internal CA
   └── Create device shadow with default config
   └── Return signed certificate + endpoint config

4. Device Configured
   └── Install certificate
   └── Connect to data plane endpoint
   └── Report initial device shadow state
   └── Start heartbeat + telemetry

5. Owner Claim
   └── User scans QR code on device
   └── Web portal shows device claimed
   └── Device appears in user's dashboard
```

## Claim Code System

- Format: `IP-XXXXX-XXXXX-XXXXX` (16 chars, base32)
- TTL: 24 hours default, configurable
- One-time use, expires on claim
- Batch generation for manufacturing
- API for claim code status lookup

## Certificate Enrollment

```python
class CertificateEnrollment:
    """Handle EST/ACME certificate enrollment for IoT devices."""
    
    async def enroll(self, device_id: str, csr_pem: str, 
                     claim_code: str) -> EnrolledCertificate:
        # 1. Validate claim code
        claim = await self.claim_store.validate(claim_code)
        if not claim.valid:
            raise ProvisioningError("Invalid or expired claim code")
        
        # 2. Attest device identity
        if not await self.attest_device(device_id, csr_pem):
            raise ProvisioningError("Device attestation failed")
        
        # 3. Sign CSR
        cert = await self.ca.sign_csr(csr_pem, 
                                       validity_days=3650,
                                       profile="iot_device")
        
        # 4. Create device shadow
        shadow = await self.create_device_shadow(device_id, {
            "provisioned_at": datetime.utcnow().isoformat(),
            "certificate_serial": cert.serial_number,
            "firmware_version": "1.0.0",
            "config": self.get_default_config(device_id)
        })
        
        # 5. Mark claim as used
        await self.claim_store.mark_used(claim_code, device_id)
        
        return EnrolledCertificate(
            certificate_pem=cert.pem,
            ca_chain_pem=self.ca.get_chain_pem(),
            endpoint_url=self.get_endpoint_url(),
            device_shadow=shadow
        )
```

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/iot_device_provisioning.py`
- Integration module: `services/integration-service/src/iot_provisioning.py`
- Test with simulated TPM and certificate operations
