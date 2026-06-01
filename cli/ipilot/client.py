import json
import urllib.request
import urllib.error


class ApiClient:

    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip('/')
        self.token = token

    def _headers(self):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def _request(self, method, path, data=None):
        url = f'{self.base_url}/api/v1{path}'
        body = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf-8') if e.fp else str(e)
            try:
                return {'error': json.loads(msg).get('message', msg)}
            except json.JSONDecodeError:
                return {'error': msg}
        except urllib.error.URLError as e:
            return {'error': f'Connection failed: {e.reason}'}

    def login(self, api_key):
        return self._request('POST', '/auth/login', {'api_key': api_key})

    def logout(self):
        return self._request('POST', '/auth/logout')

    def list_servers(self):
        return self._request('GET', '/servers')

    def get_server(self, server_id):
        return self._request('GET', f'/servers/{server_id}')

    def create_server(self, name, server_type, memory=None):
        return self._request('POST', '/servers', {
            'name': name,
            'type': server_type,
            'memory': memory,
        })

    def delete_server(self, server_id):
        return self._request('DELETE', f'/servers/{server_id}')

    def server_status(self, server_id):
        return self._request('GET', f'/servers/{server_id}/status')

    def get_logs(self, server_id, lines=50, follow=False):
        params = f'?lines={lines}&follow={"true" if follow else "false"}'
        return self._request('GET', f'/servers/{server_id}/logs{params}')

    def list_backups(self, server_id=None):
        path = f'/servers/{server_id}/backups' if server_id else '/backups'
        return self._request('GET', path)

    def create_backup(self, server_id):
        return self._request('POST', f'/servers/{server_id}/backups')

    def deploy(self, server_id, branch):
        return self._request('POST', f'/servers/{server_id}/deploy', {'branch': branch})

    # === Edge & IoT API Methods ===

    def edge_list_devices(self, device_type=None, status=None):
        params = {}
        if device_type:
            params['device_type'] = device_type
        if status:
            params['status'] = status
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/edge/devices?{qs}' if qs else '/edge/devices')

    def edge_register_device(self, name, device_type, hardware_id):
        return self._request('POST', '/edge/devices', {
            'name': name, 'device_type': device_type, 'hardware_id': hardware_id,
        })

    def edge_device_status(self, device_id):
        return self._request('GET', f'/edge/devices/{device_id}')

    def edge_send_command(self, device_id, command):
        return self._request('POST', f'/edge/devices/{device_id}/command', {'command': command})

    def edge_create_backup(self, device_id):
        return self._request('POST', f'/edge/devices/{device_id}/backup')

    def fn_list_functions(self, device_id=None):
        path = f'/edge/functions?device_id={device_id}' if device_id else '/edge/functions'
        return self._request('GET', path)

    def fn_deploy_function(self, name, runtime, device_id, source, handler):
        return self._request('POST', '/edge/functions', {
            'name': name, 'runtime': runtime, 'device_id': device_id,
            'source': source, 'handler': handler,
        })

    def fn_invoke_function(self, func_id, payload=None):
        return self._request('POST', f'/edge/functions/{func_id}/invoke', payload or {})

    def ml_list_models(self, device_id=None):
        path = f'/edge/ml/models?device_id={device_id}' if device_id else '/edge/ml/models'
        return self._request('GET', path)

    def ml_deploy_model(self, name, model_format, device_id, version):
        return self._request('POST', '/edge/ml/models', {
            'name': name, 'model_format': model_format,
            'device_id': device_id, 'version': version,
        })

    def ml_run_inference(self, model_id, input_data=None):
        return self._request('POST', f'/edge/ml/models/{model_id}/infer', {'input': input_data or 'default'})

    def iot_generate_codes(self, count=10, ttl=24):
        return self._request('POST', '/iot/codes', {'count': count, 'ttl_hours': ttl})

    def iot_enroll_device(self, code, device_id):
        return self._request('POST', '/iot/enroll', {'code': code, 'device_id': device_id})

    def cdn_get_stats(self):
        return self._request('GET', '/edge/cdn/stats')

    def mesh_list_networks(self):
        return self._request('GET', '/mesh/networks')

    def mesh_create_network(self, name, mesh_type, subnet):
        return self._request('POST', '/mesh/networks', {
            'name': name, 'mesh_type': mesh_type, 'subnet': subnet,
        })

    def gw_list_gateways(self, status=None):
        path = f'/lorawan/gateways?status={status}' if status else '/lorawan/gateways'
        return self._request('GET', path)

    def pipeline_get_statistics(self):
        return self._request('GET', '/iot/pipeline/stats')

    # === Green Computing API Methods ===

    def energy_get_current(self):
        return self._request('GET', '/energy/current')

    def energy_get_history(self, server_id=None, hours=24):
        path = f'/energy/history?hours={hours}'
        if server_id:
            path += f'&server_id={server_id}'
        return self._request('GET', path)

    def energy_get_summary(self, period='daily'):
        return self._request('GET', f'/energy/summary?period={period}')

    def carbon_get_current(self):
        return self._request('GET', '/carbon/current')

    def carbon_get_history(self):
        return self._request('GET', '/carbon/history')

    def green_get_forecast(self):
        return self._request('GET', '/green/forecast')

    def green_list_jobs(self, status=None):
        path = f'/green/jobs?status={status}' if status else '/green/jobs'
        return self._request('GET', path)

    def green_add_job(self, name, command, urgency='normal'):
        return self._request('POST', '/green/jobs', {
            'name': name, 'command': command, 'urgency': urgency,
        })

    def green_savings_report(self):
        return self._request('GET', '/green/report')

    def reclaim_list_resources(self, resource_type=None):
        path = f'/reclaim/resources?type={resource_type}' if resource_type else '/reclaim/resources'
        return self._request('GET', path)

    def reclaim_scan(self):
        return self._request('POST', '/reclaim/scan')

    def reclaim_report(self):
        return self._request('GET', '/reclaim/report')

    def shutdown_list_policies(self):
        return self._request('GET', '/shutdown/policies')

    def shutdown_create_policy(self, name, tags, shutdown_hours):
        tag_list = [t.strip() for t in tags.split(',')]
        hours = [int(h.strip()) for h in shutdown_hours.split(',')]
        return self._request('POST', '/shutdown/policies', {
            'name': name, 'tags': tag_list, 'shutdown_hours': hours,
        })

    def shutdown_savings(self):
        return self._request('GET', '/shutdown/savings')

    def hardware_list_assets(self, asset_type=None):
        path = f'/hardware/assets?type={asset_type}' if asset_type else '/hardware/assets'
        return self._request('GET', path)

    def hardware_add_asset(self, asset_type, manufacturer, model, serial):
        return self._request('POST', '/hardware/assets', {
            'asset_type': asset_type, 'manufacturer': manufacturer,
            'model': model, 'serial_number': serial,
        })

    def pue_get_current(self):
        return self._request('GET', '/pue/current')

    def pue_get_history(self, hours=168):
        return self._request('GET', f'/pue/history?hours={hours}')

    def provider_get_rankings(self):
        return self._request('GET', '/provider/rankings')

    def offset_calculate(self, energy_kwh, project_type='reforestation'):
        return self._request('POST', '/offset/calculate', {
            'energy_kwh': energy_kwh, 'project_type': project_type,
        })

    def offset_purchase(self, quote_id):
        return self._request('POST', '/offset/purchase', {'quote_id': quote_id})

    def offset_list_certificates(self):
        return self._request('GET', '/offset/certificates')

    def efficiency_get_score(self, server_id):
        return self._request('GET', f'/efficiency/servers/{server_id}/score')

    def efficiency_get_recommendations(self, server_id):
        return self._request('GET', f'/efficiency/servers/{server_id}/recommendations')

    # === v3 Identity & Access API Methods ===

    def oidc_list_clients(self):
        return self._request('GET', '/identity/oidc/clients')

    def oidc_register_client(self, name, redirect_uris, client_type='confidential'):
        return self._request('POST', '/identity/oidc/clients', {
            'client_name': name, 'redirect_uris': redirect_uris, 'client_type': client_type,
        })

    def oidc_delete_client(self, client_id):
        return self._request('DELETE', f'/identity/oidc/clients/{client_id}')

    def webauthn_list_credentials(self, user_id):
        return self._request('GET', f'/identity/webauthn/credentials?user_id={user_id}')

    def webauthn_remove_credential(self, credential_id):
        return self._request('DELETE', f'/identity/webauthn/credentials/{credential_id}')

    def session_list_active(self, user_id):
        return self._request('GET', f'/identity/sessions?user_id={user_id}')

    def session_revoke(self, session_id):
        return self._request('POST', f'/identity/sessions/{session_id}/revoke')

    def pam_list_requests(self, user_id=None, status=None):
        params = {}
        if user_id: params['user_id'] = user_id
        if status: params['status'] = status
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/identity/pam/requests?{qs}' if qs else '/identity/pam/requests')

    def pam_create_request(self, user_id, resource, role, reason, duration=3600):
        return self._request('POST', '/identity/pam/requests', {
            'user_id': user_id, 'resource': resource, 'role': role,
            'reason': reason, 'duration': duration,
        })

    def pam_approve_request(self, request_id, approver_id):
        return self._request('POST', f'/identity/pam/requests/{request_id}/approve', {'approver_id': approver_id})

    def pam_deny_request(self, request_id, approver_id):
        return self._request('POST', f'/identity/pam/requests/{request_id}/deny', {'approver_id': approver_id})

    def breach_list(self):
        return self._request('GET', '/identity/breaches')

    def breach_report(self, description, data_types, affected_users=0):
        return self._request('POST', '/identity/breaches', {
            'description': description, 'affected_data_types': data_types,
            'affected_users_count': affected_users,
        })

    # === v3 Governance API Methods ===

    def policy_list(self, category=None):
        path = f'/governance/policies?category={category}' if category else '/governance/policies'
        return self._request('GET', path)

    def policy_create(self, name, description, category='general'):
        return self._request('POST', '/governance/policies', {
            'name': name, 'description': description, 'category': category, 'rules': [],
        })

    def policy_evaluate(self, resource, action, context=None):
        return self._request('POST', '/governance/policies/evaluate', {
            'resource': resource, 'action': action, 'context': context or {},
        })

    def compliance_run_scan(self, benchmark='cis_docker'):
        return self._request('POST', '/governance/compliance/scan', {'benchmark': benchmark})

    def compliance_get_report(self, scan_id):
        return self._request('GET', f'/governance/compliance/scans/{scan_id}')

    def compliance_list_checks(self, benchmark='cis_docker'):
        return self._request('GET', f'/governance/compliance/checks?benchmark={benchmark}')

    def audit_get_anomalies(self, threshold=None):
        path = f'/governance/audit/anomalies?threshold={threshold}' if threshold else '/governance/audit/anomalies'
        return self._request('GET', path)

    def audit_get_trend(self, user_id):
        return self._request('GET', f'/governance/audit/trend/{user_id}')

    def audit_get_summary(self):
        return self._request('GET', '/governance/audit/summary')

    def classify_scan_text(self, text):
        return self._request('POST', '/governance/classify/scan', {'text': text})

    def classify_get_inventory(self):
        return self._request('GET', '/governance/classify/inventory')

    def vendor_list(self):
        return self._request('GET', '/governance/vendors')

    def vendor_create(self, name, domain, category='saas'):
        return self._request('POST', '/governance/vendors', {
            'name': name, 'domain': domain, 'category': category,
        })

    def vendor_create_assessment(self, vendor_id, questionnaire_type='sig'):
        return self._request('POST', f'/governance/vendors/{vendor_id}/assessments', {
            'questionnaire_type': questionnaire_type,
        })

    # === v3 Orchestration API Methods ===

    def workflow_list(self):
        return self._request('GET', '/orchestration/workflows')

    def workflow_create(self, name, description):
        return self._request('POST', '/orchestration/workflows', {
            'name': name, 'description': description, 'nodes': [], 'edges': [],
        })

    def workflow_execute(self, workflow_id):
        return self._request('POST', f'/orchestration/workflows/{workflow_id}/execute', {
            'trigger_data': {'source': 'cli', 'timestamp': __import__('datetime').datetime.utcnow().isoformat()},
        })

    def infra_pipeline_list(self):
        return self._request('GET', '/orchestration/pipelines')

    def infra_pipeline_run(self, pipeline_id, branch='main'):
        return self._request('POST', f'/orchestration/pipelines/{pipeline_id}/run', {
            'triggered_by': 'cli', 'branch': branch,
        })

    def drift_run_scan(self):
        return self._request('POST', '/orchestration/drift/scan')

    def drift_list_scans(self):
        return self._request('GET', '/orchestration/drift/scans')

    def quota_list(self):
        return self._request('GET', '/orchestration/quotas')

    def quota_check(self, entity_type, entity_id, resources):
        return self._request('POST', '/orchestration/quotas/check', {
            'entity_type': entity_type, 'entity_id': entity_id, 'resources': resources,
        })

    def remediation_list_rules(self):
        return self._request('GET', '/orchestration/remediation/rules')

    def remediation_get_history(self):
        return self._request('GET', '/orchestration/remediation/history')

    def maintenance_list_windows(self):
        return self._request('GET', '/orchestration/maintenance/windows')

    def maintenance_schedule(self, name, start_time, end_time, systems):
        return self._request('POST', '/orchestration/maintenance/windows', {
            'name': name, 'start_time': start_time, 'end_time': end_time,
            'affected_systems': systems,
        })

    def runbook_list_templates(self):
        return self._request('GET', '/orchestration/runbook-templates')

    def runbook_instantiate(self, template_id, variables=None):
        return self._request('POST', f'/orchestration/runbook-templates/{template_id}/instantiate', {
            'variables': variables or {},
        })

    def chaos_list_experiments(self):
        return self._request('GET', '/orchestration/chaos/experiments')

    def chaos_create_experiment(self, name, target):
        return self._request('POST', '/orchestration/chaos/experiments', {
            'name': name, 'target': target, 'faults': [],
        })

    def chaos_run_experiment(self, experiment_id):
        return self._request('POST', f'/orchestration/chaos/experiments/{experiment_id}/run')

    def chaos_stop_experiment(self, experiment_id):
        return self._request('POST', f'/orchestration/chaos/experiments/{experiment_id}/stop')

    def chaos_list_faults(self):
        return self._request('GET', '/orchestration/chaos/fault-types')

    def healing_get_status(self):
        return self._request('GET', '/orchestration/healing/status')

    def healing_get_history(self):
        return self._request('GET', '/orchestration/healing/history')

    def healing_retrain(self):
        return self._request('POST', '/orchestration/healing/retrain')

    # === v3 Networking API Methods ===

    def sdwan_status(self):
        return self._request('GET', '/networking/sdwan/status')

    def sdwan_list_apps(self):
        return self._request('GET', '/networking/sdwan/apps')

    def sdwan_create_app(self, name, provider, bandwidth):
        return self._request('POST', '/networking/sdwan/apps', {
            'name': name, 'provider': provider, 'bandwidth': bandwidth,
        })

    def sdwan_delete_app(self, app_id):
        return self._request('DELETE', f'/networking/sdwan/apps/{app_id}')

    def sdwan_toggle(self, app_id):
        return self._request('POST', f'/networking/sdwan/apps/{app_id}/toggle')

    def vpn_list_configs(self):
        return self._request('GET', '/networking/vpn/configs')

    def vpn_create_config(self, name, server, port, protocol):
        return self._request('POST', '/networking/vpn/configs', {
            'name': name, 'server': server, 'port': port, 'protocol': protocol,
        })

    def vpn_delete_config(self, config_id):
        return self._request('DELETE', f'/networking/vpn/configs/{config_id}')

    def vpn_status(self):
        return self._request('GET', '/networking/vpn/status')

    def dns_list_zones(self):
        return self._request('GET', '/networking/dns/zones')

    def dns_create_zone(self, domain, ttl):
        return self._request('POST', '/networking/dns/zones', {
            'domain': domain, 'ttl': ttl,
        })

    def dns_delete_zone(self, zone_id):
        return self._request('DELETE', f'/networking/dns/zones/{zone_id}')

    def dns_list_records(self, zone_id):
        return self._request('GET', f'/networking/dns/zones/{zone_id}/records')

    def dns_create_record(self, zone_id, name, record_type, value, ttl):
        return self._request('POST', f'/networking/dns/zones/{zone_id}/records', {
            'name': name, 'type': record_type, 'value': value, 'ttl': ttl,
        })

    def dns_delete_record(self, zone_id, record_id):
        return self._request('DELETE', f'/networking/dns/zones/{zone_id}/records/{record_id}')

    def bgp_list_sessions(self):
        return self._request('GET', '/networking/bgp/sessions')

    def bgp_create_session(self, name, peer_as, peer_ip):
        return self._request('POST', '/networking/bgp/sessions', {
            'name': name, 'peer_as': peer_as, 'peer_ip': peer_ip,
        })

    def bgp_delete_session(self, session_id):
        return self._request('DELETE', f'/networking/bgp/sessions/{session_id}')

    def bgp_routes(self):
        return self._request('GET', '/networking/bgp/routes')

    def proxy_list_rules(self):
        return self._request('GET', '/networking/proxy/rules')

    def proxy_create_rule(self, domain, target, tls):
        return self._request('POST', '/networking/proxy/rules', {
            'domain': domain, 'target': target, 'tls_enabled': tls,
        })

    def proxy_delete_rule(self, rule_id):
        return self._request('DELETE', f'/networking/proxy/rules/{rule_id}')

    def proxy_toggle(self, rule_id):
        return self._request('POST', f'/networking/proxy/rules/{rule_id}/toggle')

    def seg_list_segments(self):
        return self._request('GET', '/networking/segments')

    def seg_create_segment(self, name, cidr, env):
        return self._request('POST', '/networking/segments', {
            'name': name, 'cidr': cidr, 'environment': env,
        })

    def seg_delete_segment(self, segment_id):
        return self._request('DELETE', f'/networking/segments/{segment_id}')

    def cap_list_captures(self):
        return self._request('GET', '/networking/captures')

    def cap_start_capture(self, interface, duration, filter_expr):
        return self._request('POST', '/networking/captures', {
            'interface': interface, 'duration': duration, 'filter': filter_expr,
        })

    def cap_stop_capture(self, capture_id):
        return self._request('POST', f'/networking/captures/{capture_id}/stop')

    def dnsfilter_status(self):
        return self._request('GET', '/networking/dnsfilter/status')

    def dnsfilter_list_rules(self):
        return self._request('GET', '/networking/dnsfilter/rules')

    def dnsfilter_create_rule(self, domain, action):
        return self._request('POST', '/networking/dnsfilter/rules', {
            'domain': domain, 'action': action,
        })

    def dnsfilter_delete_rule(self, rule_id):
        return self._request('DELETE', f'/networking/dnsfilter/rules/{rule_id}')

    def dhcp_leases(self):
        return self._request('GET', '/networking/dhcp/leases')

    def cost_get_costs(self):
        return self._request('GET', '/networking/costs')

    def cost_set_budget(self, monthly_budget):
        return self._request('POST', '/networking/costs/budget', {
            'monthly_budget': monthly_budget,
        })

    def cell_list_networks(self):
        return self._request('GET', '/networking/cellular/networks')

    def cell_register_network(self, name, provider, apn):
        return self._request('POST', '/networking/cellular/networks', {
            'name': name, 'provider': provider, 'apn': apn,
        })

    def cell_delete_network(self, network_id):
        return self._request('DELETE', f'/networking/cellular/networks/{network_id}')

    def cell_status(self):
        return self._request('GET', '/networking/cellular/status')

    def cell_list_sims(self):
        return self._request('GET', '/networking/cellular/sims')

    def cell_activate_sim(self, sim_id):
        return self._request('POST', f'/networking/cellular/sims/{sim_id}/activate')

    def cell_deactivate_sim(self, sim_id):
        return self._request('POST', f'/networking/cellular/sims/{sim_id}/deactivate')

    # === v3 Marketplace API Methods ===

    def trade_list(self, status=None):
        path = f'/marketplace/trades?status={status}' if status else '/marketplace/trades'
        return self._request('GET', path)

    def trade_create(self, resource_type, quantity, price, unit):
        return self._request('POST', '/marketplace/trades', {
            'resource_type': resource_type, 'quantity': quantity,
            'price': price, 'unit': unit,
        })

    def trade_accept(self, trade_id):
        return self._request('POST', f'/marketplace/trades/{trade_id}/accept')

    def trade_cancel(self, trade_id):
        return self._request('DELETE', f'/marketplace/trades/{trade_id}')

    def appmarket_list(self, category=None):
        path = f'/marketplace/apps?category={category}' if category else '/marketplace/apps'
        return self._request('GET', path)

    def appmarket_install(self, app_id, target_server=None):
        return self._request('POST', f'/marketplace/apps/{app_id}/install', {
            'target_server_id': target_server,
        })

    def appmarket_installations(self):
        return self._request('GET', '/marketplace/apps/installations')

    def ppu_metrics(self):
        return self._request('GET', '/marketplace/ppu/metrics')

    def ppu_usage(self):
        return self._request('GET', '/marketplace/ppu/usage')

    def ppu_set_budget(self, monthly_budget):
        return self._request('POST', '/marketplace/ppu/budget', {
            'monthly_budget': monthly_budget,
        })

    def reseller_list(self):
        return self._request('GET', '/marketplace/resellers')

    def reseller_create(self, name, email, commission):
        return self._request('POST', '/marketplace/resellers', {
            'name': name, 'email': email, 'commission_rate': commission,
        })

    def reseller_delete(self, reseller_id):
        return self._request('DELETE', f'/marketplace/resellers/{reseller_id}')

    def reseller_analytics(self, reseller_id):
        return self._request('GET', f'/marketplace/resellers/{reseller_id}/analytics')

    def whitelabel_settings(self):
        return self._request('GET', '/marketplace/whitelabel')

    def sla_list(self):
        return self._request('GET', '/marketplace/slas')

    def sla_create(self, name, uptime, credit_rate):
        return self._request('POST', '/marketplace/slas', {
            'name': name, 'uptime_target': uptime, 'credit_rate': credit_rate,
        })

    def sla_delete(self, sla_id):
        return self._request('DELETE', f'/marketplace/slas/{sla_id}')

    def sla_status(self, sla_id):
        return self._request('GET', f'/marketplace/slas/{sla_id}/status')

    def credit_list(self):
        return self._request('GET', '/marketplace/credits')

    def credit_issue(self, customer_id, amount, reason):
        return self._request('POST', '/marketplace/credits', {
            'customer_id': customer_id, 'amount': amount, 'reason': reason,
        })

    def crypto_wallets(self):
        return self._request('GET', '/marketplace/crypto/wallets')

    def crypto_create_wallet(self, currency, label):
        return self._request('POST', '/marketplace/crypto/wallets', {
            'currency': currency, 'label': label,
        })

    def crypto_transactions(self):
        return self._request('GET', '/marketplace/crypto/transactions')

    def crypto_rates(self):
        return self._request('GET', '/marketplace/crypto/rates')

    def plans_list(self):
        return self._request('GET', '/marketplace/plans')

    def plans_create(self, name, price, billing_cycle, features):
        feature_list = [f.strip() for f in features.split(',')]
        return self._request('POST', '/marketplace/plans', {
            'name': name, 'price': price,
            'billing_cycle': billing_cycle, 'features': feature_list,
        })

    def plans_delete(self, plan_id):
        return self._request('DELETE', f'/marketplace/plans/{plan_id}')

    def plans_subscriptions(self):
        return self._request('GET', '/marketplace/plans/subscriptions')

    def reco_list(self):
        return self._request('GET', '/marketplace/recommendations')

    def reco_summary(self):
        return self._request('GET', '/marketplace/recommendations/summary')

    def reco_implement(self, reco_id):
        return self._request('POST', f'/marketplace/recommendations/{reco_id}/implement')

    def reco_dismiss(self, reco_id):
        return self._request('POST', f'/marketplace/recommendations/{reco_id}/dismiss')

    def tax_rates(self):
        return self._request('GET', '/marketplace/tax/rates')

    def tax_invoices(self):
        return self._request('GET', '/marketplace/tax/invoices')

    def tax_generate_invoice(self):
        return self._request('POST', '/marketplace/tax/invoices/generate')

    def tax_mark_paid(self, invoice_id):
        return self._request('POST', f'/marketplace/tax/invoices/{invoice_id}/pay')

    def tax_summary(self):
        return self._request('GET', '/marketplace/tax/summary')

    def tax_file_report(self):
        return self._request('POST', '/marketplace/tax/file')

    def loyalty_status(self):
        return self._request('GET', '/marketplace/loyalty/status')

    def loyalty_badges(self):
        return self._request('GET', '/marketplace/loyalty/badges')

    def loyalty_rewards(self):
        return self._request('GET', '/marketplace/loyalty/rewards')

    def loyalty_redeem(self, reward_id):
        return self._request('POST', f'/marketplace/loyalty/rewards/{reward_id}/redeem')

    def loyalty_leaderboard(self):
        return self._request('GET', '/marketplace/loyalty/leaderboard')
