# Review process for agents

Use this process when reviewing a pull request, branch, or proposed change in
infra-pilot. The goal is to identify concrete regressions and risks, not to
rewrite the implementation or report preferences.

## 1. Establish the review scope

- Identify the target/base branch and compare the proposed changes with it.
- Read the diff and check the worktree status. Do not include unrelated,
  pre-existing changes in the review.
- Review the complete affected flow, including callers, contracts, tests, and
  documentation where relevant. The CLI, management panel, orchestrator,
  Discord bridge, deployment configuration, and docs can be separate parts of
  one feature.
- Read the relevant service README and existing tests before evaluating a
  service change. Use [docs/DOCUMENTATION.md](./docs/DOCUMENTATION.md) to find
  the source of truth and required documentation updates.

## 2. Look for defects

Prioritize issues that can cause incorrect behavior, data loss, security
exposure, outages, compatibility breaks, or failures in supported
configurations. Check, as applicable:

- Whether the implementation meets the requested behavior and handles
  invalid, missing, boundary, and failure inputs safely.
- Whether API, CLI, service, and deployment contracts agree across boundaries.
- Whether authentication, authorization/RBAC, validation, and trust boundaries
  remain enforced. Never expose or copy secrets, tokens, private keys, `.env`
  contents, or live user data into review output.
- Whether state changes, migrations, backup/restore, and rollback preserve
  existing user data.
- Whether tests exercise meaningful behavior and regressions, and whether
  documentation, examples, schemas, and screenshots are accurate when
  behavior changes.

Report only defects introduced by the change or directly exposed by it. Do not
report stylistic preferences, speculative concerns without a concrete failure
path, or unrelated pre-existing issues. Do not silently modify the reviewed
code.

## 3. Verify proportionately

- Run the smallest relevant existing tests, lint, or validation commands when
  practical. Follow the commands documented in
  [CONTRIBUTING.md](./CONTRIBUTING.md) and the affected service README.
- For cross-service changes, verify each changed side of the contract rather
  than treating one component's tests as proof of end-to-end correctness.
- Do not run commands against production or other live infrastructure.
- Record exact commands and whether each passed, failed, or was not run.
  Explain briefly when a relevant check could not be run.
- A review does not require running every repository check; report only checks
  relevant to the change.

## 4. Write findings first

List findings in descending severity, then confidence. Each finding must:

1. Point to the smallest relevant changed-file line range.
2. Describe the concrete impact and the conditions needed to trigger it.
3. Explain why the current implementation causes the problem.
4. Avoid prescribing a large redesign when a focused correction is enough.

Use these severity levels:

- **Critical** — likely severe compromise, broad data loss, or complete
  production outage under realistic conditions, with no reasonable recovery
  or workaround available.
- **High** — significant security, data integrity, availability, or core
  feature failure affecting a realistic supported scenario.
- **Medium** — a concrete, meaningful defect with limited impact or narrower
  triggering conditions.
- **Low** — a minor but demonstrable defect that is worth fixing.

Do not inflate severity for theoretical impact. If confidence is low, gather
more evidence or omit the finding.

Use this format for each finding:

```text
### [Severity] Short description

`path/to/file:line` — Explain the impact, trigger conditions, and evidence.
Confidence: high / medium / low
```

If there are no findings, say so explicitly. Do not invent findings to fill the
report.

## 5. Summarize the review

After findings, include a short verification section with the commands and
results. End with an overall assessment: **Approve**, **Approve with
non-blocking notes**, or **Request changes**. Base it on the findings and
verification, and state any important coverage limitations.

For a security review, follow the repository's
[SECURITY.md](./SECURITY.md) handling and disclosure guidance. Keep sensitive
vulnerability details out of public review output when disclosure could create
risk.
