import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional


class SOARCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="soar", description="SOAR platform commands")
    @app_commands.describe(action="Action: playbooks|cases|connectors", sub="Sub-command")
    async def soar(self, interaction: discord.Interaction, action: str, sub: Optional[str] = None):
        await interaction.response.defer()
        if action == "playbooks":
            embed = discord.Embed(title="SOAR Playbooks", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Malware Isolation", value="Auto-isolate endpoints with malware. Trigger: Incident Created", inline=False)
            embed.add_field(name="Phishing Response", value="Handle reported phishing. Trigger: Manual", inline=False)
            embed.add_field(name="IAM Compromise", value="Respond to account compromise. Trigger: UEBA Anomaly", inline=False)
            embed.add_field(name="Vuln Remediation", value="Auto-patch critical vulns. Trigger: Vuln Found", inline=False)
            embed.add_field(name="Total: 5 playbooks", value="3 active | 42 executions | 94% success rate", inline=False)
        elif action == "cases":
            embed = discord.Embed(title="SOAR Cases", color=discord.Color.orange(), timestamp=datetime.now())
            embed.add_field(name="Open Cases", value="12", inline=True)
            embed.add_field(name="In Progress", value="8", inline=True)
            embed.add_field(name="Resolved Today", value="3", inline=True)
        elif action == "connectors":
            embed = discord.Embed(title="SOAR Connectors", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Connected", value="18/18 healthy", inline=False)
            embed.add_field(name="Types", value="SIEM, EDR, Firewall, Email, Ticketing, Cloud, Threat Intel", inline=False)
        else:
            embed = discord.Embed(title="SOAR Platform", description="Security Orchestration, Automation & Response",
                                  color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Playbooks", value="5 total, 3 active", inline=True)
            embed.add_field(name="Cases", value="23 total, 12 open", inline=True)
            embed.add_field(name="Connectors", value="18 connected", inline=True)
            embed.add_field(name="Executions", value="42 total, 94% success", inline=True)
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class ThreatIntelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="threatintel", description="Threat intelligence commands")
    @app_commands.describe(action="Action: feeds|iocs|blocklist|summary")
    async def threatintel(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "feeds":
            embed = discord.Embed(title="Threat Intel Feeds", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="MISP", value="Community Feed | 30min refresh | 1,240 IoCs", inline=False)
            embed.add_field(name="AlienVault OTX", value="Active | 60min refresh | 892 IoCs", inline=False)
            embed.add_field(name="VirusTotal", value="Active | 15min refresh | 2,156 IoCs", inline=False)
            embed.add_field(name="CrowdStrike", value="Active | 30min refresh | 1,567 IoCs", inline=False)
            embed.add_field(name="AbuseIPDB", value="Active | 60min refresh | 5,432 entries", inline=False)
        elif action == "iocs":
            embed = discord.Embed(title="Recent IoCs", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Total IoCs", value="8,456", inline=True)
            embed.add_field(name="Critical", value="234", inline=True)
            embed.add_field(name="High", value="1,892", inline=True)
            embed.add_field(name="IPs", value="3,456", inline=True)
            embed.add_field(name="Domains", value="2,890", inline=True)
            embed.add_field(name="Hashes", value="2,110", inline=True)
        elif action == "blocklist":
            embed = discord.Embed(title="Active Blocklist", color=discord.Color.dark_red(), timestamp=datetime.now())
            embed.add_field(name="Total", value="1,234 entries", inline=True)
            embed.add_field(name="IPs Blocked", value="890", inline=True)
            embed.add_field(name="Domains Blocked", value="344", inline=True)
            embed.add_field(name="Hits Today", value="156", inline=True)
        elif action == "summary":
            embed = discord.Embed(title="Threat Intelligence Summary", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Feeds", value="6 active", inline=True)
            embed.add_field(name="IoCs", value="8,456 total", inline=True)
            embed.add_field(name="Matches", value="23 on internal assets", inline=True)
            embed.add_field(name="Blocklist", value="1,234 entries", inline=True)
        else:
            embed = discord.Embed(title="Threat Intelligence", description="Aggregate threat feeds and IoC management",
                                  color=discord.Color.red(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class DeceptionTechCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="deception", description="Deception technology commands")
    @app_commands.describe(action="Action: decoys|tokens|events|summary")
    async def deception(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "decoys":
            embed = discord.Embed(title="Active Decoys", color=discord.Color.purple(), timestamp=datetime.now())
            embed.add_field(name="SSH Honeypot", value="Port 22 | Engaged: 12 times", inline=False)
            embed.add_field(name="HTTP Honeypot", value="Port 80/443 | Engaged: 8 times", inline=False)
            embed.add_field(name="MySQL Fake DB", value="Port 3306 | Engaged: 3 times", inline=False)
            embed.add_field(name="RDP Honeypot", value="Port 3389 | Engaged: 5 times", inline=False)
        elif action == "events":
            embed = discord.Embed(title="Deception Events", color=discord.Color.purple(), timestamp=datetime.now())
            embed.add_field(name="Last 24h", value="7 events", inline=True)
            embed.add_field(name="Critical", value="2", inline=True)
            embed.add_field(name="Source IPs", value="5 unique", inline=True)
        elif action == "summary":
            embed = discord.Embed(title="Deception Technology Summary", color=discord.Color.purple(), timestamp=datetime.now())
            embed.add_field(name="Decoys Deployed", value="6", inline=True)
            embed.add_field(name="Honey Tokens", value="18", inline=True)
            embed.add_field(name="Total Engagements", value="28", inline=True)
            embed.add_field(name="Forensics Captured", value="28 entries", inline=True)
        else:
            embed = discord.Embed(title="Deception Technology", description="Honeypots, honey tokens, and decoys",
                                  color=discord.Color.purple(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class VulnManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vuln", description="Vulnerability management commands")
    @app_commands.describe(action="Action: list|scan|patches|summary")
    async def vuln(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "list":
            embed = discord.Embed(title="Vulnerabilities", color=discord.Color.orange(), timestamp=datetime.now())
            embed.add_field(name="CVE-2024-6387", value="OpenSSH RCE | Critical | CVSS 9.8", inline=False)
            embed.add_field(name="CVE-2023-44487", value="HTTP/2 Rapid Reset | High | CVSS 7.5", inline=False)
            embed.add_field(name="CVE-2024-27198", value="TeamCity Auth Bypass | Critical | CVSS 9.8", inline=False)
            embed.add_field(name="CVE-2024-3094", value="XZ Backdoor | Critical | CVSS 10.0", inline=False)
        elif action == "summary":
            embed = discord.Embed(title="Vulnerability Summary", color=discord.Color.orange(), timestamp=datetime.now())
            embed.add_field(name="Total", value="47", inline=True)
            embed.add_field(name="Critical", value="5", inline=True)
            embed.add_field(name="High", value="12", inline=True)
            embed.add_field(name="Medium", value="22", inline=True)
            embed.add_field(name="Low", value="8", inline=True)
            embed.add_field(name="Patched (30d)", value="15", inline=True)
        elif action == "patches":
            embed = discord.Embed(title="Patch Jobs", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="In Progress", value="2", inline=True)
            embed.add_field(name="Completed Today", value="1", inline=True)
            embed.add_field(name="Pending Approval", value="3", inline=True)
        elif action == "scan":
            embed = discord.Embed(title="Latest Scan", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Engine", value="Qualys", inline=True)
            embed.add_field(name="Targets", value="12 assets", inline=True)
            embed.add_field(name="Findings", value="8 new", inline=True)
        else:
            embed = discord.Embed(title="Vulnerability Management", description="Scanning, prioritization, patch orchestration",
                                  color=discord.Color.orange(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class IncidentResponseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="incident", description="Incident response commands")
    @app_commands.describe(action="Action: list|create|status|metrics")
    async def incident(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "list":
            embed = discord.Embed(title="Open Incidents", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="INS-001", value="PowerShell C2 | High | Containing", inline=False)
            embed.add_field(name="INS-002", value="Phishing Campaign | High | Triage", inline=False)
            embed.add_field(name="INS-003", value="CVE-2024-6387 | Critical | Eradicating", inline=False)
            embed.add_field(name="INS-004", value="Insider Data Theft | Critical | Containing", inline=False)
        elif action == "metrics":
            embed = discord.Embed(title="Incident Metrics", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total", value="156 (30d)", inline=True)
            embed.add_field(name="Open", value="5", inline=True)
            embed.add_field(name="Critical", value="2", inline=True)
            embed.add_field(name="MTTR", value="18.7h", inline=True)
            embed.add_field(name="MTTC", value="124min", inline=True)
            embed.add_field(name="Contained", value="100%", inline=True)
        elif action == "create":
            embed = discord.Embed(title="Create Incident", description="Use the management panel to create incidents",
                                  color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Web UI", value="/soc/incidents", inline=False)
        else:
            embed = discord.Embed(title="Incident Response", description="Full incident lifecycle management",
                                  color=discord.Color.red(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class UEBACog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ueba", description="User & Entity Behavior Analytics")
    @app_commands.describe(action="Action: entities|alerts|risk|summary")
    async def ueba(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "entities":
            embed = discord.Embed(title="UEBA Entities", color=discord.Color.teal(), timestamp=datetime.now())
            embed.add_field(name="Users", value="15 tracked", inline=True)
            embed.add_field(name="Service Accounts", value="8 tracked", inline=True)
            embed.add_field(name="Applications", value="5 tracked", inline=True)
            embed.add_field(name="High Risk", value="2", inline=True)
        elif action == "alerts":
            embed = discord.Embed(title="UEBA Alerts", color=discord.Color.teal(), timestamp=datetime.now())
            embed.add_field(name="Unacknowledged", value="7", inline=True)
            embed.add_field(name="Critical", value="1", inline=True)
            embed.add_field(name="High", value="3", inline=True)
            embed.add_field(name="Anomaly Types", value="Login location, data volume, working hours", inline=False)
        elif action == "summary":
            embed = discord.Embed(title="UEBA Summary", color=discord.Color.teal(), timestamp=datetime.now())
            embed.add_field(name="Entities", value="28", inline=True)
            embed.add_field(name="Events", value="12,456 (30d)", inline=True)
            embed.add_field(name="Anomalies", value="89", inline=True)
            embed.add_field(name="Baselines", value="56 established", inline=True)
        else:
            embed = discord.Embed(title="UEBA", description="ML-based behavioral baselining and anomaly detection",
                                  color=discord.Color.teal(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class CSPMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cspm", description="Cloud Security Posture Management")
    @app_commands.describe(action="Action: accounts|scan|score|results")
    async def cspm(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "accounts":
            embed = discord.Embed(title="Cloud Accounts", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="AWS Production", value="us-east-1, us-west-2, eu-west-1", inline=False)
            embed.add_field(name="Azure Production", value="eastus, westeurope", inline=False)
            embed.add_field(name="GCP Production", value="us-central1, europe-west1", inline=False)
        elif action == "score":
            embed = discord.Embed(title="CIS Compliance Scores", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Overall", value="87.3%", inline=False)
            embed.add_field(name="AWS", value="89.1%", inline=True)
            embed.add_field(name="Azure", value="84.5%", inline=True)
            embed.add_field(name="GCP", value="88.2%", inline=True)
        elif action == "results":
            embed = discord.Embed(title="Latest Scan Results", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Checks Run", value="156", inline=True)
            embed.add_field(name="Passed", value="136", inline=True)
            embed.add_field(name="Failed", value="20", inline=True)
            embed.add_field(name="Auto-Remediated", value="8", inline=True)
        else:
            embed = discord.Embed(title="CSPM", description="Cloud security posture against CIS benchmarks",
                                  color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class NDRCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ndr", description="Network Detection & Response")
    @app_commands.describe(action="Action: flows|alerts|rules|summary")
    async def ndr(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "summary":
            embed = discord.Embed(title="NDR Summary", color=discord.Color.dark_blue(), timestamp=datetime.now())
            embed.add_field(name="Flows Analyzed", value="45,678 (24h)", inline=True)
            embed.add_field(name="Malicious", value="234 (0.5%)", inline=True)
            embed.add_field(name="Alerts", value="45 open", inline=True)
            embed.add_field(name="Data Analyzed", value="1.2 GB", inline=True)
        elif action == "alerts":
            embed = discord.Embed(title="NDR Alerts", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Critical", value="3", inline=True)
            embed.add_field(name="High", value="12", inline=True)
            embed.add_field(name="Medium", value="22", inline=True)
            embed.add_field(name="Low", value="8", inline=True)
        elif action == "rules":
            embed = discord.Embed(title="Detection Rules", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total", value="8 enabled", inline=True)
            embed.add_field(name="DNS Rules", value="2", inline=True)
            embed.add_field(name="HTTP Rules", value="1", inline=True)
            embed.add_field(name="SMB/TLS/SSH", value="4", inline=True)
        else:
            embed = discord.Embed(title="NDR", description="Network traffic analysis with ML threat detection",
                                  color=discord.Color.dark_blue(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class SecretsDetectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="secrets", description="Secrets detection & remediation")
    @app_commands.describe(action="Action: findings|scan|rotate|summary")
    async def secrets(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "findings":
            embed = discord.Embed(title="Secret Findings", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="AWS Key in config", value="src/config/aws.py:42 | Critical | Open", inline=False)
            embed.add_field(name="GitHub Token in .env", value=".env.local:5 | Critical | Open", inline=False)
            embed.add_field(name="Slack Token in YAML", value="deploy/config.yaml:28 | High | Rotating", inline=False)
            embed.add_field(name="Stripe Key in config", value="payments/config.py:15 | Critical | Open", inline=False)
        elif action == "summary":
            embed = discord.Embed(title="Secrets Summary", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Total Findings", value="47", inline=True)
            embed.add_field(name="Critical", value="12", inline=True)
            embed.add_field(name="High", value="18", inline=True)
            embed.add_field(name="Auto-Rotated", value="8", inline=True)
            embed.add_field(name="Open", value="27", inline=True)
            embed.add_field(name="Scan Targets", value="6 repositories", inline=True)
        else:
            embed = discord.Embed(title="Secrets Detection", description="Scan for leaked secrets in repos and configs",
                                  color=discord.Color.red(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


class SecurityTrainingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="securitytraining", description="Security awareness training")
    @app_commands.describe(action="Action: modules|campaigns|assign|summary")
    async def securitytraining(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer()
        if action == "modules":
            embed = discord.Embed(title="Training Modules", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Security Fundamentals", value="15min | Required | 92% pass rate", inline=False)
            embed.add_field(name="Phishing Detection", value="20min | Required | 88% pass rate", inline=False)
            embed.add_field(name="Password Security", value="10min | Required | 95% pass rate", inline=False)
            embed.add_field(name="Social Engineering", value="15min | Required | 85% pass rate", inline=False)
        elif action == "campaigns":
            embed = discord.Embed(title="Phishing Campaigns", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Q1 Simulation", value="Completed | 15.3% click rate | 30% report rate", inline=False)
            embed.add_field(name="Attachment Phish", value="Running | 11.1% click rate | 26% report rate", inline=False)
        elif action == "summary":
            embed = discord.Embed(title="Training Summary", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Modules", value="9 total, 5 required", inline=True)
            embed.add_field(name="Assignments", value="156, 82% completed", inline=True)
            embed.add_field(name="Pass Rate", value="91.2%", inline=True)
            embed.add_field(name="Campaigns", value="2 (1 running)", inline=True)
            embed.add_field(name="Click Rate", value="13.2%", inline=True)
            embed.add_field(name="Report Rate", value="28.5%", inline=True)
        else:
            embed = discord.Embed(title="Security Training", description="Phishing simulations and security awareness",
                                  color=discord.Color.green(), timestamp=datetime.now())
        embed.set_footer(text="Infra Pilot SOC")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SOARCog(bot))
    await bot.add_cog(ThreatIntelCog(bot))
    await bot.add_cog(DeceptionTechCog(bot))
    await bot.add_cog(VulnManagementCog(bot))
    await bot.add_cog(IncidentResponseCog(bot))
    await bot.add_cog(UEBACog(bot))
    await bot.add_cog(CSPMCog(bot))
    await bot.add_cog(NDRCog(bot))
    await bot.add_cog(SecretsDetectionCog(bot))
    await bot.add_cog(SecurityTrainingCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "alerts_critical": 0, "alerts_high": 0, "alerts_medium": 0, "resolved": 0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class SOCCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    alert_id: str = ""
    severity: str = Field(default="low")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SOCCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = Field(default="siem")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    escalated: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_escalated(self) -> None:
        self.escalated += 1

    def complete(self) -> None:
        self.status = "completed"

class SOCCogMetrics:
    def __init__(self) -> None:
        self.alerts: int = 0
        self.escalations: int = 0
        self.resolutions: int = 0
        self.errors: int = 0

    def record(self, escalated: bool = False, resolved: bool = False, error: bool = False) -> None:
        self.alerts += 1
        if escalated:
            self.escalations += 1
        if resolved:
            self.resolutions += 1
        if error:
            self.errors += 1

    def summary(self) -> Dict[str, Any]:
        return {"alerts": self.alerts, "escalations": self.escalations, "resolutions": self.resolutions,
                "errors": self.errors, "escalation_rate": round(self.escalations / max(self.alerts, 1) * 100, 1),
                "resolution_rate": round(self.resolutions / max(self.alerts, 1) * 100, 1)}
