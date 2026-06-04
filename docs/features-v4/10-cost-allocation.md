# Feature 10: Hybrid Cost Allocation

## Overview
Tag and allocate costs across on-prem, edge, and multi-cloud. Showback/chargeback per team, project, or environment. Export to ERP systems.

## Components
- `cost_allocation_hybrid.py` — Tag manager, chargeback engine
- `CostAllocationHybridCog` — Discord commands for cost allocation
- `CostAllocation.tsx` — React cost allocation dashboard
- CLI commands in `cli/ipilot/commands/hybrid_cloud/cost_allocation_hybrid.py`

## API Endpoints
- `GET /api/cost-allocation/allocations` — List cost allocations
- `POST /api/cost-allocation/allocations` — Create allocation
- `GET /api/cost-allocation/summary` — Get allocation summary
- `GET /api/cost-allocation/teams/:team` — Get team spend
- `GET /api/cost-allocation/chargebacks` — List chargebacks
- `POST /api/cost-allocation/chargebacks` — Create chargeback
- `GET /api/cost-allocation/tags` — List cost tags

## Allocation Sources
on-prem, edge, cloud

## Chargeback Methods
Direct, Pro Rata, Fixed, Usage Based
