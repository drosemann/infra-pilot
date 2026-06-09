import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict, List
import json
import logging
import os
import asyncio
import aiofiles
import aiohttp
import ssl
import socket
import dns.resolver

from config import config
from vps_manager import VPSManager


CHECK_TYPES = {"http", "https", "tcp", "ping", "ssl", "dns"}


class SyntheticMonitoring(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.cache_file = config.SYNTHETIC_CHECKS_FILE
        self.probe_locations = config.SYNTHETIC_PROBE_LOCATIONS
        self.synthetic_check_loop.start()

    def cog_unload(self):
        self.synthetic_check_loop.cancel()

    @tasks.loop(minutes=config.SYNTHETIC_CHECK_INTERVAL_MINUTES)
    async def synthetic_check_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM synthetic_checks WHERE enabled = 1")
            checks = cursor.fetchall()
            cursor.close()
            conn.close()

            for check in checks:
                for location in self.probe_locations:
                    result = await self._run_check(check["check_type"], check["target"], check.get("config"))
                    self._store_result(check["id"], location, result)
                    self._update_check_status(check["id"], result["status"])
        except Exception as e:
            logging.error(f"Synthetic check loop error: {e}")

    @synthetic_check_loop.before_loop
    async def before_checks(self):
        await self.bot.wait_until_ready()

    async def _run_check(self, check_type: str, target: str, check_config: dict = None) -> dict:
        start = asyncio.get_event_loop().time()
        try:
            if check_type in ("http", "https"):
                return await self._check_http(target, check_type == "https")
            elif check_type == "tcp":
                return await self._check_tcp(target)
            elif check_type == "ping":
                return await self._check_ping(target)
            elif check_type == "ssl":
                return await self._check_ssl(target)
            elif check_type == "dns":
                return await self._check_dns(target)
            else:
                return {"status": "failed", "error": f"Unknown check type: {check_type}"}
        except Exception as e:
            elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
            return {"status": "failed", "response_time_ms": elapsed, "error": str(e)}

    async def _check_http(self, target: str, tls: bool = False) -> dict:
        start = asyncio.get_event_loop().time()
        protocol = "https" if tls else "http"
        url = f"{protocol}://{target}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                return {
                    "status": "passed" if resp.status < 500 else "failed",
                    "response_time_ms": elapsed,
                    "status_code": resp.status,
                }

    async def _check_tcp(self, target: str) -> dict:
        start = asyncio.get_event_loop().time()
        host, port = target.split(":") if ":" in target else (target, "80")
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, int(port)), timeout=10)
        elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
        writer.close()
        return {"status": "passed", "response_time_ms": elapsed}

    async def _check_ping(self, target: str) -> dict:
        start = asyncio.get_event_loop().time()
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", "5", target,
            stdout=asyncio.DEVNULL, stderr=asyncio.DEVNULL,
        )
        await proc.wait()
        elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
        return {
            "status": "passed" if proc.returncode == 0 else "failed",
            "response_time_ms": elapsed,
        }

    async def _check_ssl(self, target: str) -> dict:
        start = asyncio.get_event_loop().time()
        host, port = target.split(":") if ":" in target else (target, "443")
        context = ssl.create_default_context()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, int(port), ssl=context), timeout=10
        )
        elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
        cert = writer.get_extra_info("ssl_object").getpeercert()
        writer.close()
        expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z") if cert else None
        return {
            "status": "passed",
            "response_time_ms": elapsed,
            "expires_at": str(expires) if expires else None,
        }

    async def _check_dns(self, target: str) -> dict:
        start = asyncio.get_event_loop().time()
        resolver = dns.resolver.Resolver()
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, resolver.resolve, target, "A"),
            timeout=10,
        )
        elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
        return {"status": "passed" if result else "failed", "response_time_ms": elapsed}

    def _store_result(self, check_id: int, location: str, result: dict):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO synthetic_check_results (check_id, probe_location, status, response_time_ms, status_code, error_message) VALUES (%s, %s, %s, %s, %s, %s)",
                (check_id, location, result["status"], result.get("response_time_ms"), result.get("status_code"), result.get("error")),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error storing check result: {e}")

    def _update_check_status(self, check_id: int, status: str):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE synthetic_checks SET last_status = %s, last_checked_at = NOW() WHERE id = %s",
                (status, check_id),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error updating check status: {e}")

    @app_commands.command(name="monitor", description="Synthetic monitoring management")
    @app_commands.describe(
        subcommand="create, list, delete, status, probes",
        check_type="http/https/tcp/ping/ssl/dns (for create)",
        target="Target URL/host:port (for create)",
        check_id="Check ID (for delete/status)",
    )
    async def monitor_command(
        self,
        interaction: discord.Interaction,
        subcommand: str,
        check_type: str = None,
        target: str = None,
        check_id: int = None,
    ):
        await interaction.response.defer()

        if subcommand == "create":
            if not check_type or not target:
                await interaction.followup.send(embed=discord.Embed(description="Provide check_type and target", color=0xFF0000))
                return
            await self._monitor_create(interaction, check_type, target)
        elif subcommand == "list":
            await self._monitor_list(interaction)
        elif subcommand == "delete":
            if not check_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide check_id", color=0xFF0000))
                return
            await self._monitor_delete(interaction, check_id)
        elif subcommand == "status":
            if not check_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide check_id", color=0xFF0000))
                return
            await self._monitor_status(interaction, check_id)
        elif subcommand == "probes":
            await self._monitor_probes(interaction)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Subcommand: create, list, delete, status, probes", color=0xFF0000))

    async def _monitor_create(self, interaction: discord.Interaction, check_type: str, target: str):
        if check_type not in CHECK_TYPES:
            await interaction.followup.send(embed=discord.Embed(description=f"Type must be: {', '.join(CHECK_TYPES)}", color=0xFF0000))
            return
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO synthetic_checks (check_type, target, interval_minutes, enabled) VALUES (%s, %s, %s, 1)",
                (check_type, target, config.SYNTHETIC_CHECK_INTERVAL_MINUTES),
            )
            conn.commit()
            cursor.close()
            conn.close()

            await interaction.followup.send(embed=discord.Embed(description=f"Monitor created: {check_type} -> {target}", color=0x00FF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _monitor_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM synthetic_checks ORDER BY created_at DESC")
            checks = cursor.fetchall()
            cursor.close()
            conn.close()

            if not checks:
                await interaction.followup.send(embed=discord.Embed(description="No monitors configured.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Synthetic Monitors", color=discord.Color.blue())
            for c in checks:
                status_emoji = "✅" if c.get("last_status") == "passed" else "❌" if c.get("last_status") else "⏳"
                embed.add_field(
                    name=f"{status_emoji} {c['check_type']} - {c['target'][:40]} (ID: {c['id']})",
                    value=f"Status: {c.get('last_status', 'pending')} | Interval: {c['interval_minutes']}m\n"
                    f"Last Check: {c.get('last_checked_at', 'Never')}",
                    inline=False,
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _monitor_delete(self, interaction: discord.Interaction, check_id: int):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM synthetic_checks WHERE id = %s", (check_id,))
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            if deleted:
                await interaction.followup.send(embed=discord.Embed(description=f"Monitor {check_id} deleted.", color=0x00FF00))
            else:
                await interaction.followup.send(embed=discord.Embed(description="Monitor not found.", color=0xFFFF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _monitor_status(self, interaction: discord.Interaction, check_id: int):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM synthetic_checks WHERE id = %s", (check_id,))
            check = cursor.fetchone()
            if not check:
                cursor.close()
                conn.close()
                await interaction.followup.send(embed=discord.Embed(description="Monitor not found.", color=0xFF0000))
                return

            cursor.execute(
                "SELECT * FROM synthetic_check_results WHERE check_id = %s ORDER BY checked_at DESC LIMIT 20",
                (check_id,),
            )
            results = cursor.fetchall()
            cursor.close()
            conn.close()

            embed = discord.Embed(title=f"Monitor Status: {check['check_type']} -> {check['target'][:40]}", color=discord.Color.blue())
            embed.add_field(name="Type", value=check["check_type"], inline=True)
            embed.add_field(name="Interval", value=f"{check['interval_minutes']}m", inline=True)
            embed.add_field(name="Last Status", value=check.get("last_status", "pending"), inline=True)

            passed = failed = 0
            for r in results:
                if r["status"] == "passed":
                    passed += 1
                elif r["status"] == "failed":
                    failed += 1
            embed.add_field(name="Recent Pass/Fail", value=f"{passed}/{failed}", inline=True)

            if results:
                avg_ms = int(sum(r.get("response_time_ms", 0) or 0 for r in results) / len(results))
                embed.add_field(name="Avg Response", value=f"{avg_ms}ms", inline=True)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _monitor_probes(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Global Probe Locations", color=discord.Color.blue())
        for loc in self.probe_locations:
            embed.add_field(name="📍", value=loc, inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SyntheticMonitoring(bot))
