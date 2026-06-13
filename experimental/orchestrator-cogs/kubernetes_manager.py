import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import logging
import json
import os
import subprocess
from typing import Optional

from config import config
from integration import get_db_connection
from vps_manager import VPSManager

DATA_FILE = "data/k8s_clusters.json"


class KubernetesManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.clusters = {}
        self.load_clusters()
        self.check_kubectl_helm()
        self.cluster_health_loop.start()

    def cog_unload(self):
        self.cluster_health_loop.cancel()

    def check_kubectl_helm(self):
        for binary in ("kubectl", "helm"):
            try:
                subprocess.run([binary, "version", "--client"], capture_output=True, timeout=5)
            except (FileNotFoundError, subprocess.SubprocessError):
                logging.warning(f"{binary} binary not found — K8s features limited")

    def load_clusters(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE) as f:
                    self.clusters = json.load(f)
        except Exception as e:
            logging.error(f"Error loading K8s clusters: {e}")
            self.clusters = {}

    def save_clusters(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.clusters, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving K8s clusters: {e}")

    def _record_cluster_db(self, name: str, status: str, node_count: int, type_: str):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO k8s_clusters (name, status, node_count, type) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE status = VALUES(status), node_count = VALUES(node_count), updated_at = NOW()",
                (name, status, node_count, type_),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Error recording K8s cluster to DB: {e}")

    @tasks.loop(minutes=5)
    async def cluster_health_loop(self):
        for name, info in self.clusters.items():
            try:
                result = subprocess.run(
                    ["kubectl", "get", "nodes", "--kubeconfig", info.get("kubeconfig", "")],
                    capture_output=True, text=True, timeout=15,
                )
                info["status"] = "healthy" if result.returncode == 0 else "degraded"
                info["last_checked"] = datetime.now().isoformat()
                self._record_cluster_db(name, info["status"], info.get("node_count", 0), info.get("type", "k3s"))
            except Exception as e:
                logging.error(f"Health check failed for cluster {name}: {e}")
        self.save_clusters()

    @app_commands.command(name="k8s", description="Kubernetes cluster management")
    @app_commands.describe(
        action="create/delete/list/status/nodes/deploy/proxy",
        name="Cluster name",
        chart="Helm chart to deploy (for deploy action)",
        repo="Helm chart repo URL (optional)",
    )
    async def k8s(
        self,
        interaction: discord.Interaction,
        action: str,
        name: Optional[str] = None,
        chart: Optional[str] = None,
        repo: Optional[str] = None,
    ):
        await interaction.response.defer()
        actions = {
            "create": self._create_cluster,
            "delete": self._delete_cluster,
            "list": self._list_clusters,
            "nodes": self._list_nodes,
            "deploy": self._deploy_chart,
            "proxy": self._proxy_cluster,
        }
        handler = actions.get(action)
        if not handler:
            embed = discord.Embed(description=f"Unknown action: {action}. Use create/delete/list/nodes/deploy/proxy", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        await handler(interaction, name, chart, repo)

    async def _create_cluster(self, interaction: discord.Interaction, name: Optional[str], chart: Optional[str], repo: Optional[str]):
        if not name:
            embed = discord.Embed(description="Cluster name is required", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        if name in self.clusters:
            embed = discord.Embed(description=f"Cluster '{name}' already exists", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return

        try:
            container = self.vps_manager.client.containers.run(
                image="rancher/k3s:latest",
                detach=True,
                name=f"k3s-{name}",
                environment={"K3S_KUBECONFIG_MODE": "644"},
                privileged=True,
                restart_policy={"Name": "unless-stopped"},
            )
            self.clusters[name] = {
                "name": name,
                "container_id": container.id,
                "type": "k3s",
                "status": "starting",
                "node_count": 1,
                "created_at": datetime.now().isoformat(),
                "last_checked": datetime.now().isoformat(),
                "kubeconfig": "",
            }
            self.save_clusters()
            self._record_cluster_db(name, "starting", 1, "k3s")
            embed = discord.Embed(title="K8s Cluster Created", description=f"Cluster '{name}' deployed via K3s", color=discord.Color.green())
            embed.add_field(name="Container ID", value=container.id[:12])
            embed.add_field(name="Type", value="k3s")
            embed.add_field(name="Nodes", value="1")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Failed to create cluster: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _delete_cluster(self, interaction: discord.Interaction, name: Optional[str], chart: Optional[str], repo: Optional[str]):
        if not name or name not in self.clusters:
            embed = discord.Embed(description="Cluster not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        try:
            info = self.clusters[name]
            if info.get("container_id"):
                container = self.vps_manager.client.containers.get(info["container_id"])
                container.stop()
                container.remove()
            del self.clusters[name]
            self.save_clusters()
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM k8s_clusters WHERE name = %s", (name,))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                pass
            embed = discord.Embed(description=f"Cluster '{name}' deleted", color=discord.Color.green())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Failed to delete cluster: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _list_clusters(self, interaction: discord.Interaction, name: Optional[str], chart: Optional[str], repo: Optional[str]):
        if not self.clusters:
            embed = discord.Embed(description="No clusters", color=0xFFFF00)
            await interaction.followup.send(embed=embed)
            return
        embed = discord.Embed(title="K8s Clusters", color=discord.Color.blue(), timestamp=datetime.now())
        for cname, info in self.clusters.items():
            status_emoji = "🟢" if info.get("status") == "healthy" else "🟡" if info.get("status") == "starting" else "🔴"
            embed.add_field(
                name=cname,
                value=(
                    f"Status: {status_emoji} {info.get('status', 'unknown')}\n"
                    f"Type: {info.get('type', 'k3s')}\n"
                    f"Nodes: {info.get('node_count', 0)}\n"
                    f"Created: {info.get('created_at', 'N/A')[:19]}"
                ),
                inline=False,
            )
        await interaction.followup.send(embed=embed)

    async def _list_nodes(self, interaction: discord.Interaction, name: Optional[str], chart: Optional[str], repo: Optional[str]):
        if not name or name not in self.clusters:
            embed = discord.Embed(description="Cluster not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        info = self.clusters[name]
        kubeconfig = info.get("kubeconfig", "")
        try:
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "wide", "--kubeconfig", kubeconfig],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                embed = discord.Embed(description=f"Failed to list nodes: {result.stderr}", color=0xFF0000)
                await interaction.followup.send(embed=embed)
                return
            embed = discord.Embed(title=f"Nodes: {name}", color=discord.Color.blue(), timestamp=datetime.now())
            embed.description = f"```\n{result.stdout[:1900]}\n```"
            await interaction.followup.send(embed=embed)
        except FileNotFoundError:
            embed = discord.Embed(description="kubectl not installed on host", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _deploy_chart(self, interaction: discord.Interaction, name: Optional[str], chart: Optional[str], repo: Optional[str]):
        if not name or name not in self.clusters:
            embed = discord.Embed(description="Cluster not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        if not chart:
            embed = discord.Embed(description="Chart name is required", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        info = self.clusters[name]
        kubeconfig = info.get("kubeconfig", "")
        try:
            if repo:
                subprocess.run(
                    ["helm", "repo", "add", f"{name}-repo", repo, "--kubeconfig", kubeconfig],
                    capture_output=True, timeout=30,
                )
            result = subprocess.run(
                ["helm", "upgrade", "--install", chart, chart, "--kubeconfig", kubeconfig],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                embed = discord.Embed(description=f"Helm deploy failed: {result.stderr[:500]}", color=0xFF0000)
                await interaction.followup.send(embed=embed)
                return
            embed = discord.Embed(description=f"Chart '{chart}' deployed to cluster '{name}'", color=discord.Color.green())
            embed.add_field(name="Release", value=chart)
            await interaction.followup.send(embed=embed)
        except FileNotFoundError:
            embed = discord.Embed(description="helm not installed on host", color=0xFF0000)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Deploy failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)

    async def _proxy_cluster(self, interaction: discord.Interaction, name: Optional[str], chart: Optional[str], repo: Optional[str]):
        if not name or name not in self.clusters:
            embed = discord.Embed(description="Cluster not found", color=0xFF0000)
            await interaction.followup.send(embed=embed)
            return
        info = self.clusters[name]
        kubeconfig = info.get("kubeconfig", "")
        try:
            proc = subprocess.Popen(
                ["kubectl", "proxy", "--kubeconfig", kubeconfig, "--port", "0"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            embed = discord.Embed(description=f"Proxy started for cluster '{name}'", color=discord.Color.green())
            embed.add_field(name="PID", value=str(proc.pid))
            embed.add_field(name="Note", value="Proxy runs until bot restart or manual kill")
            await interaction.followup.send(embed=embed)
        except FileNotFoundError:
            embed = discord.Embed(description="kubectl not installed on host", color=0xFF0000)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"Proxy failed: {str(e)}", color=0xFF0000)
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(KubernetesManager(bot))
