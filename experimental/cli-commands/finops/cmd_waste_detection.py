"""Feature 27: Cloud Waste Detection CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('waste', help='Cloud waste detection')
    ps = p.add_subparsers(dest='action')
    lst = ps.add_parser('list', help='List findings')
    lst.add_argument('--category', help='Filter by category')
    lst.add_argument('--severity', help='Filter by severity')
    ps.add_parser('summary', help='Waste summary')
    ps.add_parser('scan', help='Run waste scan')
    approve = ps.add_parser('approve', help='Approve cleanup')
    approve.add_argument('finding_id', help='Finding ID')
    cleanup = ps.add_parser('cleanup', help='Execute cleanup')
    cleanup.add_argument('finding_id', help='Finding ID')
    dismiss = ps.add_parser('dismiss', help='Dismiss finding')
    dismiss.add_argument('finding_id', help='Finding ID')
    cat = ps.add_parser('categorize', help='Categorize finding')
    cat.add_argument('finding_id', help='Finding ID')
    cat.add_argument('category', help='Category name')
    ac = ps.add_parser('auto-cleanup', help='Auto-cleanup by category')
    ac.add_argument('--category', help='Category filter')
    ac.add_argument('--dry-run', action='store_true', help='Dry run only')
    ps.add_parser('trend', help='Waste reduction trend')
    ps.add_parser('report', help='Generate waste report')
    ps.add_parser('savings', help='Savings summary')
    sched = ps.add_parser('schedule', help='Schedule periodic scan')
    sched.add_argument('interval', choices=['daily', 'weekly', 'monthly'], help='Scan interval')
    ps.add_parser('config', help='Waste detection config')
    return 'waste'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_waste_list(args.category, args.severity)
        print_output(data if isinstance(data, list) else data.get('findings', data), args.output)
    elif args.action == 'summary':
        print_output(client.finops_waste_summary(), args.output)
    elif args.action == 'scan':
        print_output(client.finops_waste_scan(), args.output)
    elif args.action == 'approve':
        print_output(client.finops_waste_approve(args.finding_id), args.output)
    elif args.action == 'cleanup':
        print_output(client.finops_waste_cleanup(args.finding_id), args.output)
    elif args.action == 'dismiss':
        print_output(client.finops_waste_dismiss(args.finding_id), args.output)
    elif args.action == 'categorize':
        print_output(client.finops_waste_categorize(args.finding_id, args.category), args.output)
    elif args.action == 'auto-cleanup':
        print_output(client.finops_waste_auto_cleanup(args.category, args.dry_run), args.output)
    elif args.action == 'trend':
        print_output(client.finops_waste_trend(), args.output)
    elif args.action == 'report':
        print_output(client.finops_waste_report(), args.output)
    elif args.action == 'savings':
        print_output(client.finops_waste_savings(), args.output)
    elif args.action == 'schedule':
        print_output(client.finops_waste_schedule(args.interval), args.output)
    elif args.action == 'config':
        print_output(client.finops_waste_config(), args.output)
