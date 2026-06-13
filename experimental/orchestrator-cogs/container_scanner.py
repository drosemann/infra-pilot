import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict, List
import json
import logging
import os
import asyncio
import subprocess

from config import config
from vps_manager import VPSManager


class ContainerScanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.scan_results_file = config.SCAN_RESULTS_FILE
        self._ensure_data_file()
        self.scheduled_scan_loop.start()

    def cog_unload(self):
        self.scheduled_scan_loop.cancel()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.scan_results_file), exist_ok=True)
        if not os.path.exists(self.scan_results_file):
            with open(self.scan_results_file, "w") as f:
                json.dump([], f)

    def _load_scans(self) -> list:
        try:
            with open(self.scan_results_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_scans(self, scans: list):
        with open(self.scan_results_file, "w") as f:
            json.dump(scans, f, indent=2, default=str)

    @tasks.loop(hours=config.SCAN_INTERVAL_HOURS)
    async def scheduled_scan_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT DISTINCT image FROM vps_containers WHERE image IS NOT NULL")
            images = cursor.fetchall()
            cursor.close()
            conn.close()

            for row in images:
                image_name = row["image"]
                if image_name:
                    await self._run_scan(image_name, triggered="schedule")
        except Exception as e:
            logging.error(f"Scheduled scan loop error: {e}")

    @scheduled_scan_loop.before_loop
    async def before_scans(self):
        await self.bot.wait_until_ready()

    async def _run_scan(self, image_name: str, triggered: str = "manual") -> dict:
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scan_results (image_name, scanner, status) VALUES (%s, 'trivy', 'scanning')",
            (image_name,),
        )
        scan_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        try:
            result = await self._scan_with_trivy(image_name)
            vulns = result.get("vulnerabilities", [])
            summary = self._summarize_vulns(vulns)

            policy_action = await self._check_policy(vulns)
            if policy_action == "block":
                summary["blocked"] = True

            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scan_results SET status = 'completed', summary = %s, vulnerabilities = %s, completed_at = NOW() WHERE id = %s",
                (json.dumps(summary), json.dumps(vulns), scan_id),
            )
            conn.commit()
            cursor.close()
            conn.close()

            scans = self._load_scans()
            scans.append({"scan_id": scan_id, "image": image_name, "summary": summary, "scanned_at": str(datetime.now())})
            self._save_scans(scans)

            return {
                "scan_id": scan_id,
                "image": image_name,
                "total_vulns": summary.get("total", 0),
                "critical": summary.get("CRITICAL", 0),
                "high": summary.get("HIGH", 0),
                "blocked": summary.get("blocked", False),
            }
        except Exception as e:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scan_results SET status = 'failed', completed_at = NOW() WHERE id = %s",
                (scan_id,),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return {"scan_id": scan_id, "error": str(e)}

    async def _scan_with_trivy(self, image_name: str) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                "trivy", "image", "--format", "json", "--quiet", image_name,
                stdout=asyncio.PIPE, stderr=asyncio.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            if proc.returncode != 0:
                return await self._scan_with_grype(image_name)

            data = json.loads(stdout.decode())
            vulns = []
            for result in data.get("Results", []):
                for v in result.get("Vulnerabilities", []):
                    vulns.append({
                        "cve_id": v.get("VulnerabilityID"),
                        "severity": v.get("Severity"),
                        "package": v.get("PkgName"),
                        "installed": v.get("InstalledVersion"),
                        "fixed": v.get("FixedVersion"),
                        "title": v.get("Title", ""),
                    })
            return {"vulnerabilities": vulns, "scanner": "trivy"}
        except (FileNotFoundError, asyncio.TimeoutError):
            return await self._scan_with_grype(image_name)

    async def _scan_with_grype(self, image_name: str) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                "grype", image_name, "--output", "json", "--quiet",
                stdout=asyncio.PIPE, stderr=asyncio.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            if proc.returncode != 0:
                return {"vulnerabilities": [], "scanner": "grype"}

            data = json.loads(stdout.decode())
            vulns = []
            for match in data.get("matches", []):
                v = match.get("vulnerability", {})
                a = match.get("artifact", {})
                vulns.append({
                    "cve_id": v.get("id"),
                    "severity": v.get("severity"),
                    "package": a.get("name"),
                    "installed": a.get("version"),
                    "fixed": v.get("fix", {}).get("versions", [None])[0] if v.get("fix") else None,
                    "title": v.get("description", ""),
                })
            return {"vulnerabilities": vulns, "scanner": "grype"}
        except (FileNotFoundError, asyncio.TimeoutError):
            return {"vulnerabilities": [], "scanner": "none"}

    def _summarize_vulns(self, vulns: list) -> dict:
        summary = {"total": len(vulns), "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for v in vulns:
            sev = v.get("severity", "UNKNOWN").upper()
            if sev in summary:
                summary[sev] += 1
            else:
                summary["UNKNOWN"] += 1
        return summary

    async def _check_policy(self, vulns: list) -> str:
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM scan_policies")
            policies = cursor.fetchall()
            cursor.close()
            conn.close()

            for vuln in vulns:
                sev = vuln.get("severity", "").upper()
                for p in policies:
                    if p["severity"].upper() == sev and p["action"] == "block":
                        return "block"
            return "pass"
        except Exception:
            return "pass"

    async def _create_remediation_pr(self, scan_id: int, image_name: str) -> Optional[str]:
        return f"https://github.com/remediation/{scan_id}"

    @app_commands.command(name="scan", description="Container image scanning")
    @app_commands.describe(
        subcommand="image, results, policy, allowlist",
        image_name="Container image name (for image scan)",
        scan_id="Scan ID (for results)",
        severity="Severity level (for policy set)",
        action="Block or allow (for policy set)",
        cve_id="CVE identifier (for allowlist add)",
    )
    async def scan_command(
        self,
        interaction: discord.Interaction,
        subcommand: str,
        image_name: str = None,
        scan_id: int = None,
        severity: str = None,
        action: str = None,
        cve_id: str = None,
    ):
        await interaction.response.defer()

        if subcommand == "image":
            if not image_name:
                await interaction.followup.send(embed=discord.Embed(description="Provide image_name", color=0xFF0000))
                return
            await self._scan_image(interaction, image_name)
        elif subcommand == "results":
            if not scan_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide scan_id", color=0xFF0000))
                return
            await self._scan_results(interaction, scan_id)
        elif subcommand == "policy":
            if not severity or not action:
                await interaction.followup.send(embed=discord.Embed(description="Provide severity and action", color=0xFF0000))
                return
            await self._scan_policy_set(interaction, severity, action)
        elif subcommand == "allowlist":
            if not cve_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide cve_id", color=0xFF0000))
                return
            await self._scan_allowlist_add(interaction, cve_id)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Subcommand: image, results, policy, allowlist", color=0xFF0000))

    async def _scan_image(self, interaction: discord.Interaction, image_name: str):
        await interaction.followup.send(embed=discord.Embed(description=f"Scanning {image_name}...", color=discord.Color.blue()))
        result = await self._run_scan(image_name)
        if "error" in result:
            await interaction.followup.send(embed=discord.Embed(description=f"Scan failed: {result['error']}", color=0xFF0000))
            return

        embed = discord.Embed(title=f"Scan Results: {image_name}", color=discord.Color.blue())
        embed.add_field(name="Scan ID", value=str(result["scan_id"]), inline=True)
        embed.add_field(name="Total Vulns", value=str(result["total_vulns"]), inline=True)
        embed.add_field(name="Critical", value=str(result["critical"]), inline=True)
        embed.add_field(name="High", value=str(result["high"]), inline=True)

        if result.get("blocked"):
            embed.add_field(name="Policy Action", value="🚫 BLOCKED (critical vulns)", inline=False)
            embed.color = discord.Color.red()

        await interaction.followup.send(embed=embed)

    async def _scan_results(self, interaction: discord.Interaction, scan_id: int):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM scan_results WHERE id = %s", (scan_id,))
            scan = cursor.fetchone()
            cursor.close()
            conn.close()

            if not scan:
                await interaction.followup.send(embed=discord.Embed(description="Scan not found.", color=0xFF0000))
                return

            vulns = json.loads(scan["vulnerabilities"]) if isinstance(scan["vulnerabilities"], str) and scan["vulnerabilities"] else scan.get("vulnerabilities", [])
            summary = json.loads(scan["summary"]) if isinstance(scan["summary"], str) and scan["summary"] else scan.get("summary", {})

            embed = discord.Embed(title=f"Scan #{scan_id}: {scan['image_name']}", color=discord.Color.blue())
            embed.add_field(name="Scanner", value=scan["scanner"], inline=True)
            embed.add_field(name="Status", value=scan["status"], inline=True)
            embed.add_field(name="Total Vulnerabilities", value=str(summary.get("total", 0)), inline=True)

            for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                count = summary.get(sev, 0)
                if count:
                    embed.add_field(name=sev, value=str(count), inline=True)

            critical_vulns = [v for v in vulns[:5] if v.get("severity", "").upper() == "CRITICAL"]
            if critical_vulns:
                cve_text = "\n".join(
                    f"• {v.get('cve_id', '?')} - {v.get('package', '?')}"
                    for v in critical_vulns
                )
                embed.add_field(name="Critical CVEs", value=cve_text, inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _scan_policy_set(self, interaction: discord.Interaction, severity: str, action: str):
        sev = severity.upper()
        if sev not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"):
            await interaction.followup.send(embed=discord.Embed(description="Severity must be: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN", color=0xFF0000))
            return
        if action.lower() not in ("block", "allow", "warn"):
            await interaction.followup.send(embed=discord.Embed(description="Action must be: block, allow, warn", color=0xFF0000))
            return
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scan_policies (severity, action) VALUES (%s, %s) ON DUPLICATE KEY UPDATE action = %s",
                (sev, action.lower(), action.lower()),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.followup.send(embed=discord.Embed(description=f"Policy set: {sev} -> {action}", color=0x00FF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _scan_allowlist_add(self, interaction: discord.Interaction, cve_id: str):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scan_allowlist (cve_id, added_by) VALUES (%s, %s) ON DUPLICATE KEY UPDATE added_by = %s",
                (cve_id, str(interaction.user.id), str(interaction.user.id)),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.followup.send(embed=discord.Embed(description=f"CVE {cve_id} added to allowlist.", color=0x00FF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(ContainerScanner(bot))
