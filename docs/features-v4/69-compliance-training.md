# Feature 69: Compliance Training

## Overview
Training modules, quiz assessments, and certification tracking for compliance frameworks. Built-in modules for GDPR, SOC 2, HIPAA, PCI DSS, ISO 27001, Data Residency, and Vendor Risk.

## Components
- **Integration Module**: `ComplianceTrainingManager` — modules, quizzes, assignments, certifications
- **Orchestrator Cog**: `compliance_training_cog.py`
- **Management Panel**: `ComplianceTraining.tsx`
- **CLI Commands**: `train modules|assign|status|stats`

## Key Features
- Pre-built training modules for 7 frameworks
- Quiz engine with scoring and pass/fail logic
- Assignment and certification tracking
- Expiry reminders for certifications
