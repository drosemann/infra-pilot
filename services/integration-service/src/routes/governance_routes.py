import json, logging, aiohttp
from aiohttp import web
from typing import Dict, Any

logger = logging.getLogger(__name__)

def setup_policy_routes(app, policy_manager):
    async def list_policies(request):
        package = request.query.get("package")
        enabled_only = request.query.get("enabled_only", "").lower() == "true"
        tag = request.query.get("tag")
        policies = policy_manager.list_policies(package, enabled_only, tag)
        return web.json_response(policies)

    async def get_policy(request):
        policy_id = request.match_info["policy_id"]
        policy = policy_manager.get_policy(policy_id)
        if not policy: raise web.HTTPNotFound(text=f"Policy {policy_id} not found")
        return web.json_response(policy.to_dict())

    async def create_policy(request):
        data = await request.json()
        policy = policy_manager.create_policy(
            data["name"], data.get("description", ""), data["package"],
            data["rules"], data.get("tags", []))
        return web.json_response(policy.to_dict(), status=201)

    async def update_policy(request):
        policy_id = request.match_info["policy_id"]
        data = await request.json()
        policy = policy_manager.update_policy(policy_id, data)
        if not policy: raise web.HTTPNotFound(text=f"Policy {policy_id} not found")
        return web.json_response(policy.to_dict())

    async def delete_policy(request):
        policy_id = request.match_info["policy_id"]
        result = policy_manager.delete_policy(policy_id)
        if not result: raise web.HTTPNotFound(text=f"Policy {policy_id} not found")
        return web.json_response({"deleted": True})

    async def evaluate_policy(request):
        data = await request.json()
        package = data.get("package", "")
        input_data = data.get("input", {})
        result = policy_manager.evaluate(package, input_data)
        return web.json_response(result.to_dict())

    async def evaluate_multi(request):
        data = await request.json()
        evaluations = data.get("evaluations", [])
        results = policy_manager.evaluate_multi(evaluations)
        return web.json_response({"results": results})

    async def get_policy_history(request):
        policy_id = request.match_info.get("policy_id")
        limit = int(request.query.get("limit", 100))
        offset = int(request.query.get("offset", 0))
        package = request.query.get("package")
        history = policy_manager.get_evaluation_history(limit, offset, package)
        return web.json_response(history)

    async def sync_policies(request):
        data = await request.json()
        result = policy_manager.sync_from_git(data.get("git_url", ""), data.get("git_ref", "main"))
        return web.json_response(result)

    async def policy_stats(request):
        stats = policy_manager.get_statistics()
        return web.json_response(stats)

    app.router.add_get("/api/v1/policies", list_policies)
    app.router.add_get("/api/v1/policies/{policy_id}", get_policy)
    app.router.add_post("/api/v1/policies", create_policy)
    app.router.add_put("/api/v1/policies/{policy_id}", update_policy)
    app.router.add_delete("/api/v1/policies/{policy_id}", delete_policy)
    app.router.add_post("/api/v1/policies/evaluate", evaluate_policy)
    app.router.add_post("/api/v1/policies/evaluate-multi", evaluate_multi)
    app.router.add_get("/api/v1/policies/history", get_policy_history)
    app.router.add_post("/api/v1/policies/sync", sync_policies)
    app.router.add_get("/api/v1/policies/stats", policy_stats)
    logger.info("Policy routes configured")

def setup_compliance_routes(app, compliance_scanner):
    async def run_scan(request):
        data = await request.json()
        try:
            scan = compliance_scanner.run_scan(data["standard"], data.get("target", "all"))
            return web.json_response(scan.to_dict())
        except ValueError as e:
            logger.warning("Bad request in run_scan: %s", str(e))
            raise web.HTTPBadRequest(text="Invalid scan request")

    async def get_scan(request):
        scan_id = request.match_info["scan_id"]
        scan = compliance_scanner.get_scan(scan_id)
        if not scan: raise web.HTTPNotFound(text=f"Scan {scan_id} not found")
        return web.json_response(scan.to_dict())

    async def list_scans(request):
        standard = request.query.get("standard")
        scans = compliance_scanner.list_scans(standard)
        return web.json_response(scans)

    async def generate_report(request):
        scan_id = request.match_info["scan_id"]
        try:
            report = compliance_scanner.generate_report(scan_id)
            return web.json_response(report)
        except ValueError:
            logger.warning("Failed to generate compliance report for scan_id=%s", scan_id, exc_info=True)
            raise web.HTTPNotFound(text="Report not found")

    async def overall_status(request):
        status = compliance_scanner.get_overall_status()
        return web.json_response(status)

    async def list_waivers(request):
        waivers = compliance_scanner.list_waivers()
        return web.json_response(waivers)

    async def create_waiver(request):
        data = await request.json()
        waiver = compliance_scanner.add_waiver(
            data["check_id"], data["target"], data["reason"], data.get("expires_at"))
        return web.json_response(waiver, status=201)

    async def compliance_stats(request):
        stats = compliance_scanner.get_statistics()
        return web.json_response(stats)

    app.router.add_post("/api/v1/compliance/scan", run_scan)
    app.router.add_get("/api/v1/compliance/scan/{scan_id}", get_scan)
    app.router.add_get("/api/v1/compliance/scans", list_scans)
    app.router.add_get("/api/v1/compliance/report/{scan_id}", generate_report)
    app.router.add_get("/api/v1/compliance/status", overall_status)
    app.router.add_get("/api/v1/compliance/waivers", list_waivers)
    app.router.add_post("/api/v1/compliance/waivers", create_waiver)
    app.router.add_get("/api/v1/compliance/stats", compliance_stats)
    logger.info("Compliance routes configured")

def setup_audit_routes(app, audit_manager):
    async def get_overview(request):
        stats = audit_manager.get_statistics()
        return web.json_response(stats)

    async def list_anomalies(request):
        severity = request.query.get("severity")
        event_type = request.query.get("event_type")
        limit = int(request.query.get("limit", 100))
        offset = int(request.query.get("offset", 0))
        anomalies = audit_manager.get_anomalies(severity, event_type, limit, offset)
        return web.json_response(anomalies)

    async def get_anomaly(request):
        anomaly_id = request.match_info["anomaly_id"]
        anomaly = audit_manager.get_anomaly(anomaly_id)
        if not anomaly: raise web.HTTPNotFound()
        return web.json_response(anomaly.to_dict())

    async def run_analysis(request):
        result = audit_manager.run_analysis()
        return web.json_response(result)

    async def get_trends(request):
        metric = request.query.get("metric", "events")
        days = int(request.query.get("days", 30))
        trends = audit_manager.get_trends(metric, days)
        return web.json_response(trends)

    async def get_correlations(request):
        correlations = audit_manager.get_correlations()
        return web.json_response(correlations)

    async def get_user_baseline(request):
        user_id = request.query.get("user_id", "")
        baseline = audit_manager.get_user_baseline(user_id)
        if not baseline: raise web.HTTPNotFound()
        return web.json_response(baseline)

    app.router.add_get("/api/v1/audit/analytics/overview", get_overview)
    app.router.add_get("/api/v1/audit/analytics/anomalies", list_anomalies)
    app.router.add_get("/api/v1/audit/analytics/anomalies/{anomaly_id}", get_anomaly)
    app.router.add_post("/api/v1/audit/analytics/run", run_analysis)
    app.router.add_get("/api/v1/audit/analytics/trends", get_trends)
    app.router.add_get("/api/v1/audit/analytics/correlations", get_correlations)
    app.router.add_get("/api/v1/audit/analytics/baseline", get_user_baseline)
    logger.info("Audit analytics routes configured")
