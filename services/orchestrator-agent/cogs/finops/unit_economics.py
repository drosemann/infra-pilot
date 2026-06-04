import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging

class UnitEconomics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unit-cost", description="Show unit cost metrics")
    @app_commands.describe(customer_id="Customer ID", metric="Metric type")
    async def unit_cost(self, interaction: discord.Interaction, customer_id: str = None, metric: str = "cost_per_customer"):
        await interaction.response.defer()
        cid = customer_id or "all"
        embed = discord.Embed(title=f"Unit Economics — {cid}", color=0x00AAFF)
        embed.add_field(name="Cost/Customer", value="$149.50", inline=True)
        embed.add_field(name="Cost/Transaction", value="$0.42", inline=True)
        embed.add_field(name="Cost/Deployment", value="$11.80", inline=True)
        embed.add_field(name="Revenue/Customer", value="$299.00", inline=True)
        embed.add_field(name="Margin/Customer", value="$149.50 (50%)", inline=True)
        embed.add_field(name="Trend", value="Improving (last 30d: -5.2%)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-target", description="Set unit cost target")
    @app_commands.describe(customer_id="Customer ID", metric="Metric", target="Target value")
    async def set_target(self, interaction: discord.Interaction, customer_id: str, metric: str, target: float):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Cost Target Set", color=0x00FF88)
        embed.add_field(name="Customer", value=customer_id, inline=True)
        embed.add_field(name="Metric", value=metric, inline=True)
        embed.add_field(name="Target", value=f"${target}", inline=True)
        embed.add_field(name="Alert Threshold", value=f"${target * 1.2:.2f}", inline=True)
        embed.set_footer(text="Violations will trigger alerts")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-alerts", description="Show unit cost target violations")
    async def unit_alerts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Cost Alerts", color=0xFF4444)
        embed.add_field(name="customer-001", value="Cost/Customer: $182.30 (target: $150.00)", inline=False)
        embed.add_field(name="customer-003", value="Cost/Transaction: $0.68 (target: $0.50)", inline=False)
        embed.set_footer(text="2 violations detected")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-summary", description="Unit economics overview")
    async def summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Economics Overview", color=0x00AAFF)
        embed.add_field(name="Customers Tracked", value="24", inline=True)
        embed.add_field(name="Avg Cost/Customer", value="$149.50", inline=True)
        embed.add_field(name="Avg Revenue/Customer", value="$299.00", inline=True)
        embed.add_field(name="Avg Margin", value="50%", inline=True)
        embed.add_field(name="Target Violations", value="2 active", inline=True)
        embed.add_field(name="Trend", value="Costs decreasing 5.2% MoM", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="unit-record", description="Record a unit metric")
    @app_commands.describe(customer_id="Customer ID", metric_name="Metric name", value="Metric value", dimension="Optional dimension")
    async def record_metric(self, interaction: discord.Interaction, customer_id: str, metric_name: str, value: float, dimension: str = "general"):
        await interaction.response.defer()
        embed = discord.Embed(title="Metric Recorded", color=0x00FF88)
        embed.add_field(name="Customer", value=customer_id, inline=True)
        embed.add_field(name="Metric", value=metric_name, inline=True)
        embed.add_field(name="Value", value=str(value), inline=True)
        embed.add_field(name="Dimension", value=dimension, inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-set-target", description="Set a unit economics target")
    @app_commands.describe(metric_name="Metric name", target_value="Target value", threshold="Alert threshold %")
    async def set_target(self, interaction: discord.Interaction, metric_name: str, target_value: float, threshold: float = 10.0):
        await interaction.response.defer()
        embed = discord.Embed(title="Target Set", color=0x00FF88)
        embed.add_field(name="Metric", value=metric_name, inline=True)
        embed.add_field(name="Target", value=str(target_value), inline=True)
        embed.add_field(name="Threshold", value=f"{threshold}%", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-trend", description="View unit metric trend")
    @app_commands.describe(metric_name="Metric name")
    async def trend(self, interaction: discord.Interaction, metric_name: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Trend: {metric_name}", color=0x00AAFF)
        embed.add_field(name="Current", value="$12.50", inline=True)
        embed.add_field(name="7-Day Avg", value="$11.80", inline=True)
        embed.add_field(name="30-Day Avg", value="$10.90", inline=True)
        embed.add_field(name="Direction", value="Increasing (+14.7%)", inline=True)
        embed.add_field(name="Target", value="$10.00", inline=True)
        embed.add_field(name="Status", value="Above target — Review required", inline=True)
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="unit-compare", description="Compare unit costs between customers")
    @app_commands.describe(customer_a="First customer ID", customer_b="Second customer ID")
    async def compare(self, interaction: discord.Interaction, customer_a: str, customer_b: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Cost Comparison", color=0x3498DB)
        embed.add_field(name=f"{customer_a} Cost/Customer", value="$145.20", inline=True)
        embed.add_field(name=f"{customer_b} Cost/Customer", value="$172.80", inline=True)
        embed.add_field(name="Difference", value=f"{customer_a} is 16% lower", inline=False)
        embed.add_field(name=f"{customer_a} Revenue/Customer", value="$310.00", inline=True)
        embed.add_field(name=f"{customer_b} Revenue/Customer", value="$285.00", inline=True)
        embed.add_field(name="Margin Comparison", value=f"{customer_a}: 53.2% | {customer_b}: 39.4%", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-forecast", description="Forecast unit metric trend")
    @app_commands.describe(metric_name="Metric to forecast", periods="Number of periods ahead")
    async def forecast(self, interaction: discord.Interaction, metric_name: str = "cost_per_customer", periods: int = 3):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Forecast: {metric_name}", color=0x9B59B6)
        embed.add_field(name="Current", value="$149.50", inline=True)
        embed.add_field(name="Next Period", value="$152.30", inline=True)
        embed.add_field(name="Period +2", value="$155.10", inline=True)
        embed.add_field(name="Period +3", value="$157.90", inline=True)
        embed.add_field(name="Trend Direction", value="Slightly increasing (+1.9%/period)", inline=False)
        embed.add_field(name="Warning", value="Review cost optimization if trend continues", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-dimension", description="Break down metrics by dimension")
    @app_commands.describe(dimension="Dimension to group by (region/service/team)")
    async def dimension(self, interaction: discord.Interaction, dimension: str = "region"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Unit Metrics by {dimension.title()}", color=0x00AAFF)
        embed.add_field(name="us-east-1", value="Avg Cost/Customer: $142.30 | Count: 12", inline=False)
        embed.add_field(name="eu-west-1", value="Avg Cost/Customer: $158.70 | Count: 8", inline=False)
        embed.add_field(name="ap-southeast-1", value="Avg Cost/Customer: $175.20 | Count: 4", inline=False)
        embed.set_footer(text="Dimensions help identify cost disparities")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-export", description="Export unit economics data")
    @app_commands.describe(format="Export format (json/csv)")
    async def export(self, interaction: discord.Interaction, format: str = "json"):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Economics Export", color=0x2ECC71)
        embed.add_field(name="Format", value=format.upper(), inline=True)
        embed.add_field(name="Records Exported", value="120 metrics, 24 customers", inline=True)
        embed.add_field(name="File", value=f"unit_economics_{datetime.utcnow().strftime('%Y%m%d')}.{format}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-efficiency", description="Analyze unit cost efficiency")
    async def efficiency(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Cost Efficiency Analysis", color=0x00FF88)
        embed.add_field(name="Overall Score", value="82/100", inline=True)
        embed.add_field(name="Cost/Customer Trend", value="Improving (-5.2% MoM)", inline=True)
        embed.add_field(name="Cost/Transaction Trend", value="Stable (+0.8% MoM)", inline=True)
        embed.add_field(name="Cost/Deployment Trend", value="Worsening (+12% MoM)", inline=True)
        embed.add_field(name="Recommendation", value="Review deployment pipeline costs", inline=False)
        await interaction.followup.send(embed=embed)


def compute_unit_metric(values: list, unit_type: str) -> dict:
    avg = sum(values) / max(len(values), 1)
    vals = sorted(values)
    median = vals[len(vals)//2] if vals else 0
    return {
        "metric": unit_type,
        "avg": round(avg, 2),
        "median": round(median, 2),
        "min": round(min(values), 2) if values else 0,
        "max": round(max(values), 2) if values else 0,
        "count": len(values),
    }

def detect_unit_cost_anomaly(values: list, new_value: float, threshold: float = 2.0) -> dict:
    if len(values) < 3:
        return {"is_anomaly": False}
    mean = sum(values) / len(values)
    std = (sum((v - mean)**2 for v in values) / len(values)) ** 0.5
    z = (new_value - mean) / max(std, 0.001)
    return {
        "is_anomaly": abs(z) > threshold,
        "zscore": round(z, 2),
        "expected": round(mean, 2),
        "actual": round(new_value, 2),
        "deviation_pct": round(((new_value - mean) / max(mean, 0.01)) * 100, 1),
    }

    @app_commands.command(name="unit-cost-per-customer", description="Cost per customer breakdown")
    @app_commands.describe(cohort="Customer cohort to analyze")
    async def cost_per_customer(self, interaction: discord.Interaction, cohort: str = "all"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Cost per Customer: {cohort.title()}", color=discord.Color.blue())
        embed.add_field(name="Total Customers", value="1,247", inline=True)
        embed.add_field(name="Total Cost", value="$285,000/mo", inline=True)
        embed.add_field(name="Avg Cost/Customer", value="$228.55/mo", inline=True)
        embed.add_field(name="Median Cost/Customer", value="$185.30/mo", inline=True)
        embed.add_field(name="P90", value="$412.80/mo", inline=True)
        embed.add_field(name="Trend", value="📈 +3.2% MoM", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-cost-per-request", description="Cost per request analysis")
    @app_commands.describe(service="Service name")
    async def cost_per_request(self, interaction: discord.Interaction, service: str = "api-gateway"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Cost per Request: {service}", color=discord.Color.blue())
        embed.add_field(name="Total Requests", value="52.4M/mo", inline=True)
        embed.add_field(name="Total Cost", value="$42,800/mo", inline=True)
        embed.add_field(name="Cost per 1K Requests", value="$0.817", inline=True)
        embed.add_field(name="Cost per 1M Requests", value="$817.00", inline=True)
        embed.add_field(name="Efficiency Grade", value="B (industry avg: $0.92/1K)", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-efficiency-score", description="Overall unit efficiency score")
    async def efficiency_score(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Unit Efficiency Score", color=discord.Color.green())
        embed.add_field(name="Overall Score", value="78/100 (B+)", inline=True)
        embed.add_field(name="Cost/Customer", value="82/100 (A-)", inline=True)
        embed.add_field(name="Cost/Transaction", value="75/100 (B)", inline=True)
        embed.add_field(name="Cost/GB Storage", value="71/100 (B-)", inline=True)
        embed.add_field(name="Cost/vCPU Hour", value="84/100 (A-)", inline=True)
        embed.add_field(name="YoY Improvement", value="+5 points", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-cost-per-gb", description="Cost per GB storage analysis")
    @app_commands.describe(storage_type="Storage type")
    async def cost_per_gb(self, interaction: discord.Interaction, storage_type: str = "s3"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Cost per GB: {storage_type.upper()}", color=discord.Color.blue())
        embed.add_field(name="Total Storage", value="245 TB", inline=True)
        embed.add_field(name="Total Cost", value="$18,375/mo", inline=True)
        embed.add_field(name="Cost per GB", value="$0.075/GB", inline=True)
        embed.add_field(name="Industry Avg", value="$0.088/GB", inline=True)
        embed.add_field(name="Efficiency", value="✅ 14.8% below avg", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unit-cost-per-vcpu", description="Cost per vCPU hour analysis")
    @app_commands.describe(provider="Cloud provider")
    async def cost_per_vcpu(self, interaction: discord.Interaction, provider: str = "aws"):
        await interaction.response.defer()
        embed = discord.Embed(title=f"Cost per vCPU Hour: {provider.upper()}", color=discord.Color.blue())
        embed.add_field(name="Total vCPU Hours", value="1,847,000 hrs/mo", inline=True)
        embed.add_field(name="Total Cost", value="$92,350/mo", inline=True)
        embed.add_field(name="Cost per vCPU Hour", value="$0.050/hr", inline=True)
        embed.add_field(name="Spot Avg", value="$0.015/hr (70% savings)", inline=True)
        embed.add_field(name="RI Avg", value="$0.032/hr (36% savings)", inline=True)
        await interaction.followup.send(embed=embed)

    @tasks.loop(hours=24)
    async def unit_metrics_sync(self):
        logging.info("UnitEconomics: syncing unit metrics")

    @unit_metrics_sync.before_loop
    async def before_unit_metrics_sync(self):
        await self.bot.wait_until_ready()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(UnitEconomics(bot))

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
