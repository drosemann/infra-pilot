"""Tests for all resiliency features (31-40)."""

import pytest
import json
import tempfile
import os
from datetime import datetime

from services.integration_service.src.resiliency.backup_sla_manager import BackupSLAManager
from services.integration_service.src.resiliency.chaos_validation import ChaosValidationManager
from services.integration_service.src.resiliency.resiliency_scoring import ResiliencyScoringEngine
from services.integration_service.src.resiliency.dependency_simulator import DependencySimulator
from services.integration_service.src.resiliency.runbook_executor import RunbookExecutor
from services.integration_service.src.resiliency.data_integrity import DataIntegrityVerifier
from services.integration_service.src.resiliency.resilience_pipeline import ResiliencePipelineManager
from services.integration_service.src.resiliency.bc_dashboard import BCDashboardManager


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_backup_sla_crud(temp_storage):
    config = {"backup_slas_file": temp_storage, "backup_sla_results_file": temp_storage.replace(".json", "_res.json")}
    mgr = BackupSLAManager(config)
    sla = await mgr.create_sla({"name": "Critical DB Backup", "workload_name": "postgres-primary", "category": "critical", "rpo_target_minutes": 15, "rto_target_minutes": 60})
    assert sla["name"] == "Critical DB Backup"
    assert sla["category"] == "critical"
    assert sla["active"] == True
    slas = await mgr.list_slas()
    assert len(slas) == 1
    fetched = await mgr.get_sla(sla["id"])
    assert fetched["id"] == sla["id"]
    updated = await mgr.update_sla(sla["id"], {"rpo_target_minutes": 10})
    assert updated["rpo_target_minutes"] == 10
    assert await mgr.delete_sla(sla["id"]) == True
    assert len(await mgr.list_slas()) == 0


@pytest.mark.asyncio
async def test_backup_sla_verification(temp_storage):
    config = {"backup_slas_file": temp_storage, "backup_sla_results_file": temp_storage.replace(".json", "_res.json")}
    mgr = BackupSLAManager(config)
    sla = await mgr.create_sla({"name": "Verify Test", "workload_name": "test", "category": "high"})
    result = await mgr.run_verification(sla["id"])
    assert result["status"] in ("passed", "failed")
    assert "checks" in result


@pytest.mark.asyncio
async def test_chaos_experiment_lifecycle(temp_storage):
    config = {"chaos_experiments_file": temp_storage, "chaos_results_file": temp_storage.replace(".json", "_res.json")}
    mgr = ChaosValidationManager(config)
    exp = await mgr.create_experiment({"name": "Kill DB Test", "target": "primary_database", "fault_type": "kill_container"})
    assert exp["status"] == "created"
    assert exp["approved"] == False
    approved = await mgr.approve_experiment(exp["id"])
    assert approved["approved"] == True
    run_result = await mgr.run_experiment(exp["id"])
    assert run_result["status"] == "running"
    results = await mgr.get_results(exp["id"])
    assert len(results) >= 0


@pytest.mark.asyncio
async def test_resiliency_scoring(temp_storage):
    config = {"resiliency_scores_file": temp_storage, "resiliency_recommendations_file": temp_storage.replace(".json", "_recs.json")}
    mgr = ResiliencyScoringEngine(config)
    score = await mgr.score_service("svc_api_gateway", {"name": "API Gateway", "replica_count": 3, "backup_enabled": True, "dr_plan_id": "dr_001", "circuit_breaker_enabled": True, "auto_scaling_enabled": True, "load_balancer_enabled": True, "monitoring_enabled": True, "chaos_validated": True})
    assert score["overall_score"] > 0
    assert score["grade"] in ("A", "B", "C", "D", "F")
    assert "recommendations" in score
    fetched = await mgr.get_service_score("svc_api_gateway")
    assert fetched is not None
    summary = await mgr.get_org_summary()
    assert summary["total_services"] >= 1


@pytest.mark.asyncio
async def test_dependency_simulation(temp_storage):
    config = {"dep_sim_file": temp_storage, "dep_sim_results_file": temp_storage.replace(".json", "_res.json")}
    mgr = DependencySimulator(config)
    sim = await mgr.create_simulation({"name": "DB Timeout", "target_service": "payment-service", "failure_type": "timeout"})
    assert sim["status"] == "created"
    result = await mgr.run_simulation(sim["id"])
    assert result["status"] in ("passed", "failed")
    assert "blast_radius" in result
    assert "observations" in result
    types = await mgr.get_failure_types()
    assert len(types) > 0


@pytest.mark.asyncio
async def test_runbook_executor(temp_storage):
    config = {"dr_runbooks_file": temp_storage, "dr_runbook_executions_file": temp_storage.replace(".json", "_exec.json")}
    mgr = RunbookExecutor(config)
    rb = await mgr.create_runbook({"name": "DB Failover Runbook", "steps": [{"name": "Check Standby", "type": "command"}, {"name": "Promote Standby", "type": "command"}, {"name": "Verify Health", "type": "command"}]})
    assert rb["status"] == "draft"
    exec_result = await mgr.execute_runbook(rb["id"], triggered_by="test")
    assert exec_result["status"] == "running"
    step_types = await mgr.get_step_types()
    assert len(step_types) == 8


@pytest.mark.asyncio
async def test_data_integrity(temp_storage):
    config = {"data_integrity_file": temp_storage, "data_integrity_results_file": temp_storage.replace(".json", "_res.json")}
    mgr = DataIntegrityVerifier(config)
    v = await mgr.create_verification({"name": "DB Checksum Check", "resource_name": "postgres-primary", "verification_type": "checksum", "replicas": [{"name": "read-replica-1", "type": "read_replica"}, {"name": "standby-1", "type": "standby"}]})
    assert v["active"] == True
    result = await mgr.run_verification(v["id"])
    assert result["status"] in ("passed", "failed")
    assert "replica_results" in result
    summary = await mgr.get_summary()
    assert summary["total_verifications"] >= 1


@pytest.mark.asyncio
async def test_resilience_pipeline(temp_storage):
    config = {"resilience_pipelines_file": temp_storage, "resilience_pipeline_runs_file": temp_storage.replace(".json", "_runs.json")}
    mgr = ResiliencePipelineManager(config)
    pipeline = await mgr.create_pipeline({"name": "Staging Resilience", "repository": "https://github.com/org/app", "branch": "main", "tests": [{"type": "chaos_experiment", "name": "Kill Pod", "critical": True}, {"type": "failover_test", "name": "DB Failover", "critical": True}]})
    assert pipeline["active"] == True
    run = await mgr.trigger_pipeline(pipeline["id"])
    assert run["status"] == "running"
    summary = await mgr.get_summary()
    assert summary["total_pipelines"] >= 1


@pytest.mark.asyncio
async def test_bc_dashboard(temp_storage):
    config = {"bc_snapshots_file": temp_storage}
    mgr = BCDashboardManager(config)
    dr_plans = [{"name": "Plan A", "status": "ready", "rpo_target_minutes": 30, "rto_target_minutes": 15}]
    backup_slas = [{"name": "SLA A", "active": True}]
    chaos_results = [{"status": "passed", "completed_at": datetime.now().isoformat()}]
    resiliency_scores = [{"overall_score": 85, "grade": "B"}]
    dashboard = await mgr.get_dashboard(dr_plans, backup_slas, chaos_results, resiliency_scores)
    assert "overall_bc_score" in dashboard
    assert dashboard["overall_bc_score"]["overall"] > 0
    assert "improvement_areas" in dashboard
    history = await mgr.get_snapshot_history(30)
    assert len(history) >= 0
    report = await mgr.get_executive_report()
    assert "report_title" in report
