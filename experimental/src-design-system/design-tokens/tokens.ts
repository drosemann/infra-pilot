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
export type ColorTokens = typeof colors;

export const space = {
  none: 0,
  xs: 4,
  s: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
};

export const radii = {
  none: 0,
  small: 6,
  medium: 10,
  large: 14,
  pill: 9999,
};

export const shadows = {
  elevation1: '0 1px 3px rgba(0,0,0,0.3)',
  elevation2: '0 6px 18px rgba(0,0,0,0.35)',
  focus: '0 0 0 2px rgba(78,168,255,0.5)',
  skeuoRaised: '0 10px 24px rgba(8, 15, 30, 0.3), 0 2px 6px rgba(8, 15, 30, 0.24)',
  skeuoInset: 'inset 0 1px 0 rgba(255,255,255,0.18), inset 0 -2px 4px rgba(8, 15, 30, 0.32)',
};

export const typography = {
  fontFamily:
    `'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif`,
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

export const breakpoints = {
  mobile: 0,
  tablet: 768,
  desktop: 1024,
};

export const glass = {
  regular: {
    background: 'rgba(11, 18, 32, 0.65)',
    blur: 'blur(40px) saturate(1.4)',
    border: 'rgba(255, 255, 255, 0.08)',
  },
  clear: {
    background: 'rgba(11, 18, 32, 0.35)',
    blur: 'blur(60px) saturate(1.8)',
    border: 'rgba(255, 255, 255, 0.06)',
  },
  prominent: {
    background: 'rgba(78, 168, 255, 0.2)',
    blur: 'blur(40px) saturate(1.4)',
    border: 'rgba(78, 168, 255, 0.15)',
  },
  light: {
    background: 'rgba(255, 255, 255, 0.08)',
    blur: 'blur(30px) saturate(1.2)',
    border: 'rgba(255, 255, 255, 0.1)',
  },
  dark: {
    background: 'rgba(0, 0, 0, 0.5)',
    blur: 'blur(50px) saturate(1.6)',
    border: 'rgba(255, 255, 255, 0.05)',
  },
};

export type GlassTokens = typeof glass;
