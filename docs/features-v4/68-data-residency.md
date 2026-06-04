# Feature 68: Data Residency Enforcement

## Overview
Geo-fencing and cross-border data flow compliance. Enforce data localization rules for GDPR, CCPA, HIPAA, PCI DSS, DPDP, and LGPD.

## Components
- **Integration Module**: `DataResidencyEnforcer` — asset tracking, geo-fencing, cross-border checking
- **Orchestrator Cog**: `data_residency_cog.py`
- **Management Panel**: `DataResidency.tsx`
- **CLI Commands**: `dres list|register|check|summary`

## Key Features
- Data asset registration with geo-location
- Cross-border data flow checking
- Residency violation detection
- Region-based enforcement rules
