# ai assistant playbook

this playbook defines how ai contributors should work in `infra-pilot` to keep changes safe, maintainable, and easy to review.

## goals

• keep infrastructure operations reliable for a small team.
• favor secure defaults and explicit permission checks.
• ship small, testable increments instead of sweeping rewrites.
• preserve existing behavior unless a change request says otherwise.

## working agreement

• understand before changing
   • inspect the relevant service, docs, and tests first.
   • verify assumptions in code before proposing api or schema changes.
• choose the smallest safe path
   • prefer minimal diffs that solve the root cause.
   • avoid introducing abstractions that are not currently needed.
• design for operations
   • add useful logs for admin actions and failed automation.
   • handle external service outages and partial failures gracefully.
• build with security in mind
   • never hardcode secrets or tokens.
   • validate authorization for privileged actions.
   • validate and sanitize all external input.

## change checklist

before opening a pr, confirm:

• [ ] existing behavior is preserved unless intentionally changed.
• [ ] inputs are validated at boundaries.
• [ ] permission checks are present for admin or automation paths.
• [ ] errors are actionable and do not leak sensitive details.
• [ ] logs/audit events are adequate for incident response.
• [ ] tests cover critical path and failure modes.
• [ ] docs are updated when behavior or configuration changes.

## preferred implementation patterns

### service boundaries

• keep domain logic separate from infrastructure integrations.
• keep external clients (discord, vps apis, backup providers) behind focused modules.
• avoid mixing transport concerns with business decisions.

### reliability

• prefer idempotent operations when possible.
• retry only safe operations and cap retries.
• distinguish user-action errors from platform-health errors.

### security

• treat all webhook payloads and chat commands as untrusted.
• enforce role/permission checks before state mutation.
• record sensitive admin actions in audit-friendly logs.

## testing priorities

prioritize tests in this order:

• critical path behavior.
• permission-denied and invalid-input paths.
• external dependency failure handling (timeouts, downtime, bad responses).
• recovery/rollback behavior for automation flows.

## documentation expectations

when a feature changes, document:

• what changed and why.
• required environment/config updates.
• how operators verify healthy behavior.
• known failure cases and recovery steps.

## non-goals

• no broad refactors without a scoped migration plan.
• no hidden behavior changes to existing admin workflows.
• no speculative architecture work without a concrete near-term use case.
