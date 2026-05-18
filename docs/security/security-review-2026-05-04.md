# Security Review (strict) — 2026-05-04

## Scope
Reviewed repository code for:
- command injection, path traversal, deserialization
- hardcoded secrets, unsafe dependencies
- race conditions and information leakage in error handling
- MIT license notice and dependency-license inventory concerns

## Real issues found

### 1) Critical — Command injection via shell execution in Discord command handlers
**Where**
- `services/orchestrator-agent/bot.py` (`port-forward-new` command)
- `services/orchestrator-agent/b2.py` (`execute_command` helper and `port-add` command path)

**Why this is real**
- User-controlled `container_name` is interpolated into a shell command string and executed with `asyncio.create_subprocess_shell`, enabling shell metacharacter injection.
- In `b2.py`, a command string is passed to `bash -c` inside `docker exec`; while `container_port` is typed `int`, use of shell composition remains unsafe and fragile.

**Evidence**
- `bot.py`: `command = f"docker exec -it {container_name} ..."` followed by `create_subprocess_shell(command, ...)`
- `b2.py`: generic `create_subprocess_shell(command, ...)` helper and `"bash", "-c", command` usage

**Impact**
Remote command execution as the bot host user from a Discord slash command path.

### 2) High — Hardcoded secrets and sensitive infrastructure data in source
**Where**
- `services/orchestrator-agent/bot.py`
- `services/orchestrator-agent/b2.py`

**Why this is real**
- Source contains hardcoded token/API key placeholders and a real-looking API key literal plus fixed public IP and privileged whitelist ID.
- These values are likely to be copied into deployments, leaked through forks, and can become active secret exposure if reused.

**Impact**
Credential leakage risk, infrastructure targeting, and weak secret hygiene incompatible with open-source publication best practices.

### 3) Medium — Error messages leak operational internals to end users
**Where**
- `services/orchestrator-agent/bot.py`
- `services/orchestrator-agent/b2.py`

**Why this is real**
- Exception text is sent directly back to Discord users (`{str(e)}` / `{e}`) for admin and non-admin workflows.
- Runtime exceptions from Docker/process/FS operations commonly include host paths, command fragments, container identifiers, and environment details.

**Impact**
Information disclosure that lowers attacker effort for lateral movement and exploit refinement.

### 4) Medium — TOCTOU race + non-atomic file mutation in local database handling
**Where**
- `services/orchestrator-agent/bot.py`
- `services/orchestrator-agent/b2.py`

**Why this is real**
- File update flow reads entire file then rewrites it without file locking (`open(..., 'r')` then `open(..., 'w')`).
- Multiple concurrent bot commands can interleave and lose updates/corrupt state.

**Impact**
Authorization/state integrity issues (orphaned records, mistaken container ownership mappings), potentially enabling accidental cross-user actions.

### 5) Medium — Dependency risk: very old Playwright pin in management panel
**Where**
- `services/management-panel/package.json`

**Why this is real**
- `@playwright/test` and `playwright` are pinned to `^1.40.0`, significantly behind current releases.
- Large version lag increases probability of known unfixed vulnerabilities in transitive dependencies.

**Impact**
Supply-chain and CI/runtime security posture degradation.

### 6) Compliance risk (MIT project) — No machine-readable SBOM/license inventory for dependencies
**Where**
- Dependency manifests across repo (`package.json`, `requirements.txt`, `pom.xml`)

**Why this is real**
- For MIT-licensed distribution, preserve the repository license notice and maintain dependency license attribution/compatibility records where applicable.
- Repo currently lacks an auditable dependency license report/SBOM and documented compliance workflow.

**Impact**
Potential accidental inclusion of incompatible licenses and downstream compliance violations when open-sourcing binaries/artifacts.
