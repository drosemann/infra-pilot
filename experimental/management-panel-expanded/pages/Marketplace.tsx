import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { PluginCard } from '../components/PluginCard';
import { toast } from 'sonner';
import { Plugin } from '../lib/types';

export const Marketplace = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [installing, setInstalling] = useState<string | null>(null);
  const [uninstalling, setUninstalling] = useState<string | null>(null);

  const categories = ['all', 'performance', 'security', 'backup', 'monitoring', 'logging', 'scaling', 'configuration', 'integration'];

  useEffect(() => {
    loadPlugins();
  }, []);

  const loadPlugins = async () => {
    setLoading(true);
    try {
      const data = await apiClient.listPlugins();
      setPlugins(data);
    } catch {
      toast.error('Failed to load plugins');
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async (id: string) => {
    setInstalling(id);
    try {
      await apiClient.installPlugin(id, '');
      toast.success('Plugin installed');
      loadPlugins();
    } catch {
      toast.error('Failed to install plugin');
    } finally {
      setInstalling(null);
    }
  };

  const handleUninstall = async (id: string) => {
    setUninstalling(id);
    try {
      await apiClient.uninstallPlugin(id, '');
      toast.success('Plugin uninstalled');
      loadPlugins();
    } catch {
      toast.error('Failed to uninstall plugin');
    } finally {
      setUninstalling(null);
    }
  };

  const filteredPlugins = plugins.filter(p => {
    if (categoryFilter !== 'all' && p.category !== categoryFilter) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase()) && !p.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Plugin Marketplace</h1>
          <p className="text-slate-400">Extend your infrastructure with community-built plugins</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search plugins..."
            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <button
          onClick={loadPlugins}
          className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setCategoryFilter(cat)}
            className={`px-3 py-1.5 text-xs rounded-lg border capitalize transition-colors ${
              categoryFilter === cat
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12">
          <p className="text-slate-400">Loading plugins...</p>
        </div>
      ) : filteredPlugins.length === 0 ? (
        <div className="text-center py-12 bg-slate-800 border border-slate-700 rounded-lg">
          <p className="text-slate-400">No plugins found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPlugins.map(plugin => (
            <PluginCard
              key={plugin.id}
              plugin={plugin}
              onInstall={handleInstall}
              onUninstall={handleUninstall}
              installing={installing || undefined}
              uninstalling={uninstalling || undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
};
