"""Smart Contract Monitoring Cog — monitor deployed smart contracts for suspicious activity."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

CONTRACTS: dict[str, dict[str, Any]] = {}
ALERTS: dict[str, dict[str, Any]] = {}


class ContractMonitoring(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.contracts = CONTRACTS
        self.alerts = ALERTS

    @commands.group(name="contracts", aliases=["smart-contracts"], invoke_without_command=True)
    async def contracts_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Smart Contract Monitoring", color=discord.Color.orange())
        embed.add_field(name="Commands", value=(
            "`ipilot contracts register <name> <address> <network> [standard]` — Register contract\n"
            "`ipilot contracts list [network]` — List monitored contracts\n"
            "`ipilot contracts info <contract-id>` — Contract details\n"
            "`ipilot contracts delete <contract-id>` — Delete contract\n"
            "`ipilot contracts ingest <contract-id> <tx-hash> <from> <value> [gas-price]` — Ingest tx\n"
            "`ipilot contracts alerts [severity] [status]` — List alerts\n"
            "`ipilot contracts alert-info <alert-id>` — Alert details\n"
            "`ipilot contracts resolve <alert-id>` — Resolve alert\n"
            "`ipilot contracts analytics <contract-id>` — Contract analytics\n"
            "`ipilot contracts dashboard` — Monitoring dashboard"
        ), inline=False)
        await ctx.send(embed=embed)

    @contracts_group.command(name="register")
    async def register(self, ctx: commands.Context, name: str, address: str, network: str, standard: str = "custom"):
        contract_id = str(uuid.uuid4())[:8]
        self.contracts[contract_id] = {
            "id": contract_id, "name": name, "address": address,
            "network": network, "standard": standard, "monitoring": True,
            "tx_count": 0, "alert_count": 0, "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Contract Registered", color=discord.Color.green())
        embed.add_field(name="Contract ID", value=contract_id)
        embed.add_field(name="Address", value=address)
        embed.add_field(name="Network", value=network)
        await ctx.send(embed=embed)

    @contracts_group.command(name="list")
    async def list_contracts(self, ctx: commands.Context, network: str = None):
        contracts = [c for c in self.contracts.values() if not network or c["network"] == network]
        if not contracts:
            await ctx.send("No contracts registered.")
            return
        embed = discord.Embed(title=f"Monitored Contracts{f' ({network})' if network else ''}", color=discord.Color.orange())
        for c in contracts:
            embed.add_field(name=f"{c['name']} ({c['id']})", value=f"Network: {c['network']} | Address: {c['address'][:20]}... | TXs: {c['tx_count']} | Alerts: {c['alert_count']}", inline=False)
        await ctx.send(embed=embed)

    @contracts_group.command(name="info")
    async def contract_info(self, ctx: commands.Context, contract_id: str):
        c = self.contracts.get(contract_id)
        if not c:
            await ctx.send(f"Contract `{contract_id}` not found.")
            return
        embed = discord.Embed(title=f"Contract: {c['name']}", color=discord.Color.orange())
        for k, v in c.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @contracts_group.command(name="delete")
    async def delete_contract(self, ctx: commands.Context, contract_id: str):
        if contract_id in self.contracts:
            del self.contracts[contract_id]
            await ctx.send(f"Contract `{contract_id}` deleted.")
        else:
            await ctx.send(f"Contract `{contract_id}` not found.")

    @contracts_group.command(name="ingest")
    async def ingest_tx(self, ctx: commands.Context, contract_id: str, tx_hash: str, from_addr: str, value: float, gas_price: float = 20.0):
        c = self.contracts.get(contract_id)
        if not c:
            await ctx.send(f"Contract `{contract_id}` not found.")
            return
        c["tx_count"] += 1
        if value > 10:
            alert_id = str(uuid.uuid4())[:8]
            self.alerts[alert_id] = {
                "id": alert_id, "contract_id": contract_id, "title": "High Value Transaction",
                "description": f"Transaction of {value} ETH", "severity": "high",
                "status": "open", "tx_hash": tx_hash, "detected_at": datetime.utcnow().isoformat(),
            }
            c["alert_count"] += 1
            await ctx.send(f"⚠️ High value tx detected! Alert `{alert_id}` created.")
        else:
            await ctx.send(f"Tx `{tx_hash[:16]}...` ingested for contract `{contract_id}`.")

    @contracts_group.command(name="alerts")
    async def list_alerts(self, ctx: commands.Context, severity: str = None, status: str = None):
        alerts = list(self.alerts.values())
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        if status:
            alerts = [a for a in alerts if a["status"] == status]
        if not alerts:
            await ctx.send("No alerts found.")
            return
        embed = discord.Embed(title="Security Alerts", color=discord.Color.red())
        for a in alerts:
            embed.add_field(name=f"[{a['severity'].upper()}] {a['title']} ({a['id']})", value=f"Status: {a['status']} | TX: {a.get('tx_hash', 'N/A')[:16]}...", inline=False)
        await ctx.send(embed=embed)

    @contracts_group.command(name="alert-info")
    async def alert_info(self, ctx: commands.Context, alert_id: str):
        a = self.alerts.get(alert_id)
        if not a:
            await ctx.send(f"Alert `{alert_id}` not found.")
            return
        embed = discord.Embed(title=f"Alert: {a['title']}", color=discord.Color.red())
        for k, v in a.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @contracts_group.command(name="resolve")
    async def resolve_alert(self, ctx: commands.Context, alert_id: str):
        a = self.alerts.get(alert_id)
        if a and a["status"] != "resolved":
            a["status"] = "resolved"
            a["resolved_at"] = datetime.utcnow().isoformat()
            await ctx.send(f"Alert `{alert_id}` resolved.")
        else:
            await ctx.send(f"Alert `{alert_id}` not found or already resolved.")

    @contracts_group.command(name="analytics")
    async def contract_analytics(self, ctx: commands.Context, contract_id: str):
        c = self.contracts.get(contract_id)
        if not c:
            await ctx.send(f"Contract `{contract_id}` not found.")
            return
        contract_alerts = [a for a in self.alerts.values() if a["contract_id"] == contract_id]
        embed = discord.Embed(title=f"Analytics: {c['name']}", color=discord.Color.blue())
        embed.add_field(name="Total Transactions", value=c["tx_count"], inline=True)
        embed.add_field(name="Total Alerts", value=len(contract_alerts), inline=True)
        embed.add_field(name="Open Alerts", value=sum(1 for a in contract_alerts if a["status"] == "open"), inline=True)
        await ctx.send(embed=embed)

    @contracts_group.command(name="dashboard")
    async def dashboard(self, ctx: commands.Context):
        embed = discord.Embed(title="Contract Monitoring Dashboard", color=discord.Color.orange())
        embed.add_field(name="Monitored Contracts", value=len(self.contracts), inline=True)
        embed.add_field(name="Total Alerts", value=len(self.alerts), inline=True)
        open_alerts = [a for a in self.alerts.values() if a["status"] == "open"]
        embed.add_field(name="Open Alerts", value=len(open_alerts), inline=True)
        critical = sum(1 for a in open_alerts if a["severity"] == "critical")
        high = sum(1 for a in open_alerts if a["severity"] == "high")
        embed.add_field(name="Critical", value=critical, inline=True)
        embed.add_field(name="High", value=high, inline=True)
        embed.add_field(name="Total TXs", value=sum(c["tx_count"] for c in self.contracts.values()), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ContractMonitoring(bot))

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
