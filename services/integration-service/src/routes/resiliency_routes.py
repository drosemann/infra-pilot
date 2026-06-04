"""Resiliency API routes for all 10 disaster recovery & business continuity features."""

import json
import logging
from datetime import datetime
from typing import Any, Dict
from aiohttp import web

from ..resiliency.dr_orchestrator import DROrchestrator
from ..resiliency.active_active import ActiveActiveManager
from ..resiliency.backup_sla_manager import BackupSLAManager
from ..resiliency.chaos_validation import ChaosValidationManager
from ..resiliency.resiliency_scoring import ResiliencyScoringEngine
from ..resiliency.dependency_simulator import DependencySimulator
from ..resiliency.runbook_executor import RunbookExecutor
from ..resiliency.data_integrity import DataIntegrityVerifier
from ..resiliency.resilience_pipeline import ResiliencePipelineManager
from ..resiliency.bc_dashboard import BCDashboardManager

logger = logging.getLogger(__name__)


class ResiliencyAPIRouter:
    """REST API router for all resiliency features (31-40)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dr_orchestrator = DROrchestrator(config)
        self.active_active = ActiveActiveManager(config)
        self.backup_sla = BackupSLAManager(config)
        self.chaos_validation = ChaosValidationManager(config)
        self.resiliency_scoring = ResiliencyScoringEngine(config)
        self.dep_simulator = DependencySimulator(config)
        self.runbook_executor = RunbookExecutor(config)
        self.data_integrity = DataIntegrityVerifier(config)
        self.resilience_pipeline = ResiliencePipelineManager(config)
        self.bc_dashboard = BCDashboardManager(config)
        self.initialized = False

    async def initialize(self):
        if not self.initialized:
            await self.active_active.initialize()
            self.initialized = True

    async def close(self):
        await self.active_active.close()
        self.initialized = False

    def register_routes(self, app: web.Application):
        app.router.add_get("/api/v1/resiliency/dr/plans", self.list_dr_plans)
        app.router.add_post("/api/v1/resiliency/dr/plans", self.create_dr_plan)
        app.router.add_get("/api/v1/resiliency/dr/plans/{plan_id}", self.get_dr_plan)
        app.router.add_patch("/api/v1/resiliency/dr/plans/{plan_id}", self.update_dr_plan)
        app.router.add_delete("/api/v1/resiliency/dr/plans/{plan_id}", self.delete_dr_plan)
        app.router.add_post("/api/v1/resiliency/dr/plans/{plan_id}/failover", self.execute_failover)
        app.router.add_post("/api/v1/resiliency/dr/plans/{plan_id}/readiness", self.run_readiness)
        app.router.add_get("/api/v1/resiliency/dr/executions", self.list_executions)
        app.router.add_get("/api/v1/resiliency/dr/executions/{exec_id}", self.get_execution)
        app.router.add_post("/api/v1/resiliency/dr/executions/{exec_id}/cancel", self.cancel_execution)
        app.router.add_get("/api/v1/resiliency/dr/compliance", self.dr_compliance)

        app.router.add_get("/api/v1/resiliency/active-active/regions", self.list_regions)
        app.router.add_post("/api/v1/resiliency/active-active/regions", self.register_region)
        app.router.add_get("/api/v1/resiliency/active-active/regions/{region_id}", self.get_region)
        app.router.add_patch("/api/v1/resiliency/active-active/regions/{region_id}", self.update_region)
        app.router.add_delete("/api/v1/resiliency/active-active/regions/{region_id}", self.delete_region)
        app.router.add_post("/api/v1/resiliency/active-active/regions/{region_id}/health", self.region_health)
        app.router.add_post("/api/v1/resiliency/active-active/regions/{region_id}/weight", self.update_weight)
        app.router.add_get("/api/v1/resiliency/active-active/traffic-rules", self.list_traffic_rules)
        app.router.add_post("/api/v1/resiliency/active-active/traffic-rules", self.create_traffic_rule)
        app.router.add_delete("/api/v1/resiliency/active-active/traffic-rules/{rule_id}", self.delete_traffic_rule)
        app.router.add_post("/api/v1/resiliency/active-active/metrics", self.record_metrics)
        app.router.add_get("/api/v1/resiliency/active-active/global-status", self.global_status)

        app.router.add_get("/api/v1/resiliency/backup-sla", self.list_backup_slas)
        app.router.add_post("/api/v1/resiliency/backup-sla", self.create_backup_sla)
        app.router.add_get("/api/v1/resiliency/backup-sla/{sla_id}", self.get_backup_sla)
        app.router.add_patch("/api/v1/resiliency/backup-sla/{sla_id}", self.update_backup_sla)
        app.router.add_delete("/api/v1/resiliency/backup-sla/{sla_id}", self.delete_backup_sla)
        app.router.add_post("/api/v1/resiliency/backup-sla/{sla_id}/verify", self.run_backup_verification)
        app.router.add_post("/api/v1/resiliency/backup-sla/verify-all", self.verify_all_backups)
        app.router.add_get("/api/v1/resiliency/backup-sla/{sla_id}/history", self.backup_verification_history)
        app.router.add_get("/api/v1/resiliency/backup-sla/compliance-report", self.backup_compliance_report)

        app.router.add_get("/api/v1/resiliency/chaos/experiments", self.list_chaos_experiments)
        app.router.add_post("/api/v1/resiliency/chaos/experiments", self.create_chaos_experiment)
        app.router.add_get("/api/v1/resiliency/chaos/experiments/{exp_id}", self.get_chaos_experiment)
        app.router.add_patch("/api/v1/resiliency/chaos/experiments/{exp_id}", self.update_chaos_experiment)
        app.router.add_delete("/api/v1/resiliency/chaos/experiments/{exp_id}", self.delete_chaos_experiment)
        app.router.add_post("/api/v1/resiliency/chaos/experiments/{exp_id}/approve", self.approve_chaos)
        app.router.add_post("/api/v1/resiliency/chaos/experiments/{exp_id}/run", self.run_chaos_experiment)
        app.router.add_get("/api/v1/resiliency/chaos/results", self.list_chaos_results)
        app.router.add_get("/api/v1/resiliency/chaos/dashboard", self.chaos_dashboard_summary)

        app.router.add_post("/api/v1/resiliency/score/{service_id}", self.score_service)
        app.router.add_get("/api/v1/resiliency/score/{service_id}", self.get_service_score)
        app.router.add_get("/api/v1/resiliency/scores", self.list_scores)
        app.router.add_delete("/api/v1/resiliency/score/{service_id}", self.delete_score)
        app.router.add_get("/api/v1/resiliency/scores/org-summary", self.org_summary)
        app.router.add_get("/api/v1/resiliency/recommendations", self.get_recommendations)
        app.router.add_patch("/api/v1/resiliency/recommendations/{rec_id}", self.update_recommendation)

        app.router.add_get("/api/v1/resiliency/dependency/simulations", self.list_simulations)
        app.router.add_post("/api/v1/resiliency/dependency/simulations", self.create_simulation)
        app.router.add_get("/api/v1/resiliency/dependency/simulations/{sim_id}", self.get_simulation)
        app.router.add_patch("/api/v1/resiliency/dependency/simulations/{sim_id}", self.update_simulation)
        app.router.add_delete("/api/v1/resiliency/dependency/simulations/{sim_id}", self.delete_simulation)
        app.router.add_post("/api/v1/resiliency/dependency/simulations/{sim_id}/run", self.run_simulation)
        app.router.add_get("/api/v1/resiliency/dependency/results", self.list_dep_results)
        app.router.add_get("/api/v1/resiliency/dependency/failure-types", self.failure_types)
        app.router.add_get("/api/v1/resiliency/dependency/summary", self.dep_summary)

        app.router.add_get("/api/v1/resiliency/runbooks", self.list_runbooks)
        app.router.add_post("/api/v1/resiliency/runbooks", self.create_runbook)
        app.router.add_get("/api/v1/resiliency/runbooks/{rb_id}", self.get_runbook)
        app.router.add_patch("/api/v1/resiliency/runbooks/{rb_id}", self.update_runbook)
        app.router.add_delete("/api/v1/resiliency/runbooks/{rb_id}", self.delete_runbook)
        app.router.add_post("/api/v1/resiliency/runbooks/{rb_id}/execute", self.execute_runbook)
        app.router.add_get("/api/v1/resiliency/runbooks/executions", self.list_rb_executions)
        app.router.add_get("/api/v1/resiliency/runbooks/executions/{exec_id}", self.get_rb_execution)
        app.router.add_post("/api/v1/resiliency/runbooks/executions/{exec_id}/cancel", self.cancel_rb_exec)
        app.router.add_post("/api/v1/resiliency/runbooks/executions/{exec_id}/pause", self.pause_rb_exec)
        app.router.add_post("/api/v1/resiliency/runbooks/executions/{exec_id}/resume", self.resume_rb_exec)
        app.router.add_get("/api/v1/resiliency/runbooks/step-types", self.rb_step_types)

        app.router.add_get("/api/v1/resiliency/data-integrity/verifications", self.list_verifications)
        app.router.add_post("/api/v1/resiliency/data-integrity/verifications", self.create_verification)
        app.router.add_get("/api/v1/resiliency/data-integrity/verifications/{ver_id}", self.get_verification)
        app.router.add_patch("/api/v1/resiliency/data-integrity/verifications/{ver_id}", self.update_verification)
        app.router.add_delete("/api/v1/resiliency/data-integrity/verifications/{ver_id}", self.delete_verification)
        app.router.add_post("/api/v1/resiliency/data-integrity/verifications/{ver_id}/run", self.run_verification)
        app.router.add_post("/api/v1/resiliency/data-integrity/run-all", self.run_all_verifications)
        app.router.add_get("/api/v1/resiliency/data-integrity/results", self.list_di_results)
        app.router.add_get("/api/v1/resiliency/data-integrity/summary", self.di_summary)

        app.router.add_get("/api/v1/resiliency/pipelines", self.list_pipelines)
        app.router.add_post("/api/v1/resiliency/pipelines", self.create_pipeline)
        app.router.add_get("/api/v1/resiliency/pipelines/{pipeline_id}", self.get_pipeline)
        app.router.add_patch("/api/v1/resiliency/pipelines/{pipeline_id}", self.update_pipeline)
        app.router.add_delete("/api/v1/resiliency/pipelines/{pipeline_id}", self.delete_pipeline)
        app.router.add_post("/api/v1/resiliency/pipelines/{pipeline_id}/trigger", self.trigger_pipeline)
        app.router.add_get("/api/v1/resiliency/pipelines/runs", self.list_pipeline_runs)
        app.router.add_get("/api/v1/resiliency/pipelines/runs/{run_id}", self.get_pipeline_run)
        app.router.add_get("/api/v1/resiliency/pipelines/summary", self.pipeline_summary)

        app.router.add_get("/api/v1/resiliency/bc-dashboard", self.get_bc_dashboard)
        app.router.add_get("/api/v1/resiliency/bc-dashboard/snapshots", self.bc_snapshots)
        app.router.add_get("/api/v1/resiliency/bc-dashboard/executive-report", self.bc_executive_report)

    async def list_dr_plans(self, request): return web.json_response(await self.dr_orchestrator.list_plans())
    async def create_dr_plan(self, request): return web.json_response(await self.dr_orchestrator.create_plan(await request.json()))
    async def get_dr_plan(self, request): return web.json_response(await self.dr_orchestrator.get_plan(request.match_info["plan_id"]))
    async def update_dr_plan(self, request): return web.json_response(await self.dr_orchestrator.update_plan(request.match_info["plan_id"], await request.json()))
    async def delete_dr_plan(self, request): return web.json_response({"deleted": await self.dr_orchestrator.delete_plan(request.match_info["plan_id"])})
    async def execute_failover(self, request): return web.json_response(await self.dr_orchestrator.execute_failover(request.match_info["plan_id"]))
    async def run_readiness(self, request): return web.json_response(await self.dr_orchestrator.run_readiness_check(request.match_info["plan_id"]))
    async def list_executions(self, request): return web.json_response(await self.dr_orchestrator.get_executions())
    async def get_execution(self, request): return web.json_response(await self.dr_orchestrator.get_execution(request.match_info["exec_id"]))
    async def cancel_execution(self, request): return web.json_response({"cancelled": await self.dr_orchestrator.cancel_execution(request.match_info["exec_id"])})
    async def dr_compliance(self, request): return web.json_response(await self.dr_orchestrator.get_compliance_summary())

    async def list_regions(self, request): return web.json_response(await self.active_active.list_regions())
    async def register_region(self, request): return web.json_response(await self.active_active.register_region(await request.json()))
    async def get_region(self, request): return web.json_response(await self.active_active.get_region(request.match_info["region_id"]))
    async def update_region(self, request): return web.json_response(await self.active_active.update_region(request.match_info["region_id"], await request.json()))
    async def delete_region(self, request): return web.json_response({"deleted": await self.active_active.delete_region(request.match_info["region_id"])})
    async def region_health(self, request): return web.json_response(await self.active_active.health_check(request.match_info["region_id"]))
    async def update_weight(self, request): data = await request.json(); return web.json_response(await self.active_active.update_traffic_weight(request.match_info["region_id"], data.get("weight", 100)))
    async def list_traffic_rules(self, request): return web.json_response(await self.active_active.list_traffic_rules())
    async def create_traffic_rule(self, request): return web.json_response(await self.active_active.create_traffic_rule(await request.json()))
    async def delete_traffic_rule(self, request): return web.json_response({"deleted": await self.active_active.delete_traffic_rule(request.match_info["rule_id"])})
    async def record_metrics(self, request): return web.json_response(await self.active_active.record_metrics(await request.json()))
    async def global_status(self, request): return web.json_response(await self.active_active.get_global_status())

    async def list_backup_slas(self, request): return web.json_response(await self.backup_sla.list_slas())
    async def create_backup_sla(self, request): return web.json_response(await self.backup_sla.create_sla(await request.json()))
    async def get_backup_sla(self, request): return web.json_response(await self.backup_sla.get_sla(request.match_info["sla_id"]))
    async def update_backup_sla(self, request): return web.json_response(await self.backup_sla.update_sla(request.match_info["sla_id"], await request.json()))
    async def delete_backup_sla(self, request): return web.json_response({"deleted": await self.backup_sla.delete_sla(request.match_info["sla_id"])})
    async def run_backup_verification(self, request): return web.json_response(await self.backup_sla.run_verification(request.match_info["sla_id"]))
    async def verify_all_backups(self, request): return web.json_response(await self.backup_sla.run_all_verifications())
    async def backup_verification_history(self, request): return web.json_response(await self.backup_sla.get_verification_history(request.match_info["sla_id"]))
    async def backup_compliance_report(self, request): return web.json_response(await self.backup_sla.get_compliance_report())

    async def list_chaos_experiments(self, request): return web.json_response(await self.chaos_validation.list_experiments())
    async def create_chaos_experiment(self, request): return web.json_response(await self.chaos_validation.create_experiment(await request.json()))
    async def get_chaos_experiment(self, request): return web.json_response(await self.chaos_validation.get_experiment(request.match_info["exp_id"]))
    async def update_chaos_experiment(self, request): return web.json_response(await self.chaos_validation.update_experiment(request.match_info["exp_id"], await request.json()))
    async def delete_chaos_experiment(self, request): return web.json_response({"deleted": await self.chaos_validation.delete_experiment(request.match_info["exp_id"])})
    async def approve_chaos(self, request): return web.json_response(await self.chaos_validation.approve_experiment(request.match_info["exp_id"]))
    async def run_chaos_experiment(self, request): return web.json_response(await self.chaos_validation.run_experiment(request.match_info["exp_id"]))
    async def list_chaos_results(self, request): return web.json_response(await self.chaos_validation.get_results())
    async def chaos_dashboard_summary(self, request): return web.json_response(await self.chaos_validation.get_dashboard_summary())

    async def score_service(self, request): return web.json_response(await self.resiliency_scoring.score_service(request.match_info["service_id"], await request.json() if request.can_read_body else None))
    async def get_service_score(self, request): return web.json_response(await self.resiliency_scoring.get_service_score(request.match_info["service_id"]))
    async def list_scores(self, request): return web.json_response(await self.resiliency_scoring.list_scores())
    async def delete_score(self, request): return web.json_response({"deleted": await self.resiliency_scoring.delete_score(request.match_info["service_id"])})
    async def org_summary(self, request): return web.json_response(await self.resiliency_scoring.get_org_summary())
    async def get_recommendations(self, request): return web.json_response(await self.resiliency_scoring.get_recommendations())
    async def update_recommendation(self, request): return web.json_response(await self.resiliency_scoring.update_recommendation(request.match_info["rec_id"], await request.json()))

    async def list_simulations(self, request): return web.json_response(await self.dep_simulator.list_simulations())
    async def create_simulation(self, request): return web.json_response(await self.dep_simulator.create_simulation(await request.json()))
    async def get_simulation(self, request): return web.json_response(await self.dep_simulator.get_simulation(request.match_info["sim_id"]))
    async def update_simulation(self, request): return web.json_response(await self.dep_simulator.update_simulation(request.match_info["sim_id"], await request.json()))
    async def delete_simulation(self, request): return web.json_response({"deleted": await self.dep_simulator.delete_simulation(request.match_info["sim_id"])})
    async def run_simulation(self, request): return web.json_response(await self.dep_simulator.run_simulation(request.match_info["sim_id"]))
    async def list_dep_results(self, request): return web.json_response(await self.dep_simulator.get_results())
    async def failure_types(self, request): return web.json_response(await self.dep_simulator.get_failure_types())
    async def dep_summary(self, request): return web.json_response(await self.dep_simulator.get_summary())

    async def list_runbooks(self, request): return web.json_response(await self.runbook_executor.list_runbooks())
    async def create_runbook(self, request): return web.json_response(await self.runbook_executor.create_runbook(await request.json()))
    async def get_runbook(self, request): return web.json_response(await self.runbook_executor.get_runbook(request.match_info["rb_id"]))
    async def update_runbook(self, request): return web.json_response(await self.runbook_executor.update_runbook(request.match_info["rb_id"], await request.json()))
    async def delete_runbook(self, request): return web.json_response({"deleted": await self.runbook_executor.delete_runbook(request.match_info["rb_id"])})
    async def execute_runbook(self, request): data = await request.json() if request.can_read_body else {}; return web.json_response(await self.runbook_executor.execute_runbook(request.match_info["rb_id"], data.get("variables"), data.get("triggered_by", "manual")))
    async def list_rb_executions(self, request): return web.json_response(await self.runbook_executor.list_executions())
    async def get_rb_execution(self, request): return web.json_response(await self.runbook_executor.get_execution(request.match_info["exec_id"]))
    async def cancel_rb_exec(self, request): return web.json_response({"cancelled": await self.runbook_executor.cancel_execution(request.match_info["exec_id"])})
    async def pause_rb_exec(self, request): return web.json_response({"paused": await self.runbook_executor.pause_execution(request.match_info["exec_id"])})
    async def resume_rb_exec(self, request): return web.json_response({"resumed": await self.runbook_executor.resume_execution(request.match_info["exec_id"])})
    async def rb_step_types(self, request): return web.json_response(await self.runbook_executor.get_step_types())

    async def list_verifications(self, request): return web.json_response(await self.data_integrity.list_verifications())
    async def create_verification(self, request): return web.json_response(await self.data_integrity.create_verification(await request.json()))
    async def get_verification(self, request): return web.json_response(await self.data_integrity.get_verification(request.match_info["ver_id"]))
    async def update_verification(self, request): return web.json_response(await self.data_integrity.update_verification(request.match_info["ver_id"], await request.json()))
    async def delete_verification(self, request): return web.json_response({"deleted": await self.data_integrity.delete_verification(request.match_info["ver_id"])})
    async def run_verification(self, request): return web.json_response(await self.data_integrity.run_verification(request.match_info["ver_id"]))
    async def run_all_verifications(self, request): return web.json_response(await self.data_integrity.run_all_verifications())
    async def list_di_results(self, request): return web.json_response(await self.data_integrity.get_results())
    async def di_summary(self, request): return web.json_response(await self.data_integrity.get_summary())

    async def list_pipelines(self, request): return web.json_response(await self.resilience_pipeline.list_pipelines())
    async def create_pipeline(self, request): return web.json_response(await self.resilience_pipeline.create_pipeline(await request.json()))
    async def get_pipeline(self, request): return web.json_response(await self.resilience_pipeline.get_pipeline(request.match_info["pipeline_id"]))
    async def update_pipeline(self, request): return web.json_response(await self.resilience_pipeline.update_pipeline(request.match_info["pipeline_id"], await request.json()))
    async def delete_pipeline(self, request): return web.json_response({"deleted": await self.resilience_pipeline.delete_pipeline(request.match_info["pipeline_id"])})
    async def trigger_pipeline(self, request): data = await request.json() if request.can_read_body else {}; return web.json_response(await self.resilience_pipeline.trigger_pipeline(request.match_info["pipeline_id"], data))
    async def list_pipeline_runs(self, request): return web.json_response(await self.resilience_pipeline.get_runs())
    async def get_pipeline_run(self, request): return web.json_response(await self.resilience_pipeline.get_run(request.match_info["run_id"]))
    async def pipeline_summary(self, request): return web.json_response(await self.resilience_pipeline.get_summary())

    async def get_bc_dashboard(self, request): return web.json_response(await self.bc_dashboard.get_dashboard())
    async def bc_snapshots(self, request): return web.json_response(await self.bc_dashboard.get_snapshot_history())
    async def bc_executive_report(self, request): return web.json_response(await self.bc_dashboard.get_executive_report())
