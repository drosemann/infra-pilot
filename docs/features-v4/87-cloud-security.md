# Feature 87: Cloud Security Posture

## Overview
Multi-cloud security posture management (CSPM), cloud workload protection (CWPP), and IAM security across AWS, Azure, and GCP.

## Components
- **CSPM**: 1,847 cloud resources scanned for misconfigurations
- **CWPP**: 423 workloads protected with runtime threat detection
- **IAM Security**: Role and permission analysis with least-privilege enforcement
- **Compliance**: CIS, NIST, PCI benchmarks for cloud environments

## Data Models
- CSPMFinding: id, resource, provider, rule, severity, status
- Workload: id, name, type, provider, region, runtime_status
- IAMRole: id, name, provider, policies, overprivileged

## API Endpoints
- GET /api/soc/cloud/cspm - List CSPM findings
- GET /api/soc/cloud/workloads - List workloads
- POST /api/soc/cloud/scan - Run CSPM scan
- GET /api/soc/cloud/iam/roles - List IAM roles
- PUT /api/soc/cloud/findings/:id - Update finding status

## Metrics
- Resources Scanned: 1,847
- Misconfigurations: 142 (4 critical)
- Workloads: 423 protected
- Compliance Score: 87%
- Cloud Accounts: 6
- Regions: 12

## Discord Commands
- /cloudsec - View cloud security summary
- /cloudsec cspm - List CSPM findings
- /cloudsec cwpp - View workload protection
- /cloudsec iam - View IAM security
- /cloudsec stats - View statistics
