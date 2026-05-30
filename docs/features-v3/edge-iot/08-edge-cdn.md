# Feature 8: Edge CDN / Content Distribution

## Overview
Distributed content caching at edge nodes. Pull-through cache for container images, Docker images, and application assets. Geo-distributed file synchronization for content delivery.

## Capabilities
- Distributed content caching at edge locations
- Pull-through cache for container registries (Docker Hub, GHCR, Quay)
- Geo-distributed file synchronization (rsync/rclone-based)
- Cache warming for popular content
- Smart cache eviction (LRU, LFU, TTL-based)
- Origin shield to reduce upstream bandwidth
- Content compression and optimization
- Cache statistics and hit ratio monitoring
- Multi-region replication with conflict resolution
- Signed URLs for private content

## Architecture

```
                         ┌─────────────────────────────┐
                         │      Origin Registry         │
                         │   (Docker Hub / GHCR / S3)   │
                         └──────────┬──────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │                │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
              │ Edge CDN   │  │ Edge CDN   │  │ Edge CDN   │
              │ Frankfurt  │  │ Singapore  │  │ Sao Paulo  │
              └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
                    │               │                │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
              │ Edge Node  │  │ Edge Node  │  │ Edge Node  │
              │ rpi-042    │  │ jetson-007 │  │ rock-015   │
              └───────────┘  └───────────┘  └───────────┘
```

## Cache Configuration

```yaml
edge_cdn:
  enabled: true
  cache_root: /var/cache/edge-cdn
  max_disk_usage_gb: 100
  cache_policies:
    - name: container-images
      source: docker.io
      pattern: "library/*"
      ttl: 24h
      priority: high
      compression: gzip
    
    - name: application-assets
      source: s3://my-bucket/assets
      pattern: "/static/**"
      ttl: 7d
      priority: medium
      compression: brotli
    
    - name: ml-models
      source: s3://my-bucket/models
      pattern: "*.tflite"
      ttl: 30d
      priority: low
      
  eviction_policy: lfu
  origin_shield:
    enabled: true
    max_stale: 72h
    retry_on_error: true
```

## Cache Statistics

Track the following metrics per edge node:
- Total cached objects
- Cache size (bytes)
- Hit ratio (hits / (hits + misses))
- Miss ratio by source
- Bandwidth saved (bytes not fetched from origin)
- Average download speed from origin
- Eviction rate (objects evicted per minute)
- Disk I/O statistics

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/edge_cdn.py`
- Test with simulated cache operations and registry mirrors
- CLI commands for cache management and warming
