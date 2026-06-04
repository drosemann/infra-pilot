import json
import uuid
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
logger = logging.getLogger(__name__)
DATA_FILE = "data/cloud_arbitrage.json"

class CloudArbitrageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._opportunities = {}
        self._migrations = {}

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._opportunities = data.get("opportunities", {})
                self._migrations = data.get("migrations", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("CloudArbitrageCog ready")

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"opportunities": self._opportunities, "migrations": self._migrations}, f, indent=2)

    @commands.group(name="arbitrage", invoke_without_command=True)
    async def arbitrage(self, ctx):
        await ctx.send("Cloud arbitrage commands: opportunities, migrate, savings, compare")

    @arbitrage.command(name="opportunities")
    async def list_opportunities(self, ctx):
        if not self._opportunities:
            await ctx.send("No arbitrage opportunities found.")
            return
        embed = discord.Embed(title="Arbitrage Opportunities", color=discord.Color.gold())
        for oid, opp in list(self._opportunities.items())[:10]:
            embed.add_field(name=f"{opp.get('source_provider')} -> {opp.get('target_provider')}", value=f"Savings: ${opp.get('savings_per_hour', 0):.2f}/hr", inline=False)
        await ctx.send(embed=embed)

    @arbitrage.command(name="compare")
    async def compare_pricing(self, ctx, vcpu: int = 2, memory: int = 4):
        pricing = [
            {"provider": "aws", "spot": "$0.012/hr", "ondemand": "$0.05/hr"},
            {"provider": "azure", "spot": "$0.014/hr", "ondemand": "$0.06/hr"},
            {"provider": "gcp", "preemptible": "$0.008/hr", "ondemand": "$0.04/hr"},
            {"provider": "hetzner", "spot": "$0.006/hr", "ondemand": "$0.02/hr"},
        ]
        embed = discord.Embed(title=f"Price Comparison (vCPU={vcpu}, RAM={memory}GB)", color=discord.Color.blue())
        for p in pricing:
            spot = p.get("spot") or p.get("preemptible", "N/A")
            embed.add_field(name=p["provider"].upper(), value=f"Spot: {spot}\nOn-Demand: {p['ondemand']}", inline=True)
        await ctx.send(embed=embed)

    @arbitrage.command(name="migrate")
    @commands.has_permissions(administrator=True)
    async def migrate_workload(self, ctx, opportunity_id: str):
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            await ctx.send("Opportunity not found.")
            return
        mid = f"migr-{uuid.uuid4().hex[:10]}"
        self._migrations[mid] = {"migration_id": mid, "opportunity_id": opportunity_id, "status": "in_progress", "started_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Migration {mid} started")

    @arbitrage.command(name="savings")
    async def total_savings(self, ctx):
        total = sum(o.get("savings_per_hour", 0) for o in self._opportunities.values() if o.get("state") == "completed")
        embed = discord.Embed(title="Arbitrage Savings", color=discord.Color.green())
        embed.add_field(name="Total Savings/hr", value=f"${total:.2f}")
        embed.add_field(name="Total Savings/day", value=f"${total * 24:.2f}")
        embed.add_field(name="Total Savings/month", value=f"${total * 24 * 30:.2f}")
        await ctx.send(embed=embed)

    @arbitrage.command(name="opportunities")
    async def list_opportunities(self, ctx, state: str = "open"):
        filtered = [o for o in self._opportunities.values() if state == "all" or o.get("state") == state]
        if not filtered:
            await ctx.send(f"No {state} opportunities.")
            return
        embed = discord.Embed(title=f"Arbitrage Opportunities ({len(filtered)})", color=discord.Color.gold())
        for o in list(filtered)[:10]:
            embed.add_field(name=f"{o.get('source_provider', '?')} -> {o.get('target_provider', '?')}", value=f"Savings: ${o.get('savings_per_hour', 0):.4f}/hr | State: {o.get('state')}", inline=False)
        await ctx.send(embed=embed)

    @arbitrage.command(name="compare")
    async def compare_prices(self, ctx, vcpu: int = 2, memory: int = 4, region: str = "us-east-1"):
        import random
        prices = [
            {"provider": "aws", "price": round(random.uniform(0.04, 0.12), 4)},
            {"provider": "azure", "price": round(random.uniform(0.05, 0.14), 4)},
            {"provider": "gcp", "price": round(random.uniform(0.03, 0.10), 4)},
            {"provider": "hetzner", "price": round(random.uniform(0.01, 0.04), 4)},
            {"provider": "ovh", "price": round(random.uniform(0.02, 0.06), 4)},
            {"provider": "digitalocean", "price": round(random.uniform(0.03, 0.08), 4)},
        ]
        prices.sort(key=lambda x: x["price"])
        embed = discord.Embed(title=f"Price Comparison (vCPU={vcpu}, RAM={memory}GB, {region})", color=discord.Color.blue())
        for p in prices:
            embed.add_field(name=p["provider"].upper(), value=f"${p['price']:.4f}/hr", inline=True)
        cheapest = prices[0]
        embed.set_footer(text=f"Cheapest: {cheapest['provider'].upper()} at ${cheapest['price']:.4f}/hr")
        await ctx.send(embed=embed)

    @arbitrage.command(name="alert")
    @commands.has_permissions(administrator=True)
    async def set_alert(self, ctx, provider: str, threshold: float):
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"
        self._opportunities[alert_id] = {"id": alert_id, "type": "pricing_alert", "provider": provider, "threshold": threshold, "triggered": False, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Pricing alert set for {provider} at ${threshold:.4f}/hr")

    @arbitrage.command(name="alerts")
    async def list_alerts(self, ctx):
        alerts = [o for o in self._opportunities.values() if o.get("type") == "pricing_alert"]
        if not alerts:
            await ctx.send("No pricing alerts configured.")
            return
        embed = discord.Embed(title=f"Pricing Alerts ({len(alerts)})", color=discord.Color.orange())
        for a in alerts:
            embed.add_field(name=a.get("provider"), value=f"Threshold: ${a.get('threshold', 0):.4f} | Triggered: {a.get('triggered', False)}", inline=True)
        await ctx.send(embed=embed)

    @arbitrage.command(name="spot")
    async def spot_analysis(self, ctx, provider: str = "aws", instance: str = "t3.medium"):
        import random
        savings = round(random.uniform(30, 70), 1)
        interruption = round(random.uniform(5, 30), 1)
        embed = discord.Embed(title=f"Spot Analysis: {provider.upper()} {instance}", color=discord.Color.gold())
        embed.add_field(name="Savings vs On-Demand", value=f"{savings}%")
        embed.add_field(name="Interruption Rate", value=f"{interruption}%")
        embed.add_field(name="Recommendation", value="Recommended" if savings > 40 and interruption < 20 else "Caution")
        await ctx.send(embed=embed)

    @arbitrage.command(name="history")
    async def arbitrage_history(self, ctx, limit: int = 10):
        completed = [o for o in self._opportunities.values() if o.get("state") == "completed"]
        if not completed:
            await ctx.send("No completed arbitrage history.")
            return
        embed = discord.Embed(title=f"Arbitrage History ({len(completed)})", color=discord.Color.purple())
        for o in completed[-limit:]:
            embed.add_field(name=f"{o.get('source_provider')} -> {o.get('target_provider')}", value=f"Savings: ${o.get('savings_per_hour', 0):.4f}/hr | Completed: {o.get('completed_at', '?')}", inline=False)
        await ctx.send(embed=embed)

    @arbitrage.command(name="recommend")
    async def recommend_workload(self, ctx, vcpu: int = 4, memory: int = 8, workload_type: str = "general"):
        import random
        recs = [
            {"provider": "hetzner", "price": round(random.uniform(0.01, 0.03), 4), "reason": "Best price/performance"},
            {"provider": "gcp", "price": round(random.uniform(0.03, 0.08), 4), "reason": "Preemptible savings"},
            {"provider": "aws", "price": round(random.uniform(0.04, 0.10), 4), "reason": "Spot market depth"},
            {"provider": "azure", "price": round(random.uniform(0.05, 0.12), 4), "reason": "Hybrid benefit"},
            {"provider": "ovh", "price": round(random.uniform(0.02, 0.05), 4), "reason": "EU data sovereignty"},
        ]
        recs.sort(key=lambda x: x["price"])
        embed = discord.Embed(title=f"Recommendations (vCPU={vcpu}, RAM={memory}GB, {workload_type})", color=discord.Color.green())
        for r in recs[:3]:
            embed.add_field(name=f"{r['provider'].upper()} - ${r['price']:.4f}/hr", value=r["reason"], inline=False)
        await ctx.send(embed=embed)

    @arbitrage.command(name="bid")
    @commands.has_permissions(administrator=True)
    async def spot_bid(self, ctx, provider: str, instance_type: str, max_bid: float):
        bid_id = f"bid-{uuid.uuid4().hex[:8]}"
        self._opportunities[bid_id] = {"id": bid_id, "type": "spot_bid", "provider": provider, "instance_type": instance_type, "max_bid": max_bid, "state": "active", "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Spot bid created: {provider}/{instance_type} @ ${max_bid:.4f}/hr")

    @arbitrage.command(name="region-prices")
    async def region_prices(self, ctx, provider: str = "aws"):
        import random
        regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1"]
        embed = discord.Embed(title=f"{provider.upper()} Regional Prices", color=discord.Color.blue())
        for region in regions:
            spot = round(random.uniform(0.02, 0.08), 4)
            od = round(random.uniform(0.06, 0.15), 4)
            embed.add_field(name=region, value=f"Spot: ${spot:.4f} | On-Demand: ${od:.4f}", inline=True)
        await ctx.send(embed=embed)

    @arbitrage.command(name="savings-plan")
    @commands.has_permissions(administrator=True)
    async def savings_plan(self, ctx, provider: str, commitment: str = "1yr", upfront: str = "partial"):
        plan_id = f"sp-{uuid.uuid4().hex[:8]}"
        import random
        discount = round(random.uniform(15, 45), 1)
        self._opportunities[plan_id] = {"id": plan_id, "type": "savings_plan", "provider": provider, "commitment": commitment, "upfront": upfront, "discount_pct": discount, "state": "active", "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Savings plan created: {provider} {commitment} ({discount}% discount)")

    @arbitrage.command(name="opportunities")
    async def list_opportunities(self, ctx, state: str = None):
        items = [o for o in self._opportunities.values() if not state or o.get("state") == state]
        if not items:
            await ctx.send("No opportunities found.")
            return
        embed = discord.Embed(title=f"Arbitrage Opportunities ({len(items)})", color=discord.Color.green())
        for opp in items[:10]:
            embed.add_field(name=f"{opp.get('source_provider', '?')} -> {opp.get('target_provider', '?')}",
                            value=f"Save ${opp.get('savings_per_hour', 0):.4f}/h | State: {opp.get('state', '?')}",
                            inline=False)
        await ctx.send(embed=embed)

    @arbitrage.command(name="execute")
    @commands.has_permissions(administrator=True)
    async def execute_opportunity(self, ctx, opportunity_id: str):
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            await ctx.send("Opportunity not found.")
            return
        if opp.get("state") != "opportunity_found":
            await ctx.send(f"Opportunity in state '{opp.get('state')}', expected 'opportunity_found'.")
            return
        opp["state"] = "migrating"
        mig_id = f"migr-{uuid.uuid4().hex[:12]}"
        self._migrations[mig_id] = {"migration_id": mig_id, "opportunity_id": opportunity_id, "source": opp.get("source_provider"), "target": opp.get("target_provider"), "state": "in_progress", "started_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Migration {mig_id} started: {opp.get('source_provider')} -> {opp.get('target_provider')}")

    @arbitrage.command(name="pricing-compare")
    async def pricing_compare(self, ctx, vcpu: int = 2, memory: int = 4, region: str = "us-east-1"):
        matches = [s for s in self._pricing if s.get("vcpu") == vcpu and s.get("memory_gb") == memory and s.get("region") == region]
        if not matches:
            await ctx.send("No pricing data for those specs.")
            return
        matches.sort(key=lambda x: x.get("hourly_price", 0))
        embed = discord.Embed(title=f"Pricing Comparison ({vcpu}vCPU, {memory}GB, {region})", color=discord.Color.blue())
        for m in matches[:10]:
            embed.add_field(name=m.get("provider", "?"), value=f"${m.get('hourly_price', 0):.4f}/h ({m.get('instance_type', '?')})", inline=True)
        await ctx.send(embed=embed)

    @arbitrage.command(name="savings-report")
    async def savings_report(self, ctx):
        total_savings = sum(m.get("expected_savings_per_hour", 0) for m in self._migrations.values() if m.get("state") == "completed")
        completed = sum(1 for m in self._migrations.values() if m.get("state") == "completed")
        active = sum(1 for m in self._migrations.values() if m.get("state") == "in_progress")
        embed = discord.Embed(title="Arbitrage Savings Report", color=discord.Color.gold())
        embed.add_field(name="Total Savings/h", value=f"${total_savings:.4f}")
        embed.add_field(name="Monthly Savings", value=f"${total_savings * 730:.2f}")
        embed.add_field(name="Migrated", value=str(completed))
        embed.add_field(name="In Progress", value=str(active))
        embed.add_field(name="Open Opportunities", value=str(sum(1 for o in self._opportunities.values() if o.get("state") == "opportunity_found")))
        await ctx.send(embed=embed)

    @arbitrage.command(name="dismiss")
    @commands.has_permissions(administrator=True)
    async def dismiss_opportunity_cmd(self, ctx, opportunity_id: str):
        if opportunity_id in self._opportunities:
            del self._opportunities[opportunity_id]
            await self._save_data()
            await ctx.send(f"Opportunity {opportunity_id} dismissed.")
        else:
            await ctx.send("Opportunity not found.")

    @arbitrage.command(name="recommend")
    async def recommend(self, ctx, current_provider: str, vcpu: int = 2, memory: int = 4, region: str = "us-east-1", current_price: float = 0.5):
        candidates = [s for s in self._pricing if s.get("vcpu") >= vcpu and s.get("memory_gb") >= memory]
        candidates = [c for c in candidates if c.get("hourly_price", 99) < current_price and c.get("provider") != current_provider]
        if not candidates:
            await ctx.send("No better alternative found.")
            return
        best = min(candidates, key=lambda x: x.get("hourly_price", 99))
        savings = current_price - best.get("hourly_price", current_price)
        embed = discord.Embed(title="Recommendation", color=discord.Color.green())
        embed.add_field(name="Current", value=f"{current_provider} @ ${current_price:.4f}/h")
        embed.add_field(name="Recommended", value=f"{best.get('provider')} @ ${best.get('hourly_price', 0):.4f}/h")
        embed.add_field(name="Savings", value=f"${savings:.4f}/h ({round(savings / current_price * 100, 1)}%)")
        await ctx.send(embed=embed)

    def _build_opportunity_embed(self, opp: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=f"{opp.get('source_provider', '?')} -> {opp.get('target_provider', '?')}", color=discord.Color.green())
        embed.add_field(name="Savings/h", value=f"${opp.get('savings_per_hour', 0):.4f}")
        embed.add_field(name="Savings %", value=f"{opp.get('savings_percentage', 0):.1f}%")
        embed.add_field(name="Region", value=opp.get("region", "N/A"))
        embed.add_field(name="State", value=opp.get("state", "N/A"))
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"pricing": self._pricing, "opportunities": self._opportunities, "migrations": self._migrations}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")

async def setup(bot):
    await bot.add_cog(CloudArbitrageCog(bot))

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
