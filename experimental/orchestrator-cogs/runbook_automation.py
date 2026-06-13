import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict, List
import json
import logging
import os
import yaml
import asyncio

from config import config
from vps_manager import VPSManager


class RunbookAutomation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.runbooks_file = config.RUNBOOKS_FILE
        self._ensure_data_file()
        self.scheduled_runbook_loop.start()

    def cog_unload(self):
        self.scheduled_runbook_loop.cancel()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.runbooks_file), exist_ok=True)
        if not os.path.exists(self.runbooks_file):
            with open(self.runbooks_file, "w") as f:
                json.dump([], f)

    def _load_runbooks(self) -> list:
        try:
            with open(self.runbooks_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_runbooks(self, runbooks: list):
        with open(self.runbooks_file, "w") as f:
            json.dump(runbooks, f, indent=2, default=str)

    @tasks.loop(seconds=config.RUNBOOK_CHECK_INTERVAL_SECONDS)
    async def scheduled_runbook_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM runbooks WHERE enabled = 1 AND trigger_type = 'schedule'")
            runbooks = cursor.fetchall()
            cursor.close()
            conn.close()

            for rb in runbooks:
                await self._execute_runbook(rb, triggered_by="scheduler")
        except Exception as e:
            logging.error(f"Scheduled runbook loop error: {e}")

    @scheduled_runbook_loop.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    async def _execute_runbook(self, runbook: dict, triggered_by: str = "manual") -> dict:
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO runbook_executions (runbook_id, status, triggered_by, current_step) VALUES (%s, 'running', %s, 0)",
            (runbook["id"], triggered_by),
        )
        execution_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        steps = json.loads(runbook["steps"]) if isinstance(runbook["steps"], str) else runbook["steps"]
        gates = json.loads(runbook["gates"]) if isinstance(runbook.get("gates"), str) and runbook["gates"] else runbook.get("gates", [])
        rollback = json.loads(runbook["rollback"]) if isinstance(runbook.get("rollback"), str) and runbook["rollback"] else runbook.get("rollback", [])
        step_results = []
        success = True
        error_msg = None

        for i, step in enumerate(steps):
            try:
                gate = gates[i] if i < len(gates) else None
                if gate:
                    gate_passed = await self._check_gate(gate)
                    if not gate_passed:
                        raise Exception(f"Gate check failed at step {i + 1}: {gate.get('condition', 'unknown')}")

                result = await self._run_step(step)
                step_results.append({"step": i, "action": step.get("action"), "status": "passed", "result": str(result)})

                conn = self.vps_manager._get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE runbook_executions SET current_step = %s, step_results = %s WHERE id = %s",
                    (i + 1, json.dumps(step_results), execution_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                step_results.append({"step": i, "action": step.get("action"), "status": "failed", "error": str(e)})
                success = False
                error_msg = str(e)
                if rollback:
                    for rb_step in reversed(rollback):
                        try:
                            await self._run_step(rb_step)
                        except Exception as rb_e:
                            logging.error(f"Rollback step failed: {rb_e}")
                break

        status = "completed" if success else "failed"
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runbook_executions SET status = %s, step_results = %s, error_message = %s, completed_at = NOW() WHERE id = %s",
            (status, json.dumps(step_results), error_msg, execution_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {"success": success, "execution_id": execution_id, "error": error_msg}

    async def _check_gate(self, gate: dict) -> bool:
        await asyncio.sleep(0.5)
        return True

    async def _run_step(self, step: dict) -> dict:
        action = step.get("action", "")
        if action == "restart":
            container_id = step.get("container_id")
            if container_id:
                await self.vps_manager.restart_vps(container_id)
        elif action == "stop":
            container_id = step.get("container_id")
            if container_id:
                await self.vps_manager.stop_vps(container_id)
        elif action == "start":
            container_id = step.get("container_id")
            if container_id:
                await self.vps_manager.start_vps(container_id)
        elif action == "sleep":
            await asyncio.sleep(step.get("duration", 5))
        elif action == "command":
            exec_result = await self.vps_manager.execute_command(
                step.get("container_id"), step.get("command", "")
            )
            if not exec_result.get("success"):
                raise Exception(exec_result.get("error", "Command failed"))
        return {"status": "ok"}

    @app_commands.command(name="runbook", description="Runbook automation management")
    @app_commands.describe(
        subcommand="create, list, execute, show, delete",
        name="Runbook name (for create)",
        file="YAML file content as JSON string (for create)",
        runbook_id="Runbook ID (for execute/show/delete)",
    )
    async def runbook_command(
        self,
        interaction: discord.Interaction,
        subcommand: str,
        name: str = None,
        file: str = None,
        runbook_id: int = None,
    ):
        await interaction.response.defer()

        if subcommand == "create":
            if not name or not file:
                await interaction.followup.send(embed=discord.Embed(description="Provide name and YAML file content", color=0xFF0000))
                return
            await self._runbook_create(interaction, name, file)
        elif subcommand == "list":
            await self._runbook_list(interaction)
        elif subcommand == "execute":
            if not runbook_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide runbook_id", color=0xFF0000))
                return
            await self._runbook_execute(interaction, runbook_id)
        elif subcommand == "show":
            if not runbook_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide runbook_id", color=0xFF0000))
                return
            await self._runbook_show(interaction, runbook_id)
        elif subcommand == "delete":
            if not runbook_id:
                await interaction.followup.send(embed=discord.Embed(description="Provide runbook_id", color=0xFF0000))
                return
            await self._runbook_delete(interaction, runbook_id)
        else:
            await interaction.followup.send(embed=discord.Embed(description="Subcommand: create, list, execute, show, delete", color=0xFF0000))

    async def _runbook_create(self, interaction: discord.Interaction, name: str, file_content: str):
        try:
            data = yaml.safe_load(file_content)
            if not isinstance(data, dict) or "steps" not in data:
                await interaction.followup.send(embed=discord.Embed(description="YAML must contain 'steps' array", color=0xFF0000))
                return
        except yaml.YAMLError as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Invalid YAML: {str(e)}", color=0xFF0000))
            return

        steps = data.get("steps", [])
        gates = data.get("gates", [])
        rollback = data.get("rollback", [])
        trigger_type = data.get("trigger", {}).get("type", "manual")
        trigger_config = json.dumps(data.get("trigger", {}))

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO runbooks (name, description, steps, gates, rollback, trigger_type, trigger_config, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (name, data.get("description", ""), json.dumps(steps), json.dumps(gates), json.dumps(rollback), trigger_type, trigger_config, str(interaction.user.id)),
            )
            conn.commit()
            cursor.close()
            conn.close()

            runbooks = self._load_runbooks()
            runbooks.append({"name": name, "steps": len(steps), "trigger": trigger_type, "created_at": str(datetime.now())})
            self._save_runbooks(runbooks)

            await interaction.followup.send(embed=discord.Embed(description=f"Runbook '{name}' created with {len(steps)} step(s), trigger: {trigger_type}", color=0x00FF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _runbook_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM runbooks ORDER BY created_at DESC")
            runbooks = cursor.fetchall()
            cursor.close()
            conn.close()

            if not runbooks:
                await interaction.followup.send(embed=discord.Embed(description="No runbooks found.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Runbooks", color=discord.Color.blue())
            for rb in runbooks:
                status_emoji = "✅" if rb["enabled"] else "⏸️"
                steps_count = len(json.loads(rb["steps"])) if isinstance(rb["steps"], str) else len(rb["steps"])
                embed.add_field(
                    name=f"{status_emoji} {rb['name']} (ID: {rb['id']})",
                    value=f"Steps: {steps_count} | Trigger: {rb['trigger_type']}\n"
                    f"Created: {rb['created_at']}",
                    inline=False,
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    async def _runbook_execute(self, interaction: discord.Interaction, runbook_id: int):
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM runbooks WHERE id = %s", (runbook_id,))
        runbook = cursor.fetchone()
        cursor.close()
        conn.close()

        if not runbook:
            await interaction.followup.send(embed=discord.Embed(description="Runbook not found.", color=0xFF0000))
            return

        await interaction.followup.send(embed=discord.Embed(description=f"Executing runbook '{runbook['name']}'...", color=discord.Color.blue()))
        result = await self._execute_runbook(runbook, triggered_by=str(interaction.user.id))
        if result["success"]:
            await interaction.followup.send(embed=discord.Embed(description=f"Runbook completed (ID: {result['execution_id']})", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Runbook failed: {result.get('error')}", color=0xFF0000))

    async def _runbook_show(self, interaction: discord.Interaction, runbook_id: int):
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM runbooks WHERE id = %s", (runbook_id,))
        runbook = cursor.fetchone()
        cursor.close()
        conn.close()

        if not runbook:
            await interaction.followup.send(embed=discord.Embed(description="Runbook not found.", color=0xFF0000))
            return

        steps = json.loads(runbook["steps"]) if isinstance(runbook["steps"], str) else runbook["steps"]
        steps_text = "\n".join(f"{i + 1}. {s.get('action', '?')}" for i, s in enumerate(steps[:10]))
        if len(steps) > 10:
            steps_text += f"\n... and {len(steps) - 10} more"

        embed = discord.Embed(title=f"Runbook: {runbook['name']}", color=discord.Color.blue())
        embed.add_field(name="Description", value=runbook.get("description", "N/A"), inline=False)
        embed.add_field(name="Trigger", value=runbook["trigger_type"], inline=True)
        embed.add_field(name="Steps", value=f"{len(steps)} total\n{steps_text}", inline=False)
        await interaction.followup.send(embed=embed)

    async def _runbook_delete(self, interaction: discord.Interaction, runbook_id: int):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM runbooks WHERE id = %s", (runbook_id,))
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            if deleted:
                await interaction.followup.send(embed=discord.Embed(description=f"Runbook {runbook_id} deleted.", color=0x00FF00))
            else:
                await interaction.followup.send(embed=discord.Embed(description="Runbook not found.", color=0xFFFF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(RunbookAutomation(bot))
