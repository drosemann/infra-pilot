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
    background: variant === 'primary' ? theme.colors?.primary ?? '#4ea8ff' : 'transparent',
    color: variant === 'ghost' ? theme.colors?.text ?? '#fff' : '#fff',
    opacity: disabled ? 0.5 : 1,
  };
  return (
    <button onClick={onClick} disabled={disabled} style={styles} aria-label={label}>
      {label}
    </button>
  );
};

export default Button;
