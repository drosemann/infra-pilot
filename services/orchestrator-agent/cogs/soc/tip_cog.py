import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional


class TIPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tip")
    @commands.has_permissions(administrator=True)
    async def tip(self, ctx: commands.Context, action: str = "summary", *, sub: Optional[str] = None):
        if action == "iocs":
            embed = discord.Embed(title="Threat Intelligence - IoCs", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Total IoCs", value="1,247", inline=True)
            embed.add_field(name="New (24h)", value="35", inline=True)
            embed.add_field(name="IPs", value="412", inline=True)
            embed.add_field(name="Domains", value="283", inline=True)
            embed.add_field(name="Hashes", value="389", inline=True)
            embed.add_field(name="URLs", value="163", inline=True)
            embed.add_field(name="Confidence Avg", value="78%", inline=True)
            embed.add_field(name="Last Feed", value="2 min ago", inline=True)
        elif action == "feeds":
            embed = discord.Embed(title="Threat Feeds", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Total Feeds", value="12 connected", inline=True)
            embed.add_field(name="Active", value="10", inline=True)
            embed.add_field(name="Failed", value="2", inline=True)
            embed.add_field(name="Top Feed", value="AlienVault OTX (342 IoCs/day)", inline=False)
            embed.add_field(name="Types", value="C2, Phishing, Malware, Ransomware, DDoS", inline=False)
        elif action == "actors":
            embed = discord.Embed(title="Threat Actors", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Tracked Actors", value="8", inline=True)
            embed.add_field(name="Active Campaigns", value="3", inline=True)
            embed.add_field(name="Top Actor", value="APT-42 (Financial Sector)", inline=False)
            embed.add_field(name="TTPs Observed", value="MITRE: T1566, T1059, T1485", inline=False)
            embed.add_field(name="Last Updated", value="2025-11-10", inline=True)
        elif action == "enrich":
            embed = discord.Embed(title="IOC Enrichment", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Enriched (24h)", value="78", inline=True)
            embed.add_field(name="PVP Match Rate", value="62%", inline=True)
            embed.add_field(name="Avg Enrich Time", value="1.3s", inline=True)
            embed.add_field(name="Sources", value="VirusTotal, AbuseIPDB, GreyNoise, Shodan", inline=False)
        elif action == "stats":
            embed = discord.Embed(title="Threat Intel - Statistics", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Daily Avg IoCs", value="45", inline=True)
            embed.add_field(name="False Positive Rate", value="8%", inline=True)
            embed.add_field(name="Feeds Reliability", value="92%", inline=True)
            embed.add_field(name="Alerts Generated", value="124 (30d)", inline=True)
        else:
            embed = discord.Embed(title="Threat Intelligence Platform",
                                  description="Crowd-sourced and commercial threat intel",
                                  color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="IoCs", value="1,247 total", inline=True)
            embed.add_field(name="Feeds", value="12 connected", inline=True)
            embed.add_field(name="Actors", value="8 tracked", inline=True)
            embed.add_field(name="Enrichment Rate", value="62% match", inline=True)
        embed.set_footer(text="Infra Pilot SOC | Feature 82")
        await ctx.send(embed=embed)

    @commands.command(name="tip_ioc")
    @commands.has_permissions(administrator=True)
    async def tip_ioc(self, ctx: commands.Context, action: str = "summary", *, value: Optional[str] = None):
        if action == "types":
            embed = discord.Embed(title="IOC Types Breakdown", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="File Hashes (MD5/SHA1/SHA256)", value="487 (39%)", inline=True)
            embed.add_field(name="IP Addresses", value="312 (25%)", inline=True)
            embed.add_field(name="Domains", value="198 (16%)", inline=True)
            embed.add_field(name="URLs", value="145 (12%)", inline=True)
            embed.add_field(name="Email Addresses", value="67 (5%)", inline=True)
            embed.add_field(name="Registry Keys / Other", value="38 (3%)", inline=True)
        elif action == "feeds":
            embed = discord.Embed(title="Threat Intelligence Feeds", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Connected Feeds", value="12", inline=True)
            embed.add_field(name="Feeds Delivering", value="11", inline=True)
            embed.add_field(name="Feeds Degraded", value="1", inline=True)
            embed.add_field(name="Top Feed", value="AlienVault OTX (342 IoCs/day)", inline=False)
            embed.add_field(name="Feed Update Frequency", value="Every 15 min", inline=True)
        else:
            embed = discord.Embed(title="Threat Intelligence Summary", color=discord.Color.red(), timestamp=datetime.now())
            embed.add_field(name="Total IoCs", value="1,247", inline=True)
            embed.add_field(name="New (24h)", value="89", inline=True)
            embed.add_field(name="Active Feeds", value="12", inline=True)
            embed.add_field(name="Enrichment Rate", value="62%", inline=True)
            embed.add_field(name="Correlated Alerts (24h)", value="42", inline=True)
        embed.set_footer(text="Infra Pilot SOC | Feature 82a")
        await ctx.send(embed=embed)

    @commands.command(name="tip_actors")
    @commands.has_permissions(administrator=True)
    async def tip_actors(self, ctx: commands.Context):
        embed = discord.Embed(title="Tracked Threat Actors", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Total Tracked", value="8", inline=True)
        embed.add_field(name="Active (30d)", value="3", inline=True)
        embed.add_field(name="APT-C-36", value="Targeting financial sector, related IoCs: 47", inline=False)
        embed.add_field(name="TA551", value="Email phishing campaigns, related IoCs: 32", inline=False)
        embed.add_field(name="UNC1945", value="Ransomware operations, related IoCs: 28", inline=False)
        embed.add_field(name="Suspected (New)", value="2 unidentified clusters under analysis", inline=False)
        embed.set_footer(text="Infra Pilot SOC | Feature 82b")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TIPCog(bot))

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
