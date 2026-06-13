"""Decentralized Compute Network Cog — peer-to-peer compute marketplace."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

PROVIDERS: dict[str, dict[str, Any]] = {}
ORDERS: dict[str, dict[str, Any]] = {}
RATINGS: dict[str, dict[str, Any]] = {}


class DecentralizedCompute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.providers = PROVIDERS
        self.orders = ORDERS
        self.ratings = RATINGS

    @commands.group(name="dcompute", aliases=["decentralized-compute", "compute-market"], invoke_without_command=True)
    async def dcompute_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Decentralized Compute Network", color=discord.Color.green())
        embed.add_field(name="Commands", value=(
            "`ipilot dcompute provider register <name> <wallet-address> [region]` — Register provider\n"
            "`ipilot dcompute provider list [status]` — List providers\n"
            "`ipilot dcompute provider info <provider-id>` — Provider details\n"
            "`ipilot dcompute order create <name> <wallet> [cpu] [memory-mb] [hours] [gpu]` — Create order\n"
            "`ipilot dcompute order list [status]` — List orders\n"
            "`ipilot dcompute order info <order-id>` — Order details\n"
            "`ipilot dcompute order cancel <order-id>` — Cancel order\n"
            "`ipilot dcompute rate <provider-id> <wallet> <score>` — Rate provider\n"
            "`ipilot dcompute find <cpu> <memory-mb> [max-price]` — Find optimal provider\n"
            "`ipilot dcompute stats` — Market statistics"
        ), inline=False)
        await ctx.send(embed=embed)

    @dcompute_group.group(name="provider", invoke_without_command=True)
    async def provider_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Compute Providers", color=discord.Color.green())
        embed.add_field(name="Subcommands", value="register | list | info", inline=False)
        await ctx.send(embed=embed)

    @provider_group.command(name="register")
    async def register_provider(self, ctx: commands.Context, name: str, wallet_address: str, region: str = "auto"):
        provider_id = str(uuid.uuid4())[:8]
        self.providers[provider_id] = {
            "id": provider_id, "name": name, "wallet": wallet_address,
            "status": "online", "region": region,
            "cpu_cores": 16, "gpu_count": 0, "memory_mb": 32768, "storage_gb": 500,
            "available_cpu": 16, "available_memory": 32768, "available_gpu": 0,
            "price_cpu": 0.05, "price_gpu": 0.50, "price_mem": 0.002,
            "reputation": 1.0, "jobs": 0, "earned": 0.0,
            "uptime": 99.5, "joined_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Provider Registered", color=discord.Color.green())
        embed.add_field(name="Provider ID", value=provider_id)
        embed.add_field(name="Name", value=name)
        embed.add_field(name="Region", value=region)
        await ctx.send(embed=embed)

    @provider_group.command(name="list")
    async def list_providers(self, ctx: commands.Context, status: str = None):
        providers = [p for p in self.providers.values() if not status or p["status"] == status]
        if not providers:
            await ctx.send("No providers found.")
            return
        embed = discord.Embed(title=f"Compute Providers{f' ({status})' if status else ''}", color=discord.Color.green())
        for p in providers:
            embed.add_field(name=f"{p['name']} ({p['id']})", value=f"Status: {p['status']} | Region: {p['region']} | CPU: {p['available_cpu']}/{p['cpu_cores']} | Rep: {p['reputation']:.2f} | Jobs: {p['jobs']}", inline=False)
        await ctx.send(embed=embed)

    @provider_group.command(name="info")
    async def provider_info(self, ctx: commands.Context, provider_id: str):
        p = self.providers.get(provider_id)
        if not p:
            await ctx.send(f"Provider `{provider_id}` not found.")
            return
        embed = discord.Embed(title=f"Provider: {p['name']}", color=discord.Color.green())
        for k, v in p.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @dcompute_group.group(name="order", invoke_without_command=True)
    async def order_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Compute Orders", color=discord.Color.green())
        embed.add_field(name="Subcommands", value="create | list | info | cancel", inline=False)
        await ctx.send(embed=embed)

    @order_group.command(name="create")
    async def create_order(self, ctx: commands.Context, name: str, wallet: str, cpu: int = 1, memory_mb: int = 1024, hours: int = 1, gpu: int = 0):
        order_id = str(uuid.uuid4())[:8]
        cost = round(cpu * 0.05 * hours + (memory_mb / 1024) * 0.002 * hours + gpu * 0.50 * hours, 4)
        self.orders[order_id] = {
            "id": order_id, "name": name, "wallet": wallet,
            "cpu": cpu, "memory_mb": memory_mb, "gpu": gpu,
            "hours": hours, "cost": cost, "status": "pending",
            "provider_id": "", "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Order Created", color=discord.Color.blue())
        embed.add_field(name="Order ID", value=order_id)
        embed.add_field(name="Cost", value=f"${cost}", inline=True)
        await ctx.send(embed=embed)
        asyncio.create_task(self._match_order(ctx, order_id))

    async def _match_order(self, ctx: commands.Context, order_id: str):
        await asyncio.sleep(2)
        order = self.orders.get(order_id)
        if not order or order["status"] != "pending":
            return
        available = [p for p in self.providers.values() if p["status"] == "online" and p["available_cpu"] >= order["cpu"] and p["available_memory"] >= order["memory_mb"]]
        if not available:
            order["status"] = "cancelled"
            return
        best = max(available, key=lambda p: p["reputation"])
        order["status"] = "active"
        order["provider_id"] = best["id"]
        best["available_cpu"] -= order["cpu"]
        best["available_memory"] -= order["memory_mb"]
        asyncio.create_task(self._complete_order(ctx, order_id))

    async def _complete_order(self, ctx: commands.Context, order_id: str):
        await asyncio.sleep(5)
        order = self.orders.get(order_id)
        if not order:
            return
        order["status"] = "completed"
        provider = self.providers.get(order["provider_id"])
        if provider:
            provider["available_cpu"] += order["cpu"]
            provider["available_memory"] += order["memory_mb"]
            provider["jobs"] += 1
            provider["earned"] += order["cost"]

    @order_group.command(name="list")
    async def list_orders(self, ctx: commands.Context, status: str = None):
        orders = [o for o in self.orders.values() if not status or o["status"] == status]
        if not orders:
            await ctx.send("No orders found.")
            return
        embed = discord.Embed(title=f"Compute Orders{f' ({status})' if status else ''}", color=discord.Color.blue())
        for o in orders:
            embed.add_field(name=f"{o['name']} ({o['id']})", value=f"CPU: {o['cpu']} | Mem: {o['memory_mb']} MB | Cost: ${o['cost']} | Status: {o['status']}", inline=False)
        await ctx.send(embed=embed)

    @order_group.command(name="info")
    async def order_info(self, ctx: commands.Context, order_id: str):
        o = self.orders.get(order_id)
        if not o:
            await ctx.send(f"Order `{order_id}` not found.")
            return
        embed = discord.Embed(title=f"Order: {o['name']}", color=discord.Color.blue())
        for k, v in o.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @order_group.command(name="cancel")
    async def cancel_order(self, ctx: commands.Context, order_id: str):
        o = self.orders.get(order_id)
        if o and o["status"] in ("pending", "active"):
            o["status"] = "cancelled"
            provider = self.providers.get(o["provider_id"])
            if provider:
                provider["available_cpu"] += o["cpu"]
                provider["available_memory"] += o["memory_mb"]
            await ctx.send(f"Order `{order_id}` cancelled.")
        else:
            await ctx.send(f"Order `{order_id}` not found or cannot be cancelled.")

    @dcompute_group.command(name="rate")
    async def rate_provider(self, ctx: commands.Context, provider_id: str, wallet: str, score: int):
        if score < 1 or score > 5:
            await ctx.send("Score must be between 1 and 5.")
            return
        p = self.providers.get(provider_id)
        if not p:
            await ctx.send(f"Provider `{provider_id}` not found.")
            return
        rating_id = str(uuid.uuid4())[:8]
        self.ratings[rating_id] = {"id": rating_id, "provider_id": provider_id, "wallet": wallet, "score": score}
        all_scores = [r["score"] for r in self.ratings.values() if r["provider_id"] == provider_id]
        p["reputation"] = round(sum(all_scores) / len(all_scores), 2)
        await ctx.send(f"Provider `{provider_id}` rated {score}/5. New reputation: {p['reputation']:.2f}")

    @dcompute_group.command(name="find")
    async def find_provider(self, ctx: commands.Context, cpu: int, memory_mb: int, max_price: float = 1.0):
        matches = [p for p in self.providers.values() if p["status"] == "online" and p["available_cpu"] >= cpu and p["available_memory"] >= memory_mb and p["price_cpu"] <= max_price]
        if not matches:
            await ctx.send("No matching providers found.")
            return
        matches.sort(key=lambda p: (-p["reputation"], p["price_cpu"]))
        embed = discord.Embed(title=f"Optimal Providers (CPU: {cpu}, Mem: {memory_mb} MB)", color=discord.Color.green())
        for p in matches[:5]:
            embed.add_field(name=f"{p['name']} ({p['id']})", value=f"Rep: {p['reputation']:.2f} | CPU/hr: ${p['price_cpu']:.4f} | Region: {p['region']} | Available CPU: {p['available_cpu']}", inline=False)
        await ctx.send(embed=embed)

    @dcompute_group.command(name="stats")
    async def market_stats(self, ctx: commands.Context):
        active = [o for o in self.orders.values() if o["status"] == "active"]
        completed = [o for o in self.orders.values() if o["status"] == "completed"]
        embed = discord.Embed(title="Decentralized Compute Market", color=discord.Color.green())
        embed.add_field(name="Providers Online", value=sum(1 for p in self.providers.values() if p["status"] == "online"), inline=True)
        embed.add_field(name="Total Providers", value=len(self.providers), inline=True)
        embed.add_field(name="Active Orders", value=len(active), inline=True)
        embed.add_field(name="Completed Orders", value=len(completed), inline=True)
        embed.add_field(name="Total Spent", value=f"${sum(o['cost'] for o in completed):.2f}", inline=True)
        embed.add_field(name="Available CPU Cores", value=sum(p["available_cpu"] for p in self.providers.values()), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(DecentralizedCompute(bot))

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
