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


class AIThreatDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.incidents_file = 'data/threat_incidents.json'
        self.whitelist_file = 'data/threat_whitelist.json'
        self._ensure_data_dir()
        self._load_incidents()
        self._load_whitelist()
        self.threat_loop.start()

    def cog_unload(self):
        self.threat_loop.cancel()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_incidents(self):
        if os.path.exists(self.incidents_file):
            with open(self.incidents_file) as f:
                self.incidents = json.load(f)
        else:
            self.incidents = []

    def _save_incidents(self):
        with open(self.incidents_file, 'w') as f:
            json.dump(self.incidents, f, indent=2)

    def _load_whitelist(self):
        if os.path.exists(self.whitelist_file):
            with open(self.whitelist_file) as f:
                self.whitelist = json.load(f)
        else:
            self.whitelist = []

    def _save_whitelist(self):
        with open(self.whitelist_file, 'w') as f:
            json.dump(self.whitelist, f, indent=2)

    def _score_anomaly(self, container_id: str, stats: Optional[Dict]) -> float:
        score = 0.0
        if not stats:
            return score

        cpu = stats.get("cpu_usage", 0)
        memory = stats.get("memory_usage", 0)

        if cpu > config.ALERT_THRESHOLDS.get("cpu", 90):
            score += 25
        if memory > config.ALERT_THRESHOLDS.get("memory", 90):
            score += 25

        if cpu > 95:
            score += 15
        if memory > 95:
            score += 15

        return min(score, 100)

    def _check_process_anomalies(self, container_id: str) -> List[str]:
        alerts = []
        try:
            import asyncio
            container = self.vps_manager.client.containers.get(container_id)
            exit_code, output = container.exec_run("ps aux")
            if exit_code == 0:
                output_str = output.decode() if isinstance(output, bytes) else output
                lines = output_str.strip().split("\n")
                proc_count = len(lines) - 1
                if proc_count > 100:
                    alerts.append(f"High process count: {proc_count}")
        except Exception:
            pass
        return alerts

    def _check_ssh_anomalies(self, container_id: str) -> List[str]:
        alerts = []
        try:
            container = self.vps_manager.client.containers.get(container_id)
            exit_code, output = container.exec_run("journalctl -u ssh --no-pager -n 50 2>/dev/null || cat /var/log/auth.log 2>/dev/null || echo ''")
            if exit_code == 0:
                output_str = output.decode() if isinstance(output, bytes) else output
                failed_count = output_str.count("Failed password")
                if failed_count > 10:
                    alerts.append(f"Multiple failed SSH logins: {failed_count} attempts")
        except Exception:
            pass
        return alerts

    def _check_network_anomalies(self, container_id: str, stats: Optional[Dict]) -> List[str]:
        alerts = []
        if stats and "network" in stats:
            rx = stats["network"].get("rx_bytes", 0)
            tx = stats["network"].get("tx_bytes", 0)
            if rx > 10_000_000 or tx > 10_000_000:
                alerts.append(f"High network traffic: RX {rx} bytes, TX {tx} bytes")
        return alerts

    @tasks.loop(minutes=5)
    async def threat_loop(self):
        try:
            for vps_id in list(self.vps_manager.vps_instances.keys()):
                if any(w.get("ip", "") == vps_id for w in self.whitelist):
                    continue

                try:
                    stats = await self.vps_manager.get_vps_stats(vps_id)
                except Exception:
                    stats = None

                anomaly_score = self._score_anomaly(vps_id, stats)
                alerts = []
                alerts.extend(self._check_process_anomalies(vps_id))
                alerts.extend(self._check_ssh_anomalies(vps_id))
                alerts.extend(self._check_network_anomalies(vps_id, stats))

                if anomaly_score > 50 or alerts:
                    self.incidents.append({
                        "id": str(uuid.uuid4())[:8],
                        "vps_id": vps_id,
                        "anomaly_score": anomaly_score,
                        "alerts": alerts,
                        "stats": stats,
                        "detected_at": datetime.now().isoformat(),
                        "status": "open",
                    })
                    self._save_incidents()

            self._save_incidents()
        except Exception as e:
            logger.error(f"Threat detection loop error: {e}")

    @threat_loop.before_loop
    async def before_threat_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="threat_status", description="Show current threat detection status")
    async def threat_status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        open_incidents = [i for i in self.incidents if i["status"] == "open"]
        high_risk = [i for i in open_incidents if i["anomaly_score"] > 75]

        embed = discord.Embed(title="Threat Detection Status", color=0xFF4444 if high_risk else discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Total Incidents", value=str(len(self.incidents)), inline=True)
        embed.add_field(name="Open Incidents", value=str(len(open_incidents)), inline=True)
        embed.add_field(name="High Risk", value=str(len(high_risk)), inline=True)
        embed.add_field(name="Whitelisted IPs", value=str(len(self.whitelist)), inline=True)
        embed.add_field(name="Last Scan", value=datetime.now().strftime("%Y-%m-%d %H:%M"), inline=True)

        if high_risk:
            high_list = "\n".join(f"• {i['vps_id'][:12]} (score: {i['anomaly_score']})" for i in high_risk[:5])
            embed.add_field(name="High Risk VPS", value=high_list, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="threat_incidents", description="List threat incidents")
    async def threat_incidents(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.incidents:
            await interaction.followup.send(embed=discord.Embed(description="No incidents recorded.", color=0x00FF00))
            return

        recent = sorted(self.incidents, key=lambda x: x["detected_at"], reverse=True)[:15]
        embed = discord.Embed(title="Threat Incidents", color=0xFF4444, timestamp=datetime.now())
        for inc in recent:
            icon = {"open": "🔴", "investigating": "🟡", "resolved": "🟢"}.get(inc["status"], "⚪")
            embed.add_field(
                name=f"{icon} #{inc['id']} - {inc['vps_id'][:12]} (Score: {inc['anomaly_score']})",
                value=f"{inc['detected_at'][:19]} | Alerts: {len(inc['alerts'])} | {inc['status']}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="threat_investigate", description="Investigate a threat incident")
    @app_commands.describe(incident_id="Incident ID to investigate")
    async def threat_investigate(self, interaction: discord.Interaction, incident_id: str):
        await interaction.response.defer()

        inc = next((i for i in self.incidents if i["id"] == incident_id), None)
        if not inc:
            await interaction.followup.send(embed=discord.Embed(description="Incident not found.", color=0xFF0000))
            return

        inc["status"] = "investigating"
        self._save_incidents()

        embed = discord.Embed(title=f"Incident Investigation: #{incident_id}", color=0xFFAA00, timestamp=datetime.now())
        embed.add_field(name="VPS", value=inc["vps_id"][:12], inline=True)
        embed.add_field(name="Anomaly Score", value=str(inc["anomaly_score"]), inline=True)
        embed.add_field(name="Detected At", value=inc["detected_at"][:19], inline=True)

        if inc["alerts"]:
            embed.add_field(name="Alerts", value="\n".join(f"• {a}" for a in inc["alerts"]), inline=False)
        else:
            embed.add_field(name="Alerts", value="None", inline=False)

        if inc.get("stats"):
            s = inc["stats"]
            embed.add_field(name="CPU Usage", value=f"{s.get('cpu_usage', 0)}%", inline=True)
            embed.add_field(name="Memory Usage", value=f"{s.get('memory_usage', 0)}%", inline=True)
            net = s.get("network", {})
            embed.add_field(name="Network", value=f"RX: {net.get('rx_bytes', 0)}\nTX: {net.get('tx_bytes', 0)}", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="threat_whitelist", description="Manage IP whitelist for threat detection")
    @app_commands.describe(action="add or remove", ip="IP address or VPS ID to whitelist")
    async def threat_whitelist(self, interaction: discord.Interaction, action: str, ip: str):
        await interaction.response.defer()

        if action == "add":
            if any(w["ip"] == ip for w in self.whitelist):
                await interaction.followup.send(embed=discord.Embed(description=f"{ip} is already whitelisted.", color=0xFFFF00))
                return
            self.whitelist.append({"ip": ip, "added_by": str(interaction.user.id), "added_at": datetime.now().isoformat()})
            self._save_whitelist()
            await interaction.followup.send(embed=discord.Embed(description=f"Added {ip} to whitelist.", color=0x00FF00))
        elif action == "remove":
            self.whitelist = [w for w in self.whitelist if w["ip"] != ip]
            self._save_whitelist()
            await interaction.followup.send(embed=discord.Embed(description=f"Removed {ip} from whitelist.", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description="Action must be 'add' or 'remove'.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(AIThreatDetection(bot))
