const express = require('express');
const router = express.Router();

const allocations = [];
const chargebacks = [];

router.get('/api/cost-allocation/allocations', (req, res) => res.json(allocations));
router.post('/api/cost-allocation/allocations', (req, res) => {
  const { name, amount, team, project, source } = req.body;
  const a = { id: `alloc-${Date.now()}`, name, amount: amount || 0, team: team || 'unallocated', project: project || 'unallocated', source: source || 'cloud', allocated: true, created_at: new Date().toISOString() };
  allocations.push(a); res.json(a);
});
router.get('/api/cost-allocation/summary', (req, res) => {
  const total = allocations.reduce((s, a) => s + a.amount, 0);
  const teams = [...new Set(allocations.map(a => a.team))];
  res.json({ total_allocated: total, active_teams: teams.length, total_allocations: allocations.length });
});
router.get('/api/cost-allocation/teams/:team', (req, res) => {
  const teamAllocs = allocations.filter(a => a.team === req.params.team);
  const total = teamAllocs.reduce((s, a) => s + a.amount, 0);
  res.json({ team: req.params.team, total_spend: total, allocation_count: teamAllocs.length });
});
router.get('/api/cost-allocation/chargebacks', (req, res) => res.json(chargebacks));
router.post('/api/cost-allocation/chargebacks', (req, res) => {
  const { team, project, amount, period } = req.body;
  const cb = { id: `cb-${Date.now()}`, team, project, amount: amount || 0, period: period || new Date().toISOString().slice(0, 7), created_at: new Date().toISOString(), invoiced: false };
  chargebacks.push(cb); res.json(cb);
});
router.get('/api/cost-allocation/tags', (req, res) => {
  res.json([
    { key: 'Environment', values: ['production', 'staging', 'development'] },
    { key: 'Team', values: ['platform', 'backend', 'frontend', 'sre'] },
    { key: 'Source', values: ['on-prem', 'edge', 'cloud'] },
  ]);
});

module.exports = router;
