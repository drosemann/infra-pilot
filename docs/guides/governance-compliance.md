# Infra Pilot User Guide: Governance & Compliance

## Overview
Infra Pilot's governance suite provides policy-as-code enforcement, automated compliance scanning, ML-powered audit analytics, data classification, and vendor risk management.

## Getting Started

### 1. Policy as Code

**Create a security policy:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/governance/policies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "require_mfa",
    "description": "Require MFA for all admin actions",
    "category": "security",
    "rules": [
      {
        "id": "mfa-1",
        "effect": "deny",
        "resource": "admin:*",
        "condition": {"mfa_verified": false}
      },
      {
        "id": "mfa-2",
        "effect": "require_mfa",
        "resource": "admin:*",
        "condition": {}
      }
    ]
  }'
```

**Evaluate a request against policies:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/governance/policies/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "resource": "admin:users",
    "action": "delete",
    "context": {
      "user": "admin@example.com",
      "role": "admin",
      "mfa_verified": false
    }
  }'
```

**Create an RBAC policy:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/governance/policies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rbac_production",
    "description": "RBAC rules for production environment",
    "category": "rbac",
    "rules": [
      {"id": "admin-all", "effect": "allow", "resource": "*", "condition": {"role": "admin"}},
      {"id": "operator-read", "effect": "allow", "resource": "server:*", "condition": {"role": "operator", "action": "read"}},
      {"id": "operator-write", "effect": "allow", "resource": "server:*", "condition": {"role": "operator", "action__in": ["start", "stop", "restart"]}},
      {"id": "viewer-read", "effect": "allow", "resource": "*", "condition": {"role": "viewer", "action": "read"}},
      {"id": "viewer-block", "effect": "deny", "resource": "billing:*", "condition": {"role": "viewer"}}
    ]
  }'
```

### 2. Compliance Scanning

**Run a CIS Docker benchmark scan:**
```bash
ipilot compliance scan --benchmark cis_docker
```

**View scan results:**
```bash
ipilot compliance report scan_abc123
```

**List available checks:**
```bash
ipilot compliance checks --benchmark cis_kubernetes
```

**Add a waiver for a known issue:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/governance/compliance/waivers \
  -H "Content-Type: application/json" \
  -d '{
    "check_id": "cis_docker_4_1",
    "reason": "Host network required for legacy monitoring agent",
    "expires_in_days": 30
  }'
```

### 3. Audit Analytics & Anomaly Detection

**View detected anomalies:**
```bash
ipilot audit anomalies
```

**Get user audit report:**
```bash
curl -X GET https://api.infra-pilot.io/api/v1/governance/audit/users/user-001/report
```

**View impossible travel events:**
```bash
curl -X GET https://api.infra-pilot.io/api/v1/governance/audit/anomalies/travel
```

### 4. Data Classification

**Scan text for sensitive data:**
```bash
ipilot classify scan "Customer email: user@example.com, Credit card: 4111-1111-1111-1111"
```

**View classified inventory:**
```bash
ipilot classify inventory
```

**Add to inventory:**
```bash
curl -X POST https://api.infra-pilot.io/api/v1/governance/classify/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/data/customers/production.db",
    "category": "database",
    "classification": "pii",
    "patterns": ["email", "phone", "ssn"]
  }'
```

### 5. Vendor Risk Management

**Register a vendor:**
```bash
ipilot vendor create "CloudProvider Inc" "cloudprovider.com" --category cloud_infrastructure
```

**Create an assessment:**
```bash
ipilot vendor assess vendor_001 --type sig
```

**View vendor risk score:**
```bash
curl -X GET https://api.infra-pilot.io/api/v1/governance/vendors/vendor_001/risk-score
```

## Configuration

### Policy Engine Configuration
```yaml
policy_engine:
  default_decision: allow           # Default decision when no policy matches
  max_evaluation_depth: 10          # Max nested condition depth
  cache_ttl: 300                    # Policy cache TTL in seconds
  deny_overrides: true              # Deny takes precedence over allow
```

### Compliance Scanner Configuration
```yaml
compliance_scanner:
  benchmarks_enabled:
    - cis_docker
    - cis_kubernetes
    - nist_800_53
    - bsi_grundschutz
  max_concurrent_checks: 10
  scan_timeout: 300                  # Timeout in seconds
  report_format: json
```

### Audit Analytics Configuration
```yaml
audit_analytics:
  anomaly_threshold: 0.8            # Threshold for flagging anomalies
  baseline_window_days: 30          # Days of history for baselines
  isolation_forest_contamination: 0.1  # Expected anomaly ratio
  max_events_per_batch: 1000
  trend_period_days: 7
```

### Data Classification Configuration
```yaml
classification_engine:
  pii_patterns_enabled: true
  phi_patterns_enabled: true
  pci_patterns_enabled: true
  confidence_threshold: 0.6
  max_scan_size_mb: 100
  inventory_auto_update: true
  scan_schedule_cron: "0 2 * * 0"   # Weekly scan at 2 AM Sunday
```

### Vendor Risk Configuration
```yaml
vendor_risk:
  assessment_frequency_days: 365
  score_weights:
    security: 0.4
    privacy: 0.3
    compliance: 0.2
    operations: 0.1
  auto_tier_update: true
  risk_tiers:
    critical: { min_score: 0, max_score: 30 }
    high: { min_score: 31, max_score: 50 }
    medium: { min_score: 51, max_score: 70 }
    low: { min_score: 71, max_score: 100 }
```

## Troubleshooting

### Policy not matching
1. Check that the policy is enabled
2. Verify resource pattern matches (supports glob patterns)
3. Check condition fields match context structure
4. Review policy evaluation order (deny overrides)
5. Enable policy debug logging

### Compliance scan fails
1. Check that Docker/Kubernetes is accessible
2. Verify benchmark checks are compatible with your version
3. Review scan timeout settings for large environments
4. Check system resource availability (CPU/memory for checks)
5. Review scan logs for specific error messages

### Anomaly detection false positives
1. Adjust anomaly threshold (higher = fewer alerts)
2. Increase baseline window for better pattern learning
3. Exclude known maintenance patterns
4. Review user baseline data completeness
5. Consider seasonal patterns in your environment
