"""Tests for Disaster Recovery Orchestrator (feature 31)."""

import pytest
import json
import tempfile
import os
from services.integration_service.src.resiliency.dr_orchestrator import DROrchestrator


@pytest.fixture
def orchestrator():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    config = {"dr_plans_file": path, "dr_executions_file": path.replace(".json", "_exec.json")}
    yield DROrchestrator(config)
    if os.path.exists(path):
        os.remove(path)
    if os.path.exists(config["dr_executions_file"]):
        os.remove(config["dr_executions_file"])


@pytest.mark.asyncio
async def test_create_plan(orchestrator):
    plan = await orchestrator.create_plan({"name": "Test DR", "plan_type": "active-passive", "rpo_target_minutes": 30, "rto_target_minutes": 15})
    assert plan["name"] == "Test DR"
    assert plan["plan_type"] == "active-passive"
    assert plan["rpo_target_minutes"] == 30
    assert plan["rto_target_minutes"] == 15
    assert plan["status"] == "draft"


@pytest.mark.asyncio
async def test_create_plan_invalid_type(orchestrator):
    plan = await orchestrator.create_plan({"name": "Bad", "plan_type": "invalid"})
    assert "error" in plan


@pytest.mark.asyncio
async def test_list_plans(orchestrator):
    await orchestrator.create_plan({"name": "Plan 1"})
    await orchestrator.create_plan({"name": "Plan 2"})
    plans = await orchestrator.list_plans()
    assert len(plans) == 2


@pytest.mark.asyncio
async def test_get_plan(orchestrator):
    created = await orchestrator.create_plan({"name": "Get Me"})
    fetched = await orchestrator.get_plan(created["id"])
    assert fetched is not None
    assert fetched["name"] == "Get Me"


@pytest.mark.asyncio
async def test_update_plan(orchestrator):
    created = await orchestrator.create_plan({"name": "Update Me", "rpo_target_minutes": 60})
    updated = await orchestrator.update_plan(created["id"], {"rpo_target_minutes": 30, "status": "ready"})
    assert updated["rpo_target_minutes"] == 30
    assert updated["status"] == "ready"


@pytest.mark.asyncio
async def test_delete_plan(orchestrator):
    created = await orchestrator.create_plan({"name": "Delete Me"})
    assert await orchestrator.delete_plan(created["id"]) == True
    assert await orchestrator.get_plan(created["id"]) is None


@pytest.mark.asyncio
async def test_execute_failover(orchestrator):
    plan = await orchestrator.create_plan({"name": "Failover Test", "plan_type": "active-passive"})
    execution = await orchestrator.execute_failover(plan["id"])
    assert execution["status"] == "in_progress"
    assert execution["plan_id"] == plan["id"]
    assert execution["is_drill"] == False


@pytest.mark.asyncio
async def test_run_readiness_check(orchestrator):
    plan = await orchestrator.create_plan({"name": "Readiness Test"})
    result = await orchestrator.run_readiness_check(plan["id"])
    assert "healthy" in result
    assert "checks" in result


@pytest.mark.asyncio
async def test_cancel_execution(orchestrator):
    plan = await orchestrator.create_plan({"name": "Cancel Test"})
    execution = await orchestrator.execute_failover(plan["id"])
    assert await orchestrator.cancel_execution(execution["id"]) == True


@pytest.mark.asyncio
async def test_compliance_summary(orchestrator):
    summary = await orchestrator.get_compliance_summary()
    assert "total_plans" in summary
    assert "ready_plans" in summary
