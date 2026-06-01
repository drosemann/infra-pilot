import { useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useConfig } from '../lib/types';
import { LanguageSelector } from '../i18n/LanguageSelector';

interface SidebarItem {
  id: string;
  label: string;
  icon: string;
  route?: string;
  children?: SidebarItem[];
  attrs?: Record<string, string>;
}

const SimpleLogo = ({ size = 32 }: { size?: number }) => (
  <div
    className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold"
    style={{ width: size, height: size, fontSize: size * 0.4 }}
  >
    IP
  </div>
);

export const Sidebar = ({ isMobileOpen, onMobileClose }: { isMobileOpen?: boolean; onMobileClose?: () => void }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mode } = useConfig();
  const intl = useIntl();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpanded = (id: string) => {
    setExpandedItems((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const sidebarItems: SidebarItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: '📊',
      route: '/dashboard',
    },
    {
      id: 'bi-dashboard',
      label: 'BI Dashboard',
      icon: '📈',
      route: '/bi-dashboard',
    },
    {
      id: 'topology',
      label: '3D Topology',
      icon: '🌐',
      route: '/topology',
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: '📈',
      route: '/monitoring',
      attrs: { 'data-tour': 'monitoring' },
    },
    {
      id: 'apps',
      label: 'Apps',
      icon: '📦',
      route: '/apps',
      attrs: { 'data-tour': 'apps' },
    },
    {
      id: 'deployments',
      label: 'Deployments',
      icon: '🚀',
      route: '/deployments',
    },
    {
      id: 'logs',
      label: 'Logs',
      icon: '📝',
      children: [
        { id: 'live-logs', label: 'Live Logs', icon: '📋', route: '/logs' },
        { id: 'access-logs', label: 'Access Logs', icon: '🔐', route: '/logs/access' },
      ],
    },
    ...(mode === 'business'
      ? [
          {
            id: 'customers',
            label: 'Customers',
            icon: '👥',
            route: '/customers',
          },
          {
      id: 'billing',
      label: 'Billing',
      icon: '💳',
      route: '/billing',
    },
    {
      id: 'cost-analytics',
      label: 'Cost Analytics',
      icon: '💰',
      route: '/cost-analytics',
          },
          {
            id: 'teams',
            label: 'Teams',
            icon: '👨‍💼',
            route: '/teams',
          },
        ]
      : []),
    {
      id: 'dependencies',
      label: 'Dependencies',
      icon: '🔗',
      route: '/dependencies',
    },
    {
      id: 'backups',
      label: 'Backups',
      icon: '💾',
      route: '/backups',
      attrs: { 'data-tour': 'backups' },
    },
    {
      id: 'reports',
      label: 'Reports',
      icon: '📄',
      children: [
        { id: 'report-viewer', label: 'Report Viewer', icon: '📋', route: '/reports' },
        { id: 'report-builder', label: 'Report Builder', icon: '🛠️', route: '/reports/builder' },
      ],
    },
    {
      id: 'theme-studio',
      label: 'Theme Studio',
      icon: '🎨',
      route: '/theme-studio',
    },
    {
      id: 'knowledge-base',
      label: 'Knowledge Base',
      icon: '📚',
      route: '/knowledge-base',
    },
    {
      id: 'activity',
      label: 'Activity',
      icon: '📋',
      route: '/activity',
    },
    {
      id: 'dashboard-builder',
      label: 'Dashboards',
      icon: '📐',
      route: '/dashboard-builder',
    },
    {
      id: 'marketplace',
      label: 'Marketplace',
      icon: '🧩',
      route: '/marketplace',
    },
    {
      id: 'geo-heatmap',
      label: 'Geo Heatmap',
      icon: '🗺️',
      route: '/geo-heatmap',
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: '⚙️',
      attrs: { 'data-tour': 'settings' },
      children: [
        { id: 'general', label: 'General', icon: '🔧', route: '/settings' },
        { id: 'alerts', label: 'Alerts', icon: '🔔', route: '/settings/alerts' },
        { id: 'maintenance', label: 'Maintenance', icon: '🛠️', route: '/settings/maintenance' },
      ],
    },
  ];

  const isActive = (route?: string) => {
    if (!route) return false;
    return location.pathname.startsWith(route);
  };

  const handleNavigation = (route?: string) => {
    if (route) {
      navigate(route);
      onMobileClose?.();
    }
  };

  return (
    <>
      {isMobileOpen && <div className="fixed inset-0 z-20 bg-black/50 md:hidden" onClick={onMobileClose} />}
      <div className={`fixed md:sticky inset-y-0 left-0 z-30 w-56 h-screen bg-slate-900 dark:bg-slate-950 border-r border-slate-800 flex flex-col overflow-y-auto transition-transform duration-200 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
      {/* Logo Section */}
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => { navigate('/dashboard'); onMobileClose?.(); }}>
          <SimpleLogo size={40} />
          <div>
            <h1 className="text-lg font-bold text-white">Infra Pilot</h1>
            <p className="text-xs text-slate-400">v2.4.1</p>
          </div>
        </div>
      </div>

      {/* Organization Selector */}
      <div className="p-4 border-b border-slate-800">
        <button className="w-full px-3 py-2 bg-slate-800 hover:bg-slate-700 text-left rounded-lg transition-colors group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-white group-hover:text-blue-300 transition-colors">
                Acme Corp
              </p>
              <p className="text-xs text-slate-400">Production</p>
            </div>
            <span className="text-slate-500">▼</span>
          </div>
        </button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 p-4 space-y-2">
        {sidebarItems.map((item) => (
          <div key={item.id}>
            <button
              {...(item.attrs || {})}
              onClick={() => {
                if (item.children) {
                  toggleExpanded(item.id);
                } else {
                  handleNavigation(item.route);
                }
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive(item.route)
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="text-sm font-medium flex-1 text-left">{item.label}</span>
              {item.children && (
                <span
                  className={`transition-transform ${
                    expandedItems.includes(item.id) ? 'rotate-90' : ''
                  }`}
                >
                  ▶
                </span>
              )}
            </button>

            {/* Nested Items */}
            {item.children && expandedItems.includes(item.id) && (
              <div className="pl-4 space-y-1 mt-1">
                {item.children.map((child) => (
                  <button
                    key={child.id}
                    onClick={() => handleNavigation(child.route)}
                    className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                      isActive(child.route)
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    <span>{child.icon}</span>
                    <span>{child.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Docker Host Status */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <div className="px-3 py-2 bg-slate-800 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-white">Docker Host</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-xs text-green-400">Healthy</span>
            </span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <div className="flex justify-between">
              <span>CPU</span>
              <span className="font-semibold">23%</span>
            </div>
            <div className="w-full h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-green-500" style={{ width: '23%' }}></div>
            </div>
          </div>
          <div className="space-y-1 text-xs text-slate-300 mt-2">
            <div className="flex justify-between">
              <span>Memory</span>
              <span className="font-semibold">6.1 / 15.6 GB</span>
            </div>
            <div className="w-full h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500" style={{ width: '39%' }}></div>
            </div>
          </div>
          <div className="space-y-1 text-xs text-slate-300 mt-2">
            <div className="flex justify-between">
              <span>Disk</span>
              <span className="font-semibold">112 / 250 GB</span>
            </div>
            <div className="w-full h-1 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-orange-500" style={{ width: '45%' }}></div>
            </div>
          </div>
          <div className="space-y-1 text-xs text-slate-300 mt-2">
            <div className="flex justify-between">
              <span>Uptime</span>
              <span className="font-semibold">15d 6h 24m</span>
            </div>
          </div>
        </div>
      </div>

      {/* Help & Documentation */}
      <div className="p-4 border-t border-slate-800 space-y-2">
        <div className="px-2">
          <LanguageSelector />
        </div>
        <button className="w-full flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors text-sm">
          <span>❓</span>
          <span>Need help?</span>
        </button>
        <button className="w-full flex items-center gap-2 px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors text-sm">
          <span>📚</span>
          <span>Documentation</span>
        </button>
      </div>
    </div>
    </>
  );
};
