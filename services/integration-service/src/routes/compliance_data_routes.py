import json, logging
from aiohttp import web

logger = logging.getLogger(__name__)

def setup_classification_routes(app, classification_engine):
    async def scan_text(request):
        data = await request.json()
        result = classification_engine.scan_text(data["text"], data.get("resource_id", "manual"), data.get("resource_type", "text"))
        return web.json_response(result.to_dict())

    async def get_result(request):
        scan_id = request.match_info["scan_id"]
        result = classification_engine.get_result(scan_id)
        if not result: raise web.HTTPNotFound()
        return web.json_response(result.to_dict())

    async def list_inventory(request):
        level = request.query.get("classification_level")
        rtype = request.query.get("resource_type")
        inventory = classification_engine.get_inventory(level, rtype)
        return web.json_response(inventory)

    async def label_resource(request):
        data = await request.json()
        try:
            result = classification_engine.label_resource(data["resource_id"], data["label"])
            return web.json_response({"success": result})
        except ValueError:
            logger.warning("Invalid label request in /api/v1/classification/label", exc_info=True)
            raise web.HTTPBadRequest(text="Invalid request payload.")

    async def classification_stats(request):
        stats = classification_engine.get_statistics()
        return web.json_response(stats)

    app.router.add_post("/api/v1/classification/scan", scan_text)
    app.router.add_get("/api/v1/classification/results/{scan_id}", get_result)
    app.router.add_get("/api/v1/classification/inventory", list_inventory)
    app.router.add_post("/api/v1/classification/label", label_resource)
    app.router.add_get("/api/v1/classification/stats", classification_stats)
    logger.info("Classification routes configured")

def setup_vendor_routes(app, vendor_manager):
    async def list_vendors(request):
        category = request.query.get("category")
        risk_tier = request.query.get("risk_tier")
        status = request.query.get("status")
        vendors = vendor_manager.list_vendors(category, risk_tier, status)
        return web.json_response(vendors)

    async def add_vendor(request):
        data = await request.json()
        vendor = vendor_manager.add_vendor(data["name"], data["category"], data.get("website"), data.get("contact_name"), data.get("contact_email"), data.get("risk_tier", "medium"), data.get("metadata"))
        return web.json_response(vendor, status=201)

    async def get_vendor(request):
        vendor_id = request.match_info["vendor_id"]
        vendor = vendor_manager.get_vendor(vendor_id)
        if not vendor: raise web.HTTPNotFound()
        return web.json_response(vendor)

    async def update_vendor(request):
        vendor_id = request.match_info["vendor_id"]
        data = await request.json()
        vendor = vendor_manager.update_vendor(vendor_id, data)
        if not vendor: raise web.HTTPNotFound()
        return web.json_response(vendor)

    async def delete_vendor(request):
        vendor_id = request.match_info["vendor_id"]
        result = vendor_manager.delete_vendor(vendor_id)
        return web.json_response({"deleted": result})

    async def create_assessment(request):
        vendor_id = request.match_info["vendor_id"]
        data = await request.json()
        try:
            assessment = vendor_manager.create_assessment(vendor_id, data["template_type"], data.get("assessor", "system"))
            return web.json_response(assessment, status=201)
        except ValueError:
            logger.exception("Failed to create assessment for vendor_id=%s", vendor_id)
            raise web.HTTPBadRequest(text="Invalid assessment request")

    async def get_assessment(request):
        vendor_id = request.match_info["vendor_id"]
        assessment_id = request.match_info["assessment_id"]
        assessment = vendor_manager.get_assessment(vendor_id, assessment_id)
        if not assessment: raise web.HTTPNotFound()
        return web.json_response(assessment)

    async def submit_responses(request):
        vendor_id = request.match_info["vendor_id"]
        assessment_id = request.match_info["assessment_id"]
        data = await request.json()
        result = vendor_manager.submit_responses(vendor_id, assessment_id, data.get("responses", {}))
        if not result: raise web.HTTPNotFound()
        return web.json_response(result)

    async def score_assessment(request):
        vendor_id = request.match_info["vendor_id"]
        assessment_id = request.match_info["assessment_id"]
        result = vendor_manager.score_assessment(vendor_id, assessment_id)
        if not result: raise web.HTTPBadRequest(text="Cannot score assessment")
        return web.json_response(result)

    app.router.add_get("/api/v1/vendors", list_vendors)
    app.router.add_post("/api/v1/vendors", add_vendor)
    app.router.add_get("/api/v1/vendors/{vendor_id}", get_vendor)
    app.router.add_put("/api/v1/vendors/{vendor_id}", update_vendor)
    app.router.add_delete("/api/v1/vendors/{vendor_id}", delete_vendor)
    app.router.add_post("/api/v1/vendors/{vendor_id}/assessments", create_assessment)
    app.router.add_get("/api/v1/vendors/{vendor_id}/assessments/{assessment_id}", get_assessment)
    app.router.add_put("/api/v1/vendors/{vendor_id}/assessments/{assessment_id}/responses", submit_responses)
    app.router.add_post("/api/v1/vendors/{vendor_id}/assessments/{assessment_id}/score", score_assessment)
    logger.info("Vendor routes configured")

def setup_breach_routes(app, breach_manager):
    async def report_breach(request):
        data = await request.json()
        breach = breach_manager.report_breach(
            data["description"], data["data_types_affected"], data["affected_users"],
            data.get("severity", "medium"), data.get("reported_by", "system"), data.get("affected_systems"))
        return web.json_response(breach, status=201)

    async def list_breaches(request):
        status = request.query.get("status")
        severity = request.query.get("severity")
        limit = int(request.query.get("limit", 50))
        offset = int(request.query.get("offset", 0))
        breaches = breach_manager.list_breaches(status, severity, limit, offset)
        return web.json_response(breaches)

    async def get_breach(request):
        breach_id = request.match_info["breach_id"]
        breach = breach_manager.get_breach(breach_id)
        if not breach: raise web.HTTPNotFound()
        return web.json_response(breach.to_dict())

    async def update_breach(request):
        breach_id = request.match_info["breach_id"]
        data = await request.json()
        breach = breach_manager.update_breach(breach_id, data)
        if not breach: raise web.HTTPNotFound()
        return web.json_response(breach)

    async def contain_breach(request):
        breach_id = request.match_info["breach_id"]
        data = await request.json()
        breach = breach_manager.contain_breach(breach_id, data.get("actions", []))
        if not breach: raise web.HTTPNotFound()
        return web.json_response(breach)

    async def resolve_breach(request):
        breach_id = request.match_info["breach_id"]
        data = await request.json()
        breach = breach_manager.resolve_breach(breach_id, data["root_cause"], data.get("remediation_completed", []))
        if not breach: raise web.HTTPNotFound()
        return web.json_response(breach)

    async def send_notification(request):
        breach_id = request.match_info["breach_id"]
        data = await request.json()
        try:
            notification = breach_manager.send_notification(breach_id, data["template_type"], data.get("fields", {}))
            return web.json_response(notification)
        except (ValueError, KeyError) as e:
            logger.warning("Bad request in send_notification: %s", str(e))
            raise web.HTTPBadRequest(text="Invalid notification request")

    async def get_timeline(request):
        breach_id = request.match_info["breach_id"]
        timeline = breach_manager.get_timeline(breach_id)
        return web.json_response(timeline)

    async def generate_report(request):
        breach_id = request.match_info["breach_id"]
        try:
            report = breach_manager.generate_report(breach_id)
            return web.json_response(report)
        except ValueError as e:
            logger.warning("Report generation failed for %s: %s", breach_id, str(e))
            raise web.HTTPNotFound(text="Report not found")

    app.router.add_post("/api/v1/breaches", report_breach)
    app.router.add_get("/api/v1/breaches", list_breaches)
    app.router.add_get("/api/v1/breaches/{breach_id}", get_breach)
    app.router.add_put("/api/v1/breaches/{breach_id}", update_breach)
    app.router.add_post("/api/v1/breaches/{breach_id}/contain", contain_breach)
    app.router.add_post("/api/v1/breaches/{breach_id}/resolve", resolve_breach)
    app.router.add_post("/api/v1/breaches/{breach_id}/notify", send_notification)
    app.router.add_get("/api/v1/breaches/{breach_id}/timeline", get_timeline)
    app.router.add_get("/api/v1/breaches/{breach_id}/report", generate_report)
    logger.info("Breach routes configured")
