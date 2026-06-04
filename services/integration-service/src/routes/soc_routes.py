"""SOC API Routes - REST endpoints for all 10 SOC features."""

import json
import logging
from aiohttp import web
from typing import Dict, Any

from .soc.soar_platform import SOARPlatform
from .soc.threat_intel import ThreatIntelligenceManager
from .soc.deception_tech import DeceptionTechnology
from .soc.vuln_management import VulnerabilityManagement
from .soc.incident_response import SecurityIncidentResponse
from .soc.ueba import UserEntityBehaviorAnalytics
from .soc.cspm import CloudSecurityPostureManagement
from .soc.ndr import NetworkDetectionResponse
from .soc.secrets_detection import SecretsDetection
from .soc.security_training import SecurityAwarenessTraining

logger = logging.getLogger(__name__)


def setup_soc_routes(app, config: Dict[str, Any]):
    soar = SOARPlatform(config.get("soar", {}))
    threat_intel = ThreatIntelligenceManager(config.get("threat_intel", {}))
    deception = DeceptionTechnology(config.get("deception", {}))
    vuln_mgmt = VulnerabilityManagement(config.get("vuln_mgmt", {}))
    ir = SecurityIncidentResponse(config.get("incident_response", {}))
    ueba = UserEntityBehaviorAnalytics(config.get("ueba", {}))
    cspm = CloudSecurityPostureManagement(config.get("cspm", {}))
    ndr = NetworkDetectionResponse(config.get("ndr", {}))
    secrets = SecretsDetection(config.get("secrets", {}))
    training = SecurityAwarenessTraining(config.get("training", {}))

    # === SOAR Routes ===
    async def soar_playbooks(request):
        trigger = request.query.get("trigger")
        enabled = request.query.get("enabled")
        enabled_bool = None if enabled is None else enabled.lower() == "true"
        return web.json_response([p.to_dict() for p in soar.list_playbooks(trigger, enabled_bool)])

    async def soar_playbook_create(request):
        body = await request.json()
        pb = soar.create_playbook(body["name"], body.get("description", ""), body["trigger"], body.get("created_by", ""))
        return web.json_response(pb.to_dict(), status=201)

    async def soar_playbook_get(request):
        pb_id = request.match_info.get("playbook_id")
        pb = soar.get_playbook(pb_id)
        if not pb:
            return web.json_response({"error": "Playbook not found"}, status=404)
        return web.json_response(pb.to_dict())

    async def soar_playbook_update(request):
        pb_id = request.match_info.get("playbook_id")
        body = await request.json()
        pb = soar.update_playbook(pb_id, body)
        if not pb:
            return web.json_response({"error": "Playbook not found"}, status=404)
        return web.json_response(pb.to_dict())

    async def soar_playbook_delete(request):
        pb_id = request.match_info.get("playbook_id")
        if soar.delete_playbook(pb_id):
            return web.json_response({"status": "deleted"})
        return web.json_response({"error": "Playbook not found"}, status=404)

    async def soar_playbook_execute(request):
        pb_id = request.match_info.get("playbook_id")
        body = await request.json() if request.can_read_body else {}
        try:
            exec_id = await soar.execute_playbook(pb_id, body)
            return web.json_response({"execution_id": exec_id, "status": "queued"})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    async def soar_cases(request):
        status = request.query.get("status")
        priority = request.query.get("priority")
        assignee = request.query.get("assignee")
        return web.json_response([c.to_dict() for c in soar.list_cases(status, priority, assignee)])

    async def soar_case_create(request):
        body = await request.json()
        case = soar.create_case(body["title"], body["description"], body.get("priority", "medium"), body.get("assignee"))
        return web.json_response(case.to_dict(), status=201)

    async def soar_case_get(request):
        case_id = request.match_info.get("case_id")
        case = soar.get_case(case_id)
        if not case:
            return web.json_response({"error": "Case not found"}, status=404)
        return web.json_response(case.to_dict())

    async def soar_connectors(request):
        conn_type = request.query.get("type")
        return web.json_response([c.to_dict() for c in soar.list_connectors(conn_type)])

    async def soar_metrics(request):
        return web.json_response(soar.get_metrics())

    # === Threat Intel Routes ===
    async def ti_feeds(request):
        provider = request.query.get("provider")
        status = request.query.get("status")
        return web.json_response([f.to_dict() for f in threat_intel.list_feeds(provider, status)])

    async def ti_feed_create(request):
        body = await request.json()
        feed = await threat_intel.add_feed(body["name"], body["provider"], body["url"], body.get("api_key"),
                                            body.get("refresh_interval", 60), body.get("ioc_types"))
        return web.json_response(feed.to_dict(), status=201)

    async def ti_feed_refresh(request):
        feed_id = request.match_info.get("feed_id")
        result = await threat_intel.refresh_feed(feed_id)
        return web.json_response(result)

    async def ti_iocs(request):
        page = int(request.query.get("page", 1))
        page_size = int(request.query.get("page_size", 50))
        iocs, total = threat_intel.list_iocs(ioc_type=request.query.get("type"), severity=request.query.get("severity"),
                                              search=request.query.get("search"), page=page, page_size=page_size)
        return web.json_response({"iocs": [i.to_dict() for i in iocs], "total": total, "page": page})

    async def ti_ioc_create(request):
        body = await request.json()
        ioc = threat_intel.add_ioc(body["type"], body["value"], body.get("severity", "medium"),
                                    body.get("confidence", "medium"), body.get("source", "manual"),
                                    body.get("source_feed", ""), body.get("tags"))
        return web.json_response(ioc.to_dict(), status=201)

    async def ti_blocklist(request):
        active_only = request.query.get("active_only", "true").lower() == "true"
        ioc_type = request.query.get("type")
        return web.json_response([e.to_dict() for e in threat_intel.list_blocklist(active_only, ioc_type)])

    async def ti_summary(request):
        return web.json_response(threat_intel.get_threat_summary())

    # === Deception Routes ===
    async def decoy_list(request):
        return web.json_response([d.to_dict() for d in deception.list_decoys(
            decoy_type=request.query.get("type"), status=request.query.get("status"),
            network_zone=request.query.get("zone"))])

    async def decoy_create(request):
        body = await request.json()
        decoy = deception.deploy_decoy(body["name"], body["decoy_type"], body.get("network_zone", "internal"),
                                        body.get("tags"), body.get("config"))
        return web.json_response(decoy.to_dict(), status=201)

    async def decoy_engage(request):
        decoy_id = request.match_info.get("decoy_id")
        body = await request.json()
        event = deception.simulate_engagement(decoy_id, body["source_ip"], body.get("event_type", "connection"),
                                               body.get("user_agent"))
        return web.json_response(event.to_dict())

    async def decoy_events(request):
        return web.json_response([e.to_dict() for e in deception.list_events(
            decoy_id=request.query.get("decoy_id"), severity=request.query.get("severity"))])

    async def deception_summary(request):
        return web.json_response(deception.get_deception_summary())

    # === Vulnerability Management Routes ===
    async def vuln_list(request):
        page = int(request.query.get("page", 1))
        page_size = int(request.query.get("page_size", 50))
        vulns, total = vuln_mgmt.search_vulnerabilities(
            severity=request.query.get("severity"), status=request.query.get("status"),
            exploit_available=request.query.get("exploit_available"), search=request.query.get("search"),
            page=page, page_size=page_size)
        return web.json_response({"vulnerabilities": [v.to_dict() for v in vulns], "total": total, "page": page})

    async def vuln_scan_start(request):
        body = await request.json()
        scan = await vuln_mgmt.start_scan(body["name"], body["engine"], body["targets"], body.get("config"))
        return web.json_response(scan.to_dict(), status=201)

    async def vuln_scans(request):
        return web.json_response([s.to_dict() for s in vuln_mgmt.list_scans(
            status=request.query.get("status"), engine=request.query.get("engine"))])

    async def vuln_patch_create(request):
        body = await request.json()
        job = await vuln_mgmt.create_patch_job(body["name"], body["targets"], body["vuln_ids"],
                                                body.get("patch_type", "os_patch"),
                                                body.get("approval_required", False),
                                                body.get("maintenance_window_id"))
        return web.json_response(job.to_dict(), status=201)

    async def vuln_summary(request):
        return web.json_response(vuln_mgmt.get_vulnerability_summary())

    # === Incident Response Routes ===
    async def ir_incidents(request):
        page = int(request.query.get("page", 1))
        page_size = int(request.query.get("page_size", 25))
        incs, total = ir.list_incidents(status=request.query.get("status"), severity=request.query.get("severity"),
                                         assignee=request.query.get("assignee"), page=page, page_size=page_size)
        return web.json_response({"incidents": [i.to_dict() for i in incs], "total": total, "page": page})

    async def ir_incident_create(request):
        body = await request.json()
        inc = ir.create_incident(body["title"], body["description"], body["severity"],
                                  body.get("detection_source", ""), body.get("assignee"),
                                  body.get("affected_systems"), body.get("indicators"))
        return web.json_response(inc.to_dict(), status=201)

    async def ir_incident_get(request):
        inc_id = request.match_info.get("incident_id")
        inc = ir.get_incident(inc_id)
        if not inc:
            return web.json_response({"error": "Incident not found"}, status=404)
        return web.json_response(inc.to_dict())

    async def ir_evidence_add(request):
        inc_id = request.match_info.get("incident_id")
        body = await request.json()
        ev = ir.add_evidence(inc_id, body["artifact_type"], body["name"], body.get("description", ""),
                              body.get("source", ""), body.get("collected_by", ""))
        if not ev:
            return web.json_response({"error": "Incident not found"}, status=404)
        return web.json_response(ev.to_dict(), status=201)

    async def ir_report_generate(request):
        inc_id = request.match_info.get("incident_id")
        body = await request.json() if request.can_read_body else {}
        report = ir.generate_report(inc_id, body.get("report_type", "post_mortem"), body.get("generated_by", ""))
        if not report:
            return web.json_response({"error": "Incident not found"}, status=404)
        return web.json_response(report.to_dict(), status=201)

    async def ir_metrics(request):
        return web.json_response(ir.get_metrics())

    # === UEBA Routes ===
    async def ueba_entities(request):
        return web.json_response([e.to_dict() for e in ueba.list_entities(
            entity_type=request.query.get("type"), risk_level=request.query.get("risk_level"))])

    async def ueba_entity_get(request):
        entity_id = request.match_info.get("entity_id")
        return web.json_response(ueba.get_entity_risk(entity_id))

    async def ueba_ingest(request):
        body = await request.json()
        event = ueba.ingest_event(body["entity_id"], body["metric_type"], body["value"],
                                   body.get("source_ip"), body.get("location"), body.get("user_agent"))
        return web.json_response(event.to_dict(), status=201)

    async def ueba_alerts(request):
        return web.json_response([a.to_dict() for a in ueba.list_alerts(
            risk_level=request.query.get("risk_level"),
            acknowledged=request.query.get("acknowledged"),
            entity_id=request.query.get("entity_id"))])

    async def ueba_metrics(request):
        return web.json_response(ueba.get_metrics())

    # === CSPM Routes ===
    async def cspm_accounts(request):
        return web.json_response([a.to_dict() for a in cspm.list_accounts(provider=request.query.get("provider"))])

    async def cspm_scan_run(request):
        body = await request.json() if request.can_read_body else {}
        result = await cspm.run_scan(body.get("account_ids"), body.get("benchmarks"))
        return web.json_response(result)

    async def cspm_results(request):
        page = int(request.query.get("page", 1))
        results, total = cspm.get_scan_results(account_id=request.query.get("account_id"),
                                                status=request.query.get("status"),
                                                severity=request.query.get("severity"),
                                                page=page)
        return web.json_response({"results": [r.to_dict() for r in results], "total": total, "page": page})

    async def cspm_score(request):
        return web.json_response(cspm.get_compliance_score())

    # === NDR Routes ===
    async def ndr_flows(request):
        return web.json_response([f.to_dict() for f in ndr.search_flows(
            src_ip=request.query.get("src_ip"), dst_ip=request.query.get("dst_ip"),
            protocol=request.query.get("protocol"),
            malicious_only=request.query.get("malicious_only", "false").lower() == "true")])

    async def ndr_flow_ingest(request):
        body = await request.json()
        flow = ndr.ingest_flow(body["src_ip"], body["dst_ip"], body["src_port"], body["dst_port"],
                                body["protocol"], body["bytes_sent"], body["bytes_received"],
                                body["packets_sent"], body["packets_received"], body["duration_seconds"],
                                body.get("app_protocol"), body.get("tls_sni"), body.get("dns_query"))
        return web.json_response(flow.to_dict(), status=201)

    async def ndr_alerts(request):
        return web.json_response([a.to_dict() for a in ndr.list_alerts(
            severity=request.query.get("severity"), category=request.query.get("category"),
            source_ip=request.query.get("source_ip"))])

    async def ndr_summary(request):
        return web.json_response(ndr.get_network_summary())

    # === Secrets Detection Routes ===
    async def secrets_findings(request):
        page = int(request.query.get("page", 1))
        findings, total = secrets.list_findings(severity=request.query.get("severity"),
                                                 secret_type=request.query.get("type"),
                                                 status=request.query.get("status"),
                                                 repository=request.query.get("repository"),
                                                 page=page)
        return web.json_response({"findings": [f.to_dict() for f in findings], "total": total, "page": page})

    async def secrets_scan(request):
        target_id = request.match_info.get("target_id")
        result = await secrets.scan_target(target_id)
        return web.json_response(result)

    async def secrets_rotate(request):
        finding_id = request.match_info.get("finding_id")
        finding = await secrets.auto_rotate_secret(finding_id)
        if not finding:
            return web.json_response({"error": "Finding not found"}, status=404)
        return web.json_response(finding.to_dict())

    async def secrets_summary(request):
        return web.json_response(secrets.get_secrets_summary())

    # === Security Training Routes ===
    async def training_modules(request):
        return web.json_response([m.to_dict() for m in training.list_modules(
            category=request.query.get("category"), module_type=request.query.get("type"),
            required_only=request.query.get("required_only", "false").lower() == "true")])

    async def training_assign(request):
        body = await request.json()
        assignment = training.assign_module(body["user_id"], body["user_email"], body["user_name"],
                                             body["module_id"], body.get("department", ""),
                                             datetime.fromisoformat(body["deadline"]) if body.get("deadline") else None)
        return web.json_response(assignment.to_dict(), status=201)

    async def training_complete(request):
        assign_id = request.match_info.get("assignment_id")
        body = await request.json()
        assignment = training.complete_assignment(assign_id, body["score"])
        if not assignment:
            return web.json_response({"error": "Assignment not found"}, status=404)
        return web.json_response(assignment.to_dict())

    async def training_campaigns(request):
        return web.json_response([c.to_dict() for c in training.list_campaigns(status=request.query.get("status"))])

    async def training_campaign_create(request):
        body = await request.json()
        campaign = training.create_campaign(body["name"], body.get("description", ""), body["simulation_type"],
                                             body["target_departments"], body.get("template", "standard"),
                                             datetime.fromisoformat(body["scheduled_start"]) if body.get("scheduled_start") else None,
                                             body.get("created_by", ""))
        return web.json_response(campaign.to_dict(), status=201)

    async def training_summary(request):
        return web.json_response(training.get_training_summary())

    # Register SOAR routes
    app.router.add_get("/api/v1/soc/soar/playbooks", soar_playbooks)
    app.router.add_post("/api/v1/soc/soar/playbooks", soar_playbook_create)
    app.router.add_get("/api/v1/soc/soar/playbooks/{playbook_id}", soar_playbook_get)
    app.router.add_put("/api/v1/soc/soar/playbooks/{playbook_id}", soar_playbook_update)
    app.router.add_delete("/api/v1/soc/soar/playbooks/{playbook_id}", soar_playbook_delete)
    app.router.add_post("/api/v1/soc/soar/playbooks/{playbook_id}/execute", soar_playbook_execute)
    app.router.add_get("/api/v1/soc/soar/cases", soar_cases)
    app.router.add_post("/api/v1/soc/soar/cases", soar_case_create)
    app.router.add_get("/api/v1/soc/soar/cases/{case_id}", soar_case_get)
    app.router.add_get("/api/v1/soc/soar/connectors", soar_connectors)
    app.router.add_get("/api/v1/soc/soar/metrics", soar_metrics)

    # Register Threat Intel routes
    app.router.add_get("/api/v1/soc/threat-intel/feeds", ti_feeds)
    app.router.add_post("/api/v1/soc/threat-intel/feeds", ti_feed_create)
    app.router.add_post("/api/v1/soc/threat-intel/feeds/{feed_id}/refresh", ti_feed_refresh)
    app.router.add_get("/api/v1/soc/threat-intel/iocs", ti_iocs)
    app.router.add_post("/api/v1/soc/threat-intel/iocs", ti_ioc_create)
    app.router.add_get("/api/v1/soc/threat-intel/blocklist", ti_blocklist)
    app.router.add_get("/api/v1/soc/threat-intel/summary", ti_summary)

    # Register Deception routes
    app.router.add_get("/api/v1/soc/deception/decoys", decoy_list)
    app.router.add_post("/api/v1/soc/deception/decoys", decoy_create)
    app.router.add_post("/api/v1/soc/deception/decoys/{decoy_id}/engage", decoy_engage)
    app.router.add_get("/api/v1/soc/deception/events", decoy_events)
    app.router.add_get("/api/v1/soc/deception/summary", deception_summary)

    # Register Vulnerability Mgmt routes
    app.router.add_get("/api/v1/soc/vulnerabilities", vuln_list)
    app.router.add_post("/api/v1/soc/vulnerabilities/scans", vuln_scan_start)
    app.router.add_get("/api/v1/soc/vulnerabilities/scans", vuln_scans)
    app.router.add_post("/api/v1/soc/vulnerabilities/patches", vuln_patch_create)
    app.router.add_get("/api/v1/soc/vulnerabilities/summary", vuln_summary)

    # Register Incident Response routes
    app.router.add_get("/api/v1/soc/incidents", ir_incidents)
    app.router.add_post("/api/v1/soc/incidents", ir_incident_create)
    app.router.add_get("/api/v1/soc/incidents/{incident_id}", ir_incident_get)
    app.router.add_post("/api/v1/soc/incidents/{incident_id}/evidence", ir_evidence_add)
    app.router.add_post("/api/v1/soc/incidents/{incident_id}/report", ir_report_generate)
    app.router.add_get("/api/v1/soc/incidents/metrics", ir_metrics)

    # Register UEBA routes
    app.router.add_get("/api/v1/soc/ueba/entities", ueba_entities)
    app.router.add_get("/api/v1/soc/ueba/entities/{entity_id}", ueba_entity_get)
    app.router.add_post("/api/v1/soc/ueba/events", ueba_ingest)
    app.router.add_get("/api/v1/soc/ueba/alerts", ueba_alerts)
    app.router.add_get("/api/v1/soc/ueba/metrics", ueba_metrics)

    # Register CSPM routes
    app.router.add_get("/api/v1/soc/cspm/accounts", cspm_accounts)
    app.router.add_post("/api/v1/soc/cspm/scan", cspm_scan_run)
    app.router.add_get("/api/v1/soc/cspm/results", cspm_results)
    app.router.add_get("/api/v1/soc/cspm/score", cspm_score)

    # Register NDR routes
    app.router.add_get("/api/v1/soc/ndr/flows", ndr_flows)
    app.router.add_post("/api/v1/soc/ndr/flows", ndr_flow_ingest)
    app.router.add_get("/api/v1/soc/ndr/alerts", ndr_alerts)
    app.router.add_get("/api/v1/soc/ndr/summary", ndr_summary)

    # Register Secrets Detection routes
    app.router.add_get("/api/v1/soc/secrets/findings", secrets_findings)
    app.router.add_post("/api/v1/soc/secrets/scan/{target_id}", secrets_scan)
    app.router.add_post("/api/v1/soc/secrets/rotate/{finding_id}", secrets_rotate)
    app.router.add_get("/api/v1/soc/secrets/summary", secrets_summary)

    # Register Security Training routes
    app.router.add_get("/api/v1/soc/training/modules", training_modules)
    app.router.add_post("/api/v1/soc/training/assign", training_assign)
    app.router.add_post("/api/v1/soc/training/complete/{assignment_id}", training_complete)
    app.router.add_get("/api/v1/soc/training/campaigns", training_campaigns)
    app.router.add_post("/api/v1/soc/training/campaigns", training_campaign_create)
    app.router.add_get("/api/v1/soc/training/summary", training_summary)

    return {"soar": soar, "threat_intel": threat_intel, "deception": deception, "vuln_mgmt": vuln_mgmt,
            "incident_response": ir, "ueba": ueba, "cspm": cspm, "ndr": ndr, "secrets": secrets, "training": training}
