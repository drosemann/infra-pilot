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
from datetime import datetime, timedelta  # Added for VPS renewal
from threading import Lock

# -----------------------------------------------------------------------------
# Bot Configuration and Global Variables
# -----------------------------------------------------------------------------

# Bot token and configuration settings
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
RAM_LIMIT = '1g'  # Maximum memory allocation for user instances
SERVER_LIMIT = 1  # Maximum allowed instances per user
database_file = 'database.txt'  # File to store instance information

# Docker client for container management
client = docker.from_env()

# Discord bot intents and bot/client initialization
intents = discord.Intents.default()
intents.messages = False
intents.message_content = False
bot = commands.Bot(command_prefix='/', intents=intents)

# A set of whitelisted user IDs (admin privileges)
whitelist_ids = set(filter(None, os.getenv("WHITELIST_IDS", "").split(",")))

# In-memory dictionary to keep track of user credits (should be replaced with persistent storage in production)
user_credits = {}

# API key for the cuty.io URL-shortening service
API_KEY = os.getenv("CUTTLY_API_KEY", "")

# Public IP address used in port forwarding commands
PUBLIC_IP = os.getenv("PUBLIC_IP", "")
database_lock = Lock()
SAFE_CONTAINER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def add_to_database(userid, container_name, ssh_command):
    """
    Records the VPS instance data to a local database file.
    Format: userID|containerID|ssh_command
    """
    with database_lock:
        with open(database_file, 'a', encoding='utf-8') as f:
            f.write(f"{userid}|{container_name}|{ssh_command}\n")

def remove_from_database(ssh_command):
    """
    Removes a VPS instance entry from the local database using its SSH command signature.
    """
    if not os.path.exists(database_file):
        return
    with database_lock:
        with open(database_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(database_file, 'w', encoding='utf-8') as f:
            for line in lines:
                if ssh_command not in line:
                    f.write(line)

def _is_safe_container_name(name: str) -> bool:
    return bool(SAFE_CONTAINER_RE.fullmatch(name))

def get_user_servers(user):
    """
    Returns a list of VPS entries associated with the given user.
    Each entry is stored as a string in the format: userID|containerID|ssh_command.
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
    Returns the count of VPS instances associated with the given user.
    """
    return len(get_user_servers(userid))

def get_container_id_from_database(userid, container_name):
    """
    Retrieves the container ID corresponding to the given user ID and container identifier.
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
    Generates a random available port number.
    """
    return random.randint(1025, 65535)

async def capture_ssh_session_line(process):
    """
    Captures the SSH session command line from the process output.
    This function continuously reads the output until it finds a line containing "ssh session:".
    """
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        if "ssh session:" in output:
            return output.split("ssh session:")[1].strip()
    return None

async def capture_output(process, keyword):
    """
    Reads process output until a line containing the specified keyword is found.
    Used particularly for capturing port forwarding details.
    """
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        if keyword in output:
            return output
    return None

# -----------------------------------------------------------------------------
# Discord Bot Commands
# -----------------------------------------------------------------------------

@bot.tree.command(name="earncredit", description="Generate a URL to shorten and earn credits.")
async def earncredit(interaction: discord.Interaction):
    """
    Slash command that shortens a predetermined URL using the cuty.io API.
    On successful shortening, the user earns a fixed amount of credit.
    """
    print("Received request to shorten URL")
    user_id = interaction.user.id

    # Predetermined URL to shorten (can be modified as per requirements)
    default_url = "https://cuty.io/e58WUzLMmE3S"

    # Construct API URL for cuty.io
    api_url = f"https://cutt.ly/api/api.php?key={API_KEY}&short={default_url}"
    print(f"Making API call to: {api_url}")
    response = requests.get(api_url).json()
    print(f"API response: {response}")

    if response['url']['status'] == 7:
        shortened_url = response['url']['shortLink']
        credits_earned = 1  # Fixed earning per URL shortening request
        user_credits[user_id] = user_credits.get(user_id, 0) + credits_earned
        await interaction.response.send_message(
            f"Success! Here's your shortened URL: {shortened_url}. You earned {credits_earned} credit!"
        )
    else:
        error_message = response['url'].get('title', 'Failed to generate a shortened URL. Please try again.')
        await interaction.response.send_message(error_message)

@bot.tree.command(name="bal", description="Check your credit balance.")
async def bal(interaction: discord.Interaction):
    """
    Slash command that shows the user their current credit balance.
    """
    user_id = interaction.user.id
    credits = user_credits.get(user_id, 0)
    await interaction.response.send_message(f"You have {credits} credits.")

@bot.tree.command(name="port-forward-new", description="Set up port forwarding for a container using localhost.run.")
@app_commands.describe(container_name="The name of the container", container_port="The internal container port to forward")
async def port_forward_win(interaction: discord.Interaction, container_name: str, container_port: int):
    """
    Sets up port forwarding for the specified container and port using localhost.run.
    It executes a docker command and sends the forwarding result back to the user.
    """
    await interaction.response.defer()  # Defer the response to get extra processing time
    try:
        if not _is_safe_container_name(container_name):
            await interaction.followup.send("Invalid container name.", ephemeral=True)
            return
        process = await asyncio.create_subprocess_exec(
            "docker", "exec", "-i", container_name, "ssh", "-R", f"80:localhost:{container_port}", "ssh.localhost.run",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            output = stdout.decode().strip()
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"### Port Forwarding Successful:\n{output}",
                    color=0x00ff00
                )
            )
        if stderr:
            error = stderr.decode().strip()
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"### Error in Port Forwarding:\n{error}",
                    color=0xff0000
                )
            )
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description="### Failed to set up port forwarding.",
                color=0xff0000
            )
        )

def get_node_status():
    """
    Retrieves the status of all Docker containers and system memory usage.
    Returns a dictionary with container statuses and memory usage statistics.
    """
    try:
        containers = client.containers.list(all=True)
        container_status = "\n".join(
            [f"{container.name} - {container.status}" for container in containers]
        ) or "No containers running."

        # Read system memory information (Linux-specific)
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1)) / 1024  # MB
        mem_free = int(re.search(r'MemFree:\s+(\d+)', meminfo).group(1)) / 1024     # MB
        mem_available = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1)) / 1024  # MB

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

@bot.tree.command(name="node", description="Show the current status of the VPS node.")
async def node_status(interaction: discord.Interaction):
    """
    Slash command to display the VPS node's current container status and system memory usage.
    """
    try:
        node_info = get_node_status()
        if isinstance(node_info, str):  # Error handling for node status retrieval
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"### Error fetching node status: {node_info}",
                    color=0xff0000
                )
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

    except Exception as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"### Failed to fetch node status: {str(e)}",
                color=0xff0000
            )
        )

@bot.tree.command(name="renew", description="Renew a VPS for 8 days using 2 credits.")
@app_commands.describe(vps_id="ID of the VPS to renew")
async def renew(interaction: discord.Interaction, vps_id: str):
    """
    Renews an active VPS instance by extending its duration by 8 days.
    This command deducts 2 credits from the user's balance and updates the expiry.
    """
    user_id = str(interaction.user.id)
    credits = user_credits.get(user_id, 0)

    if credits < 2:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="You don't have enough credits to renew the VPS. You need 2 credits.",
                color=0xff0000
            )
        )
        return

    container_id = get_container_id_from_database(user_id, vps_id)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"VPS with ID {vps_id} not found.",
                color=0xff0000
            )
        )
        return

    # Deduct credits and renew the VPS (update expiry date)
    user_credits[user_id] -= 2
    renewal_date = datetime.now() + timedelta(days=8)
    # vps_renewals should be maintained in persistent storage; here it is assumed as in-memory
    vps_renewals = {}
    vps_renewals[vps_id] = renewal_date

    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"VPS {vps_id} has been renewed for 8 days. New expiry date: {renewal_date.strftime('%Y-%m-%d')}. "
                        f"You now have {user_credits[user_id]} credits remaining.",
            color=0x00ff00
        )
    )

async def remove_everything_task(interaction: discord.Interaction):
    """
    Removal task triggered when the node is full.
    It terminates all Docker containers, clears the local database, and kills all Python processes.
    """
    await interaction.channel.send("### Node is full. Resetting all user instances...")
    try:
        subprocess.run("docker rm -f $(sudo docker ps -a -q)", shell=True, check=True)
        os.remove(database_file)
        subprocess.run("pkill pytho*", shell=True, check=True)
        await interaction.channel.send("### All instances and data have been reset.")
    except Exception as e:
        await interaction.channel.send("### Failed to reset instances.")

@bot.tree.command(name="killvps", description="Kill all user VPS instances. Admin only.")
async def kill_vps(interaction: discord.Interaction):
    """
    Admin-only command to terminate all VPS instances across all users.
    It performs a complete cleanup of Docker containers and database records.
    """
    userid = str(interaction.user.id)
    if userid not in whitelist_ids:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="You do not have permission to use this command.",
                color=0xff0000
            )
        )
        return

    await remove_everything_task(interaction)
    await interaction.response.send_message(
        embed=discord.Embed(
            description="### All user VPS instances have been terminated.",
            color=0x00ff00
        )
    )

@bot.tree.command(name="remove-everything", description="Removes all data and containers")
async def remove_everything(interaction: discord.Interaction):
    """
    Admin-only command that removes all Docker containers and clears the local database and port files.
    It also attempts to restart the bot service.
    """
    userid = str(interaction.user.id)
    if userid not in whitelist_ids:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="You do not have permission to use this command.",
                color=0xff0000
            )
        )
        return

    try:
        subprocess.run("docker rm -f $(sudo docker ps -a -q)", shell=True, check=True)
        await interaction.response.send_message(
            embed=discord.Embed(
                description="All Docker containers have been removed.",
                color=0x00ff00
            )
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Failed to remove Docker containers.",
                color=0xff0000
            )
        )

    try:
        os.remove(database_file)
        # Ensure that 'port_db_file' exists before removing or handle exception if it doesn't.
        os.remove("port_db_file")  
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Database and port files have been cleared. Service has been restarted. Please start the bot in the shell",
                color=0x00ff00
            )
        )
        subprocess.run("pkill pytho*", shell=True, check=True)
    except Exception as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Failed to clear database or restart service.",
                color=0xff0000
            )
        )

def get_ssh_command_from_database(container_id):
    """
    Retrieves the SSH command associated with a given container ID from the database.
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
    Returns a list of VPS entries belonging to the specified user.
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
    Counts the number of VPS instances a user has.
    """
    return len(get_user_servers(userid))

def get_container_id_from_database(userid):
    """
    Returns the first container ID from the user's VPS entries in the database.
    """
    servers = get_user_servers(userid)
    if servers:
        return servers[0].split('|')[1]
    return None

@bot.event
async def on_ready():
    """
    Event handler that is called when the bot is online.
    Syncs commands with Discord and logs the bot's ready status.
    """
    # change_status.start()  # Uncomment if using status updating task
    print(f'Bot is ready. Logged in as {bot.user}')
    await bot.tree.sync()

async def regen_ssh_command(interaction: discord.Interaction, container_name: str):
    """
    Regenerates the SSH session command for a specified VPS.
    It executes the tmate command inside the Docker container to produce a new session.
    """
    user = str(interaction.user)
    container_id = get_container_id_from_database(user, container_name)

    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### No active instance found for your user.",
                color=0xff0000
            )
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
                color=0xff0000
            )
        )
        return

    ssh_session_line = await capture_ssh_session_line(exec_cmd)
    if ssh_session_line:
        await interaction.user.send(
            embed=discord.Embed(
                description=f"### New SSH Session Command: ```{ssh_session_line}```",
                color=0x00ff00
            )
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### New SSH session generated. Check your DMs for details.",
                color=0x00ff00
            )
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### Failed to generate new SSH session.",
                color=0xff0000
            )
        )

async def start_server(interaction: discord.Interaction, container_name: str):
    """
    Starts an existing VPS instance and retrieves a new SSH session command from the container.
    """
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)

    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### No instance found for your user.",
                color=0xff0000
            )
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
                    description=f"### Instance Started\nSSH Session Command: ```{ssh_session_line}```",
                    color=0x00ff00
                )
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="### Instance started successfully. Check your DMs for details.",
                    color=0x00ff00
                )
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="### Instance started, but failed to get SSH session line.",
                    color=0xff0000
                )
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error starting instance: {e}",
                color=0xff0000
            )
        )

async def stop_server(interaction: discord.Interaction, container_name: str):
    """
    Stops a running VPS instance.
    """
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)

    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### No instance found for your user.",
                color=0xff0000
            )
        )
        return

    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### Instance stopped successfully.",
                color=0x00ff00
            )
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"### Error stopping instance: {e}",
                color=0xff0000
            )
        )

async def restart_server(interaction: discord.Interaction, container_name: str):
    """
    Restarts a VPS instance and retrieves an updated SSH session command.
    """
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)

    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### No instance found for your user.",
                color=0xff0000
            )
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
                    description=f"### Instance Restarted\nSSH Session Command: ```{ssh_session_line}```\nOS: Ubuntu 22.04",
                    color=0x00ff00
                )
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="### Instance restarted successfully. Check your DMs for details.",
                    color=0x00ff00
                )
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="### Instance restarted, but failed to get SSH session line.",
                    color=0xff0000
                )
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error restarting instance: {e}",
                color=0xff0000
            )
        )

async def create_server_task(interaction):
    """
    Creates a new VPS instance by spinning up a Docker container.
    Executes the tmate command inside the container to generate the SSH session.
    Limits the user to a maximum number of instances.
    """
    await interaction.response.send_message(
        embed=discord.Embed(
            description="### Creating Instance, this may take a few seconds. Powered by [CrashOfGuys](https://discord.com/invite/VWm8zUEQN8)",
            color=0x00ff00
        )
    )
    userid = str(interaction.user.id)
    if count_user_servers(userid) >= SERVER_LIMIT:
        await interaction.followup.send(
            embed=discord.Embed(
                description="```Error: Instance Limit reached```",
                color=0xff0000
            )
        )
        return

    image = "ubuntu-22.04-with-tmate"
    try:
        container_id = subprocess.check_output([
           "docker", "run", "-itd", "--privileged", "--hostname", "crashcloud", "--cap-add=ALL", image
        ]).strip().decode('utf-8')
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"### Error creating Docker container: {e}",
                color=0xff0000
            )
        )
        return

    try:
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"### Error executing tmate in Docker container: {e}",
                color=0xff0000
            )
        )
        subprocess.run(["docker", "kill", container_id])
        subprocess.run(["docker", "rm", container_id])
        return

    ssh_session_line = await capture_ssh_session_line(exec_cmd)
    if ssh_session_line:
        await interaction.user.send(
            embed=discord.Embed(
                description=f"### Successfully created Instance\nSSH Session Command: ```{ssh_session_line}```\nOS: Ubuntu 22.04\nPassword: root",
                color=0x00ff00
            )
        )
        add_to_database(userid, container_id, ssh_session_line)
        await interaction.followup.send(
            embed=discord.Embed(
                description="### Instance created successfully. Check your DMs for details.",
                color=0x00ff00
            )
        )
    else:
        await interaction.followup.send(
            embed=discord.Embed(
                description="### Something went wrong or the Instance is taking longer than expected. Contact Support if the issue persists.",
                color=0xff0000
            )
        )
        subprocess.run(["docker", "kill", container_id])
        subprocess.run(["docker", "rm", container_id])

@bot.tree.command(name="deploy", description="Creates a new instance with Ubuntu 22.04.")
async def deploy_ubuntu(interaction: discord.Interaction):
    """
    Slash command that deploys a new Ubuntu 22.04-based VPS instance.
    """
    await create_server_task(interaction)

@bot.tree.command(name="regen-ssh", description="Generates a new SSH session for your instance.")
@app_commands.describe(container_name="The identifier (name or SSH command) of your instance")
async def regen_ssh(interaction: discord.Interaction, container_name: str):
    """
    Command to regenerate the SSH session command for an existing VPS.
    """
    await regen_ssh_command(interaction, container_name)

@bot.tree.command(name="start", description="Starts your instance.")
@app_commands.describe(container_name="The identifier (name or SSH command) of your instance")
async def start(interaction: discord.Interaction, container_name: str):
    """
    Command to start a paused or stopped VPS instance.
    """
    await start_server(interaction, container_name)

@bot.tree.command(name="stop", description="Stops your instance.")
@app_commands.describe(container_name="The identifier (name or SSH command) of your instance")
async def stop(interaction: discord.Interaction, container_name: str):
    """
    Command to stop a running VPS instance.
    """
    await stop_server(interaction, container_name)

@bot.tree.command(name="restart", description="Restarts your instance.")
@app_commands.describe(container_name="The identifier (name or SSH command) of your instance")
async def restart(interaction: discord.Interaction, container_name: str):
    """
    Command to restart a VPS instance and refresh its SSH session.
    """
    await restart_server(interaction, container_name)

@bot.tree.command(name="ping", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):
    """
    Command to check and display the bot's current latency.
    """
    await interaction.response.defer()
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {latency}ms",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="list", description="Lists all your instances.")
async def list_servers(interaction: discord.Interaction):
    """
    Retrieves and displays a list of all VPS instances deployed by the user.
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
                description="You have no servers.",
                color=0xff0000
            )
        )

@bot.tree.command(name="port-add", description="Adds a port forwarding rule.")
@app_commands.describe(container_name="The name of the container", container_port="The internal container port")
async def port_add(interaction: discord.Interaction, container_name: str, container_port: int):
    """
    Sets up a port forwarding rule by selecting a random public port.
    The container connects to serveo.net and the user is informed of the accessible address.
    """
    await interaction.response.send_message(
        embed=discord.Embed(
            description="### Setting up port forwarding. This might take a moment...",
            color=0x00ff00
        )
    )
    public_port = generate_random_port()
    try:
        if not _is_safe_container_name(container_name):
            await interaction.followup.send("Invalid container name.", ephemeral=True)
            return
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
                description=f"### Port added successfully. Your service is hosted on {PUBLIC_IP}:{public_port}.",
                color=0x00ff00
            )
        )
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                description="### An unexpected error occurred.",
                color=0xff0000
            )
        )

@bot.tree.command(name="port-http", description="Forward HTTP traffic to your container.")
@app_commands.describe(container_name="The name of your container", container_port="The internal container port to forward")
async def port_forward_website(interaction: discord.Interaction, container_name: str, container_port: int):
    """
    Forwards HTTP traffic to the specified container port using serveo.net.
    It extracts the forwarding URL from the command output for user reference.
    """
    try:
        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "ssh", "-o StrictHostKeyChecking=no",
            "-R", f"80:localhost:{container_port}", "serveo.net",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        url_line = await capture_output(exec_cmd, "Forwarding HTTP traffic from")
        if url_line:
            url = url_line.split(" ")[-1]
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"### Website forwarded successfully. Your website is accessible at {url}.",
                    color=0x00ff00
                )
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="### Failed to capture forwarding URL.",
                    color=0xff0000
                )
            )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"### Error executing website forwarding: {e}",
                color=0xff0000
            )
        )

@bot.tree.command(name="remove", description="Removes an instance.")
@app_commands.describe(container_name="The identifier (name or SSH command) of your instance")
async def remove_server(interaction: discord.Interaction, container_name: str):
    """
    Removes the specified VPS instance by stopping and deleting its Docker container.
    It also removes the instance record from the local database.
    """
    await interaction.response.defer()
    userid = str(interaction.user.id)
    container_id = get_container_id_from_database(userid, container_name)
    if not container_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="### No instance found for your user with that name.",
                color=0xff0000
            )
        )
        return

    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        subprocess.run(["docker", "rm", container_id], check=True)
        remove_from_database(container_id)
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Instance '{container_name}' removed successfully.",
                color=0x00ff00
            )
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Error removing instance: {e}",
                color=0xff0000
            )
        )

@bot.tree.command(name="help", description="Shows the help message.")
async def help_command(interaction: discord.Interaction):
    """
    Displays an embedded help message with details about available commands.
    """
    embed = discord.Embed(title="Help", color=0x00ff00)
    embed.add_field(name="/deploy", value="Creates a new instance with Ubuntu 22.04.", inline=False)
    embed.add_field(name="/remove <ssh_command/Name>", value="Removes a server.", inline=False)
    embed.add_field(name="/start <ssh_command/Name>", value="Starts a server.", inline=False)
    embed.add_field(name="/stop <ssh_command/Name>", value="Stops a server.", inline=False)
    embed.add_field(name="/regen-ssh <ssh_command/Name>", value="Regenerates SSH credentials.", inline=False)
    embed.add_field(name="/restart <ssh_command/Name>", value="Restarts a server.", inline=False)
    embed.add_field(name="/list", value="Lists all your servers.", inline=False)
    embed.add_field(name="/ping", value="Checks the bot's latency.", inline=False)
    embed.add_field(name="/node", value="Shows the node storage and memory usage.", inline=False)
    embed.add_field(name="/bal", value="Displays your current credit balance.", inline=False)
    embed.add_field(name="/renew", value="Renews your VPS.", inline=False)
    embed.add_field(name="/earncredit", value="Earn credits by shortening a URL.", inline=False)
    await interaction.response.send_message(embed=embed)

# -----------------------------------------------------------------------------
# Run the Bot
# -----------------------------------------------------------------------------

bot.run(TOKEN)
