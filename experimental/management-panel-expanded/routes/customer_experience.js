const express = require('express');
const router = express.Router();

// Customer Experience API Routes

router.get('/api/customer_experience/health-scoring', (req, res) => {
  res.json(global.customer_experience_health_scoring_data || []);
});

router.post('/api/customer_experience/health-scoring', (req, res) => {
  const item = { id: 'health-scoring-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_health_scoring_data) global.customer_experience_health_scoring_data = [];
  global.customer_experience_health_scoring_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/health-scoring/:id', (req, res) => {
  const arr = global.customer_experience_health_scoring_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/health-scoring/:id', (req, res) => {
  const arr = global.customer_experience_health_scoring_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/ticketing', (req, res) => {
  res.json(global.customer_experience_ticketing_data || []);
});

router.post('/api/customer_experience/ticketing', (req, res) => {
  const item = { id: 'ticketing-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_ticketing_data) global.customer_experience_ticketing_data = [];
  global.customer_experience_ticketing_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/ticketing/:id', (req, res) => {
  const arr = global.customer_experience_ticketing_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/ticketing/:id', (req, res) => {
  const arr = global.customer_experience_ticketing_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/sentiment', (req, res) => {
  res.json(global.customer_experience_sentiment_data || []);
});

router.post('/api/customer_experience/sentiment', (req, res) => {
  const item = { id: 'sentiment-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_sentiment_data) global.customer_experience_sentiment_data = [];
  global.customer_experience_sentiment_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/sentiment/:id', (req, res) => {
  const arr = global.customer_experience_sentiment_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/sentiment/:id', (req, res) => {
  const arr = global.customer_experience_sentiment_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/adoption', (req, res) => {
  res.json(global.customer_experience_adoption_data || []);
});

router.post('/api/customer_experience/adoption', (req, res) => {
  const item = { id: 'adoption-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_adoption_data) global.customer_experience_adoption_data = [];
  global.customer_experience_adoption_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/adoption/:id', (req, res) => {
  const arr = global.customer_experience_adoption_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/adoption/:id', (req, res) => {
  const arr = global.customer_experience_adoption_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/onboarding', (req, res) => {
  res.json(global.customer_experience_onboarding_data || []);
});

router.post('/api/customer_experience/onboarding', (req, res) => {
  const item = { id: 'onboarding-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_onboarding_data) global.customer_experience_onboarding_data = [];
  global.customer_experience_onboarding_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/onboarding/:id', (req, res) => {
  const arr = global.customer_experience_onboarding_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/onboarding/:id', (req, res) => {
  const arr = global.customer_experience_onboarding_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/knowledge-base', (req, res) => {
  res.json(global.customer_experience_knowledge_base_data || []);
});

router.post('/api/customer_experience/knowledge-base', (req, res) => {
  const item = { id: 'knowledge-base-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_knowledge_base_data) global.customer_experience_knowledge_base_data = [];
  global.customer_experience_knowledge_base_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/knowledge-base/:id', (req, res) => {
  const arr = global.customer_experience_knowledge_base_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/knowledge-base/:id', (req, res) => {
  const arr = global.customer_experience_knowledge_base_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/community', (req, res) => {
  res.json(global.customer_experience_community_data || []);
});

router.post('/api/customer_experience/community', (req, res) => {
  const item = { id: 'community-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_community_data) global.customer_experience_community_data = [];
  global.customer_experience_community_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/community/:id', (req, res) => {
  const arr = global.customer_experience_community_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/community/:id', (req, res) => {
  const arr = global.customer_experience_community_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/communication', (req, res) => {
  res.json(global.customer_experience_communication_data || []);
});

router.post('/api/customer_experience/communication', (req, res) => {
  const item = { id: 'communication-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_communication_data) global.customer_experience_communication_data = [];
  global.customer_experience_communication_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/communication/:id', (req, res) => {
  const arr = global.customer_experience_communication_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/communication/:id', (req, res) => {
  const arr = global.customer_experience_communication_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/nps', (req, res) => {
  res.json(global.customer_experience_nps_data || []);
});

router.post('/api/customer_experience/nps', (req, res) => {
  const item = { id: 'nps-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_nps_data) global.customer_experience_nps_data = [];
  global.customer_experience_nps_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/nps/:id', (req, res) => {
  const arr = global.customer_experience_nps_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/nps/:id', (req, res) => {
  const arr = global.customer_experience_nps_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/customer_experience/success', (req, res) => {
  res.json(global.customer_experience_success_data || []);
});

router.post('/api/customer_experience/success', (req, res) => {
  const item = { id: 'success-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.customer_experience_success_data) global.customer_experience_success_data = [];
  global.customer_experience_success_data.push(item);
  res.json(item);
});

router.get('/api/customer_experience/success/:id', (req, res) => {
  const arr = global.customer_experience_success_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/customer_experience/success/:id', (req, res) => {
  const arr = global.customer_experience_success_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
