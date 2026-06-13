import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface UsageRecommendation { id: string; title: string; description: string; savings_potential: number; category: string; difficulty: string; effort: string; roi: string; action_url: string; created_at: string }
interface SavingsSummary { total_savings: number; active_recommendations: number; implemented_count: number }

export const UsageRecommendationsPage = () => {
  const [recommendations, setRecommendations] = useState<UsageRecommendation[]>([]);
  const [summary, setSummary] = useState<SavingsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('savings');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [recs, summ] = await Promise.all([
        apiClient.get('/api/marketplace/recommendations'),
        apiClient.get('/api/marketplace/recommendations/summary'),
      ]);
      setRecommendations(Array.isArray(recs) ? recs : recs?.recommendations || []);
      setSummary(summ?.summary || summ || null);
    } catch { toast.error('Failed to load recommendations'); }
    finally { setLoading(false); }
  };

  const handleImplement = async (id: string) => {
    try {
      const r = await apiClient.post(`/api/marketplace/recommendations/${id}/implement`, {});
      toast.success(`Implementing: ${r.title || id}`);
      loadData();
    } catch { toast.error('Failed to implement recommendation'); }
  };

  const handleDismiss = async (id: string) => {
    try {
      await apiClient.post(`/api/marketplace/recommendations/${id}/dismiss`, {});
      toast.success('Recommendation dismissed');
      loadData();
    } catch { toast.error('Failed to dismiss'); }
  };

  const categories = [...new Set(recommendations.map(r => r.category))];
  const filtered = recommendations
    .filter(r => categoryFilter === 'all' || r.category === categoryFilter)
    .sort((a, b) => sortBy === 'savings' ? b.savings_potential - a.savings_potential : a.title.localeCompare(b.title));

  if (loading) return <div className="text-slate-400 p-8">Loading recommendations...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Usage-Based Recommendations</h1>
          <p className="text-slate-400">Optimize infrastructure and reduce costs</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="text-sm text-slate-400">Total Potential Savings</div>
            <div className="text-3xl font-bold text-green-400">${summary.total_savings.toFixed(2)}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="text-sm text-slate-400">Active Recommendations</div>
            <div className="text-3xl font-bold text-yellow-400">{summary.active_recommendations}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="text-sm text-slate-400">Implemented</div>
            <div className="text-3xl font-bold text-blue-400">{summary.implemented_count}</div>
          </div>
        </div>
      )}

      <div className="flex gap-2 items-center">
        <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className="bg-slate-900 border border-slate-700 text-sm text-white rounded px-3 py-2">
          <option value="all">All Categories</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="bg-slate-900 border border-slate-700 text-sm text-white rounded px-3 py-2">
          <option value="savings">Sort by Savings</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map(r => (
          <div key={r.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-1 rounded">{r.category}</span>
                <h3 className="text-lg font-semibold text-white mt-2">{r.title}</h3>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-green-400">${r.savings_potential.toFixed(2)}</div>
                <div className="text-xs text-slate-500">savings/month</div>
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-4">{r.description}</p>
            <div className="flex items-center gap-3 text-xs text-slate-500 mb-4">
              <span>Difficulty: <span className="text-white">{r.difficulty}</span></span>
              <span>Effort: <span className="text-white">{r.effort}</span></span>
              <span>ROI: <span className="text-white">{r.roi}</span></span>
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleImplement(r.id)} className="px-4 py-2 bg-green-700 hover:bg-green-600 text-white rounded text-xs font-semibold">Implement</button>
              <button onClick={() => handleDismiss(r.id)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs">Dismiss</button>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <div className="col-span-full text-center py-8 text-slate-500">No recommendations found.</div>}
      </div>
    </div>
  );
};

export default UsageRecommendationsPage;
