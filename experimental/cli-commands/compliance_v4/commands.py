"""CLI commands for compliance automation & audit 2.0 features (61-70)."""

from ..cli import get_client, print_output


def cmd_cc_status(args):
    r = get_client().get('/api/v1/compliance/postures')
    print_output(r if isinstance(r, list) else list(r.values()) if isinstance(r, dict) else r, args.output)

def cmd_cc_scan(args):
    r = get_client().post('/api/v1/compliance/scan', {'framework': args.framework} if args.framework else {})
    print_output(r, args.output)

def cmd_cc_alerts(args):
    r = get_client().get('/api/v1/compliance/alerts')
    data = r if isinstance(r, list) else r.get('alerts', r)
    print_output(data, args.output)

def cmd_cc_summary(args):
    r = get_client().get('/api/v1/compliance/summary')
    print_output(r, args.output)

def cmd_ec_list(args):
    r = get_client().get('/api/v1/compliance/evidence')
    print_output(r if isinstance(r, list) else r.get('evidence', r), args.output)

def cmd_ec_collect(args):
    r = get_client().post('/api/v1/compliance/evidence/collect', {'type': args.ev_type, 'control_id': args.control})
    print_output(r, args.output)

def cmd_ec_packages(args):
    r = get_client().get('/api/v1/compliance/evidence/packages')
    print_output(r if isinstance(r, list) else r.get('packages', r), args.output)

def cmd_ec_stats(args):
    r = get_client().get('/api/v1/compliance/evidence/stats')
    print_output(r, args.output)

def cmd_cac_list(args):
    r = get_client().get('/api/v1/compliance/cac/templates')
    print_output(r if isinstance(r, list) else r.get('templates', r), args.output)

def cmd_cac_evaluate(args):
    r = get_client().post('/api/v1/compliance/cac/evaluate', {'template_id': args.template_id})
    print_output(r, args.output)

def cmd_cac_templates(args):
    r = get_client().get('/api/v1/compliance/cac/templates')
    print_output(r if isinstance(r, list) else r.get('templates', r), args.output)

def cmd_cac_stats(args):
    r = get_client().get('/api/v1/compliance/cac/stats')
    print_output(r, args.output)

def cmd_ar_list(args):
    r = get_client().get('/api/v1/compliance/attestation/reports')
    print_output(r if isinstance(r, list) else r.get('reports', r), args.output)

def cmd_ar_generate(args):
    r = get_client().post('/api/v1/compliance/attestation/generate', {'framework': args.framework, 'period_start': args.start, 'period_end': args.end})
    print_output(r, args.output)

def cmd_ar_sign(args):
    r = get_client().post(f'/api/v1/compliance/attestation/sign/{args.report_id}', {'signed_by': args.signed_by})
    print_output(r, args.output)

def cmd_ar_stats(args):
    r = get_client().get('/api/v1/compliance/attestation/stats')
    print_output(r, args.output)

def cmd_vc_list(args):
    r = get_client().get('/api/v1/compliance/vendors')
    print_output(r if isinstance(r, list) else r.get('vendors', r), args.output)

def cmd_vc_register(args):
    r = get_client().post('/api/v1/compliance/vendors', {'name': args.name, 'category': args.category})
    print_output(r, args.output)

def cmd_vc_assess(args):
    r = get_client().post('/api/v1/compliance/vendors/assess', {'vendor_id': args.vendor_id})
    print_output(r, args.output)

def cmd_vc_risk(args):
    r = get_client().get('/api/v1/compliance/vendors/risk-summary')
    print_output(r, args.output)

def cmd_ri_changes(args):
    r = get_client().get('/api/v1/compliance/regulatory/changes')
    data = r if isinstance(r, list) else r.get('changes', r)
    print_output(data, args.output)

def cmd_ri_detect(args):
    r = get_client().post('/api/v1/compliance/regulatory/detect', {'regulation': args.regulation, 'jurisdiction': args.jurisdiction, 'impact_level': args.impact, 'title': args.title})
    print_output(r, args.output)

def cmd_ri_sources(args):
    r = get_client().get('/api/v1/compliance/regulatory/sources')
    print_output(r if isinstance(r, list) else r.get('sources', r), args.output)

def cmd_ri_stats(args):
    r = get_client().get('/api/v1/compliance/regulatory/stats')
    print_output(r, args.output)

def cmd_am_list(args):
    r = get_client().get('/api/v1/compliance/audit/schedules')
    print_output(r if isinstance(r, list) else r.get('schedules', r), args.output)

def cmd_am_schedule(args):
    r = get_client().post('/api/v1/compliance/audit/schedules', {'audit_type': args.audit_type, 'framework': args.framework, 'scheduled_date': args.date, 'assignee': args.assignee})
    print_output(r, args.output)

def cmd_am_rights(args):
    r = get_client().get('/api/v1/compliance/audit/rights')
    print_output(r if isinstance(r, list) else r.get('rights', r), args.output)

def cmd_am_stats(args):
    r = get_client().get('/api/v1/compliance/audit/stats')
    print_output(r, args.output)

def cmd_dr_list(args):
    r = get_client().get('/api/v1/compliance/residency/assets')
    print_output(r if isinstance(r, list) else r.get('assets', r), args.output)

def cmd_dr_register(args):
    r = get_client().post('/api/v1/compliance/residency/assets', {'asset_name': args.name, 'region': args.region, 'data_classification': args.classification, 'owner': args.owner})
    print_output(r, args.output)

def cmd_dr_check(args):
    r = get_client().post('/api/v1/compliance/residency/check', {'asset_id': args.asset_id, 'target_region': args.target_region})
    print_output(r, args.output)

def cmd_dr_summary(args):
    r = get_client().get('/api/v1/compliance/residency/summary')
    print_output(r, args.output)

def cmd_ct_modules(args):
    r = get_client().get('/api/v1/compliance/training/modules')
    print_output(r if isinstance(r, list) else r.get('modules', r), args.output)

def cmd_ct_assign(args):
    r = get_client().post('/api/v1/compliance/training/assign', {'user_id': args.user_id, 'module_id': args.module_id})
    print_output(r, args.output)

def cmd_ct_status(args):
    r = get_client().get('/api/v1/compliance/training/assignments')
    data = r if isinstance(r, list) else r.get('assignments', r)
    print_output(data, args.output)

def cmd_ct_stats(args):
    r = get_client().get('/api/v1/compliance/training/stats')
    print_output(r, args.output)

def cmd_ap_sessions(args):
    r = get_client().get('/api/v1/compliance/auditor/sessions')
    data = r if isinstance(r, list) else r.get('sessions', r)
    print_output(data, args.output)

def cmd_ap_evidence(args):
    r = get_client().get('/api/v1/compliance/auditor/evidence')
    print_output(r if isinstance(r, list) else r.get('evidence', r), args.output)

def cmd_ap_findings(args):
    r = get_client().get('/api/v1/compliance/auditor/findings')
    data = r if isinstance(r, list) else r.get('findings', r)
    print_output(data, args.output)

def cmd_ap_stats(args):
    r = get_client().get('/api/v1/compliance/auditor/stats')
    print_output(r, args.output)

def cmd_am_upcoming(args):
    r = get_client().get('/api/v1/compliance/audit/schedules/upcoming')
    data = r if isinstance(r, list) else r.get('upcoming', r)
    print_output(data, args.output)

def cmd_am_overdue(args):
    r = get_client().get('/api/v1/compliance/audit/schedules/overdue')
    data = r if isinstance(r, list) else r.get('overdue', r)
    print_output(data, args.output)

def cmd_am_workflow(args):
    r = get_client().get(f'/api/v1/compliance/audit/workflow/{args.audit_id}')
    print_output(r, args.output)

def cmd_am_report(args):
    r = get_client().get(f'/api/v1/compliance/audit/reports/{args.report_id}')
    print_output(r, args.output)

def cmd_am_register_right(args):
    r = get_client().post('/api/v1/compliance/audit/rights', {'audit_type': args.type, 'description': args.description})
    print_output(r, args.output)

def cmd_am_calendar(args):
    r = get_client().get('/api/v1/compliance/audit/calendar')
    data = r if isinstance(r, list) else r.get('events', r)
    print_output(data, args.output)

def cmd_ri_impact(args):
    r = get_client().get(f'/api/v1/compliance/regulatory/impact/{args.change_id}')
    print_output(r, args.output)

def cmd_ri_matrix(args):
    r = get_client().get('/api/v1/compliance/regulatory/matrix')
    print_output(r, args.output)

def cmd_ri_calendar(args):
    r = get_client().get('/api/v1/compliance/regulatory/calendar')
    data = r if isinstance(r, list) else r.get('events', r)
    print_output(data, args.output)

def cmd_ri_notify(args):
    r = get_client().post('/api/v1/compliance/regulatory/notify', {'change_id': args.change_id, 'channels': args.channels.split(',')})
    print_output(r, args.output)

def cmd_ri_pending(args):
    r = get_client().get('/api/v1/compliance/regulatory/changes/pending')
    data = r if isinstance(r, list) else r.get('pending', r)
    print_output(data, args.output)

def cmd_ri_search(args):
    r = get_client().get('/api/v1/compliance/regulatory/search', params={'q': args.query})
    print_output(r if isinstance(r, list) else r.get('results', r), args.output)

def cmd_vc_scorecard(args):
    r = get_client().get(f'/api/v1/compliance/vendors/{args.vendor_id}/scorecard')
    print_output(r, args.output)

def cmd_vc_assessments(args):
    r = get_client().get(f'/api/v1/compliance/vendors/{args.vendor_id}/assessments')
    data = r if isinstance(r, list) else r.get('assessments', r)
    print_output(data, args.output)

def cmd_vc_migrate_tier(args):
    r = get_client().post(f'/api/v1/compliance/vendors/{args.vendor_id}/tier', {'tier': args.tier})
    print_output(r, args.output)

def cmd_vc_categories(args):
    r = get_client().get('/api/v1/compliance/vendors/categories')
    data = r if isinstance(r, list) else r.get('categories', r)
    print_output(data, args.output)

def cmd_vc_discover(args):
    r = get_client().post('/api/v1/compliance/vendors/discover', {'cloud_provider': args.provider})
    print_output(r, args.output)

def cmd_vc_remediation(args):
    r = get_client().get(f'/api/v1/compliance/vendors/{args.vendor_id}/remediation')
    data = r if isinstance(r, list) else r.get('remediation', r)
    print_output(data, args.output)

def cmd_ar_approve(args):
    r = get_client().post(f'/api/v1/compliance/attestation/approve/{args.report_id}', {'approver': args.approver})
    print_output(r, args.output)

def cmd_ar_verify(args):
    r = get_client().post(f'/api/v1/compliance/attestation/verify/{args.report_id}')
    print_output(r, args.output)

def cmd_ar_compare(args):
    r = get_client().post('/api/v1/compliance/attestation/compare', {'report_ids': args.report_ids.split(',')})
    print_output(r, args.output)

def cmd_ar_schedule(args):
    r = get_client().post('/api/v1/compliance/attestation/schedule', {'framework': args.framework, 'period_start': args.start, 'period_end': args.end})
    print_output(r, args.output)

def cmd_ar_coverage(args):
    r = get_client().get('/api/v1/compliance/attestation/coverage')
    print_output(r, args.output)

def cmd_cac_create(args):
    r = get_client().post('/api/v1/compliance/cac/controls', {'name': args.name, 'framework': args.framework, 'severity': args.severity, 'description': args.description})
    print_output(r, args.output)

def cmd_cac_gap(args):
    r = get_client().get(f'/api/v1/compliance/cac/gap/{args.framework}')
    print_output(r, args.output)

def cmd_cac_test(args):
    r = get_client().post('/api/v1/compliance/cac/test', {'control_id': args.control_id, 'test_cases': args.test_cases.split(';')})
    print_output(r, args.output)

def cmd_cac_dry_run(args):
    r = get_client().post('/api/v1/compliance/cac/dry-run', {'control_id': args.control_id})
    print_output(r, args.output)

def cmd_cac_version(args):
    r = get_client().get(f'/api/v1/compliance/cac/controls/{args.control_id}/versions')
    data = r if isinstance(r, list) else r.get('versions', r)
    print_output(data, args.output)

def cmd_ec_auto_collect(args):
    r = get_client().post('/api/v1/compliance/evidence/auto-collect', {'framework': args.framework})
    print_output(r, args.output)

def cmd_ec_search(args):
    r = get_client().get('/api/v1/compliance/evidence/search', params={'q': args.query})
    print_output(r if isinstance(r, list) else r.get('results', r), args.output)

def cmd_ec_validate(args):
    r = get_client().post(f'/api/v1/compliance/evidence/{args.evidence_id}/validate')
    print_output(r, args.output)

def cmd_ec_package_create(args):
    r = get_client().post('/api/v1/compliance/evidence/packages', {'name': args.name, 'framework': args.framework, 'evidence_ids': args.evidence_ids.split(',')})
    print_output(r, args.output)

def cmd_ec_expired(args):
    r = get_client().get('/api/v1/compliance/evidence/expired')
    data = r if isinstance(r, list) else r.get('evidence', r)
    print_output(data, args.output)

def cmd_ec_custody(args):
    r = get_client().get(f'/api/v1/compliance/evidence/{args.evidence_id}/custody')
    data = r if isinstance(r, list) else r.get('chain', r)
    print_output(data, args.output)

def cmd_cc_remediate(args):
    r = get_client().post('/api/v1/compliance/continuous/remediate', {'finding_id': args.finding_id, 'action': args.action})
    print_output(r, args.output)

def cmd_cc_drift(args):
    r = get_client().get('/api/v1/compliance/continuous/drift')
    print_output(r, args.output)

def cmd_cc_compare(args):
    r = get_client().post('/api/v1/compliance/continuous/compare', {'checkpoint_a': args.checkpoint_a, 'checkpoint_b': args.checkpoint_b})
    print_output(r, args.output)

def cmd_cc_report(args):
    r = get_client().post('/api/v1/compliance/continuous/report', {'framework': args.framework, 'format': args.format})
    print_output(r, args.output)

def cmd_cc_schedule(args):
    r = get_client().post('/api/v1/compliance/continuous/schedule', {'interval': args.interval})
    print_output(r, args.output)

def cmd_cc_weakest(args):
    r = get_client().get('/api/v1/compliance/continuous/weakest-controls')
    data = r if isinstance(r, list) else r.get('controls', r)
    print_output(data, args.output)

def cmd_ap_engagement_create(args):
    r = get_client().post('/api/v1/compliance/auditor/engagements', {'framework': args.framework, 'auditor_name': args.name, 'scope': args.scope})
    print_output(r, args.output)

def cmd_ap_engagement_complete(args):
    r = get_client().post(f'/api/v1/compliance/auditor/engagements/{args.engagement_id}/complete')
    print_output(r, args.output)

def cmd_ap_finding_create(args):
    r = get_client().post('/api/v1/compliance/auditor/findings', {'engagement_id': args.engagement_id, 'title': args.title, 'severity': args.severity})
    print_output(r, args.output)

def cmd_ap_session_revoke(args):
    r = get_client().post(f'/api/v1/compliance/auditor/sessions/{args.session_id}/revoke')
    print_output(r, args.output)

def cmd_ap_session_extend(args):
    r = get_client().post(f'/api/v1/compliance/auditor/sessions/{args.session_id}/extend', {'hours': args.hours})
    print_output(r, args.output)

def cmd_ap_finding_update(args):
    r = get_client().put(f'/api/v1/compliance/auditor/findings/{args.finding_id}', {'status': args.status})
    print_output(r, args.output)

def cmd_ct_certifications(args):
    r = get_client().get('/api/v1/compliance/training/certifications')
    data = r if isinstance(r, list) else r.get('certifications', r)
    print_output(data, args.output)

def cmd_ct_expiring(args):
    r = get_client().get('/api/v1/compliance/training/expiring')
    data = r if isinstance(r, list) else r.get('expiring', r)
    print_output(data, args.output)

def cmd_ct_search(args):
    r = get_client().get('/api/v1/compliance/training/search', params={'q': args.query})
    print_output(r if isinstance(r, list) else r.get('results', r), args.output)

def cmd_ct_report(args):
    r = get_client().get('/api/v1/compliance/training/reports')
    print_output(r, args.output)

def cmd_ct_progress(args):
    r = get_client().get(f'/api/v1/compliance/training/progress/{args.user_id}')
    print_output(r, args.output)

def cmd_ct_batch_assign(args):
    r = get_client().post('/api/v1/compliance/training/batch-assign', {'user_ids': args.user_ids.split(','), 'module_ids': args.module_ids.split(',')})
    print_output(r, args.output)

def cmd_dr_flows(args):
    r = get_client().get('/api/v1/compliance/residency/flows')
    data = r if isinstance(r, list) else r.get('flows', r)
    print_output(data, args.output)

def cmd_dr_move(args):
    r = get_client().post('/api/v1/compliance/residency/move', {'asset_id': args.asset_id, 'source_region': args.source, 'destination_region': args.dest})
    print_output(r, args.output)

def cmd_dr_audit(args):
    r = get_client().get('/api/v1/compliance/residency/audit')
    print_output(r, args.output)

def cmd_dr_violations(args):
    r = get_client().get('/api/v1/compliance/residency/violations')
    data = r if isinstance(r, list) else r.get('violations', r)
    print_output(data, args.output)

def cmd_dr_compliance_report(args):
    r = get_client().get('/api/v1/compliance/residency/compliance-report')
    print_output(r, args.output)

def cmd_dr_asset_search(args):
    r = get_client().get('/api/v1/compliance/residency/search', params={'q': args.query})
    print_output(r if isinstance(r, list) else r.get('results', r), args.output)

import click

@click.group(name="compliance-v4")
def cli():
    """Compliance V4 management commands."""

@cli.command()
@click.option("--output", "-o", default="json")
def report(output):
    """Generate compliance report."""
    click.echo(f"Report in {output} format")

@cli.command()
@click.argument("control_id")
def evaluate(control_id):
    """Evaluate a specific control."""
    click.echo(f"Evaluating {control_id}")

@cli.command()
@click.option("--days", "-d", default=30)
def history(days):
    """Show compliance history."""
    click.echo(f"History for last {days} days")

