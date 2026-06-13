"""Feature 22: Spot/Preemptible Manager CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('spot', help='Spot/preemptible instance management')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('list', help='List fleets')
    create = ps.add_parser('create', help='Create fleet')
    create.add_argument('name', help='Fleet name')
    create.add_argument('instance_types', help='Comma-separated instance types')
    create.add_argument('--target-capacity', type=int, default=2, help='Target capacity')
    create.add_argument('--regions', default='us-east-1', help='Comma-separated regions')
    get = ps.add_parser('get', help='Get fleet details')
    get.add_argument('fleet_id', help='Fleet ID')
    instances = ps.add_parser('instances', help='List fleet instances')
    instances.add_argument('fleet_id', help='Fleet ID')
    ps.add_parser('savings', help='Spot savings summary')
    launch = ps.add_parser('launch', help='Launch instances')
    launch.add_argument('fleet_id', help='Fleet ID')
    launch.add_argument('--count', type=int, help='Number to launch')
    interrupt = ps.add_parser('interrupt', help='Simulate interruption')
    interrupt.add_argument('instance_id', help='Instance ID')
    update = ps.add_parser('update', help='Update fleet capacity')
    update.add_argument('fleet_id', help='Fleet ID')
    update.add_argument('capacity', type=int, help='New capacity')
    cp = ps.add_parser('checkpoint', help='Create fleet checkpoint')
    cp.add_argument('fleet_id', help='Fleet ID')
    drain = ps.add_parser('drain', help='Drain instance')
    drain.add_argument('instance_id', help='Instance ID')
    strat = ps.add_parser('strategy', help='Set allocation strategy')
    strat.add_argument('fleet_id', help='Fleet ID')
    strat.add_argument('strategy', choices=['lowest_price', 'capacity_optimized', 'diversified'], help='Strategy')
    ph = ps.add_parser('price-history', help='Show price history')
    ph.add_argument('instance_type', help='Instance type')
    ph.add_argument('--region', default='us-east-1', help='Region')
    div = ps.add_parser('diversity', help='Instance type diversity score')
    div.add_argument('fleet_id', help='Fleet ID')
    ps.add_parser('summary', help='Spot manager summary')
    delete = ps.add_parser('delete', help='Delete fleet')
    delete.add_argument('fleet_id', help='Fleet ID')
    metrics = ps.add_parser('metrics', help='Fleet metrics')
    metrics.add_argument('fleet_id', help='Fleet ID')
    return 'spot'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_spot_list()
        print_output(data if isinstance(data, list) else data.get('fleets', data), args.output)
    elif args.action == 'create':
        types = [t.strip() for t in args.instance_types.split(',')]
        regions = [r.strip() for r in args.regions.split(',')]
        print_output(client.finops_spot_create(args.name, types, args.target_capacity, regions), args.output)
    elif args.action == 'get':
        print_output(client.finops_spot_get(args.fleet_id), args.output)
    elif args.action == 'instances':
        data = client.finops_spot_instances(args.fleet_id)
        print_output(data if isinstance(data, list) else data.get('instances', data), args.output)
    elif args.action == 'savings':
        print_output(client.finops_spot_savings(), args.output)
    elif args.action == 'launch':
        print_output(client.finops_spot_launch(args.fleet_id, args.count), args.output)
    elif args.action == 'interrupt':
        print_output(client.finops_spot_interrupt(args.instance_id), args.output)
    elif args.action == 'update':
        print_output(client.finops_spot_update(args.fleet_id, args.capacity), args.output)
    elif args.action == 'checkpoint':
        print_output(client.finops_spot_checkpoint(args.fleet_id), args.output)
    elif args.action == 'drain':
        print_output(client.finops_spot_drain(args.instance_id), args.output)
    elif args.action == 'strategy':
        print_output(client.finops_spot_strategy(args.fleet_id, args.strategy), args.output)
    elif args.action == 'price-history':
        print_output(client.finops_spot_price_history(args.instance_type, args.region), args.output)
    elif args.action == 'diversity':
        print_output(client.finops_spot_diversity(args.fleet_id), args.output)
    elif args.action == 'summary':
        print_output(client.finops_spot_summary(), args.output)
    elif args.action == 'delete':
        print_output(client.finops_spot_delete(args.fleet_id), args.output)
    elif args.action == 'metrics':
        print_output(client.finops_spot_metrics(args.fleet_id), args.output)
