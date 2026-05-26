import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { apiClient } from './lib/api';
import { getAccessToken, setAccessToken } from './lib/auth';
import { ConfigContext, SetupMode } from './lib/types';
import { Setup } from './pages/Setup';
import { Dashboard } from './pages/Dashboard';
import Customers from './pages/Customers';
import { AppForm } from './pages/AppForm';
import { AppDetail } from './pages/AppDetail';
import { Monitoring } from './pages/Monitoring';
import { AccessLogs } from './pages/AccessLogs';
import { Backups } from './pages/Backups';
import { Reports } from './pages/Reports';
import { SettingsPage } from './pages/Settings';
import { BillingPage } from './pages/Billing';
import { AuditLog } from './pages/AuditLog';
import { MainLayout } from './components/MainLayout';
import { OnboardingWizard } from './components/OnboardingWizard';
import { GlobalSearch } from './components/GlobalSearch';
import { featureGates } from './lib/types';

const SimpleLogo = ({ size = 64 }: { size?: number }) => (
  <div
    className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-3xl"
    style={{ width: size, height: size }}
  >
    IP
  </div>
);

export default function App() {
  const [initialized, setInitialized] = useState(false);
  const [mode, setMode] = useState<SetupMode>('personal');
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      try {
        // Check setup status
        const status = await apiClient.getSetupStatus();

        if (!status.initialized) {
          setInitialized(false);
        } else {
          setInitialized(true);
          setMode(status.mode as SetupMode);

          // If we have a token, set it
          const token = getAccessToken();
          if (token) {
            apiClient.setToken(token);
            setAuthenticated(true);
          }
        }
      } catch (error) {
        console.error('Failed to check setup status:', error);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <SimpleLogo size={64} />
          <p className="text-slate-400 mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <ConfigContext.Provider value={{ mode, loading: false }}>
      <BrowserRouter>
        <Routes>
          {!initialized ? (
            <Route path="*" element={<Setup />} />
          ) : !authenticated ? (
            <Route path="*" element={<Navigate to="/setup" replace />} />
            ) : (
              <Route element={<MainLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/apps/new" element={<AppForm />} />
                <Route path="/apps/:appId" element={<AppDetail />} />
                <Route path="/apps/:appId/edit" element={<AppForm />} />
                <Route path="/logs/access" element={<AccessLogs />} />
                <Route path="/backups" element={<Backups />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/audit" element={<AuditLog />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/settings/alerts" element={<SettingsPage />} />
                <Route path="/settings/maintenance" element={<SettingsPage />} />
                {featureGates.canManageCustomers(mode) && (
                  <Route path="/customers" element={<Customers />} />
                )}
                {featureGates.canViewBilling(mode) && (
                  <Route path="/billing" element={<BillingPage />} />
                )}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            )}
        </Routes>
        <OnboardingWizard />
        <GlobalSearch />
      </BrowserRouter>
      <Toaster />
    </ConfigContext.Provider>
  );
}
