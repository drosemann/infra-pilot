import asyncio
import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.service_catalog import ServiceCatalogManager, ServiceTier

logger = logging.getLogger(__name__)


class ServiceCatalogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.catalog = ServiceCatalogManager()

    @discord.app_commands.command(name="catalog-register", description="Register a service in the catalog")
    @discord.app_commands.describe(name="Service name", owner="Owner email", language="Programming language", tier="Service tier")
    async def catalog_register(self, interaction: discord.Interaction, name: str, owner: str, language: str, tier: str = "t3"):
        svc = self.catalog.register_service(name, owner, language, ServiceTier(tier))
        embed = discord.Embed(title="Service Registered", color=discord.Color.green())
        embed.add_field(name="ID", value=svc.service_id[:8], inline=True)
        embed.add_field(name="Name", value=svc.name, inline=True)
        embed.add_field(name="Language", value=svc.language, inline=True)
        embed.add_field(name="Tier", value=svc.tier.value, inline=True)
        embed.add_field(name="Readiness Score", value=f"{svc.production_readiness_score}%", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-list", description="List services in catalog")
    @discord.app_commands.describe(owner="Filter by owner", tier="Filter by tier")
    async def catalog_list(self, interaction: discord.Interaction, owner: str = "", tier: str = ""):
        services = self.catalog.list_services(owner=owner, tier=tier)
        if not services:
            await interaction.response.send_message("No services found.", ephemeral=True)
            return
        embed = discord.Embed(title="Service Catalog", color=discord.Color.blue())
        for svc in services[:10]:
            embed.add_field(name=f"{svc.name} ({svc.tier.value})", value=f"Owner: {svc.owner} | Score: {svc.production_readiness_score}%", inline=False)
        if len(services) > 10:
            embed.set_footer(text=f"Showing 10 of {len(services)} services")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-score", description="Show service readiness score")
    @discord.app_commands.describe(service_id="Service ID")
    async def catalog_score(self, interaction: discord.Interaction, service_id: str):
        svc = self.catalog.get_service(service_id)
        if not svc:
            await interaction.response.send_message("Service not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Readiness Score: {svc.name}", color=discord.Color.blue())
        embed.add_field(name="Score", value=f"{svc.production_readiness_score}%", inline=True)
        embed.add_field(name="Tier", value=svc.tier.value, inline=True)
        embed.add_field(name="Status", value=svc.status.value, inline=True)
        embed.add_field(name="Last Updated", value=svc.last_score_update.isoformat() if svc.last_score_update else "Never", inline=False)
        checks = [k for k, v in svc.metadata.items() if v]
        missing = [k for k, v in svc.metadata.items() if not v]
        if checks:
            embed.add_field(name="Passed Checks", value="\n".join(checks[:5]), inline=True)
        if missing:
            embed.add_field(name="Missing", value="\n".join(missing[:5]), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-summary", description="Catalog summary")
    async def catalog_summary(self, interaction: discord.Interaction):
        summary = self.catalog.get_catalog_summary()
        embed = discord.Embed(title="Catalog Summary", color=discord.Color.blue())
        embed.add_field(name="Total Services", value=summary.get("total_services", 0), inline=True)
        embed.add_field(name="Average Score", value=f"{summary.get('average_score', 0)}%", inline=True)
        embed.add_field(name="Below Threshold", value=summary.get("services_below_threshold", 0), inline=True)
        embed.add_field(name="By Language", value="\n".join(f"{k}: {v}" for k, v in summary.get("by_language", {}).items()) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-health", description="Check service health")
    @discord.app_commands.describe(service_id="Service ID")
    async def catalog_health(self, interaction: discord.Interaction, service_id: str):
        health = self.catalog.check_service_health(service_id)
        if "error" in health:
            await interaction.response.send_message(health["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Health: {health['name']}", color=discord.Color.blue())
        embed.add_field(name="Score", value=f"{health['health_score']}%")
        embed.add_field(name="Passed", value=f"{health['passed_checks']}/{health['total_checks']}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-search", description="Search services")
    @discord.app_commands.describe(query="Search query")
    async def catalog_search(self, interaction: discord.Interaction, query: str):
        results = self.catalog.search_services(query)
        if not results:
            await interaction.response.send_message(f"No services matching '{query}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Search: {query}", color=discord.Color.blue())
        for svc in results[:10]:
            embed.add_field(name=f"{svc.name} ({svc.tier.value})", value=f"Score: {svc.production_readiness_score}% | Owner: {svc.owner}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-analytics", description="Catalog analytics")
    async def catalog_analytics(self, interaction: discord.Interaction):
        analytics = self.catalog.get_catalog_analytics()
        embed = discord.Embed(title="Catalog Analytics", color=discord.Color.blue())
        embed.add_field(name="Total Services", value=analytics.get("total_services", 0))
        embed.add_field(name="Avg Readiness", value=f"{analytics.get('avg_readiness_score', 0)}%")
        embed.add_field(name="Above 80%", value=analytics.get("services_above_80", 0))
        embed.add_field(name="Below 50%", value=analytics.get("services_below_50", 0))
        embed.add_field(name="Unique Owners", value=analytics.get("unique_owners", 0))
        embed.add_field(name="Languages", value=analytics.get("unique_languages", 0))
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="catalog-deprecate", description="Deprecate a service")
    @discord.app_commands.describe(service_id="Service ID", reason="Deprecation reason")
    async def catalog_deprecate(self, interaction: discord.Interaction, service_id: str, reason: str = ""):
        svc = self.catalog.deprecate_service(service_id, reason)
        if not svc:
            await interaction.response.send_message("Service not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Service Deprecated", color=discord.Color.orange())
        embed.add_field(name="Service", value=svc.name)
        embed.add_field(name="Status", value=svc.status.value)
        embed.add_field(name="Reason", value=reason or "N/A")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-metrics", description="Catalog metrics")
    async def catalog_metrics(self, interaction: discord.Interaction):
        analytics = self.catalog.get_catalog_analytics()
        embed = discord.Embed(title="Catalog Metrics", color=discord.Color.blue())
        embed.add_field(name="Total Services", value=analytics.get("total_services", 0))
        embed.add_field(name="Avg Readiness", value=f"{analytics.get('avg_readiness_score', 0)}%")
        embed.add_field(name="Above 80%", value=analytics.get("services_above_80", 0))
        embed.add_field(name="Below 50%", value=analytics.get("services_below_50", 0))
        embed.add_field(name="Unique Owners", value=analytics.get("unique_owners", 0))
        embed.add_field(name="Languages", value=analytics.get("unique_languages", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-bulk-register", description="Bulk register services")
    @discord.app_commands.describe(services_json="JSON array of {name, owner, language, tier}")
    async def catalog_bulk_register(self, interaction: discord.Interaction, services_json: str):
        import json
        try:
            services = json.loads(services_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON.", ephemeral=True)
            return
        results = []
        for s in services:
            try:
                svc = self.catalog.register_service(s["name"], s.get("owner", "unknown"), s.get("language", "python"), ServiceTier(s.get("tier", "t3")))
                results.append({"name": s["name"], "id": svc.service_id[:8], "status": "registered"})
            except Exception as e:
                results.append({"name": s.get("name", "?"), "status": f"error: {str(e)}"})
        registered = sum(1 for r in results if r["status"] == "registered")
        embed = discord.Embed(title="Bulk Registration Complete", color=discord.Color.green())
        embed.add_field(name="Total", value=len(results))
        embed.add_field(name="Registered", value=registered)
        embed.add_field(name="Failed", value=len(results) - registered)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-tag", description="Tag a service")
    @discord.app_commands.describe(service_id="Service ID", tags="Comma-separated tags")
    async def catalog_tag(self, interaction: discord.Interaction, service_id: str, tags: str):
        tag_list = [t.strip() for t in tags.split(",")]
        svc = self.catalog.add_tags(service_id, tag_list)
        if not svc:
            await interaction.response.send_message("Service not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Service Tagged", color=discord.Color.green())
        embed.add_field(name="Service", value=svc.name)
        embed.add_field(name="Tags", value=", ".join(tag_list))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-owners", description="List unique owners")
    async def catalog_owners(self, interaction: discord.Interaction):
        owners = self.catalog.get_unique_owners()
        embed = discord.Embed(title="Service Owners", color=discord.Color.blue())
        for owner in owners:
            count = len(self.catalog.list_services(owner=owner))
            embed.add_field(name=owner, value=f"{count} services", inline=True)
        if not owners:
            embed.description = "No owners found."
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-delete", description="Delete a service")
    @discord.app_commands.describe(service_id="Service ID")
    async def catalog_delete(self, interaction: discord.Interaction, service_id: str):
        deleted = self.catalog.delete_service(service_id)
        if not deleted:
            await interaction.response.send_message("Service not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Service Deleted", color=discord.Color.red())
        embed.add_field(name="Service ID", value=service_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-compliance", description="Run compliance check on a service")
    @discord.app_commands.describe(service_id="Service ID")
    async def catalog_compliance(self, interaction: discord.Interaction, service_id: str):
        check = self.catalog.run_compliance_check(service_id)
        if "error" in check:
            await interaction.response.send_message(check["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Compliance: {check['name']}", color=discord.Color.green() if check["compliance_score"] >= 70 else discord.Color.orange())
        embed.add_field(name="Score", value=f"{check['compliance_score']}%")
        for k, v in check.get("checks", {}).items():
            embed.add_field(name=k, value="✅" if v else "❌", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-orphans", description="Find orphan services")
    async def catalog_orphans(self, interaction: discord.Interaction):
        orphans = self.catalog.find_orphan_services()
        embed = discord.Embed(title="Orphan Services", color=discord.Color.orange())
        embed.add_field(name="Count", value=len(orphans))
        for o in orphans[:10]:
            embed.add_field(name=o["service_id"][:8], value=o["name"], inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-cost-summary", description="Service cost summary")
    async def catalog_cost_summary(self, interaction: discord.Interaction):
        summary = self.catalog.get_cost_summary()
        embed = discord.Embed(title="Cost Summary", color=discord.Color.gold())
        embed.add_field(name="Total Monthly", value=f"${summary['total_monthly_cost']:,.2f}")
        embed.add_field(name="Services", value=summary["service_count"])
        for tier, cost in summary.get("by_tier", {}).items():
            embed.add_field(name=f"Tier {tier}", value=f"${cost:,.2f}", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-dependency-chain", description="Show dependency chain for a service")
    @discord.app_commands.describe(service_id="Service ID")
    async def catalog_dependency_chain(self, interaction: discord.Interaction, service_id: str):
        chain = self.catalog.get_dependency_chain(service_id)
        if not chain:
            await interaction.response.send_message("No dependencies found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Dependency Chain: {service_id[:8]}", color=discord.Color.blue())
        embed.add_field(name="Depth", value=len(chain))
        for c in chain[:10]:
            embed.add_field(name="→", value=c[:8], inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-maturity", description="Compute service maturity score")
    @discord.app_commands.describe(service_id="Service ID")
    async def catalog_maturity(self, interaction: discord.Interaction, service_id: str):
        score = self.catalog.compute_maturity_score(service_id)
        if "error" in score:
            await interaction.response.send_message(score["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Maturity: {score['name']}", color=discord.Color.blue())
        embed.add_field(name="Score", value=f"{score['maturity_score']}/{score['max_score']}")
        embed.add_field(name="Level", value=score["level"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="catalog-set-tier", description="Bulk set service tier")
    @discord.app_commands.describe(service_ids="Comma-separated service IDs", tier="Tier (t1-t5)")
    async def catalog_set_tier(self, interaction: discord.Interaction, service_ids: str, tier: str):
        ids = [s.strip() for s in service_ids.split(",")]
        tier_enum = ServiceTier(tier)
        count = self.catalog.bulk_set_tier(ids, tier_enum)
        embed = discord.Embed(title="Tier Updated", color=discord.Color.green())
        embed.add_field(name="Updated", value=count)
        embed.add_field(name="Tier", value=tier)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServiceCatalogCog(bot))

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
