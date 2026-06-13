const express = require('express');
const router = express.Router();

const cloudResources = [];
const providers = ['aws', 'azure', 'gcp', 'hetzner', 'ovh', 'digitalocean'];

router.get('/api/cloud/resources', (req, res) => {
  res.json(cloudResources);
});

router.post('/api/cloud/resources', (req, res) => {
  const { provider, type, name, region, count } = req.body;
  const resource = { id: `${provider}-${type}-${Date.now()}`, provider, type, name, region, count: count || 1, status: 'provisioning', cost_per_hour: 0.05, created_at: new Date().toISOString() };
  cloudResources.push(resource);
  res.json(resource);
});

router.get('/api/cloud/resources/:id', (req, res) => {
  const r = cloudResources.find(x => x.id === req.params.id);
  if (!r) return res.status(404).json({ error: 'Not found' });
  res.json(r);
});

router.delete('/api/cloud/resources/:id', (req, res) => {
  const idx = cloudResources.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  cloudResources.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/cloud/providers', (req, res) => {
  res.json(providers.map(p => ({ id: p, name: p.toUpperCase(), connected: true })));
});

router.get('/api/cloud/scores', (req, res) => {
  const { vcpu = 2, memory = 4 } = req.query;
  res.json([
    { provider: 'aws', overall: 92, cost_score: 85, latency_score: 95, availability_score: 99 },
    { provider: 'azure', overall: 88, cost_score: 80, latency_score: 90, availability_score: 99 },
    { provider: 'gcp', overall: 85, cost_score: 88, latency_score: 85, availability_score: 99 },
    { provider: 'hetzner', overall: 72, cost_score: 95, latency_score: 60, availability_score: 97 },
    { provider: 'ovh', overall: 65, cost_score: 90, latency_score: 55, availability_score: 95 },
    { provider: 'digitalocean', overall: 78, cost_score: 82, latency_score: 75, availability_score: 98 },
  ]);
});

module.exports = router;
