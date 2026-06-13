import React from 'react';
import { ThemeProvider } from '../design-system';
import Card from '../design-system/components/Card';
import Button from '../design-system/components/Button';
import DonutChart from '../design-system/components/DonutChart';
import Grid from '../design-system/components/Grid';
import GlassEffect from '../design-system/components/GlassEffect';
import GlassEffectContainer from '../design-system/components/GlassEffectContainer';
import Sidebar from '../design-system/layout/Sidebar';
import Topbar from '../design-system/layout/Topbar';

export const DemoDashboard: React.FC = () => {
  return (
    <ThemeProvider>
      <div
        style={{
          display: 'flex',
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0b1220 0%, #0d1a2d 40%, #0f1428 100%)',
          color: '#e9f0ff',
        }}
      >
        <Sidebar />
        <div style={{ flex: 1, padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Topbar />

          <GlassEffectContainer>
            <GlassEffect variant="clear" style={{ padding: 24, borderRadius: 14 }}>
              <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>Dashboard</h1>
              <p style={{ margin: '4px 0 0', color: '#a7b6d9', fontSize: 14 }}>
                Liquid Glass interface — dynamically adapting to content beneath
              </p>
            </GlassEffect>
          </GlassEffectContainer>

          <GlassEffectContainer>
            <Grid columns={3} gap={16}>
              <GlassEffect variant="regular" style={{ padding: 16, borderRadius: 10 }}>
                <Card title="Total Apps" variant="flat" compact>
                  <DonutChart value={24} size={90} />
                </Card>
              </GlassEffect>
              <GlassEffect variant="regular" style={{ padding: 16, borderRadius: 10 }}>
                <Card title="Running Containers" variant="flat" compact>
                  <DonutChart value={18} size={90} color="#58a6ff" />
                </Card>
              </GlassEffect>
              <GlassEffect variant="regular" style={{ padding: 16, borderRadius: 10 }}>
                <Card title="Errors" variant="flat" compact>
                  <DonutChart value={2} size={90} color="#f44336" />
                </Card>
              </GlassEffect>
            </Grid>
          </GlassEffectContainer>

          <Grid columns={3} gap={16}>
            <Card title="Recent Activity" variant="glass">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['Deploy web v2.1', 'Scaling worker pool', 'Backup completed'].map((item, i) => (
                  <div key={i} style={{ fontSize: 13, color: '#a7b6d9', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    {item}
                  </div>
                ))}
              </div>
            </Card>
            <Card title="System Overview" variant="glass">
              <div style={{ fontSize: 13, color: '#a7b6d9', lineHeight: 1.6 }}>
                CPU: 34%<br />
                Memory: 62%<br />
                Network: 1.2 Gbps
              </div>
            </Card>
            <Card title="Resource Distribution" variant="glassClear">
              <DonutChart value={67} size={80} color="#7bd389" />
            </Card>
          </Grid>

          <div style={{ display: 'flex', gap: 8 }}>
            <Button variant="glass" label="Refresh" />
            <Button variant="glassProminent" label="New Deployment" />
            <Button variant="primary" label="Create App" />
            <Button variant="secondary" label="Cancel" />
          </div>

          <GlassEffect variant="dark" style={{ borderRadius: 10, overflow: 'hidden' }}>
            <Card title="Live Logs (Demo)" variant="flat" compact>
              <pre
                style={{
                  margin: 0,
                  height: 120,
                  overflowY: 'scroll',
                  background: 'rgba(10, 18, 32, 0.6)',
                  color: '#cde5ff',
                  padding: 8,
                  fontSize: 12,
                  borderRadius: 6,
                }}
              >
{`[INFO] web-frontend: container started
[WARN] worker: queue size high
[INFO] db: connection pool healthy
[OK]   health-check: all services passing`}
              </pre>
            </Card>
          </GlassEffect>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default DemoDashboard;
