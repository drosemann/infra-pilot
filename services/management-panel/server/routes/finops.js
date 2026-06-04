const express = require('express');
const router = express.Router();

let recommendations = [];
let fleets = [];
let fleetInstances = {};
let unitMetrics = [];
let unitTargets = [];
let anomalies = [];
let profiles = [];
let budgets = [];
let budgetSpend = [];
let rightsizingRecs = [];
let resources = [];
let wasteFindings = [];
let carbonAssets = [];
let carbonRecs = [];
let workloads = [];
let comparisons = [];
let reports = [];
let allocations = [];

// === Commitment Discount Optimizer ===
router.get('/api/finops/commitment/recommendations', (req, res) => res.json(recommendations));
router.post('/api/finops/commitment/recommendations', (req, res) => {
  const r = { id: `rec-${Date.now()}`, ...req.body, status: 'open', savings_pct: 25, created_at: new Date().toISOString() };
  recommendations.push(r); res.json(r);
});
router.get('/api/finops/commitment/summary', (req, res) => {
  const totalSavings = recommendations.filter(r => r.status === 'implemented').reduce((s, r) => s + (r.estimated_monthly_savings || 0), 0);
  res.json({ total_recommendations: recommendations.length, open: recommendations.filter(r => r.status === 'open').length, implemented: recommendations.filter(r => r.status === 'implemented').length, total_estimated_savings: totalSavings, coverage_pct: 68 });
});
router.post('/api/finops/commitment/recommendations/:id/implement', (req, res) => {
  const r = recommendations.find(x => x.id === req.params.id); if (!r) return res.status(404).json({ error: 'Not found' });
  r.status = 'implemented'; r.implemented_at = new Date().toISOString(); res.json(r);
});
router.get('/api/finops/commitment/commitments', (req, res) => {
  res.json([{ provider: 'aws', commitment_type: 'compute_savings_plan', term: '1yr', monthly_cost: 5200, coverage_pct: 72, status: 'active' }, { provider: 'azure', commitment_type: 'reserved_instance', term: '3yr', monthly_cost: 3800, coverage_pct: 65, status: 'active' }]);
});
router.post('/api/finops/commitment/analyze', (req, res) => {
  res.json({ analysis_id: `analysis-${Date.now()}`, current_coverage: 68, recommended_coverage: 85, potential_savings: 4200, recommendation: 'Increase 1yr Compute Savings Plan coverage by 15%', risk_level: 'low' });
});
router.get('/api/finops/commitment/coverage-gaps', (req, res) => {
  res.json([{ service: 'EC2', coverage_pct: 55, gap_pct: 45, potential_savings: 1800 }, { service: 'RDS', coverage_pct: 40, gap_pct: 60, potential_savings: 1200 }, { service: 'Lambda', coverage_pct: 0, gap_pct: 100, potential_savings: 600 }]);
});

// === Spot/Preemptible Manager ===
router.get('/api/finops/spot/fleets', (req, res) => res.json(fleets));
router.post('/api/finops/spot/fleets', (req, res) => {
  const f = { id: `fleet-${Date.now()}`, ...req.body, status: 'active', running_instances: 0, savings_pct: 62, created_at: new Date().toISOString() };
  fleets.push(f); fleetInstances[f.id] = []; res.json(f);
});
router.get('/api/finops/spot/fleets/:id', (req, res) => {
  const f = fleets.find(x => x.id === req.params.id); if (!f) return res.status(404).json({ error: 'Not found' }); res.json(f);
});
router.patch('/api/finops/spot/fleets/:id', (req, res) => {
  const f = fleets.find(x => x.id === req.params.id); if (!f) return res.status(404).json({ error: 'Not found' });
  Object.assign(f, req.body); res.json(f);
});
router.get('/api/finops/spot/fleets/:id/instances', (req, res) => {
  res.json(fleetInstances[req.params.id] || []);
});
router.get('/api/finops/spot/savings', (req, res) => {
  const totalSavings = fleets.reduce((s, f) => s + (f.savings_pct || 0) * 100, 0);
  res.json({ total_savings: totalSavings, savings_pct: 62, instance_count: fleets.reduce((s, f) => s + (f.running_instances || 0), 0), fleets_count: fleets.length });
});
router.post('/api/finops/spot/fleets/:id/launch', (req, res) => {
  const f = fleets.find(x => x.id === req.params.id); if (!f) return res.status(404).json({ error: 'Not found' });
  const count = req.body.count || 1; f.running_instances = (f.running_instances || 0) + count;
  for (let i = 0; i < count; i++) { const inst = { id: `inst-${Date.now()}-${i}`, fleet_id: f.id, status: 'running', launched_at: new Date().toISOString() }; fleetInstances[f.id] = fleetInstances[f.id] || []; fleetInstances[f.id].push(inst); }
  res.json({ success: true, launched: count, fleet_id: f.id, total_running: f.running_instances });
});
router.post('/api/finops/spot/instances/:id/interrupt', (req, res) => {
  res.json({ success: true, instance_id: req.params.id, status: 'interrupted', interruption_time: new Date().toISOString(), savings_lost: 12.5 });
});
router.get('/api/finops/spot/savings', (req, res) => {
  res.json({ total_savings: 45200, savings_pct: 62, instance_count: 24, fleets_count: fleets.length });
});

// === Unit Economics ===
router.get('/api/finops/unit-economics/metrics', (req, res) => {
  let filtered = [...unitMetrics];
  if (req.query.customer_id) filtered = filtered.filter(m => m.customer_id === req.query.customer_id);
  if (req.query.dimension) filtered = filtered.filter(m => m.dimension === req.query.dimension);
  res.json(filtered);
});
router.post('/api/finops/unit-economics/metrics', (req, res) => {
  const m = { id: `um-${Date.now()}`, ...req.body, recorded_at: new Date().toISOString() }; unitMetrics.push(m); res.json(m);
});
router.get('/api/finops/unit-economics/targets', (req, res) => res.json(unitTargets));
router.post('/api/finops/unit-economics/targets', (req, res) => {
  const t = { id: `ut-${Date.now()}`, ...req.body, created_at: new Date().toISOString() }; unitTargets.push(t); res.json(t);
});
router.get('/api/finops/unit-economics/violations', (req, res) => {
  res.json(unitMetrics.filter(m => { const t = unitTargets.find(x => x.metric_name === m.metric_name); return t && m.value > t.target_value * (1 + (t.threshold_pct || 10) / 100); }));
});
router.get('/api/finops/unit-economics/overview', (req, res) => {
  res.json({ total_metrics: unitMetrics.length, total_targets: unitTargets.length, violations: unitMetrics.filter(m => { const t = unitTargets.find(x => x.metric_name === m.metric_name); return t && m.value > t.target_value * (1 + (t.threshold_pct || 10) / 100); }).length, customer_breakdown: [...new Set(unitMetrics.map(m => m.customer_id))].length });
});

// === Real-Time Cost Anomaly ===
router.get('/api/finops/anomaly/detections', (req, res) => {
  let filtered = [...anomalies]; if (req.query.severity) filtered = filtered.filter(a => a.severity === req.query.severity); res.json(filtered);
});
router.get('/api/finops/anomaly/summary', (req, res) => {
  res.json({ total: anomalies.length, critical: anomalies.filter(a => a.severity === 'critical').length, high: anomalies.filter(a => a.severity === 'high').length, medium: anomalies.filter(a => a.severity === 'medium').length, low: anomalies.filter(a => a.severity === 'low').length, estimated_excess_spend: anomalies.reduce((s, a) => s + (a.excess_amount || 0), 0) });
});
router.post('/api/finops/anomaly/detections/:id/investigate', (req, res) => {
  const a = anomalies.find(x => x.id === req.params.id); if (!a) return res.status(404).json({ error: 'Not found' });
  a.status = 'investigating'; res.json({ ...a, investigation: { root_cause: 'Unexpected spike in EC2 m5.2xlarge usage', severity: a.severity, recommended_action: 'Review recent deployments and rollback if necessary' } });
});
router.post('/api/finops/anomaly/detections/:id/resolve', (req, res) => {
  const a = anomalies.find(x => x.id === req.params.id); if (!a) return res.status(404).json({ error: 'Not found' });
  a.status = 'resolved'; a.resolved_at = new Date().toISOString(); res.json(a);
});
router.get('/api/finops/anomaly/profiles', (req, res) => res.json(profiles));
router.post('/api/finops/anomaly/profiles', (req, res) => {
  const p = { id: `profile-${Date.now()}`, ...req.body, created_at: new Date().toISOString() }; profiles.push(p); res.json(p);
});
router.post('/api/finops/anomaly/ingest', (req, res) => {
  const { service, amount, region } = req.body; const a = { id: `anom-${Date.now()}`, service, amount, region, detected_at: new Date().toISOString(), severity: amount > 10000 ? 'critical' : amount > 5000 ? 'high' : 'medium', status: 'open', excess_amount: amount * 0.3 }; anomalies.push(a); res.json(a);
});

// === Budget & Forecast Engine ===
router.get('/api/finops/budget', (req, res) => res.json(budgets));
router.post('/api/finops/budget', (req, res) => {
  const b = { id: `budget-${Date.now()}`, ...req.body, spent: 0, status: 'active', created_at: new Date().toISOString() }; budgets.push(b); res.json(b);
});
router.get('/api/finops/budget/:id', (req, res) => {
  const b = budgets.find(x => x.id === req.params.id); if (!b) return res.status(404).json({ error: 'Not found' }); res.json(b);
});
router.post('/api/finops/budget/:id/spend', (req, res) => {
  const b = budgets.find(x => x.id === req.params.id); if (!b) return res.status(404).json({ error: 'Not found' });
  b.spent = (b.spent || 0) + req.body.amount; res.json(b);
});
router.get('/api/finops/budget/:id/forecast', (req, res) => {
  const b = budgets.find(x => x.id === req.params.id); if (!b) return res.status(404).json({ error: 'Not found' });
  res.json({ budget_id: b.id, budget_name: b.name, total_budget: b.amount, spent: b.spent || 0, remaining: b.amount - (b.spent || 0), forecasted_spend: b.spent * 1.15, forecasted_remaining: b.amount - b.spent * 1.15, at_risk: (b.spent || 0) > b.amount * 0.8 });
});
router.post('/api/finops/budget/:id/scenario', (req, res) => {
  const b = budgets.find(x => x.id === req.params.id); if (!b) return res.status(404).json({ error: 'Not found' });
  res.json({ scenario: req.body.scenario, current_forecast: b.spent * 1.15, scenario_forecast: b.spent * 1.3, impact: b.spent * 0.15, recommendation: 'Consider reducing EC2 spend by 10%' });
});
router.get('/api/finops/budget/summary', (req, res) => {
  const total = budgets.reduce((s, b) => s + b.amount, 0);
  const totalSpent = budgets.reduce((s, b) => s + (b.spent || 0), 0);
  res.json({ total_budgets: budgets.length, total_budget_amount: total, total_spent: totalSpent, utilization_pct: total > 0 ? (totalSpent / total) * 100 : 0, at_risk: budgets.filter(b => (b.spent || 0) > b.amount * 0.8).length });
});
router.get('/api/finops/budget/:id/variance', (req, res) => {
  const b = budgets.find(x => x.id === req.params.id); if (!b) return res.status(404).json({ error: 'Not found' });
  res.json({ budget_id: b.id, budgeted: b.amount, actual: b.spent || 0, variance: (b.spent || 0) - b.amount, variance_pct: b.amount > 0 ? (((b.spent || 0) - b.amount) / b.amount) * 100 : 0, status: (b.spent || 0) > b.amount ? 'over_budget' : 'under_budget' });
});

// === Resource Right-Sizing ===
router.get('/api/finops/rightsizing/recommendations', (req, res) => res.json(rightsizingRecs));
router.post('/api/finops/rightsizing/recommendations', (req, res) => {
  const r = { id: `rs-${Date.now()}`, ...req.body, status: 'open', created_at: new Date().toISOString() }; rightsizingRecs.push(r); res.json(r);
});
router.get('/api/finops/rightsizing/summary', (req, res) => {
  res.json({ total: rightsizingRecs.length, open: rightsizingRecs.filter(r => r.status === 'open').length, approved: rightsizingRecs.filter(r => r.status === 'approved').length, implemented: rightsizingRecs.filter(r => r.status === 'implemented').length, total_potential_savings: rightsizingRecs.reduce((s, r) => s + (r.estimated_savings || 0), 0) });
});
router.post('/api/finops/rightsizing/recommendations/:id/approve', (req, res) => {
  const r = rightsizingRecs.find(x => x.id === req.params.id); if (!r) return res.status(404).json({ error: 'Not found' });
  r.status = 'approved'; res.json(r);
});
router.post('/api/finops/rightsizing/recommendations/:id/implement', (req, res) => {
  const r = rightsizingRecs.find(x => x.id === req.params.id); if (!r) return res.status(404).json({ error: 'Not found' });
  r.status = 'implemented'; r.implemented_at = new Date().toISOString(); res.json(r);
});
router.post('/api/finops/rightsizing/recommendations/:id/dismiss', (req, res) => {
  const r = rightsizingRecs.find(x => x.id === req.params.id); if (!r) return res.status(404).json({ error: 'Not found' });
  r.status = 'dismissed'; res.json(r);
});
router.post('/api/finops/rightsizing/resources', (req, res) => {
  const r = { id: `res-${Date.now()}`, ...req.body, registered_at: new Date().toISOString() }; resources.push(r); res.json(r);
});
router.post('/api/finops/rightsizing/resources/:id/analyze', (req, res) => {
  const r = resources.find(x => x.id === req.params.id); if (!r) return res.status(404).json({ error: 'Not found' });
  res.json({ resource_id: r.id, name: r.name, current_size: r.current_size, recommended_size: r.current_size + '-small', utilization_pct: 23, estimated_savings: r.monthly_cost * 0.4, recommendation: 'Downgrade to smaller instance type', confidence: 'high' });
});

// === Cloud Waste Detection ===
router.get('/api/finops/waste/findings', (req, res) => {
  let filtered = [...wasteFindings]; if (req.query.category) filtered = filtered.filter(w => w.category === req.query.category); if (req.query.severity) filtered = filtered.filter(w => w.severity === req.query.severity); res.json(filtered);
});
router.get('/api/finops/waste/summary', (req, res) => {
  res.json({ total: wasteFindings.length, total_waste: wasteFindings.reduce((s, w) => s + (w.estimated_waste || 0), 0), categories: [...new Set(wasteFindings.map(w => w.category))].reduce((o, c) => ({ ...o, [c]: wasteFindings.filter(w => w.category === c).length }), {}) });
});
router.post('/api/finops/waste/scan', (req, res) => {
  const results = [
    { id: `wf-${Date.now()}-1`, category: 'idle_resources', resource: 'i-0abcd1234', estimated_waste: 450, severity: 'high', status: 'open', description: 'EC2 instance idle for 14 days' },
    { id: `wf-${Date.now()}-2`, category: 'unattached_storage', resource: 'vol-0efgh5678', estimated_waste: 120, severity: 'medium', status: 'open', description: 'Unattached EBS volume 50GB' },
    { id: `wf-${Date.now()}-3`, category: 'over_provisioned', resource: 'rds-0ijkl9012', estimated_waste: 280, severity: 'high', status: 'open', description: 'RDS instance over-provisioned 2x' },
  ];
  wasteFindings.push(...results); res.json({ scanned: true, findings_count: results.length, total_estimated_waste: results.reduce((s, w) => s + w.estimated_waste, 0), results });
});
router.post('/api/finops/waste/findings/:id/approve', (req, res) => {
  const w = wasteFindings.find(x => x.id === req.params.id); if (!w) return res.status(404).json({ error: 'Not found' });
  w.status = 'approved'; res.json(w);
});
router.post('/api/finops/waste/findings/:id/cleanup', (req, res) => {
  const w = wasteFindings.find(x => x.id === req.params.id); if (!w) return res.status(404).json({ error: 'Not found' });
  w.status = 'cleaned_up'; w.cleaned_at = new Date().toISOString(); res.json(w);
});
router.post('/api/finops/waste/findings/:id/dismiss', (req, res) => {
  const w = wasteFindings.find(x => x.id === req.params.id); if (!w) return res.status(404).json({ error: 'Not found' });
  w.status = 'dismissed'; res.json(w);
});

// === Carbon-Aware Cost Optimization ===
router.get('/api/finops/carbon/recommendations', (req, res) => res.json(carbonRecs));
router.get('/api/finops/carbon/assets', (req, res) => res.json(carbonAssets));
router.post('/api/finops/carbon/assets', (req, res) => {
  const a = { id: `ca-${Date.now()}`, ...req.body, registered_at: new Date().toISOString() }; carbonAssets.push(a); res.json(a);
});
router.get('/api/finops/carbon/sustainability-budget', (req, res) => {
  res.json({ total_carbon_footprint: carbonAssets.reduce((s, a) => s + (a.kwh || 0), 0) * 0.0007, annual_target: 50000, current_ytd: 28500, budget_remaining: 21500, offset_purchased: 12000, recommendations: [ 'Migrate 30% of compute to regions with lower carbon intensity', 'Schedule batch jobs during low-carbon hours', 'Increase spot instance usage for non-critical workloads' ] });
});
router.get('/api/finops/carbon/assets/:id/footprint', (req, res) => {
  const a = carbonAssets.find(x => x.id === req.params.id); if (!a) return res.status(404).json({ error: 'Not found' });
  res.json({ asset_id: a.id, name: a.name, provider: a.provider, region: a.region, estimated_kwh_monthly: a.kwh || (a.monthly_cost * 10), carbon_intensity: 0.00042, monthly_tons_co2: (a.kwh || a.monthly_cost * 10) * 0.00042, annual_tons_co2: (a.kwh || a.monthly_cost * 10) * 0.00042 * 12 });
});
router.get('/api/finops/carbon/assets/:id/tradeoff', (req, res) => {
  const a = carbonAssets.find(x => x.id === req.params.id); if (!a) return res.status(404).json({ error: 'Not found' });
  res.json({ asset_id: a.id, name: a.name, current_cost: a.monthly_cost, current_carbon: (a.kwh || a.monthly_cost * 10) * 0.00042, options: [ { name: 'Move to us-west-2', cost: a.monthly_cost * 0.95, carbon: (a.kwh || a.monthly_cost * 10) * 0.00042 * 0.7, savings: a.monthly_cost * 0.05 }, { name: 'Move to eu-west-1', cost: a.monthly_cost * 1.1, carbon: (a.kwh || a.monthly_cost * 10) * 0.00042 * 0.5, savings: -a.monthly_cost * 0.1 } ] });
});
router.get('/api/finops/carbon/intensity/:region', (req, res) => {
  const intensities = { 'us-east-1': 0.00042, 'us-west-1': 0.00035, 'us-west-2': 0.00030, 'eu-west-1': 0.00025, 'eu-central-1': 0.00032, 'ap-southeast-1': 0.00055, 'ap-northeast-1': 0.00048 };
  res.json({ region: req.params.region, carbon_intensity_kg_per_kwh: intensities[req.params.region] || 0.00040, grid_mix: { renewable_pct: 35, natural_gas_pct: 40, coal_pct: 15, nuclear_pct: 10 }, trend: 'decreasing' });
});

// === Multi-Cloud Discount Arbitrage ===
router.get('/api/finops/arbitrage/workloads', (req, res) => res.json(workloads));
router.post('/api/finops/arbitrage/workloads', (req, res) => {
  const w = { id: `wl-${Date.now()}`, ...req.body, status: 'active', created_at: new Date().toISOString() }; workloads.push(w); res.json(w);
});
router.get('/api/finops/arbitrage/comparisons', (req, res) => res.json(comparisons));
router.post('/api/finops/arbitrage/comparisons', (req, res) => {
  const c = { id: `comp-${Date.now()}`, ...req.body, created_at: new Date().toISOString() }; comparisons.push(c); res.json(c);
});
router.get('/api/finops/arbitrage/savings', (req, res) => {
  res.json({ total_comparisons: comparisons.length, total_potential_savings: comparisons.reduce((s, c) => s + (c.savings || 0), 0), best_provider: 'aws', workloads_analyzed: workloads.length, average_savings_pct: 23 });
});
router.get('/api/finops/arbitrage/workloads/:id/compare', (req, res) => {
  const w = workloads.find(x => x.id === req.params.id); if (!w) return res.status(404).json({ error: 'Not found' });
  res.json({ workload_id: w.id, name: w.name, current_provider: w.current_provider, current_cost: w.current_cost, alternatives: [{ provider: 'aws', estimated_cost: w.current_cost * 0.85, savings: w.current_cost * 0.15 }, { provider: 'azure', estimated_cost: w.current_cost * 0.90, savings: w.current_cost * 0.10 }, { provider: 'gcp', estimated_cost: w.current_cost * 0.82, savings: w.current_cost * 0.18 }], recommendation: 'gcp' });
});
router.post('/api/finops/arbitrage/workloads/:id/migrate', (req, res) => {
  const w = workloads.find(x => x.id === req.params.id); if (!w) return res.status(404).json({ error: 'Not found' });
  res.json({ workload_id: w.id, name: w.name, source_provider: w.current_provider, target_provider: 'gcp', estimated_savings: w.current_cost * 0.18, migration_steps: ['Provision target infrastructure', 'Configure networking', 'Migrate data', 'Switch traffic', 'Decommission source'], estimated_duration_hours: 8, status: 'migration_planned' });
});

// === FinOps Reporting & Compliance ===
router.get('/api/finops/reports', (req, res) => res.json(reports));
router.post('/api/finops/reports/generate', (req, res) => {
  const r = { id: `report-${Date.now()}`, ...req.body, status: 'generated', generated_at: new Date().toISOString(), download_url: `/api/finops/reports/${Date.now()}/download` }; reports.push(r); res.json(r);
});
router.get('/api/finops/reports/summary', (req, res) => {
  res.json({ total_reports: reports.length, report_types: [...new Set(reports.map(r => r.report_type))], recent_reports: reports.slice(-5) });
});
router.get('/api/finops/reports/:id', (req, res) => {
  const r = reports.find(x => x.id === req.params.id); if (!r) return res.status(404).json({ error: 'Not found' }); res.json(r);
});
router.get('/api/finops/reports/dashboard/:type', (req, res) => {
  res.json({ dashboard_type: req.params.type, generated_at: new Date().toISOString(), kpis: { total_spend: 245000, budget_variance: -3.2, savings_achieved: 18500, anomaly_count: 7, coverage_pct: 72 }, charts: { spend_by_service: { EC2: 82000, S3: 34000, RDS: 28000, Lambda: 15000, Other: 86000 }, savings_breakdown: { commitment_discounts: 12000, spot_usage: 4500, rightsizing: 2000 } } });
});
router.get('/api/finops/reports/allocations', (req, res) => {
  let filtered = [...allocations]; if (req.query.team) filtered = filtered.filter(a => a.team === req.query.team); res.json(filtered);
});
router.post('/api/finops/reports/allocations', (req, res) => {
  const a = { id: `alloc-${Date.now()}`, ...req.body, created_at: new Date().toISOString() }; allocations.push(a); res.json(a);
});

// === Additional FinOps Endpoints ===
router.post('/api/finops/commitment/renew', (req, res) => {
  res.json({ success: true, renewal_id: `renew-${Date.now()}`, term: req.body.term, status: 'renewed' });
});
router.get('/api/finops/commitment/history', (req, res) => {
  const days = parseInt(req.query.days) || 30;
  res.json({ history_count: 12, period_days: days, entries: Array.from({length: 6}, (_, i) => ({ date: new Date(Date.now() - i * 86400000 * 5).toISOString().split('T')[0], action: ['created', 'renewed', 'expired'][i % 3], service: 'EC2', amount: 5200 })) });
});
router.get('/api/finops/commitment/roi', (req, res) => {
  const upfront = parseFloat(req.query.upfront) || 10000;
  const monthly = parseFloat(req.query.monthly_savings) || 1200;
  const term = parseInt(req.query.term) || 12;
  const totalSavings = monthly * term;
  const roi = ((totalSavings - upfront) / upfront) * 100;
  res.json({ upfront, monthly_savings: monthly, term_months: term, total_savings: totalSavings, roi_pct: roi, payback_months: upfront / monthly, recommendation: roi > 50 ? 'Recommended' : 'Evaluate further' });
});
router.get('/api/finops/anomaly/severity-breakdown', (req, res) => {
  res.json({ critical: 3, high: 5, medium: 8, low: 8, total: 24, estimated_excess: 12450 });
});
router.post('/api/finops/anomaly/respond', (req, res) => {
  res.json({ success: true, anomaly_id: req.body.anomaly_id, action: req.body.action, status: 'ticket_created', assignee: 'FinOps team' });
});
router.post('/api/finops/anomaly/alert-config', (req, res) => {
  res.json({ success: true, channel: req.body.channel || 'discord', min_severity: req.body.min_severity || 'medium', updated: true });
});
router.post('/api/finops/budget/alert', (req, res) => {
  const { budget_id, threshold_pct } = req.body;
  res.json({ success: true, budget_id, threshold_pct, alert_id: `alert-${Date.now()}`, enabled: true });
});
router.get('/api/finops/budget/health', (req, res) => {
  const total = budgets.length;
  const atRisk = budgets.filter(b => (b.spent || 0) > b.amount * 0.8).length;
  const healthy = total - atRisk;
  res.json({ total_budgets: total, healthy, at_risk: atRisk, health_score: total > 0 ? Math.round((healthy / total) * 100) : 100 });
});
router.post('/api/finops/waste/auto-cleanup', (req, res) => {
  const category = req.body.category || 'all';
  const targets = wasteFindings.filter(w => w.status === 'approved' && (category === 'all' || w.category === category));
  targets.forEach(w => { w.status = 'cleaned_up'; w.cleaned_at = new Date().toISOString(); });
  res.json({ success: true, category, cleaned: targets.length, estimated_savings: targets.reduce((s, w) => s + (w.estimated_waste || 0), 0) });
});
router.get('/api/finops/waste/trend', (req, res) => {
  res.json({ months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], values: [3200, 2800, 2500, 2100, 1900, 1847], reduction_pct: 42.3 });
});

module.exports = router;
