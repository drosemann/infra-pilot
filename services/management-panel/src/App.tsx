import { useEffect, useState, useCallback, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { IntlProvider } from 'react-intl';
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
import { ThemeStudio } from './pages/ThemeStudio';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { DashboardBuilder } from './pages/DashboardBuilder';
import { Marketplace } from './pages/Marketplace';
import { SDWANPage } from './pages/networking/SDWANPage';
import { VPNPage } from './pages/networking/VPNPage';
import { DNSManagementPage } from './pages/networking/DNSManagementPage';
import { BGPPage } from './pages/networking/BGPPage';
import { ReverseProxyPage } from './pages/networking/ReverseProxyPage';
import { SegmentationPage } from './pages/networking/SegmentationPage';
import { PacketCapturePage } from './pages/networking/PacketCapturePage';
import { DNSFilteringPage } from './pages/networking/DNSFilteringPage';
import { CostAnalyzerPage } from './pages/networking/CostAnalyzerPage';
import { CellularPage } from './pages/networking/CellularPage';
import { PolicyAsCodePage, AuditAnalyticsPage, DataClassificationPage, VendorRiskPage, BreachNotificationPage } from './pages/compliance/CompliancePages';
import BudgetForecast from './pages/finops/BudgetForecast';
import CostAnomalyDetection from './pages/finops/CostAnomalyDetection';
import CommitmentOptimizer from './pages/finops/CommitmentOptimizer';
import SpotManager from './pages/finops/SpotManager';
import { ResourceTradingPage } from './pages/marketplace/ResourceTradingPage';
import { AppMarketplacePage } from './pages/marketplace/AppMarketplacePage';
import { PayPerUsePage } from './pages/marketplace/PayPerUsePage';
import { ResellerPage } from './pages/marketplace/ResellerPage';
import { SLAPage } from './pages/marketplace/SLAPage';
import { CryptoPaymentPage } from './pages/marketplace/CryptoPaymentPage';
import { SubscriptionPlansPage } from './pages/marketplace/SubscriptionPlansPage';
import { UsageRecommendationsPage } from './pages/marketplace/UsageRecommendationsPage';
import { TaxAutomationPage } from './pages/marketplace/TaxAutomationPage';
import { LoyaltyPage } from './pages/marketplace/LoyaltyPage';
import GeolocationHeatmap from './pages/GeolocationHeatmap';
import CustomReportBuilder from './pages/CustomReportBuilder';
import BIDashboard from './pages/BIDashboard';
import DependencyGraphViewer from './pages/DependencyGraphViewer';
import CostAnalytics from './pages/CostAnalytics';
import Topology3D from './pages/Topology3D';
import { ActivityFeed } from './components/ActivityFeed';
import { MainLayout } from './components/MainLayout';
import { OnboardingWizard } from './components/OnboardingWizard';
import { GlobalSearch } from './components/GlobalSearch';
import { featureGates } from './lib/types';
import { I18nContext } from './i18n/index';
import { detectBrowserLocale, type SupportedLocale } from './i18n/locale-detector';
import { isRTL } from './i18n/locale-detector';
import { RTLProvider } from './i18n/rtl-support';
import { SkipLink } from './components/accessibility/SkipLink';
import { KeyboardShortcuts } from './components/accessibility/KeyboardShortcuts';
import en from './i18n/en.json';
import de from './i18n/de.json';
import zh from './i18n/zh.json';
import es from './i18n/es.json';
import fr from './i18n/fr.json';
import ja from './i18n/ja.json';
import pt from './i18n/pt.json';
import ru from './i18n/ru.json';
import ar from './i18n/ar.json';
import ko from './i18n/ko.json';
import tr from './i18n/tr.json';

const messages: Record<string, Record<string, string>> = {
  en, de, zh, es, fr, ja, pt, ru, ar, ko, tr,
};

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
  const [locale, setLocaleState] = useState<SupportedLocale>(detectBrowserLocale());

  const setLocale = useCallback((l: SupportedLocale) => {
    setLocaleState(l);
    localStorage.setItem('locale', l);
  }, []);

  const direction = useMemo(() => isRTL(locale) ? 'rtl' : 'ltr', [locale]);
  const i18nCtx = useMemo(() => ({ locale, setLocale, direction }), [locale, setLocale, direction]);

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
        const status = await apiClient.getSetupStatus();

        if (!status.initialized) {
          setInitialized(false);
        } else {
          setInitialized(true);
          setMode(status.mode as SetupMode);

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
    <IntlProvider messages={messages[locale]} locale={locale} defaultLocale="en">
      <I18nContext.Provider value={i18nCtx}>
        <RTLProvider>
          <ConfigContext.Provider value={{ mode, loading: false }}>
            <BrowserRouter>
              <SkipLink />
              <KeyboardShortcuts />
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
                <Route path="/activity" element={<ActivityFeed limit={50} />} />
                <Route path="/knowledge-base" element={<KnowledgeBase />} />
                <Route path="/knowledge-base/:articleId" element={<KnowledgeBase />} />
                <Route path="/dashboard-builder" element={<DashboardBuilder />} />
                <Route path="/dashboard-builder/:id" element={<DashboardBuilder />} />
                <Route path="/settings" element={<SettingsPage />} />
                      <Route path="/settings/alerts" element={<SettingsPage />} />
                      <Route path="/settings/maintenance" element={<SettingsPage />} />
                      <Route path="/theme-studio" element={<ThemeStudio />} />
                      {featureGates.canManageCustomers(mode) && (
                        <Route path="/customers" element={<Customers />} />
                      )}
                {featureGates.canViewBilling(mode) && (
                  <Route path="/billing" element={<BillingPage />} />
                )}
                <Route path="/finops/budget" element={<BudgetForecast />} />
                <Route path="/finops/anomalies" element={<CostAnomalyDetection />} />
                <Route path="/finops/commitments" element={<CommitmentOptimizer />} />
                <Route path="/finops/spot" element={<SpotManager />} />
                <Route path="/compliance/policy" element={<PolicyAsCodePage />} />
                <Route path="/compliance/audit-analytics" element={<AuditAnalyticsPage />} />
                <Route path="/compliance/data-classification" element={<DataClassificationPage />} />
                <Route path="/compliance/vendor-risk" element={<VendorRiskPage />} />
                <Route path="/compliance/breach-notification" element={<BreachNotificationPage />} />
                <Route path="/marketplace" element={<Marketplace />} />
                <Route path="/networking/sdwan" element={<SDWANPage />} />
                <Route path="/networking/vpn" element={<VPNPage />} />
                <Route path="/networking/dns" element={<DNSManagementPage />} />
                <Route path="/networking/bgp" element={<BGPPage />} />
                <Route path="/networking/proxy" element={<ReverseProxyPage />} />
                <Route path="/networking/segments" element={<SegmentationPage />} />
                <Route path="/networking/capture" element={<PacketCapturePage />} />
                <Route path="/networking/dnsfilter" element={<DNSFilteringPage />} />
                <Route path="/networking/cost" element={<CostAnalyzerPage />} />
                <Route path="/networking/cellular" element={<CellularPage />} />
                <Route path="/marketplace/trading" element={<ResourceTradingPage />} />
                <Route path="/marketplace/apps" element={<AppMarketplacePage />} />
                <Route path="/marketplace/ppu" element={<PayPerUsePage />} />
                <Route path="/marketplace/reseller" element={<ResellerPage />} />
                <Route path="/marketplace/sla" element={<SLAPage />} />
                <Route path="/marketplace/crypto" element={<CryptoPaymentPage />} />
                <Route path="/marketplace/plans" element={<SubscriptionPlansPage />} />
                <Route path="/marketplace/recommendations" element={<UsageRecommendationsPage />} />
                <Route path="/marketplace/tax" element={<TaxAutomationPage />} />
                <Route path="/marketplace/loyalty" element={<LoyaltyPage />} />
                <Route path="/geo-heatmap" element={<GeolocationHeatmap />} />
                <Route path="/reports/builder" element={<CustomReportBuilder />} />
                <Route path="/bi-dashboard" element={<BIDashboard />} />
                <Route path="/dependencies" element={<DependencyGraphViewer />} />
                <Route path="/cost-analytics" element={<CostAnalytics />} />
                <Route path="/topology" element={<Topology3D />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Route>
                  )}
              </Routes>
              <OnboardingWizard />
              <GlobalSearch />
            </BrowserRouter>
            <Toaster />
          </ConfigContext.Provider>
        </RTLProvider>
      </I18nContext.Provider>
    </IntlProvider>
  );
}
