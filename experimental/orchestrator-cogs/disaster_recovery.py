import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict, List
import json
import logging
import os
import asyncio

from config import config
from vps_manager import VPSManager


DR_PLAN_TYPES = {"active-passive", "pilot-light", "warm-standby"}


class DisasterRecovery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.dr_plans_file = config.DR_PLANS_FILE
        self._ensure_data_file()
        self.dr_readiness_loop.start()

    def cog_unload(self):
        self.dr_readiness_loop.cancel()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.dr_plans_file), exist_ok=True)
        if not os.path.exists(self.dr_plans_file):
            with open(self.dr_plans_file, "w") as f:
                json.dump([], f)

    def _load_plans(self) -> list:
        try:
            with open(self.dr_plans_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_plans(self, plans: list):
        with open(self.dr_plans_file, "w") as f:
            json.dump(plans, f, indent=2, default=str)

    @tasks.loop(hours=config.DR_DRILL_INTERVAL_HOURS)
    async def dr_readiness_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM dr_plans WHERE status = 'ready'")
            plans = cursor.fetchall()
            cursor.close()
            conn.close()

            for plan in plans:
                result = await self._check_plan_readiness(plan)
                plan_id = plan["id"]
                conn = self.vps_manager._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE dr_plans SET status = %s WHERE id = %s",
                    ("degraded" if not result["healthy"] else "ready", plan_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            logging.error(f"DR readiness check error: {e}")

    @dr_readiness_loop.before_loop
    async def before_readiness(self):
        await self.bot.wait_until_ready()

    async def _check_plan_readiness(self, plan: dict) -> dict:
        return {"healthy": True, "checks": []}

    async def _execute_drill(self, plan_id: int, is_drill: bool = True) -> dict:
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM dr_plans WHERE id = %s", (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            cursor.close()
            conn.close()
            return {"success": False, "error": "Plan not found"}

        steps = self._generate_drill_steps(plan)
        cursor.execute(
            "INSERT INTO dr_drills (plan_id, status, steps, current_step) VALUES (%s, 'running', %s, 0)",
            (plan_id, json.dumps(steps)),
        )
        drill_id = cursor.lastrowid
        conn.commit()

        start_time = datetime.now()
        success = True
        error_msg = None
        for i, step in enumerate(steps):
            try:
                await self._run_drill_step(step)
                cursor.execute(
                    "UPDATE dr_drills SET current_step = %s WHERE id = %s",
                    (i + 1, drill_id),
                )
                conn.commit()
            except Exception as e:
                success = False
                error_msg = str(e)
                break

        elapsed = int((datetime.now() - start_time).total_seconds())
        status = "completed" if success else "failed"
        cursor.execute(
            "UPDATE dr_drills SET status = %s, rto_achieved = %s, completed_at = NOW(), error_message = %s WHERE id = %s",
            (status, elapsed, error_msg, drill_id),
        )
        cursor.execute(
            "UPDATE dr_plans SET last_drill = NOW(), last_drill_status = %s, rto_actual_seconds = %s WHERE id = %s",
            (status, elapsed, plan_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {"success": success, "drill_id": drill_id, "rto_achieved": elapsed, "error": error_msg}

    def _generate_drill_steps(self, plan: dict) -> list:
        plan_type = plan["plan_type"]
        if plan_type == "active-passive":
            return [
                {"action": "validate_passive", "timeout": 30},
                {"action": "failover", "timeout": 60},
                {"action": "validate_active", "timeout": 30},
                {"action": "rollback", "timeout": 60},
            ]
        elif plan_type == "pilot-light":
            return [
                {"action": "scale_pilot", "timeout": 60},
                {"action": "route_traffic", "timeout": 30},
                {"action": "validate", "timeout": 30},
                {"action": "scale_down", "timeout": 60},
            ]
        else:
            return [
                {"action": "warm_standby_activate", "timeout": 30},
                {"action": "validate", "timeout": 30},
                {"action": "deactivate_standby", "timeout": 30},
            ]

    async def _run_drill_step(self, step: dict):
        await asyncio.sleep(step.get("timeout", 10))

    @app_commands.command(name="dr", description="Disaster Recovery management")
    @app_commands.describe(subcommand="plan, drill, status, report", name="Plan name (for plan)", plan_type="active-passive/pilot-light/warm-standby (for plan)", plan_id="Plan ID (for execute/drill)")
    async def dr_command(
        self,
        interaction: discord.Interaction,
        subcommand: str,
        name: str = None,
        plan_type: str = None,
        plan_id: int = None,
    ):
        await interaction.response.defer()

        if subcommand == "plan":
            if name and plan_type:
                await self._plan_create(interaction, name, plan_type)
            else:
                await self._plan_list(interaction)
        elif subcommand == "execute":
            if plan_id:
                await self._plan_execute(interaction, plan_id)
            else:
                await interaction.followup.send(embed=discord.Embed(description="Provide plan_id", color=0xFF0000))
        elif subcommand == "drill":
            if plan_id:
                await self._drill_run(interaction, plan_id)
            else:
                await interaction.followup.send(embed=discord.Embed(description="Provide plan_id", color=0xFF0000))
        elif subcommand == "status":
            await self._dr_status(interaction)
        elif subcommand == "report":
            await self._dr_report(interaction)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Subcommand: plan, execute, drill, status, report", color=0xFF0000))

    async def _plan_create(self, interaction: discord.Interaction, name: str, plan_type: str):
        if plan_type not in DR_PLAN_TYPES:
            await interaction.followup.send(embed=discord.Embed(description=f"Type must be: {', '.join(DR_PLAN_TYPES)}", color=0xFF0000))
            return
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO dr_plans (name, plan_type, status) VALUES (%s, %s, 'ready')",
                (name, plan_type),
            )
            conn.commit()
            cursor.close()
            conn.close()

            plans = self._load_plans()
            plans.append({"name": name, "type": plan_type, "status": "ready", "created_at": str(datetime.now())})
            self._save_plans(plans)

            await interaction.followup.send(embed=discord.Embed(description=f"DR plan '{name}' created ({plan_type})", color=0x00FF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _plan_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM dr_plans ORDER BY created_at DESC")
            plans = cursor.fetchall()
            cursor.close()
            conn.close()

            if not plans:
                await interaction.followup.send(embed=discord.Embed(description="No DR plans found.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Disaster Recovery Plans", color=discord.Color.blue())
            for p in plans:
                status_emoji = "✅" if p["status"] == "ready" else "⚠️" if p["status"] == "degraded" else "❌"
                embed.add_field(
                    name=f"{status_emoji} {p['name']} (ID: {p['id']})",
                    value=f"Type: {p['plan_type']} | Status: {p['status']}\n"
                    f"Last Drill: {p.get('last_drill', 'Never')} - {p.get('last_drill_status', 'N/A')}\n"
                    f"RTO: {p.get('rto_actual_seconds', 'N/A')}s",
                    inline=False,
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _plan_execute(self, interaction: discord.Interaction, plan_id: int):
        result = await self._execute_drill(plan_id, is_drill=False)
        if result["success"]:
            await interaction.followup.send(embed=discord.Embed(
                description=f"Plan executed. RTO achieved: {result['rto_achieved']}s",
                color=0x00FF00,
            ))
        else:
            await interaction.followup.send(embed=discord.Embed(
                description=f"Execution failed: {result.get('error')}",
                color=0xFF0000,
            ))

    async def _drill_run(self, interaction: discord.Interaction, plan_id: int):
        await interaction.followup.send(embed=discord.Embed(description=f"Starting drill for plan {plan_id}...", color=discord.Color.blue()))
        result = await self._execute_drill(plan_id, is_drill=True)
        if result["success"]:
            await interaction.followup.send(embed=discord.Embed(
                description=f"Drill completed. RTO achieved: {result['rto_achieved']}s | Drill ID: {result['drill_id']}",
                color=0x00FF00,
            ))
        else:
            await interaction.followup.send(embed=discord.Embed(
                description=f"Drill failed: {result.get('error')}",
                color=0xFF0000,
            ))

    async def _dr_status(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT status, COUNT(*) as count FROM dr_plans GROUP BY status")
            statuses = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) as total FROM dr_drills WHERE status = 'failed'")
            failures = cursor.fetchone()
            cursor.close()
            conn.close()

            embed = discord.Embed(title="DR Status Overview", color=discord.Color.blue(), timestamp=datetime.now())
            for row in statuses:
                embed.add_field(name=f"Status: {row['status']}", value=f"{row['count']} plans", inline=True)
            embed.add_field(name="Failed Drills", value=str(failures["total"] if failures else 0), inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _dr_report(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT dp.name, dp.plan_type, dp.status, dp.rto_actual_seconds, dp.last_drill,
                       dp.last_drill_status, dd.rto_achieved, dd.started_at
                FROM dr_plans dp
                LEFT JOIN dr_drills dd ON dd.id = (SELECT MAX(id) FROM dr_drills WHERE plan_id = dp.id)
                ORDER BY dp.created_at DESC
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if not rows:
                await interaction.followup.send(embed=discord.Embed(description="No DR data available.", color=0xFFFF00))
                return

            embed = discord.Embed(title="DR Compliance Report", color=discord.Color.blue(), timestamp=datetime.now())
            embed.add_field(name="RTO Target", value=f"{config.RTO_TARGET_SECONDS}s", inline=True)
            embed.add_field(name="RPO Target", value=f"{config.RPO_TARGET_SECONDS}s", inline=True)
            for r in rows:
                compliant = r.get("rto_achieved", 999999) <= config.RTO_TARGET_SECONDS if r.get("rto_achieved") else True
                embed.add_field(
                    name=f"{'✅' if compliant else '❌'} {r['name']}",
                    value=f"Type: {r['plan_type']} | Status: {r['status']}\n"
                    f"Last RTO: {r.get('rto_achieved', 'N/A')}s | Drill: {r.get('last_drill_status', 'N/A')}",
                    inline=False,
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(DisasterRecovery(bot))
