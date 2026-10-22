# Living Fleet — Implementation Plan

Status: **BARECODE v0 landed (single session, untested).** Skeleton exists;
all Phase 1–6 hardening, signal inventory, tests, and docs units are still open.
This file remains the single brief for implementing agents. Do not invent
contracts that contradict this plan without updating it first. Do not write
placeholder/demo behaviour: every phase below must work end-to-end
(orchestrator → panel → Discord → CLI) before it is marked done.

Barecode v0 files (untested, no deps installed, nothing run):

| Piece | File |
| --- | --- |
| Mood engine + JSON store + fleet handlers | `services/orchestrator-agent/living_fleet.py` |
| Fleet routes (wired) | `services/orchestrator-agent/webhook_server.py` (`/api/v1/fleet/…`) |
| CLI `ipilot pet list/status/rename` (registered) | `cli/ipilot/commands/pet.py`, `cli/ipilot/commands/__init__.py` |
| Discord `/pet`, `/pet-status` (registered) | `services/discord-service/modules/petCommands.js`, `services/discord-service/index.js` |
| Panel `<FleetPet>` (created, NOT mounted — see mount TODO in file) | `services/management-panel/src/components/FleetPet.tsx` |

Sources of truth this plan builds on (read before coding):

| Area | File(s) |
| --- | --- |
| Panel routes / UI | `services/management-panel/server/index.ts`, `services/management-panel/src/` |
| Panel docs | `services/management-panel/README.md`, OpenAPI at `/api/openapi.json` |
| Orchestrator routes, manifests, RBAC | `services/orchestrator-agent/webhook_server.py`, `manifest/`, `compute/`, `rbac/` |
| Orchestrator docs | `services/orchestrator-agent/README.md`, `services/orchestrator-agent/api_docs/openapi.yaml` |
| Discord integration | `services/discord-service/index.js`, `services/discord-service/modules/` |
| CLI | `cli/ipilot/main.py`, `cli/ipilot/commands/` |
| Docs contract | `docs/DOCUMENTATION.md` (25-line rule applies) |

---

## 1. Concept (one sentence)

Every managed app/container gets a persistent virtual creature whose
mood, health, hunger, growth stage, and (eventual) death/ghost state
are derived **exclusively** from real infrastructure signals Infra
Pilot already observes — deploys, restarts, CPU/memory pressure,
backup results, uptime, and patch recency.

Core promise: **the creature is never fake.** No random mood rolls, no
idle animation disconnected from telemetry. If the creature is sad,
something real is wrong or neglected. Operators should be able to
trace every emotion back to a metric, event, or config value in the UI.

### 1.1 Why this exists (product framing)

- Proxmox / OpenStack / Pterodactyl / Coolify / Portainer all present
  infrastructure as inert rows and graphs. Infra Pilot's philosophy
  (see root `README.md`) is Docker-native, API-first, observable,
  operator-owned. Living Fleet turns observability into attachment:
  operators *care for* their fleet, so they patch, back up, and
  investigate — the behaviours that actually keep a homelab / small
  fleet alive.
- Primary failure mode this attacks: **neglect.** Stale images,
  untested backups, silently crash-looping sidecars, certs expiring.
  A hungry/sick creature is a more effective nudge than a red graph
  nobody looks at.

### 1.2 Non-goals (explicit)

1. Not a game economy. No coins, shop, trading, breeding, PvP,
   leaderboards, or cross-operator interaction in v1.
2. No new telemetry stack. Do not add agents, exporters, or a metrics
   DB. Consume only signals the orchestrator/panel already have
   (see §3 inventory). If a signal does not exist, the plan marks it
   OPTIONAL/future — do not fabricate it.
3. No public multi-tenancy features. Infra Pilot is an internal ops
   tool (root `README.md` non-goals). Creatures are per-operator-fleet,
   not social.
4. Not a replacement for alerts. Existing health/alert paths stay
   authoritative. The creature is a *presentation + engagement* layer
   over the same truth. A "happy" creature must never suppress or
   contradict a real alert.
5. No AI/LLM-generated dialogue in v1. All creature speech is
   deterministic, template-based, and derived from the triggering
   signal (so it is always explainable). LLM flavour text is a future
   option (§12) behind a flag, never on the critical path.
6. No blockchain/NFT anything. Ever.

---

## 2. Product specification

### 2.1 Creature identity

Each creature is bound 1:1 to one *managed workload identity* — the
same identity the panel/orchestrator already use for an app/container
(manifest name / app id). Rules:

- **Birth:** a creature is born automatically the first time a
  workload is observed in a healthy running state. Birth records
  `born_at`, `workload_id`, `display_name` (defaults to workload
  name; operator-renamable, see §2.5).
- **Persistence:** the creature survives restarts, redeploys, and
  image updates of its workload. It is the workload's long-lived
  identity, not an instance/container-id identity. Rebuilding a
  container must not reset the creature.
- **Retirement:** if a workload is permanently deleted, its creature
  is retired (not deleted — see §2.4 graveyard). Retired creatures
  are read-only history.
- **One creature per workload, always.** No duplicates, no
  un-creatured workloads in the panel once the feature is enabled.
  Adoption/backfill for pre-existing workloads is part of Phase 1
  (§10).

### 2.2 Vital signs (the model)

Every creature has **5 core vitals**, each an integer `0–100`, plus a
derived **mood** and **stage**. Vitals are computed, never stored as
mutable counters that drift — see §4 for the computation contract.

| Vital | Meaning | Primary real signals |
| --- | --- | --- |
| `health` | Is it running correctly right now? | Container state, healthcheck result, restart count (windowed), OOM events, HTTP health probe if already configured |
| `energy` | Is it under resource pressure? | CPU utilisation %, memory utilisation % vs. limit, throttling if already exposed |
| `hunger` | Is it stale / under-maintained? | Days since last successful deploy/update, days since last image rebuild, pending update signal **iff** one already exists |
| `hygiene` | Is it protected? | Last backup result + age, snapshot age (orchestrator already tracks snapshots), secret/rotation age **iff** already tracked |
| `morale` | Is it reliable over time? | Rolling uptime %, successful deploy streak, days since last incident/downtime |

Invariants:

- Every vital must be explainable: the API returns, per vital, the
  list of contributing signals with their raw values (see §5.2).
  The panel renders this as "Why does Pixel feel like this?"
- A vital with **no available signal** is `null` (unknown), never
  defaulted to 50/100. Mood computation must handle null vitals
  explicitly (§4.3). Never fabricate a score from missing data.
- Vitals are computed on a schedule and on relevant events (§4.4),
  not on every panel page load.

### 2.3 Moods

Mood is a **derived enum**, exactly one at a time, computed from
vitals + lifecycle state. V1 mood set (closed enum — do not add moods
without updating this file and the API schema):

| Mood | Trigger sketch (exact thresholds in §4) | Panel/Discord presentation |
| --- | --- | --- |
| `thriving` | All known vitals high, no recent incident | Bright, animated, occasional happy template line |
| `content` | Default healthy state | Calm idle |
| `sleepy` | Long idle / near-zero traffic or CPU for a sustained window (only if signal exists) | Drowsy; **optional in v1, only when an idle signal is wired** |
| `hungry` | Hunger vital at or below 35 (no successful deploy for ~30 days) | Restless, rattling the food bowl |
| `sick` | Health vital at or below 35, failed healthcheck, or confirmed stopped | Pale, needs attention; never decorative |
| `stressed` | CPU at or above 85% or memory at or above 90% | Sweating, fanning itself |
| `sad` | Any known vital at or below 50 with no stronger mood match | Drooping, generally disappointed |
| `ghost` | Down 360+ minutes unacknowledged | Haunts the dashboard until resurrected |

*Note: this plan was cut off mid-table by a truncated write; the table above is now complete and matches `services/orchestrator-agent/living_fleet.py`. The remaining design sections (signal inventory, API contracts, rollout phases) are still to be restored.*
