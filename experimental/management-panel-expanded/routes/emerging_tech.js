const express = require('express');
const router = express.Router();

// Emerging Tech API Routes

router.get('/api/emerging_tech/blockchain', (req, res) => {
  res.json(global.emerging_tech_blockchain_data || []);
});

router.post('/api/emerging_tech/blockchain', (req, res) => {
  const item = { id: 'blockchain-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_blockchain_data) global.emerging_tech_blockchain_data = [];
  global.emerging_tech_blockchain_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/blockchain/:id', (req, res) => {
  const arr = global.emerging_tech_blockchain_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/blockchain/:id', (req, res) => {
  const arr = global.emerging_tech_blockchain_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/storage', (req, res) => {
  res.json(global.emerging_tech_storage_data || []);
});

router.post('/api/emerging_tech/storage', (req, res) => {
  const item = { id: 'storage-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_storage_data) global.emerging_tech_storage_data = [];
  global.emerging_tech_storage_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/storage/:id', (req, res) => {
  const arr = global.emerging_tech_storage_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/storage/:id', (req, res) => {
  const arr = global.emerging_tech_storage_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/quantum', (req, res) => {
  res.json(global.emerging_tech_quantum_data || []);
});

router.post('/api/emerging_tech/quantum', (req, res) => {
  const item = { id: 'quantum-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_quantum_data) global.emerging_tech_quantum_data = [];
  global.emerging_tech_quantum_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/quantum/:id', (req, res) => {
  const arr = global.emerging_tech_quantum_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/quantum/:id', (req, res) => {
  const arr = global.emerging_tech_quantum_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/contracts', (req, res) => {
  res.json(global.emerging_tech_contracts_data || []);
});

router.post('/api/emerging_tech/contracts', (req, res) => {
  const item = { id: 'contracts-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_contracts_data) global.emerging_tech_contracts_data = [];
  global.emerging_tech_contracts_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/contracts/:id', (req, res) => {
  const arr = global.emerging_tech_contracts_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/contracts/:id', (req, res) => {
  const arr = global.emerging_tech_contracts_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/web3id', (req, res) => {
  res.json(global.emerging_tech_web3id_data || []);
});

router.post('/api/emerging_tech/web3id', (req, res) => {
  const item = { id: 'web3id-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_web3id_data) global.emerging_tech_web3id_data = [];
  global.emerging_tech_web3id_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/web3id/:id', (req, res) => {
  const arr = global.emerging_tech_web3id_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/web3id/:id', (req, res) => {
  const arr = global.emerging_tech_web3id_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/confidential', (req, res) => {
  res.json(global.emerging_tech_confidential_data || []);
});

router.post('/api/emerging_tech/confidential', (req, res) => {
  const item = { id: 'confidential-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_confidential_data) global.emerging_tech_confidential_data = [];
  global.emerging_tech_confidential_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/confidential/:id', (req, res) => {
  const arr = global.emerging_tech_confidential_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/confidential/:id', (req, res) => {
  const arr = global.emerging_tech_confidential_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/federated', (req, res) => {
  res.json(global.emerging_tech_federated_data || []);
});

router.post('/api/emerging_tech/federated', (req, res) => {
  const item = { id: 'federated-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_federated_data) global.emerging_tech_federated_data = [];
  global.emerging_tech_federated_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/federated/:id', (req, res) => {
  const arr = global.emerging_tech_federated_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/federated/:id', (req, res) => {
  const arr = global.emerging_tech_federated_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/zkp', (req, res) => {
  res.json(global.emerging_tech_zkp_data || []);
});

router.post('/api/emerging_tech/zkp', (req, res) => {
  const item = { id: 'zkp-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_zkp_data) global.emerging_tech_zkp_data = [];
  global.emerging_tech_zkp_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/zkp/:id', (req, res) => {
  const arr = global.emerging_tech_zkp_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/zkp/:id', (req, res) => {
  const arr = global.emerging_tech_zkp_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

router.get('/api/emerging_tech/dcn', (req, res) => {
  res.json(global.emerging_tech_dcn_data || []);
});

router.post('/api/emerging_tech/dcn', (req, res) => {
  const item = { id: 'dcn-' + Date.now(), ...req.body, created_at: new Date().toISOString() };
  if (!global.emerging_tech_dcn_data) global.emerging_tech_dcn_data = [];
  global.emerging_tech_dcn_data.push(item);
  res.json(item);
});

router.get('/api/emerging_tech/dcn/:id', (req, res) => {
  const arr = global.emerging_tech_dcn_data || [];
  const item = arr.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
});

router.delete('/api/emerging_tech/dcn/:id', (req, res) => {
  const arr = global.emerging_tech_dcn_data || [];
  const idx = arr.findIndex(x => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  arr.splice(idx, 1);
  res.json({ success: true });
});

module.exports = router;
