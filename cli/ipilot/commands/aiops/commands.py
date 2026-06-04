"""CLI commands for AIOps features (61-70)."""

import json
from ..cli import get_client, print_output


def cmd_aiops_alert_correlate(args):
    result = get_client().post('/api/v1/aiops/alert-correlation/correlate', {'window_minutes': args.window})
    print_output(result, args.output)

def cmd_aiops_alert_sources(args):
    result = get_client().get('/api/v1/aiops/alert-correlation/sources')
    print_output(result, args.output)

def cmd_aiops_alert_suppress(args):
    result = get_client().post('/api/v1/aiops/alert-correlation/suppress', {'window_minutes': args.window})
    print_output(result, args.output)

def cmd_aiops_alert_stats(args):
    result = get_client().get('/api/v1/aiops/alert-correlation/stats')
    print_output(result, args.output)

def cmd_aiops_rca_analyze(args):
    result = get_client().post(f'/api/v1/aiops/rca/analyze/{args.incident_id}')
    print_output(result, args.output)

def cmd_aiops_rca_impact(args):
    result = get_client().get(f'/api/v1/aiops/rca/impact/{args.event_id}')
    print_output(result, args.output)

def cmd_aiops_rca_timeline(args):
    result = get_client().get('/api/v1/aiops/rca/timeline', params={'hours': args.hours})
    print_output(result, args.output)

def cmd_aiops_rca_patterns(args):
    result = get_client().get('/api/v1/aiops/rca/patterns')
    print_output(result, args.output)

def cmd_aiops_capacity_recommend(args):
    result = get_client().get('/api/v1/aiops/capacity/recommendations')
    print_output(result, args.output)

def cmd_aiops_capacity_simulate(args):
    result = get_client().post('/api/v1/aiops/capacity/simulate', {'scenario': args.scenario, 'peak_pct': args.peak})
    print_output(result, args.output)

def cmd_aiops_capacity_forecast(args):
    result = get_client().get('/api/v1/aiops/capacity/forecast')
    print_output(result, args.output)

def cmd_aiops_capacity_alerts(args):
    result = get_client().get('/api/v1/aiops/capacity/alerts')
    print_output(result, args.output)

def cmd_aiops_change_analyze(args):
    result = get_client().post('/api/v1/aiops/change-risk/analyze', {'change_id': args.change_id})
    print_output(result, args.output)

def cmd_aiops_change_trend(args):
    result = get_client().get('/api/v1/aiops/change-risk/trend', params={'days': args.days})
    print_output(result, args.output)

def cmd_aiops_change_ranking(args):
    result = get_client().get('/api/v1/aiops/change-risk/ranking')
    print_output(result, args.output)

def cmd_aiops_convo_health(args):
    result = get_client().get('/api/v1/aiops/conversational/slo-health')
    print_output(result, args.output)

def cmd_aiops_convo_feedback(args):
    result = get_client().get('/api/v1/aiops/conversational/feedback', params={'days': args.days})
    print_output(result, args.output)

def cmd_aiops_convo_popular(args):
    result = get_client().get('/api/v1/aiops/conversational/popular-commands')
    print_output(result, args.output)

def cmd_aiops_digital_monitors(args):
    result = get_client().get('/api/v1/aiops/digital-experience/monitors')
    print_output(result, args.output)

def cmd_aiops_digital_regression(args):
    result = get_client().get('/api/v1/aiops/digital-experience/regression', params={'days': args.days})
    print_output(result, args.output)

def cmd_aiops_digital_health(args):
    result = get_client().get('/api/v1/aiops/digital-experience/health')
    print_output(result, args.output)

def cmd_aiops_health_forecast(args):
    result = get_client().get('/api/v1/aiops/health-forecasting/forecast', params={'hours': args.hours})
    print_output(result, args.output)

def cmd_aiops_health_alerts(args):
    result = get_client().get('/api/v1/aiops/health-forecasting/alerts', params={'days': args.days})
    print_output(result, args.output)

def cmd_aiops_health_accuracy(args):
    result = get_client().get('/api/v1/aiops/health-forecasting/accuracy', params={'weeks': args.weeks})
    print_output(result, args.output)

def cmd_aiops_incident_remediate(args):
    result = get_client().post('/api/v1/aiops/incident-remediation/remediate', {'incident_id': args.incident_id, 'action': args.action})
    print_output(result, args.output)

def cmd_aiops_incident_analytics(args):
    result = get_client().get('/api/v1/aiops/incident-remediation/analytics', params={'days': args.days})
    print_output(result, args.output)

def cmd_aiops_incident_mttr(args):
    result = get_client().get('/api/v1/aiops/incident-remediation/mttr')
    print_output(result, args.output)

def cmd_aiops_ops_chat(args):
    result = get_client().post('/api/v1/aiops/ops-chatbot/chat', {'message': args.message})
    print_output(result, args.output)

def cmd_aiops_ops_tasks(args):
    result = get_client().get('/api/v1/aiops/ops-chatbot/tasks')
    print_output(result, args.output)

def cmd_aiops_ops_priorities(args):
    result = get_client().get('/api/v1/aiops/ops-chatbot/priorities')
    print_output(result, args.output)

def cmd_aiops_scaling_forecast(args):
    result = get_client().get('/api/v1/aiops/predictive-scaling/forecast', params={'resource_id': args.resource_id, 'metric': args.metric})
    print_output(result, args.output)

def cmd_aiops_scaling_alerts(args):
    result = get_client().get('/api/v1/aiops/predictive-scaling/alerts')
    print_output(result, args.output)

def cmd_aiops_scaling_recommend(args):
    result = get_client().get('/api/v1/aiops/predictive-scaling/recommendations')
    print_output(result, args.output)
