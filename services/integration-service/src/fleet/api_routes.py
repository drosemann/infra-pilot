import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiohttp import web

from .manager import (
    FleetManager, DeviceConfig, DeviceFirmware, DeviceCapability,
    FleetGroup, DeploymentPlan, FleetCommand, DeviceStatus, DeviceType,
)

routes = web.RouteTableDef()
manager = FleetManager()


@routes.get("/api/v1/fleet/health")
async def fleet_health(request: web.Request) -> web.Response:
    health = await manager.health_check()
    return web.json_response(health)


@routes.post("/api/v1/fleet/devices")
async def register_device(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    device_id = body.get("device_id", str(uuid.uuid4()))
    device = DeviceConfig(
        device_id=device_id,
        name=body.get("name", f"Device-{device_id}"),
        device_type=DeviceType(body.get("device_type", "unknown")),
        location=body.get("location"),
        status=DeviceStatus.PROVISIONING,
        tags=body.get("tags", {}),
        metadata=body.get("metadata", {}),
    )
    try:
        manager.registry.register_device(device)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=409)
    return web.json_response({"status": "registered", "device": device_id}, status=201)


@routes.post("/api/v1/fleet/devices/batch")
async def batch_register(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    configs = body.get("devices", [])
    registered = []
    for cfg in configs:
        device = DeviceConfig(
            device_id=cfg.get("device_id", str(uuid.uuid4())),
            name=cfg.get("name", "Unknown"),
            device_type=DeviceType(cfg.get("device_type", "unknown")),
            location=cfg.get("location"),
            tags=cfg.get("tags", {}),
        )
        try:
            manager.registry.register_device(device)
            registered.append(device.device_id)
        except ValueError:
            pass
    return web.json_response({"registered": registered, "count": len(registered)}, status=201)


@routes.get("/api/v1/fleet/devices")
async def list_devices(request: web.Request) -> web.Response:
    status_str = request.query.get("status")
    device_type_str = request.query.get("device_type")
    group_id = request.query.get("group_id")
    status = DeviceStatus(status_str) if status_str else None
    device_type = DeviceType(device_type_str) if device_type_str else None
    devices = manager.registry.list_devices(status=status, device_type=device_type, group_id=group_id)
    return web.json_response({
        "devices": [{
            "device_id": d.device_id,
            "name": d.name,
            "device_type": d.device_type.value,
            "status": d.status.value,
            "location": d.location,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "cpu_usage": d.cpu_usage,
            "memory_usage": d.memory_usage,
            "battery_level": d.battery_level,
        } for d in devices],
        "count": len(devices),
    })


@routes.get("/api/v1/fleet/devices/search")
async def search_devices(request: web.Request) -> web.Response:
    query = request.query.get("q", "")
    results = manager.registry.search_devices(query)
    return web.json_response({
        "query": query,
        "results": [{"device_id": d.device_id, "name": d.name, "status": d.status.value} for d in results],
        "count": len(results),
    })


@routes.get("/api/v1/fleet/devices/{device_id}")
async def get_device(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    device = manager.registry.get_device(device_id)
    if not device:
        return web.json_response({"error": "Device not found"}, status=404)
    return web.json_response({
        "device_id": device.device_id,
        "name": device.name,
        "device_type": device.device_type.value,
        "status": device.status.value,
        "location": device.location,
        "tags": device.tags,
        "metadata": device.metadata,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "created_at": device.created_at.isoformat(),
        "updated_at": device.updated_at.isoformat(),
        "cpu_usage": device.cpu_usage,
        "memory_usage": device.memory_usage,
        "disk_usage": device.disk_usage,
        "battery_level": device.battery_level,
        "signal_strength": device.signal_strength,
        "temperature": device.temperature,
        "firmware_version": device.firmware.version if device.firmware else None,
        "capabilities": [{"name": c.name, "version": c.version, "enabled": c.enabled} for c in device.capabilities],
        "power_state": device.power_state,
        "owner": device.owner,
        "group": device.group,
        "priority": device.priority,
    })


@routes.put("/api/v1/fleet/devices/{device_id}")
async def update_device(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    updates = {}
    for field in ["name", "location", "status", "cpu_usage", "memory_usage",
                  "disk_usage", "battery_level", "signal_strength", "temperature",
                  "power_state", "owner", "group", "priority"]:
        if field in body:
            updates[field] = body[field]
    if "status" in updates and isinstance(updates["status"], str):
        updates["status"] = DeviceStatus(updates["status"])
    device = manager.registry.update_device(device_id, updates)
    if not device:
        return web.json_response({"error": "Device not found"}, status=404)
    return web.json_response({"status": "updated", "device_id": device_id})


@routes.delete("/api/v1/fleet/devices/{device_id}")
async def deregister_device(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    if manager.registry.deregister_device(device_id):
        return web.json_response({"status": "deregistered", "device_id": device_id})
    return web.json_response({"error": "Device not found"}, status=404)


@routes.post("/api/v1/fleet/devices/{device_id}/heartbeat")
async def device_heartbeat(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    try:
        body = await request.json() if request.has_body else {}
    except json.JSONDecodeError:
        body = {}
    try:
        await manager.handle_heartbeat(device_id, metrics=body.get("metrics"))
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=404)
    return web.json_response({"status": "heartbeat_received", "device_id": device_id})


@routes.post("/api/v1/fleet/devices/{device_id}/command")
async def send_command(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    cmd = FleetCommand(
        command_id=str(uuid.uuid4()),
        device_id=device_id,
        command_type=body.get("command_type", "ping"),
        payload=body.get("payload", {}),
        timeout=body.get("timeout", 30),
        priority=body.get("priority", 5),
    )
    manager.registry.queue_command(cmd)
    result = await manager.execute_command(cmd.command_id)
    return web.json_response({
        "command_id": cmd.command_id,
        "device_id": device_id,
        "command_type": cmd.command_type,
        "result": result,
    })


@routes.post("/api/v1/fleet/devices/batch-command")
async def batch_command(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    device_ids = body.get("device_ids", [])
    command_type = body.get("command_type", "ping")
    payload = body.get("payload", {})
    results = await manager.batch_command(device_ids, command_type, payload)
    return web.json_response({"results": results, "count": len(results)})


@routes.get("/api/v1/fleet/devices/{device_id}/analytics")
async def device_analytics(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    analytics = await manager.get_device_analytics(device_id)
    if "error" in analytics:
        return web.json_response(analytics, status=404)
    return web.json_response(analytics)


@routes.get("/api/v1/fleet/devices/{device_id}/commands")
async def list_device_commands(request: web.Request) -> web.Response:
    device_id = request.match_info["device_id"]
    status_str = request.query.get("status")
    cmds = manager.registry.list_commands(device_id=device_id, status=status_str)
    return web.json_response({
        "commands": [{
            "command_id": c.command_id,
            "command_type": c.command_type,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "executed_at": c.executed_at.isoformat() if c.executed_at else None,
            "result": c.result,
            "error": c.error,
        } for c in cmds],
        "count": len(cmds),
    })


@routes.post("/api/v1/fleet/groups")
async def create_group(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    group = FleetGroup(
        group_id=body.get("group_id", str(uuid.uuid4())),
        name=body.get("name", "New Group"),
        description=body.get("description", ""),
        tags=body.get("tags", {}),
    )
    try:
        manager.registry.create_group(group)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=409)
    return web.json_response({"status": "created", "group_id": group.group_id}, status=201)


@routes.get("/api/v1/fleet/groups")
async def list_groups(request: web.Request) -> web.Response:
    groups = manager.registry.list_groups()
    return web.json_response({
        "groups": [{
            "group_id": g.group_id,
            "name": g.name,
            "description": g.description,
            "device_count": len(g.device_ids),
            "created_at": g.created_at.isoformat(),
        } for g in groups],
        "count": len(groups),
    })


@routes.get("/api/v1/fleet/groups/{group_id}")
async def get_group(request: web.Request) -> web.Response:
    group_id = request.match_info["group_id"]
    group = manager.registry.get_group(group_id)
    if not group:
        return web.json_response({"error": "Group not found"}, status=404)
    return web.json_response({
        "group_id": group.group_id,
        "name": group.name,
        "description": group.description,
        "device_ids": list(group.device_ids),
        "tags": group.tags,
        "created_at": group.created_at.isoformat(),
        "updated_at": group.updated_at.isoformat(),
    })


@routes.put("/api/v1/fleet/groups/{group_id}")
async def update_group(request: web.Request) -> web.Response:
    group_id = request.match_info["group_id"]
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    group = manager.registry.update_group(group_id, body)
    if not group:
        return web.json_response({"error": "Group not found"}, status=404)
    return web.json_response({"status": "updated", "group_id": group_id})


@routes.delete("/api/v1/fleet/groups/{group_id}")
async def delete_group(request: web.Request) -> web.Response:
    group_id = request.match_info["group_id"]
    if manager.registry.delete_group(group_id):
        return web.json_response({"status": "deleted", "group_id": group_id})
    return web.json_response({"error": "Group not found"}, status=404)


@routes.post("/api/v1/fleet/groups/{group_id}/devices/{device_id}")
async def add_device_to_group(request: web.Request) -> web.Response:
    group_id = request.match_info["group_id"]
    device_id = request.match_info["device_id"]
    if manager.registry.add_device_to_group(device_id, group_id):
        return web.json_response({"status": "added", "device_id": device_id, "group_id": group_id})
    return web.json_response({"error": "Device or group not found"}, status=404)


@routes.delete("/api/v1/fleet/groups/{group_id}/devices/{device_id}")
async def remove_device_from_group(request: web.Request) -> web.Response:
    group_id = request.match_info["group_id"]
    device_id = request.match_info["device_id"]
    if manager.registry.remove_device_from_group(device_id, group_id):
        return web.json_response({"status": "removed", "device_id": device_id, "group_id": group_id})
    return web.json_response({"error": "Group not found"}, status=404)


@routes.post("/api/v1/fleet/deployments")
async def create_deployment(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    plan = DeploymentPlan(
        plan_id=body.get("plan_id", str(uuid.uuid4())),
        name=body.get("name", "New Deployment"),
        description=body.get("description", ""),
        target_groups=body.get("target_groups", []),
        target_devices=body.get("target_devices", []),
        actions=body.get("actions", []),
    )
    try:
        manager.registry.create_deployment(plan)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=409)
    return web.json_response({"status": "created", "plan_id": plan.plan_id}, status=201)


@routes.get("/api/v1/fleet/deployments")
async def list_deployments(request: web.Request) -> web.Response:
    status_filter = request.query.get("status")
    plans = manager.registry.list_deployments(status=status_filter)
    return web.json_response({
        "deployments": [{
            "plan_id": p.plan_id,
            "name": p.name,
            "status": p.status,
            "progress": p.progress,
            "created_at": p.created_at.isoformat(),
            "started_at": p.started_at.isoformat() if p.started_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        } for p in plans],
        "count": len(plans),
    })


@routes.post("/api/v1/fleet/deployments/{plan_id}/execute")
async def execute_deployment(request: web.Request) -> web.Response:
    plan_id = request.match_info["plan_id"]
    result = await manager.execute_deployment(plan_id)
    if "error" in result:
        return web.json_response(result, status=404)
    return web.json_response(result)


@routes.post("/api/v1/fleet/firmware")
async def add_firmware(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    checksum = body.get("checksum", "")
    fw = DeviceFirmware(
        version=body.get("version", "1.0.0"),
        build=body.get("build", ""),
        release_date=datetime.fromisoformat(body.get("release_date", datetime.utcnow().isoformat())),
        checksum=checksum,
        download_url=body.get("download_url", ""),
        changelog=body.get("changelog", []),
        required=body.get("required", False),
    )
    manager.add_firmware(fw)
    return web.json_response({"status": "added", "version": fw.version}, status=201)


@routes.get("/api/v1/fleet/firmware")
async def list_firmware(request: web.Request) -> web.Response:
    firmware_list = manager.list_firmware()
    return web.json_response({
        "firmware": [{
            "version": fw.version,
            "build": fw.build,
            "release_date": fw.release_date.isoformat(),
            "checksum": fw.checksum,
            "required": fw.required,
            "changelog": fw.changelog,
        } for fw in firmware_list],
        "count": len(firmware_list),
    })


@routes.post("/api/v1/fleet/ota-update")
async def ota_update(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    device_ids = body.get("device_ids", [])
    firmware_version = body.get("firmware_version")
    if not firmware_version:
        return web.json_response({"error": "firmware_version required"}, status=400)
    result = await manager.ota_update(device_ids, firmware_version)
    return web.json_response(result)


@routes.get("/api/v1/fleet/stats")
async def fleet_stats(request: web.Request) -> web.Response:
    by_type = manager.group_devices_by_type()
    by_status = manager.group_devices_by_status()
    by_location = manager.group_devices_by_location()
    return web.json_response({
        "by_type": {k: len(v) for k, v in by_type.items()},
        "by_status": {k: len(v) for k, v in by_status.items()},
        "by_location": {k: len(v) for k, v in by_location.items()},
        "total_devices": sum(len(v) for v in by_status.values()),
        "total_groups": len(manager.registry.list_groups()),
    })


@routes.post("/api/v1/fleet/reboot")
async def reboot_devices(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    device_ids = body.get("device_ids", [])
    result = await manager.reboot_devices(device_ids)
    return web.json_response(result)


@routes.post("/api/v1/fleet/shutdown")
async def shutdown_devices(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    device_ids = body.get("device_ids", [])
    result = await manager.shutdown_devices(device_ids)
    return web.json_response(result)


def setup_fleet_routes(app: web.Application):
    app.router.add_routes(routes)
    return manager
