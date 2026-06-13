export const theme = {
  colors: {
    primary: '#6C5CE7',
    secondary: '#EC4899',
    accent: '#22D3EE',
    background: '#0B0720',
    surface: '#11182B',
    surface2: '#0E1628',
    text: '#F6F3FF',
    textSecondary: '#A7B6D9',
    border: '#1B2A4A',
    success: '#4BD37B',
    warning: '#F2C14E',
    danger: '#F44336',
    info: '#58A6FF',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: {
    sm: 6,
    md: 10,
    lg: 16,
    xl: 24,
  },
  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 20,
    xl: 28,
    xxl: 36,
  },
};

export type Theme = typeof theme;
