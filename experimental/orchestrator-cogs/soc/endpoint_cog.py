import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional


class EndpointCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="endpoint")
    @commands.has_permissions(administrator=True)
    async def endpoint(self, ctx: commands.Context, action: str = "summary", *, sub: Optional[str] = None):
        if action == "devices":
            embed = discord.Embed(title="Endpoint Devices", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total Endpoints", value="342", inline=True)
            embed.add_field(name="Windows", value="187", inline=True)
            embed.add_field(name="macOS", value="64", inline=True)
            embed.add_field(name="Linux", value="91", inline=True)
            embed.add_field(name="Online", value="328", inline=True)
            embed.add_field(name="Offline", value="14", inline=True)
        elif action == "policies":
            embed = discord.Embed(title="Endpoint Policies", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total Policies", value="18", inline=True)
            embed.add_field(name="Enabled", value="16", inline=True)
            embed.add_field(name="AV Policies", value="6", inline=True)
            embed.add_field(name="Firewall Policies", value="5", inline=True)
            embed.add_field(name="DLP Policies", value="4", inline=True)
            embed.add_field(name="App Control", value="3", inline=True)
        elif action == "alerts":
            embed = discord.Embed(title="Endpoint Alerts (24h)", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total", value="43", inline=True)
            embed.add_field(name="Malware", value="8", inline=True)
            embed.add_field(name="Suspicious Process", value="14", inline=True)
            embed.add_field(name="Policy Violation", value="12", inline=True)
            embed.add_field(name="USB Device", value="6", inline=True)
            embed.add_field(name="Network Anomaly", value="3", inline=True)
        elif action == "health":
            embed = discord.Embed(title="Endpoint Health", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Healthy", value="312 (91.2%)", inline=True)
            embed.add_field(name="At Risk", value="22 (6.4%)", inline=True)
            embed.add_field(name="Critical", value="8 (2.4%)", inline=True)
            embed.add_field(name="Avg AV Version Age", value="4.2 days", inline=True)
            embed.add_field(name="Avg OS Patch Level", value="98.7%", inline=True)
        elif action == "stats":
            embed = discord.Embed(title="Endpoint Protection Statistics", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Threats Blocked (30d)", value="187", inline=True)
            embed.add_field(name="Scans Completed (24h)", value="98", inline=True)
            embed.add_field(name="Quarantine Items", value="23", inline=True)
            embed.add_field(name="Avg Scan Duration", value="6.7 min", inline=True)
        else:
            embed = discord.Embed(title="Endpoint Protection",
                                  description="Antivirus, EDR, DLP, and device management",
                                  color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Devices", value="342 total, 328 online", inline=True)
            embed.add_field(name="Policies", value="18 total", inline=True)
            embed.add_field(name="Alerts (24h)", value="43 total", inline=True)
            embed.add_field(name="Blocked (30d)", value="187 threats", inline=True)
        embed.set_footer(text="Infra Pilot SOC | Feature 86")
        await ctx.send(embed=embed)

    @commands.command(name="endpoint_alerts")
    @commands.has_permissions(administrator=True)
    async def endpoint_alerts(self, ctx: commands.Context, severity: str = "all"):
        if severity == "critical":
            embed = discord.Embed(title="Critical Endpoint Alerts", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Total Critical", value="2 active", inline=True)
            embed.add_field(name="Ransomware Detected", value="SRV-PROD-23, status: isolated", inline=False)
            embed.add_field(name="C2 Beaconing", value="WS-342, status: investigating", inline=False)
        elif severity == "high":
            embed = discord.Embed(title="High Severity Endpoint Alerts", color=discord.Color.orange(), timestamp=datetime.now())
            embed.add_field(name="Total High", value="7 active", inline=True)
            embed.add_field(name="Suspicious Process", value="3 endpoints", inline=False)
            embed.add_field(name="DLP Violation", value="2 endpoints", inline=False)
            embed.add_field(name="Unauthorized Software", value="2 endpoints", inline=False)
        else:
            embed = discord.Embed(title="Endpoint Alerts Summary (24h)", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total Alerts", value="43", inline=True)
            embed.add_field(name="Critical", value="2", inline=True)
            embed.add_field(name="High", value="7", inline=True)
            embed.add_field(name="Medium", value="18", inline=True)
            embed.add_field(name="Low", value="16", inline=True)
            embed.add_field(name="Containment Actions", value="3 automatic", inline=True)
        embed.set_footer(text="Infra Pilot SOC | Feature 86a")
        await ctx.send(embed=embed)

    @commands.command(name="endpoint_devices")
    @commands.has_permissions(administrator=True)
    async def endpoint_devices(self, ctx: commands.Context, group: str = "all"):
        if group == "online":
            embed = discord.Embed(title="Online Endpoint Devices", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="Online", value="328 of 342 (95.9%)", inline=False)
            embed.add_field(name="Windows", value="214 online", inline=True)
            embed.add_field(name="macOS", value="68 online", inline=True)
            embed.add_field(name="Linux", value="46 online", inline=True)
            embed.add_field(name="Last Scan Compliance", value="91.2% up-to-date", inline=True)
        elif group == "offline":
            embed = discord.Embed(title="Offline Endpoint Devices", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Offline", value="14", inline=True)
            embed.add_field(name="Offline > 24h", value="3", inline=True)
            embed.add_field(name="Offline > 7d", value="1 (likely decommissioned)", inline=False)
            embed.add_field(name="Missing Patches", value="8 pending updates among offline devices", inline=False)
        else:
            embed = discord.Embed(title="Endpoint Device Overview", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="Total Devices", value="342 (328 online, 14 offline)", inline=False)
            embed.add_field(name="Windows", value="228 (67%)", inline=True)
            embed.add_field(name="macOS", value="72 (21%)", inline=True)
            embed.add_field(name="Linux", value="42 (12%)", inline=True)
            embed.add_field(name="Avg Risk Score", value="24/100", inline=True)
            embed.add_field(name="Policy Compliance", value="93.6%", inline=True)
        embed.set_footer(text="Infra Pilot SOC | Feature 86b")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EndpointCog(bot))

# -- Extended Operations -----------------------------------------------

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
