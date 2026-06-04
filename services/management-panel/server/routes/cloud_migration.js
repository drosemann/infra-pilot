const express = require('express');
const router = express.Router();

const workloads = [];
const waves = [];

router.get('/api/migration/workloads', (req, res) => res.json(workloads));
router.post('/api/migration/discover', (req, res) => {
  const { name, hostname, os_type, vcpu, memory_gb } = req.body;
  const wl = { id: `wl-${Date.now()}`, name, hostname, os_type: os_type || 'linux', vcpu: vcpu || 2, memory_gb: memory_gb || 4, state: 'discovered', discovered_at: new Date().toISOString() };
  workloads.push(wl); res.json(wl);
});
router.get('/api/migration/workloads/:id/assess', (req, res) => {
  const wl = workloads.find(x => x.id === req.params.id);
  if (!wl) return res.status(404).json({ error: 'Not found' });
  wl.state = 'assessed';
  res.json({ workload_id: wl.id, compatibility: true, recommended_instance: 't3.large', estimated_monthly_cost: 45.50 });
});
router.post('/api/migration/waves', (req, res) => {
  const { name, workload_ids, target_provider } = req.body;
  const wave = { id: `wave-${Date.now()}`, name, workload_ids: workload_ids || [], target_provider: target_provider || 'aws', state: 'planned', created_at: new Date().toISOString() };
  waves.push(wave); res.json(wave);
});
router.get('/api/migration/waves', (req, res) => res.json(waves));
router.post('/api/migration/waves/:id/execute', (req, res) => {
  const wave = waves.find(x => x.id === req.params.id);
  if (!wave) return res.status(404).json({ error: 'Not found' });
  wave.state = 'completed'; wave.completed_at = new Date().toISOString();
  res.json({ status: 'completed', wave_id: wave.id });
});
router.post('/api/migration/waves/:id/rollback', (req, res) => {
  const wave = waves.find(x => x.id === req.params.id);
  if (!wave) return res.status(404).json({ error: 'Not found' });
  wave.state = 'rolled_back';
  res.json({ status: 'rolled_back' });
});

module.exports = router;
