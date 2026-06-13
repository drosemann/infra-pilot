import json, logging
from aiohttp import web

logger = logging.getLogger(__name__)

def setup_orchestration_routes(app, wf_manager, ansible_manager, pipeline_manager, drift_manager, quota_manager, remediation_manager, maintenance_planner, runbook_manager, chaos_manager, healing_manager):
    async def list_workflows(request):
        status = request.query.get("status")
        tag = request.query.get("tag")
        workflows = wf_manager.list_workflows(status, tag)
        return web.json_response(workflows)

    async def create_workflow(request):
        data = await request.json()
        wf = wf_manager.create_workflow(data["name"], data.get("description", ""), data.get("nodes"), data.get("edges"), data.get("tags"))
        return web.json_response(wf.to_dict(), status=201)

    async def get_workflow(request):
        wf = wf_manager.get_workflow(request.match_info["workflow_id"])
        if not wf: raise web.HTTPNotFound()
        return web.json_response(wf.to_dict())

    async def update_workflow(request):
        wf = wf_manager.update_workflow(request.match_info["workflow_id"], await request.json())
        if not wf: raise web.HTTPNotFound()
        return web.json_response(wf.to_dict())

    async def delete_workflow(request):
        return web.json_response({"deleted": wf_manager.delete_workflow(request.match_info["workflow_id"])})

    async def execute_workflow(request):
        data = await request.json()
        try:
            execution = await wf_manager.execute_workflow(request.match_info["workflow_id"], data.get("trigger_data", {}))
            return web.json_response(execution.to_dict())
        except ValueError as e:
            logger.exception("Invalid execute_workflow request: %s", e)
            raise web.HTTPBadRequest(text="Invalid request.")

    async def get_executions(request):
        wf_id = request.match_info.get("workflow_id", "")
        limit = int(request.query.get("limit", 50))
        executions = wf_manager.get_workflow_executions(wf_id, limit)
        return web.json_response(executions)

    async def get_execution(request):
        execution = wf_manager.get_execution(request.match_info["execution_id"])
        if not execution: raise web.HTTPNotFound()
        return web.json_response(execution.to_dict())

    async def list_node_types(request):
        category = request.query.get("category")
        types = wf_manager.get_node_types(category)
        return web.json_response(types)

    async def list_playbooks(request):
        return web.json_response(ansible_manager.ansible.list_playbooks())

    async def execute_playbook(request):
        data = await request.json()
        try:
            result = await ansible_manager.ansible.execute_playbook(data["playbook_id"], data.get("inventory_override"), data.get("extra_vars"), data.get("tags"), data.get("limit"))
            return web.json_response(result)
        except ValueError as e:
            logger.exception("Invalid execute_playbook request: %s", e)
            raise web.HTTPBadRequest(text="Invalid request.")

    async def ansible_executions(request):
        playbook_id = request.query.get("playbook_id")
        limit = int(request.query.get("limit", 50))
        return web.json_response(ansible_manager.ansible.list_executions(playbook_id, limit))

    async def ansible_execution_detail(request):
        execution = ansible_manager.ansible.get_execution(request.match_info["execution_id"])
        if not execution: raise web.HTTPNotFound()
        return web.json_response(execution)

    async def list_salt_states(request):
        return web.json_response(ansible_manager.salt.list_states())

    async def apply_salt_state(request):
        data = await request.json()
        try:
            result = await ansible_manager.salt.apply_state(data["state_id"], data.get("target_minions"), data.get("pillar"))
            return web.json_response(result)
        except ValueError as e:
            logger.exception("Invalid apply_salt_state request: %s", e)
            raise web.HTTPBadRequest(text="Invalid request.")

    async def list_pipelines(request):
        status = request.query.get("status")
        return web.json_response(pipeline_manager.list_pipelines(status))

    async def create_pipeline(request):
        data = await request.json()
        pipeline = pipeline_manager.create_pipeline(data["name"], data.get("description", ""), data["repo_url"], data.get("branch", "main"), data.get("stages"), data.get("triggers"), data.get("notifications"))
        return web.json_response(pipeline, status=201)

    async def get_pipeline(request):
        pipeline = pipeline_manager.get_pipeline(request.match_info["pipeline_id"])
        if not pipeline: raise web.HTTPNotFound()
        return web.json_response(pipeline)

    async def run_pipeline(request):
        data = await request.json()
        try:
            run = await pipeline_manager.run_pipeline(request.match_info["pipeline_id"], data.get("triggered_by", "manual"), data.get("variables"))
            return web.json_response(run)
        except ValueError as e:
            logger.exception("Invalid run_pipeline request: %s", e)
            raise web.HTTPBadRequest(text="Invalid request.")

    async def get_pipeline_runs(request):
        limit = int(request.query.get("limit", 50))
        runs = pipeline_manager.get_pipeline_runs(request.match_info["pipeline_id"], limit)
        return web.json_response(runs)

    async def get_run_detail(request):
        run = pipeline_manager.get_run(request.match_info["run_id"])
        if not run: raise web.HTTPNotFound()
        return web.json_response(run)

    async def approve_pipeline_run(request):
        data = await request.json()
        result = pipeline_manager.approve_run(request.match_info["run_id"], data.get("approved_by", "system"))
        return web.json_response({"approved": result})

    async def run_drift_scan(request):
        data = await request.json() if request.body_exists else {}
        scan = drift_manager.run_scan(data.get("target"), data.get("resource_types"))
        return web.json_response(scan)

    async def get_drift_scan(request):
        scan = drift_manager.get_scan(request.match_info["scan_id"])
        if not scan: raise web.HTTPNotFound()
        return web.json_response(scan)

    async def list_drift_scans(request):
        return web.json_response(drift_manager.list_scans())

    async def remediate_drift(request):
        data = await request.json()
        return web.json_response(drift_manager.remediate_drift(data["drift_id"]))

    async def list_quotas(request):
        entity_type = request.query.get("entity_type")
        return web.json_response(quota_manager.list_quotas(entity_type))

    async def create_quota(request):
        data = await request.json()
        quota = quota_manager.create_quota(data["name"], data["entity_type"], data["entity_id"], data.get("limits", {}), data.get("parent_id"), data.get("description", ""))
        return web.json_response(quota, status=201)

    async def get_quota(request):
        quota = quota_manager.get_quota(request.match_info["quota_id"])
        if not quota: raise web.HTTPNotFound()
        return web.json_response(quota)

    async def check_quota(request):
        data = await request.json()
        result = quota_manager.check_quota(data["quota_id"], data.get("requested", {}))
        return web.json_response(result)

    async def request_quota_increase(request):
        data = await request.json()
        req = quota_manager.request_increase(data["quota_id"], data["requested_limits"], data["reason"], data.get("requested_by", "system"))
        return web.json_response(req)

    async def list_remediation_rules(request):
        status = request.query.get("status")
        return web.json_response(remediation_manager.list_rules(status))

    async def create_remediation_rule(request):
        data = await request.json()
        rule = remediation_manager.create_rule(data["name"], data.get("description", ""), data["conditions"], data["actions"], data.get("cooldown", 300))
        return web.json_response(rule, status=201)

    async def test_rule(request):
        data = await request.json()
        event = data.get("event", {})
        results = await remediation_manager.evaluate_event(event)
        return web.json_response(results)

    async def list_maintenance_windows(request):
        status = request.query.get("status")
        team = request.query.get("team")
        date_from = request.query.get("from")
        date_to = request.query.get("to")
        return web.json_response(maintenance_planner.list_windows(status, team, date_from, date_to))

    async def create_maintenance_window(request):
        data = await request.json()
        try:
            window = maintenance_planner.create_window(data["name"], data.get("description", ""), data["start_time"], data["end_time"], data["affected_resources"], data["action_plan"], data.get("rollback_plan", ""), data.get("assigned_team", "ops"), data.get("requires_approval", True), data.get("notification_channels"), data.get("tags"))
            return web.json_response(window, status=201)
        except ValueError:
            logger.warning("Invalid maintenance window request", exc_info=True)
            raise web.HTTPBadRequest(text="Invalid maintenance window request.")

    async def list_runbook_templates(request):
        category = request.query.get("category")
        return web.json_response(runbook_manager.list_templates(category))

    async def search_templates(request):
        query = request.query.get("q", "")
        category = request.query.get("category")
        results = runbook_manager.search_templates(query, category)
        return web.json_response(results)

    async def instantiate_template(request):
        data = await request.json()
        try:
            instance = runbook_manager.instantiate_template(request.match_info["template_id"], data.get("variables", {}), data.get("initiated_by", "system"))
            return web.json_response(instance, status=201)
        except ValueError:
            logger.warning("Invalid template instantiation request", exc_info=True)
            raise web.HTTPBadRequest(text="Invalid template instantiation request.")

    async def list_chaos_experiments(request):
        status = request.query.get("status")
        return web.json_response(chaos_manager.list_experiments(status))

    async def create_chaos_experiment(request):
        data = await request.json()
        exp = chaos_manager.create_experiment(data["name"], data.get("description", ""), data["target"], data["faults"], data.get("steady_state"), data.get("rollback_on_failure", True), data.get("blast_radius"))
        return web.json_response(exp, status=201)

    async def run_chaos_experiment(request):
        try:
            result = await chaos_manager.run_experiment(request.match_info["experiment_id"])
            return web.json_response(result)
        except ValueError:
            logger.warning("Invalid chaos experiment request", exc_info=True)
            raise web.HTTPBadRequest(text="Invalid chaos experiment request.")

    async def stop_chaos_experiment(request):
        result = await chaos_manager.stop_experiment(request.match_info["experiment_id"])
        return web.json_response(result)

    async def healing_status(request):
        stats = healing_manager.get_statistics()
        return web.json_response(stats)

    async def trigger_healing(request):
        data = await request.json()
        result = healing_manager.trigger_remediation(data.get("context", {}))
        return web.json_response(result)

    async def healing_history(request):
        limit = int(request.query.get("limit", 100))
        return web.json_response(healing_manager.get_history(limit))

    async def healing_patterns(request):
        return web.json_response(healing_manager.get_patterns())

    async def provide_healing_feedback(request):
        data = await request.json()
        result = healing_manager.provide_feedback(data["remediation_id"], data["feedback"])
        return web.json_response(result)

    async def retrain_healing(request):
        result = healing_manager.retrain_model()
        return web.json_response(result)

    routes = [
        ("GET", "/api/v1/workflows", list_workflows),
        ("POST", "/api/v1/workflows", create_workflow),
        ("GET", "/api/v1/workflows/node-types", list_node_types),
        ("GET", "/api/v1/workflows/{workflow_id}", get_workflow),
        ("PUT", "/api/v1/workflows/{workflow_id}", update_workflow),
        ("DELETE", "/api/v1/workflows/{workflow_id}", delete_workflow),
        ("POST", "/api/v1/workflows/{workflow_id}/execute", execute_workflow),
        ("GET", "/api/v1/workflows/{workflow_id}/executions", get_executions),
        ("GET", "/api/v1/workflows/executions/{execution_id}", get_execution),
        ("GET", "/api/v1/integration/ansible/playbooks", list_playbooks),
        ("POST", "/api/v1/integration/ansible/playbook", execute_playbook),
        ("GET", "/api/v1/integration/ansible/executions", ansible_executions),
        ("GET", "/api/v1/integration/ansible/executions/{execution_id}", ansible_execution_detail),
        ("GET", "/api/v1/integration/salt/states", list_salt_states),
        ("POST", "/api/v1/integration/salt/state", apply_salt_state),
        ("GET", "/api/v1/pipelines", list_pipelines),
        ("POST", "/api/v1/pipelines", create_pipeline),
        ("GET", "/api/v1/pipelines/{pipeline_id}", get_pipeline),
        ("POST", "/api/v1/pipelines/{pipeline_id}/run", run_pipeline),
        ("GET", "/api/v1/pipelines/{pipeline_id}/runs", get_pipeline_runs),
        ("GET", "/api/v1/pipelines/runs/{run_id}", get_run_detail),
        ("POST", "/api/v1/pipelines/runs/{run_id}/approve", approve_pipeline_run),
        ("POST", "/api/v1/drift/scan", run_drift_scan),
        ("GET", "/api/v1/drift/scans/{scan_id}", get_drift_scan),
        ("GET", "/api/v1/drift/scans", list_drift_scans),
        ("POST", "/api/v1/drift/remediate", remediate_drift),
        ("GET", "/api/v1/quotas", list_quotas),
        ("POST", "/api/v1/quotas", create_quota),
        ("GET", "/api/v1/quotas/{quota_id}", get_quota),
        ("POST", "/api/v1/quotas/check", check_quota),
        ("POST", "/api/v1/quotas/request-increase", request_quota_increase),
        ("GET", "/api/v1/remediation/rules", list_remediation_rules),
        ("POST", "/api/v1/remediation/rules", create_remediation_rule),
        ("POST", "/api/v1/remediation/test", test_rule),
        ("GET", "/api/v1/maintenance/windows", list_maintenance_windows),
        ("POST", "/api/v1/maintenance/windows", create_maintenance_window),
        ("GET", "/api/v1/runbook-templates", list_runbook_templates),
        ("GET", "/api/v1/runbook-templates/search", search_templates),
        ("POST", "/api/v1/runbook-templates/{template_id}/instantiate", instantiate_template),
        ("GET", "/api/v1/chaos/experiments", list_chaos_experiments),
        ("POST", "/api/v1/chaos/experiments", create_chaos_experiment),
        ("POST", "/api/v1/chaos/experiments/{experiment_id}/run", run_chaos_experiment),
        ("POST", "/api/v1/chaos/experiments/{experiment_id}/stop", stop_chaos_experiment),
        ("GET", "/api/v1/healing/status", healing_status),
        ("POST", "/api/v1/healing/remediate", trigger_healing),
        ("GET", "/api/v1/healing/history", healing_history),
        ("GET", "/api/v1/healing/patterns", healing_patterns),
        ("POST", "/api/v1/healing/feedback", provide_healing_feedback),
        ("POST", "/api/v1/healing/retrain", retrain_healing),
    ]

    for method, path, handler in routes:
        app.router.add_route(method, path, handler)

    logger.info(f"Orchestration routes configured ({len(routes)} endpoints)")
