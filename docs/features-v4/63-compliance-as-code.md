# Feature 63: Compliance as Code Engine

## Overview
Policy-as-code evaluation with automated remediation. Uses OPA/Rego-style templates to evaluate infrastructure configurations against compliance rules.

## Components
- **Integration Module**: `ComplianceAsCodeEngine` — template management, evaluation engine, remediation
- **Orchestrator Cog**: `compliance_as_code_cog.py`
- **Management Panel**: `ComplianceAsCode.tsx`
- **CLI Commands**: `cac list|evaluate|templates|stats`

## Key Features
- Rego-compatible policy templates
- Automated compliance evaluation
- Pass/fail scoring per template
- Auto-remediation for known violations
