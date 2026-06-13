"""Tests for Compliance Scanner."""
import pytest
import json
from datetime import datetime
from compliance_scanner import ComplianceScanner, ComplianceCheck, ScanResult, Waiver


@pytest.fixture
def scanner():
    return ComplianceScanner({
        "benchmarks_enabled": ["cis_docker", "cis_kubernetes", "nist_800_53", "bsi_grundschutz"],
        "max_concurrent_checks": 10,
        "scan_timeout": 300,
        "report_format": "json"
    })


class TestComplianceCheck:
    def test_run_checks(self, scanner):
        checks = scanner.run_checks("cis_docker")
        assert len(checks) > 0
        assert all(c.benchmark == "cis_docker" for c in checks)

    def test_get_check(self, scanner):
        check = scanner.get_check("cis_docker_4_1")
        assert check is not None
        assert check.check_id == "cis_docker_4_1"

    def test_get_missing_check(self, scanner):
        assert scanner.get_check("nonexistent_check") is None

    def test_list_checks_by_benchmark(self, scanner):
        docker_checks = scanner.list_checks("cis_docker")
        assert len(docker_checks) >= 20
        k8s_checks = scanner.list_checks("cis_kubernetes")
        assert len(k8s_checks) >= 15
        nist_checks = scanner.list_checks("nist_800_53")
        assert len(nist_checks) >= 30


class TestScanExecution:
    def test_run_full_scan(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker"])
        assert result.scan_id is not None
        assert result.benchmark == "cis_docker"
        assert result.total_checks > 0
        assert result.status == "completed"

    def test_scan_with_multiple_benchmarks(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker", "cis_kubernetes"])
        assert result.total_checks >= 40
        assert result.passed + result.failed + result.warning == result.total_checks

    def test_scan_results_contain_details(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker"])
        assert len(result.check_results) == result.total_checks
        for cr in result.check_results:
            assert cr.check_id is not None
            assert cr.status in ("pass", "fail", "warning", "error")

    def test_scan_compliance_score(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker"])
        assert 0 <= result.compliance_score <= 100
        assert result.passed_percentage >= 0

    def test_scan_with_waived_checks(self, scanner):
        check = scanner.get_check("cis_docker_1_1")
        scanner.add_waiver(check.check_id, "Known issue, waived", "admin-001", expires_in_days=30)
        result = scanner.run_scan(benchmarks=["cis_docker"], apply_waivers=True)
        waived_result = next((cr for cr in result.check_results if cr.check_id == check.check_id), None)
        assert waived_result is not None
        assert waived_result.status == "waived" or waived_result.is_waived is True

    def test_scan_history(self, scanner):
        scanner.run_scan(benchmarks=["cis_docker"])
        scanner.run_scan(benchmarks=["cis_kubernetes"])
        history = scanner.get_scan_history(limit=5)
        assert len(history) >= 2

    def test_get_scan_by_id(self, scanner):
        original = scanner.run_scan(benchmarks=["cis_docker"])
        retrieved = scanner.get_scan(original.scan_id)
        assert retrieved.scan_id == original.scan_id

    def test_get_missing_scan(self, scanner):
        assert scanner.get_scan("nonexistent") is None


class TestCISDockerBenchmark:
    def test_check_4_1_host_network(self, scanner):
        check = scanner.get_check("cis_docker_4_1")
        assert "host" in check.description.lower()
        assert check.severity == "high"

    def test_check_4_4_host_pid(self, scanner):
        check = scanner.get_check("cis_docker_4_4")
        assert check is not None
        assert check.severity == "medium"

    def test_check_5_1_apparmor(self, scanner):
        check = scanner.get_check("cis_docker_5_1")
        assert check is not None
        assert "apparmor" in check.description.lower()

    def test_check_5_7_selinux(self, scanner):
        check = scanner.get_check("cis_docker_5_7")
        assert check is not None
        assert check.severity == "medium"

    def test_check_5_19_mount_propagation(self, scanner):
        check = scanner.get_check("cis_docker_5_19")
        assert check is not None
        assert "propagation" in check.description.lower()

    def test_check_8_5_syslog(self, scanner):
        check = scanner.get_check("cis_docker_8_5")
        assert check is not None
        assert "log" in check.description.lower()


class TestCISKubernetesBenchmark:
    def test_check_k8s_1_1_rbac(self, scanner):
        check = scanner.get_check("cis_k8s_1_1_1")
        assert check is not None
        assert "rbac" in check.description.lower()

    def test_check_k8s_2_1_kubelet(self, scanner):
        check = scanner.get_check("cis_k8s_2_1")
        assert check is not None
        assert "kubelet" in check.description.lower()

    def test_check_k8s_3_2_network(self, scanner):
        check = scanner.get_check("cis_k8s_3_2")
        assert check is not None
        assert "network" in check.description.lower()

    def test_check_k8s_4_1_secret(self, scanner):
        check = scanner.get_check("cis_k8s_4_1")
        assert check is not None
        assert "secret" in check.description.lower()

    def test_check_k8s_5_5_pod_security(self, scanner):
        check = scanner.get_check("cis_k8s_5_5_1")
        assert check is not None
        assert "pod" in check.description.lower()

    def test_check_k8s_5_7_sysctl(self, scanner):
        check = scanner.get_check("cis_k8s_5_7")
        assert check is not None
        assert check.severity == "medium"


class TestNISTBenchmark:
    def test_check_ac_1_access_control(self, scanner):
        check = scanner.get_check("nist_ac_1")
        assert check is not None
        assert check.severity == "high"

    def test_check_au_2_audit_events(self, scanner):
        check = scanner.get_check("nist_au_2")
        assert check is not None
        assert "audit" in check.description.lower()

    def test_check_cm_2_config_baseline(self, scanner):
        check = scanner.get_check("nist_cm_2")
        assert check is not None
        assert check.severity == "medium"

    def test_check_ia_2_auth_identifier(self, scanner):
        check = scanner.get_check("nist_ia_2")
        assert check is not None
        assert "authenticat" in check.description.lower()

    def test_check_sc_7_boundary(self, scanner):
        check = scanner.get_check("nist_sc_7")
        assert check is not None
        assert "boundary" in check.description.lower()

    def test_check_si_4_monitoring(self, scanner):
        check = scanner.get_check("nist_si_4")
        assert check is not None
        assert "monitor" in check.description.lower()

    def test_check_cp_9_backup(self, scanner):
        check = scanner.get_check("nist_cp_9")
        assert check is not None
        assert "backup" in check.description.lower()

    def test_check_ir_4_incident(self, scanner):
        check = scanner.get_check("nist_ir_4")
        assert check is not None
        assert "incident" in check.description.lower()

    def test_check_pe_3_physical(self, scanner):
        check = scanner.get_check("nist_pe_3")
        assert check is not None
        assert "physical" in check.description.lower()

    def test_check_ra_3_risk(self, scanner):
        check = scanner.get_check("nist_ra_3")
        assert check is not None
        assert "risk" in check.description.lower()

    def test_check_sa_22_diversity(self, scanner):
        check = scanner.get_check("nist_sa_22")
        assert check is not None
        assert check.severity == "low"

    def test_check_ca_7_continuous_monitor(self, scanner):
        check = scanner.get_check("nist_ca_7")
        assert check is not None
        assert "continuous" in check.description.lower()

    def test_check_pl_4_rules(self, scanner):
        check = scanner.get_check("nist_pl_4")
        assert check is not None
        assert "rules" in check.description.lower()

    def test_check_at_3_training(self, scanner):
        check = scanner.get_check("nist_at_3")
        assert check is not None
        assert "training" in check.description.lower()

    def test_check_ma_2_maintenance(self, scanner):
        check = scanner.get_check("nist_ma_2")
        assert check is not None
        assert "maintenance" in check.description.lower()

    def test_check_mp_2_media(self, scanner):
        check = scanner.get_check("nist_mp_2")
        assert check is not None
        assert check.severity == "medium"

    def test_check_si_12_data_leak(self, scanner):
        check = scanner.get_check("nist_si_12")
        assert check is not None
        assert "leak" in check.description.lower()

    def test_check_sc_28_protection(self, scanner):
        check = scanner.get_check("nist_sc_28")
        assert check is not None
        assert "protect" in check.description.lower()

    def test_check_ac_6_least_privilege(self, scanner):
        check = scanner.get_check("nist_ac_6")
        assert check is not None
        assert "least" in check.description.lower()

    def test_check_au_12_comprehensive(self, scanner):
        check = scanner.get_check("nist_au_12")
        assert check is not None
        assert "comprehensive" in check.description.lower()

    def test_check_si_16_memory(self, scanner):
        check = scanner.get_check("nist_si_16")
        assert check is not None
        assert "memory" in check.description.lower()

    def test_check_ir_6_reporting(self, scanner):
        check = scanner.get_check("nist_ir_6")
        assert check is not None
        assert "report" in check.description.lower()

    def test_check_cm_8_asset(self, scanner):
        check = scanner.get_check("nist_cm_8")
        assert check is not None
        assert "asset" in check.description.lower()

    def test_check_ia_5_password(self, scanner):
        check = scanner.get_check("nist_ia_5")
        assert check is not None
        assert "password" in check.description.lower()

    def test_check_ac_3_enforcement(self, scanner):
        check = scanner.get_check("nist_ac_3")
        assert check is not None
        assert "enforcement" in check.description.lower()

    def test_check_au_3_content(self, scanner):
        check = scanner.get_check("nist_au_3")
        assert check is not None
        assert "content" in check.description.lower()

    def test_check_si_3_malicious(self, scanner):
        check = scanner.get_check("nist_si_3")
        assert check is not None
        assert "malicious" in check.description.lower()


class TestBSIBenchmark:
    def test_check_bsi_1_1_org(self, scanner):
        check = scanner.get_check("bsi_1_1")
        assert check is not None
        assert "organisation" in check.description.lower() or "organization" in check.description.lower()

    def test_check_bsi_2_1_personnel(self, scanner):
        check = scanner.get_check("bsi_2_1")
        assert check is not None
        assert "personnel" in check.description.lower()

    def test_check_bsi_3_1_emergency(self, scanner):
        check = scanner.get_check("bsi_3_1")
        assert check is not None
        assert "emergency" in check.description.lower()

    def test_check_bsi_4_3_identity(self, scanner):
        check = scanner.get_check("bsi_4_3")
        assert check is not None
        assert "identity" in check.description.lower()

    def test_check_bsi_5_1_network(self, scanner):
        check = scanner.get_check("bsi_5_1")
        assert check is not None
        assert "network" in check.description.lower()

    def test_check_bsi_1_5_crypto(self, scanner):
        check = scanner.get_check("bsi_1_5")
        assert check is not None
        assert "crypto" in check.description.lower()

    def test_check_bsi_2_5_clean_desk(self, scanner):
        check = scanner.get_check("bsi_2_5")
        assert check is not None
        assert "clean" in check.description.lower()

    def test_check_bsi_6_1_software(self, scanner):
        check = scanner.get_check("bsi_6_1")
        assert check is not None
        assert "software" in check.description.lower()

    def test_check_bsi_4_4_privilege(self, scanner):
        check = scanner.get_check("bsi_4_4")
        assert check is not None
        assert "privilege" in check.description.lower()

    def test_check_bsi_3_3_data_backup(self, scanner):
        check = scanner.get_check("bsi_3_3")
        assert check is not None
        assert "backup" in check.description.lower()


class TestWaiverManagement:
    def test_add_waiver(self, scanner):
        waiver = scanner.add_waiver("cis_docker_1_1", "Known issue", "admin-001")
        assert waiver.waiver_id is not None
        assert waiver.check_id == "cis_docker_1_1"
        assert waiver.is_active is True

    def test_revoke_waiver(self, scanner):
        waiver = scanner.add_waiver("cis_docker_4_1", "Testing revocation", "admin-001")
        assert scanner.revoke_waiver(waiver.waiver_id) is True
        assert waiver.is_active is False

    def test_list_waivers(self, scanner):
        scanner.add_waiver("cis_docker_1_1", "Waiver 1", "admin-001")
        scanner.add_waiver("cis_docker_5_1", "Waiver 2", "admin-002")
        waivers = scanner.list_waivers()
        assert len(waivers) >= 2

    def test_waiver_expiry(self, scanner):
        from datetime import timedelta
        waiver = scanner.add_waiver("cis_docker_5_7", "Expiring waiver", "admin-001", expires_in_days=0)
        assert waiver.is_expired is True
        assert waiver.is_active is False


class TestReportGeneration:
    def test_generate_report_json(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker"])
        report = scanner.generate_report(result.scan_id, fmt="json")
        assert report is not None
        assert "scan_id" in report
        assert "compliance_score" in report
        assert "check_results" in report

    def test_generate_report_html_summary(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker"])
        report = scanner.generate_report(result.scan_id, fmt="json")
        assert report["total_checks"] > 0
        assert report["passed"] + report["failed"] + report["warning"] == report["total_checks"]

    def test_generate_report_with_recommendations(self, scanner):
        result = scanner.run_scan(benchmarks=["cis_docker"])
        report = scanner.generate_report(result.scan_id, fmt="json", include_recommendations=True)
        for cr in report["check_results"]:
            if cr.get("status") == "fail":
                assert "recommendation" in cr or cr.get("remediation") is not None
