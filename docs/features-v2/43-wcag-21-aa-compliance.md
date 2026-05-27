# feature 43: wcag 2.1 aa compliance

- feature id: 43
- status: planned
- priority: high
- primary service: management panel
- effort estimate: large (7-10 pt)
- dependencies: none

## overview

bring the management panel into conformance with the web content accessibility guidelines (wcag) 2.1 level aa. this covers screen-reader compatibility, keyboard-only navigation, visible focus indicators, sufficient colour contrast, aria landmark / live-region annotations, and respect for user reduced-motion preferences.

### goals

• achieve wcag 2.1 aa audit pass rate ≥ 95 % (automated tools + manual checks).
• every interactive element operable via keyboard alone.
• no information conveyed solely through colour.
• all motion / animation respects `prefers-reduced-motion`.

## architecture & component map

```
┌─────────────────────────────────────────────────────────────────┐
│                     Management Panel                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  AccessibilityProvider (React Context)                    │   │
│  │  • reads prefers-reduced-motion                           │   │
│  │  • exposes ariaAnnouncer (live region)                    │   │
│  │  • tracks focus trap state                                │   │
│  └──────────────┬────────────────────────────────────────────┘   │
│                 │                                                 │
│  ┌──────────────▼────────────────────────────────────────────┐   │
│  │  @infra-pilot/ui — component library                      │   │
│  │  • Button, Input, Select, Modal, Table, etc.             │   │
│  │  • each component owns its ARIA attributes                │   │
│  │  • focus management hooks (useFocusTrap, useTabIndex)     │   │
│  └──────────────┬────────────────────────────────────────────┘   │
│                 │                                                 │
│  ┌──────────────▼────────────────────────────────────────────┐   │
│  │  Pages / Features                                         │   │
│  │  • compose shared components                              │   │
│  │  • add page-level landmarks (<nav>, <main>, etc.)         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Audit Tooling (dev / CI)                                 │   │
│  │  • axe-core (unit + E2E)                                  │   │
│  │  • Lighthouse CI (per-PR gate)                            │   │
│  │  • Storybook → a11y addon                                 │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1 — foundation (2-3 pt)

• accessibilityprovider
  - create react context that reads `prefers-reduced-motion` via `matchMedia`.
  - provide an `announce(message, priority)` method backed by an `aria-live` region.
  - track modal / drawer open state to manage focus trapping.

• shared hooks
  - `useFocusTrap(containerRef, isActive)` — traps tab cycling.
  - `useSkipLink()` — renders a "skip to content" link.
  - `useAnnounce()` — convenience wrapper for the live region.

• ci audit gate
  - add `@axe-core/playwright` to e2e suite.
  - configure lighthouse ci to fail builds if accessibility score < 90.

### phase 2 — component audit & fixes (3-4 pt)

for each component in `@infra-pilot/ui`:

| component | required aria |
|---|---|
| button | `role="button"` (if not native `<button>`) |
| input | `aria-invalid`, `aria-describedby` (hint/error) |
| select | `aria-expanded`, `aria-activedescendant` |
| modal | `role="dialog"`, `aria-modal`, `aria-labelledby` |
| table | `<caption>`, `scope` on `<th>`, `aria-sort` |
| tabs | `role="tablist"`, `role="tab"`, `aria-selected` |
| toast | `role="alert"` / `aria-live="polite"` |
| tooltip | `role="tooltip"`, `aria-describedby` |

checklist applied to every component:
• visible focus ring (`:focus-visible`) — minimum 3 px offset.
• keyboard interaction spec documented in storybook.
• colour-contrast ratio ≥ 4.5 : 1 (normal) / 3 : 1 (large).
• no colour-only state indicators (add icons / underlines).
• respects `prefers-reduced-motion` — replace animations with instant transitions.

### phase 3 — page-level landmarks (1 pt)

- every top-level route renders `<SkipLink />`.
- pages use semantic landmarks: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`.
- dynamic content updates announced via `useAnnounce()`.

### phase 4 — qa & remediation (1-2 pt)

- run full axe-core scan on every route; fix violations.
- manual keyboard walk-through (tab, shift+tab, enter, escape, arrow keys).
- screen-reader testing with nvda (windows) and voiceover (macos).
- reduced-motion validation — enable os setting, verify all animations honour the preference.

## api design

most work is client-side; no new backend endpoints are required.
one new internal context api:

### `AccessibilityContext`

```typescript
interface AccessibilityContextValue {
  /** True when user prefers reduced motion */
  prefersReducedMotion: boolean;
  /** Send a message to the aria-live region */
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
  /** Register a focus trap; returns unregister function */
  registerFocusTrap: (id: string, containerRef: RefObject<HTMLElement>) => () => void;
}
```

### css custom properties for contrast

```css
:root {
  --a11y-focus-ring-color: #0066cc;
  --a11y-focus-ring-width: 3px;
  --a11y-focus-ring-offset: 2px;
  --a11y-motion-duration: 0ms;          /* overridden for reduced-motion */
  --a11y-motion-easing: step-start;
}
```

## data model

no new database tables. an audit-trail store (localstorage / indexeddb) may be added later for tracking user-driven accessibility preferences:

```typescript
interface A11yPreferences {
  highContrast?: boolean;        // optional forced high-contrast override
  fontSizeScale?: number;        // 1.0 = default, 1.25 = 125 %
  reducedMotionOverride?: 'auto' | 'reduce' | 'no-preference';
}
```

stored under key `infra-pilot:a11y-preferences`.

## service assignments

| service | role |
|---|---|
| management panel | all ui changes, component library audit, context provider, e2e |
| design (figma) | provide colour tokens with verified contrast ratios |
| qa | manual screen-reader + keyboard audit, lighthouse ci gate review |

## effort estimate

| phase | person-days |
|---|---|
| foundation (provider + ci) | 2-3 |
| component audit & fixes | 3-4 |
| page-level landmarks | 1 |
| qa & remediation | 1-2 |
| total | **7-10** |

## acceptance criteria

• all automated axe-core tests pass with zero violations.
• lighthouse a11y score ≥ 90 in ci.
• every `<button>`, `<a>`, `<input>`, `<select>`, `<textarea>` is reachable and operable by keyboard.
• visible focus indicator is present on all interactive elements.
• colour-contrast ratio ≥ 4.5 : 1 for body text.
• no information conveyed by colour alone (icons / labels added).
• all animations respect `prefers-reduced-motion`.
• screen-reader test passes for top-5 user flows (login, list servers, create server, edit config, view logs).
