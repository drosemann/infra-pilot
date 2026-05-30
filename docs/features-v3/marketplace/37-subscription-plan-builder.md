# Feature 37: Subscription Plan Builder

## Overview
Admin tool for creating custom subscription plans with resource tiers, feature flags, addons (extra RAM, more backups, etc.), and instant plan switching.

## Components

### Integration Service: `marketplace/plan_builder.py`
- `PlanBuilderManager` - Core plan builder
  - Plan template CRUD
  - Resource tier definition (CPU, RAM, disk, bandwidth, GPU)
  - Feature flag management
  - Addon/upsell product definition
  - Plan pricing with billing cycles (monthly/yearly)
  - Plan switching logic (proration, upgrades/downgrades)
  - Plan comparison engine

### Management Panel: `pages/marketplace/PlansPage.tsx`
- Plan list management
- Plan editor with resource sliders
- Feature flag toggles
- Addon management
- Pricing configuration
- Plan comparison preview
- Plan switching simulation

### CLI Commands
- `ipilot plan create --name "Pro" --cpu 4 --ram 8 --disk 100 --price 29.99`
- `ipilot plan list`
- `ipilot plan addon add <plan_id> --name "Extra RAM" --ram 4 --price 5`
- `ipilot plan publish <plan_id>`

## API Endpoints
- `GET /api/marketplace/plans` - List plans
- `POST /api/marketplace/plans` - Create plan
- `GET /api/marketplace/plans/{id}` - Get plan
- `PUT /api/marketplace/plans/{id}` - Update plan
- `DELETE /api/marketplace/plans/{id}` - Delete plan
- `POST /api/marketplace/plans/{id}/publish` - Publish plan
- `POST /api/marketplace/plans/{id}/unpublish` - Unpublish plan
- `GET /api/marketplace/plans/{id}/addons` - List addons
- `POST /api/marketplace/plans/{id}/addons` - Create addon
- `PUT /api/marketplace/plans/{id}/addons/{addon_id}` - Update addon
- `DELETE /api/marketplace/plans/{id}/addons/{addon_id}` - Delete addon
- `GET /api/marketplace/plans/{id}/compare` - Compare with other plans
- `POST /api/marketplace/plans/{id}/switch` - Simulate plan switch

## Data Models

### SubscriptionPlan
- id, name, slug, description, tagline
- status (draft/active/archived), visibility (public/private/hidden)
- sort_order, is_featured
- resources (JSON: {cpu: 2, ram_gb: 4, disk_gb: 100, bandwidth_tb: 1, gpu: null})
- features (JSON: {backups: true, ssl: true, priority_support: false, ...})
- pricing (JSON: {monthly: 19.99, yearly: 199.99, setup_fee: 0})
- max_servers, max_backups, max_databases
- created_at, updated_at

### PlanAddon
- id, plan_id, name, slug, description
- resource_changes (JSON: {ram_gb: 4, disk_gb: 50})
- feature_changes (JSON: {backup_limit: 10})
- pricing (JSON: {monthly: 5, yearly: 50})
- max_qty, is_available

### PlanSwitch
- id, user_id, from_plan_id, to_plan_id
- scheduled_date, status (pending/completed/cancelled)
- proration_amount, refund_amount
- switch_type (upgrade/downgrade/crossgrade)
- effective_immediately

## Implementation Details
- Plan validation (resource conflicts)
- Proration calculation for mid-cycle switches
- Upgrade fees and downgrade credits
- Plan comparison engine
- Feature inheritance from base plan + addons
- Grace period handling for downgrades
- Resource limit enforcement
- Billing cycle alignment on switch
- Plan templates for quick creation
- Bulk plan updates via CSV/JSON import

## Testing
- Plan CRUD operations
- Addon calculation and bundling
- Proration formula accuracy
- Plan comparison output
- Feature flag resolution
- Visibility/access control
- Switch simulation correctness
