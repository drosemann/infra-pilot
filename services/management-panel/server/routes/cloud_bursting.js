const express = require('express');
const router = express.Router();

const workloads = [];
const bursts = [];

router.get('/api/burst/workloads', (req, res) => res.json(workloads));
router.post('/api/burst/workloads', (req, res) => {
  const { name, target_capacity, priority } = req.body;
  const wl = { workload_id: `wl-${Date.now()}`, name, target_capacity: target_capacity || 100, current_capacity: 0, priority: priority || 5, state: 'idle', created_at: new Date().toISOString() };
  workloads.push(wl); res.json(wl);
});
router.get('/api/burst/check', (req, res) => {
  const total = workloads.reduce((s, w) => s + w.target_capacity, 0);
  res.json({ burst_needed: total > 80, utilization: Math.min(total, 100), on_prem_capacity: 100, cloud_capacity: 500 });
});
router.post('/api/burst/start', (req, res) => {
  const burst = { burst_id: `burst-${Date.now()}`, state: 'bursting', started_at: new Date().toISOString(), workloads: workloads.map(w => w.workload_id), cloud_resources: 10 };
  bursts.push(burst); res.json(burst);
});
router.post('/api/burst/:id/drain', (req, res) => {
  const b = bursts.find(x => x.burst_id === req.params.id);
  if (!b) return res.status(404).json({ error: 'Not found' });
  b.state = 'draining'; b.completed_at = new Date().toISOString();
  res.json({ status: 'completed' });
});
router.get('/api/burst/active', (req, res) => res.json(bursts));
router.get('/api/burst/:id', (req, res) => {
  const b = bursts.find(x => x.burst_id === req.params.id);
  if (!b) return res.status(404).json({ error: 'Not found' });
  res.json(b);
});

module.exports = router;
