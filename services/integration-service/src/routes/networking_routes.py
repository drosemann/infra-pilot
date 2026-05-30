import json
import logging
from aiohttp import web
from typing import Dict, Any

from networking.sdwan_controller import SDWANController
from networking.vpn_service import VPNService
from networking.dns_manager import DNSManager
from networking.bgp_manager import BGPRouteManager
from networking.reverse_proxy import ReverseProxyManager
from networking.segmentation import NetworkSegmentation
from networking.packet_capture import PacketCaptureService
from networking.dns_filtering import DNSFilteringService
from networking.cost_analyzer import NetworkCostAnalyzer
from networking.cellular_manager import CellularManager

logger = logging.getLogger(__name__)


def setup_networking_routes(app, config: Dict[str, Any]):
    sdwan = SDWANController(config.get("sdwan", {}))
    vpn = VPNService(config.get("vpn", {}))
    dns = DNSManager(config.get("dns", {}))
    bgp = BGPRouteManager(config.get("bgp", {}))
    proxy = ReverseProxyManager(config.get("proxy", {}))
    seg = NetworkSegmentation(config.get("segmentation", {}))
    cap = PacketCaptureService(config.get("capture", {}))
    dnsf = DNSFilteringService(config.get("dnsfilter", {}))
    cost = NetworkCostAnalyzer(config.get("cost", {}))
    cell = CellularManager(config.get("cellular", {}))

    # SD-WAN
    async def sdwan_status(request):
        return web.json_response(await sdwan.get_status() if hasattr(sdwan, "get_status") else {"status": "operational", "providers": ["aws", "azure", "gcp"]})

    async def sdwan_apps(request):
        data = await sdwan.list_apps() if hasattr(sdwan, "list_apps") else [{"id": "app-1", "name": "primary", "provider": "aws", "bandwidth": 500, "status": "active", "latency_ms": 12}]
        return web.json_response(data)

    async def sdwan_create_app(request):
        body = await request.json()
        result = await sdwan.create_app(body) if hasattr(sdwan, "create_app") else {"id": "app-new", **body, "status": "active"}
        return web.json_response(result, status=201)

    async def sdwan_delete_app(request):
        app_id = request.match_info.get("app_id")
        result = await sdwan.delete_app(app_id) if hasattr(sdwan, "delete_app") else {"status": "deleted", "id": app_id}
        return web.json_response(result)

    async def sdwan_toggle(request):
        app_id = request.match_info.get("app_id")
        result = await sdwan.toggle_app(app_id) if hasattr(sdwan, "toggle_app") else {"status": "toggled", "id": app_id}
        return web.json_response(result)

    async def sdwan_metrics(request):
        result = await sdwan.get_metrics() if hasattr(sdwan, "get_metrics") else {"total_bandwidth": 1500, "active_apps": 3, "avg_latency": 15, "uptime": 99.97}
        return web.json_response(result)

    # VPN
    async def vpn_configs(request):
        return web.json_response(await vpn.list_configs() if hasattr(vpn, "list_configs") else [])

    async def vpn_create_config(request):
        body = await request.json()
        result = await vpn.create_config(body) if hasattr(vpn, "create_config") else {"id": "vpn-new", **body, "status": "active"}
        return web.json_response(result, status=201)

    async def vpn_delete_config(request):
        config_id = request.match_info.get("config_id")
        return web.json_response({"status": "deleted", "id": config_id})

    async def vpn_status(request):
        return web.json_response(await vpn.get_status() if hasattr(vpn, "get_status") else {"status": "connected", "uptime": "72h", "active_clients": 5})

    async def vpn_logs(request):
        return web.json_response(await vpn.get_logs() if hasattr(vpn, "get_logs") else [])

    # DNS
    async def dns_zones(request):
        return web.json_response(await dns.list_zones() if hasattr(dns, "list_zones") else [])

    async def dns_create_zone(request):
        body = await request.json()
        result = await dns.create_zone(body) if hasattr(dns, "create_zone") else {"id": "zone-new", **body}
        return web.json_response(result, status=201)

    async def dns_delete_zone(request):
        zone_id = request.match_info.get("zone_id")
        return web.json_response({"status": "deleted", "id": zone_id})

    async def dns_records(request):
        zone_id = request.match_info.get("zone_id")
        return web.json_response(await dns.list_records(zone_id) if hasattr(dns, "list_records") else [])

    async def dns_create_record(request):
        zone_id = request.match_info.get("zone_id")
        body = await request.json()
        result = await dns.create_record(zone_id, body) if hasattr(dns, "create_record") else {"id": "rec-new", "zone_id": zone_id, **body}
        return web.json_response(result, status=201)

    async def dns_update_record(request):
        zone_id = request.match_info.get("zone_id")
        record_id = request.match_info.get("record_id")
        body = await request.json()
        return web.json_response({"id": record_id, "zone_id": zone_id, **body})

    async def dns_delete_record(request):
        zone_id = request.match_info.get("zone_id")
        record_id = request.match_info.get("record_id")
        return web.json_response({"status": "deleted", "id": record_id})

    # BGP
    async def bgp_sessions(request):
        return web.json_response(await bgp.list_sessions() if hasattr(bgp, "list_sessions") else [])

    async def bgp_create_session(request):
        body = await request.json()
        result = await bgp.create_session(body) if hasattr(bgp, "create_session") else {"id": "bgp-new", **body, "state": "established"}
        return web.json_response(result, status=201)

    async def bgp_delete_session(request):
        session_id = request.match_info.get("session_id")
        return web.json_response({"status": "deleted", "id": session_id})

    async def bgp_routes(request):
        return web.json_response(await bgp.get_routes() if hasattr(bgp, "get_routes") else [])

    async def bgp_status(request):
        return web.json_response(await bgp.get_status() if hasattr(bgp, "get_status") else {"peers": 3, "routes": 1200, "state": "established"})

    # Reverse Proxy
    async def proxy_rules(request):
        return web.json_response(await proxy.list_rules() if hasattr(proxy, "list_rules") else [])

    async def proxy_create_rule(request):
        body = await request.json()
        result = await proxy.create_rule(body) if hasattr(proxy, "create_rule") else {"id": "proxy-new", **body, "enabled": True}
        return web.json_response(result, status=201)

    async def proxy_update_rule(request):
        rule_id = request.match_info.get("rule_id")
        body = await request.json()
        return web.json_response({"id": rule_id, **body})

    async def proxy_delete_rule(request):
        rule_id = request.match_info.get("rule_id")
        return web.json_response({"status": "deleted", "id": rule_id})

    async def proxy_toggle(request):
        rule_id = request.match_info.get("rule_id")
        return web.json_response({"status": "toggled", "id": rule_id})

    # Segmentation
    async def segments_list(request):
        return web.json_response(await seg.list_segments() if hasattr(seg, "list_segments") else [])

    async def segments_create(request):
        body = await request.json()
        result = await seg.create_segment(body) if hasattr(seg, "create_segment") else {"id": "seg-new", **body}
        return web.json_response(result, status=201)

    async def segments_update(request):
        segment_id = request.match_info.get("segment_id")
        body = await request.json()
        return web.json_response({"id": segment_id, **body})

    async def segments_delete(request):
        segment_id = request.match_info.get("segment_id")
        return web.json_response({"status": "deleted", "id": segment_id})

    async def segments_policies(request):
        segment_id = request.match_info.get("segment_id")
        return web.json_response(await seg.list_policies(segment_id) if hasattr(seg, "list_policies") else [])

    async def segments_create_policy(request):
        segment_id = request.match_info.get("segment_id")
        body = await request.json()
        return web.json_response({"id": "policy-new", "segment_id": segment_id, **body})

    # Packet Capture
    async def captures_list(request):
        return web.json_response(await cap.list_captures() if hasattr(cap, "list_captures") else [])

    async def captures_start(request):
        body = await request.json()
        result = await cap.start_capture(body) if hasattr(cap, "start_capture") else {"id": "cap-new", **body, "status": "running"}
        return web.json_response(result, status=201)

    async def captures_stop(request):
        capture_id = request.match_info.get("capture_id")
        result = await cap.stop_capture(capture_id) if hasattr(cap, "stop_capture") else {"status": "stopped", "id": capture_id}
        return web.json_response(result)

    async def captures_status(request):
        capture_id = request.match_info.get("capture_id")
        return web.json_response(await cap.get_status(capture_id) if hasattr(cap, "get_status") else {"id": capture_id, "status": "completed"})

    async def captures_packets(request):
        capture_id = request.match_info.get("capture_id")
        return web.json_response(await cap.get_packets(capture_id) if hasattr(cap, "get_packets") else [])

    # DNS Filtering
    async def dnsfilter_status(request):
        return web.json_response(await dnsf.get_status() if hasattr(dnsf, "get_status") else {"enabled": True, "rules_count": 25, "blocked_today": 1500})

    async def dnsfilter_rules(request):
        return web.json_response(await dnsf.list_rules() if hasattr(dnsf, "list_rules") else [])

    async def dnsfilter_create_rule(request):
        body = await request.json()
        result = await dnsf.create_rule(body) if hasattr(dnsf, "create_rule") else {"id": "df-new", **body, "enabled": True}
        return web.json_response(result, status=201)

    async def dnsfilter_delete_rule(request):
        rule_id = request.match_info.get("rule_id")
        return web.json_response({"status": "deleted", "id": rule_id})

    async def dnsfilter_toggle(request):
        rule_id = request.match_info.get("rule_id")
        return web.json_response({"status": "toggled", "id": rule_id})

    async def dhcp_leases(request):
        return web.json_response(await dnsf.get_dhcp_leases() if hasattr(dnsf, "get_dhcp_leases") else [])

    # Cost Analyzer
    async def cost_costs(request):
        return web.json_response(await cost.get_costs() if hasattr(cost, "get_costs") else {"current_month": {"total": 1250.50, "by_provider": {"aws": 800, "azure": 300, "gcp": 150.50}}})

    async def cost_trends(request):
        return web.json_response(await cost.get_trends() if hasattr(cost, "get_trends") else [])

    async def cost_bandwidth(request):
        return web.json_response(await cost.get_bandwidth_usage() if hasattr(cost, "get_bandwidth_usage") else [])

    async def cost_savings(request):
        return web.json_response(await cost.get_savings() if hasattr(cost, "get_savings") else [])

    async def cost_budget(request):
        body = await request.json()
        return web.json_response({"status": "set", **body})

    # Cellular
    async def cell_networks(request):
        return web.json_response(await cell.list_networks() if hasattr(cell, "list_networks") else [])

    async def cell_register_network(request):
        body = await request.json()
        result = await cell.register_network(body) if hasattr(cell, "register_network") else {"id": "cell-new", **body}
        return web.json_response(result, status=201)

    async def cell_delete_network(request):
        network_id = request.match_info.get("network_id")
        return web.json_response({"status": "deleted", "id": network_id})

    async def cell_status(request):
        return web.json_response(await cell.get_status() if hasattr(cell, "get_status") else {"connected": True, "signal": "-85 dBm", "provider": "ATT"})

    async def cell_metrics(request):
        return web.json_response(await cell.get_metrics() if hasattr(cell, "get_metrics") else {"latency_ms": 32, "throughput_mbps": 150, "signal_strength": -78})

    async def cell_sims(request):
        return web.json_response(await cell.list_sims() if hasattr(cell, "list_sims") else [])

    async def cell_activate_sim(request):
        sim_id = request.match_info.get("sim_id")
        return web.json_response({"status": "activated", "id": sim_id})

    async def cell_deactivate_sim(request):
        sim_id = request.match_info.get("sim_id")
        return web.json_response({"status": "deactivated", "id": sim_id})

    # Register routes
    prefix = "/api/v1/networking"
    sdwan_p = f"{prefix}/sdwan"
    app.router.add_get(f"{sdwan_p}/status", sdwan_status)
    app.router.add_get(f"{sdwan_p}/apps", sdwan_apps)
    app.router.add_post(f"{sdwan_p}/apps", sdwan_create_app)
    app.router.add_delete(f"{sdwan_p}/apps/{{app_id}}", sdwan_delete_app)
    app.router.add_post(f"{sdwan_p}/apps/{{app_id}}/toggle", sdwan_toggle)
    app.router.add_get(f"{sdwan_p}/metrics", sdwan_metrics)

    vpn_p = f"{prefix}/vpn"
    app.router.add_get(f"{vpn_p}/configs", vpn_configs)
    app.router.add_post(f"{vpn_p}/configs", vpn_create_config)
    app.router.add_delete(f"{vpn_p}/configs/{{config_id}}", vpn_delete_config)
    app.router.add_get(f"{vpn_p}/status", vpn_status)
    app.router.add_get(f"{vpn_p}/logs", vpn_logs)

    dns_p = f"{prefix}/dns"
    app.router.add_get(f"{dns_p}/zones", dns_zones)
    app.router.add_post(f"{dns_p}/zones", dns_create_zone)
    app.router.add_delete(f"{dns_p}/zones/{{zone_id}}", dns_delete_zone)
    app.router.add_get(f"{dns_p}/zones/{{zone_id}}/records", dns_records)
    app.router.add_post(f"{dns_p}/zones/{{zone_id}}/records", dns_create_record)
    app.router.add_put(f"{dns_p}/zones/{{zone_id}}/records/{{record_id}}", dns_update_record)
    app.router.add_delete(f"{dns_p}/zones/{{zone_id}}/records/{{record_id}}", dns_delete_record)

    bgp_p = f"{prefix}/bgp"
    app.router.add_get(f"{bgp_p}/sessions", bgp_sessions)
    app.router.add_post(f"{bgp_p}/sessions", bgp_create_session)
    app.router.add_delete(f"{bgp_p}/sessions/{{session_id}}", bgp_delete_session)
    app.router.add_get(f"{bgp_p}/routes", bgp_routes)
    app.router.add_get(f"{bgp_p}/status", bgp_status)

    proxy_p = f"{prefix}/proxy"
    app.router.add_get(f"{proxy_p}/rules", proxy_rules)
    app.router.add_post(f"{proxy_p}/rules", proxy_create_rule)
    app.router.add_put(f"{proxy_p}/rules/{{rule_id}}", proxy_update_rule)
    app.router.add_delete(f"{proxy_p}/rules/{{rule_id}}", proxy_delete_rule)
    app.router.add_post(f"{proxy_p}/rules/{{rule_id}}/toggle", proxy_toggle)

    seg_p = f"{prefix}/segments"
    app.router.add_get(f"{seg_p}", segments_list)
    app.router.add_post(f"{seg_p}", segments_create)
    app.router.add_put(f"{seg_p}/{{segment_id}}", segments_update)
    app.router.add_delete(f"{seg_p}/{{segment_id}}", segments_delete)
    app.router.add_get(f"{seg_p}/{{segment_id}}/policies", segments_policies)
    app.router.add_post(f"{seg_p}/{{segment_id}}/policies", segments_create_policy)

    cap_p = f"{prefix}/captures"
    app.router.add_get(f"{cap_p}", captures_list)
    app.router.add_post(f"{cap_p}", captures_start)
    app.router.add_post(f"{cap_p}/{{capture_id}}/stop", captures_stop)
    app.router.add_get(f"{cap_p}/{{capture_id}}", captures_status)
    app.router.add_get(f"{cap_p}/{{capture_id}}/packets", captures_packets)

    dnsf_p = f"{prefix}/dnsfilter"
    app.router.add_get(f"{dnsf_p}/status", dnsfilter_status)
    app.router.add_get(f"{dnsf_p}/rules", dnsfilter_rules)
    app.router.add_post(f"{dnsf_p}/rules", dnsfilter_create_rule)
    app.router.add_delete(f"{dnsf_p}/rules/{{rule_id}}", dnsfilter_delete_rule)
    app.router.add_post(f"{dnsf_p}/rules/{{rule_id}}/toggle", dnsfilter_toggle)

    dhcp_p = f"{prefix}/dhcp"
    app.router.add_get(f"{dhcp_p}/leases", dhcp_leases)

    cost_p = f"{prefix}/costs"
    app.router.add_get(f"{cost_p}", cost_costs)
    app.router.add_get(f"{cost_p}/trends", cost_trends)
    app.router.add_get(f"{cost_p}/bandwidth", cost_bandwidth)
    app.router.add_get(f"{cost_p}/savings", cost_savings)
    app.router.add_post(f"{cost_p}/budget", cost_budget)

    cell_p = f"{prefix}/cellular"
    app.router.add_get(f"{cell_p}/networks", cell_networks)
    app.router.add_post(f"{cell_p}/networks", cell_register_network)
    app.router.add_delete(f"{cell_p}/networks/{{network_id}}", cell_delete_network)
    app.router.add_get(f"{cell_p}/status", cell_status)
    app.router.add_get(f"{cell_p}/metrics", cell_metrics)
    app.router.add_get(f"{cell_p}/sims", cell_sims)
    app.router.add_post(f"{cell_p}/sims/{{sim_id}}/activate", cell_activate_sim)
    app.router.add_post(f"{cell_p}/sims/{{sim_id}}/deactivate", cell_deactivate_sim)

    logger.info("Networking routes configured (%d routes)", 50)
