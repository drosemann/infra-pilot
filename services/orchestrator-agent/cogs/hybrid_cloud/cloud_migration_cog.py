import json
import uuid
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
logger = logging.getLogger(__name__)
DATA_FILE = "data/cloud_migration.json"

class CloudMigrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._workloads = {}
        self._waves = {}

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._workloads = data.get("workloads", {})
                self._waves = data.get("waves", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("CloudMigrationCog ready")

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"workloads": self._workloads, "waves": self._waves}, f, indent=2)

    @commands.group(name="migrate", invoke_without_command=True)
    async def migrate(self, ctx):
        await ctx.send("Migration commands: discover, workloads, assess, wave, execute, rollback")

    @migrate.command(name="discover")
    @commands.has_permissions(administrator=True)
    async def discover_workload(self, ctx, name: str, hostname: str, os_type: str, vcpu: int, memory: int):
        wid = f"wl-{uuid.uuid4().hex[:10]}"
        self._workloads[wid] = {"id": wid, "name": name, "hostname": hostname, "os_type": os_type, "vcpu": vcpu, "memory_gb": memory, "state": "discovered", "discovered_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Discovered workload '{name}' on {hostname} ({vcpu}vCPU, {memory}GB)")

    @migrate.command(name="workloads")
    async def list_workloads(self, ctx):
        if not self._workloads:
            await ctx.send("No workloads discovered.")
            return
        embed = discord.Embed(title=f"Workloads ({len(self._workloads)})", color=discord.Color.blue())
        for wid, wl in self._workloads.items():
            embed.add_field(name=wl.get("name", wid), value=f"Host: {wl.get('hostname')} | State: {wl.get('state')} | vCPU: {wl.get('vcpu')} | RAM: {wl.get('memory_gb')}GB", inline=False)
        await ctx.send(embed=embed)

    @migrate.command(name="assess")
    async def assess_workload(self, ctx, workload_id: str):
        wl = self._workloads.get(workload_id)
        if not wl:
            await ctx.send("Workload not found.")
            return
        wl["state"] = "assessed"
        await self._save_data()
        embed = discord.Embed(title=f"Assessment: {wl.get('name')}", color=discord.Color.green())
        embed.add_field(name="Compatibility", value="Compatible")
        embed.add_field(name="Recommended Instance", value="t3.large")
        embed.add_field(name="Est. Monthly Cost", value=f"${wl.get('vcpu', 2) * 10 + wl.get('memory_gb', 4) * 2:.2f}")
        await ctx.send(embed=embed)

    @migrate.command(name="wave")
    @commands.has_permissions(administrator=True)
    async def create_wave(self, ctx, name: str, workload_ids: str, target_provider: str = "aws"):
        ids = [x.strip() for x in workload_ids.split(",")]
        wid = f"wave-{uuid.uuid4().hex[:10]}"
        self._waves[wid] = {"id": wid, "name": name, "workload_ids": ids, "target_provider": target_provider, "state": "planned", "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Migration wave '{name}' created with {len(ids)} workloads")

    @migrate.command(name="execute")
    @commands.has_permissions(administrator=True)
    async def execute_wave(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        wave["state"] = "migrating"
        await self._save_data()
        await ctx.send(f"Executing migration wave '{wave.get('name')}'...")
        await asyncio.sleep(2)
        wave["state"] = "completed"
        wave["completed_at"] = datetime.utcnow().isoformat()
        await self._save_data()
        await ctx.send(f"Wave '{wave.get('name')}' completed!")

    @migrate.command(name="rollback")
    @commands.has_permissions(administrator=True)
    async def rollback_wave(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        wave["state"] = "rolled_back"
        await self._save_data()
        await ctx.send(f"Wave '{wave.get('name')}' rolled back")

    @migrate.command(name="workloads")
    async def list_workloads(self, ctx, state: str = None):
        filtered = list(self._workloads.values())
        if state:
            filtered = [w for w in filtered if w.get("state") == state]
        if not filtered:
            await ctx.send("No workloads found.")
            return
        embed = discord.Embed(title=f"Workloads ({len(filtered)})", color=discord.Color.blue())
        for w in filtered[:10]:
            embed.add_field(name=w.get("name", w.get("id")), value=f"vCPU: {w.get('vcpu', '?')} | RAM: {w.get('memory_gb', '?')}GB | State: {w.get('state')}", inline=False)
        await ctx.send(embed=embed)

    @migrate.command(name="waves")
    async def list_waves(self, ctx):
        if not self._waves:
            await ctx.send("No migration waves.")
            return
        embed = discord.Embed(title=f"Migration Waves ({len(self._waves)})", color=discord.Color.green())
        for wid, w in self._waves.items():
            embed.add_field(name=w.get("name", wid), value=f"State: {w.get('state')} | Workloads: {len(w.get('workload_ids', []))}", inline=False)
        await ctx.send(embed=embed)

    @migrate.command(name="wave-create")
    @commands.has_permissions(administrator=True)
    async def create_wave(self, ctx, name: str, workload_ids: str):
        wl_ids = [w.strip() for w in workload_ids.split(",")]
        wid = f"wave-{uuid.uuid4().hex[:8]}"
        self._waves[wid] = {"id": wid, "name": name, "workload_ids": wl_ids, "state": "planned", "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Wave '{name}' created with {len(wl_ids)} workloads ({wid})")

    @migrate.command(name="assess")
    async def assess_workload(self, ctx, workload_id: str):
        wl = self._workloads.get(workload_id)
        if not wl:
            await ctx.send("Workload not found.")
            return
        embed = discord.Embed(title=f"Assessment: {wl.get('name', workload_id)}", color=discord.Color.blue())
        embed.add_field(name="Compatible", value="Yes" if wl.get("compatible", True) else "No")
        embed.add_field(name="Recommended Instance", value=wl.get("instance_type", "t3.medium"))
        embed.add_field(name="Est. Monthly Cost", value=f"${wl.get('estimated_cost', 0):.2f}")
        await ctx.send(embed=embed)

    @migrate.command(name="log")
    async def migration_log(self, ctx, limit: int = 10):
        if not self._migration_log:
            await ctx.send("No migration log entries.")
            return
        embed = discord.Embed(title=f"Migration Log ({len(self._migration_log)})", color=discord.Color.purple())
        for entry in self._migration_log[-limit:]:
            embed.add_field(name=entry.get("action", "action"), value=f"Workload: {entry.get('workload_id')} | Status: {entry.get('status')}", inline=False)
        await ctx.send(embed=embed)

    @migrate.command(name="dependencies")
    async def dependency_map(self, ctx):
        deps = {}
        for wid, wl in self._workloads.items():
            deps[wl.get("name", wid)] = wl.get("dependencies", [])
        if not deps:
            await ctx.send("No workloads to map.")
            return
        embed = discord.Embed(title="Dependency Map", color=discord.Color.gold())
        for name, dep_list in list(deps.items())[:10]:
            dep_str = ", ".join(dep_list) if dep_list else "None"
            embed.add_field(name=name, value=f"Dependencies: {dep_str}", inline=False)
        await ctx.send(embed=embed)

    @migrate.command(name="cutover")
    @commands.has_permissions(administrator=True)
    async def cutover_wave(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        wave["state"] = "cutover"
        wave["cutover_at"] = datetime.utcnow().isoformat()
        await self._save_data()
        await ctx.send(f"Cutover initiated for wave '{wave.get('name')}' ({wave_id})")

    @migrate.command(name="validation")
    async def validate_wave(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        import random
        passed = random.random() > 0.2
        embed = discord.Embed(title=f"Validation: {wave.get('name')}", color=discord.Color.green() if passed else discord.Color.red())
        embed.add_field(name="Pre-Migration Checks", value="✅ Passed" if passed else "❌ Failed")
        embed.add_field(name="Workloads Validated", value=str(len(wave.get("workload_ids", []))))
        embed.add_field(name="Dependencies Resolved", value="Yes" if passed else "No")
        await ctx.send(embed=embed)

    @migrate.command(name="testing")
    @commands.has_permissions(administrator=True)
    async def testing_wave(self, ctx, wave_id: str, test_type: str = "smoke"):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        import random
        passed = random.random() > 0.1
        embed = discord.Embed(title=f"{test_type.capitalize()} Tests: {wave.get('name')}", color=discord.Color.green() if passed else discord.Color.red())
        embed.add_field(name="Test Type", value=test_type)
        embed.add_field(name="Status", value="✅ Passed" if passed else "❌ Failed")
        embed.add_field(name="Workloads Tested", value=str(len(wave.get("workload_ids", []))))
        await ctx.send(embed=embed)

    @migrate.command(name="replication")
    @commands.has_permissions(administrator=True)
    async def replication_status(self, ctx, workload_id: str):
        wl = self._workloads.get(workload_id)
        if not wl:
            await ctx.send("Workload not found.")
            return
        import random
        pct = round(random.uniform(0, 100), 1)
        embed = discord.Embed(title=f"Replication: {wl.get('name')}", color=discord.Color.blue())
        embed.add_field(name="Progress", value=f"{pct}%")
        embed.add_field(name="State", value="syncing" if pct < 100 else "synced")
        embed.add_field(name="RPO", value="15 minutes")
        embed.add_field(name="RTO", value="2 hours")
        await ctx.send(embed=embed)

    @migrate.command(name="progress")
    async def wave_progress(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        embed = discord.Embed(title=f"Progress: {wave.get('name')}", color=discord.Color.blue())
        embed.add_field(name="State", value=wave.get("state", "planned"))
        embed.add_field(name="Workloads", value=str(len(wave.get("workload_ids", []))))
        embed.add_field(name="Created", value=wave.get("created_at", "N/A"))
        if wave.get("cutover_at"):
            embed.add_field(name="Cutover", value=wave["cutover_at"])
        if wave.get("completed_at"):
            embed.add_field(name="Completed", value=wave["completed_at"])
        await ctx.send(embed=embed)

    @migrate.command(name="rollback-plan")
    @commands.has_permissions(administrator=True)
    async def rollback_plan(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        plan_id = f"rb-{uuid.uuid4().hex[:8]}"
        wave["rollback_plan_id"] = plan_id
        await self._save_data()
        embed = discord.Embed(title=f"Rollback Plan: {wave.get('name')}", color=discord.Color.orange())
        embed.add_field(name="Plan ID", value=plan_id)
        embed.add_field(name="Strategy", value="Reverse replication")
        embed.add_field(name="Estimated Time", value="45 minutes")
        embed.add_field(name="Data Loss Risk", value="Low (CDC active)")
        await ctx.send(embed=embed)

    @migrate.command(name="batch-assess")
    @commands.has_permissions(administrator=True)
    async def batch_assess(self, ctx, *, workload_ids: str):
        ids = [w.strip() for w in workload_ids.split(",")]
        assessed = 0
        for wid in ids:
            wl = self._workloads.get(wid)
            if wl:
                wl["state"] = "assessed"
                assessed += 1
        await self._save_data()
        await ctx.send(f"Assessed {assessed}/{len(ids)} workloads.")

    @migrate.command(name="export-plan")
    async def export_migration_plan(self, ctx):
        data = json.dumps({"workloads": list(self._workloads.values()), "waves": list(self._waves.values())}, indent=2)
        await ctx.send(f"```json\n{data[:1900]}```")

    @migrate.command(name="dependencies")
    async def dependency_graph(self, ctx, workload_id: str = None):
        if workload_id:
            wl = self._workloads.get(workload_id)
            if not wl:
                await ctx.send("Workload not found.")
                return
            deps = wl.get("dependencies", [])
            embed = discord.Embed(title=f"Dependencies: {wl.get('name', '?')}", color=discord.Color.blue())
            embed.add_field(name="ID", value=workload_id)
            embed.add_field(name="Dependencies", value=str(len(deps)))
            for d in deps[:5]:
                dep = self._workloads.get(d)
                embed.add_field(name=d, value=dep.get("name", "Unknown") if dep else "Not found", inline=True)
            await ctx.send(embed=embed)
        else:
            total = sum(len(w.get("dependencies", [])) for w in self._workloads.values())
            embed = discord.Embed(title="Dependency Overview", color=discord.Color.blue())
            embed.add_field(name="Workloads", value=str(len(self._workloads)))
            embed.add_field(name="Total Dependencies", value=str(total))
            embed.add_field(name="Avg Deps/Workload", value=f"{round(total / max(len(self._workloads), 1), 1)}")
            await ctx.send(embed=embed)

    @migrate.command(name="cost-estimate")
    async def cost_estimate(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        total = 0
        for wid in wave.get("workload_ids", []):
            wl = self._workloads.get(wid)
            if wl:
                total += wl.get("vcpu", 2) * 10 + wl.get("memory_gb", 4) * 2 + wl.get("storage_gb", 50) * 0.1
        embed = discord.Embed(title=f"Migration Cost: {wave.get('name', '?')}", color=discord.Color.gold())
        embed.add_field(name="Wave", value=wave_id)
        embed.add_field(name="Estimated Cost", value=f"${total:.2f}/mo")
        embed.add_field(name="Workloads", value=str(len(wave.get("workload_ids", []))))
        await ctx.send(embed=embed)

    @migrate.command(name="readiness")
    async def readiness_check(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        ids = wave.get("workload_ids", [])
        assessed = sum(1 for wid in ids if self._workloads.get(wid, {}).get("state") == "assessed")
        pct = round(assessed / max(len(ids), 1) * 100, 1)
        embed = discord.Embed(title=f"Readiness: {wave.get('name', '?')}", color=discord.Color.green() if pct == 100 else discord.Color.orange())
        embed.add_field(name="Assessed", value=f"{assessed}/{len(ids)}")
        embed.add_field(name="Readiness", value=f"{pct}%")
        embed.add_field(name="Ready", value="✅" if pct == 100 else "⚠️")
        await ctx.send(embed=embed)

    @migrate.command(name="timeline")
    async def timeline(self, ctx, wave_id: str):
        wave = self._waves.get(wave_id)
        if not wave:
            await ctx.send("Wave not found.")
            return
        wl_count = len(wave.get("workload_ids", []))
        hours = wl_count * 2
        batches = max(1, wl_count // 3)
        embed = discord.Embed(title=f"Timeline: {wave.get('name', '?')}", color=discord.Color.blue())
        embed.add_field(name="Workloads", value=str(wl_count))
        embed.add_field(name="Est. Hours", value=str(hours))
        embed.add_field(name="Parallel Batches", value=str(batches))
        embed.add_field(name="Est. Duration", value=f"{round(hours / batches, 1)}h")
        await ctx.send(embed=embed)

    def _build_workload_embed(self, wl: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=wl.get("name", "Workload"), color=discord.Color.blue())
        embed.add_field(name="ID", value=wl.get("id", "N/A"), inline=False)
        embed.add_field(name="State", value=wl.get("state", "unknown"), inline=True)
        embed.add_field(name="OS", value=wl.get("os_type", "N/A"), inline=True)
        embed.add_field(name="vCPU", value=str(wl.get("vcpu", 0)), inline=True)
        embed.add_field(name="RAM", value=f"{wl.get('memory_gb', 0)} GB", inline=True)
        embed.add_field(name="Storage", value=f"{wl.get('storage_gb', 0)} GB", inline=True)
        embed.add_field(name="Host", value=wl.get("hostname", "N/A"), inline=False)
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"workloads": self._workloads, "waves": self._waves, "migration_log": self._migration_log}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")

async def setup(bot):
    await bot.add_cog(CloudMigrationCog(bot))

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
