import React from 'react';
import { useTheme } from '../theme/ThemeProvider';
import './LiquidGlass.css';

type ButtonProps = {
  label: string;
  variant?: 'primary' | 'secondary' | 'ghost' | 'glass' | 'glassProminent';
  onClick?: () => void;
  disabled?: boolean;
  style?: React.CSSProperties;
};

export const Button: React.FC<ButtonProps> = ({ label, variant = 'primary', onClick, disabled, style }) => {
  const theme = useTheme() || {} as any;
  const glassStyle = variant === 'glass' ? 'lg-glass-morph lg-glass' : variant === 'glassProminent' ? 'lg-glass-morph lg-glass-prominent' : '';

  const base: React.CSSProperties = {
    padding: '8px 16px',
    borderRadius: (theme.radii?.small ?? 6) as any,
    border: `1px solid ${theme.colors?.border ?? '#222'}`,
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontFamily: theme.typography?.fontFamily ?? 'inherit',
    fontSize: (theme.typography?.fontSizes?.sm ?? 14) as any,
    fontWeight: (theme.typography?.fontWeights?.medium ?? 500) as any,
    ...style,
  };

  if (variant === 'primary') {
    base.background = `linear-gradient(180deg, ${theme.colors?.primary ?? '#63b3ff'} 0%, ${theme.colors?.primaryDark ?? '#2d7dd2'} 100%)`;
    base.color = '#fff';
    base.boxShadow = `${theme.shadows?.skeuoRaised ?? '0 8px 20px rgba(0,0,0,0.25)'}, ${theme.shadows?.skeuoInset ?? 'inset 0 1px 0 rgba(255,255,255,0.25)'}`;
  } else if (variant === 'glass') {
    base.background = 'rgba(11, 18, 32, 0.65)';
    base.backdropFilter = 'blur(40px) saturate(1.4)';
    base.WebkitBackdropFilter = 'blur(40px) saturate(1.4)';
    base.color = theme.colors?.text ?? '#e9f0ff';
    base.border = '1px solid rgba(255, 255, 255, 0.08)';
  } else if (variant === 'glassProminent') {
    base.background = 'rgba(78, 168, 255, 0.2)';
    base.backdropFilter = 'blur(40px) saturate(1.4)';
    base.WebkitBackdropFilter = 'blur(40px) saturate(1.4)';
    base.color = theme.colors?.primary ?? '#4ea8ff';
    base.border = '1px solid rgba(78, 168, 255, 0.15)';
  } else if (variant === 'secondary') {
    base.background = 'transparent';
    base.color = theme.colors?.text ?? '#fff';
  } else if (variant === 'ghost') {
    base.background = 'transparent';
    base.color = theme.colors?.text ?? '#fff';
  }

  base.opacity = disabled ? 0.5 : 1;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={glassStyle}
      style={base}
      aria-label={label}
    >
      {label}
    </button>
  );
};

export default Button;
