# Feature 34: Reseller / White-Label

## Overview
Full reseller portal with custom domain support, branded management panel, sub-admin accounts, margin management, and automated provisioning.

## Components

### Integration Service: `marketplace/reseller.py`
- `ResellerManager` - Core reseller management
  - Reseller account CRUD
  - Custom domain management (white-label panel)
  - Sub-admin account management
  - Margin management (overrides on base pricing)
  - Automated provisioning delegation
  - Brand customization (logo, colors, CSS)
  - Reseller analytics dashboard

### Management Panel: `pages/marketplace/ResellerPage.tsx`
- Reseller overview dashboard
- Customer management
- Margin configuration
- Brand customization
- Sub-admin role management
- Reseller analytics (revenue, signups, churn)
- White-label domain settings

### CLI Commands
- `ipilot reseller create --name "Partner" --margin 15`
- `ipilot reseller list`
- `ipilot reseller customer list <reseller_id>`

## API Endpoints
- `GET /api/marketplace/resellers` - List resellers
- `POST /api/marketplace/resellers` - Create reseller
- `GET /api/marketplace/resellers/{id}` - Get reseller
- `PUT /api/marketplace/resellers/{id}` - Update reseller
- `GET /api/marketplace/resellers/{id}/customers` - List customers
- `GET /api/marketplace/resellers/{id}/revenue` - Revenue analytics
- `PUT /api/marketplace/resellers/{id}/branding` - Update branding
- `PUT /api/marketplace/resellers/{id}/margins` - Update margins
- `POST /api/marketplace/resellers/{id}/sub-admins` - Create sub-admin
- `GET /api/marketplace/resellers/{id}/sub-admins` - List sub-admins
- `DELETE /api/marketplace/resellers/{id}/sub-admins/{admin_id}` - Remove sub-admin

## Data Models

### Reseller
- id, name, email, status (active/suspended/terminated)
- custom_domain, panel_branding (JSON: logo, colors, css)
- base_margin_pct (default margin on all products)
- commission_tier (bronze/silver/gold/platinum)
- total_customers, total_revenue, lifetime_value
- api_key (for programmatic access)
- created_at

### ResellerProduct
- id, reseller_id, product_name, base_price
- margin_pct, final_price
- product_type (vps/storage/bandwidth/app)
- min_commitment, max_qty

### SubAdmin
- id, reseller_id, email, name, role
- permissions (JSON array of resource:action pairs)
- status (active/invited/disabled)
- created_at, last_login

## Implementation Details
- Custom domain via reverse proxy config generation
- Branding via CSS injection and logo URL
- Margin calculation on base prices
- Sub-admin permissions matrix
- Automated provisioning via API delegation
- Revenue sharing calculations
- Reseller signup flow with KYC
- White-label dashboard template
- Multi-tenant data isolation
- Reseller API keys with scoped permissions

## Testing
- Reseller CRUD operations
- Custom domain DNS verification
- Margin calculation accuracy
- Sub-admin permission enforcement
- Branding application
- Revenue analytics
- Data isolation verification
