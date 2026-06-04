const express = require('express');
const router = express.Router();

const opportunities = [];
const migrations = [];

router.get('/api/arbitrage/opportunities', (req, res) => res.json(opportunities));
router.get('/api/arbitrage/compare', (req, res) => {
  const { vcpu = 2, memory = 4 } = req.query;
  res.json([
    { provider: 'aws', spot_price: 0.012, on_demand: 0.05, savings: 76 },
    { provider: 'azure', spot_price: 0.014, on_demand: 0.06, savings: 77 },
    { provider: 'gcp', spot_price: 0.008, on_demand: 0.04, savings: 80 },
    { provider: 'hetzner', spot_price: 0.006, on_demand: 0.02, savings: 70 },
  ]);
});
router.post('/api/arbitrage/migrate/:opportunityId', (req, res) => {
  const opp = opportunities.find(x => x.id === req.params.opportunityId);
  if (!opp) return res.status(404).json({ error: 'Not found' });
  const mig = { migration_id: `migr-${Date.now()}`, opportunity_id: opp.id, source_provider: opp.source_provider, target_provider: opp.target_provider, state: 'in_progress', started_at: new Date().toISOString() };
  migrations.push(mig); res.json(mig);
});
router.get('/api/arbitrage/migrations', (req, res) => res.json(migrations));
router.get('/api/arbitrage/savings', (req, res) => {
  const total = opportunities.filter(o => o.state === 'completed').reduce((s, o) => s + o.savings_per_hour, 0);
  res.json({ total_savings_per_hour: total, total_savings_per_month: total * 24 * 30 });
});

module.exports = router;
