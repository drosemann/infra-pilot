# Feature 39: Invoice & Tax Automation

## Overview
Automated tax calculation (VAT/GST/sales tax per region), tax report generation, credit note handling, and XRechnung/ZUGFeRD compliance for EU billing.

## Components

### Integration Service: `marketplace/tax_automation.py`
- `TaxAutomationManager` - Core tax automation
  - Tax rate database (per country, per region, per product type)
  - Automated tax calculation on invoices
  - VAT/GST/Sales tax handling
  - Tax report generation (quarterly/annual)
  - Credit note / refund processing
  - XRechnung and ZUGFeRD format generation
  - EU VAT reverse charge handling
  - Digital tax report submission (via API)

### Management Panel: `pages/marketplace/TaxPage.tsx`
- Tax configuration dashboard
- Tax rate management
- Invoice history with tax breakdown
- Tax report generation and download
- Credit note management
- XRechnung/ZUGFeRD export
- Tax filing status tracker

### CLI Commands
- `ipilot tax rates list`
- `ipilot tax report generate --period Q1-2026`
- `ipilot tax invoice preview --invoice <id>`

## API Endpoints
- `GET /api/marketplace/tax/rates` - List tax rates
- `POST /api/marketplace/tax/rates` - Add tax rate
- `PUT /api/marketplace/tax/rates/{id}` - Update tax rate
- `DELETE /api/marketplace/tax/rates/{id}` - Delete tax rate
- `GET /api/marketplace/tax/calculate` - Calculate tax for amount
- `GET /api/marketplace/tax/reports` - List reports
- `POST /api/marketplace/tax/reports/generate` - Generate report
- `GET /api/marketplace/tax/reports/{id}` - Get report
- `GET /api/marketplace/tax/reports/{id}/download` - Download report
- `GET /api/marketplace/tax/credit-notes` - List credit notes
- `POST /api/marketplace/tax/credit-notes` - Create credit note
- `GET /api/marketplace/tax/settings` - Tax settings
- `PUT /api/marketplace/tax/settings` - Update tax settings

## Data Models

### TaxRate
- id, country_code (ISO 3166-1 alpha-2)
- region (state/province, nullable), city (nullable)
- tax_type (vat/gst/sales_tax/none)
- rate_percentage, reduced_rate_percentage
- is_reverse_charge, applies_to (products/services/both)
- effective_from, effective_to
- jurisdiction_level (country/state/city)

### TaxReport
- id, period_type (monthly/quarterly/annual)
- period_start, period_end
- total_sales, total_tax_collected
- tax_breakdown (JSON: {vat: {rate: 20, amount: 1000}, ...})
- status (draft/generated/submitted/acknowledged)
- report_format (csv/xml/xrechnung/zugferd)
- filing_deadline, submitted_at

### CreditNote
- id, invoice_id, reason, total_amount
- tax_amount, refund_amount
- status (draft/issued/applied/void)
- issued_at, applied_to_invoice

### XRechnungDocument
- id, invoice_id, xml_content
- format (xrechnung/zugferd), version
- validation_status (valid/invalid)
- checksum, created_at

## Implementation Details
- Tax rate database with 200+ jurisdictions
- EU VAT rules (MOSS, reverse charge, intra-community)
- US sales tax (state-level + origin/destination-based)
- XRechnung: UBL 2.1 XML with German-specific extensions
- ZUGFeRD: Hybrid PDF + XML (Factur-X)
- Tax report generation as CSV/XML
- GDPdU/GoBD compliance for German tax authorities
- Automatic tax calculation on invoice creation
- Tax exemption handling (business customers, charities)
- Currency conversion for tax base amount

## Testing
- Tax rate lookup by jurisdiction
- Tax calculation accuracy (all types)
- Reverse charge logic for EU B2B
- Report generation with correct totals
- XRechnung XML validation against schema
- ZUGFeRD PDF/A-3 generation
- Credit note lifecycle
- Multi-currency tax calculation
