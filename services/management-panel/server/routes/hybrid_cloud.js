const express = require('express');
const router = express.Router();

// Hybrid Cloud API Routes

router.get('/api/hybrid_cloud/resources', (req, res) => {
  res.json(global.hybrid_cloud_resources_data || []);
});

router.post('/api/hybrid_cloud/resources', (req, res) => {
  const item = { id: 'resources-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_resources_data) global.hybrid_cloud_resources_data = [];
  global.hybrid_cloud_resources_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/resources/:id', (req, res) => {
  const arr = global.hybrid_cloud_resources_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/resources/:id', (req, res) => {
  const arr = global.hybrid_cloud_resources_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/bursting', (req, res) => {
  res.json(global.hybrid_cloud_bursting_data || []);
});

router.post('/api/hybrid_cloud/bursting', (req, res) => {
  const item = { id: 'bursting-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_bursting_data) global.hybrid_cloud_bursting_data = [];
  global.hybrid_cloud_bursting_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/bursting/:id', (req, res) => {
  const arr = global.hybrid_cloud_bursting_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/bursting/:id', (req, res) => {
  const arr = global.hybrid_cloud_bursting_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/arbitrage', (req, res) => {
  res.json(global.hybrid_cloud_arbitrage_data || []);
});

router.post('/api/hybrid_cloud/arbitrage', (req, res) => {
  const item = { id: 'arbitrage-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_arbitrage_data) global.hybrid_cloud_arbitrage_data = [];
  global.hybrid_cloud_arbitrage_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/arbitrage/:id', (req, res) => {
  const arr = global.hybrid_cloud_arbitrage_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/arbitrage/:id', (req, res) => {
  const arr = global.hybrid_cloud_arbitrage_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/cost-control', (req, res) => {
  res.json(global.hybrid_cloud_cost_control_data || []);
});

router.post('/api/hybrid_cloud/cost-control', (req, res) => {
  const item = { id: 'cost-control-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_cost_control_data) global.hybrid_cloud_cost_control_data = [];
  global.hybrid_cloud_cost_control_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/cost-control/:id', (req, res) => {
  const arr = global.hybrid_cloud_cost_control_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/cost-control/:id', (req, res) => {
  const arr = global.hybrid_cloud_cost_control_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/networking', (req, res) => {
  res.json(global.hybrid_cloud_networking_data || []);
});

router.post('/api/hybrid_cloud/networking', (req, res) => {
  const item = { id: 'networking-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_networking_data) global.hybrid_cloud_networking_data = [];
  global.hybrid_cloud_networking_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/networking/:id', (req, res) => {
  const arr = global.hybrid_cloud_networking_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/networking/:id', (req, res) => {
  const arr = global.hybrid_cloud_networking_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/migration', (req, res) => {
  res.json(global.hybrid_cloud_migration_data || []);
});

router.post('/api/hybrid_cloud/migration', (req, res) => {
  const item = { id: 'migration-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_migration_data) global.hybrid_cloud_migration_data = [];
  global.hybrid_cloud_migration_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/migration/:id', (req, res) => {
  const arr = global.hybrid_cloud_migration_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/migration/:id', (req, res) => {
  const arr = global.hybrid_cloud_migration_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/iam', (req, res) => {
  res.json(global.hybrid_cloud_iam_data || []);
});

router.post('/api/hybrid_cloud/iam', (req, res) => {
  const item = { id: 'iam-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_iam_data) global.hybrid_cloud_iam_data = [];
  global.hybrid_cloud_iam_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/iam/:id', (req, res) => {
  const arr = global.hybrid_cloud_iam_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/iam/:id', (req, res) => {
  const arr = global.hybrid_cloud_iam_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/backup', (req, res) => {
  res.json(global.hybrid_cloud_backup_data || []);
});

router.post('/api/hybrid_cloud/backup', (req, res) => {
  const item = { id: 'backup-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_backup_data) global.hybrid_cloud_backup_data = [];
  global.hybrid_cloud_backup_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/backup/:id', (req, res) => {
  const arr = global.hybrid_cloud_backup_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/backup/:id', (req, res) => {
  const arr = global.hybrid_cloud_backup_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/registry', (req, res) => {
  res.json(global.hybrid_cloud_registry_data || []);
});

router.post('/api/hybrid_cloud/registry', (req, res) => {
  const item = { id: 'registry-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_registry_data) global.hybrid_cloud_registry_data = [];
  global.hybrid_cloud_registry_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/registry/:id', (req, res) => {
  const arr = global.hybrid_cloud_registry_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/registry/:id', (req, res) => {
  const arr = global.hybrid_cloud_registry_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/hybrid_cloud/cost-allocation', (req, res) => {
  res.json(global.hybrid_cloud_cost_allocation_data || []);
});

router.post('/api/hybrid_cloud/cost-allocation', (req, res) => {
  const item = { id: 'cost-allocation-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.hybrid_cloud_cost_allocation_data) global.hybrid_cloud_cost_allocation_data = [];
  global.hybrid_cloud_cost_allocation_data.push(item);
  res.json(item);
});

router.get('/api/hybrid_cloud/cost-allocation/:id', (req, res) => {
  const arr = global.hybrid_cloud_cost_allocation_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/hybrid_cloud/cost-allocation/:id', (req, res) => {
  const arr = global.hybrid_cloud_cost_allocation_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
