# design tokens — starter template

a token-based foundation for colors, typography, spacing, radii, and shadows that powers the ui design system. this document describes the token taxonomy, how to consume tokens in code, and how to extend them.

## goals
• provide a single source of truth for visual language (colors, typography, spacing, radii, shadows).
• expose tokens as both typescript modules and css variables for broad consumption.
• enable rapid theming and branding swaps without touching component code.

## token taxonomy

• colors
  • semantic surface tokens: surface, surface-2
  • text tokens: text, text-secondary
  • ui chrome: border
  • core palette: primary, accent, surface-accent, success, warning, danger, info
• typography
  • fontfamily, fontsizecale, lineheightscale, fontweight
  • a compact scale (e.g., 12, 14, 16, 20, 24, 32)
• spacing
  • a single spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64
• radii
  • radii: none, small, medium, large, pill
• shadows/elevation
  • elevation-1, elevation-2, focus-ring
• breakpoints
  • desktop, tablet, mobile

## token sources and formats

• typescript modules
  • src/design-tokens/colors.ts
  • src/design-tokens/typography.ts
  • src/design-tokens/space.ts
  • src/design-tokens/radius.ts
  • src/design-tokens/shadow.ts
  • src/design-tokens/breakpoints.ts
• css variables (css-internal theme)
  • themes.css (or generated at runtime)
• optional json interchange format
  • tokens/colors.json, tokens/typography.json, etc.

## token export strategy

• ts tokens for type-safe imports in components.
• css variables for plain css usage and css-in-js fallback.
• themeprovider (react) to bridge ts tokens to components.

## starter token files (examples)

• example colors.ts
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
• example typography.ts
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
• example space.ts
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
• example breakpoints.ts
  ```ts
  // src/design-tokens/breakpoints.ts
  export const breakpoints = {
    mobile: 0,
    tablet: 768,
    desktop: 1024,
  };
  ```

## token export strategy

• ts tokens for type-safe imports in components.
• css variables for plain css usage and css-in-js fallback.
• themeprovider (react) to bridge ts tokens to components.

## starter token files (examples)

• example colors.ts
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

## themeprovider — starter concept

• purpose: provide tokens via react context to components.
• basic structure (conceptual):
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

## consuming tokens

• in ts components: import { useTheme } from '.../themeprovider' and read theme.colors.primary, etc.
• in css: reference css vars like var(--color-primary) if you emit css vars from tokens.

## quick start

• add tokens to your repo (colors.ts, typography.ts, space.ts, etc.).
• wrap your app with themeprovider at the root.
• start consuming tokens in components.

## documentation and maintenance
• update this file whenever you introduce new tokens or token changes.
• maintain a changelog for token evolution.

## contributing
• prs should add token tests (where relevant) and update token docs if needed.
• follow the repo's contribution guidelines.
