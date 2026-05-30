import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface TaxRate { id: string; country: string; region: string; rate: number; category: string; is_reverse_charge: boolean; valid_from: string }
interface Invoice { id: string; invoice_number: string; customer_name: string; amount: number; tax_amount: number; total: number; currency: string; status: string; issued_at: string; due_at: string; paid_at: string }
interface TaxSummary { total_tax_collected: number; invoices_this_month: number; overdue_count: number }

export const TaxAutomationPage = () => {
  const [rates, setRates] = useState<TaxRate[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [summary, setSummary] = useState<TaxSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'rates' | 'invoices' | 'filing'>('invoices');
  const [savingRate, setSavingRate] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [r, i, s] = await Promise.all([
        apiClient.get('/api/marketplace/tax/rates'),
        apiClient.get('/api/marketplace/tax/invoices'),
        apiClient.get('/api/marketplace/tax/summary'),
      ]);
      setRates(Array.isArray(r) ? r : r?.rates || []);
      setInvoices(Array.isArray(i) ? i : i?.invoices || []);
      setSummary(s?.summary || s || null);
    } catch { toast.error('Failed to load tax data'); }
    finally { setLoading(false); }
  };

  const handleAddRate = async () => {
    setSavingRate(true);
    try {
      await apiClient.post('/api/marketplace/tax/rates', { country: 'US', region: 'CA', rate: 0.0875, category: 'standard' });
      toast.success('Rate added');
      loadData();
    } catch { toast.error('Failed to add rate'); }
    finally { setSavingRate(false); }
  };

  const handleGenerateInvoice = async () => {
    try {
      await apiClient.post('/api/marketplace/tax/invoices/generate', {});
      toast.success('Invoice generated');
      loadData();
    } catch { toast.error('Failed to generate'); }
  };

  const handleMarkPaid = async (id: string) => {
    try {
      await apiClient.post(`/api/marketplace/tax/invoices/${id}/pay`, {});
      toast.success('Invoice marked as paid');
      loadData();
    } catch { toast.error('Failed to update invoice'); }
  };

  const handleFileReport = async () => {
    try {
      await apiClient.post('/api/marketplace/tax/file', { period: new Date().toISOString().slice(0, 7) });
      toast.success('Tax report filed');
      loadData();
    } catch { toast.error('Failed to file report'); }
  };

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'paid': return 'text-green-400';
      case 'overdue': return 'text-red-400';
      case 'pending': case 'sent': return 'text-yellow-400';
      default: return 'text-slate-400';
    }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading tax data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Invoice & Tax Automation</h1>
          <p className="text-slate-400">Automate invoicing, tax calculation, and filing</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="text-sm text-slate-400">Total Tax Collected</div>
            <div className="text-3xl font-bold text-white">${summary.total_tax_collected.toFixed(2)}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="text-sm text-slate-400">Invoices This Month</div>
            <div className="text-3xl font-bold text-blue-400">{summary.invoices_this_month}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
            <div className="text-sm text-slate-400">Overdue Invoices</div>
            <div className="text-3xl font-bold text-red-400">{summary.overdue_count}</div>
          </div>
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {(['rates', 'invoices', 'filing'] as const).map(t => (
          <button key={t} onClick={() => setActiveTab(t)} className={`px-4 py-2 text-sm rounded-t-lg capitalize ${activeTab === t ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>
            {t === 'rates' ? 'Tax Rates' : t === 'invoices' ? 'Invoices' : 'Tax Filing'}
          </button>
        ))}
      </div>

      {activeTab === 'rates' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">Configured Tax Rates</h3>
            <button onClick={handleAddRate} disabled={savingRate} className="px-4 py-2 bg-blue-700 hover:bg-blue-600 text-white rounded text-xs font-semibold">
              {savingRate ? 'Adding...' : '+ Add Rate'}
            </button>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead><tr className="text-slate-400 text-xs border-b border-slate-800"><th className="text-left px-4 py-3">Country</th><th className="text-left px-4 py-3">Region</th><th className="text-right px-4 py-3">Rate</th><th className="text-left px-4 py-3">Category</th><th className="text-left px-4 py-3">Reverse Charge</th><th className="text-left px-4 py-3">Valid From</th></tr></thead>
              <tbody>
                {rates.map(r => (
                  <tr key={r.id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                    <td className="px-4 py-3">{r.country}</td>
                    <td className="px-4 py-3">{r.region}</td>
                    <td className="px-4 py-3 text-right font-bold">{(r.rate * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 capitalize">{r.category}</td>
                    <td className="px-4 py-3">{r.is_reverse_charge ? 'Yes' : 'No'}</td>
                    <td className="px-4 py-3 text-slate-400">{r.valid_from?.split('T')[0]}</td>
                  </tr>
                ))}
                {rates.length === 0 && <tr><td colSpan={6} className="text-center py-4 text-slate-500">No tax rates configured.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'invoices' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">Invoices</h3>
            <button onClick={handleGenerateInvoice} className="px-4 py-2 bg-blue-700 hover:bg-blue-600 text-white rounded text-xs font-semibold">+ Generate Invoice</button>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead><tr className="text-slate-400 text-xs border-b border-slate-800"><th className="text-left px-4 py-3">Invoice #</th><th className="text-left px-4 py-3">Customer</th><th className="text-right px-4 py-3">Amount</th><th className="text-right px-4 py-3">Tax</th><th className="text-right px-4 py-3">Total</th><th className="text-left px-4 py-3">Status</th><th className="text-left px-4 py-3">Due</th><th className="text-left px-4 py-3">Actions</th></tr></thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                    <td className="px-4 py-3 font-mono text-xs">{inv.invoice_number}</td>
                    <td className="px-4 py-3">{inv.customer_name}</td>
                    <td className="px-4 py-3 text-right">{inv.amount.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right">{inv.tax_amount.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-bold">{inv.total.toFixed(2)}</td>
                    <td className={`px-4 py-3 capitalize ${getStatusColor(inv.status)}`}>{inv.status}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{inv.due_at?.split('T')[0]}</td>
                    <td className="px-4 py-3">
                      {inv.status !== 'paid' && <button onClick={() => handleMarkPaid(inv.id)} className="px-3 py-1 bg-green-700 hover:bg-green-600 text-white rounded text-xs">Mark Paid</button>}
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && <tr><td colSpan={8} className="text-center py-4 text-slate-500">No invoices.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'filing' && (
        <div className="max-w-2xl">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Tax Filing</h3>
            <p className="text-slate-400 text-sm mb-6">Automatically file tax reports for the current period. This will calculate tax due based on configured rates and issued invoices.</p>
            <div className="bg-slate-800 rounded-lg p-4 mb-6">
              <h4 className="text-white font-medium mb-2">Current Period</h4>
              <div className="text-sm text-slate-400">Period: {new Date().toISOString().slice(0, 7)}</div>
              <div className="text-sm text-slate-400">Invoices: {summary?.invoices_this_month || 0}</div>
              <div className="text-sm text-slate-400">Overdue: {summary?.overdue_count || 0}</div>
            </div>
            <button onClick={handleFileReport} className="px-6 py-3 bg-blue-700 hover:bg-blue-600 text-white rounded-lg text-sm font-semibold">File Tax Report</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaxAutomationPage;
