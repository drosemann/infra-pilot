"""Feature 26: Resource Right-Sizing CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('rightsizing', help='Resource right-sizing recommendations')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('list', help='List recommendations')
    ps.add_parser('summary', help='Rightsizing summary')
    approve = ps.add_parser('approve', help='Approve recommendation')
    approve.add_argument('rec_id', help='Recommendation ID')
    implement = ps.add_parser('implement', help='Implement recommendation')
    implement.add_argument('rec_id', help='Recommendation ID')
    dismiss = ps.add_parser('dismiss', help='Dismiss recommendation')
    dismiss.add_argument('rec_id', help='Recommendation ID')
    register_cmd = ps.add_parser('register', help='Register resource')
    register_cmd.add_argument('name', help='Resource name')
    register_cmd.add_argument('resource_type', help='Type (compute/database/storage)')
    register_cmd.add_argument('current_size', help='Current size')
    register_cmd.add_argument('--monthly-cost', type=float, default=100, help='Monthly cost')
    register_cmd.add_argument('--provider', default='aws', help='Provider')
    register_cmd.add_argument('--region', default='us-east-1', help='Region')
    analyze = ps.add_parser('analyze', help='Analyze resource')
    analyze.add_argument('resource_id', help='Resource ID')
    ps.add_parser('report', help='Generate rightsizing report')
    ba = ps.add_parser('batch-approve', help='Batch approve recommendations')
    ba.add_argument('rec_ids', help='Comma-separated recommendation IDs')
    sim = ps.add_parser('simulate', help='Simulate resize')
    sim.add_argument('resource_id', help='Resource ID')
    sim.add_argument('target_size', help='Target size')
    bsim = ps.add_parser('batch-simulate', help='Batch simulate')
    bsim.add_argument('rec_ids', help='Comma-separated recommendation IDs')
    ps.add_parser('insights', help='Show rightsizing insights')
    delete = ps.add_parser('delete', help='Delete recommendation')
    delete.add_argument('rec_id', help='Recommendation ID')
    return 'rightsizing'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_rightsizing_list()
        print_output(data if isinstance(data, list) else data.get('recommendations', data), args.output)
    elif args.action == 'summary':
        print_output(client.finops_rightsizing_summary(), args.output)
    elif args.action == 'approve':
        print_output(client.finops_rightsizing_approve(args.rec_id), args.output)
    elif args.action == 'implement':
        print_output(client.finops_rightsizing_implement(args.rec_id), args.output)
    elif args.action == 'dismiss':
        print_output(client.finops_rightsizing_dismiss(args.rec_id), args.output)
    elif args.action == 'register':
        specs = {'cpu': 2, 'memory_gb': 8}
        print_output(client.finops_rightsizing_register(args.name, args.resource_type, args.current_size, specs, args.monthly_cost, args.provider, args.region), args.output)
    elif args.action == 'analyze':
        print_output(client.finops_rightsizing_analyze(args.resource_id), args.output)
    elif args.action == 'report':
        print_output(client.finops_rightsizing_report(), args.output)
    elif args.action == 'batch-approve':
        recs = [r.strip() for r in args.rec_ids.split(',')]
        print_output(client.finops_rightsizing_batch_approve(recs), args.output)
    elif args.action == 'simulate':
        print_output(client.finops_rightsizing_simulate(args.resource_id, args.target_size), args.output)
    elif args.action == 'batch-simulate':
        recs = [r.strip() for r in args.rec_ids.split(',')]
        print_output(client.finops_rightsizing_batch_simulate(recs), args.output)
    elif args.action == 'insights':
        print_output(client.finops_rightsizing_insights(), args.output)
    elif args.action == 'delete':
        print_output(client.finops_rightsizing_delete(args.rec_id), args.output)
