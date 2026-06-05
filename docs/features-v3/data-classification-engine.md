# Feature 68: Data Classification Engine

## Overview
Automated classification of data assets for PII (Personally Identifiable Information), PHI (Protected Health Information), and PCI (Payment Card Industry) data with tagging, scanning, and policy enforcement.

## Components
- `classification_engine.py` - Core classification logic
- `pii_detector.py` - PII pattern detection (SSN, email, phone, address, etc.)
- `phi_detector.py` - PHI detection (HIPAA identifiers)
- `pci_detector.py` - PCI detection (credit card numbers, CVV)
- `classification_routes.py` - API endpoints
- `ClassificationEngine` - Manager class

## Detected Data Types
- **PII**: SSN, Email, Phone, Address, DOB, Passport, Driver's License, IP Address
- **PHI**: Medical Records, Patient IDs, Health Insurance Info, Diagnoses
- **PCI**: Credit Card Numbers (PAN), CVV, Track Data, PIN
- **Custom**: Regex-based custom patterns

## Classification Levels
- `public` - No sensitivity
- `internal` - Internal use only
- `confidential` - Business confidential
- `restricted` - Highly sensitive
- `regulated` - Subject to compliance (PII/PHI/PCI)

## API Endpoints
- `POST /api/v1/classification/scan` - Scan data source
- `GET /api/v1/classification/results` - Scan results
- `GET /api/v1/classification/results/{id}` - Result details
- `GET /api/v1/classification/inventory` - Classified data inventory
- `PUT /api/v1/classification/label/{resource_id}` - Manual label override
- `GET /api/v1/classification/policies` - Classification policies
- `POST /api/v1/classification/policies` - Create policy

## Scanning Capabilities
- File system scanning (local and network)
- Database column scanning
- API response inspection
- Log file scanning
- Object storage scanning (S3, GCS, Azure Blob)
- Email and document scanning
