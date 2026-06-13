import { useState, useEffect, useCallback } from 'react';
import { useIntl } from 'react-intl';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';
import { ThemeEditor, defaultTheme, type ThemeConfig } from '../components/ThemeStudio/ThemeEditor';
import { ThemePreview } from '../components/ThemeStudio/ThemePreview';
import { ThemeGallery } from '../components/ThemeStudio/ThemeGallery';
import { ThemeExport } from '../components/ThemeStudio/ThemeExport';

export const ThemeStudio = () => {
  const intl = useIntl();
  const [config, setConfig] = useState<ThemeConfig>(() => {
    const saved = localStorage.getItem('theme-config');
    return saved ? JSON.parse(saved) : defaultTheme;
  });

  useEffect(() => {
    localStorage.setItem('theme-config', JSON.stringify(config));
    applyTheme(config);
  }, [config]);

  const applyTheme = (cfg: ThemeConfig) => {
    const root = document.documentElement;
    root.style.setProperty('--brand-primary', cfg.colors.primary);
    root.style.setProperty('--brand-primary-dark', cfg.colors.primaryDark);
    root.style.setProperty('--brand-secondary', cfg.colors.secondary);
    root.style.setProperty('--brand-accent', cfg.colors.accent);
    root.style.setProperty('--bg-primary', cfg.colors.bgPrimary);
    root.style.setProperty('--bg-secondary', cfg.colors.bgSecondary);
    root.style.setProperty('--bg-card', cfg.colors.bgCard);
    root.style.setProperty('--text-primary', cfg.colors.textPrimary);
    root.style.setProperty('--text-secondary', cfg.colors.textSecondary);
    root.style.setProperty('--border-color', cfg.colors.borderColor);
    root.style.setProperty('--spacing-unit', `${cfg.spacing}px`);
    root.style.setProperty('--border-radius', `${cfg.borderRadius}px`);
    root.style.fontFamily = cfg.font;
  };

  const handleSelect = useCallback((theme: ThemeConfig) => {
    setConfig(theme);
    toast.success(`Theme "${theme.name}" applied`);
  }, []);

  const handleSave = async () => {
    try {
      await apiClient.saveTheme({ name: config.name, config: config });
      toast.success('Theme saved');
    } catch {
      toast.error('Failed to save theme');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            {intl.formatMessage({ id: 'themeStudio.title' })}
          </h1>
          <p className="text-slate-400">
            Customize the look and feel of your management panel
          </p>
        </div>
        <button
          onClick={handleSave}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
        >
          {intl.formatMessage({ id: 'common.save' })}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <ThemeEditor config={config} onChange={setConfig} />
          <ThemeExport config={config} />
        </div>
        <div className="space-y-6">
          <ThemePreview config={config} />
          <ThemeGallery onSelect={handleSelect} />
        </div>
      </div>
    </div>
  );
};
