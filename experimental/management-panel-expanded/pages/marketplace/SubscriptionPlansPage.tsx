import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface Plan { id: string; name: string; description: string; price_monthly: number; cpu_cores: number; ram_gb: number; storage_gb: number; bandwidth_tb: number; features: string[] }
interface Addon { id: string; name: string; description: string; price_monthly: number; plan_id: string }
interface Subscription { id: string; plan_id: string; plan_name: string; status: string; next_billing: string; addons: string[] }

export const SubscriptionPlansPage = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [addons, setAddons] = useState<Addon[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [p, a, s] = await Promise.all([
        apiClient.get('/api/marketplace/plans'),
        apiClient.get('/api/marketplace/plans/addons'),
        apiClient.get('/api/marketplace/plans/my-subscription'),
      ]);
      setPlans(Array.isArray(p) ? p : p?.plans || []);
      setAddons(Array.isArray(a) ? a : a?.addons || []);
      setSubscription(s);
    } catch { toast.error('Failed to load plans'); }
    finally { setLoading(false); }
  };

  const handleSubscribe = async (planId: string) => {
    try {
      await apiClient.post('/api/marketplace/plans/subscribe', { plan_id: planId });
      toast.success('Subscribed!');
      loadData();
    } catch { toast.error('Failed to subscribe'); }
  };

  const handleSwitch = async (planId: string) => {
    try {
      const r = await apiClient.post('/api/marketplace/plans/switch', { new_plan_id: planId });
      toast.success(`Switched! Credit: $${r.prorated_credit?.toFixed(2) || '0.00'}`);
      loadData();
    } catch { toast.error('Failed to switch'); }
  };

  const handleCancel = async () => {
    try {
      await apiClient.post('/api/marketplace/plans/cancel', {});
      toast.success('Subscription cancelled');
      loadData();
    } catch { toast.error('Failed to cancel'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading plans...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Subscription Plan Builder</h1>
          <p className="text-slate-400">Choose or customize your subscription plan</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {subscription && (
        <div className="bg-slate-900 border border-blue-500/50 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-white">Current Plan: {subscription.plan_name}</h3>
              <p className="text-sm text-slate-400">Next billing: {subscription.next_billing || 'N/A'} | Status: <span className="text-green-400 capitalize">{subscription.status}</span></p>
            </div>
            <button onClick={handleCancel} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors">Cancel Subscription</button>
          </div>
          {subscription.addons?.length > 0 && <div className="text-sm text-slate-400">Addons: {subscription.addons.join(', ')}</div>}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {plans.map(p => {
          const isCurrent = subscription?.plan_id === p.id;
          return (
            <div key={p.id} className={`bg-slate-900 border rounded-lg p-6 flex flex-col ${isCurrent ? 'border-blue-500 ring-1 ring-blue-500' : 'border-slate-800'}`}>
              {isCurrent && <div className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded self-start mb-2">Current</div>}
              <h3 className="text-xl font-bold text-white mb-1">{p.name}</h3>
              <p className="text-sm text-slate-400 mb-4">{p.description}</p>
              <div className="text-3xl font-bold text-white mb-4">${p.price_monthly.toFixed(2)}<span className="text-sm text-slate-400 font-normal">/mo</span></div>
              <div className="space-y-2 mb-6 flex-1">
                {[
                  { label: 'CPU Cores', value: p.cpu_cores },
                  { label: 'RAM', value: `${p.ram_gb} GB` },
                  { label: 'Storage', value: `${p.storage_gb} GB` },
                  { label: 'Bandwidth', value: `${p.bandwidth_tb} TB/mo` },
                ].map(f => (
                  <div key={f.label} className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">{f.label}</span>
                    <span className="text-white">{f.value}</span>
                  </div>
                ))}
              </div>
              {p.features && (
                <div className="mb-4 space-y-1">
                  {p.features.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
                      <span className="text-green-400">✓</span> {f}
                    </div>
                  ))}
                </div>
              )}
              <button onClick={() => isCurrent ? handleSwitch(p.id) : handleSubscribe(p.id)} className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors ${isCurrent ? 'bg-slate-800 text-white hover:bg-slate-700' : 'bg-blue-600 text-white hover:bg-blue-700'}`}>
                {isCurrent ? 'Switch to This' : 'Subscribe'}
              </button>
            </div>
          );
        })}
      </div>

      {addons.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">Available Addons</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {addons.map(a => (
              <div key={a.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-white font-medium">{a.name}</h3>
                  <span className="text-yellow-400 font-bold">${a.price_monthly.toFixed(2)}/mo</span>
                </div>
                <p className="text-sm text-slate-400">{a.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SubscriptionPlansPage;
