"""Auto-Shutdown Policies Cog - Auto-stop dev/staging during off-hours."""

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


class ShutdownAction(Enum):
    SHUTDOWN = "shutdown"
    STARTUP = "startup"
    NOTIFY = "notify"
    DRAIN = "drain"


class PolicyStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"


class ShutdownTime:
    """Defines when to shut down."""

    def __init__(self, weekday: int, hour: int, minute: int = 0):
        self.weekday = weekday
        self.hour = hour
        self.minute = minute

    def to_dict(self) -> dict[str, Any]:
        return {"weekday": self.weekday, "hour": self.hour, "minute": self.minute}


class StartupTime:
    """Defines when to start up."""

    def __init__(self, weekday: int, hour: int, minute: int = 0):
        self.weekday = weekday
        self.hour = hour
        self.minute = minute

    def to_dict(self) -> dict[str, Any]:
        return {"weekday": self.weekday, "hour": self.hour, "minute": self.minute}


class AutoShutdownPolicy:
    """Policy for auto-shutdown of environments."""

    def __init__(self, policy_id: str, name: str, environment_tags: list[str]):
        self.policy_id = policy_id
        self.name = name
        self.environment_tags = environment_tags
        self.shutdown_times: list[ShutdownTime] = []
        self.startup_times: list[StartupTime] = []
        self.grace_period_minutes: int = 15
        self.drain_timeout_minutes: int = 5
        self.force_stop_after_minutes: int = 30
        self.notify_users: bool = True
        self.allow_override: bool = True
        self.override_max_hours: int = 4
        self.dry_run: bool = False
        self.status: PolicyStatus = PolicyStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "environment_tags": self.environment_tags,
            "shutdown_times": [s.to_dict() for s in self.shutdown_times],
            "startup_times": [s.to_dict() for s in self.startup_times],
            "grace_period_minutes": self.grace_period_minutes,
            "drain_timeout_minutes": self.drain_timeout_minutes,
            "force_stop_after_minutes": self.force_stop_after_minutes,
            "notify_users": self.notify_users,
            "allow_override": self.allow_override,
            "override_max_hours": self.override_max_hours,
            "dry_run": self.dry_run,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Environment:
    """An environment that can be auto-shutdown."""

    def __init__(self, env_id: str, name: str, tags: list[str]):
        self.env_id = env_id
        self.name = name
        self.tags = tags
        self.is_running: bool = True
        self.override_until: Optional[datetime] = None
        self.resources: dict[str, Any] = {
            "containers": random.randint(1, 8),
            "cpu_cores": random.randint(1, 8),
            "memory_gb": random.randint(2, 32),
            "cost_per_hour": round(random.uniform(0.10, 1.50), 2),
        }
        self.last_action: Optional[str] = None
        self.last_action_time: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "env_id": self.env_id,
            "name": self.name,
            "tags": self.tags,
            "is_running": self.is_running,
            "override_until": self.override_until.isoformat() if self.override_until else None,
            "resources": self.resources,
            "last_action": self.last_action,
            "last_action_time": self.last_action_time.isoformat() if self.last_action_time else None,
        }


class AutoShutdownManager:
    """Manager for auto-shutdown policies."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.policies: dict[str, AutoShutdownPolicy] = {}
        self.environments: dict[str, Environment] = {}
        self._executor_task: Optional[asyncio.Task] = None
        self._seed_data()

    def _seed_data(self):
        self.policies["pol-dev-nightly"] = AutoShutdownPolicy(
            "pol-dev-nightly", "Dev Nightly Shutdown", ["dev", "staging"]
        )
        self.policies["pol-dev-nightly"].shutdown_times = [
            ShutdownTime(0, 19), ShutdownTime(1, 19), ShutdownTime(2, 19),
            ShutdownTime(3, 19), ShutdownTime(4, 19),
        ]
        self.policies["pol-dev-nightly"].startup_times = [
            StartupTime(0, 8), StartupTime(1, 8), StartupTime(2, 8),
            StartupTime(3, 8), StartupTime(4, 8),
        ]

        self.policies["pol-weekend"] = AutoShutdownPolicy(
            "pol-weekend", "Weekend Shutdown", ["staging", "test"]
        )
        self.policies["pol-weekend"].shutdown_times = [ShutdownTime(5, 18)]

        for i in range(5):
            env = Environment(f"env-{i:03d}", f"{['dev', 'staging', 'test', 'qa', 'demo'][i]}",
                             [["dev"], ["staging"], ["test"], ["qa"], ["demo"]][i])
            self.environments[env.env_id] = env

    async def initialize(self):
        self._executor_task = asyncio.create_task(self._executor_loop())
        logger.info("AutoShutdownManager initialized")

    async def close(self):
        if self._executor_task:
            self._executor_task.cancel()
        logger.info("AutoShutdownManager closed")

    async def _executor_loop(self):
        while True:
            try:
                await asyncio.sleep(60)
                self._check_policies()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Executor error: %s", e)

    def _check_policies(self):
        now = datetime.utcnow()
        for policy in self.policies.values():
            if policy.status != PolicyStatus.ACTIVE:
                continue
            for st in policy.shutdown_times:
                if (now.weekday() == st.weekday and now.hour == st.hour
                        and now.minute == st.minute):
                    self._execute_shutdown(policy)
            for sut in policy.startup_times:
                if (now.weekday() == sut.weekday and now.hour == sut.hour
                        and now.minute == sut.minute):
                    self._execute_startup(policy)

    def _execute_shutdown(self, policy: AutoShutdownPolicy):
        for env in self.environments.values():
            if any(tag in env.tags for tag in policy.environment_tags):
                if env.override_until and env.override_until > datetime.utcnow():
                    logger.info("Skipping shutdown of %s (overridden)", env.name)
                    continue
                if not env.is_running:
                    continue
                if policy.dry_run:
                    logger.info("[DRY RUN] Would shut down %s", env.name)
                    env.last_action = "dry_shutdown"
                else:
                    env.is_running = False
                    env.last_action = "auto_shutdown"
                    env.last_action_time = datetime.utcnow()
                    logger.info("Auto-shutdown: %s", env.name)

    def _execute_startup(self, policy: AutoShutdownPolicy):
        for env in self.environments.values():
            if any(tag in env.tags for tag in policy.environment_tags):
                if env.is_running:
                    continue
                if policy.dry_run:
                    logger.info("[DRY RUN] Would start up %s", env.name)
                    env.last_action = "dry_startup"
                else:
                    env.is_running = True
                    env.last_action = "auto_startup"
                    env.last_action_time = datetime.utcnow()
                    logger.info("Auto-startup: %s", env.name)

    def create_policy(self, name: str, tags: list[str],
                      shutdown_hours: Optional[list[int]] = None,
                      startup_hours: Optional[list[int]] = None) -> AutoShutdownPolicy:
        policy_id = f"pol-{uuid.uuid4().hex[:8]}"
        policy = AutoShutdownPolicy(policy_id, name, tags)
        if shutdown_hours:
            for hour in shutdown_hours:
                policy.shutdown_times.append(ShutdownTime(datetime.utcnow().weekday(), hour))
        if startup_hours:
            for hour in startup_hours:
                policy.startup_times.append(StartupTime(datetime.utcnow().weekday(), hour))
        self.policies[policy_id] = policy
        return policy

    def get_policy(self, policy_id: str) -> Optional[AutoShutdownPolicy]:
        return self.policies.get(policy_id)

    def list_policies(self, status: Optional[str] = None) -> list[AutoShutdownPolicy]:
        result = list(self.policies.values())
        if status:
            result = [p for p in result if p.status.value == status]
        return result

    def update_policy(self, policy_id: str, updates: dict[str, Any]) -> Optional[AutoShutdownPolicy]:
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        if "grace_period_minutes" in updates:
            policy.grace_period_minutes = updates["grace_period_minutes"]
        if "dry_run" in updates:
            policy.dry_run = updates["dry_run"]
        if "notify_users" in updates:
            policy.notify_users = updates["notify_users"]
        policy.updated_at = datetime.utcnow()
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self.policies:
            del self.policies[policy_id]
            return True
        return False

    def pause_policy(self, policy_id: str) -> bool:
        policy = self.policies.get(policy_id)
        if not policy:
            return False
        policy.status = PolicyStatus.PAUSED
        policy.updated_at = datetime.utcnow()
        return True

    def resume_policy(self, policy_id: str) -> bool:
        policy = self.policies.get(policy_id)
        if not policy:
            return False
        policy.status = PolicyStatus.ACTIVE
        policy.updated_at = datetime.utcnow()
        return True

    def list_environments(self, tag: Optional[str] = None) -> list[Environment]:
        if tag:
            return [e for e in self.environments.values() if tag in e.tags]
        return list(self.environments.values())

    def set_override(self, env_id: str, hours: int) -> bool:
        env = self.environments.get(env_id)
        if not env:
            return False
        env.override_until = datetime.utcnow() + timedelta(hours=hours)
        env.last_action = f"override_{hours}h"
        env.last_action_time = datetime.utcnow()
        return True

    def start_environment(self, env_id: str) -> bool:
        env = self.environments.get(env_id)
        if not env:
            return False
        env.is_running = True
        env.last_action = "manual_start"
        env.last_action_time = datetime.utcnow()
        return True

    def stop_environment(self, env_id: str) -> bool:
        env = self.environments.get(env_id)
        if not env:
            return False
        env.is_running = False
        env.last_action = "manual_stop"
        env.last_action_time = datetime.utcnow()
        return True

    def get_savings(self) -> dict[str, Any]:
        total_off_hours = 0
        for policy in self.policies.values():
            if policy.status != PolicyStatus.ACTIVE:
                continue
            for st in policy.shutdown_times:
                for sut in policy.startup_times:
                    if st.weekday == sut.weekday:
                        off_hours = st.hour - sut.hour
                        if off_hours > 0:
                            total_off_hours += off_hours
        matching_envs = []
        for policy in self.policies.values():
            for env in self.environments.values():
                if any(tag in env.tags for tag in policy.environment_tags):
                    if env not in matching_envs:
                        matching_envs.append(env)
        monthly_off = total_off_hours * 4.33
        total_hourly = sum(e.resources["cost_per_hour"] for e in matching_envs)
        monthly_savings = monthly_off * total_hourly
        return {
            "weekly_off_hours": total_off_hours,
            "monthly_off_hours": round(monthly_off, 1),
            "environments_affected": len(matching_envs),
            "total_hourly_rate": round(total_hourly, 2),
            "monthly_savings": round(monthly_savings, 2),
            "annual_savings": round(monthly_savings * 12, 2),
        }


class AutoShutdownCog(commands.Cog):
    """Discord cog for auto-shutdown policies."""

    def __init__(self, bot):
        self.bot = bot
        self.mgr = AutoShutdownManager({})

    async def cog_load(self):
        await self.mgr.initialize()

    async def cog_unload(self):
        await self.mgr.close()

    @discord.app_commands.command(name="shutdown_policies", description="List auto-shutdown policies")
    async def shutdown_policies(self, interaction: discord.Interaction):
        policies = self.mgr.list_policies()
        embed = discord.Embed(title="Auto-Shutdown Policies", color=discord.Color.blue())
        for p in policies:
            status_emoji = {"active": "🟢", "paused": "🟡", "expired": "🔴"}
            emoji = status_emoji.get(p.status.value, "⚪")
            sh = ", ".join(f"Day {s.weekday} @ {s.hour:02d}:{s.minute:02d}" for s in p.shutdown_times) or "None"
            su = ", ".join(f"Day {s.weekday} @ {s.hour:02d}:{s.minute:02d}" for s in p.startup_times) or "None"
            embed.add_field(
                name=f"{emoji} {p.name}",
                value=f"Tags: {', '.join(p.environment_tags)}\n"
                     f"Shutdown: {sh}\n"
                     f"Startup: {su}\n"
                     f"Grace: {p.grace_period_minutes}m | Dry: {p.dry_run}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="shutdown_create", description="Create a shutdown policy")
    async def shutdown_create(self, interaction: discord.Interaction,
                               name: str, tags: str, shutdown_hours: str):
        tag_list = [t.strip() for t in tags.split(",")]
        hours = [int(h.strip()) for h in shutdown_hours.split(",")]
        policy = self.mgr.create_policy(name, tag_list, hours)
        embed = discord.Embed(title="Policy Created", color=discord.Color.green())
        embed.add_field(name="Name", value=policy.name, inline=True)
        embed.add_field(name="ID", value=policy.policy_id, inline=True)
        embed.add_field(name="Tags", value=", ".join(policy.environment_tags), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="shutdown_environments", description="List environments")
    async def shutdown_environments(self, interaction: discord.Interaction):
        envs = self.mgr.list_environments()
        embed = discord.Embed(title="Environments", color=discord.Color.blue())
        for e in envs:
            status_emoji = "🟢" if e.is_running else "🔴"
            override = f" (override until {e.override_until.strftime('%H:%M')})" if e.override_until else ""
            embed.add_field(
                name=f"{status_emoji} {e.name}{override}",
                value=f"Tags: {', '.join(e.tags)}\n"
                     f"Containers: {e.resources['containers']} | "
                     f"Cost: ${e.resources['cost_per_hour']}/h\n"
                     f"Last: {e.last_action or 'none'}",
                inline=True
            )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="shutdown_override", description="Override shutdown for env")
    async def shutdown_override(self, interaction: discord.Interaction,
                                 env_id: str, hours: int = 4):
        if self.mgr.set_override(env_id, hours):
            await interaction.response.send_message(f"Override set for {env_id} for {hours}h")
        else:
            await interaction.response.send_message("Environment not found.", ephemeral=True)

    @discord.app_commands.command(name="shutdown_savings", description="Show shutdown savings")
    async def shutdown_savings(self, interaction: discord.Interaction):
        savings = self.mgr.get_savings()
        embed = discord.Embed(title="Shutdown Savings", color=discord.Color.green())
        for k, v in savings.items():
            embed.add_field(name=k.replace("_", " ").title(),
                           value=f"${v}" if "savings" in k or "rate" in k else str(v),
                           inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AutoShutdownCog(bot))
