# Feature 38: Data Integrity Verification

## Overview
Periodic checksum/consistency validation across replicas and backups. Detect silent data corruption and auto-repair from trusted source.

## Components
- `data_integrity.py` - Verification engine with 6 verification types
- `DataIntegrityCog` - Discord commands
- `DataIntegrity.tsx` - Management panel UI

## Verification Types
- Checksum comparison
- Row count comparison
- Schema comparison
- Sample data comparison
- Replica lag monitoring
- Backup restore verification

## API Endpoints
- `GET /api/v1/resiliency/data-integrity/verifications` - List verifications
- `POST /api/v1/resiliency/data-integrity/verifications` - Create verification
- `POST /api/v1/resiliency/data-integrity/verifications/{id}/run` - Run verification
