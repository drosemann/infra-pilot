import React, { useMemo } from 'react';
import { useTheme } from '../theme/ThemeProvider';
import './LiquidGlass.css';

export type GlassVariant = 'regular' | 'clear' | 'prominent' | 'light' | 'dark';

type GlassEffectProps = {
  variant?: GlassVariant;
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
  morph?: boolean;
  id?: string;
};

const variantClassMap: Record<GlassVariant, string> = {
  regular: 'lg-glass',
  clear: 'lg-glass-clear',
  prominent: 'lg-glass-prominent',
  light: 'lg-glass-light',
  dark: 'lg-glass-dark',
};

export const GlassEffect: React.FC<GlassEffectProps> = ({
  variant = 'regular',
  children,
  style,
  className = '',
  morph = false,
  id,
}) => {
  const theme = useTheme() as any;
  const glass = theme?.glass?.[variant];

  const resolvedStyle: React.CSSProperties = useMemo(() => {
    if (glass) {
      return {
        background: glass.background,
        backdropFilter: glass.blur,
        WebkitBackdropFilter: glass.blur,
        border: `1px solid ${glass.border}`,
        borderRadius: (theme?.radii?.medium ?? 10) as any,
        ...style,
      };
    }
    return style;
  }, [glass, style, theme?.radii?.medium]);

  const cssClass = [
    morph ? 'lg-glass-morph' : '',
    !glass ? variantClassMap[variant] : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div id={id} className={cssClass} style={resolvedStyle}>
      {children}
    </div>
  );
};

export default GlassEffect;
