import React from 'react';

export const Topbar: React.FC = () => {
  return (
    <header style={{ height: 64, display: 'flex', alignItems: 'center', padding: '0 16px', background: '#0b1320', borderBottom: '1px solid #1b2a4a' }}>
      <div style={{ fontWeight: 600, color: '#e8f0ff' }}>Acme Corp / Production</div>
      <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
        <span style={{ color: '#9fb3d9' }}>Search</span>
        <span style={{ width: 32, height: 32, borderRadius: 16, background: '#1a2a50' }} />
      </div>
    </header>
  );
};

export default Topbar;
