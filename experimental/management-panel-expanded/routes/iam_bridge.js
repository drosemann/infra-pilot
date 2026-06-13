const express = require('express');
const router = express.Router();

const mappings = [];
const policies = [];

router.get('/api/iam/mappings', (req, res) => res.json(mappings));
router.post('/api/iam/mappings', (req, res) => {
  const { source_role, source_provider, target_role, target_provider } = req.body;
  const m = { id: `map-${Date.now()}`, source_role, source_provider: source_provider || 'aws', target_role, target_provider: target_provider || 'azure', active: true, created_at: new Date().toISOString() };
  mappings.push(m); res.json(m);
});
router.post('/api/iam/sync', (req, res) => {
  mappings.forEach(m => { m.last_synced = new Date().toISOString(); });
  res.json({ status: 'synced', count: mappings.length });
});
router.get('/api/iam/roles', (req, res) => {
  res.json([
    { name: 'Admin', provider: 'aws', policies: 3 },
    { name: 'ReadOnly', provider: 'aws', policies: 1 },
    { name: 'Contributor', provider: 'azure', policies: 2 },
  ]);
});
router.get('/api/iam/policies', (req, res) => res.json(policies));
router.post('/api/iam/policies', (req, res) => {
  const { name, statements } = req.body;
  const p = { id: `pol-${Date.now()}`, name, statements: statements || [], version: '2012-10-17' };
  policies.push(p); res.json(p);
});

module.exports = router;
