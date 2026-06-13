const express = require('express');
const router = express.Router();

const images = [];
const rules = [];

router.get('/api/registry/images', (req, res) => res.json(images));
router.post('/api/registry/images', (req, res) => {
  const { name, tag, registry, repository } = req.body;
  const img = { id: `img-${Date.now()}`, name, tag: tag || 'latest', registry: registry || 'docker_hub', repository, size_bytes: 0, vulnerability_count: 0, created_at: new Date().toISOString() };
  images.push(img); res.json(img);
});
router.post('/api/registry/images/:id/scan', (req, res) => {
  const img = images.find(x => x.id === req.params.id);
  if (!img) return res.status(404).json({ error: 'Not found' });
  img.vulnerability_count = Math.floor(Math.random() * 10);
  res.json({ image_id: img.id, vulnerability_count: img.vulnerability_count, max_severity: img.vulnerability_count > 5 ? 'HIGH' : 'LOW' });
});
router.post('/api/registry/images/:id/replicate', (req, res) => {
  const img = images.find(x => x.id === req.params.id);
  if (!img) return res.status(404).json({ error: 'Not found' });
  res.json({ status: 'replicating', image: `${img.name}:${img.tag}`, targets: ['aws_ecr', 'azure_acr', 'gcp_gcr'] });
});
router.get('/api/registry/rules', (req, res) => res.json(rules));
router.post('/api/registry/rules', (req, res) => {
  const { source_registry, target_registries, image_pattern } = req.body;
  const rule = { id: `rule-${Date.now()}`, source_registry, target_registries: target_registries || [], image_pattern: image_pattern || '*', created_at: new Date().toISOString() };
  rules.push(rule); res.json(rule);
});
router.get('/api/registry/registries', (req, res) => {
  res.json(['aws_ecr', 'azure_acr', 'gcp_gcr', 'docker_hub', 'ghcr', 'gitlab'].map(r => ({ name: r, connected: true })));
});

module.exports = router;
