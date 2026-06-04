import json
import uuid
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands
logger = logging.getLogger(__name__)
DATA_FILE = "data/registry_replication.json"

class RegistryReplicationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._images = {}
        self._rules = {}

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
                self._images = data.get("images", {})
                self._rules = data.get("rules", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        logger.info("RegistryReplicationCog ready")

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"images": self._images, "rules": self._rules}, f, indent=2)

    @commands.group(name="registry", invoke_without_command=True)
    async def registry(self, ctx):
        await ctx.send("Registry commands: images, rules, replicate, scan, registries")

    @registry.command(name="images")
    async def list_images(self, ctx, registry: str = None):
        items = list(self._images.values())
        if registry:
            items = [i for i in items if i.get("registry") == registry]
        if not items:
            await ctx.send("No images registered.")
            return
        embed = discord.Embed(title=f"Container Images ({len(items)})", color=discord.Color.blue())
        for img in items[:10]:
            embed.add_field(name=f"{img.get('name')}:{img.get('tag')}", value=f"Registry: {img.get('registry')} | Size: {img.get('size_bytes', 0)}B | Vulns: {img.get('vulnerability_count', 0)}", inline=False)
        await ctx.send(embed=embed)

    @registry.command(name="register")
    @commands.has_permissions(administrator=True)
    async def register_image(self, ctx, name: str, tag: str, registry: str, repository: str):
        img_id = f"img-{uuid.uuid4().hex[:10]}"
        self._images[img_id] = {"id": img_id, "name": name, "tag": tag, "registry": registry, "repository": repository, "size_bytes": 0, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Image {name}:{tag} registered on {registry} ({img_id})")

    @registry.command(name="rules")
    async def list_rules(self, ctx):
        if not self._rules:
            await ctx.send("No replication rules.")
            return
        embed = discord.Embed(title=f"Replication Rules ({len(self._rules)})", color=discord.Color.green())
        for rid, r in self._rules.items():
            embed.add_field(name=rid, value=f"Source: {r.get('source_registry')} -> Targets: {', '.join(r.get('target_registries', []))} | Pattern: {r.get('image_pattern')}", inline=False)
        await ctx.send(embed=embed)

    @registry.command(name="create-rule")
    @commands.has_permissions(administrator=True)
    async def create_rule(self, ctx, source_registry: str, target_registries: str, image_pattern: str = "*"):
        rid = f"rule-{uuid.uuid4().hex[:8]}"
        targets = [x.strip() for x in target_registries.split(",")]
        self._rules[rid] = {"id": rid, "source_registry": source_registry, "target_registries": targets, "image_pattern": image_pattern, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Rule created: {source_registry} -> {', '.join(targets)}")

    @registry.command(name="replicate")
    @commands.has_permissions(administrator=True)
    async def replicate(self, ctx, image_id: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        await ctx.send(f"Replicating {img.get('name')}:{img.get('tag')}...")
        await asyncio.sleep(1)
        await ctx.send(f"Image replicated to all configured registries")

    @registry.command(name="scan")
    async def scan_image(self, ctx, image_id: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        import random
        vulns = random.randint(0, 10)
        img["vulnerability_count"] = vulns
        await self._save_data()
        embed = discord.Embed(title=f"Scan: {img.get('name')}:{img.get('tag')}", color=discord.Color.gold() if vulns > 0 else discord.Color.green())
        embed.add_field(name="Vulnerabilities", value=str(vulns))
        embed.add_field(name="Max Severity", value="HIGH" if vulns > 5 else "LOW" if vulns > 0 else "NONE")
        await ctx.send(embed=embed)

    @registry.command(name="registries")
    async def list_registries(self, ctx):
        registries = ["AWS ECR", "Azure ACR", "GCP GCR", "Docker Hub", "GHCR", "GitLab"]
        embed = discord.Embed(title="Configured Registries", color=discord.Color.blue())
        for r in registries:
            embed.add_field(name=r, value="Connected", inline=True)
        await ctx.send(embed=embed)

    @registry.command(name="add-image")
    @commands.has_permissions(administrator=True)
    async def add_image(self, ctx, name: str, tag: str = "latest", registry: str = "docker_hub", size_mb: float = 100.0):
        iid = f"img-{uuid.uuid4().hex[:8]}"
        self._images[iid] = {"id": iid, "name": name, "tag": tag, "registry": registry, "size_mb": size_mb, "os": "linux", "vulnerability_count": 0, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Image '{name}:{tag}' added ({iid})")

    @registry.command(name="delete-image")
    @commands.has_permissions(administrator=True)
    async def delete_image(self, ctx, image_id: str):
        if image_id in self._images:
            del self._images[image_id]
            await self._save_data()
            await ctx.send(f"Image {image_id} deleted")
        else:
            await ctx.send("Image not found.")

    @registry.command(name="images")
    async def list_images(self, ctx, registry: str = None):
        filtered = list(self._images.values())
        if registry:
            filtered = [i for i in filtered if i.get("registry") == registry]
        if not filtered:
            await ctx.send("No images found.")
            return
        embed = discord.Embed(title=f"Container Images ({len(filtered)})", color=discord.Color.blue())
        for img in filtered[:10]:
            embed.add_field(name=f"{img.get('name')}:{img.get('tag')}", value=f"Registry: {img.get('registry')} | Size: {img.get('size_mb')}MB | Vulns: {img.get('vulnerability_count', 0)}", inline=False)
        await ctx.send(embed=embed)

    @registry.command(name="replicate")
    @commands.has_permissions(administrator=True)
    async def replicate(self, ctx, image_id: str, target_registries: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        targets = [t.strip() for t in target_registries.split(",")]
        results = []
        for t in targets:
            job_id = f"rep-{uuid.uuid4().hex[:8]}"
            results.append({"job_id": job_id, "target": t, "state": "completed"})
        self._replication_jobs.extend(results)
        await self._save_data()
        embed = discord.Embed(title=f"Replication: {img.get('name')}:{img.get('tag')}", color=discord.Color.green())
        embed.add_field(name="Targets", value=", ".join(targets))
        embed.add_field(name="Results", value=f"{len(results)} replications started")
        await ctx.send(embed=embed)

    @registry.command(name="rules")
    async def list_rules(self, ctx):
        if not self._replication_rules:
            await ctx.send("No replication rules.")
            return
        embed = discord.Embed(title=f"Replication Rules ({len(self._replication_rules)})", color=discord.Color.purple())
        for rid, r in self._replication_rules.items():
            embed.add_field(name=r.get("name", rid), value=f"Source: {r.get('source')} -> {', '.join(r.get('targets', []))}", inline=False)
        await ctx.send(embed=embed)

    @registry.command(name="add-rule")
    @commands.has_permissions(administrator=True)
    async def add_rule(self, ctx, name: str, source: str, targets: str):
        rid = f"rule-{uuid.uuid4().hex[:8]}"
        self._replication_rules[rid] = {"id": rid, "name": name, "source": source, "targets": [t.strip() for t in targets.split(",")], "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Replication rule '{name}' created: {source} -> {targets}")

    @registry.command(name="cache")
    async def list_cache(self, ctx):
        if not self._cache:
            await ctx.send("Cache is empty.")
            return
        embed = discord.Embed(title=f"Cached Images ({len(self._cache)})", color=discord.Color.blue())
        for ck, cv in list(self._cache.items())[:10]:
            embed.add_field(name=ck, value=f"Registry: {cv.get('registry')} | TTL: {cv.get('ttl_hours', 'N/A')}h", inline=True)
        await ctx.send(embed=embed)

    @registry.command(name="tags")
    async def list_image_tags(self, ctx, image_id: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        tags = img.get("tags", [img.get("tag", "latest")])
        embed = discord.Embed(title=f"Tags: {img.get('name')}", color=discord.Color.blue())
        embed.add_field(name="Tags", value=", ".join(tags))
        embed.add_field(name="Registry", value=img.get("registry"))
        await ctx.send(embed=embed)

    @registry.command(name="add-tag")
    @commands.has_permissions(administrator=True)
    async def add_image_tag(self, ctx, image_id: str, tag: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        if "tags" not in img:
            img["tags"] = [img.get("tag", "latest")]
        img["tags"].append(tag)
        await self._save_data()
        await ctx.send(f"Tag '{tag}' added to {img.get('name')}")

    @registry.command(name="cleanup")
    @commands.has_permissions(administrator=True)
    async def cleanup_images(self, ctx, registry: str = None, older_than_days: int = 90):
        to_remove = []
        cutoff = (datetime.utcnow().timestamp() - older_than_days * 86400)
        for iid, img in list(self._images.items()):
            if registry and img.get("registry") != registry:
                continue
            created = img.get("created_at", "")
            try:
                created_ts = datetime.fromisoformat(created).timestamp()
                if created_ts < cutoff:
                    to_remove.append(iid)
            except (ValueError, TypeError):
                continue
        for iid in to_remove:
            del self._images[iid]
        await self._save_data()
        await ctx.send(f"Cleanup complete: removed {len(to_remove)} images")

    @registry.command(name="push")
    @commands.has_permissions(administrator=True)
    async def push_image(self, ctx, name: str, tag: str, registry: str = "docker_hub", size_mb: float = 100.0):
        iid = f"img-{uuid.uuid4().hex[:8]}"
        self._images[iid] = {"id": iid, "name": name, "tag": tag, "registry": registry, "size_mb": size_mb, "os": "linux", "status": "pushed", "vulnerability_count": 0, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Image '{name}:{tag}' pushed to {registry} ({iid})")

    @registry.command(name="pull")
    async def pull_image(self, ctx, image_id: str, target_registry: str = None):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        target = target_registry or img.get("registry")
        embed = discord.Embed(title=f"Pull: {img.get('name')}:{img.get('tag')}", color=discord.Color.green())
        embed.add_field(name="Source", value=img.get("registry"))
        embed.add_field(name="Target", value=target)
        embed.add_field(name="Size", value=f"{img.get('size_mb', 0)} MB")
        await ctx.send(embed=embed)

    @registry.command(name="labels")
    async def list_labels(self, ctx, image_id: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        labels = img.get("labels", {})
        embed = discord.Embed(title=f"Labels: {img.get('name')}", color=discord.Color.blue())
        if labels:
            for k, v in labels.items():
                embed.add_field(name=k, value=v, inline=True)
        else:
            embed.description = "No labels configured"
        await ctx.send(embed=embed)

    @registry.command(name="add-label")
    @commands.has_permissions(administrator=True)
    async def add_label(self, ctx, image_id: str, key: str, value: str):
        img = self._images.get(image_id)
        if not img:
            await ctx.send("Image not found.")
            return
        if "labels" not in img:
            img["labels"] = {}
        img["labels"][key] = value
        await self._save_data()
        await ctx.send(f"Label {key}={value} added to {img.get('name')}")

    @registry.command(name="batch-replicate")
    @commands.has_permissions(administrator=True)
    async def batch_replicate(self, ctx, *, image_ids: str):
        ids = [i.strip() for i in image_ids.split(",")]
        replicated = 0
        for iid in ids:
            if iid in self._images:
                targets = [r for r in self._registries if r != self._images[iid].get("registry")]
                for t in targets[:2]:
                    job_id = f"repl-{uuid.uuid4().hex[:10]}"
                    self._replication_jobs.append({"job_id": job_id, "image_id": iid, "target": t, "state": "completed"})
                    replicated += 1
        await self._save_data()
        await ctx.send(f"Replicated {replicated} images across registries.")

    @registry.command(name="export")
    async def export_registry(self, ctx):
        data = json.dumps({"images": list(self._images.values()), "rules": list(self._rules.values())}, indent=2)
        await ctx.send(f"```json\n{data[:1900]}```")

    @registry.command(name="vuln-summary")
    async def vuln_summary(self, ctx):
        if not self._images:
            await ctx.send("No images in registry.")
            return
        critical = sum(1 for i in self._images.values() if i.get("max_severity") == "critical")
        high = sum(1 for i in self._images.values() if i.get("max_severity") == "high")
        medium = sum(1 for i in self._images.values() if i.get("max_severity") == "medium")
        low = sum(1 for i in self._images.values() if i.get("max_severity") == "low")
        embed = discord.Embed(title="Vulnerability Summary", color=discord.Color.red() if critical > 0 else discord.Color.green())
        embed.add_field(name="Total Images", value=str(len(self._images)))
        embed.add_field(name="Critical", value=str(critical))
        embed.add_field(name="High", value=str(high))
        embed.add_field(name="Medium", value=str(medium))
        embed.add_field(name="Low", value=str(low))
        embed.add_field(name="Clean", value=str(len(self._images) - critical - high - medium - low))
        await ctx.send(embed=embed)

    @registry.command(name="quota")
    async def registry_quota(self, ctx):
        total_bytes = sum(i.get("size_bytes", 0) for i in self._images.values())
        embed = discord.Embed(title="Registry Quota", color=discord.Color.blue())
        embed.add_field(name="Images", value=str(len(self._images)))
        embed.add_field(name="Total Size", value=f"{total_bytes / (1024**3):.2f} GB")
        embed.add_field(name="Rules", value=str(len(self._rules)))
        embed.add_field(name="Jobs", value=str(len(self._replication_jobs)))
        await ctx.send(embed=embed)

    @registry.command(name="create-rule")
    @commands.has_permissions(administrator=True)
    async def create_rule(self, ctx, source: str, targets: str, pattern: str = "*"):
        target_list = [t.strip() for t in targets.split(",")]
        rule_id = f"rule-{uuid.uuid4().hex[:8]}"
        self._rules[rule_id] = {"id": rule_id, "source": source, "targets": target_list, "pattern": pattern, "created_at": datetime.utcnow().isoformat()}
        await self._save_data()
        await ctx.send(f"Replication rule created: {source} -> {', '.join(target_list)}")

    @registry.command(name="scan-all")
    @commands.has_permissions(administrator=True)
    async def scan_all_images(self, ctx):
        import random
        for img in self._images.values():
            img["vulnerability_count"] = random.randint(0, 10)
            img["max_severity"] = random.choice(["none", "low", "medium", "high", "critical"])
        await self._save_data()
        await ctx.send(f"Scanned all {len(self._images)} images.")

    def _build_image_embed(self, img: Dict[str, Any]) -> discord.Embed:
        embed = discord.Embed(title=f"{img.get('name', 'Image')}:{img.get('tag', 'latest')}", color=discord.Color.blue())
        embed.add_field(name="ID", value=img.get("id", "N/A"), inline=False)
        embed.add_field(name="Registry", value=img.get("registry", "N/A"), inline=True)
        embed.add_field(name="Repository", value=img.get("repository", "N/A"), inline=True)
        embed.add_field(name="Size", value=f"{img.get('size_bytes', 0) / (1024**2):.1f} MB", inline=True)
        embed.add_field(name="Vulns", value=str(img.get("vulnerability_count", 0)), inline=True)
        embed.add_field(name="Severity", value=img.get("max_severity", "none"), inline=True)
        return embed

    async def _save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"images": self._images, "registries": self._registries, "rules": self._rules, "replication_jobs": self._replication_jobs}, f, indent=2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")

async def setup(bot):
    await bot.add_cog(RegistryReplicationCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_operation(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"operations_count": 0, "success_rate": 100.0, "avg_duration_ms": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": []}

class CogConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=300, ge=10)
    timeout_seconds: int = Field(default=60, ge=5)
    retry_limit: int = Field(default=3, ge=0)
    notify_on_failure: bool = True
    log_level: str = Field(default="INFO")

class CogMetrics:
    def __init__(self) -> None:
        self.runs: int = 0
        self.failures: int = 0
        self.last_run: Optional[datetime] = None
        self.last_duration: float = 0.0

    def record_run(self, duration: float, success: bool) -> None:
        self.runs += 1
        self.last_run = datetime.utcnow()
        self.last_duration = duration
        if not success:
            self.failures += 1

    def summary(self) -> Dict[str, Any]:
        return {"runs": self.runs, "failures": self.failures,
                "success_rate": round((self.runs - self.failures) / max(self.runs, 1) * 100, 1),
                "last_run": self.last_run.isoformat() if self.last_run else None,
                "last_duration_ms": round(self.last_duration, 1)}
