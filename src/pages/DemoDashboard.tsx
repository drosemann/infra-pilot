import React from 'react';
import { ThemeProvider } from '../design-system';
import Card from '../design-system/components/Card';
import Button from '../design-system/components/Button';
import DonutChart from '../design-system/components/DonutChart';
import Grid from '../design-system/components/Grid';
import Sidebar from '../design-system/layout/Sidebar';
import Topbar from '../design-system/layout/Topbar';

// Simple demo page that uses the skeleton DS to render a mock-like layout
export const DemoDashboard: React.FC = () => {
  return (
    <ThemeProvider>
      <div style={{ display: 'flex', minHeight: '100vh', background: '#0b1220', color: '#e9f0ff' }}>
        <Sidebar />
        <div style={{ flex: 1, padding: 16 }}>
          <Topbar />
          <h1 style={{ marginTop: 16 }}>Dashboard (Demo)</h1>
          <Grid columns={3} gap={16}>
            <Card title="Total Apps">
              <DonutChart value={24} size={90} />
            </Card>
            <Card title="Running Containers">
              <DonutChart value={18} size={90} color="#58a6ff" />
            </Card>
            <Card title="Errors">
              <DonutChart value={2} size={90} color="#f44336" />
            </Card>
          </Grid>
          <div style={{ height: 16 }} />
          <Grid columns={3} gap={16}>
            <Card title="Recent Activity">Demo data</Card>
            <Card title="System Overview">Demo data</Card>
            <Card title="Resource Distribution">Demo data</Card>
          </Grid>
          <div style={{ height: 16 }} />
          <Card title="Live Logs (Demo)" compact>
            <pre style={{ margin: 0, height: 120, overflowY: 'scroll', background: '#0a1220', color: '#cde5ff', padding: 8 }}>
{`[INFO] web-frontend: container started
[WARN] worker: queue size high
... (demo) ...`}
            </pre>
          </Card>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default DemoDashboard;
