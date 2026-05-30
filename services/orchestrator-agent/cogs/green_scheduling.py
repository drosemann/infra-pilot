"""Green Scheduling Cog - Schedule workloads when grid carbon is lowest."""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class UrgencyTier(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class JobStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    FAILED = "failed"
    SKIPPED = "skipped"


class GreenJob:
    """A scheduled job with carbon-aware scheduling."""

    def __init__(self, job_id: str, name: str, command: str, urgency: UrgencyTier):
        self.job_id = job_id
        self.name = name
        self.command = command
        self.urgency = urgency
        self.status = JobStatus.PENDING
        self.max_delay_hours: int = 24
        self.carbon_threshold: Optional[float] = None
        self.preferred_hours: Optional[tuple[int, int]] = None
        self.allowed_days: Optional[list[int]] = None
        self.notify_on_deferral: bool = True
        self.scheduled_at: Optional[datetime] = None
        self.executed_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.original_energy_kwh: float = 0.0
        self.green_energy_kwh: float = 0.0
        self.co2_saved_grams: float = 0.0
        self.error_message: Optional[str] = None
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "command": self.command,
            "urgency": self.urgency.value,
            "status": self.status.value,
            "max_delay_hours": self.max_delay_hours,
            "carbon_threshold": self.carbon_threshold,
            "preferred_hours": self.preferred_hours,
            "allowed_days": self.allowed_days,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "original_energy_kwh": self.original_energy_kwh,
            "green_energy_kwh": self.green_energy_kwh,
            "co2_saved_grams": self.co2_saved_grams,
            "created_at": self.created_at.isoformat(),
        }


class CarbonForecast:
    """Carbon intensity forecast for a region."""

    def __init__(self, region: str):
        self.region = region
        self.current_intensity: float = 300.0
        self.forecast: list[dict[str, Any]] = []
        self.updated_at = datetime.utcnow()
        self._generate_forecast()

    def _generate_forecast(self):
        base = random.uniform(150, 400)
        for hour in range(48):
            variation = random.uniform(-100, 100)
            time_of_day_factor = 0.5 + 0.5 * abs(12 - (hour % 24)) / 12
            intensity = max(50, base + variation * time_of_day_factor)
            self.forecast.append({
                "hour": (datetime.utcnow() + timedelta(hours=hour)).isoformat(),
                "intensity_g_per_kwh": round(intensity, 1),
                "renewable_pct": round(100 - intensity / 5, 1),
            })

    def get_forecast(self) -> list[dict[str, Any]]:
        return self.forecast

    def get_lowest_carbon_window(self, window_hours: int = 4) -> dict[str, Any]:
        best_window = None
        best_avg = float("inf")
        for i in range(len(self.forecast) - window_hours + 1):
            window = self.forecast[i:i + window_hours]
            avg = sum(f["intensity_g_per_kwh"] for f in window) / window_hours
            if avg < best_avg:
                best_avg = avg
                best_window = {
                    "start": window[0]["hour"],
                    "end": window[-1]["hour"],
                    "avg_intensity": round(best_avg, 1),
                    "window_hours": window_hours,
                }
        return best_window or {"error": "No suitable window found"}

    def get_current_intensity(self) -> dict[str, Any]:
        return {
            "region": self.region,
            "intensity_g_per_kwh": self.current_intensity,
            "renewable_pct": round(100 - self.current_intensity / 5, 1),
            "timestamp": self.updated_at.isoformat(),
        }


class GreenScheduling:
    """Carbon-aware job scheduler."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.jobs: dict[str, GreenJob] = {}
        self.forecast = CarbonForecast("region-default")
        self._schedule_task: Optional[asyncio.Task] = None
        self._seed_jobs()

    def _seed_jobs(self):
        demo_jobs = [
            ("job-001", "nightly-backup", "backup_manager create --all", UrgencyTier.LOW),
            ("job-002", "data-analytics", "analytics run --full", UrgencyTier.NORMAL),
            ("job-003", "model-training", "ml train --model v2", UrgencyTier.BACKGROUND),
            ("job-004", "report-generation", "report generate --monthly", UrgencyTier.LOW),
            ("job-005", "cache-warming", "cdn warm --all", UrgencyTier.BACKGROUND),
        ]
        for jid, name, cmd, urgency in demo_jobs:
            job = GreenJob(jid, name, cmd, urgency)
            job.status = JobStatus.COMPLETED if hash(jid) % 3 != 0 else JobStatus.PENDING
            job.co2_saved_grams = random.uniform(100, 5000)
            self.jobs[jid] = job

    async def initialize(self):
        self._schedule_task = asyncio.create_task(self._scheduling_loop())
        logger.info("GreenScheduling initialized")

    async def close(self):
        if self._schedule_task:
            self._schedule_task.cancel()
        logger.info("GreenScheduling closed")

    async def _scheduling_loop(self):
        while True:
            try:
                await asyncio.sleep(300)
                self._evaluate_pending_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduling error: %s", e)

    def _evaluate_pending_jobs(self):
        for job in self.jobs.values():
            if job.status != JobStatus.PENDING:
                continue
            best_window = self.forecast.get_lowest_carbon_window(2)
            if isinstance(best_window.get("avg_intensity"), (int, float)):
                if job.carbon_threshold and best_window["avg_intensity"] > job.carbon_threshold:
                    job.status = JobStatus.DEFERRED
                else:
                    job.status = JobStatus.SCHEDULED
                    job.scheduled_at = datetime.fromisoformat(best_window["start"])

    def add_job(self, name: str, command: str,
                urgency: str = "normal", **kwargs) -> GreenJob:
        try:
            tier = UrgencyTier(urgency)
        except ValueError:
            tier = UrgencyTier.NORMAL
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        job = GreenJob(job_id, name, command, tier)
        if "max_delay_hours" in kwargs:
            job.max_delay_hours = kwargs["max_delay_hours"]
        if "carbon_threshold" in kwargs:
            job.carbon_threshold = kwargs["carbon_threshold"]
        if "preferred_hours" in kwargs:
            job.preferred_hours = kwargs["preferred_hours"]
        if "allowed_days" in kwargs:
            job.allowed_days = kwargs["allowed_days"]
        self.jobs[job_id] = job
        self._evaluate_pending_jobs()
        return job

    def get_job(self, job_id: str) -> Optional[GreenJob]:
        return self.jobs.get(job_id)

    def list_jobs(self, status: Optional[str] = None,
                  urgency: Optional[str] = None) -> list[GreenJob]:
        result = list(self.jobs.values())
        if status:
            result = [j for j in result if j.status.value == status]
        if urgency:
            result = [j for j in result if j.urgency.value == urgency]
        return sorted(result, key=lambda j: j.created_at, reverse=True)

    def execute_job(self, job_id: str) -> Optional[GreenJob]:
        job = self.jobs.get(job_id)
        if not job or job.status != JobStatus.SCHEDULED:
            return None
        job.status = JobStatus.RUNNING
        job.executed_at = datetime.utcnow()
        original_intensity = random.uniform(300, 500)
        green_intensity = self.forecast.current_intensity
        energy_kwh = random.uniform(0.5, 5.0)
        job.original_energy_kwh = energy_kwh
        job.green_energy_kwh = energy_kwh * (green_intensity / original_intensity)
        job.co2_saved_grams = (original_intensity - green_intensity) * energy_kwh
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        return job

    def get_savings_report(self) -> dict[str, Any]:
        completed = [j for j in self.jobs.values() if j.status == JobStatus.COMPLETED]
        total_original = sum(j.original_energy_kwh for j in completed)
        total_green = sum(j.green_energy_kwh for j in completed)
        total_co2_saved = sum(j.co2_saved_grams for j in completed)
        return {
            "total_jobs": len(self.jobs),
            "completed_jobs": len(completed),
            "original_energy_kwh": round(total_original, 2),
            "green_energy_kwh": round(total_green, 2),
            "energy_saved_kwh": round(total_original - total_green, 2),
            "co2_saved_grams": round(total_co2_saved, 1),
            "co2_saved_kg": round(total_co2_saved / 1000, 2),
            "savings_pct": round((1 - total_green / max(total_original, 0.01)) * 100, 1),
        }

    def get_forecast(self) -> dict[str, Any]:
        return {
            "current": self.forecast.get_current_intensity(),
            "best_window": self.forecast.get_lowest_carbon_window(4),
            "forecast": self.forecast.get_forecast()[:24],
        }


class GreenSchedulingCog(commands.Cog):
    """Discord cog for green scheduling."""

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = GreenScheduling({})

    async def cog_load(self):
        await self.scheduler.initialize()

    async def cog_unload(self):
        await self.scheduler.close()

    @discord.app_commands.command(name="green_forecast", description="Show carbon intensity forecast")
    async def green_forecast(self, interaction: discord.Interaction):
        data = self.scheduler.get_forecast()
        embed = discord.Embed(title="Carbon Intensity Forecast", color=discord.Color.green())
        curr = data["current"]
        embed.add_field(name="Current Intensity",
                       value=f"{curr['intensity_g_per_kwh']} gCO2/kWh\n"
                            f"Renewable: {curr['renewable_pct']}%", inline=True)
        bw = data["best_window"]
        embed.add_field(name="Best Window (4h)",
                       value=f"Avg: {bw['avg_intensity']} gCO2/kWh\n"
                            f"Start: {bw.get('start', 'N/A')[:16]}", inline=True)
        embed.set_footer(text="Forecast for next 48 hours")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="green_jobs", description="List green jobs")
    async def green_jobs(self, interaction: discord.Interaction,
                         status: Optional[str] = None):
        jobs = self.scheduler.list_jobs(status=status)
        embed = discord.Embed(title="Green Jobs", color=discord.Color.blue())
        if not jobs:
            embed.description = "No jobs found."
        else:
            lines = []
            for j in jobs[:20]:
                emoji = {"completed": "✅", "scheduled": "📅", "pending": "⏳",
                         "deferred": "⏰", "running": "🔄", "failed": "❌"}
                e = emoji.get(j.status.value, "⚪")
                lines.append(f"{e} **{j.name}** (`{j.job_id}`)")
                lines.append(f"   Urgency: {j.urgency.value} | CO2 Saved: {j.co2_saved_grams:.0f}g")
            embed.description = "\n".join(lines[:20])
        report = self.scheduler.get_savings_report()
        embed.set_footer(text=f"CO2 Saved: {report['co2_saved_kg']} kg | "
                            f"Savings: {report['savings_pct']}%")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="green_schedule", description="Add a green job")
    async def green_schedule(self, interaction: discord.Interaction,
                             name: str, command: str, urgency: str = "normal"):
        job = self.scheduler.add_job(name, command, urgency)
        embed = discord.Embed(title="Green Job Created", color=discord.Color.green())
        embed.add_field(name="Name", value=job.name, inline=True)
        embed.add_field(name="Job ID", value=job.job_id, inline=True)
        embed.add_field(name="Urgency", value=job.urgency.value, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="green_report", description="Get green savings report")
    async def green_report(self, interaction: discord.Interaction):
        report = self.scheduler.get_savings_report()
        embed = discord.Embed(title="Green Scheduling Savings Report", color=discord.Color.green())
        for k, v in report.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(GreenSchedulingCog(bot))
