import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import logging

from config import config
from vps_manager import VPSManager


class SSLManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.ssl_renewal_loop.start()

    def cog_unload(self):
        self.ssl_renewal_loop.cancel()

    @tasks.loop(hours=24)
    async def ssl_renewal_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM ssl_certificates WHERE status = 'active'")
            certs = cursor.fetchall()
            cursor.close()
            conn.close()

            for cert in certs:
                if cert["expires_at"] and cert["expires_at"] - datetime.now() < timedelta(days=config.SSL_RENEWAL_DAYS_BEFORE_EXPIRY):
                    logging.info(f"SSL cert for {cert['domain']} needs renewal")
                    # Auto-renewal logic would go here with certbot/LE
        except Exception as e:
            logging.error(f"SSL renewal loop error: {e}")

    @app_commands.command(name="sslrequest", description="Request an SSL certificate")
    @app_commands.describe(domain="Domain name (e.g. example.com)", email="Email for Let's Encrypt")
    async def ssl_request(self, interaction: discord.Interaction, domain: str, email: str = None):
        await interaction.response.defer()

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ssl_certificates (domain, status, issued_at) VALUES (%s, 'requested', NOW())",
                (domain,),
            )
            conn.commit()
            cert_id = cursor.lastrowid
            cursor.close()
            conn.close()

            embed = discord.Embed(title="SSL Certificate Requested", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Domain", value=domain, inline=True)
            embed.add_field(name="ID", value=str(cert_id), inline=True)
            embed.add_field(name="Status", value="Requested - processing", inline=True)
            embed.add_field(name="Email", value=email or config.SSL_EMAIL, inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="sslstatus", description="Check SSL certificate status")
    @app_commands.describe(domain="Domain name")
    async def ssl_status(self, interaction: discord.Interaction, domain: str):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM ssl_certificates WHERE domain = %s ORDER BY created_at DESC LIMIT 1", (domain,))
            cert = cursor.fetchone()
            cursor.close()
            conn.close()

            if not cert:
                await interaction.response.send_message(embed=discord.Embed(description=f"No SSL certificate for {domain}", color=0xFFFF00))
                return

            embed = discord.Embed(title=f"SSL: {domain}", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Status", value=cert["status"], inline=True)
            embed.add_field(name="Issued", value=str(cert.get("issued_at", "N/A")), inline=True)
            embed.add_field(name="Expires", value=str(cert.get("expires_at", "N/A")), inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="sslrenew", description="Renew an SSL certificate")
    @app_commands.describe(domain="Domain name")
    async def ssl_renew(self, interaction: discord.Interaction, domain: str):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ssl_certificates SET status = 'renewing', issued_at = NOW() WHERE domain = %s",
                (domain,),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"SSL renewal initiated for {domain}", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(SSLManager(bot))
