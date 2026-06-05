# feature 44: theme studio

- feature id: 44
- status: planned
- priority: medium
- primary service: management panel
- effort estimate: medium (4-6 pt)
- dependencies: feature 43 (wcag contrast tokens as baseline)

## overview

a visual theme builder that lets users customise the look and feel of the management panel without writing css. users manipulate colours, fonts, border radii, spacing, and shadows through a graphical editor, see changes in a live preview pane, and export the result as a portable json theme bundle. a community gallery allows sharing and discovering themes.

### goals

• reduce styling friction for operators who want white-label or dark-mode dashboards.
• provide a single-file export/import format so themes are portable across environments.
• ship with two built-in themes: light (default) and dark.
• community gallery backed by the existing api (themes stored as json blobs).

## architecture & component map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Theme Studio (Management Panel)              │
│                                                                     │
│  ┌──────────────────────┐      ┌────────────────────────────────┐   │
│  │  ThemeEditor          │      │  LivePreview                   │   │
│  │  ┌──────────────────┐ │      │  ┌──────────────────────────┐  │   │
│  │  │ ColourPicker     │ │      │  │ Mini dashboard mockup   │  │   │
│  │  │ FontSelector     │ │      │  │ (iframe / same-frame)    │  │   │
│  │  │ SpacingSliders   │ │      │  └──────────────────────────┘  │   │
│  │  │ BorderRadiusCtrls│ │      └────────────────────────────────┘   │
│  │  │ ShadowControls   │ │                                          │
│  │  └──────────────────┘ │                                          │
│  └──────────┬────────────┘                                          │
│             │                                                        │
│  ┌──────────▼────────────────────────────────────────────────────┐  │
│  │  ThemeEngine (core library)                                   │  │
│  │  • reads ThemeConfig (JSON schema)                            │  │
│  │  • generates CSS custom properties                            │  │
│  │  • applies to :root via style-setter                          │  │
│  │  • validates contrast ratios (reuses F43 helpers)             │  │
│  └──────────┬────────────────────────────────────────────────────┘  │
│             │                                                        │
│  ┌──────────▼────────────────────────────────────────────────────┐  │
│  │  ThemeStore (Zustand)                                        │  │
│  │  • current active theme                                      │  │
│  │  • draft (unsaved changes)                                   │  │
│  │  • gallery listing cache                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Backend (API gateway)                                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  GET/POST /api/v2/themes                                      │ │
│  │  GET/PUT/DELETE /api/v2/themes/:id                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## implementation plan

### phase 1 — theme engine (1-2 pt)

• define the themeconfig json schema (see §5).
• build the `ThemeEngine` class:
  - accepts a `ThemeConfig` object.
  - generates a flat map of css custom properties.
  - applies properties to `document.documentElement.style`.
  - validates colour-contrast ratios (reuse f43 helpers).
• write unit tests for serialisation, application, and contrast validation.

### phase 2 — editor ui (2 pt)

• build the `ThemeEditor` panel:
  - colour picker — grouped by token role (primary, surface, text, border, danger, success, warning).
  - font selector — system fonts + google fonts dropdown (optional).
  - spacing / radius / shadow sliders — adjust base unit (4 px grid).
• build the `LivePreview` pane:
  - renders a miniature dashboard (sidebar, cards, table, button, input).
  - can be an iframe pointing at a stripped-down preview route or a same-frame styled wrapper.
• connect editor changes to `ThemeEngine` → live preview updates in real-time (debounced 100 ms).

### phase 3 — persistence & portability (1 pt)

• export — serialize current `ThemeConfig` to json and trigger a file download (`theme-name.json`).
• import — file-upload input that validates against the json schema and applies the theme.
• save to profile — persist chosen theme per user via `PUT /api/v2/users/me/preferences { theme: { ... } }`.

### phase 4 — community gallery (1-2 pt)

• list endpoint `GET /api/v2/themes?page=&per_page=` — returns publicly shared themes.
• publish flow — user fills in name, description, tags; hits "publish"; theme is upserted to `POST /api/v2/themes`.
• gallery ui — grid of theme cards (thumbnail, name, author, usage count).
• "install" button — applies the theme locally and saves to preferences.

## api design

### endpoints

| method | path | description |
|---|---|---|
| `GET` | `/api/v2/themes` | list public themes (paginated) |
| `POST` | `/api/v2/themes` | publish a new theme |
| `GET` | `/api/v2/themes/:id` | get a single theme by id |
| `PUT` | `/api/v2/themes/:id` | update a published theme (owner) |
| `DELETE` | `/api/v2/themes/:id` | delete a theme (owner / admin) |
| `PUT` | `/api/v2/users/me/preferences` | save active theme as user pref |

### request / response example

```json
POST /api/v2/themes
{
  "name": "Midnight Ops",
  "description": "Dark theme optimized for NOC dashboards.",
  "tags": ["dark", "high-contrast", "noc"],
  "isPublic": true,
  "config": {
    "colors": {
      "primary": "#00bcd4",
      "surface": "#121212",
      "text": "#e0e0e0",
      "border": "#333333",
      "danger": "#cf6679",
      "success": "#4caf50",
      "warning": "#ff9800"
    },
    "fonts": {
      "heading": "'Inter', system-ui, sans-serif",
      "body": "'Inter', system-ui, sans-serif",
      "monospace": "'JetBrains Mono', monospace"
    },
    "radii": {
      "sm": 4,
      "md": 8,
      "lg": 12,
      "xl": 16,
      "full": 9999
    },
    "spacing": {
      "base": 4,
      "xs": 4,
      "sm": 8,
      "md": 16,
      "lg": 24,
      "xl": 32,
      "xxl": 48
    },
    "shadows": {
      "sm": "0 1px 2px rgba(0,0,0,0.3)",
      "md": "0 4px 6px rgba(0,0,0,0.4)",
      "lg": "0 10px 25px rgba(0,0,0,0.5)"
    }
  }
}

Response 201
{
  "id": "a1b2c3d4",
  "name": "Midnight Ops",
  "author": { "id": "u42", "name": "ops-admin" },
  "installCount": 0,
  "createdAt": "2026-05-27T12:00:00Z"
}
```

## data model

### themeconfig (json schema)

```typescript
interface ThemeConfig {
  colors: {
    primary: string;        // hex / hsl
    surface: string;
    text: string;
    border: string;
    danger: string;
    success: string;
    warning: string;
    // optional semantic overrides
    primaryHover?: string;
    surfaceAlt?: string;
    textMuted?: string;
  };
  fonts: {
    heading: string;        // font-family string
    body: string;
    monospace?: string;
  };
  radii: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
    full: number;           // typically 9999 for pills
  };
  spacing: {
    base: number;           // grid unit in px (default 4)
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl?: number;
  };
  shadows: {
    sm: string;             // full box-shadow value
    md: string;
    lg: string;
  };
}
```

### database (postgresql)

```sql
CREATE TABLE themes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id   UUID NOT NULL REFERENCES users(id),
  name        VARCHAR(128) NOT NULL,
  description TEXT,
  tags        TEXT[],
  config      JSONB NOT NULL,
  is_public   BOOLEAN NOT NULL DEFAULT false,
  install_count INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_themes_public ON themes (is_public, install_count DESC)
  WHERE is_public = true;
```

## service assignments

| service | role |
|---|---|
| management panel | themeengine library, editor ui, live preview, gallery ui |
| api gateway | theme crud endpoints, user-preference proxy |
| database | `themes` table |
| cdn / storage | optional: theme thumbnail images stored in s3-compatible bucket |

## effort estimate

| phase | person-days |
|---|---|
| theme engine + validation | 1-2 |
| editor ui + live preview | 2 |
| persistence / portability | 1 |
| community gallery | 1-2 |
| total | **4-6** |

## acceptance criteria

• users can edit every colour, font, radius, spacing, and shadow token via the visual editor.
• live preview reflects changes in ≤ 150 ms.
• export produces a valid `ThemeConfig` json file.
• import accepts the same json and applies the theme immediately.
• built-in light and dark themes are available on first load.
• community gallery lists public themes, supports search by tag.
• "install" applies the gallery theme and persists to user preferences.
• all custom themes are validated against the contrast-ratio rules from feature 43.
