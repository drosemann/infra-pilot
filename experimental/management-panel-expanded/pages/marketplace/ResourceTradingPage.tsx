import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface TradeListing { id: string; resource_type: string; quantity: number; price: number; listing_type: string; seller: string; status: string; created_at: string; min_quantity: number }
interface TradeOrder { id: string; listing_id: string; buyer: string; quantity: number; total_price: number; status: string; created_at: string }

export const ResourceTradingPage = () => {
  const [listings, setListings] = useState<TradeListing[]>([]);
  const [orders, setOrders] = useState<TradeOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'sell' | 'buy'>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [newListing, setNewListing] = useState({ resource_type: 'cpu', quantity: 1, price: 0.01, listing_type: 'sell' });
  const [reputation, setReputation] = useState<any>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (categoryFilter) params.set('category', categoryFilter);
      if (typeFilter !== 'all') params.set('type', typeFilter);
      const [l, o, r] = await Promise.all([
        apiClient.get(`/api/marketplace/trading/listings?${params}`),
        apiClient.get('/api/marketplace/trading/orders'),
        apiClient.get('/api/marketplace/trading/reputation/me'),
      ]);
      setListings(Array.isArray(l) ? l : l?.listings || []);
      setOrders(Array.isArray(o) ? o : o?.orders || []);
      setReputation(r);
    } catch { toast.error('Failed to load trading data'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, [categoryFilter, typeFilter]);

  const handleCreate = async () => {
    try {
      await apiClient.post('/api/marketplace/trading/listings', newListing);
      toast.success('Listing created');
      setShowCreate(false);
      loadData();
    } catch { toast.error('Failed to create listing'); }
  };

  const handleBuy = async (id: string) => {
    try {
      await apiClient.post(`/api/marketplace/trading/listings/${id}/buy`, { quantity: 1 });
      toast.success('Purchase completed');
      loadData();
    } catch { toast.error('Failed to buy'); }
  };

  const handleCancel = async (id: string) => {
    try {
      await apiClient.delete(`/api/marketplace/trading/listings/${id}`);
      toast.success('Listing cancelled');
      loadData();
    } catch { toast.error('Failed to cancel'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading marketplace...</div>;

  const resourceTypes = ['cpu', 'ram', 'storage', 'bandwidth'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Resource Trading Platform</h1>
          <p className="text-slate-400">Buy and sell compute resources with other users</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCreate(!showCreate)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">+ New Listing</button>
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
        </div>
      </div>

      {reputation && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 grid grid-cols-3 gap-4 text-sm">
          <div><span className="text-slate-400">Rating</span><p className="text-white text-lg font-bold">{reputation.rating?.toFixed(1) || '0.0'}/5.0</p></div>
          <div><span className="text-slate-400">Total Trades</span><p className="text-white text-lg font-bold">{reputation.total_trades || 0}</p></div>
          <div><span className="text-slate-400">Completion Rate</span><p className="text-white text-lg font-bold">{((reputation.completion_rate || 0) * 100).toFixed(0)}%</p></div>
        </div>
      )}

      {showCreate && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">New Listing</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
            <div><label className="block text-sm text-slate-400 mb-1">Type</label><select value={newListing.listing_type} onChange={e => setNewListing({...newListing, listing_type: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm"><option value="sell">Sell</option><option value="buy">Buy</option></select></div>
            <div><label className="block text-sm text-slate-400 mb-1">Resource</label><select value={newListing.resource_type} onChange={e => setNewListing({...newListing, resource_type: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm">{resourceTypes.map(r => <option key={r} value={r}>{r.toUpperCase()}</option>)}</select></div>
            <div><label className="block text-sm text-slate-400 mb-1">Quantity</label><input type="number" value={newListing.quantity} onChange={e => setNewListing({...newListing, quantity: parseFloat(e.target.value) || 1})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Price/Unit</label><input type="number" step="0.0001" value={newListing.price} onChange={e => setNewListing({...newListing, price: parseFloat(e.target.value) || 0.01})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div className="flex items-end"><button onClick={handleCreate} className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">Create</button></div>
          </div>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setCategoryFilter('')} className={`px-3 py-1.5 text-xs rounded-lg border capitalize ${!categoryFilter ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>All</button>
        {resourceTypes.map(r => (
          <button key={r} onClick={() => setCategoryFilter(categoryFilter === r ? '' : r)} className={`px-3 py-1.5 text-xs rounded-lg border uppercase ${categoryFilter === r ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>{r}</button>
        ))}
        <div className="flex-1" />
        <button onClick={() => setTypeFilter('all')} className={`px-3 py-1.5 text-xs rounded-lg border ${typeFilter === 'all' ? 'bg-slate-700 border-slate-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>All</button>
        <button onClick={() => setTypeFilter('sell')} className={`px-3 py-1.5 text-xs rounded-lg border ${typeFilter === 'sell' ? 'bg-green-700 border-green-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>Sell</button>
        <button onClick={() => setTypeFilter('buy')} className={`px-3 py-1.5 text-xs rounded-lg border ${typeFilter === 'buy' ? 'bg-blue-700 border-blue-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>Buy</button>
      </div>

      <div className="grid gap-3">
        {listings.map(l => (
          <div key={l.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${l.listing_type === 'sell' ? 'bg-green-600 text-white' : 'bg-blue-600 text-white'}`}>{l.listing_type === 'sell' ? 'SELL' : 'BUY'}</span>
                <span className="text-white font-mono font-medium uppercase">{l.resource_type}</span>
                <span className="text-white">x{l.quantity}</span>
                <span className="text-yellow-400">${l.price.toFixed(4)}/unit</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded ${l.status === 'active' ? 'bg-green-600' : 'bg-slate-600'} text-white`}>{l.status}</span>
                {l.status === 'active' && l.listing_type === 'sell' && <button onClick={() => handleBuy(l.id)} className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors">Buy</button>}
                <button onClick={() => handleCancel(l.id)} className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded transition-colors">Cancel</button>
              </div>
            </div>
            <div className="text-xs text-slate-500">Seller: {l.seller?.slice(0, 12)}... | Listed: {l.created_at?.split('T')[0]}</div>
          </div>
        ))}
        {listings.length === 0 && <p className="text-slate-500 text-center py-8">No listings match your filters.</p>}
      </div>

      {orders.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">My Orders</h2>
          <div className="grid gap-2">
            {orders.map(o => (
              <div key={o.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between text-sm">
                <div>
                  <span className="text-white">Order #{o.id.slice(0, 8)}</span>
                  <span className="text-slate-400 ml-3">x{o.quantity} @ ${o.total_price.toFixed(4)}</span>
                  <span className={`ml-3 text-xs px-1.5 py-0.5 rounded ${o.status === 'completed' ? 'bg-green-600 text-white' : o.status === 'pending' ? 'bg-yellow-600 text-white' : 'bg-red-600 text-white'}`}>{o.status}</span>
                </div>
                <span className="text-xs text-slate-500">{o.created_at?.split('T')[0]}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResourceTradingPage;
