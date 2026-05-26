import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict, List
import logging
import json

from config import config
from vps_manager import VPSManager
from croniter import croniter


class TaskScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.task_scheduler_loop.start()

    def cog_unload(self):
        self.task_scheduler_loop.cancel()

    @tasks.loop(seconds=30)
    async def task_scheduler_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM scheduled_tasks WHERE enabled = TRUE AND (next_run_at IS NULL OR next_run_at <= NOW())"
            )
            tasks = cursor.fetchall()
            cursor.close()
            conn.close()

            for task in tasks:
                await self.execute_task(task)
        except Exception as e:
            logging.error(f"Task scheduler loop error: {e}")

    @task_scheduler_loop.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    async def execute_task(self, task: Dict):
        task_id = task["id"]
        task_type = task["task_type"]
        status = "success"
        error = None

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scheduled_tasks SET last_run_at = NOW(), last_run_status = 'running' WHERE id = %s",
                (task_id,),
            )
            conn.commit()
            cursor.close()
            conn.close()

            if task_type == "restart":
                container_id = task.get("target_container_id")
                if container_id:
                    await self.vps_manager.restart_container(container_id)

            elif task_type == "command":
                container_id = task.get("target_container_id")
                command = task.get("command")
                if container_id and command:
                    result = await self.vps_manager.execute_command(container_id, command)
                    if not result.get("success"):
                        status = "failed"
                        error = result.get("error")

            elif task_type == "backup":
                container_id = task.get("target_container_id")
                if container_id:
                    await self.vps_manager.create_backup(container_id, "scheduled")

            elif task_type == "custom":
                command = task.get("command")
                if command:
                    import subprocess
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    if result.returncode != 0:
                        status = "failed"
                        error = result.stderr

        except Exception as e:
            status = "failed"
            error = str(e)
            logging.error(f"Task {task_id} execution error: {e}")

        try:
            next_run = None
            try:
                cron = croniter(task["cron_expression"], datetime.now())
                next_run = cron.get_next(datetime)
            except:
                pass

            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scheduled_tasks SET last_run_at = NOW(), last_run_status = %s, next_run_at = %s WHERE id = %s",
                (status, next_run, task_id),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error updating task {task_id} status: {e}")

    @app_commands.command(name="cron", description="Manage scheduled tasks")
    @app_commands.describe(
        action="create, list, delete, toggle",
        name="Task name (for create)",
        task_type="restart, command, backup, custom (for create)",
        target="Container ID (for create)",
        cron_expr="Cron expression (for create)",
        command="Shell command (for command/custom type)",
    )
    async def cron_manager(
        self,
        interaction: discord.Interaction,
        action: str,
        name: str = None,
        task_type: str = None,
        target: str = None,
        cron_expr: str = None,
        command: str = None,
    ):
        await interaction.response.defer()

        if action == "create":
            if not all([name, task_type, cron_expr]):
                await interaction.followup.send(
                    embed=discord.Embed(description="Missing required fields: name, task_type, cron_expr", color=0xFF0000)
                )
                return

            try:
                if not croniter.is_valid(cron_expr):
                    await interaction.followup.send(
                        embed=discord.Embed(description="Invalid cron expression", color=0xFF0000)
                    )
                    return
            except:
                await interaction.followup.send(
                    embed=discord.Embed(description="Invalid cron expression", color=0xFF0000)
                )
                return

            try:
                conn = self.vps_manager._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO scheduled_tasks (name, task_type, target_container_id, cron_expression, command, created_by)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (name, task_type, target, cron_expr, command, str(interaction.user.id)),
                )
                conn.commit()
                cursor.close()
                conn.close()
                await interaction.followup.send(
                    embed=discord.Embed(description=f"Scheduled task '{name}' created", color=0x00FF00)
                )
            except Exception as e:
                await interaction.followup.send(
                    embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
                )

        elif action == "list":
            try:
                conn = self.vps_manager._get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM scheduled_tasks ORDER BY created_at DESC")
                tasks = cursor.fetchall()
                cursor.close()
                conn.close()

                if not tasks:
                    await interaction.followup.send(
                        embed=discord.Embed(description="No scheduled tasks configured.", color=0xFFFF00)
                    )
                    return

                embed = discord.Embed(title="Scheduled Tasks", color=discord.Color.blue())
                for t in tasks:
                    status_emoji = "✅" if t["enabled"] else "⏸️"
                    last_status = t.get("last_run_status", "never")
                    embed.add_field(
                        name=f"{status_emoji} {t['name']}",
                        value=f"Type: {t['task_type']} | Cron: `{t['cron_expression']}`\n"
                        f"Container: {t.get('target_container_id', 'N/A')[:16]}\n"
                        f"Last: {last_status} | ID: `{t['id']}`",
                        inline=False,
                    )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(
                    embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
                )

        elif action == "delete":
            if not name and not target:
                await interaction.followup.send(
                    embed=discord.Embed(description="Provide task name or ID to delete", color=0xFF0000)
                )
                return
            try:
                conn = self.vps_manager._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM scheduled_tasks WHERE name = %s OR id = %s", (name, name))
                deleted = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                if deleted:
                    await interaction.followup.send(
                        embed=discord.Embed(description=f"Deleted {deleted} task(s)", color=0x00FF00)
                    )
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(description="Task not found", color=0xFFFF00)
                    )
            except Exception as e:
                await interaction.followup.send(
                    embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
                )

        elif action == "toggle":
            if not name and not target:
                await interaction.followup.send(
                    embed=discord.Embed(description="Provide task name or ID to toggle", color=0xFF0000)
                )
                return
            try:
                conn = self.vps_manager._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE scheduled_tasks SET enabled = NOT enabled WHERE name = %s OR id = %s",
                    (name, name),
                )
                conn.commit()
                cursor.close()
                conn.close()
                await interaction.followup.send(
                    embed=discord.Embed(description=f"Task '{name}' toggled", color=0x00FF00)
                )
            except Exception as e:
                await interaction.followup.send(
                    embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
                )

        else:
            await interaction.followup.send(
                embed=discord.Embed(description="Action must be: create, list, delete, toggle", color=0xFF0000)
            )


async def setup(bot):
    await bot.add_cog(TaskScheduler(bot))
