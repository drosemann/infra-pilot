import logging
import subprocess
import sys
import os
import re
import time
import concurrent.futures
import random
import discord
from discord.ext import commands, tasks
import docker
import asyncio
from discord import app_commands
import requests
from datetime import datetime, timedelta
from threading import Lock

# =============================================================================
# Configuration Section
# =============================================================================

# Bot and Docker configuration
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
RAM_LIMIT = '1g'  # Memory limit allocation for user instances
SERVER_LIMIT = 1  # Maximum number of VPS instances allowed per user
database_file = 'database.txt'  # File used to store instance details

# Discord Intents: Disable some events to reduce unnecessary data processing
intents = discord.Intents.default()
intents.messages = False
intents.message_content = False

# Initialize the bot with a command prefix and defined intents
bot = commands.Bot(command_prefix='/', intents=intents)

# Initialize Docker client (assumes Docker is installed and running)
client = docker.from_env()

# Set of admin user IDs (as strings) who may execute restricted commands
whitelist_ids = set(filter(None, os.getenv("WHITELIST_IDS", "").split(",")))
database_lock = Lock()
SAFE_CONTAINER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")

# =============================================================================
# Utility Functions for Database Management
# =============================================================================

def add_to_database(userid, container_name, ssh_command):
    """
    Append instance details (user ID, container identifier, SSH command) to the database file.
    """
    with database_lock:
        with open(database_file, 'a', encoding='utf-8') as f:
            f.write(f"{userid}|{container_name}|{ssh_command}\n")

def remove_from_database(ssh_command):
    """
    Remove an entry containing the specified SSH command from the database.
    """
    if not os.path.exists(database_file):
        return
    with database_lock:
        with open(database_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Write back all lines that do not contain the provided SSH command
        with open(database_file, 'w', encoding='utf-8') as f:
            for line in lines:
                if ssh_command not in line:
                    f.write(line)

def get_user_servers(user):
    """
    Retrieve all VPS instance records associated with a given user.
    """
    if not os.path.exists(database_file):
        return []
    servers = []
    with open(database_file, 'r') as f:
        for line in f:
            if line.startswith(user):
                servers.append(line.strip())
    return servers

def count_user_servers(userid):
    """
    Count the number of active VPS instances a user currently has.
    """
    return len(get_user_servers(userid))

def get_container_id_from_database(userid, container_name):
    """
    Find and return a container's identifier from the database for the given user and container name.
    """
    if not os.path.exists(database_file):
        return None
    with open(database_file, 'r') as f:
        for line in f:
            if line.startswith(userid) and container_name in line:
                return line.split('|')[1]
    return None

def generate_random_port():
    """
    Generate a random port number within the valid range (1025-65535).
    """
    return random.randint(1025, 65535)

async def capture_ssh_session_line(process):
    """
    Asynchronously read stdout from the process until the SSH session command line is captured.
    """
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        # Look for the expected output pattern containing "ssh session:"
        if "ssh session:" in output:
            return output.split("ssh session:")[1].strip()
    return None

# =============================================================================
# User Credits and Third-Party API Integration (Cuty.io)
# =============================================================================

# In-memory database to hold user credit balances
user_credits = {}

# API key for URL-shortening service (Cuty.io) integration
API_KEY = os.getenv("CUTTLY_API_KEY", "")

# =============================================================================
# Slash Commands Definitions
# =============================================================================

@bot.tree.command(name="earncredit", description="Generate a shortened URL to earn credits.")
async def earncredit(interaction: discord.Interaction):
    """
    Shorten a predefined URL using the Cuty.io API and award the user with credits.
    """
    user_id = interaction.user.id
    default_url = "https://cuty.io/e58WUzLMmE3S"  # Predefined URL to be shortened

    # Construct API URL call
    api_url = f"https://cutt.ly/api/api.php?key={API_KEY}&short={default_url}"
    response = requests.get(api_url).json()
    
    # Evaluate API response for success
    if response['url']['status'] == 7:
        shortened_url = response['url']['shortLink']
        credits_earned = 1  # Award one credit per successful shortening

        # Update the in-memory credit balance for the user
        user_credits[user_id] = user_credits.get(user_id, 0) + credits_earned

        await interaction.response.send_message(
            f"Success! Here is your shortened URL: {shortened_url}. You earned {credits_earned} credit!"
        )
    else:
        error_message = response['url'].get('title', 'Failed to generate a shortened URL. Please try again.')
        await interaction.response.send_message(error_message)

@bot.tree.command(name="bal", description="Check your credit balance.")
async def bal(interaction: discord.Interaction):
    """
    Respond with the current number of credits available to the user.
    """
    user_id = interaction.user.id
    credits = user_credits.get(user_id, 0)
    await interaction.response.send_message(f"You have {credits} credits.")

# =============================================================================
# Node/VPS Status Functions
# =============================================================================

def get_node_status():
    """
    Retrieve details about the VPS node including container statuses and memory usage.
    """
    try:
        # List all Docker containers and their statuses
        containers = client.containers.list(all=True)
        container_status = "\n".join([f"{container.name} - {container.status}" for container in containers]) or "No containers running."

        # Read system memory information from '/proc/meminfo'
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1)) / 1024  # Convert from kB to MB
        mem_free = int(re.search(r'MemFree:\s+(\d+)', meminfo).group(1)) / 1024
        mem_available = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1)) / 1024

        memory_used = mem_total - mem_available
        memory_percentage = (memory_used / mem_total) * 100 if mem_total else 0

        node_info = {
            "containers": container_status,
            "memory_total": mem_total,
            "memory_used": memory_used,
            "memory_percentage": memory_percentage
        }
        return node_info
    except Exception as e:
        return str(e)

@bot.tree.command(name="node", description="Display the current node/VPS status including memory usage.")
async def node_status(interaction: discord.Interaction):
    """
    Present an embed message with current container statuses and memory usage statistics.
    """
    node_info = get_node_status()

    if isinstance(node_info, str):  # Check for errors during status retrieval
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"### Error fetching node status: {node_info}",
                color=0xff0000)
        )
        return

    embed = discord.Embed(title="VPS Node1 Status", color=0x00ff00)
    embed.add_field(name="Containers", value=node_info["containers"], inline=False)
    embed.add_field(
        name="Memory Usage",
        value=f"{node_info['memory_used']:.2f} / {node_info['memory_total']:.2f} MB ({node_info['memory_percentage']:.2f}%)",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="renew", description="Renew a VPS for an additional 8 days using 2 credits.")
@app_commands.describe(vps_id="ID of the VPS to renew")
async def renew(interaction: discord.Interaction, vps_id: str):
    """
    Renew a VPS instance by extending its expiry date, after verifying sufficient user credits.
    """
    user_id = str(interaction.user.id)
    credits = user_credits.get(user_id, 0)

    if credits < 2:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Insufficient credits. You require 2 credits to renew the VPS.",
                color=0xff0000)
        )
        return

    container_id = get_container_id_from_database(user_id, vps_id)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"VPS with ID {vps_id} not found.",
                color=0xff0000)
        )
        return

    # Deduct credits and update the renewal expiration date for the VPS
    user_credits[user_id] -= 2
    renewal_date = datetime.now() + timedelta(days=8)
    vps_renewals = {}  # This should be persisted; here it's in-memory
    vps_renewals[vps_id] = renewal_date

    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"VPS {vps_id} has been renewed for 8 days. New expiry date: {renewal_date.strftime('%Y-%m-%d')}. "
                        f"Remaining Credits: {user_credits[user_id]}",
            color=0x00ff00)
    )

# =============================================================================
# Administrative Tasks and Cleanup Functions
# =============================================================================

async def remove_everything_task(interaction: discord.Interaction):
    """
    Stop all running Docker containers, clear the database and kill related services.
    """
    await interaction.channel.send("### Node is full. Resetting all user instances...")
    try:
        subprocess.run("docker rm -f $(sudo docker ps -a -q)", shell=True, check=True)
        os.remove(database_file)
        subprocess.run("pkill pytho*", shell=True, check=True)
        await interaction.channel.send("### All instances and data have been reset.")
    except Exception as e:
        await interaction.channel.send(f"### Failed to reset instances: {str(e)}")

@bot.tree.command(name="killvps", description="Terminate all VPS instances (Admin only).")
async def kill_vps(interaction: discord.Interaction):
    """
    Admin command to remove all VPS instances and data.
    """
    userid = str(interaction.user.id)
    if userid not in whitelist_ids:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="You do not have permission to use this command.",
                color=0xff0000)
        )
        return

    await remove_everything_task(interaction)
    await interaction.response.send_message(
        embed=discord.Embed(
            description="All user VPS instances have been terminated.",
            color=0x00ff00)
    )

# =============================================================================
# Duplicate Utility Functions (May be refactored to avoid repetition)
# =============================================================================

def get_ssh_command_from_database(container_id):
    """
    Retrieve the SSH command associated with a given container from the database.
    """
    if not os.path.exists(database_file):
        return None
    with open(database_file, 'r') as f:
        for line in f:
            if container_id in line:
                return line.split('|')[2]
    return None

def get_user_servers(user):
    """
    Retrieve VPS instance details linked to a specific user.
    """
    if not os.path.exists(database_file):
        return []
    servers = []
    with open(database_file, 'r') as f:
        for line in f:
            if line.startswith(user):
                servers.append(line.strip())
    return servers

def count_user_servers(userid):
    """
    Compute the number of VPS instances owned by a user.
    """
    return len(get_user_servers(userid))

def get_container_id_from_database(userid):
    """
    Return the container ID for the given user (if available, taking the first entry).
    """
    servers = get_user_servers(userid)
    if servers:
        return servers[0].split('|')[1]
    return None

# =============================================================================
# Event Listener: on_ready
# =============================================================================

@bot.event
async def on_ready():
    """
    Event triggered when the bot is successfully connected.
    """
    # Uncomment the following line if you wish to use the periodic status update task.
    # change_status.start()
    print(f'Bot is ready. Logged in as {bot.user}')
    await bot.tree.sync()

# =============================================================================
# Functions to Regenerate SSH Session and Manage Server Instance State
# =============================================================================

async def regen_ssh_command(interaction: discord.Interaction, container_name: str):
    """
    Regenerate an SSH session command for a specific container.
    """
    user = str(interaction.user)
    container_id = get_container_id_from_database(user, container_name)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="No active instance found for your user.",
                color=0xff0000)
        )
        return

    try:
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error executing tmate in Docker container: {e}",
                color=0xff0000)
        )
        return

    ssh_session_line = await capture_ssh_session_line(exec_cmd)
    if ssh_session_line:
        await interaction.user.send(
            embed=discord.Embed(
                description=f"New SSH Session Command: ```{ssh_session_line}```",
                color=0x00ff00)
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                description="New SSH session generated. Check your DMs for details.",
                color=0x00ff00)
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Failed to generate new SSH session.",
                color=0xff0000)
        )

async def start_server(interaction: discord.Interaction, container_name: str):
    """
    Start a stopped VPS instance and retrieve an SSH session command.
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
        subprocess.run(["docker", "start", container_id], check=True)
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        ssh_session_line = await capture_ssh_session_line(exec_cmd)
        if ssh_session_line:
            await interaction.user.send(
                embed=discord.Embed(
                    description=f"Instance Started\nSSH Session Command: ```{ssh_session_line}```",
                    color=0x00ff00)
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Instance started successfully. Check your DMs for details.",
                    color=0x00ff00)
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Instance started, but failed to retrieve SSH session line.",
                    color=0xff0000)
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error starting instance: {e}",
                color=0xff0000)
        )

async def stop_server(interaction: discord.Interaction, container_name: str):
    """
    Stop a running VPS instance.
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
        subprocess.run(["docker", "stop", container_id], check=True)
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Instance stopped successfully.",
                color=0x00ff00)
        )
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
