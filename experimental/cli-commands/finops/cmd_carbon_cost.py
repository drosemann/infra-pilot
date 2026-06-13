"""Feature 28: Carbon-Aware Cost Optimization CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('carbon', help='Carbon-aware cost optimization')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('list', help='List carbon recommendations')
    ps.add_parser('assets', help='List registered assets')
    register_cmd = ps.add_parser('register', help='Register asset')
    register_cmd.add_argument('name', help='Asset name')
    register_cmd.add_argument('provider', choices=['aws', 'azure', 'gcp'], help='Provider')
    register_cmd.add_argument('region', help='Region')
    register_cmd.add_argument('--monthly-cost', type=float, default=1000, help='Monthly cost')
    register_cmd.add_argument('--kwh', type=float, help='Estimated monthly kWh')
    ps.add_parser('sustainability', help='Sustainability budget')
    footprint = ps.add_parser('footprint', help='Get asset carbon footprint')
    footprint.add_argument('asset_id', help='Asset ID')
    tradeoff = ps.add_parser('tradeoff', help='Trade-off analysis')
    tradeoff.add_argument('asset_id', help='Asset ID')
    intensity = ps.add_parser('intensity', help='Get carbon intensity')
    intensity.add_argument('region', help='Region')
    sp = ps.add_parser('sustainability-plan', help='Sustainability plan')
    sp.add_argument('--target-reduction-pct', type=float, default=30, help='Target reduction %')
    sp.add_argument('--by', default='next-year', help='Target date')
    migrate = ps.add_parser('migrate', help='Migrate asset to greener region')
    migrate.add_argument('asset_id', help='Asset ID')
    migrate.add_argument('target_region', help='Target region')
    ps.add_parser('report', help='Generate carbon report')
    benchmark = ps.add_parser('benchmark', help='Carbon intensity benchmark')
    benchmark.add_argument('region', help='Region')
    ps.add_parser('summary', help='Carbon summary')
    ps.add_parser('breakdown', help='Carbon breakdown by provider')
    delete = ps.add_parser('delete', help='Delete asset')
    delete.add_argument('asset_id', help='Asset ID')
    return 'carbon'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_carbon_list()
        print_output(data if isinstance(data, list) else data.get('recommendations', data), args.output)
    elif args.action == 'assets':
        data = client.finops_carbon_assets()
        print_output(data if isinstance(data, list) else data.get('assets', data), args.output)
    elif args.action == 'register':
        print_output(client.finops_carbon_register(args.name, args.provider, args.region, args.monthly_cost, args.kwh), args.output)
    elif args.action == 'sustainability':
        print_output(client.finops_carbon_sustainability(), args.output)
    elif args.action == 'footprint':
        print_output(client.finops_carbon_footprint(args.asset_id), args.output)
    elif args.action == 'tradeoff':
        print_output(client.finops_carbon_tradeoff(args.asset_id), args.output)
    elif args.action == 'intensity':
        print_output(client.finops_carbon_intensity(args.region), args.output)
    elif args.action == 'sustainability-plan':
        print_output(client.finops_carbon_sustainability_plan(args.target_reduction_pct, args.by), args.output)
    elif args.action == 'migrate':
        print_output(client.finops_carbon_migrate(args.asset_id, args.target_region), args.output)
    elif args.action == 'report':
        print_output(client.finops_carbon_report(), args.output)
    elif args.action == 'benchmark':
        print_output(client.finops_carbon_benchmark(args.region), args.output)
    elif args.action == 'summary':
        print_output(client.finops_carbon_summary(), args.output)
    elif args.action == 'breakdown':
        print_output(client.finops_carbon_breakdown(), args.output)
    elif args.action == 'delete':
        print_output(client.finops_carbon_delete(args.asset_id), args.output)
