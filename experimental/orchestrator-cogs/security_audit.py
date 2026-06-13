import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

from config import config
from vps_manager import VPSManager


class SecurityAudit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    async def _audit_container(self, container_id: str) -> dict:
        findings = {}
        try:
            container = self.vps_manager.client.containers.get(container_id)

            # Check exposed ports
            port_info = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            open_ports = []
            for port, mappings in port_info.items():
                if mappings:
                    for m in mappings:
                        open_ports.append(f"{port} -> {m.get('HostIp', '0.0.0.0')}:{m.get('HostPort', '?')}")
            findings["open_ports"] = open_ports or ["No exposed ports"]

            # Check capabilities
            host_config = container.attrs.get("HostConfig", {})
            privileged = host_config.get("Privileged", False)
            findings["privileged"] = privileged

            cap_add = host_config.get("CapAdd", [])
            findings["capabilities"] = cap_add or ["None"]

            # Check image
            findings["image"] = container.attrs.get("Config", {}).get("Image", "unknown")

            # Check restart policy
            restart_policy = host_config.get("RestartPolicy", {}).get("Name", "none")
            findings["restart_policy"] = restart_policy

            # Check security options
            sec_opts = host_config.get("SecurityOpt", [])
            findings["security_options"] = sec_opts or ["None"]

            # Check resource limits
            findings["memory_limit"] = host_config.get("Memory", 0)
            findings["cpu_shares"] = host_config.get("CpuShares", 0)

        except Exception as e:
            findings["error"] = str(e)

        return findings

    def _generate_recommendations(self, findings: dict) -> list:
        recs = []

        if findings.get("privileged"):
            recs.append("Container runs in privileged mode - avoid unless absolutely necessary")

        if not findings.get("security_options") or findings["security_options"] == ["None"]:
            recs.append("No security options set - consider adding seccomp or AppArmor profiles")

        if findings.get("restart_policy") == "always":
            recs.append("Restart policy is 'always' - consider 'unless-stopped' to prevent unexpected restarts")

        return recs

    @app_commands.command(name="securityaudit", description="Run a security audit on a VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def security_audit(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        findings = await self._audit_container(vps_id)
        recommendations = self._generate_recommendations(findings)

        embed = discord.Embed(title=f"Security Audit: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())

        embed.add_field(name="Image", value=findings.get("image", "N/A"), inline=True)
        embed.add_field(name="Privileged", value="⚠️ Yes" if findings.get("privileged") else "✅ No", inline=True)
        embed.add_field(name="Restart Policy", value=findings.get("restart_policy", "N/A"), inline=True)

        ports = findings.get("open_ports", [])
        embed.add_field(name=f"Open Ports ({len(ports)})", value="\n".join(ports[:5]) or "None", inline=False)

        caps = findings.get("capabilities", [])
        embed.add_field(name="Capabilities", value="\n".join(caps[:5]) or "None", inline=False)

        if recommendations:
            embed.add_field(name="Recommendations", value="\n".join(f"• {r}" for r in recommendations), inline=False)
        else:
            embed.add_field(name="Recommendations", value="No issues found", inline=False)

        if findings.get("error"):
            embed.add_field(name="Error", value=findings["error"], inline=False)
            embed.color = discord.Color.red()

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SecurityAudit(bot))
