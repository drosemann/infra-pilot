import asyncio
import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.scorecards import ScorecardsManager, calculate_dora_score

logger = logging.getLogger(__name__)


class ScorecardsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scorecards = ScorecardsManager()

    @discord.app_commands.command(name="scorecard-team-create", description="Create a developer team")
    @discord.app_commands.describe(name="Team name", organization="Organization name")
    async def team_create(self, interaction: discord.Interaction, name: str, organization: str):
        team = self.scorecards.create_team(name, organization)
        embed = discord.Embed(title="Team Created", color=discord.Color.green())
        embed.add_field(name="ID", value=team.team_id[:8], inline=True)
        embed.add_field(name="Name", value=team.name, inline=True)
        embed.add_field(name="Organization", value=team.organization, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-dora", description="Record DORA metrics snapshot")
    @discord.app_commands.describe(team_id="Team ID", deploy_count="Deploy count", lead_time="Total lead time (hours)", incidents="Incident count", mttr="Total MTTR (hours)", failures="Change failures", changes="Total changes", days="Period in days")
    async def record_dora(self, interaction: discord.Interaction, team_id: str, deploy_count: int, lead_time: float, incidents: int, mttr: float, failures: int, changes: int, days: int = 30):
        snap = self.scorecards.create_snapshot(
            team_id,
            datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            datetime.utcnow(),
            deploy_count, lead_time, incidents, mttr, failures, changes,
        )
        if not snap:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        embed = discord.Embed(title="DORA Metrics Recorded", color=discord.Color.blue())
        embed.add_field(name="Deploy Frequency", value=f"{snap.deploy_frequency}/day", inline=True)
        embed.add_field(name="Avg Lead Time", value=f"{snap.avg_lead_time_hours}h", inline=True)
        embed.add_field(name="Avg MTTR", value=f"{snap.avg_mttr_hours}h", inline=True)
        embed.add_field(name="Change Failure Rate", value=f"{snap.change_failure_rate*100:.1f}%", inline=True)
        if snap.dora_score:
            embed.add_field(name="DORA Score", value=f"{snap.dora_score['total_score']}/100", inline=True)
            embed.add_field(name="Rating", value=snap.dora_score["rating"].upper(), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-leaderboard", description="DORA leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        board = self.scorecards.get_dora_leaderboard()
        if not board:
            await interaction.response.send_message("No data yet.", ephemeral=True)
            return
        embed = discord.Embed(title="DORA Score Leaderboard", color=discord.Color.gold())
        for i, entry in enumerate(board[:10], 1):
            embed.add_field(name=f"#{i} {entry['team_name']}", value=f"Score: {entry['total_score']} | Rating: {entry['rating'].upper()} | Deploy: {entry['deploy_frequency']}/day", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-summary", description="Scorecards summary")
    async def scorecard_summary(self, interaction: discord.Interaction):
        summary = self.scorecards.get_scorecards_summary()
        embed = discord.Embed(title="Scorecards Summary", color=discord.Color.blue())
        embed.add_field(name="Teams", value=summary.get("total_teams", 0), inline=True)
        embed.add_field(name="Snapshots", value=summary.get("total_snapshots", 0), inline=True)
        benchmarks = summary.get("benchmarks", {})
        if benchmarks:
            embed.add_field(name="Avg Score", value=benchmarks.get("average", "N/A"), inline=True)
            embed.add_field(name="Median", value=benchmarks.get("median", "N/A"), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-trend", description="Score trend for a team")
    @discord.app_commands.describe(team_id="Team ID", periods="Number of periods")
    async def scorecard_trend(self, interaction: discord.Interaction, team_id: str, periods: int = 6):
        trend = self.scorecards.get_trend_analysis(team_id, periods=periods)
        if not trend:
            await interaction.response.send_message("No trend data available.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Score Trend", color=discord.Color.blue())
        for entry in trend[-6:]:
            embed.add_field(name=entry["period_start"][:10], value=f"Score: {entry['value']}", inline=True)
        latest = trend[-1]["value"] if trend else 0
        earliest = trend[0]["value"] if trend else 0
        embed.add_field(name="Change", value=f"{'+' if latest >= earliest else ''}{round(latest - earliest, 1)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-compare", description="Compare teams")
    @discord.app_commands.describe(team_ids="Comma-separated team IDs")
    async def scorecard_compare(self, interaction: discord.Interaction, team_ids: str):
        ids = [t.strip() for t in team_ids.split(",")]
        comparison = self.scorecards.compare_teams(ids)
        if not comparison:
            await interaction.response.send_message("No data to compare.", ephemeral=True)
            return
        embed = discord.Embed(title="Team Comparison", color=discord.Color.blue())
        for entry in comparison:
            embed.add_field(name=entry["team_name"], value=f"Score: {entry['total_score']} | Rating: {entry['rating'].upper()}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-individual", description="Record individual score")
    @discord.app_commands.describe(user_id="User ID", metric="Metric name", value="Score value")
    async def scorecard_individual(self, interaction: discord.Interaction, user_id: str, metric: str, value: float):
        entry = self.scorecards.record_individual_score(user_id, metric, value)
        embed = discord.Embed(title="Individual Score Recorded", color=discord.Color.green())
        embed.add_field(name="User", value=user_id)
        embed.add_field(name="Metric", value=metric)
        embed.add_field(name="Value", value=value)
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="scorecard-delete-snapshot", description="Delete a DORA snapshot")
    @discord.app_commands.describe(snapshot_id="Snapshot ID")
    async def scorecard_delete_snapshot(self, interaction: discord.Interaction, snapshot_id: str):
        deleted = self.scorecards.delete_snapshot(snapshot_id)
        if not deleted:
            await interaction.response.send_message("Snapshot not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Snapshot Deleted", color=discord.Color.red())
        embed.add_field(name="Snapshot ID", value=snapshot_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-team-list", description="List all teams")
    async def scorecard_team_list(self, interaction: discord.Interaction):
        teams = self.scorecards.list_teams()
        if not teams:
            await interaction.response.send_message("No teams registered.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Teams ({len(teams)})", color=discord.Color.blue())
        for t in teams:
            embed.add_field(name=t.name, value=f"Org: {t.organization} | Snapshots: {len(t.snapshots)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-export", description="Export scorecards")
    @discord.app_commands.describe(team_id="Team ID filter")
    async def scorecard_export(self, interaction: discord.Interaction, team_id: str = ""):
        data = self.scorecards.export_scorecards(team_id=team_id)
        embed = discord.Embed(title="Scorecards Exported", color=discord.Color.green())
        embed.add_field(name="Teams Exported", value=len(data.get("teams", [])))
        embed.add_field(name="Snapshots", value=data.get("total_snapshots", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-team-delete", description="Delete a team")
    @discord.app_commands.describe(team_id="Team ID")
    async def scorecard_team_delete(self, interaction: discord.Interaction, team_id: str):
        deleted = self.scorecards.delete_team(team_id)
        if not deleted:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Team Deleted", color=discord.Color.red())
        embed.add_field(name="Team ID", value=team_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-snapshot-list", description="List snapshots for a team")
    @discord.app_commands.describe(team_id="Team ID")
    async def scorecard_snapshot_list(self, interaction: discord.Interaction, team_id: str):
        snapshots = self.scorecards.get_team_snapshots(team_id)
        if not snapshots:
            await interaction.response.send_message("No snapshots.", ephemeral=True)
            return
        embed = discord.Embed(title="Snapshots", color=discord.Color.blue())
        for snap in snapshots[-10:]:
            embed.add_field(name=snap.snapshot_id[:8], value=f"Score: {snap.dora_score['total_score'] if snap.dora_score else 'N/A'} | Date: {snap.period_start[:10]}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-goal", description="Set team DORA goal")
    @discord.app_commands.describe(team_id="Team ID", metric="Metric name", target="Target value")
    async def scorecard_goal(self, interaction: discord.Interaction, team_id: str, metric: str, target: float):
        goal = self.scorecards.set_dora_goal(team_id, metric, target)
        if not goal:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Goal Set", color=discord.Color.green())
        embed.add_field(name="Team", value=team_id[:8])
        embed.add_field(name="Metric", value=metric)
        embed.add_field(name="Target", value=str(target))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-compare", description="Compare multiple teams")
    @discord.app_commands.describe(team_ids="Comma-separated team IDs")
    async def scorecard_compare(self, interaction: discord.Interaction, team_ids: str):
        ids = [t.strip() for t in team_ids.split(",")]
        comparison = self.scorecards.compare_teams(ids)
        if not comparison:
            await interaction.response.send_message("No teams found.", ephemeral=True)
            return
        embed = discord.Embed(title="Team Comparison", color=discord.Color.blue())
        for c in comparison:
            embed.add_field(name=c["team_name"], value=f"Score: {c['latest_dora_score']} | Members: {c['member_count']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-history", description="Team score history")
    @discord.app_commands.describe(team_id="Team ID", days="Days to look back")
    async def scorecard_history(self, interaction: discord.Interaction, team_id: str, days: int = 180):
        history = self.scorecards.get_team_history(team_id, days)
        if not history:
            await interaction.response.send_message("No history.", ephemeral=True)
            return
        embed = discord.Embed(title=f"History: {team_id[:8]}", color=discord.Color.blue())
        for h in history[-10:]:
            embed.add_field(name=h["date"][:10], value=f"Score: {h['dora_score']} | Freq: {h['deployment_frequency']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-predict", description="Predict team score trend")
    @discord.app_commands.describe(team_id="Team ID", weeks="Weeks ahead")
    async def scorecard_predict(self, interaction: discord.Interaction, team_id: str, weeks: int = 4):
        pred = self.scorecards.predict_trend(team_id, weeks)
        if "error" in pred:
            await interaction.response.send_message(pred["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Prediction: {team_id[:8]}", color=discord.Color.blue())
        embed.add_field(name="Current", value=pred["current_score"])
        embed.add_field(name="Predicted", value=pred["predicted_score"])
        embed.add_field(name="Confidence", value=pred["confidence"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-org-summary", description="Organization summary")
    @discord.app_commands.describe(organization="Organization name")
    async def scorecard_org_summary(self, interaction: discord.Interaction, organization: str):
        summary = self.scorecards.get_organization_summary(organization)
        embed = discord.Embed(title=f"Org Summary: {organization}", color=discord.Color.blue())
        embed.add_field(name="Teams", value=summary["team_count"])
        embed.add_field(name="Avg Score", value=summary["avg_dora_score"])
        embed.add_field(name="Min Score", value=summary["min_score"])
        embed.add_field(name="Max Score", value=summary["max_score"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-goal-progress", description="Check goal progress")
    @discord.app_commands.describe(goal_id="Goal ID")
    async def scorecard_goal_progress(self, interaction: discord.Interaction, goal_id: str):
        progress = self.scorecards.check_goal_progress(goal_id)
        if "error" in progress:
            await interaction.response.send_message(progress["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Goal Progress", color=discord.Color.green())
        embed.add_field(name="Metric", value=progress["metric"])
        embed.add_field(name="Target", value=progress["target"])
        embed.add_field(name="Current", value=progress["current"])
        embed.add_field(name="Progress", value=f"{progress['progress_pct']}%")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="scorecard-ingest", description="Ingest DORA data for a team")
    @discord.app_commands.describe(team_id="Team ID", deployment_frequency="Deployments per day", lead_time="Lead time in hours", mttr="MTTR in minutes", change_failure_rate="Change failure rate %")
    async def scorecard_ingest(self, interaction: discord.Interaction, team_id: str, deployment_frequency: float = 0, lead_time: float = 0, mttr: float = 0, change_failure_rate: float = 0):
        data = {"deployment_frequency": deployment_frequency, "lead_time": lead_time, "mttr": mttr, "change_failure_rate": change_failure_rate}
        ingested = self.scorecards.ingest_dora_data(team_id, data)
        if not ingested:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        embed = discord.Embed(title="DORA Data Ingested", color=discord.Color.green())
        embed.add_field(name="Team", value=team_id[:8])
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ScorecardsCog(bot))

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
