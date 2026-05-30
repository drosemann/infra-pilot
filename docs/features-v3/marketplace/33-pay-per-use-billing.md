# Feature 33: Pay-Per-Use Billing

## Overview
Per-second billing for compute resources with usage metering, invoice generation, and Stripe integration. Supports granular tracking of CPU-seconds, RAM-GB-seconds, and storage-GB-seconds.

## Components

### Integration Service: `marketplace/pay_per_use.py`
- `PayPerUseBillingManager` - Core billing management
  - Usage metering (per-second granularity)
  - Resource pricing model (CPU, RAM, storage, network)
  - Invoice generation (hourly/daily/monthly aggregation)
  - Stripe payment integration
  - Usage reports and analytics
  - Refund and credit processing
  - Tiered pricing (volume discounts)
  - Prepaid balance integration

### Orchestrator Agent: `cogs/metering_manager.py`
- Discord commands:
  - `/metering status` - Current usage
  - `/metering estimate` - Cost estimate
  - `/metering invoice` - View invoice
  - `/metering rates` - Current rates

### Management Panel: `pages/marketplace/BillingPage.tsx` (enhance existing)
- Real-time usage dashboard
- Cost breakdown by resource
- Invoice history with PDF download
- Payment method management (Stripe)
- Usage alerts configuration
- Budget management
- Billing settings

### CLI Commands
- `ipilot billing usage`
- `ipilot billing estimate --cpu 2 --ram 4 --storage 50 --hours 720`
- `ipilot billing invoices`
- `ipilot billing payment-methods`

## API Endpoints
- `GET /api/marketplace/billing/usage` - Current usage
- `GET /api/marketplace/billing/usage/history` - Usage history
- `POST /api/marketplace/billing/estimate` - Cost estimate
- `GET /api/marketplace/billing/invoices` - List invoices
- `GET /api/marketplace/billing/invoices/{id}` - Get invoice
- `GET /api/marketplace/billing/invoices/{id}/pdf` - Download invoice PDF
- `GET /api/marketplace/billing/rates` - Current rates
- `PUT /api/marketplace/billing/rates` - Update rates (admin)
- `POST /api/marketplace/billing/payment-methods` - Add payment method
- `GET /api/marketplace/billing/payment-methods` - List payment methods
- `DELETE /api/marketplace/billing/payment-methods/{id}` - Remove payment method
- `GET /api/marketplace/billing/balance` - Account balance
- `POST /api/marketplace/billing/balance/topup` - Top up balance

## Data Models

### UsageMetering
- id, user_id, resource_type (cpu/ram/disk/network/gpu)
- quantity (seconds for cpu, GB-seconds for ram/disk)
- meter_type (per_second/per_gb_hour/per_request)
- start_time, end_time, cost
- invoice_id (nullable, until invoiced)

### PricingRate
- id, resource_type, meter_type
- unit_price (per second/hour/GB), currency
- tier_min, tier_max, tier_price
- region, effective_from, effective_to
- is_active

### Invoice
- id, user_id, invoice_number
- period_start, period_end, issue_date, due_date
- line_items (JSON array: [{description, quantity, unit_price, total}])
- subtotal, tax_amount, total_amount
- currency, status (draft/open/paid/overdue/cancelled)
- stripe_invoice_id, paid_at

## Implementation Details
- Per-second metering via usage aggregation pipeline
- Stripe Invoicing API for payment collection
- PDF invoice generation via WeasyPrint/reportlab
- Currency conversion for multi-currency support
- Usage metering data in ClickHouse/TimescaleDB
- Aggregation queries: hourly -> daily -> monthly
- Proration for mid-cycle changes
- Volume discount calculations
- Tax calculation integration
- Payment retry logic for failed payments

## Testing
- Usage metering accuracy (per-second)
- Invoice generation correctness
- Stripe integration (mock mode)
- Pricing tier calculations
- Proration logic
- PDF generation format
- Payment method CRUD
