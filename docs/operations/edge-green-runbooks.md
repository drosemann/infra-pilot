# Edge, IoT & Green Computing Operations Runbooks

## Overview

This document provides operational runbooks for managing Edge Computing, IoT Device, and Green Computing infrastructure within Infra-pilot. Each runbook covers incident response, routine maintenance, troubleshooting, and escalation procedures.

---

## 1. Edge Device Outage

### Severity Levels
- **SEV1**: Complete edge site outage affecting production workloads
- **SEV2**: Partial service degradation at edge location
- **SEV3**: Single device failure or non-critical service impact

### Detection
- Monitor alert: `edge.device.offline` or `edge.site.down`
- Grafana dashboard shows zero throughput from affected site
- Users report latency spikes or inability to access edge services

### Initial Diagnosis (5 min)
```bash
# Check edge device connectivity
infra-pilot edge ping --device-id <device_id>

# Check edge agent status
infra-pilot edge status --site <site_name>

# Review recent edge logs
infra-pilot edge logs --device-id <device_id> --tail 100

# Check resource utilization
infra-pilot edge metrics --device-id <device_id> --metric cpu_usage
```

### Escalation Path
1. **L1**: Site reliability engineer verifies connectivity and restarts edge agent
2. **L2**: Edge infrastructure team investigates hardware or network issues
3. **L3**: Vendor support engaged for hardware replacement

### Resolution Steps

#### Step 1: Verify Network Connectivity
```bash
ping <edge_device_ip>
traceroute <edge_device_ip>
# Verify VPN or direct connection status
infra-pilot edge network-check --device-id <device_id>
```

#### Step 2: Restart Edge Services
```bash
# Restart edge agent
infra-pilot edge restart --device-id <device_id> --service edge-agent

# Restart all edge services
infra-pilot edge restart --device-id <device_id> --all

# Verify service recovery
infra-pilot edge status --device-id <device_id>
```

#### Step 3: Check Disk and Memory
```bash
# SSH into device (if accessible)
ssh admin@<edge_device_ip>
df -h
free -m
top -bn1

# Clear temporary files if disk is full
sudo find /tmp -type f -atime +7 -delete
sudo journalctl --vacuum-time=3d
```

#### Step 4: Failover (if available)
```bash
# Trigger failover to redundant edge node
infra-pilot edge failover --from <failed_device> --to <backup_device>

# Verify traffic routing
infra-pilot edge traffic-check --device-id <backup_device>
```

#### Step 5: Post-Recovery Verification
```bash
# Verify device heartbeat
infra-pilot edge heartbeat --device-id <device_id>

# Check sync status with central orchestrator
infra-pilot edge sync-status --device-id <device_id>

# Validate data replication
infra-pilot edge data-consistency --device-id <device_id>
```

### Post-Mortem Actions
- Document root cause in incident report
- Update monitoring thresholds if needed
- Schedule hardware replacement if applicable
- Review failover test results

---

## 2. IoT Device Provisioning Failure

### Severity Levels
- **SEV2**: Bulk provisioning failure affecting 10+ devices
- **SEV3**: Single device provisioning failure
- **SEV4**: Intermittent provisioning delays

### Detection
- Monitor alert: `iot.provisioning.failed`
- Device remains in `PROVISIONING` state for > 30 minutes
- Provisioning queue backlog growing

### Initial Diagnosis
```bash
# Check provisioning status
infra-pilot iot provisioning-status --device-id <device_id>

# View provisioning logs
infra-pilot iot logs --device-id <device_id> --component provisioning

# Check certificate status
infra-pilot iot certificate-check --device-id <device_id>

# Verify device credentials
infra-pilot iot verify-credentials --device-id <device_id>
```

### Resolution Steps

#### Step 1: Validate Device Identity
```bash
# Check device enrollment status
infra-pilot iot get-device --device-id <device_id>

# Re-register device if needed
infra-pilot iot register-device --device-id <device_id> --force

# Verify device certificate
openssl x509 -in /path/to/cert.pem -text -noout
```

#### Step 2: Check Network Access
```bash
# Verify device can reach provisioning endpoint
infra-pilot iot network-test --device-id <device_id>

# Check firewall rules
infra-pilot iot firewall-check --device-id <device_id>

# Test MQTT/CoAP connectivity
infra-pilot iot protocol-test --device-id <device_id> --protocol mqtt
```

#### Step 3: Reset and Retry
```bash
# Reset device to factory defaults
infra-pilot iot reset --device-id <device_id> --type factory

# Re-initiate provisioning
infra-pilot iot provision --device-id <device_id> --profile <profile_name>

# Monitor provisioning progress
infra-pilot iot provisioning-watch --device-id <device_id>
```

#### Step 4: Manual Configuration (last resort)
```bash
# Generate device config manually
infra-pilot iot generate-config --device-id <device_id> --output config.json

# Push config to device via side-channel
infra-pilot iot push-config --device-id <device_id> --file config.json

# Force status update
infra-pilot iot update-status --device-id <device_id> --status active
```

### Prevention
- Pre-provision device certificates before physical deployment
- Implement DHCP reservation for IoT device subnets
- Regular auditing of provisioning queue health
- Capacity planning for PKI infrastructure

---

## 3. Green Computing: High PUE Alert

### Severity Levels
- **SEV2**: PUE > 2.0 for > 1 hour
- **SEV3**: PUE > 1.8 for > 2 hours
- **SEV4**: PUE > 1.6 for > 4 hours

### Detection
- Monitor alert: `green.pue.high` with threshold exceeded
- Energy dashboard shows cooling inefficiency
- Utility bill anomaly detection triggered

### Initial Diagnosis
```bash
# Check current PUE value
infra-pilot green pue --site <site_name>

# View PUE trend over last 24 hours
infra-pilot green pue-trend --site <site_name> --hours 24

# Check cooling system status
infra-pilot green cooling-status --site <site_name>

# Review power distribution
infra-pilot green power-distribution --site <site_name>
```

### Resolution Steps

#### Step 1: Identify Root Cause
```bash
# Check IT load vs total power
infra-pilot green power-breakdown --site <site_name>

# Identify inefficient cooling units
infra-pilot green cooling-efficiency --site <site_name>

# Check for hot spots
infra-pilot green thermal-map --site <site_name>
```

#### Step 2: Optimize Cooling
```bash
# Adjust cooling setpoints
infra-pilot green set-cooling --site <site_name> --target-temperature 24

# Enable economizer mode if conditions permit
infra-pilot green enable-economizer --site <site_name>

# Balance CRAC unit loads
infra-pilot green balance-cooling --site <site_name>

# Verify airflow management
infra-pilot green airflow-check --site <site_name>
```

#### Step 3: Reduce IT Load
```bash
# Consolidate workloads
infra-pilot green consolidate-workloads --site <site_name>

# Migrate non-critical workloads
infra-pilot green migrate-workloads --source <site_name> --target <alt_site>

# Implement power capping
infra-pilot green power-cap --site <site_name> --limit 80%
```

#### Step 4: Verify Improvement
```bash
# Check PUE after changes
infra-pilot green pue --site <site_name>

# View 1-hour trend
infra-pilot green pue-trend --site <site_name> --hours 1

# Compare with baseline
infra-pilot green pue-compare --site <site_name> --baseline last-week
```

### Long-term Remediation
- Implement hot aisle/cold aisle containment if not present
- Upgrade to more efficient cooling infrastructure
- Consider liquid cooling for high-density racks
- Optimize UPS efficiency (operate in eco-mode)
- Regular cleaning of cooling coils and filters

---

## 4. Carbon Offset Integration Failure

### Severity Levels
- **SEV3**: Carbon offset reporting delayed > 24 hours
- **SEV4**: Offset certificate verification failure

### Detection
- Monitoring alert: `green.carbon.offset.failed`
- Compliance report shows missing offset data
- API integration with carbon registry returns errors

### Initial Diagnosis
```bash
# Check offset integration status
infra-pilot green carbon-offset-status

# View recent offset transactions
infra-pilot green offset-transactions --limit 10

# Check registry API connectivity
infra-pilot green test-registry-connection

# Validate certificates
infra-pilot green validate-certificates
```

### Resolution Steps

#### Step 1: API Integration Check
```bash
# Test registry API endpoint
curl -I https://carbon-registry.example.com/api/v1/health

# Check API authentication
infra-pilot green verify-api-credentials

# Review API rate limits
infra-pilot green check-rate-limits
```

#### Step 2: Data Reconciliation
```bash
# Compare local offset data with registry
infra-pilot green reconcile-offsets --date 2024-01-01

# Identify missing certificates
infra-pilot green find-missing-certificates --year 2024

# Re-submit failed transactions
infra-pilot green retry-failed-transactions
```

#### Step 3: Manual Certificate Upload
```bash
# Upload certificate file
infra-pilot green upload-certificate --file /path/to/certificate.pdf

# Register offset in local system
infra-pilot green register-offset --amount 100 --unit tCO2 --certificate-id <id>

# Verify offset appears in report
infra-pilot green carbon-report --month 2024-01
```

### Prevention
- Implement automatic retry with exponential backoff
- Monitor registry API status upstream
- Maintain buffer of pre-validated carbon credits
- Regular data reconciliation (daily)

---

## 5. Idle Resource Reclamation Failure

### Severity Levels
- **SEV3**: Reclamation policy not executing
- **SEV4**: False positive reclamation of active resources

### Detection
- Monitor alert: `green.reclamation.failed`
- Idle resources not being reclaimed within policy window
- Users reporting resources incorrectly marked as idle

### Initial Diagnosis
```bash
# Check reclamation policy status
infra-pilot green reclamation-status

# View pending reclamation candidates
infra-pilot green list-idle-resources

# Check reclamation logs
infra-pilot green reclamation-logs --tail 50

# Verify resource activity metrics
infra-pilot green resource-activity --resource-id <resource_id>
```

### Resolution Steps

#### Step 1: Verify Policy Configuration
```bash
# Display current reclamation policies
infra-pilot green show-reclamation-policies

# Check idle thresholds
infra-pilot green get-policy-config --policy-id <policy_id>

# Validate policy schedule
infra-pilot green check-policy-schedule --policy-id <policy_id>
```

#### Step 2: Manual Reclamation
```bash
# Force reclamation for specific resource
infra-pilot green reclaim --resource-id <resource_id> --force

# Reclaim by resource type
infra-pilot green reclaim-by-type --type compute --older-than 7d

# Verify reclamation
infra-pilot green verify-reclamation --resource-id <resource_id>
```

#### Step 3: Handle False Positives
```bash
# Mark resource as active (exclude from reclamation)
infra-pilot green mark-active --resource-id <resource_id>

# Add resource to exclusion list
infra-pilot green add-exclusion --resource-id <resource_id> --reason "Critical production"

# Review exclusion list
infra-pilot green list-exclusions
```

### Optimization
- Tune idle detection thresholds based on workload patterns
- Implement grace periods for known batch jobs
- Use machine learning for predictive idle detection
- Regular review of exclusion list

---

## 6. Auto-Shutdown Policy Violations

### Severity Levels
- **SEV3**: Critical resource auto-shutdown prevented
- **SEV4**: Non-critical resource shutdown delayed

### Detection
- Monitor alert: `green.shutdown.policy.violation`
- Resources not shutting down within policy window
- Policy override count exceeding threshold

### Initial Diagnosis
```bash
# Check auto-shutdown policy status
infra-pilot green shutdown-status

# View resources due for shutdown
infra-pilot green list-shutdown-candidates

# Check override audit log
infra-pilot green shutdown-override-log --hours 24

# Verify scheduler health
infra-pilot green check-shutdown-scheduler
```

### Resolution Steps

#### Step 1: Policy Compliance Check
```bash
# Verify policy is enabled
infra-pilot green get-shutdown-policy --policy-id <policy_id>

# Check schedule configuration
infra-pilot green get-shutdown-schedule --policy-id <policy_id>

# Validate resource tags/selectors
infra-pilot green validate-selectors --policy-id <policy_id>
```

#### Step 2: Manual Enforcement
```bash
# Trigger shutdown for specific resource
infra-pilot green shutdown --resource-id <resource_id>

# Shutdown by group
infra-pilot green shutdown-group --group <group_name>

# Schedule ad-hoc shutdown
infra-pilot green schedule-shutdown --resource-id <resource_id> --at "23:00"
```

#### Step 3: Prevent Unauthorized Overrides
```bash
# Review who has override permissions
infra-pilot green list-shutdown-override-users

# Restrict override capability
infra-pilot green restrict-override --role admin-only

# Enable override notification
infra-pilot green enable-override-notifications
```

### Best Practices
- Configure canary testing before widespread shutdown
- Maintain override audit trail
- Regular policy review with stakeholders
- Implement gradual shutdown (drain → notify → shutdown)

---

## 7. IoT Data Pipeline Backpressure

### Severity Levels
- **SEV2**: Data pipeline latency > 5 minutes
- **SEV3**: Pipeline latency > 2 minutes
- **SEV4**: Intermittent processing delays

### Detection
- Monitor alert: `iot.pipeline.backpressure`
- Kafka consumer lag increasing
- Database write throughput dropping
- Processing queue growing

### Initial Diagnosis
```bash
# Check pipeline status
infra-pilot iot pipeline-status

# View consumer lag
infra-pilot iot consumer-lag --group <consumer_group>

# Check processing rate
infra-pilot iot processing-rate --pipeline <pipeline_name>

# Review error logs
infra-pilot iot pipeline-errors --pipeline <pipeline_name> --tail 50
```

### Resolution Steps

#### Step 1: Scale Processing
```bash
# Increase consumer instances
infra-pilot iot scale-consumer --pipeline <pipeline_name> --instances 5

# Adjust batch size
infra-pilot iot set-batch-size --pipeline <pipeline_name> --size 1000

# Increase partition count
infra-pilot iot repartition --topic <topic_name> --partitions 12
```

#### Step 2: Optimize Data Flow
```bash
# Enable data filtering at edge
infra-pilot iot enable-edge-filtering --device-group <group>

# Reduce data granularity
infra-pilot iot set-sampling-rate --device-group <group> --rate 60

# Prioritize critical data streams
infra-pilot iot set-priority --stream <stream_name> --priority high
```

#### Step 3: Clear Backlog
```bash
# Purge old data if acceptable
infra-pilot iot purge-topic --topic <topic_name> --older-than 24h

# Replay from checkpoint
infra-pilot iot replay --pipeline <pipeline_name> --from-offset <offset>

# Reset consumer offset
infra-pilot iot reset-offset --group <consumer_group> --to latest
```

### Long-term Solutions
- Implement data TTL policies
- Add auto-scaling for consumers
- Optimize serialization (use Avro/Protobuf)
- Consider edge preprocessing

---

## 8. Edge Function Runtime Crash

### Severity Levels
- **SEV1**: All edge functions failing at location
- **SEV2**: Specific function type failing
- **SEV3**: Single function invocation failures

### Detection
- Monitor alert: `edge.function.runtime.crash`
- Function invocation error rate spiking
- Sandbox container restarting repeatedly

### Initial Diagnosis
```bash
# Check runtime status
infra-pilot edge function-runtime-status --site <site_name>

# View function logs
infra-pilot edge function-logs --function-id <function_id> --tail 100

# Check resource limits
infra-pilot edge function-resources --function-id <function_id>

# Test function invocation
infra-pilot edge invoke-function --function-id <function_id> --test
```

### Resolution Steps

#### Step 1: Isolate Faulty Function
```bash
# Disable problematic function
infra-pilot edge disable-function --function-id <function_id>

# Route traffic to healthy functions
infra-pilot edge reroute-traffic --exclude <function_id>

# Verify other functions operational
infra-pilot edge list-functions --status running
```

#### Step 2: Restart Runtime
```bash
# Restart function runtime
infra-pilot edge restart-runtime --site <site_name>

# Clear function cache
infra-pilot edge clear-cache --function-id <function_id>

# Verify runtime health
infra-pilot edge runtime-health --site <site_name>
```

#### Step 3: Debug Function Code
```bash
# Pull latest function code
infra-pilot edge pull-function-code --function-id <function_id> --output /tmp/code

# Check for memory leaks
infra-pilot edge profile-function --function-id <function_id> --duration 60

# Review function dependencies
infra-pilot edge list-dependencies --function-id <function_id>
```

### Prevention
- Set appropriate memory/timeout limits
- Implement function canary deployments
- Regular dependency audits
- Use language-specific best practices

---

## 9. Green Scheduling Compliance Audit

### Frequency: Monthly

### Audit Scope
- Scheduling policy adherence
- Energy-aware workload distribution
- Carbon-aware scheduling effectiveness
- Resource utilization efficiency

### Pre-Audit Checklist
```bash
# Export scheduling policies
infra-pilot green export-policies --output policies.json

# Collect scheduling metrics
infra-pilot green scheduling-metrics --month 2024-01

# Generate compliance report
infra-pilot green compliance-report --month 2024-01
```

### Audit Procedures

#### 1. Policy Compliance Verification
```bash
# Check active policies
infra-pilot green list-active-policies

# Verify policy enforcement
infra-pilot green verify-enforcement --policy-id <policy_id>

# Identify policy violations
infra-pilot green list-violations --month 2024-01
```

#### 2. Energy Efficiency Analysis
```bash
# Calculate energy savings
infra-pilot green energy-savings --month 2024-01

# Compare with baseline
infra-pilot green compare-efficiency --baseline 2023-Q4

# Review workload distribution
infra-pilot green workload-distribution --month 2024-01
```

#### 3. Carbon Impact Assessment
```bash
# Calculate carbon footprint
infra-pilot green carbon-footprint --month 2024-01

# Verify offset coverage
infra-pilot green offset-coverage --month 2024-01

# Generate sustainability score
infra-pilot green sustainability-score --month 2024-01
```

### Remediation Actions
- Update scheduling policies based on findings
- Optimize workload placement
- Adjust carbon intensity thresholds
- Implement recommendations from audit report

---

## 10. Hardware Lifecycle Management

### Stages
1. **Procurement**: Hardware ordering and intake
2. **Provisioning**: Configuration and deployment
3. **Operations**: Active monitoring and maintenance
4. **Decommissioning**: Secure data wipe and disposal

### Routine Maintenance Tasks

#### Weekly
```bash
# Check hardware health
infra-pilot green hardware-health --all

# Review warranty status
infra-pilot green warranty-check --all

# Identify expiring contracts
infra-pilot green expiring-contracts --days 90
```

#### Monthly
```bash
# Generate lifecycle report
infra-pilot green lifecycle-report --month 2024-01

# Review decommission queue
infra-pilot green decommission-queue

# Audit asset tags
infra-pilot green audit-assets
```

#### Quarterly
```bash
# Full hardware inventory
infra-pilot green inventory --format json

# Refresh depreciation schedules
infra-pilot green depreciation-report

# Plan hardware refresh
infra-pilot green refresh-planning --budget 500000
```

### Decommissioning Procedure
```bash
# Step 1: Identify decommission candidates
infra-pilot green decommission-candidates --older-than 5y

# Step 2: Verify data sanitization
infra-pilot green sanitize --asset-id <asset_id>

# Step 3: Update asset registry
infra-pilot green mark-decommissioned --asset-id <asset_id>

# Step 4: Arrange recycling
infra-pilot green schedule-pickup --assets <asset_ids> --recycler <vendor>

# Step 5: Document disposal
infra-pilot green disposal-certificate --asset-id <asset_id>
```

### Environmental Compliance
- Ensure e-waste recycling vendor is certified
- Maintain chain of custody documentation
- Track recycling rates against targets
- Report disposal volumes quarterly

---

## Incident Response Playbook

### Pre-Incident Preparation
1. Ensure runbooks are accessible offline
2. Maintain incident response contact list
3. Configure monitoring alerts for all critical metrics
4. Regularly test disaster recovery procedures
5. Keep infrastructure diagrams up-to-date

### Incident Classification Matrix

| Severity | Response Time | Escalation | Example |
|----------|--------------|------------|---------|
| SEV1 | 15 min | VP + Engineering | Complete site outage |
| SEV2 | 30 min | Engineering Manager | High PUE, pipeline backpressure |
| SEV3 | 2 hours | Team Lead | Single device failure |
| SEV4 | 8 hours | On-call engineer | Reporting delay |

### Post-Incident Review Process
1. Schedule review within 5 business days
2. Document timeline of events
3. Identify root cause and contributing factors
4. Define action items with owners
5. Update runbooks based on learnings
6. Share findings in post-mortem meeting

### Change Management
- All operational changes require change request
- Emergency changes require manager approval
- Document change outcome and rollback steps
- Review changes in weekly operations meeting

---

## Appendices

### A. Useful Commands Reference
```bash
edge device list
edge device show <id>
edge device update <id> --field value
edge device delete <id>
edge device logs <id> --tail N
edge device restart <id>
iot provision <id>
iot deprovision <id>
iot data query --from <time> --to <time>
iot data export --format csv
green pue show
green carbon footprint --period <period>
green energy report --site <site>
green schedule list
green schedule apply <id>
green hardware list
green hardware decommission <id>
```

### B. Monitoring Alert Thresholds

| Metric | Warning | Critical | Evaluation Window |
|--------|---------|----------|-------------------|
| Edge CPU Usage | > 80% | > 95% | 5 min |
| Edge Memory Usage | > 85% | > 95% | 5 min |
| Edge Disk Usage | > 80% | > 90% | 10 min |
| IoT Message Lag | > 1000 | > 10000 | 1 min |
| PUE | > 1.6 | > 2.0 | 1 hour |
| Carbon Emission | > 200 kg/h | > 500 kg/h | 1 hour |
| Pipeline Latency | > 60s | > 300s | 1 min |
| Provisioning Failure | > 5% | > 20% | 10 min |
| Device Offline | > 5% | > 15% | 5 min |
| Battery Level | < 30% | < 10% | Per device |

### C. Contact List
- **Edge Infrastructure Team**: edge-team@company.com / #edge-ops Slack
- **IoT Platform Team**: iot-team@company.com / #iot-ops Slack
- **Green Computing Team**: green-team@company.com / #green-ops Slack
- **Security Team**: security@company.com / #security Slack
- **Vendor Support**: See vendor portal for contact info
- **Emergency**: On-call rotation in PagerDuty

### D. SLA Targets
- Edge device uptime: 99.9% (monthly)
- IoT message delivery: 99.99% (monthly)
- Pipeline processing latency: < 60s P99
- Provisioning success rate: > 99.5%
- PUE target: < 1.4 (monthly average)
- Carbon reporting: < 24h from month end
- Hardware deployment: < 5 business days
- Decommissioning: < 10 business days

### E. Training Resources
- Edge Computing Fundamentals (internal wiki)
- IoT Security Best Practices (mandatory annual)
- Green Computing Certification (recommended)
- Incident Response Workshop (quarterly)
- Runbook Drills (bi-monthly)

---

*Document version: 2.0.0 | Last updated: 2024-01-15 | Owner: Infrastructure Operations*
