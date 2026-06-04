"""CLI commands for Customer Experience features (NPS, sentiment, onboarding, comms, support)."""

from ..cli import get_client, print_output


def cmd_ticket_list(args):
    r = get_client().get('/api/v1/cx/tickets')
    data = r if isinstance(r, list) else r.get('tickets', r)
    print_output(data, args.output)

def cmd_ticket_get(args):
    r = get_client().get(f'/api/v1/cx/tickets/{args.ticket_id}')
    print_output(r, args.output)

def cmd_ticket_create(args):
    r = get_client().post('/api/v1/cx/tickets', {'subject': args.subject, 'description': args.description, 'customer_id': args.customer_id, 'priority': args.priority, 'tags': args.tags.split(',') if args.tags else []})
    print_output(r, args.output)

def cmd_ticket_update(args):
    r = get_client().put(f'/api/v1/cx/tickets/{args.ticket_id}', json={'status': args.status} if args.status else {})
    print_output(r, args.output)

def cmd_ticket_assign(args):
    r = get_client().post(f'/api/v1/cx/tickets/{args.ticket_id}/assign', {'assignee': args.assignee})
    print_output(r, args.output)

def cmd_ticket_comment(args):
    r = get_client().post(f'/api/v1/cx/tickets/{args.ticket_id}/comments', {'author': args.author, 'content': args.content, 'internal': args.internal})
    print_output(r, args.output)

def cmd_ticket_sla(args):
    r = get_client().get(f'/api/v1/cx/tickets/{args.ticket_id}/sla')
    print_output(r, args.output)

def cmd_ticket_overdue(args):
    r = get_client().get('/api/v1/cx/tickets/overdue')
    data = r if isinstance(r, list) else r.get('tickets', r)
    print_output(data, args.output)

def cmd_ticket_unassigned(args):
    r = get_client().get('/api/v1/cx/tickets/unassigned')
    data = r if isinstance(r, list) else r.get('tickets', r)
    print_output(data, args.output)

def cmd_ticket_stats(args):
    r = get_client().get('/api/v1/cx/tickets/stats')
    print_output(r, args.output)

def cmd_ticket_search(args):
    r = get_client().get('/api/v1/cx/tickets/search', params={'q': args.query})
    data = r if isinstance(r, list) else r.get('results', r)
    print_output(data, args.output)

def cmd_ticket_canned(args):
    r = get_client().get('/api/v1/cx/tickets/canned-responses')
    data = r if isinstance(r, list) else r.get('responses', r)
    print_output(data, args.output)

def cmd_nps_list(args):
    r = get_client().get('/api/v1/cx/nps/surveys')
    data = r if isinstance(r, list) else r.get('surveys', r)
    print_output(data, args.output)

def cmd_nps_score(args):
    r = get_client().get('/api/v1/cx/nps/score')
    print_output(r, args.output)

def cmd_nps_trend(args):
    r = get_client().get('/api/v1/cx/nps/trend')
    print_output(r, args.output)

def cmd_nps_detractors(args):
    r = get_client().get('/api/v1/cx/nps/detractors')
    data = r if isinstance(r, list) else r.get('detractors', r)
    print_output(data, args.output)

def cmd_nps_promoters(args):
    r = get_client().get('/api/v1/cx/nps/promoters')
    data = r if isinstance(r, list) else r.get('promoters', r)
    print_output(data, args.output)

def cmd_nps_send(args):
    r = get_client().post('/api/v1/cx/nps/send', {'survey_id': args.survey_id, 'customer_ids': args.customer_ids.split(',')})
    print_output(r, args.output)

def cmd_nps_respond(args):
    r = get_client().post(f'/api/v1/cx/nps/respond/{args.survey_id}', {'customer_id': args.customer_id, 'answers': {'nps_score': args.score}})
    print_output(r, args.output)

def cmd_sentiment_profile(args):
    r = get_client().get(f'/api/v1/cx/sentiment/{args.customer_id}')
    print_output(r, args.output)

def cmd_sentiment_trend(args):
    r = get_client().get(f'/api/v1/cx/sentiment/{args.customer_id}/trend')
    print_output(r, args.output)

def cmd_sentiment_alerts(args):
    r = get_client().get('/api/v1/cx/sentiment/alerts')
    data = r if isinstance(r, list) else r.get('alerts', r)
    print_output(data, args.output)

def cmd_sentiment_distribution(args):
    r = get_client().get('/api/v1/cx/sentiment/distribution')
    print_output(r, args.output)

def cmd_sentiment_search(args):
    r = get_client().get('/api/v1/cx/sentiment/search', params={'q': args.query})
    data = r if isinstance(r, list) else r.get('results', r)
    print_output(data, args.output)

def cmd_sentiment_record(args):
    r = get_client().post('/api/v1/cx/sentiment/record', {'customer_id': args.customer_id, 'channel': args.channel, 'content': args.content, 'score': args.score})
    print_output(r, args.output)

def cmd_onboard_list(args):
    r = get_client().get('/api/v1/cx/onboarding/sessions')
    data = r if isinstance(r, list) else r.get('sessions', r)
    print_output(data, args.output)

def cmd_onboard_get(args):
    r = get_client().get(f'/api/v1/cx/onboarding/sessions/{args.session_id}')
    print_output(r, args.output)

def cmd_onboard_create(args):
    r = get_client().post('/api/v1/cx/onboarding/sessions', {'customer_id': args.customer_id})
    print_output(r, args.output)

def cmd_onboard_complete_step(args):
    r = get_client().post(f'/api/v1/cx/onboarding/sessions/{args.session_id}/steps/{args.step_id}/complete')
    print_output(r, args.output)

def cmd_onboard_skip_step(args):
    r = get_client().post(f'/api/v1/cx/onboarding/sessions/{args.session_id}/steps/{args.step_id}/skip')
    print_output(r, args.output)

def cmd_onboard_stuck(args):
    r = get_client().get('/api/v1/cx/onboarding/sessions/stuck')
    data = r if isinstance(r, list) else r.get('sessions', r)
    print_output(data, args.output)

def cmd_onboard_stats(args):
    r = get_client().get('/api/v1/cx/onboarding/stats')
    print_output(r, args.output)

def cmd_onboard_summary(args):
    r = get_client().get('/api/v1/cx/onboarding/summary')
    print_output(r, args.output)

def cmd_comms_list(args):
    r = get_client().get('/api/v1/cx/communications')
    data = r if isinstance(r, list) else r.get('notifications', r)
    print_output(data, args.output)

def cmd_comms_send(args):
    r = get_client().post('/api/v1/cx/communications', {'notification_type': args.type, 'subject': args.subject, 'body': args.body, 'priority': args.priority, 'channels': args.channels.split(',') if args.channels else ['email']})
    print_output(r, args.output)

def cmd_comms_maintenance(args):
    r = get_client().get('/api/v1/cx/communications/maintenance')
    data = r if isinstance(r, list) else r.get('windows', r)
    print_output(data, args.output)

def cmd_comms_templates(args):
    r = get_client().get('/api/v1/cx/communications/templates')
    data = r if isinstance(r, list) else r.get('templates', r)
    print_output(data, args.output)

def cmd_comms_stats(args):
    r = get_client().get('/api/v1/cx/communications/stats')
    print_output(r, args.output)

def cmd_adoption_profile(args):
    r = get_client().get(f'/api/v1/cx/adoption/{args.customer_id}')
    print_output(r, args.output)

def cmd_adoption_features(args):
    r = get_client().get('/api/v1/cx/adoption/features')
    data = r if isinstance(r, list) else r.get('features', r)
    print_output(data, args.output)

def cmd_adoption_segments(args):
    r = get_client().get('/api/v1/cx/adoption/segments')
    print_output(r, args.output)

def cmd_adoption_funnel(args):
    r = get_client().get('/api/v1/cx/adoption/funnel')
    print_output(r, args.output)

def cmd_adoption_ranking(args):
    r = get_client().get('/api/v1/cx/adoption/ranking')
    data = r if isinstance(r, list) else r.get('ranking', r)
    print_output(data, args.output)

def cmd_health_profile(args):
    r = get_client().get(f'/api/v1/cx/health/{args.customer_id}')
    print_output(r, args.output)

def cmd_health_summary(args):
    r = get_client().get('/api/v1/cx/health/summary')
    print_output(r, args.output)

def cmd_health_at_risk(args):
    r = get_client().get('/api/v1/cx/health/at-risk')
    data = r if isinstance(r, list) else r.get('profiles', r)
    print_output(data, args.output)

def cmd_health_distribution(args):
    r = get_client().get('/api/v1/cx/health/distribution')
    print_output(r, args.output)

def cmd_kb_search(args):
    r = get_client().get('/api/v1/cx/knowledge-base/search', params={'q': args.query})
    data = r if isinstance(r, list) else r.get('results', r)
    print_output(data, args.output)

def cmd_kb_popular(args):
    r = get_client().get('/api/v1/cx/knowledge-base/popular')
    data = r if isinstance(r, list) else r.get('articles', r)
    print_output(data, args.output)

def cmd_kb_categories(args):
    r = get_client().get('/api/v1/cx/knowledge-base/categories')
    print_output(r, args.output)

def cmd_kb_stats(args):
    r = get_client().get('/api/v1/cx/knowledge-base/stats')
    print_output(r, args.output)

def cmd_automation_list(args):
    r = get_client().get('/api/v1/cx/automation/plays')
    data = r if isinstance(r, list) else r.get('plays', r)
    print_output(data, args.output)

def cmd_automation_create(args):
    r = get_client().post('/api/v1/cx/automation/plays', {'name': args.name, 'description': args.description, 'trigger_event': args.trigger})
    print_output(r, args.output)

def cmd_automation_executions(args):
    r = get_client().get('/api/v1/cx/automation/executions')
    data = r if isinstance(r, list) else r.get('executions', r)
    print_output(data, args.output)

def cmd_automation_failed(args):
    r = get_client().get('/api/v1/cx/automation/executions/failed')
    data = r if isinstance(r, list) else r.get('executions', r)
    print_output(data, args.output)

def cmd_automation_stats(args):
    r = get_client().get('/api/v1/cx/automation/stats')
    print_output(r, args.output)

def cmd_community_posts(args):
    r = get_client().get('/api/v1/cx/community/posts')
    data = r if isinstance(r, list) else r.get('posts', r)
    print_output(data, args.output)

def cmd_community_trending(args):
    r = get_client().get('/api/v1/cx/community/posts/trending')
    data = r if isinstance(r, list) else r.get('posts', r)
    print_output(data, args.output)

def cmd_community_categories(args):
    r = get_client().get('/api/v1/cx/community/categories')
    data = r if isinstance(r, list) else r.get('categories', r)
    print_output(data, args.output)

def cmd_community_search(args):
    r = get_client().get('/api/v1/cx/community/search', params={'q': args.query})
    data = r if isinstance(r, list) else r.get('results', r)
    print_output(data, args.output)

def cmd_community_leaderboard(args):
    r = get_client().get('/api/v1/cx/community/leaderboard')
    data = r if isinstance(r, list) else r.get('authors', r)
    print_output(data, args.output)
