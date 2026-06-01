"""Tests for compliance_scanner_ext module."""
import pytest
import tempfile
import os
from datetime import datetime
from services.integration_service.src.compliance_scanner_ext import ComplianceScanner, ComplianceFramework, ComplianceStatus


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = ComplianceScanner(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestCISBenchmarks:
    def test_run_cis_docker_scan(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="docker://localhost")
        assert len(results) > 0
        assert any(r["framework"] == "cis_docker" for r in results)

    def test_run_cis_k8s_scan(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_K8S, target="k8s://production")
        assert len(results) > 0
        assert any(r["framework"] == "cis_kubernetes" for r in results)

    def test_cis_docker_checks_exist(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="test")
        check_categories = set(r["check_id"].split(".")[0] for r in results)
        assert len(check_categories) > 0

    def test_cis_check_ids(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="test")
        for r in results:
            assert r["check_id"].startswith(("1.", "2.", "3.", "4.", "5."))


class TestNISTChecks:
    def test_run_nist_scan(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.NIST_800_53, target="system://production")
        assert len(results) > 0
        check_families = set(r["check_id"].split("-")[0] for r in results)
        assert len(check_families) > 0

    def test_nist_check_ids(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.NIST_800_53, target="test")
        for r in results:
            assert r["check_id"].startswith(("AC-", "AU-", "AT-", "CA-", "CM-", "CP-", "IA-", "IR-", "MA-", "MP-", "PE-", "PL-", "PS-", "RA-", "SA-", "SC-", "SI-"))


class TestBSIChecks:
    def test_run_bsi_scan(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.BSI_GRUNDSCHUTZ, target="system://test")
        assert len(results) > 0

    def test_bsi_check_ids(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.BSI_GRUNDSCHUTZ, target="test")
        for r in results:
            assert r["check_id"].startswith("BSI-")


class TestAllFrameworks:
    def test_scan_all_frameworks(self, manager):
        for framework in ComplianceFramework:
            results = manager.run_scan(framework=framework, target="test")
            assert len(results) > 0, f"No results for {framework}"


class TestRemediation:
    def test_get_remediation(self, manager):
        remediation = manager.get_remediation("cis_docker", "4.1")
        assert remediation is not None
        assert len(remediation) > 0

    def test_remediation_for_unknown_check(self, manager):
        remediation = manager.get_remediation("unknown", "nonexistent")
        assert remediation == "No remediation available"

    def test_remediation_tracking(self, manager):
        manager.track_remediation("check-123", "remediation-steps", status="in_progress")
        manager.track_remediation("check-123", "remediation-steps", status="completed")


class TestWaivers:
    def test_create_waiver(self, manager):
        waiver = manager.create_waiver(
            check_id="cis_5.1",
            framework="cis_docker",
            reason="Temporary exception for migration",
            expires_at=datetime(2025, 12, 31),
            created_by="security-team",
        )
        assert waiver is not None
        assert waiver["check_id"] == "cis_5.1"

    def test_list_waivers(self, manager):
        manager.create_waiver(check_id="cis_4.1", framework="cis_docker", reason="Test", expires_at=datetime(2025, 12, 31), created_by="admin")
        waivers = manager.list_waivers()
        assert len(waivers) >= 1

    def test_expired_waiver(self, manager):
        waiver = manager.create_waiver(check_id="cis_5.2", framework="cis_docker", reason="Test", expires_at=datetime(2020, 1, 1), created_by="admin")
        assert waiver["expired"] == True


class TestReporting:
    def test_generate_csv_report(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="test")
        report = manager.generate_report(results, format="csv")
        assert report is not None
        assert "check_id" in report

    def test_generate_html_report(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.NIST_800_53, target="test")
        report = manager.generate_report(results, format="html")
        assert report is not None
        assert "<html>" in report

    def test_score_calculation(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="test")
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "pass")
        score = (passed / total * 100) if total > 0 else 0
        assert 0 <= score <= 100


class TestEdgeCases:
    def test_scan_invalid_target(self, manager):
        results = manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="")
        assert len(results) > 0

    def test_duplicate_waiver(self, manager):
        manager.create_waiver(check_id="cis_4.1", framework="cis_docker", reason="Test", expires_at=datetime(2025, 12, 31), created_by="admin")
        manager.create_waiver(check_id="cis_4.1", framework="cis_docker", reason="Test2", expires_at=datetime(2025, 12, 31), created_by="admin")
        waivers = manager.list_waivers()
        cis_waivers = [w for w in waivers if w["check_id"] == "cis_4.1"]
        assert len(cis_waivers) >= 2

    def test_statistics(self, manager):
        manager.run_scan(framework=ComplianceFramework.CIS_DOCKER, target="test")
        stats = manager.get_statistics()
        assert stats["total_scans"] >= 0
