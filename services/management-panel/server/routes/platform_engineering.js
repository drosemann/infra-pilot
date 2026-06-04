const express = require('express');
const router = express.Router();

// Platform Engineering API Routes

router.get('/api/platform_engineering/developer-portal', (req, res) => {
  res.json(global.platform_engineering_developer_portal_data || []);
});

router.post('/api/platform_engineering/developer-portal', (req, res) => {
  const item = { id: 'developer-portal-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_developer_portal_data) global.platform_engineering_developer_portal_data = [];
  global.platform_engineering_developer_portal_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/developer-portal/:id', (req, res) => {
  const arr = global.platform_engineering_developer_portal_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/developer-portal/:id', (req, res) => {
  const arr = global.platform_engineering_developer_portal_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/scaffold', (req, res) => {
  res.json(global.platform_engineering_scaffold_data || []);
});

router.post('/api/platform_engineering/scaffold', (req, res) => {
  const item = { id: 'scaffold-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_scaffold_data) global.platform_engineering_scaffold_data = [];
  global.platform_engineering_scaffold_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/scaffold/:id', (req, res) => {
  const arr = global.platform_engineering_scaffold_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/scaffold/:id', (req, res) => {
  const arr = global.platform_engineering_scaffold_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/service-catalog', (req, res) => {
  res.json(global.platform_engineering_service_catalog_data || []);
});

router.post('/api/platform_engineering/service-catalog', (req, res) => {
  const item = { id: 'service-catalog-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_service_catalog_data) global.platform_engineering_service_catalog_data = [];
  global.platform_engineering_service_catalog_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/service-catalog/:id', (req, res) => {
  const arr = global.platform_engineering_service_catalog_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/service-catalog/:id', (req, res) => {
  const arr = global.platform_engineering_service_catalog_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/scorecards', (req, res) => {
  res.json(global.platform_engineering_scorecards_data || []);
});

router.post('/api/platform_engineering/scorecards', (req, res) => {
  const item = { id: 'scorecards-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_scorecards_data) global.platform_engineering_scorecards_data = [];
  global.platform_engineering_scorecards_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/scorecards/:id', (req, res) => {
  const arr = global.platform_engineering_scorecards_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/scorecards/:id', (req, res) => {
  const arr = global.platform_engineering_scorecards_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/template-registry', (req, res) => {
  res.json(global.platform_engineering_template_registry_data || []);
});

router.post('/api/platform_engineering/template-registry', (req, res) => {
  const item = { id: 'template-registry-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_template_registry_data) global.platform_engineering_template_registry_data = [];
  global.platform_engineering_template_registry_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/template-registry/:id', (req, res) => {
  const arr = global.platform_engineering_template_registry_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/template-registry/:id', (req, res) => {
  const arr = global.platform_engineering_template_registry_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/tech-debt', (req, res) => {
  res.json(global.platform_engineering_tech_debt_data || []);
});

router.post('/api/platform_engineering/tech-debt', (req, res) => {
  const item = { id: 'tech-debt-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_tech_debt_data) global.platform_engineering_tech_debt_data = [];
  global.platform_engineering_tech_debt_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/tech-debt/:id', (req, res) => {
  const arr = global.platform_engineering_tech_debt_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/tech-debt/:id', (req, res) => {
  const arr = global.platform_engineering_tech_debt_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/environments', (req, res) => {
  res.json(global.platform_engineering_environments_data || []);
});

router.post('/api/platform_engineering/environments', (req, res) => {
  const item = { id: 'environments-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_environments_data) global.platform_engineering_environments_data = [];
  global.platform_engineering_environments_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/environments/:id', (req, res) => {
  const arr = global.platform_engineering_environments_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/environments/:id', (req, res) => {
  const arr = global.platform_engineering_environments_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/api-catalog', (req, res) => {
  res.json(global.platform_engineering_api_catalog_data || []);
});

router.post('/api/platform_engineering/api-catalog', (req, res) => {
  const item = { id: 'api-catalog-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_api_catalog_data) global.platform_engineering_api_catalog_data = [];
  global.platform_engineering_api_catalog_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/api-catalog/:id', (req, res) => {
  const arr = global.platform_engineering_api_catalog_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/api-catalog/:id', (req, res) => {
  const arr = global.platform_engineering_api_catalog_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/doc-generator', (req, res) => {
  res.json(global.platform_engineering_doc_generator_data || []);
});

router.post('/api/platform_engineering/doc-generator', (req, res) => {
  const item = { id: 'doc-generator-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_doc_generator_data) global.platform_engineering_doc_generator_data = [];
  global.platform_engineering_doc_generator_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/doc-generator/:id', (req, res) => {
  const arr = global.platform_engineering_doc_generator_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/doc-generator/:id', (req, res) => {
  const arr = global.platform_engineering_doc_generator_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/platform_engineering/developer-pulse', (req, res) => {
  res.json(global.platform_engineering_developer_pulse_data || []);
});

router.post('/api/platform_engineering/developer-pulse', (req, res) => {
  const item = { id: 'developer-pulse-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.platform_engineering_developer_pulse_data) global.platform_engineering_developer_pulse_data = [];
  global.platform_engineering_developer_pulse_data.push(item);
  res.json(item);
});

router.get('/api/platform_engineering/developer-pulse/:id', (req, res) => {
  const arr = global.platform_engineering_developer_pulse_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/platform_engineering/developer-pulse/:id', (req, res) => {
  const arr = global.platform_engineering_developer_pulse_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
