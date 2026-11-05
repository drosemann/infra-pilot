import { useLocation } from 'react-router';
import { FormattedMessage, useIntl } from 'react-intl';
import { MaintenanceScheduler } from '../components/MaintenanceScheduler';
import { AlertConfig } from '../components/AlertConfig';
import { AlertHistory } from '../components/AlertHistory';
import { TwoFactorSetup } from '../components/TwoFactorSetup';
import MetricsConfig from '../components/MetricsConfig';
import { LanguageSelector } from '../i18n/LanguageSelector';
import { PageHeader } from '../components/PageHeader';

export const SettingsPage = () => {
  const location = useLocation();
  const intl = useIntl();
  const isAlerts = location.pathname.includes('/settings/alerts');
  const isMaintenance = location.pathname.includes('/settings/maintenance');

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader eyebrow="Configure">
        <h1 className="text-4xl font-semibold tracking-tight text-white"><FormattedMessage id="settings.title" /></h1>
        <p className="mt-2 text-white/55">
          {isAlerts ? intl.formatMessage({ id: 'nav.alerts' }) :
           isMaintenance ? intl.formatMessage({ id: 'nav.maintenance' }) :
           intl.formatMessage({ id: 'settings.general' })}
        </p>
      </PageHeader>

      {isAlerts ? (
        <>
          <AlertConfig />
          <AlertHistory />
        </>
      ) : isMaintenance ? (
        <MaintenanceScheduler />
      ) : (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">Language</h2>
            <LanguageSelector />
          </div>

          <TwoFactorSetup />

          <MetricsConfig />

          <MaintenanceScheduler />
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
