"""Storage Tiering cog."""
import asyncio, datetime, logging, random
from typing import Any, Dict, List, Optional
from discord.ext import commands, tasks
logger = logging.getLogger(__name__)
TIERS = {"hot": {"name": "Hot Storage", "latency_ms": 1, "cost_per_gb": 0.023, "min_days": 0}, "warm": {"name": "Warm Storage", "latency_ms": 5, "cost_per_gb": 0.01, "min_days": 30}, "cold": {"name": "Cold Storage", "latency_ms": 50, "cost_per_gb": 0.004, "min_days": 90}, "glacier": {"name": "Glacier Deep Archive", "latency_ms": 3600000, "cost_per_gb": 0.00099, "min_days": 180}}
class DataTier:
    def __init__(self, tier_id: str, name: str, tier_type: str, size_gb: float = 0):
        self.tier_id = tier_id; self.name = name; self.tier_type = tier_type; self.size_gb = size_gb
        self.object_count = random.randint(100, 10000); self.last_accessed = datetime.datetime.utcnow().isoformat()
    def monthly_cost(self) -> float: return self.size_gb * TIERS.get(self.tier_type, TIERS["cold"])["cost_per_gb"]
    def to_dict(self) -> Dict[str, Any]:
        t = TIERS.get(self.tier_type, TIERS["cold"])
        return {"tier_id": self.tier_id, "name": self.name, "tier_type": self.tier_type, "size_gb": round(self.size_gb, 1), "object_count": self.object_count, "monthly_cost": round(self.monthly_cost(), 2), "latency_ms": t["latency_ms"], "cost_per_gb": t["cost_per_gb"], "last_accessed": self.last_accessed}

class StorageTiering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.tiers: Dict[str, DataTier] = {}
        self.tier_analysis_loop.start()
    def cog_unload(self): self.tier_analysis_loop.cancel()
    @tasks.loop(hours=1)
    async def tier_analysis_loop(self):
        logger.info("Running tier analysis...")
        for tid, tier in list(self.tiers.items()):
            if random.random() < 0.1 and tier.tier_type != "hot":
                logger.info(f"Tier {tier.name} has cold data - recommending migration")
    @commands.group(name="tier")
    async def tier_group(self, ctx): pass
    @tier_group.command(name="create")
    async def create_tier(self, ctx, name: str, tier_type: str = "hot", size_gb: float = 100):
        if tier_type not in TIERS: await ctx.send(f"Invalid tier type. Options: {', '.join(TIERS.keys())}"); return
        tid = f"tier-{random.randint(10000, 99999)}"
        self.tiers[tid] = DataTier(tier_id=tid, name=name, tier_type=tier_type, size_gb=size_gb)
        await ctx.send(f"? Created tier '{name}' ({tier_type}) - ${TIERS[tier_type]['cost_per_gb']}/GB")
    @tier_group.command(name="list")
    async def list_tiers(self, ctx):
        if not self.tiers: await ctx.send("No tiers configured"); return
        lines = ["**Storage Tiers:**"]
        for tid, t in self.tiers.items(): lines.append(f"• {t.name} ({t.tier_type}) - {t.size_gb}GB - ${t.monthly_cost():.2f}/mo")
        await ctx.send("\n".join(lines))
    @tier_group.command(name="move")
    async def move_to_tier(self, ctx, tier_id: str, target_type: str):
        t = self.tiers.get(tier_id)
        if not t: await ctx.send("Tier not found"); return
        if target_type not in TIERS: await ctx.send("Invalid target tier"); return
        old_cost = t.monthly_cost(); t.tier_type = target_type
        new_cost = t.monthly_cost(); savings = old_cost - new_cost
        await ctx.send(f"? Moved '{t.name}' to {target_type}. Savings: ${savings:.2f}/mo")
    @tier_group.command(name="analyze")
    async def analyze_costs(self, ctx):
        total = sum(t.monthly_cost() for t in self.tiers.values())
        lines = ["**Cost Analysis:**"]
        for t in self.tiers.values(): lines.append(f"• {t.name}: ${t.monthly_cost():.2f}/mo ({t.size_gb}GB @ ${TIERS[t.tier_type]['cost_per_gb']}/GB)")
        lines.append(f"**Total: ${total:.2f}/mo**"); await ctx.send("\n".join(lines))
    @tier_group.command(name="recommend")
    async def recommend_tier(self, ctx):
        usage_patterns = {"hot": 0.15, "warm": 0.35, "cold": 0.35, "glacier": 0.15}
        lines = ["**Tier Distribution Recommendation:**"]
        for ttype, pct in usage_patterns.items(): lines.append(f"• {TIERS[ttype]['name']}: {pct*100:.0f}% (${TIERS[ttype]['cost_per_gb']}/GB, {TIERS[ttype]['latency_ms']}ms latency)")
        current_total = sum(t.size_gb for t in self.tiers.values()); current_cost = sum(t.monthly_cost() for t in self.tiers.values())
        optimal_cost = sum(current_total * pct * TIERS[ttype]["cost_per_gb"] for ttype, pct in usage_patterns.items())
        lines.append(f"Current: ${current_cost:.2f}/mo ? Optimal: ${optimal_cost:.2f}/mo (save ${current_cost - optimal_cost:.2f}/mo)")
        await ctx.send("\n".join(lines))
    @tier_group.command(name="delete")
    async def delete_tier(self, ctx, tier_id: str):
        if tier_id in self.tiers: del self.tiers[tier_id]; await ctx.send(f"? Deleted tier")
        else: await ctx.send("Tier not found")
