"""Feature 30: FinOps Reporting & Compliance CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('reports', help='FinOps reporting & compliance')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('list', help='List reports')
    ps.add_parser('summary', help='Reports summary')
    generate = ps.add_parser('generate', help='Generate report')
    generate.add_argument('report_type', help='Report type (executive_summary, cost_breakdown, savings_opportunity, budget_vs_actual, showback, chargeback, commitment_utilization, waste_analysis, forecast, compliance, kpi_dashboard)')
    generate.add_argument('--period', default='monthly', help='Period')
    get = ps.add_parser('get', help='Get report')
    get.add_argument('report_id', help='Report ID')
    dashboard = ps.add_parser('dashboard', help='Get pre-built dashboard')
    dashboard.add_argument('--type', default='kpi_dashboard', help='Dashboard type')
    allocation = ps.add_parser('allocation', help='List cost allocations')
    allocation.add_argument('--team', help='Filter by team')
    create_allocation = ps.add_parser('create-allocation', help='Create allocation tag')
    create_allocation.add_argument('tag_key', help='Tag key')
    create_allocation.add_argument('tag_value', help='Tag value')
    create_allocation.add_argument('cost_pct', type=float, help='Cost percentage')
    create_allocation.add_argument('--team', help='Team')
    create_allocation.add_argument('--project', help='Project')
    export = ps.add_parser('export', help='Export report')
    export.add_argument('report_id', help='Report ID')
    export.add_argument('--format', default='csv', choices=['csv', 'json', 'pdf'], help='Export format')
    ps.add_parser('compliance', help='Compliance overview')
    cc = ps.add_parser('compliance-check', help='Run compliance check')
    cc.add_argument('check_name', help='Check name')
    ps.add_parser('forecast-summary', help='Forecast summary')
    ps.add_parser('chargeback', help='Chargeback summary')
    delete = ps.add_parser('delete', help='Delete report')
    delete.add_argument('report_id', help='Report ID')
    sched = ps.add_parser('schedule', help='Schedule recurring report')
    sched.add_argument('report_type', help='Report type')
    sched.add_argument('--interval', default='monthly', help='Schedule interval')
    return 'reports'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_reports_list()
        print_output(data if isinstance(data, list) else data.get('reports', data), args.output)
    elif args.action == 'summary':
        print_output(client.finops_reports_summary(), args.output)
    elif args.action == 'generate':
        print_output(client.finops_reports_generate(args.report_type, args.period), args.output)
    elif args.action == 'get':
        print_output(client.finops_reports_get(args.report_id), args.output)
    elif args.action == 'dashboard':
        print_output(client.finops_reports_dashboard(args.type), args.output)
    elif args.action == 'allocation':
        data = client.finops_reports_allocations(args.team)
        print_output(data if isinstance(data, list) else data.get('allocations', data), args.output)
    elif args.action == 'create-allocation':
        print_output(client.finops_reports_create_allocation(args.tag_key, args.tag_value, args.cost_pct, args.team, args.project), args.output)
    elif args.action == 'export':
        print_output(client.finops_reports_export(args.report_id, args.format), args.output)
    elif args.action == 'compliance':
        print_output(client.finops_reports_compliance(), args.output)
    elif args.action == 'compliance-check':
        print_output(client.finops_reports_compliance_check(args.check_name), args.output)
    elif args.action == 'forecast-summary':
        print_output(client.finops_reports_forecast_summary(), args.output)
    elif args.action == 'chargeback':
        data = client.finops_reports_chargeback()
        print_output(data if isinstance(data, list) else data.get('teams', data), args.output)
    elif args.action == 'delete':
        print_output(client.finops_reports_delete(args.report_id), args.output)
    elif args.action == 'schedule':
        print_output(client.finops_reports_schedule(args.report_type, args.interval), args.output)
