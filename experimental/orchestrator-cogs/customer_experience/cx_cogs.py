import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthScoringCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="health", description="View customer health profile")
    @app_commands.describe(customer_id="Customer ID")
    async def health_profile(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/profile/{customer_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(title=f"Health Profile: {customer_id}", color=discord.Color.green() if data.get("composite_score", 0) >= 70 else discord.Color.orange())
                    embed.add_field(name="Composite Score", value=f"{data.get('composite_score', 'N/A')}/100", inline=True)
                    embed.add_field(name="Risk Level", value=data.get("risk_level", "N/A").upper(), inline=True)
                    embed.add_field(name="Churn Probability", value=f"{data.get('churn_probability', 0)*100:.1f}%", inline=True)
                    embed.add_field(name="Trend", value=data.get("trend", "N/A"), inline=True)
                    for comp in data.get("components", []):
                        embed.add_field(name=f"{comp['category'].title()} Score", value=f"{comp['score']}/100 ({comp['trend']})", inline=True)
                    if data.get("recommendations"):
                        embed.add_field(name="Recommendations", value="\n".join(f"• {r}" for r in data["recommendations"][:3]), inline=False)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(embed=discord.Embed(description="Customer not found", color=0xFF0000))
        except Exception as e:
            logger.error(f"Health profile error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthstats", description="Health scoring statistics")
    async def health_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Customer Health Stats", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Customers", value=data.get("total_customers", 0), inline=True)
                embed.add_field(name="Average Score", value=data.get("average_score", 0), inline=True)
                embed.add_field(name="At Risk", value=data.get("at_risk_count", 0), inline=True)
                segments = data.get("segments", {})
                for k, v in segments.items():
                    embed.add_field(name=k.title(), value=v, inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthrisk", description="List at-risk customer profiles")
    async def health_at_risk(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/at-risk") as resp:
                data = await resp.json()
                profiles = data.get("profiles", [])
                embed = discord.Embed(title=f"At-Risk Profiles ({len(profiles)})", color=discord.Color.red(), timestamp=datetime.now())
                for p in profiles[:8]:
                    embed.add_field(name=f"{p.get('customer_name', p.get('customer_id', '?'))} [{p.get('risk_level', '?')}]", value=f"Health: {p.get('overall_health_score', '?')} | Trend: {p.get('trend', '?')}", inline=False)
                if not profiles:
                    embed.description = "No at-risk profiles"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health risk error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthdistribution", description="Health score distribution")
    async def health_distribution(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/distribution") as resp:
                data = await resp.json()
                buckets = data.get("buckets", {})
                embed = discord.Embed(title="Health Score Distribution", color=discord.Color.blue(), timestamp=datetime.now())
                for k, v in sorted(buckets.items()):
                    bar = "█" * min(v, 20) + "░" * max(0, 20 - min(v, 20))
                    embed.add_field(name=f"{k}", value=f"{bar} {v}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health distribution error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthtrend", description="Health score trends")
    async def health_trend(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/trend?days={days}") as resp:
                data = await resp.json()
                points = data.get("points", [])
                embed = discord.Embed(title=f"Health Score Trend ({days}d)", color=discord.Color.green(), timestamp=datetime.now())
                for p in points[-7:]:
                    arrow = "⬆" if p.get('trend') == 'improving' else "⬇" if p.get('trend') == 'declining' else "➡"
                    embed.add_field(name=p.get('date','?'), value=f"{arrow} Score: {p.get('avg_score',0)}", inline=True)
                if not points:
                    embed.description = "No trend data available"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health trend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthchurn", description="Customers at churn risk")
    async def health_churn(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/churn-risk") as resp:
                data = await resp.json()
                customers = data.get("customers", [])
                embed = discord.Embed(title=f"Churn Risk ({len(customers)})", color=discord.Color.red(), timestamp=datetime.now())
                for c in customers[:5]:
                    embed.add_field(name=c.get('customer_name', c.get('customer_id', '?')), value=f"Score: {c.get('churn_probability', 0)*100:.0f}%", inline=False)
                if not customers:
                    embed.description = "No customers at churn risk"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Churn risk error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class TicketingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="ticket", description="View support ticket details")
    @app_commands.describe(ticket_id="Ticket ID")
    async def get_ticket(self, interaction: discord.Interaction, ticket_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/{ticket_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(title=f"Ticket: {ticket_id}", description=data.get("subject", ""), color=discord.Color.blue(), timestamp=datetime.now())
                    embed.add_field(name="Status", value=data.get("status", "N/A"), inline=True)
                    embed.add_field(name="Priority", value=data.get("priority", "N/A"), inline=True)
                    embed.add_field(name="Customer", value=data.get("customer_name", "N/A"), inline=True)
                    embed.add_field(name="Assigned To", value=data.get("assigned_to", "Unassigned"), inline=True)
                    embed.add_field(name="SLA", value="Breached" if data.get("sla_breached") else "OK", inline=True)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(embed=discord.Embed(description="Ticket not found", color=0xFF0000))
        except Exception as e:
            logger.error(f"Get ticket error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="tickets", description="List support tickets")
    @app_commands.describe(status="Filter by status")
    async def list_tickets(self, interaction: discord.Interaction, status: str = None):
        await interaction.response.defer()
        try:
            params = f"?status={status}" if status else ""
            async with self.bot.session.get(f"{self.api_base}/tickets{params}") as resp:
                data = await resp.json()
                tickets = data.get("tickets", [])[:10]
                embed = discord.Embed(title=f"Tickets ({data.get('total', 0)} total)", color=discord.Color.blue(), timestamp=datetime.now())
                for t in tickets:
                    embed.add_field(name=f"[{t['priority'].upper()}] {t['ticket_id']}", value=f"{t['subject'][:80]} — {t['status']}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"List tickets error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketstats", description="Ticket system statistics")
    async def ticket_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Ticket System Stats", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total", value=data.get("total_tickets", 0), inline=True)
                embed.add_field(name="Open", value=data.get("open_tickets", 0), inline=True)
                embed.add_field(name="SLA Breaches", value=data.get("sla_breaches", 0), inline=True)
                embed.add_field(name="Avg Resolution", value=f"{data.get('avg_resolution_time_hours', 0)}h", inline=True)
                embed.add_field(name="Avg Satisfaction", value=f"{data.get('avg_satisfaction', 0)}/5", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketsla", description="SLA compliance breakdown")
    async def ticket_sla(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="SLA Compliance", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="SLA Met", value=data.get("sla_met", 0), inline=True)
                embed.add_field(name="SLA Breached", value=data.get("sla_breaches", 0), inline=True)
                embed.add_field(name="Compliance %", value=f"{data.get('sla_compliance_pct', 0)}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"SLA error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketassign", description="Assign ticket to user")
    async def ticket_assign(self, interaction: discord.Interaction, ticket_id: str, assignee: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.put(f"{self.api_base}/tickets/{ticket_id}/assign", json={"assignee": assignee}) as resp:
                if resp.ok:
                    embed = discord.Embed(description=f"Ticket {ticket_id} assigned to {assignee}", color=discord.Color.green())
                else:
                    embed = discord.Embed(description="Assignment failed", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Assign error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketoverdue", description="List overdue tickets")
    async def list_overdue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/overdue") as resp:
                data = await resp.json()
                tickets = data.get("tickets", [])
                embed = discord.Embed(title=f"Overdue Tickets ({len(tickets)})", color=discord.Color.red(), timestamp=datetime.now())
                for t in tickets[:10]:
                    embed.add_field(name=f"[{t.get('priority','?').upper()}] {t.get('ticket_id','?')}", value=f"{t.get('subject','')[:80]} | SLA Breached", inline=False)
                if not tickets:
                    embed.description = "No overdue tickets"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Overdue tickets error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketunassigned", description="List unassigned tickets")
    async def list_unassigned(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/unassigned") as resp:
                data = await resp.json()
                tickets = data.get("tickets", [])
                embed = discord.Embed(title=f"Unassigned Tickets ({len(tickets)})", color=discord.Color.orange(), timestamp=datetime.now())
                for t in tickets[:10]:
                    embed.add_field(name=f"[{t.get('priority','?').upper()}] {t.get('ticket_id','?')}", value=t.get('subject','')[:80], inline=False)
                if not tickets:
                    embed.description = "No unassigned tickets"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Unassigned tickets error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class SentimentAnalysisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="sentiment", description="View customer sentiment profile")
    @app_commands.describe(customer_id="Customer ID")
    async def sentiment_profile(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/profile/{customer_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(title=f"Sentiment Profile: {customer_id}", color=discord.Color.green() if data.get("overall_sentiment", 0) >= 0.5 else discord.Color.red())
                    embed.add_field(name="Overall Sentiment", value=f"{data.get('overall_sentiment', 0)*100:.1f}%", inline=True)
                    embed.add_field(name="Risk Level", value=data.get("risk_level", "N/A").upper(), inline=True)
                    embed.add_field(name="Trend", value=data.get("trend", "N/A"), inline=True)
                    embed.add_field(name="Interactions", value=data.get("interaction_count", 0), inline=True)
                    embed.add_field(name="Negative Recent", value=data.get("recent_negative_count", 0), inline=True)
                    aspects = data.get("aspects", {})
                    if aspects:
                        embed.add_field(name="Aspect Scores", value="\n".join(f"{k}: {v*100:.0f}%" for k, v in aspects.items()), inline=False)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(embed=discord.Embed(description="Customer not found", color=0xFF0000))
        except Exception as e:
            logger.error(f"Sentiment profile error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentalerts", description="View sentiment alerts")
    async def sentiment_alerts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/alerts") as resp:
                data = await resp.json()
                alerts = data.get("alerts", [])
                embed = discord.Embed(title=f"Sentiment Alerts ({len(alerts)})", color=discord.Color.red() if alerts else discord.Color.green(), timestamp=datetime.now())
                for a in alerts[:10]:
                    embed.add_field(name=f"{a.get('risk_level', 'UNKNOWN').upper()}: {a.get('customer_name', a.get('customer_id', '?'))}", value=a.get("message", ""), inline=False)
                if not alerts:
                    embed.description = "No active sentiment alerts"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment alerts error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentdistribution", description="Sentiment distribution")
    async def sentiment_distribution(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/distribution") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Sentiment Distribution", color=discord.Color.blue(), timestamp=datetime.now())
                for k, v in data.items():
                    embed.add_field(name=k.title(), value=v, inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment distribution error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimenttrend", description="Customer sentiment trend")
    @app_commands.describe(customer_id="Customer ID")
    async def sentiment_trend(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/trend/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Sentiment Trend: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                trend = data.get("trend", {})
                for day, score in list(trend.items())[:10]:
                    bar = "🟢" if score >= 0.5 else "🟡" if score >= 0 else "🔴"
                    embed.add_field(name=day, value=f"{bar} {score*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment trend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class AdoptionAnalyticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="adoption", description="View customer adoption analytics")
    @app_commands.describe(customer_id="Customer ID")
    async def adoption_summary(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/summary/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Adoption Analytics: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Active Users (30d)", value=data.get("active_users_30d", 0), inline=True)
                embed.add_field(name="Features Used", value=f"{data.get('features_used_30d', 0)}/{data.get('total_features', 0)}", inline=True)
                embed.add_field(name="Adoption Rate", value=f"{data.get('adoption_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Login Count", value=data.get("login_count_30d", 0), inline=True)
                embed.add_field(name="API Calls", value=data.get("api_call_count_30d", 0), inline=True)
                embed.add_field(name="Total Events", value=data.get("total_events_30d", 0), inline=True)
                top = data.get("most_used_features", [])
                if top:
                    embed.add_field(name="Top Features", value="\n".join(f"• {f['name']} ({f['count']})" for f in top[:5]), inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption summary error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionsegments", description="Adoption segment breakdown")
    async def adoption_segments(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/segments") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Adoption Segments", color=discord.Color.blue(), timestamp=datetime.now())
                for seg, info in data.items():
                    embed.add_field(name=seg.title(), value=f"Count: {info.get('count', 0)} ({info.get('pct', 0)}%)", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption segments error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionfunnel", description="Onboarding funnel analysis")
    async def adoption_funnel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/funnel") as resp:
                data = await resp.json()
                steps = data.get("steps", {})
                conversions = data.get("conversions", [])
                embed = discord.Embed(title="Onboarding Funnel", color=discord.Color.blue(), timestamp=datetime.now())
                for step, count in steps.items():
                    embed.add_field(name=step.replace("_", " ").title(), value=f"{count} users", inline=True)
                for c in conversions:
                    embed.add_field(name=f"{c['from']} → {c['to']}", value=f"{c['rate']}% conversion", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption funnel error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class OnboardingWizardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="onboarding", description="View customer onboarding progress")
    @app_commands.describe(customer_id="Customer ID")
    async def onboarding_status(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/session/{customer_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(title=f"Onboarding: {customer_id}", color=discord.Color.green() if data.get("overall_progress", 0) >= 100 else discord.Color.blue(), timestamp=datetime.now())
                    embed.add_field(name="Status", value=data.get("status", "N/A"), inline=True)
                    embed.add_field(name="Progress", value=f"{data.get('overall_progress', 0):.0f}%", inline=True)
                    if data.get("time_to_value_days"):
                        embed.add_field(name="Time to Value", value=f"{data['time_to_value_days']} days", inline=True)
                    steps = data.get("steps", [])
                    completed = sum(1 for s in steps if s.get("status") == "completed")
                    embed.add_field(name="Steps", value=f"{completed}/{len(steps)} completed", inline=True)
                    milestones = data.get("milestones", [])
                    achieved = sum(1 for m in milestones if m.get("achieved"))
                    embed.add_field(name="Milestones", value=f"{achieved}/{len(milestones)}", inline=True)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(embed=discord.Embed(description="No onboarding session found", color=0xFF0000))
        except Exception as e:
            logger.error(f"Onboarding status error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingstats", description="Onboarding statistics")
    async def onboarding_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Onboarding Stats", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Sessions", value=data.get("total_sessions", 0), inline=True)
                embed.add_field(name="Completed", value=data.get("completed", 0), inline=True)
                embed.add_field(name="In Progress", value=data.get("in_progress", 0), inline=True)
                embed.add_field(name="Completion Rate", value=f"{data.get('completion_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Avg Progress", value=f"{data.get('avg_progress_pct', 0):.0f}%", inline=True)
                if data.get("avg_time_to_value_days"):
                    embed.add_field(name="Avg TTV", value=f"{data['avg_time_to_value_days']} days", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingstuck", description="Stuck onboarding sessions")
    async def stuck_sessions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/sessions/stuck") as resp:
                data = await resp.json()
                sessions = data.get("sessions", [])
                embed = discord.Embed(title=f"Stuck Sessions ({len(sessions)})", color=discord.Color.orange(), timestamp=datetime.now())
                for s in sessions[:8]:
                    embed.add_field(name=s.get('customer_id', '?'), value=f"Progress: {s.get('overall_progress', 0)}% | Last: {str(s.get('last_activity','')[:16])}", inline=False)
                if not sessions:
                    embed.description = "No stuck sessions"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Stuck sessions error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingsummary", description="Onboarding summary")
    async def onboarding_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/summary") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Onboarding Summary", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total", value=data.get("total_sessions", 0), inline=True)
                embed.add_field(name="Completed", value=data.get("completed", 0), inline=True)
                embed.add_field(name="In Progress", value=data.get("in_progress", 0), inline=True)
                embed.add_field(name="Abandoned", value=data.get("abandoned", 0), inline=True)
                embed.add_field(name="Completion Rate", value=f"{data.get('completion_rate', 0)}%", inline=True)
                embed.add_field(name="Avg Progress", value=f"{data.get('average_progress', 0)}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding summary error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class KnowledgeBaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="kbsearch", description="Search knowledge base")
    @app_commands.describe(query="Search query")
    async def search_kb(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/search?q={query}&limit=5") as resp:
                data = await resp.json()
                results = data.get("results", [])
                embed = discord.Embed(title=f"Knowledge Base: \"{query}\"", color=discord.Color.blue(), timestamp=datetime.now())
                if results:
                    for r in results[:5]:
                        embed.add_field(name=r["title"], value=f"Score: {r['score']} | {r['excerpt'][:100]}...", inline=False)
                else:
                    embed.description = "No results found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB search error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbpopular", description="Popular knowledge base articles")
    async def popular_articles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/popular") as resp:
                data = await resp.json()
                articles = data.get("articles", [])
                embed = discord.Embed(title="Popular Articles", color=discord.Color.blue(), timestamp=datetime.now())
                for a in articles[:5]:
                    embed.add_field(name=a.get('title', '?'), value=f"Views: {a.get('view_count', 0)} | Helpful: {a.get('helpful_votes', 0)}", inline=False)
                if not articles:
                    embed.description = "No articles found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Popular articles error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbcategories", description="Knowledge base categories")
    async def kb_categories(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/categories") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Knowledge Base Categories", color=discord.Color.blue(), timestamp=datetime.now())
                for cat, count in data.items():
                    embed.add_field(name=cat.replace("_", " ").title(), value=f"{count} articles", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB categories error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbarticle", description="Get article details")
    async def kb_article(self, interaction: discord.Interaction, article_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/articles/{article_id}") as resp:
                if resp.ok:
                    a = await resp.json()
                    embed = discord.Embed(title=a.get('title', '?'), color=discord.Color.blue(), timestamp=datetime.now())
                    embed.add_field(name="Category", value=a.get('category', '?'), inline=True)
                    embed.add_field(name="Views", value=a.get('view_count', 0), inline=True)
                    embed.add_field(name="Helpful", value=a.get('helpful_votes', 0), inline=True)
                    embed.set_footer(text=f"ID: {article_id}")
                else:
                    embed = discord.Embed(description="Article not found", color=0xFF0000)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB article error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class CommunityPlatformCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="community", description="View community forum posts")
    async def community_posts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/posts?limit=5") as resp:
                data = await resp.json()
                posts = data.get("posts", [])
                embed = discord.Embed(title=f"Community Posts ({data.get('total', 0)} total)", color=discord.Color.blue(), timestamp=datetime.now())
                for p in posts[:5]:
                    embed.add_field(name=f"[{p.get('post_type','?').upper()}] {p.get('title','')[:80]}", value=f"👍 {p.get('upvotes',0)} | 💬 {p.get('comment_count',0)} | by {p.get('author_name','?')}", inline=False)
                if not posts:
                    embed.description = "No posts yet"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community posts error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="leaderboard", description="Community leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/leaderboard") as resp:
                data = await resp.json()
                lb = data.get("leaderboard", [])
                embed = discord.Embed(title="Community Leaderboard", color=discord.Color.gold(), timestamp=datetime.now())
                for u in lb[:10]:
                    embed.add_field(name=f"#{u['rank']} {u['username']}", value=f"Rep: {u['reputation']} | Level {u['level']} | Posts: {u.get('post_count',0)}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="featuresuggest", description="Top feature requests")
    async def feature_requests(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/feature-requests?limit=5") as resp:
                data = await resp.json()
                requests = data.get("feature_requests", [])
                embed = discord.Embed(title="Top Feature Requests", color=discord.Color.purple(), timestamp=datetime.now())
                for r in requests[:5]:
                    status = r.get("feature_status", "open")
                    embed.add_field(name=f"👍 {r.get('feature_votes',0)} — {r.get('title','')[:80]}", value=f"Status: {status}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Feature requests error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communitysearch", description="Search community posts")
    @app_commands.describe(query="Search query")
    async def community_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/search?q={query}&limit=5") as resp:
                data = await resp.json()
                results = data.get("results", [])
                embed = discord.Embed(title=f"Community Search: \"{query}\"", color=discord.Color.blue(), timestamp=datetime.now())
                for r in results[:5]:
                    embed.add_field(name=r.get('title', '?')[:80], value=f"by {r.get('author_name', '?')} | 👍 {r.get('like_count', 0)}", inline=False)
                if not results:
                    embed.description = "No results found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community search error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communitytrending", description="Trending community posts")
    async def community_trending(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/posts/trending") as resp:
                data = await resp.json()
                posts = data.get("posts", [])
                embed = discord.Embed(title=f"Trending Posts ({len(posts)})", color=discord.Color.gold(), timestamp=datetime.now())
                for p in posts[:5]:
                    embed.add_field(name=p.get('title', '?')[:80], value=f"👍 {p.get('like_count', 0)} | 💬 {p.get('comment_count', 0)} | 👁 {p.get('view_count', 0)}", inline=False)
                if not posts:
                    embed.description = "No trending posts"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Trending posts error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class CommunicationHubCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="maintenance", description="View upcoming maintenance")
    async def list_maintenance(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/maintenance?status=scheduled") as resp:
                data = await resp.json()
                windows = data.get("maintenance_windows", [])
                embed = discord.Embed(title=f"Maintenance Windows ({len(windows)})", color=discord.Color.orange(), timestamp=datetime.now())
                for m in windows[:5]:
                    embed.add_field(name=m.get("title", "Maintenance"), value=f"Status: {m.get('status')}\nStart: {m.get('start_time','')[:16]}\nAffected: {', '.join(m.get('affected_services',[]))}", inline=False)
                if not windows:
                    embed.description = "No scheduled maintenance"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Maintenance list error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commsstats", description="Communication stats")
    async def comms_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Communication Hub Stats", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Notifications", value=data.get("total_notifications", 0), inline=True)
                embed.add_field(name="Templates", value=data.get("templates", 0), inline=True)
                embed.add_field(name="Maintenance Windows", value=data.get("maintenance_windows", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commstemplates", description="Message templates")
    async def comms_templates(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/templates") as resp:
                data = await resp.json()
                templates = data.get("templates", [])
                embed = discord.Embed(title=f"Message Templates ({len(templates)})", color=discord.Color.blue(), timestamp=datetime.now())
                for t in templates[:8]:
                    embed.add_field(name=t.get('name', '?'), value=f"Vars: {', '.join(t.get('variables', []))}", inline=False)
                if not templates:
                    embed.description = "No templates"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms templates error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class NPSSurveysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="nps", description="View NPS score")
    async def nps_score(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/score") as resp:
                data = await resp.json()
                embed = discord.Embed(title="NPS Score", color=discord.Color.green() if data.get("nps_score", 0) >= 0 else discord.Color.red(), timestamp=datetime.now())
                embed.add_field(name="NPS", value=data.get("nps_score", "N/A"), inline=True)
                embed.add_field(name="Promoters", value=f'{data.get("promoters", 0)} ({data.get("promoter_pct", 0)}%)', inline=True)
                embed.add_field(name="Passives", value=f'{data.get("passives", 0)} ({data.get("passive_pct", 0)}%)', inline=True)
                embed.add_field(name="Detractors", value=f'{data.get("detractors", 0)} ({data.get("detractor_pct", 0)}%)', inline=True)
                embed.add_field(name="Total Responses", value=data.get("total_responses", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS score error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npstrend", description="NPS score trend")
    async def nps_trend(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/trend") as resp:
                data = await resp.json()
                embed = discord.Embed(title="NPS Trend", color=discord.Color.blue(), timestamp=datetime.now())
                for entry in data[-6:]:
                    embed.add_field(name=entry.get('month', '?'), value=f"Score: {entry.get('avg_score', 0)} | Responses: {entry.get('responses', 0)}", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS trend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npsdetractors", description="Recent detractor feedback")
    async def nps_detractors(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/detractors") as resp:
                data = await resp.json()
                detractors = data.get("detractors", [])
                embed = discord.Embed(title=f"Detractor Feedback ({len(detractors)})", color=discord.Color.red(), timestamp=datetime.now())
                for d in detractors[:5]:
                    embed.add_field(name=d.get('customer_id', '?'), value=f"Score: {d.get('score', '?')}", inline=False)
                if not detractors:
                    embed.description = "No detractors"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS detractors error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


class SuccessAutomationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "http://localhost:8080/api/v1/cx"

    @app_commands.command(name="successplays", description="List success automation plays")
    async def list_plays(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/plays") as resp:
                data = await resp.json()
                plays = data.get("plays", [])
                embed = discord.Embed(title=f"Success Plays ({len(plays)})", color=discord.Color.blue(), timestamp=datetime.now())
                for p in plays[:8]:
                    embed.add_field(name=p.get("name", "?"), value=f"Trigger: {p.get('trigger_event', '?')} | Execs: {p.get('execution_count', 0)} | Status: {p.get('status', '?')}", inline=False)
                if not plays:
                    embed.description = "No success plays configured"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"List plays error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successstats", description="Success automation statistics")
    async def success_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Success Automation Stats", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Plays", value=data.get("total_plays", 0), inline=True)
                embed.add_field(name="Active Plays", value=data.get("active_plays", 0), inline=True)
                embed.add_field(name="Total Executions", value=data.get("total_executions", 0), inline=True)
                embed.add_field(name="Success Rate", value=f"{data.get('success_rate', 0)*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successexecutions", description="Recent play executions")
    async def recent_executions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/executions") as resp:
                data = await resp.json()
                executions = data.get("executions", [])
                embed = discord.Embed(title=f"Recent Executions ({len(executions)})", color=discord.Color.blue(), timestamp=datetime.now())
                for e in executions[:8]:
                    status = "✅" if e.get('status') == 'success' else "❌" if e.get('status') == 'failed' else "⏳"
                    embed.add_field(name=f"{status} {e.get('trigger_event', '?')}", value=f"Play: {e.get('play_id', '?')} | {str(e.get('executed_at','')[:16])}", inline=False)
                if not executions:
                    embed.description = "No executions found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Executions error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successfailed", description="Failed automations")
    async def failed_executions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/executions/failed") as resp:
                data = await resp.json()
                executions = data.get("executions", [])
                embed = discord.Embed(title=f"Failed Executions ({len(executions)})", color=discord.Color.red(), timestamp=datetime.now())
                for e in executions[:8]:
                    embed.add_field(name=e.get('play_id', '?'), value=f"Error: {e.get('error', '?')[:100]} | {str(e.get('executed_at','')[:16])}", inline=False)
                if not executions:
                    embed.description = "No failed executions"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed executions error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── HealthScoringCog additional commands ──

    @app_commands.command(name="healthcompare", description="Compare multiple customer health profiles")
    @app_commands.describe(customer_ids="Comma-separated customer IDs")
    async def health_compare(self, interaction: discord.Interaction, customer_ids: str):
        await interaction.response.defer()
        try:
            ids = [c.strip() for c in customer_ids.split(",")]
            async with self.bot.session.get(f"{self.api_base}/health/compare", params={"ids": ids}) as resp:
                data = await resp.json()
                embed = discord.Embed(title="Health Profile Comparison", color=discord.Color.blue(), timestamp=datetime.now())
                for cid, info in data.items():
                    embed.add_field(name=cid, value=f"Score: {info.get('composite_score', '?')} | Risk: {info.get('risk_level', '?')} | Churn: {info.get('churn_probability', 0)*100:.0f}%", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health compare error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthforecast", description="Health score forecast for customer")
    @app_commands.describe(customer_id="Customer ID", days="Days ahead to forecast")
    async def health_forecast(self, interaction: discord.Interaction, customer_id: str, days: int = 30):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/forecast/{customer_id}?days={days}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Health Forecast: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                scores = data.get("forecast_scores", [])
                if scores:
                    embed.add_field(name="Direction", value=data.get("direction", "stable"), inline=True)
                    embed.add_field(name="Start", value=scores[0], inline=True)
                    embed.add_field(name="End", value=scores[-1], inline=True)
                    bar = "🟢" if scores[-1] >= 70 else "🟡" if scores[-1] >= 40 else "🔴"
                    embed.description = f"{bar} Forecast trend: {data.get('direction', 'stable')}"
                else:
                    embed.description = "Insufficient data for forecast"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health forecast error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthanomalies", description="Anomalous health profiles")
    async def health_anomalies(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/anomalies") as resp:
                data = await resp.json()
                profiles = data.get("anomalies", [])
                embed = discord.Embed(title=f"Health Anomalies ({len(profiles)})", color=discord.Color.orange(), timestamp=datetime.now())
                for p in profiles[:8]:
                    embed.add_field(name=p.get("customer_id", "?"), value=f"Score: {p.get('composite_score', '?')} | Risk: {p.get('risk_level', '?')}", inline=False)
                if not profiles:
                    embed.description = "No anomalies detected"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health anomalies error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthcomponents", description="Health score component breakdown")
    @app_commands.describe(customer_id="Customer ID")
    async def health_components(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/components/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Health Components: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for name, comp in data.get("components", {}).items():
                    embed.add_field(name=name.title(), value=f"Score: {comp['score']} | Weight: {comp['weight']} | {comp.get('trend', 'stable')}", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health components error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthreport", description="Detailed health report for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def health_report(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/report/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Health Report: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Composite Score", value=data.get("composite_score", "N/A"), inline=True)
                embed.add_field(name="Risk Level", value=data.get("risk_level", "N/A"), inline=True)
                embed.add_field(name="Churn Probability", value=f"{data.get('churn_probability', 0)*100:.1f}%", inline=True)
                if data.get("recommendations"):
                    embed.add_field(name="Recommendations", value="\n".join(f"• {r}" for r in data["recommendations"][:5]), inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health report error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── TicketingCog additional commands ──

    @app_commands.command(name="ticketcreate", description="Create a support ticket")
    @app_commands.describe(subject="Ticket subject", description="Ticket description", customer_id="Customer ID", priority="Priority (low/medium/high/critical)")
    async def ticket_create(self, interaction: discord.Interaction, subject: str, description: str, customer_id: str, priority: str = "medium"):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/tickets", json={"subject": subject, "description": description, "customer_id": customer_id, "priority": priority}) as resp:
                data = await resp.json()
                embed = discord.Embed(title="Ticket Created", color=discord.Color.green(), timestamp=datetime.now())
                embed.add_field(name="Ticket ID", value=data.get("ticket_id", "?"), inline=True)
                embed.add_field(name="Priority", value=priority, inline=True)
                embed.add_field(name="Subject", value=subject[:80], inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket create error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketupdate", description="Update ticket status")
    @app_commands.describe(ticket_id="Ticket ID", status="New status")
    async def ticket_update(self, interaction: discord.Interaction, ticket_id: str, status: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.put(f"{self.api_base}/tickets/{ticket_id}/status", json={"status": status}) as resp:
                if resp.ok:
                    embed = discord.Embed(description=f"Ticket {ticket_id} → {status}", color=discord.Color.green())
                else:
                    embed = discord.Embed(description="Update failed", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket update error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketcomment", description="Add comment to ticket")
    @app_commands.describe(ticket_id="Ticket ID", comment="Comment text", internal="Internal note?")
    async def ticket_comment(self, interaction: discord.Interaction, ticket_id: str, comment: str, internal: bool = False):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/tickets/{ticket_id}/comments", json={"author": str(interaction.user), "content": comment, "internal": internal}) as resp:
                if resp.ok:
                    embed = discord.Embed(description=f"Comment added to {ticket_id}", color=discord.Color.green())
                else:
                    embed = discord.Embed(description="Failed to add comment", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket comment error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketsearch", description="Search tickets by query")
    @app_commands.describe(query="Search query")
    async def ticket_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/search?q={query}") as resp:
                data = await resp.json()
                results = data.get("results", [])
                embed = discord.Embed(title=f"Ticket Search: \"{query}\" ({len(results)})", color=discord.Color.blue(), timestamp=datetime.now())
                for r in results[:10]:
                    embed.add_field(name=f"{r.get('ticket_id', '?')} [{r.get('status', '?')}]", value=r.get('subject', '')[:80], inline=False)
                if not results:
                    embed.description = "No matching tickets"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket search error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketbycustomer", description="List tickets for a customer")
    @app_commands.describe(customer_id="Customer ID")
    async def ticket_by_customer(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets?customer_id={customer_id}") as resp:
                data = await resp.json()
                tickets = data.get("tickets", [])
                embed = discord.Embed(title=f"Tickets for {customer_id} ({len(tickets)})", color=discord.Color.blue(), timestamp=datetime.now())
                for t in tickets[:10]:
                    embed.add_field(name=f"[{t.get('priority','?').upper()}] {t.get('ticket_id','?')}", value=f"{t.get('subject','')[:60]} — {t.get('status','?')}", inline=False)
                if not tickets:
                    embed.description = "No tickets found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket by customer error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketbyassignee", description="Tickets assigned to user")
    @app_commands.describe(assignee="Assignee user ID")
    async def ticket_by_assignee(self, interaction: discord.Interaction, assignee: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets?assigned_to={assignee}") as resp:
                data = await resp.json()
                tickets = data.get("tickets", [])
                embed = discord.Embed(title=f"Tickets assigned to {assignee} ({len(tickets)})", color=discord.Color.blue(), timestamp=datetime.now())
                for t in tickets[:10]:
                    embed.add_field(name=f"[{t.get('priority','?').upper()}] {t.get('ticket_id','?')}", value=f"{t.get('subject','')[:60]} — {t.get('status','?')}", inline=False)
                if not tickets:
                    embed.description = "No tickets found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket by assignee error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketmetrics", description="Ticket system metrics")
    async def ticket_metrics(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/metrics") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Ticket Metrics", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Avg First Response", value=f"{data.get('avg_first_response_minutes', 0)} min", inline=True)
                embed.add_field(name="Avg Resolution", value=f"{data.get('avg_resolution_hours', 0)} hrs", inline=True)
                embed.add_field(name="SLA Compliance", value=f"{data.get('sla_compliance', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Reopened", value=data.get("reopened_count", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket metrics error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketslareport", description="SLA compliance report")
    async def ticket_sla_report(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/sla/report") as resp:
                data = await resp.json()
                embed = discord.Embed(title="SLA Compliance Report", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Compliance Rate", value=f"{data.get('compliance_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Breach Rate", value=f"{data.get('breach_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Breached", value=data.get("breached", 0), inline=True)
                embed.add_field(name="Active Within SLA", value=data.get("active_within_sla", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket SLA report error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketagentperf", description="Agent performance stats")
    @app_commands.describe(agent_id="Agent user ID")
    async def ticket_agent_perf(self, interaction: discord.Interaction, agent_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/agent/{agent_id}/performance") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Agent Performance: {agent_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Assigned", value=data.get("total_assigned", 0), inline=True)
                embed.add_field(name="Resolved", value=data.get("total_resolved", 0), inline=True)
                embed.add_field(name="Resolution Rate", value=f"{data.get('resolution_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Avg Resolution", value=f"{data.get('avg_resolution_hours', 0)} hrs", inline=True)
                embed.add_field(name="Avg Satisfaction", value=f"{data.get('avg_satisfaction', 0)}/5", inline=True)
                embed.add_field(name="Open", value=data.get("current_open", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Agent perf error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── SentimentAnalysisCog additional commands ──

    @app_commands.command(name="sentimentsummary", description="Customer sentiment summary")
    @app_commands.describe(customer_id="Customer ID")
    async def sentiment_summary(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/summary/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Sentiment Summary: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Overall", value=data.get("overall_sentiment", "N/A"), inline=True)
                embed.add_field(name="Trend", value=data.get("trend", "N/A"), inline=True)
                embed.add_field(name="Risk", value=data.get("risk_level", "N/A"), inline=True)
                embed.add_field(name="Interactions", value=data.get("interaction_count", 0), inline=True)
                embed.add_field(name="Negative Recent", value=data.get("recent_negative_count", 0), inline=True)
                keywords = data.get("top_keywords", [])
                if keywords:
                    embed.add_field(name="Top Keywords", value=", ".join(keywords[:5]), inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment summary error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentchannel", description="Sentiment by channel")
    async def sentiment_channel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/by-channel") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Sentiment by Channel", color=discord.Color.blue(), timestamp=datetime.now())
                for ch, info in data.items():
                    embed.add_field(name=ch.replace("_", " ").title(), value=f"Avg: {info.get('avg_score', 0)*100:.0f}% | Count: {info.get('count', 0)}", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment channel error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentforecast", description="Sentiment forecast for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def sentiment_forecast(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/forecast/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Sentiment Forecast: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Direction", value=data.get("direction", "stable"), inline=True)
                embed.add_field(name="Historical Avg", value=f"{data.get('historical_avg', 0)*100:.0f}%", inline=True)
                scores = data.get("forecast_scores", [])
                if scores:
                    embed.add_field(name="Forecast Start", value=f"{scores[0]*100:.0f}%", inline=True)
                    embed.add_field(name="Forecast End", value=f"{scores[-1]*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment forecast error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentkeywords", description="Top sentiment keywords")
    async def sentiment_keywords(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/keywords") as resp:
                data = await resp.json()
                keywords = data.get("top_keywords", [])
                embed = discord.Embed(title="Top Sentiment Keywords", color=discord.Color.blue(), timestamp=datetime.now())
                for kw in keywords[:15]:
                    embed.add_field(name=kw.get("keyword", "?"), value=f"Count: {kw.get('count', 0)}", inline=True)
                if not keywords:
                    embed.description = "No keyword data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment keywords error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentcompare", description="Compare sentiment across customers")
    @app_commands.describe(customer_ids="Comma-separated customer IDs")
    async def sentiment_compare(self, interaction: discord.Interaction, customer_ids: str):
        await interaction.response.defer()
        try:
            ids = [c.strip() for c in customer_ids.split(",")]
            async with self.bot.session.post(f"{self.api_base}/sentiment/compare", json={"customer_ids": ids}) as resp:
                data = await resp.json()
                embed = discord.Embed(title="Sentiment Comparison", color=discord.Color.blue(), timestamp=datetime.now())
                for cid, info in data.items():
                    embed.add_field(name=cid, value=f"Score: {info.get('overall_sentiment', 0)*100:.0f}% | Risk: {info.get('risk_level', '?')} | Trend: {info.get('trend', '?')}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment compare error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentheatmap", description="Sentiment heatmap by day")
    async def sentiment_heatmap(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/heatmap") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Sentiment Heatmap (Last 30 Days)", color=discord.Color.blue(), timestamp=datetime.now())
                for day, aspects in list(data.items())[:10]:
                    avg = sum(aspects.values()) / max(len(aspects), 1)
                    bar = "🟢" if avg >= 0.6 else "🟡" if avg >= 0.4 else "🔴"
                    embed.add_field(name=day, value=f"{bar} {avg*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment heatmap error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── AdoptionAnalyticsCog additional commands ──

    @app_commands.command(name="adoptionfeatures", description="Feature adoption breakdown")
    @app_commands.describe(customer_id="Customer ID")
    async def adoption_features(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/features/{customer_id}") as resp:
                data = await resp.json()
                features = data.get("features", [])
                embed = discord.Embed(title=f"Feature Adoption: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for f in features[:8]:
                    embed.add_field(name=f.get("feature_name", "?"), value=f"Rate: {f.get('adoption_rate', 0)*100:.0f}% | Users: {f.get('active_users_30d', 0)} | Trend: {f.get('trend', '?')}", inline=False)
                if not features:
                    embed.description = "No adoption data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption features error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionrecommend", description="Adoption recommendations")
    @app_commands.describe(customer_id="Customer ID")
    async def adoption_recommend(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/recommendations/{customer_id}") as resp:
                data = await resp.json()
                recs = data.get("recommendations", [])
                embed = discord.Embed(title=f"Adoption Recommendations: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for r in recs[:8]:
                    embed.add_field(name=f"[{r.get('priority','?').upper()}] {r.get('type','?').replace('_',' ').title()}", value=r.get("message", ""), inline=False)
                if not recs:
                    embed.description = "No recommendations"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption recommend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptioncohorts", description="User cohort analysis")
    async def adoption_cohorts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/cohorts") as resp:
                data = await resp.json()
                embed = discord.Embed(title="User Cohorts", color=discord.Color.blue(), timestamp=datetime.now())
                for cohort, info in list(data.items())[:8]:
                    embed.add_field(name=cohort, value=f"Users: {info.get('unique_users', 0)} | Events: {info.get('total_events', 0)}", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption cohorts error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionretention", description="Customer retention analysis")
    async def adoption_retention(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/retention") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Customer Retention", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Retention Rate", value=f"{data.get('retention_rate', 0)}%", inline=True)
                embed.add_field(name="Active", value=data.get("active_customers", 0), inline=True)
                embed.add_field(name="Total", value=data.get("total_customers", 0), inline=True)
                embed.add_field(name="Period", value=f"{data.get('period_days', 0)} days", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption retention error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionchurn", description="Churn risk prediction")
    @app_commands.describe(customer_id="Customer ID")
    async def adoption_churn(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/churn-risk/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Churn Risk: {customer_id}", color=discord.Color.red() if data.get("risk_level") == "high" else discord.Color.orange(), timestamp=datetime.now())
                embed.add_field(name="Risk Score", value=f"{data.get('risk_score', 0)}/100", inline=True)
                embed.add_field(name="Risk Level", value=data.get("risk_level", "N/A"), inline=True)
                embed.add_field(name="Logins (30d)", value=data.get("login_frequency_30d", 0), inline=True)
                embed.add_field(name="Features Used", value=data.get("features_used_30d", 0), inline=True)
                embed.add_field(name="Recommendation", value=data.get("recommendation", ""), inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption churn error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptiongaps", description="Feature adoption gaps")
    async def adoption_gaps(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/gaps") as resp:
                data = await resp.json()
                gaps = data.get("gaps", [])
                embed = discord.Embed(title=f"Adoption Gaps ({len(gaps)})", color=discord.Color.orange(), timestamp=datetime.now())
                for g in gaps[:8]:
                    embed.add_field(name=g.get("feature_name", "?"), value=f"Gap: {g.get('gap_pct', 0)}% | Non-users: {g.get('adoption_gap', 0)}", inline=False)
                if not gaps:
                    embed.description = "No adoption gaps"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption gaps error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionranking", description="Feature usage ranking")
    async def adoption_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/feature-ranking") as resp:
                data = await resp.json()
                ranking = data.get("ranking", [])
                embed = discord.Embed(title="Feature Usage Ranking", color=discord.Color.blue(), timestamp=datetime.now())
                for r in ranking[:10]:
                    embed.add_field(name=f"#{r.get('rank', '?')} {r.get('name', '?')}", value=f"Events: {r.get('event_count', 0)} | Users: {r.get('unique_users', 0)}", inline=False)
                if not ranking:
                    embed.description = "No ranking data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption ranking error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── OnboardingWizardCog additional commands ──

    @app_commands.command(name="onboardingprogress", description="Detailed onboarding progress")
    @app_commands.describe(customer_id="Customer ID")
    async def onboarding_progress(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/progress/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Onboarding Progress: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Status", value=data.get("status", "N/A"), inline=True)
                embed.add_field(name="Progress", value=f"{data.get('overall_progress', 0)}%", inline=True)
                steps = data.get("steps", [])
                for s in steps[:6]:
                    status_icon = "✅" if s.get("status") == "completed" else "⏳" if s.get("status") == "in_progress" else "⬜"
                    embed.add_field(name=f"{status_icon} {s.get('title', '?')}", value=s.get("status", "?").replace("_", " ").title(), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding progress error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingmilestones", description="Onboarding milestone status")
    @app_commands.describe(customer_id="Customer ID")
    async def onboarding_milestones(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/milestones/{customer_id}") as resp:
                data = await resp.json()
                milestones = data.get("milestones", [])
                embed = discord.Embed(title=f"Milestones: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for m in milestones:
                    icon = "🏆" if m.get("achieved") else "🏃"
                    embed.add_field(name=f"{icon} {m.get('name', '?')}", value=f"Achieved: {m.get('achieved', False)} | Progress: {m.get('progress_pct', 0)}%", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding milestones error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingabandon", description="Onboarding abandonment analysis")
    async def onboarding_abandon(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/abandonment") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Onboarding Abandonment", color=discord.Color.red(), timestamp=datetime.now())
                embed.add_field(name="Rate", value=f"{data.get('abandonment_rate', 0)}%", inline=True)
                embed.add_field(name="Abandoned", value=data.get("abandoned", 0), inline=True)
                embed.add_field(name="Stale", value=data.get("stale", 0), inline=True)
                embed.add_field(name="Total", value=data.get("total", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding abandon error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingttv", description="Time-to-value report")
    async def onboarding_ttv(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/time-to-value") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Time to Value Report", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Average", value=f"{data.get('avg_ttv_days', 0)} days", inline=True)
                embed.add_field(name="Median", value=f"{data.get('median_ttv_days', 0)} days", inline=True)
                embed.add_field(name="Min", value=f"{data.get('min_ttv_days', 0)} days", inline=True)
                embed.add_field(name="Max", value=f"{data.get('max_ttv_days', 0)} days", inline=True)
                embed.add_field(name="Samples", value=data.get("samples", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding TTV error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingdropoff", description="Step drop-off rates")
    async def onboarding_dropoff(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/drop-off") as resp:
                data = await resp.json()
                steps = data.get("steps", [])
                embed = discord.Embed(title="Step Drop-off Rates", color=discord.Color.orange(), timestamp=datetime.now())
                for s in steps[:8]:
                    bar = "🟢" if s.get("drop_off_rate", 0) < 0.3 else "🟡" if s.get("drop_off_rate", 0) < 0.6 else "🔴"
                    embed.add_field(name=f"{bar} {s.get('step_id', '?').replace('step-','').replace('_',' ').title()}", value=f"Drop-off: {s.get('drop_off_rate', 0)*100:.0f}% | Entered: {s.get('entered', 0)}", inline=False)
                if not steps:
                    embed.description = "No drop-off data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding dropoff error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingeffectiveness", description="Onboarding effectiveness")
    async def onboarding_effectiveness(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/effectiveness") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Onboarding Effectiveness", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Completion Rate", value=f"{data.get('completion_rate', 0)}%", inline=True)
                embed.add_field(name="Avg Progress", value=f"{data.get('average_progress', 0)}%", inline=True)
                embed.add_field(name="Avg TTV", value=f"{data.get('average_time_to_value_days', 'N/A')} days", inline=True)
                embed.add_field(name="Stuck Sessions", value=data.get("stuck_sessions", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding effectiveness error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── KnowledgeBaseCog additional commands ──

    @app_commands.command(name="kbbycategory", description="Articles by category")
    @app_commands.describe(category="Category slug")
    async def kb_by_category(self, interaction: discord.Interaction, category: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/articles?category={category}") as resp:
                data = await resp.json()
                articles = data.get("articles", [])
                embed = discord.Embed(title=f"KB: {category.replace('-',' ').title()} ({len(articles)})", color=discord.Color.blue(), timestamp=datetime.now())
                for a in articles[:8]:
                    embed.add_field(name=a.get("title", "?"), value=f"Views: {a.get('view_count', 0)} | Helpful: {a.get('helpful_count', 0)}", inline=False)
                if not articles:
                    embed.description = "No articles in this category"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB by category error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbhelpfulness", description="Article helpfulness report")
    async def kb_helpfulness(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/helpfulness") as resp:
                data = await resp.json()
                embed = discord.Embed(title="KB Helpfulness Report", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="High Helpfulness", value=f"{data.get('high_helpfulness_count', 0)} ({data.get('high_helpfulness_pct', 0)}%)", inline=True)
                embed.add_field(name="Low Helpfulness", value=f"{data.get('low_helpfulness_count', 0)} ({data.get('low_helpfulness_pct', 0)}%)", inline=True)
                embed.add_field(name="Articles Needing Review", value=data.get("needs_review_count", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB helpfulness error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbfeatured", description="Featured articles")
    async def kb_featured(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/featured") as resp:
                data = await resp.json()
                articles = data.get("articles", [])
                embed = discord.Embed(title="Featured Articles", color=discord.Color.blue(), timestamp=datetime.now())
                for a in articles[:5]:
                    embed.add_field(name=a.get("title", "?"), value=f"Read time: {a.get('estimated_read_minutes', 0)} min", inline=False)
                if not articles:
                    embed.description = "No featured articles"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB featured error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbgaps", description="Content gap analysis")
    async def kb_gaps(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/gaps") as resp:
                data = await resp.json()
                gaps = data.get("gaps", [])
                embed = discord.Embed(title="Content Gaps", color=discord.Color.orange(), timestamp=datetime.now())
                for g in gaps[:8]:
                    embed.add_field(name=g.get("category_name", "?"), value=f"Articles: {g.get('article_count', 0)} | Need: {g.get('gap', 0)} more", inline=False)
                if not gaps:
                    embed.description = "No content gaps found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB gaps error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbrecommend", description="Article recommendations")
    @app_commands.describe(interests="Comma-separated interests")
    async def kb_recommend(self, interaction: discord.Interaction, interests: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/recommend", params={"interests": interests}) as resp:
                data = await resp.json()
                articles = data.get("articles", [])
                embed = discord.Embed(title="Recommended Articles", color=discord.Color.blue(), timestamp=datetime.now())
                for a in articles[:5]:
                    embed.add_field(name=a.get("title", "?"), value=a.get("category", "?"), inline=False)
                if not articles:
                    embed.description = "No recommendations found"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB recommend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbstats", description="Knowledge base statistics")
    async def kb_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Knowledge Base Stats", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Articles", value=data.get("total_articles", 0), inline=True)
                embed.add_field(name="Published", value=data.get("published_articles", 0), inline=True)
                embed.add_field(name="Total Views", value=data.get("total_views", 0), inline=True)
                embed.add_field(name="Helpfulness Rate", value=f"{data.get('helpfulness_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Categories", value=data.get("categories", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── CommunityPlatformCog additional commands ──

    @app_commands.command(name="communitycategories", description="Community forum categories")
    async def community_categories(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/categories") as resp:
                data = await resp.json()
                categories = data.get("categories", [])
                embed = discord.Embed(title="Forum Categories", color=discord.Color.blue(), timestamp=datetime.now())
                for c in categories[:8]:
                    embed.add_field(name=f"{c.get('icon', '📁')} {c.get('name', '?')}", value=f"Posts: {c.get('post_count', 0)} | Threads: {c.get('thread_count', 0)}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community categories error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communitypost", description="View community post details")
    @app_commands.describe(post_id="Post ID")
    async def community_post_detail(self, interaction: discord.Interaction, post_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/posts/{post_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=data.get("title", "Post"), description=data.get("content", "")[:200], color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Author", value=data.get("author_name", "?"), inline=True)
                embed.add_field(name="Votes", value=f"👍 {data.get('upvotes', 0)} 👎 {data.get('downvotes', 0)}", inline=True)
                embed.add_field(name="Comments", value=data.get("comment_count", 0), inline=True)
                embed.add_field(name="Type", value=data.get("post_type", "?"), inline=True)
                embed.add_field(name="Status", value=data.get("status", "?"), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community post detail error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communitybadges", description="Badge leaderboard")
    @app_commands.describe(badge_name="Badge name")
    async def community_badges(self, interaction: discord.Interaction, badge_name: str = "Top Contributor"):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/badges/leaderboard", params={"badge": badge_name}) as resp:
                data = await resp.json()
                users = data.get("users", [])
                embed = discord.Embed(title=f"Badge Leaderboard: {badge_name}", color=discord.Color.gold(), timestamp=datetime.now())
                for u in users[:10]:
                    embed.add_field(name=f"#{u.get('rank', '?')} {u.get('username', '?')}", value=f"Rep: {u.get('reputation', 0)}", inline=False)
                if not users:
                    embed.description = "No badge holders"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community badges error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communityunanswered", description="Unanswered questions")
    async def community_unanswered(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/unanswered") as resp:
                data = await resp.json()
                questions = data.get("questions", [])
                embed = discord.Embed(title=f"Unanswered Questions ({len(questions)})", color=discord.Color.orange(), timestamp=datetime.now())
                for q in questions[:5]:
                    embed.add_field(name=q.get("title", "?"), value=f"👍 {q.get('upvotes', 0)} | by {q.get('author_name', '?')}", inline=False)
                if not questions:
                    embed.description = "No unanswered questions"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community unanswered error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communityactivity", description="Recent community activity")
    async def community_activity(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/activity") as resp:
                data = await resp.json()
                activity = data.get("activity", [])
                embed = discord.Embed(title="Recent Activity", color=discord.Color.blue(), timestamp=datetime.now())
                for a in activity[:10]:
                    embed.add_field(name=a.get("type", "?").title(), value=f"{a.get('title', a.get('post_title', '?'))} — {str(a.get('timestamp','')[:16])}", inline=False)
                if not activity:
                    embed.description = "No recent activity"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community activity error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communityroadmap", description="Feature request roadmap")
    async def community_roadmap(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/roadmap") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Feature Request Roadmap", color=discord.Color.purple(), timestamp=datetime.now())
                for status, requests in data.items():
                    if requests:
                        names = [r.get('title', '?')[:40] for r in requests[:3]]
                        embed.add_field(name=status.replace("_", " ").title(), value="\n".join(f"• {n}" for n in names), inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community roadmap error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── CommunicationHubCog additional commands ──

    @app_commands.command(name="maintenancecreate", description="Schedule maintenance window")
    @app_commands.describe(title="Title", description="Description", services="Affected services (comma-separated)", start="Start time (ISO)", end="End time (ISO)")
    async def maintenance_create(self, interaction: discord.Interaction, title: str, description: str, services: str, start: str, end: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/communication/maintenance", json={"title": title, "description": description, "affected_services": [s.strip() for s in services.split(",")], "start_time": start, "end_time": end}) as resp:
                data = await resp.json()
                embed = discord.Embed(title="Maintenance Scheduled", color=discord.Color.green(), timestamp=datetime.now())
                embed.add_field(name="ID", value=data.get("maintenance_id", "?"), inline=True)
                embed.add_field(name="Title", value=title, inline=True)
                embed.add_field(name="Status", value=data.get("status", "scheduled"), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Maintenance create error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="maintenancecomplete", description="Complete maintenance window")
    @app_commands.describe(maintenance_id="Maintenance ID", downtime_actual="Actual downtime in minutes")
    async def maintenance_complete(self, interaction: discord.Interaction, maintenance_id: str, downtime_actual: int = None):
        await interaction.response.defer()
        try:
            async with self.bot.session.put(f"{self.api_base}/communication/maintenance/{maintenance_id}/complete", json={"actual_downtime": downtime_actual}) as resp:
                if resp.ok:
                    embed = discord.Embed(description=f"Maintenance {maintenance_id} completed", color=discord.Color.green())
                else:
                    embed = discord.Embed(description="Failed to complete maintenance", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Maintenance complete error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commssend", description="Send notification")
    @app_commands.describe(notification_type="Type", subject="Subject", body="Body")
    async def comms_send(self, interaction: discord.Interaction, notification_type: str, subject: str, body: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/communication/send", json={"notification_type": notification_type, "subject": subject, "body": body, "channels": ["in_app"]}) as resp:
                data = await resp.json()
                embed = discord.Embed(title="Notification Sent", color=discord.Color.green(), timestamp=datetime.now())
                embed.add_field(name="Batch ID", value=data.get("batch_id", "?"), inline=True)
                embed.add_field(name="Type", value=notification_type, inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms send error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commsdelivery", description="Delivery analytics")
    async def comms_delivery(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/delivery-analytics") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Delivery Analytics", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Delivery Rate", value=f"{data.get('overall_delivery_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Read Rate", value=f"{data.get('overall_read_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Period", value=f"{data.get('period_days', 30)} days", inline=True)
                embed.add_field(name="Total Records", value=data.get("total_records", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms delivery error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commschannelhealth", description="Channel health status")
    async def comms_channel_health(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/channel-health") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Channel Health", color=discord.Color.blue(), timestamp=datetime.now())
                for ch, info in data.items():
                    icon = "🟢" if info.get("status") == "healthy" else "🟡" if info.get("status") == "degraded" else "🔴"
                    embed.add_field(name=f"{icon} {ch}", value=f"Status: {info.get('status', '?')} | Failure: {info.get('failure_rate', 0)*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms channel health error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="maintenanceschedule", description="Upcoming maintenance schedule")
    async def maintenance_schedule(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/maintenance/schedule") as resp:
                data = await resp.json()
                schedule = data.get("schedule", [])
                embed = discord.Embed(title=f"Maintenance Schedule ({len(schedule)})", color=discord.Color.orange(), timestamp=datetime.now())
                for m in schedule[:8]:
                    embed.add_field(name=m.get("title", "?"), value=f"Start: {str(m.get('start','')[:16])} | Status: {m.get('status','?')}", inline=False)
                if not schedule:
                    embed.description = "No upcoming maintenance"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Maintenance schedule error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commscampaign", description="Notification campaign performance")
    @app_commands.describe(batch_id="Batch ID")
    async def comms_campaign(self, interaction: discord.Interaction, batch_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/batches/{batch_id}/stats") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Campaign: {batch_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Delivered", value=data.get("delivered", 0), inline=True)
                embed.add_field(name="Read", value=data.get("read", 0), inline=True)
                embed.add_field(name="Clicked", value=data.get("clicked", 0), inline=True)
                embed.add_field(name="Failed", value=data.get("failed", 0), inline=True)
                embed.add_field(name="Delivery Rate", value=f"{data.get('delivery_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Read Rate", value=f"{data.get('read_rate', 0)*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms campaign error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── NPSSurveysCog additional commands ──

    @app_commands.command(name="npssurveys", description="List active surveys")
    async def nps_surveys(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/surveys") as resp:
                data = await resp.json()
                surveys = data.get("surveys", [])
                embed = discord.Embed(title=f"Active Surveys ({len(surveys)})", color=discord.Color.blue(), timestamp=datetime.now())
                for s in surveys[:8]:
                    embed.add_field(name=s.get("title", "?"), value=f"Type: {s.get('survey_type', '?')} | Responses: {s.get('response_count', 0)} | Status: {s.get('status', '?')}", inline=False)
                if not surveys:
                    embed.description = "No surveys"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS surveys error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npsanalytics", description="Survey analytics")
    @app_commands.describe(survey_id="Survey ID")
    async def nps_analytics(self, interaction: discord.Interaction, survey_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/surveys/{survey_id}/analytics") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Survey Analytics: {survey_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Sent", value=data.get("total_sent", 0), inline=True)
                embed.add_field(name="Completed", value=data.get("completed", 0), inline=True)
                embed.add_field(name="Response Rate", value=f"{data.get('response_rate', 0)*100:.0f}%", inline=True)
                if data.get("avg_nps"):
                    embed.add_field(name="Avg NPS", value=data["avg_nps"], inline=True)
                if data.get("avg_csat"):
                    embed.add_field(name="Avg CSAT", value=data["avg_csat"], inline=True)
                if data.get("avg_ces"):
                    embed.add_field(name="Avg CES", value=data["avg_ces"], inline=True)
                dist = data.get("nps_distribution", {})
                if dist:
                    embed.add_field(name="NPS Distribution", value=f"Promoters: {dist.get('promoters', 0)} | Passives: {dist.get('passives', 0)} | Detractors: {dist.get('detractors', 0)}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS analytics error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npscustomer", description="Customer NPS history")
    @app_commands.describe(customer_id="Customer ID")
    async def nps_customer(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/customer/{customer_id}/history") as resp:
                data = await resp.json()
                history = data.get("history", [])
                embed = discord.Embed(title=f"NPS History: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for h in history[:8]:
                    embed.add_field(name=str(h.get("completed_at", "")[:10]), value=f"Score: {h.get('nps_score', '?')} | Label: {h.get('nps_label', '?')}", inline=True)
                if not history:
                    embed.description = "No NPS history"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS customer error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npsbenchmark", description="NPS benchmark")
    async def nps_benchmark(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/benchmark") as resp:
                data = await resp.json()
                embed = discord.Embed(title="NPS Benchmark", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Average", value=data.get("avg_nps", 0), inline=True)
                embed.add_field(name="Median", value=data.get("median_nps", 0), inline=True)
                embed.add_field(name="Std Dev", value=data.get("std_dev", 0), inline=True)
                embed.add_field(name="Sample Size", value=data.get("sample_size", 0), inline=True)
                embed.add_field(name="Min", value=data.get("min", 0), inline=True)
                embed.add_field(name="Max", value=data.get("max", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS benchmark error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npsthemes", description="NPS feedback themes")
    async def nps_themes(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/themes") as resp:
                data = await resp.json()
                themes = data.get("themes", [])
                embed = discord.Embed(title="Feedback Themes", color=discord.Color.blue(), timestamp=datetime.now())
                for t in themes[:10]:
                    embed.add_field(name=t.get("theme", "?").title(), value=f"Mentions: {t.get('count', 0)}", inline=True)
                if not themes:
                    embed.description = "No theme data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS themes error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npsresponserate", description="Response rate trend")
    async def nps_response_rate(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/response-rate-trend") as resp:
                data = await resp.json()
                monthly = data.get("monthly", {})
                embed = discord.Embed(title="Response Rate Trend", color=discord.Color.blue(), timestamp=datetime.now())
                for month, info in list(monthly.items())[:6]:
                    embed.add_field(name=month, value=f"Sent: {info.get('sent', 0)} | Rate: {info.get('rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Overall", value=f"Rate: {data.get('overall_rate', 0)*100:.0f}%", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS response rate error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npspromoters", description="Recent promoter feedback")
    async def nps_promoters(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/promoters") as resp:
                data = await resp.json()
                promoters = data.get("promoters", [])
                embed = discord.Embed(title=f"Promoter Feedback ({len(promoters)})", color=discord.Color.green(), timestamp=datetime.now())
                for p in promoters[:5]:
                    embed.add_field(name=p.get('customer_id', '?'), value=f"Score: {p.get('score', '?')}", inline=False)
                if not promoters:
                    embed.description = "No promoter feedback"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS promoters error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── SuccessAutomationCog additional commands ──

    @app_commands.command(name="successplaydetail", description="Play details")
    @app_commands.describe(play_id="Play ID")
    async def success_play_detail(self, interaction: discord.Interaction, play_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/plays/{play_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=data.get("name", "Play"), color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Trigger", value=data.get("trigger_event", "?"), inline=True)
                embed.add_field(name="Status", value=data.get("status", "?"), inline=True)
                embed.add_field(name="Executions", value=data.get("execution_count", 0), inline=True)
                embed.add_field(name="Cooldown", value=f"{data.get('cooldown_days', 0)} days", inline=True)
                actions = data.get("actions", [])
                for a in actions[:5]:
                    embed.add_field(name=f"Action {a.get('order', '?')}: {a.get('action_type', '?')}", value=str(a.get('config', {}))[:80], inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success play detail error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successtriggerperf", description="Trigger performance metrics")
    async def success_trigger_perf(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/triggers/performance") as resp:
                data = await resp.json()
                triggers = data.get("triggers", [])
                embed = discord.Embed(title="Trigger Performance", color=discord.Color.blue(), timestamp=datetime.now())
                for t in triggers[:8]:
                    embed.add_field(name=t.get("trigger", "?").replace("_", " ").title(), value=f"Execs: {t.get('executions', 0)} | Success: {t.get('success_rate', 0)*100:.0f}%", inline=False)
                if not triggers:
                    embed.description = "No trigger data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success trigger perf error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successcustomerplays", description="Plays triggered for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def success_customer_plays(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/customer/{customer_id}/plays") as resp:
                data = await resp.json()
                plays = data.get("plays", [])
                embed = discord.Embed(title=f"Plays for {customer_id} ({len(plays)})", color=discord.Color.blue(), timestamp=datetime.now())
                for p in plays[:8]:
                    embed.add_field(name=p.get("name", "?"), value=f"Trigger: {p.get('trigger_event', '?')} | Execs: {p.get('execution_count', 0)}", inline=False)
                if not plays:
                    embed.description = "No plays for this customer"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success customer plays error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successautomationsummary", description="Automation summary")
    async def success_automation_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/summary") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Automation Summary", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Plays", value=data.get("total_plays", 0), inline=True)
                embed.add_field(name="Active", value=data.get("active_plays", 0), inline=True)
                embed.add_field(name="Executions", value=data.get("total_executions", 0), inline=True)
                embed.add_field(name="Success Rate", value=f"{data.get('success_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Customers Affected", value=data.get("unique_customers_affected", 0), inline=True)
                embed.add_field(name="Triggers Covered", value=data.get("trigger_events_covered", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success automation summary error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successtimeline", description="Execution timeline for play")
    @app_commands.describe(play_id="Play ID")
    async def success_timeline(self, interaction: discord.Interaction, play_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/plays/{play_id}/timeline") as resp:
                data = await resp.json()
                executions = data.get("executions", [])
                embed = discord.Embed(title=f"Execution Timeline: {play_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for e in executions[:8]:
                    status = "✅" if e.get("status") == "completed" else "❌"
                    embed.add_field(name=f"{status} {e.get('customer_id', '?')}", value=f"Trigger: {e.get('trigger_event', '?')} | {str(e.get('started_at','')[:16])}", inline=False)
                if not executions:
                    embed.description = "No executions"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success timeline error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successrecommend", description="Automation recommendations")
    async def success_recommend(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/recommendations") as resp:
                data = await resp.json()
                recs = data.get("recommendations", [])
                embed = discord.Embed(title="Automation Recommendations", color=discord.Color.blue(), timestamp=datetime.now())
                for r in recs[:8]:
                    embed.add_field(name=r.get("type", "?").replace("_", " ").title(), value=r.get("message", ""), inline=False)
                if not recs:
                    embed.description = "No recommendations"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success recommend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successretry", description="Retry failed execution")
    @app_commands.describe(execution_id="Execution ID")
    async def success_retry(self, interaction: discord.Interaction, execution_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/success/executions/{execution_id}/retry") as resp:
                if resp.ok:
                    embed = discord.Embed(description=f"Retrying execution {execution_id}", color=discord.Color.green())
                else:
                    embed = discord.Embed(description="Retry failed", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success retry error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))


# ── HealthScoringCog additional commands ──

    @app_commands.command(name="healthalerts", description="Health alerts for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def health_alerts(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/alerts/{customer_id}") as resp:
                data = await resp.json()
                alerts = data.get("alerts", [])
                embed = discord.Embed(title=f"Health Alerts: {customer_id} ({len(alerts)})", color=discord.Color.red(), timestamp=datetime.now())
                for a in alerts[:8]:
                    embed.add_field(name=a.get("alert", "Alert"), value=f"Score: {a.get('score', '?')} | {str(a.get('timestamp','')[:16])}", inline=False)
                if not alerts:
                    embed.description = "No active alerts"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health alerts error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthfactors", description="Health score contributing factors")
    @app_commands.describe(customer_id="Customer ID")
    async def health_factors(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/factors/{customer_id}") as resp:
                data = await resp.json()
                factors = data.get("factors", [])
                embed = discord.Embed(title=f"Health Factors: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for f in factors:
                    icon = "🟢" if f.get("impact") == "positive" else "🟡" if f.get("impact") == "neutral" else "🔴"
                    embed.add_field(name=f"{icon} {f.get('component', '?').replace('_',' ').title()}", value=f"Score: {f.get('score', 0)} | {f.get('action', '')}", inline=False)
                if not factors:
                    embed.description = "No factor data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health factors error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthpredict", description="Health score prediction")
    @app_commands.describe(customer_id="Customer ID")
    async def health_predict(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/prediction/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Health Prediction: {customer_id}", color=discord.Color.purple(), timestamp=datetime.now())
                embed.add_field(name="Current", value=data.get("current", "?"), inline=True)
                embed.add_field(name="Predicted (30d)", value=data.get("predicted_30d", "?"), inline=True)
                embed.add_field(name="Direction", value=data.get("direction", "stable"), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health predict error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthexport", description="Export health data as CSV")
    async def health_export(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/export") as resp:
                data = await resp.text()
                embed = discord.Embed(title="Health Export", color=discord.Color.green(), timestamp=datetime.now())
                embed.description = "Health data exported successfully"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health export error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── TicketingCog additional commands ──

    @app_commands.command(name="ticketsuggest", description="Ticket suggestions for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def ticket_suggest(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/suggest/{customer_id}") as resp:
                data = await resp.json()
                suggestions = data.get("suggestions", [])
                embed = discord.Embed(title=f"Ticket Suggestions: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for s in suggestions[:5]:
                    embed.add_field(name=s.get("type", "?").replace("_", " ").title(), value=s.get("title", s.get("subject", "")), inline=False)
                if not suggestions:
                    embed.description = "No suggestions available"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket suggest error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketblocked", description="List blocked tickets")
    async def ticket_blocked(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/blocked") as resp:
                data = await resp.json()
                blocked = data.get("blocked", [])
                embed = discord.Embed(title=f"Blocked Tickets ({len(blocked)})", color=discord.Color.red(), timestamp=datetime.now())
                for b in blocked[:8]:
                    embed.add_field(name=b.get("ticket_id", "?"), value=f"{b.get('subject','')[:60]} — Blocked by: {', '.join(b.get('blocked_by', []))}", inline=False)
                if not blocked:
                    embed.description = "No blocked tickets"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket blocked error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketworkload", description="Agent workload report")
    @app_commands.describe(team="Team name")
    async def ticket_workload(self, interaction: discord.Interaction, team: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/workload/{team}") as resp:
                data = await resp.json()
                members = data.get("members", {})
                embed = discord.Embed(title=f"Workload: {team}", color=discord.Color.blue(), timestamp=datetime.now())
                for agent, info in list(members.items())[:10]:
                    embed.add_field(name=agent, value=f"Open: {info.get('open_count', 0)} | Critical: {info.get('critical_count', 0)}", inline=True)
                if not members:
                    embed.description = "No workload data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket workload error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketrebalance", description="Rebalance team ticket assignments")
    @app_commands.describe(team="Team name")
    async def ticket_rebalance(self, interaction: discord.Interaction, team: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/tickets/rebalance/{team}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Team Rebalanced: {team}", color=discord.Color.green(), timestamp=datetime.now())
                embed.add_field(name="Reassigned", value=data.get("total_reassigned", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket rebalance error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── SentimentAnalysisCog additional commands ──

    @app_commands.command(name="sentimentbreakdown", description="Sentiment breakdown by channel")
    @app_commands.describe(customer_id="Customer ID")
    async def sentiment_breakdown(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/breakdown/{customer_id}") as resp:
                data = await resp.json()
                breakdown = data.get("breakdown", {})
                embed = discord.Embed(title=f"Sentiment Breakdown: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for ch, info in breakdown.items():
                    embed.add_field(name=ch.replace("_", " ").title(), value=f"Avg: {info.get('avg_score', 0)*100:.0f}% | Count: {info.get('count', 0)}", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment breakdown error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentnegative", description="Recent negative interactions")
    async def sentiment_negative(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/negative") as resp:
                data = await resp.json()
                interactions = data.get("interactions", [])
                embed = discord.Embed(title=f"Negative Interactions ({len(interactions)})", color=discord.Color.red(), timestamp=datetime.now())
                for i in interactions[:8]:
                    embed.add_field(name=i.get("customer_id", "?"), value=f"Score: {i.get('score', 0)*100:.0f}% | {str(i.get('created_at','')[:16])}", inline=False)
                if not interactions:
                    embed.description = "No negative interactions"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment negative error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimenttimeline", description="Sentiment timeline for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def sentiment_timeline(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/timeline/{customer_id}") as resp:
                data = await resp.json()
                timeline = data.get("timeline", [])
                embed = discord.Embed(title=f"Sentiment Timeline: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for t in timeline[:10]:
                    embed.add_field(name=t.get("date", "?"), value=f"Score: {t.get('score', 0)*100:.0f}% | Channel: {t.get('channel', '?')}", inline=True)
                if not timeline:
                    embed.description = "No timeline data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment timeline error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="sentimentalerts", description="Sentiment alert count")
    async def sentiment_alerts_count(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/sentiment/alert-count") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Sentiment Alert Summary", color=discord.Color.orange(), timestamp=datetime.now())
                embed.add_field(name="Total Alerts", value=data.get("total_alerts", 0), inline=True)
                embed.add_field(name="High Priority", value=data.get("high_priority", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Sentiment alerts error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── AdoptionAnalyticsCog additional commands ──

    @app_commands.command(name="adoptionforecast", description="Adoption forecast for feature")
    @app_commands.describe(feature_id="Feature ID", days="Days ahead")
    async def adoption_forecast(self, interaction: discord.Interaction, feature_id: str, days: int = 30):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/forecast/{feature_id}?days={days}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Adoption Forecast: {feature_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Trend", value=data.get("trend", "?"), inline=True)
                embed.add_field(name="Current Weekly", value=data.get("current_weekly_events", 0), inline=True)
                forecast = data.get("forecast_events", [])
                if forecast:
                    embed.add_field(name="Forecast (weekly)", value=", ".join(str(v) for v in forecast[:6]), inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption forecast error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionsegments", description="User segment analysis")
    async def adoption_segments(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/segments") as resp:
                data = await resp.json()
                embed = discord.Embed(title="User Segments", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total", value=data.get("total_customers", 0), inline=True)
                embed.add_field(name="Active 30d", value=data.get("active_30d", 0), inline=True)
                embed.add_field(name="Active 7d", value=data.get("active_7d", 0), inline=True)
                embed.add_field(name="Dormant", value=data.get("dormant", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption segments error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionactivation", description="Customer activation score")
    @app_commands.describe(customer_id="Customer ID")
    async def adoption_activation(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/activation/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Activation Score: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Score", value=f"{data.get('activation_score', 0)}/100", inline=True)
                embed.add_field(name="Activated", value=data.get("activated", False), inline=True)
                embed.add_field(name="Features Used", value=data.get("used_features", 0), inline=True)
                embed.add_field(name="Sessions", value=data.get("total_sessions", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption activation error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="adoptionratechange", description="Adoption rate change over time")
    @app_commands.describe(feature_id="Feature ID")
    async def adoption_rate_change(self, interaction: discord.Interaction, feature_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/adoption/rate-change/{feature_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Adoption Rate Change: {feature_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="First Half Users", value=data.get("first_half_users", 0), inline=True)
                embed.add_field(name="Second Half Users", value=data.get("second_half_users", 0), inline=True)
                embed.add_field(name="Change", value=data.get("change", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Adoption rate change error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── OnboardingWizardCog additional commands ──

    @app_commands.command(name="onboardinganalytics", description="Onboarding analytics overview")
    async def onboarding_analytics(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/analytics") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Onboarding Analytics", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Sessions", value=data.get("total_sessions", 0), inline=True)
                embed.add_field(name="Completed", value=data.get("completed", 0), inline=True)
                embed.add_field(name="Completion Rate", value=f"{data.get('completion_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Abandonment Rate", value=f"{data.get('abandonment_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Avg TTV", value=f"{data.get('avg_time_to_value_days', 'N/A')} days", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding analytics error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingstalled", description="Stalled onboarding sessions")
    async def onboarding_stalled(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/stalled") as resp:
                data = await resp.json()
                stalled = data.get("sessions", [])
                embed = discord.Embed(title=f"Stalled Sessions ({len(stalled)})", color=discord.Color.orange(), timestamp=datetime.now())
                for s in stalled[:8]:
                    embed.add_field(name=s.get("customer_id", "?"), value=f"Progress: {s.get('overall_progress', 0)}% | Updated: {str(s.get('updated_at','')[:16])}", inline=False)
                if not stalled:
                    embed.description = "No stalled sessions"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding stalled error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingcustomer", description="Onboarding sessions for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def onboarding_customer(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/customer/{customer_id}") as resp:
                data = await resp.json()
                sessions = data.get("sessions", [])
                embed = discord.Embed(title=f"Onboarding: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Sessions", value=data.get("total_sessions", 0), inline=True)
                for s in sessions[:3]:
                    embed.add_field(name=f"Session: {s.get('session_id','?')[:8]}", value=f"Progress: {s.get('overall_progress', 0)}% | Status: {s.get('status', '?')}", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding customer error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="onboardingexport", description="Export onboarding data")
    async def onboarding_export(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/onboarding/export") as resp:
                embed = discord.Embed(title="Onboarding Export", color=discord.Color.green(), timestamp=datetime.now())
                embed.description = "Onboarding data exported"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Onboarding export error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── KnowledgeBaseCog additional commands ──

    @app_commands.command(name="kbpopular", description="Most popular articles")
    async def kb_popular(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/popular") as resp:
                data = await resp.json()
                articles = data.get("articles", [])
                embed = discord.Embed(title="Popular Articles", color=discord.Color.blue(), timestamp=datetime.now())
                for a in articles[:8]:
                    embed.add_field(name=a.get("title", "?"), value=f"Views: {a.get('view_count', 0)} | Helpful: {a.get('helpful_count', 0)}", inline=False)
                if not articles:
                    embed.description = "No popular articles"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB popular error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbtrending", description="Trending KB topics")
    async def kb_trending(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/trending") as resp:
                data = await resp.json()
                topics = data.get("topics", [])
                embed = discord.Embed(title="Trending Topics", color=discord.Color.blue(), timestamp=datetime.now())
                for t in topics[:10]:
                    embed.add_field(name=t.get("topic", "?"), value=f"Articles: {t.get('articles', 0)} | Mentions: {t.get('count', 0)}", inline=True)
                if not topics:
                    embed.description = "No trending topics"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB trending error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbsearch", description="Search knowledge base")
    @app_commands.describe(query="Search query")
    async def kb_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/search?q={query}") as resp:
                data = await resp.json()
                articles = data.get("articles", [])
                embed = discord.Embed(title=f"KB Search: \"{query}\" ({len(articles)})", color=discord.Color.blue(), timestamp=datetime.now())
                for a in articles[:8]:
                    embed.add_field(name=a.get("title", "?"), value=f"Category: {a.get('category', '?')} | Views: {a.get('view_count', 0)}", inline=False)
                if not articles:
                    embed.description = "No matching articles"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB search error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="kbweekly", description="Weekly KB report")
    async def kb_weekly(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/kb/weekly") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Weekly KB Report", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="New Articles", value=data.get("new_articles", 0), inline=True)
                embed.add_field(name="Recent Views", value=data.get("recent_views", 0), inline=True)
                embed.add_field(name="Published", value=data.get("articles_published", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"KB weekly error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── CommunityPlatformCog additional commands ──

    @app_commands.command(name="communitysearch", description="Search community posts")
    @app_commands.describe(query="Search query")
    async def community_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/search?q={query}") as resp:
                data = await resp.json()
                posts = data.get("posts", [])
                embed = discord.Embed(title=f"Community Search: \"{query}\" ({len(posts)})", color=discord.Color.blue(), timestamp=datetime.now())
                for p in posts[:8]:
                    embed.add_field(name=p.get("title", "?"), value=f"Type: {p.get('post_type', '?')} | 👍 {p.get('upvotes', 0)}", inline=False)
                if not posts:
                    embed.description = "No matching posts"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community search error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communityleaderboard", description="Reputation leaderboard")
    async def community_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/leaderboard") as resp:
                data = await resp.json()
                users = data.get("users", [])
                embed = discord.Embed(title="Reputation Leaderboard", color=discord.Color.gold(), timestamp=datetime.now())
                for u in users[:10]:
                    embed.add_field(name=f"#{u.get('rank', '?')} {u.get('username', '?')}", value=f"Rep: {u.get('reputation', 0)}", inline=False)
                if not users:
                    embed.description = "No leaderboard data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community leaderboard error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communitymodqueue", description="Moderation queue")
    async def community_modqueue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/moderation") as resp:
                data = await resp.json()
                queue = data.get("queue", [])
                embed = discord.Embed(title=f"Moderation Queue ({len(queue)})", color=discord.Color.orange(), timestamp=datetime.now())
                for q in queue[:8]:
                    embed.add_field(name=q.get("title", "?"), value=f"Flags: {q.get('flag_count', 0)} | by {q.get('author_name', '?')}", inline=False)
                if not queue:
                    embed.description = "Queue is clear"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community modqueue error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="communityweekly", description="Weekly community summary")
    async def community_weekly_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/community/weekly") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Weekly Community Summary", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="New Posts", value=data.get("new_posts", 0), inline=True)
                embed.add_field(name="New Comments", value=data.get("new_comments", 0), inline=True)
                embed.add_field(name="Total Votes", value=data.get("total_votes", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Community weekly error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── CommunicationHubCog additional commands ──

    @app_commands.command(name="commshistory", description="Notification history for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def comms_history(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/history/{customer_id}") as resp:
                data = await resp.json()
                records = data.get("records", [])
                embed = discord.Embed(title=f"Notification History: {customer_id} ({len(records)})", color=discord.Color.blue(), timestamp=datetime.now())
                for r in records[:8]:
                    embed.add_field(name=r.get("channel", "?"), value=f"Type: {r.get('notification_type', '?')} | Status: {r.get('status', '?')} | {str(r.get('created_at','')[:16])}", inline=False)
                if not records:
                    embed.description = "No notification history"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms history error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commsfailed", description="Failed deliveries")
    async def comms_failed(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/failed") as resp:
                data = await resp.json()
                failed = data.get("failed", [])
                embed = discord.Embed(title=f"Failed Deliveries ({len(failed)})", color=discord.Color.red(), timestamp=datetime.now())
                for f in failed[:8]:
                    embed.add_field(name=f.get("record_id", "?"), value=f"Channel: {f.get('channel', '?')} | Error: {str(f.get('error', '?'))[:60]}", inline=False)
                if not failed:
                    embed.description = "No failed deliveries"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms failed error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commstemplates", description="Notification templates")
    async def comms_templates(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/templates") as resp:
                data = await resp.json()
                templates = data.get("templates", [])
                embed = discord.Embed(title=f"Notification Templates ({len(templates)})", color=discord.Color.blue(), timestamp=datetime.now())
                for t in templates[:8]:
                    embed.add_field(name=t.get("name", "?"), value=f"Channel: {t.get('channel', '?')} | Subject: {t.get('subject', '')[:40]}", inline=False)
                if not templates:
                    embed.description = "No templates"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms templates error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="commsdaily", description="Daily communication summary")
    async def comms_daily(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/communication/daily") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Daily Summary", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Sent", value=data.get("total_sent", 0), inline=True)
                embed.add_field(name="Delivered", value=data.get("delivered", 0), inline=True)
                embed.add_field(name="Read", value=data.get("read", 0), inline=True)
                embed.add_field(name="Failed", value=data.get("failed", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Comms daily error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── NPSSurveysCog additional commands ──

    @app_commands.command(name="npstrend", description="NPS score trend")
    async def nps_trend(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/trend") as resp:
                data = await resp.json()
                embed = discord.Embed(title="NPS Trend", color=discord.Color.blue(), timestamp=datetime.now())
                for month, info in list(data.items())[:8]:
                    embed.add_field(name=month, value=f"Avg: {info.get('avg', 0)} | Count: {info.get('count', 0)}", inline=True)
                if not data:
                    embed.description = "No NPS trend data"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS trend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npsdetractors", description="Detractor feedback")
    @app_commands.describe(survey_id="Survey ID")
    async def nps_detractors(self, interaction: discord.Interaction, survey_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/surveys/{survey_id}/detractors") as resp:
                data = await resp.json()
                feedback = data.get("feedback", [])
                embed = discord.Embed(title=f"Detractor Feedback ({len(feedback)})", color=discord.Color.red(), timestamp=datetime.now())
                for f in feedback[:5]:
                    embed.add_field(name=f.get("customer_id", "?"), value=f"Score: {f.get('nps_score', '?')} | {f.get('comments', '')[:100]}", inline=False)
                if not feedback:
                    embed.description = "No detractor feedback"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS detractors error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npssegments", description="NPS benchmark by segment")
    async def nps_segments(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/benchmark/segments") as resp:
                data = await resp.json()
                embed = discord.Embed(title="NPS by Segment", color=discord.Color.blue(), timestamp=datetime.now())
                for seg, info in data.items():
                    embed.add_field(name=seg.replace("_", " ").title(), value=f"Avg: {info.get('avg', 0)} | Count: {info.get('count', 0)}", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS segments error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="npscompletion", description="Survey completion rate")
    @app_commands.describe(survey_id="Survey ID")
    async def nps_completion(self, interaction: discord.Interaction, survey_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/nps/surveys/{survey_id}/completion") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Completion Rate: {survey_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Sent", value=data.get("sent", 0), inline=True)
                embed.add_field(name="Started", value=data.get("started", 0), inline=True)
                embed.add_field(name="Completed", value=data.get("completed", 0), inline=True)
                embed.add_field(name="Completion Rate", value=f"{data.get('completion_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Drop-off Rate", value=f"{data.get('drop_off_rate', 0)*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"NPS completion error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── SuccessAutomationCog additional commands ──

    @app_commands.command(name="successstats", description="Automation statistics")
    async def success_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/statistics") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Automation Statistics", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Plays", value=data.get("total_plays", 0), inline=True)
                embed.add_field(name="Active", value=data.get("active_plays", 0), inline=True)
                embed.add_field(name="Total Executions", value=data.get("total_executions", 0), inline=True)
                embed.add_field(name="Error Rate", value=f"{data.get('error_rate', 0)*100:.0f}%", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success stats error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successerrors", description="Failed executions")
    async def success_errors(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/executions/errors") as resp:
                data = await resp.json()
                errors = data.get("errors", [])
                embed = discord.Embed(title=f"Execution Errors ({len(errors)})", color=discord.Color.red(), timestamp=datetime.now())
                for e in errors[:8]:
                    embed.add_field(name=e.get("play_id", "?"), value=f"Error: {str(e.get('error', '?'))[:80]} | {str(e.get('started_at','')[:16])}", inline=False)
                if not errors:
                    embed.description = "No execution errors"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success errors error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successplayperf", description="Play performance metrics")
    @app_commands.describe(play_id="Play ID")
    async def success_play_perf(self, interaction: discord.Interaction, play_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/plays/{play_id}/performance") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Play Performance: {play_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Executions", value=data.get("total_executions", 0), inline=True)
                embed.add_field(name="Success Rate", value=f"{data.get('success_rate', 0)*100:.0f}%", inline=True)
                embed.add_field(name="Avg Time", value=f"{data.get('avg_execution_time_ms', 0)} ms", inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success play perf error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="successaudit", description="Automation audit log")
    async def success_audit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/success/audit") as resp:
                data = await resp.json()
                changes = data.get("changes", [])
                embed = discord.Embed(title=f"Audit Log ({len(changes)})", color=discord.Color.blue(), timestamp=datetime.now())
                for c in changes[:8]:
                    embed.add_field(name=c.get("play_id", "?"), value=f"{c.get('action', '?')}: {c.get('name', '')} | {str(c.get('timestamp','')[:16])}", inline=False)
                if not changes:
                    embed.description = "No audit log entries"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Success audit error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

# ── Additional HealthScoring commands ──

    @app_commands.command(name="healthtrend", description="Health scoring trend for customer")
    @app_commands.describe(customer_id="Customer ID")
    async def health_trend(self, interaction: discord.Interaction, customer_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/trend/{customer_id}") as resp:
                data = await resp.json()
                embed = discord.Embed(title=f"Health Trend: {customer_id}", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Direction", value=data.get("direction", "?"), inline=True)
                embed.add_field(name="Start Score", value=data.get("start_score", "?"), inline=True)
                embed.add_field(name="End Score", value=data.get("end_score", "?"), inline=True)
                embed.add_field(name="Change", value=data.get("change", "?"), inline=True)
                embed.add_field(name="Volatility", value=data.get("volatility", "?"), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health trend error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthsummary", description="Summary of all health profiles")
    async def health_summary_all(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/health/summary") as resp:
                data = await resp.json()
                embed = discord.Embed(title="Health Profile Summary", color=discord.Color.blue(), timestamp=datetime.now())
                embed.add_field(name="Total Profiles", value=data.get("total_profiles", 0), inline=True)
                embed.add_field(name="Avg Score", value=data.get("avg_score", "?"), inline=True)
                embed.add_field(name="Median Score", value=data.get("median_score", "?"), inline=True)
                embed.add_field(name="At Risk", value=data.get("risk_distribution", {}).get("high", 0) + data.get("risk_distribution", {}).get("critical", 0), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health summary error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="healthschedule", description="Schedule health check")
    @app_commands.describe(customer_id="Customer ID", days="Days from now")
    async def health_schedule(self, interaction: discord.Interaction, customer_id: str, days: int = 7):
        await interaction.response.defer()
        try:
            async with self.bot.session.post(f"{self.api_base}/health/schedule", json={"customer_id": customer_id, "days": days}) as resp:
                data = await resp.json()
                embed = discord.Embed(title="Health Check Scheduled", color=discord.Color.green(), timestamp=datetime.now())
                embed.add_field(name="Check ID", value=data.get("check_id", "?"), inline=True)
                embed.add_field(name="Scheduled", value=str(data.get("scheduled_at", "")[:16]), inline=True)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Health schedule error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000})

# ── Additional Ticketing commands ──

    @app_commands.command(name="ticketchain", description="View ticket chain")
    @app_commands.describe(ticket_id="Ticket ID")
    async def ticket_chain(self, interaction: discord.Interaction, ticket_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/{ticket_id}/chain") as resp:
                data = await resp.json()
                chain = data.get("chain", [])
                embed = discord.Embed(title=f"Ticket Chain: {ticket_id} ({len(chain)})", color=discord.Color.blue(), timestamp=datetime.now())
                for t in chain:
                    embed.add_field(name=t.get("ticket_id", "?"), value=f"Subject: {t.get('subject', '')[:40]} | Status: {t.get('status', '?')}", inline=False)
                if not chain:
                    embed.description = "No related tickets"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket chain error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="ticketaudit", description="Ticket audit log")
    @app_commands.describe(ticket_id="Ticket ID")
    async def ticket_audit(self, interaction: discord.Interaction, ticket_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/{ticket_id}/audit") as resp:
                data = await resp.json()
                log = data.get("log", [])
                embed = discord.Embed(title=f"Audit Log: {ticket_id}", color=discord.Color.blue(), timestamp=datetime.now())
                for entry in log[:10]:
                    embed.add_field(name=entry.get("action", "?").replace("_", " ").title(), value=f"by {entry.get('actor', '?')} | {str(entry.get('timestamp','')[:16])}", inline=False)
                if not log:
                    embed.description = "No audit entries"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket audit error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="tickettemplates", description="Available ticket templates")
    async def ticket_templates(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/templates") as resp:
                data = await resp.json()
                templates = data.get("templates", [])
                embed = discord.Embed(title="Ticket Templates", color=discord.Color.blue(), timestamp=datetime.now())
                for t in templates:
                    embed.add_field(name=t.get("name", "?"), value=f"ID: {t.get('id', '?')} | Priority: {t.get('fields', {}).get('priority', '?')}", inline=False)
                if not templates:
                    embed.description = "No templates"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket templates error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

    @app_commands.command(name="tickettimeline", description="Ticket event timeline")
    @app_commands.describe(ticket_id="Ticket ID")
    async def ticket_timeline(self, interaction: discord.Interaction, ticket_id: str):
        await interaction.response.defer()
        try:
            async with self.bot.session.get(f"{self.api_base}/tickets/{ticket_id}/timeline") as resp:
                data = await resp.json()
                timeline = data.get("timeline", [])
                embed = discord.Embed(title=f"Timeline: {ticket_id} ({len(timeline)})", color=discord.Color.blue(), timestamp=datetime.now())
                for entry in timeline[:8]:
                    embed.add_field(name=entry.get("action", "?").title(), value=str(entry.get("timestamp", "")[:16]), inline=False)
                if not timeline:
                    embed.description = "No timeline entries"
                await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Ticket timeline error: {e}")
            await interaction.followup.send(embed=discord.Embed(description="Service unavailable", color=0xFF0000))

async def setup(bot):
    await bot.add_cog(HealthScoringCog(bot))
    await bot.add_cog(TicketingCog(bot))
    await bot.add_cog(SentimentAnalysisCog(bot))
    await bot.add_cog(AdoptionAnalyticsCog(bot))
    await bot.add_cog(OnboardingWizardCog(bot))
    await bot.add_cog(KnowledgeBaseCog(bot))
    await bot.add_cog(CommunityPlatformCog(bot))
    await bot.add_cog(CommunicationHubCog(bot))
    await bot.add_cog(NPSSurveysCog(bot))
    await bot.add_cog(SuccessAutomationCog(bot))

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
        return {"total_ops": 0, "satisfied": 0, "neutral": 0, "dissatisfied": 0, "nps": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class CXCogResult(BaseModel):
    success: bool = True
    operation: str = ""
    customer_id: str = ""
    interaction_id: str = ""
    satisfaction: Optional[int] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CXCogBatch(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    responded: int = Field(default=0)

    def record_success(self) -> None:
        self.processed += 1

    def record_response(self) -> None:
        self.responded += 1

    def complete(self) -> None:
        self.status = "completed"

class CXCogMetrics:
    def __init__(self) -> None:
        self.interactions: int = 0
        self.satisfaction_sum: int = 0
        self.satisfaction_count: int = 0
        self.errors: int = 0

    def record_interaction(self, satisfaction: Optional[int] = None, error: bool = False) -> None:
        self.interactions += 1
        if satisfaction is not None:
            self.satisfaction_sum += satisfaction
            self.satisfaction_count += 1
        if error:
            self.errors += 1

    def avg_satisfaction(self) -> float:
        return round(self.satisfaction_sum / max(self.satisfaction_count, 1), 1)

    def summary(self) -> Dict[str, Any]:
        return {"interactions": self.interactions, "errors": self.errors,
                "avg_satisfaction": self.avg_satisfaction(),
                "error_rate": round(self.errors / max(self.interactions, 1) * 100, 1)}
