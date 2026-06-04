const express = require('express');
const router = express.Router();

// Data Platform API Routes

router.get('/api/data_platform/lakehouse', (req, res) => {
  res.json(global.data_platform_lakehouse_data || []);
});

router.post('/api/data_platform/lakehouse', (req, res) => {
  const item = { id: 'lakehouse-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_lakehouse_data) global.data_platform_lakehouse_data = [];
  global.data_platform_lakehouse_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/lakehouse/:id', (req, res) => {
  const arr = global.data_platform_lakehouse_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/lakehouse/:id', (req, res) => {
  const arr = global.data_platform_lakehouse_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/streaming', (req, res) => {
  res.json(global.data_platform_streaming_data || []);
});

router.post('/api/data_platform/streaming', (req, res) => {
  const item = { id: 'streaming-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_streaming_data) global.data_platform_streaming_data = [];
  global.data_platform_streaming_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/streaming/:id', (req, res) => {
  const arr = global.data_platform_streaming_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/streaming/:id', (req, res) => {
  const arr = global.data_platform_streaming_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/quality', (req, res) => {
  res.json(global.data_platform_quality_data || []);
});

router.post('/api/data_platform/quality', (req, res) => {
  const item = { id: 'quality-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_quality_data) global.data_platform_quality_data = [];
  global.data_platform_quality_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/quality/:id', (req, res) => {
  const arr = global.data_platform_quality_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/quality/:id', (req, res) => {
  const arr = global.data_platform_quality_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/analytics', (req, res) => {
  res.json(global.data_platform_analytics_data || []);
});

router.post('/api/data_platform/analytics', (req, res) => {
  const item = { id: 'analytics-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_analytics_data) global.data_platform_analytics_data = [];
  global.data_platform_analytics_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/analytics/:id', (req, res) => {
  const arr = global.data_platform_analytics_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/analytics/:id', (req, res) => {
  const arr = global.data_platform_analytics_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/catalog', (req, res) => {
  res.json(global.data_platform_catalog_data || []);
});

router.post('/api/data_platform/catalog', (req, res) => {
  const item = { id: 'catalog-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_catalog_data) global.data_platform_catalog_data = [];
  global.data_platform_catalog_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/catalog/:id', (req, res) => {
  const arr = global.data_platform_catalog_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/catalog/:id', (req, res) => {
  const arr = global.data_platform_catalog_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/data-masking', (req, res) => {
  res.json(global.data_platform_data_masking_data || []);
});

router.post('/api/data_platform/data-masking', (req, res) => {
  const item = { id: 'data-masking-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_data_masking_data) global.data_platform_data_masking_data = [];
  global.data_platform_data_masking_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/data-masking/:id', (req, res) => {
  const arr = global.data_platform_data_masking_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/data-masking/:id', (req, res) => {
  const arr = global.data_platform_data_masking_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/self-service', (req, res) => {
  res.json(global.data_platform_self_service_data || []);
});

router.post('/api/data_platform/self-service', (req, res) => {
  const item = { id: 'self-service-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_self_service_data) global.data_platform_self_service_data = [];
  global.data_platform_self_service_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/self-service/:id', (req, res) => {
  const arr = global.data_platform_self_service_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/self-service/:id', (req, res) => {
  const arr = global.data_platform_self_service_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/realtime', (req, res) => {
  res.json(global.data_platform_realtime_data || []);
});

router.post('/api/data_platform/realtime', (req, res) => {
  const item = { id: 'realtime-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_realtime_data) global.data_platform_realtime_data = [];
  global.data_platform_realtime_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/realtime/:id', (req, res) => {
  const arr = global.data_platform_realtime_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/realtime/:id', (req, res) => {
  const arr = global.data_platform_realtime_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/observability', (req, res) => {
  res.json(global.data_platform_observability_data || []);
});

router.post('/api/data_platform/observability', (req, res) => {
  const item = { id: 'observability-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_observability_data) global.data_platform_observability_data = [];
  global.data_platform_observability_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/observability/:id', (req, res) => {
  const arr = global.data_platform_observability_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/observability/:id', (req, res) => {
  const arr = global.data_platform_observability_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/data_platform/embedded-analytics', (req, res) => {
  res.json(global.data_platform_embedded_analytics_data || []);
});

router.post('/api/data_platform/embedded-analytics', (req, res) => {
  const item = { id: 'embedded-analytics-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.data_platform_embedded_analytics_data) global.data_platform_embedded_analytics_data = [];
  global.data_platform_embedded_analytics_data.push(item);
  res.json(item);
});

router.get('/api/data_platform/embedded-analytics/:id', (req, res) => {
  const arr = global.data_platform_embedded_analytics_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/data_platform/embedded-analytics/:id', (req, res) => {
  const arr = global.data_platform_embedded_analytics_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
