# Feature 69: Vendor Risk Assessment

## Overview
Automated security questionnaire management supporting SIG (Standard Information Gathering) and CAIQ (Consensus Assessments Initiative Questionnaire) formats for third-party vendor risk evaluation.

## Components
- `vendor_risk.py` - Core vendor risk management
- `questionnaire_engine.py` - Questionnaire generation and scoring
- `sig_processor.py` - SIG-specific format handling
- `caiq_processor.py` - CAIQ format handling
- `vendor_routes.py` - API endpoints
- `VendorRiskManager` - Manager class

## Questionnaire Formats
- **SIG** (Standard Information Gathering) - Shared Assessments format
- **CAIQ** (Consensus Assessments Initiative Questionnaire) - CSA format
- **Custom** - User-defined questionnaire templates

## Risk Scoring
- Weighted scoring methodology
- Per-domain scores (Security, Privacy, Compliance, Business Continuity)
- Overall vendor risk rating
- Automated evidence validation
- Historical trend analysis

## API Endpoints
- `GET /api/v1/vendors` - List vendors
- `POST /api/v1/vendors` - Add vendor
- `GET /api/v1/vendors/{id}` - Vendor details
- `PUT /api/v1/vendors/{id}` - Update vendor
- `DELETE /api/v1/vendors/{id}` - Remove vendor
- `POST /api/v1/vendors/{id}/assessments` - Create assessment
- `GET /api/v1/vendors/{id}/assessments` - List assessments
- `GET /api/v1/vendors/{id}/assessments/{assessment_id}` - Assessment details
- `PUT /api/v1/vendors/{id}/assessments/{assessment_id}/responses` - Submit responses
- `POST /api/v1/vendors/{id}/assessments/{assessment_id}/score` - Score assessment

## Vendor Risk Rating
```json
{
  "vendor_id": "uuid",
  "name": "CloudProvider Inc.",
  "risk_rating": "medium",
  "scores": {
    "security": 78,
    "privacy": 85,
    "compliance": 72,
    "business_continuity": 65,
    "overall": 75
  },
  "last_assessment": "2025-01-15",
  "findings_count": 8,
  "critical_findings": 1
}
```
