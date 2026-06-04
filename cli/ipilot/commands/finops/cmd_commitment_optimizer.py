"""Feature 21: Commitment Discount Optimizer CLI"""
import json
import sys
from ...client import ApiClient
from ...output import print_output

def register(subparsers):
    p = subparsers.add_parser('commitment', help='Commitment discount optimization')
    ps = p.add_subparsers(dest='action')
    ps.add_parser('list', help='List recommendations')
    ps.add_parser('summary', help='Commitment summary')
    imp = ps.add_parser('implement', help='Implement recommendation')
    imp.add_argument('rec_id', help='Recommendation ID')
    ps.add_parser('commitments', help='List active commitments')
    ps.add_parser('analyze', help='Analyze usage patterns')
    ps.add_parser('coverage', help='Coverage gaps')
    renew = ps.add_parser('renew', help='Renew commitment')
    renew.add_argument('rec_id', help='Recommendation or commitment ID')
    renew.add_argument('--term', default='1yr', help='Renewal term (1yr/3yr)')
    benchmark = ps.add_parser('benchmark', help='Benchmark providers')
    benchmark.add_argument('--provider', default='aws', help='Provider to benchmark')
    history = ps.add_parser('history', help='Show commitment history')
    history.add_argument('--days', type=int, default=30, help='History period in days')
    export = ps.add_parser('export', help='Export commitment data')
    export.add_argument('--format', default='json', help='Export format (json/csv)')
    roi = ps.add_parser('roi', help='Calculate commitment ROI')
    roi.add_argument('--upfront', type=float, required=True, help='Upfront cost')
    roi.add_argument('--monthly-savings', type=float, required=True, help='Monthly savings')
    roi.add_argument('--term', type=int, default=12, help='Term in months')
    plan = ps.add_parser('plan', help='Build commitment plan')
    plan.add_argument('--provider', default='aws', help='Cloud provider')
    plan.add_argument('--monthly', type=float, required=True, help='Monthly on-demand spend')
    return 'commitment'

def execute(args, client):
    if args.action == 'list':
        data = client.finops_commitment_list()
        print_output(data if isinstance(data, list) else data.get('recommendations', data), args.output)
    elif args.action == 'summary':
        print_output(client.finops_commitment_summary(), args.output)
    elif args.action == 'implement':
        print_output(client.finops_commitment_implement(args.rec_id), args.output)
    elif args.action == 'commitments':
        print_output(client.finops_commitment_commitments(), args.output)
    elif args.action == 'analyze':
        print_output(client.finops_commitment_analyze(), args.output)
    elif args.action == 'coverage':
        print_output(client.finops_commitment_coverage(), args.output)
    elif args.action == 'renew':
        print_output(client.finops_commitment_renew(args.rec_id, args.term), args.output)
    elif args.action == 'benchmark':
        print_output(client.finops_commitment_benchmark(args.provider), args.output)
    elif args.action == 'history':
        print_output(client.finops_commitment_history(args.days), args.output)
    elif args.action == 'export':
        print_output(client.finops_commitment_export(args.format), args.output)
    elif args.action == 'roi':
        print_output(client.finops_commitment_roi(args.upfront, args.monthly_savings, args.term), args.output)
    elif args.action == 'plan':
        print_output(client.finops_commitment_plan(args.provider, args.monthly), args.output)
