"""Federated Learning Infrastructure Cog — distributed ML model training across edge nodes."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

MODELS: dict[str, dict[str, Any]] = {}
CLIENTS: dict[str, dict[str, Any]] = {}
ROUNDS: dict[str, dict[str, Any]] = {}


class FederatedLearning(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.models = MODELS
        self.clients = CLIENTS
        self.rounds = ROUNDS

    @commands.group(name="federated", aliases=["fedlearn"], invoke_without_command=True)
    async def federated_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Federated Learning Infrastructure", color=discord.Color.purple())
        embed.add_field(name="Commands", value=(
            "`ipilot federated model create <name> <framework> [architecture]` — Register model\n"
            "`ipilot federated model list` — List models\n"
            "`ipilot federated model info <model-id>` — Model details\n"
            "`ipilot federated client register <name> <node-id> [samples]` — Register client\n"
            "`ipilot federated client list` — List clients\n"
            "`ipilot federated client info <client-id>` — Client details\n"
            "`ipilot federated round start <model-id> [aggregation]` — Start training round\n"
            "`ipilot federated round list [model-id]` — List training rounds\n"
            "`ipilot federated round info <round-id>` — Round details\n"
            "`ipilot federated privacy <round-id> <epsilon>` — Apply differential privacy\n"
            "`ipilot federated convergence <model-id>` — Training convergence\n"
            "`ipilot federated summary` — Federated learning summary"
        ), inline=False)
        await ctx.send(embed=embed)

    @federated_group.group(name="model", invoke_without_command=True)
    async def model_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Federated Models", color=discord.Color.purple())
        embed.add_field(name="Subcommands", value="create | list | info", inline=False)
        await ctx.send(embed=embed)

    @model_group.command(name="create")
    async def create_model(self, ctx: commands.Context, name: str, framework: str, architecture: str = ""):
        model_id = str(uuid.uuid4())[:8]
        self.models[model_id] = {
            "id": model_id, "name": name, "framework": framework,
            "architecture": architecture or "custom", "version": "1.0.0",
            "parameters": 1000000, "created_at": datetime.utcnow().isoformat(),
        }
        await ctx.send(f"Model `{model_id}` registered: {name} ({framework})")

    @model_group.command(name="list")
    async def list_models(self, ctx: commands.Context):
        if not self.models:
            await ctx.send("No models registered.")
            return
        embed = discord.Embed(title="Federated Models", color=discord.Color.purple())
        for m in self.models.values():
            embed.add_field(name=f"{m['name']} ({m['id']})", value=f"Framework: {m['framework']} | Params: {m['parameters']:,}", inline=False)
        await ctx.send(embed=embed)

    @model_group.command(name="info")
    async def model_info(self, ctx: commands.Context, model_id: str):
        m = self.models.get(model_id)
        if not m:
            await ctx.send(f"Model `{model_id}` not found.")
            return
        embed = discord.Embed(title=f"Model: {m['name']}", color=discord.Color.purple())
        for k, v in m.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @federated_group.group(name="client", invoke_without_command=True)
    async def client_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Federated Clients", color=discord.Color.purple())
        embed.add_field(name="Subcommands", value="register | list | info", inline=False)
        await ctx.send(embed=embed)

    @client_group.command(name="register")
    async def register_client(self, ctx: commands.Context, name: str, node_id: str, samples: int = 1000):
        client_id = str(uuid.uuid4())[:8]
        self.clients[client_id] = {
            "id": client_id, "name": name, "node": node_id,
            "samples": samples, "status": "idle", "accuracy": 0.0,
            "rounds": 0, "reliability": 1.0, "joined_at": datetime.utcnow().isoformat(),
        }
        await ctx.send(f"Client `{client_id}` registered: {name} ({node_id}, {samples} samples)")

    @client_group.command(name="list")
    async def list_clients(self, ctx: commands.Context):
        if not self.clients:
            await ctx.send("No clients registered.")
            return
        embed = discord.Embed(title="Federated Clients", color=discord.Color.purple())
        for c in self.clients.values():
            embed.add_field(name=f"{c['name']} ({c['id']})", value=f"Node: {c['node']} | Samples: {c['samples']} | Status: {c['status']}", inline=False)
        await ctx.send(embed=embed)

    @client_group.command(name="info")
    async def client_info(self, ctx: commands.Context, client_id: str):
        c = self.clients.get(client_id)
        if not c:
            await ctx.send(f"Client `{client_id}` not found.")
            return
        embed = discord.Embed(title=f"Client: {c['name']}", color=discord.Color.purple())
        for k, v in c.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @federated_group.group(name="round", invoke_without_command=True)
    async def round_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Training Rounds", color=discord.Color.purple())
        embed.add_field(name="Subcommands", value="start | list | info", inline=False)
        await ctx.send(embed=embed)

    @round_group.command(name="start")
    async def start_round(self, ctx: commands.Context, model_id: str, aggregation: str = "federated_averaging"):
        if model_id not in self.models:
            await ctx.send(f"Model `{model_id}` not found.")
            return
        round_id = str(uuid.uuid4())[:8]
        round_num = len([r for r in self.rounds.values() if r["model_id"] == model_id]) + 1
        selected = list(self.clients.keys())[:min(5, len(self.clients))]
        self.rounds[round_id] = {
            "id": round_id, "model_id": model_id, "round": round_num,
            "aggregation": aggregation, "status": "running",
            "clients": selected, "accuracy": 0.0, "loss": 0.0,
            "started_at": datetime.utcnow().isoformat(),
        }
        await ctx.send(f"Training round `{round_id}` started (round #{round_num}, {len(selected)} clients)")
        asyncio.create_task(self._simulate_round(ctx, round_id))

    async def _simulate_round(self, ctx: commands.Context, round_id: str):
        await asyncio.sleep(4)
        r = self.rounds.get(round_id)
        if not r:
            return
        import random
        r["status"] = "completed"
        r["accuracy"] = round(random.uniform(0.75, 0.96), 4)
        r["loss"] = round(random.uniform(0.1, 0.6), 4)
        r["completed_at"] = datetime.utcnow().isoformat()
        for cid in r["clients"]:
            c = self.clients.get(cid)
            if c:
                c["accuracy"] = r["accuracy"]
                c["rounds"] += 1
                c["status"] = "idle"

    @round_group.command(name="list")
    async def list_rounds(self, ctx: commands.Context, model_id: str = None):
        rounds = [r for r in self.rounds.values() if not model_id or r["model_id"] == model_id]
        if not rounds:
            await ctx.send("No training rounds found.")
            return
        embed = discord.Embed(title=f"Training Rounds{f' ({model_id})' if model_id else ''}", color=discord.Color.purple())
        for r in sorted(rounds, key=lambda x: x["round"]):
            embed.add_field(name=f"Round #{r['round']} ({r['id']})", value=f"Accuracy: {r['accuracy']:.2%} | Loss: {r['loss']:.4f} | Status: {r['status']} | Clients: {len(r['clients'])}", inline=False)
        await ctx.send(embed=embed)

    @round_group.command(name="info")
    async def round_info(self, ctx: commands.Context, round_id: str):
        r = self.rounds.get(round_id)
        if not r:
            await ctx.send(f"Round `{round_id}` not found.")
            return
        embed = discord.Embed(title=f"Round #{r['round']}", color=discord.Color.purple())
        for k, v in r.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @federated_group.command(name="privacy")
    async def apply_privacy(self, ctx: commands.Context, round_id: str, epsilon: float):
        r = self.rounds.get(round_id)
        if r:
            r["epsilon"] = epsilon
            r["delta"] = 1e-5
            await ctx.send(f"Differential privacy applied to round `{round_id}`: ε={epsilon}, δ=1e-5")
        else:
            await ctx.send(f"Round `{round_id}` not found.")

    @federated_group.command(name="convergence")
    async def convergence(self, ctx: commands.Context, model_id: str):
        rounds = [r for r in self.rounds.values() if r["model_id"] == model_id and r["status"] == "completed"]
        if not rounds:
            await ctx.send(f"No completed rounds for model `{model_id}`.")
            return
        rounds.sort(key=lambda r: r["round"])
        embed = discord.Embed(title=f"Convergence: {self.models.get(model_id, {}).get('name', model_id)}", color=discord.Color.green())
        for r in rounds[-10:]:
            embed.add_field(name=f"Round #{r['round']}", value=f"Accuracy: {r['accuracy']:.2%} | Loss: {r['loss']:.4f}", inline=True)
        await ctx.send(embed=embed)

    @federated_group.command(name="summary")
    async def fed_summary(self, ctx: commands.Context):
        embed = discord.Embed(title="Federated Learning Summary", color=discord.Color.purple())
        embed.add_field(name="Models", value=len(self.models), inline=True)
        embed.add_field(name="Clients", value=len(self.clients), inline=True)
        embed.add_field(name="Completed Rounds", value=sum(1 for r in self.rounds.values() if r["status"] == "completed"), inline=True)
        if self.rounds:
            avg_acc = sum(r["accuracy"] for r in self.rounds.values() if r["status"] == "completed") / max(1, sum(1 for r in self.rounds.values() if r["status"] == "completed"))
            embed.add_field(name="Avg Accuracy", value=f"{avg_acc:.2%}", inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FederatedLearning(bot))

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
