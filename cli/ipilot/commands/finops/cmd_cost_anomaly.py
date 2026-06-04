"""Feature 24: Real-Time Cost Anomaly Detection CLI"""
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('anomaly', help='Cost anomaly detection')
    ps = p.add_subparsers(dest='action')
    lst = ps.add_parser('list', help='List detections')
    lst.add_argument('--severity', help='Filter by severity')
    ps.add_parser('summary', help='Anomaly summary')
    inv = ps.add_parser('investigate', help='Investigate anomaly')
    inv.add_argument('anomaly_id', help='Anomaly ID')
    resolve = ps.add_parser('resolve', help='Resolve anomaly')
    resolve.add_argument('anomaly_id', help='Anomaly ID')
    ps.add_parser('profiles', help='List detection profiles')
    cp = ps.add_parser('create-profile', help='Create profile')
    cp.add_argument('name', help='Profile name')
    cp.add_argument('--method', default='zscore', choices=['zscore', 'mad', 'iqr', 'adaptive'], help='Detection method')
    cp.add_argument('--sensitivity', type=float, default=2.0, help='Sensitivity')
    ingest = ps.add_parser('ingest', help='Ingest spend record')
    ingest.add_argument('service', help='Service name')
    ingest.add_argument('amount', type=float, help='Spend amount')
    ingest.add_argument('--region', default='global', help='Region')
    ps.add_parser('trend', help='Anomaly trend')
    ps.add_parser('config', help='Show config')
    ps.add_parser('report', help='Generate anomaly report')
    dismiss = ps.add_parser('dismiss', help='Dismiss anomaly')
    dismiss.add_argument('anomaly_id', help='Anomaly ID')
    up = ps.add_parser('update-profile', help='Update profile')
    up.add_argument('profile_id', help='Profile ID')
    up.add_argument('--sensitivity', type=float, help='New sensitivity')
    dp = ps.add_parser('delete-profile', help='Delete profile')
    dp.add_argument('profile_id', help='Profile ID')
    ps.add_parser('stats', help='Anomaly statistics')
    sev = ps.add_parser('severity-breakdown', help='Severity breakdown')
    sev.add_argument('--severity', help='Filter by severity')
    respond = ps.add_parser('respond', help='Respond to anomaly')
    respond.add_argument('anomaly_id', help='Anomaly ID')
    respond.add_argument('action', choices=['investigate', 'dismiss', 'escalate', 'suppress'], help='Action')
    alarm = ps.add_parser('alert-config', help='Alert configuration')
    alarm.add_argument('--channel', default='discord', help='Alert channel')
    alarm.add_argument('--min-severity', default='medium', help='Minimum severity')
    return 'anomaly'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_anomaly_list(args.severity)
        print_output(data if isinstance(data, list) else data.get('anomalies', data), args.output)
    elif args.action == 'summary':
        print_output(client.finops_anomaly_summary(), args.output)
    elif args.action == 'investigate':
        print_output(client.finops_anomaly_investigate(args.anomaly_id), args.output)
    elif args.action == 'resolve':
        print_output(client.finops_anomaly_resolve(args.anomaly_id), args.output)
    elif args.action == 'profiles':
        data = client.finops_anomaly_profiles()
        print_output(data if isinstance(data, list) else data.get('profiles', data), args.output)
    elif args.action == 'create-profile':
        print_output(client.finops_anomaly_create_profile(args.name, args.method, args.sensitivity), args.output)
    elif args.action == 'ingest':
        print_output(client.finops_anomaly_ingest(args.service, args.amount, args.region), args.output)
    elif args.action == 'trend':
        print_output(client.finops_anomaly_trend(), args.output)
    elif args.action == 'config':
        print_output(client.finops_anomaly_config(), args.output)
    elif args.action == 'report':
        print_output(client.finops_anomaly_report(), args.output)
    elif args.action == 'dismiss':
        print_output(client.finops_anomaly_dismiss(args.anomaly_id), args.output)
    elif args.action == 'update-profile':
        print_output(client.finops_anomaly_update_profile(args.profile_id, args.sensitivity), args.output)
    elif args.action == 'delete-profile':
        print_output(client.finops_anomaly_delete_profile(args.profile_id), args.output)
    elif args.action == 'stats':
        print_output(client.finops_anomaly_stats(), args.output)
    elif args.action == 'severity-breakdown':
        print_output(client.finops_anomaly_severity_breakdown(args.severity), args.output)
    elif args.action == 'respond':
        print_output(client.finops_anomaly_respond(args.anomaly_id, args.action), args.output)
    elif args.action == 'alert-config':
        print_output(client.finops_anomaly_alert_config(args.channel, args.min_severity), args.output)
