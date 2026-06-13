"""Feature 25: Budget & Forecast Engine CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('budget', help='Budget forecasting')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('list', help='List budgets')
    create = ps.add_parser('create', help='Create budget')
    create.add_argument('name', help='Budget name')
    create.add_argument('amount', type=float, help='Budget amount')
    create.add_argument('--period', default='monthly', choices=['weekly', 'monthly', 'quarterly', 'annual'], help='Period')
    create.add_argument('--scope', default='team', help='Scope')
    get = ps.add_parser('get', help='Get budget')
    get.add_argument('budget_id', help='Budget ID')
    spend = ps.add_parser('spend', help='Record spend')
    spend.add_argument('budget_id', help='Budget ID')
    spend.add_argument('amount', type=float, help='Spend amount')
    forecast = ps.add_parser('forecast', help='Get budget forecast')
    forecast.add_argument('budget_id', help='Budget ID')
    scenario = ps.add_parser('scenario', help='What-if scenario')
    scenario.add_argument('budget_id', help='Budget ID')
    scenario.add_argument('changes', help='JSON changes object')
    ps.add_parser('summary', help='Budget summary')
    variance = ps.add_parser('variance', help='Variance analysis')
    variance.add_argument('budget_id', help='Budget ID')
    ps.add_parser('alerts', help='List budget alerts')
    ca = ps.add_parser('create-alert', help='Create budget alert')
    ca.add_argument('budget_id', help='Budget ID')
    ca.add_argument('--threshold', type=float, default=80, help='Alert threshold %')
    delete = ps.add_parser('delete', help='Delete budget')
    delete.add_argument('budget_id', help='Budget ID')
    export = ps.add_parser('export', help='Export budget data')
    export.add_argument('budget_id', help='Budget ID')
    export.add_argument('--format', default='csv', choices=['csv', 'json', 'pdf'], help='Export format')
    st = ps.add_parser('set-threshold', help='Set alert threshold')
    st.add_argument('budget_id', help='Budget ID')
    st.add_argument('threshold_pct', type=float, help='Threshold %')
    ps.add_parser('health', help='Budget health check')
    trend = ps.add_parser('trend', help='Show budget trend')
    trend.add_argument('budget_id', help='Budget ID')
    return 'budget'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_budget_list()
        print_output(data if isinstance(data, list) else data.get('budgets', data), args.output)
    elif args.action == 'create':
        print_output(client.finops_budget_create(args.name, args.amount, args.period, args.scope), args.output)
    elif args.action == 'get':
        print_output(client.finops_budget_get(args.budget_id), args.output)
    elif args.action == 'spend':
        print_output(client.finops_budget_spend(args.budget_id, args.amount), args.output)
    elif args.action == 'forecast':
        print_output(client.finops_budget_forecast(args.budget_id), args.output)
    elif args.action == 'scenario':
        changes = json.loads(args.changes)
        print_output(client.finops_budget_scenario(args.budget_id, changes), args.output)
    elif args.action == 'summary':
        print_output(client.finops_budget_summary(), args.output)
    elif args.action == 'variance':
        print_output(client.finops_budget_variance(args.budget_id), args.output)
    elif args.action == 'alerts':
        data = client.finops_budget_alerts()
        print_output(data if isinstance(data, list) else data.get('alerts', data), args.output)
    elif args.action == 'create-alert':
        print_output(client.finops_budget_create_alert(args.budget_id, args.threshold), args.output)
    elif args.action == 'delete':
        print_output(client.finops_budget_delete(args.budget_id), args.output)
    elif args.action == 'export':
        print_output(client.finops_budget_export(args.budget_id, args.format), args.output)
    elif args.action == 'set-threshold':
        print_output(client.finops_budget_set_threshold(args.budget_id, args.threshold_pct), args.output)
    elif args.action == 'health':
        print_output(client.finops_budget_health(), args.output)
    elif args.action == 'trend':
        print_output(client.finops_budget_trend(args.budget_id), args.output)
