import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.tech_debt_tracker import TechDebtTracker, DebtCategory, DebtSeverity

logger = logging.getLogger(__name__)


class TechDebtCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracker = TechDebtTracker()

    @discord.app_commands.command(name="debt-detect", description="Detect a tech debt item")
    @discord.app_commands.describe(service_id="Service ID", category="Debt category", severity="Severity", title="Title")
    async def debt_detect(self, interaction: discord.Interaction, service_id: str, category: str, severity: str, title: str):
        item = self.tracker.detect_debt(service_id, DebtCategory(category), DebtSeverity(severity), title)
        embed = discord.Embed(title="Tech Debt Detected", color=discord.Color.red())
        embed.add_field(name="ID", value=item.item_id[:8])
        embed.add_field(name="Service", value=item.service_id[:8])
        embed.add_field(name="Severity", value=item.severity.value.upper())
        embed.add_field(name="Category", value=item.category.value)
        embed.add_field(name="Title", value=item.title, inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-list", description="List tech debt items")
    @discord.app_commands.describe(service_id="Filter by service", severity="Filter by severity", status="Filter by status")
    async def debt_list(self, interaction: discord.Interaction, service_id: str = "", severity: str = "", status: str = ""):
        items = self.tracker.list_items(service_id=service_id, severity=severity, status=status)
        if not items:
            await interaction.response.send_message("No debt items found.", ephemeral=True)
            return
        embed = discord.Embed(title="Tech Debt Items", color=discord.Color.orange())
        for item in items[:10]:
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}
            embed.add_field(name=f"{emoji.get(item.severity.value, '⚪')} {item.title[:50]}", value=f"Service: {item.service_id[:8]} | Sev: {item.severity.value} | Status: {item.status.value}", inline=False)
        if len(items) > 10:
            embed.set_footer(text=f"Showing 10 of {len(items)}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-scan", description="Run automated debt scan on a service")
    @discord.app_commands.describe(service_id="Service ID")
    async def debt_scan(self, interaction: discord.Interaction, service_id: str):
        items = self.tracker.run_automated_scan(service_id)
        embed = discord.Embed(title=f"Auto-Scan Complete: {service_id[:8]}", color=discord.Color.green())
        embed.add_field(name="Items Found", value=len(items))
        by_severity = {}
        for item in items:
            by_severity[item.severity.value] = by_severity.get(item.severity.value, 0) + 1
        embed.add_field(name="By Severity", value="\n".join(f"{k}: {v}" for k, v in by_severity.items()), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-summary", description="Tech debt summary")
    async def debt_summary(self, interaction: discord.Interaction):
        summary = self.tracker.get_organization_summary()
        embed = discord.Embed(title="Tech Debt Summary", color=discord.Color.blue())
        embed.add_field(name="Total Items", value=summary.get("total_items", 0))
        embed.add_field(name="Open Items", value=summary.get("open_items", 0))
        embed.add_field(name="Debt Score", value=summary.get("debt_score", 0))
        embed.add_field(name="Critical", value=summary.get("critical_count", 0))
        embed.add_field(name="High", value=summary.get("high_count", 0))
        embed.add_field(name="Services Affected", value=summary.get("unique_services", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-sla", description="Tech debt SLA report")
    async def debt_sla(self, interaction: discord.Interaction):
        report = self.tracker.get_sla_report()
        embed = discord.Embed(title="Tech Debt SLA Report", color=discord.Color.red())
        embed.add_field(name="Total Overdue", value=report.get("total_overdue", 0))
        embed.add_field(name="Avg Resolution Time", value=f"{report.get('avg_resolution_time_hours', 0)}h")
        overdue = report.get("overdue_items", [])
        if overdue:
            embed.add_field(name="Most Overdue", value=f"{overdue[0].get('title', 'N/A')} ({overdue[0].get('days_overdue', 0)} days)", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-assign", description="Assign tech debt items")
    @discord.app_commands.describe(item_ids="Comma-separated item IDs", assignee="Assignee email")
    async def debt_assign(self, interaction: discord.Interaction, item_ids: str, assignee: str):
        ids = [i.strip() for i in item_ids.split(",")]
        count = self.tracker.assign_items_bulk(ids, assignee)
        embed = discord.Embed(title="Items Assigned", color=discord.Color.green())
        embed.add_field(name="Assigned", value=f"{count} items to {assignee}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-export", description="Export debt report")
    async def debt_export(self, interaction: discord.Interaction, service_id: str = ""):
        report = self.tracker.export_debt_report(service_id)
        embed = discord.Embed(title="Debt Report Exported", color=discord.Color.blue())
        embed.add_field(name="Total Items", value=report.get("total_items", 0))
        embed.add_field(name="Generated At", value=report.get("generated_at", ""))
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="debt-trend", description="Tech debt trend analysis")
    @discord.app_commands.describe(service_id="Service ID", periods="Number of periods")
    async def debt_trend(self, interaction: discord.Interaction, service_id: str = "", periods: int = 6):
        trend = self.tracker.get_debt_trend(service_id=service_id, periods=periods)
        if not trend:
            await interaction.response.send_message("No trend data available.", ephemeral=True)
            return
        embed = discord.Embed(title="Tech Debt Trend", color=discord.Color.blue())
        for entry in trend[-periods:]:
            embed.add_field(name=entry.get("period", "?"), value=f"Items: {entry.get('total', 0)} | Score: {entry.get('score', 0)}", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-add-comment", description="Add comment to debt item")
    @discord.app_commands.describe(item_id="Item ID", comment="Comment text")
    async def debt_add_comment(self, interaction: discord.Interaction, item_id: str, comment: str):
        item = self.tracker.add_comment(item_id, comment, interaction.user.name)
        if not item:
            await interaction.response.send_message("Item not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Comment Added", color=discord.Color.green())
        embed.add_field(name="Item", value=item_id[:8])
        embed.add_field(name="Comment", value=comment[:100])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-priority-matrix", description="Priority matrix")
    async def debt_priority_matrix(self, interaction: discord.Interaction):
        matrix = self.tracker.get_priority_matrix()
        embed = discord.Embed(title="Debt Priority Matrix", color=discord.Color.blue())
        for k, v in matrix.items():
            embed.add_field(name=k.capitalize(), value=f"Count: {v.get('count', 0)} | Effort: {v.get('effort', 'N/A')}", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-resolve", description="Mark item as resolved")
    @discord.app_commands.describe(item_id="Item ID", resolution_notes="Resolution notes")
    async def debt_resolve(self, interaction: discord.Interaction, item_id: str, resolution_notes: str = ""):
        item = self.tracker.resolve_item(item_id, resolution_notes)
        if not item:
            await interaction.response.send_message("Item not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Debt Resolved", color=discord.Color.green())
        embed.add_field(name="Item", value=item_id[:8])
        embed.add_field(name="Status", value=item.status.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-by-service", description="Debt items grouped by service")
    async def debt_by_service(self, interaction: discord.Interaction):
        grouped = self.tracker.get_items_by_service()
        embed = discord.Embed(title="Debt by Service", color=discord.Color.orange())
        for svc_id, items in list(grouped.items())[:10]:
            critical = sum(1 for i in items if i.severity.value == "critical")
            embed.add_field(name=svc_id[:8], value=f"Total: {len(items)} | Critical: {critical}", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-recalculate", description="Recalculate debt scores")
    async def debt_recalculate(self, interaction: discord.Interaction):
        result = self.tracker.recalculate_scores()
        embed = discord.Embed(title="Scores Recalculated", color=discord.Color.green())
        embed.add_field(name="Total Score", value=result.get("total_score", 0))
        embed.add_field(name="Items Scored", value=result.get("items_scored", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-trend", description="Debt trend analysis")
    @discord.app_commands.describe(days="Number of days to analyze")
    async def debt_trend(self, interaction: discord.Interaction, days: int = 90):
        trend = self.tracker.get_trend_analysis(days)
        embed = discord.Embed(title=f"Debt Trend ({days} days)", color=discord.Color.blue())
        embed.add_field(name="Created", value=trend["created"])
        embed.add_field(name="Resolved", value=trend["resolved"])
        embed.add_field(name="Net Change", value=trend["net_change"])
        embed.add_field(name="By Month", value="\n".join(f"{k}: {v}" for k, v in list(trend.get("by_month", {}).items())[:6]) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-scan-schedule", description="Schedule a debt scan")
    @discord.app_commands.describe(service_id="Service ID", scan_type="Scan type", interval_hours="Hours between scans")
    async def debt_scan_schedule(self, interaction: discord.Interaction, service_id: str, scan_type: str = "full", interval_hours: int = 24):
        scan = self.tracker.schedule_scan(service_id, scan_type, interval_hours)
        embed = discord.Embed(title="Scan Scheduled", color=discord.Color.green())
        embed.add_field(name="Scan ID", value=scan["scan_id"][:8])
        embed.add_field(name="Next Run", value=scan["next_run"])
        embed.add_field(name="Interval", value=f"{interval_hours}h")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-scans-list", description="List scheduled scans")
    async def debt_scans_list(self, interaction: discord.Interaction):
        scans = self.tracker.get_scheduled_scans()
        if not scans:
            await interaction.response.send_message("No scans scheduled.", ephemeral=True)
            return
        embed = discord.Embed(title="Scheduled Scans", color=discord.Color.blue())
        for s in scans[:10]:
            embed.add_field(name=s["scan_id"][:8], value=f"Service: {s['service_id'][:8]} | Status: {s['status']} | Next: {s['next_run']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-scan-cancel", description="Cancel a scheduled scan")
    @discord.app_commands.describe(scan_id="Scan ID")
    async def debt_scan_cancel(self, interaction: discord.Interaction, scan_id: str):
        cancelled = self.tracker.cancel_scheduled_scan(scan_id)
        if not cancelled:
            await interaction.response.send_message("Scan not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Scan Cancelled", color=discord.Color.orange())
        embed.add_field(name="Scan ID", value=scan_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-report", description="Debt report for a service")
    @discord.app_commands.describe(service_id="Service ID")
    async def debt_report(self, interaction: discord.Interaction, service_id: str = ""):
        report = self.tracker.get_debt_report(service_id)
        embed = discord.Embed(title=f"Debt Report: {service_id or 'All'}", color=discord.Color.blue())
        embed.add_field(name="Total Items", value=report["total_items"])
        embed.add_field(name="Critical Open", value=report["critical_open"])
        embed.add_field(name="High Open", value=report["high_open"])
        embed.add_field(name="Aging Critical", value=report["aging_critical"])
        embed.add_field(name="Resolution Rate", value=f"{report['resolution_rate']}%")
        embed.add_field(name="Avg Effort", value=f"{report['avg_effort_hours']}h")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-rankings", description="Service debt rankings")
    async def debt_rankings(self, interaction: discord.Interaction):
        rankings = self.tracker.get_service_rankings()
        if not rankings:
            await interaction.response.send_message("No data.", ephemeral=True)
            return
        embed = discord.Embed(title="Service Debt Rankings", color=discord.Color.orange())
        for r in rankings[:5]:
            embed.add_field(name=r["service_id"][:8], value=f"Total: {r['total']} | Critical: {r['critical']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="debt-bulk-remediate", description="Bulk auto-remediate debt items")
    @discord.app_commands.describe(item_ids="Comma-separated item IDs")
    async def debt_bulk_remediate(self, interaction: discord.Interaction, item_ids: str):
        ids = [i.strip() for i in item_ids.split(",")]
        result = self.tracker.bulk_remediate_items(ids)
        embed = discord.Embed(title="Bulk Remediation", color=discord.Color.green())
        embed.add_field(name="Total", value=result["total"])
        embed.add_field(name="Succeeded", value=result["succeeded"])
        embed.add_field(name="Failed", value=result["failed"])
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TechDebtCog(bot))

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
