import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.developer_portal import DeveloperPortalManager

logger = logging.getLogger(__name__)


class DevPortalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.portal = DeveloperPortalManager()

    @discord.app_commands.command(name="portal-summary", description="Developer portal summary")
    async def portal_summary(self, interaction: discord.Interaction):
        summary = self.portal.get_catalog_summary()
        embed = discord.Embed(title="Developer Portal Summary", color=discord.Color.blue())
        embed.add_field(name="Total Components", value=summary["total_components"], inline=True)
        embed.add_field(name="Total Systems", value=summary["total_systems"], inline=True)
        embed.add_field(name="Average Health", value=f"{summary['average_health']}%", inline=True)
        embed.add_field(name="By Type", value="\n".join(f"{k}: {v}" for k, v in summary["by_type"].items()) or "None", inline=False)
        embed.add_field(name="By Owner", value="\n".join(f"{k}: {v}" for k, v in summary["by_owner"].items()) or "None", inline=False)
        embed.timestamp = datetime.utcnow()
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-register", description="Register a software component")
    @discord.app_commands.describe(name="Component name", component_type="Type (service, library, api)", owner="Owner email/team")
    async def portal_register(self, interaction: discord.Interaction, name: str, component_type: str, owner: str):
        comp = self.portal.register_component(name, component_type, owner)
        embed = discord.Embed(title="Component Registered", color=discord.Color.green())
        embed.add_field(name="ID", value=comp.component_id[:8], inline=True)
        embed.add_field(name="Name", value=comp.name, inline=True)
        embed.add_field(name="Type", value=comp.component_type, inline=True)
        embed.add_field(name="Owner", value=comp.owner, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-deps", description="Show component dependencies")
    @discord.app_commands.describe(component_id="Component ID")
    async def portal_deps(self, interaction: discord.Interaction, component_id: str):
        graph = self.portal.get_dependency_graph()
        nodes = graph.get("nodes", {})
        comp = nodes.get(component_id)
        if not comp:
            await interaction.response.send_message("Component not found.", ephemeral=True)
            return
        deps = comp.get("dependencies", [])
        dep_names = [nodes.get(d, {}).get("name", d) for d in deps]
        embed = discord.Embed(title=f"Dependencies: {comp['name']}", color=discord.Color.blue())
        embed.add_field(name="Depends On", value="\n".join(dep_names) or "None", inline=True)
        depended = comp.get("depended_by", [])
        depby_names = [nodes.get(d, {}).get("name", d) for d in depended]
        embed.add_field(name="Depended By", value="\n".join(depby_names) or "None", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-impact", description="Impact analysis for a component")
    @discord.app_commands.describe(component_id="Component ID")
    async def portal_impact(self, interaction: discord.Interaction, component_id: str):
        affected = self.portal.get_impact_analysis(component_id)
        nodes = self.portal.get_dependency_graph().get("nodes", {})
        names = [nodes.get(a, {}).get("name", a) for a in affected]
        embed = discord.Embed(title="Impact Analysis", color=discord.Color.orange())
        embed.add_field(name="Component ID", value=component_id, inline=False)
        embed.add_field(name="Affected Components", value="\n".join(names) or "None (leaf node)", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-maturity", description="Calculate maturity level")
    @discord.app_commands.describe(component_id="Component ID")
    async def portal_maturity(self, interaction: discord.Interaction, component_id: str):
        maturity = self.portal.calculate_maturity(component_id)
        if "error" in maturity:
            await interaction.response.send_message(maturity["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Maturity Assessment", color=discord.Color.gold())
        embed.add_field(name="Level", value=f"{maturity['level']} - {maturity['level_name']}", inline=True)
        embed.add_field(name="Score", value=f"{maturity['score']}/100", inline=True)
        if maturity.get("next_level"):
            embed.add_field(name="Next Level", value=f"{maturity['next_level']['name']} ({maturity['next_level']['score']})", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-search", description="Search components")
    @discord.app_commands.describe(query="Search query")
    async def portal_search(self, interaction: discord.Interaction, query: str):
        results = self.portal.search_components(query)
        if not results:
            await interaction.response.send_message(f"No components matching '{query}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Search: {query}", color=discord.Color.blue())
        for comp in results[:10]:
            embed.add_field(name=comp.name, value=f"Type: {comp.component_type} | Owner: {comp.owner} | Health: {comp.health_score}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-health", description="Health check all components")
    async def portal_health(self, interaction: discord.Interaction):
        checks = self.portal.health_check_all()
        passed = sum(1 for c in checks if c["health_score"] >= 80)
        total = len(checks)
        embed = discord.Embed(title="Component Health Overview", color=discord.Color.blue())
        embed.add_field(name="Total Components", value=total)
        embed.add_field(name="Healthy (80%+)", value=passed)
        embed.add_field(name="Needs Attention", value=total - passed)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-system-create", description="Create a system")
    @discord.app_commands.describe(name="System name", description="Description", domain="Domain")
    async def portal_system_create(self, interaction: discord.Interaction, name: str, description: str, domain: str):
        system = self.portal.create_system(name, description, domain)
        embed = discord.Embed(title="System Created", color=discord.Color.green())
        embed.add_field(name="ID", value=system["system_id"][:8])
        embed.add_field(name="Name", value=system["name"])
        embed.add_field(name="Domain", value=system["domain"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-dependency-report", description="Dependency report")
    async def portal_dependency_report(self, interaction: discord.Interaction):
        report = self.portal.get_dependency_report()
        embed = discord.Embed(title="Dependency Report", color=discord.Color.blue())
        embed.add_field(name="Total Dependencies", value=report.get("total_dependencies", 0))
        embed.add_field(name="Circular Deps", value=len(report.get("circular_dependencies", [])))
        embed.add_field(name="Orphaned Components", value=len(report.get("orphaned_components", [])))
        await interaction.response.send_message(embed=embed)

    @portal_summary.error
    @portal_register.error
    async def cmd_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(f"Error: {str(error)}", ephemeral=True)


    @discord.app_commands.command(name="portal-lifecycle", description="Set component lifecycle")
    @discord.app_commands.describe(component_id="Component ID", lifecycle="Lifecycle stage")
    async def portal_lifecycle(self, interaction: discord.Interaction, component_id: str, lifecycle: str):
        result = self.portal.set_lifecycle(component_id, lifecycle)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Lifecycle Updated", color=discord.Color.green())
        embed.add_field(name="Component", value=component_id[:8])
        embed.add_field(name="Lifecycle", value=lifecycle)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-tag", description="Tag a component")
    @discord.app_commands.describe(component_id="Component ID", tags="Comma-separated tags")
    async def portal_tag(self, interaction: discord.Interaction, component_id: str, tags: str):
        tag_list = [t.strip() for t in tags.split(",")]
        result = self.portal.add_tags(component_id, tag_list)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Component Tagged", color=discord.Color.green())
        embed.add_field(name="Component", value=component_id[:8])
        embed.add_field(name="Tags", value=", ".join(tag_list))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-system-components", description="List system components")
    @discord.app_commands.describe(system_id="System ID")
    async def portal_system_components(self, interaction: discord.Interaction, system_id: str):
        components = self.portal.get_system_components(system_id)
        if not components:
            await interaction.response.send_message("No components found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"System Components", color=discord.Color.blue())
        for comp in components[:10]:
            embed.add_field(name=comp.name, value=f"Type: {comp.component_type} | Health: {comp.health_score}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-ownership-report", description="Ownership report")
    async def portal_ownership_report(self, interaction: discord.Interaction):
        report = self.portal.get_ownership_report()
        embed = discord.Embed(title="Ownership Report", color=discord.Color.blue())
        embed.add_field(name="Total Components", value=report.get("total_components", 0))
        embed.add_field(name="Orphaned", value=report.get("orphaned_components", 0))
        embed.add_field(name="Unique Owners", value=report.get("unique_owners", 0))
        embed.add_field(name="By Owner", value="\n".join(f"{k}: {v}" for k, v in list(report.get("by_owner", {}).items())[:5]) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-scorecard", description="Component scorecard")
    @discord.app_commands.describe(component_id="Component ID")
    async def portal_scorecard(self, interaction: discord.Interaction, component_id: str):
        scorecard = self.portal.get_component_scorecard(component_id)
        if "error" in scorecard:
            await interaction.response.send_message(scorecard["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Scorecard: {scorecard['name']}", color=discord.Color.blue())
        embed.add_field(name="Health", value=f"{scorecard['health']}%")
        embed.add_field(name="Maturity", value=scorecard.get("maturity", "N/A"))
        embed.add_field(name="Dependencies", value=scorecard.get("dependency_count", 0))
        if scorecard.get("checks"):
            for k, v in scorecard["checks"].items():
                embed.add_field(name=k, value="✅" if v else "❌", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-audit", description="Portal change audit log")
    async def portal_audit(self, interaction: discord.Interaction):
        audit = self.portal.get_audit_log()
        embed = discord.Embed(title="Portal Audit Log", color=discord.Color.purple())
        for entry in audit[-5:]:
            embed.add_field(name=entry.get("action", "change"), value=f"Component: {entry.get('component_id', '?')[:8]} | By: {entry.get('actor', 'system')} | At: {entry.get('timestamp', '?')}", inline=False)
        if not audit:
            embed.description = "No audit entries."
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-dependency-viz", description="Dependency chain visualization")
    @discord.app_commands.describe(component_id="Component ID")
    async def portal_dependency_viz(self, interaction: discord.Interaction, component_id: str):
        viz = self.portal.get_dependency_chain_visualization(component_id)
        if "error" in viz:
            await interaction.response.send_message(viz["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Dependency Map: {component_id[:8]}", color=discord.Color.blue())
        embed.add_field(name="Nodes", value=len(viz["nodes"]))
        embed.add_field(name="Edges", value=len(viz["edges"]))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-scorecard", description="Portal-wide scorecard")
    @discord.app_commands.describe(system_id="System ID")
    async def portal_scorecard_view(self, interaction: discord.Interaction, system_id: str = ""):
        scorecard = self.portal.get_portal_scorecard(system_id)
        if "error" in scorecard:
            await interaction.response.send_message(scorecard["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Portal Scorecard", color=discord.Color.blue())
        embed.add_field(name="Components", value=scorecard["component_count"])
        embed.add_field(name="Avg Maturity", value=scorecard["avg_maturity_score"])
        health = scorecard.get("health_summary", {})
        embed.add_field(name="Healthy", value=health.get("healthy", 0))
        embed.add_field(name="Needs Attention", value=health.get("needs_attention", 0))
        embed.add_field(name="Critical", value=health.get("critical", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-search", description="Search portal components and systems")
    @discord.app_commands.describe(query="Search query")
    async def portal_search(self, interaction: discord.Interaction, query: str):
        results = self.portal.search_portal(query)
        embed = discord.Embed(title=f"Portal Search: {query}", color=discord.Color.blue())
        embed.add_field(name="Components", value=len(results.get("components", [])))
        embed.add_field(name="Systems", value=len(results.get("systems", [])))
        embed.add_field(name="Total Matches", value=results.get("total_matches", 0))
        for c in results.get("components", [])[:5]:
            embed.add_field(name=c.get("name", "?"), value=f"Owner: {c.get('owner', 'N/A')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-bulk-update-owner", description="Bulk update component owners")
    @discord.app_commands.describe(component_ids="Comma-separated component IDs", new_owner="New owner name")
    async def portal_bulk_update_owner(self, interaction: discord.Interaction, component_ids: str, new_owner: str):
        ids = [c.strip() for c in component_ids.split(",")]
        count = self.portal.bulk_update_component_owner(ids, new_owner)
        embed = discord.Embed(title="Owners Updated", color=discord.Color.green())
        embed.add_field(name="Updated", value=count)
        embed.add_field(name="New Owner", value=new_owner)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-system-maturity", description="Calculate system maturity")
    @discord.app_commands.describe(system_id="System ID")
    async def portal_system_maturity(self, interaction: discord.Interaction, system_id: str):
        maturity = self.portal.calculate_system_maturity(system_id)
        if "error" in maturity:
            await interaction.response.send_message(maturity["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"System Maturity: {maturity['system_name']}", color=discord.Color.blue())
        embed.add_field(name="Score", value=maturity["score"])
        embed.add_field(name="Level", value=maturity["level"])
        embed.add_field(name="Components", value=maturity["component_count"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-system-dep-map", description="System dependency map")
    @discord.app_commands.describe(system_id="System ID")
    async def portal_system_dep_map(self, interaction: discord.Interaction, system_id: str):
        dep_map = self.portal.get_system_dependency_map(system_id)
        if "error" in dep_map:
            await interaction.response.send_message(dep_map["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"System Dep Map: {dep_map['system_name']}", color=discord.Color.blue())
        embed.add_field(name="Nodes", value=len(dep_map["nodes"]))
        embed.add_field(name="Edges", value=len(dep_map["edges"]))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="portal-health-trend", description="Component health trend")
    @discord.app_commands.describe(component_id="Component ID")
    async def portal_health_trend(self, interaction: discord.Interaction, component_id: str):
        trend = self.portal.get_health_trend(component_id)
        if not trend:
            await interaction.response.send_message("Component not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Health Trend", color=discord.Color.blue())
        for t in trend[-5:]:
            embed.add_field(name=t["date"][:10], value=f"Score: {t['health_score']}%", inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DevPortalCog(bot))

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
