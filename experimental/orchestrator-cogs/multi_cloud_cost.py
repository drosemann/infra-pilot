import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging
import json
import os
from typing import Optional

from config import config
from integration import get_db_connection
from vps_manager import VPSManager

DATA_FILE = "data/cloud_pricing.json"

PROVIDER_PRICING = {
    "aws": {
        "name": "AWS",
        "instances": {
            "t3.nano": {"cpu": 2, "memory": 512, "price_monthly": 5.52},
            "t3.micro": {"cpu": 2, "memory": 1024, "price_monthly": 11.04},
            "t3.small": {"cpu": 2, "memory": 2048, "price_monthly": 22.08},
            "t3.medium": {"cpu": 2, "memory": 4096, "price_monthly": 44.16},
            "t3.large": {"cpu": 2, "memory": 8192, "price_monthly": 88.32},
            "t3.xlarge": {"cpu": 4, "memory": 16384, "price_monthly": 176.64},
        },
    },
    "gcp": {
        "name": "GCP",
        "instances": {
            "e2-micro": {"cpu": 2, "memory": 1024, "price_monthly": 6.40},
            "e2-small": {"cpu": 2, "memory": 2048, "price_monthly": 12.80},
            "e2-medium": {"cpu": 2, "memory": 4096, "price_monthly": 25.60},
            "e2-standard-2": {"cpu": 2, "memory": 8192, "price_monthly": 48.64},
            "e2-standard-4": {"cpu": 4, "memory": 16384, "price_monthly": 97.28},
            "e2-standard-8": {"cpu": 8, "memory": 32768, "price_monthly": 194.56},
        },
    },
    "azure": {
        "name": "Azure",
        "instances": {
            "B1s": {"cpu": 1, "memory": 1024, "price_monthly": 6.72},
            "B2s": {"cpu": 2, "memory": 4096, "price_monthly": 30.14},
            "B4ms": {"cpu": 4, "memory": 16384, "price_monthly": 68.64},
            "D2s_v3": {"cpu": 2, "memory": 8192, "price_monthly": 70.08},
            "D4s_v3": {"cpu": 4, "memory": 16384, "price_monthly": 140.16},
            "D8s_v3": {"cpu": 8, "memory": 32768, "price_monthly": 280.32},
        },
    },
    "hetzner": {
        "name": "Hetzner",
        "instances": {
            "CX22": {"cpu": 2, "memory": 4096, "price_monthly": 5.49},
            "CX32": {"cpu": 4, "memory": 8192, "price_monthly": 11.49},
            "CX42": {"cpu": 8, "memory": 16384, "price_monthly": 23.49},
            "CX52": {"cpu": 16, "memory": 32768, "price_monthly": 45.49},
            "CCX13": {"cpu": 4, "memory": 16384, "price_monthly": 18.49},
            "CCX23": {"cpu": 8, "memory": 32768, "price_monthly": 36.99},
        },
    },
}


class MultiCloudCost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.pricing_cache = self._load_pricing_cache()
        self.refresh_pricing_loop.start()

    def cog_unload(self):
        self.refresh_pricing_loop.cancel()

    def _load_pricing_cache(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE) as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading pricing cache: {e}")
        return {}

    def _save_pricing_cache(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.pricing_cache, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving pricing cache: {e}")

    def _record_pricing_db(self, provider: str, instance_type: str, price_monthly: float):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cloud_pricing_cache (provider, instance_type, price_monthly) "
                "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE price_monthly = VALUES(price_monthly), updated_at = NOW()",
                (provider, instance_type, price_monthly),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error recording pricing to DB: {e}")

    @tasks.loop(hours=24)
    async def refresh_pricing_loop(self):
        for provider_key, provider_data in PROVIDER_PRICING.items():
            for inst_type, specs in provider_data["instances"].items():
                self.pricing_cache[f"{provider_key}/{inst_type}"] = {
                    "provider": provider_key,
                    "provider_name": provider_data["name"],
                    "instance_type": inst_type,
                    "cpu": specs["cpu"],
                    "memory": specs["memory"],
                    "price_monthly": specs["price_monthly"],
                    "last_updated": datetime.now().isoformat(),
                }
                self._record_pricing_db(provider_key, inst_type, specs["price_monthly"])
        self._save_pricing_cache()

    async def _compare_vps_cost(self, cpu: float, memory_mb: int) -> list:
        comparisons = []
        for provider_key, provider_data in PROVIDER_PRICING.items():
            for inst_type, specs in provider_data["instances"].items():
                if specs["cpu"] >= cpu and specs["memory"] >= memory_mb:
                    comparisons.append({
                        "provider": provider_data["name"],
                        "instance": inst_type,
                        "cpu": specs["cpu"],
                        "memory": specs["memory"],
                        "price_monthly": specs["price_monthly"],
                    })
        comparisons.sort(key=lambda x: x["price_monthly"])
        return comparisons[:5]

    @app_commands.command(name="cost", description="Multi-cloud cost optimization")
    @app_commands.describe(
        action="compare/providers/recommend/history",
        vps_id="VPS ID (for compare action)",
    )
    async def cost(
        self,
        interaction: discord.Interaction,
        action: str,
        vps_id: Optional[str] = None,
    ):
        await interaction.response.defer()
        actions = {
            "compare": self._compare_pricing,
            "providers": self._list_providers,
            "recommend": self._recommend,
            "history": self._cost_history,
        }
        handler = actions.get(action)
        if not handler:
            embed = discord.Embed(description=f"Unknown action: {action}. Use compare/providers/recommend/history", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        await handler(interaction, vps_id)

    async def _compare_pricing(self, interaction: discord.Interaction, vps_id: Optional[str]):
        if not vps_id:
            embed = discord.Embed(description="VPS ID required", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            embed = discord.Embed(description="VPS not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        cfg = instance["config"]
        cpu = cfg["cpu_limit"]
        memory = cfg["memory_limit"]
        comparisons = await self._compare_vps_cost(cpu, memory)
        current_cost = cpu * config.PRICING["cpu_per_core"] + (memory / 1024) * config.PRICING["memory_per_gb"]
        embed = discord.Embed(title=f"Cost Comparison: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Current (Your VPS)", value=f"${current_cost:.2f}/mo\n{cpu} cores, {memory}MB", inline=False)
        for c in comparisons[:3]:
            embed.add_field(
                name=f"{c['provider']} {c['instance']}",
                value=f"${c['price_monthly']:.2f}/mo\n{c['cpu']} cores, {c['memory']}MB",
                inline=True,
            )
        savings = current_cost - comparisons[0]["price_monthly"] if comparisons else 0
        if savings > 0:
            embed.add_field(name="💡 Potential Savings", value=f"Up to ${savings:.2f}/mo with {comparisons[0]['provider']} {comparisons[0]['instance']}", inline=False)
        await interaction.followup.send(embed=embed)

    async def _list_providers(self, interaction: discord.Interaction, vps_id: Optional[str]):
        embed = discord.Embed(title="Cloud Providers", color=discord.Color.blue(), timestamp=datetime.now())
        for provider_key, provider_data in PROVIDER_PRICING.items():
            prices = [s["price_monthly"] for s in provider_data["instances"].values()]
            embed.add_field(
                name=provider_data["name"],
                value=(
                    f"Instances: {len(provider_data['instances'])}\n"
                    f"Price range: ${min(prices):.2f} - ${max(prices):.2f}/mo"
                ),
                inline=True,
            )
        await interaction.followup.send(embed=embed)

    async def _recommend(self, interaction: discord.Interaction, vps_id: Optional[str]):
        all_options = []
        for provider_key, provider_data in PROVIDER_PRICING.items():
            for inst_type, specs in provider_data["instances"].items():
                all_options.append({
                    "provider": provider_data["name"],
                    "instance": inst_type,
                    "cpu": specs["cpu"],
                    "memory": specs["memory"],
                    "price_monthly": specs["price_monthly"],
                    "value_score": specs["cpu"] * 10 + specs["memory"] / 1024 * 5 - specs["price_monthly"] * 0.1,
                })
        all_options.sort(key=lambda x: x["value_score"], reverse=True)
        embed = discord.Embed(title="Recommended Cloud Instances", color=discord.Color.blue(), timestamp=datetime.now())
        for opt in all_options[:6]:
            embed.add_field(
                name=f"{opt['provider']} {opt['instance']}",
                value=(
                    f"${opt['price_monthly']:.2f}/mo\n"
                    f"{opt['cpu']} cores, {opt['memory']}MB"
                ),
                inline=True,
            )
        await interaction.followup.send(embed=embed)

    async def _cost_history(self, interaction: discord.Interaction, vps_id: Optional[str]):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT provider, instance_type, price_monthly, updated_at FROM cloud_pricing_cache ORDER BY updated_at DESC LIMIT 20"
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if not rows:
                embed = discord.Embed(description="No pricing history available", color=0xFFFF00)
                await interaction.followup.send(embed=embed)
                return
            embed = discord.Embed(title="Pricing Cache (Last 20)", color=discord.Color.blue(), timestamp=datetime.now())
            for row in rows[:10]:
                embed.add_field(
                    name=f"{row['provider']} {row['instance_type']}",
                    value=f"${row['price_monthly']:.2f}/mo\nUpdated: {row['updated_at'].isoformat()[:19] if hasattr(row['updated_at'], 'isoformat') else row['updated_at']}",
                    inline=True,
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MultiCloudCost(bot))
