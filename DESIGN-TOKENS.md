# Design Tokens — Starter Template

A token-based foundation for colors, typography, spacing, radii, and shadows that powers the UI design system. This document describes the token taxonomy, how to consume tokens in code, and how to extend them.

## Goals
- Provide a single source of truth for visual language (colors, typography, spacing, radii, shadows).
- Expose tokens as both TypeScript modules and CSS variables for broad consumption.
- Enable rapid theming and branding swaps without touching component code.

## Token Taxonomy

- Colors
  - Semantic surface tokens: surface, surface-2
  - Text tokens: text, text-secondary
  - UI chrome: border
  - Core palette: primary, accent, surface-accent, success, warning, danger, info
- Typography
  - fontFamily, fontSizeScale, lineHeightScale, fontWeight
  - A compact scale (e.g., 12, 14, 16, 20, 24, 32)
- Spacing
  - A single spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64
- Radii
  - radii: none, small, medium, large, pill
- Shadows/Elevation
  - elevation-1, elevation-2, focus-ring
- Breakpoints
  - desktop, tablet, mobile

## Token Sources and Formats

- TypeScript modules
  - src/design-tokens/colors.ts
  - src/design-tokens/typography.ts
  - src/design-tokens/space.ts
  - src/design-tokens/radius.ts
  - src/design-tokens/shadow.ts
  - src/design-tokens/breakpoints.ts
- CSS Variables (CSS-internal theme)
  - themes.css (or generated at runtime)
- Optional JSON interchange format
  - tokens/colors.json, tokens/typography.json, etc.

## Token Export Strategy

- TS tokens for type-safe imports in components.
- CSS variables for plain CSS usage and CSS-in-JS fallback.
- ThemeProvider (React) to bridge TS tokens to components.

## Starter Token Files (Examples)

- Example colors.ts
  ```ts
  // src/design-tokens/colors.ts
  export const colors = {
    background: "#0b1220",
    surface: "#11182b",
    surface2: "#0e1628",
    text: "#e9f0ff",
    textSecondary: "#a7b6d9",
    border: "#1b2a4a",
    primary: "#4ea8ff",
    accent: "#7bd389",
    success: "#4bd37b",
    warning: "#f2c14e",
    danger: "#f44336",
    info: "#58a6ff",
  };
  ```
- Example typography.ts
  ```ts
  // src/design-tokens/typography.ts
  export const typography = {
    fontFamily: `'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif`,
    fontSizes: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 20,
      xl: 24,
      xl2: 32,
    },
    lineHeights: {
      tight: 1.25,
      base: 1.5,
      loose: 1.75,
    },
    fontWeights: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  };
  ```
- Example space.ts
  ```ts
  // src/design-tokens/space.ts
  export const space = {
    none: 0,
    xs: 4,
    s: 8,
    md: 12,
    lg: 16,
    xl: 24,
    xxl: 32,
  };
  ```
- Example breakpoints.ts
  ```ts
  // src/design-tokens/breakpoints.ts
  export const breakpoints = {
    mobile: 0,
    tablet: 768,
    desktop: 1024,
  };
  ```

## Token Export Strategy

- TS tokens for type-safe imports in components.
- CSS variables for plain CSS usage and CSS-in-JS fallback.
- ThemeProvider (React) to bridge TS tokens to components.

## Starter Token Files (Examples)

- Example colors.ts
  ```ts
  // src/design-tokens/colors.ts
  export const colors = {
    background: "#0b1220",
    surface: "#11182b",
    surface2: "#0e1628",
    text: "#e9f0ff",
    textSecondary: "#a7b6d9",
    border: "#1b2a4a",
    primary: "#4ea8ff",
    accent: "#7bd389",
    success: "#4bd37b",
    warning: "#f2c14e",
    danger: "#f44336",
    info: "#58a6ff",
  };
  ```

## ThemeProvider — starter concept

- Purpose: provide tokens via React context to components.
- Basic structure (conceptual):
  ```tsx
  // src/design-system/theme/ThemeProvider.tsx
  import React from 'react';
  import { colors } from '../../design-tokens/colors';
  import { typography } from '../../design-tokens/typography';
  // ... import other token groups

  export const ThemeContext = React.createContext({});

  export const ThemeProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
    const theme = {
      colors,
      typography,
      // space, radii, shadow, breakpoints
    };
    return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
  };

  export const useTheme = () => React.useContext(ThemeContext);
  ```

## Consuming Tokens

- In TS components: import { useTheme } from '.../ThemeProvider' and read theme.colors.primary, etc.
- In CSS: reference CSS vars like var(--color-primary) if you emit CSS vars from tokens.

## Quick Start

- Add tokens to your repo (colors.ts, typography.ts, space.ts, etc.).
- Wrap your app with ThemeProvider at the root.
- Start consuming tokens in components.

## Documentation and Maintenance
- Update this file whenever you introduce new tokens or token changes.
- Maintain a changelog for token evolution.

## Contributing
- PRs should add token tests (where relevant) and update token docs if needed.
- Follow the repo’s contribution guidelines.
