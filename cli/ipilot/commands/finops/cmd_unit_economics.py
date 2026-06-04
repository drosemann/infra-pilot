"""Feature 23: Unit Economics CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('uoe', help='Unit economics dashboard')
    ps = p.add_subparsers(dest='action')
    metrics = ps.add_parser('metrics', help='List metrics')
    metrics.add_argument('--customer-id', help='Filter by customer')
    metrics.add_argument('--dimension', help='Filter by dimension')
    record = ps.add_parser('record', help='Record metric')
    record.add_argument('customer_id', help='Customer ID')
    record.add_argument('metric_name', help='Metric name')
    record.add_argument('value', type=float, help='Metric value')
    record.add_argument('--dimension', default='general', help='Dimension')
    ps.add_parser('targets', help='List targets')
    sett = ps.add_parser('set-target', help='Set target')
    sett.add_argument('metric_name', help='Metric name')
    sett.add_argument('target_value', type=float, help='Target value')
    sett.add_argument('--threshold', type=float, default=10.0, help='Alert threshold %')
    ps.add_parser('violations', help='List violations')
    ps.add_parser('overview', help='Unit economics overview')
    compare = ps.add_parser('compare', help='Compare customers')
    compare.add_argument('customer_id_1', help='First customer ID')
    compare.add_argument('customer_id_2', help='Second customer ID')
    forecast = ps.add_parser('forecast', help='Forecast metric')
    forecast.add_argument('metric_name', help='Metric name')
    ps.add_parser('dimensions', help='List dimensions')
    ps.add_parser('export', help='Export metrics')
    ps.add_parser('efficiency', help='Efficiency analysis')
    ps.add_parser('segments', help='List customer segments')
    dm = ps.add_parser('delete-metric', help='Delete metric')
    dm.add_argument('metric_id', help='Metric ID')
    return 'uoe'

def execute(args, client):
    if args.action == 'metrics':
        data = client.finops_uoe_metrics(args.customer_id, args.dimension)
        print_output(data if isinstance(data, list) else data.get('metrics', data), args.output)
    elif args.action == 'record':
        print_output(client.finops_uoe_record(args.customer_id, args.metric_name, args.value, args.dimension), args.output)
    elif args.action == 'targets':
        data = client.finops_uoe_targets()
        print_output(data if isinstance(data, list) else data.get('targets', data), args.output)
    elif args.action == 'set-target':
        print_output(client.finops_uoe_set_target(args.metric_name, args.target_value, args.threshold), args.output)
    elif args.action == 'violations':
        data = client.finops_uoe_violations()
        print_output(data if isinstance(data, list) else data.get('violations', data), args.output)
    elif args.action == 'overview':
        print_output(client.finops_uoe_overview(), args.output)
    elif args.action == 'compare':
        print_output(client.finops_uoe_compare(args.customer_id_1, args.customer_id_2), args.output)
    elif args.action == 'forecast':
        print_output(client.finops_uoe_forecast(args.metric_name), args.output)
    elif args.action == 'dimensions':
        print_output(client.finops_uoe_dimensions(), args.output)
    elif args.action == 'export':
        print_output(client.finops_uoe_export(), args.output)
    elif args.action == 'efficiency':
        print_output(client.finops_uoe_efficiency(), args.output)
    elif args.action == 'segments':
        data = client.finops_uoe_segments()
        print_output(data if isinstance(data, list) else data.get('segments', data), args.output)
    elif args.action == 'delete-metric':
        print_output(client.finops_uoe_delete_metric(args.metric_id), args.output)
