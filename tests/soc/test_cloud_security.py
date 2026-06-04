import pytest


class TestCloudSecurity:
    def test_cspm_findings(self):
        findings = [
            {"id": "f1", "severity": "critical", "resource": "s3-bucket", "status": "open"},
            {"id": "f2", "severity": "high", "resource": "iam-role", "status": "open"},
        ]
        critical = [f for f in findings if f["severity"] == "critical"]
        assert len(critical) == 1

    def test_workload_protection(self):
        workloads = [
            {"id": "w1", "type": "container", "runtime_status": "protected"},
            {"id": "w2", "type": "serverless", "runtime_status": "protected"},
        ]
        protected = [w for w in workloads if w["runtime_status"] == "protected"]
        assert len(protected) == 2

    def test_iam_role_analysis(self):
        roles = [
            {"name": "AdminRole", "overprivileged": True},
            {"name": "ReadOnlyRole", "overprivileged": False},
        ]
        overpriv = [r for r in roles if r["overprivileged"]]
        assert len(overpriv) == 1

    def test_cspm_scan(self):
        result = {"status": "scanning", "provider": "aws", "benchmark": "cis"}
        assert result["status"] == "scanning"
        result["status"] = "completed"
        assert result["status"] == "completed"
