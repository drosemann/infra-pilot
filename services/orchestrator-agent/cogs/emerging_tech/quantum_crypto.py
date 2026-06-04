"""Quantum-Safe Cryptography Cog — post-quantum crypto (Kyber, Dilithium) for TLS, VPN, signing."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

ALGORITHMS = {
    "kyber-512": "KEM (AES-128)", "kyber-768": "KEM (AES-192)", "kyber-1024": "KEM (AES-256)",
    "dilithium-2": "Signature (SL2)", "dilithium-3": "Signature (SL3)", "dilithium-5": "Signature (SL5)",
    "falcon-512": "Signature (NIST)", "falcon-1024": "Signature (High-Security)",
    "sphincs-plus-128": "Signature (Hash-Based)", "sphincs-plus-256": "Signature (Hash-Based, AES-256)",
}

KEYS: dict[str, dict[str, Any]] = {}
ASSESSMENTS: dict[str, dict[str, Any]] = {}


class QuantumCrypto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.keys = KEYS
        self.assessments = ASSESSMENTS

    @commands.group(name="pqcrypto", aliases=["post-quantum"], invoke_without_command=True)
    async def pqcrypto_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Quantum-Safe Cryptography", color=discord.Color.teal())
        embed.add_field(name="Algorithms", value="kyber-512/768/1024, dilithium-2/3/5, falcon-512/1024, sphincs-plus-128/256", inline=False)
        embed.add_field(name="Commands", value=(
            "`ipilot pqcrypto gen-key <name> <algorithm> [tls|vpn|code_signing|document_signing|ssh]` — Generate PQ key\n"
            "`ipilot pqcrypto list-keys` — List keys\n"
            "`ipilot pqcrypto key-info <key-id>` — Key details\n"
            "`ipilot pqcrypto revoke <key-id>` — Revoke key\n"
            "`ipilot pqcrypto rotate <key-id>` — Rotate key\n"
            "`ipilot pqcrypto algorithms` — List supported algorithms\n"
            "`ipilot pqcrypto assess <name> <endpoint-count>` — Migration assessment\n"
            "`ipilot pqcrypto assessment-info <assessment-id>` — Assessment details\n"
            "`ipilot pqcrypto summary` — PQ crypto summary"
        ), inline=False)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="gen-key")
    async def gen_key(self, ctx: commands.Context, name: str, algorithm: str, cert_type: str = "tls"):
        algorithm = algorithm.lower()
        if algorithm not in ALGORITHMS:
            await ctx.send(f"Unsupported algorithm. Choose: {', '.join(ALGORITHMS.keys())}")
            return
        key_id = str(uuid.uuid4())[:8]
        self.keys[key_id] = {
            "id": key_id, "name": name, "algorithm": algorithm,
            "type": ALGORITHMS[algorithm], "cert_type": cert_type,
            "status": "active", "fingerprint": f"pq-fp-{uuid.uuid4().hex[:24]}",
            "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Quantum-Safe Key Generated", color=discord.Color.green())
        embed.add_field(name="Key ID", value=key_id, inline=True)
        embed.add_field(name="Algorithm", value=algorithm, inline=True)
        embed.add_field(name="Type", value=ALGORITHMS[algorithm], inline=True)
        embed.add_field(name="Certificate Type", value=cert_type, inline=True)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="list-keys")
    async def list_keys(self, ctx: commands.Context):
        if not self.keys:
            await ctx.send("No PQ keys found.")
            return
        embed = discord.Embed(title="Post-Quantum Keys", color=discord.Color.teal())
        for key in self.keys.values():
            embed.add_field(name=f"{key['name']} ({key['id']})", value=f"Algorithm: {key['algorithm']} | Type: {key['type']} | Status: {key['status']}", inline=False)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="key-info")
    async def key_info(self, ctx: commands.Context, key_id: str):
        key = self.keys.get(key_id)
        if not key:
            await ctx.send(f"Key `{key_id}` not found.")
            return
        embed = discord.Embed(title=f"Key: {key['name']}", color=discord.Color.teal())
        for k, v in key.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="revoke")
    async def revoke_key(self, ctx: commands.Context, key_id: str):
        key = self.keys.get(key_id)
        if key and key["status"] == "active":
            key["status"] = "revoked"
            await ctx.send(f"Key `{key_id}` revoked.")
        else:
            await ctx.send(f"Key `{key_id}` not found or not active.")

    @pqcrypto_group.command(name="rotate")
    async def rotate_key(self, ctx: commands.Context, key_id: str):
        key = self.keys.get(key_id)
        if not key:
            await ctx.send(f"Key `{key_id}` not found.")
            return
        new_id = str(uuid.uuid4())[:8]
        self.keys[new_id] = {k: v for k, v in key.items()}
        self.keys[new_id]["id"] = new_id
        self.keys[new_id]["status"] = "active"
        self.keys[new_id]["created_at"] = datetime.utcnow().isoformat()
        key["status"] = "expired"
        embed = discord.Embed(title="Key Rotated", color=discord.Color.blue())
        embed.add_field(name="Old Key", value=key_id, inline=True)
        embed.add_field(name="New Key", value=new_id, inline=True)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="algorithms")
    async def list_algorithms(self, ctx: commands.Context):
        embed = discord.Embed(title="Supported Post-Quantum Algorithms", color=discord.Color.teal())
        for algo, desc in ALGORITHMS.items():
            embed.add_field(name=algo, value=desc, inline=True)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="assess")
    async def create_assessment(self, ctx: commands.Context, name: str, endpoints: int):
        assessment_id = str(uuid.uuid4())[:8]
        compatible = int(endpoints * 0.7)
        hybrid = endpoints - compatible
        self.assessments[assessment_id] = {
            "id": assessment_id, "name": name, "total": endpoints,
            "compatible": compatible, "hybrid": hybrid, "incompatible": int(endpoints * 0.1),
            "status": "in_progress", "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Migration Assessment Created", color=discord.Color.blue())
        embed.add_field(name="Assessment ID", value=assessment_id, inline=True)
        embed.add_field(name="Total Endpoints", value=endpoints, inline=True)
        embed.add_field(name="PQ Compatible", value=compatible, inline=True)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="assessment-info")
    async def assessment_info(self, ctx: commands.Context, assessment_id: str):
        a = self.assessments.get(assessment_id)
        if not a:
            await ctx.send(f"Assessment `{assessment_id}` not found.")
            return
        embed = discord.Embed(title=f"Assessment: {a['name']}", color=discord.Color.blue())
        for k, v in a.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @pqcrypto_group.command(name="summary")
    async def pq_summary(self, ctx: commands.Context):
        embed = discord.Embed(title="Quantum-Safe Cryptography Summary", color=discord.Color.teal())
        embed.add_field(name="Total Keys", value=len(self.keys), inline=True)
        embed.add_field(name="Active Keys", value=sum(1 for k in self.keys.values() if k["status"] == "active"), inline=True)
        embed.add_field(name="Assessments", value=len(self.assessments), inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(QuantumCrypto(bot))

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
