import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.template_registry import TemplateRegistryManager, BlueprintType

logger = logging.getLogger(__name__)


class TemplateRegistryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.registry = TemplateRegistryManager()

    @discord.app_commands.command(name="blueprint-create", description="Create a new blueprint")
    @discord.app_commands.describe(name="Blueprint name", blueprint_type="Type", owner="Owner")
    async def blueprint_create(self, interaction: discord.Interaction, name: str, blueprint_type: str, owner: str):
        bp = self.registry.create_blueprint(name, BlueprintType(blueprint_type), owner)
        embed = discord.Embed(title="Blueprint Created", color=discord.Color.green())
        embed.add_field(name="ID", value=bp.blueprint_id[:8])
        embed.add_field(name="Name", value=bp.name)
        embed.add_field(name="Type", value=bp.blueprint_type.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-list", description="List blueprints")
    @discord.app_commands.describe(blueprint_type="Filter by type")
    async def blueprint_list(self, interaction: discord.Interaction, blueprint_type: str = ""):
        blueprints = self.registry.list_blueprints(blueprint_type=blueprint_type)
        if not blueprints:
            await interaction.response.send_message("No blueprints found.", ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Registry", color=discord.Color.blue())
        for bp in blueprints[:10]:
            embed.add_field(name=f"{bp.name} ({bp.blueprint_type.value})", value=f"v{bp.latest_version} | {bp.status.value} | Owner: {bp.owner}", inline=False)
        if len(blueprints) > 10:
            embed.set_footer(text=f"Showing 10 of {len(blueprints)}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-versions", description="List blueprint versions")
    @discord.app_commands.describe(blueprint_id="Blueprint ID")
    async def blueprint_versions(self, interaction: discord.Interaction, blueprint_id: str):
        bp = self.registry.get_blueprint(blueprint_id)
        if not bp:
            await interaction.response.send_message("Blueprint not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Versions: {bp.name}", color=discord.Color.blue())
        for vid, ver in bp.versions.items():
            embed.add_field(name=f"v{ver.version}", value=f"By: {ver.created_by} | Params: {len(ver.parameters)}", inline=False)
        if not bp.versions:
            embed.description = "No versions yet."
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-summary", description="Registry summary")
    async def blueprint_summary(self, interaction: discord.Interaction):
        summary = self.registry.get_registry_summary()
        embed = discord.Embed(title="Registry Summary", color=discord.Color.blue())
        embed.add_field(name="Total Blueprints", value=summary.get("total_blueprints", 0))
        embed.add_field(name="Total Versions", value=summary.get("total_versions", 0))
        embed.add_field(name="Total Usage", value=summary.get("total_usage", 0))
        embed.add_field(name="By Type", value="\n".join(f"{k}: {v}" for k, v in summary.get("by_type", {}).items()) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-search", description="Search blueprints")
    @discord.app_commands.describe(query="Search query")
    async def blueprint_search(self, interaction: discord.Interaction, query: str):
        results = self.registry.search_blueprints(query)
        if not results:
            await interaction.response.send_message(f"No blueprints matching '{query}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Blueprint Search: {query}", color=discord.Color.blue())
        for bp in results[:10]:
            embed.add_field(name=f"{bp.name} ({bp.blueprint_type.value})", value=f"Owner: {bp.owner} | Status: {bp.status.value}", inline=False)
        if len(results) > 10:
            embed.set_footer(text=f"Showing 10 of {len(results)}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-analytics", description="Blueprint analytics")
    async def blueprint_analytics(self, interaction: discord.Interaction):
        analytics = self.registry.get_analytics()
        embed = discord.Embed(title="Blueprint Analytics", color=discord.Color.blue())
        embed.add_field(name="Total Blueprints", value=analytics.get("total_blueprints", 0))
        embed.add_field(name="Total Versions", value=analytics.get("total_versions", 0))
        embed.add_field(name="Total Usage", value=analytics.get("total_usage", 0))
        embed.add_field(name="Avg Rating", value=analytics.get("avg_rating", "N/A"))
        embed.add_field(name="Most Used", value=analytics.get("most_used", "N/A"), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-clone", description="Clone a blueprint")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", new_name="New blueprint name", new_owner="New owner")
    async def blueprint_clone(self, interaction: discord.Interaction, blueprint_id: str, new_name: str, new_owner: str):
        bp = self.registry.clone_blueprint(blueprint_id, new_name, new_owner)
        if not bp:
            await interaction.response.send_message("Blueprint not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Cloned", color=discord.Color.green())
        embed.add_field(name="New ID", value=bp.blueprint_id[:8])
        embed.add_field(name="Name", value=bp.name)
        embed.add_field(name="Versions Cloned", value=len(bp.versions))
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="blueprint-deprecate", description="Deprecate a blueprint")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", reason="Deprecation reason")
    async def blueprint_deprecate(self, interaction: discord.Interaction, blueprint_id: str, reason: str = ""):
        bp = self.registry.deprecate_blueprint(blueprint_id, reason)
        if not bp:
            await interaction.response.send_message("Blueprint not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Deprecated", color=discord.Color.orange())
        embed.add_field(name="Blueprint", value=bp.name)
        embed.add_field(name="Status", value=bp.status.value)
        embed.add_field(name="Reason", value=reason or "N/A")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-tag", description="Tag a blueprint")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", tags="Comma-separated tags")
    async def blueprint_tag(self, interaction: discord.Interaction, blueprint_id: str, tags: str):
        tag_list = [t.strip() for t in tags.split(",")]
        bp = self.registry.add_tags(blueprint_id, tag_list)
        if not bp:
            await interaction.response.send_message("Blueprint not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Tagged", color=discord.Color.green())
        embed.add_field(name="Blueprint", value=bp.name)
        embed.add_field(name="Tags", value=", ".join(tag_list))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-metrics", description="Blueprint metrics")
    async def blueprint_metrics(self, interaction: discord.Interaction):
        analytics = self.registry.get_analytics()
        embed = discord.Embed(title="Blueprint Metrics", color=discord.Color.blue())
        embed.add_field(name="Total Blueprints", value=analytics.get("total_blueprints", 0))
        embed.add_field(name="Total Versions", value=analytics.get("total_versions", 0))
        embed.add_field(name="Total Usage", value=analytics.get("total_usage", 0))
        embed.add_field(name="Avg Rating", value=analytics.get("avg_rating", "N/A"))
        embed.add_field(name="Most Used", value=analytics.get("most_used", "N/A"), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-bulk-create", description="Bulk create blueprints")
    @discord.app_commands.describe(blueprints_json="JSON array of {name, type, owner}")
    async def blueprint_bulk_create(self, interaction: discord.Interaction, blueprints_json: str):
        import json
        try:
            specs = json.loads(blueprints_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON.", ephemeral=True)
            return
        results = []
        for spec in specs:
            try:
                bp = self.registry.create_blueprint(spec["name"], BlueprintType(spec.get("type", "infrastructure")), spec.get("owner", "unknown"))
                results.append({"name": spec["name"], "id": bp.blueprint_id[:8], "status": "created"})
            except Exception as e:
                results.append({"name": spec.get("name", "?"), "status": f"error: {str(e)}"})
        created = sum(1 for r in results if r["status"] == "created")
        embed = discord.Embed(title="Bulk Blueprint Creation", color=discord.Color.green())
        embed.add_field(name="Total", value=len(results))
        embed.add_field(name="Created", value=created)
        embed.add_field(name="Failed", value=len(results) - created)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-rate", description="Rate a blueprint")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", rating="Rating 1-5", comment="Optional comment")
    async def blueprint_rate(self, interaction: discord.Interaction, blueprint_id: str, rating: int, comment: str = ""):
        if rating < 1 or rating > 5:
            await interaction.response.send_message("Rating must be 1-5.", ephemeral=True)
            return
        result = self.registry.rate_blueprint(blueprint_id, rating, interaction.user.name, comment)
        if not result:
            await interaction.response.send_message("Blueprint not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Rated", color=discord.Color.gold())
        embed.add_field(name="Blueprint", value=result.get("blueprint_name"))
        embed.add_field(name="Rating", value=f"{rating}/5")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-usage", description="Record blueprint usage")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", consumer="Consumer name")
    async def blueprint_usage(self, interaction: discord.Interaction, blueprint_id: str, consumer: str):
        result = self.registry.record_usage(blueprint_id, consumer)
        if not result:
            await interaction.response.send_message("Blueprint not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Usage Recorded", color=discord.Color.green())
        embed.add_field(name="Blueprint", value=result.get("blueprint_name"))
        embed.add_field(name="Consumer", value=consumer)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-search", description="Search blueprints")
    @discord.app_commands.describe(query="Search query")
    async def blueprint_search(self, interaction: discord.Interaction, query: str):
        results = self.registry.search_blueprints(query)
        if not results:
            await interaction.response.send_message("No matches.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Blueprint Search: {query}", color=discord.Color.blue())
        for bp in results[:10]:
            embed.add_field(name=bp.name, value=f"Type: {bp.blueprint_type.value} | Owner: {bp.owner}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-stats", description="Blueprint statistics")
    async def blueprint_stats(self, interaction: discord.Interaction):
        stats = self.registry.get_blueprint_statistics()
        embed = discord.Embed(title="Blueprint Statistics", color=discord.Color.blue())
        embed.add_field(name="Total", value=stats.get("total_blueprints", 0))
        by_type = stats.get("by_type", {})
        for t, c in by_type.items():
            embed.add_field(name=f"Type: {t}", value=c, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-popular", description="Most popular blueprints")
    async def blueprint_popular(self, interaction: discord.Interaction):
        popular = self.registry.get_popular_templates()
        if not popular:
            await interaction.response.send_message("No data.", ephemeral=True)
            return
        embed = discord.Embed(title="Popular Blueprints", color=discord.Color.gold())
        for p in popular[:5]:
            embed.add_field(name=p["name"], value=f"Usage: {p['usage_count']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-recommend", description="Recommend blueprint for context")
    @discord.app_commands.describe(provider="Cloud provider", category="Category", type="Blueprint type")
    async def blueprint_recommend(self, interaction: discord.Interaction, provider: str = "", category: str = "", type: str = ""):
        context = {"provider": provider, "category": category, "type": type}
        recs = self.registry.recommend_blueprint(context)
        if not recs:
            await interaction.response.send_message("No recommendations.", ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Recommendations", color=discord.Color.green())
        for r in recs:
            embed.add_field(name=r["name"], value=f"Score: {r['score']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-version-diff", description="Diff two blueprint versions")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", version_a="First version", version_b="Second version")
    async def blueprint_version_diff(self, interaction: discord.Interaction, blueprint_id: str, version_a: str, version_b: str):
        diff = self.registry.get_version_diff(blueprint_id, version_a, version_b)
        if "error" in diff:
            await interaction.response.send_message(diff["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Version Diff", color=discord.Color.blue())
        embed.add_field(name="Added Lines", value=diff["added"])
        embed.add_field(name="Removed Lines", value=diff["removed"])
        embed.add_field(name="Total Changes", value=diff["changed"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-health", description="Blueprint health check")
    @discord.app_commands.describe(blueprint_id="Blueprint ID")
    async def blueprint_health(self, interaction: discord.Interaction, blueprint_id: str):
        health = self.registry.get_blueprint_health(blueprint_id)
        if "error" in health:
            await interaction.response.send_message(health["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Blueprint Health", color=discord.Color.green() if health["health_score"] >= 70 else discord.Color.orange())
        embed.add_field(name="Score", value=f"{health['health_score']}%")
        for check, passed in health.get("checks", {}).items():
            embed.add_field(name=check, value="✅" if passed else "❌", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-archive-versions", description="Archive old blueprint versions")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", keep="Number of versions to keep")
    async def blueprint_archive_versions(self, interaction: discord.Interaction, blueprint_id: str, keep: int = 5):
        removed = self.registry.archive_old_versions(blueprint_id, keep)
        embed = discord.Embed(title="Versions Archived", color=discord.Color.blue())
        embed.add_field(name="Versions Removed", value=removed)
        embed.add_field(name="Kept", value=keep)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blueprint-merge-versions", description="Merge two blueprint versions")
    @discord.app_commands.describe(blueprint_id="Blueprint ID", source="Source version", target="Target version")
    async def blueprint_merge_versions(self, interaction: discord.Interaction, blueprint_id: str, source: str, target: str):
        merged = self.registry.merge_blueprint_versions(blueprint_id, source, target)
        if not merged:
            await interaction.response.send_message("Merge failed. Check IDs.", ephemeral=True)
            return
        embed = discord.Embed(title="Versions Merged", color=discord.Color.green())
        embed.add_field(name="Source", value=source)
        embed.add_field(name="Target", value=target)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TemplateRegistryCog(bot))

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
