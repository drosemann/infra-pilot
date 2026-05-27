# design system skeleton — starter template

a minimal, reusable design-system skeleton that wires tokens to core ui primitives (card, button, grid, donutchart) and provides layout scaffolding (sidebar, topbar) for a dense analytics dashboard.

## goals
• provide a clean, maintainable foundation for a pixel-parity dashboard ui.
• be token-driven to enable branding/theme swaps with minimal code changes.
• be react/typescript-friendly with a small, approachable api.

## tech stack (starter)
• react + typescript
• css variables + optional css-in-js (adapter-ready)
• lightweight es modules for tokens
• no heavy dependencies required for mvp

## repository layout (proposed)
• src/
  • design-tokens/
    • colors.ts
    • typography.ts
    • space.ts
    • radius.ts
    • shadow.ts
    • breakpoints.ts
  • design-system/
    • index.ts
    • theme/
      • themeprovider.tsx
      • usetheme.ts
    • components/
      • card.tsx
      • button.tsx
      • donutchart.tsx
      • grid.tsx
    • layout/
      • sidebar.tsx
      • topbar.tsx
  • pages/
    • demodashboard.tsx
  • docs/
    • design-tokens.md
    • design-system.md

## getting started (template)
• install dependencies (adjust to your package manager)
  • npm install
  • or yarn install
• start the development server
  • npm run start
• quick-start example (pseudo-code)
  ```tsx
  import React from 'react';
  import { ThemeProvider, Card, Button, DonutChart, Grid } from './design-system';
  import { colors } from './design-tokens/colors';

  const DemoDashboard: React.FC = () => (
    <ThemeProvider>
      <Grid columns={3} gap={16}>
        <Card title="Total Apps"><DonutChart value={72} size={80} color={colors.primary} /></Card>
        <Card title="Running" /><Card title="Uptime" />
      </Grid>
      <Button variant="primary" label="Create New App" />
    </ThemeProvider>
  );
  export default DemoDashboard;
  ```

## primitives api (mvp)
• card: title, subtitle, children, variant, compact
• button: label, variant, onclick, disabled
• donutchart: value, size, thickness, color
• grid: columns, gap, children
• layout: sidebar, topbar

## demo dashboard (phase 2 — demo-only)
• create a demodashboard page that uses ds primitives to render a dense dashboard layout with static data.

## theming and tokens
• this skeleton consumes tokens from the design tokens repo.
• themeprovider exposes a context for colors, typography, spacing, and shadows.
• css variables can be generated from tokens for css usage.

## accessibility
• ensure interactive controls have keyboard focus.
• provide aria labels for charts and live regions.

## documentation
• docs/design-tokens.md
• docs/design-system.md
• docs/quickstart.md

## contributing
• follow the project's contributing guidelines.
• add tests and update docs when introducing new tokens or components.
