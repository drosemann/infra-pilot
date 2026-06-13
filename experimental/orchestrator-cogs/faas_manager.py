import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging
import json
import os
import asyncio
from typing import Optional

from config import config
from integration import get_db_connection
from vps_manager import VPSManager

DATA_FILE = "data/faas_functions.json"


class FaaSManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.functions = {}
        self.load_functions()
        self.auto_scale_loop.start()

    def cog_unload(self):
        self.auto_scale_loop.cancel()

    def load_functions(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE) as f:
                    self.functions = json.load(f)
        except Exception as e:
            logging.error(f"Error loading FaaS functions: {e}")
            self.functions = {}

    def save_functions(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.functions, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving FaaS functions: {e}")

    def _record_function_db(self, name: str, repo: str, status: str):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO faas_functions (name, repo, status) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = NOW()",
                (name, repo, status),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error recording FaaS function to DB: {e}")

    @tasks.loop(minutes=5)
    async def auto_scale_loop(self):
        for name, info in self.functions.items():
            if info.get("status") != "active":
                continue
            try:
                invocation_count = info.get("invocations_24h", 0)
                replicas = info.get("replicas", 1)
                if invocation_count > 1000 and replicas < 5:
                    info["replicas"] = replicas + 1
                    logging.info(f"Scaled up {name} to {info['replicas']} replicas")
                elif invocation_count < 100 and replicas > 1:
                    info["replicas"] = max(1, replicas - 1)
                    logging.info(f"Scaled down {name} to {info['replicas']} replicas")
                info["invocations_24h"] = 0
            except Exception as e:
                logging.error(f"Auto-scale error for {name}: {e}")
        self.save_functions()

    @app_commands.command(name="faas", description="Serverless function management")
    @app_commands.describe(
        action="deploy/list/invoke/logs/delete",
        name="Function name",
        repo="Git repository URL (for deploy)",
    )
    async def faas(
        self,
        interaction: discord.Interaction,
        action: str,
        name: Optional[str] = None,
        repo: Optional[str] = None,
    ):
        await interaction.response.defer()
        actions = {
            "deploy": self._deploy_function,
            "list": self._list_functions,
            "invoke": self._invoke_function,
            "logs": self._function_logs,
            "delete": self._delete_function,
        }
        handler = actions.get(action)
        if not handler:
            embed = discord.Embed(description=f"Unknown action: {action}. Use deploy/list/invoke/logs/delete", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        await handler(interaction, name, repo)

    async def _deploy_function(self, interaction: discord.Interaction, name: Optional[str], repo: Optional[str]):
        if not name or not repo:
            embed = discord.Embed(description="Function name and repo URL are required", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        if name in self.functions:
            embed = discord.Embed(description=f"Function '{name}' already exists", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return

        try:
            container = self.vps_manager.client.containers.run(
                image="python:3.11-slim",
                detach=True,
                name=f"faas-{name}",
                command="tail -f /dev/null",
                restart_policy={"Name": "unless-stopped"},
            )
            self.functions[name] = {
                "name": name,
                "repo": repo,
                "status": "active",
                "container_id": container.id,
                "replicas": 1,
                "invocations_24h": 0,
                "total_invocations": 0,
                "billing_balance": 0.0,
                "deployed_at": datetime.now().isoformat(),
            }
            self.save_functions()
            self._record_function_db(name, repo, "active")
            embed = discord.Embed(description=f"Function '{name}' deployed", color=discord.Color.green())
            embed.add_field(name="Repo", value=repo)
            embed.add_field(name="Container ID", value=container.id[:12])
            embed.add_field(name="Replicas", value="1")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Deploy failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _list_functions(self, interaction: discord.Interaction, name: Optional[str], repo: Optional[str]):
        if not self.functions:
            embed = discord.Embed(description="No functions deployed", color=0xFFFF00)
            await interaction.followup.send(embed=embed)
            return
        embed = discord.Embed(title="FaaS Functions", color=discord.Color.blue(), timestamp=datetime.now())
        for fname, info in self.functions.items():
            status_emoji = "🟢" if info.get("status") == "active" else "🔴"
            embed.add_field(
                name=fname,
                value=(
                    f"Status: {status_emoji} {info.get('status', 'unknown')}\n"
                    f"Replicas: {info.get('replicas', 1)}\n"
                    f"Invocations: {info.get('total_invocations', 0)}\n"
                    f"Billing: ${info.get('billing_balance', 0):.4f}\n"
                    f"Deployed: {info.get('deployed_at', 'N/A')[:19]}"
                ),
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    async def _invoke_function(self, interaction: discord.Interaction, name: Optional[str], repo: Optional[str]):
        if not name or name not in self.functions:
            embed = discord.Embed(description="Function not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        info = self.functions[name]
        cost_per_invocation = 0.0001
        try:
            container = self.vps_manager.client.containers.get(info.get("container_id", ""))
            exit_code, output = container.exec_run("python -c 'print(\"ok\")'")
            info["total_invocations"] = info.get("total_invocations", 0) + 1
            info["invocations_24h"] = info.get("invocations_24h", 0) + 1
            info["billing_balance"] = info.get("billing_balance", 0) + cost_per_invocation
            self.save_functions()
            embed = discord.Embed(description=f"Function '{name}' invoked", color=discord.Color.green())
            embed.add_field(name="Output", value=output.decode()[:500] if exit_code == 0 else "Error", inline=False)
            embed.add_field(name="Cost", value=f"${cost_per_invocation:.4f}")
            embed.add_field(name="Total", value=f"${info['billing_balance']:.4f}")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Invocation failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _function_logs(self, interaction: discord.Interaction, name: Optional[str], repo: Optional[str]):
        if not name or name not in self.functions:
            embed = discord.Embed(description="Function not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        info = self.functions[name]
        try:
            container = self.vps_manager.client.containers.get(info.get("container_id", ""))
            logs = container.logs(tail=50).decode()
            embed = discord.Embed(title=f"Logs: {name}", color=discord.Color.blue(), timestamp=datetime.now())
            embed.description = f"```\n{logs[:1900]}\n```"
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Logs failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _delete_function(self, interaction: discord.Interaction, name: Optional[str], repo: Optional[str]):
        if not name or name not in self.functions:
            embed = discord.Embed(description="Function not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        try:
            info = self.functions[name]
            if info.get("container_id"):
                container = self.vps_manager.client.containers.get(info["container_id"])
                container.stop()
                container.remove()
            del self.functions[name]
            self.save_functions()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM faas_functions WHERE name = %s", (name,))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                pass
            embed = discord.Embed(description=f"Function '{name}' deleted", color=discord.Color.green())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Delete failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(FaaSManager(bot))
