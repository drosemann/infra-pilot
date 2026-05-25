import discord
from discord.ext import commands, tasks
from discord import app_commands
import psutil
import docker
import mysql.connector
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import os

from config import config
from vps_manager import VPSManager


class Monitoring(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.docker_client = docker.from_env()
        self.vps_manager = VPSManager()
        self.stats_cache: Dict[str, Dict] = {}
        self.alert_thresholds = dict(config.ALERT_THRESHOLDS)
        self.monitoring_loop.start()
        self.update_status.start()

    def cog_unload(self):
        self.monitoring_loop.cancel()
        self.update_status.cancel()

    def get_db(self):
        return mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )

    @tasks.loop(minutes=1)
    async def monitoring_loop(self):
        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                stats = self._get_container_stats(container)
                if stats:
                    self.stats_cache[container.id] = stats
                    await self._check_alerts(container.id, stats)
                    await self._update_db_stats(container.id, stats)
        except Exception as e:
            logging.error(f"Monitoring loop error: {e}")

    def _get_container_stats(self, container) -> Optional[Dict]:
        try:
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0

            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0

            net = stats["networks"]["eth0"]
            disk_percent = 0
            try:
                out = container.exec_run("df -h /").output.decode()
                disk_percent = float(out.split()[11].strip("%"))
            except Exception:
                pass

            return {
                "timestamp": datetime.now().isoformat(),
                "container_id": container.id,
                "name": container.name,
                "status": container.status,
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory_percent, 2),
                "memory_used": memory_usage,
                "memory_total": memory_limit,
                "network": {"rx_bytes": net["rx_bytes"], "tx_bytes": net["tx_bytes"]},
                "disk_usage": disk_percent,
            }
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return None

    async def _update_db_stats(self, container_id: str, stats: Dict):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO vps_statistics (container_id, cpu_usage, memory_usage, memory_used, memory_total, network_rx, network_tx, disk_usage, status, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (container_id, stats["cpu_usage"], stats["memory_usage"], stats["memory_used"], stats["memory_total"], stats["network"]["rx_bytes"], stats["network"]["tx_bytes"], stats["disk_usage"], stats["status"], stats["timestamp"]),
            )
            cursor.execute(
                "INSERT INTO vps_peak_statistics (container_id, peak_cpu, peak_memory, peak_network) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE peak_cpu = GREATEST(peak_cpu, VALUES(peak_cpu)), peak_memory = GREATEST(peak_memory, VALUES(peak_memory)), peak_network = GREATEST(peak_network, VALUES(peak_network)), last_updated = NOW()",
                (container_id, stats["cpu_usage"], stats["memory_usage"], max(stats["network"]["rx_bytes"], stats["network"]["tx_bytes"])),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error updating DB stats: {e}")

    async def _check_alerts(self, container_id: str, stats: Dict):
        alerts = []
        if stats["cpu_usage"] > self.alert_thresholds["cpu"]:
            alerts.append(f"High CPU: {stats['cpu_usage']}%")
        if stats["memory_usage"] > self.alert_thresholds["memory"]:
            alerts.append(f"High Memory: {stats['memory_usage']}%")
        if stats["disk_usage"] > self.alert_thresholds["disk"]:
            alerts.append(f"High Disk: {stats['disk_usage']}%")
        if alerts:
            await self._send_alert(container_id, alerts)

    async def _send_alert(self, container_id: str, alerts: List[str]):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM vps_containers WHERE container_id = %s", (container_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                user = await self.bot.fetch_user(int(result[0]))
                if user:
                    embed = discord.Embed(title="VPS Resource Alert", description=f"Container: {container_id[:12]}", color=discord.Color.red())
                    embed.add_field(name="Alerts", value="\n".join(alerts), inline=False)
                    await user.send(embed=embed)
        except Exception as e:
            logging.error(f"Error sending alert: {e}")

    @app_commands.command(name="vpsstats", description="Get VPS statistics")
    @app_commands.describe(container_id="Container ID")
    async def vps_stats(self, interaction: discord.Interaction, container_id: str):
        await interaction.response.defer()
        stats = self.stats_cache.get(container_id)
        if not stats:
            stats = await self.vps_manager.get_vps_stats(container_id)
        if not stats:
            await interaction.followup.send(embed=discord.Embed(description="No stats available.", color=0xFF0000))
            return

        embed = discord.Embed(title=f"VPS Stats: {container_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Status", value=stats.get("status", "unknown"), inline=True)
        embed.add_field(name="CPU", value=f"{stats.get('cpu_usage', 0)}%", inline=True)
        embed.add_field(name="Memory", value=f"{stats.get('memory_usage', 0)}%", inline=True)
        net = stats.get("network", {})
        embed.add_field(name="Network", value=f"↓ {net.get('rx_bytes', 0)}\n↑ {net.get('tx_bytes', 0)}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="vpsgraph", description="Generate resource usage graph")
    @app_commands.describe(container_id="Container ID", metric="Metric (cpu/memory/disk)", period="Period in hours (default: 24)")
    async def vps_graph(self, interaction: discord.Interaction, container_id: str, metric: str = "cpu", period: int = 24):
        await interaction.response.defer()
        history = await self.vps_manager.get_usage_history(container_id, period)
        if not history:
            await interaction.followup.send(embed=discord.Embed(description="No data available.", color=0xFF0000))
            return

        metric_map = {"cpu": "cpu_usage", "memory": "memory_usage", "disk": "disk_usage"}
        col = metric_map.get(metric.lower(), "cpu_usage")

        timestamps = [datetime.fromisoformat(r["timestamp"].strftime("%Y-%m-%dT%H:%M:%S") if isinstance(r["timestamp"], datetime) else r["timestamp"]) for r in history]
        values = [r[col] for r in history]

        plt.figure(figsize=(10, 4))
        plt.plot(timestamps, values, color="#00d2ff")
        plt.title(f"{metric.upper()} Usage - Last {period}h")
        plt.xlabel("Time")
        plt.ylabel(f"{metric.upper()} %")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        await interaction.followup.send(file=discord.File(buf, f"{metric}_graph.png"))

    @app_commands.command(name="setalertthreshold", description="Set alert threshold (Admin)")
    @app_commands.describe(resource="cpu/memory/disk/network", threshold="Threshold percentage (0-100)")
    async def set_alert_threshold(self, interaction: discord.Interaction, resource: str, threshold: float):
        if str(interaction.user.id) not in config.WHITELIST_IDS:
            await interaction.response.send_message(embed=discord.Embed(description="Admin only.", color=0xFF0000), ephemeral=True)
            return
        if resource not in self.alert_thresholds or not (0 <= threshold <= 100):
            await interaction.response.send_message(embed=discord.Embed(description="Invalid resource or threshold.", color=0xFF0000))
            return
        self.alert_thresholds[resource] = threshold
        await interaction.response.send_message(embed=discord.Embed(description=f"Threshold for {resource} set to {threshold}%", color=0x00FF00))

    @tasks.loop(minutes=5)
    async def update_status(self):
        try:
            containers = self.docker_client.containers.list()
            status = f"VPS: {len(containers)} containers"
            await self.bot.change_presence(activity=discord.Game(name=status))
        except Exception:
            pass

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Monitoring(bot))
