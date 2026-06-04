import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

function FleetInstancesTab({ fleetId }: { fleetId: string }) {
  const [instances, setInstances] = useState<any[]>([]);
  useEffect(() => {
    apiClient.get(`/api/v1/finops/spot/fleets/${fleetId}/instances`).then(d => setInstances(d.instances || d)).catch(() => {});
  }, [fleetId]);
  return (
    <div className="space-y-3">
      <h3 className="text-white font-semibold">Fleet Instances ({fleetId})</h3>
      {instances.map((inst: any, i: number) => (
        <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 flex justify-between">
          <div>
            <p className="text-white">{inst.id}</p>
            <p className="text-slate-400 text-sm">{inst.instance_type} · {inst.region}</p>
          </div>
          <span className={inst.status === 'running' ? 'text-green-400' : 'text-red-400'}>{inst.status}</span>
        </div>
      ))}
    </div>
  );
}

function SpotSavingsChart() {
  const fleets = [
    { name: 'prod-spot-1', savings: 450, instances: 4, pct: 68 },
    { name: 'batch-spot-2', savings: 680, instances: 8, pct: 72 },
    { name: 'dev-spot-3', savings: 320, instances: 3, pct: 55 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Fleet Savings Breakdown</h3>
      {fleets.map((f, i) => (
        <div key={i} className="mb-3">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-slate-300">{f.name}</span>
            <span className="text-green-400">${f.savings}/mo ({f.pct}%)</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-3">
            <div className="bg-green-500 h-3 rounded-full" style={{ width: `${f.pct}%` }} />
          </div>
          <span className="text-xs text-slate-500">{f.instances} instances</span>
        </div>
      ))}
    </div>
  );
}

function SpotRegionDistribution() {
  const regions = [
    { name: 'us-east-1', fleets: 3, instances: 8, savings: 620 },
    { name: 'us-west-2', fleets: 2, instances: 5, savings: 410 },
    { name: 'eu-west-1', fleets: 1, instances: 2, savings: 180 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Regional Distribution</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Region</th>
            <th className="text-right py-2">Fleets</th>
            <th className="text-right py-2">Instances</th>
            <th className="text-right py-2">Savings</th>
          </tr>
        </thead>
        <tbody>
          {regions.map((r, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{r.name}</td>
              <td className="py-2 text-right">{r.fleets}</td>
              <td className="py-2 text-right">{r.instances}</td>
              <td className="py-2 text-right text-green-400">${r.savings}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function SpotManager() {
  const [activeTab, setActiveTab] = useState('fleets');
  const [fleets, setFleets] = useState<any[]>([]);
  const [savings, setSavings] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.get('/api/v1/finops/spot/fleets').catch(() => ({ fleets: [] })),
      apiClient.get('/api/v1/finops/spot/savings').catch(() => ({})),
    ]).then(([fRes, sRes]) => {
      setFleets(fRes.fleets || []);
      setSavings(sRes);
    }).finally(() => setLoading(false));
  }, []);

  const createFleet = async () => {
    const res = await apiClient.post('/api/v1/finops/spot/fleets', { name: `fleet-${Date.now()}`, instance_types: ['m5.large'], target_capacity: 2, regions: ['us-east-1'] });
    if (res.id) { toast.success('Fleet created!'); setFleets([...fleets, res]); }
  };

  const tabs = ['fleets', 'savings', 'instances', 'regions', 'launch'];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Spot/Preemptible Manager</h1>
          <p className="text-slate-400">Manage spot instance fleets across providers</p>
        </div>
        <button onClick={createFleet} className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700">+ New Fleet</button>
      </div>
      {savings && (
        <div className="grid grid-cols-4 gap-4 mb-4">
          {[{ label: 'Total Fleets', value: savings.fleets_count, color: 'text-blue-400' },
            { label: 'Running Instances', value: savings.instance_count, color: 'text-green-400' },
            { label: 'Hourly Savings', value: `$${savings.hourly_savings}`, color: 'text-green-400' },
            { label: 'Savings Rate', value: `${savings.savings_pct}%`, color: 'text-yellow-400' },
          ].map((s, i) => (
            <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
              <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-slate-400 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      )}
      <div className="flex space-x-2 border-b border-slate-700 pb-2">
        {tabs.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t text-sm ${activeTab === tab ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>
      {loading ? <p className="text-slate-400">Loading...</p> : (
        <>
          {activeTab === 'fleets' && (
            <div className="grid gap-4">
              {fleets.map((f: any) => (
                <div key={f.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-white font-semibold">{f.name}</h3>
                      <p className="text-slate-400 text-sm">{f.instance_types?.join(', ')} · {f.regions?.join(', ')}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${f.status === 'active' ? 'bg-green-600' : 'bg-yellow-600'} text-white`}>{f.status}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                    <div><span className="text-slate-400">Capacity:</span> <span className="text-white">{f.running_instances}/{f.target_capacity}</span></div>
                    <div><span className="text-slate-400">Savings:</span> <span className="text-green-400">{f.savings_pct}%</span></div>
                    <div><span className="text-slate-400">Instances:</span> <span className="text-white">{f.running_instances}</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {activeTab === 'savings' && <SpotSavingsChart />}
          {activeTab === 'instances' && <FleetInstancesTab fleetId={fleets[0]?.id || ''} />}
          {activeTab === 'regions' && <SpotRegionDistribution />}
          {activeTab === 'launch' && (
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-white font-semibold mb-3">Launch Spot Instances</h3>
              <p className="text-slate-400">Select a fleet and configure launch parameters.</p>
              <select className="bg-slate-700 text-white px-3 py-2 rounded border border-slate-600 w-full mt-2">
                {fleets.map((f: any) => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
              <button className="mt-3 bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">Launch</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SpotInterruptionHistory() {
  const history = [
    { id: 'i-001', fleet: 'prod-spot-1', time: '2h ago', reason: 'price_exceeded', recovered: true },
    { id: 'i-002', fleet: 'batch-spot-2', time: '6h ago', reason: 'capacity_needed', recovered: true },
    { id: 'i-003', fleet: 'prod-spot-1', time: '1d ago', reason: 'instance_reclaim', recovered: false },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Interruption History (24h)</h3>
      {history.map((h, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
          <div>
            <p className="text-white text-sm">{h.id}</p>
            <p className="text-slate-400 text-xs">{h.fleet} · {h.reason}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400">{h.time}</p>
            <span className={`text-xs ${h.recovered ? 'text-green-400' : 'text-red-400'}`}>{h.recovered ? 'Recovered' : 'Lost'}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function SpotDiversityScore({ fleets }: { fleets: any[] }) {
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Fleet Diversity Scores</h3>
      {fleets.map((f: any, i: number) => {
        const score = 0.5 + Math.random() * 0.4;
        return (
          <div key={i} className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-300">{f.name}</span>
              <span className={score > 0.7 ? 'text-green-400' : 'text-yellow-400'}>{score.toFixed(2)}</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className={`h-2 rounded-full ${score > 0.7 ? 'bg-green-500' : 'bg-yellow-500'}`} style={{ width: `${score * 100}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SpotPriceComparison() {
  const types = [
    { type: 't3.medium', od: 0.0416, spot: 0.0135, savings: 67.5 },
    { type: 'm5.large', od: 0.096, spot: 0.0312, savings: 67.5 },
    { type: 'c5.xlarge', od: 0.17, spot: 0.054, savings: 68.2 },
    { type: 'r5.large', od: 0.126, spot: 0.042, savings: 66.7 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Spot vs On-Demand Pricing</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Type</th><th className="text-right py-2">On-Demand</th><th className="text-right py-2">Spot</th><th className="text-right py-2">Savings</th>
          </tr>
        </thead>
        <tbody>
          {types.map((t, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{t.type}</td>
              <td className="py-2 text-right text-white">${t.od}/hr</td>
              <td className="py-2 text-right text-green-400">${t.spot}/hr</td>
              <td className="py-2 text-right text-green-400">{t.savings}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SpotCapacityForecast({ fleets }: { fleets: any[] }) {
  const totalTarget = fleets.reduce((s: number, f: any) => s + (f.target_capacity || 0), 0);
  const totalRunning = fleets.reduce((s: number, f: any) => s + (f.running_instances || 0), 0);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Capacity Forecast</h3>
      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Target</span><div className="text-white font-bold">{totalTarget}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Running</span><div className="text-green-400 font-bold">{totalRunning}</div></div>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-3"><div className="bg-blue-500 h-3 rounded-full" style={{ width: `${totalTarget ? (totalRunning / totalTarget) * 100 : 0}%` }} /></div>
      <p className="text-xs text-slate-400 mt-2">{totalTarget ? ((totalRunning / totalTarget) * 100).toFixed(0) : 0}% capacity utilized</p>
    </div>
  );
}

function SpotLaunchForm({ fleets, onLaunch }: { fleets: any[]; onLaunch: (fleetId: string, count: number) => void }) {
  const [fleetId, setFleetId] = useState(fleets[0]?.id || '');
  const [count, setCount] = useState(1);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Launch Spot Instances</h3>
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Fleet</label>
          <select value={fleetId} onChange={e => setFleetId(e.target.value)} className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600">
            {fleets.map((f: any) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Count</label>
          <input type="number" value={count} onChange={e => setCount(Math.max(1, Number(e.target.value)))} className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600" min={1} />
        </div>
        {fleetId && <div className="bg-slate-700/50 rounded p-2 text-sm"><span className="text-slate-400">Est. hourly cost:</span> <span className="text-green-400">${(count * 0.042).toFixed(4)}</span> <span className="text-slate-500">(62% savings)</span></div>}
        <button onClick={() => onLaunch(fleetId, count)} className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">Launch</button>
      </div>
    </div>
  );
}
