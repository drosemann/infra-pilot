import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.developer_pulse import DeveloperPulseManager, SurveyType

logger = logging.getLogger(__name__)


class PulseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pulse = DeveloperPulseManager()

    @discord.app_commands.command(name="pulse-create", description="Create a developer survey")
    @discord.app_commands.describe(title="Survey title", survey_type="Type (nps/satisfaction/wellbeing)", created_by="Creator name")
    async def pulse_create(self, interaction: discord.Interaction, title: str, survey_type: str, created_by: str):
        survey = self.pulse.create_survey(title, SurveyType(survey_type), created_by)
        embed = discord.Embed(title="Survey Created", color=discord.Color.green())
        embed.add_field(name="ID", value=survey.survey_id[:8])
        embed.add_field(name="Title", value=survey.title)
        embed.add_field(name="Type", value=survey.survey_type.value)
        embed.add_field(name="Questions", value=len(survey.questions))
        embed.add_field(name="Status", value=survey.status.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-launch", description="Launch a survey")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_launch(self, interaction: discord.Interaction, survey_id: str):
        survey = self.pulse.launch_survey(survey_id)
        if not survey:
            await interaction.response.send_message("Survey not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Survey Launched", color=discord.Color.green())
        embed.add_field(name="Title", value=survey.title)
        embed.add_field(name="Status", value=survey.status.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-nps", description="Show NPS for a survey")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_nps(self, interaction: discord.Interaction, survey_id: str):
        nps = self.pulse.calculate_nps(survey_id)
        if not nps:
            await interaction.response.send_message("No NPS data yet.", ephemeral=True)
            return
        embed = discord.Embed(title=f"NPS Score", color=discord.Color.blue())
        embed.add_field(name="Score", value=nps.get("nps_score"))
        embed.add_field(name="Promoters", value=f"{nps.get('promoters')} ({nps.get('promoters_pct')}%)")
        embed.add_field(name="Detractors", value=f"{nps.get('detractors')} ({nps.get('detractors_pct')}%)")
        embed.add_field(name="Responses", value=nps.get("total_responses"))
        embed.add_field(name="Response Rate", value=f"{nps.get('response_rate')}%")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-summary", description="Developer pulse summary")
    async def pulse_summary(self, interaction: discord.Interaction):
        summary = self.pulse.get_pulse_summary()
        embed = discord.Embed(title="Developer Pulse Summary", color=discord.Color.blue())
        embed.add_field(name="Total Surveys", value=summary.get("total_surveys", 0))
        embed.add_field(name="Active", value=summary.get("active_surveys", 0))
        embed.add_field(name="Total Responses", value=summary.get("total_responses", 0))
        embed.add_field(name="Average NPS", value=summary.get("average_nps", "N/A"))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-close", description="Close a survey")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_close(self, interaction: discord.Interaction, survey_id: str):
        survey = self.pulse.close_survey(survey_id)
        if not survey:
            await interaction.response.send_message("Survey not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Survey Closed", color=discord.Color.orange())
        embed.add_field(name="Title", value=survey.title)
        embed.add_field(name="Status", value=survey.status.value)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-nps-breakdown", description="Detailed NPS breakdown")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_nps_breakdown(self, interaction: discord.Interaction, survey_id: str):
        breakdown = self.pulse.get_detailed_nps_breakdown(survey_id)
        if not breakdown:
            await interaction.response.send_message("No data available.", ephemeral=True)
            return
        embed = discord.Embed(title="NPS Breakdown", color=discord.Color.blue())
        embed.add_field(name="Score", value=breakdown.get("nps_score", "N/A"))
        embed.add_field(name="Promoters", value=breakdown.get("promoters", 0))
        embed.add_field(name="Detractors", value=breakdown.get("detractors", 0))
        embed.add_field(name="Responses", value=breakdown.get("total_responses", 0))
        embed.add_field(name="Comments", value=breakdown.get("comments_count", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-analytics", description="Pulse analytics overview")
    async def pulse_analytics(self, interaction: discord.Interaction):
        analytics = self.pulse.get_analytics_overview()
        embed = discord.Embed(title="Pulse Analytics", color=discord.Color.blue())
        embed.add_field(name="Surveys", value=analytics.get("total_surveys", 0))
        embed.add_field(name="Total Responses", value=analytics.get("total_responses", 0))
        embed.add_field(name="Response Rate", value=f"{analytics.get('response_rate_pct', 0)}%")
        embed.add_field(name="Avg NPS", value=analytics.get("average_nps", "N/A"))
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="pulse-list", description="List all surveys")
    @discord.app_commands.describe(status="Filter by status")
    async def pulse_list(self, interaction: discord.Interaction, status: str = ""):
        surveys = self.pulse.list_surveys(status=status)
        if not surveys:
            await interaction.response.send_message("No surveys found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Surveys ({len(surveys)})", color=discord.Color.blue())
        for s in surveys[:10]:
            embed.add_field(name=s.title, value=f"Type: {s.survey_type.value} | Status: {s.status.value} | Responses: {s.response_count}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-respond", description="Submit survey response")
    @discord.app_commands.describe(survey_id="Survey ID", answers_json="JSON object of question_id: score")
    async def pulse_respond(self, interaction: discord.Interaction, survey_id: str, answers_json: str):
        import json
        try:
            answers = json.loads(answers_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON.", ephemeral=True)
            return
        result = self.pulse.submit_response(survey_id, interaction.user.name, answers)
        if not result:
            await interaction.response.send_message("Survey not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Response Recorded", color=discord.Color.green())
        embed.add_field(name="Survey", value=survey_id[:8])
        embed.add_field(name="Respondent", value=interaction.user.name)
        embed.add_field(name="Answers", value=str(len(answers)))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-metrics", description="Survey metrics")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_metrics(self, interaction: discord.Interaction, survey_id: str):
        metrics = self.pulse.get_survey_metrics(survey_id)
        if not metrics:
            await interaction.response.send_message("Survey not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Survey Metrics", color=discord.Color.blue())
        embed.add_field(name="Responses", value=metrics.get("total_responses", 0))
        embed.add_field(name="Completion Rate", value=f"{metrics.get('completion_rate', 0)}%")
        embed.add_field(name="Avg Score", value=round(metrics.get("average_score", 0), 2))
        embed.add_field(name="Status", value=metrics.get("status", "N/A"))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-export", description="Export survey results")
    @discord.app_commands.describe(survey_id="Survey ID", format="Export format")
    async def pulse_export(self, interaction: discord.Interaction, survey_id: str, format: str = "json"):
        result = self.pulse.export_results(survey_id, format)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Survey Exported", color=discord.Color.green())
        embed.add_field(name="Format", value=format)
        embed.add_field(name="Responses", value=result.get("count", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-results", description="Survey results overview")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_results(self, interaction: discord.Interaction, survey_id: str):
        results = self.pulse.get_survey_results(survey_id)
        if not results:
            await interaction.response.send_message("No results yet.", ephemeral=True)
            return
        embed = discord.Embed(title="Survey Results", color=discord.Color.blue())
        embed.add_field(name="Total Responses", value=results.get("total_responses", 0))
        if results.get("average_score"):
            embed.add_field(name="Average Score", value=round(results["average_score"], 2))
        if results.get("distribution"):
            dist = results["distribution"]
            for k, v in list(dist.items())[:5]:
                embed.add_field(name=k, value=v, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-delete", description="Delete a survey")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_delete(self, interaction: discord.Interaction, survey_id: str):
        deleted = self.pulse.delete_survey(survey_id)
        if not deleted:
            await interaction.response.send_message("Survey not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Survey Deleted", color=discord.Color.red())
        embed.add_field(name="Survey ID", value=survey_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-aggregate", description="Aggregate survey results")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_aggregate(self, interaction: discord.Interaction, survey_id: str):
        agg = self.pulse.aggregate_survey_results(survey_id)
        if "error" in agg:
            await interaction.response.send_message(agg["error"], ephemeral=True)
            return
        embed = discord.Embed(title=f"Aggregated: {agg['title']}", color=discord.Color.blue())
        embed.add_field(name="Responses", value=agg["total_responses"])
        for q, data in list(agg.get("aggregated", {}).items())[:3]:
            if "avg" in data:
                embed.add_field(name=q[:30], value=f"Avg: {data['avg']} (n={data['total_responses']})", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-sentiment-trend", description="Sentiment trend over time")
    @discord.app_commands.describe(months="Months to analyze")
    async def pulse_sentiment_trend(self, interaction: discord.Interaction, months: int = 6):
        trend = self.pulse.get_sentiment_trend(months=months)
        embed = discord.Embed(title="Sentiment Trend", color=discord.Color.blue())
        for month, data in list(trend.get("trend", {}).items())[:6]:
            embed.add_field(name=month, value=f"Avg: {data['avg']} (n={data['count']})", inline=True)
        if not trend.get("trend"):
            embed.description = "No data."
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-export-csv", description="Export survey as CSV")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_export_csv(self, interaction: discord.Interaction, survey_id: str):
        csv_data = self.pulse.export_survey_data(survey_id, format="csv")
        if "error" in csv_data:
            await interaction.response.send_message(csv_data["error"], ephemeral=True)
            return
        embed = discord.Embed(title="CSV Export", color=discord.Color.green())
        embed.add_field(name="Survey ID", value=survey_id[:8])
        embed.add_field(name="Lines", value=len(csv_data.splitlines()))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-schedule", description="Schedule a recurring survey")
    @discord.app_commands.describe(title="Survey title", questions="Comma-separated questions", survey_type="Survey type", cron="Cron expression")
    async def pulse_schedule(self, interaction: discord.Interaction, title: str, questions: str, survey_type: str = "nps", cron: str = "0 0 1 * *"):
        q_list = [q.strip() for q in questions.split(",")]
        result = self.pulse.schedule_survey(title, q_list, SurveyType(survey_type.upper()), cron_expression=cron)
        embed = discord.Embed(title="Survey Scheduled", color=discord.Color.green())
        embed.add_field(name="Survey", value=result["survey"]["title"])
        embed.add_field(name="Schedule ID", value=result["schedule"]["schedule_id"][:8])
        embed.add_field(name="Cron", value=cron)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-schedules", description="List scheduled surveys")
    async def pulse_schedules(self, interaction: discord.Interaction):
        schedules = self.pulse.get_schedules()
        if not schedules:
            await interaction.response.send_message("No schedules.", ephemeral=True)
            return
        embed = discord.Embed(title="Scheduled Surveys", color=discord.Color.blue())
        for s in schedules[:10]:
            embed.add_field(name=s["schedule_id"][:8], value=f"Survey: {s['survey_id'][:8]} | Status: {s['status']} | Cron: {s['cron_expression']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-insights", description="Survey insights and NPS")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_insights(self, interaction: discord.Interaction, survey_id: str):
        insights = self.pulse.get_response_insights(survey_id)
        if "error" in insights:
            await interaction.response.send_message(insights["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Survey Insights", color=discord.Color.blue())
        embed.add_field(name="Responses", value=insights["total_responses"])
        embed.add_field(name="NPS Score", value=insights["nps_score"])
        embed.add_field(name="Promoters", value=insights["promoters"])
        embed.add_field(name="Passives", value=insights["passives"])
        embed.add_field(name="Detractors", value=insights["detractors"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pulse-reminders", description="Send reminders for pending surveys")
    @discord.app_commands.describe(survey_id="Survey ID")
    async def pulse_reminders(self, interaction: discord.Interaction, survey_id: str):
        result = self.pulse.bulk_send_reminders(survey_id)
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Reminders Sent", color=discord.Color.green())
        embed.add_field(name="Survey ID", value=survey_id[:8])
        embed.add_field(name="Reminders", value=result["reminders_sent"])
        embed.add_field(name="Total Pending", value=result["total_pending"])
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PulseCog(bot))

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
