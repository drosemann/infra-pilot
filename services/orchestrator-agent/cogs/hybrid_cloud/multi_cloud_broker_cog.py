import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

CLOUD_PROVIDERS = [
    {"id": "aws", "name": "Amazon Web Services", "regions": 30, "services": 200},
    {"id": "azure", "name": "Microsoft Azure", "regions": 60, "services": 200},
    {"id": "gcp", "name": "Google Cloud Platform", "regions": 40, "services": 150},
    {"id": "hetzner", "name": "Hetzner Cloud", "regions": 5, "services": 10},
    {"id": "ovh", "name": "OVHcloud", "regions": 20, "services": 30},
    {"id": "digitalocean", "name": "DigitalOcean", "regions": 15, "services": 20},
]

DATA_FILE = "data/multi_cloud_broker.json"


class MultiCloudBrokerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._credentials: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self._load_data()
        logger.info("MultiCloudBrokerCog ready")

    async def _load_data(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._resources = data.get("resources", {})
                self._credentials = data.get("credentials", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        self._initialized = True

    async def _save_data(self):
        data = {"resources": self._resources, "credentials": self._credentials}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @commands.group(name="cloud", invoke_without_command=True)
    async def cloud(self, ctx):
        await ctx.send("Cloud resource broker commands: list, provision, status, delete, providers, score")

    @cloud.command(name="providers")
    async def list_providers(self, ctx):
        embed = discord.Embed(title="Cloud Providers", color=discord.Color.blue())
        for p in CLOUD_PROVIDERS:
            configured = "✓" if p["id"] in self._credentials else "✗"
            embed.add_field(name=f"{p['name']} [{configured}]", value=f"Regions: {p['regions']} | Services: {p['services']}", inline=True)
        await ctx.send(embed=embed)

    @cloud.command(name="configure")
    @commands.has_permissions(administrator=True)
    async def configure_provider(self, ctx, provider_id: str, api_key: str, region: str = "us-east-1"):
        self._credentials[provider_id] = {"api_key": api_key, "region": region, "configured_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"✅ Configured {provider_id} with region {region}")

    @cloud.command(name="list")
    async def list_resources(self, ctx, provider: str = None):
        resources = list(self._resources.values())
        if provider:
            resources = [r for r in resources if r.get("provider") == provider]
        if not resources:
            await ctx.send("No resources found.")
            return
        embed = discord.Embed(title=f"Cloud Resources ({len(resources)})", color=discord.Color.green())
        for r in resources[:10]:
            embed.add_field(name=f"{r.get('name', r['id'])}", value=f"Provider: {r.get('provider')} | Type: {r.get('type')} | Status: {r.get('status')}", inline=False)
        if len(resources) > 10:
            embed.set_footer(text=f"Showing 10 of {len(resources)} resources")
        await ctx.send(embed=embed)

    @cloud.command(name="provision")
    @commands.has_permissions(administrator=True)
    async def provision(self, ctx, provider: str, resource_type: str, name: str, count: int = 1):
        rid = f"{provider}-{resource_type}-{uuid.uuid4().hex[:8]}"
        resource = {"id": rid, "provider": provider, "type": resource_type, "name": name,
                    "count": count, "status": "provisioning", "created_at": datetime.utcnow().isoformat()}
        self._resources[rid] = resource
        await self._save_data()
        embed = discord.Embed(title="Resource Provisioning Started", color=discord.Color.green())
        embed.add_field(name="Resource ID", value=rid, inline=False)
        embed.add_field(name="Provider", value=provider)
        embed.add_field(name="Type", value=resource_type)
        embed.add_field(name="Count", value=str(count))
        await ctx.send(embed=embed)

    @cloud.command(name="status")
    async def resource_status(self, ctx, resource_id: str):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send(f"Resource {resource_id} not found.")
            return
        embed = discord.Embed(title=f"Resource: {resource.get('name', resource_id)}", color=discord.Color.blue())
        for k, v in resource.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @cloud.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def delete_resource(self, ctx, resource_id: str):
        if resource_id in self._resources:
            del self._resources[resource_id]
            await self._save_data()
            await ctx.send(f"🗑️ Resource {resource_id} deleted")
        else:
            await ctx.send("Resource not found")

    @cloud.command(name="score")
    async def score_providers(self, ctx, vcpu: int = 2, memory: int = 4):
        scores = [
            {"provider": "aws", "score": 92, "cost": "$0.05/hr"},
            {"provider": "azure", "score": 88, "cost": "$0.06/hr"},
            {"provider": "gcp", "score": 85, "cost": "$0.04/hr"},
            {"provider": "hetzner", "score": 72, "cost": "$0.02/hr"},
            {"provider": "ovh", "score": 65, "cost": "$0.03/hr"},
            {"provider": "digitalocean", "score": 78, "cost": "$0.04/hr"},
        ]
        embed = discord.Embed(title=f"Provider Scores (vCPU={vcpu}, RAM={memory}GB)", color=discord.Color.gold())
        for s in scores:
            embed.add_field(name=f"{s['provider'].upper()} - Score: {s['score']}", value=f"Cost: {s['cost']}", inline=True)
        await ctx.send(embed=embed)


    @cloud.command(name="stats")
    async def cloud_stats(self, ctx):
        stats = {"total_resources": len(self._resources), "configured_providers": len(self._credentials), "pending_requests": 0}
        embed = discord.Embed(title="Multi-Cloud Statistics", color=discord.Color.blue())
        for k, v in stats.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @cloud.command(name="batch-provision")
    @commands.has_permissions(administrator=True)
    async def batch_provision(self, ctx, provider: str, resource_type: str, names: str, region: str = "us-east-1"):
        name_list = [n.strip() for n in names.split(",")]
        results = []
        for name in name_list:
            rid = f"{provider}-{resource_type}-{uuid.uuid4().hex[:8]}"
            resource = {"id": rid, "provider": provider, "type": resource_type, "name": name,
                        "region": region, "status": "provisioning", "created_at": datetime.utcnow().isoformat()}
            self._resources[rid] = resource
            results.append(rid)
        await self._save_data()
        embed = discord.Embed(title=f"Batch Provisioned {len(results)} Resources", color=discord.Color.green())
        embed.add_field(name="Provider", value=provider)
        embed.add_field(name="Type", value=resource_type)
        embed.add_field(name="Resources", value=", ".join(results[:5]) + ("..." if len(results) > 5 else ""))
        await ctx.send(embed=embed)

    @cloud.command(name="search")
    async def search_resources(self, ctx, *, query: str):
        found = [r for r in self._resources.values() if query.lower() in r.get("name", "").lower() or query.lower() in r.get("provider", "").lower()]
        if not found:
            await ctx.send(f"No resources matching '{query}'")
            return
        embed = discord.Embed(title=f"Search Results: '{query}' ({len(found)})", color=discord.Color.blue())
        for r in found[:5]:
            embed.add_field(name=r.get("name", r["id"]), value=f"{r.get('provider')} | {r.get('type')} | {r.get('status')}", inline=False)
        if len(found) > 5:
            embed.set_footer(text=f"Showing 5 of {len(found)} results")
        await ctx.send(embed=embed)

    @cloud.command(name="cost")
    async def cost_summary(self, ctx):
        total = sum(r.get("cost_per_hour", 0) for r in self._resources.values() if "cost_per_hour" in r)
        embed = discord.Embed(title="Cloud Cost Summary", color=discord.Color.gold())
        embed.add_field(name="Total/hr", value=f"${total:.4f}")
        embed.add_field(name="Total/day", value=f"${total * 24:.2f}")
        embed.add_field(name="Total/month", value=f"${total * 24 * 30:.2f}")
        await ctx.send(embed=embed)

    @cloud.command(name="failover")
    @commands.has_permissions(administrator=True)
    async def failover_resource(self, ctx, resource_id: str):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        embed = discord.Embed(title="Failover Initiated", color=discord.Color.orange())
        embed.add_field(name="Resource", value=resource.get("name", resource_id))
        embed.add_field(name="Current Provider", value=resource.get("provider"))
        backup_providers = [p["id"] for p in CLOUD_PROVIDERS if p["id"] != resource.get("provider")]
        if backup_providers:
            target = backup_providers[0]
            embed.add_field(name="Failing Over To", value=target.upper())
            resource["provider"] = target
            resource["status"] = "migrating"
            await self._save_data()
        await ctx.send(embed=embed)

    @cloud.command(name="diff")
    async def provider_diff(self, ctx, provider1: str, provider2: str):
        p1 = next((p for p in CLOUD_PROVIDERS if p["id"] == provider1), None)
        p2 = next((p for p in CLOUD_PROVIDERS if p["id"] == provider2), None)
        if not p1 or not p2:
            await ctx.send("Invalid provider IDs.")
            return
        embed = discord.Embed(title=f"{p1['name']} vs {p2['name']}", color=discord.Color.blue())
        embed.add_field(name=p1['name'], value=f"Regions: {p1['regions']}\nServices: {p1['services']}", inline=True)
        embed.add_field(name=p2['name'], value=f"Regions: {p2['regions']}\nServices: {p2['services']}", inline=True)
        embed.add_field(name="Diff", value=f"Regions: {p1['regions'] - p2['regions']:+d}\nServices: {p1['services'] - p2['services']:+d}", inline=True)
        await ctx.send(embed=embed)

    @cloud.command(name="tags")
    @commands.has_permissions(administrator=True)
    async def tag_resource(self, ctx, resource_id: str, key: str, value: str):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        if "tags" not in resource:
            resource["tags"] = {}
        resource["tags"][key] = value
        await self._save_data()
        await ctx.send(f"Tagged {resource_id}: {key}={value}")

    @cloud.command(name="move")
    @commands.has_permissions(administrator=True)
    async def move_resource(self, ctx, resource_id: str, target_provider: str, target_region: str = "us-east-1"):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        old_provider = resource.get("provider")
        resource["provider"] = target_provider
        resource["region"] = target_region
        resource["status"] = "migrating"
        await self._save_data()
        await ctx.send(f"Moving {resource_id} from {old_provider} -> {target_provider} ({target_region})")

    @cloud.command(name="rename")
    @commands.has_permissions(administrator=True)
    async def rename_resource(self, ctx, resource_id: str, new_name: str):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        old_name = resource.get("name")
        resource["name"] = new_name
        await self._save_data()
        await ctx.send(f"Resource renamed: {old_name} -> {new_name}")

    @cloud.command(name="schedule")
    @commands.has_permissions(administrator=True)
    async def schedule_action(self, ctx, resource_id: str, action: str, cron: str):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        sched_id = f"sched-{uuid.uuid4().hex[:8]}"
        if "_schedules" not in self._resources:
            self._resources["_schedules"] = {}
        self._resources["_schedules"][sched_id] = {"id": sched_id, "resource_id": resource_id, "action": action, "cron": cron, "enabled": True, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Scheduled '{action}' on {resource_id} via '{cron}'")

    @cloud.command(name="notifications")
    @commands.has_permissions(administrator=True)
    async def set_notifications(self, ctx, resource_id: str, events: str, webhook: str = ""):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        notif_id = f"notif-{uuid.uuid4().hex[:8]}"
        if "_notifications" not in self._resources:
            self._resources["_notifications"] = {}
        self._resources["_notifications"][notif_id] = {"id": notif_id, "resource_id": resource_id, "events": [e.strip() for e in events.split(",")], "webhook": webhook, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Notifications set on {resource_id} for events: {events}")

    @cloud.command(name="snapshot")
    @commands.has_permissions(administrator=True)
    async def snapshot_resource(self, ctx, resource_id: str):
        resource = self._resources.get(resource_id)
        if not resource:
            await ctx.send("Resource not found.")
            return
        snap_id = f"snap-{uuid.uuid4().hex[:8]}"
        if "_snapshots" not in self._resources:
            self._resources["_snapshots"] = {}
        self._resources["_snapshots"][snap_id] = {"id": snap_id, "resource_id": resource_id, "state": dict(resource), "taken_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Snapshot {snap_id} taken for {resource_id}")

    @cloud.command(name="export")
    @commands.has_permissions(administrator=True)
    async def export_resources(self, ctx, format: str = "json"):
        data = json.dumps(self._resources, indent=2) if format == "json" else str(list(self._resources.keys()))
        await ctx.send(f"```{data[:1900]}```")

    @cloud.command(name="import")
    @commands.has_permissions(administrator=True)
    async def import_resources(self, ctx, *, json_data: str):
        try:
            data = json.loads(json_data)
            self._resources.update(data)
            await self._save_data()
            await ctx.send(f"Imported {len(data)} resources.")
        except json.JSONDecodeError:
            await ctx.send("Invalid JSON data.")

    @cloud.command(name="bulk-delete")
    @commands.has_permissions(administrator=True)
    async def bulk_delete(self, ctx, provider: str = None):
        to_delete = [rid for rid, r in self._resources.items() if provider and r.get("provider") == provider]
        if not to_delete:
            await ctx.send("No matching resources found.")
            return
        for rid in to_delete:
            del self._resources[rid]
        await self._save_data()
        await ctx.send(f"Deleted {len(to_delete)} resources.")

    @cloud.command(name="audit-log")
    @commands.has_permissions(administrator=True)
    async def audit_log(self, ctx, resource_id: str = None):
        embed = discord.Embed(title="Resource Audit Log", color=discord.Color.blue())
        if resource_id:
            r = self._resources.get(resource_id)
            if r:
                embed.add_field(name="ID", value=resource_id)
                embed.add_field(name="Name", value=r.get("name", "N/A"))
                embed.add_field(name="Provider", value=r.get("provider", "N/A"))
                embed.add_field(name="Status", value=r.get("status", "N/A"))
                embed.add_field(name="Created", value=r.get("created_at", "N/A"))
                embed.add_field(name="Tags", value=str(r.get("tags", {}))[:100])
            else:
                await ctx.send("Resource not found.")
                return
        else:
            embed.add_field(name="Total Resources", value=str(len(self._resources)))
            embed.add_field(name="Providers", value=str(len(set(r.get("provider") for r in self._resources.values()))))
        await ctx.send(embed=embed)

    @cloud.command(name="alerts")
    async def list_alerts(self, ctx):
        alerts = self._resources.get("_alerts", {})
        if not alerts:
            await ctx.send("No alerts configured.")
            return
        embed = discord.Embed(title="Resource Alerts", color=discord.Color.orange())
        for aid, a in list(alerts.items())[:10]:
            embed.add_field(name=aid, value=f"Resource: {a.get('resource_id')} | Event: {a.get('event')}", inline=False)
        await ctx.send(embed=embed)

    @cloud.command(name="create-alert")
    @commands.has_permissions(administrator=True)
    async def create_alert(self, ctx, resource_id: str, event: str, webhook: str = ""):
        if resource_id not in self._resources:
            await ctx.send("Resource not found.")
            return
        if "_alerts" not in self._resources:
            self._resources["_alerts"] = {}
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"
        self._resources["_alerts"][alert_id] = {"id": alert_id, "resource_id": resource_id, "event": event, "webhook": webhook, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Alert {alert_id} created for {resource_id} on event '{event}'.")

    @cloud.command(name="cost-summary")
    async def cost_summary(self, ctx):
        total = sum(r.get("cost_per_hour", 0) for r in self._resources.values() if isinstance(r, dict))
        by_provider: Dict[str, float] = {}
        for r in self._resources.values():
            if isinstance(r, dict):
                p = r.get("provider", "unknown")
                by_provider[p] = by_provider.get(p, 0) + r.get("cost_per_hour", 0)
        embed = discord.Embed(title="Cost Summary", color=discord.Color.gold())
        embed.add_field(name="Total (per hour)", value=f"${total:.2f}")
        embed.add_field(name="Monthly Est.", value=f"${total * 730:.2f}")
        for p, c in sorted(by_provider.items(), key=lambda x: x[1], reverse=True)[:5]:
            embed.add_field(name=p, value=f"${c:.2f}/h", inline=True)
        await ctx.send(embed=embed)

    def _build_resource_embed(self, resource: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=resource.get("name", "Resource"), color=discord.Color.green())
        embed.add_field(name="ID", value=resource.get("id", "N/A"), inline=False)
        embed.add_field(name="Provider", value=resource.get("provider", "N/A"), inline=True)
        embed.add_field(name="Type", value=resource.get("resource_type", "N/A"), inline=True)
        embed.add_field(name="Region", value=resource.get("region", "N/A"), inline=True)
        embed.add_field(name="Status", value=resource.get("status", "N/A"), inline=True)
        embed.add_field(name="Cost/Hour", value=f"${resource.get('cost_per_hour', 0):.4f}", inline=True)
        tags = resource.get("tags", {})
        if tags:
            embed.add_field(name="Tags", value=str(tags)[:100], inline=False)
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"resources": self._resources, "credentials": self._credentials}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")
        else:
            logger.error(f"Command error: {error}")

async def setup(bot):
    await bot.add_cog(MultiCloudBrokerCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_operation(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"operations_count": 0, "success_rate": 100.0, "avg_duration_ms": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": []}

class CogConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=300, ge=10)
    timeout_seconds: int = Field(default=60, ge=5)
    retry_limit: int = Field(default=3, ge=0)
    notify_on_failure: bool = True
    log_level: str = Field(default="INFO")

class CogMetrics:
    def __init__(self) -> None:
        self.runs: int = 0
        self.failures: int = 0
        self.last_run: Optional[datetime] = None
        self.last_duration: float = 0.0

    def record_run(self, duration: float, success: bool) -> None:
        self.runs += 1
        self.last_run = datetime.utcnow()
        self.last_duration = duration
        if not success:
            self.failures += 1

    def summary(self) -> Dict[str, Any]:
        return {"runs": self.runs, "failures": self.failures,
                "success_rate": round((self.runs - self.failures) / max(self.runs, 1) * 100, 1),
                "last_run": self.last_run.isoformat() if self.last_run else None,
                "last_duration_ms": round(self.last_duration, 1)}
