"""Tests for Mesh Network Manager."""

import pytest
from mesh_network_manager import (
    MeshNetworkManager, MeshNode, MeshLink,
    NodeRole, LinkStatus, MeshTopology, RoutingProtocol
)


@pytest.fixture
def mesh():
    return MeshNetworkManager({})


class TestMeshNode:
    def test_create(self):
        node = MeshNode("node-01", "gateway-1", NodeRole.GATEWAY,
                         "192.168.1.1", {"cpu": 4, "ram": 8})
        assert node.node_id == "node-01"
        assert node.role == NodeRole.GATEWAY
        assert node.is_online is True

    def test_to_dict(self):
        node = MeshNode("node-01", "gw", NodeRole.RELAY,
                         "10.0.0.1", {"cpu": 2})
        d = node.to_dict()
        assert d["node_id"] == "node-01"
        assert d["role"] == "relay"


class TestMeshLink:
    def test_create(self):
        link = MeshLink("link-01", "node-a", "node-b", 802.11, 300)
        assert link.link_id == "link-01"
        assert link.status == LinkStatus.ACTIVE
        assert link.signal_dbm == -65

    def test_to_dict(self):
        link = MeshLink("l-01", "a", "b", 802.11, 300)
        d = link.to_dict()
        assert d["source_id"] == "a"
        assert d["frequency_mhz"] == 300

    def test_link_status_enum(self):
        assert LinkStatus.ACTIVE.value == "active"
        assert LinkStatus.DEGRADED.value == "degraded"
        assert LinkStatus.DOWN.value == "down"


class TestMeshNetworkManager:
    def test_initialization(self, mesh):
        assert len(mesh.nodes) > 0
        assert len(mesh.links) > 0

    def test_register_node(self, mesh):
        node = mesh.register_node(
            "node-new", "mesh-1", NodeRole.RELAY,
            "10.0.0.5", {"cpu": 2, "ram": 4}
        )
        assert node.node_id == "node-new"
        assert node.gateway_id == "mesh-1"

    def test_get_node(self, mesh):
        nid = list(mesh.nodes.keys())[0]
        assert mesh.get_node(nid) is not None

    def test_get_node_not_found(self, mesh):
        assert mesh.get_node("nonexistent") is None

    def test_list_nodes(self, mesh):
        nodes = mesh.list_nodes()
        assert len(nodes) > 0

    def test_unregister_node(self, mesh):
        nid = list(mesh.nodes.keys())[0]
        assert mesh.unregister_node(nid) is True
        assert mesh.get_node(nid) is None

    def test_unregister_node_not_found(self, mesh):
        assert mesh.unregister_node("nonexistent") is False

    def test_create_link(self, mesh):
        nodes = list(mesh.nodes.values())
        link = mesh.create_link(nodes[0].node_id, nodes[1].node_id, 5000, 65)
        assert link is not None
        assert link.source_id == nodes[0].node_id

    def test_create_link_node_not_found(self, mesh):
        assert mesh.create_link("nonexistent", "nonexistent2", 5000, 60) is None

    def test_get_link(self, mesh):
        lid = list(mesh.links.keys())[0]
        assert mesh.get_link(lid) is not None

    def test_get_link_not_found(self, mesh):
        assert mesh.get_link("nonexistent") is None

    def test_list_links(self, mesh):
        links = mesh.list_links()
        assert len(links) > 0

    def test_remove_link(self, mesh):
        lid = list(mesh.links.keys())[0]
        assert mesh.remove_link(lid) is True

    def test_remove_link_not_found(self, mesh):
        assert mesh.remove_link("nonexistent") is False

    def test_get_topology(self, mesh):
        topology = mesh.get_topology()
        assert "nodes" in topology
        assert "links" in topology

    def test_find_path(self, mesh):
        nodes = list(mesh.nodes.values())
        path = mesh.find_path(nodes[0].node_id, nodes[-1].node_id)
        assert path is not None

    def test_find_path_no_route(self, mesh):
        assert mesh.find_path("nonexistent", "other") is None

    def test_get_network_stats(self, mesh):
        stats = mesh.get_network_stats()
        assert "total_nodes" in stats
        assert "online_nodes" in stats
        assert "total_links" in stats
        assert "active_links" in stats

    def test_get_routing_table(self, mesh):
        table = mesh.get_routing_table("node-001")
        assert len(table) > 0

    def test_optimize_routes(self, mesh):
        result = mesh.optimize_routes()
        assert "status" in result
        assert result["status"] == "optimized"

    def test_get_node_links(self, mesh):
        nid = list(mesh.nodes.keys())[0]
        links = mesh.get_node_links(nid)
        assert len(links) >= 0

    def test_node_role_enum(self):
        assert NodeRole.GATEWAY.value == "gateway"
        assert NodeRole.RELAY.value == "relay"
        assert NodeRole.LEAF.value == "leaf"

    def test_routing_protocol_enum(self):
        assert RoutingProtocol.OSPF.value == "ospf"
        assert RoutingProtocol.BATMAN.value == "batman"
        assert RoutingProtocol.HWMP.value == "hwmp"
