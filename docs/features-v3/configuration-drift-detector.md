# Feature 74: Configuration Drift Detector

## Overview
Periodic detection of configuration drift between desired state (as defined in code/config) and actual state (running infrastructure), with remediation suggestions and automated correction.

## Components
- `drift_detector.py` - Core drift detection engine
- `state_collector.py` - Actual state collection from infrastructure
- `drift_remediator.py` - Automated drift remediation
- `drift_routes.py` - API endpoints
- `DriftManager` - Manager class

## Drift Detection Methods
- **File hash comparison** - Compare config files against known good hashes
- **Terraform plan** - Run terraform plan to detect drift
- **API comparison** - Query infrastructure APIs and compare
- **Agent-based** - Local agent reports actual state
- **Git diff** - Compare running config with git HEAD

## Supported Resources
- Docker containers (image, env, volumes, networks)
- Kubernetes resources (deployments, configmaps, secrets)
- Linux system configs (sshd_config, nginx.conf, iptables)
- Database schemas and users
- Network device configurations
- Cloud resources (AWS, GCP, Azure)

## API Endpoints
- `POST /api/v1/drift/scan` - Trigger drift scan
- `GET /api/v1/drift/scans` - List scans
- `GET /api/v1/drift/scans/{id}` - Scan results
- `GET /api/v1/drift/scans/{id}/drifts` - Individual drifts
- `POST /api/v1/drift/scans/{id}/remediate` - Auto-remediate
- `GET /api/v1/drift/suppressions` - List suppressions
- `POST /api/v1/drift/suppressions` - Suppress drift
- `GET /api/v1/drift/reports` - Drift reports

## Drift Severity
- `critical` - Security-relevant drift
- `high` - Functional impact likely
- `medium` - Minor deviation
- `low` - Cosmetic only
- `info` - Informational

## Remediation Actions
- Auto-revert to desired state
- Generate correction playbook
- Notify responsible team
- Create incident ticket
- Log for audit review
