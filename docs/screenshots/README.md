# Screenshots

Browser captures use safe demo API responses (three demo apps and a demo
admin) rather than a live customer account. The capture process requires only
the local Vite frontend; no real hostnames, secrets, or personal data appear
in the images.

---

## Capture log

| File | Status | Captured from | Date |
| --- | --- | --- | --- |
| `01-dashboard.png` | verified | `/dashboard`, self-contained demo capture v0.1.0 | 2026-10-01 |
| `02-monitoring.png` | verified | `/monitoring` (shop-api selected), self-contained demo capture v0.1.0 | 2026-10-01 |
| `03-applications.png` | verified | `/apps/:id` (shop-api detail), self-contained demo capture v0.1.0 | 2026-10-01 |
| `04-backups.png` | verified | `/backups`, self-contained demo capture v0.1.0 | 2026-10-01 |
| `05-cli-gitops.png` | verified | `/settings`, self-contained demo capture v0.1.0 | 2026-10-01 |
| `tour.gif` | verified | generated from the five current captures | 2026-10-01 |

Promoting a file to `verified` requires a browser capture via
`scripts/capture-screenshots.mjs`, plus version, date, and environment filled
in above. One verified view of the highest-value
workflow beats five more concepts.

---

## Files

| File | View | Source fidelity |
| --- | --- | --- |
| `01-dashboard.png` | Dashboard hero, metrics, demo apps | Matches `src/pages/Dashboard.tsx` |
| `02-monitoring.png` | Throughput, health, live charts (shop-api) | Matches `src/pages/Monitoring.tsx` |
| `03-applications.png` | App detail with status and ports | Matches `src/pages/AppDetail.tsx` |
| `04-backups.png` | Retention stats and demo backup jobs | Matches `src/pages/Backups.tsx` |
| `05-cli-gitops.png` | Settings (general, 2FA, metrics) | Matches `src/pages/Settings.tsx` |
| `tour.gif` | Rotating tour of the current UI captures | Generated from current PNGs, 800x450, under 500 KB |

All PNG images are `1600x900`. The tour GIF is generated from the current captures and kept small
enough to pass the `check-added-large-files` hook.

---

## Regenerating

Use browser captures for future updates. The capture script includes safe demo
API responses, so it can run without a separate backend or personal data.

### 1. Real browser captures (preferred)

Requires Node.js 22+, Playwright Chromium, the local Vite frontend, and
Python 3 with Pillow installed (`python3 -m pip install Pillow`) to rebuild the GIF:

```bash
cd services/management-panel
npm install --legacy-peer-deps
npx playwright install chromium
npm run dev:frontend &
node ../../scripts/capture-screenshots.mjs
python3 -c "from PIL import Image; from pathlib import Path; p=Path('../../docs/screenshots'); f=[Image.open(p / n).convert('RGB').resize((800, 450)).convert('P', palette=Image.Palette.ADAPTIVE) for n in ['01-dashboard.png', '02-monitoring.png', '03-applications.png', '04-backups.png', '05-cli-gitops.png']]; f[0].save(p / 'tour.gif', save_all=True, append_images=f[1:], duration=1800, loop=0, optimize=True)"
```

The script navigates the local panel with intercepted demo responses and
overwrites the PNGs. The final command rebuilds the rotating GIF from those
captures. Review diffs before committing; mask secrets and personal data.

---

## Contribution rules

- Keep the same five filenames and dimensions.
- Update this README when views change materially.
- Do not commit screenshots with secrets, tokens, or
  personal data.
- Reference images from the root `README.md` only; wiki
  pages link back to the root for visual context.
