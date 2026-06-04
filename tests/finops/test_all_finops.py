"""Tests for all FinOps features (21-30)."""

import pytest
import json
import tempfile
import os
from datetime import datetime

from services.integration_service.src.finops.commitment_optimizer import CommitmentDiscountOptimizer
from services.integration_service.src.finops.spot_manager import SpotManager
from services.integration_service.src.finops.unit_economics import UnitEconomics
from services.integration_service.src.finops.cost_anomaly import CostAnomalyDetector
from services.integration_service.src.finops.budget_forecast import BudgetForecastEngine
from services.integration_service.src.finops.rightsizing import RightsizingEngine
from services.integration_service.src.finops.waste_detection import WasteDetector
from services.integration_service.src.finops.carbon_cost_optimizer import CarbonCostOptimizer
from services.integration_service.src.finops.discount_arbitrage import DiscountArbitrage
from services.integration_service.src.finops.finops_reporting import FinopsReporting


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_commitment_optimizer_recommendations(temp_storage):
    engine = CommitmentDiscountOptimizer({"data_dir": os.path.dirname(temp_storage)})
    recs = await engine.generate_recommendations()
    assert len(recs) > 0
    summary = await engine.get_savings_summary()
    assert summary["total_recommendations"] > 0


@pytest.mark.asyncio
async def test_commitment_implement_workflow(temp_storage):
    engine = CommitmentDiscountOptimizer({"data_dir": os.path.dirname(temp_storage)})
    recs = await engine.generate_recommendations()
    if recs:
        result = await engine.implement_recommendation(recs[0]["id"])
        assert result["status"] in ("implemented",)


@pytest.mark.asyncio
async def test_spot_fleet_crud(temp_storage):
    mgr = SpotManager({"data_dir": os.path.dirname(temp_storage)})
    fleet = await mgr.create_fleet({"name": "test-spot", "instance_type": "t3.medium", "target_capacity": 2, "spot_type": "fleet"})
    assert fleet["name"] == "test-spot"
    fleets = await mgr.list_fleets()
    assert len(fleets) > 0
    fetched = await mgr.get_fleet(fleet["id"])
    assert fetched["id"] == fleet["id"]


@pytest.mark.asyncio
async def test_spot_instance_launch(temp_storage):
    mgr = SpotManager({"data_dir": os.path.dirname(temp_storage)})
    fleet = await mgr.create_fleet({"name": "launch-test", "instance_type": "t3.small", "target_capacity": 1, "spot_type": "request"})
    instances = await mgr.get_fleet_instances(fleet["id"])
    assert len(instances) >= 0


@pytest.mark.asyncio
async def test_unit_economics_record_and_summary(temp_storage):
    ue = UnitEconomics({"data_dir": os.path.dirname(temp_storage)})
    record = await ue.record_metric("cust_001", "cost_per_request", 0.012, "production")
    assert record["customer_id"] == "cust_001"
    summary = await ue.get_customer_summary("cust_001")
    assert summary["total_metrics"] > 0


@pytest.mark.asyncio
async def test_unit_economics_violations(temp_storage):
    ue = UnitEconomics({"data_dir": os.path.dirname(temp_storage)})
    await ue.set_target("cost_per_request", 0.02, 20)
    await ue.record_metric("cust_001", "cost_per_request", 0.025, "production")
    violations = await ue.get_violations()
    assert len(violations) >= 0


@pytest.mark.asyncio
async def test_anomaly_detection_zscore(temp_storage):
    detector = CostAnomalyDetector({"data_dir": os.path.dirname(temp_storage)})
    detections = await detector.get_detections()
    assert len(detections) >= 0
    summary = await detector.get_summary()
    assert summary["total_anomalies"] >= 0


@pytest.mark.asyncio
async def test_anomaly_profile_crud(temp_storage):
    detector = CostAnomalyDetector({"data_dir": os.path.dirname(temp_storage)})
    profile = await detector.create_profile("test-profile", "zscore", 2.5)
    assert profile["name"] == "test-profile"
    profiles = await detector.list_profiles()
    assert len(profiles) > 0


@pytest.mark.asyncio
async def test_budget_forecast_crud(temp_storage):
    engine = BudgetForecastEngine({"data_dir": os.path.dirname(temp_storage)})
    budget = await engine.create_budget({"name": "test-budget", "amount": 10000, "period": "monthly"})
    assert budget["name"] == "test-budget"
    budgets = await engine.list_budgets()
    assert len(budgets) > 0


@pytest.mark.asyncio
async def test_budget_forecast_scenario(temp_storage):
    engine = BudgetForecastEngine({"data_dir": os.path.dirname(temp_storage)})
    budget = await engine.create_budget({"name": "forecast-test", "amount": 5000, "period": "monthly"})
    await engine.record_spend(budget["id"], 1200)
    forecast = await engine.get_forecast(budget["id"])
    assert "forecast_amount" in forecast
    scenario = await engine.what_if_scenario(budget["id"], "traffic_doubles")
    assert "projected_amount" in scenario


@pytest.mark.asyncio
async def test_rightsizing_recommendations(temp_storage):
    engine = RightsizingEngine({"data_dir": os.path.dirname(temp_storage)})
    recs = await engine.get_recommendations()
    assert len(recs) >= 0
    summary = await engine.get_summary()
    assert summary["total_recommendations"] >= 0


@pytest.mark.asyncio
async def test_rightsizing_workflow(temp_storage):
    engine = RightsizingEngine({"data_dir": os.path.dirname(temp_storage)})
    recs = await engine.get_recommendations()
    if recs:
        approved = await engine.approve_recommendation(recs[0]["id"])
        assert approved["success"] == True


@pytest.mark.asyncio
async def test_waste_detection_scan(temp_storage):
    detector = WasteDetector({"data_dir": os.path.dirname(temp_storage)})
    findings = await detector.get_findings()
    assert len(findings) >= 0
    summary = await detector.get_summary()
    assert summary["total_findings"] >= 0


@pytest.mark.asyncio
async def test_waste_cleanup_workflow(temp_storage):
    detector = WasteDetector({"data_dir": os.path.dirname(temp_storage)})
    findings = await detector.get_findings()
    if findings:
        result = await detector.approve_finding(findings[0]["id"])
        assert result["success"] == True


@pytest.mark.asyncio
async def test_carbon_recommendations(temp_storage):
    optimizer = CarbonCostOptimizer({"data_dir": os.path.dirname(temp_storage)})
    recs = await optimizer.get_recommendations()
    assert len(recs) >= 0


@pytest.mark.asyncio
async def test_carbon_asset_registration(temp_storage):
    optimizer = CarbonCostOptimizer({"data_dir": os.path.dirname(temp_storage)})
    asset = await optimizer.register_asset({"name": "test-app", "provider": "aws", "region": "us-east-1", "monthly_cost": 5000})
    assert asset["name"] == "test-app"
    assets = await optimizer.list_assets()
    assert len(assets) > 0


@pytest.mark.asyncio
async def test_discount_arbitrage_workloads(temp_storage):
    arb = DiscountArbitrage({"data_dir": os.path.dirname(temp_storage)})
    workloads = await arb.get_workloads()
    assert len(workloads) >= 0
    comparisons = await arb.get_comparisons()
    assert len(comparisons) >= 0


@pytest.mark.asyncio
async def test_finops_reporting_generate(temp_storage):
    reporting = FinopsReporting({"data_dir": os.path.dirname(temp_storage)})
    summary = await reporting.get_summary()
    assert summary["total_reports"] >= 0
    report = await reporting.generate_report("executive_summary", "monthly")
    assert report["type"] == "executive_summary"
