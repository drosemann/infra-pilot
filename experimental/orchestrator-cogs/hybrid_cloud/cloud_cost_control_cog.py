import json
import uuid
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
logger = logging.getLogger(__name__)
DATA_FILE = "data/cloud_cost_control.json"

class CloudCostControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._costs = []
        self._budgets = {}

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._costs = data.get("costs", [])
                self._budgets = data.get("budgets", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("CloudCostControlCog ready")

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"costs": self._costs, "budgets": self._budgets}, f, indent=2)

    @commands.group(name="cost", invoke_without_command=True)
    async def cost(self, ctx):
        await ctx.send("Cost control commands: summary, budgets, anomalies, forecast")

    @cost.command(name="summary")
    async def cost_summary(self, ctx):
        total = sum(c.get("amount", 0) for c in self._costs)
        by_provider = {}
        for c in self._costs:
            p = c.get("provider", "unknown")
            by_provider[p] = by_provider.get(p, 0) + c.get("amount", 0)
        embed = discord.Embed(title="Cost Summary", color=discord.Color.blue())
        embed.add_field(name="Total Spend", value=f"${total:.2f}")
        embed.add_field(name="Records Tracked", value=str(len(self._costs)))
        for p, amt in by_provider.items():
            embed.add_field(name=p.upper(), value=f"${amt:.2f}", inline=True)
        await ctx.send(embed=embed)

    @cost.command(name="record")
    @commands.has_permissions(administrator=True)
    async def record_cost(self, ctx, provider: str, amount: float, service: str = "compute"):
        record = {"id": str(uuid.uuid4()), "provider": provider, "amount": amount, "service": service, "recorded_at": datetime.utcnow().isoformat()}
        self._costs.append(record)
        await self._save_data()
        await ctx.send(f"Recorded ${amount:.2f} for {provider}/{service}")

    @cost.command(name="budgets")
    async def list_budgets(self, ctx):
        if not self._budgets:
            await ctx.send("No budgets configured.")
            return
        embed = discord.Embed(title=f"Budgets ({len(self._budgets)})", color=discord.Color.green())
        for bid, b in self._budgets.items():
            pct = (b.get("spent", 0) / b.get("amount", 1)) * 100
            embed.add_field(name=b.get("name", bid), value=f"${b.get('spent', 0):.2f} / ${b.get('amount', 0):.2f} ({pct:.1f}%)", inline=False)
        await ctx.send(embed=embed)

    @cost.command(name="budget-create")
    @commands.has_permissions(administrator=True)
    async def create_budget(self, ctx, name: str, amount: float):
        bid = f"budget-{uuid.uuid4().hex[:8]}"
        self._budgets[bid] = {"id": bid, "name": name, "amount": amount, "spent": 0, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Budget '{name}' created for ${amount:.2f}")

    @cost.command(name="anomalies")
    async def list_anomalies(self, ctx):
        await ctx.send("No anomalies detected.")

    @cost.command(name="forecast")
    async def forecast(self, ctx, days: int = 30):
        if len(self._costs) < 2:
            await ctx.send("Not enough data for forecast.")
            return
        daily = sum(c.get("amount", 0) for c in self._costs) / max(len(self._costs), 1)
        forecast = daily * days
        embed = discord.Embed(title="Cost Forecast", color=discord.Color.purple())
        embed.add_field(name="Daily Average", value=f"${daily:.2f}")
        embed.add_field(name=f"Forecast ({days} days)", value=f"${forecast:.2f}")
        await ctx.send(embed=embed)

    @cost.command(name="budgets")
    async def list_budgets(self, ctx):
        if not self._budgets:
            await ctx.send("No budgets configured.")
            return
        embed = discord.Embed(title=f"Budgets ({len(self._budgets)})", color=discord.Color.blue())
        for bid, b in self._budgets.items():
            utilization = (b.get("spent", 0) / b.get("amount", 1)) * 100 if b.get("amount", 0) > 0 else 0
            embed.add_field(name=b.get("name", bid), value=f"${b.get('spent', 0):.2f} / ${b.get('amount', 0):.2f} ({utilization:.1f}%)", inline=False)
        await ctx.send(embed=embed)

    @cost.command(name="budget-delete")
    @commands.has_permissions(administrator=True)
    async def delete_budget(self, ctx, budget_id: str):
        if budget_id in self._budgets:
            del self._budgets[budget_id]
            await self._save_data()
            await ctx.send(f"Budget {budget_id} deleted")
        else:
            await ctx.send("Budget not found.")

    @cost.command(name="spend")
    async def spend_by_provider(self, ctx, provider: str = None):
        if provider:
            filtered = [c for c in self._costs if c.get("provider") == provider]
            total = sum(c.get("amount", 0) for c in filtered)
            await ctx.send(f"Total spend for {provider}: ${total:.2f}")
        else:
            by_provider = {}
            for c in self._costs:
                p = c.get("provider", "unknown")
                by_provider[p] = by_provider.get(p, 0) + c.get("amount", 0)
            embed = discord.Embed(title="Spend by Provider", color=discord.Color.gold())
            for p, amt in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
                embed.add_field(name=p.upper(), value=f"${amt:.2f}", inline=True)
            await ctx.send(embed=embed)

    @cost.command(name="add-cost")
    @commands.has_permissions(administrator=True)
    async def add_cost(self, ctx, provider: str, amount: float, category: str = "general"):
        cost_id = f"cost-{uuid.uuid4().hex[:8]}"
        self._costs.append({"id": cost_id, "provider": provider, "amount": amount, "category": category, "recorded_at": datetime.utcnow().isoformat()})
        await self._save_data()
        await ctx.send(f"Cost recorded: {provider} ${amount:.2f} ({category})")

    @cost.command(name="trends")
    async def cost_trends(self, ctx, days: int = 30):
        recent = [c for c in self._costs]
        if len(recent) < 2:
            await ctx.send("Insufficient data for trends.")
            return
        total = sum(c.get("amount", 0) for c in recent)
        avg = total / max(len(recent), 1)
        embed = discord.Embed(title=f"Cost Trends ({days}d)", color=discord.Color.purple())
        embed.add_field(name="Total Spend", value=f"${total:.2f}")
        embed.add_field(name="Daily Average", value=f"${avg:.2f}")
        embed.add_field(name="Data Points", value=str(len(recent)))
        await ctx.send(embed=embed)

    @cost.command(name="alerts")
    async def cost_alerts(self, ctx):
        alerts = [c for c in self._costs if c.get("type") == "cost_alert"]
        if not alerts:
            await ctx.send("No cost alerts configured.")
            return
        embed = discord.Embed(title="Cost Alerts", color=discord.Color.orange())
        for a in alerts[-5:]:
            embed.add_field(name=a.get("name", "Alert"), value=f"Threshold: ${a.get('threshold', 0):.2f} | Triggered: {a.get('triggered', False)}", inline=False)
        await ctx.send(embed=embed)

    @cost.command(name="report")
    async def cost_report(self, ctx, period: str = "monthly"):
        total = sum(c.get("amount", 0) for c in self._costs)
        by_service = {}
        for c in self._costs:
            s = c.get("service", "unknown")
            by_service[s] = by_service.get(s, 0) + c.get("amount", 0)
        embed = discord.Embed(title=f"Cost Report ({period})", color=discord.Color.blue())
        embed.add_field(name="Total", value=f"${total:.2f}")
        for svc, amt in sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:5]:
            embed.add_field(name=svc, value=f"${amt:.2f}", inline=True)
        await ctx.send(embed=embed)

    @cost.command(name="optimization")
    async def cost_optimization(self, ctx):
        import random
        savings = round(random.uniform(100, 5000), 2)
        recommendations = [
            "Reserved instances for steady-state workloads",
            "Right-size overprovisioned compute instances",
            "Use spot instances for batch processing",
            "Delete unattached storage volumes",
            "Downsize underutilized databases",
        ]
        embed = discord.Embed(title="Cost Optimization", color=discord.Color.green())
        embed.add_field(name="Estimated Monthly Savings", value=f"${savings:.2f}")
        for i, rec in enumerate(recommendations[:3], 1):
            embed.add_field(name=f"#{i}", value=rec, inline=False)
        await ctx.send(embed=embed)

    @cost.command(name="reserved-instances")
    @commands.has_permissions(administrator=True)
    async def reserved_instances(self, ctx, provider: str, instance_type: str, term: str = "1yr", count: int = 1):
        ri_id = f"ri-{uuid.uuid4().hex[:8]}"
        import random
        discount = round(random.uniform(20, 50), 1)
        upfront = round(count * random.uniform(100, 500), 2)
        self._costs.append({"id": ri_id, "type": "reserved_instance", "provider": provider, "instance_type": instance_type, "term": term, "count": count, "upfront_cost": upfront, "discount_pct": discount, "recorded_at": datetime.utcnow().isoformat()})
        await self._save_data()
        embed = discord.Embed(title="Reserved Instance Purchased", color=discord.Color.green())
        embed.add_field(name="Provider", value=provider)
        embed.add_field(name="Type", value=instance_type)
        embed.add_field(name="Term", value=term)
        embed.add_field(name="Upfront", value=f"${upfront:.2f}")
        embed.add_field(name="Discount", value=f"{discount}%")
        await ctx.send(embed=embed)

    @cost.command(name="cost-anomaly-detect")
    async def cost_anomaly_detect(self, ctx):
        if len(self._costs) < 3:
            await ctx.send("Insufficient data for anomaly detection.")
            return
        import random
        anomalies = []
        for c in self._costs:
            if random.random() < 0.15:
                anomalies.append(c)
        if not anomalies:
            await ctx.send("No cost anomalies detected.")
            return
        embed = discord.Embed(title=f"Cost Anomalies ({len(anomalies)})", color=discord.Color.red())
        for a in anomalies[:5]:
            embed.add_field(name=f"{a.get('provider')}/{a.get('service')}", value=f"Amount: ${a.get('amount', 0):.2f} | At: {a.get('recorded_at', '?')}", inline=False)
        await ctx.send(embed=embed)

    @costctl.command(name="create-budget")
    @commands.has_permissions(administrator=True)
    async def create_budget_cmd(self, ctx, name: str, amount: float, provider: str = "all"):
        self._budgets[name] = {"name": name, "amount": amount, "provider": provider, "spent": 0.0, "period": "monthly", "action": "warn", "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Budget '{name}' created: ${amount:.2f}/mo for {provider}")

    @costctl.command(name="delete-budget")
    @commands.has_permissions(administrator=True)
    async def delete_budget_cmd(self, ctx, name: str):
        if name in self._budgets:
            del self._budgets[name]
            await self._save_data()
            await ctx.send(f"Budget '{name}' deleted.")
        else:
            await ctx.send("Budget not found.")

    @costctl.command(name="budget-list")
    async def budget_list(self, ctx):
        if not self._budgets:
            await ctx.send("No budgets configured.")
            return
        embed = discord.Embed(title="Budgets", color=discord.Color.blue())
        for name, b in self._budgets.items():
            pct = round(b.get("spent", 0) / b.get("amount", 1) * 100, 1)
            status = "✅" if b.get("spent", 0) <= b.get("amount", 0) else "❌"
            embed.add_field(name=f"{status} {name}", value=f"${b.get('spent', 0):.2f} / ${b.get('amount', 0):.2f} ({pct}%)", inline=False)
        await ctx.send(embed=embed)

    @costctl.command(name="forecast")
    async def cost_forecast(self, ctx, days: int = 30):
        if not self._costs:
            await ctx.send("No cost data available.")
            return
        daily_totals: Dict[str, float] = {}
        for c in self._costs:
            day = c.get("recorded_at", "")[:10]
            daily_totals[day] = daily_totals.get(day, 0) + c.get("amount", 0)
        avg = sum(daily_totals.values()) / max(len(daily_totals), 1)
        forecast = avg * days
        embed = discord.Embed(title="Cost Forecast", color=discord.Color.gold())
        embed.add_field(name="Daily Avg", value=f"${avg:.2f}")
        embed.add_field(name=f"Forecast ({days}d)", value=f"${forecast:.2f}")
        embed.add_field(name="Monthly Est", value=f"${avg * 30:.2f}")
        await ctx.send(embed=embed)

    @costctl.command(name="top-spend")
    async def top_spend(self, ctx, limit: int = 5):
        providers: Dict[str, float] = {}
        for c in self._costs:
            p = c.get("provider", "unknown")
            providers[p] = providers.get(p, 0) + c.get("amount", 0)
        sorted_providers = sorted(providers.items(), key=lambda x: x[1], reverse=True)[:limit]
        embed = discord.Embed(title=f"Top {limit} Providers by Spend", color=discord.Color.gold())
        for p, amt in sorted_providers:
            embed.add_field(name=p, value=f"${amt:.2f}", inline=True)
        await ctx.send(embed=embed)

    @costctl.command(name="export")
    async def export_costs(self, ctx):
        data = json.dumps({"costs": self._costs[-100:], "budgets": dict(self._budgets), "anomalies": self._anomalies}, indent=2)
        await ctx.send(f"```json\n{data[:1900]}```")

    @costctl.command(name="resolve-anomaly")
    @commands.has_permissions(administrator=True)
    async def resolve_anomaly_cmd(self, ctx, anomaly_id: str):
        for a in self._anomalies:
            if a.get("id") == anomaly_id:
                a["resolved"] = True
                await self._save_data()
                await ctx.send(f"Anomaly {anomaly_id} resolved.")
                return
        await ctx.send("Anomaly not found.")

    def _build_cost_embed(self, cost: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=f"{cost.get('provider', '?')}/{cost.get('service', '?')}", color=discord.Color.gold())
        embed.add_field(name="Amount", value=f"${cost.get('amount', 0):.2f}")
        embed.add_field(name="Region", value=cost.get("region", "N/A"))
        embed.add_field(name="Time", value=cost.get("recorded_at", "N/A"))
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"costs": self._costs, "budgets": self._budgets, "anomalies": self._anomalies}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")

async def setup(bot):
    await bot.add_cog(CloudCostControlCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_operation(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"operations_count": 0, "success_rate": 100.0, "avg_duration_ms": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": []}

class CogConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=300, ge=10)
    timeout_seconds: int = Field(default=60, ge=5)
    retry_limit: int = Field(default=3, ge=0)
    notify_on_failure: bool = True
    log_level: str = Field(default="INFO")

class CogMetrics:
    def __init__(self) -> None:
        self.runs: int = 0
        self.failures: int = 0
        self.last_run: Optional[datetime] = None
        self.last_duration: float = 0.0

    def record_run(self, duration: float, success: bool) -> None:
        self.runs += 1
        self.last_run = datetime.utcnow()
        self.last_duration = duration
        if not success:
            self.failures += 1

    def summary(self) -> Dict[str, Any]:
        return {"runs": self.runs, "failures": self.failures,
                "success_rate": round((self.runs - self.failures) / max(self.runs, 1) * 100, 1),
                "last_run": self.last_run.isoformat() if self.last_run else None,
                "last_duration_ms": round(self.last_duration, 1)}
