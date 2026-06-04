# Feature 46: Data Masking & Anonymization

## Overview
Column-level data masking with multiple masking methods (redaction, substitution, encryption, hashing), grouped into profiles for consistent application across environments.

## Components
- `data_masking.py` - Masking rule and profile management with application engine
- `cog_data_masking.py` - Discord bot commands for masking operations

## Data Models
- MaskingRule - Rule with name, column pattern, method (redact/substitute/encrypt/hash/nullify), condition
- MaskingProfile - Profile with targets (database/schema/table), rule references, enabled flag
- MaskingResult - Application result with rows masked and affected columns

## API Endpoints
- `GET /api/v4/data/masking/rules` - List rules
- `POST /api/v4/data/masking/rules` - Create rule
- `GET /api/v4/data/masking/profiles` - List profiles
- `POST /api/v4/data/masking/profiles` - Create profile
- `POST /api/v4/data/masking/profiles/:id/apply` - Apply profile

## Metrics
- Rules defined
- Profiles active
- Rows masked per application

## Discord Commands
- `/masking list-rules` - List masking rules
- `/masking create-rule` - Create new rule
- `/masking list-profiles` - List profiles
- `/masking create-profile` - Create profile
- `/masking apply` - Apply profile to data
