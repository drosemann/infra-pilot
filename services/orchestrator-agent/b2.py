import logging
import subprocess
import sys
import os
import re
import time
import concurrent.futures
import random
import asyncio
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands, tasks
from discord import app_commands
import docker
import requests

# =============================================================================
# Configuration
# =============================================================================

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DATABASE_FILE = os.getenv("DATABASE_FILE", "database.db")
CUTTLY_API_KEY = os.getenv("CUTTLY_API_KEY", "")
PUBLIC_IP = os.getenv("PUBLIC_IP", "")
WHITELIST_IDS = set(filter(None, os.getenv("WHITELIST_IDS", "").split(",")))

# Bot configuration
RAM_LIMIT = "1g"
SERVER_LIMIT = 1
DOCKER_IMAGE = "ubuntu-22.04-with-tmate"
SAFE_CONTAINER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")
DEFAULT_SHORTENING_URL = "https://cuty.io/e58WUzLMmE3S"

# Bot setup
intents = discord.Intents.default()
intents.messages = False
intents.message_content = False
bot = commands.Bot(command_prefix="/", intents=intents)
client = docker.from_env()

# State management
user_credits: Dict[str, int] = {}
vps_renewals: Dict[str, datetime] = {}
database_lock = Lock()

logger = logging.getLogger(__name__)

# =============================================================================
# Database Management
# =============================================================================

def init_database() -> None:
    """Initialize the database if it doesn't exist."""
    with database_lock:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                container_id TEXT UNIQUE NOT NULL,
                container_name TEXT NOT NULL,
                ssh_command TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()


def add_to_database(user_id: str, container_id: str, container_name: str, ssh_command: str) -> None:
    """Store server information in database."""
    with database_lock:
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO servers (user_id, container_id, container_name, ssh_command) VALUES (?, ?, ?, ?)",
                (user_id, container_id, container_name, ssh_command),
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            logger.warning(f"Container {container_id} already exists in database")


def remove_from_database(container_id: str) -> None:
    """Remove server information from database."""
    with database_lock:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM servers WHERE container_id = ?", (container_id,))
        conn.commit()
        conn.close()


def get_user_servers(user_id: str) -> List[str]:
    """Retrieve all servers for a user."""
    with database_lock:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT container_id, container_name, ssh_command FROM servers WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
    return rows


def count_user_servers(user_id: str) -> int:
    """Count servers owned by a user."""
    return len(get_user_servers(user_id))


def get_container_id_from_database(user_id: str, container_name: str) -> Optional[str]:
    """Find container ID by name for a user."""
    servers = get_user_servers(user_id)
    for container_id, name, _ in servers:
        if name == container_name or container_id == container_name:
            return container_id
    return None


def get_ssh_command_from_database(container_id: str) -> Optional[str]:
    """Retrieve SSH command for a container."""
    with database_lock:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT ssh_command FROM servers WHERE container_id = ?", (container_id,))
        row = cursor.fetchone()
        conn.close()
    return row[0] if row else None

# =============================================================================
# Utility Functions
# =============================================================================

def is_safe_container_name(name: str) -> bool:
    """Validate container name against security regex."""
    return bool(SAFE_CONTAINER_RE.fullmatch(name))


def generate_random_port() -> int:
    """Generate random port in valid range."""
    return random.randint(1025, 65535)


async def capture_ssh_session_line(process) -> Optional[str]:
    """Extract SSH session line from process output."""
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode("utf-8").strip()
        if "ssh session:" in output:
            return output.split("ssh session:")[1].strip()
    return None


def get_node_status() -> Dict[str, Any]:
    """Get current node and container status."""
    try:
        containers = client.containers.list(all=True)
        container_status = "\n".join(
            [f"{c.name} - {c.status}" for c in containers]
        ) or "No containers running."

        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        
        mem_total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1)) / 1024
        mem_free = int(re.search(r"MemFree:\s+(\d+)", meminfo).group(1)) / 1024
        mem_available = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1)) / 1024

        memory_used = mem_total - mem_available
        memory_percentage = (memory_used / mem_total) * 100 if mem_total else 0

        return {
            "containers": container_status,
            "memory_total": mem_total,
            "memory_used": memory_used,
            "memory_percentage": memory_percentage,
        }
    except Exception as e:
        logger.error(f"Failed to get node status: {e}")
        return {}

# =============================================================================
# Discord Bot Events
# =============================================================================

@bot.event
async def on_ready():
    """Bot ready event."""
    init_database()
    logger.info(f"Bot ready. Logged in as {bot.user}")
    await bot.tree.sync()

# =============================================================================
# Credit System Commands
# =============================================================================

@bot.tree.command(name="earncredit", description="Generate a shortened URL to earn credits.")
async def earn_credit(interaction: discord.Interaction):
    """Earn credits by creating a shortened URL."""
    user_id = str(interaction.user.id)
    
    try:
        api_url = f"https://cutt.ly/api/api.php?key={CUTTLY_API_KEY}&short={DEFAULT_SHORTENING_URL}"
        response = requests.get(api_url, timeout=5).json()
        
        if response.get("url", {}).get("status") == 7:
            shortened_url = response["url"]["shortLink"]
            user_credits[user_id] = user_credits.get(user_id, 0) + 1
            
            await interaction.response.send_message(
                f"Success! Shortened URL: {shortened_url}. You earned 1 credit!"
            )
        else:
            error = response.get("url", {}).get("title", "Failed to generate URL")
            await interaction.response.send_message(error)
    except Exception as e:
        logger.error(f"Error earning credit: {e}")
        await interaction.response.send_message("Failed to earn credit. Please try again.")


@bot.tree.command(name="bal", description="Check your credit balance.")
async def check_balance(interaction: discord.Interaction):
    """Display user's credit balance."""
    user_id = str(interaction.user.id)
    credits = user_credits.get(user_id, 0)
    await interaction.response.send_message(f"You have {credits} credits.")

# =============================================================================
# Node Status Commands
# =============================================================================

@bot.tree.command(name="node", description="Display node status.")
async def node_status(interaction: discord.Interaction):
    """Show node and container status."""
    info = get_node_status()
    
    if not info:
        await interaction.response.send_message(
            embed=discord.Embed(description="Error fetching node status", color=0xFF0000)
        )
        return
    
    embed = discord.Embed(title="VPS Node Status", color=0x00FF00)
    embed.add_field(name="Containers", value=info["containers"], inline=False)
    embed.add_field(
        name="Memory Usage",
        value=f"{info['memory_used']:.2f} / {info['memory_total']:.2f} MB ({info['memory_percentage']:.2f}%)",
        inline=False,
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="renew", description="Renew a VPS for 8 days (costs 2 credits).")
@app_commands.describe(vps_id="ID of the VPS to renew")
async def renew_vps(interaction: discord.Interaction, vps_id: str):
    """Renew a VPS instance."""
    user_id = str(interaction.user.id)
    credits = user_credits.get(user_id, 0)
    
    if credits < 2:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Insufficient credits. You need 2 credits to renew.",
                color=0xFF0000,
            )
        )
        return
    
    container_id = get_container_id_from_database(user_id, vps_id)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(description=f"VPS {vps_id} not found.", color=0xFF0000)
        )
        return
    
    user_credits[user_id] -= 2
    renewal_date = datetime.now() + timedelta(days=8)
    vps_renewals[vps_id] = renewal_date
    
    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"VPS renewed for 8 days until {renewal_date.strftime('%Y-%m-%d')}. "
            f"Remaining: {user_credits[user_id]} credits",
            color=0x00FF00,
        )
    )

# =============================================================================
# Server Lifecycle Commands
# =============================================================================

async def create_server_task(interaction: discord.Interaction) -> None:
    """Create a new VPS instance."""
    await interaction.response.send_message(
        embed=discord.Embed(
            description="Creating instance. This may take a few seconds...",
            color=0x00FF00,
        )
    )
    
    user_id = str(interaction.user.id)
    if count_user_servers(user_id) >= SERVER_LIMIT:
        await interaction.followup.send(
            embed=discord.Embed(
                description="Error: Instance limit reached.",
                color=0xFF0000,
            )
        )
        return
    
    try:
        container_id = subprocess.check_output(
            ["docker", "run", "-itd", "--privileged", "--hostname", "crashcloud", 
             "--cap-add=ALL", DOCKER_IMAGE]
        ).strip().decode("utf-8")
        
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        ssh_session = await capture_ssh_session_line(exec_cmd)
        if ssh_session:
            add_to_database(user_id, container_id, container_id[:12], ssh_session)
            
            await interaction.user.send(
                embed=discord.Embed(
                    description=f"Instance created!\nSSH Command: ```{ssh_session}```\nOS: Ubuntu 22.04",
                    color=0x00FF00,
                )
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Instance created. Check your DMs for details.",
                    color=0x00FF00,
                )
            )
        else:
            subprocess.run(["docker", "kill", container_id], check=False)
            subprocess.run(["docker", "rm", container_id], check=False)
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Instance creation timed out. Please try again.",
                    color=0xFF0000,
                )
            )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating container: {e}")
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Error: {str(e)}",
                color=0xFF0000,
            )
        )


async def _execute_server_action(
    interaction: discord.Interaction,
    container_name: str,
    action: str,
) -> None:
    """Execute a server action (start, stop, restart)."""
    user_id = str(interaction.user.id)
    container_id = get_container_id_from_database(user_id, container_name)
    
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(description="Instance not found.", color=0xFF0000)
        )
        return
    
    try:
        subprocess.run(["docker", action, container_id], check=True)
        
        # Generate SSH session for start/restart
        if action in ("start", "restart"):
            exec_cmd = await asyncio.create_subprocess_exec(
                "docker", "exec", container_id, "tmate", "-F",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            ssh_session = await capture_ssh_session_line(exec_cmd)
            
            if ssh_session:
                await interaction.user.send(
                    embed=discord.Embed(
                        description=f"Instance {action}ed\nSSH: ```{ssh_session}```",
                        color=0x00FF00,
                    )
                )
        
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Instance {action}ed successfully.",
                color=0x00FF00,
            )
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error: {str(e)}",
                color=0xFF0000,
            )
        )


@bot.tree.command(name="deploy", description="Deploy a new Ubuntu 22.04 instance.")
async def deploy_ubuntu(interaction: discord.Interaction):
    """Deploy a new VPS."""
    await create_server_task(interaction)


@bot.tree.command(name="start", description="Start your VPS instance.")
@app_commands.describe(container_name="Container name or ID")
async def start_server(interaction: discord.Interaction, container_name: str):
    """Start a VPS instance."""
    await _execute_server_action(interaction, container_name, "start")


@bot.tree.command(name="stop", description="Stop your VPS instance.")
@app_commands.describe(container_name="Container name or ID")
async def stop_server(interaction: discord.Interaction, container_name: str):
    """Stop a VPS instance."""
    await _execute_server_action(interaction, container_name, "stop")


@bot.tree.command(name="restart", description="Restart your VPS instance.")
@app_commands.describe(container_name="Container name or ID")
async def restart_server(interaction: discord.Interaction, container_name: str):
    """Restart a VPS instance."""
    await _execute_server_action(interaction, container_name, "restart")


@bot.tree.command(name="regen-ssh", description="Regenerate SSH credentials.")
@app_commands.describe(container_name="Container name or ID")
async def regen_ssh(interaction: discord.Interaction, container_name: str):
    """Regenerate SSH session."""
    user_id = str(interaction.user.id)
    container_id = get_container_id_from_database(user_id, container_name)
    
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
        ssh_session = await capture_ssh_session_line(exec_cmd)
        
        if ssh_session:
            await interaction.user.send(
                embed=discord.Embed(
                    description=f"New SSH Session: ```{ssh_session}```",
                    color=0x00FF00,
                )
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="SSH regenerated. Check your DMs.",
                    color=0x00FF00,
                )
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(description="Failed to generate SSH.", color=0xFF0000)
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
        )


@bot.tree.command(name="remove", description="Remove a VPS instance.")
@app_commands.describe(container_name="Container name or ID")
async def remove_server(interaction: discord.Interaction, container_name: str):
    """Remove a VPS instance."""
    await interaction.response.defer()
    
    user_id = str(interaction.user.id)
    container_id = get_container_id_from_database(user_id, container_name)
    
    if not container_id:
        await interaction.followup.send(
            embed=discord.Embed(description="Instance not found.", color=0xFF0000)
        )
        return
    
    try:
        subprocess.run(["docker", "stop", container_id], check=False)
        subprocess.run(["docker", "rm", container_id], check=False)
        remove_from_database(container_id)
        
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Instance removed successfully.",
                color=0x00FF00,
            )
        )
    except Exception as e:
        logger.error(f"Error removing instance: {e}")
        await interaction.followup.send(
            embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
        )

# =============================================================================
# Utility Commands
# =============================================================================

@bot.tree.command(name="list", description="List all your VPS instances.")
async def list_servers(interaction: discord.Interaction):
    """List user's VPS instances."""
    await interaction.response.defer()
    
    user_id = str(interaction.user.id)
    servers = get_user_servers(user_id)
    
    if servers:
        embed = discord.Embed(title="Your Instances", color=0x00FF00)
        for container_id, container_name, _ in servers:
            embed.add_field(name=container_name, value="32GB RAM - Premium - 4 cores", inline=False)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(
            embed=discord.Embed(
                description="You don't have any active servers.",
                color=0xFF0000,
            )
        )


@bot.tree.command(name="ping", description="Check bot latency.")
async def ping(interaction: discord.Interaction):
    """Ping command."""
    await interaction.response.defer()
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {latency}ms",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="Display help message.")
async def help_command(interaction: discord.Interaction):
    """Show help for all commands."""
    embed = discord.Embed(title="Available Commands", color=0x00FF00)
    commands_list = [
        ("/deploy", "Deploy a new Ubuntu 22.04 VPS"),
        ("/remove <id>", "Remove a VPS instance"),
        ("/start <id>", "Start a VPS instance"),
        ("/stop <id>", "Stop a VPS instance"),
        ("/restart <id>", "Restart a VPS instance"),
        ("/regen-ssh <id>", "Regenerate SSH credentials"),
        ("/list", "List your VPS instances"),
        ("/ping", "Check bot latency"),
        ("/node", "Display node status"),
        ("/bal", "Check credit balance"),
        ("/renew <id>", "Renew VPS for 8 days (2 credits)"),
        ("/earncredit", "Earn credits via URL shortening"),
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await interaction.response.send_message(embed=embed)

# =============================================================================
# Port Forwarding Commands
# =============================================================================

async def capture_output(process, keyword: str) -> Optional[str]:
    """Capture output containing a specific keyword."""
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode("utf-8").strip()
        if keyword in output:
            return output
    return None


@bot.tree.command(name="port-add", description="Add port forwarding.")
@app_commands.describe(
    container_name="Container name or ID",
    container_port="Internal container port",
)
async def port_add(interaction: discord.Interaction, container_name: str, container_port: int):
    """Set up port forwarding."""
    if not is_safe_container_name(container_name):
        await interaction.response.send_message(
            embed=discord.Embed(description="Invalid container name.", color=0xFF0000),
            ephemeral=True,
        )
        return
    
    await interaction.response.send_message(
        embed=discord.Embed(
            description="Setting up port forwarding...",
            color=0x00FF00,
        )
    )
    
    public_port = generate_random_port()
    
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
                description=f"Port forwarding active: {PUBLIC_IP}:{public_port}",
                color=0x00FF00,
            )
        )
    except Exception as e:
        logger.error(f"Port forwarding error: {e}")
        await interaction.followup.send(
            embed=discord.Embed(
                description="Error setting up port forwarding.",
                color=0xFF0000,
            )
        )


@bot.tree.command(name="port-http", description="Forward HTTP traffic.")
@app_commands.describe(
    container_name="Container name or ID",
    container_port="Internal HTTP port",
)
async def port_forward_http(interaction: discord.Interaction, container_name: str, container_port: int):
    """Set up HTTP port forwarding."""
    try:
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-R", f"80:localhost:{container_port}",
            "serveo.net",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        url_line = await capture_output(exec_cmd, "Forwarding HTTP traffic from")
        if url_line:
            url = url_line.split()[-1]
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"Website available at: {url}",
                    color=0x00FF00,
                )
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Failed to get forwarding URL.",
                    color=0xFF0000,
                )
            )
    except Exception as e:
        logger.error(f"HTTP forwarding error: {e}")
        await interaction.response.send_message(
            embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000)
        )

# =============================================================================
# Admin Commands
# =============================================================================

@app_commands.command(name="delvps", description="Delete VPS containers for a user (Admin).")
@app_commands.checks.has_permissions(administrator=True)
async def admin_delete_vps(interaction: discord.Interaction, user_id: str):
    """Delete all VPS containers for a user."""
    await interaction.response.defer(thinking=True)
    
    try:
        deleted = []
        for container in client.containers.list(all=True):
            if user_id in container.name:
                container.remove(force=True)
                deleted.append(container.name)
                remove_from_database(container.id)
        
        if deleted:
            await interaction.followup.send(f"Deleted: {', '.join(deleted)}")
        else:
            await interaction.followup.send("No containers found for that user.")
    except Exception as e:
        logger.error(f"Error in admin delete: {e}")
        await interaction.followup.send(f"Error: {str(e)}")


@app_commands.command(name="node-admin", description="Show detailed node stats (Admin).")
@app_commands.checks.has_permissions(administrator=True)
async def admin_node_stats(interaction: discord.Interaction):
    """Display detailed container statistics."""
    await interaction.response.defer(thinking=True)
    
    try:
        container_data = []
        for container in client.containers.list(all=True):
            stats = container.stats(stream=False)
            cpu_usage = stats["cpu_stats"]["cpu_usage"]["total_usage"] / 1e9
            memory_usage = stats["memory_stats"]["usage"] / 1e6
            container_data.append(
                f"{container.name[:20]} | CPU: {cpu_usage:.2f}% | RAM: {memory_usage:.2f}MB"
            )
        
        if container_data:
            await interaction.followup.send("```\n" + "\n".join(container_data) + "\n```")
        else:
            await interaction.followup.send("No containers found.")
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await interaction.followup.send(f"Error: {str(e)}")


@app_commands.command(name="killvps", description="Terminate all VPS (Admin).")
@app_commands.checks.has_permissions(administrator=True)
async def admin_kill_all_vps(interaction: discord.Interaction):
    """Admin command to kill all VPS instances."""
    await interaction.response.defer(thinking=True)
    
    try:
        subprocess.run("docker rm -f $(docker ps -a -q)", shell=True, check=False)
        subprocess.run("pkill python", shell=True, check=False)
        init_database()  # Reset database
        user_credits.clear()
        
        await interaction.followup.send("All instances terminated and database reset.")
    except Exception as e:
        logger.error(f"Error in killvps: {e}")
        await interaction.followup.send(f"Error: {str(e)}")

# =============================================================================
# Bot Startup
# =============================================================================

if __name__ == "__main__":
    init_database()
    bot.run(TOKEN)
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error stopping instance: {e}",
                color=0xff0000)
        )

async def restart_server(interaction: discord.Interaction, container_name: str):
    """
    Restart a VPS instance and generate a new SSH session.
    """
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="No instance found for your user.",
                color=0xff0000)
        )
        return

    try:
        subprocess.run(["docker", "restart", container_id], check=True)
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        ssh_session_line = await capture_ssh_session_line(exec_cmd)
        if ssh_session_line:
            await interaction.user.send(
                embed=discord.Embed(
                    description=f"Instance Restarted\nSSH Session Command: ```{ssh_session_line}```\nOS: Ubuntu 22.04",
                    color=0x00ff00)
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Instance restarted successfully. Check your DMs for details.",
                    color=0x00ff00)
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Instance restarted, but failed to retrieve SSH session line.",
                    color=0xff0000)
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error restarting instance: {e}",
                color=0xff0000)
        )

# =============================================================================
# Server Creation and Deployment Functionality
# =============================================================================

async def create_server_task(interaction):
    """
    Create and deploy a new VPS instance in a Docker container using the specified image.
    """
    await interaction.response.send_message(
        embed=discord.Embed(
            description="Creating instance. This may take a few seconds. Powered by [CrashOfGuys](https://discord.com/invite/VWm8zUEQN8)",
            color=0x00ff00)
    )
    userid = str(interaction.user.id)
    if count_user_servers(userid) >= SERVER_LIMIT:
        await interaction.followup.send(
            embed=discord.Embed(
                description="Error: Instance limit reached.",
                color=0xff0000)
        )
        return

    image = "ubuntu-22.04-with-tmate"  # Docker image used to deploy the VPS instance

    try:
        # Create a new Docker container for the VPS instance
        container_id = subprocess.check_output([
            "docker", "run", "-itd", "--privileged", "--hostname", "crashcloud", "--cap-add=ALL", image
        ]).strip().decode('utf-8')
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Error creating Docker container: {e}",
                color=0xff0000)
        )
        return

    try:
        # Execute tmate within the container to generate an SSH session command
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Error executing tmate in Docker container: {e}",
                color=0xff0000)
        )
        subprocess.run(["docker", "kill", container_id])
        subprocess.run(["docker", "rm", container_id])
        return

    ssh_session_line = await capture_ssh_session_line(exec_cmd)
    if ssh_session_line:
        await interaction.user.send(
            embed=discord.Embed(
                description=f"Successfully created instance\nSSH Session Command: ```{ssh_session_line}```\nOS: Ubuntu 22.04\nPassword: root",
                color=0x00ff00)
        )
        add_to_database(userid, container_id, ssh_session_line)
        await interaction.followup.send(
            embed=discord.Embed(
                description="Instance created successfully. Check your DMs for details.",
                color=0x00ff00)
        )
    else:
        await interaction.followup.send(
            embed=discord.Embed(
                description="Instance creation timed out. Please contact support if the issue persists.",
                color=0xff0000)
        )
        subprocess.run(["docker", "kill", container_id])
        subprocess.run(["docker", "rm", container_id])

@bot.tree.command(name="deploy", description="Deploy a new Ubuntu 22.04 instance.")
async def deploy_ubuntu(interaction: discord.Interaction):
    """
    Command to deploy a new VPS instance running Ubuntu 22.04.
    """
    await create_server_task(interaction)

@bot.tree.command(name="regen-ssh", description="Regenerate SSH credentials for your instance.")
@app_commands.describe(container_name="The name or SSH command associated with your instance")
async def regen_ssh(interaction: discord.Interaction, container_name: str):
    """
    Command to regenerate the SSH session command for an existing instance.
    # Beschreibung der Funktion
    """
    await regen_ssh_command(interaction, container_name)

@bot.tree.command(name="start", description="Start your VPS instance.")
@app_commands.describe(container_name="The name or SSH command associated with your instance")
async def start(interaction: discord.Interaction, container_name: str):
    """
    Command to start a previously stopped VPS instance.
    """
    await start_server(interaction, container_name)

@bot.tree.command(name="stop", description="Stop your VPS instance.")
@app_commands.describe(container_name="The name or SSH command associated with your instance")
async def stop(interaction: discord.Interaction, container_name: str):
    """
    Command to stop a running VPS instance.
    """
    await stop_server(interaction, container_name)

@bot.tree.command(name="restart", description="Restart your VPS instance.")
@app_commands.describe(container_name="The name or SSH command associated with your instance")
async def restart(interaction: discord.Interaction, container_name: str):
    """
    Command to restart an active VPS instance.
    """
    await restart_server(interaction, container_name)

@bot.tree.command(name="ping", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):
    """
    Command to test the connection latency to Discord's servers.
    """
    await interaction.response.defer()
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {latency}ms",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="list", description="List all of your VPS instances.")
async def list_servers(interaction: discord.Interaction):
    """
    Command to list all VPS instances owned by the user.
    """
    await interaction.response.defer()
    userid = str(interaction.user.id)
    servers = get_user_servers(userid)
    if servers:
        embed = discord.Embed(title="Your Instances", color=0x00ff00)
        for server in servers:
            _, container_name, _ = server.split('|')
            embed.add_field(name=container_name, value="32GB RAM - Premium - 4 cores", inline=False)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(
            embed=discord.Embed(
                description="You don't have any active servers.",
                color=0xff0000)
        )

# =============================================================================
# Port Forwarding Commands
# =============================================================================

async def execute_command(command):
    """
    Helper function to execute a shell command asynchronously.
    """
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()

PUBLIC_IP = os.getenv("PUBLIC_IP", "")  # Public IP address for service hosting

def _is_safe_container_name(name: str) -> bool:
    return bool(SAFE_CONTAINER_RE.fullmatch(name))

async def capture_output(process, keyword):
    """
    Capture a line from the process output that contains a specific keyword.
    """
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        if keyword in output:
            return output
    return None

@bot.tree.command(name="port-add", description="Add a port forwarding rule for your container.")
@app_commands.describe(container_name="The name of the container", container_port="The internal container port")
async def port_add(interaction: discord.Interaction, container_name: str, container_port: int):
    """
    Set up port forwarding using SSH reverse tunneling.
    """
    await interaction.response.send_message(
        embed=discord.Embed(
            description="Setting up port forwarding. Please wait...",
            color=0x00ff00)
    )
    public_port = generate_random_port()  # Generate a random public-facing port

    # Command to establish SSH reverse tunnel via serveo.net
    try:
        if not _is_safe_container_name(container_name):
            await interaction.followup.send("Invalid container name.", ephemeral=True)
            return
        # Execute the reverse tunnel command inside the Docker container
        await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-R", f"{public_port}:localhost:{container_port}",
            "serveo.net", "-N", "-f",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Port added successfully. Your service is accessible at {PUBLIC_IP}:{public_port}.",
                color=0x00ff00)
        )
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description="An error occurred while configuring port forwarding.",
                color=0xff0000)
        )

@bot.tree.command(name="port-http", description="Forward HTTP traffic to your container.")
@app_commands.describe(container_name="The container name", container_port="The internal container port for HTTP forwarding")
async def port_forward_website(interaction: discord.Interaction, container_name: str, container_port: int):
    """
    Create an HTTP reverse tunnel for the user's container.
    """
    try:
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "ssh", "-o StrictHostKeyChecking=no", "-R", f"80:localhost:{container_port}", "serveo.net",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        url_line = await capture_output(exec_cmd, "Forwarding HTTP traffic from")
        if url_line:
            url = url_line.split(" ")[-1]
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"Website forwarded successfully. Access your site at {url}.",
                    color=0x00ff00)
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Failed to capture forwarding URL.",
                    color=0xff0000)
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error executing website forwarding: {e}",
                color=0xff0000)
        )

# =============================================================================
# Server Removal Command
# =============================================================================

@bot.tree.command(name="remove", description="Remove a VPS instance.")
@app_commands.describe(container_name="The name or SSH command of your instance")
async def remove_server(interaction: discord.Interaction, container_name: str):
    """
    Command to stop and remove a VPS instance, as well as clear its record from the database.
    """
    await interaction.response.defer()
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="No instance found with the specified name.",
                color=0xff0000)
        )
        return

    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        subprocess.run(["docker", "rm", container_id], check=True)
        remove_from_database(container_id)
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Instance '{container_name}' removed successfully.",
                color=0x00ff00)
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error removing instance: {e}",
                color=0xff0000)
        )

# =============================================================================
# Help Command
# =============================================================================

@bot.tree.command(name="help", description="Display this help message.")
async def help_command(interaction: discord.Interaction):
    """
    Command to list all available commands and provide brief descriptions.
    """
    embed = discord.Embed(title="Help", color=0x00ff00)
    embed.add_field(name="/deploy", value="Deploy a new Ubuntu 22.04 VPS instance.", inline=False)
    embed.add_field(name="/remove <ssh_command/Name>", value="Remove a VPS instance.", inline=False)
    embed.add_field(name="/start <ssh_command/Name>", value="Start a VPS instance.", inline=False)
    embed.add_field(name="/stop <ssh_command/Name>", value="Stop a VPS instance.", inline=False)
    embed.add_field(name="/regen-ssh <ssh_command/Name>", value="Regenerate SSH credentials for an instance.", inline=False)
    embed.add_field(name="/restart <ssh_command/Name>", value="Restart a VPS instance.", inline=False)
    embed.add_field(name="/list", value="List all your VPS instances.", inline=False)
    embed.add_field(name="/ping", value="Check the bot's latency.", inline=False)
    embed.add_field(name="/node", value="Display the node/VPS usage status.", inline=False)
    embed.add_field(name="/bal", value="Check your credit balance.", inline=False)
    embed.add_field(name="/renew", value="Renew VPS instance for 8 days (cost: 2 credits).", inline=False)
    embed.add_field(name="/earncredit", value="Earn credits by generating a shortened URL.", inline=False)
    await interaction.response.send_message(embed=embed)

# =============================================================================
# Additional Admin Commands (Optional)
# =============================================================================

@app_commands.command(name="delvps", description="Delete all VPS containers for a specified user (Admin only).")
@app_commands.checks.has_permissions(administrator=True)
async def delvps(interaction: discord.Interaction, user_id: str):
    """
    Admin command to delete all VPS containers that contain the specified user ID in their name.
    """
    await interaction.response.defer(thinking=True)
    docker_client = docker.from_env()
    deleted_containers = []
    for container in docker_client.containers.list(all=True):
        if user_id in container.name:
            container.remove(force=True)
            deleted_containers.append(container.name)
    if deleted_containers:
        await interaction.followup.send(f"Deleted containers: {', '.join(deleted_containers)}")
    else:
        await interaction.followup.send("No containers found for the specified user.")

@app_commands.command(name="node_admin", description="Show detailed usage statistics for all containers (Admin only).")
@app_commands.checks.has_permissions(administrator=True)
async def node_admin(interaction: discord.Interaction):
    """
    Admin command to display detailed stats (CPU, RAM) for each container.
    Count the number of active VPS instances a user currently has.
    """
    await interaction.response.defer(thinking=True)
    docker_client = docker.from_env()
    container_data = []
    for container in docker_client.containers.list(all=True):
        stats = container.stats(stream=False)
        cpu_usage = stats["cpu_stats"]["cpu_usage"]["total_usage"] / 1e9  # CPU usage in seconds
        memory_usage = stats["memory_stats"]["usage"] / 1e6  # Memory usage in MB
        container_data.append(f"User: {container.name.split('_')[0]} | ID: {container.id[:12]} | CPU: {cpu_usage:.2f}% | RAM: {memory_usage:.2f}MB")
    if container_data:
        await interaction.followup.send("```\n" + "\n".join(container_data) + "\n```")
    else:
        await interaction.followup.send("No containers found.")

# =============================================================================
# Start the Bot
# =============================================================================

bot.run(TOKEN)
    # Gibt die Anzahl der Server zurück
    return len(get_user_servers(userid)) """