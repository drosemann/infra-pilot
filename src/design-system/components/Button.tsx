import React from 'react';
import { useTheme } from '../theme/ThemeProvider';

type ButtonProps = {
  label: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  onClick?: () => void;
  disabled?: boolean;
};

export const Button: React.FC<ButtonProps> = ({ label, variant = 'primary', onClick, disabled }) => {
  const theme = useTheme() || {} as any;
  const base = {
    padding: 8,
    borderRadius: (theme.radii?.small ?? 6) as any,
    border: `1px solid ${theme.colors?.border ?? '#222'}`,
    cursor: disabled ? 'not-allowed' : 'pointer',
  } as React.CSSProperties;
  const styles: React.CSSProperties = {
    ...base,
    background:
      variant === 'primary'
        ? `linear-gradient(180deg, ${theme.colors?.primary ?? '#63b3ff'} 0%, ${theme.colors?.primaryDark ?? '#2d7dd2'} 100%)`
        : 'transparent',
    color: variant === 'ghost' ? theme.colors?.text ?? '#fff' : '#fff',
    opacity: disabled ? 0.5 : 1,
    boxShadow:
      variant === 'primary'
        ? `${theme.shadows?.skeuoRaised ?? '0 8px 20px rgba(0,0,0,0.25)'}, ${theme.shadows?.skeuoInset ?? 'inset 0 1px 0 rgba(255,255,255,0.25)'}`
        : 'none',
  };
  return (
    <button onClick={onClick} disabled={disabled} style={styles} aria-label={label}>
      {label}
    </button>
  );
};

export default Button;
