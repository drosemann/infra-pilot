import React from 'react';
import { useTheme } from '../theme/ThemeProvider';
import '../components/LiquidGlass.css';

const navItems = [
  { label: 'Dashboard', icon: '◉' },
  { label: 'Apps', icon: '▦' },
  { label: 'Deployments', icon: '↗' },
  { label: 'Logs', icon: '☰' },
  { label: 'Customers', icon: '◉' },
  { label: 'Billing', icon: '$' },
  { label: 'Teams', icon: '◎' },
  { label: 'Settings', icon: '⚙' },
];

export const Sidebar: React.FC = () => {
  const theme = useTheme() as any;
  const glass = theme?.glass?.regular;

  return (
    <aside
      className="lg-glass lg-glass-morph"
      style={{
        width: 240,
        padding: 12,
        background: glass?.background ?? 'rgba(15, 26, 43, 0.65)',
        backdropFilter: glass?.blur ?? 'blur(40px) saturate(1.4)',
        WebkitBackdropFilter: glass?.blur ?? 'blur(40px) saturate(1.4)',
        border: `1px solid ${glass?.border ?? 'rgba(255,255,255,0.08)'}`,
        color: theme.colors?.text ?? '#cbd6e8',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 16, fontSize: 18, letterSpacing: '-0.02em' }}>
        Infra Pilot
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {navItems.map((item) => (
          <div
            key={item.label}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 14,
              color: theme.colors?.textSecondary ?? '#a7b6d9',
              transition: 'background 0.2s, color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
              e.currentTarget.style.color = theme.colors?.text ?? '#e9f0ff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.color = theme.colors?.textSecondary ?? '#a7b6d9';
            }}
          >
            <span style={{ width: 20, textAlign: 'center', opacity: 0.6 }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
