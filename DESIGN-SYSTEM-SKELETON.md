# Design System Skeleton — Starter Template

A minimal, reusable design-system skeleton that wires tokens to core UI primitives (Card, Button, Grid, DonutChart) and provides layout scaffolding (Sidebar, Topbar) for a dense analytics dashboard.

## Goals
- Provide a clean, maintainable foundation for a pixel-parity dashboard UI.
- Be token-driven to enable branding/theme swaps with minimal code changes.
- Be React/TypeScript-friendly with a small, approachable API.

## Tech Stack (Starter)
- React + TypeScript
- CSS Variables + optional CSS-in-JS (adapter-ready)
- Lightweight ES modules for tokens
- No heavy dependencies required for MVP

## Repository Layout (Proposed)
- src/
  - design-tokens/
    - colors.ts
    - typography.ts
    - space.ts
    - radius.ts
    - shadow.ts
    - breakpoints.ts
  - design-system/
    - index.ts
    - theme/
      - ThemeProvider.tsx
      - useTheme.ts
    - components/
      - Card.tsx
      - Button.tsx
      - DonutChart.tsx
      - Grid.tsx
    - layout/
      - Sidebar.tsx
      - Topbar.tsx
  - pages/
    - DemoDashboard.tsx
  - docs/
    - design-tokens.md
    - design-system.md

## Getting Started (Template)
- Install dependencies (adjust to your package manager)
  - npm install
  - or yarn install

- Start the development server
  - npm run start
- Quick-start example (pseudo-code)
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

## Primitives API (MVP)
- Card: title, subtitle, children, variant, compact
- Button: label, variant, onClick, disabled
- DonutChart: value, size, thickness, color
- Grid: columns, gap, children
- Layout: Sidebar, Topbar

## Demo Dashboard (Phase 2 — Demo-Only)
- Create a DemoDashboard page that uses DS primitives to render a dense dashboard layout with static data.

## Theming and Tokens
- This skeleton consumes tokens from the Design Tokens repo.
- ThemeProvider exposes a context for colors, typography, spacing, and shadows.
- CSS variables can be generated from tokens for CSS usage.

## Accessibility
- Ensure interactive controls have keyboard focus.
- Provide ARIA labels for charts and live regions.

## Documentation
- docs/design-tokens.md
- docs/design-system.md
- docs/quickstart.md

## Contributing
- Follow the project’s contributing guidelines.
- Add tests and update docs when introducing new tokens or components.
