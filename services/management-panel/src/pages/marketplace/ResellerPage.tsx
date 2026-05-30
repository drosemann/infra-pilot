import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface Reseller { id: string; name: string; email: string; margin_percent: number; status: string; customer_count: number; total_revenue: number; company_name: string; logo_url: string; primary_color: string }
interface SubAdmin { id: string; reseller_id: string; email: string; permissions: string[] }

export const ResellerPage = () => {
  const [resellers, setResellers] = useState<Reseller[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReseller, setSelectedReseller] = useState<string | null>(null);
  const [salesData, setSalesData] = useState<any>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newReseller, setNewReseller] = useState({ name: '', email: '', margin_percent: 10 });
  const [brandingForm, setBrandingForm] = useState({ logo_url: '', primary_color: '#3b82f6', company_name: '' });

  useEffect(() => { loadData(); }, []);
  useEffect(() => { if (selectedReseller) loadSales(); }, [selectedReseller]);

  const loadData = async () => {
    setLoading(true);
    try {
      const d = await apiClient.get('/api/marketplace/resellers');
      setResellers(Array.isArray(d) ? d : d?.resellers || []);
    } catch { toast.error('Failed to load resellers'); }
    finally { setLoading(false); }
  };

  const loadSales = async () => {
    if (!selectedReseller) return;
    try {
      const d = await apiClient.get(`/api/marketplace/resellers/${selectedReseller}/sales`);
      setSalesData(d);
      const r = resellers.find(x => x.id === selectedReseller);
      if (r) setBrandingForm({ logo_url: r.logo_url || '', primary_color: r.primary_color || '#3b82f6', company_name: r.company_name || '' });
    } catch { }
  };

  const handleCreate = async () => {
    try {
      await apiClient.post('/api/marketplace/resellers', newReseller);
      toast.success('Reseller created');
      setShowCreate(false);
      setNewReseller({ name: '', email: '', margin_percent: 10 });
      loadData();
    } catch { toast.error('Failed to create reseller'); }
  };

  const handleBranding = async () => {
    if (!selectedReseller) return;
    try {
      await apiClient.put(`/api/marketplace/resellers/${selectedReseller}/branding`, brandingForm);
      toast.success('Branding updated');
    } catch { toast.error('Failed to update branding'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading resellers...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Reseller & White-Label</h1>
          <p className="text-slate-400">Manage resellers, branding, and white-label configurations</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCreate(!showCreate)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">+ Add Reseller</button>
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
        </div>
      </div>

      {showCreate && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">New Reseller</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div><label className="block text-sm text-slate-400 mb-1">Name</label><input value={newReseller.name} onChange={e => setNewReseller({...newReseller, name: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Email</label><input value={newReseller.email} onChange={e => setNewReseller({...newReseller, email: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Margin %</label><input type="number" value={newReseller.margin_percent} onChange={e => setNewReseller({...newReseller, margin_percent: parseFloat(e.target.value) || 10})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">Create Reseller</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="text-lg font-semibold text-white mb-2">Resellers</h2>
          {resellers.map(r => (
            <div key={r.id} onClick={() => setSelectedReseller(r.id)} className={`bg-slate-900 border rounded-lg p-4 cursor-pointer transition-colors ${selectedReseller === r.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <span className="text-white font-medium">{r.name}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${r.status === 'active' ? 'bg-green-600' : 'bg-slate-600'} text-white`}>{r.status}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">{r.email} | {r.margin_percent}% margin | {r.customer_count} customers</div>
            </div>
          ))}
          {resellers.length === 0 && <p className="text-slate-500 text-center py-4">No resellers.</p>}
        </div>

        <div className="lg:col-span-2">
          {!selectedReseller && <p className="text-slate-500 text-center py-8">Select a reseller to manage.</p>}
          {selectedReseller && (
            <div className="space-y-4">
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                <h3 className="text-lg font-semibold text-white mb-3">Branding</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div><label className="block text-sm text-slate-400 mb-1">Logo URL</label><input value={brandingForm.logo_url} onChange={e => setBrandingForm({...brandingForm, logo_url: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
                  <div><label className="block text-sm text-slate-400 mb-1">Primary Color</label><div className="flex gap-2"><input value={brandingForm.primary_color} onChange={e => setBrandingForm({...brandingForm, primary_color: e.target.value})} className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /><input type="color" value={brandingForm.primary_color} onChange={e => setBrandingForm({...brandingForm, primary_color: e.target.value})} className="w-10 h-10 rounded cursor-pointer" /></div></div>
                  <div><label className="block text-sm text-slate-400 mb-1">Company Name</label><input value={brandingForm.company_name} onChange={e => setBrandingForm({...brandingForm, company_name: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
                </div>
                <button onClick={handleBranding} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">Save Branding</button>
              </div>

              {salesData && (
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                  <h3 className="text-lg font-semibold text-white mb-3">Sales Report</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div><span className="text-slate-400">Total Revenue</span><p className="text-white text-xl font-bold">${salesData.total_revenue?.toFixed(2)}</p></div>
                    <div><span className="text-slate-400">Your Earnings</span><p className="text-white text-xl font-bold">${salesData.reseller_earnings?.toFixed(2)}</p></div>
                    <div><span className="text-slate-400">Transactions</span><p className="text-white text-xl font-bold">{salesData.transaction_count}</p></div>
                    <div><span className="text-slate-400">Period</span><p className="text-white text-xl">{salesData.period || 'N/A'}</p></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResellerPage;
