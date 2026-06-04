import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from hybrid_networking import HybridNetworking

@pytest.fixture
def mesh():
    m = HybridNetworking({"asn": 64512})
    m.initialize()
    yield m
    m.close()

class TestHybridNetworking:
    def test_list_peers_empty(self, mesh):
        assert mesh.list_peers() == []

    def test_register_peer(self, mesh):
        p = mesh.register_peer(name="node1", endpoint="10.0.0.1", subnet="10.0.1.0/24")
        assert p.peer_id is not None
        assert p.connected is False

    def test_list_tunnels_empty(self, mesh):
        assert mesh.list_tunnels() == []

    def test_create_tunnel(self, mesh):
        p = mesh.register_peer("node1", "10.0.0.1", "10.0.1.0/24")
        t = mesh.create_tunnel(p.peer_id)
        assert t.tunnel_id is not None
        assert t.status == "established"

    def test_topology(self, mesh):
        topo = mesh.get_topology()
        assert topo["mesh_name"] is not None
        assert topo["total_peers"] == 0

    def test_topology_with_peers(self, mesh):
        mesh.register_peer("n1", "10.0.0.1", "10.0.1.0/24")
        mesh.register_peer("n2", "10.0.0.2", "10.0.2.0/24")
        topo = mesh.get_topology()
        assert topo["total_peers"] == 2

    def test_add_route(self, mesh):
        r = mesh.add_route(prefix="10.0.0.0/8", next_hop="192.168.1.1")
        assert r["added"] is True

    def test_register_peer_minimal(self, mesh):
        p = mesh.register_peer("minimal", "10.0.0.99")
        assert p.peer_id is not None
        assert p.node_type == "on_prem"
