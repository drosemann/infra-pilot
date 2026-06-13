const express = require('express');
const router = express.Router();

const peers = [];
const tunnels = [];

router.get('/api/mesh/peers', (req, res) => res.json(peers));
router.post('/api/mesh/peers', (req, res) => {
  const { name, node_type, endpoint, subnet } = req.body;
  const p = { peer_id: `peer-${Date.now()}`, name, node_type: node_type || 'on_prem', endpoint, subnet, connected: false, latency_ms: 0, registered_at: new Date().toISOString() };
  peers.push(p); res.json(p);
});
router.get('/api/mesh/tunnels', (req, res) => res.json(tunnels));
router.post('/api/mesh/tunnels', (req, res) => {
  const t = { tunnel_id: `tun-${Date.now()}`, peer_id: req.body.peer_id, peer_name: req.body.peer_name, type: 'wireguard', status: 'established', created_at: new Date().toISOString() };
  tunnels.push(t); res.json(t);
});
router.get('/api/mesh/topology', (req, res) => {
  res.json({ mesh_name: 'infrapilot-mesh', total_peers: peers.length, connected_peers: peers.filter(p => p.connected).length, active_tunnels: tunnels.length, bgp_asn: 64512 });
});
router.post('/api/mesh/routes', (req, res) => {
  const { prefix, next_hop } = req.body;
  res.json({ id: `route-${Date.now()}`, prefix, next_hop, added: true });
});

module.exports = router;
