import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';
import type { KPISummary, MRRPoint, ARRBreakdown, ChurnAnalysis, LTVSegment, CACMetrics, AcquisitionChannel, RevenueBreakdown, RevenueForecast, CohortRow } from '../lib/types';

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

function BarChart({ data, color, height, width }: { data: { label: string; value: number }[]; color: string; height: number; width: number }) {
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
    const barW = width / data.length * 0.7;
    const gap = width / data.length * 0.3;
    const supportsHtml = typeof (ctx as any).drawElementImage === 'function';
    data.forEach((d, i) => {
      const x = i * (barW + gap) + gap / 2;
      const barH = (d.value / max) * (height - 20);
      ctx.fillStyle = color;
      ctx.fillRect(x, height - barH - 10, barW, barH);
      if (supportsHtml) {
        let span = canvas.querySelector<HTMLSpanElement>(`[data-bc="${i}"]`);
        if (!span) { span = document.createElement('span'); span.setAttribute('data-bc', String(i)); canvas.appendChild(span); }
        span.textContent = d.label;
        span.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;font:8px sans-serif;color:#94a3b8;white-space:nowrap;';
      } else {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '8px sans-serif';
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
          const span = canvas.querySelector<HTMLSpanElement>(`[data-bc="${i}"]`);
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

function MiniPieChart({ data, size }: { data: { label: string; value: number; color: string }[]; size: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const paintedRef = useRef(false);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;
    canvas.setAttribute('layoutsubtree', '');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, size, size);
    const total = data.reduce((s, d) => s + d.value, 0) || 1;
    let start = -Math.PI / 2;
    data.forEach(d => {
      const angle = (d.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(size / 2, size / 2);
      ctx.arc(size / 2, size / 2, size / 2 - 4, start, start + angle);
      ctx.closePath();
      ctx.fillStyle = d.color;
      ctx.fill();
      start += angle;
    });
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 4, 0, Math.PI * 2);
    ctx.fillStyle = '#0f172a';
    ctx.fill();
    const supportsHtml = typeof (ctx as any).drawElementImage === 'function';
    if (supportsHtml) {
      let span = canvas.querySelector<HTMLSpanElement>('[data-mpc]');
      if (!span) { span = document.createElement('span'); span.setAttribute('data-mpc', ''); canvas.appendChild(span); }
      span.textContent = `${total}`;
      span.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;font:bold 10px sans-serif;color:#e2e8f0;';
      if (!paintedRef.current) {
        paintedRef.current = true;
        const onPaint = () => {
          const c = canvasRef.current;
          const cx = c?.getContext('2d');
          if (!cx || typeof (cx as any).drawElementImage !== 'function') return;
          const dp = window.devicePixelRatio || 1;
          cx.save();
          cx.setTransform(dp, 0, 0, dp, 0, 0);
          const el = canvas.querySelector<HTMLSpanElement>('[data-mpc]');
          if (el) {
            try {
              const tr = (cx as any).drawElementImage(el, size / 2, size / 2);
              if (tr) el.style.transform = tr.toString();
            } catch {}
          }
          cx.restore();
        };
        canvas.addEventListener('paint', onPaint, { once: true });
        if (typeof (canvas as any).requestPaint === 'function') (canvas as any).requestPaint();
      }
    } else {
      ctx.fillStyle = '#e2e8f0';
      ctx.font = 'bold 10px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${total}`, size / 2, size / 2);
    }
  }, [data, size]);
  return <canvas ref={canvasRef} style={{ width: size, height: size }} />;
}

function KPICard({ title, value, subtitle, trend, color }: { title: string; value: string; subtitle?: string; trend?: { value: string; up: boolean }; color: string }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <p className="text-xs text-slate-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      {trend && (
        <p className={`text-xs mt-1 ${trend.up ? 'text-green-400' : 'text-red-400'}`}>
          {trend.up ? '↑' : '↓'} {trend.value}
        </p>
      )}
    </div>
  );
}

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

export default function BIDashboard() {
  const [kpi, setKpi] = useState<KPISummary | null>(null);
  const [mrr, setMrr] = useState<MRRPoint[]>([]);
  const [arr, setArr] = useState<ARRBreakdown | null>(null);
  const [churn, setChurn] = useState<ChurnAnalysis | null>(null);
  const [ltv, setLtv] = useState<LTVSegment[]>([]);
  const [cac, setCac] = useState<CACMetrics | null>(null);
  const [acquisition, setAcquisition] = useState<AcquisitionChannel[]>([]);
  const [revenueBreakdown, setRevenueBreakdown] = useState<RevenueBreakdown | null>(null);
  const [forecast, setForecast] = useState<RevenueForecast | null>(null);
  const [cohorts, setCohorts] = useState<CohortRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('12m');
  const [activeSection, setActiveSection] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [k, m, a, ch, l, c, acq, rev, fc, co] = await Promise.all([
        apiClient.getKpiSummary(),
        apiClient.getMRR(),
        apiClient.getARR(),
        apiClient.getChurnAnalysis(),
        apiClient.getLTVSegments(),
        apiClient.getCACMetrics(),
        apiClient.getAcquisitionChannels(),
        apiClient.getRevenueBreakdown(),
        apiClient.getRevenueForecasts(),
        apiClient.getCohortData(),
      ]);
      setKpi(k); setMrr(m); setArr(a); setChurn(ch); setLtv(l);
      setCac(c); setAcquisition(acq); setRevenueBreakdown(rev);
      setForecast(fc); setCohorts(co);
    } catch { toast.error('Failed to load BI dashboard data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const mrrTrend = mrr.map(m => m.mrr);
  const mrrLabels = mrr.map(m => m.month.slice(0, 7));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Business Intelligence</h1>
          <p className="text-slate-400">Revenue, churn, LTV, and acquisition analytics</p>
        </div>
        <select value={selectedPeriod} onChange={e => setSelectedPeriod(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm text-white outline-none focus:border-blue-500">
          <option value="1m">1 Month</option>
          <option value="3m">3 Months</option>
          <option value="6m">6 Months</option>
          <option value="12m">12 Months</option>
          <option value="all">All Time</option>
        </select>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400">Loading BI data...</div>
      ) : kpi ? (
        <>
          {/* KPI Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            <KPICard title="MRR" value={formatCurrency(kpi.mrr)} trend={{ value: `${kpi.mrr_growth.toFixed(1)}%`, up: kpi.mrr_growth >= 0 }} color="text-blue-400" subtitle="Monthly Recurring Revenue" />
            <KPICard title="ARR" value={formatCurrency(kpi.arr)} color="text-indigo-400" subtitle="Annual Run Rate" />
            <KPICard title="LTV" value={formatCurrency(kpi.ltv)} color="text-green-400" subtitle="Customer Lifetime Value" />
            <KPICard title="CAC" value={formatCurrency(kpi.cac)} color="text-yellow-400" subtitle="Customer Acquisition Cost" />
            <KPICard title="LTV:CAC" value={`${kpi.ltv_cac_ratio.toFixed(1)}x`} color={kpi.ltv_cac_ratio >= 3 ? 'text-green-400' : 'text-yellow-400'} subtitle="Ratio" />
            <KPICard title="Churn Rate" value={`${(kpi.churn_rate * 100).toFixed(1)}%`} color={kpi.churn_rate < 0.05 ? 'text-green-400' : 'text-red-400'} subtitle="Monthly" />
            <KPICard title="NRR" value={`${(kpi.nrr * 100).toFixed(1)}%`} color={kpi.nrr >= 1 ? 'text-green-400' : 'text-red-400'} subtitle="Net Revenue Retention" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPICard title="GRR" value={`${(kpi.grr * 100).toFixed(1)}%`} color="text-blue-400" subtitle="Gross Revenue Retention" />
            <KPICard title="Active Customers" value={kpi.active_customers.toLocaleString()} color="text-white" subtitle="Current" />
            <KPICard title="New Customers" value={kpi.new_customers_this_month.toLocaleString()} color="text-green-400" subtitle="This Month" />
            <KPICard title="Expansion Revenue" value={formatCurrency(kpi.expansion_revenue)} color={kpi.expansion_revenue > 0 ? 'text-green-400' : 'text-slate-400'} subtitle="From Upsells" />
          </div>

          {/* MRR / Revenue Chart */}
          {mrr.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">MRR Trend</h3>
                  <p className="text-xs text-slate-400">Monthly Recurring Revenue over time</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-blue-400">● Revenue</span>
                  <span className="text-xs text-green-400">● New</span>
                  <span className="text-xs text-red-400">● Churn</span>
                </div>
              </div>
              <div className="flex gap-6">
                <div className="flex-1">
                  <SparklineCanvas data={mrrTrend} color="#3b82f6" height={160} width={600} fillColor="rgba(59,130,246,0.1)" />
                </div>
                <div className="w-64">
                  <BarChart
                    data={mrr.map(m => ({ label: m.month.slice(5, 7), value: m.new_business }))}
                    color="#10b981" height={160} width={256} />
                </div>
              </div>
              <div className="mt-3 grid grid-cols-6 gap-2">
                {mrr.slice(-6).map(m => (
                  <div key={m.month} className="text-center">
                    <p className="text-xs text-white font-semibold">{formatCurrency(m.mrr)}</p>
                    <p className="text-xs text-slate-500">{m.month.slice(0, 7)}</p>
                    <div className="flex justify-center gap-1 mt-1">
                      <span className="text-xs text-green-400">+{formatCurrency(m.new_business)}</span>
                      <span className="text-xs text-red-400">-{formatCurrency(m.churn)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ARR Breakdown + Revenue Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {arr && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">ARR Breakdown</h3>
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-2xl font-bold text-white">{formatCurrency(arr.current_arr)}</span>
                  <span className={`text-sm ${arr.growth_rate >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {arr.growth_rate >= 0 ? '↑' : '↓'} {Math.abs(arr.growth_rate).toFixed(1)}% YoY
                  </span>
                </div>
                <div className="space-y-2">
                  {arr.segments.map((s, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">{s.name}</span>
                          <span className="text-white font-medium">{formatCurrency(s.value)}</span>
                        </div>
                        <div className="w-full h-2 bg-slate-700 rounded-full mt-1">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${s.percentage}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {revenueBreakdown && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Revenue by Category</h3>
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-2xl font-bold text-white">{formatCurrency(revenueBreakdown.total_revenue)}</span>
                  <span className={`text-sm ${revenueBreakdown.month_over_month >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {revenueBreakdown.month_over_month >= 0 ? '↑' : '↓'} {Math.abs(revenueBreakdown.month_over_month).toFixed(1)}% MoM
                  </span>
                </div>
                <div className="space-y-2">
                  {revenueBreakdown.categories.map((c, i) => (
                    <div key={i} className="flex items-center justify-between bg-slate-700/50 rounded-lg px-3 py-2">
                      <div>
                        <p className="text-sm text-white">{c.name}</p>
                        <p className="text-xs text-slate-400">{c.percentage.toFixed(1)}% of total</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-white font-medium">{formatCurrency(c.revenue)}</p>
                        <p className={`text-xs ${c.growth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {c.growth >= 0 ? '↑' : '↓'} {Math.abs(c.growth).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Churn Analysis + LTV */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {churn && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Churn Analysis</h3>
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="text-center p-2 bg-slate-700/50 rounded-lg">
                    <p className="text-lg font-bold text-red-400">{(churn.monthly_rate * 100).toFixed(1)}%</p>
                    <p className="text-xs text-slate-400">Monthly</p>
                  </div>
                  <div className="text-center p-2 bg-slate-700/50 rounded-lg">
                    <p className="text-lg font-bold text-orange-400">{(churn.quarterly_rate * 100).toFixed(1)}%</p>
                    <p className="text-xs text-slate-400">Quarterly</p>
                  </div>
                  <div className="text-center p-2 bg-slate-700/50 rounded-lg">
                    <p className="text-lg font-bold text-yellow-400">{(churn.annual_rate * 100).toFixed(1)}%</p>
                    <p className="text-xs text-slate-400">Annual</p>
                  </div>
                </div>
                <div className="flex gap-4 mb-4">
                  <div className="flex-1 text-center">
                    <p className="text-sm text-white font-semibold">NRR</p>
                    <p className={`text-lg font-bold ${churn.nrr >= 1 ? 'text-green-400' : 'text-red-400'}`}>{(churn.nrr * 100).toFixed(1)}%</p>
                  </div>
                  <div className="flex-1 text-center">
                    <p className="text-sm text-white font-semibold">GRR</p>
                    <p className={`text-lg font-bold ${churn.grr >= 0.9 ? 'text-green-400' : 'text-red-400'}`}>{(churn.grr * 100).toFixed(1)}%</p>
                  </div>
                </div>
                {churn.reasons.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-400 mb-2">Top Churn Reasons</p>
                    {churn.reasons.slice(0, 5).map((r, i) => (
                      <div key={i} className="flex items-center justify-between text-xs text-slate-300 py-1">
                        <span>{r.reason}</span>
                        <span>{r.count} customers (${r.revenue_impact.toFixed(0)})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {ltv.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">LTV by Segment</h3>
                <div className="space-y-3">
                  {ltv.map((s, i) => (
                    <div key={i} className="bg-slate-700/50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-white font-medium capitalize">{s.segment}</p>
                        <p className="text-sm text-white font-bold">{formatCurrency(s.avg_ltv)}</p>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div><span className="text-slate-400">Customers:</span> <span className="text-white">{s.customers}</span></div>
                        <div><span className="text-slate-400">Avg Months:</span> <span className="text-white">{s.avg_lifetime_months.toFixed(1)}</span></div>
                        <div><span className="text-slate-400">$/mo:</span> <span className="text-white">{formatCurrency(s.avg_revenue_per_month)}</span></div>
                      </div>
                      <div className="w-full h-1.5 bg-slate-600 rounded-full mt-2">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(s.avg_ltv / Math.max(...ltv.map(x => x.avg_ltv))) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* CAC + Acquisition */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {cac && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Customer Acquisition Cost</h3>
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="text-center p-2 bg-slate-700/50 rounded-lg">
                    <p className="text-lg font-bold text-yellow-400">{formatCurrency(cac.overall_cac)}</p>
                    <p className="text-xs text-slate-400">Avg CAC</p>
                  </div>
                  <div className="text-center p-2 bg-slate-700/50 rounded-lg">
                    <p className="text-lg font-bold text-green-400">{cac.ltv_cac_ratio.toFixed(1)}x</p>
                    <p className="text-xs text-slate-400">LTV:CAC</p>
                  </div>
                  <div className="text-center p-2 bg-slate-700/50 rounded-lg">
                    <p className="text-lg font-bold text-blue-400">{cac.payback_months.toFixed(1)}</p>
                    <p className="text-xs text-slate-400">Payback (mo)</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {cac.by_channel.map((c, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-slate-300 capitalize">{c.channel}</span>
                      <div className="flex gap-4">
                        <span className="text-white">{formatCurrency(c.cac)}</span>
                        <span className="text-slate-400">{c.conversions} conv.</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {acquisition.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Acquisition Channels</h3>
                <div className="space-y-2">
                  {acquisition.map((a, i) => (
                    <div key={i} className="bg-slate-700/50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm text-white font-medium capitalize">{a.channel}</p>
                        <p className="text-sm text-white">{a.customers} customers</p>
                      </div>
                      <div className="w-full h-2 bg-slate-600 rounded-full">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${a.percentage}%` }} />
                      </div>
                      <div className="flex justify-between text-xs text-slate-400 mt-1">
                        <span>Cost: {formatCurrency(a.cost)}</span>
                        <span>Conv: {(a.conversion_rate * 100).toFixed(1)}%</span>
                        <span>{a.percentage.toFixed(1)}% of total</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Revenue Forecast */}
          {forecast && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Revenue Forecast</h3>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-xs text-slate-400">Confidence: {(forecast.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-400 mb-2">Historical</p>
                  <div className="space-y-1">
                    {forecast.historical.slice(-6).map((h, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-slate-300">{h.month}</span>
                        <span className="text-white">{formatCurrency(h.revenue)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-2">Forecast</p>
                  <div className="space-y-1">
                    {forecast.forecast.map((f, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-blue-300">{f.month}</span>
                        <div className="text-right">
                          <span className="text-white">{formatCurrency(f.revenue)}</span>
                          <span className="text-xs text-slate-500 ml-2">
                            ({formatCurrency(f.lower_bound)} - {formatCurrency(f.upper_bound)})
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Cohort Analysis */}
          {cohorts.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Cohort Analysis</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-700">
                      <th className="pb-2 pr-3 text-left">Cohort</th>
                      <th className="pb-2 pr-3">Size</th>
                      {Array.from({ length: Math.max(...cohorts.map(c => c.periods.length)) }, (_, i) => (
                        <th key={i} className="pb-2 pr-3">M{i}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cohorts.map((c, i) => (
                      <tr key={i} className="border-b border-slate-800">
                        <td className="py-1.5 pr-3 text-white">{c.cohort}</td>
                        <td className="py-1.5 pr-3 text-slate-300">{c.size}</td>
                        {c.periods.map((p, j) => (
                          <td key={j} className="py-1.5 pr-3">
                            <span className={`px-1.5 py-0.5 rounded ${p >= 80 ? 'bg-green-600/30 text-green-300' : p >= 50 ? 'bg-yellow-600/30 text-yellow-300' : 'bg-red-600/30 text-red-300'}`}>
                              {p}%
                            </span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-slate-500">No BI data available</div>
      )}
    </div>
  );
}