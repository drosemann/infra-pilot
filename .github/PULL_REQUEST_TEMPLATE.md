# Pull request template

## Summary

<!-- What changes and why. Link issues with Closes #id. -->

## Changes

- [ ] ...
- [ ] ...

## Screenshots or API output

<!-- UI: attach before/after. API/CLI: paste command output. -->

## Verification

- [ ] `git diff --check` clean
- [ ] `pytest tests/ -q` passes
- [ ] Panel `npm run lint` and `npm test` pass (if touched)
- [ ] Docs updated (`README`, `wiki/`, service README as needed)
- [ ] No secrets, tokens, `.env`, or private keys committed
- [ ] Help, schema, or contract output recorded (if API/CLI changed)

```text
# Paste relevant command output here
```

## Risk and rollback

<!-- Impact, feature flags, migration notes, rollback steps. -->
