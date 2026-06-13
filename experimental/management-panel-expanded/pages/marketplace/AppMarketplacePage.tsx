import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface MarketplaceApp { id: string; name: string; description: string; version: string; category: string; price: number; install_count: number; icon_url: string; requirements: string; docker_image: string }
interface Deployment { id: string; app_id: string; app_name: string; server_id: string; status: string; url: string; deployed_at: string }

export const AppMarketplacePage = () => {
  const [apps, setApps] = useState<MarketplaceApp[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [deploying, setDeploying] = useState<string | null>(null);
  const [showDeployments, setShowDeployments] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [a, d] = await Promise.all([
        apiClient.get('/api/marketplace/apps'),
        apiClient.get('/api/marketplace/apps/deployments'),
      ]);
      setApps(Array.isArray(a) ? a : a?.apps || []);
      setDeployments(Array.isArray(d) ? d : d?.deployments || []);
    } catch { toast.error('Failed to load marketplace'); }
    finally { setLoading(false); }
  };

  const handleDeploy = async (appId: string) => {
    setDeploying(appId);
    try {
      const result = await apiClient.post(`/api/marketplace/apps/${appId}/install`, {});
      toast.success(`Deploying: ${result.app_name || appId}`);
      loadData();
    } catch { toast.error('Failed to deploy'); }
    finally { setDeploying(null); }
  };

  const categories = [...new Set(apps.map(a => a.category))];
  const filtered = apps.filter(a => {
    if (categoryFilter !== 'all' && a.category !== categoryFilter) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && !a.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (loading) return <div className="text-slate-400 p-8">Loading marketplace...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">One-Click App Marketplace</h1>
          <p className="text-slate-400">Deploy popular applications with a single click</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowDeployments(!showDeployments)} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">{showDeployments ? 'Browse Apps' : `Deployments (${deployments.length})`}</button>
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
        </div>
      </div>

      <div className="relative max-w-md">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search apps..." className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500" />
      </div>

      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setCategoryFilter('all')} className={`px-3 py-1.5 text-xs rounded-lg border capitalize ${categoryFilter === 'all' ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>All</button>
        {categories.map(c => (
          <button key={c} onClick={() => setCategoryFilter(c)} className={`px-3 py-1.5 text-xs rounded-lg border capitalize ${categoryFilter === c ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>{c}</button>
        ))}
      </div>

      {showDeployments ? (
        <div className="grid gap-3">
          <h2 className="text-lg font-semibold text-white">Your Deployments</h2>
          {deployments.map(d => (
            <div key={d.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${d.status === 'running' ? 'bg-green-500' : d.status === 'deploying' ? 'bg-yellow-500' : 'bg-red-500'}`} />
                  <span className="text-white font-medium">{d.app_name}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${d.status === 'running' ? 'bg-green-600' : d.status === 'deploying' ? 'bg-yellow-600' : 'bg-slate-600'} text-white`}>{d.status}</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-slate-400">Server</span><p className="text-white">{d.server_id || 'N/A'}</p></div>
                <div><span className="text-slate-400">URL</span><p className="text-blue-400">{d.url || 'N/A'}</p></div>
              </div>
              <div className="text-xs text-slate-500 mt-2">Deployed: {d.deployed_at || 'N/A'}</div>
            </div>
          ))}
          {deployments.length === 0 && <p className="text-slate-500 text-center py-4">No deployments yet.</p>}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(app => (
            <div key={app.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition-colors">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-12 h-12 bg-slate-800 rounded-lg flex items-center justify-center text-2xl">{app.icon_url ? <img src={app.icon_url} className="w-8 h-8" /> : '📦'}</div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-semibold truncate">{app.name}</h3>
                  <p className="text-xs text-slate-500">v{app.version} | {app.category}</p>
                </div>
                <span className="text-sm font-bold text-yellow-400">${app.price.toFixed(2)}</span>
              </div>
              <p className="text-sm text-slate-400 mb-3 line-clamp-2">{app.description}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">{app.install_count} installs</span>
                <button onClick={() => handleDeploy(app.id)} disabled={deploying === app.id} className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white text-xs rounded transition-colors">{deploying === app.id ? 'Deploying...' : 'Deploy'}</button>
              </div>
              {app.requirements && <div className="mt-2 text-xs text-slate-500">Requires: {app.requirements}</div>}
            </div>
          ))}
          {filtered.length === 0 && <p className="text-slate-500 col-span-full text-center py-8">No apps match your search.</p>}
        </div>
      )}
    </div>
  );
};

export default AppMarketplacePage;
