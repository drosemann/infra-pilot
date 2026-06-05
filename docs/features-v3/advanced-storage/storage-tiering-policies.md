# Feature 44: Storage Tiering Policies

## Overview
Auto-move data between hot/warm/cold tiers based on access frequency. Configurable policies based on last accessed, file age, and size.

## Components
- **Orchestrator Agent Cog**: `advanced-storage/storage_tiering.py` - Tier management
- **Management Panel Page**: `advanced-storage/StorageTiering.tsx` - Policy configuration UI

## Storage Tiers
- **Hot**: NVMe/SSD - <1ms latency - for active data
- **Warm**: SATA SSD - <5ms latency - for recent data  
- **Cold**: HDD - <20ms latency - for archival data
- **Glacier**: Deep archive - minutes to hours retrieval

## Policy Rules
- Based on last access time
- Based on file age
- Based on file size
- Based on file type/extension
- Based on user/project tags
- Custom cron schedules

## API Endpoints
- `GET /api/v1/storage/tiers` - List tiers
- `POST /api/v1/storage/tiers` - Create tier
- `GET /api/v1/storage/tiers/policies` - List policies
- `POST /api/v1/storage/tiers/policies` - Create policy
- `PUT /api/v1/storage/tiers/policies/{id}` - Update policy
- `DELETE /api/v1/storage/tiers/policies/{id}` - Delete policy
- `POST /api/v1/storage/tiers/manual-move` - Manual move data
- `GET /api/v1/storage/tiers/savings` - Cost savings report
