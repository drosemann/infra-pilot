const express = require('express');
const router = express.Router();

// AIOps API Routes

router.get('/api/aiops/rca', (req, res) => {
  res.json(global.aiops_rca_data || []);
});

router.post('/api/aiops/rca', (req, res) => {
  const item = { id: 'rca-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_rca_data) global.aiops_rca_data = [];
  global.aiops_rca_data.push(item);
  res.json(item);
});

router.get('/api/aiops/rca/:id', (req, res) => {
  const arr = global.aiops_rca_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/rca/:id', (req, res) => {
  const arr = global.aiops_rca_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/remediation', (req, res) => {
  res.json(global.aiops_remediation_data || []);
});

router.post('/api/aiops/remediation', (req, res) => {
  const item = { id: 'remediation-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_remediation_data) global.aiops_remediation_data = [];
  global.aiops_remediation_data.push(item);
  res.json(item);
});

router.get('/api/aiops/remediation/:id', (req, res) => {
  const arr = global.aiops_remediation_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/remediation/:id', (req, res) => {
  const arr = global.aiops_remediation_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/dem', (req, res) => {
  res.json(global.aiops_dem_data || []);
});

router.post('/api/aiops/dem', (req, res) => {
  const item = { id: 'dem-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_dem_data) global.aiops_dem_data = [];
  global.aiops_dem_data.push(item);
  res.json(item);
});

router.get('/api/aiops/dem/:id', (req, res) => {
  const arr = global.aiops_dem_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/dem/:id', (req, res) => {
  const arr = global.aiops_dem_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/alerts', (req, res) => {
  res.json(global.aiops_alerts_data || []);
});

router.post('/api/aiops/alerts', (req, res) => {
  const item = { id: 'alerts-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_alerts_data) global.aiops_alerts_data = [];
  global.aiops_alerts_data.push(item);
  res.json(item);
});

router.get('/api/aiops/alerts/:id', (req, res) => {
  const arr = global.aiops_alerts_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/alerts/:id', (req, res) => {
  const arr = global.aiops_alerts_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/scaling', (req, res) => {
  res.json(global.aiops_scaling_data || []);
});

router.post('/api/aiops/scaling', (req, res) => {
  const item = { id: 'scaling-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_scaling_data) global.aiops_scaling_data = [];
  global.aiops_scaling_data.push(item);
  res.json(item);
});

router.get('/api/aiops/scaling/:id', (req, res) => {
  const arr = global.aiops_scaling_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/scaling/:id', (req, res) => {
  const arr = global.aiops_scaling_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/health', (req, res) => {
  res.json(global.aiops_health_data || []);
});

router.post('/api/aiops/health', (req, res) => {
  const item = { id: 'health-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_health_data) global.aiops_health_data = [];
  global.aiops_health_data.push(item);
  res.json(item);
});

router.get('/api/aiops/health/:id', (req, res) => {
  const arr = global.aiops_health_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/health/:id', (req, res) => {
  const arr = global.aiops_health_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/assistant', (req, res) => {
  res.json(global.aiops_assistant_data || []);
});

router.post('/api/aiops/assistant', (req, res) => {
  const item = { id: 'assistant-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_assistant_data) global.aiops_assistant_data = [];
  global.aiops_assistant_data.push(item);
  res.json(item);
});

router.get('/api/aiops/assistant/:id', (req, res) => {
  const arr = global.aiops_assistant_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/assistant/:id', (req, res) => {
  const arr = global.aiops_assistant_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/change-risk', (req, res) => {
  res.json(global.aiops_change_risk_data || []);
});

router.post('/api/aiops/change-risk', (req, res) => {
  const item = { id: 'change-risk-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_change_risk_data) global.aiops_change_risk_data = [];
  global.aiops_change_risk_data.push(item);
  res.json(item);
});

router.get('/api/aiops/change-risk/:id', (req, res) => {
  const arr = global.aiops_change_risk_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/change-risk/:id', (req, res) => {
  const arr = global.aiops_change_risk_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/capacity', (req, res) => {
  res.json(global.aiops_capacity_data || []);
});

router.post('/api/aiops/capacity', (req, res) => {
  const item = { id: 'capacity-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_capacity_data) global.aiops_capacity_data = [];
  global.aiops_capacity_data.push(item);
  res.json(item);
});

router.get('/api/aiops/capacity/:id', (req, res) => {
  const arr = global.aiops_capacity_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/capacity/:id', (req, res) => {
  const arr = global.aiops_capacity_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/aiops/chatbot', (req, res) => {
  res.json(global.aiops_chatbot_data || []);
});

router.post('/api/aiops/chatbot', (req, res) => {
  const item = { id: 'chatbot-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.aiops_chatbot_data) global.aiops_chatbot_data = [];
  global.aiops_chatbot_data.push(item);
  res.json(item);
});

router.get('/api/aiops/chatbot/:id', (req, res) => {
  const arr = global.aiops_chatbot_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/aiops/chatbot/:id', (req, res) => {
  const arr = global.aiops_chatbot_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
