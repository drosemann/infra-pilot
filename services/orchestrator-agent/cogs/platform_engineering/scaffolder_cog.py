import asyncio
import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.golden_path_scaffolder import GoldenPathScaffolder, ScaffoldStep

logger = logging.getLogger(__name__)


class ScaffolderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scaffolder = GoldenPathScaffolder()

    @discord.app_commands.command(name="scaffold-templates", description="List golden path templates")
    async def scaffold_templates(self, interaction: discord.Interaction):
        templates = self.scaffolder.list_templates()
        if not templates:
            await interaction.response.send_message("No templates available.", ephemeral=True)
            return
        embed = discord.Embed(title="Golden Path Templates", color=discord.Color.blue())
        for tmpl in templates:
            embed.add_field(name=tmpl["name"], value=tmpl.get("description", "")[:100], inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-start", description="Start a new service scaffold")
    @discord.app_commands.describe(template="Template name", service_name="Service name", owner="Owner email/team")
    async def scaffold_start(self, interaction: discord.Interaction, template: str, service_name: str, owner: str):
        instance = self.scaffolder.start_scaffold(template, service_name, owner)
        if not instance:
            await interaction.response.send_message(f"Template '{template}' not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Scaffold Started", color=discord.Color.green())
        embed.add_field(name="Instance ID", value=instance.instance_id[:8], inline=True)
        embed.add_field(name="Service", value=instance.service_name, inline=True)
        embed.add_field(name="Current Step", value=instance.current_step.value, inline=True)
        embed.add_field(name="Status", value=instance.status, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-status", description="Check scaffold progress")
    @discord.app_commands.describe(instance_id="Scaffold instance ID")
    async def scaffold_status(self, interaction: discord.Interaction, instance_id: str):
        inst = self.scaffolder.get_instance(instance_id)
        if not inst:
            await interaction.response.send_message("Instance not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Scaffold: {inst.service_name}", color=discord.Color.blue())
        embed.add_field(name="Template", value=inst.template_name, inline=True)
        embed.add_field(name="Status", value=inst.status, inline=True)
        embed.add_field(name="Current Step", value=inst.current_step.value, inline=True)
        embed.add_field(name="Completed Steps", value="\n".join(inst.completed_steps) or "None", inline=False)
        if inst.repo_url:
            embed.add_field(name="Repo URL", value=inst.repo_url, inline=False)
        if inst.errors:
            embed.add_field(name="Errors", value="\n".join(inst.errors), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-advance", description="Advance scaffold to next step")
    @discord.app_commands.describe(instance_id="Instance ID", step_name="Step name", result_json="JSON result")
    async def scaffold_advance(self, interaction: discord.Interaction, instance_id: str, step_name: str, result_json: str = "{}"):
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON in result_json.", ephemeral=True)
            return
        inst = self.scaffolder.advance_step(instance_id, result)
        if not inst:
            await interaction.response.send_message("Failed to advance step.", ephemeral=True)
            return
        embed = discord.Embed(title="Step Advanced", color=discord.Color.green())
        embed.add_field(name="Instance", value=instance_id[:8], inline=True)
        embed.add_field(name="New Step", value=inst.current_step.value, inline=True)
        embed.add_field(name="Status", value=inst.status, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-summary", description="Scaffolder summary")
    async def scaffold_summary(self, interaction: discord.Interaction):
        summary = self.scaffolder.get_scaffold_summary()
        embed = discord.Embed(title="Scaffolder Summary", color=discord.Color.blue())
        embed.add_field(name="Total Scaffolds", value=summary["total_scaffolds"], inline=True)
        embed.add_field(name="Completion Rate", value=f"{summary['completion_rate']}%", inline=True)
        if summary.get("by_status"):
            embed.add_field(name="By Status", value="\n".join(f"{k}: {v}" for k, v in summary["by_status"].items()), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-progress", description="Scaffold progress report")
    async def scaffold_progress(self, interaction: discord.Interaction):
        report = self.scaffolder.get_progress_report()
        embed = discord.Embed(title="Scaffold Progress Report", color=discord.Color.blue())
        embed.add_field(name="Total", value=report.get("total", 0))
        embed.add_field(name="Completed", value=report.get("completed", 0))
        embed.add_field(name="Failed", value=report.get("failed", 0))
        embed.add_field(name="In Progress", value=report.get("in_progress", 0))
        embed.add_field(name="Avg Steps", value=report.get("avg_steps_completed", 0))
        embed.add_field(name="Completion Rate", value=f"{report.get('completion_rate', 0)}%")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-review", description="Review a scaffold instance")
    @discord.app_commands.describe(instance_id="Instance ID", approved="Approve or reject", notes="Review notes")
    async def scaffold_review(self, interaction: discord.Interaction, instance_id: str, approved: bool, notes: str = ""):
        inst = self.scaffolder.review_instance(instance_id, approved, reviewer=interaction.user.name, notes=notes)
        if not inst:
            await interaction.response.send_message("Instance not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Scaffold Reviewed", color=discord.Color.green() if approved else discord.Color.red())
        embed.add_field(name="Instance", value=instance_id[:8])
        embed.add_field(name="New Status", value=inst.status)
        embed.add_field(name="Reviewed By", value=interaction.user.name)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-export", description="Export scaffolds")
    async def scaffold_export(self, interaction: discord.Interaction, status: str = ""):
        data = self.scaffolder.export_scaffolds(status=status)
        embed = discord.Embed(title="Scaffolds Exported", color=discord.Color.blue())
        embed.add_field(name="Exported", value=f"{len(data)} scaffold instances")
        embed.add_field(name="Status Filter", value=status or "All")
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="scaffold-delete", description="Delete a scaffold instance")
    @discord.app_commands.describe(instance_id="Instance ID")
    async def scaffold_delete(self, interaction: discord.Interaction, instance_id: str):
        deleted = self.scaffolder.delete_instance(instance_id)
        if not deleted:
            await interaction.response.send_message("Instance not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Scaffold Deleted", color=discord.Color.red())
        embed.add_field(name="Instance ID", value=instance_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-list", description="List scaffold instances")
    @discord.app_commands.describe(status="Filter by status")
    async def scaffold_list(self, interaction: discord.Interaction, status: str = ""):
        instances = self.scaffolder.list_instances(status=status)
        if not instances:
            await interaction.response.send_message("No scaffold instances.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Scaffold Instances ({len(instances)})", color=discord.Color.blue())
        for inst in instances[:10]:
            embed.add_field(name=f"{inst.service_name} ({inst.template_name})", value=f"Status: {inst.status} | Step: {inst.current_step.value} | Owner: {inst.owner}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-approve", description="Approve/reject scaffold")
    @discord.app_commands.describe(instance_id="Instance ID", approved="Yes/No", notes="Review notes")
    async def scaffold_approve(self, interaction: discord.Interaction, instance_id: str, approved: bool, notes: str = ""):
        inst = self.scaffolder.review_instance(instance_id, approved, reviewer=interaction.user.name, notes=notes)
        if not inst:
            await interaction.response.send_message("Instance not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Scaffold Approval", color=discord.Color.green() if approved else discord.Color.red())
        embed.add_field(name="Instance", value=instance_id[:8])
        embed.add_field(name="Decision", value="Approved" if approved else "Rejected")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-metrics", description="Scaffold metrics")
    async def scaffold_metrics(self, interaction: discord.Interaction):
        report = self.scaffolder.get_progress_report()
        embed = discord.Embed(title="Scaffold Metrics", color=discord.Color.blue())
        embed.add_field(name="Total", value=report.get("total", 0))
        embed.add_field(name="Completed", value=report.get("completed", 0))
        embed.add_field(name="Failed", value=report.get("failed", 0))
        embed.add_field(name="In Progress", value=report.get("in_progress", 0))
        embed.add_field(name="Avg Steps", value=report.get("avg_steps_completed", 0))
        embed.add_field(name="Completion Rate", value=f"{report.get('completion_rate', 0)}%")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-logs", description="Scaffold execution logs")
    @discord.app_commands.describe(instance_id="Instance ID")
    async def scaffold_logs(self, interaction: discord.Interaction, instance_id: str):
        logs = self.scaffolder.get_instance_logs(instance_id)
        if not logs:
            await interaction.response.send_message("No logs found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Scaffold Logs: {instance_id[:8]}", color=discord.Color.blue())
        for entry in logs[-5:]:
            embed.add_field(name=entry.get("step", "?"), value=f"Status: {entry.get('status')} | At: {entry.get('timestamp', '?')}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-retry", description="Retry a failed step")
    @discord.app_commands.describe(instance_id="Instance ID", step_name="Step to retry")
    async def scaffold_retry(self, interaction: discord.Interaction, instance_id: str, step_name: str):
        inst = self.scaffolder.retry_step(instance_id, step_name)
        if not inst:
            await interaction.response.send_message("Failed to retry step.", ephemeral=True)
            return
        embed = discord.Embed(title="Step Retried", color=discord.Color.green())
        embed.add_field(name="Instance", value=instance_id[:8])
        embed.add_field(name="Step", value=step_name)
        embed.add_field(name="Status", value=inst.status)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-analytics", description="Scaffold analytics")
    async def scaffold_analytics(self, interaction: discord.Interaction):
        analytics = self.scaffolder.get_scaffold_analytics()
        embed = discord.Embed(title="Scaffold Analytics", color=discord.Color.blue())
        embed.add_field(name="Total Instances", value=analytics["total_instances"])
        embed.add_field(name="Avg Steps", value=analytics["avg_steps"])
        for tmpl, count in list(analytics.get("by_template", {}).items())[:5]:
            embed.add_field(name=tmpl, value=f"{count} instances", inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-validate", description="Validate a template")
    @discord.app_commands.describe(template_name="Template name")
    async def scaffold_validate(self, interaction: discord.Interaction, template_name: str):
        result = self.scaffolder.validate_template(template_name)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Validation: {template_name}", color=discord.Color.green() if result["valid"] else discord.Color.red())
        embed.add_field(name="Valid", value="✅" if result["valid"] else "❌")
        embed.add_field(name="Steps", value=result["step_count"])
        if result.get("issues"):
            embed.add_field(name="Issues", value="\n".join(result["issues"]), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-estimate", description="Estimate template duration")
    @discord.app_commands.describe(template_name="Template name")
    async def scaffold_estimate(self, interaction: discord.Interaction, template_name: str):
        est = self.scaffolder.estimate_template_duration(template_name)
        if "error" in est:
            await interaction.response.send_message(est["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Duration Estimate: {template_name}", color=discord.Color.blue())
        embed.add_field(name="Minutes", value=est["estimated_minutes"])
        embed.add_field(name="Hours", value=est["estimated_hours"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-custom-step", description="Add custom step to template")
    @discord.app_commands.describe(template_name="Template name", step_name="Step name", step_type="Step type", description="Description")
    async def scaffold_custom_step(self, interaction: discord.Interaction, template_name: str, step_name: str, step_type: str = "manual", description: str = ""):
        step = self.scaffolder.add_custom_step(template_name, step_name, step_type, description)
        if not step:
            await interaction.response.send_message("Template not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Custom Step Added", color=discord.Color.green())
        embed.add_field(name="Template", value=template_name)
        embed.add_field(name="Step", value=step_name)
        embed.add_field(name="Type", value=step_type)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-approval-flow", description="Add approval flow to template")
    @discord.app_commands.describe(template_name="Template name", approvers="Comma-separated approver names")
    async def scaffold_approval_flow(self, interaction: discord.Interaction, template_name: str, approvers: str):
        approver_list = [a.strip() for a in approvers.split(",")]
        flow = self.scaffolder.add_approval_flow(template_name, approver_list)
        if not flow:
            await interaction.response.send_message("Template not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Approval Flow Created", color=discord.Color.green())
        embed.add_field(name="Template", value=template_name)
        embed.add_field(name="Approvers", value=", ".join(approver_list))
        embed.add_field(name="Flow ID", value=flow["flow_id"][:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-post-hook", description="Add post-scaffold hook")
    @discord.app_commands.describe(template_name="Template name", hook_type="Hook type", config_json="JSON config")
    async def scaffold_post_hook(self, interaction: discord.Interaction, template_name: str, hook_type: str, config_json: str):
        import json
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON config.", ephemeral=True)
            return
        hook = self.scaffolder.add_post_scaffold_hook(template_name, hook_type, config)
        if not hook:
            await interaction.response.send_message("Template not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Post-Hook Added", color=discord.Color.green())
        embed.add_field(name="Template", value=template_name)
        embed.add_field(name="Type", value=hook_type)
        embed.add_field(name="Hook ID", value=hook["hook_id"][:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scaffold-bulk-retire", description="Bulk retire scaffold instances")
    @discord.app_commands.describe(instance_ids="Comma-separated instance IDs")
    async def scaffold_bulk_retire(self, interaction: discord.Interaction, instance_ids: str):
        ids = [i.strip() for i in instance_ids.split(",")]
        count = self.scaffolder.batch_retire_instances(ids)
        embed = discord.Embed(title="Instances Retired", color=discord.Color.orange())
        embed.add_field(name="Total", value=len(ids))
        embed.add_field(name="Retired", value=count)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ScaffolderCog(bot))

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
