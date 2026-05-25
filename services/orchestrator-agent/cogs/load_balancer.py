import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class LoadBalancer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="lbcreate", description="Create a load balancer pool")
    @app_commands.describe(name="Pool name", algorithm="round_robin/least_connections/ip_hash", health_check_type="tcp/http")
    async def lb_create(self, interaction: discord.Interaction, name: str, algorithm: str = "round_robin", health_check_type: str = "tcp"):
        if algorithm not in ("round_robin", "least_connections", "ip_hash"):
            await interaction.response.send_message(embed=discord.Embed(description="Algorithm must be round_robin, least_connections, or ip_hash", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO load_balancer_pools (name, algorithm, health_check_type) VALUES (%s, %s, %s)",
                (name, algorithm, health_check_type),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"LB pool '{name}' created ({algorithm}, {health_check_type})", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="lbadd", description="Add a VPS to a load balancer pool")
    @app_commands.describe(pool_name="Pool name", vps_id="VPS ID", port="Service port", weight="Weight (1-10)")
    async def lb_add(self, interaction: discord.Interaction, pool_name: str, vps_id: str, port: int = 80, weight: int = 1):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM load_balancer_pools WHERE name = %s", (pool_name,))
            pool = cursor.fetchone()
            if not pool:
                await interaction.response.send_message(embed=discord.Embed(description="Pool not found.", color=0xFF0000))
                cursor.close()
                conn.close()
                return

            cursor.execute(
                "INSERT INTO lb_pool_members (pool_id, container_id, port, weight) VALUES (%s, %s, %s, %s)",
                (pool["id"], vps_id, port, weight),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"VPS {vps_id[:12]} added to pool '{pool_name}' on port {port} (weight: {weight})", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="lbremove", description="Remove a VPS from a load balancer pool")
    @app_commands.describe(pool_name="Pool name", vps_id="VPS ID")
    async def lb_remove(self, interaction: discord.Interaction, pool_name: str, vps_id: str):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM load_balancer_pools WHERE name = %s", (pool_name,))
            pool = cursor.fetchone()
            if not pool:
                await interaction.response.send_message(embed=discord.Embed(description="Pool not found.", color=0xFF0000))
                cursor.close()
                conn.close()
                return

            cursor.execute("DELETE FROM lb_pool_members WHERE pool_id = %s AND container_id = %s", (pool["id"], vps_id))
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"VPS {vps_id[:12]} removed from pool '{pool_name}'.", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="lblist", description="List load balancer pools")
    async def lb_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM load_balancer_pools")
            pools = cursor.fetchall()
            conn.close()

            if not pools:
                await interaction.response.send_message(embed=discord.Embed(description="No LB pools.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Load Balancer Pools", color=discord.Color.blue())
            for p in pools:
                conn2 = self.vps_manager._get_db_connection()
                c2 = conn2.cursor(dictionary=True)
                c2.execute("SELECT COUNT(*) as count FROM lb_pool_members WHERE pool_id = %s", (p["id"],))
                count = c2.fetchone()["count"]
                c2.close()
                conn2.close()

                embed.add_field(
                    name=p["name"],
                    value=f"Algorithm: {p['algorithm']}\nHealth: {p['health_check_type']}\nMembers: {count}",
                    inline=False,
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(LoadBalancer(bot))
