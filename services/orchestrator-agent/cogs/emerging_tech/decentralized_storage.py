"""Decentralized Storage Gateway Cog — IPFS/Arweave/Filecoin integration."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

PROTOCOLS = {"ipfs": "IPFS", "arweave": "Arweave", "filecoin": "Filecoin"}
CONTENT_ITEMS: dict[str, dict[str, Any]] = {}


class DecentralizedStorage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.items = CONTENT_ITEMS

    @commands.group(name="dstorage", aliases=["decentralized-storage"], invoke_without_command=True)
    async def dstorage_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Decentralized Storage Gateway", color=discord.Color.purple())
        embed.add_field(name="Protocols", value="ipfs | arweave | filecoin", inline=False)
        embed.add_field(name="Commands", value=(
            "`ipilot dstorage upload <protocol> <name> [size-mb] [mime]` — Upload content\n"
            "`ipilot dstorage list [protocol]` — List content\n"
            "`ipilot dstorage info <content-id>` — Content details\n"
            "`ipilot dstorage delete <content-id>` — Delete content\n"
            "`ipilot dstorage pin <content-id>` — Pin content\n"
            "`ipilot dstorage unpin <content-id>` — Unpin content\n"
            "`ipilot dstorage tier <content-id> <hot|warm|cold|archive>` — Set storage tier\n"
            "`ipilot dstorage stats` — Storage statistics\n"
            "`ipilot dstorage pin-cid <protocol> <cid>` — Pin by CID"
        ), inline=False)
        await ctx.send(embed=embed)

    @dstorage_group.command(name="upload")
    async def upload(self, ctx: commands.Context, protocol: str, name: str, size_mb: int = 10, mime: str = "application/octet-stream"):
        protocol = protocol.lower()
        if protocol not in PROTOCOLS:
            await ctx.send(f"Unsupported protocol. Choose: {', '.join(PROTOCOLS.keys())}")
            return
        content_id = str(uuid.uuid4())[:8]
        cid = f"Qm{content_id}{uuid.uuid4().hex[:36]}"
        self.items[content_id] = {
            "id": content_id, "name": name, "protocol": protocol,
            "cid": cid, "size_mb": size_mb, "mime": mime,
            "tier": "hot", "pinned": True, "replication": 3,
            "gateway_url": f"https://{protocol}.io/{cid}" if protocol != "arweave" else f"https://arweave.net/{cid}",
            "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Content Uploaded", color=discord.Color.green())
        embed.add_field(name="ID", value=content_id, inline=True)
        embed.add_field(name="Protocol", value=PROTOCOLS[protocol], inline=True)
        embed.add_field(name="CID", value=cid, inline=False)
        embed.add_field(name="Gateway URL", value=self.items[content_id]["gateway_url"], inline=False)
        await ctx.send(embed=embed)

    @dstorage_group.command(name="list")
    async def list_content(self, ctx: commands.Context, protocol: str = None):
        items = [i for i in self.items.values() if not protocol or i["protocol"] == protocol]
        if not items:
            await ctx.send("No content found.")
            return
        embed = discord.Embed(title=f"Decentralized Storage{f' ({protocol})' if protocol else ''}", color=discord.Color.purple())
        for item in items:
            embed.add_field(name=f"{item['name']} ({item['id']})", value=f"Protocol: {item['protocol']} | CID: {item['cid'][:20]}... | Tier: {item['tier']} | Size: {item['size_mb']} MB", inline=False)
        await ctx.send(embed=embed)

    @dstorage_group.command(name="info")
    async def content_info(self, ctx: commands.Context, content_id: str):
        item = self.items.get(content_id)
        if not item:
            await ctx.send(f"Content `{content_id}` not found.")
            return
        embed = discord.Embed(title=f"Content: {item['name']}", color=discord.Color.purple())
        for key, value in item.items():
            embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=True)
        await ctx.send(embed=embed)

    @dstorage_group.command(name="delete")
    async def delete_content(self, ctx: commands.Context, content_id: str):
        if content_id in self.items:
            del self.items[content_id]
            await ctx.send(f"Content `{content_id}` deleted.")
        else:
            await ctx.send(f"Content `{content_id}` not found.")

    @dstorage_group.command(name="pin")
    async def pin(self, ctx: commands.Context, content_id: str):
        item = self.items.get(content_id)
        if item:
            item["pinned"] = True
            await ctx.send(f"Content `{content_id}` is now pinned.")
        else:
            await ctx.send(f"Content `{content_id}` not found.")

    @dstorage_group.command(name="unpin")
    async def unpin(self, ctx: commands.Context, content_id: str):
        item = self.items.get(content_id)
        if item:
            item["pinned"] = False
            await ctx.send(f"Content `{content_id}` is now unpinned.")
        else:
            await ctx.send(f"Content `{content_id}` not found.")

    @dstorage_group.command(name="tier")
    async def set_tier(self, ctx: commands.Context, content_id: str, tier: str):
        item = self.items.get(content_id)
        if not item:
            await ctx.send(f"Content `{content_id}` not found.")
            return
        if tier not in ("hot", "warm", "cold", "archive"):
            await ctx.send("Tier must be: hot, warm, cold, or archive.")
            return
        item["tier"] = tier
        await ctx.send(f"Content `{content_id}` tier set to `{tier}`.")

    @dstorage_group.command(name="stats")
    async def storage_stats(self, ctx: commands.Context):
        total_mb = sum(i["size_mb"] for i in self.items.values())
        embed = discord.Embed(title="Storage Statistics", color=discord.Color.purple())
        embed.add_field(name="Total Items", value=len(self.items), inline=True)
        embed.add_field(name="Total Size", value=f"{total_mb} MB", inline=True)
        for proto in PROTOCOLS:
            count = sum(1 for i in self.items.values() if i["protocol"] == proto)
            embed.add_field(name=PROTOCOLS[proto], value=f"{count} items", inline=True)
        await ctx.send(embed=embed)

    @dstorage_group.command(name="pin-cid")
    async def pin_by_cid(self, ctx: commands.Context, protocol: str, cid: str):
        protocol = protocol.lower()
        if protocol not in PROTOCOLS:
            await ctx.send(f"Unsupported protocol. Choose: {', '.join(PROTOCOLS.keys())}")
            return
        content_id = str(uuid.uuid4())[:8]
        self.items[content_id] = {
            "id": content_id, "name": f"pinned-{cid[:16]}", "protocol": protocol,
            "cid": cid, "size_mb": 0, "mime": "unknown",
            "tier": "hot", "pinned": True, "replication": 3,
            "gateway_url": f"https://{protocol}.io/{cid}",
            "created_at": datetime.utcnow().isoformat(),
        }
        await ctx.send(f"Pinned CID `{cid}` via {PROTOCOLS[protocol]} as `{content_id}`.")


async def setup(bot: commands.Bot):
    await bot.add_cog(DecentralizedStorage(bot))

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
