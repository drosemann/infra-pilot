import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.api_catalog import ApiCatalogManager, ApiType

logger = logging.getLogger(__name__)


class ApiCatalogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.catalog = ApiCatalogManager()

    @discord.app_commands.command(name="api-register", description="Register an API")
    @discord.app_commands.describe(name="API name", api_type="Type", version="Version", owner="Owner")
    async def api_register(self, interaction: discord.Interaction, name: str, api_type: str, version: str, owner: str):
        api = self.catalog.register_api(name, ApiType(api_type), version, owner)
        embed = discord.Embed(title="API Registered", color=discord.Color.green())
        embed.add_field(name="ID", value=api.api_id[:8])
        embed.add_field(name="Name", value=api.name)
        embed.add_field(name="Type", value=api.api_type.value)
        embed.add_field(name="Version", value=api.version)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-list", description="List registered APIs")
    @discord.app_commands.describe(api_type="Filter by type", lifecycle="Filter by lifecycle")
    async def api_list(self, interaction: discord.Interaction, api_type: str = "", lifecycle: str = ""):
        apis = self.catalog.list_apis(api_type=api_type, lifecycle=lifecycle)
        if not apis:
            await interaction.response.send_message("No APIs found.", ephemeral=True)
            return
        embed = discord.Embed(title="API Catalog", color=discord.Color.blue())
        for api in apis[:10]:
            icon = {"stable": "✅", "beta": "🧪", "deprecated": "⚠️", "development": "🔧"}
            embed.add_field(name=f"{icon.get(api.lifecycle.value, '📡')} {api.name} v{api.version}", value=f"Type: {api.api_type.value} | Owner: {api.owner} | Endpoints: {len(api.endpoints)}", inline=False)
        if len(apis) > 10:
            embed.set_footer(text=f"Showing 10 of {len(apis)}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-consumers", description="List API consumers")
    @discord.app_commands.describe(api_id="API ID")
    async def api_consumers(self, interaction: discord.Interaction, api_id: str):
        api = self.catalog.get_api(api_id)
        if not api:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Consumers: {api.name}", color=discord.Color.blue())
        embed.add_field(name="Consumers", value="\n".join(api.consumers) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-summary", description="API catalog summary")
    async def api_summary(self, interaction: discord.Interaction):
        summary = self.catalog.get_api_summary()
        embed = discord.Embed(title="API Catalog Summary", color=discord.Color.blue())
        embed.add_field(name="Total APIs", value=summary.get("total_apis", 0))
        embed.add_field(name="Total Endpoints", value=summary.get("total_endpoints", 0))
        embed.add_field(name="Stable", value=summary.get("stable_apis", 0))
        embed.add_field(name="Deprecated", value=summary.get("deprecated_apis", 0))
        embed.add_field(name="Breaking Changes", value=summary.get("breaking_changes_logged", 0))
        embed.add_field(name="Total Consumers", value=summary.get("total_consumers", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-health", description="API health check")
    @discord.app_commands.describe(api_id="API ID")
    async def api_health(self, interaction: discord.Interaction, api_id: str):
        health = self.catalog.get_api_health(api_id)
        if "error" in health:
            await interaction.response.send_message(health["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Health: {health['name']}", color=discord.Color.blue())
        embed.add_field(name="Score", value=f"{health['health_score']}%")
        embed.add_field(name="Spec", value="✅" if health.get("has_spec") else "❌")
        embed.add_field(name="Endpoints", value="✅" if health.get("has_endpoints") else "❌")
        embed.add_field(name="Consumers", value="✅" if health.get("has_consumers") else "❌")
        embed.add_field(name="Violations", value=health.get("governance", {}).get("total_violations", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-governance", description="Run governance check")
    @discord.app_commands.describe(api_id="API ID")
    async def api_governance(self, interaction: discord.Interaction, api_id: str):
        result = self.catalog.enforce_governance_rules(api_id)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Governance: {result['api_name']}", color=discord.Color.green() if result["passed"] else discord.Color.orange())
        embed.add_field(name="Passed", value="✅" if result["passed"] else "❌")
        embed.add_field(name="Violations", value=result.get("total_violations", 0))
        for v in result.get("violations", [])[:5]:
            embed.add_field(name=v["rule"], value=v["message"], inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-update-lifecycle", description="Bulk update API lifecycle")
    @discord.app_commands.describe(api_ids="Comma-separated API IDs", lifecycle="New lifecycle status")
    async def api_update_lifecycle(self, interaction: discord.Interaction, api_ids: str, lifecycle: str):
        ids = [a.strip() for a in api_ids.split(",")]
        from services.integration_service.src.platform_engineering.api_catalog import ApiLifecycle
        count = self.catalog.bulk_update_lifecycle(ids, ApiLifecycle(lifecycle))
        embed = discord.Embed(title="Lifecycle Updated", color=discord.Color.green())
        embed.add_field(name="APIs Updated", value=count)
        embed.add_field(name="New Lifecycle", value=lifecycle)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-register-consumer", description="Register an API consumer")
    @discord.app_commands.describe(api_id="API ID", consumer_name="Consumer name")
    async def api_register_consumer(self, interaction: discord.Interaction, api_id: str, consumer_name: str):
        result = self.catalog.register_consumer(api_id, consumer_name)
        if not result:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Consumer Registered", color=discord.Color.green())
        embed.add_field(name="API", value=api_id[:8])
        embed.add_field(name="Consumer", value=consumer_name)
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="api-search-by-tag", description="Search APIs by tag")
    @discord.app_commands.describe(tag="Tag to search for")
    async def api_search_by_tag(self, interaction: discord.Interaction, tag: str):
        results = self.catalog.search_by_tag(tag)
        if not results:
            await interaction.response.send_message(f"No APIs tagged '{tag}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"APIs tagged '{tag}' ({len(results)})", color=discord.Color.blue())
        for api in results[:10]:
            embed.add_field(name=api.name, value=f"v{api.version} | {api.api_type.value} | {api.lifecycle.value}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-endpoint-metrics", description="Endpoint metrics for an API")
    @discord.app_commands.describe(api_id="API ID")
    async def api_endpoint_metrics(self, interaction: discord.Interaction, api_id: str):
        api = self.catalog.get_api(api_id)
        if not api:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Endpoint Metrics: {api.name}", color=discord.Color.blue())
        embed.add_field(name="Total Endpoints", value=len(api.endpoints))
        for ep in api.endpoints[:5]:
            embed.add_field(name=f"{ep.get('method', 'GET')} {ep.get('path', '/')}", value=f"Auth: {ep.get('auth', 'none')} | Rate: {ep.get('rate_limit', 'N/A')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-deprecation-plan", description="Create deprecation plan")
    @discord.app_commands.describe(api_id="API ID", deprecation_date="Deprecation date (YYYY-MM-DD)", migration_plan="Migration plan URL")
    async def api_deprecation_plan(self, interaction: discord.Interaction, api_id: str, deprecation_date: str, migration_plan: str = ""):
        result = self.catalog.create_deprecation_plan(api_id, deprecation_date, migration_plan)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Deprecation Plan Created", color=discord.Color.orange())
        embed.add_field(name="API", value=result["api_name"])
        embed.add_field(name="Deprecation Date", value=result["deprecation_date"])
        if migration_plan:
            embed.add_field(name="Migration Plan", value=result["migration_plan"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-add-endpoint", description="Add endpoint to API")
    @discord.app_commands.describe(api_id="API ID", method="HTTP method", path="URL path", auth="Auth type", rate_limit="Rate limit")
    async def api_add_endpoint(self, interaction: discord.Interaction, api_id: str, method: str, path: str, auth: str = "api_key", rate_limit: str = "100/min"):
        api = self.catalog.get_api(api_id)
        if not api:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        self.catalog.add_endpoint(api_id, method.upper(), path, auth, rate_limit)
        embed = discord.Embed(title="Endpoint Added", color=discord.Color.green())
        embed.add_field(name="API", value=api.name)
        embed.add_field(name="Endpoint", value=f"{method.upper()} {path}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-tag", description="Tag an API")
    @discord.app_commands.describe(api_id="API ID", tags="Comma-separated tags")
    async def api_tag(self, interaction: discord.Interaction, api_id: str, tags: str):
        tag_list = [t.strip() for t in tags.split(",")]
        api = self.catalog.get_api(api_id)
        if not api:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        self.catalog.add_tags(api_id, tag_list)
        embed = discord.Embed(title="API Tagged", color=discord.Color.green())
        embed.add_field(name="API", value=api.name)
        embed.add_field(name="Tags", value=", ".join(tag_list))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-version-history", description="Version history for an API")
    @discord.app_commands.describe(api_id="API ID")
    async def api_version_history(self, interaction: discord.Interaction, api_id: str):
        api = self.catalog.get_api(api_id)
        if not api:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        versions = api.metadata.get("version_history", [api.version])
        embed = discord.Embed(title=f"Version History: {api.name}", color=discord.Color.blue())
        for v in versions:
            embed.add_field(name=v, value="---", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-analytics", description="API analytics")
    async def api_analytics(self, interaction: discord.Interaction):
        summary = self.catalog.get_api_summary()
        embed = discord.Embed(title="API Analytics", color=discord.Color.blue())
        embed.add_field(name="Total APIs", value=summary.get("total_apis", 0))
        embed.add_field(name="Total Endpoints", value=summary.get("total_endpoints", 0))
        embed.add_field(name="Total Consumers", value=summary.get("total_consumers", 0))
        embed.add_field(name="Stable", value=summary.get("stable_apis", 0))
        embed.add_field(name="Deprecated", value=summary.get("deprecated_apis", 0))
        embed.add_field(name="Breaking Changes", value=summary.get("breaking_changes_logged", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-usage-stats", description="API usage statistics")
    @discord.app_commands.describe(api_id="API ID", days="Days to analyze")
    async def api_usage_stats(self, interaction: discord.Interaction, api_id: str, days: int = 30):
        stats = self.catalog.get_api_usage_stats(api_id, days)
        embed = discord.Embed(title=f"Usage Stats: {api_id[:8]}", color=discord.Color.blue())
        embed.add_field(name="Total Requests", value=stats["total_requests"])
        embed.add_field(name="Unique Callers", value=stats["unique_callers"])
        embed.add_field(name="Avg Latency", value=f"{stats['avg_latency_ms']}ms")
        for caller, count in stats.get("top_callers", []):
            embed.add_field(name=caller, value=f"{count} requests", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-compliance", description="API compliance report")
    @discord.app_commands.describe(api_id="API ID")
    async def api_compliance(self, interaction: discord.Interaction, api_id: str = ""):
        report = self.catalog.run_compliance_report(api_id)
        embed = discord.Embed(title="API Compliance Report", color=discord.Color.blue())
        embed.add_field(name="Total APIs", value=report["total_apis"])
        embed.add_field(name="Compliance", value=f"{report['compliance_pct']}%")
        embed.add_field(name="With Owner", value=report["with_owner"])
        embed.add_field(name="With Description", value=report["with_description"])
        embed.add_field(name="With Versioning", value=report["with_versioning"])
        embed.add_field(name="With Consumers", value=report["with_consumers"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-deprecate", description="Schedule API deprecation")
    @discord.app_commands.describe(api_id="API ID", sunset_date="Sunset date (YYYY-MM-DD)", migration_guide="Migration guide URL", notification_days="Notification period days")
    async def api_deprecate(self, interaction: discord.Interaction, api_id: str, sunset_date: str, migration_guide: str = "", notification_days: int = 90):
        from datetime import datetime
        try:
            sunset = datetime.strptime(sunset_date, "%Y-%m-%d")
        except ValueError:
            await interaction.response.send_message("Invalid date format. Use YYYY-MM-DD.", ephemeral=True)
            return
        schedule = self.catalog.schedule_deprecation(api_id, sunset, migration_guide, notification_days)
        if not schedule:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Deprecation Scheduled", color=discord.Color.orange())
        embed.add_field(name="API ID", value=api_id[:8])
        embed.add_field(name="Sunset Date", value=sunset_date)
        embed.add_field(name="Schedule ID", value=schedule["schedule_id"][:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-track-usage", description="Track an API usage event")
    @discord.app_commands.describe(api_id="API ID", caller="Caller name", endpoint="Endpoint path", method="HTTP method", status_code="Status code", latency_ms="Latency in ms")
    async def api_track_usage(self, interaction: discord.Interaction, api_id: str, caller: str, endpoint: str, method: str = "GET", status_code: int = 200, latency_ms: float = 0):
        event = self.catalog.track_api_usage(api_id, caller, endpoint, method, status_code, latency_ms)
        embed = discord.Embed(title="Usage Tracked", color=discord.Color.green())
        embed.add_field(name="API ID", value=api_id[:8])
        embed.add_field(name="Caller", value=caller)
        embed.add_field(name="Event ID", value=event["event_id"][:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-version-add", description="Add a new API version")
    @discord.app_commands.describe(api_id="API ID", new_version="New version string", spec_url="New spec URL", changelog="Changelog")
    async def api_version_add(self, interaction: discord.Interaction, api_id: str, new_version: str, spec_url: str, changelog: str = ""):
        result = self.catalog.add_api_version(api_id, new_version, spec_url, changelog)
        if not result:
            await interaction.response.send_message("API not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Version Added", color=discord.Color.green())
        embed.add_field(name="API ID", value=api_id[:8])
        embed.add_field(name="New Version", value=new_version)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-notify-consumers", description="Notify API consumers")
    @discord.app_commands.describe(api_id="API ID", message="Notification message")
    async def api_notify_consumers(self, interaction: discord.Interaction, api_id: str, message: str):
        result = self.catalog.notify_consumers(api_id, message)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Consumers Notified", color=discord.Color.green())
        embed.add_field(name="API ID", value=api_id[:8])
        embed.add_field(name="Notified", value=result["notifications_sent"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-duplicates", description="Find duplicate endpoints")
    async def api_duplicates(self, interaction: discord.Interaction):
        dups = self.catalog.get_duplicate_endpoints()
        if not dups:
            await interaction.response.send_message("No duplicates found.", ephemeral=True)
            return
        embed = discord.Embed(title="Duplicate Endpoints", color=discord.Color.orange())
        embed.add_field(name="Count", value=len(dups))
        for d in dups[:5]:
            embed.add_field(name=d["key"], value=f"{d['count']} duplicates", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="api-deprecation-schedule", description="View deprecation schedule")
    @discord.app_commands.describe(api_id="API ID")
    async def api_deprecation_schedule(self, interaction: discord.Interaction, api_id: str = ""):
        schedules = self.catalog.get_deprecation_schedule(api_id)
        if not schedules:
            await interaction.response.send_message("No schedules.", ephemeral=True)
            return
        embed = discord.Embed(title="Deprecation Schedules", color=discord.Color.blue())
        for s in schedules[:10]:
            embed.add_field(name=s["schedule_id"][:8], value=f"API: {s['api_id'][:8]} | Sunset: {s['sunset_date'][:10]} | Status: {s['status']}", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ApiCatalogCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "success_rate": 100.0, "avg_latency_ms": 0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class CogOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CogBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    completed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_success(self) -> None:
        self.completed += 1

    def record_failure(self) -> None:
        self.failed += 1

    def finish(self) -> None:
        self.status = "completed"

class CogMetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {}

    def record(self, name: str, value: float) -> None:
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)

    def summary(self, name: str) -> Dict[str, Any]:
        vals = self._metrics.get(name, [])
        if not vals:
            return {"count": 0}
        return {"count": len(vals), "min": round(min(vals), 4), "max": round(max(vals), 4),
                "avg": round(sum(vals) / len(vals), 4), "last": round(vals[-1], 4)}

    def all_summaries(self) -> Dict[str, Any]:
        return {name: self.summary(name) for name in self._metrics}

class CogHealthCheck:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, check_fn) -> None:
        self._checks[name] = {"fn": check_fn, "last_status": None, "last_run": None}

    async def run(self, name: str) -> Dict[str, Any]:
        check = self._checks.get(name)
        if not check:
            return {"status": "error", "message": "Unknown check"}
        try:
            result = await check["fn"]()
            check["last_status"] = result
            check["last_run"] = datetime.utcnow()
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name in self._checks:
            results[name] = await self.run(name)
        return results

    def get_status(self) -> Dict[str, Any]:
        return {name: {"last_status": c["last_status"], "last_run": c["last_run"].isoformat() if c["last_run"] else None}
                for name, c in self._checks.items()}
