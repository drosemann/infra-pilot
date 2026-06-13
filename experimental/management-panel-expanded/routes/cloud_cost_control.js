const express = require('express');
const router = express.Router();

const costRecords = [];
const budgets = [];
const anomalies = [];

router.get('/api/cost/summary', (req, res) => {
  const total = costRecords.reduce((s, c) => s + c.amount, 0);
  const by_provider = {};
  costRecords.forEach(c => { by_provider[c.provider] = (by_provider[c.provider] || 0) + c.amount; });
  res.json({ total, by_provider, record_count: costRecords.length });
});
router.post('/api/cost/record', (req, res) => {
  const { provider, amount, service } = req.body;
  const rec = { id: `cost-${Date.now()}`, provider, amount, service: service || 'compute', recorded_at: new Date().toISOString() };
  costRecords.push(rec); res.json(rec);
});
router.get('/api/cost/budgets', (req, res) => res.json(budgets));
router.post('/api/cost/budgets', (req, res) => {
  const { name, amount } = req.body;
  const b = { id: `budget-${Date.now()}`, name, amount: amount || 1000, spent: 0, period: 'monthly', created_at: new Date().toISOString() };
  budgets.push(b); res.json(b);
});
router.get('/api/cost/anomalies', (req, res) => res.json(anomalies));
router.get('/api/cost/forecast', (req, res) => {
  const { days = 30 } = req.query;
  const avg = costRecords.length > 0 ? costRecords.reduce((s, c) => s + c.amount, 0) / costRecords.length : 0;
  res.json({ forecast: avg * parseInt(days), daily_average: avg, days_analyzed: costRecords.length });
});

module.exports = router;
