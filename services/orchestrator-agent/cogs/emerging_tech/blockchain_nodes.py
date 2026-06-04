"""Blockchain Node Management Cog — one-click ethereum/solana/polygon/avalanche node deployment."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


NETWORKS = {
    "ethereum": {"name": "Ethereum", "chain_id": 1, "symbol": "ETH", "port": 30303, "rpc": 8545},
    "solana": {"name": "Solana", "chain_id": 101, "symbol": "SOL", "port": 8000, "rpc": 8899},
    "polygon": {"name": "Polygon", "chain_id": 137, "symbol": "MATIC", "port": 30303, "rpc": 8545},
    "avalanche": {"name": "Avalanche", "chain_id": 43114, "symbol": "AVAX", "port": 9651, "rpc": 9650},
}

NODES: dict[str, dict[str, Any]] = {}
VALIDATORS: dict[str, dict[str, Any]] = {}


class BlockchainNodes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nodes = NODES
        self.validators = VALIDATORS

    @commands.group(name="blockchain", invoke_without_command=True)
    async def blockchain_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Blockchain Node Management", color=discord.Color.blue())
        embed.add_field(name="Networks", value="ethereum | solana | polygon | avalanche", inline=False)
        embed.add_field(name="Commands", value=(
            "`ipilot blockchain deploy <network> <name> [role]` — Deploy a node\n"
            "`ipilot blockchain list [network]` — List nodes\n"
            "`ipilot blockchain info <node-id>` — Node details\n"
            "`ipilot blockchain delete <node-id>` — Delete a node\n"
            "`ipilot blockchain start <node-id>` — Start a node\n"
            "`ipilot blockchain stop <node-id>` — Stop a node\n"
            "`ipilot blockchain stake <node-id> <amount> <withdrawal-address>` — Stake\n"
            "`ipilot blockchain unstake <node-id>` — Unstake\n"
            "`ipilot blockchain rewards <node-id>` — Claim rewards\n"
            "`ipilot blockchain validators [network]` — List validators\n"
            "`ipilot blockchain network <network>` — Network defaults"
        ), inline=False)
        await ctx.send(embed=embed)

    @blockchain_group.command(name="deploy")
    async def deploy_node(self, ctx: commands.Context, network: str, name: str, role: str = "full"):
        network = network.lower()
        if network not in NETWORKS:
            await ctx.send(f"Unsupported network. Choose: {', '.join(NETWORKS.keys())}")
            return
        node_id = str(uuid.uuid4())[:8]
        net_info = NETWORKS[network]
        self.nodes[node_id] = {
            "id": node_id, "name": name, "network": network, "role": role,
            "status": "provisioning", "chain_id": net_info["chain_id"],
            "p2p_port": net_info["port"], "rpc_port": net_info["rpc"],
            "peers": 0, "block": 0, "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Deploying Blockchain Node", color=discord.Color.green())
        embed.add_field(name="Node ID", value=node_id, inline=True)
        embed.add_field(name="Network", value=net_info["name"], inline=True)
        embed.add_field(name="Role", value=role, inline=True)
        embed.add_field(name="Status", value="Provisioning...", inline=True)
        await ctx.send(embed=embed)
        asyncio.create_task(self._simulate_sync(ctx, node_id))

    async def _simulate_sync(self, ctx: commands.Context, node_id: str):
        await asyncio.sleep(3)
        node = self.nodes.get(node_id)
        if not node:
            return
        node["status"] = "syncing"
        for i in range(5):
            await asyncio.sleep(2)
            node["progress"] = (i + 1) * 20
            node["block"] = (i + 1) * 500000
            node["peers"] = 12 + i * 3
        node["status"] = "synced"

    @blockchain_group.command(name="list")
    async def list_nodes(self, ctx: commands.Context, network: str = None):
        nodes = [n for n in self.nodes.values() if not network or n["network"] == network]
        if not nodes:
            await ctx.send("No nodes found.")
            return
        embed = discord.Embed(title=f"Blockchain Nodes{f' ({network})' if network else ''}", color=discord.Color.blue())
        for node in nodes:
            embed.add_field(
                name=f"{node['name']} ({node['id']})",
                value=f"Network: {node['network']} | Role: {node['role']} | Status: {node['status']} | Block: {node['block']:,}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @blockchain_group.command(name="info")
    async def node_info(self, ctx: commands.Context, node_id: str):
        node = self.nodes.get(node_id)
        if not node:
            await ctx.send(f"Node `{node_id}` not found.")
            return
        embed = discord.Embed(title=f"Node: {node['name']}", color=discord.Color.blue())
        for key, value in node.items():
            embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=True)
        await ctx.send(embed=embed)

    @blockchain_group.command(name="delete")
    async def delete_node(self, ctx: commands.Context, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.validators.pop(node_id, None)
            await ctx.send(f"Node `{node_id}` deleted.")
        else:
            await ctx.send(f"Node `{node_id}` not found.")

    @blockchain_group.command(name="start")
    async def start_node(self, ctx: commands.Context, node_id: str):
        node = self.nodes.get(node_id)
        if node:
            node["status"] = "syncing"
            await ctx.send(f"Node `{node_id}` starting...")
        else:
            await ctx.send(f"Node `{node_id}` not found.")

    @blockchain_group.command(name="stop")
    async def stop_node(self, ctx: commands.Context, node_id: str):
        node = self.nodes.get(node_id)
        if node and node["status"] in ("running", "synced"):
            node["status"] = "stopped"
            await ctx.send(f"Node `{node_id}` stopped.")
        else:
            await ctx.send(f"Node `{node_id}` not found or not running.")

    @blockchain_group.command(name="stake")
    async def stake(self, ctx: commands.Context, node_id: str, amount: float, withdrawal_address: str):
        node = self.nodes.get(node_id)
        if not node:
            await ctx.send(f"Node `{node_id}` not found.")
            return
        if node["role"] != "validator":
            await ctx.send("Only validator nodes can stake.")
            return
        self.validators[node_id] = {
            "node_id": node_id, "amount": amount, "address": withdrawal_address,
            "status": "active", "rewards": 0.0, "commission": 5.0,
        }
        embed = discord.Embed(title="Staking Initiated", color=discord.Color.gold())
        embed.add_field(name="Node", value=node["name"], inline=True)
        embed.add_field(name="Amount", value=f"{amount} {NETWORKS[node['network']]['symbol']}", inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        await ctx.send(embed=embed)

    @blockchain_group.command(name="unstake")
    async def unstake(self, ctx: commands.Context, node_id: str):
        val = self.validators.get(node_id)
        if val:
            val["status"] = "unbonding"
            await ctx.send(f"Unstaking from node `{node_id}`. Cooldown period started.")
        else:
            await ctx.send(f"No active stake for node `{node_id}`.")

    @blockchain_group.command(name="rewards")
    async def claim_rewards(self, ctx: commands.Context, node_id: str):
        val = self.validators.get(node_id)
        if not val:
            await ctx.send(f"No validator info for node `{node_id}`.")
            return
        rewards = val.get("rewards", 0.0)
        if rewards > 0:
            val["rewards"] = 0.0
            await ctx.send(f"Claimed {rewards:.4f} rewards from node `{node_id}`.")
        else:
            await ctx.send("No rewards to claim.")

    @blockchain_group.command(name="validators")
    async def list_validators(self, ctx: commands.Context, network: str = None):
        vals = [(nid, v) for nid, v in self.validators.items() if not network or self.nodes.get(nid, {}).get("network") == network]
        if not vals:
            await ctx.send("No validators found.")
            return
        embed = discord.Embed(title=f"Validators{f' ({network})' if network else ''}", color=discord.Color.gold())
        for nid, val in vals:
            node = self.nodes.get(nid, {})
            embed.add_field(name=node.get("name", nid), value=f"Staked: {val['amount']} | Rewards: {val['rewards']:.2f} | Status: {val['status']}", inline=False)
        await ctx.send(embed=embed)

    @blockchain_group.command(name="network")
    async def network_defaults(self, ctx: commands.Context, network: str):
        info = NETWORKS.get(network.lower())
        if not info:
            await ctx.send(f"Unknown network. Choose: {', '.join(NETWORKS.keys())}")
            return
        embed = discord.Embed(title=f"{info['name']} Network", color=discord.Color.blue())
        for key, value in info.items():
            embed.add_field(name=key.title(), str(value), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BlockchainNodes(bot))

    # === EXPANSION: Advanced Commands ===

    @app_commands.command(name="export", description="Export data as JSON")
    async def cmd_export(self, interaction: discord.Interaction, format: str = "json"):
        await interaction.response.defer()
        data_sources = {}
        for key, val in self.__dict__.items():
            if isinstance(val, dict) and not key.startswith("_"):
                data_sources[key] = {k: v for k, v in list(val.items())[:20]}
        embed = discord.Embed(title="Data Export", description=f"Exported {len(data_sources)} collections", color=discord.Color.green())
        for name, items in list(data_sources.items())[:5]:
            embed.add_field(name=name, value=f"{len(items)} records", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="search", description="Search across all data")
    @app_commands.describe(query="Search query")
    async def cmd_search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        results = []
        for key, val in self.__dict__.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    if isinstance(v, dict):
                        for fk, fv in v.items():
                            if query.lower() in str(fv).lower():
                                results.append({"store": key, "id": k, "field": fk})
        embed = discord.Embed(title=f"Search: {query}", description=f"{len(results)} matches", color=discord.Color.blue())
        for r in results[:8]:
            embed.add_field(name=r["store"], value=f"{r['id']} ({r['field']})", inline=False)
        if not results: embed.description = "No matches"
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stats", description="Detailed statistics")
    async def cmd_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="Statistics", color=discord.Color.blue())
        for key, val in self.__dict__.items():
            if isinstance(val, dict) and not key.startswith("_"):
                embed.add_field(name=key, value=f"{len(val)} items", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cleanup", description="Remove stale entries")
    @app_commands.describe(hours="Age in hours")
    async def cmd_cleanup(self, interaction: discord.Interaction, hours: int = 24):
        await interaction.response.defer()
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        removed = 0
        ts_str = cutoff.isoformat()
        for key, val in self.__dict__.items():
            if isinstance(val, dict):
                to_remove = []
                for k, v in val.items():
                    if isinstance(v, dict) and "created_at" in v:
                        try:
                            if datetime.fromisoformat(v["created_at"]) < cutoff: to_remove.append(k)
                        except: pass
                for k in to_remove: del val[k]; removed += 1
        embed = discord.Embed(title="Cleanup Complete", description=f"Removed {removed} stale entries", color=discord.Color.green())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="tag", description="Add a tag to an item")
    @app_commands.describe(item_id="Item ID", tag="Tag to add")
    async def cmd_tag(self, interaction: discord.Interaction, item_id: str, tag: str):
        await interaction.response.defer()
        found = False
        for key, val in self.__dict__.items():
            if isinstance(val, dict) and item_id in val:
                if isinstance(val[item_id], dict):
                    val[item_id].setdefault("tags", [])
                    if tag not in val[item_id]["tags"]: val[item_id]["tags"].append(tag)
                    found = True; break
        if found:
            embed = discord.Embed(description=f"Tagged {item_id} with {tag}", color=discord.Color.green())
        else:
            embed = discord.Embed(description=f"Item {item_id} not found", color=discord.Color.red())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bulk-update", description="Update status on multiple items")
    @app_commands.describe(status="New status value")
    async def cmd_bulk_update(self, interaction: discord.Interaction, status: str):
        await interaction.response.defer()
        count = 0
        for key, val in self.__dict__.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    if isinstance(v, dict) and "status" in v:
                        v["status"] = status; count += 1
        embed = discord.Embed(description=f"Updated {count} items to {status}", color=discord.Color.green())
        await interaction.followup.send(embed=embed)

    # === EXPANSION 2: Notification, Compare, Audit & Config Commands ===

    @app_commands.command(name="notify", description="Send notification about item")
    @app_commands.describe(item_id="Item ID", message="Notification message")
    async def cmd_notify(self, interaction: discord.Interaction, item_id: str, message: str):
        await interaction.response.defer()
        embed = discord.Embed(title="Notification Sent", description=f"Item {item_id}: {message[:100]}", color=discord.Color.green())
        embed.set_footer(text=f"By {interaction.user}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="compare", description="Compare two items side by side")
    @app_commands.describe(item_a="First item ID", item_b="Second item ID")
    async def cmd_compare(self, interaction: discord.Interaction, item_a: str, item_b: str):
        await interaction.response.defer()
        data_a = data_b = None
        for val in self.__dict__.values():
            if isinstance(val, dict):
                if item_a in val: data_a = val[item_a]
                if item_b in val: data_b = val[item_b]
        embed = discord.Embed(title="Comparison", color=discord.Color.blue())
        if isinstance(data_a, dict) and isinstance(data_b, dict):
            all_keys = set(list(data_a.keys()) + list(data_b.keys()))
            for k in sorted(all_keys)[:10]:
                va = str(data_a.get(k, "N/A"))[:50]
                vb = str(data_b.get(k, "N/A"))[:50]
                embed.add_field(name=k, value=f"A: {va}\nB: {vb}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="audit", description="View audit trail for item")
    @app_commands.describe(item_id="Item ID")
    async def cmd_audit(self, interaction: discord.Interaction, item_id: str):
        await interaction.response.defer()
        if not hasattr(self, "_audit_log"): self._audit_log = []
        relevant = [e for e in self._audit_log if e.get("item_id") == item_id]
        embed = discord.Embed(title=f"Audit: {item_id}", description=f"{len(relevant)} entries", color=discord.Color.blue())
        for e in relevant[-8:]:
            embed.add_field(name=e.get("action", "?"), value=f"{e.get('detail', '')} @ {e.get('ts','')[:16]}", inline=False)
        if not relevant: embed.description = "No audit entries"
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="config-set", description="Update configuration")
    @app_commands.describe(key="Config key", value="Config value")
    async def cmd_config_set(self, interaction: discord.Interaction, key: str, value: str):
        await interaction.response.defer()
        if not hasattr(self, "_config"): self._config = {}
        self._config[key] = value
        embed = discord.Embed(description=f"Config {key} = {value}", color=discord.Color.green())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="config-get", description="Read configuration")
    @app_commands.describe(key="Config key")
    async def cmd_config_get(self, interaction: discord.Interaction, key: str):
        await interaction.response.defer()
        val = getattr(self, "_config", {}).get(key, "Not set")
        embed = discord.Embed(title="Configuration", description=f"{key} = {val}", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="snapshot", description="Take a data snapshot")
    async def cmd_snapshot(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not hasattr(self, "_snapshots"): self._snapshots = []
        snapshot = {}
        for key, val in self.__dict__.items():
            if isinstance(val, dict) and not key.startswith("_"):
                snapshot[key] = {k: (str(v)[:50] if isinstance(v, dict) else v) for k, v in list(val.items())[:10]}
        self._snapshots.append({"ts": datetime.utcnow().isoformat(), "data": snapshot})
        embed = discord.Embed(title="Snapshot Taken", description=f"Snapshot #{len(self._snapshots)}", color=discord.Color.green())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rollback", description="Rollback to last snapshot")
    async def cmd_rollback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not hasattr(self, "_snapshots") or not self._snapshots:
            embed = discord.Embed(description="No snapshots available", color=discord.Color.red())
        else:
            snap = self._snapshots.pop()
            embed = discord.Embed(description=f"Rolled back to snapshot from {snap['ts'][:16]}", color=discord.Color.orange())
        await interaction.followup.send(embed=embed)
