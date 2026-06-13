import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface CryptoWallet { id: string; currency: string; address: string; balance: number; label: string }
interface CryptoInvoice { id: string; amount_usd: number; currency: string; address: string; status: string; created_at: string; paid_at: string; txid: string }
interface CryptoTransaction { id: string; txid: string; amount: number; currency: string; from_address: string; to_address: string; status: string; confirmations: number; timestamp: string }

export const CryptoPaymentPage = () => {
  const [wallets, setWallets] = useState<CryptoWallet[]>([]);
  const [invoices, setInvoices] = useState<CryptoInvoice[]>([]);
  const [transactions, setTransactions] = useState<CryptoTransaction[]>([]);
  const [rates, setRates] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'wallets' | 'invoices' | 'txs'>('wallets');
  const [showCreate, setShowCreate] = useState(false);
  const [newInvoice, setNewInvoice] = useState({ amount_usd: 10, currency: 'usdc' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [w, i, t, r] = await Promise.all([
        apiClient.get('/api/marketplace/crypto/wallets'),
        apiClient.get('/api/marketplace/crypto/invoices'),
        apiClient.get('/api/marketplace/crypto/transactions'),
        apiClient.get('/api/marketplace/crypto/rates'),
      ]);
      setWallets(Array.isArray(w) ? w : w?.wallets || []);
      setInvoices(Array.isArray(i) ? i : i?.invoices || []);
      setTransactions(Array.isArray(t) ? t : t?.transactions || []);
      setRates(r?.rates || {});
    } catch { toast.error('Failed to load crypto data'); }
    finally { setLoading(false); }
  };

  const handleCreateInvoice = async () => {
    try {
      const r = await apiClient.post('/api/marketplace/crypto/invoices', newInvoice);
      toast.success(`Invoice created: ${r.id?.slice(0, 8)}...`);
      setShowCreate(false);
      loadData();
    } catch { toast.error('Failed to create invoice'); }
  };

  if (loading) return <div className="text-slate-400 p-8">Loading crypto data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Crypto Payment Gateway</h1>
          <p className="text-slate-400">Accept cryptocurrency payments (BTC, ETH, SOL, USDC)</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCreate(!showCreate)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">+ New Invoice</button>
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(rates).map(([currency, rate]) => (
          <div key={currency} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-slate-400 text-xs mb-1 uppercase">{currency}</div>
            <div className="text-lg font-bold text-white">${(rate as number).toFixed(2)}</div>
          </div>
        ))}
      </div>

      {showCreate && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-4">New Crypto Invoice</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div><label className="block text-sm text-slate-400 mb-1">Amount (USD)</label><input type="number" value={newInvoice.amount_usd} onChange={e => setNewInvoice({...newInvoice, amount_usd: parseFloat(e.target.value) || 10})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm" /></div>
            <div><label className="block text-sm text-slate-400 mb-1">Currency</label><select value={newInvoice.currency} onChange={e => setNewInvoice({...newInvoice, currency: e.target.value})} className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm"><option value="btc">Bitcoin (BTC)</option><option value="eth">Ethereum (ETH)</option><option value="sol">Solana (SOL)</option><option value="usdc">USD Coin (USDC)</option></select></div>
            <div className="flex items-end"><button onClick={handleCreateInvoice} className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors">Create Invoice</button></div>
          </div>
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {(['wallets', 'invoices', 'txs'] as const).map(t => (
          <button key={t} onClick={() => setActiveTab(t)} className={`px-4 py-2 text-sm rounded-t-lg capitalize ${activeTab === t ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>{t === 'txs' ? 'Transactions' : t} ({t === 'wallets' ? wallets.length : t === 'invoices' ? invoices.length : transactions.length})</button>
        ))}
      </div>

      {activeTab === 'wallets' && (
        <div className="grid md:grid-cols-2 gap-4">
          {wallets.map(w => (
            <div key={w.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white uppercase">{w.currency}</h3>
                <span className="text-xl font-bold text-green-400">{w.balance} {w.currency.toUpperCase()}</span>
              </div>
              <div className="text-xs text-slate-400 font-mono break-all bg-slate-800 p-2 rounded">{w.address}</div>
              {w.label && <div className="text-xs text-slate-500 mt-2">{w.label}</div>}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'invoices' && (
        <div className="grid gap-3">
          {invoices.map(inv => (
            <div key={inv.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className={`text-lg ${inv.status === 'paid' ? 'text-green-400' : inv.status === 'pending' ? 'text-yellow-400' : 'text-red-400'}`}>{inv.status === 'paid' ? '✅' : inv.status === 'pending' ? '⏳' : '❌'}</span>
                  <span className="text-white font-medium">${inv.amount_usd.toFixed(2)} USD</span>
                  <span className="text-xs text-slate-500 uppercase">{inv.currency}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${inv.status === 'paid' ? 'bg-green-600 text-white' : inv.status === 'pending' ? 'bg-yellow-600 text-white' : 'bg-red-600 text-white'}`}>{inv.status}</span>
              </div>
              <div className="text-xs text-slate-500 font-mono">Address: {inv.address}</div>
              {inv.txid && <div className="text-xs text-slate-500 font-mono">TX: {inv.txid}</div>}
            </div>
          ))}
          {invoices.length === 0 && <p className="text-slate-500 text-center py-4">No invoices.</p>}
        </div>
      )}

      {activeTab === 'txs' && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-xs border-b border-slate-800">
              <th className="text-left px-3 py-2">TXID</th><th className="text-right px-3 py-2">Amount</th><th className="text-left px-3 py-2">Currency</th><th className="text-left px-3 py-2">Status</th><th className="text-right px-3 py-2">Confirmations</th>
            </tr></thead>
            <tbody>
              {transactions.map(tx => (
                <tr key={tx.id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                  <td className="px-3 py-2 font-mono text-xs">{tx.txid?.slice(0, 16)}...</td>
                  <td className="px-3 py-2 text-right">{tx.amount} {tx.currency.toUpperCase()}</td>
                  <td className="px-3 py-2 uppercase text-xs">{tx.currency}</td>
                  <td className="px-3 py-2"><span className={`text-xs px-1.5 py-0.5 rounded ${tx.status === 'confirmed' ? 'bg-green-600' : tx.status === 'pending' ? 'bg-yellow-600' : 'bg-red-600'} text-white`}>{tx.status}</span></td>
                  <td className="px-3 py-2 text-right">{tx.confirmations}</td>
                </tr>
              ))}
              {transactions.length === 0 && <tr><td colSpan={5} className="text-center py-4 text-slate-500">No transactions.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default CryptoPaymentPage;
