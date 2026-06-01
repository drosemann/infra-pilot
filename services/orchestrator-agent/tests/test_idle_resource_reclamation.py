"""Tests for Idle Resource Reclamation."""

import pytest
from cogs.idle_resource_reclamation import (
    IdleResourceReclamation, ReclamationCandidate, ReclamationPolicy,
    ReclamationAction, ResourceType, ReclamationStatus
)


@pytest.fixture
def reclaimer():
    return IdleResourceReclamation({})


class TestReclamationCandidate:
    def test_create(self):
        cand = ReclamationCandidate("dev-001", "worker-node-1", ResourceType.COMPUTE,
                                     "cpu", 0.05)
        assert cand.device_id == "dev-001"
        assert cand.usage_pct == 0.05
        assert cand.status == ReclamationStatus.IDENTIFIED

    def test_to_dict(self):
        cand = ReclamationCandidate("dev-001", "node-1", ResourceType.COMPUTE, "cpu", 0.02)
        d = cand.to_dict()
        assert d["device_id"] == "dev-001"
        assert d["resource_path"] == "cpu"


class TestIdleResourceReclamation:
    def test_initialization(self, reclaimer):
        assert len(reclaimer.candidates) > 0
        assert len(reclaimer.policies) > 0

    def test_scan_for_idle(self, reclaimer):
        candidates = reclaimer.scan_for_idle("dev-001")
        assert len(candidates) > 0

    def test_scan_for_idle_nonexistent(self, reclaimer):
        assert len(reclaimer.scan_for_idle("nonexistent")) == 0

    def test_get_candidate(self, reclaimer):
        cid = list(reclaimer.candidates.keys())[0]
        cand = reclaimer.get_candidate(cid)
        assert cand is not None

    def test_get_candidate_not_found(self, reclaimer):
        assert reclaimer.get_candidate("nonexistent") is None

    def test_list_candidates(self, reclaimer):
        candidates = reclaimer.list_candidates()
        assert len(candidates) > 0

    def test_list_candidates_by_status(self, reclaimer):
        identified = reclaimer.list_candidates(status=ReclamationStatus.IDENTIFIED)
        assert len(identified) > 0

    def test_create_policy(self, reclaimer):
        policy = reclaimer.create_policy(
            "policy-001", "aggressive-reclaim",
            idle_threshold_pct=0.1,
            cool_down_minutes=5,
            max_reclaim_per_hour=50
        )
        assert policy.policy_id == "policy-001"
        assert policy.idle_threshold_pct == 0.1

    def test_get_policy(self, reclaimer):
        pid = list(reclaimer.policies.keys())[0]
        assert reclaimer.get_policy(pid) is not None

    def test_get_policy_not_found(self, reclaimer):
        assert reclaimer.get_policy("nonexistent") is None

    def test_list_policies(self, reclaimer):
        policies = reclaimer.list_policies()
        assert len(policies) > 0

    def test_update_policy(self, reclaimer):
        pid = list(reclaimer.policies.keys())[0]
        updated = reclaimer.update_policy(pid, {"idle_threshold_pct": 0.2})
        assert updated is not None
        assert updated.idle_threshold_pct == 0.2

    def test_delete_policy(self, reclaimer):
        pid = list(reclaimer.policies.keys())[0]
        assert reclaimer.delete_policy(pid) is True
        assert reclaimer.get_policy(pid) is None

    def test_reclaim_resource(self, reclaimer):
        cid = list(reclaimer.candidates.keys())[0]
        result = reclaimer.reclaim_resource(cid)
        assert result["status"] == "reclaimed"

    def test_reclaim_resource_not_found(self, reclaimer):
        result = reclaimer.reclaim_resource("nonexistent")
        assert result["status"] == "not_found"

    def test_reclaim_all(self, reclaimer):
        results = reclaimer.reclaim_all("dev-001")
        assert len(results) > 0

    def test_get_reclamation_summary(self, reclaimer):
        summary = reclaimer.get_reclamation_summary()
        assert "total_candidates" in summary
        assert "reclaimed_resources" in summary
        assert "estimated_savings_hourly" in summary
        assert "active_policies" in summary

    def test_get_savings_projection(self, reclaimer):
        projection = reclaimer.get_savings_projection("dev-001")
        assert "hourly_savings" in projection
        assert "daily_savings" in projection
        assert "monthly_savings" in projection

    def test_get_savings_projection_nonexistent(self, reclaimer):
        projection = reclaimer.get_savings_projection("nonexistent")
        assert projection["hourly_savings"] == 0

    def test_get_resource_type_breakdown(self, reclaimer):
        breakdown = reclaimer.get_resource_type_breakdown()
        assert len(breakdown) > 0

    def test_update_candidate_status(self, reclaimer):
        cid = list(reclaimer.candidates.keys())[0]
        reclaimer._update_candidate_status(cid, ReclamationStatus.RECLAIMED)
        assert reclaimer.candidates[cid].status == ReclamationStatus.RECLAIMED

    def test_resource_type_enum(self):
        assert ResourceType.COMPUTE.value == "compute"
        assert ResourceType.MEMORY.value == "memory"
        assert ResourceType.STORAGE.value == "storage"
        assert ResourceType.NETWORK.value == "network"
        assert ResourceType.GPU.value == "gpu"

    def test_reclamation_status_enum(self):
        assert ReclamationStatus.IDENTIFIED.value == "identified"
        assert ReclamationStatus.PENDING.value == "pending"
        assert ReclamationStatus.RECLAIMED.value == "reclaimed"
        assert ReclamationStatus.SKIPPED.value == "skipped"
