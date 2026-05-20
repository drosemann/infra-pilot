# Issue Triage Rules

Use labels to make the next action clear for maintainers and contributors. Prefer a small set of labels that describe readiness, scope, and contributor fit.

## Good First Issue

Apply `good first issue` when all of these are true:

- The issue can be solved in one or two focused files.
- The expected behavior is already described in the issue.
- A contributor can verify the change locally without production credentials.
- The task does not require architectural decisions, secret access, or ownership of an external service.
- A maintainer can review the result with a clear checklist.

Good examples:

- Add a missing README section for an existing setup command.
- Fix a typo or stale link in documentation.
- Add a small UI label, empty state, or validation message that follows an existing pattern.
- Add a focused unit test around already implemented behavior.

Poor examples:

- Redesign the management panel navigation.
- Add a new cloud provider integration.
- Rework billing, authentication, or deployment architecture.
- Debug a flaky production-only incident without a reproduction path.

## Help Wanted

Apply `help wanted` when the task is open to outside contributors but may require more project context than a first issue.

Good fits:

- Small service integrations with clear acceptance criteria.
- Test coverage for an existing feature.
- Documentation that benefits from operator feedback.
- Refactors where the target module and desired outcome are already named.

Avoid `help wanted` when the issue is still a question, needs product direction, or depends on credentials that only maintainers have.

## Needs Reproduction

Apply `needs repro` when a bug report describes symptoms but lacks enough detail to verify the problem.

Ask for:

- Exact command or user flow.
- Expected and actual behavior.
- Relevant service, environment, and version.
- Logs or screenshots with secrets removed.

Remove `needs repro` once a maintainer or contributor can reproduce the issue locally or in CI.
