# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## chore/dead-code-build — smaller repo, modern build target

- Removed tracked `python.exe` (274KB interpreter binary at repo root):
  smaller clone/fetch, no stray binary on PATH. If your workflow needs
  it back, keep it outside git (suggest `/*.exe` in `.gitignore`).
- `vite.config.ts`: non-Windows build target `safari13` → `es2020`.
  safari13 forces downlevel transpilation + helpers into every bundle;
  es2020 matches what the code actually uses. Expect faster builds and
  a smaller bundle (compare `vite build` output sizes before/after).
- Deliberately NOT deleted (correction of the review): orchestrator
  `fun_wave1-5.py` are lazily imported inside CLI command functions,
  so they cost zero startup/memory until invoked; the CLI `fun_wave*`
  commands are unregistered but harmless. The `.tl` mirrors and
  `traumalang-*` trees are a source-of-truth decision, not a perf
  issue — left for you. `effect` is genuinely used
  (`ServerOperationsHub`, `src/lib/effect/`) — kept.
- Verify: `git count-objects -v` / fresh clone size; `npm run build`
  duration + output bytes. (Not run in this branch — run before merge.)
