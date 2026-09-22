# Changelog

All notable changes are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Pre-1.0: no tagged releases yet; entries track `main`.

## [Unreleased]

### Added

- Enterprise README with screenshots, architecture diagram,
  and operator guides.
- `docs/ARCHITECTURE.md` and `docs/OPERATIONS.md` as
  contributor and operator companions to the wiki.
- `docs/screenshots/` with five representative panel views
  plus regeneration instructions.
- `scripts/capture-screenshots.mjs` for real Playwright
  captures.
- GitHub pull request template and structured issue forms.
- `SUPPORT.md` with triage and redaction expectations.
- `.markdownlint.json` so the CI docs gate matches this repo
  (120 chars, tables and code blocks exempt).

### Fixed

- Panel sidebar no longer hardcodes `v2.4.1`. The version is
  injected at build time from `APP_VERSION` or the npm package
  version (`0.1.0`), matching the Helm chart.
- Wrapped long prose lines in `docs/` and `wiki/` to satisfy
  the markdownlint gate.

### Changed

- README rewritten in English with docs map, API table,
  deployment notes, and roadmap.
