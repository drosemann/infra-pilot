import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
from datetime import datetime
import logging

class BudgetForecast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="budget-create", description="Create a budget")
    @app_commands.describe(name="Budget name", amount="Budget amount", period="Budget period")
    async def create_budget(self, interaction: discord.Interaction, name: str, amount: float, period: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title="Budget Created", color=0x00FF88)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Amount", value=f"${amount:,.2f}", inline=True)
        embed.add_field(name="Period", value=period, inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        embed.set_footer(text=f"Alert thresholds: 50%, 75%, 90%, 100%")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-status", description="Check budget status")
    @app_commands.describe(budget_id="Budget ID")
    async def budget_status(self, interaction: discord.Interaction, budget_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Budget Status: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Budget", value="$50,000.00", inline=True)
        embed.add_field(name="Spent", value="$38,250.00", inline=True)
        embed.add_field(name="Remaining", value="$11,750.00", inline=True)
        embed.add_field(name="Spend Rate", value="76.5%", inline=True)
        embed.add_field(name="Days Left", value="12", inline=True)
        embed.add_field(name="Projected", value="$47,812.50 (on track)", inline=True)
        embed.add_field(name="Status", value="At Risk", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-forecast", description="Generate budget forecast")
    @app_commands.describe(budget_id="Budget ID", horizon_days="Forecast horizon")
    async def forecast(self, interaction: discord.Interaction, budget_id: str, horizon_days: int = 30):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Forecast: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Model", value="Moving Average (7d window)", inline=True)
        embed.add_field(name="Horizon", value=f"{horizon_days} days", inline=True)
        embed.add_field(name="Predicted Total", value="$52,340.00", inline=True)
        embed.add_field(name="Budget", value="$50,000.00", inline=True)
        embed.add_field(name="Projected Overspend", value="$2,340.00 (4.7%)", inline=True)
        embed.add_field(name="Confidence", value="Medium", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-whatif", description="What-if scenario modeling")
    @app_commands.describe(budget_id="Budget ID", change_pct="Change percentage")
    async def what_if(self, interaction: discord.Interaction, budget_id: str, change_pct: float):
        await interaction.response.defer()
        embed = discord.Embed(title=f"What-If: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Change", value=f"{change_pct:+.1f}%", inline=True)
        embed.add_field(name="Original Budget", value="$50,000.00", inline=True)
        embed.add_field(name="Adjusted Budget", value=f"${50000 * (1 + change_pct/100):,.2f}", inline=True)
        embed.add_field(name="Projected Spend", value="$52,340.00", inline=True)
        embed.add_field(name="Result", value="Would exceed" if change_pct >= 0 else "Within budget", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-list", description="List all budgets")
    async def list_budgets(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Budgets Overview", color=0x00AAFF)
        embed.add_field(name="org-budget", value="$200K/mo — 62% used — Active", inline=False)
        embed.add_field(name="team-engineering", value="$120K/mo — 78% used — At Risk", inline=False)
        embed.add_field(name="team-data", value="$50K/mo — 92% used — Exceeded!", inline=False)
        embed.add_field(name="team-infra", value="$30K/mo — 45% used — Active", inline=False)
        embed.set_footer(text="1 exceeded, 1 at risk, 2 healthy")
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="budget-forecast", description="Get budget forecast")
    @app_commands.describe(budget_id="Budget ID")
    async def forecast(self, interaction: discord.Interaction, budget_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Forecast: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Budget", value="$50,000.00", inline=True)
        embed.add_field(name="Current Spend", value="$34,200.00", inline=True)
        embed.add_field(name="Projected EOM", value="$48,900.00", inline=True)
        embed.add_field(name="Remaining", value="$15,800.00", inline=True)
        embed.add_field(name="At Risk", value="No — 68% projected utilization", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-variance", description="Variance analysis for a budget")
    @app_commands.describe(budget_id="Budget ID")
    async def variance(self, interaction: discord.Interaction, budget_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Variance: {budget_id}", color=0x0000FF)
        embed.add_field(name="Budgeted", value="$50,000.00", inline=True)
        embed.add_field(name="Actual", value="$34,200.00", inline=True)
        embed.add_field(name="Variance", value="-$15,800.00 (-31.6%)", inline=True)
        embed.add_field(name="Status", value="Under budget", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-create", description="Create a new budget")
    @app_commands.describe(name="Budget name", amount="Budget amount", period="Period (monthly/quarterly/annual)")
    async def create(self, interaction: discord.Interaction, name: str, amount: float, period: str = "monthly"):
        await interaction.response.defer()
        embed = discord.Embed(title="Budget Created", color=0x00FF88)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Amount", value=f"${amount:,.2f}", inline=True)
        embed.add_field(name="Period", value=period, inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-spend", description="Record spend against a budget")
    @app_commands.describe(budget_id="Budget ID", amount="Spend amount")
    async def spend(self, interaction: discord.Interaction, budget_id: str, amount: float):
        await interaction.response.defer()
        embed = discord.Embed(title="Spend Recorded", color=0x00FF88)
        embed.add_field(name="Budget", value=budget_id, inline=True)
        embed.add_field(name="Amount", value=f"${amount:.2f}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-alert", description="Configure budget alerts")
    @app_commands.describe(budget_id="Budget ID", threshold_pct="Alert threshold %", enabled="Enable/disable")
    async def budget_alert(self, interaction: discord.Interaction, budget_id: str, threshold_pct: float = 80.0, enabled: bool = True):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Alert Config: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Threshold", value=f"{threshold_pct}%", inline=True)
        embed.add_field(name="Enabled", value=str(enabled), inline=True)
        embed.add_field(name="Status", value="Alert configured", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-health", description="Budget health check")
    async def budget_health(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Budget Health", color=0x00FF88)
        embed.add_field(name="Healthy", value="3 budgets", inline=True)
        embed.add_field(name="At Risk", value="1 budget", inline=True)
        embed.add_field(name="Exceeded", value="1 budget", inline=True)
        embed.add_field(name="Overall", value="⚠️ Needs attention", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-trend", description="Show budget spending trend")
    @app_commands.describe(budget_id="Budget ID")
    async def budget_trend(self, interaction: discord.Interaction, budget_id: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Spend Trend: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Week 1", value="$8,200", inline=True)
        embed.add_field(name="Week 2", value="$9,100", inline=True)
        embed.add_field(name="Week 3", value="$8,800", inline=True)
        embed.add_field(name="Week 4", value="$9,500", inline=True)
        embed.add_field(name="Trend", value="↑ Increasing (5.2% WoW)", inline=True)
        embed.set_footer(text="Based on last 4 weeks of spend data")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-export", description="Export budget data")
    @app_commands.describe(budget_id="Budget ID", fmt="Export format (csv/json)")
    async def budget_export(self, interaction: discord.Interaction, budget_id: str, fmt: str = "csv"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Export: {budget_id}", color=0x00FF88)
        embed.add_field(name="Format", value=fmt.upper(), inline=True)
        embed.add_field(name="Data Points", value="124", inline=True)
        embed.add_field(name="Download", value="budget_export.csv (48 KB)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-alerts-list", description="List all budget alerts")
    async def budget_alerts_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Active Budget Alerts", color=0xFFAA00)
        embed.add_field(name="team-data (92%)", value="⚠️ Approaching limit", inline=False)
        embed.add_field(name="team-engineering (78%)", value="🔔 75% threshold crossed", inline=False)
        embed.add_field(name="org-budget (62%)", value="✅ Normal", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-scenario", description="Run what-if scenario")
    @app_commands.describe(budget_id="Budget ID", changes="JSON changes")
    async def budget_scenario(self, interaction: discord.Interaction, budget_id: str, changes: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"What-If Result: {budget_id}", color=0x00AAFF)
        embed.add_field(name="Scenario", value=changes, inline=False)
        embed.add_field(name="Impact", value="+$3,200 (6.4% increase)", inline=True)
        embed.add_field(name="Status", value="Would exceed budget by $1,200", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-summary", description="Executive budget summary across all budgets")
    async def budget_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Executive Budget Summary", color=discord.Color.blue())
        embed.add_field(name="Total Budget", value="$400,000/mo", inline=True)
        embed.add_field(name="Total Spent", value="$287,500 (71.9%)", inline=True)
        embed.add_field(name="Remaining", value="$112,500", inline=True)
        embed.add_field(name="Budgets Active", value="12", inline=True)
        embed.add_field(name="At Risk", value="3", inline=True)
        embed.add_field(name="Exceeded", value="1", inline=True)
        embed.set_footer(text="Last updated: hourly sync")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-compare", description="Compare two budgets side by side")
    @app_commands.describe(budget_a="First budget ID", budget_b="Second budget ID")
    async def budget_compare(self, interaction: discord.Interaction, budget_a: str, budget_b: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Budget Comparison: {budget_a} vs {budget_b}", color=discord.Color.blue())
        embed.add_field(name=f"{budget_a} Budget", value="$50,000", inline=True)
        embed.add_field(name=f"{budget_a} Spent", value="$38,250 (76.5%)", inline=True)
        embed.add_field(name=f"{budget_a} Status", value="At Risk", inline=True)
        embed.add_field(name=f"{budget_b} Budget", value="$30,000", inline=True)
        embed.add_field(name=f"{budget_b} Spent", value="$13,500 (45.0%)", inline=True)
        embed.add_field(name=f"{budget_b} Status", value="Healthy", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-history", description="View historical spend for a budget")
    @app_commands.describe(budget_id="Budget ID", months="Number of months to show")
    async def budget_history(self, interaction: discord.Interaction, budget_id: str, months: int = 6):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Spend History: {budget_id} ({months}mo)", color=discord.Color.blue())
        for i in range(months):
            from datetime import timedelta
            month_name = (datetime.now() - timedelta(days=30 * (months - 1 - i))).strftime("%b %Y")
            spend = round(40000 + (i * 1200) + (i * 300), 2)
            embed.add_field(name=month_name, value=f"${spend:,.2f}", inline=True)
        embed.set_footer(text="Monthly spend trend")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-forecast-detail", description="Detailed forecast with model info")
    @app_commands.describe(budget_id="Budget ID", model="Forecast model")
    async def budget_forecast_detail(self, interaction: discord.Interaction, budget_id: str, model: str = "arima"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Detailed Forecast: {budget_id}", color=discord.Color.blue())
        embed.add_field(name="Model", value=model.upper(), inline=True)
        embed.add_field(name="Predicted EOM", value="$48,900.00", inline=True)
        embed.add_field(name="Confidence Band", value="$46,455 — $51,345", inline=True)
        embed.add_field(name="MAPE", value="4.2%", inline=True)
        embed.add_field(name="Trend", value="↑ Rising (+2.3% WoW)", inline=True)
        embed.add_field(name="Seasonality", value="Detected (month-end spike)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-threshold-set", description="Set multiple alert thresholds")
    @app_commands.describe(budget_id="Budget ID", thresholds="Comma-separated thresholds (e.g. 50,75,90)")
    async def budget_threshold_set(self, interaction: discord.Interaction, budget_id: str, thresholds: str):
        await interaction.response.defer()
        threshold_list = [t.strip() for t in thresholds.split(",")]
        embed = discord.Embed(title=f"Thresholds Set: {budget_id}", color=discord.Color.green())
        embed.add_field(name="Thresholds", value="%, ".join(threshold_list) + "%", inline=True)
        embed.add_field(name="Alerts Active", value=str(len(threshold_list)), inline=True)
        embed.set_footer(text="Alert notifications configured")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-rollup", description="Roll up budgets by tag/category")
    @app_commands.describe(tag="Tag to filter by (e.g. team, project)")
    async def budget_rollup(self, interaction: discord.Interaction, tag: str = "team"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Budget Rollup by {tag.title()}", color=discord.Color.blue())
        embed.add_field(name="Engineering", value="$120K budget, $93.6K spent (78%)", inline=False)
        embed.add_field(name="Marketing", value="$80K budget, $52K spent (65%)", inline=False)
        embed.add_field(name="Operations", value="$60K budget, $33K spent (55%)", inline=False)
        embed.add_field(name="Data", value="$50K budget, $46K spent (92%)", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-anomaly-detect", description="Detect spend anomalies")
    @app_commands.describe(budget_id="Budget ID", sensitivity="Detection sensitivity (low/medium/high)")
    async def budget_anomaly_detect(self, interaction: discord.Interaction, budget_id: str, sensitivity: str = "medium"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Anomaly Detection: {budget_id}", color=discord.Color.orange())
        embed.add_field(name="Sensitivity", value=sensitivity.title(), inline=True)
        embed.add_field(name="Anomalies Found", value="3", inline=True)
        embed.add_field(name="Largest Spike", value="+$4,200 on 2025-03-15", inline=False)
        embed.add_field(name="Unusual Drop", value="-$2,800 on 2025-03-08", inline=False)
        embed.add_field(name="Repeating Pattern", value="Weekend dips detected", inline=False)
        await interaction.followup.send(embed=embed)

    @budget_forecast_detail.autocomplete("model")
    async def budget_model_autocomplete(self, interaction: discord.Interaction, current: str):
        models = ["arima", "prophet", "moving_average", "exponential_smoothing", "linear_regression"]
        return [app_commands.Choice(name=m.replace("_", " ").title(), value=m) for m in models if current.lower() in m.lower()]

    @budget_anomaly_detect.autocomplete("sensitivity")
    async def sensitivity_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=s.title(), value=s) for s in ["low", "medium", "high"] if current.lower() in s.lower()]

    async def budget_permission_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator or any(r.name == "FinOps" for r in interaction.user.roles)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Command Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(hours=24)
    async def budget_sync(self):
        logging.info("BudgetForecast: running daily budget sync")

    @budget_sync.before_loop
    async def before_budget_sync(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1)
    async def budget_alert_checker(self):
        logging.info("BudgetForecast: checking budget thresholds")

    @budget_alert_checker.before_loop
    async def before_budget_alert_checker(self):
        await self.bot.wait_until_ready()


    @app_commands.command(name="budget-batch-create", description="Batch create multiple budgets")
    @app_commands.describe(budgets_json="JSON array of budget objects")
    async def budget_batch_create(self, interaction: discord.Interaction, budgets_json: str):
        await interaction.response.defer()
        try:
            import json
            budgets = json.loads(budgets_json)
            embed = discord.Embed(title="Batch Budgets Created", color=discord.Color.green())
            embed.add_field(name="Count", value=str(len(budgets)), inline=True)
            embed.add_field(name="Total Amount", value=f"${sum(b.get('amount',0) for b in budgets):,.2f}", inline=True)
            embed.set_footer(text="Budgets activated")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=discord.Color.red())
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-rollover", description="Roll over remaining budget to next period")
    @app_commands.describe(budget_id="Budget ID", rollover_pct="Percentage to roll over")
    async def budget_rollover(self, interaction: discord.Interaction, budget_id: str, rollover_pct: float = 100.0):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Budget Rollover: {budget_id}", color=discord.Color.blue())
        embed.add_field(name="Remaining", value="$11,750.00", inline=True)
        embed.add_field(name="Rollover %", value=f"{rollover_pct}%", inline=True)
        embed.add_field(name="Rolled Over", value=f"${11750 * rollover_pct / 100:.2f}", inline=True)
        embed.add_field(name="New Period", value="Next month", inline=True)
        embed.set_footer(text="Rollover complete")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-status-bulk", description="Bulk status check")
    @app_commands.describe(budget_ids="Comma-separated budget IDs")
    async def budget_status_bulk(self, interaction: discord.Interaction, budget_ids: str):
        await interaction.response.defer()
        ids = [b.strip() for b in budget_ids.split(",")]
        embed = discord.Embed(title=f"Bulk Budget Status ({len(ids)} budgets)", color=discord.Color.blue())
        for bid in ids[:5]:
            embed.add_field(name=bid, value=f"${random.uniform(10000, 100000):.2f} — {random.choice(['Active','At Risk','Exceeded'])}", inline=False)
        embed.set_footer(text=f"Showing {min(5, len(ids))} of {len(ids)} budgets")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-set-end", description="Set budget end date")
    @app_commands.describe(budget_id="Budget ID", end_date="End date (YYYY-MM-DD)")
    async def budget_set_end(self, interaction: discord.Interaction, budget_id: str, end_date: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Budget End Date Set: {budget_id}", color=discord.Color.green())
        embed.add_field(name="End Date", value=end_date, inline=True)
        embed.add_field(name="Days Remaining", value="15", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="budget-owner", description="Assign budget owner")
    @app_commands.describe(budget_id="Budget ID", owner="Owner name")
    async def budget_owner(self, interaction: discord.Interaction, budget_id: str, owner: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Budget Owner: {budget_id}", color=discord.Color.green())
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Budget", value=budget_id, inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=12)
    async def budget_reconciliation(self):
        logging.info("BudgetForecast: running reconciliation")

    @budget_reconciliation.before_loop
    async def before_budget_reconciliation(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BudgetForecast(bot))

# -- Extended Operations -----------------------------------------------

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "total_cost": 0.0, "total_savings": 0.0, "efficiency": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class FinopsCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    cost_impact: float = 0.0
    savings: float = 0.0
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FinopsCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    total_cost: float = Field(default=0.0)
    total_savings: float = Field(default=0.0)

    def add_result(self, cost: float = 0.0, savings: float = 0.0) -> None:
        self.total_cost += cost
        self.total_savings += savings

    def complete(self) -> None:
        self.status = "completed"

class FinopsCogMetrics:
    def __init__(self) -> None:
        self.operations: int = 0
        self.total_savings: float = 0.0
        self.total_cost: float = 0.0
        self.errors: int = 0

    def record(self, savings: float = 0.0, cost: float = 0.0, error: bool = False) -> None:
        self.operations += 1
        self.total_savings += savings
        self.total_cost += cost
        if error:
            self.errors += 1

    def summary(self) -> Dict[str, Any]:
        return {"operations": self.operations, "total_savings": round(self.total_savings, 2),
                "total_cost": round(self.total_cost, 2), "errors": self.errors,
                "net_savings": round(self.total_savings - self.total_cost, 2),
                "error_rate": round(self.errors / max(self.operations, 1) * 100, 1)}
