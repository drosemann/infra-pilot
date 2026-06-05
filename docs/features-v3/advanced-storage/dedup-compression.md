# Feature 48: Deduplication & Compression

## Overview
Inline deduplication (zstd/btrfs/zfs) for container volumes. Per-volume dedup ratio reporting, savings dashboard.

## Components
- **Orchestrator Agent Cog**: `advanced-storage/dedup_compression.py` - Dedup management
- **Management Panel Page**: `advanced-storage/DedupCompression.tsx` - Savings dashboard

## Supported Technologies
- ZFS deduplication
- Btrfs deduplication
- ZSTD compression
- LZ4 compression
- VDO (Virtual Data Optimizer)
- Per-volume settings

## Features
- Inline deduplication
- Real-time compression
- Per-volume dedup ratio
- Savings dashboard
- Compression level selection
- Background dedup scanning
- Integrity verification
- Performance impact monitoring
