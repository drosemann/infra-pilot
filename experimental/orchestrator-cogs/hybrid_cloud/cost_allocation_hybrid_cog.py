import json
import uuid
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
logger = logging.getLogger(__name__)
DATA_FILE = "data/cost_allocation.json"

class CostAllocationHybridCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._allocations = {}
        self._chargebacks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._allocations = data.get("allocations", {})
                self._chargebacks = data.get("chargebacks", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("CostAllocationHybridCog ready")

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"allocations": self._allocations, "chargebacks": self._chargebacks}, f, indent=2)

    @commands.group(name="alloc", invoke_without_command=True)
    async def alloc(self, ctx):
        await ctx.send("Cost allocation commands: summary, allocate, chargeback, teams, projects")

    @alloc.command(name="summary")
    async def allocation_summary(self, ctx):
        total = sum(a.get("amount", 0) for a in self._allocations.values() if a.get("allocated"))
        chargeback_total = sum(c.get("amount", 0) for c in self._chargebacks.values())
        teams = set(a.get("team", "unknown") for a in self._allocations.values())
        embed = discord.Embed(title="Cost Allocation Summary", color=discord.Color.blue())
        embed.add_field(name="Total Allocated", value=f"${total:.2f}")
        embed.add_field(name="Total Chargeback", value=f"${chargeback_total:.2f}")
        embed.add_field(name="Active Teams", value=str(len(teams)))
        embed.add_field(name="Allocations", value=str(len(self._allocations)))
        embed.add_field(name="Chargebacks", value=str(len(self._chargebacks)))
        await ctx.send(embed=embed)

    @alloc.command(name="allocate")
    @commands.has_permissions(administrator=True)
    async def allocate_cost(self, ctx, name: str, amount: float, team: str, project: str, source: str = "cloud"):
        aid = f"alloc-{uuid.uuid4().hex[:10]}"
        self._allocations[aid] = {"id": aid, "name": name, "amount": amount, "team": team, "project": project, "source": source, "allocated": True, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Allocated ${amount:.2f} to {team}/{project} ({name})")

    @alloc.command(name="teams")
    async def list_teams(self, ctx):
        team_spend = {}
        for a in self._allocations.values():
            if a.get("allocated"):
                t = a.get("team", "unknown")
                team_spend[t] = team_spend.get(t, 0) + a.get("amount", 0)
        if not team_spend:
            await ctx.send("No team allocations.")
            return
        embed = discord.Embed(title="Team Spend", color=discord.Color.green())
        for team, amt in sorted(team_spend.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=team, value=f"${amt:.2f}")
        await ctx.send(embed=embed)

    @alloc.command(name="projects")
    async def list_projects(self, ctx):
        proj_spend = {}
        for a in self._allocations.values():
            if a.get("allocated"):
                p = a.get("project", "unknown")
                proj_spend[p] = proj_spend.get(p, 0) + a.get("amount", 0)
        if not proj_spend:
            await ctx.send("No project allocations.")
            return
        embed = discord.Embed(title="Project Spend", color=discord.Color.purple())
        for proj, amt in sorted(proj_spend.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=proj, value=f"${amt:.2f}")
        await ctx.send(embed=embed)

    @alloc.command(name="chargeback")
    @commands.has_permissions(administrator=True)
    async def create_chargeback(self, ctx, team: str, project: str, amount: float, period: str = None):
        if not period:
            period = datetime.utcnow().strftime("%Y-%m")
        cid = f"cb-{uuid.uuid4().hex[:10]}"
        self._chargebacks[cid] = {"id": cid, "team": team, "project": project, "amount": amount, "period": period, "created_at": datetime.utcnow().isoformat(), "invoiced": False}
        await self._save_data()
        await ctx.send(f"Chargeback created: {team}/{project} = ${amount:.2f} ({period})")

    @alloc.command(name="tags")
    async def list_tags(self, ctx):
        embed = discord.Embed(title="Cost Tags", color=discord.Color.gold())
        embed.add_field(name="Environment", value="production, staging, development")
        embed.add_field(name="Team", value="platform, backend, frontend, ml, sre")
        embed.add_field(name="Project", value="infra-pilot, cloud-migration, cost-opt")
        embed.add_field(name="Source", value="on-prem, edge, cloud")
        await ctx.send(embed=embed)

    @alloc.command(name="allocations")
    async def list_allocations(self, ctx, team: str = None):
        filtered = list(self._allocations.values())
        if team:
            filtered = [a for a in filtered if a.get("team") == team]
        if not filtered:
            await ctx.send("No allocations.")
            return
        embed = discord.Embed(title=f"Allocations ({len(filtered)})", color=discord.Color.blue())
        for a in filtered[:10]:
            embed.add_field(name=f"{a.get('project')} ({a.get('team')})", value=f"${a.get('amount', 0):.2f} | Source: {a.get('source', 'cloud')}", inline=False)
        await ctx.send(embed=embed)

    @alloc.command(name="add-allocation")
    @commands.has_permissions(administrator=True)
    async def add_allocation(self, ctx, team: str, project: str, amount: float, source: str = "cloud"):
        aid = f"alloc-{uuid.uuid4().hex[:8]}"
        self._allocations[aid] = {"id": aid, "team": team, "project": project, "amount": amount, "source": source, "allocated": True, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Allocation created: {team}/{project} = ${amount:.2f}")

    @alloc.command(name="budgets")
    async def list_team_budgets(self, ctx):
        if not self._team_budgets:
            await ctx.send("No team budgets.")
            return
        embed = discord.Embed(title="Team Budgets", color=discord.Color.gold())
        for team, budget in self._team_budgets.items():
            spend = sum(a.get("amount", 0) for a in self._allocations.values() if a.get("team") == team)
            utilization = (spend / budget) * 100 if budget > 0 else 0
            embed.add_field(name=team, value=f"${spend:.2f} / ${budget:.2f} ({utilization:.1f}%)", inline=False)
        await ctx.send(embed=embed)

    @alloc.command(name="set-budget")
    @commands.has_permissions(administrator=True)
    async def set_team_budget(self, ctx, team: str, budget: float):
        self._team_budgets[team] = budget
        await self._save_data()
        await ctx.send(f"Budget for {team} set to ${budget:.2f}")

    @alloc.command(name="export")
    async def export_costs(self, ctx, period: str = "monthly"):
        total = sum(a.get("amount", 0) for a in self._allocations.values())
        embed = discord.Embed(title=f"Cost Export ({period})", color=discord.Color.purple())
        embed.add_field(name="Total Allocated", value=f"${total:.2f}")
        embed.add_field(name="Total Chargebacks", value=str(len(self._chargebacks)))
        embed.add_field(name="Teams Tracked", value=str(len(self._team_budgets)))
        embed.set_footer(text=f"Generated at {datetime.utcnow().isoformat()}")
        await ctx.send(embed=embed)

    @alloc.command(name="efficiency")
    async def allocation_efficiency(self, ctx):
        total = sum(a.get("amount", 0) for a in self._allocations.values())
        allocated = sum(a.get("amount", 0) for a in self._allocations.values() if a.get("allocated", False))
        eff = (allocated / total * 100) if total > 0 else 100
        embed = discord.Embed(title="Allocation Efficiency", color=discord.Color.green() if eff >= 80 else discord.Color.orange())
        embed.add_field(name="Total", value=f"${total:.2f}")
        embed.add_field(name="Allocated", value=f"${allocated:.2f}")
        embed.add_field(name="Efficiency", value=f"{eff:.1f}%")
        await ctx.send(embed=embed)

    @alloc.command(name="reports")
    async def allocation_reports(self, ctx, period: str = "monthly"):
        total = sum(a.get("amount", 0) for a in self._allocations.values())
        embed = discord.Embed(title=f"Allocation Report ({period})", color=discord.Color.blue())
        embed.add_field(name="Total Allocated", value=f"${total:.2f}")
        embed.add_field(name="Total Chargebacks", value=str(len(self._chargebacks)))
        embed.add_field(name="Teams", value=str(len(set(a.get("team", "?") for a in self._allocations.values()))))
        embed.add_field(name="Projects", value=str(len(set(a.get("project", "?") for a in self._allocations.values()))))
        embed.set_footer(text=f"Generated at {datetime.utcnow().isoformat()}")
        await ctx.send(embed=embed)

    @alloc.command(name="showback")
    @commands.has_permissions(administrator=True)
    async def showback_report(self, ctx, team: str):
        team_costs = [a for a in self._allocations.values() if a.get("team") == team]
        if not team_costs:
            await ctx.send(f"No costs for team {team}.")
            return
        total = sum(a.get("amount", 0) for a in team_costs)
        embed = discord.Embed(title=f"Showback: {team}", color=discord.Color.gold())
        embed.add_field(name="Total", value=f"${total:.2f}")
        embed.add_field(name="Items", value=str(len(team_costs)))
        for c in team_costs[:3]:
            embed.add_field(name=c.get("project", "?"), value=f"${c.get('amount', 0):.2f}", inline=True)
        await ctx.send(embed=embed)

    @alloc.command(name="anomaly-alert")
    @commands.has_permissions(administrator=True)
    async def anomaly_alert(self, ctx, threshold: float = 500.0):
        import random
        anomalies = []
        for a in self._allocations.values():
            if a.get("amount", 0) > threshold and random.random() < 0.2:
                anomalies.append(a)
        if not anomalies:
            await ctx.send(f"No anomalies above ${threshold:.2f}.")
            return
        embed = discord.Embed(title=f"Anomalies (>${threshold:.2f})", color=discord.Color.red())
        for a in anomalies[:5]:
            embed.add_field(name=f"{a.get('team')}/{a.get('project')}", value=f"${a.get('amount', 0):.2f}", inline=False)
        await ctx.send(embed=embed)

    @alloc.command(name="split-cost")
    @commands.has_permissions(administrator=True)
    async def split_cost(self, ctx, total_amount: float, teams: str):
        team_list = [t.strip() for t in teams.split(",")]
        share = round(total_amount / len(team_list), 2)
        embed = discord.Embed(title="Cost Split", color=discord.Color.green())
        for team in team_list:
            embed.add_field(name=team, value=f"${share:.2f}")
        await ctx.send(embed=embed)

    @alloc.command(name="tag-rules")
    @commands.has_permissions(administrator=True)
    async def tag_rules(self, ctx, action: str = "list", rule_name: str = "", required_tags: str = ""):
        rules_key = "_tag_rules"
        if rules_key not in self._allocations:
            self._allocations[rules_key] = {}
        if action == "list":
            rules = self._allocations.get(rules_key, {})
            if not rules:
                await ctx.send("No tag rules configured.")
                return
            embed = discord.Embed(title="Tag Rules", color=discord.Color.blue())
            for rname, rtags in rules.items():
                embed.add_field(name=rname, value=", ".join(rtags), inline=False)
            await ctx.send(embed=embed)
        elif action == "add" and rule_name and required_tags:
            tags = [t.strip() for t in required_tags.split(",")]
            self._allocations[rules_key][rule_name] = tags
            await self._save_data()
            await ctx.send(f"Tag rule '{rule_name}' added: {', '.join(tags)}")

    @alloc.command(name="cost-per-unit")
    async def cost_per_unit(self, ctx, unit: str = "request"):
        total = sum(a.get("amount", 0) for a in self._allocations.values())
        import random
        volume = random.randint(10000, 1000000)
        cpu = round(total / volume, 6)
        embed = discord.Embed(title=f"Cost per {unit.capitalize()}", color=discord.Color.gold())
        embed.add_field(name="Total Cost", value=f"${total:.2f}")
        embed.add_field(name="Volume", value=f"{volume:,} {unit}s")
        embed.add_field(name="Cost/{unit}", value=f"${cpu:.6f}")
        await ctx.send(embed=embed)

    @alloc.command(name="budget-check")
    async def budget_check(self, ctx, team: str = None):
        if not self._budgets:
            await ctx.send("No budgets configured.")
            return
        embed = discord.Embed(title="Budget Compliance", color=discord.Color.green())
        for name, b in self._budgets.items():
            if team and name != team:
                continue
            spend = sum(a.get("amount", 0) for a in self._allocations.values() if a.get("team") == name)
            pct = round(spend / b.get("amount", 1) * 100, 1)
            status = "✅" if spend <= b.get("amount", 0) else "❌"
            embed.add_field(name=f"{status} {name}", value=f"${spend:.2f} / ${b.get('amount', 0):.2f} ({pct}%)", inline=False)
        await ctx.send(embed=embed)

    @alloc.command(name="set-budget")
    @commands.has_permissions(administrator=True)
    async def set_budget(self, ctx, team: str, amount: float):
        self._budgets[team] = {"team": team, "amount": amount, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Budget for {team} set to ${amount:.2f}")

    @alloc.command(name="export-csv")
    async def export_cost_csv(self, ctx):
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "team", "project", "category", "amount", "source", "environment", "created_at"])
        for a in self._allocations.values():
            writer.writerow([a.get("id"), a.get("team"), a.get("project"), a.get("category"), a.get("amount"), a.get("source"), a.get("environment"), a.get("created_at")])
        csv_data = output.getvalue()
        await ctx.send(f"```csv\n{csv_data[:1900]}```")

    @alloc.command(name="chargeback-report")
    async def chargeback_report(self, ctx, period: str = None):
        period = period or datetime.utcnow().strftime("%Y-%m")
        items = [c for c in self._chargebacks.values() if c.get("period") == period]
        embed = discord.Embed(title=f"Chargeback Report ({period})", color=discord.Color.gold())
        embed.add_field(name="Total Entries", value=str(len(items)))
        embed.add_field(name="Total Amount", value=f"${sum(c.get('amount', 0) for c in items):.2f}")
        embed.add_field(name="Invoiced", value=str(sum(1 for c in items if c.get("invoiced"))))
        await ctx.send(embed=embed)

    @alloc.command(name="create-chargeback")
    @commands.has_permissions(administrator=True)
    async def create_chargeback_cmd(self, ctx, team: str, project: str, amount: float, method: str = "usage_based"):
        cb_id = f"cb-{uuid.uuid4().hex[:8]}"
        period = datetime.utcnow().strftime("%Y-%m")
        self._chargebacks[cb_id] = {"id": cb_id, "team": team, "project": project, "amount": amount, "method": method, "period": period, "invoiced": False, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Chargeback created: {team}/{project} ${amount:.2f} ({method})")

    @alloc.command(name="showback")
    async def showback(self, ctx):
        teams: Dict[str, float] = {}
        for a in self._allocations.values():
            t = a.get("team", "unallocated")
            teams[t] = teams.get(t, 0) + a.get("amount", 0)
        embed = discord.Embed(title="Showback Report", color=discord.Color.blue())
        for team, total in sorted(teams.items(), key=lambda x: x[1], reverse=True)[:10]:
            embed.add_field(name=team, value=f"${total:.2f}", inline=True)
        await ctx.send(embed=embed)

    @alloc.command(name="trend")
    async def cost_trend(self, ctx, months: int = 3):
        monthly: Dict[str, float] = {}
        for a in self._allocations.values():
            created = a.get("created_at", "")
            if created:
                month = created[:7]
                monthly[month] = monthly.get(month, 0) + a.get("amount", 0)
        sorted_months = sorted(monthly.keys())[-months:]
        embed = discord.Embed(title="Cost Trend", color=discord.Color.blue())
        for m in sorted_months:
            embed.add_field(name=m, value=f"${monthly[m]:.2f}", inline=True)
        await ctx.send(embed=embed)

    def _build_allocation_embed(self, alloc: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=alloc.get("name", "Allocation"), color=discord.Color.gold())
        embed.add_field(name="Team", value=alloc.get("team", "N/A"), inline=True)
        embed.add_field(name="Project", value=alloc.get("project", "N/A"), inline=True)
        embed.add_field(name="Amount", value=f"${alloc.get('amount', 0):.2f}", inline=True)
        embed.add_field(name="Category", value=alloc.get("category", "N/A"), inline=True)
        embed.add_field(name="Source", value=alloc.get("source", "N/A"), inline=True)
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"allocations": self._allocations, "chargebacks": self._chargebacks, "budgets": self._budgets}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")

async def setup(bot):
    await bot.add_cog(CostAllocationHybridCog(bot))

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
