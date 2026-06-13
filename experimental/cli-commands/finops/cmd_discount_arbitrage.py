"""Feature 29: Multi-Cloud Discount Arbitrage CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('arbitrage', help='Multi-cloud discount arbitrage')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('workloads', help='List workloads')
    ps.add_parser('comparisons', help='Provider comparisons')
    ps.add_parser('savings', help='Savings summary')
    register_cmd = ps.add_parser('register', help='Register workload')
    register_cmd.add_argument('name', help='Workload name')
    register_cmd.add_argument('cpu_cores', type=int, help='CPU cores')
    register_cmd.add_argument('memory_gb', type=int, help='Memory GB')
    register_cmd.add_argument('storage_gb', type=int, help='Storage GB')
    register_cmd.add_argument('data_transfer_gb', type=int, help='Data transfer GB')
    register_cmd.add_argument('current_provider', help='Current provider')
    register_cmd.add_argument('current_cost', type=float, help='Current monthly cost')
    compare = ps.add_parser('compare', help='Compare providers')
    compare.add_argument('workload_id', help='Workload ID')
    migrate = ps.add_parser('migrate', help='Auto-migration recommendation')
    migrate.add_argument('workload_id', help='Workload ID')
    ps.add_parser('export', help='Export arbitrage data')
    risk = ps.add_parser('risk', help='Risk assessment')
    risk.add_argument('workload_id', help='Workload ID')
    svod = ps.add_parser('spot-vs-od', help='Spot vs on-demand comparison')
    svod.add_argument('instance_type', help='Instance type')
    svod.add_argument('--region', default='us-east-1', help='Region')
    ps.add_parser('report', help='Generate arbitrage report')
    pricing = ps.add_parser('pricing', help='List pricing data')
    pricing.add_argument('--provider', choices=['aws', 'azure', 'gcp'], help='Provider')
    pricing.add_argument('--region', default='us-east-1', help='Region')
    recommend = ps.add_parser('recommend', help='Best provider recommendation')
    recommend.add_argument('workload_id', help='Workload ID')
    uw = ps.add_parser('update-workload', help='Update workload cost')
    uw.add_argument('workload_id', help='Workload ID')
    uw.add_argument('new_cost', type=float, help='New monthly cost')
    return 'arbitrage'

def execute(args, client):
    if args.action == 'workloads':
        data = client.finops_arbitrage_workloads()
        print_output(data if isinstance(data, list) else data.get('workloads', data), args.output)
    elif args.action == 'comparisons':
        data = client.finops_arbitrage_comparisons()
        print_output(data if isinstance(data, list) else data.get('comparisons', data), args.output)
    elif args.action == 'savings':
        print_output(client.finops_arbitrage_savings(), args.output)
    elif args.action == 'register':
        print_output(client.finops_arbitrage_register(args.name, args.cpu_cores, args.memory_gb, args.storage_gb, args.data_transfer_gb, args.current_provider, args.current_cost), args.output)
    elif args.action == 'compare':
        print_output(client.finops_arbitrage_compare(args.workload_id), args.output)
    elif args.action == 'migrate':
        print_output(client.finops_arbitrage_migrate(args.workload_id), args.output)
    elif args.action == 'export':
        print_output(client.finops_arbitrage_export(), args.output)
    elif args.action == 'risk':
        print_output(client.finops_arbitrage_risk(args.workload_id), args.output)
    elif args.action == 'spot-vs-od':
        print_output(client.finops_arbitrage_spot_vs_od(args.instance_type, args.region), args.output)
    elif args.action == 'report':
        print_output(client.finops_arbitrage_report(), args.output)
    elif args.action == 'pricing':
        data = client.finops_arbitrage_pricing(args.provider, args.region)
        print_output(data if isinstance(data, list) else data.get('prices', data), args.output)
    elif args.action == 'recommend':
        print_output(client.finops_arbitrage_recommend(args.workload_id), args.output)
    elif args.action == 'update-workload':
        print_output(client.finops_arbitrage_update_workload(args.workload_id, args.new_cost), args.output)
