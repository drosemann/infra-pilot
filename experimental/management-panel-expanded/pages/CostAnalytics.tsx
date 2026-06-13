import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';
import type { CostBreakdown, CostTrendPoint, UnitEconomics, Budget, SavingsRecommendation, CostForecast } from '../lib/types';

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(2)}K`;
  return `$${n.toFixed(2)}`;
}

function SparklineCanvas({ data, color, height, width, fillColor }: { data: number[]; color: string; height: number; width: number; fillColor?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
    if (fillColor) {
      ctx.lineTo(width, height);
      ctx.lineTo(0, height);
      ctx.closePath();
      ctx.fillStyle = fillColor;
      ctx.fill();
    }
  }, [data, color, height, width, fillColor]);
  return <canvas ref={canvasRef} style={{ width, height }} />;
}

function MiniBarChart({ data, color, height, width }: { data: { label: string; value: number; color?: string }[]; color: string; height: number; width: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const paintedRef = useRef(false);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;
    canvas.setAttribute('layoutsubtree', '');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);
    const max = Math.max(...data.map(d => d.value), 1);
    const barW = width / data.length * 0.6;
    const gap = width / data.length * 0.4;
    const supportsHtml = typeof (ctx as any).drawElementImage === 'function';
    data.forEach((d, i) => {
      const x = i * (barW + gap) + gap / 2;
      const barH = (d.value / max) * (height - 20);
      ctx.fillStyle = d.color || color;
      ctx.fillRect(x, height - barH - 14, barW, barH);
      if (supportsHtml) {
        let span = canvas.querySelector<HTMLSpanElement>(`[data-mbc="${i}"]`);
        if (!span) { span = document.createElement('span'); span.setAttribute('data-mbc', String(i)); canvas.appendChild(span); }
        span.textContent = d.label;
        span.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;font:7px sans-serif;color:#94a3b8;white-space:nowrap;';
      } else {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '7px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.label, x + barW / 2, height - 2);
      }
    });
    if (supportsHtml && !paintedRef.current) {
      paintedRef.current = true;
      const onPaint = () => {
        const c = canvasRef.current;
        const cx = c?.getContext('2d');
        if (!cx || typeof (cx as any).drawElementImage !== 'function') return;
        const dp = window.devicePixelRatio || 1;
        cx.save();
        cx.setTransform(dp, 0, 0, dp, 0, 0);
        data.forEach((d, i) => {
          const span = canvas.querySelector<HTMLSpanElement>(`[data-mbc="${i}"]`);
          if (!span) return;
          const x = i * (barW + gap) + gap / 2;
          try {
            const tr = (cx as any).drawElementImage(span, x + barW / 2, height - 2);
            if (tr) span.style.transform = tr.toString();
          } catch {}
        });
        cx.restore();
      };
      canvas.addEventListener('paint', onPaint, { once: true });
      if (typeof (canvas as any).requestPaint === 'function') (canvas as any).requestPaint();
    }
  }, [data, color, height, width]);
  return <canvas ref={canvasRef} style={{ width, height }} />;
}

function BudgetGauge({ spent, budget, threshold }: { spent: number; budget: number; threshold: number }) {
  const pct = budget > 0 ? (spent / budget) * 100 : 0;
  const circumference = 2 * Math.PI * 32;
  const offset = circumference - (Math.min(pct, 100) / 100) * circumference;
  const color = pct >= 100 ? '#ef4444' : pct >= threshold ? '#f59e0b' : '#10b981';
  return (
    <svg width="80" height="80" viewBox="0 0 80 80">
      <circle cx="40" cy="40" r="32" fill="none" stroke="#1e293b" strokeWidth="6" />
      <circle cx="40" cy="40" r="32" fill="none" stroke={color} strokeWidth="6"
        strokeDasharray={circumference} strokeDashoffset={offset}
        transform="rotate(-90 40 40)" strokeLinecap="round" />
      <text x="40" y="36" textAnchor="middle" dominantBaseline="central"
        fontSize="14" fontWeight="bold" fill="#e2e8f0">{Math.round(pct)}%</text>
      <text x="40" y="54" textAnchor="middle" dominantBaseline="central"
        fontSize="7" fill="#64748b">used</text>
    </svg>
  );
}

export default function CostAnalytics() {
  const [breakdown, setBreakdown] = useState<CostBreakdown | null>(null);
  const [trends, setTrends] = useState<CostTrendPoint[]>([]);
  const [unitEconomics, setUnitEconomics] = useState<UnitEconomics | null>(null);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [recommendations, setRecommendations] = useState<SavingsRecommendation[]>([]);
  const [forecast, setForecast] = useState<CostForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [trendPeriod, setTrendPeriod] = useState('30d');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [b, t, u, buds, recs, fc] = await Promise.all([
        apiClient.getCostBreakdown(),
        apiClient.getCostTrends(),
        apiClient.getUnitEconomics(),
        apiClient.getBudgets(),
        apiClient.getSavingsRecommendations(),
        apiClient.getCostForecast(),
      ]);
      setBreakdown(b); setTrends(t); setUnitEconomics(u);
      setBudgets(buds); setRecommendations(recs); setForecast(fc);
    } catch { toast.error('Failed to load cost analytics'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const trendValues = useMemo(() => trends.map(t => t.cost), [trends]);
  const trendLabels = useMemo(() => trends.map(t => t.date.slice(5)), [trends]);
  const totalPotentialSavings = useMemo(() => recommendations.reduce((s, r) => s + r.potential_savings, 0), [recommendations]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Cost & Usage Analytics</h1>
          <p className="text-slate-400">Per-service cost breakdown, unit economics, budgets, and optimization</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400">Loading cost data...</div>
      ) : (
        <>
          {/* KPI Summary */}
          {breakdown && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Total Monthly Cost</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(breakdown.total_cost)}</p>
                <p className={`text-xs mt-1 ${breakdown.month_over_month >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {breakdown.month_over_month >= 0 ? '↑' : '↓'} {Math.abs(breakdown.month_over_month).toFixed(1)}% MoM
                </p>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Cost per Request</p>
                <p className="text-2xl font-bold text-blue-400">{unitEconomics?.cost_per_request.toFixed(5) ?? '--'}</p>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Cost per Active User</p>
                <p className="text-2xl font-bold text-green-400">{formatCurrency(unitEconomics?.cost_per_active_user ?? 0)}</p>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Potential Savings</p>
                <p className="text-2xl font-bold text-yellow-400">{formatCurrency(totalPotentialSavings)}</p>
              </div>
            </div>
          )}

          {/* Cost Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {breakdown && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Cost by Service</h3>
                <div className="space-y-2">
                  {breakdown.by_service.slice(0, 10).map((s, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-full">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-300">{s.service}</span>
                          <span className="text-white font-medium">{formatCurrency(s.cost)}</span>
                        </div>
                        <div className="w-full h-2 bg-slate-700 rounded-full">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${s.percentage}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {breakdown && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Cost by Provider</h3>
                <div className="space-y-2">
                  {breakdown.by_provider.map((p, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-full">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-300 capitalize">{p.provider}</span>
                          <span className="text-white font-medium">{formatCurrency(p.cost)} ({p.percentage.toFixed(1)}%)</span>
                        </div>
                        <div className="w-full h-2 bg-slate-700 rounded-full">
                          <div className="h-full rounded-full" style={{ width: `${p.percentage}%`, backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'][i % 5] }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Cost Trends */}
          {trends.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Cost Trends</h3>
                <div className="flex gap-2">
                  {['7d', '30d', '90d', '1y'].map(p => (
                    <button key={p} onClick={() => setTrendPeriod(p)}
                      className={`px-2 py-1 text-xs rounded transition-colors ${trendPeriod === p ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>{p}</button>
                  ))}
                </div>
              </div>
              <div className="flex gap-6">
                <div className="flex-1">
                  <SparklineCanvas data={trendValues} color="#3b82f6" height={160} width={600} fillColor="rgba(59,130,246,0.1)" />
                </div>
                <div className="w-48">
                  <MiniBarChart
                    data={trends.slice(-7).map(t => ({ label: t.date.slice(5, 10), value: t.cost }))}
                    color="#3b82f6" height={160} width={192} />
                </div>
              </div>
              <div className="mt-3 flex gap-2 flex-wrap">
                {trends.slice(-5).map(t => (
                  <div key={t.date} className="text-center px-3 py-1 bg-slate-700/50 rounded">
                    <p className="text-xs text-slate-400">{t.date.slice(5, 10)}</p>
                    <p className="text-sm text-white font-semibold">{formatCurrency(t.cost)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unit Economics + Environment/Team */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {unitEconomics && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Unit Economics</h3>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400">Cost/Request</p>
                    <p className="text-lg font-bold text-blue-400">${unitEconomics.cost_per_request.toFixed(5)}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400">Cost/GB Storage</p>
                    <p className="text-lg font-bold text-green-400">${unitEconomics.cost_per_gb_storage.toFixed(4)}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400">Cost/User</p>
                    <p className="text-lg font-bold text-purple-400">{formatCurrency(unitEconomics.cost_per_active_user)}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400">Cost/API Call</p>
                    <p className="text-lg font-bold text-yellow-400">${unitEconomics.cost_per_api_call.toFixed(5)}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {unitEconomics.by_service.slice(0, 8).map((s, i) => (
                    <div key={i} className="flex justify-between text-xs text-slate-300">
                      <span>{s.service}</span>
                      <span>${s.cost_per_request.toFixed(4)}/req | ${s.cost_per_user.toFixed(2)}/user</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {breakdown && (
              <div className="space-y-4">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">By Environment</h3>
                  {breakdown.by_environment.map((e, i) => (
                    <div key={i} className="flex items-center gap-3 mb-2">
                      <span className="text-xs text-slate-400 w-16 capitalize">{e.environment}</span>
                      <div className="flex-1 h-2 bg-slate-700 rounded-full">
                        <div className="h-full rounded-full" style={{ width: `${e.percentage}%`, backgroundColor: e.environment === 'production' ? '#ef4444' : e.environment === 'staging' ? '#f59e0b' : '#3b82f6' }} />
                      </div>
                      <span className="text-xs text-white w-20 text-right">{formatCurrency(e.cost)}</span>
                    </div>
                  ))}
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">By Team</h3>
                  {breakdown.by_team.map((t, i) => (
                    <div key={i} className="flex items-center gap-3 mb-2">
                      <span className="text-xs text-slate-400 w-24">{t.team}</span>
                      <div className="flex-1 h-2 bg-slate-700 rounded-full">
                        <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${t.percentage}%` }} />
                      </div>
                      <span className="text-xs text-white w-20 text-right">{formatCurrency(t.cost)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Budgets */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Budgets</h3>
              <button onClick={() => setShowBudgetForm(!showBudgetForm)}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors">
                + Add Budget
              </button>
            </div>

            {showBudgetForm && (
              <div className="mb-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                <BudgetForm onSaved={() => { setShowBudgetForm(false); loadData(); }} onCancel={() => setShowBudgetForm(false)} />
              </div>
            )}

            {budgets.length === 0 ? (
              <div className="text-center py-8 text-slate-500">No budgets configured</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {budgets.map(b => {
                  const pct = b.amount > 0 ? (b.spent / b.amount) * 100 : 0;
                  return (
                    <div key={b.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-sm font-semibold text-white">{b.name}</p>
                        <span className={`text-xs px-2 py-0.5 rounded ${b.status === 'active' ? 'bg-green-600/20 text-green-400' : b.status === 'exceeded' ? 'bg-red-600/20 text-red-400' : b.status === 'at_risk' ? 'bg-yellow-600/20 text-yellow-400' : 'bg-slate-600/20 text-slate-400'}`}>
                          {b.status.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <BudgetGauge spent={b.spent} budget={b.amount} threshold={b.alert_threshold} />
                        <div className="flex-1">
                          <p className="text-xs text-slate-400">Spent</p>
                          <p className="text-sm font-bold text-white">{formatCurrency(b.spent)}</p>
                          <p className="text-xs text-slate-400 mt-1">Budget</p>
                          <p className="text-sm font-bold text-white">{formatCurrency(b.amount)}</p>
                          <p className="text-xs text-slate-500 mt-1 capitalize">{b.period} | Alert at {b.alert_threshold}%</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Savings Recommendations */}
          {recommendations.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">
                Savings Recommendations
                <span className="text-sm font-normal text-green-400 ml-2">Total: {formatCurrency(totalPotentialSavings)}/mo</span>
              </h3>
              <div className="space-y-3">
                {recommendations.map(r => (
                  <div key={r.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-semibold text-white">{r.title}</p>
                          <span className={`text-xs px-2 py-0.5 rounded ${r.effort === 'low' ? 'bg-green-600/20 text-green-400' : r.effort === 'medium' ? 'bg-yellow-600/20 text-yellow-400' : 'bg-red-600/20 text-red-400'}`}>
                            {r.effort} effort
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">{r.description}</p>
                        <span className="text-xs text-slate-500 bg-slate-600 px-2 py-0.5 rounded mt-2 inline-block">{r.category}</span>
                      </div>
                      <div className="text-right ml-4">
                        <p className="text-sm font-bold text-green-400">{formatCurrency(r.potential_savings)}</p>
                        <p className="text-xs text-slate-500">/mo</p>
                      </div>
                    </div>
                    <div className="mt-2">
                      <span className="text-xs text-blue-400 hover:text-blue-300 cursor-pointer">{r.action}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cost Forecast */}
          {forecast && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Cost Forecast</h3>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-2xl font-bold text-white">{formatCurrency(forecast.next_month_estimate)}</span>
                <span className="text-xs text-slate-400">Next month estimate</span>
                <span className="text-xs text-slate-500">Confidence: {(forecast.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {forecast.historical.slice(-3).map(h => (
                  <div key={h.month} className="bg-slate-700/50 rounded-lg p-3">
                    <p className="text-xs text-slate-400">{h.month}</p>
                    <p className="text-sm text-white font-semibold">{formatCurrency(h.actual)}</p>
                    <p className="text-xs text-slate-500">actual</p>
                  </div>
                ))}
                {forecast.projected.map(p => (
                  <div key={p.month} className="bg-blue-600/10 border border-blue-600/30 rounded-lg p-3">
                    <p className="text-xs text-blue-300">{p.month}</p>
                    <p className="text-sm text-blue-400 font-semibold">{formatCurrency(p.forecast)}</p>
                    <p className="text-xs text-slate-500">{formatCurrency(p.lower)} - {formatCurrency(p.upper)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function BudgetForm({ onSaved, onCancel }: { onSaved: () => void; onCancel: () => void }) {
  const [name, setName] = useState('');
  const [amount, setAmount] = useState(1000);
  const [period, setPeriod] = useState<'monthly' | 'quarterly' | 'annual'>('monthly');
  const [alertThreshold, setAlertThreshold] = useState(80);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!name || amount <= 0) { toast.error('Enter a name and valid amount'); return; }
    setSaving(true);
    try {
      await apiClient.createBudget({
        name, amount, period, alert_threshold: alertThreshold,
        scope: 'general', spent: 0, start_date: new Date().toISOString(), status: 'active',
      });
      toast.success('Budget created');
      onSaved();
    } catch { toast.error('Failed to create budget'); }
    finally { setSaving(false); }
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Name</label>
        <input type="text" value={name} onChange={e => setName(e.target.value)}
          placeholder="e.g. Infrastructure"
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Amount ($)</label>
        <input type="number" min={0} value={amount} onChange={e => setAmount(Number(e.target.value))}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Period</label>
        <select value={period} onChange={e => setPeriod(e.target.value as any)}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
          <option value="annual">Annual</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">Alert at %</label>
        <input type="number" min={1} max={100} value={alertThreshold} onChange={e => setAlertThreshold(Number(e.target.value))}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
      </div>
      <div className="flex items-end gap-2">
        <button onClick={handleSave} disabled={saving}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
          {saving ? '...' : 'Create'}
        </button>
        <button onClick={onCancel}
          className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">Cancel</button>
      </div>
    </div>
  );
}