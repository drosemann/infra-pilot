const express = require('express');
const router = express.Router();

// Compliance V4 API Routes

router.get('/api/compliance_v4/continuous-compliance', (req, res) => {
  res.json(global.compliance_v4_continuous_compliance_data || []);
});

router.post('/api/compliance_v4/continuous-compliance', (req, res) => {
  const item = { id: 'continuous-compliance-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_continuous_compliance_data) global.compliance_v4_continuous_compliance_data = [];
  global.compliance_v4_continuous_compliance_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/continuous-compliance/:id', (req, res) => {
  const arr = global.compliance_v4_continuous_compliance_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/continuous-compliance/:id', (req, res) => {
  const arr = global.compliance_v4_continuous_compliance_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/evidence', (req, res) => {
  res.json(global.compliance_v4_evidence_data || []);
});

router.post('/api/compliance_v4/evidence', (req, res) => {
  const item = { id: 'evidence-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_evidence_data) global.compliance_v4_evidence_data = [];
  global.compliance_v4_evidence_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/evidence/:id', (req, res) => {
  const arr = global.compliance_v4_evidence_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/evidence/:id', (req, res) => {
  const arr = global.compliance_v4_evidence_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/cac', (req, res) => {
  res.json(global.compliance_v4_cac_data || []);
});

router.post('/api/compliance_v4/cac', (req, res) => {
  const item = { id: 'cac-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_cac_data) global.compliance_v4_cac_data = [];
  global.compliance_v4_cac_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/cac/:id', (req, res) => {
  const arr = global.compliance_v4_cac_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/cac/:id', (req, res) => {
  const arr = global.compliance_v4_cac_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/attestation', (req, res) => {
  res.json(global.compliance_v4_attestation_data || []);
});

router.post('/api/compliance_v4/attestation', (req, res) => {
  const item = { id: 'attestation-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_attestation_data) global.compliance_v4_attestation_data = [];
  global.compliance_v4_attestation_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/attestation/:id', (req, res) => {
  const arr = global.compliance_v4_attestation_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/attestation/:id', (req, res) => {
  const arr = global.compliance_v4_attestation_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/vendor', (req, res) => {
  res.json(global.compliance_v4_vendor_data || []);
});

router.post('/api/compliance_v4/vendor', (req, res) => {
  const item = { id: 'vendor-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_vendor_data) global.compliance_v4_vendor_data = [];
  global.compliance_v4_vendor_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/vendor/:id', (req, res) => {
  const arr = global.compliance_v4_vendor_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/vendor/:id', (req, res) => {
  const arr = global.compliance_v4_vendor_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/regulatory', (req, res) => {
  res.json(global.compliance_v4_regulatory_data || []);
});

router.post('/api/compliance_v4/regulatory', (req, res) => {
  const item = { id: 'regulatory-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_regulatory_data) global.compliance_v4_regulatory_data = [];
  global.compliance_v4_regulatory_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/regulatory/:id', (req, res) => {
  const arr = global.compliance_v4_regulatory_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/regulatory/:id', (req, res) => {
  const arr = global.compliance_v4_regulatory_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/audit-management', (req, res) => {
  res.json(global.compliance_v4_audit_management_data || []);
});

router.post('/api/compliance_v4/audit-management', (req, res) => {
  const item = { id: 'audit-management-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_audit_management_data) global.compliance_v4_audit_management_data = [];
  global.compliance_v4_audit_management_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/audit-management/:id', (req, res) => {
  const arr = global.compliance_v4_audit_management_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/audit-management/:id', (req, res) => {
  const arr = global.compliance_v4_audit_management_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/data-residency', (req, res) => {
  res.json(global.compliance_v4_data_residency_data || []);
});

router.post('/api/compliance_v4/data-residency', (req, res) => {
  const item = { id: 'data-residency-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_data_residency_data) global.compliance_v4_data_residency_data = [];
  global.compliance_v4_data_residency_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/data-residency/:id', (req, res) => {
  const arr = global.compliance_v4_data_residency_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/data-residency/:id', (req, res) => {
  const arr = global.compliance_v4_data_residency_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/training', (req, res) => {
  res.json(global.compliance_v4_training_data || []);
});

router.post('/api/compliance_v4/training', (req, res) => {
  const item = { id: 'training-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_training_data) global.compliance_v4_training_data = [];
  global.compliance_v4_training_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/training/:id', (req, res) => {
  const arr = global.compliance_v4_training_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/training/:id', (req, res) => {
  const arr = global.compliance_v4_training_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/compliance_v4/auditor-portal', (req, res) => {
  res.json(global.compliance_v4_auditor_portal_data || []);
});

router.post('/api/compliance_v4/auditor-portal', (req, res) => {
  const item = { id: 'auditor-portal-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.compliance_v4_auditor_portal_data) global.compliance_v4_auditor_portal_data = [];
  global.compliance_v4_auditor_portal_data.push(item);
  res.json(item);
});

router.get('/api/compliance_v4/auditor-portal/:id', (req, res) => {
  const arr = global.compliance_v4_auditor_portal_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/compliance_v4/auditor-portal/:id', (req, res) => {
  const arr = global.compliance_v4_auditor_portal_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
