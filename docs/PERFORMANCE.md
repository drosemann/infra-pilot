# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## perf/resource-monitor — non-blocking samples, lazy connections

- `resource_monitor.py` `collect_system_stats`: `psutil.cpu_percent(interval=1)`
  blocked ~1s per scrape; now primed once in `__init__` and sampled
  with `interval=None` (non-blocking delta since last call).
- `ResourceMonitor.__init__` no longer connects to Docker/MySQL at
  construction: both are lazy properties, and `mysql.connector` is
  imported lazily (it is not in `requirements.txt`, so the top-level
  import made the module unimportable in this environment).
- `collect_container_stats`: `df` output parsed by mount point (`/`)
  instead of fixed token index `[11]` — one layout change no longer
  discards the container's cpu/mem/network stats too.
- Verify: import the module without Docker/MySQL installed; scrape
  latency no longer has a ~1s floor. (Not run in this branch — run
  before merge.)
