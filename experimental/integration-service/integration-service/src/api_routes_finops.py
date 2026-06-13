"""REST API routes for FinOps & Advanced Cost Management features (21-30)."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from aiohttp import web

from .finops.commitment_optimizer import CommitmentDiscountOptimizer
from .finops.spot_manager import SpotManager
from .finops.unit_economics import UnitEconomics
from .finops.cost_anomaly import CostAnomalyDetector
from .finops.budget_forecast import BudgetForecastEngine
from .finops.rightsizing import RightsizingEngine
from .finops.waste_detection import WasteDetector
from .finops.carbon_cost_optimizer import CarbonCostOptimizer
from .finops.discount_arbitrage import DiscountArbitrage
from .finops.finops_reporting import FinopsReporting

logger = logging.getLogger(__name__)


class FinopsAPIRouter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.commitment = CommitmentDiscountOptimizer(config)
        self.spot = SpotManager(config)
        self.unit_economics = UnitEconomics(config)
        self.anomaly = CostAnomalyDetector(config)
        self.budget = BudgetForecastEngine(config)
        self.rightsizing = RightsizingEngine(config)
        self.waste = WasteDetector(config)
        self.carbon = CarbonCostOptimizer(config)
        self.arbitrage = DiscountArbitrage(config)
        self.reporting = FinopsReporting(config)
        self.initialized = False

    async def initialize(self):
        if not self.initialized:
            self.initialized = True

    async def close(self):
        self.initialized = False

    def register_routes(self, app: web.Application):
        op = "/api/v1/finops"

        app.router.add_post(f"{op}/commitment/analyze", self.commitment_analyze)
        app.router.add_get(f"{op}/commitment/recommendations", self.commitment_recommendations)
        app.router.add_post(f"{op}/commitment/recommendations/implement", self.commitment_implement)
        app.router.add_get(f"{op}/commitment/active", self.commitment_active)
        app.router.add_get(f"{op}/commitment/summary", self.commitment_summary)
        app.router.add_get(f"{op}/commitment/coverage-gaps", self.commitment_coverage_gaps)

        app.router.add_post(f"{op}/spot/fleets", self.spot_create_fleet)
        app.router.add_get(f"{op}/spot/fleets", self.spot_list_fleets)
        app.router.add_get(f"{op}/spot/fleets/{{fleet_id}}", self.spot_get_fleet)
        app.router.add_post(f"{op}/spot/fleets/{{fleet_id}}/launch", self.spot_launch_instances)
        app.router.add_post(f"{op}/spot/fleets/{{fleet_id}}/capacity", self.spot_update_capacity)
        app.router.add_get(f"{op}/spot/fleets/{{fleet_id}}/summary", self.spot_fleet_summary)
        app.router.add_get(f"{op}/spot/instances", self.spot_list_instances)
        app.router.add_post(f"{op}/spot/interrupt/{{instance_id}}", self.spot_interrupt)
        app.router.add_get(f"{op}/spot/savings", self.spot_savings)

        app.router.add_post(f"{op}/unit/metrics", self.unit_record_metric)
        app.router.add_get(f"{op}/unit/customers/{{customer_id}}", self.unit_customer_summary)
        app.router.add_post(f"{op}/unit/targets", self.unit_set_target)
        app.router.add_get(f"{op}/unit/targets", self.unit_get_targets)
        app.router.add_get(f"{op}/unit/violations", self.unit_violations)
        app.router.add_get(f"{op}/unit/overview", self.unit_overview)

        app.router.add_post(f"{op}/anomaly/ingest", self.anomaly_ingest)
        app.router.add_post(f"{op}/anomaly/detect", self.anomaly_detect)
        app.router.add_get(f"{op}/anomaly/list", self.anomaly_list)
        app.router.add_post(f"{op}/anomaly/{{anomaly_id}}/status", self.anomaly_update_status)
        app.router.add_post(f"{op}/anomaly/profiles", self.anomaly_create_profile)
        app.router.add_get(f"{op}/anomaly/profiles", self.anomaly_get_profiles)
        app.router.add_get(f"{op}/anomaly/summary", self.anomaly_summary)

        app.router.add_post(f"{op}/budgets", self.budget_create)
        app.router.add_get(f"{op}/budgets", self.budget_list)
        app.router.add_get(f"{op}/budgets/{{budget_id}}", self.budget_get)
        app.router.add_get(f"{op}/budgets/{{budget_id}}/tree", self.budget_tree)
        app.router.add_post(f"{op}/budgets/{{budget_id}}/spend", self.budget_record_spend)
        app.router.add_get(f"{op}/budgets/{{budget_id}}/forecast", self.budget_forecast)
        app.router.add_get(f"{op}/budgets/{{budget_id}}/variance", self.budget_variance)
        app.router.add_post(f"{op}/budgets/what-if", self.budget_whatif)
        app.router.add_get(f"{op}/budgets/summary", self.budget_summary)

        app.router.add_post(f"{op}/rightsizing/resources", self.rightsize_register)
        app.router.add_post(f"{op}/rightsizing/resources/{{resource_id}}/utilization", self.rightsize_utilization)
        app.router.add_get(f"{op}/rightsizing/resources/{{resource_id}}/analysis", self.rightsize_analysis)
        app.router.add_get(f"{op}/rightsizing/recommendations", self.rightsize_recommendations)
        app.router.add_post(f"{op}/rightsizing/recommendations/{{rec_id}}/approve", self.rightsize_approve)
        app.router.add_post(f"{op}/rightsizing/recommendations/{{rec_id}}/implement", self.rightsize_implement)
        app.router.add_post(f"{op}/rightsizing/recommendations/{{rec_id}}/dismiss", self.rightsize_dismiss)
        app.router.add_get(f"{op}/rightsizing/summary", self.rightsize_summary)

        app.router.add_post(f"{op}/waste/scan", self.waste_scan)
        app.router.add_get(f"{op}/waste/findings", self.waste_findings)
        app.router.add_post(f"{op}/waste/findings/{{finding_id}}/approve", self.waste_approve)
        app.router.add_post(f"{op}/waste/findings/{{finding_id}}/cleanup", self.waste_cleanup)
        app.router.add_post(f"{op}/waste/findings/{{finding_id}}/dismiss", self.waste_dismiss)
        app.router.add_get(f"{op}/waste/summary", self.waste_summary)

        app.router.add_post(f"{op}/carbon/assets", self.carbon_register_asset)
        app.router.add_get(f"{op}/carbon/assets/{{asset_id}}/footprint", self.carbon_footprint)
        app.router.add_get(f"{op}/carbon/intensity/{{region}}", self.carbon_intensity)
        app.router.add_post(f"{op}/carbon/recommendations", self.carbon_recommendations)
        app.router.add_get(f"{op}/carbon/recommendations", self.carbon_get_recommendations)
        app.router.add_get(f"{op}/carbon/assets/{{asset_id}}/tradeoff", self.carbon_tradeoff)
        app.router.add_get(f"{op}/carbon/sustainability-budget", self.carbon_sustainability)

        app.router.add_post(f"{op}/arbitrage/workloads", self.arbitrage_register_workload)
        app.router.add_get(f"{op}/arbitrage/workloads", self.arbitrage_list_workloads)
        app.router.add_get(f"{op}/arbitrage/workloads/{{workload_id}}/compare", self.arbitrage_compare)
        app.router.add_get(f"{op}/arbitrage/workloads/{{workload_id}}/migrate", self.arbitrage_migrate)
        app.router.add_get(f"{op}/arbitrage/comparisons", self.arbitrage_comparisons)
        app.router.add_get(f"{op}/arbitrage/savings", self.arbitrage_savings)

        app.router.add_post(f"{op}/reports/generate", self.report_generate)
        app.router.add_get(f"{op}/reports", self.report_list)
        app.router.add_get(f"{op}/reports/{{report_id}}", self.report_get)
        app.router.add_get(f"{op}/reports/dashboards/{{dashboard_type}}", self.report_dashboard)
        app.router.add_post(f"{op}/reports/allocations", self.report_create_allocation)
        app.router.add_get(f"{op}/reports/allocations", self.report_allocations)
        app.router.add_get(f"{op}/reports/summary", self.report_summary)

    # --- Commitment Optimizer ---
    async def commitment_analyze(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.commitment.analyze_usage_patterns(data.get("service", "aws-ec2"), data.get("resource_type", "compute")))

    async def commitment_recommendations(self, request: web.Request) -> web.Response:
        service = request.query.get("service")
        status = request.query.get("status")
        if service:
            self.commitment.generate_recommendations(service)
        return web.json_response({"recommendations": self.commitment.get_recommendations(status)})

    async def commitment_implement(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.commitment.implement_recommendation(data["recommendation_id"]))

    async def commitment_active(self, request: web.Request) -> web.Response:
        return web.json_response({"commitments": self.commitment.get_active_commitments()})

    async def commitment_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.commitment.get_savings_summary())

    async def commitment_coverage_gaps(self, request: web.Request) -> web.Response:
        return web.json_response({"gaps": self.commitment.get_coverage_gaps()})

    # --- Spot Manager ---
    async def spot_create_fleet(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.spot.create_fleet(data["name"], data["target_capacity"], data["instance_types"], data.get("regions", ["us-east-1"]), data.get("strategy")))

    async def spot_list_fleets(self, request: web.Request) -> web.Response:
        return web.json_response({"fleets": self.spot.list_fleets()})

    async def spot_get_fleet(self, request: web.Request) -> web.Response:
        fleet = self.spot.get_fleet(request.match_info["fleet_id"])
        return web.json_response(fleet or {"error": "Not found"})

    async def spot_launch_instances(self, request: web.Request) -> web.Response:
        data = await request.json() if request.body_exists else {}
        return web.json_response({"instances": self.spot.launch_instances(request.match_info["fleet_id"], data.get("count"))})

    async def spot_update_capacity(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.spot.update_fleet_capacity(request.match_info["fleet_id"], data["capacity"]))

    async def spot_fleet_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.spot.get_fleet_summary(request.match_info["fleet_id"]))

    async def spot_list_instances(self, request: web.Request) -> web.Response:
        return web.json_response({"instances": self.spot.list_instances(request.query.get("fleet_id"), request.query.get("status"))})

    async def spot_interrupt(self, request: web.Request) -> web.Response:
        return web.json_response(self.spot.simulate_interruption(request.match_info["instance_id"]))

    async def spot_savings(self, request: web.Request) -> web.Response:
        return web.json_response(self.spot.get_overall_savings())

    # --- Unit Economics ---
    async def unit_record_metric(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.unit_economics.record_metric(data["customer_id"], data["metric_type"], data["value"], data.get("dimension"), data.get("metadata")))

    async def unit_customer_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.unit_economics.get_customer_summary(request.match_info["customer_id"]))

    async def unit_set_target(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.unit_economics.set_target(data["customer_id"], data["metric_type"], data["target_value"], data.get("alert_threshold")))

    async def unit_get_targets(self, request: web.Request) -> web.Response:
        return web.json_response({"targets": self.unit_economics.get_targets(request.query.get("customer_id"), request.query.get("metric_type"))})

    async def unit_violations(self, request: web.Request) -> web.Response:
        return web.json_response({"violations": self.unit_economics.check_target_violations(request.query.get("customer_id"))})

    async def unit_overview(self, request: web.Request) -> web.Response:
        return web.json_response(self.unit_economics.get_overview())

    # --- Cost Anomaly ---
    async def anomaly_ingest(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.anomaly.ingest_spend_record(data["service"], data["amount"], data.get("region"), data.get("resource_id"), data.get("tags")))

    async def anomaly_detect(self, request: web.Request) -> web.Response:
        data = await request.json() if request.body_exists else {}
        return web.json_response({"anomalies": self.anomaly.detect_anomalies(data.get("service"), data.get("method", "zscore"))})

    async def anomaly_list(self, request: web.Request) -> web.Response:
        return web.json_response({"anomalies": self.anomaly.get_anomalies(request.query.get("status"), request.query.get("severity"), int(request.query.get("hours", 168)))})

    async def anomaly_update_status(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.anomaly.update_anomaly_status(request.match_info["anomaly_id"], data["status"], data.get("notes")))

    async def anomaly_create_profile(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.anomaly.create_profile(data["name"], data["metric"], data.get("method", "zscore"), data.get("sensitivity", 2.0), data.get("cooldown_minutes", 60)))

    async def anomaly_get_profiles(self, request: web.Request) -> web.Response:
        return web.json_response({"profiles": self.anomaly.get_profiles()})

    async def anomaly_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.anomaly.get_summary())

    # --- Budget & Forecast ---
    async def budget_create(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.budget.create_budget(data["name"], data["amount"], data.get("period", "monthly"), data.get("scope", "project"), data.get("scope_id"), data.get("parent_id"), data.get("alert_thresholds")))

    async def budget_list(self, request: web.Request) -> web.Response:
        return web.json_response({"budgets": self.budget.list_budgets(request.query.get("scope"), request.query.get("scope_id"))})

    async def budget_get(self, request: web.Request) -> web.Response:
        b = self.budget.get_budget(request.match_info["budget_id"])
        return web.json_response(b or {"error": "Not found"})

    async def budget_tree(self, request: web.Request) -> web.Response:
        return web.json_response(self.budget.get_budget_tree(request.match_info["budget_id"]))

    async def budget_record_spend(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.budget.record_actual_spend(request.match_info["budget_id"], data["amount"], data.get("category"), data.get("description")))

    async def budget_forecast(self, request: web.Request) -> web.Response:
        return web.json_response(self.budget.generate_forecast(request.match_info["budget_id"], request.query.get("model", "moving_average"), int(request.query.get("horizon_days", 30))))

    async def budget_variance(self, request: web.Request) -> web.Response:
        return web.json_response(self.budget.get_variance_analysis(request.match_info["budget_id"]))

    async def budget_whatif(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.budget.what_if_scenario(data["budget_id"], data.get("changes", {})))

    async def budget_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.budget.get_summary())

    # --- Rightsizing ---
    async def rightsize_register(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.rightsizing.register_resource(data["name"], data["resource_type"], data["current_size"], data["specs"], data["monthly_cost"], data.get("provider", "aws"), data.get("region", "us-east-1")))

    async def rightsize_utilization(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.rightsizing.record_utilization(request.match_info["resource_id"], data["cpu_pct"], data["memory_pct"], data.get("disk_pct"), data.get("iops_pct")))

    async def rightsize_analysis(self, request: web.Request) -> web.Response:
        return web.json_response(self.rightsizing.analyze_resource(request.match_info["resource_id"]))

    async def rightsize_recommendations(self, request: web.Request) -> web.Response:
        return web.json_response({"recommendations": self.rightsizing.get_recommendations(request.query.get("status"), request.query.get("priority"))})

    async def rightsize_approve(self, request: web.Request) -> web.Response:
        return web.json_response(self.rightsizing.approve_recommendation(request.match_info["rec_id"]))

    async def rightsize_implement(self, request: web.Request) -> web.Response:
        return web.json_response(self.rightsizing.implement_recommendation(request.match_info["rec_id"]))

    async def rightsize_dismiss(self, request: web.Request) -> web.Response:
        return web.json_response(self.rightsizing.dismiss_recommendation(request.match_info["rec_id"]))

    async def rightsize_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.rightsizing.get_summary())

    # --- Waste Detection ---
    async def waste_scan(self, request: web.Request) -> web.Response:
        data = await request.json() if request.body_exists else {}
        return web.json_response(self.waste.scan_for_waste(data.get("provider")))

    async def waste_findings(self, request: web.Request) -> web.Response:
        return web.json_response({"findings": self.waste.get_findings(request.query.get("category"), request.query.get("severity"), request.query.get("status"))})

    async def waste_approve(self, request: web.Request) -> web.Response:
        return web.json_response(self.waste.approve_cleanup(request.match_info["finding_id"]))

    async def waste_cleanup(self, request: web.Request) -> web.Response:
        return web.json_response(self.waste.execute_cleanup(request.match_info["finding_id"]))

    async def waste_dismiss(self, request: web.Request) -> web.Response:
        data = await request.json() if request.body_exists else {}
        return web.json_response(self.waste.dismiss_finding(request.match_info["finding_id"], data.get("reason")))

    async def waste_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.waste.get_summary())

    # --- Carbon Cost Optimizer ---
    async def carbon_register_asset(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.carbon.register_asset(data["name"], data.get("provider", "aws"), data["region"], data["monthly_cost"], data.get("estimated_kwh")))

    async def carbon_footprint(self, request: web.Request) -> web.Response:
        return web.json_response(self.carbon.get_asset_carbon_footprint(request.match_info["asset_id"]))

    async def carbon_intensity(self, request: web.Request) -> web.Response:
        return web.json_response(self.carbon.get_carbon_intensity(request.match_info["region"]))

    async def carbon_recommendations(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response({"recommendations": self.carbon.generate_recommendations(data.get("asset_id"), data.get("strategy", "balanced"))})

    async def carbon_get_recommendations(self, request: web.Request) -> web.Response:
        return web.json_response({"recommendations": self.carbon.get_recommendations(request.query.get("asset_id"), request.query.get("strategy"))})

    async def carbon_tradeoff(self, request: web.Request) -> web.Response:
        return web.json_response(self.carbon.get_trade_off_analysis(request.match_info["asset_id"]))

    async def carbon_sustainability(self, request: web.Request) -> web.Response:
        return web.json_response(self.carbon.get_sustainability_budget())

    # --- Discount Arbitrage ---
    async def arbitrage_register_workload(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.arbitrage.register_workload(data["name"], data["cpu_cores"], data["memory_gb"], data["storage_gb"], data["data_transfer_gb"], data.get("current_provider", "aws"), data.get("current_cost", 0)))

    async def arbitrage_list_workloads(self, request: web.Request) -> web.Response:
        return web.json_response({"workloads": self.arbitrage.list_workloads()})

    async def arbitrage_compare(self, request: web.Request) -> web.Response:
        return web.json_response(self.arbitrage.compare_providers(request.match_info["workload_id"]))

    async def arbitrage_migrate(self, request: web.Request) -> web.Response:
        return web.json_response(self.arbitrage.auto_migrate_recommendation(request.match_info["workload_id"]))

    async def arbitrage_comparisons(self, request: web.Request) -> web.Response:
        return web.json_response({"comparisons": self.arbitrage.get_all_comparisons()})

    async def arbitrage_savings(self, request: web.Request) -> web.Response:
        return web.json_response(self.arbitrage.get_aggregate_savings())

    # --- FinOps Reporting ---
    async def report_generate(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.reporting.generate_report(data["report_type"], data.get("period", "monthly"), data.get("format", "json"), data.get("filters")))

    async def report_list(self, request: web.Request) -> web.Response:
        return web.json_response({"reports": self.reporting.list_reports(request.query.get("report_type"))})

    async def report_get(self, request: web.Request) -> web.Response:
        r = self.reporting.get_report(request.match_info["report_id"])
        return web.json_response(r or {"error": "Not found"})

    async def report_dashboard(self, request: web.Request) -> web.Response:
        return web.json_response(self.reporting.get_prebuilt_dashboard(request.match_info["dashboard_type"]))

    async def report_create_allocation(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.reporting.create_allocation_tag(data["tag_key"], data["tag_value"], data["cost_pct"], data.get("team"), data.get("project")))

    async def report_allocations(self, request: web.Request) -> web.Response:
        return web.json_response({"allocations": self.reporting.get_allocations(request.query.get("team"))})

    async def report_summary(self, request: web.Request) -> web.Response:
        return web.json_response(self.reporting.get_summary())

    # --- Additional Endpoints ---
    def register_additional_routes(self, app: web.Application):
        op = "/api/v1/finops"
        app.router.add_get(f"{op}/commitment/history", self.commitment_history)
        app.router.add_get(f"{op}/commitment/roi", self.commitment_roi)
        app.router.add_post(f"{op}/commitment/renew", self.commitment_renew)
        app.router.add_get(f"{op}/anomaly/severity-breakdown", self.anomaly_severity_breakdown)
        app.router.add_post(f"{op}/anomaly/respond", self.anomaly_respond)
        app.router.add_post(f"{op}/anomaly/alert-config", self.anomaly_alert_config)
        app.router.add_get(f"{op}/budget/health", self.budget_health)
        app.router.add_post(f"{op}/budget/alert", self.budget_alert)
        app.router.add_get(f"{op}/waste/trend", self.waste_trend)
        app.router.add_post(f"{op}/waste/auto-cleanup", self.waste_auto_cleanup)
        app.router.add_get(f"{op}/carbon/assets", self.carbon_assets)
        app.router.add_get(f"{op}/carbon/breakdown", self.carbon_breakdown)

    async def commitment_history(self, request: web.Request) -> web.Response:
        days = int(request.query.get("days", 30))
        return web.json_response({"history": self.commitment.get_history(days)})

    async def commitment_roi(self, request: web.Request) -> web.Response:
        upfront = float(request.query.get("upfront", 0))
        monthly = float(request.query.get("monthly_savings", 0))
        term = int(request.query.get("term", 12))
        return web.json_response(self.commitment.calculate_roi(upfront, monthly, term))

    async def commitment_renew(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.commitment.renew_commitment(data.get("rec_id"), data.get("term", "1yr")))

    async def anomaly_severity_breakdown(self, request: web.Request) -> web.Response:
        severity = request.query.get("severity")
        return web.json_response(self.anomaly.get_severity_breakdown(severity))

    async def anomaly_respond(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.anomaly.respond_to_anomaly(data["anomaly_id"], data["action"]))

    async def anomaly_alert_config(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.anomaly.configure_alerts(data.get("channel", "discord"), data.get("min_severity", "medium")))

    async def budget_health(self, request: web.Request) -> web.Response:
        return web.json_response(self.budget.get_health_check())

    async def budget_alert(self, request: web.Request) -> web.Response:
        data = await request.json()
        return web.json_response(self.budget.create_alert(data["budget_id"], data.get("threshold_pct", 80)))

    async def waste_trend(self, request: web.Request) -> web.Response:
        return web.json_response(self.waste.get_waste_trend())

    async def waste_auto_cleanup(self, request: web.Request) -> web.Response:
        data = await request.json() if request.body_exists else {}
        return web.json_response(self.waste.auto_cleanup(data.get("category"), data.get("dry_run", True)))

    async def carbon_assets(self, request: web.Request) -> web.Response:
        return web.json_response({"assets": self.carbon.list_assets()})

    async def carbon_breakdown(self, request: web.Request) -> web.Response:
        return web.json_response(self.carbon.get_breakdown_by_provider())
