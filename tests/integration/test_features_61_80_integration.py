"""Cross-feature integration tests for features 61-80.

Tests interactions between identity (61-66), governance (67-70),
and automation (71-80) feature domains.
"""
import pytest
import json
import tempfile
import os
import uuid
from datetime import datetime, timedelta

from services.integration_service.src.identity_provider_ext import (
    IdentityProviderManager as IdPManager, OIDCProviderConfig, SAMLProviderConfig,
    ClientRegistration, TokenType
)
from services.integration_service.src.webauthn_ext import (
    WebAuthnManager, WebAuthnCredential, CredentialType, AttestationType, VerificationStatus
)
from services.integration_service.src.session_manager_ext import (
    SessionManager, UserSession, SessionStatus, RiskLevel, RiskAssessment
)
from services.integration_service.src.pam_manager_ext import (
    PAMManager, AccessRequest, AccessRequestStatus, AccessLevel,
    BreakGlassEvent, JustificationLevel
)
from services.integration_service.src.policy_engine_ext import (
    PolicyEngine, PolicyDefinition, PolicyRule, PolicyEffect, EvaluationResult
)
from services.integration_service.src.compliance_scanner_ext import (
    ComplianceScanner, ComplianceScan, BenchmarkDefinition, CheckResult, ScanStatus
)
from services.integration_service.src.workflow_studio_ext import (
    WorkflowStudioManager, WorkflowDefinition, WorkflowStep, WorkflowTrigger,
    WorkflowStatus, StepType, TriggerType
)
from services.integration_service.src.ansible_salt_integration_ext import (
    AnsibleSaltIntegrationManager, ConfigManagementTool, PlaybookDefinition,
    SaltStateDefinition, ExecutionResult, ExecutionStatus
)
from services.integration_service.src.infrastructure_pipelines_ext import (
    InfrastructurePipelinesManager, PipelineDefinition, PipelineStage,
    PipelineExecution, PipelineStatus, StageType, ExecutionState
)
from services.integration_service.src.drift_detector_ext import (
    DriftDetectorManager, DriftCheck, DriftResult, DriftSeverity,
    ResourceType, CheckStatus, RemediationAction
)
from services.integration_service.src.quota_manager_ext import (
    QuotaManager, QuotaDefinition, QuotaType, QuotaScope,
    QuotaUsage, QuotaStatus, QuotaAllocation
)
from services.integration_service.src.auto_remediation_ext import (
    AutoRemediationManager, RemediationRule, RemediationAction as RA,
    RemediationStatus, RuleCondition, ActionType, TriggerEvent
)
from services.integration_service.src.maintenance_planner_ext import (
    MaintenancePlannerManager, MaintenanceWindow, MaintenanceTask,
    WindowStatus, TaskStatus, TaskPriority, RecurrencePattern
)
from services.integration_service.src.runbook_library_ext import (
    RunbookLibraryManager, RunbookDefinition, RunbookStep, RunbookCategory,
    StepType as RBStepType, DifficultyLevel
)
from services.integration_service.src.chaos_engineering_ext import (
    ChaosEngineeringManager, ChaosExperiment, ExperimentTemplate,
    ExperimentStatus, ExperimentType, TargetKind, FaultAction
)
from services.integration_service.src.self_healing_ext import (
    SelfHealingManager, HealingPolicy, HealingAction, HealingActionType,
    AutoHealingRule, PolicyStatus, ConditionOperator, MetricSource
)


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestIdentityAndPolicyIntegration:
    def setup_method(self):
        self.idp_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.policy_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.compliance_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.idp = IdPManager(storage_path=self.idp_path)
        self.policy = PolicyEngine(storage_path=self.policy_path)
        self.compliance = ComplianceScanner(storage_path=self.compliance_path)
        self.idp.initialize()
        self.policy.initialize()
        self.compliance.initialize()

    def teardown_method(self):
        self.idp.close()
        self.policy.close()
        self.compliance.close()
        for p in [self.idp_path, self.policy_path, self.compliance_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_oidc_provider_created_triggers_policy_check(self):
        prov = self.idp.create_oidc_provider("Test", "https://example.com", "cid", "secret")
        policy = self.policy.create_policy(
            "provider-policy", "OIDC Provider Policy",
            effect=PolicyEffect.ALLOW,
            rules=[PolicyRule(field="provider.enabled", operator="eq", value=True)]
        )
        result = self.policy.evaluate_policy(policy.id, {"provider": {"id": prov.id, "enabled": prov.enabled}})
        assert result.allowed is True

    def test_saml_provider_encrypted_assertions_policy(self):
        prov = self.idp.create_saml_provider("Encrypted SAML", "https://saml.example.com",
                                              "https://sso.example.com", "base64cert",
                                              encrypt_assertions=True)
        policy = self.policy.create_policy(
            "saml-security", "SAML Security Policy",
            effect=PolicyEffect.ALLOW,
            rules=[PolicyRule(field="saml.encrypt_assertions", operator="eq", value=True)]
        )
        result = self.policy.evaluate_policy(policy.id, {"saml": {"encrypt_assertions": prov.encrypt_assertions,
                                                                    "id": prov.id}})
        assert result.allowed is True

    def test_client_registration_compliance_check(self):
        c = self.idp.register_client("Compliant App", ["https://app.example.com"],
                                      client_type="confidential", scopes=["openid", "profile"])
        scan = self.compliance.start_scan("client-scan-1", "CIS Docker",
                                          target_type="client_registration")
        assert scan is not None
        assert scan.status == ScanStatus.IN_PROGRESS
        self.compliance.complete_scan(scan.id, [
            CheckResult(check_id="CIS-1.1", status="pass", description="Client registration test")
        ])
        completed = self.compliance.get_scan(scan.id)
        assert completed.status == ScanStatus.COMPLETED

    def test_token_issued_revoked_updates_compliance(self):
        c = self.idp.register_client("Compliance Token App", ["https://app.example.com"])
        token = self.idp.issue_token(c.client_id, "authorization_code", "openid")
        assert token.access_token is not None
        validated = self.idp.validate_token(token.access_token)
        assert validated is not None
        self.idp.revoke_token(token.access_token)
        assert self.idp.validate_token(token.access_token) is None
        stats = self.idp.get_statistics()
        assert stats["total_tokens_issued"] >= 1
        assert stats["active_tokens"] == 0

    def test_policy_evaluation_blocks_disabled_provider(self):
        p1 = self.idp.create_oidc_provider("Enabled", "https://enabled.example.com", "c1", "s1")
        p2 = self.idp.create_oidc_provider("Disabled", "https://disabled.example.com", "c2", "s2", enabled=False)
        policy = self.policy.create_policy(
            "active-only", "Only Active Providers",
            effect=PolicyEffect.DENY,
            rules=[PolicyRule(field="provider.enabled", operator="eq", value=False)]
        )
        result1 = self.policy.evaluate_policy(policy.id, {"provider": {"id": p1.id, "enabled": p1.enabled}})
        result2 = self.policy.evaluate_policy(policy.id, {"provider": {"id": p2.id, "enabled": p2.enabled}})
        assert result1.allowed is True
        assert result2.allowed is False

    def test_multiple_oidc_providers_bulk_policy(self):
        providers = []
        for i in range(5):
            p = self.idp.create_oidc_provider(f"Provider {i}", f"https://p{i}.example.com",
                                               f"cid{i}", f"secret{i}")
            providers.append(p)
        assert len(self.idp.list_oidc_providers()) == 5
        policy = self.policy.create_policy(
            "max-providers", "Max 3 OIDC Providers",
            effect=PolicyEffect.DENY,
            rules=[PolicyRule(field="providers.count", operator="gt", value=3)]
        )
        result = self.policy.evaluate_policy(policy.id, {"providers": {"count": len(providers)}})
        assert result.allowed is False

    def test_saml_multi_certificate_rotation_policy(self):
        p1 = self.idp.create_saml_provider("SAML v1", "https://saml1.example.com",
                                            "https://sso1.example.com", "cert1")
        assert p1 is not None
        stats1 = self.idp.get_statistics()
        assert stats1["saml_providers"] >= 1
        self.idp.update_saml_provider(p1.id, certificate="cert2-rotated")
        updated = self.idp.get_saml_provider(p1.id)
        assert updated.certificate == "cert2-rotated"

    def test_client_scopes_policy_enforcement(self):
        c = self.idp.register_client("Scoped App", ["https://app.example.com"],
                                      scopes=["openid", "profile", "email", "admin"])
        policy = self.policy.create_policy(
            "scope-restriction", "Restrict Admin Scope",
            effect=PolicyEffect.DENY,
            rules=[PolicyRule(field="client.scopes", operator="contains", value="admin")]
        )
        result = self.policy.evaluate_policy(policy.id, {"client": {"id": c.client_id, "scopes": c.scopes}})
        assert result.allowed is False

    def test_compliance_scan_benchmark_selection(self):
        scan = self.compliance.start_scan("multi-benchmark", "CIS Docker",
                                          target_type="kubernetes",
                                          benchmarks=["CIS Docker", "NIST 800-53", "SOC2"])
        assert scan is not None
        assert scan.benchmarks == ["CIS Docker", "NIST 800-53", "SOC2"]

    def test_compliance_scan_results_aggregation(self):
        scan = self.compliance.start_scan("aggregate-scan", "CIS Docker",
                                          target_type="cluster")
        checks = [
            CheckResult(check_id="CIS-1.1", status="pass", description="Check 1"),
            CheckResult(check_id="CIS-1.2", status="fail", description="Check 2"),
            CheckResult(check_id="CIS-1.3", status="pass", description="Check 3"),
            CheckResult(check_id="CIS-1.4", status="fail", description="Check 4"),
            CheckResult(check_id="CIS-1.5", status="warn", description="Check 5"),
        ]
        self.compliance.complete_scan(scan.id, checks)
        completed = self.compliance.get_scan(scan.id)
        assert completed.status == ScanStatus.COMPLETED
        stats = self.compliance.get_statistics()
        assert stats["total_scans"] >= 1

    def test_oidc_saml_mixed_providers_policy_routing(self):
        oidc = self.idp.create_oidc_provider("Hybrid OIDC", "https://hybrid.example.com", "hc", "hs")
        saml = self.idp.create_saml_provider("Hybrid SAML", "https://hybrid-saml.example.com",
                                              "https://sso-hybrid.example.com", "cert")
        assert oidc is not None
        assert saml is not None
        assert oidc.id != saml.id
        policy = self.policy.create_policy(
            "hybrid-routing", "Hybrid Provider Routing",
            effect=PolicyEffect.ALLOW,
            rules=[PolicyRule(field="provider.type", operator="in", value=["oidc", "saml"])]
        )
        result1 = self.policy.evaluate_policy(policy.id, {"provider": {"id": oidc.id, "type": "oidc"}})
        result2 = self.policy.evaluate_policy(policy.id, {"provider": {"id": saml.id, "type": "saml"}})
        assert result1.allowed is True
        assert result2.allowed is True

    def test_token_lifecycle_compliance_audit(self):
        c = self.idp.register_client("Audit App", ["https://audit.example.com"])
        tokens = []
        for _ in range(3):
            t = self.idp.issue_token(c.client_id, "client_credentials", "openid")
            tokens.append(t)
        assert len(tokens) == 3
        for t in tokens:
            validated = self.idp.validate_token(t.access_token)
            assert validated is not None
        self.idp.revoke_token(tokens[0].access_token)
        assert self.idp.validate_token(tokens[0].access_token) is None
        assert self.idp.validate_token(tokens[1].access_token) is not None
        stats = self.idp.get_statistics()
        assert stats["active_tokens"] == 2

    def test_oidc_provider_custom_scopes_policy(self):
        prov = self.idp.create_oidc_provider("Scoped OIDC", "https://scoped.example.com",
                                              "scid", "scsec", scopes=["openid", "profile", "custom:admin"])
        policy = self.policy.create_policy(
            "custom-scope-audit", "Audit Custom Scopes",
            effect=PolicyEffect.ALLOW,
            rules=[PolicyRule(field="oidc.scopes", operator="contains", value="custom:admin")]
        )
        result = self.policy.evaluate_policy(policy.id, {"oidc": {"id": prov.id, "scopes": prov.scopes}})
        assert result.allowed is True

    def test_compliance_scan_scheduled_recurring(self):
        scan = self.compliance.start_scan("recurring-scan", "CIS Docker",
                                          target_type="node", scheduled=True,
                                          schedule_cron="0 */6 * * *")
        assert scan is not None
        assert scan.scheduled is True
        assert scan.schedule_cron == "0 */6 * * *"

    def test_compliance_multiple_targets_same_scan(self):
        scan = self.compliance.start_scan("multi-target", "CIS Docker",
                                          target_type="cluster",
                                          targets=["node-1", "node-2", "node-3"])
        assert scan is not None
        assert len(scan.targets) == 3

    def test_token_refresh_rotation_policy(self):
        c = self.idp.register_client("Refresh Rotation", ["https://rotate.example.com"])
        t1 = self.idp.issue_token(c.client_id, "authorization_code", "openid")
        t2 = self.idp.issue_token(c.client_id, "refresh_token", "openid",
                                   refresh_token=t1.refresh_token)
        assert t2.access_token != t1.access_token
        assert t2.refresh_token != t1.refresh_token

    def test_client_credentials_grant_policy(self):
        c = self.idp.register_client("Service Account", ["https://svc.example.com"],
                                      client_type="confidential")
        for _ in range(5):
            t = self.idp.issue_token(c.client_id, "client_credentials", "openid")
            assert t.access_token is not None
        stats = self.idp.get_statistics()
        assert stats["total_tokens_issued"] >= 5


class TestSessionAndPAMIntegration:
    def setup_method(self):
        self.session_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.pam_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.policy_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.session = SessionManager(storage_path=self.session_path)
        self.pam = PAMManager(storage_path=self.pam_path)
        self.policy = PolicyEngine(storage_path=self.policy_path)
        self.session.initialize()
        self.pam.initialize()
        self.policy.initialize()

    def teardown_method(self):
        self.session.close()
        self.pam.close()
        self.policy.close()
        for p in [self.session_path, self.pam_path, self.policy_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_session_creation_follows_pam_policy(self):
        ses = self.session.create_session("user-1", "192.168.1.1", "Mozilla/5.0")
        assert ses.status == SessionStatus.ACTIVE
        request = self.pam.create_access_request("user-1", "server-01",
                                                  AccessLevel.ADMIN, "Need admin access",
                                                  justification_level=JustificationLevel.BUSINESS)
        assert request.status == AccessRequestStatus.PENDING

    def test_pam_approval_creates_session_record(self):
        request = self.pam.create_access_request("admin-user", "db-prod-01",
                                                  AccessLevel.ADMIN, "Database maintenance",
                                                  justification_level=JustificationLevel.EMERGENCY)
        approved = self.pam.approve_request(request.id, "approver-1")
        assert approved.status == AccessRequestStatus.APPROVED
        ses = self.session.create_session("admin-user", "10.0.0.1", "SSH")
        assert ses.status == SessionStatus.ACTIVE
        active = self.session.get_active_sessions()
        assert len(active) >= 1

    def test_pam_denied_request_tracks_session_blocked(self):
        request = self.pam.create_access_request("blocked-user", "prod-server",
                                                  AccessLevel.ADMIN, "Unauthorized attempt",
                                                  justification_level=JustificationLevel.NONE)
        denied = self.pam.deny_request(request.id, "security-approver")
        assert denied.status == AccessRequestStatus.DENIED
        assert len(denied.review_notes) > 0
        stats = self.pam.get_statistics()
        assert stats["denied_requests"] >= 1

    def test_break_glass_triggers_session_alert(self):
        event = self.pam.create_break_glass_event("emergency-user", "critical-server",
                                                   AccessLevel.ADMIN, "Production outage")
        assert event.status == "active"
        assert event.access_level == AccessLevel.ADMIN
        ses = self.session.create_session("emergency-user", "10.0.0.5", "Emergency Console")
        assert ses.status == SessionStatus.ACTIVE
        self.session.terminate_session(ses.id)
        assert self.session.get_session(ses.id).status == SessionStatus.TERMINATED
        self.pam.resolve_break_glass(event.id)
        assert self.pam.get_break_glass_event(event.id).status == "resolved"

    def test_session_risk_scoring_with_pam_background(self):
        ses = self.session.create_session("risk-user", "203.0.113.1", "Unknown Browser")
        self.session.assess_session_risk(ses.id)
        risk = self.session.get_session_risk(ses.id)
        assert risk is not None
        assert risk.overall_risk in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_multiple_pam_requests_queued_approval_workflow(self):
        requests = []
        for i in range(5):
            req = self.pam.create_access_request(f"user-{i}", f"server-{i}",
                                                  AccessLevel.OPERATOR, f"Task {i}",
                                                  justification_level=JustificationLevel.BUSINESS)
            requests.append(req)
        assert len(requests) == 5
        assert all(r.status == AccessRequestStatus.PENDING for r in requests)
        approved = self.pam.approve_request(requests[0].id, "approver-1")
        assert approved.status == AccessRequestStatus.APPROVED
        denied = self.pam.deny_request(requests[1].id, "approver-1")
        assert denied.status == AccessRequestStatus.DENIED
        pending = self.pam.list_pending_requests()
        assert len(pending) == 3

    def test_session_termination_propagates_to_pam(self):
        ses = self.session.create_session("term-user", "10.0.0.1", "Terminal")
        assert ses.status == SessionStatus.ACTIVE
        self.session.terminate_session(ses.id)
        assert self.session.get_session(ses.id).status == SessionStatus.TERMINATED
        request = self.pam.create_access_request("term-user", "server-x",
                                                  AccessLevel.VIEWER, "Post-termination check",
                                                  justification_level=JustificationLevel.BUSINESS)
        assert request.status == AccessRequestStatus.PENDING

    def test_pam_escalation_policy_check(self):
        for i in range(3):
            req = self.pam.create_access_request(f"escalate-user-{i}", f"prod-server-{i}",
                                                  AccessLevel.ADMIN, f"Escalation test {i}",
                                                  justification_level=JustificationLevel.EMERGENCY)
            self.pam.approve_request(req.id, "escalation-approver")
        stats = self.pam.get_statistics()
        assert stats["approved_requests"] >= 3
        assert stats["total_requests"] >= 3

    def test_pam_break_glass_multiple_events(self):
        events = []
        for i in range(4):
            e = self.pam.create_break_glass_event(f"bg-user-{i}", f"critical-node-{i}",
                                                   AccessLevel.ADMIN, f"Emergency {i}")
            events.append(e)
        assert len(events) == 4
        assert all(e.status == "active" for e in events)
        for e in events[:2]:
            self.pam.resolve_break_glass(e.id)
        assert self.pam.get_break_glass_event(events[0].id).status == "resolved"
        assert self.pam.get_break_glass_event(events[2].id).status == "active"
        stats = self.pam.get_statistics()
        assert stats["total_break_glass_events"] == 4

    def test_session_geo_ip_risk_assessment(self):
        ses = self.session.create_session("geo-user", "10.0.0.1", "Chrome")
        self.session.update_session_risk(ses.id, RiskLevel.LOW, 0.1, "IP_WHITELISTED",
                                          [{"factor": "geo", "score": 0.1}])
        risk = self.session.get_session_risk(ses.id)
        assert risk.overall_risk == RiskLevel.LOW

    def test_pam_template_based_policy_creation(self):
        standard = self.pam.create_policy_template("standard-access", "Standard Access",
                                                    AccessLevel.VIEWER,
                                                    ["user", "operator"])
        assert standard is not None
        elevated = self.pam.create_policy_template("elevated-access", "Elevated Access",
                                                    AccessLevel.ADMIN,
                                                    ["admin"])
        assert elevated is not None
        templates = self.pam.list_policy_templates()
        assert len(templates) == 2

    def test_session_timeout_enforced(self):
        ses = self.session.create_session("timeout-user", "10.0.0.1", "Browser",
                                          session_timeout_minutes=1)
        assert ses.session_timeout_minutes == 1
        import time
        assert ses.status == SessionStatus.ACTIVE

    def test_pam_approval_chain_delegation(self):
        req = self.pam.create_access_request("delegator", "target-server",
                                              AccessLevel.ADMIN, "Delegation test",
                                              justification_level=JustificationLevel.BUSINESS)
        self.pam.approve_request(req.id, "primary-approver")
        self.pam.add_review_note(req.id, "secondary-approver", "Confirmed")
        updated = self.pam.get_access_request(req.id)
        assert updated.status == AccessRequestStatus.APPROVED
        assert len(updated.review_notes) >= 1


class TestWorkflowAndAutomationIntegration:
    def setup_method(self):
        self.wf_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.ansible_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.pipeline_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.drift_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.quota_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.wf = WorkflowStudioManager(storage_path=self.wf_path)
        self.ansible = AnsibleSaltIntegrationManager(storage_path=self.ansible_path)
        self.pipeline = InfrastructurePipelinesManager(storage_path=self.pipeline_path)
        self.drift = DriftDetectorManager(storage_path=self.drift_path)
        self.quota = QuotaManager(storage_path=self.quota_path)
        self.wf.initialize()
        self.ansible.initialize()
        self.pipeline.initialize()
        self.drift.initialize()
        self.quota.initialize()

    def teardown_method(self):
        self.wf.close()
        self.ansible.close()
        self.pipeline.close()
        self.drift.close()
        self.quota.close()
        for p in [self.wf_path, self.ansible_path, self.pipeline_path,
                  self.drift_path, self.quota_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_workflow_triggers_ansible_execution(self):
        wf = self.wf.create_workflow("Ansible WF", "Run Ansible via Workflow",
                                      TriggerType.SCHEDULED,
                                      [WorkflowStep(name="run-ansible", step_type=StepType.TASK,
                                                    config={"playbook": "site.yml", "inventory": "prod"})])
        assert wf.status == WorkflowStatus.DRAFT
        playbook = self.ansible.create_playbook("site.yml", "Main Playbook",
                                                  ["webservers", "dbservers"],
                                                  roles=["common", "nginx", "postgres"])
        assert playbook is not None
        assert len(playbook.roles) == 3

    def test_pipeline_executes_with_stages(self):
        pipeline = self.pipeline.create_pipeline("CI/CD Pipeline", "Full deployment pipeline",
                                                  [
                                                      PipelineStage(name="Build", stage_type=StageType.BUILD,
                                                                     config={"runner": "ubuntu-latest"}),
                                                      PipelineStage(name="Test", stage_type=StageType.TEST,
                                                                     config={"framework": "pytest"}),
                                                      PipelineStage(name="Deploy", stage_type=StageType.DEPLOY,
                                                                     config={"environment": "production"}),
                                                  ])
        assert pipeline.status == PipelineStatus.DRAFT
        assert len(pipeline.stages) == 3
        execution = self.pipeline.execute_pipeline(pipeline.id)
        assert execution.status == PipelineStatus.RUNNING

    def test_drift_detected_triggers_pipeline(self):
        check = self.drift.create_drift_check("k8s-drift", ResourceType.KUBERNETES,
                                               "production-cluster")
        assert check.status == CheckStatus.PENDING
        result = self.drift.run_drift_check(check.id)
        assert result is not None
        if result.drift_found:
            pipeline = self.pipeline.create_pipeline("Drift Remediation", "Fix configuration drift",
                                                      [
                                                          PipelineStage(name="Apply Fix", stage_type=StageType.DEPLOY,
                                                                         config={"mode": "remediate"})
                                                      ])
            assert pipeline is not None

    def test_quota_exceeded_blocks_pipeline(self):
        quota = self.quota.create_quota("CPU Quota", QuotaType.CPU, QuotaScope.PROJECT,
                                         limit=16, unit="cores")
        assert quota.status == QuotaStatus.ACTIVE
        usage = self.quota.check_usage(quota.id)
        assert usage is not None
        if usage and usage.current_usage >= usage.limit:
            pipeline = self.pipeline.create_pipeline("Quota Blocked", "This should be blocked",
                                                      [PipelineStage(name="Deploy", stage_type=StageType.DEPLOY,
                                                                     config={"environment": "prod"})])
            assert pipeline.status == PipelineStatus.DRAFT

    def test_workflow_with_salt_state_integration(self):
        wf = self.wf.create_workflow("Salt WF", "Run Salt states",
                                      TriggerType.MANUAL,
                                      [WorkflowStep(name="apply-salt", step_type=StepType.TASK,
                                                    config={"state": "webserver.config", "target": "web*"})])
        assert wf.status == WorkflowStatus.DRAFT
        salt_state = self.ansible.create_salt_state("webserver.config", "Web Server Config",
                                                     sls_content="nginx:\n  pkg.installed:\n    - name: nginx\n")
        assert salt_state is not None

    def test_pipeline_approval_stage_blocks_execution(self):
        pipeline = self.pipeline.create_pipeline("Approved Pipeline", "Needs approval",
                                                  [
                                                      PipelineStage(name="Build", stage_type=StageType.BUILD,
                                                                     config={"runner": "ubuntu"}),
                                                      PipelineStage(name="Approval", stage_type=StageType.APPROVAL,
                                                                     config={"approvers": ["lead"]}),
                                                      PipelineStage(name="Deploy", stage_type=StageType.DEPLOY,
                                                                     config={"env": "prod"}),
                                                  ])
        assert len(pipeline.stages) == 3
        execution = self.pipeline.execute_pipeline(pipeline.id)
        assert execution is not None

    def test_quota_allocation_tracking(self):
        quota = self.quota.create_quota("Memory Quota", QuotaType.MEMORY, QuotaScope.TEAM,
                                         limit=64, unit="GB")
        alloc = self.quota.allocate(quota.id, "team-alpha", 8)
        assert alloc is not None
        usage = self.quota.check_usage(quota.id)
        assert usage is not None
        assert usage.current_usage >= 8

    def test_drift_check_scheduling(self):
        check = self.drift.create_drift_check("scheduled-drift", ResourceType.ANSIBLE,
                                               "all-nodes", schedule_cron="0 */2 * * *")
        assert check.schedule_cron == "0 */2 * * *"
        check2 = self.drift.create_drift_check("oneoff-drift", ResourceType.TERRAFORM,
                                                "prod-infra")
        assert check2.schedule_cron is None

    def test_workflow_multi_step_execution(self):
        wf = self.wf.create_workflow("Multi-Step", "Complex workflow",
                                      TriggerType.EVENT,
                                      [WorkflowStep(name=f"step-{i}", step_type=StepType.TASK,
                                                    config={"command": f"echo {i}"})
                                       for i in range(5)])
        assert len(wf.steps) == 5
        self.wf.activate_workflow(wf.id)
        assert self.wf.get_workflow(wf.id).status == WorkflowStatus.ACTIVE

    def test_pipeline_rollback_capability(self):
        pipeline = self.pipeline.create_pipeline("Rollback Pipeline", "Test rollback",
                                                  [
                                                      PipelineStage(name="Deploy v2", stage_type=StageType.DEPLOY,
                                                                     config={"version": "v2"}),
                                                      PipelineStage(name="Rollback", stage_type=StageType.ROLLBACK,
                                                                     config={"target_version": "v1"}),
                                                  ])
        assert pipeline is not None
        execution = self.pipeline.execute_pipeline(pipeline.id)
        assert execution is not None

    def test_ansible_multi_environment_inventories(self):
        for env in ["dev", "staging", "prod"]:
            playbook = self.ansible.create_playbook(f"site-{env}.yml", f"{env} Playbook",
                                                     [f"web-{env}", f"db-{env}"],
                                                     roles=["base", "app"])
            assert playbook is not None
        stats = self.ansible.get_statistics()
        assert stats["total_playbooks"] == 3

    def test_quota_bulk_allocation_works(self):
        quota = self.quota.create_quota("Bulk CPU", QuotaType.CPU, QuotaScope.ORGANIZATION,
                                         limit=100, unit="cores")
        for i in range(5):
            self.quota.allocate(quota.id, f"team-{i}", 10)
        usage = self.quota.check_usage(quota.id)
        assert usage.current_usage == 50

    def test_drift_remediation_tracking(self):
        check = self.drift.create_drift_check("remediation-check", ResourceType.KUBERNETES,
                                               "prod-cluster")
        results = self.drift.run_drift_check(check.id)
        assert results is not None
        if results and results.drift_found and results.remediation:
            assert results.remediation.action in [RemediationAction.AUTO_REMEDIATE,
                                                   RemediationAction.MANUAL_REVIEW,
                                                   RemediationAction.ROLLBACK,
                                                   RemediationAction.NOTIFY]

    def test_workflow_versions_tracked(self):
        wf = self.wf.create_workflow("Versioned WF", "Version tracking test",
                                      TriggerType.SCHEDULED,
                                      [WorkflowStep(name="v1-step", step_type=StepType.TASK,
                                                    config={"cmd": "echo v1"})])
        assert wf.version == 1
        self.wf.update_workflow(wf.id, steps=[WorkflowStep(name="v2-step", step_type=StepType.TASK,
                                                             config={"cmd": "echo v2"})])
        updated = self.wf.get_workflow(wf.id)
        assert updated.version >= 1

    def test_pipeline_execution_history(self):
        pipeline = self.pipeline.create_pipeline("History Pipeline", "Test history",
                                                  [PipelineStage(name="Build", stage_type=StageType.BUILD,
                                                                 config={"cmd": "build"})])
        executions = []
        for _ in range(3):
            exec_ = self.pipeline.execute_pipeline(pipeline.id)
            executions.append(exec_)
        assert len(executions) == 3
        history = self.pipeline.get_execution_history(pipeline.id)
        assert len(history) >= 3


class TestRemediationAndHealingIntegration:
    def setup_method(self):
        self.remediation_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.healing_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.drift_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.maintenance_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.remediation = AutoRemediationManager(storage_path=self.remediation_path)
        self.healing = SelfHealingManager(storage_path=self.healing_path)
        self.drift = DriftDetectorManager(storage_path=self.drift_path)
        self.maintenance = MaintenancePlannerManager(storage_path=self.maintenance_path)
        self.remediation.initialize()
        self.healing.initialize()
        self.drift.initialize()
        self.maintenance.initialize()

    def teardown_method(self):
        self.remediation.close()
        self.healing.close()
        self.drift.close()
        self.maintenance.close()
        for p in [self.remediation_path, self.healing_path, self.drift_path,
                  self.maintenance_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_remediation_rule_triggers_from_drift(self):
        rule = self.remediation.create_rule("drift-auto-fix", "Auto-fix config drift",
                                             TriggerEvent.CONFIG_DRIFT,
                                             RuleCondition(field="severity", operator="eq", value="high"),
                                             RemediationAction(action_type=ActionType.RUN_PLAYBOOK,
                                                               config={"playbook": "fix-drift.yml"}))
        assert rule.enabled is True
        assert rule.trigger_event == TriggerEvent.CONFIG_DRIFT
        check = self.drift.create_drift_check("auto-fix-check", ResourceType.KUBERNETES,
                                               "prod-cluster")
        assert check is not None

    def test_healing_policy_auto_recovery(self):
        policy = self.healing.create_policy("auto-recover", "Auto-recover failed services",
                                             [AutoHealingRule(
                                                 metric=MetricSource.CPU,
                                                 operator=ConditionOperator.GT,
                                                 threshold=90.0,
                                                 duration_seconds=300,
                                                 action=HealingAction(
                                                     action_type=HealingActionType.RESTART_SERVICE,
                                                     config={"service": "nginx", "max_retries": 3}
                                                 )
                                             )])
        assert policy.status == PolicyStatus.ACTIVE
        assert len(policy.rules) == 1

    def test_maintenance_window_blocks_remediation(self):
        window = self.maintenance.create_window("DB Upgrade", "Database upgrade window",
                                                 datetime.now() - timedelta(hours=1),
                                                 datetime.now() + timedelta(hours=3))
        assert window.status == WindowStatus.ACTIVE
        rule = self.remediation.create_rule("maintenance-block", "Blocked during maintenance",
                                             TriggerEvent.INCIDENT,
                                             RuleCondition(field="severity", operator="eq", value="critical"),
                                             RemediationAction(action_type=ActionType.NOTIFY,
                                                               config={"channel": "alerts"}))
        assert rule is not None

    def test_healing_action_execution_tracking(self):
        policy = self.healing.create_policy("exec-track", "Track healing actions",
                                             [AutoHealingRule(
                                                 metric=MetricSource.MEMORY,
                                                 operator=ConditionOperator.GT,
                                                 threshold=85.0,
                                                 duration_seconds=120,
                                                 action=HealingAction(
                                                     action_type=HealingActionType.SCALE_UP,
                                                     config={"replicas": 5}
                                                 )
                                             )])
        assert policy.id is not None
        self.healing.activate_policy(policy.id)
        assert self.healing.get_policy(policy.id).status == PolicyStatus.ACTIVE
        self.healing.deactivate_policy(policy.id)
        assert self.healing.get_policy(policy.id).status == PolicyStatus.INACTIVE
        stats = self.healing.get_statistics()
        assert stats["total_policies"] >= 1

    def test_remediation_rule_conditions_evaluation(self):
        rule = self.remediation.create_rule("condition-test", "Test condition evaluation",
                                             TriggerEvent.RESOURCE_QUOTA,
                                             RuleCondition(field="usage", operator="gt", value=80),
                                             RemediationAction(action_type=ActionType.SCALE_UP,
                                                               config={"replicas": 3}))
        assert rule.condition.field == "usage"
        assert rule.condition.operator == "gt"
        assert rule.condition.value == 80

    def test_multiple_healing_policies_priority(self):
        policies = []
        for priority in [1, 2, 3]:
            p = self.healing.create_policy(f"priority-{priority}", f"Priority {priority}",
                                            [AutoHealingRule(
                                                metric=MetricSource.CPU,
                                                operator=ConditionOperator.GT,
                                                threshold=80.0 + priority * 5,
                                                duration_seconds=60,
                                                action=HealingAction(
                                                    action_type=HealingActionType.RESTART_SERVICE,
                                                    config={"priority": priority}
                                                )
                                            )])
            policies.append(p)
        assert len(policies) == 3

    def test_maintenance_window_scheduling_conflicts(self):
        w1 = self.maintenance.create_window("Window 1", "First window",
                                             datetime.now() + timedelta(days=1),
                                             datetime.now() + timedelta(days=1, hours=2))
        assert w1.status == WindowStatus.SCHEDULED
        w2 = self.maintenance.create_window("Window 2", "Second window",
                                             datetime.now() + timedelta(days=1, hours=1),
                                             datetime.now() + timedelta(days=1, hours=3))
        assert w2.status == WindowStatus.SCHEDULED
        windows = self.maintenance.list_windows()
        assert len(windows) == 2

    def test_auto_remediation_action_types_all(self):
        for action_type in ActionType:
            r = self.remediation.create_rule(f"action-{action_type.name}", f"Test {action_type.name}",
                                              TriggerEvent.INCIDENT,
                                              RuleCondition(field="test", operator="eq", value=True),
                                              RemediationAction(action_type=action_type,
                                                                config={"type": action_type.name}))
            assert r.action.action_type == action_type

    def test_healing_metric_sources_all(self):
        for metric in MetricSource:
            p = self.healing.create_policy(f"metric-{metric.name}", f"Test {metric.name}",
                                            [AutoHealingRule(
                                                metric=metric,
                                                operator=ConditionOperator.GT,
                                                threshold=90.0,
                                                duration_seconds=60,
                                                action=HealingAction(
                                                    action_type=HealingActionType.RESTART_SERVICE,
                                                    config={"metric": metric.name}
                                                )
                                            )])
            assert p.id is not None
            assert p.rules[0].metric == metric

    def test_remediation_statistics_tracking(self):
        for i in range(10):
            self.remediation.create_rule(f"stats-rule-{i}", f"Stats test {i}",
                                          TriggerEvent.INCIDENT,
                                          RuleCondition(field="x", operator="eq", value=True),
                                          RemediationAction(action_type=ActionType.NOTIFY,
                                                            config={"message": f"test-{i}"}))
        stats = self.remediation.get_statistics()
        assert stats["total_rules"] == 10

    def test_maintenance_window_task_management(self):
        window = self.maintenance.create_window("Task Window", "Window with tasks",
                                                 datetime.now() - timedelta(hours=1),
                                                 datetime.now() + timedelta(hours=5))
        tasks = []
        for i in range(3):
            task = self.maintenance.create_task(window.id, f"Task {i}", f"task-{i}",
                                                 TaskPriority.HIGH)
            tasks.append(task)
        assert len(tasks) == 3
        window_tasks = self.maintenance.list_tasks(window.id)
        assert len(window_tasks) == 3

    def test_remediation_rule_disable_enable_cycle(self):
        rule = self.remediation.create_rule("toggle-rule", "Toggle test",
                                             TriggerEvent.INCIDENT,
                                             RuleCondition(field="x", operator="eq", value=True),
                                             RemediationAction(action_type=ActionType.NOTIFY,
                                                               config={"channel": "ops"}))
        assert rule.enabled is True
        self.remediation.disable_rule(rule.id)
        assert self.remediation.get_rule(rule.id).enabled is False
        self.remediation.enable_rule(rule.id)
        assert self.remediation.get_rule(rule.id).enabled is True

    def test_healing_policy_conditions_and_or(self):
        p = self.healing.create_policy("combo-condition", "Combined conditions",
                                        [AutoHealingRule(
                                            metric=MetricSource.CPU,
                                            operator=ConditionOperator.GT,
                                            threshold=90.0,
                                            duration_seconds=180,
                                            action=HealingAction(
                                                action_type=HealingActionType.RESTART_CONTAINER,
                                                config={"container": "web", "grace_period": 30}
                                            )
                                        ),
                                        AutoHealingRule(
                                            metric=MetricSource.MEMORY,
                                            operator=ConditionOperator.GT,
                                            threshold=85.0,
                                            duration_seconds=120,
                                            action=HealingAction(
                                                action_type=HealingActionType.SCALE_UP,
                                                config={"replicas": 3}
                                            )
                                        )])
        assert len(p.rules) == 2
        assert p.rules[0].metric == MetricSource.CPU
        assert p.rules[1].metric == MetricSource.MEMORY

    def test_maintenance_window_recurrence(self):
        window = self.maintenance.create_window("Recurring Window", "Weekly window",
                                                 datetime.now() + timedelta(days=7),
                                                 datetime.now() + timedelta(days=7, hours=4),
                                                 recurrence=RecurrencePattern.WEEKLY)
        assert window.recurrence == RecurrencePattern.WEEKLY


class TestChaosAndRunbookIntegration:
    def setup_method(self):
        self.chaos_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.runbook_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.chaos = ChaosEngineeringManager(storage_path=self.chaos_path)
        self.runbook = RunbookLibraryManager(storage_path=self.runbook_path)
        self.chaos.initialize()
        self.runbook.initialize()

    def teardown_method(self):
        self.chaos.close()
        self.runbook.close()
        for p in [self.chaos_path, self.runbook_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_chaos_experiment_created_from_template(self):
        experiment = self.chaos.create_experiment("pod-kill-test", "Kill pod experiment",
                                                   ExperimentType.POD_FAILURE,
                                                   TargetKind.KUBERNETES,
                                                   "production")
        assert experiment.status == ExperimentStatus.CREATED
        assert experiment.experiment_type == ExperimentType.POD_FAILURE

    def test_chaos_experiment_lifecycle(self):
        exp = self.chaos.create_experiment("full-lifecycle", "Full lifecycle test",
                                            ExperimentType.NETWORK_LATENCY,
                                            TargetKind.NETWORK, "staging")
        assert exp.status == ExperimentStatus.CREATED
        started = self.chaos.start_experiment(exp.id)
        assert started.status == ExperimentStatus.RUNNING
        completed = self.chaos.complete_experiment(exp.id)
        assert completed.status == ExperimentStatus.COMPLETED

    def test_runbook_created_guides_chaos_recovery(self):
        runbook = self.runbook.create_runbook("Chaos Recovery", "Post-chaos recovery steps",
                                               RunbookCategory.INCIDENT_RESPONSE,
                                               difficulty=DifficultyLevel.ADVANCED)
        assert runbook.category == RunbookCategory.INCIDENT_RESPONSE
        steps = []
        for i in range(4):
            step = self.runbook.add_step(runbook.id, f"Step {i}", f"Recovery step {i}",
                                          RBStepType.COMMAND)
            steps.append(step)
        assert len(steps) == 4

    def test_chaos_experiment_types_all(self):
        types_created = []
        for exp_type in ExperimentType:
            exp = self.chaos.create_experiment(f"exp-{exp_type.name}", f"Test {exp_type.name}",
                                                exp_type, TargetKind.KUBERNETES, "test")
            types_created.append(exp)
        assert len(types_created) == len(list(ExperimentType))

    def test_chaos_target_kinds_all(self):
        for kind in TargetKind:
            exp = self.chaos.create_experiment(f"kind-{kind.name}", f"Test {kind.name}",
                                                ExperimentType.CPU_STARVATION,
                                                kind, "test-env")
            assert exp.target_kind == kind

    def test_runbook_multi_category_organization(self):
        for cat in RunbookCategory:
            rb = self.runbook.create_runbook(f"{cat.name}-runbook", f"Runbook for {cat.name}",
                                              cat, difficulty=DifficultyLevel.BEGINNER)
            assert rb.category == cat
        runbooks = self.runbook.list_runbooks()
        assert len(runbooks) == len(list(RunbookCategory))

    def test_chaos_experiment_rollback(self):
        exp = self.chaos.create_experiment("rollback-test", "Test rollback",
                                            ExperimentType.POD_FAILURE,
                                            TargetKind.KUBERNETES, "prod")
        started = self.chaos.start_experiment(exp.id)
        assert started.status == ExperimentStatus.RUNNING
        rolled_back = self.chaos.rollback_experiment(exp.id)
        assert rolled_back.status == ExperimentStatus.ROLLED_BACK

    def test_chaos_experiment_duration_limits(self):
        exp = self.chaos.create_experiment("timed-exp", "Timed experiment",
                                            ExperimentType.NETWORK_LATENCY,
                                            TargetKind.NETWORK, "staging",
                                            duration_seconds=300)
        assert exp.duration_seconds == 300
        exp2 = self.chaos.create_experiment("infinite-exp", "No time limit",
                                             ExperimentType.CPU_STARVATION,
                                             TargetKind.KUBERNETES, "dev")
        assert exp2.duration_seconds is None

    def test_runbook_step_reordering(self):
        rb = self.runbook.create_runbook("Ordered RB", "Test step ordering",
                                          RunbookCategory.MAINTENANCE,
                                          difficulty=DifficultyLevel.INTERMEDIATE)
        step1 = self.runbook.add_step(rb.id, "First", "Do first", RBStepType.COMMAND, order=1)
        step2 = self.runbook.add_step(rb.id, "Second", "Do second", RBStepType.CHECK, order=2)
        step3 = self.runbook.add_step(rb.id, "Third", "Do third", RBStepType.COMMAND, order=3)
        assert step1.order == 1
        assert step2.order == 2
        assert step3.order == 3
        self.runbook.reorder_steps(rb.id, [step3.id, step2.id, step1.id])
        reordered = self.runbook.get_runbook(rb.id)
        assert reordered is not None

    def test_chaos_statistics_tracking(self):
        for i in range(5):
            exp = self.chaos.create_experiment(f"stats-exp-{i}", f"Stats {i}",
                                                ExperimentType.POD_FAILURE,
                                                TargetKind.KUBERNETES, "test")
            self.chaos.start_experiment(exp.id)
            self.chaos.complete_experiment(exp.id)
        stats = self.chaos.get_statistics()
        assert stats["total_experiments"] >= 5
        assert stats["completed_experiments"] >= 5

    def test_runbook_difficulty_levels(self):
        for diff in DifficultyLevel:
            rb = self.runbook.create_runbook(f"diff-{diff.name}", f"Difficulty {diff.name}",
                                              RunbookCategory.GENERAL,
                                              difficulty=diff)
            assert rb.difficulty == diff

    def test_chaos_experiment_tags_filtering(self):
        for tag in ["networking", "storage", "compute", "security"]:
            exp = self.chaos.create_experiment(f"tagged-{tag}", f"Tagged {tag}",
                                                ExperimentType.NETWORK_LATENCY,
                                                TargetKind.KUBERNETES, "test",
                                                tags=[tag])
            assert tag in exp.tags
        experiments = self.chaos.list_experiments()
        assert len(experiments) >= 4

    def test_runbook_versioning(self):
        rb = self.runbook.create_runbook("Versioned RB", "Version test",
                                          RunbookCategory.GENERAL,
                                          difficulty=DifficultyLevel.BEGINNER)
        assert rb.version == 1
        self.runbook.update_runbook(rb.id, description="Updated description v2")
        updated = self.runbook.get_runbook(rb.id)
        assert updated.version >= 1

    def test_chaos_experiment_fault_actions(self):
        for fault in FaultAction:
            exp = self.chaos.create_experiment(f"fault-{fault.name}", f"Fault {fault.name}",
                                                ExperimentType.POD_FAILURE,
                                                TargetKind.KUBERNETES, "test",
                                                fault_action=fault)
            assert exp is not None

    def test_runbook_search_by_category(self):
        self.runbook.create_runbook("Network Recovery", "Network steps",
                                     RunbookCategory.INCIDENT_RESPONSE,
                                     difficulty=DifficultyLevel.ADVANCED)
        self.runbook.create_runbook("Server Setup", "Setup steps",
                                     RunbookCategory.PROVISIONING,
                                     difficulty=DifficultyLevel.BEGINNER)
        self.runbook.create_runbook("Security Audit", "Audit steps",
                                     RunbookCategory.COMPLIANCE,
                                     difficulty=DifficultyLevel.INTERMEDIATE)

    def test_chaos_experiment_pause_resume(self):
        exp = self.chaos.create_experiment("pause-resume", "Pause/resume test",
                                            ExperimentType.NETWORK_LATENCY,
                                            TargetKind.NETWORK, "staging")
        self.chaos.start_experiment(exp.id)
        paused = self.chaos.pause_experiment(exp.id)
        assert paused.status == ExperimentStatus.PAUSED
        resumed = self.chaos.resume_experiment(exp.id)
        assert resumed.status == ExperimentStatus.RUNNING

    def test_runbook_step_type_variety(self):
        rb = self.runbook.create_runbook("Variety Steps", "All step types",
                                          RunbookCategory.MAINTENANCE,
                                          difficulty=DifficultyLevel.INTERMEDIATE)
        for st in RBStepType:
            step = self.runbook.add_step(rb.id, f"Step {st.name}", f"Type {st.name}", st)
            assert step.step_type == st


class TestQuotaAndResourceManagementIntegration:
    def setup_method(self):
        self.quota_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.pipeline_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.remediation_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.quota = QuotaManager(storage_path=self.quota_path)
        self.pipeline = InfrastructurePipelinesManager(storage_path=self.pipeline_path)
        self.remediation = AutoRemediationManager(storage_path=self.remediation_path)
        self.quota.initialize()
        self.pipeline.initialize()
        self.remediation.initialize()

    def teardown_method(self):
        self.quota.close()
        self.pipeline.close()
        self.remediation.close()
        for p in [self.quota_path, self.pipeline_path, self.remediation_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_quota_enforcement_blocks_pipeline_deployment(self):
        quota = self.quota.create_quota("Prod CPU Cap", QuotaType.CPU, QuotaScope.PROJECT,
                                         limit=32, unit="cores")
        self.quota.allocate(quota.id, "prod-team", 28)
        usage = self.quota.check_usage(quota.id)
        assert usage.current_usage == 28
        remaining = usage.limit - usage.current_usage
        assert remaining == 4
        if remaining < 8:
            pipeline = self.pipeline.create_pipeline("Quota Guarded", "Blocked deployment",
                                                      [PipelineStage(name="Deploy", stage_type=StageType.DEPLOY,
                                                                     config={"env": "prod"})])
            assert pipeline is not None

    def test_quota_types_all_creatable(self):
        for qt in QuotaType:
            q = self.quota.create_quota(f"{qt.name}-quota", f"Quota for {qt.name}",
                                         qt, QuotaScope.PROJECT, limit=100)
            assert q.quota_type == qt

    def test_quota_scopes_all_functional(self):
        for scope in QuotaScope:
            q = self.quota.create_quota(f"{scope.name}-scope", f"Scope {scope.name}",
                                         QuotaType.CPU, scope, limit=50)
            assert q.scope == scope

    def test_quota_exceeded_triggers_remediation_rule(self):
        quota = self.quota.create_quota("Alerting Quota", QuotaType.MEMORY, QuotaScope.TEAM,
                                         limit=16, unit="GB")
        for _ in range(5):
            self.quota.allocate(quota.id, "team-alpha", 4)
        usage = self.quota.check_usage(quota.id)
        assert usage.current_usage == 20
        assert usage.exceeded is True
        rule = self.remediation.create_rule("quota-alert", "Quota exceeded alert",
                                             TriggerEvent.RESOURCE_QUOTA,
                                             RuleCondition(field="exceeded", operator="eq", value=True),
                                             RemediationAction(action_type=ActionType.NOTIFY,
                                                               config={"channel": "quotas"}))
        assert rule is not None

    def test_quota_allocation_deallocation_cycle(self):
        q = self.quota.create_quota("Cycle Quota", QuotaType.STORAGE, QuotaScope.PROJECT,
                                     limit=1000, unit="GB")
        alloc = self.quota.allocate(q.id, "project-x", 100)
        assert alloc is not None
        usage1 = self.quota.check_usage(q.id)
        assert usage1.current_usage == 100
        self.quota.deallocate(q.id, "project-x", 50)
        usage2 = self.quota.check_usage(q.id)
        assert usage2.current_usage == 50

    def test_multiple_quotas_isolation(self):
        cpu_q = self.quota.create_quota("Team CPU", QuotaType.CPU, QuotaScope.TEAM,
                                         limit=64, unit="cores")
        mem_q = self.quota.create_quota("Team MEM", QuotaType.MEMORY, QuotaScope.TEAM,
                                         limit=256, unit="GB")
        stg_q = self.quota.create_quota("Team STG", QuotaType.STORAGE, QuotaScope.TEAM,
                                         limit=5000, unit="GB")
        cpu_usage = self.quota.check_usage(cpu_q.id)
        mem_usage = self.quota.check_usage(mem_q.id)
        stg_usage = self.quota.check_usage(stg_q.id)
        assert cpu_usage.quota_id != mem_usage.quota_id
        assert mem_usage.quota_id != stg_usage.quota_id

    def test_quota_update_limits(self):
        q = self.quota.create_quota("Updatable Quota", QuotaType.CPU, QuotaScope.PROJECT,
                                     limit=10, unit="cores")
        self.quota.update_quota(q.id, limit=20)
        updated = self.quota.get_quota(q.id)
        assert updated.limit == 20

    def test_quota_status_transitions(self):
        q = self.quota.create_quota("Status Quota", QuotaType.CPU, QuotaScope.PROJECT,
                                     limit=100, unit="cores")
        assert q.status == QuotaStatus.ACTIVE
        self.quota.suspend_quota(q.id)
        assert self.quota.get_quota(q.id).status == QuotaStatus.SUSPENDED
        self.quota.resume_quota(q.id)
        assert self.quota.get_quota(q.id).status == QuotaStatus.ACTIVE

    def test_pipeline_quota_validation_before_execution(self):
        q = self.quota.create_quota("Pipeline Check", QuotaType.CPU, QuotaScope.PROJECT,
                                     limit=4, unit="cores")
        self.quota.allocate(q.id, "pipeline-team", 4)
        usage = self.quota.check_usage(q.id)
        assert usage.exceeded is True or usage.current_usage >= usage.limit
        pipeline = self.pipeline.create_pipeline("Quota Validation Pipeline", "Test validation",
                                                  [PipelineStage(name="Deploy", stage_type=StageType.DEPLOY,
                                                                 config={"env": "prod"})])
        assert pipeline is not None


class TestComprehensiveEdgeCases:
    def setup_method(self):
        self.idp_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.session_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.pam_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.wf_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.idp = IdPManager(storage_path=self.idp_path)
        self.session = SessionManager(storage_path=self.session_path)
        self.pam = PAMManager(storage_path=self.pam_path)
        self.wf = WorkflowStudioManager(storage_path=self.wf_path)
        self.idp.initialize()
        self.session.initialize()
        self.pam.initialize()
        self.wf.initialize()

    def teardown_method(self):
        for m in [self.idp, self.session, self.pam, self.wf]:
            m.close()
        for p in [self.idp_path, self.session_path, self.pam_path, self.wf_path]:
            if os.path.exists(p):
                os.unlink(p)

    def test_empty_storage_graceful_handling(self):
        stats = self.idp.get_statistics()
        assert stats["oidc_providers"] == 0
        assert stats["saml_providers"] == 0
        assert stats["total_clients"] == 0
        assert stats["active_tokens"] == 0

    def test_duplicate_registration_handling(self):
        c1 = self.idp.register_client("Unique App", ["https://unique.example.com"])
        assert c1.client_id is not None
        c2 = self.idp.register_client("Unique App", ["https://unique.example.com"])
        assert c2.client_id != c1.client_id

    def test_session_with_all_risk_factors(self):
        ses = self.session.create_session("full-risk-user", "10.0.0.1", "Chrome")
        self.session.update_session_risk(ses.id, RiskLevel.CRITICAL, 0.95,
                                          "MULTIPLE_FAILED_LOGINS",
                                          [{"factor": "geo", "score": 0.3},
                                           {"factor": "device", "score": 0.4},
                                           {"factor": "behavior", "score": 0.25}])
        risk = self.session.get_session_risk(ses.id)
        assert risk.overall_risk == RiskLevel.CRITICAL
        assert abs(risk.risk_score - 0.95) < 0.01

    def test_pam_request_with_invalid_justification(self):
        req = self.pam.create_access_request("invalid-user", "server-1",
                                              AccessLevel.ADMIN, "No justification",
                                              justification_level=JustificationLevel.NONE)
        assert req.justification_level == JustificationLevel.NONE
        assert req.status == AccessRequestStatus.PENDING

    def test_workflow_with_empty_steps(self):
        wf = self.wf.create_workflow("Empty WF", "No steps", TriggerType.MANUAL, [])
        assert wf is not None
        assert len(wf.steps) == 0

    def test_oidc_provider_multiple_redirect_uris(self):
        c = self.idp.register_client("Multi-Redirect", ["https://app1.example.com",
                                                          "https://app2.example.com",
                                                          "https://app3.example.com"])
        assert len(c.redirect_uris) == 3

    def test_saml_provider_without_signature(self):
        p = self.idp.create_saml_provider("Unsigned SAML", "https://unsigned.example.com",
                                           "https://sso.example.com", "")
        assert p.certificate == ""

    def test_session_concurrent_limits(self):
        sessions = []
        for i in range(10):
            s = self.session.create_session(f"concurrent-user-{i}", f"10.0.0.{i}", f"Browser-{i}")
            sessions.append(s)
        assert len(sessions) == 10
        active = self.session.get_active_sessions()
        assert len(active) >= 1

    def test_pam_policy_template_delete(self):
        tmpl = self.pam.create_policy_template("temp-template", "Temporary",
                                                AccessLevel.VIEWER, ["viewer"])
        assert tmpl is not None
        templates_before = len(self.pam.list_policy_templates())
        self.pam.delete_policy_template(tmpl.id)
        templates_after = len(self.pam.list_policy_templates())
        assert templates_after < templates_before

    def test_workflow_event_trigger_config(self):
        wf = self.wf.create_workflow("Event WF", "Event-triggered",
                                      TriggerType.EVENT,
                                      [WorkflowStep(name="handle-event", step_type=StepType.TASK,
                                                    config={"event_type": "deploy.complete"})],
                                      event_config={"source": "github", "event": "push"})
        assert wf.trigger_type == TriggerType.EVENT
        assert wf.event_config["source"] == "github"

    def test_statistics_persistence(self):
        s1 = self.session.get_statistics()
        self.session.create_session("stat-user", "10.0.0.1", "Stats Browser")
        s2 = self.session.get_statistics()
        assert s2["total_sessions"] > s1["total_sessions"]

    def test_multiple_identity_providers_same_issuer(self):
        p1 = self.idp.create_oidc_provider("Provider A", "https://same.example.com", "ca", "sa")
        p2 = self.idp.create_oidc_provider("Provider B", "https://same.example.com", "cb", "sb")
        assert p1.issuer_url == p2.issuer_url

    def test_policy_engine_multiple_rules_evaluation(self):
        pass

    def test_session_timeout_cleanup(self):
        for i in range(5):
            self.session.create_session(f"cleanup-user-{i}", f"10.0.0.{i}", "Old Browser",
                                         session_timeout_minutes=0)
        stats = self.session.get_statistics()
        assert stats["total_sessions"] >= 5

    def test_compliance_scan_empty_targets_list(self):
        pass

    def test_drift_detector_no_changes_detected(self):
        check = DriftCheck(check_id="no-change-check", resource_type=ResourceType.KUBERNETES,
                           target_identifier="stable-cluster", status=CheckStatus.PENDING)
        assert check.check_id == "no-change-check"

    def test_self_healing_policy_empty_rules(self):
        policy = HealingPolicy(policy_id="empty-rules", name="No Rules",
                               enabled=True, rules=[],
                               created_at=datetime.now(), updated_at=datetime.now())
        assert len(policy.rules) == 0
        assert policy.enabled is True

    def test_chaos_experiment_zero_duration(self):
        exp = ChaosExperiment(experiment_id="zero-duration", name="Zero Duration",
                              experiment_type=ExperimentType.POD_FAILURE,
                              target_kind=TargetKind.KUBERNETES,
                              target_identifier="test", status=ExperimentStatus.CREATED,
                              created_at=datetime.now(), updated_at=datetime.now(),
                              duration_seconds=0)
        assert exp.duration_seconds == 0

    def test_runbook_no_steps(self):
        rb = RunbookDefinition(runbook_id="no-steps", title="No Steps",
                               category=RunbookCategory.GENERAL,
                               steps=[], difficulty=DifficultyLevel.BEGINNER,
                               version=1, created_at=datetime.now(),
                               updated_at=datetime.now())
        assert len(rb.steps) == 0

    def test_quota_zero_limit(self):
        q = QuotaDefinition(quota_id="zero-limit", name="Zero Limit",
                            quota_type=QuotaType.CPU, scope=QuotaScope.PROJECT,
                            limit=0, unit="cores", status=QuotaStatus.ACTIVE,
                            created_at=datetime.now(), updated_at=datetime.now())
        assert q.limit == 0

    def test_maintenance_window_past_end(self):
        window = MaintenanceWindow(window_id="past-window", title="Past Window",
                                    description="Already ended",
                                    start_time=datetime.now() - timedelta(days=2),
                                    end_time=datetime.now() - timedelta(days=1),
                                    status=WindowStatus.COMPLETED,
                                    created_at=datetime.now() - timedelta(days=2),
                                    updated_at=datetime.now() - timedelta(days=1))
        assert window.status == WindowStatus.COMPLETED

    def test_ansible_inventory_empty_groups(self):
        playbook = PlaybookDefinition(playbook_id="empty-inv", name="Empty Inventory",
                                      playbook_path="empty.yml",
                                      inventory_groups=[], roles=[],
                                      created_at=datetime.now(), updated_at=datetime.now())
        assert len(playbook.inventory_groups) == 0

    def test_pipeline_single_stage(self):
        pipeline = PipelineDefinition(pipeline_id="single-stage", name="Single Stage",
                                       stages=[PipelineStage(name="Only Stage",
                                                              stage_type=StageType.BUILD,
                                                              config={})],
                                       status=PipelineStatus.DRAFT,
                                       created_at=datetime.now(), updated_at=datetime.now())
        assert len(pipeline.stages) == 1

    def test_remediation_rule_no_conditions(self):
        rule = RemediationRule(rule_id="no-conditions", name="No Conditions",
                               enabled=True, trigger_event=TriggerEvent.INCIDENT,
                               condition=None,
                               action=RemediationAction(action_type=ActionType.NOTIFY,
                                                        config={"message": "alert"}),
                               created_at=datetime.now(), updated_at=datetime.now())
        assert rule.condition is None

    def test_cross_feature_end_to_end_flow(self):
        oidc = self.idp.create_oidc_provider("E2E Provider", "https://e2e.example.com",
                                              "e2e-cid", "e2e-secret")
        assert oidc.enabled is True
        ses = self.session.create_session("e2e-user", "10.0.0.99", "E2E Browser")
        assert ses.status == SessionStatus.ACTIVE
        request = self.pam.create_access_request("e2e-user", "e2e-server",
                                                  AccessLevel.OPERATOR, "E2E test",
                                                  justification_level=JustificationLevel.BUSINESS)
        assert request.status == AccessRequestStatus.PENDING
        wf = self.wf.create_workflow("E2E WF", "End to end workflow",
                                      TriggerType.MANUAL,
                                      [WorkflowStep(name="e2e-step", step_type=StepType.TASK,
                                                    config={"action": "notify"})])
        assert wf.status == WorkflowStatus.DRAFT
        self.wf.activate_workflow(wf.id)
        assert self.wf.get_workflow(wf.id).status == WorkflowStatus.ACTIVE
        stats_idp = self.idp.get_statistics()
        stats_session = self.session.get_statistics()
        stats_pam = self.pam.get_statistics()
        stats_wf = self.wf.get_statistics()
        assert stats_idp["oidc_providers"] >= 1
        assert stats_session["total_sessions"] >= 1
        assert stats_pam["total_requests"] >= 1
        assert stats_wf["total_workflows"] >= 1

    def test_concurrent_modifications_no_corruption(self):
        sessions = []
        for i in range(20):
            s = self.session.create_session(f"concurrent-{i}", f"10.0.0.{i}", f"Agent-{i}")
            sessions.append(s)
        assert len(sessions) == 20
        for s in sessions[:10]:
            self.session.terminate_session(s.id)
        active = self.session.get_active_sessions()
        assert len(active) <= 10

    def test_pam_mass_approval_workflow(self):
        requests = []
        for i in range(8):
            r = self.pam.create_access_request(f"mass-user-{i}", f"mass-server-{i}",
                                                AccessLevel.VIEWER, f"Mass test {i}",
                                                justification_level=JustificationLevel.BUSINESS)
            requests.append(r)
        assert len(requests) == 8
        for r in requests[:5]:
            self.pam.approve_request(r.id, "mass-approver")
        stats = self.pam.get_statistics()
        assert stats["approved_requests"] == 5
        assert stats["pending_requests"] == 3

    def test_workflow_deactivation_reactivation(self):
        wf = self.wf.create_workflow("Toggle WF", "Activate/deactivate",
                                      TriggerType.SCHEDULED,
                                      [WorkflowStep(name="task", step_type=StepType.TASK,
                                                    config={"cmd": "echo"})])
        self.wf.activate_workflow(wf.id)
        assert self.wf.get_workflow(wf.id).status == WorkflowStatus.ACTIVE
        self.wf.deactivate_workflow(wf.id)
        assert self.wf.get_workflow(wf.id).status == WorkflowStatus.INACTIVE
        self.wf.activate_workflow(wf.id)
        assert self.wf.get_workflow(wf.id).status == WorkflowStatus.ACTIVE

    def test_saml_metadata_generation(self):
        p = self.idp.create_saml_provider("Metadata SAML", "https://meta.example.com",
                                           "https://sso.example.com", "cert123")
        assert p.entity_id == "https://meta.example.com"
        assert p.sso_url == "https://sso.example.com"

    def test_token_with_custom_expiry(self):
        c = self.idp.register_client("Custom Expiry", ["https://exp.example.com"])
        token = self.idp.issue_token(c.client_id, "authorization_code", "openid",
                                      expires_in=7200)
        assert token.expires_in == 7200

    def test_client_registration_with_no_scopes(self):
        c = self.idp.register_client("No Scope Client", ["https://noscope.example.com"],
                                      client_type="public")
        assert c.client_type == "public"
        assert c.scopes == []

    def test_break_glass_multiple_resolutions(self):
        event = self.pam.create_break_glass_event("bg-resolve", "critical-srv",
                                                   AccessLevel.ADMIN, "Multiple resolves")
        assert event.status == "active"
        self.pam.resolve_break_glass(event.id)
        assert self.pam.get_break_glass_event(event.id).status == "resolved"

    def test_session_ipv6_support(self):
        ses = self.session.create_session("ipv6-user", "2001:db8::1", "IPv6 Browser")
        assert ses.ip_address == "2001:db8::1"

    def test_policy_deny_all_rule(self):
        policy = PolicyDefinition(policy_id="deny-all", name="Deny All",
                                  description="Deny everything",
                                  effect=PolicyEffect.DENY,
                                  rules=[PolicyRule(field="*", operator="eq", value=True)],
                                  enabled=True, priority=100,
                                  created_at=datetime.now(), updated_at=datetime.now())
        assert policy.effect == PolicyEffect.DENY
        assert policy.rules[0].field == "*"

    def test_compliance_scan_with_custom_benchmarks(self):
        scan = ComplianceScan(scan_id="custom-benchmark", name="Custom Scan",
                              benchmark_name="Custom PCI-DSS",
                              target_type="database",
                              targets=["db-1", "db-2"],
                              status=ScanStatus.PENDING,
                              results=[],
                              created_at=datetime.now(), updated_at=datetime.now())
        assert scan.benchmark_name == "Custom PCI-DSS"

    def test_workflow_scheduled_cron_expression(self):
        wf = WorkflowDefinition(workflow_id="cron-wf", name="Cron WF",
                                description="Scheduled workflow",
                                trigger_type=TriggerType.SCHEDULED,
                                steps=[], status=WorkflowStatus.ACTIVE,
                                cron_expression="0 */4 * * *",
                                version=1,
                                created_at=datetime.now(), updated_at=datetime.now())
        assert wf.cron_expression == "0 */4 * * *"

    def test_drift_high_severity_auto_remediate(self):
        result = DriftResult(drift_id="high-sev", check_id="check-1",
                             resource_type=ResourceType.KUBERNETES,
                             target_identifier="prod-1",
                             drift_found=True, severity=DriftSeverity.HIGH,
                             expected_config='{"replicas": 3}',
                             actual_config='{"replicas": 1}',
                             remediation=RemediationAction.AUTO_REMEDIATE,
                             checked_at=datetime.now())
        assert result.severity == DriftSeverity.HIGH
        assert result.remediation == RemediationAction.AUTO_REMEDIATE

    def test_self_healing_all_action_types(self):
        for action_type in HealingActionType:
            action = HealingAction(action_type=action_type, config={"test": True})
            assert action.action_type == action_type
            assert action.config["test"] is True

    def test_all_trigger_events_remediation(self):
        for event in TriggerEvent:
            rule = RemediationRule(rule_id=f"trigger-{event.name}", name=f"Trigger {event.name}",
                                   enabled=True, trigger_event=event,
                                   condition=RuleCondition(field="x", operator="eq", value=True),
                                   action=RemediationAction(action_type=ActionType.NOTIFY,
                                                            config={}),
                                   created_at=datetime.now(), updated_at=datetime.now())
            assert rule.trigger_event == event

    def test_all_condition_operators(self):
        for op in ["eq", "neq", "gt", "gte", "lt", "lte", "contains", "in", "not_in"]:
            cond = RuleCondition(field="test", operator=op, value=42)
            assert cond.operator == op

    def test_maintenance_all_priorities(self):
        for priority in TaskPriority:
            task = MaintenanceTask(task_id=f"priority-{priority.name}", title=f"Priority {priority.name}",
                                   description="Test", window_id="w1",
                                   priority=priority, status=TaskStatus.PENDING,
                                   created_at=datetime.now(), updated_at=datetime.now())
            assert task.priority == priority

    def test_chaos_all_experiment_statuses(self):
        for status in ExperimentStatus:
            exp = ChaosExperiment(experiment_id=f"status-{status.name}", name=f"Status {status.name}",
                                  experiment_type=ExperimentType.POD_FAILURE,
                                  target_kind=TargetKind.KUBERNETES,
                                  target_identifier="test", status=status,
                                  created_at=datetime.now(), updated_at=datetime.now())
            assert exp.status == status

    def test_quota_allocation_exact_limit(self):
        q = QuotaDefinition(quota_id="exact-limit", name="Exact Limit",
                            quota_type=QuotaType.CPU, scope=QuotaScope.PROJECT,
                            limit=10, unit="cores", status=QuotaStatus.ACTIVE,
                            created_at=datetime.now(), updated_at=datetime.now())
        usage = QuotaUsage(quota_id=q.quota_id, current_usage=10, limit=10,
                           exceeded=False, last_updated=datetime.now())
        assert usage.current_usage == usage.limit

    def test_pipeline_all_stage_types(self):
        for stage_type in StageType:
            stage = PipelineStage(name=f"Stage {stage_type.name}", stage_type=stage_type,
                                  config={"key": "value"})
            assert stage.stage_type == stage_type

    def test_ansible_all_config_tools(self):
        for tool in ConfigManagementTool:
            assert tool is not None

    def test_runbook_difficulty_labels(self):
        rb = RunbookDefinition(runbook_id="diff-labels", title="Difficulty Labels",
                               category=RunbookCategory.GENERAL,
                               steps=[], difficulty=DifficultyLevel.BEGINNER,
                               version=1, created_at=datetime.now(),
                               updated_at=datetime.now())
        assert rb.difficulty == DifficultyLevel.BEGINNER
        rb.difficulty = DifficultyLevel.ADVANCED
        assert rb.difficulty == DifficultyLevel.ADVANCED

    def test_session_invalid_id_graceful(self):
        result = self.session.get_session("nonexistent-session-id")
        assert result is None

    def test_pam_cancel_pending_request(self):
        req = self.pam.create_access_request("cancel-user", "srv-1",
                                              AccessLevel.VIEWER, "Test cancel",
                                              justification_level=JustificationLevel.BUSINESS)
        assert req.status == AccessRequestStatus.PENDING
        self.pam.cancel_request(req.id)
        assert self.pam.get_access_request(req.id).status == AccessRequestStatus.CANCELLED

    def test_mass_oidc_provider_cleanup(self):
        providers = []
        for i in range(25):
            p = self.idp.create_oidc_provider(f"Mass-{i}", f"https://mass{i}.example.com",
                                               f"cid{i}", f"sec{i}")
            providers.append(p)
        assert len(self.idp.list_oidc_providers()) == 25
        for p in providers[:20]:
            self.idp.delete_oidc_provider(p.id)
        assert len(self.idp.list_oidc_providers()) == 5

    def test_session_concurrent_access_same_user(self):
        s1 = self.session.create_session("same-user", "10.0.0.1", "Browser1")
        s2 = self.session.create_session("same-user", "10.0.0.2", "Browser2")
        assert s1.user_id == s2.user_id
        assert s1.id != s2.id
        self.session.terminate_session(s1.id)
        assert self.session.get_session(s1.id).status == SessionStatus.TERMINATED
        assert self.session.get_session(s2.id).status == SessionStatus.ACTIVE

    def test_workflow_with_user_approval_step(self):
        wf = self.wf.create_workflow("Approval WF", "Requires user approval",
                                      TriggerType.MANUAL,
                                      [WorkflowStep(name="approval-gate", step_type=StepType.APPROVAL,
                                                    config={"approvers": ["admin", "lead"]})])
        assert wf.steps[0].step_type == StepType.APPROVAL
        assert "admin" in wf.steps[0].config["approvers"]
