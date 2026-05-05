import React from 'react';

export const Sidebar: React.FC = () => {
  // Minimal static sidebar for demo skeleton
  return (
    <aside style={{ width: 240, padding: 12, background: '#0f1a2b', color: '#cbd6e8' }}>
      <div style={{ fontWeight: 700, marginBottom: 12 }}>Infra Pilot</div>
      <nav>
        <div>Dashboard</div>
        <div>Apps</div>
        <div>Deployments</div>
        <div>Logs</div>
        <div>Customers</div>
        <div>Billing</div>
        <div>Teams</div>
        <div>Settings</div>
      </nav>
    </aside>
  );
};

export default Sidebar;
