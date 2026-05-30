import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface PPUUsage { current_period: number; cpu_seconds: number; ram_gb_hours: number; storage_gb_hours: number; bandwidth_gb: number; rate_per_second: number }
interface PPUInvoice { id: string; period: string; amount: number; paid: boolean; status: string; due_date: string; paid_at: string; items: PPULineItem[] }
interface PPULineItem { description: string; quantity: number; unit_price: number; total: number }
interface PPURates { rates: Record<string, number> }

export const PayPerUsePage = () => {
  const [usage, setUsage] = useState<PPUUsage | null>(null);
  const [invoices, setInvoices] = useState<PPUInvoice[]>([]);
  const [rates, setRates] = useState<PPURates | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'usage' | 'invoices' | 'rates'>('usage');
  const [selectedInvoice, setSelectedInvoice] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [u, i, r] = await Promise.all([
        apiClient.get('/api/marketplace/ppu/usage'),
        apiClient.get('/api/marketplace/ppu/invoices'),
        apiClient.get('/api/marketplace/ppu/rates'),
      ]);
      setUsage(u);
      setInvoices(Array.isArray(i) ? i : i?.invoices || []);
      setRates(r);
    } catch { toast.error('Failed to load PPU data'); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading pay-per-use data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Pay-Per-Use Billing</h1>
          <p className="text-slate-400">Per-second billing for compute resources</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {usage && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Current Cost</div><div className="text-2xl font-bold text-white">${usage.current_period.toFixed(4)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">CPU Seconds</div><div className="text-2xl font-bold text-blue-400">{usage.cpu_seconds.toFixed(0)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">RAM GB-Hours</div><div className="text-2xl font-bold text-green-400">{usage.ram_gb_hours.toFixed(2)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Storage GB-Hours</div><div className="text-2xl font-bold text-yellow-400">{usage.storage_gb_hours.toFixed(2)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Bandwidth GB</div><div className="text-2xl font-bold text-purple-400">{usage.bandwidth_gb.toFixed(2)}</div></div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4"><div className="text-slate-400 text-xs mb-1">Rate</div><div className="text-2xl font-bold text-red-400">${usage.rate_per_second.toFixed(6)}/s</div></div>
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button onClick={() => setActiveTab('usage')} className={`px-4 py-2 text-sm rounded-t-lg ${activeTab === 'usage' ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>Usage Summary</button>
        <button onClick={() => setActiveTab('invoices')} className={`px-4 py-2 text-sm rounded-t-lg ${activeTab === 'invoices' ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>Invoices ({invoices.length})</button>
        <button onClick={() => setActiveTab('rates')} className={`px-4 py-2 text-sm rounded-t-lg ${activeTab === 'rates' ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>Rates</button>
      </div>

      {activeTab === 'usage' && usage && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">Resource Breakdown</h3>
          <div className="space-y-4">
            {[
              { label: 'CPU', value: usage.cpu_seconds, unit: 'seconds', color: 'blue', pct: Math.min(100, usage.cpu_seconds / 3600 * 100) },
              { label: 'RAM', value: usage.ram_gb_hours, unit: 'GB-hours', color: 'green', pct: Math.min(100, usage.ram_gb_hours / 100 * 100) },
              { label: 'Storage', value: usage.storage_gb_hours, unit: 'GB-hours', color: 'yellow', pct: Math.min(100, usage.storage_gb_hours / 1000 * 100) },
              { label: 'Bandwidth', value: usage.bandwidth_gb, unit: 'GB', color: 'purple', pct: Math.min(100, usage.bandwidth_gb / 100 * 100) },
            ].map(item => (
              <div key={item.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-white">{item.label}</span>
                  <span className="text-slate-400">{item.value.toFixed(2)} {item.unit}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div className={`bg-${item.color}-600 h-2 rounded-full`} style={{ width: `${item.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'invoices' && (
        <div className="grid gap-3">
          {invoices.map(inv => (
            <div key={inv.id}>
              <div onClick={() => setSelectedInvoice(selectedInvoice === inv.id ? null : inv.id)} className="bg-slate-900 border border-slate-800 rounded-lg p-4 cursor-pointer hover:border-slate-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`text-lg ${inv.paid ? 'text-green-400' : 'text-yellow-400'}`}>{inv.paid ? '✅' : '⏳'}</span>
                    <div>
                      <span className="text-white font-medium">{inv.period}</span>
                      <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${inv.status === 'paid' ? 'bg-green-600' : inv.status === 'overdue' ? 'bg-red-600' : 'bg-yellow-600'} text-white`}>{inv.status}</span>
                    </div>
                  </div>
                  <span className="text-lg font-bold text-white">${inv.amount.toFixed(2)}</span>
                </div>
                <div className="text-xs text-slate-500 mt-1">Due: {inv.due_date} {inv.paid_at ? `| Paid: ${inv.paid_at}` : ''}</div>
              </div>
              {selectedInvoice === inv.id && inv.items && (
                <div className="bg-slate-800 border-x border-b border-slate-700 rounded-b-lg p-4">
                  <table className="w-full text-sm">
                    <thead><tr className="text-slate-400 text-xs border-b border-slate-700"><th className="text-left pb-2">Item</th><th className="text-right pb-2">Qty</th><th className="text-right pb-2">Unit Price</th><th className="text-right pb-2">Total</th></tr></thead>
                    <tbody>
                      {inv.items.map((item, i) => (
                        <tr key={i} className="text-white border-b border-slate-700/50">
                          <td className="py-2">{item.description}</td>
                          <td className="py-2 text-right">{item.quantity.toFixed(2)}</td>
                          <td className="py-2 text-right">${item.unit_price.toFixed(6)}</td>
                          <td className="py-2 text-right">${item.total.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
          {invoices.length === 0 && <p className="text-slate-500 text-center py-4">No invoices yet.</p>}
        </div>
      )}

      {activeTab === 'rates' && rates && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-xs border-b border-slate-800"><th className="text-left px-4 py-3">Resource</th><th className="text-right px-4 py-3">Rate (per unit)</th></tr></thead>
            <tbody>
              {Object.entries(rates.rates || {}).map(([key, val]) => (
                <tr key={key} className="border-b border-slate-800 text-white">
                  <td className="px-4 py-3 capitalize">{key.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-right font-mono">${(val as number).toFixed(6)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PayPerUsePage;
