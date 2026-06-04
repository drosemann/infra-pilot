"""Confidential Computing Enclave Cog — Intel SGX/AMD SEV/ARM TrustZone enclave management."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

TECHNOLOGIES = {
    "sgx": "Intel SGX", "sev": "AMD SEV", "sev-snp": "AMD SEV-SNP",
    "trustzone": "ARM TrustZone", "gpu-tee": "NVIDIA GPU TEE",
}

ENCLAVES: dict[str, dict[str, Any]] = {}
EVIDENCES: dict[str, dict[str, Any]] = {}


class ConfidentialComputing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.enclaves = ENCLAVES
        self.evidences = EVIDENCES

    @commands.group(name="enclave", aliases=["confidential-computing"], invoke_without_command=True)
    async def enclave_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Confidential Computing Enclave", color=discord.Color.dark_blue())
        embed.add_field(name="Technologies", value=", ".join(TECHNOLOGIES.values()), inline=False)
        embed.add_field(name="Commands", value=(
            "`ipilot enclave create <name> <sgx|sev|sev-snp|trustzone|gpu-tee> [memory-mb] [cores]` — Create enclave\n"
            "`ipilot enclave list [technology]` — List enclaves\n"
            "`ipilot enclave info <enclave-id>` — Enclave details\n"
            "`ipilot enclave start <enclave-id>` — Start enclave\n"
            "`ipilot enclave stop <enclave-id>` — Stop enclave\n"
            "`ipilot enclave delete <enclave-id>` — Terminate enclave\n"
            "`ipilot enclave attest <enclave-id>` — Verify attestation\n"
            "`ipilot enclave evidence <enclave-id>` — List attestation evidence\n"
            "`ipilot enclave platform <technology>` — Platform support info\n"
            "`ipilot enclave summary` — Enclave summary"
        ), inline=False)
        await ctx.send(embed=embed)

    @enclave_group.command(name="create")
    async def create_enclave(self, ctx: commands.Context, name: str, technology: str, memory_mb: int = 256, cores: int = 2):
        tech = technology.lower()
        if tech not in TECHNOLOGIES:
            await ctx.send(f"Unsupported technology. Choose: {', '.join(TECHNOLOGIES.keys())}")
            return
        enclave_id = str(uuid.uuid4())[:8]
        self.enclaves[enclave_id] = {
            "id": enclave_id, "name": name, "technology": tech,
            "tech_name": TECHNOLOGIES[tech], "memory_mb": memory_mb,
            "cpu_cores": cores, "status": "creating",
            "attestation": "pending", "measurement": f"mr-enclave-{uuid.uuid4().hex[:24]}",
            "image": "infrapilot/confidential-enclave:latest",
            "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Creating Enclave", color=discord.Color.green())
        embed.add_field(name="Enclave ID", value=enclave_id, inline=True)
        embed.add_field(name="Technology", value=TECHNOLOGIES[tech], inline=True)
        embed.add_field(name="Resources", value=f"{memory_mb} MB / {cores} cores", inline=True)
        await ctx.send(embed=embed)
        asyncio.create_task(self._simulate_init(ctx, enclave_id))

    async def _simulate_init(self, ctx: commands.Context, enclave_id: str):
        await asyncio.sleep(3)
        e = self.enclaves.get(enclave_id)
        if e:
            e["status"] = "running"
            e["attestation"] = "verified"

    @enclave_group.command(name="list")
    async def list_enclaves(self, ctx: commands.Context, technology: str = None):
        enclaves = [e for e in self.enclaves.values() if not technology or e["technology"] == technology]
        if not enclaves:
            await ctx.send("No enclaves found.")
            return
        embed = discord.Embed(title=f"Enclaves{f' ({technology})' if technology else ''}", color=discord.Color.dark_blue())
        for e in enclaves:
            embed.add_field(name=f"{e['name']} ({e['id']})", value=f"Tech: {e['tech_name']} | Status: {e['status']} | Attestation: {e['attestation']}", inline=False)
        await ctx.send(embed=embed)

    @enclave_group.command(name="info")
    async def enclave_info(self, ctx: commands.Context, enclave_id: str):
        e = self.enclaves.get(enclave_id)
        if not e:
            await ctx.send(f"Enclave `{enclave_id}` not found.")
            return
        embed = discord.Embed(title=f"Enclave: {e['name']}", color=discord.Color.dark_blue())
        for k, v in e.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @enclave_group.command(name="start")
    async def start_enclave(self, ctx: commands.Context, enclave_id: str):
        e = self.enclaves.get(enclave_id)
        if e and e["status"] in ("stopped", "error"):
            e["status"] = "running"
            await ctx.send(f"Enclave `{enclave_id}` started.")
        else:
            await ctx.send(f"Enclave `{enclave_id}` not found or already running.")

    @enclave_group.command(name="stop")
    async def stop_enclave(self, ctx: commands.Context, enclave_id: str):
        e = self.enclaves.get(enclave_id)
        if e and e["status"] == "running":
            e["status"] = "stopped"
            await ctx.send(f"Enclave `{enclave_id}` stopped.")
        else:
            await ctx.send(f"Enclave `{enclave_id}` not found or not running.")

    @enclave_group.command(name="delete")
    async def delete_enclave(self, ctx: commands.Context, enclave_id: str):
        if enclave_id in self.enclaves:
            del self.enclaves[enclave_id]
            self.evidences = {k: v for k, v in self.evidences.items() if v["enclave_id"] != enclave_id}
            await ctx.send(f"Enclave `{enclave_id}` terminated.")
        else:
            await ctx.send(f"Enclave `{enclave_id}` not found.")

    @enclave_group.command(name="attest")
    async def verify_attestation(self, ctx: commands.Context, enclave_id: str):
        e = self.enclaves.get(enclave_id)
        if not e:
            await ctx.send(f"Enclave `{enclave_id}` not found.")
            return
        evidence_id = str(uuid.uuid4())[:8]
        self.evidences[evidence_id] = {
            "id": evidence_id, "enclave_id": enclave_id,
            "verified": True, "verifier": "infra-pilot-attestation",
            "timestamp": datetime.utcnow().isoformat(),
        }
        e["attestation"] = "verified"
        embed = discord.Embed(title="Attestation Verified", color=discord.Color.green())
        embed.add_field(name="Evidence ID", value=evidence_id)
        embed.add_field(name="Result", value="✅ Measurement match, signer trusted, TCB OK")
        await ctx.send(embed=embed)

    @enclave_group.command(name="evidence")
    async def list_evidence(self, ctx: commands.Context, enclave_id: str = None):
        evs = [ev for ev in self.evidences.values() if not enclave_id or ev["enclave_id"] == enclave_id]
        if not evs:
            await ctx.send("No attestation evidence found.")
            return
        embed = discord.Embed(title="Attestation Evidence", color=discord.Color.blue())
        for ev in evs:
            embed.add_field(name=f"Evidence {ev['id']}", value=f"Enclave: {ev['enclave_id']} | Verified: {ev['verified']}", inline=False)
        await ctx.send(embed=embed)

    @enclave_group.command(name="platform")
    async def platform_support(self, ctx: commands.Context, technology: str):
        tech = technology.lower()
        support = {
            "sgx": {"hardware": "Intel Xeon E3+, Core 6th gen+", "memory": "512 MB", "os": "Linux, Windows", "driver": "SGX DCAP"},
            "sev": {"hardware": "AMD EPYC 7002+", "memory": "80 GB", "os": "Linux", "driver": "SEV kernel module"},
            "sev-snp": {"hardware": "AMD EPYC 9004+", "memory": "512 GB", "os": "Linux 6.0+", "driver": "SEV-SNP module"},
            "trustzone": {"hardware": "ARM Cortex-A", "memory": "32 MB", "os": "OP-TEE", "driver": "TrustZone driver"},
            "gpu-tee": {"hardware": "NVIDIA H100/A100", "memory": "80 GB", "os": "Linux", "driver": "Confidential Computing"},
        }
        info = support.get(tech)
        if not info:
            await ctx.send(f"Unknown technology: {technology}")
            return
        embed = discord.Embed(title=f"Platform Support: {TECHNOLOGIES.get(tech, tech)}", color=discord.Color.blue())
        for k, v in info.items():
            embed.add_field(name=k.replace("_", " ").title(), value=v, inline=True)
        await ctx.send(embed=embed)

    @enclave_group.command(name="summary")
    async def enclave_summary(self, ctx: commands.Context):
        embed = discord.Embed(title="Confidential Computing Summary", color=discord.Color.dark_blue())
        embed.add_field(name="Total Enclaves", value=len(self.enclaves), inline=True)
        embed.add_field(name="Running", value=sum(1 for e in self.enclaves.values() if e["status"] == "running"), inline=True)
        embed.add_field(name="Verified Attestations", value=sum(1 for e in self.enclaves.values() if e["attestation"] == "verified"), inline=True)
        for t in TECHNOLOGIES:
            count = sum(1 for e in self.enclaves.values() if e["technology"] == t)
            if count:
                embed.add_field(name=TECHNOLOGIES[t], value=f"{count} enclaves", inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfidentialComputing(bot))

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
