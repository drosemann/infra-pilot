# Feature 62: Evidence Collection

## Overview
Automated evidence gathering for auditor review. Supports config/log/scan/policy/screenshot evidence types with package grouping and hash verification.

## Components
- **Integration Module**: `EvidenceCollector` — evidence CRUD, package management, hash verification
- **Orchestrator Cog**: `evidence_collection_cog.py`
- **Management Panel**: `EvidenceCollection.tsx`
- **CLI Commands**: `evidence list|collect|packages|stats`

## Key Features
- Evidence item collection with metadata
- Evidence package grouping by framework
- Package finalization workflow
- Control coverage tracking
