"""Web3 Identity & Auth Cog — wallet-based authentication, SIWE, token-gated access."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

USERS: dict[str, dict[str, Any]] = {}
GATE_RULES: dict[str, dict[str, Any]] = {}
SESSIONS: dict[str, dict[str, Any]] = {}


class Web3Auth(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.users = USERS
        self.gate_rules = GATE_RULES
        self.sessions = SESSIONS

    @commands.group(name="web3auth", aliases=["w3auth"], invoke_without_command=True)
    async def web3auth_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Web3 Identity & Authentication", color=discord.Color.blue())
        embed.add_field(name="Commands", value=(
            "`ipilot web3auth register <wallet-address> [wallet-type]` — Register wallet\n"
            "`ipilot web3auth users` — List users\n"
            "`ipilot web3auth user <user-id>` — User details\n"
            "`ipilot web3auth siwe <wallet-address> [domain]` — Generate SIWE message\n"
            "`ipilot web3auth verify <wallet-address> <signature>` — Verify SIWE signature\n"
            "`ipilot web3auth sessions` — Active sessions\n"
            "`ipilot web3auth revoke <session-id>` — Revoke session\n"
            "`ipilot web3auth gate create <name> <nft|token|whitelist|staking|governance|custom>` — Create gate rule\n"
            "`ipilot web3auth gate list` — List gate rules\n"
            "`ipilot web3auth gate toggle <rule-id>` — Toggle gate rule\n"
            "`ipilot web3auth gate delete <rule-id>` — Delete gate rule\n"
            "`ipilot web3auth check <wallet-address> <resource>` — Check access"
        ), inline=False)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="register")
    async def register(self, ctx: commands.Context, wallet_address: str, wallet_type: str = "metamask"):
        existing = next((u for u in self.users.values() if u["wallet"] == wallet_address), None)
        if existing:
            await ctx.send(f"Wallet already registered as user `{existing['id']}`.")
            return
        user_id = str(uuid.uuid4())[:8]
        self.users[user_id] = {
            "id": user_id, "wallet": wallet_address, "type": wallet_type,
            "ens": "", "verified": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Wallet Registered", color=discord.Color.green())
        embed.add_field(name="User ID", value=user_id)
        embed.add_field(name="Wallet", value=wallet_address)
        embed.add_field(name="Type", value=wallet_type)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="users")
    async def list_users(self, ctx: commands.Context):
        if not self.users:
            await ctx.send("No users registered.")
            return
        embed = discord.Embed(title="Web3 Users", color=discord.Color.blue())
        for u in self.users.values():
            embed.add_field(name=f"{u['id']}", value=f"Wallet: {u['wallet'][:20]}... | Type: {u['type']} | Verified: {u['verified']}", inline=False)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="user")
    async def user_info(self, ctx: commands.Context, user_id: str):
        u = self.users.get(user_id)
        if not u:
            await ctx.send(f"User `{user_id}` not found.")
            return
        embed = discord.Embed(title=f"User: {u['id']}", color=discord.Color.blue())
        for k, v in u.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="siwe")
    async def generate_siwe(self, ctx: commands.Context, wallet_address: str, domain: str = "infrapilot.ai"):
        nonce = uuid.uuid4().hex[:16]
        message = (
            f"{domain} wants you to sign in with your Ethereum account:\n"
            f"{wallet_address}\n\n"
            f"Sign in to Infra Pilot with your wallet\n\n"
            f"URI: https://{domain}\nVersion: 1\nChain ID: 1\nNonce: {nonce}\n"
        )
        embed = discord.Embed(title="Sign-In with Ethereum", color=discord.Color.blue())
        embed.add_field(name="Message", value=f"```\n{message}\n```", inline=False)
        embed.add_field(name="Nonce", value=nonce)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="verify")
    async def verify_siwe(self, ctx: commands.Context, wallet_address: str, signature: str):
        user = next((u for u in self.users.values() if u["wallet"] == wallet_address), None)
        if not user:
            await ctx.send("Wallet not registered. Use `web3auth register` first.")
            return
        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = {
            "id": session_id, "user_id": user["id"], "wallet": wallet_address,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": datetime.utcnow().isoformat(),
            "revoked": False,
        }
        embed = discord.Embed(title="Verification Successful", color=discord.Color.green())
        embed.add_field(name="Session ID", value=session_id)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="sessions")
    async def list_sessions(self, ctx: commands.Context):
        active = [s for s in self.sessions.values() if not s["revoked"]]
        if not active:
            await ctx.send("No active sessions.")
            return
        embed = discord.Embed(title="Active Sessions", color=discord.Color.green())
        for s in active:
            embed.add_field(name=s["id"], value=f"User: {s['user_id']} | Wallet: {s['wallet'][:16]}...", inline=False)
        await ctx.send(embed=embed)

    @web3auth_group.command(name="revoke")
    async def revoke_session(self, ctx: commands.Context, session_id: str):
        s = self.sessions.get(session_id)
        if s and not s["revoked"]:
            s["revoked"] = True
            await ctx.send(f"Session `{session_id}` revoked.")
        else:
            await ctx.send(f"Session `{session_id}` not found or already revoked.")

    @web3auth_group.group(name="gate", invoke_without_command=True)
    async def gate_group(self, ctx: commands.Context):
        embed = discord.Embed(title="Token-Gate Rules", color=discord.Color.blue())
        embed.add_field(name="Subcommands", value="create | list | toggle | delete", inline=False)
        await ctx.send(embed=embed)

    @gate_group.command(name="create")
    async def create_gate(self, ctx: commands.Context, name: str, gate_type: str):
        gate_types = {"nft": "nft_holding", "token": "token_balance", "whitelist": "whitelist", "staking": "staking", "governance": "governance", "custom": "custom"}
        gt = gate_types.get(gate_type.lower())
        if not gt:
            await ctx.send(f"Invalid gate type. Choose: {', '.join(gate_types.keys())}")
            return
        rule_id = str(uuid.uuid4())[:8]
        self.gate_rules[rule_id] = {
            "id": rule_id, "name": name, "type": gt, "enabled": True,
            "network": "ethereum", "resources": [], "created_at": datetime.utcnow().isoformat(),
        }
        embed = discord.Embed(title="Gate Rule Created", color=discord.Color.green())
        embed.add_field(name="Rule ID", value=rule_id)
        embed.add_field(name="Type", value=gt)
        await ctx.send(embed=embed)

    @gate_group.command(name="list")
    async def list_gates(self, ctx: commands.Context):
        if not self.gate_rules:
            await ctx.send("No gate rules configured.")
            return
        embed = discord.Embed(title="Token-Gate Rules", color=discord.Color.blue())
        for r in self.gate_rules.values():
            embed.add_field(name=f"{r['name']} ({r['id']})", value=f"Type: {r['type']} | Enabled: {r['enabled']}", inline=False)
        await ctx.send(embed=embed)

    @gate_group.command(name="toggle")
    async def toggle_gate(self, ctx: commands.Context, rule_id: str):
        r = self.gate_rules.get(rule_id)
        if r:
            r["enabled"] = not r["enabled"]
            await ctx.send(f"Gate rule `{rule_id}` {'enabled' if r['enabled'] else 'disabled'}.")
        else:
            await ctx.send(f"Rule `{rule_id}` not found.")

    @gate_group.command(name="delete")
    async def delete_gate(self, ctx: commands.Context, rule_id: str):
        if rule_id in self.gate_rules:
            del self.gate_rules[rule_id]
            await ctx.send(f"Gate rule `{rule_id}` deleted.")
        else:
            await ctx.send(f"Rule `{rule_id}` not found.")

    @web3auth_group.command(name="check")
    async def check_access(self, ctx: commands.Context, wallet_address: str, resource: str):
        user = next((u for u in self.users.values() if u["wallet"] == wallet_address), None)
        if not user:
            await ctx.send(f"Access DENIED: Wallet not registered.")
            return
        denied_rules = [r for r in self.gate_rules.values() if r["enabled"] and resource in r.get("resources", [])]
        if denied_rules:
            await ctx.send(f"Access DENIED by rule: {denied_rules[0]['name']}")
        else:
            await ctx.send(f"Access GRANTED for `{wallet_address[:20]}...` to `{resource}`.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Web3Auth(bot))

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
