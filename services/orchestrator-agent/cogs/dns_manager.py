import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from config import config
from vps_manager import VPSManager


class DNSManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    def _get_container_ip(self, container_id: str) -> str:
        try:
            container = self.vps_manager.client.containers.get(container_id)
            networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
            for net_name, net_config in networks.items():
                ip = net_config.get("IPAddress")
                if ip:
                    return ip
        except Exception:
            pass
        return "0.0.0.0"

    @app_commands.command(name="dnsadd", description="Add a DNS record")
    @app_commands.describe(name="Record name (e.g. myserver)", value="IP address or container ID", record_type="A/AAAA/CNAME", zone="DNS zone")
    async def dns_add(self, interaction: discord.Interaction, name: str, value: str, record_type: str = "A", zone: str = None):
        # If value is a container ID, resolve its IP
        if value in self.vps_manager.vps_instances:
            value = self._get_container_ip(value)

        if record_type not in ("A", "AAAA", "CNAME"):
            await interaction.response.send_message(embed=discord.Embed(description="Type must be A, AAAA, or CNAME", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO dns_records (name, type, value, ttl, zone) VALUES (%s, %s, %s, %s, %s)",
                (name, record_type, value, config.DNS_TTL, zone),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"DNS {record_type} record '{name}' -> {value}", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="dnsremove", description="Remove a DNS record")
    @app_commands.describe(name="Record name", record_type="Record type")
    async def dns_remove(self, interaction: discord.Interaction, name: str, record_type: str = None):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            if record_type:
                cursor.execute("DELETE FROM dns_records WHERE name = %s AND type = %s", (name, record_type))
            else:
                cursor.execute("DELETE FROM dns_records WHERE name = %s", (name,))
            conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Deleted {deleted} DNS record(s) for '{name}'", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="dnslist", description="List DNS records")
    async def dns_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM dns_records ORDER BY name")
            records = cursor.fetchall()
            cursor.close()
            conn.close()

            if not records:
                await interaction.response.send_message(embed=discord.Embed(description="No DNS records.", color=0xFFFF00))
                return

            embed = discord.Embed(title="DNS Records", color=discord.Color.blue())
            for r in records:
                embed.add_field(
                    name=f"{r['name']} ({r['type']})",
                    value=f"Value: {r['value']}\nTTL: {r['ttl']}\nZone: {r.get('zone', 'default')}",
                    inline=True,
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(DNSManager(bot))
