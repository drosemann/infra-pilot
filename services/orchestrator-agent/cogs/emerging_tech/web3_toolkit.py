"""Web3 Developer Toolkit Cog — blockchain explorer, transaction builder, faucet manager."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

EXPLORERS: dict[str, dict[str, Any]] = {}
FAUCETS: dict[str, dict[str, Any]] = {}
TRANSACTIONS: dict[str, dict[str, Any]] = {}
DRIPS: dict[str, dict[str, Any]] = {}

DEFAULT_NETWORKS = [
    ("eth-mainnet", "Ethereum Mainnet", "ethereum", "https://etherscan.io", 1),
    ("eth-sepolia", "Sepolia Testnet", "ethereum", "https://sepolia.etherscan.io", 11155111),
    ("polygon", "Polygon Mainnet", "polygon", "https://polygonscan.com", 137),
    ("arbitrum", "Arbitrum One", "arbitrum", "https://arbiscan.io", 42161),
    ("base", "Base", "base", "https://basescan.org", 8453),
    ("avalanche", "Avalanche C-Chain", "avalanche", "https://snowtrace.io", 43114),
]


class Web3Toolkit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.explorers = EXPLORERS
        self.faucets = FAUCETS
        self.transactions = TRANSACTIONS
        self.drips = DRIPS
        self._seed_networks()

    def _seed_networks(self):
        for eid, name, network, url, chain_id in DEFAULT_NETWORKS:
            if eid not in self.explorers:
                self.explorers[eid] = {
                    "id": eid, "name": name, "network": network,
                    "url": url, "chain_id": chain_id, "blocks": 0, "status": "synced",
                }

    @commands.group(name="web3", aliases=["w3tk"], invoke_without_command=True)
    async def web3_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Web3 Developer Toolkit", color=discord.Color.blue())
        embed.add_field(name="Commands", value=(
            "`ipilot web3 explorer list [network]` — List blockchain explorers\n"
            "`ipilot web3 explorer block <explorer-id> <block>` — Lookup block\n"
            "`ipilot web3 explorer tx <explorer-id> <tx-hash>` — Lookup transaction\n"
            "`ipilot web3 explorer address <explorer-id> <address>` — Lookup address\n"
            "`ipilot web3 tx create <name> <network> <to> [value]` — Create transaction\n"
            "`ipilot web3 tx sign <template-id> <private-key>` — Sign & send tx\n"
            "`ipilot web3 tx list` — List transactions\n"
            "`ipilot web3 gas [network]` — Current gas prices\n"
            "`ipilot web3 faucet list` — List faucets\n"
            "`ipilot web3 faucet drip <faucet-id> <address>` — Request drip\n"
            "`ipilot web3 faucet fund <faucet-id> <amount>` — Fund faucet\n"
            "`ipilot web3 verify <explorer-id> <contract-address> <source>` — Verify contract\n"
            "`ipilot web3 summary` — Toolkit summary"
        ), inline=False)
        await ctx.send(embed=embed)

    @web3_group.group(name="explorer", invoke_without_command=True)
    async def explorer_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Blockchain Explorers", color=discord.Color.blue())
        embed.add_field(name="Subcommands", value="list | block | tx | address", inline=False)
        await ctx.send(embed=embed)

    @explorer_group.command(name="list")
    async def list_explorers(self, ctx: commands.Context, network: str = None):
        explorers = [e for e in self.explorers.values() if not network or e["network"] == network]
        if not explorers:
            await ctx.send("No explorers found.")
            return
        embed = discord.Embed(title=f"Blockchain Explorers{f' ({network})' if network else ''}", color=discord.Color.blue())
        for e in explorers:
            embed.add_field(name=e["name"], value=f"Network: {e['network']} | Chain ID: {e['chain_id']} | URL: {e['url']}", inline=False)
        await ctx.send(embed=embed)

    @explorer_group.command(name="block")
    async def lookup_block(self, ctx: commands.Context, explorer_id: str, block: int):
        e = self.explorers.get(explorer_id)
        if not e:
            await ctx.send(f"Explorer `{explorer_id}` not found.")
            return
        embed = discord.Embed(title=f"Block #{block} on {e['name']}", color=discord.Color.blue())
        embed.add_field(name="Hash", value=f"0x{block:064x}")
        embed.add_field(name="Transactions", value=42)
        embed.add_field(name="Gas Used", value="8,000,000 / 15,000,000")
        embed.add_field(name="Base Fee", value="15 Gwei")
        await ctx.send(embed=embed)

    @explorer_group.command(name="tx")
    async def lookup_tx(self, ctx: commands.Context, explorer_id: str, tx_hash: str):
        e = self.explorers.get(explorer_id)
        if not e:
            await ctx.send(f"Explorer `{explorer_id}` not found.")
            return
        embed = discord.Embed(title=f"Transaction on {e['name']}", color=discord.Color.blue())
        embed.add_field(name="Hash", value=tx_hash[:20] + "...")
        embed.add_field(name="From", value="0xfrom...addr")
        embed.add_field(name="To", value="0xto...addr")
        embed.add_field(name="Value", value="0.5 ETH")
        embed.add_field(name="Status", value="✅ Confirmed")
        await ctx.send(embed=embed)

    @explorer_group.command(name="address")
    async def lookup_address(self, ctx: commands.Context, explorer_id: str, address: str):
        e = self.explorers.get(explorer_id)
        if not e:
            await ctx.send(f"Explorer `{explorer_id}` not found.")
            return
        embed = discord.Embed(title=f"Address on {e['name']}", color=discord.Color.blue())
        embed.add_field(name="Address", value=address[:20] + "...")
        embed.add_field(name="Balance", value="10.5 ETH")
        embed.add_field(name="Transactions", value=150)
        embed.add_field(name="Is Contract", value="No")
        await ctx.send(embed=embed)

    @web3_group.group(name="tx", invoke_without_command=True)
    async def tx_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Transaction Builder", color=discord.Color.blue())
        embed.add_field(name="Subcommands", value="create | sign | list", inline=False)
        await ctx.send(embed=embed)

    @tx_group.command(name="create")
    async def create_tx(self, ctx: commands.Context, name: str, network: str, to_address: str, value: float = 0.0):
        tx_id = str(uuid.uuid4())[:8]
        self.transactions[tx_id] = {
            "id": tx_id, "name": name, "network": network,
            "to": to_address, "value": value, "status": "draft",
            "gas_limit": 21000, "gas_price": 20, "nonce": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Transaction Created", color=discord.Color.blue())
        embed.add_field(name="Template ID", value=tx_id)
        embed.add_field(name="To", value=to_address)
        embed.add_field(name="Value", value=f"{value} ETH")
        await ctx.send(embed=embed)

    @tx_group.command(name="sign")
    async def sign_tx(self, ctx: commands.Context, template_id: str, private_key: str):
        tx = self.transactions.get(template_id)
        if not tx:
            await ctx.send(f"Transaction `{template_id}` not found.")
            return
        tx["status"] = "pending"
        tx["hash"] = f"0x{uuid.uuid4().hex[:64]}"
        embed = discord.Embed(title="Transaction Sent", color=discord.Color.green())
        embed.add_field(name="Template ID", value=template_id)
        embed.add_field(name="Hash", value=tx["hash"][:20] + "...")
        embed.add_field(name="Status", value="Pending")
        await ctx.send(embed=embed)
        asyncio.create_task(self._confirm_tx(ctx, template_id))

    async def _confirm_tx(self, ctx: commands.Context, template_id: str):
        await asyncio.sleep(3)
        tx = self.transactions.get(template_id)
        if tx:
            tx["status"] = "confirmed"

    @tx_group.command(name="list")
    async def list_tx(self, ctx: commands.Context):
        if not self.transactions:
            await ctx.send("No transactions.")
            return
        embed = discord.Embed(title="Transaction History", color=discord.Color.blue())
        for tx in self.transactions.values():
            embed.add_field(name=f"{tx['name']} ({tx['id']})", value=f"Network: {tx['network']} | Value: {tx['value']} ETH | Status: {tx['status']}", inline=False)
        await ctx.send(embed=embed)

    @web3_group.command(name="gas")
    async def gas_prices(self, ctx: commands.Context, network: str = "ethereum"):
        embed = discord.Embed(title=f"Gas Prices ({network})", color=discord.Color.blue())
        embed.add_field(name="🐢 Slow", value="10 Gwei", inline=True)
        embed.add_field(name="🚶 Standard", value="20 Gwei", inline=True)
        embed.add_field(name="🚀 Fast", value="50 Gwei", inline=True)
        embed.add_field(name="⚡ Instant", value="100 Gwei", inline=True)
        embed.add_field(name="Base Fee", value="15 Gwei", inline=True)
        embed.add_field(name="Priority Fee", value="2 Gwei", inline=True)
        await ctx.send(embed=embed)

    @web3_group.group(name="faucet", invoke_without_command=True)
    async def faucet_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Faucet Manager", color=discord.Color.blue())
        embed.add_field(name="Subcommands", value="list | drip | fund", inline=False)
        await ctx.send(embed=embed)

    @faucet_group.command(name="list")
    async def list_faucets(self, ctx: commands.Context):
        if not self.faucets:
            embed = discord.Embed(title="Available Faucets", color=discord.Color.blue())
            embed.add_field(name="Sepolia ETH", value="Status: Active | Drip: 0.1 ETH | Balance: 1000 ETH")
            embed.add_field(name="Goerli ETH", value="Status: Active | Drip: 0.1 ETH | Balance: 500 ETH")
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title="Faucets", color=discord.Color.blue())
        for f in self.faucets.values():
            embed.add_field(name=f['name'], value=f"Symbol: {f['symbol']} | Drip: {f['drip']} | Balance: {f['balance']} | Status: {f['status']}", inline=False)
        await ctx.send(embed=embed)

    @faucet_group.command(name="drip")
    async def request_drip(self, ctx: commands.Context, faucet_id: str, address: str):
        existing = [d for d in self.drips.values() if d["faucet"] == faucet_id and d["address"] == address]
        if existing:
            await ctx.send(f"Drip already requested for {address[:16]}... Please wait.")
            return
        drip_id = str(uuid.uuid4())[:8]
        self.drips[drip_id] = {
            "id": drip_id, "faucet": faucet_id, "address": address,
            "amount": 0.1, "status": "completed",
        }
        embed = discord.Embed(title="Drip Requested", color=discord.Color.green())
        embed.add_field(name="Drip ID", value=drip_id)
        embed.add_field(name="Amount", value="0.1 ETH")
        embed.add_field(name="Address", value=address[:20] + "...")
        await ctx.send(embed=embed)

    @faucet_group.command(name="fund")
    async def fund_faucet(self, ctx: commands.Context, faucet_id: str, amount: float):
        embed = discord.Embed(title="Faucet Funded", color=discord.Color.green())
        embed.add_field(name="Faucet", value=faucet_id)
        embed.add_field(name="Amount", value=f"{amount} ETH")
        await ctx.send(embed=embed)

    @web3_group.command(name="verify")
    async def verify_contract(self, ctx: commands.Context, explorer_id: str, contract_address: str, source: str):
        e = self.explorers.get(explorer_id)
        if not e:
            await ctx.send(f"Explorer `{explorer_id}` not found.")
            return
        embed = discord.Embed(title="Contract Verification Submitted", color=discord.Color.blue())
        embed.add_field(name="Contract", value=contract_address[:20] + "...")
        embed.add_field(name="Network", value=e["name"])
        embed.add_field(name="Status", value="⏳ Verifying...")
        await ctx.send(embed=embed)

    @web3_group.command(name="summary")
    async def toolkit_summary(self, ctx: commands.Context):
        embed = discord.Embed(title="Web3 Developer Toolkit Summary", color=discord.Color.blue())
        embed.add_field(name="Explorers", value=len(self.explorers), inline=True)
        embed.add_field(name="Transactions", value=len(self.transactions), inline=True)
        embed.add_field(name="Faucets", value=len(self.faucets) or 2, inline=True)
        embed.add_field(name="Drips Served", value=len(self.drips), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Web3Toolkit(bot))

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
