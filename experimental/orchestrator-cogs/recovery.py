import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import json
from typing import Optional
import logging
import asyncio

from config import config
from vps_manager import VPSManager


class Recovery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.recovery_check_loop.start()

    def cog_unload(self):
        self.recovery_check_loop.cancel()

    @tasks.loop(minutes=5)
    async def recovery_check_loop(self):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM recovery_executions WHERE status = 'pending' OR status = 'running'")
            executions = cursor.fetchall()
            cursor.close()
            conn.close()

            for exec_data in executions:
                await self._execute_playbook_step(exec_data)
        except Exception as e:
            logging.error(f"Recovery check error: {e}")

    async def _execute_playbook_step(self, exec_data: dict):
        conn = self.vps_manager._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM recovery_playbooks WHERE id = %s", (exec_data["playbook_id"],))
        playbook = cursor.fetchone()
        cursor.close()

        if not playbook:
            return

        steps = json.loads(playbook["steps"])
        current_step = exec_data["current_step"]

        if current_step >= len(steps):
            cursor = conn.cursor()
            cursor.execute("UPDATE recovery_executions SET status = 'completed', completed_at = NOW() WHERE id = %s", (exec_data["id"],))
            conn.commit()
            cursor.close()
            conn.close()
            return

        step = steps[current_step]
        container_id = exec_data["container_id"]

        try:
            action = step["action"]
            if action == "restart":
                await self.vps_manager.restart_vps(container_id)
            elif action == "stop":
                await self.vps_manager.stop_vps(container_id)
            elif action == "start":
                await self.vps_manager.start_vps(container_id)
            elif action == "wait":
                await asyncio.sleep(step.get("duration", 10))

            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recovery_executions SET current_step = %s WHERE id = %s",
                (current_step + 1, exec_data["id"]),
            )
            conn.commit()
            cursor.close()
        except Exception as e:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recovery_executions SET status = 'failed', error_message = %s WHERE id = %s",
                (str(e), exec_data["id"]),
            )
            conn.commit()
            cursor.close()

        conn.close()

    @app_commands.command(name="recoveryplaybookcreate", description="Create a recovery playbook")
    @app_commands.describe(name="Playbook name", steps_json="JSON array of steps e.g. [{\"action\":\"restart\"},{\"action\":\"wait\",\"duration\":10},{\"action\":\"start\"}]")
    async def playbook_create(self, interaction: discord.Interaction, name: str, steps_json: str):
        try:
            steps = json.loads(steps_json)
            if not isinstance(steps, list):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            await interaction.response.send_message(embed=discord.Embed(description="Invalid JSON. Must be an array of step objects.", color=0xFF0000))
            return

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO recovery_playbooks (name, steps) VALUES (%s, %s)",
                (name, json.dumps(steps)),
            )
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(embed=discord.Embed(description=f"Playbook '{name}' created with {len(steps)} steps.", color=0x00FF00))
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="recoveryplaybooklist", description="List recovery playbooks")
    async def playbook_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM recovery_playbooks")
            playbooks = cursor.fetchall()
            cursor.close()
            conn.close()

            if not playbooks:
                await interaction.response.send_message(embed=discord.Embed(description="No playbooks.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Recovery Playbooks", color=discord.Color.blue())
            for p in playbooks:
                steps = json.loads(p["steps"])
                step_desc = " -> ".join(s.get("action", s.get("wait", "?")) for s in steps)
                embed.add_field(name=p["name"], value=f"Steps: {step_desc}\nCreated: {p['created_at']}", inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="recoverystatus", description="Check recovery execution status")
    async def recovery_status(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM recovery_executions ORDER BY started_at DESC LIMIT 10")
            executions = cursor.fetchall()
            cursor.close()
            conn.close()

            if not executions:
                await interaction.response.send_message(embed=discord.Embed(description="No recovery executions.", color=0xFFFF00))
                return

            embed = discord.Embed(title="Recovery Status", color=discord.Color.blue())
            for e in executions:
                embed.add_field(
                    name=f"Execution #{e['id']}",
                    value=f"Container: {e['container_id'][:12]}\nStatus: {e['status']}\nStep: {e['current_step']}\nStarted: {e['started_at']}",
                    inline=False,
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="recoveryrun", description="Run a recovery playbook on a VPS")
    @app_commands.describe(playbook_name="Playbook name", vps_id="VPS ID")
    async def recovery_run(self, interaction: discord.Interaction, playbook_name: str, vps_id: str):
        await interaction.response.defer()

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM recovery_playbooks WHERE name = %s", (playbook_name,))
            playbook = cursor.fetchone()
            cursor.close()

            if not playbook:
                await interaction.followup.send(embed=discord.Embed(description="Playbook not found.", color=0xFF0000))
                return

            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO recovery_executions (playbook_id, container_id, status) VALUES (%s, %s, 'pending')",
                (playbook["id"], vps_id),
            )
            conn.commit()
            cursor.close()
            conn.close()

            await interaction.followup.send(embed=discord.Embed(description=f"Recovery started for {vps_id[:12]} using playbook '{playbook_name}'.", color=0x00FF00))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(Recovery(bot))
