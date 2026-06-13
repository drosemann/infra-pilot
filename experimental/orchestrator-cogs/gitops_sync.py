import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import logging
import uuid
import difflib

import aiohttp
from aiohttp import web

from config import config
from vps_manager import VPSManager

logger = logging.getLogger(__name__)


class GitOpsSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()
        self.state_file = 'data/gitops_state.json'
        self._ensure_data_dir()
        self._load_state()
        self.drift_loop.start()

    def cog_unload(self):
        self.drift_loop.cancel()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                data = json.load(f)
                self.sync_history = data.get("history", [])
                self.versions = data.get("versions", {})
        else:
            self.sync_history = []
            self.versions = {}

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump({"history": self.sync_history, "versions": self.versions}, f, indent=2)

    def _get_vps_config_snapshot(self, vps_id: str) -> Optional[Dict]:
        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            return None
        return {
            "vps_id": vps_id,
            "config": instance.get("config", {}),
            "status": instance.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

    def _detect_drift(self, vps_id: str, desired: Dict) -> List[str]:
        current = self._get_vps_config_snapshot(vps_id)
        if not current:
            return ["VPS not found"]
        diffs = []
        current_cfg = current.get("config", {})
        desired_cfg = desired.get("config", {})
        for key in desired_cfg:
            if current_cfg.get(key) != desired_cfg.get(key):
                diffs.append(f"{key}: {current_cfg.get(key)} -> {desired_cfg.get(key)}")
        return diffs

    def _compute_diff_text(self, vps_id: str, version_id: str) -> str:
        versions = self.versions.get(vps_id, [])
        target = next((v for v in versions if v["version_id"] == version_id), None)
        if not target:
            return "Version not found"
        current = self._get_vps_config_snapshot(vps_id)
        if not current:
            return "VPS not found"
        current_str = json.dumps(current.get("config", {}), indent=2)
        target_str = json.dumps(target.get("snapshot", {}).get("config", {}), indent=2)
        diff = difflib.unified_diff(
            target_str.splitlines(), current_str.splitlines(),
            fromfile=f"version {version_id}", tofile="current",
            lineterm=""
        )
        return "\n".join(diff) or "No differences"

    async def handle_webhook(self, request):
        try:
            data = await request.json()
            repo = data.get("repository", {}).get("full_name", "")
            ref = data.get("ref", "")
            branch = ref.replace("refs/heads/", "")
            commits = data.get("commits", [])

            for commit in commits:
                self.sync_history.append({
                    "id": str(uuid.uuid4())[:8],
                    "type": "git_push",
                    "repo": repo,
                    "branch": branch,
                    "message": commit.get("message", ""),
                    "committer": commit.get("committer", {}).get("name", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                })
            self._save_state()

            return web.json_response({"status": "ok", "commits_processed": len(commits)})
        except Exception as e:
            logger.error(f"GitOps webhook error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)

    @tasks.loop(minutes=5)
    async def drift_loop(self):
        try:
            for vps_id in list(self.vps_manager.vps_instances.keys()):
                current = self._get_vps_config_snapshot(vps_id)
                if not current:
                    continue

                versions = self.versions.get(vps_id, [])
                if not versions:
                    versions.append({
                        "version_id": str(uuid.uuid4())[:8],
                        "snapshot": current,
                        "created_at": datetime.now().isoformat(),
                    })
                    self.versions[vps_id] = versions
                    continue

                latest = versions[-1]["snapshot"]
                diffs = self._detect_drift(vps_id, latest)
                if diffs:
                    self.sync_history.append({
                        "id": str(uuid.uuid4())[:8],
                        "type": "drift_detected",
                        "vps_id": vps_id,
                        "diffs": diffs,
                        "timestamp": datetime.now().isoformat(),
                    })
                    versions.append({
                        "version_id": str(uuid.uuid4())[:8],
                        "snapshot": current,
                        "created_at": datetime.now().isoformat(),
                    })
                    self.versions[vps_id] = versions[-50:]

            self._save_state()
        except Exception as e:
            logger.error(f"Drift detection loop error: {e}")

    @drift_loop.before_loop
    async def before_drift_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="gitops_sync", description="Sync VPS config from Git or apply current state")
    @app_commands.describe(vps_id="VPS ID to sync")
    async def gitops_sync(self, interaction: discord.Interaction, vps_id: str):
        await interaction.response.defer()

        snapshot = self._get_vps_config_snapshot(vps_id)
        if not snapshot:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        versions = self.versions.get(vps_id, [])
        versions.append({
            "version_id": str(uuid.uuid4())[:8],
            "snapshot": snapshot,
            "created_at": datetime.now().isoformat(),
        })
        self.versions[vps_id] = versions[-50:]
        self.sync_history.append({
            "id": str(uuid.uuid4())[:8],
            "type": "sync",
            "vps_id": vps_id,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_state()

        embed = discord.Embed(title=f"GitOps Sync: {vps_id[:12]}", color=0x00FF00, timestamp=datetime.now())
        embed.add_field(name="Status", value="Synced successfully", inline=True)
        embed.add_field(name="Version", value=versions[-1]["version_id"], inline=True)
        embed.add_field(name="Config Version", value=str(len(versions)), inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gitops_status", description="Show GitOps sync status")
    async def gitops_status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        drift_entries = [h for h in self.sync_history if h["type"] == "drift_detected"]
        vps_count = len(self.versions)
        total_versions = sum(len(v) for v in self.versions.values())

        embed = discord.Embed(title="GitOps Sync Status", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="VPS Tracked", value=str(vps_count), inline=True)
        embed.add_field(name="Total Versions", value=str(total_versions), inline=True)
        embed.add_field(name="Drift Events", value=str(len(drift_entries)), inline=True)
        embed.add_field(name="Total Syncs", value=str(len(self.sync_history)), inline=True)

        if drift_entries:
            recent_drifts = drift_entries[-5:]
            drift_text = "\n".join(
                f"• {d['vps_id'][:12]}: {', '.join(d['diffs'][:2])}"
                for d in recent_drifts
            )
            embed.add_field(name="Recent Drift", value=drift_text, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gitops_history", description="Show GitOps sync history")
    async def gitops_history(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.sync_history:
            await interaction.followup.send(embed=discord.Embed(description="No sync history.", color=0xFFFF00))
            return

        recent = sorted(self.sync_history, key=lambda x: x["timestamp"], reverse=True)[:10]
        embed = discord.Embed(title="GitOps Sync History", color=discord.Color.blue(), timestamp=datetime.now())
        for entry in recent:
            icon = {"sync": "🔄", "drift_detected": "⚠️", "git_push": "📥", "rollback": "↩️"}.get(entry["type"], "❓")
            name = entry.get("vps_id", entry.get("repo", "unknown"))[:12]
            embed.add_field(
                name=f"{icon} {entry['type']} - {name}",
                value=f"{entry['timestamp'][:19]} | ID: {entry['id']}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gitops_diff", description="Show config drift diff for a VPS")
    @app_commands.describe(vps_id="VPS ID", version_id="Optional version ID to diff against")
    async def gitops_diff(self, interaction: discord.Interaction, vps_id: str, version_id: Optional[str] = None):
        await interaction.response.defer()

        if version_id:
            diff_text = self._compute_diff_text(vps_id, version_id)
        else:
            versions = self.versions.get(vps_id, [])
            if len(versions) < 2:
                await interaction.followup.send(embed=discord.Embed(description="Need at least 2 versions to diff.", color=0xFFFF00))
                return
            prev = versions[-2]["snapshot"]
            current = self._get_vps_config_snapshot(vps_id)
            if not current:
                await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
                return
            diff_text = "\n".join(self._detect_drift(vps_id, prev)) or "No differences"

        if len(diff_text) > 1000:
            diff_text = diff_text[:1000] + "\n... (truncated)"

        embed = discord.Embed(title=f"GitOps Diff: {vps_id[:12]}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Diff", value=f"```diff\n{diff_text}\n```" if diff_text.strip() else "No differences", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gitops_rollback", description="Rollback VPS config to a previous version")
    @app_commands.describe(vps_id="VPS ID", version_id="Version ID to rollback to")
    async def gitops_rollback(self, interaction: discord.Interaction, vps_id: str, version_id: str):
        await interaction.response.defer()

        versions = self.versions.get(vps_id, [])
        target = next((v for v in versions if v["version_id"] == version_id), None)
        if not target:
            await interaction.followup.send(embed=discord.Embed(description="Version not found.", color=0xFF0000))
            return

        snapshot = target["snapshot"]
        desired_cfg = snapshot.get("config", {})

        instance = self.vps_manager.vps_instances.get(vps_id)
        if not instance:
            await interaction.followup.send(embed=discord.Embed(description="VPS not found.", color=0xFF0000))
            return

        from vps_manager import VPSConfig
        new_config = VPSConfig(
            cpu_limit=desired_cfg.get("cpu_limit", instance["config"]["cpu_limit"]),
            memory_limit=desired_cfg.get("memory_limit", instance["config"]["memory_limit"]),
            storage_limit=desired_cfg.get("storage_limit", instance["config"]["storage_limit"]),
            image=desired_cfg.get("image", instance["config"]["image"]),
            ports=desired_cfg.get("ports", instance["config"]["ports"]),
            env_vars={},
        )

        if await self.vps_manager.update_vps_config(vps_id, new_config):
            versions.append({
                "version_id": str(uuid.uuid4())[:8],
                "snapshot": self._get_vps_config_snapshot(vps_id),
                "created_at": datetime.now().isoformat(),
                "rolled_back_to": version_id,
            })
            self.versions[vps_id] = versions[-50:]
            self.sync_history.append({
                "id": str(uuid.uuid4())[:8],
                "type": "rollback",
                "vps_id": vps_id,
                "version_id": version_id,
                "timestamp": datetime.now().isoformat(),
            })
            self._save_state()
            await interaction.followup.send(embed=discord.Embed(description=f"Rolled back {vps_id[:12]} to version {version_id}.", color=0x00FF00))
        else:
            await interaction.followup.send(embed=discord.Embed(description="Failed to apply rollback.", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(GitOpsSync(bot))
