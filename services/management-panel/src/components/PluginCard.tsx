import { Plugin } from '../lib/types';

interface PluginCardProps {
  plugin: Plugin;
  onInstall: (id: string) => void;
  onUninstall: (id: string) => void;
  installing?: string;
  uninstalling?: string;
}

export const PluginCard = ({ plugin, onInstall, onUninstall, installing, uninstalling }: PluginCardProps) => {
  const getCategoryColor = (cat: string) => {
    const colors: Record<string, string> = {
      performance: 'bg-green-500/20 text-green-400 border-green-500/30',
      security: 'bg-red-500/20 text-red-400 border-red-500/30',
      backup: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      monitoring: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      logging: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      scaling: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
      configuration: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
      integration: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    };
    return colors[cat] || 'bg-slate-500/20 text-white/45 border-slate-500/30';
  };

  return (
    <div className="card p-4 hover:border-white/25 transition-colors flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0">
          {plugin.iconUrl ? (
            <img src={plugin.iconUrl} alt="" className="w-10 h-10 rounded-lg shrink-0" />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center text-white/45 text-lg shrink-0">
              {plugin.name[0]}
            </div>
          )}
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-white truncate">{plugin.name}</h4>
            <p className="text-xs text-white/45">v{plugin.version} by {plugin.author}</p>
          </div>
        </div>
        <span className={`px-2 py-0.5 text-xs rounded border shrink-0 ${getCategoryColor(plugin.category)}`}>
          {plugin.category}
        </span>
      </div>

      <p className="text-xs text-white/45 mb-3 line-clamp-2 flex-1">{plugin.description}</p>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-white/40">
          <span>{plugin.downloads.toLocaleString()} downloads</span>
          {plugin.installed && (
            <span className="text-green-400">Installed</span>
          )}
        </div>

        {plugin.installed ? (
          <button
            onClick={() => onUninstall(plugin.id)}
            disabled={uninstalling === plugin.id}
            className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 disabled:bg-white/10 text-white rounded transition-colors"
          >
            {uninstalling === plugin.id ? 'Removing...' : 'Uninstall'}
          </button>
        ) : (
          <button
            onClick={() => onInstall(plugin.id)}
            disabled={installing === plugin.id}
            className="primary-button"
          >
            {installing === plugin.id ? 'Installing...' : 'Install'}
          </button>
        )}
      </div>
    </div>
  );
};
