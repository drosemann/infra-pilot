# ai performance profiler

| field | value |
|-------|-------|
| id | f-008 |
| name | ai performance profiler |
| category | ai & intelligence |
| primary service | service core |
| effort | medium (4-6 pt) |
| dependencies | feature 1 (ai log anomaly detector), minecraft server agent |
| phase | phase 1 |

## overview

the ai performance profiler deeply profiles minecraft server tick performance to identify sources of lag and performance degradation. it tracks entity counts, redstone activity, plugin execution times, chunk loading patterns, and hardware utilization, then correlates these signals to produce actionable, prioritized recommendations for server administrators.

### goals

- identify tick lag sources within 60 seconds of profiling start
- pinpoint lag to specific entities, chunks, plugins, or redstone contraptions
- provide ranked, actionable fix suggestions with estimated impact
- track performance trends over time for proactive maintenance

### non-goals

- not a real-time monitoring dashboard (sessions are on-demand or scheduled)
- does not automatically modify server properties or plugins
- not a benchmarking tool (comparative performance across different servers)

## architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Minecraft Server (Target)                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                         Server Plugins                            │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │ │
│  │  │ Profiler   │  │ Entity     │  │ Redstone   │  │ Chunk      │ │ │
│  │  │ Agent      │  │ Tracker    │  │ Analyzer   │  │ Profiler   │ │ │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │                     Tick Execution Loop                       │ │ │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────┐ │ │ │
│  │  │  │Entities  │ │Tile Ent. │ │Chunks    │ │Plugins   │ │Phys│ │ │ │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
         │                          │
         │ RCON / Plugin API        │ Metrics via Agent
         ▼                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Service Core (Primary)                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Profile Orchestrator                         │  │
│  │  ┌───────────────┐ ┌───────────────┐ ┌──────────────────────┐ │  │
│  │  │ Profile       │ │ Data          │ │ Profile History      │ │  │
│  │  │ Scheduler     │ │ Collector     │ │ & Trends             │ │  │
│  │  └───────────────┘ └───────┬───────┘ └──────────────────────┘ │  │
│  └────────────────────────────┼───────────────────────────────────┘  │
│                               │                                       │
│  ┌────────────────────────────▼───────────────────────────────────┐  │
│  │                      Analysis Pipeline                           │  │
│  │                                                                  │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │  │
│  │  │ Tick Time        │  │ Entity Lag       │  │ Redstone Lag   │ │  │
│  │  │ Analyzer         │  │ Analyzer         │  │ Analyzer       │ │  │
│  │  │                  │  │                  │  │                │ │  │
│  │  │ - MSPT tracking  │  │ - Entity counts  │  │ - Active       │ │  │
│  │  │ - TPS calculation│  │ - Per-entity     │  │   contraptions │ │  │
│  │  │ - Phase breakdown│  │   tick time      │  │ - Update       │ │  │
│  │  │ - GC pressure    │  │ - AI mob farms   │  │   frequency    │ │  │
│  │  └──────────────────┘  │ - Hopper lag     │  │ - Chunk        │ │  │
│  │                        └──────────────────┘  │   loading      │ │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  └────────────────┘ │  │
│  │  │ Plugin Timing    │  │ Chunk & World    │  ┌────────────────┐ │  │
│  │  │ Analyzer         │  │ Analyzer         │  │ Suggestion     │ │  │
│  │  │                  │  │                  │  │ Engine         │ │  │
│  │  │ - Per-plugin MSPT│  │ - Chunk loading  │  │                │ │  │
│  │  │ - Event handler  │  │ - Mob spawning   │  │ - Prioritized  │ │  │
│  │  │   profiling      │  │ - Village/AI     │  │   fixes        │ │  │
│  │  │ - DB query times │  │ - Liquid physics │  │ - Impact       │ │  │
│  │  └──────────────────┘  └──────────────────┘  │   estimation   │ │  │
│  │                                                └────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                               │                                       │
│                               ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Report Generator                               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │ Flame Graph│  │ Timeline   │  │ Ranked     │  │ Export     │  │  │
│  │  │ Generator  │  │ Viewer     │  │ Issues     │  │ (PDF/JSON) │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Management Panel (UI)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Profile      │  │ Report View  │  │ Trend Chart  │  │Suggested │ │
│  │ Dashboard    │  │ (flame +     │  │ (MSPT over   │  │Fixes     │ │
│  │              │  │  timeline)   │  │  time)       │  │Panel     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### profiling flow

```
User starts profile ──► Profiler agent plugin injected
                           │
                           ▼
                    Profile Orchestrator manages session
                           │
                     ┌─────┴──────┐
                     ▼            ▼
              5-sec snapshot    Continuous 60s
              (quick check)     (deep profile)
                           │
                           ▼
                    Data Collector gathers:
                    - Per-tick MSPT (milliseconds per tick)
                    - Per-entity tick time
                    - Per-plugin hook execution times
                    - Chunk load/unload events
                    - GC pause events
                    - Redstone update counts
                           │
                           ▼
                    Analysis Pipeline (parallel)
                           │
                           ▼
                    Suggestion Engine ranks findings
                           │
                           ▼
                    Report generated with flame graphs
```

## implementation plan

### phase 1: profiler agent plugin (week 1, 1.5 pt)

1. **minecraft plugin (paper/bukkit/spigot)**
   - custom plugin loaded on-demand via rcon or plugin manager api
   - tick hook injection (using `servertickevents` / `scheduler`)
   - entity tracking via entity tick event listeners
   - plugin timing via `pluginmanager` call event hooks

2. **data collection modules**
   - **mspt sampler**: record per-tick mspt, tps, phase timing
   - **entity tracker**: per-entity-type count and tick time (mobs, items, minecarts, etc.)
   - **redstone analyzer**: count redstone updates per tick per chunk
   - **plugin timer**: wrap `onenable`, `ondisable`, event handlers with timing
   - **chunk profiler**: track loading/unloading, active chunk count
   - **gc monitor**: capture gc pause events via `garbagecollectormxbean`

3. **data export**
   - metrics pushed to service core via websocket or http post
   - configurable sampling interval (100ms, 500ms, 1s)
   - batch export every 1 second during profiling session

### phase 2: analysis pipeline (week 2-3, 2.5 pt)

1. **tick time analyzer**
   - parse mspt -> compute average, p50, p95, p99
   - break down tick phases: entities, tile entities, chunks, plugins, physics
   - identify "lag spikes" (ticks > 100ms for <20 tps)

2. **entity lag analyzer**
   - aggregate entity tick time by type, chunk, world
   - detect "entity hoarding" (>100 entities per chunk)
   - identify specific ai-heavy mobs (villagers, zombies, illagers)
   - find hopper lag (hoppers checking above them)
   - detect item frame clusters

3. **redstone lag analyzer**
   - identify chunks with excessive redstone updates (>1000/tick)
   - detect clock circuits (rapid toggling)
   - find piston animation spam
   - locate unloaded redstone chunks causing cascade loads

4. **plugin timing analyzer**
   - per-plugin average mspt contribution
   - per-event-handler timing breakdown
   - detect plugin event cascades (plugin a -> plugin b -> plugin c)
   - database query timing (if plugin uses external db)
   - identify plugins with >5ms/tick average overhead

5. **chunk & world analyzer**
   - active vs. loaded chunk ratio
   - mob cap utilization
   - liquid physics hotspot detection
   - village ai impact (golem spawning, gossip updates)

### phase 3: suggestion engine & reporting (week 3-4, 1.5 pt)

1. **suggestion engine**
   - knowledge base of 40+ common lag sources with fixes
   - pattern -> suggestion mapping with impact scoring

2. **report generator**
   - flame graph visualization (using d3-flame-graph)
   - timeline view (mspt over profile duration)
   - ranked issue list with severity, impact, effort
   - export to pdf, png, json

3. **historical trends**
   - store profile summaries in timeseries db
   - show mspt trend over days/weeks
   - alert on sustained high mspt

## api design

### endpoints

all endpoints are prefixed with `/api/v2/performance-profiler`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/profiles` | Start a new profiling session |
| `GET`  | `/profiles` | List profiles for a server |
| `GET`  | `/profiles/{profileId}` | Get profile report |
| `DELETE` | `/profiles/{profileId}` | Delete a profile |
| `GET`  | `/profiles/{profileId}/flamegraph` | Get flame graph data |
| `GET`  | `/profiles/{profileId}/timeline` | Get timeline data |
| `GET`  | `/profiles/{profileId}/suggestions` | Get ranked suggestions |
| `GET`  | `/trends/{serverId}` | Get MSPT trends over time |
| `GET`  | `/trends/{serverId}/anomaly` | Check for performance anomalies |

### request/response examples

**POST /api/v2/performance-profiler/profiles**

```json
{
  "server_id": "srv-mc-42",
  "duration_seconds": 60,
  "sampling_interval_ms": 200,
  "type": "deep",
  "modules": {
    "entity_tracking": true,
    "plugin_timing": true,
    "redstone_analysis": true,
    "chunk_profiling": true
  },
  "scheduled": false
}
```

**response**

```json
{
  "profile_id": "prof-20260527-abc789",
  "server_id": "srv-mc-42",
  "status": "completed",
  "started_at": "2026-05-27T14:30:00Z",
  "completed_at": "2026-05-27T14:31:00Z",
  "duration_seconds": 60,
  "total_ticks_sampled": 1200,
  "summary": {
    "average_mspt": 38.2,
    "min_mspt": 12.1,
    "max_mspt": 245.7,
    "p50_mspt": 32.5,
    "p95_mspt": 68.3,
    "p99_mspt": 142.8,
    "average_tps": 19.2,
    "ticks_below_20_tps": 45,
    "worst_ticks": [
      { "tick": 847, "mspt": 245.7, "cause": "chunk_load_storm" },
      { "tick": 312, "mspt": 198.3, "cause": "redstone_clock" },
      { "tick": 561, "mspt": 167.2, "cause": "entity_spawn" }
    ]
  },
  "phase_breakdown": {
    "entities": 14.2,
    "tile_entities": 4.1,
    "chunks": 8.3,
    "plugins": 6.5,
    "physics": 3.1,
    "other": 2.0
  },
  "top_issues": [
    {
      "rank": 1,
      "category": "redstone",
      "title": "redstone clock in overworld (chunk 12, -34)",
      "impact": "high",
      "current_mspt": 28.4,
      "estimated_after_fix": 10.2,
      "description": "detected a rapid redstone clock circuit toggling ~1200 times/second in chunk [12, -34]. this accounts for 18.4mspt.",
      "suggestion": "replace the clock with an observer-based design or reduce clock speed. consider using a hopper clock for slower timings.",
      "commands": [
        "/tp @s 192 64 -544",
        "/fill 192 64 -544 200 64 -536 air"
      ],
      "references": [
        "https://minecraft.wiki/w/Redstone_circuits#Clock_circuits"
      ]
    }
  ],
  "suggestions": [
    {
      "id": "sug-001",
      "category": "entities",
      "severity": "warning",
      "title": "excessive villager population in spawn chunks",
      "impact": "high",
      "effort": "medium",
      "current_value": "247 villagers in spawn chunks",
      "target_value": "<50 villagers per village",
      "description": "the spawn chunk village has 247 villagers causing significant ai tick overhead (~6.2mspt).",
      "fix": "move excess villagers to a trading hall outside spawn chunks, or reduce via natural causes.",
      "estimated_mspt_reduction": 5.1
    },
    {
      "id": "sug-002",
      "category": "plugins",
      "severity": "warning",
      "title": "plugin 'customenchants' taking 4.2mspt average",
      "impact": "medium",
      "effort": "low",
      "current_value": "4.2 mspt",
      "target_value": "<1.0 mspt",
      "description": "customenchants v3.1 consumes 4.2mspt on every tick, primarily in projectile-hit detection.",
      "fix": "update to v3.2+ which has projectile-hit optimization, or reduce enchantment tick checks via config.",
      "estimated_mspt_reduction": 3.5
    }
  ],
  "health_score": 62
}
```

## data model

```yaml
Profile:
  id: string (UUID)
  server_id: string
  status: "pending" | "running" | "completed" | "failed"
  type: "snapshot" | "deep" | "continuous"
  duration_seconds: integer
  sampling_interval_ms: integer
  started_at: datetime
  completed_at: datetime
  triggered_by: "manual" | "scheduled" | "alert"
  summary: ProfileSummary
  phase_breakdown: PhaseBreakdown
  tick_samples: TickSample[]
  entity_data: EntityProfilingData
  plugin_data: PluginProfilingData
  redstone_data: RedstoneProfilingData
  chunk_data: ChunkProfilingData
  suggestions: Suggestion[]

ProfileSummary:
  average_mspt: float
  min_mspt: float
  max_mspt: float
  p50_mspt: float
  p95_mspt: float
  p99_mspt: float
  average_tps: float
  ticks_below_20_tps: integer

PhaseBreakdown:
  entities_mspt: float
  tile_entities_mspt: float
  chunks_mspt: float
  plugins_mspt: float
  physics_mspt: float
  other_mspt: float

TickSample:
  tick_number: integer
  mspt: float
  tps: float
  entity_count: integer
  active_chunks: integer
  redstone_updates: integer
  plugin_hooks_run: integer
  gc_paused: boolean
  gc_pause_ms: float

EntityProfilingData:
  total_entities: integer
  by_type: dict
  by_chunk: dict
  top_entities_by_tick_time: EntityMetric[]
  hopper_count: integer
  hopper_tick_time: float
  item_count: integer
  item_frame_count: integer

PluginProfilingData:
  plugins: PluginMetric[]

PluginMetric:
  name: string
  version: string
  average_mspt: float
  max_mspt: float
  total_calls: integer
  event_handlers: EventHandlerMetric[]

EventHandlerMetric:
  event: string
  plugin: string
  average_ms: float
  max_ms: float
  calls: integer

RedstoneProfilingData:
  total_updates: integer
  updates_per_tick: integer
  hot_chunks: RedstoneChunkData[]

RedstoneChunkData:
  chunk_x: integer
  chunk_z: integer
  world: string
  updates_per_tick: integer
  estimated_mspt: float
  detected_circuit_type: string

ChunkProfilingData:
  total_loaded: integer
  total_active: integer
  spawn_chunk_entities: integer
  liquid_tick_hotspots: ChunkLocation[]

Suggestion:
  id: string (UUID)
  category: "entities" | "redstone" | "plugins" | "chunks" | "config" | "hardware"
  severity: "critical" | "warning" | "info"
  title: string
  description: string
  impact: "high" | "medium" | "low"
  effort: "high" | "medium" | "low"
  estimated_mspt_reduction: float
  current_value: string
  target_value: string
  fix: string
  commands: string[]
  references: string[]
  auto_fixable: boolean

ServerTrend:
  server_id: string
  period_start: datetime
  period_end: datetime
  daily_summaries: DailySummary[]

DailySummary:
  date: date
  avg_mspt: float
  max_mspt: float
  p95_mspt: float
  avg_tps: float
  peak_player_count: integer
  profile_count: integer
  suggestion_count: integer
```

## service assignments

| Service | Responsibility |
|---------|---------------|
| service core | primary: profile orchestration, analysis pipeline, suggestion engine, report generation, trend tracking |
| management panel | secondary: ui for profile dashboard, flame graph, timeline, suggestions panel, trend charts |
| orchestrator agent | secondary: deploy profiler plugin to target server, manage plugin lifecycle |
| discord service | none directly; may receive summary notifications |
| integration service | secondary: alert integration on performance anomaly detection |

## effort estimate

| Phase | Task | PT | Owner |
|-------|------|----|-------|
| P1 | Minecraft profiler plugin (Paper API) | 1.0 | Minecraft Dev |
| P1 | Data collector modules (entity, redstone, plugin) | 0.5 | Minecraft Dev |
| P2 | Tick time analyzer + flame graph data | 0.75 | Backend |
| P2 | Entity/redstone/plugin analysis pipeline | 1.0 | Backend |
| P2 | Chunk & world analyzer | 0.5 | Backend |
| P3 | Suggestion engine (40+ patterns) | 0.75 | Backend/GameDev |
| P3 | Report generator (flame graph, timeline, export) | 0.75 | Frontend |
| P3 | Trend tracking + dashboard | 0.5 | Frontend+Backend |
| total | | 5.75 pt | |

## risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Profiler plugin itself causes lag | high | ultra-lightweight sampling; disable in production by default; never sample >1% of tick time |
| minecraft version incompatibilities | medium | target paper 1.20+ api; version detection; graceful fallback to mspt-only mode |
| false positives in lag attribution | medium | cross-reference multiple indicators; confidence scoring; human validation loop |
| large servers with 100+ plugins | medium | plugin timing is best-effort; aggregate high-level data for overwhelmed servers |
| player privacy (player entities tracked) | low | anonymize player data; no uuid/username storage; aggregate by entity type only |
| redstone analysis on highly active servers | medium | enable redstone module only on-demand; set max update tracking threshold |

## suggestion knowledge base categories

| Category | Count | Examples |
|----------|-------|----------|
| Entity Optimization | 12 | Villager cap, hopper chains, item frames, AI mob farms, animal breeding caps |
| Redstone Optimization | 8 | Clock circuits, piston spam, comparator loops, observer chains |
| Plugin Optimization | 10 | Heavy event handlers, DB query frequency, async processing, scheduler usage |
| World Optimization | 6 | View-distance, simulation-distance, entity-activation-range, mob-spawn |
| Chunk Optimization | 5 | Spawn chunk management, lazy loading, pre-generation |
| Hardware/JVM | 4 | GC tuning, RAM allocation, CPU core pinning, SSD vs HDD |
| Network | 3 | Compression threshold, rate limits, proxy configuration |

## future enhancements

- v2.0: auto-remediation (apply fix suggestions via rcon)
- v2.1: player-reported lag correlation (where players experience lag)
- v2.2: cross-server profiling comparison
- v2.3: predictive lag detection (ml model trained on historical profiles)
- v2.4: modded server support (forge, fabric, neoforge)
- v2.5: profiling during specific activities (pvp, redstone tests, server startup)
