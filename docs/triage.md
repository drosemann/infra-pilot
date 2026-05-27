# issue triage rules

use labels to make the next action clear for maintainers and contributors. prefer a small set of labels that describe readiness, scope, and contributor fit.

## good first issue

apply `good first issue` when all of these are true:

- the issue can be solved in one or two focused files.
- the expected behavior is already described in the issue.
- a contributor can verify the change locally without production credentials.
- the task does not require architectural decisions, secret access, or ownership of an external service.
- a maintainer can review the result with a clear checklist.

good examples:

- add a missing readme section for an existing setup command.
- fix a typo or stale link in documentation.
- add a small ui label, empty state, or validation message that follows an existing pattern.
- add a focused unit test around already implemented behavior.

poor examples:

- redesign the management panel navigation.
- add a new cloud provider integration.
- rework billing, authentication, or deployment architecture.
- debug a flaky production-only incident without a reproduction path.

## help wanted

apply `help wanted` when the task is open to outside contributors but may require more project context than a first issue.

good fits:

- small service integrations with clear acceptance criteria.
- test coverage for an existing feature.
- documentation that benefits from operator feedback.
- refactors where the target module and desired outcome are already named.

avoid `help wanted` when the issue is still a question, needs product direction, or depends on credentials that only maintainers have.

## needs reproduction

apply `needs repro` when a bug report describes symptoms but lacks enough detail to verify the problem.

ask for:

- exact command or user flow.
- expected and actual behavior.
- relevant service, environment, and version.
- logs or screenshots with secrets removed.

remove `needs repro` once a maintainer or contributor can reproduce the issue locally or in ci.
