import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from integration import APIClient


class LoyaltyRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = APIClient()

    @app_commands.command(name="loyalty_status", description="Check your loyalty status")
    async def loyalty_status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.api.get("/api/marketplace/loyalty/status")
        embed = discord.Embed(title="Loyalty Status", color=discord.Color.gold(), timestamp=datetime.now())
        embed.add_field(name="Points", value=str(result.get("points", 0)), inline=True)
        embed.add_field(name="Level", value=result.get("level", "Bronze"), inline=True)
        embed.add_field(name="Points to Next Level", value=str(result.get("points_to_next", 0)), inline=True)
        embed.add_field(name="Total Spent", value=f"${result.get('total_spent', 0):.2f}", inline=True)
        embed.add_field(name="Badges", value=", ".join(result.get("badges", [])) or "None", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="loyalty_badges", description="List available badges")
    async def loyalty_badges(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/loyalty/badges")
        badges = data if isinstance(data, list) else data.get("badges", [])
        if not badges:
            await interaction.followup.send(embed=discord.Embed(description="No badges available.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Loyalty Badges", color=discord.Color.gold(), timestamp=datetime.now())
        for b in badges[:10]:
            unlocked = "✅" if b.get("unlocked") else "🔒"
            embed.add_field(name=f"{unlocked} {b.get('name', 'Unknown')}", value=b.get("description", ""), inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="loyalty_rewards", description="List available rewards")
    async def loyalty_rewards(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/loyalty/rewards")
        rewards = data if isinstance(data, list) else data.get("rewards", [])
        if not rewards:
            await interaction.followup.send(embed=discord.Embed(description="No rewards available.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Loyalty Rewards", color=discord.Color.gold(), timestamp=datetime.now())
        for r in rewards[:10]:
            embed.add_field(name=f"{r.get('name', 'Unknown')} - {r.get('points_cost', 0)} pts", value=r.get("description", ""), inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="loyalty_redeem", description="Redeem loyalty points for a reward")
    @app_commands.describe(reward_id="Reward ID")
    async def loyalty_redeem(self, interaction: discord.Interaction, reward_id: str):
        await interaction.response.defer()
        result = await self.api.post(f"/api/marketplace/loyalty/rewards/{reward_id}/redeem", {})
        if result.get("status") == "redeemed":
            await interaction.followup.send(embed=discord.Embed(description=f"Reward redeemed: {result.get('reward_name', reward_id)}", color=discord.Color.green()))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Failed: {result.get('error', 'Unknown')}", color=discord.Color.red()))

    @app_commands.command(name="loyalty_leaderboard", description="Show loyalty leaderboard")
    async def loyalty_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.api.get("/api/marketplace/loyalty/leaderboard")
        users = data if isinstance(data, list) else data.get("leaderboard", [])
        if not users:
            await interaction.followup.send(embed=discord.Embed(description="No data.", color=0xFFFF00))
            return
        embed = discord.Embed(title="Loyalty Leaderboard", color=discord.Color.gold(), timestamp=datetime.now())
        for i, u in enumerate(users[:10]):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            embed.add_field(name=f"{medal} {u.get('user_id', 'Unknown')[:8]}...", value=f"Level: {u.get('level', 'Bronze')} | Points: {u.get('points', 0)} | Badges: {u.get('badge_count', 0)}", inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LoyaltyRewards(bot))
