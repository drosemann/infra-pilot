import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging
import json
import os
from typing import Optional

from config import config
from integration import get_db_connection
from vps_manager import VPSManager

DATA_FILE = "data/edge_nodes.json"


class EdgeCompute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.edge_nodes = {}
        self.load_nodes()
        self.edge_health_loop.start()

    def cog_unload(self):
        self.edge_health_loop.cancel()

    def load_nodes(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE) as f:
                    self.edge_nodes = json.load(f)
        except Exception as e:
            logging.error(f"Error loading edge nodes: {e}")
            self.edge_nodes = {}

    def save_nodes(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.edge_nodes, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving edge nodes: {e}")

    def _record_node_db(self, name: str, location: str, status: str):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO edge_nodes (name, location, status) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE status = VALUES(status), last_seen = NOW()",
                (name, location, status),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error recording edge node to DB: {e}")

    @tasks.loop(minutes=1)
    async def edge_health_loop(self):
        for name, info in list(self.edge_nodes.items()):
            try:
                container = self.vps_manager.client.containers.get(info.get("container_id", ""))
                container_state = container.status
                info["status"] = "online" if container_state == "running" else "offline"
                latency = None
                try:
                    exit_code, output = container.exec_run("cat /proc/uptime")
                    if exit_code == 0:
                        info["uptime_seconds"] = float(output.decode().split()[0])
                except Exception:
                    pass
                info["last_ping"] = datetime.now().isoformat()
            except Exception:
                info["status"] = "offline"
                info["last_ping"] = datetime.now().isoformat()
            self._record_node_db(name, info.get("location", ""), info.get("status", "offline"))
        self.save_nodes()

    @app_commands.command(name="edge", description="Edge compute node management")
    @app_commands.describe(
        action="register/nodes/deploy/functions/status",
        name="Node name",
        location="Geographic location",
        node="Existing node name (for deploy/status)",
        image="Container image to deploy",
    )
    async def edge(
        self,
        interaction: discord.Interaction,
        action: str,
        name: Optional[str] = None,
        location: Optional[str] = None,
        node: Optional[str] = None,
        image: Optional[str] = None,
    ):
        await interaction.response.defer()
        actions = {
            "register": self._register_node,
            "nodes": self._list_nodes,
            "deploy": self._deploy_to_node,
            "functions": self._list_functions,
            "status": self._node_status,
        }
        handler = actions.get(action)
        if not handler:
            embed = discord.Embed(description=f"Unknown action: {action}. Use register/nodes/deploy/functions/status", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        await handler(interaction, name, location, node, image)

    async def _register_node(self, interaction: discord.Interaction, name: Optional[str], location: Optional[str], node: Optional[str], image: Optional[str]):
        if not name or not location:
            embed = discord.Embed(description="Name and location are required", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        if name in self.edge_nodes:
            embed = discord.Embed(description=f"Node '{name}' already registered", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return

        self.edge_nodes[name] = {
            "name": name,
            "location": location,
            "status": "registered",
            "container_id": "",
            "functions": [],
            "registered_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat(),
        }
        self.save_nodes()
        self._record_node_db(name, location, "registered")
        embed = discord.Embed(description=f"Edge node '{name}' registered at {location}", color=discord.Color.green())
        embed.add_field(name="Location", value=location)
        embed.add_field(name="Status", value="registered")
        await interaction.followup.send(embed=embed)

    async def _list_nodes(self, interaction: discord.Interaction, name: Optional[str], location: Optional[str], node: Optional[str], image: Optional[str]):
        if not self.edge_nodes:
            embed = discord.Embed(description="No edge nodes registered", color=0xFFFF00)
            await interaction.followup.send(embed=embed)
            return
        embed = discord.Embed(title="Edge Compute Nodes", color=discord.Color.blue(), timestamp=datetime.now())
        for nname, info in self.edge_nodes.items():
            status_emoji = "🟢" if info.get("status") == "online" else "🟡" if info.get("status") == "registered" else "🔴"
            embed.add_field(
                name=nname,
                value=(
                    f"Status: {status_emoji} {info.get('status', 'unknown')}\n"
                    f"Location: {info.get('location', 'N/A')}\n"
                    f"Functions: {len(info.get('functions', []))}\n"
                    f"Last Ping: {info.get('last_ping', 'N/A')[:19]}"
                ),
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    async def _deploy_to_node(self, interaction: discord.Interaction, name: Optional[str], location: Optional[str], node: Optional[str], image: Optional[str]):
        if not node or node not in self.edge_nodes:
            embed = discord.Embed(description="Node not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        if not image:
            embed = discord.Embed(description="Image name is required", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        try:
            info = self.edge_nodes[node]
            container = self.vps_manager.client.containers.run(
                image=image,
                detach=True,
                name=f"edge-{node}-{image.replace('/', '-').replace(':', '-')}",
                restart_policy={"Name": "unless-stopped"},
            )
            func_entry = {
                "function_id": container.id,
                "image": image,
                "deployed_at": datetime.now().isoformat(),
                "status": "running",
            }
            info.setdefault("functions", []).append(func_entry)
            info["container_id"] = container.id
            info["status"] = "online"
            self.save_nodes()
            embed = discord.Embed(description=f"Deployed {image} to node '{node}'", color=discord.Color.green())
            embed.add_field(name="Container ID", value=container.id[:12])
            embed.add_field(name="Image", value=image)
            embed.add_field(name="Node", value=node)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Deploy failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _list_functions(self, interaction: discord.Interaction, name: Optional[str], location: Optional[str], node: Optional[str], image: Optional[str]):
        functions = []
        for nname, info in self.edge_nodes.items():
            for fn in info.get("functions", []):
                fn["node"] = nname
                functions.append(fn)
        if not functions:
            embed = discord.Embed(description="No functions deployed to edge nodes", color=0xFFFF00)
            await interaction.followup.send(embed=embed)
            return
        embed = discord.Embed(title="Edge Functions", color=discord.Color.blue(), timestamp=datetime.now())
        for fn in functions[-10:]:
            embed.add_field(
                name=f"{fn.get('image', 'unknown')} @ {fn.get('node', '?')}",
                value=(
                    f"Status: {fn.get('status', 'unknown')}\n"
                    f"ID: `{fn.get('function_id', '')[:12]}`\n"
                    f"Deployed: {fn.get('deployed_at', 'N/A')[:19]}"
                ),
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    async def _node_status(self, interaction: discord.Interaction, name: Optional[str], location: Optional[str], node: Optional[str], image: Optional[str]):
        if not node or node not in self.edge_nodes:
            embed = discord.Embed(description="Node not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        info = self.edge_nodes[node]
        embed = discord.Embed(title=f"Edge Node: {node}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Location", value=info.get("location", "N/A"), inline=True)
        embed.add_field(name="Status", value=info.get("status", "unknown"), inline=True)
        embed.add_field(name="Functions", value=str(len(info.get("functions", []))), inline=True)
        embed.add_field(name="Last Ping", value=info.get("last_ping", "N/A")[:19], inline=True)
        embed.add_field(name="Registered", value=info.get("registered_at", "N/A")[:19], inline=True)
        if info.get("uptime_seconds"):
            embed.add_field(name="Uptime", value=f"{int(info['uptime_seconds'] / 60)} min", inline=True)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EdgeCompute(bot))
