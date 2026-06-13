"""Edge CDN Cog - Distributed content caching at edge nodes."""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, BinaryIO
from collections import OrderedDict

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class CachePolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    FIFO = "fifo"


class CacheEntry:
    """Represents a single cached content item."""

    def __init__(self, key: str, source: str, content_type: str, size_bytes: int):
        self.key = key
        self.source = source
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count: int = 0
        self.ttl_seconds: int = 86400
        self.compressed: bool = False
        self.compression_type: Optional[str] = None
        self.etag: str = hashlib.md5(key.encode()).hexdigest()
        self.checksum: str = ""
        self.metadata: dict[str, Any] = {}

    @property
    def is_expired(self) -> bool:
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "source": self.source,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
            "compressed": self.compressed,
            "etag": self.etag,
            "checksum": self.checksum,
        }


class CachePolicy:
    """Defines caching behavior for a content source."""

    def __init__(self, name: str, pattern: str, source: str,
                 ttl_seconds: int = 86400, priority: str = "normal",
                 compression: Optional[str] = None):
        self.name = name
        self.pattern = pattern
        self.source = source
        self.ttl_seconds = ttl_seconds
        self.priority = priority
        self.compression = compression
        self.enabled: bool = True
        self.max_objects: int = 1000
        self.max_size_mb: int = 500

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pattern": self.pattern,
            "source": self.source,
            "ttl_seconds": self.ttl_seconds,
            "priority": self.priority,
            "compression": self.compression,
            "enabled": self.enabled,
            "max_objects": self.max_objects,
            "max_size_mb": self.max_size_mb,
        }


class OriginShield:
    """Origin shield configuration to reduce upstream bandwidth."""

    def __init__(self):
        self.enabled: bool = True
        self.max_stale_hours: int = 72
        self.retry_on_error: bool = True
        self.retry_count: int = 3
        self.batch_requests: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_stale_hours": self.max_stale_hours,
            "retry_on_error": self.retry_on_error,
            "retry_count": self.retry_count,
            "batch_requests": self.batch_requests,
        }


class EdgeCDN:
    """Distributed content caching system for edge nodes."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_root = config.get("cache_root", "/var/cache/edge-cdn")
        self.max_disk_usage_gb = config.get("max_disk_usage_gb", 100)
        self.eviction_policy = CachePolicy.LFU

        self.cache: dict[str, CacheEntry] = {}
        self.policies: dict[str, CachePolicy] = {}
        self.origin_shield = OriginShield()
        self._eviction_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._seed_data()

    def _seed_data(self):
        self.policies["container-images"] = CachePolicy(
            "container-images", "library/*", "docker.io",
            ttl_seconds=86400, priority="high", compression="gzip"
        )
        self.policies["application-assets"] = CachePolicy(
            "application-assets", "/static/**", "s3://assets",
            ttl_seconds=604800, priority="medium", compression="brotli"
        )
        self.policies["ml-models"] = CachePolicy(
            "ml-models", "*.tflite", "s3://models",
            ttl_seconds=2592000, priority="low"
        )

        for i in range(20):
            policy_key = list(self.policies.keys())[i % len(self.policies)]
            policy = self.policies[policy_key]
            key = f"cache:{policy.name}:obj-{i:04d}"
            entry = CacheEntry(
                key, policy.source,
                "application/octet-stream",
                (hash(f"data_{i}") % (10 * 1024 * 1024)) + 1024
            )
            entry.ttl_seconds = policy.ttl_seconds
            entry.access_count = hash(f"access_{i}") % 1000
            self.cache[key] = entry

    async def initialize(self):
        self._eviction_task = asyncio.create_task(self._eviction_loop())
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("EdgeCDN initialized with %d cached objects", len(self.cache))

    async def close(self):
        if self._eviction_task:
            self._eviction_task.cancel()
        if self._sync_task:
            self._sync_task.cancel()
        logger.info("EdgeCDN closed")

    async def _eviction_loop(self):
        while True:
            try:
                await asyncio.sleep(300)
                self._evict_if_needed()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Eviction error: %s", e)

    async def _sync_loop(self):
        while True:
            try:
                await asyncio.sleep(60)
                self._sync_statistics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Sync error: %s", e)

    def _evict_if_needed(self):
        total_bytes = sum(e.size_bytes for e in self.cache.values())
        max_bytes = self.max_disk_usage_gb * 1024 * 1024 * 1024
        if total_bytes <= max_bytes:
            return

        to_free = total_bytes - max_bytes
        freed = 0

        if self.eviction_policy == CachePolicy.LFU:
            sorted_entries = sorted(self.cache.values(), key=lambda e: e.access_count)
        elif self.eviction_policy == CachePolicy.LRU:
            sorted_entries = sorted(self.cache.values(), key=lambda e: e.last_accessed)
        elif self.eviction_policy == CachePolicy.TTL:
            sorted_entries = sorted(self.cache.values(), key=lambda e: e.created_at)
        else:
            sorted_entries = list(self.cache.values())

        for entry in sorted_entries:
            if freed >= to_free:
                break
            del self.cache[entry.key]
            freed += entry.size_bytes

        logger.info("Evicted %d bytes (%d objects)", freed, len(sorted_entries))

    def _sync_statistics(self):
        now = datetime.utcnow()
        for entry in self.cache.values():
            if entry.is_expired:
                pass

    def get(self, key: str) -> Optional[CacheEntry]:
        entry = self.cache.get(key)
        if entry and entry.is_expired:
            del self.cache[key]
            return None
        if entry:
            entry.last_accessed = datetime.utcnow()
            entry.access_count += 1
        return entry

    def put(self, key: str, source: str, content_type: str,
            size_bytes: int, ttl_seconds: Optional[int] = None,
            policy_name: Optional[str] = None) -> CacheEntry:
        entry = CacheEntry(key, source, content_type, size_bytes)
        if ttl_seconds:
            entry.ttl_seconds = ttl_seconds
        elif policy_name and policy_name in self.policies:
            entry.ttl_seconds = self.policies[policy_name].ttl_seconds
        entry.access_count = 1
        self.cache[key] = entry
        self._evict_if_needed()
        return entry

    def invalidate(self, pattern: str) -> int:
        import fnmatch
        keys_to_remove = [k for k in self.cache if fnmatch.fnmatch(k, f"*{pattern}*")]
        for k in keys_to_remove:
            del self.cache[k]
        return len(keys_to_remove)

    def warm(self, source: str, keys: list[str]) -> list[CacheEntry]:
        entries = []
        for key in keys:
            entry = CacheEntry(key, source, "application/octet-stream",
                               hash(key) % (1024 * 1024))
            entry.access_count = 0
            self.cache[key] = entry
            entries.append(entry)
        return entries

    def add_policy(self, name: str, pattern: str, source: str,
                   ttl_seconds: int = 86400, priority: str = "normal",
                   compression: Optional[str] = None) -> CachePolicy:
        policy = CachePolicy(name, pattern, source, ttl_seconds, priority, compression)
        self.policies[name] = policy
        return policy

    def get_stats(self) -> dict[str, Any]:
        total_objects = len(self.cache)
        total_bytes = sum(e.size_bytes for e in self.cache.values())
        total_hits = sum(e.access_count for e in self.cache.values())
        expired_count = sum(1 for e in self.cache.values() if e.is_expired)
        active_policies = sum(1 for p in self.policies.values() if p.enabled)

        return {
            "total_objects": total_objects,
            "total_size_bytes": total_bytes,
            "total_size_gb": round(total_bytes / (1024**3), 2),
            "total_hits": total_hits,
            "avg_hits_per_object": round(total_hits / max(total_objects, 1), 1),
            "expired_objects": expired_count,
            "active_policies": active_policies,
            "max_disk_gb": self.max_disk_usage_gb,
            "disk_usage_pct": round(total_bytes / (self.max_disk_usage_gb * 1024**3) * 100, 1),
            "eviction_policy": self.eviction_policy.value,
            "origin_shield_enabled": self.origin_shield.enabled,
        }

    def get_content_type_breakdown(self) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for entry in self.cache.values():
            ct = entry.content_type
            breakdown[ct] = breakdown.get(ct, 0) + 1
        return breakdown


class EdgeCDNCog(commands.Cog):
    """Discord cog for edge CDN management."""

    def __init__(self, bot):
        self.bot = bot
        self.cdn = EdgeCDN({})

    async def cog_load(self):
        await self.cdn.initialize()

    async def cog_unload(self):
        await self.cdn.close()

    @discord.app_commands.command(name="cdn_stats", description="Get CDN cache statistics")
    async def cdn_stats(self, interaction: discord.Interaction):
        stats = self.cdn.get_stats()
        embed = discord.Embed(title="Edge CDN Statistics", color=discord.Color.blue())
        embed.add_field(name="Cached Objects", value=stats["total_objects"], inline=True)
        embed.add_field(name="Cache Size", value=f"{stats['total_size_gb']} GB", inline=True)
        embed.add_field(name="Disk Usage", value=f"{stats['disk_usage_pct']}%", inline=True)
        embed.add_field(name="Total Hits", value=stats["total_hits"], inline=True)
        embed.add_field(name="Avg Hits/Object", value=stats["avg_hits_per_object"], inline=True)
        embed.add_field(name="Eviction Policy", value=stats["eviction_policy"], inline=True)
        embed.add_field(name="Active Policies", value=stats["active_policies"], inline=True)
        embed.add_field(name="Origin Shield", value="Enabled" if stats["origin_shield_enabled"] else "Disabled", inline=True)
        embed.add_field(name="Expired Objects", value=stats["expired_objects"], inline=True)
        embed.set_footer(text=f"Max disk: {stats['max_disk_gb']} GB")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="cdn_invalidate", description="Invalidate cached content")
    async def cdn_invalidate(self, interaction: discord.Interaction, pattern: str):
        count = self.cdn.invalidate(pattern)
        await interaction.response.send_message(f"Invalidated {count} objects matching '{pattern}'")

    @discord.app_commands.command(name="cdn_warm", description="Warm the cache with content")
    async def cdn_warm(self, interaction: discord.Interaction, source: str, keys: str):
        key_list = [k.strip() for k in keys.split(",")]
        entries = self.cdn.warm(source, key_list)
        await interaction.response.send_message(
            f"Warmed cache with {len(entries)} objects from {source}"
        )

    @discord.app_commands.command(name="cdn_policies", description="List cache policies")
    async def cdn_policies(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Cache Policies", color=discord.Color.blue())
        for name, policy in self.cdn.policies.items():
            embed.add_field(
                name=name,
                value=f"Source: {policy.source}\n"
                     f"Pattern: {policy.pattern}\n"
                     f"TTL: {policy.ttl_seconds}s\n"
                     f"Priority: {policy.priority}\n"
                     f"Compression: {policy.compression or 'none'}",
                inline=True
            )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="cdn_content_types", description="Show content type breakdown")
    async def cdn_content_types(self, interaction: discord.Interaction):
        breakdown = self.cdn.get_content_type_breakdown()
        embed = discord.Embed(title="Content Type Breakdown", color=discord.Color.blue())
        for ct, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=ct, value=str(count), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(EdgeCDNCog(bot))
