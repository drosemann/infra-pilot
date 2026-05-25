import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import subprocess
import random
import os
import requests
from datetime import datetime, timedelta
import docker

from config import config
from vps_manager import VPSManager


class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.docker_client = docker.from_env()
        self.user_credits = {}
        self.vps_renewals = {}

    def _is_whitelisted(self, user_id: str) -> bool:
        return user_id in config.WHITELIST_IDS

    async def _capture_ssh_session_line(self, process):
        while True:
            output = await process.stdout.readline()
            if not output:
                break
            output = output.decode("utf-8").strip()
            if "ssh session:" in output:
                return output.split("ssh session:")[1].strip()
        return None

    async def _capture_output(self, process, keyword: str):
        while True:
            output = await process.stdout.readline()
            if not output:
                break
            output = output.decode("utf-8").strip()
            if keyword in output:
                return output
        return None

    @app_commands.command(name="earncredit", description="Earn credits by shortening a URL")
    async def earn_credit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        api_url = f"https://cutt.ly/api/api.php?key={config.CUTTLY_API_KEY}&short=https://cuty.io/e58WUzLMmE3S"
        try:
            response = requests.get(api_url, timeout=5).json()
            if response.get("url", {}).get("status") == 7:
                shortened_url = response["url"]["shortLink"]
                self.user_credits[user_id] = self.user_credits.get(user_id, 0) + 1
                await interaction.response.send_message(
                    f"Success! Shortened URL: {shortened_url}. You earned 1 credit!"
                )
            else:
                error = response.get("url", {}).get("title", "Failed to generate URL")
                await interaction.response.send_message(error)
        except Exception as e:
            await interaction.response.send_message("Failed to earn credit. Please try again.")

    @app_commands.command(name="bal", description="Check your credit balance")
    async def check_balance(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        credits = self.user_credits.get(user_id, 0)
        await interaction.response.send_message(f"You have {credits} credits.")

    @app_commands.command(name="node", description="Display node status")
    async def node_status(self, interaction: discord.Interaction):
        try:
            containers = self.docker_client.containers.list(all=True)
            container_status = "\n".join(
                [f"{c.name} - {c.status}" for c in containers]
            ) or "No containers."

            embed = discord.Embed(title="VPS Node Status", color=0x00FF00)
            embed.add_field(name="Containers", value=container_status, inline=False)
            embed.add_field(
                name="Total Containers",
                value=str(len(containers)),
                inline=True,
            )
            embed.add_field(
                name="Running",
                value=str(sum(1 for c in containers if c.status == "running")),
                inline=True,
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            )

    @app_commands.command(name="renew", description="Renew a VPS for 8 days (costs 2 credits)")
    @app_commands.describe(vps_id="ID of the VPS to renew")
    async def renew_vps(self, interaction: discord.Interaction, vps_id: str):
        user_id = str(interaction.user.id)
        credits = self.user_credits.get(user_id, 0)

        if credits < 2:
            await interaction.response.send_message(
                embed=discord.Embed(description="You need 2 credits to renew.", color=0xFF0000)
            )
            return

        container_id = self.vps_manager.get_container_id_from_database(user_id, vps_id)
        if not container_id:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"VPS {vps_id} not found.", color=0xFF0000)
            )
            return

        self.user_credits[user_id] -= 2
        renewal_date = datetime.now() + timedelta(days=8)
        self.vps_renewals[vps_id] = renewal_date

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"VPS renewed for 8 days until {renewal_date.strftime('%Y-%m-%d')}. Remaining: {self.user_credits[user_id]} credits",
                color=0x00FF00,
            )
        )

    @app_commands.command(name="deploy", description="Deploy a new Ubuntu 22.04 VPS")
    async def deploy_ubuntu(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Creating instance. This may take a few seconds...",
                color=0x00FF00,
            )
        )

        user_id = str(interaction.user.id)
        if self.vps_manager.count_user_servers(user_id) >= config.SERVER_LIMIT:
            await interaction.followup.send(
                embed=discord.Embed(description="Instance limit reached.", color=0xFF0000)
            )
            return

        try:
            container_id = subprocess.check_output(
                ["docker", "run", "-itd", "--privileged", "--hostname", "vps",
                 "--cap-add=ALL", config.DEFAULT_SSH_IMAGE]
            ).strip().decode("utf-8")

            exec_cmd = await asyncio.create_subprocess_exec(
                "docker", "exec", container_id, "tmate", "-F",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            ssh_session = await self._capture_ssh_session_line(exec_cmd)
            if ssh_session:
                self.vps_manager.add_to_database(user_id, container_id, ssh_session)
                try:
                    await interaction.user.send(
                        embed=discord.Embed(
                            description=f"Instance created!\nSSH: ```{ssh_session}```\nOS: Ubuntu 22.04",
                            color=0x00FF00,
                        )
                    )
                except Exception:
                    pass
                await interaction.followup.send(
                    embed=discord.Embed(description="Instance created. Check your DMs for SSH details.", color=0x00FF00)
                )
            else:
                subprocess.run(["docker", "kill", container_id], check=False)
                subprocess.run(["docker", "rm", container_id], check=False)
                await interaction.followup.send(
                    embed=discord.Embed(description="Creation failed. Please try again.", color=0xFF0000)
                )
        except subprocess.CalledProcessError as e:
            await interaction.followup.send(
                embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            )

    async def _execute_server_action(self, interaction: discord.Interaction, container_name: str, action: str):
        user_id = str(interaction.user.id)
        container_id = self.vps_manager.get_container_id_from_database(user_id, container_name)

        if not container_id:
            await interaction.response.send_message(
                embed=discord.Embed(description="Instance not found.", color=0xFF0000)
            )
            return

        try:
            subprocess.run(["docker", action, container_id], check=True)

            if action in ("start", "restart"):
                exec_cmd = await asyncio.create_subprocess_exec(
                    "docker", "exec", container_id, "tmate", "-F",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                ssh_session = await self._capture_ssh_session_line(exec_cmd)
                if ssh_session:
                    try:
                        await interaction.user.send(
                            embed=discord.Embed(
                                description=f"Instance {action}ed\nSSH: ```{ssh_session}```",
                                color=0x00FF00,
                            )
                        )
                    except Exception:
                        pass

            await interaction.response.send_message(
                embed=discord.Embed(description=f"Instance {action}ed successfully.", color=0x00FF00)
            )
        except subprocess.CalledProcessError as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            )

    @app_commands.command(name="start", description="Start your VPS")
    @app_commands.describe(container_name="Container name or ID")
    async def start_server(self, interaction: discord.Interaction, container_name: str):
        await self._execute_server_action(interaction, container_name, "start")

    @app_commands.command(name="stop", description="Stop your VPS")
    @app_commands.describe(container_name="Container name or ID")
    async def stop_server(self, interaction: discord.Interaction, container_name: str):
        await self._execute_server_action(interaction, container_name, "stop")

    @app_commands.command(name="restart", description="Restart your VPS")
    @app_commands.describe(container_name="Container name or ID")
    async def restart_server(self, interaction: discord.Interaction, container_name: str):
        await self._execute_server_action(interaction, container_name, "restart")

    @app_commands.command(name="regen-ssh", description="Regenerate SSH credentials")
    @app_commands.describe(container_name="Container name or ID")
    async def regen_ssh(self, interaction: discord.Interaction, container_name: str):
        user_id = str(interaction.user.id)
        container_id = self.vps_manager.get_container_id_from_database(user_id, container_name)

        if not container_id:
            await interaction.response.send_message(
                embed=discord.Embed(description="Instance not found.", color=0xFF0000)
            )
            return

        try:
            exec_cmd = await asyncio.create_subprocess_exec(
                "docker", "exec", container_id, "tmate", "-F",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            ssh_session = await self._capture_ssh_session_line(exec_cmd)
            if ssh_session:
                try:
                    await interaction.user.send(
                        embed=discord.Embed(description=f"New SSH: ```{ssh_session}```", color=0x00FF00)
                    )
                except Exception:
                    pass
                await interaction.response.send_message(
                    embed=discord.Embed(description="SSH regenerated. Check your DMs.", color=0x00FF00)
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(description="Failed to generate SSH.", color=0xFF0000)
                )
        except subprocess.CalledProcessError as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            )

    @app_commands.command(name="remove", description="Remove a VPS instance")
    @app_commands.describe(container_name="Container name or ID")
    async def remove_server(self, interaction: discord.Interaction, container_name: str):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        container_id = self.vps_manager.get_container_id_from_database(user_id, container_name)

        if not container_id:
            await interaction.followup.send(
                embed=discord.Embed(description="Instance not found.", color=0xFF0000)
            )
            return

        try:
            subprocess.run(["docker", "stop", container_id], check=False)
            subprocess.run(["docker", "rm", container_id], check=False)
            self.vps_manager.remove_from_database(container_id)
            await interaction.followup.send(
                embed=discord.Embed(description="Instance removed successfully.", color=0x00FF00)
            )
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            )

    @app_commands.command(name="list", description="List all your VPS instances")
    async def list_servers(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        servers = self.vps_manager.get_user_servers(user_id)

        if servers:
            embed = discord.Embed(title="Your Instances", color=0x00FF00)
            for container_id, container_name, _ in servers:
                stats = await self.vps_manager.get_vps_stats(container_id)
                status = stats["status"] if stats else "unknown"
                embed.add_field(
                    name=container_name,
                    value=f"Status: {status}\nID: `{container_id[:12]}`",
                    inline=False,
                )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(
                embed=discord.Embed(description="You don't have any active servers.", color=0xFF0000)
            )

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Pong!", description=f"Latency: {latency}ms", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show available commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Available Commands", color=0x00FF00)
        commands_data = [
            ("/deploy", "Deploy a new Ubuntu 22.04 VPS"),
            ("/createvps", "Create VPS with custom specs"),
            ("/listvps", "List your VPS instances"),
            ("/start <id>", "Start a VPS"),
            ("/stop <id>", "Stop a VPS"),
            ("/restart <id>", "Restart a VPS"),
            ("/remove <id>", "Remove a VPS"),
            ("/regen-ssh <id>", "Regenerate SSH"),
            ("/vpsstats <id>", "View VPS statistics"),
            ("/node", "Node status"),
            ("/bal", "Credit balance"),
            ("/renew <id>", "Renew VPS (2 credits)"),
            ("/earncredit", "Earn credits"),
            ("/vpscost", "Calculate VPS cost"),
            ("/purchasevps", "Purchase a VPS"),
        ]
        for cmd, desc in commands_data:
            embed.add_field(name=cmd, value=desc, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="port-add", description="Add port forwarding")
    @app_commands.describe(container_name="Container name", container_port="Internal port")
    async def port_add(self, interaction: discord.Interaction, container_name: str, container_port: int):
        if not self.vps_manager.is_safe_name(container_name):
            await interaction.response.send_message("Invalid container name.", ephemeral=True)
            return

        await interaction.response.send_message(
            embed=discord.Embed(description="Setting up port forwarding...", color=0x00FF00)
        )

        public_port = self.vps_manager.generate_random_port()
        try:
            await asyncio.create_subprocess_exec(
                "docker", "exec", container_name, "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-R", f"{public_port}:localhost:{container_port}",
                "serveo.net", "-N", "-f",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"Port forwarding: {config.PUBLIC_IP}:{public_port}",
                    color=0x00FF00,
                )
            )
        except Exception:
            await interaction.followup.send(
                embed=discord.Embed(description="Error setting up port forwarding.", color=0xFF0000)
            )

    @app_commands.command(name="port-http", description="Forward HTTP traffic")
    @app_commands.describe(container_name="Container name", container_port="Internal HTTP port")
    async def port_http(self, interaction: discord.Interaction, container_name: str, container_port: int):
        try:
            exec_cmd = await asyncio.create_subprocess_exec(
                "docker", "exec", container_name, "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-R", f"80:localhost:{container_port}",
                "serveo.net",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            url_line = await self._capture_output(exec_cmd, "Forwarding HTTP traffic from")
            if url_line:
                url = url_line.split()[-1]
                await interaction.response.send_message(
                    embed=discord.Embed(description=f"Website available at: {url}", color=0x00FF00)
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(description="Failed to get forwarding URL.", color=0xFF0000)
                )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
            )


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
