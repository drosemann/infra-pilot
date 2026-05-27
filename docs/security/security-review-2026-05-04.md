# security review (strict) — 2026-05-04

## scope
reviewed repository code for:
• command injection, path traversal, deserialization
• hardcoded secrets, unsafe dependencies
• race conditions and information leakage in error handling
• mit license notice and dependency-license inventory concerns

## real issues found

### 1) critical — command injection via shell execution in discord command handlers
where
• `services/orchestrator-agent/bot.py` (`port-forward-new` command)
• `services/orchestrator-agent/b2.py` (`execute_command` helper and `port-add` command path)

why this is real
• user-controlled `container_name` is interpolated into a shell command string and executed with `asyncio.create_subprocess_shell`, enabling shell metacharacter injection.
• in `b2.py`, a command string is passed to `bash -c` inside `docker exec`; while `container_port` is typed `int`, use of shell composition remains unsafe and fragile.

evidence
• `bot.py`: `command = f"docker exec -it {container_name} ..."` followed by `create_subprocess_shell(command, ...)`
• `b2.py`: generic `create_subprocess_shell(command, ...)` helper and `"bash", "-c", command` usage

impact
remote command execution as the bot host user from a discord slash command path.

### 2) high — hardcoded secrets and sensitive infrastructure data in source
where
• `services/orchestrator-agent/bot.py`
• `services/orchestrator-agent/b2.py`

why this is real
• source contains hardcoded token/api key placeholders and a real-looking api key literal plus fixed public ip and privileged whitelist id.
• these values are likely to be copied into deployments, leaked through forks, and can become active secret exposure if reused.

impact
credential leakage risk, infrastructure targeting, and weak secret hygiene incompatible with open-source publication best practices.

### 3) medium — error messages leak operational internals to end users
where
• `services/orchestrator-agent/bot.py`
• `services/orchestrator-agent/b2.py`

why this is real
• exception text is sent directly back to discord users (`{str(e)}` / `{e}`) for admin and non-admin workflows.
• runtime exceptions from docker/process/fs operations commonly include host paths, command fragments, container identifiers, and environment details.

impact
information disclosure that lowers attacker effort for lateral movement and exploit refinement.

### 4) medium — toctou race + non-atomic file mutation in local database handling
where
• `services/orchestrator-agent/bot.py`
• `services/orchestrator-agent/b2.py`

why this is real
• file update flow reads entire file then rewrites it without file locking (`open(..., 'r')` then `open(..., 'w')`).
• multiple concurrent bot commands can interleave and lose updates/corrupt state.

impact
authorization/state integrity issues (orphaned records, mistaken container ownership mappings), potentially enabling accidental cross-user actions.

### 5) medium — dependency risk: very old playwright pin in management panel
where
• `services/management-panel/package.json`

why this is real
• `@playwright/test` and `playwright` are pinned to `^1.40.0`, significantly behind current releases.
• large version lag increases probability of known unfixed vulnerabilities in transitive dependencies.

impact
supply-chain and ci/runtime security posture degradation.

### 6) compliance risk (mit project) — no machine-readable sbom/license inventory for dependencies
where
• dependency manifests across repo (`package.json`, `requirements.txt`, `pom.xml`)

why this is real
• for mit-licensed distribution, preserve the repository license notice and maintain dependency license attribution/compatibility records where applicable.
• repo currently lacks an auditable dependency license report/sbom and documented compliance workflow.

impact
potential accidental inclusion of incompatible licenses and downstream compliance violations when open-sourcing binaries/artifacts.
