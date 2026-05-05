import React from 'react';
import { colors } from '../../design-tokens/colors';
import { typography } from '../../design-tokens/typography';
import { space } from '../../design-tokens/space';
import { radii } from '../../design-tokens/radius';
import { shadows } from '../../design-tokens/shadow';
import { breakpoints } from '../../design-tokens/breakpoints';

type Theme = typeof colors & typeof typography & typeof space & typeof radii & typeof shadows & typeof breakpoints;

export const ThemeContext = React.createContext<Partial<Theme>>({});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme: Partial<Theme> = {
    colors,
    ...typography,
    ...space,
    ...radii,
    ...shadows,
    breakpoints,
  } as any;
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  // Cast to any to avoid heavy typing in this starter
  return React.useContext(ThemeContext) as any;
};
