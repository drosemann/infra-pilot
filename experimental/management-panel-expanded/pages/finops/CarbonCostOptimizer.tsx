import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

function CarbonIntensityBadge({ level }: { level: string }) {
  const colors: Record<string, string> = { very_low: 'bg-green-600', low: 'bg-emerald-600', moderate: 'bg-yellow-600', high: 'bg-orange-600', very_high: 'bg-red-600' };
  return <span className={`px-2 py-0.5 rounded text-xs text-white ${colors[level] || 'bg-slate-600'}`}>{level.replace('_', ' ')}</span>;
}

function RegionCarbonTable() {
  const regions = [
    { region: 'eu-north-1', intensity: 0.12, level: 'very_low', costMult: 1.09 },
    { region: 'eu-west-1', intensity: 0.25, level: 'low', costMult: 1.12 },
    { region: 'us-west-2', intensity: 0.28, level: 'low', costMult: 1.04 },
    { region: 'us-east-1', intensity: 0.42, level: 'high', costMult: 1.0 },
    { region: 'ap-southeast-1', intensity: 0.48, level: 'high', costMult: 1.22 },
    { region: 'ap-south-1', intensity: 0.62, level: 'very_high', costMult: 1.18 },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Region Carbon Intensity</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left py-2">Region</th><th className="text-right py-2">Intensity</th><th className="text-right py-2">Level</th><th className="text-right py-2">Cost Mult</th>
          </tr>
        </thead>
        <tbody>
          {regions.map((r, i) => (
            <tr key={i} className="border-b border-slate-700">
              <td className="py-2 text-white">{r.region}</td>
              <td className="py-2 text-right text-white">{r.intensity} kg/kWh</td>
              <td className="py-2 text-right"><CarbonIntensityBadge level={r.level} /></td>
              <td className="py-2 text-right text-white">×{r.costMult}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CarbonTradeoffChart() {
  const options = [
    { region: 'us-east-1 (current)', cost: 2500, co2: 504, color: 'text-slate-400' },
    { region: 'us-west-2', cost: 2375, co2: 360, color: 'text-green-400' },
    { region: 'eu-west-1', cost: 2750, co2: 300, color: 'text-yellow-400' },
    { region: 'eu-north-1', cost: 2825, co2: 144, color: 'text-emerald-400' },
  ];
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Cost-Carbon Tradeoff</h3>
      {options.map((o, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
          <span className={o.color + ' text-sm'}>{o.region}</span>
          <div className="text-right text-sm">
            <span className="text-white">${o.cost}/mo</span>
            <span className="text-slate-400 ml-2">{o.co2} kg CO2</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function CarbonMigrationEstimator() {
  const [fromRegion, setFromRegion] = useState('us-east-1');
  const [toRegion, setToRegion] = useState('eu-west-1');
  const [monthlyKwh, setMonthlyKwh] = useState(10000);
  const intensities: Record<string, number> = { 'us-east-1': 0.42, 'us-west-2': 0.28, 'eu-west-1': 0.25, 'eu-north-1': 0.12 };
  const fromInt = intensities[fromRegion] || 0.40;
  const toInt = intensities[toRegion] || 0.40;
  const currentCo2 = monthlyKwh * fromInt;
  const targetCo2 = monthlyKwh * toInt;
  const reductionPct = ((currentCo2 - targetCo2) / currentCo2) * 100;
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Migration Carbon Estimator</h3>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <select value={fromRegion} onChange={e => setFromRegion(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="us-east-1">us-east-1</option><option value="us-west-2">us-west-2</option><option value="eu-west-1">eu-west-1</option>
        </select>
        <select value={toRegion} onChange={e => setToRegion(e.target.value)} className="bg-slate-700 text-white p-2 rounded">
          <option value="eu-west-1">eu-west-1</option><option value="eu-north-1">eu-north-1</option><option value="us-west-2">us-west-2</option>
        </select>
        <input type="number" value={monthlyKwh} onChange={e => setMonthlyKwh(Number(e.target.value))} className="bg-slate-700 text-white p-2 rounded" />
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm bg-slate-700/50 rounded p-3">
        <div><span className="text-slate-400">Current CO2:</span> <span className="text-white">{currentCo2.toFixed(0)} kg/mo</span></div>
        <div><span className="text-slate-400">Target CO2:</span> <span className="text-green-400">{targetCo2.toFixed(0)} kg/mo</span></div>
        <div><span className="text-slate-400">Reduction:</span> <span className="text-green-400">{reductionPct.toFixed(1)}%</span></div>
        <div><span className="text-slate-400">Annual Savings:</span> <span className="text-green-400">{((currentCo2 - targetCo2) * 12 / 1000).toFixed(2)} tons</span></div>
      </div>
    </div>
  );
}

export default function CarbonOffsetCalculator() {
  const [co2Kg, setCo2Kg] = useState(12450);
  const [pricePerTon, setPricePerTon] = useState(50);
  const tons = co2Kg / 1000;
  const offsetCost = tons * pricePerTon;
  const treesNeeded = Math.round(tons * 45);
  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-3">Offset Calculator</h3>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div><label className="block text-xs text-slate-400 mb-1">CO2 (kg)</label><input type="number" value={co2Kg} onChange={e => setCo2Kg(+e.target.value)} className="w-full bg-slate-700 text-white p-2 rounded" /></div>
        <div><label className="block text-xs text-slate-400 mb-1">Price/Ton ($)</label><input type="number" value={pricePerTon} onChange={e => setPricePerTon(+e.target.value)} className="w-full bg-slate-700 text-white p-2 rounded" /></div>
      </div>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Tons</span><div className="text-white font-semibold">{tons.toFixed(2)}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Cost</span><div className="text-green-400 font-semibold">${offsetCost.toFixed(2)}</div></div>
        <div className="bg-slate-700/50 rounded p-2"><span className="text-slate-400">Trees</span><div className="text-white font-semibold">{treesNeeded}</div></div>
      </div>
    </div>
  );
}

function CarbonCostOptimizer() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [sustainability, setSustainability] = useState<any>(null);
  const [showRegister, setShowRegister] = useState(false);
  const [form, setForm] = useState({ name: '', provider: 'aws', region: 'us-east-1', monthly_cost: 1000 });

  useEffect(() => {
    apiClient.get('/api/v1/finops/carbon/recommendations').then(r => setRecommendations(r.recommendations || [])).catch(() => {});
    apiClient.get('/api/v1/finops/carbon/sustainability-budget').then(r => setSustainability(r)).catch(() => {});
  }, []);

  const registerAsset = async () => {
    const res = await apiClient.post('/api/v1/finops/carbon/assets', form);
    if (res.id) { toast?.success('Asset registered!'); setShowRegister(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Carbon-Aware Cost Optimization</h1>
          <p className="text-slate-400">Combine cost and carbon data for sustainable savings</p>
        </div>
        <button onClick={() => setShowRegister(!showRegister)} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
          {showRegister ? 'Cancel' : '+ Register Asset'}
        </button>
      </div>
      {sustainability && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-white">{sustainability.total_assets}</div>
            <div className="text-sm text-slate-400">Assets</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-green-400">{sustainability.total_annual_co2_tons}t</div>
            <div className="text-sm text-slate-400">Annual CO2</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-blue-400">${sustainability.total_monthly_cost?.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Monthly Cost</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <div className="text-2xl font-bold text-yellow-400">{sustainability.avg_intensity_level}</div>
            <div className="text-sm text-slate-400">Carbon Intensity</div>
          </div>
        </div>
      )}
      {showRegister && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 space-y-3">
          <input placeholder="Asset name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full bg-slate-700 text-white p-2 rounded" />
          <div className="grid grid-cols-3 gap-3">
            <select value={form.provider} onChange={e => setForm({...form, provider: e.target.value})} className="bg-slate-700 text-white p-2 rounded">
              <option value="aws">AWS</option><option value="azure">Azure</option><option value="gcp">GCP</option>
            </select>
            <select value={form.region} onChange={e => setForm({...form, region: e.target.value})} className="bg-slate-700 text-white p-2 rounded">
              <option value="us-east-1">us-east-1</option><option value="eu-west-1">eu-west-1</option><option value="eu-north-1">eu-north-1</option>
            </select>
            <input type="number" placeholder="Monthly cost" value={form.monthly_cost} onChange={e => setForm({...form, monthly_cost: +e.target.value})} className="bg-slate-700 text-white p-2 rounded" />
          </div>
          <button onClick={registerAsset} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">Register</button>
        </div>
      )}
      <div className="space-y-3">
        {recommendations.map((r: any) => (
          <div key={r.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="flex justify-between">
              <h3 className="text-white font-semibold">{r.asset_name}: {r.current_region} → {r.recommended_region}</h3>
              <span className="text-xs text-slate-400">{r.strategy}</span>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
              <div><span className="text-slate-400">Cost:</span> <span className="text-white">${r.current_monthly_cost} → ${r.new_monthly_cost}</span></div>
              <div><span className="text-slate-400">CO2:</span> <span className={r.monthly_co2_reduction_kg > 0 ? 'text-green-400' : 'text-red-400'}>
                {r.current_monthly_co2_kg}kg → {r.new_monthly_co2_kg}kg
              </span></div>
              <div><span className="text-slate-400">Score:</span> <span className="text-white">{r.optimization_score}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
