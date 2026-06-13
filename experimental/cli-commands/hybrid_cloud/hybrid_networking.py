"""Hybrid networking CLI commands."""
from ...client import ApiClient
from ...output import print_output


def cmd_mesh_peers(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_mesh_peers()
    print_output(data, args.output)


def cmd_mesh_register(args):
    client = ApiClient(args.api_url, args.token)
    data = client.register_mesh_peer(args.name, args.node_type, args.endpoint, args.subnet)
    print_output(data, args.output)


def cmd_mesh_tunnels(args):
    client = ApiClient(args.api_url, args.token)
    data = client.list_mesh_tunnels()
    print_output(data, args.output)


def cmd_mesh_topology(args):
    client = ApiClient(args.api_url, args.token)
    data = client.get_mesh_topology()
    print_output(data, args.output)


def cmd_mesh_route(args):
    client = ApiClient(args.api_url, args.token)
    data = client.add_mesh_route(args.prefix, args.next_hop)
    print_output(data, args.output)


def cmd_mesh_add_peer(args):
    """Add a mesh peer."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_mesh_peer(args.name, args.endpoint, args.node_type)
    print_output(data, args.output)


def cmd_mesh_remove_peer(args):
    """Remove a mesh peer."""
    client = ApiClient(args.api_url, args.token)
    data = client.remove_mesh_peer(args.peer_id)
    print_output(data, args.output)


def cmd_mesh_add_tunnel(args):
    """Add a tunnel."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_mesh_tunnel(args.name, args.peer_id, args.local_cidr, args.remote_cidr, args.tunnel_type)
    print_output(data, args.output)


def cmd_mesh_diagnose(args):
    """Diagnose a peer's connectivity."""
    client = ApiClient(args.api_url, args.token)
    data = client.diagnose_mesh_peer(args.peer_id)
    print_output(data, args.output)


def cmd_mesh_routes(args):
    """List mesh routes."""
    client = ApiClient(args.api_url, args.token)
    data = client.list_mesh_routes()
    print_output(data, args.output)


def cmd_mesh_export(args):
    """Export mesh topology."""
    client = ApiClient(args.api_url, args.token)
    data = client.export_mesh_topology()
    print_output(data, args.output)


def cmd_mesh_stats(args):
    """Show mesh statistics."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_mesh_statistics()
    print_output(data, args.output)


def cmd_mesh_add_peer(args):
    """Register a new peer."""
    client = ApiClient(args.api_url, args.token)
    data = client.register_mesh_peer(args.name, args.endpoint, args.node_type, args.subnet)
    print_output(data, args.output)


def cmd_mesh_add_route(args):
    """Add a BGP route."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_mesh_route(args.prefix, args.next_hop, args.asn)
    print_output(data, args.output)


def cmd_mesh_withdraw_route(args):
    """Withdraw a BGP route."""
    client = ApiClient(args.api_url, args.token)
    data = client.withdraw_mesh_route(args.route_id)
    print_output(data, args.output)


def cmd_mesh_diagnose(args):
    """Diagnose a peer connection."""
    client = ApiClient(args.api_url, args.token)
    data = client.diagnose_mesh_peer(args.peer_id)
    print_output(data, args.output)


def cmd_mesh_latency(args):
    """Show latency matrix."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_mesh_latency_matrix()
    print_output(data, args.output)


def cmd_mesh_bgp_status(args):
    """Show BGP status."""
    client = ApiClient(args.api_url, args.token)
    data = client.get_mesh_bgp_status()
    print_output(data, args.output)


def cmd_mesh_dns_record(args):
    """Add a DNS record."""
    client = ApiClient(args.api_url, args.token)
    data = client.add_mesh_dns_record(args.name, args.type, args.value, args.ttl)
    print_output(data, args.output)
