# Feature 65: Vendor Compliance Manager

## Overview
Third-party vendor risk assessment and compliance tracking. Register vendors, assess compliance posture, and monitor risk levels across categories.

## Components
- **Integration Module**: `VendorComplianceManager` — vendor registration, assessment, risk scoring
- **Orchestrator Cog**: `vendor_compliance_cog.py`
- **Management Panel**: `VendorCompliance.tsx`
- **CLI Commands**: `vcom list|register|assess|risk`

## Key Features
- Vendor lifecycle management
- Automated risk scoring
- Category-based grouping (security, backup, network, iam)
- Assessment history tracking
