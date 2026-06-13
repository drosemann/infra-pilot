import React from 'react';
import { useTheme } from '../theme/ThemeProvider';
import '../components/LiquidGlass.css';

export const Topbar: React.FC = () => {
  const theme = useTheme() as any;
  const glass = theme?.glass?.regular;

  return (
    <header
      className="lg-glass lg-glass-morph"
      style={{
        height: 56,
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        background: glass?.background ?? 'rgba(11, 18, 32, 0.65)',
        backdropFilter: glass?.blur ?? 'blur(40px) saturate(1.4)',
        WebkitBackdropFilter: glass?.blur ?? 'blur(40px) saturate(1.4)',
        border: `1px solid ${glass?.border ?? 'rgba(255,255,255,0.08)'}`,
        borderRadius: (theme?.radii?.medium ?? 10) as any,
        color: theme.colors?.text ?? '#e8f0ff',
      }}
    >
      <div style={{ fontWeight: 600, fontSize: 15 }}>Acme Corp / Production</div>
      <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
        <div
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            background: 'rgba(255,255,255,0.06)',
            fontSize: 13,
            color: theme.colors?.textSecondary ?? '#9fb3d9',
            cursor: 'pointer',
          }}
        >
          Search
        </div>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 16,
            background: 'linear-gradient(135deg, #4ea8ff, #7bd389)',
          }}
        />
      </div>
    </header>
  );
};

export default Topbar;
