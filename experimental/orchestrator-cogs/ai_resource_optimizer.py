import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import logging
import uuid

from config import config
from vps_manager import VPSManager

logger = logging.getLogger(__name__)


class AIResourceOptimizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.recommendations_file = 'data/optimization_recommendations.json'
        self._ensure_data_dir()
        self._load_recommendations()
        self.optimize_loop.start()

    def cog_unload(self):
        self.optimize_loop.cancel()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_recommendations(self):
        if os.path.exists(self.recommendations_file):
            with open(self.recommendations_file) as f:
                self.recommendations = json.load(f)
        else:
            self.recommendations = []

    def _save_recommendations(self):
        with open(self.recommendations_file, 'w') as f:
            json.dump(self.recommendations, f, indent=2)

    def _detect_idle(self, history: List[Dict], days: int = 7) -> bool:
        threshold = datetime.now() - timedelta(days=days)
        cutoff = threshold.isoformat()
        recent = [r for r in history if str(r.get("timestamp", "")) > cutoff]
        if not recent:
            return False
        avg_cpu = sum(r.get("cpu_usage", 0) for r in recent) / len(recent)
        avg_memory = sum(r.get("memory_usage", 0) for r in recent) / len(recent)
        return avg_cpu < 5.0 and avg_memory < 10.0

    def _analyze_trends(self, vps_id: str, instance: Dict) -> Optional[Dict]:
        cfg = instance["config"]
        try:
            import asyncio
            history = asyncio.run_coroutine_threadsafe(
                self.vps_manager.get_usage_history(vps_id, hours=168),
                self.bot.loop
            ).result()
        except Exception:
            history = None

        if not history or len(history) < 10:
            return None

        avg_cpu = sum(r.get("cpu_usage", 0) for r in history) / len(history)
        avg_memory = sum(r.get("memory_usage", 0) for r in history) / len(history)
        peak_cpu = max(r.get("cpu_usage", 0) for r in history)
        peak_memory = max(r.get("memory_usage", 0) for r in history)

        suggestions = []
        savings = 0.0
        current_cost = (cfg["cpu_limit"] * config.PRICING["cpu_per_core"]
                        + (cfg["memory_limit"] / 1024) * config.PRICING["memory_per_gb"]
                        + cfg["storage_limit"] * config.PRICING["storage_per_gb"])

        if avg_cpu < 20 and cfg["cpu_limit"] > config.RESOURCE_LIMITS["min_cpu"]:
            recommended_cpu = max(cfg["cpu_limit"] * 0.5, config.RESOURCE_LIMITS["min_cpu"])
            new_cost = (recommended_cpu * config.PRICING["cpu_per_core"]
                        + (cfg["memory_limit"] / 1024) * config.PRICING["memory_per_gb"]
                        + cfg["storage_limit"] * config.PRICING["storage_per_gb"])
            savings += current_cost - new_cost
            suggestions.append({
                "type": "downsize_cpu",
                "from": cfg["cpu_limit"],
                "to": round(recommended_cpu, 1),
                "savings": round(current_cost - new_cost, 2),
                "reason": f"Avg CPU usage {avg_cpu:.1f}% is low"
            })

        if avg_memory < 30 and cfg["memory_limit"] > config.RESOURCE_LIMITS["min_memory_mb"]:
            recommended_mem = int(max(cfg["memory_limit"] * 0.75, config.RESOURCE_LIMITS["min_memory_mb"]))
            new_cost = (cfg["cpu_limit"] * config.PRICING["cpu_per_core"]
                        + (recommended_mem / 1024) * config.PRICING["memory_per_gb"]
                        + cfg["storage_limit"] * config.PRICING["storage_per_gb"])
            savings += current_cost - new_cost
            suggestions.append({
                "type": "downsize_memory",
                "from": cfg["memory_limit"],
                "to": recommended_mem,
                "savings": round(current_cost - new_cost, 2),
                "reason": f"Avg memory usage {avg_memory:.1f}% is low"
            })

        if self._detect_idle(history):
            suggestions.append({
                "type": "idle_warning",
                "from": None,
                "to": None,
                "savings": current_cost,
                "reason": "VPS has been idle for over 7 days. Consider stopping or downsizing."
            })

        return {
            "current_cost": round(current_cost, 2),
            "avg_cpu": round(avg_cpu, 1),
            "avg_memory": round(avg_memory, 1),
            "peak_cpu": round(peak_cpu, 1),
            "peak_memory": round(peak_memory, 1),
            "suggestions": suggestions,
            "total_savings": round(savings, 2),
        }

    @tasks.loop(minutes=15)
    async def optimize_loop(self):
        try:
            for vps_id, instance in self.vps_manager.vps_instances.items():
                analysis = self._analyze_trends(vps_id, instance)
                if analysis and analysis["suggestions"]:
                    existing = [r for r in self.recommendations
                                if r["vps_id"] == vps_id and r["status"] == "pending"]
                    if not existing:
                        self.recommendations.append({
                            "id": str(uuid.uuid4())[:8],
                            "vps_id": vps_id,
                            "created_at": datetime.now().isoformat(),
                            "status": "pending",
                            "analysis": analysis,
                        })
            self._save_recommendations()
        except Exception as e:
            logger.error(f"Optimize loop error: {e}")

    @optimize_loop.before_loop
    async def before_optimize_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="optimize", description="Analyze resource usage and get optimization recommendations")
    async def optimize_resources(self, interaction: discord.Interaction):
        await interaction.response.defer()

        results = []
        for vps_id, instance in self.vps_manager.vps_instances.items():
            analysis = self._analyze_trends(vps_id, instance)
            if analysis:
                results.append((vps_id, analysis))

        if not results:
            await interaction.followup.send(embed=discord.Embed(description="No VPS data available for analysis.", color=0xFFFF00))
            return

        embed = discord.Embed(title="Resource Optimization Analysis", color=discord.Color.blue(), timestamp=datetime.now())
        for vps_id, analysis in results[:5]:
            status = "⚠️ Needs attention" if analysis["suggestions"] else "✅ Optimized"
            val = (f"CPU: {analysis['avg_cpu']}% avg / {analysis['peak_cpu']}% peak\n"
                   f"RAM: {analysis['avg_memory']}% avg / {analysis['peak_memory']}% peak\n"
                   f"Suggestions: {len(analysis['suggestions'])}")
            embed.add_field(name=f"{vps_id[:12]} - {status}", value=val, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="recommendations", description="List pending optimization recommendations")
    async def optimize_recommendations(self, interaction: discord.Interaction):
        await interaction.response.defer()

        pending = [r for r in self.recommendations if r["status"] == "pending"]
        if not pending:
            await interaction.followup.send(embed=discord.Embed(description="No pending recommendations.", color=0x00FF00))
            return

        embed = discord.Embed(title="Optimization Recommendations", color=discord.Color.blue(), timestamp=datetime.now())
        for rec in pending[:10]:
            a = rec["analysis"]
            sug_text = "\n".join(f"• {s['reason']}" for s in a["suggestions"][:3])
            embed.add_field(
                name=f"#{rec['id']} - {rec['vps_id'][:12]} (${a['current_cost']}/mo)",
                value=f"Savings: ${a['total_savings']}/mo\n{sug_text}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="optimize_apply", description="Apply an optimization recommendation by ID")
    @app_commands.describe(recommendation_id="Recommendation ID to apply")
    async def optimize_apply(self, interaction: discord.Interaction, recommendation_id: str):
        await interaction.response.defer()

        rec = next((r for r in self.recommendations if r["id"] == recommendation_id), None)
        if not rec:
            await interaction.followup.send(embed=discord.Embed(description="Recommendation not found.", color=0xFF0000))
            return

        if rec["status"] != "pending":
            await interaction.followup.send(embed=discord.Embed(description="Recommendation already applied or rejected.", color=0xFFFF00))
            return

        vps_id = rec["vps_id"]
        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        cfg = instance["config"]
        new_cpu = cfg["cpu_limit"]
        new_memory = cfg["memory_limit"]

        for s in rec["analysis"]["suggestions"]:
            if s["type"] == "downsize_cpu":
                new_cpu = s["to"]
            elif s["type"] == "downsize_memory":
                new_memory = s["to"]

        from vps_manager import VPSConfig
        new_config = VPSConfig(
            cpu_limit=new_cpu,
            memory_limit=new_memory,
            storage_limit=cfg["storage_limit"],
            image=cfg["image"],
            ports=cfg["ports"],
            env_vars={},
        )

        if await self.vps_manager.update_vps_config(vps_id, new_config):
            rec["status"] = "applied"
            rec["applied_at"] = datetime.now().isoformat()
            rec["applied_by"] = str(interaction.user.id)
            self._save_recommendations()
            await interaction.followup.send(embed=discord.Embed(description=f"Applied recommendation {recommendation_id}. CPU: {new_cpu}, RAM: {new_memory}MB", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to apply recommendation.", color=0xFF0000))

    @app_commands.command(name="optimize_history", description="View optimization recommendation history")
    async def optimize_history(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.recommendations:
            await interaction.followup.send(embed=discord.Embed(description="No recommendation history.", color=0xFFFF00))
            return

        embed = discord.Embed(title="Optimization History", color=discord.Color.blue(), timestamp=datetime.now())
        for rec in self.recommendations[-10:]:
            icon = {"pending": "⏳", "applied": "✅", "rejected": "❌"}.get(rec["status"], "❓")
            embed.add_field(
                name=f"{icon} #{rec['id']} - {rec['vps_id'][:12]}",
                value=f"Status: {rec['status']} | Savings: ${rec['analysis']['total_savings']}/mo | {rec['created_at'][:19]}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AIResourceOptimizer(bot))
