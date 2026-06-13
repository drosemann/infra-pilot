import React from 'react';
import { useTheme } from '../theme/ThemeProvider';
import './LiquidGlass.css';

type CardProps = {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  variant?: 'elevated' | 'flat' | 'glass' | 'glassClear';
  compact?: boolean;
};

export const Card: React.FC<CardProps> = ({ title, subtitle, children, variant = 'elevated', compact = false }) => {
  const theme = useTheme() || {} as any;

  const glassClass =
    variant === 'glass' ? 'lg-glass lg-glass-morph' :
    variant === 'glassClear' ? 'lg-glass-clear lg-glass-morph' : '';

  const styles: React.CSSProperties = {};
  if (variant === 'elevated' || variant === 'flat') {
    styles.background = `linear-gradient(180deg, ${theme.colors?.surface ?? '#1a2333'} 0%, ${theme.colors?.surfaceAlt ?? '#101726'} 100%)`;
    styles.border = `1px solid ${theme.colors?.border ?? '#222'}`;
    styles.boxShadow =
      variant === 'elevated'
        ? `${theme.shadows?.skeuoRaised ?? theme.shadows?.elevation2 ?? 'none'}, ${theme.shadows?.skeuoInset ?? ''}`
        : 'none';
  }

  return (
    <div
      className={`ds-card ${glassClass}`}
      style={{
        borderRadius: (theme.radii?.medium ?? 10) as any,
        padding: (theme.space?.md ?? 12) as any,
        ...styles,
      }}
    >
      {title && <div style={{ fontWeight: (theme.fontWeights?.semibold ?? 600) as any }}>{title}</div>}
      {subtitle && <div style={{ color: theme.colors?.textSecondary }}>{subtitle}</div>}
      <div style={compact ? { paddingTop: 0 } : { paddingTop: 8 }}>{children}</div>
    </div>
  );
};

export default Card;
