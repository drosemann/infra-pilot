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

    # === v4 Platform Engineering API Methods ===

    def devportal_list_components(self, domain=None):
        path = '/v4/platform-engineering/portal/components'
        if domain:
            path += f'?domain={domain}'
        return self._request('GET', path)

    def devportal_register_component(self, name, domain, description, owner):
        return self._request('POST', '/v4/platform-engineering/portal/components', {
            'name': name, 'domain': domain, 'description': description, 'owner': owner,
        })

    def devportal_get_component(self, component_id):
        return self._request('GET', f'/v4/platform-engineering/portal/components/{component_id}')

    def devportal_summary(self):
        return self._request('GET', '/v4/platform-engineering/portal/summary')

    def scaffold_list_templates(self):
        return self._request('GET', '/v4/platform-engineering/scaffold/templates')

    def scaffold_generate(self, template_id, project_name, params=None):
        return self._request('POST', f'/v4/platform-engineering/scaffold/templates/{template_id}/generate', {
            'project_name': project_name, 'params': params or {},
        })

    def scaffold_status(self, generation_id):
        return self._request('GET', f'/v4/platform-engineering/scaffold/generations/{generation_id}')

    def scaffold_complete_step(self, generation_id, step_name, outputs=None):
        return self._request('POST', f'/v4/platform-engineering/scaffold/generations/{generation_id}/steps/{step_name}/complete', {
            'outputs': outputs or {},
        })

    def catalog_list_services(self):
        return self._request('GET', '/v4/platform-engineering/catalog/services')

    def catalog_register_service(self, name, domain, description, owner):
        return self._request('POST', '/v4/platform-engineering/catalog/services', {
            'name': name, 'domain': domain, 'description': description, 'owner': owner,
        })

    def catalog_get_service(self, service_id):
        return self._request('GET', f'/v4/platform-engineering/catalog/services/{service_id}')

    def catalog_score_service(self, service_id):
        return self._request('POST', f'/v4/platform-engineering/catalog/services/{service_id}/score')

    def catalog_summary(self):
        return self._request('GET', '/v4/platform-engineering/catalog/summary')

    def scorecards_list(self):
        return self._request('GET', '/v4/platform-engineering/scorecards')

    def scorecards_create(self, name, team, dora=False):
        return self._request('POST', '/v4/platform-engineering/scorecards', {
            'name': name, 'team': team, 'include_dora': dora,
        })

    def scorecards_get(self, scorecard_id):
        return self._request('GET', f'/v4/platform-engineering/scorecards/{scorecard_id}')

    def scorecards_update_metric(self, scorecard_id, metric, value):
        return self._request('PATCH', f'/v4/platform-engineering/scorecards/{scorecard_id}/metrics/{metric}', {
            'value': value,
        })

    def scorecards_summary(self):
        return self._request('GET', '/v4/platform-engineering/scorecards/summary')

    def templatereg_list(self):
        return self._request('GET', '/v4/platform-engineering/templates')

    def templatereg_create(self, name, category, params_schema=None):
        return self._request('POST', '/v4/platform-engineering/templates', {
            'name': name, 'category': category, 'params_schema': params_schema or {},
        })

    def templatereg_get(self, template_id):
        return self._request('GET', f'/v4/platform-engineering/templates/{template_id}')

    def templatereg_use(self, template_id):
        return self._request('POST', f'/v4/platform-engineering/templates/{template_id}/use')

    def templatereg_summary(self):
        return self._request('GET', '/v4/platform-engineering/templates/summary')

    def techdebt_list(self, severity=None):
        path = '/v4/platform-engineering/tech-debt'
        if severity:
            path += f'?severity={severity}'
        return self._request('GET', path)

    def techdebt_report(self, title, severity, effort_hours, area):
        return self._request('POST', '/v4/platform-engineering/tech-debt', {
            'title': title, 'severity': severity, 'effort_hours': effort_hours, 'area': area,
        })

    def techdebt_get(self, debt_id):
        return self._request('GET', f'/v4/platform-engineering/tech-debt/{debt_id}')

    def techdebt_fix(self, debt_id):
        return self._request('POST', f'/v4/platform-engineering/tech-debt/{debt_id}/fix')

    def techdebt_summary(self):
        return self._request('GET', '/v4/platform-engineering/tech-debt/summary')

    def environments_list(self, status=None):
        path = '/v4/platform-engineering/environments'
        if status:
            path += f'?status={status}'
        return self._request('GET', path)

    def environments_create(self, name, template, ttl, branch):
        return self._request('POST', '/v4/platform-engineering/environments', {
            'name': name, 'template': template, 'ttl_hours': ttl, 'branch': branch,
        })

    def environments_get(self, env_id):
        return self._request('GET', f'/v4/platform-engineering/environments/{env_id}')

    def environments_delete(self, env_id):
        return self._request('DELETE', f'/v4/platform-engineering/environments/{env_id}')

    def environments_extend(self, env_id, hours):
        return self._request('POST', f'/v4/platform-engineering/environments/{env_id}/extend', {
            'additional_hours': hours,
        })

    def environments_summary(self):
        return self._request('GET', '/v4/platform-engineering/environments/summary')

    def apicatalog_list(self):
        return self._request('GET', '/v4/platform-engineering/api-catalog')

    def apicatalog_register(self, name, version, spec_content):
        return self._request('POST', '/v4/platform-engineering/api-catalog', {
            'name': name, 'version': version, 'spec': spec_content,
        })

    def apicatalog_get(self, api_id):
        return self._request('GET', f'/v4/platform-engineering/api-catalog/{api_id}')

    def apicatalog_summary(self):
        return self._request('GET', '/v4/platform-engineering/api-catalog/summary')

    def docgen_list(self):
        return self._request('GET', '/v4/platform-engineering/docs')

    def docgen_generate(self, title, doc_type):
        return self._request('POST', '/v4/platform-engineering/docs', {
            'title': title, 'doc_type': doc_type,
        })

    def docgen_get(self, doc_id):
        return self._request('GET', f'/v4/platform-engineering/docs/{doc_id}')

    def docgen_summary(self):
        return self._request('GET', '/v4/platform-engineering/docs/summary')

    def pulse_list_surveys(self):
        return self._request('GET', '/v4/platform-engineering/pulse/surveys')

    def pulse_create_survey(self, title, questions):
        return self._request('POST', '/v4/platform-engineering/pulse/surveys', {
            'title': title, 'questions': questions,
        })

    def pulse_respond(self, survey_id, respondent, answers):
        return self._request('POST', f'/v4/platform-engineering/pulse/surveys/{survey_id}/respond', {
            'respondent': respondent, 'answers': answers,
        })

    def pulse_results(self, survey_id):
        return self._request('GET', f'/v4/platform-engineering/pulse/surveys/{survey_id}/results')

    def pulse_summary(self):
        return self._request('GET', '/v4/platform-engineering/pulse/summary')

    # === v4 Customer Experience API Methods ===

    def cx_list_health_profiles(self, risk_level=None, min_score=None):
        params = {}
        if risk_level: params['risk_level'] = risk_level
        if min_score is not None: params['min_score'] = min_score
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/health/profile?{qs}' if qs else '/cx/health/profile')

    def cx_get_health_profile(self, customer_id):
        return self._request('GET', f'/cx/health/profile/{customer_id}')

    def cx_compute_health(self, customer_id, data):
        return self._request('POST', f'/cx/health/compute/{customer_id}', data)

    def cx_get_health_history(self, customer_id, days=30):
        return self._request('GET', f'/cx/health/history/{customer_id}?days={days}')

    def cx_get_health_stats(self):
        return self._request('GET', '/cx/health/stats')

    def cx_list_tickets(self, status=None, priority=None, customer_id=None, assigned_to=None, search=None, limit=50, offset=0):
        params = {}
        if status: params['status'] = status
        if priority: params['priority'] = priority
        if customer_id: params['customer_id'] = customer_id
        if assigned_to: params['assigned_to'] = assigned_to
        if search: params['search'] = search
        params['limit'] = limit
        params['offset'] = offset
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/tickets?{qs}')

    def cx_create_ticket(self, subject, description, customer_id, customer_name='', customer_email='', priority='medium', channel='web', category=None, tags=None):
        return self._request('POST', '/cx/tickets', {
            'subject': subject, 'description': description, 'customer_id': customer_id,
            'customer_name': customer_name, 'customer_email': customer_email,
            'priority': priority, 'channel': channel, 'category': category, 'tags': tags,
        })

    def cx_get_ticket(self, ticket_id):
        return self._request('GET', f'/cx/tickets/{ticket_id}')

    def cx_update_ticket_status(self, ticket_id, status, agent_id=None):
        return self._request('PATCH', f'/cx/tickets/{ticket_id}/status', {'status': status, 'agent_id': agent_id})

    def cx_add_comment(self, ticket_id, author_id, body, author_name='', is_internal=False):
        return self._request('POST', f'/cx/tickets/{ticket_id}/comments', {
            'author_id': author_id, 'author_name': author_name, 'body': body, 'is_internal': is_internal,
        })

    def cx_assign_ticket(self, ticket_id, agent_id, team=None):
        return self._request('POST', f'/cx/tickets/{ticket_id}/assign', {'agent_id': agent_id, 'team': team})

    def cx_get_ticket_stats(self):
        return self._request('GET', '/cx/tickets/stats')

    def cx_list_slas(self):
        return self._request('GET', '/cx/slas')

    def cx_create_sla(self, name, priority, response_time, resolution_time, business_hours=True):
        return self._request('POST', '/cx/slas', {
            'name': name, 'priority': priority, 'response_time': response_time,
            'resolution_time': resolution_time, 'business_hours': business_hours,
        })

    def cx_list_canned_responses(self, category=None):
        path = f'/cx/canned-responses?category={category}' if category else '/cx/canned-responses'
        return self._request('GET', path)

    def cx_create_canned_response(self, title, body, category, tags=None, created_by=''):
        return self._request('POST', '/cx/canned-responses', {
            'title': title, 'body': body, 'category': category, 'tags': tags, 'created_by': created_by,
        })

    def cx_analyze_sentiment(self, text, source_type='support_ticket', source_id='', customer_id='', customer_name='', metadata=None):
        return self._request('POST', '/cx/sentiment/analyze', {
            'text': text, 'source_type': source_type, 'source_id': source_id,
            'customer_id': customer_id, 'customer_name': customer_name, 'metadata': metadata,
        })

    def cx_get_sentiment_profile(self, customer_id):
        return self._request('GET', f'/cx/sentiment/profile/{customer_id}')

    def cx_list_sentiment_interactions(self, customer_id=None, source_type=None, min_score=None, max_score=None, escalated_only=False, limit=50):
        params = {}
        if customer_id: params['customer_id'] = customer_id
        if source_type: params['source_type'] = source_type
        if min_score is not None: params['min_score'] = min_score
        if max_score is not None: params['max_score'] = max_score
        if escalated_only: params['escalated_only'] = 'true'
        params['limit'] = limit
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/sentiment/interactions?{qs}')

    def cx_get_sentiment_trends(self, period='daily', days=30):
        return self._request('GET', f'/cx/sentiment/trends?period={period}&days={days}')

    def cx_get_sentiment_alerts(self):
        return self._request('GET', '/cx/sentiment/alerts')

    def cx_get_adoption_summary(self, customer_id):
        return self._request('GET', f'/cx/adoption/summary/{customer_id}')

    def cx_get_feature_adoption(self, customer_id, days=30):
        return self._request('GET', f'/cx/adoption/features/{customer_id}?days={days}')

    def cx_track_event(self, event_type, customer_id, user_id, feature_id=None, feature_name=None, metadata=None, session_id=None):
        return self._request('POST', '/cx/adoption/track', {
            'event_type': event_type, 'customer_id': customer_id, 'user_id': user_id,
            'feature_id': feature_id, 'feature_name': feature_name, 'metadata': metadata, 'session_id': session_id,
        })

    def cx_get_adoption_recommendations(self, customer_id):
        return self._request('GET', f'/cx/adoption/recommendations/{customer_id}')

    def cx_get_adoption_stats(self):
        return self._request('GET', '/cx/adoption/stats')

    def cx_start_onboarding(self, customer_id, customer_name='', product_tier='standard'):
        return self._request('POST', '/cx/onboarding/start', {
            'customer_id': customer_id, 'customer_name': customer_name, 'product_tier': product_tier,
        })

    def cx_get_onboarding_session(self, customer_id):
        return self._request('GET', f'/cx/onboarding/session/{customer_id}')

    def cx_update_onboarding_step(self, session_id, step_id, status, metadata=None):
        return self._request('POST', '/cx/onboarding/step', {
            'session_id': session_id, 'step_id': step_id, 'status': status, 'metadata': metadata,
        })

    def cx_get_onboarding_stats(self):
        return self._request('GET', '/cx/onboarding/stats')

    def cx_list_articles(self, category=None, article_type=None, status=None, limit=50):
        params = {}
        if category: params['category'] = category
        if article_type: params['type'] = article_type
        if status: params['status'] = status
        params['limit'] = limit
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/kb/articles?{qs}')

    def cx_create_article(self, title, content, category, article_type='guide', tags=None, author='', language='en'):
        return self._request('POST', '/cx/kb/articles', {
            'title': title, 'content': content, 'category': category,
            'article_type': article_type, 'tags': tags, 'author': author, 'language': language,
        })

    def cx_get_article(self, article_id):
        return self._request('GET', f'/cx/kb/articles/{article_id}')

    def cx_update_article(self, article_id, data):
        return self._request('PUT', f'/cx/kb/articles/{article_id}', data)

    def cx_search_articles(self, query, category=None, limit=20):
        params = f'q={query}'
        if category: params += f'&category={category}'
        params += f'&limit={limit}'
        return self._request('GET', f'/cx/kb/search?{params}')

    def cx_list_categories(self):
        return self._request('GET', '/cx/kb/categories')

    def cx_add_article_feedback(self, article_id, helpful, comment=None, user_id=None):
        return self._request('POST', '/cx/kb/feedback', {
            'article_id': article_id, 'helpful': helpful, 'comment': comment, 'user_id': user_id,
        })

    def cx_list_posts(self, category_id=None, post_type=None, sort='hot', limit=50, offset=0):
        params = {}
        if category_id: params['category_id'] = category_id
        if post_type: params['post_type'] = post_type
        params['sort'] = sort
        params['limit'] = limit
        params['offset'] = offset
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/community/posts?{qs}')

    def cx_create_post(self, title, content, category_id, post_type='discussion', author_id='', author_name='', tags=None):
        return self._request('POST', '/cx/community/posts', {
            'title': title, 'content': content, 'category_id': category_id,
            'post_type': post_type, 'author_id': author_id, 'author_name': author_name, 'tags': tags,
        })

    def cx_get_post(self, post_id):
        return self._request('GET', f'/cx/community/posts/{post_id}')

    def cx_vote_post(self, post_id, user_id, vote_type):
        return self._request('POST', f'/cx/community/posts/{post_id}/vote', {'user_id': user_id, 'vote_type': vote_type})

    def cx_add_community_comment(self, post_id, author_id, body, author_name='', parent_comment_id=None):
        return self._request('POST', f'/cx/community/posts/{post_id}/comments', {
            'author_id': author_id, 'author_name': author_name, 'body': body, 'parent_comment_id': parent_comment_id,
        })

    def cx_get_post_comments(self, post_id):
        return self._request('GET', f'/cx/community/posts/{post_id}/comments')

    def cx_get_feature_requests(self, sort='votes', limit=50):
        return self._request('GET', f'/cx/community/feature-requests?sort={sort}&limit={limit}')

    def cx_get_community_categories(self):
        return self._request('GET', '/cx/community/categories')

    def cx_get_leaderboard(self, limit=20):
        return self._request('GET', f'/cx/community/leaderboard?limit={limit}')

    def cx_get_community_stats(self):
        return self._request('GET', '/cx/community/stats')

    def cx_send_notification(self, ntype, subject, body, channels, priority='normal', target_segment='all', target_customer_ids=None, template_id=None, scheduled_at=None, created_by=''):
        return self._request('POST', '/cx/communication/send', {
            'type': ntype, 'priority': priority, 'subject': subject, 'body': body,
            'channels': channels, 'target_segment': target_segment,
            'target_customer_ids': target_customer_ids, 'template_id': template_id,
            'scheduled_at': scheduled_at, 'created_by': created_by,
        })

    def cx_list_batches(self, limit=50):
        return self._request('GET', f'/cx/communication/batches?limit={limit}')

    def cx_get_batch_stats(self, batch_id):
        return self._request('GET', f'/cx/communication/batch/{batch_id}')

    def cx_schedule_maintenance(self, title, description, affected_services, start_time, end_time, expected_downtime, created_by=''):
        return self._request('POST', '/cx/communication/maintenance', {
            'title': title, 'description': description, 'affected_services': affected_services,
            'start_time': start_time, 'end_time': end_time, 'expected_downtime': expected_downtime, 'created_by': created_by,
        })

    def cx_list_maintenance(self, status=None):
        path = f'/cx/communication/maintenance?status={status}' if status else '/cx/communication/maintenance'
        return self._request('GET', path)

    def cx_complete_maintenance(self, maintenance_id, actual_downtime=None, post_mortem=None):
        return self._request('POST', f'/cx/communication/maintenance/{maintenance_id}/complete', {
            'actual_downtime': actual_downtime, 'post_mortem': post_mortem,
        })

    def cx_list_templates(self, channel=None):
        path = f'/cx/communication/templates?channel={channel}' if channel else '/cx/communication/templates'
        return self._request('GET', path)

    def cx_create_template(self, name, subject, body, channel, category='general', variables=None):
        return self._request('POST', '/cx/communication/templates', {
            'name': name, 'subject': subject, 'body': body, 'channel': channel,
            'category': category, 'variables': variables,
        })

    def cx_create_survey(self, title, description, survey_type, trigger, questions, target_segment='all', frequency_days=None):
        return self._request('POST', '/cx/nps/surveys', {
            'title': title, 'description': description, 'survey_type': survey_type,
            'trigger': trigger, 'questions': questions, 'target_segment': target_segment,
            'frequency_days': frequency_days,
        })

    def cx_get_surveys(self, trigger=None, survey_type=None):
        params = {}
        if trigger: params['trigger'] = trigger
        if survey_type: params['survey_type'] = survey_type
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/nps/surveys?{qs}' if qs else '/cx/nps/surveys')

    def cx_get_survey(self, survey_id):
        return self._request('GET', f'/cx/nps/surveys/{survey_id}')

    def cx_send_survey(self, survey_id, customer_id, customer_name=''):
        return self._request('POST', f'/cx/nps/send/{survey_id}', {'customer_id': customer_id, 'customer_name': customer_name})

    def cx_submit_response(self, response_id, answers=None, comments=None):
        return self._request('POST', f'/cx/nps/respond/{response_id}', {'answers': answers or {}, 'comments': comments})

    def cx_get_nps_score(self):
        return self._request('GET', '/cx/nps/score')

    def cx_get_nps_trend(self, days=90):
        return self._request('GET', f'/cx/nps/trend?days={days}')

    def cx_get_detractor_feedback(self, limit=50):
        return self._request('GET', f'/cx/nps/detractors?limit={limit}')

    def cx_get_nps_stats(self):
        return self._request('GET', '/cx/nps/stats')

    def cx_list_plays(self, trigger_event=None, status=None):
        params = {}
        if trigger_event: params['trigger_event'] = trigger_event
        if status: params['status'] = status
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/success/plays?{qs}' if qs else '/cx/success/plays')

    def cx_create_play(self, name, description, trigger_event, actions, tags=None, trigger_conditions=None, cooldown_days=30):
        return self._request('POST', '/cx/success/plays', {
            'name': name, 'description': description, 'trigger_event': trigger_event,
            'actions': actions, 'tags': tags, 'trigger_conditions': trigger_conditions, 'cooldown_days': cooldown_days,
        })

    def cx_update_play_status(self, play_id, status):
        return self._request('PATCH', f'/cx/success/plays/{play_id}/status', {'status': status})

    def cx_evaluate_trigger(self, event, customer_id, event_data=None):
        return self._request('POST', '/cx/success/trigger', {'event': event, 'customer_id': customer_id, 'event_data': event_data})

    def cx_get_executions(self, play_id=None, customer_id=None, limit=50):
        params = {}
        if play_id: params['play_id'] = play_id
        if customer_id: params['customer_id'] = customer_id
        params['limit'] = limit
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        return self._request('GET', f'/cx/success/executions?{qs}')

    def cx_get_success_stats(self):
        return self._request('GET', '/cx/success/stats')

    # === v4 AIOps API Methods ===

    def rca_analyze(self, title, description):
        return self._request('POST', '/aiops/rca/analyze', {'incident_title': title, 'incident_description': description})

    def rca_ingest_event(self, event_type, source, title, description, metadata=None, severity='info'):
        return self._request('POST', '/aiops/rca/events', {'event_type': event_type, 'source': source, 'title': title, 'description': description, 'metadata': metadata or {}, 'severity': severity})

    def rca_incidents(self):
        return self._request('GET', '/aiops/rca/incidents')

    def rca_events(self, source=None):
        params = f'?source={source}' if source else ''
        return self._request('GET', f'/aiops/rca/events{params}')

    def rca_dependency_graph(self):
        return self._request('GET', '/aiops/rca/dependencies')

    def remediate_suggest(self, incident):
        return self._request('POST', '/aiops/remediate/suggest', incident)

    def remediate_create(self, incident_id, action, params, confidence, pattern):
        return self._request('POST', '/aiops/remediate/create', {'incident_id': incident_id, 'action': action, 'params': params, 'confidence': confidence, 'pattern': pattern})

    def remediate_approve(self, remediation_id, approver):
        return self._request('POST', f'/aiops/remediate/{remediation_id}/approve', {'approver': approver})

    def remediate_reject(self, remediation_id, reason):
        return self._request('POST', f'/aiops/remediate/{remediation_id}/reject', {'reason': reason})

    def remediate_execute(self, remediation_id):
        return self._request('POST', f'/aiops/remediate/{remediation_id}/execute')

    def remediate_list(self):
        return self._request('GET', '/aiops/remediate')

    def remediate_stats(self):
        return self._request('GET', '/aiops/remediate/stats')

    def remediate_patterns(self):
        return self._request('GET', '/aiops/remediate/patterns')

    def dem_list(self, status=None):
        params = f'?status={status}' if status else ''
        return self._request('GET', f'/aiops/dem/monitors{params}')

    def dem_create(self, name, url, monitor_type='browser_synthetic', status='active'):
        return self._request('POST', '/aiops/dem/monitors', {'name': name, 'url': url, 'monitor_type': monitor_type, 'status': status})

    def dem_get(self, monitor_id):
        return self._request('GET', f'/aiops/dem/monitors/{monitor_id}')

    def dem_update(self, monitor_id, data):
        return self._request('PATCH', f'/aiops/dem/monitors/{monitor_id}', data)

    def dem_delete(self, monitor_id):
        return self._request('DELETE', f'/aiops/dem/monitors/{monitor_id}')

    def dem_run_check(self, monitor_id):
        return self._request('POST', f'/aiops/dem/monitors/{monitor_id}/check')

    def dem_stats(self, monitor_id):
        return self._request('GET', f'/aiops/dem/monitors/{monitor_id}/stats')

    def dem_summary(self):
        return self._request('GET', '/aiops/dem/summary')

    def dem_vitals(self, monitor_id):
        return self._request('GET', f'/aiops/dem/monitors/{monitor_id}/vitals')

    def alert_ingest(self, name, source, severity, message):
        return self._request('POST', '/aiops/alerts', {'name': name, 'source': source, 'severity': severity, 'message': message})

    def alert_ack(self, alert_id):
        return self._request('POST', f'/aiops/alerts/{alert_id}/acknowledge')

    def alert_resolve(self, alert_id):
        return self._request('POST', f'/aiops/alerts/{alert_id}/resolve')

    def alert_suppression(self, name, match_name):
        return self._request('POST', '/aiops/alerts/suppression', {'name': name, 'match_name': match_name})

    def alert_incidents(self, status=None):
        params = f'?status={status}' if status else ''
        return self._request('GET', f'/aiops/alerts/incidents{params}')

    def alert_resolve_incident(self, incident_id):
        return self._request('POST', f'/aiops/alerts/incidents/{incident_id}/resolve')

    def alert_stats(self):
        return self._request('GET', '/aiops/alerts/stats')

    def scaling_record_metric(self, resource_id, metric, value):
        return self._request('POST', '/aiops/scaling/metrics', {'resource_id': resource_id, 'metric': metric, 'value': value})

    def scaling_predict(self, resource_id, metric):
        return self._request('GET', f'/aiops/scaling/predict/{resource_id}/{metric}')

    def scaling_policy(self, resource_id, policy):
        return self._request('POST', '/aiops/scaling/policy', {'resource_id': resource_id, 'policy': policy})

    def scaling_metrics(self, resource_id, metric):
        return self._request('GET', f'/aiops/scaling/metrics/{resource_id}/{metric}')

    def scaling_summary(self):
        return self._request('GET', '/aiops/scaling/summary')

    def health_register(self, service_id, name):
        return self._request('POST', '/aiops/health/services', {'service_id': service_id, 'name': name})

    def health_snapshot(self, service_id, metrics):
        return self._request('POST', '/aiops/health/snapshots', {'service_id': service_id, 'metrics': metrics})

    def health_forecast(self, service_id):
        return self._request('GET', f'/aiops/health/forecast/{service_id}')

    def health_dashboard(self):
        return self._request('GET', '/aiops/health/dashboard')

    def health_services(self):
        return self._request('GET', '/aiops/health/services')

    def health_get(self, service_id):
        return self._request('GET', f'/aiops/health/services/{service_id}')

    def health_delete(self, service_id):
        return self._request('DELETE', f'/aiops/health/services/{service_id}')

    def ops_assistant_message(self, session_id, user_id, message):
        return self._request('POST', '/aiops/assistant/message', {'session_id': session_id, 'user_id': user_id, 'message': message})

    def ops_assistant_session(self, session_id):
        return self._request('GET', f'/aiops/assistant/session/{session_id}')

    def ops_assistant_stats(self):
        return self._request('GET', '/aiops/assistant/stats')

    def change_plan(self, title, description, change_type, target, affected_resources):
        return self._request('POST', '/aiops/changes', {'title': title, 'description': description, 'change_type': change_type, 'target': target, 'affected_resources': affected_resources})

    def change_approve(self, change_id, approver):
        return self._request('POST', f'/aiops/changes/{change_id}/approve', {'approver': approver})

    def change_reject(self, change_id, reason):
        return self._request('POST', f'/aiops/changes/{change_id}/reject', {'reason': reason})

    def change_outcome(self, change_id, status, result):
        return self._request('POST', f'/aiops/changes/{change_id}/outcome', {'status': status, 'result': result})

    def change_stats(self):
        return self._request('GET', '/aiops/changes/stats')

    def capacity_record_usage(self, resource_id, metric, total, used):
        return self._request('POST', '/aiops/capacity/usage', {'resource_id': resource_id, 'metric': metric, 'total': total, 'used': used})

    def capacity_usage(self, resource_id, metric):
        return self._request('GET', f'/aiops/capacity/usage/{resource_id}/{metric}')

    def capacity_recommend(self, resource_id, metric):
        return self._request('GET', f'/aiops/capacity/recommend/{resource_id}/{metric}')

    def capacity_simulate(self, resource_id, metric, scenario):
        return self._request('POST', '/aiops/capacity/simulate', {'resource_id': resource_id, 'metric': metric, 'scenario': scenario})

    def capacity_summary(self):
        return self._request('GET', '/aiops/capacity/summary')

    def chatbot_message(self, user_id, message, conversation_id=None):
        return self._request('POST', '/aiops/chatbot/message', {'user_id': user_id, 'message': message, 'conversation_id': conversation_id})

    def chatbot_conversation(self, conversation_id):
        return self._request('GET', f'/aiops/chatbot/conversation/{conversation_id}')

    def chatbot_tasks(self, user_id):
        return self._request('GET', f'/aiops/chatbot/tasks/{user_id}')

    def chatbot_analytics(self):
        return self._request('GET', '/aiops/chatbot/analytics')

    # === v4 SOC API Methods ===

    def soar_playbooks(self):
        return self._request('GET', '/api/v1/soc/soar/playbooks')

    def soar_playbook_get(self, playbook_id):
        return self._request('GET', f'/api/v1/soc/soar/playbooks/{playbook_id}')

    def soar_playbook_run(self, playbook_id):
        return self._request('POST', f'/api/v1/soc/soar/playbooks/{playbook_id}/run')

    def soar_playbook_create(self, name, description, category):
        return self._request('POST', '/api/v1/soc/soar/playbooks', {'name': name, 'description': description, 'category': category})

    def soar_cases(self):
        return self._request('GET', '/api/v1/soc/soar/cases')

    def soar_connectors(self):
        return self._request('GET', '/api/v1/soc/soar/connectors')

    def threatintel_feeds(self):
        return self._request('GET', '/api/v1/soc/threat-intel/feeds')

    def threatintel_iocs(self):
        return self._request('GET', '/api/v1/soc/threat-intel/iocs')

    def threatintel_blocklist(self):
        return self._request('GET', '/api/v1/soc/threat-intel/blocklist')

    def threatintel_add_ioc(self, ioc_type, value, confidence):
        return self._request('POST', '/api/v1/soc/threat-intel/iocs', {'type': ioc_type, 'value': value, 'confidence': confidence})

    def threatintel_analyze(self, text):
        return self._request('POST', '/api/v1/soc/threat-intel/analyze', {'text': text})

    def deception_decoys(self):
        return self._request('GET', '/api/v1/soc/deception/decoys')

    def deception_tokens(self):
        return self._request('GET', '/api/v1/soc/deception/tokens')

    def deception_create_decoy(self, name, decoy_type, target_ip, port):
        return self._request('POST', '/api/v1/soc/deception/decoys', {'name': name, 'decoy_type': decoy_type, 'target_ip': target_ip, 'port': port})

    def deception_deploy(self, decoy_id):
        return self._request('POST', f'/api/v1/soc/deception/decoys/{decoy_id}/deploy')

    def vuln_cves(self):
        return self._request('GET', '/api/v1/soc/vulnerabilities/cves')

    def vuln_scan(self, target):
        return self._request('POST', '/api/v1/soc/vulnerabilities/scan', {'target': target})

    def vuln_patch(self, cve_id):
        return self._request('POST', f'/api/v1/soc/vulnerabilities/cves/{cve_id}/patch')

    def vuln_summary(self):
        return self._request('GET', '/api/v1/soc/vulnerabilities/summary')

    def ir_incidents(self):
        return self._request('GET', '/api/v1/soc/incidents')

    def ir_get_incident(self, incident_id):
        return self._request('GET', f'/api/v1/soc/incidents/{incident_id}')

    def ir_create_incident(self, title, severity, incident_type):
        return self._request('POST', '/api/v1/soc/incidents', {'title': title, 'severity': severity, 'incident_type': incident_type})

    def ir_update_status(self, incident_id, status):
        return self._request('PATCH', f'/api/v1/soc/incidents/{incident_id}/status', {'status': status})

    def ir_add_evidence(self, incident_id, title, content, evidence_type):
        return self._request('POST', f'/api/v1/soc/incidents/{incident_id}/evidence', {'title': title, 'content': content, 'evidence_type': evidence_type})

    def ir_timeline(self, incident_id):
        return self._request('GET', f'/api/v1/soc/incidents/{incident_id}/timeline')

    def ir_report(self, incident_id):
        return self._request('GET', f'/api/v1/soc/incidents/{incident_id}/report')

    def ueba_entities(self):
        return self._request('GET', '/api/v1/soc/ueba/entities')

    def ueba_alerts(self):
        return self._request('GET', '/api/v1/soc/ueba/alerts')

    def cspm_accounts(self):
        return self._request('GET', '/api/v1/soc/cspm/accounts')

    def cspm_results(self):
        return self._request('GET', '/api/v1/soc/cspm/results')

    def cspm_scan(self):
        return self._request('POST', '/api/v1/soc/cspm/scan')

    def ndr_flows(self, malicious_only=True):
        path = '/api/v1/soc/ndr/flows'
        if malicious_only:
            path += '?malicious_only=true'
        return self._request('GET', path)

    def ndr_alerts(self):
        return self._request('GET', '/api/v1/soc/ndr/alerts')

    def secrets_findings(self):
        return self._request('GET', '/api/v1/soc/secrets/findings')

    def secrets_targets(self):
        return self._request('GET', '/api/v1/soc/secrets/targets')

    def secrets_rotate(self, finding_id):
        return self._request('POST', f'/api/v1/soc/secrets/rotate/{finding_id}')

    def training_modules(self):
        return self._request('GET', '/api/v1/soc/training/modules')

    def training_campaigns(self):
        return self._request('GET', '/api/v1/soc/training/campaigns')

    def training_assignments(self):
        return self._request('GET', '/api/v1/soc/training/assignments')

    # === v4 FinOps API Methods ===

    def finops_commitment_list(self):
        return self._request('GET', '/finops/commitment/recommendations')

    def finops_commitment_summary(self):
        return self._request('GET', '/finops/commitment/summary')

    def finops_commitment_implement(self, rec_id):
        return self._request('POST', f'/finops/commitment/recommendations/{rec_id}/implement')

    def finops_commitment_commitments(self):
        return self._request('GET', '/finops/commitment/commitments')

    def finops_spot_list(self, status=None):
        path = f'/finops/spot/fleets?status={status}' if status else '/finops/spot/fleets'
        return self._request('GET', path)

    def finops_spot_create(self, name, instance_types, target_capacity, regions):
        return self._request('POST', '/finops/spot/fleets', {'name': name, 'instance_types': instance_types, 'target_capacity': target_capacity, 'regions': regions})

    def finops_spot_get(self, fleet_id):
        return self._request('GET', f'/finops/spot/fleets/{fleet_id}')

    def finops_spot_instances(self, fleet_id):
        return self._request('GET', f'/finops/spot/fleets/{fleet_id}/instances')

    def finops_spot_savings(self):
        return self._request('GET', '/finops/spot/savings')

    def finops_uoe_metrics(self, customer_id=None, dimension=None):
        path = '/finops/unit-economics/metrics'
        params = []
        if customer_id: params.append(f'customer_id={customer_id}')
        if dimension: params.append(f'dimension={dimension}')
        if params: path += '?' + '&'.join(params)
        return self._request('GET', path)

    def finops_uoe_record(self, customer_id, metric_name, value, dimension):
        return self._request('POST', '/finops/unit-economics/metrics', {'customer_id': customer_id, 'metric_name': metric_name, 'value': value, 'dimension': dimension})

    def finops_uoe_targets(self):
        return self._request('GET', '/finops/unit-economics/targets')

    def finops_uoe_set_target(self, metric_name, target_value, threshold):
        return self._request('POST', '/finops/unit-economics/targets', {'metric_name': metric_name, 'target_value': target_value, 'threshold_pct': threshold})

    def finops_uoe_violations(self):
        return self._request('GET', '/finops/unit-economics/violations')

    def finops_uoe_overview(self):
        return self._request('GET', '/finops/unit-economics/overview')

    def finops_anomaly_list(self, severity=None):
        path = f'/finops/anomaly/detections?severity={severity}' if severity else '/finops/anomaly/detections'
        return self._request('GET', path)

    def finops_anomaly_summary(self):
        return self._request('GET', '/finops/anomaly/summary')

    def finops_anomaly_investigate(self, anomaly_id):
        return self._request('POST', f'/finops/anomaly/detections/{anomaly_id}/investigate')

    def finops_anomaly_resolve(self, anomaly_id):
        return self._request('POST', f'/finops/anomaly/detections/{anomaly_id}/resolve')

    def finops_anomaly_profiles(self):
        return self._request('GET', '/finops/anomaly/profiles')

    def finops_anomaly_create_profile(self, name, method, sensitivity):
        return self._request('POST', '/finops/anomaly/profiles', {'name': name, 'detection_method': method, 'sensitivity': sensitivity})

    def finops_budget_list(self):
        return self._request('GET', '/finops/budget')

    def finops_budget_create(self, name, amount, period, scope=None):
        return self._request('POST', '/finops/budget', {'name': name, 'amount': amount, 'period': period, 'scope': scope})

    def finops_budget_get(self, budget_id):
        return self._request('GET', f'/finops/budget/{budget_id}')

    def finops_budget_spend(self, budget_id, amount):
        return self._request('POST', f'/finops/budget/{budget_id}/spend', {'amount': amount})

    def finops_budget_forecast(self, budget_id):
        return self._request('GET', f'/finops/budget/{budget_id}/forecast')

    def finops_budget_scenario(self, budget_id, scenario):
        return self._request('POST', f'/finops/budget/{budget_id}/scenario', {'scenario': scenario})

    def finops_budget_summary(self):
        return self._request('GET', '/finops/budget/summary')

    def finops_rightsizing_list(self):
        return self._request('GET', '/finops/rightsizing/recommendations')

    def finops_rightsizing_summary(self):
        return self._request('GET', '/finops/rightsizing/summary')

    def finops_rightsizing_approve(self, rec_id):
        return self._request('POST', f'/finops/rightsizing/recommendations/{rec_id}/approve')

    def finops_rightsizing_implement(self, rec_id):
        return self._request('POST', f'/finops/rightsizing/recommendations/{rec_id}/implement')

    def finops_rightsizing_dismiss(self, rec_id):
        return self._request('POST', f'/finops/rightsizing/recommendations/{rec_id}/dismiss')

    def finops_waste_list(self, category=None, severity=None):
        path = '/finops/waste/findings'
        params = []
        if category: params.append(f'category={category}')
        if severity: params.append(f'severity={severity}')
        if params: path += '?' + '&'.join(params)
        return self._request('GET', path)

    def finops_waste_summary(self):
        return self._request('GET', '/finops/waste/summary')

    def finops_waste_scan(self):
        return self._request('POST', '/finops/waste/scan')

    def finops_waste_approve(self, finding_id):
        return self._request('POST', f'/finops/waste/findings/{finding_id}/approve')

    def finops_waste_cleanup(self, finding_id):
        return self._request('POST', f'/finops/waste/findings/{finding_id}/cleanup')

    def finops_waste_dismiss(self, finding_id):
        return self._request('POST', f'/finops/waste/findings/{finding_id}/dismiss')

    def finops_carbon_list(self):
        return self._request('GET', '/finops/carbon/recommendations')

    def finops_carbon_assets(self):
        return self._request('GET', '/finops/carbon/assets')

    def finops_carbon_register(self, name, provider, region, monthly_cost, kwh=None):
        return self._request('POST', '/finops/carbon/assets', {'name': name, 'provider': provider, 'region': region, 'monthly_cost': monthly_cost, 'kwh': kwh})

    def finops_carbon_sustainability(self):
        return self._request('GET', '/finops/carbon/sustainability-budget')

    def finops_arbitrage_workloads(self):
        return self._request('GET', '/finops/arbitrage/workloads')

    def finops_arbitrage_comparisons(self):
        return self._request('GET', '/finops/arbitrage/comparisons')

    def finops_arbitrage_savings(self):
        return self._request('GET', '/finops/arbitrage/savings')

    def finops_reports_list(self):
        return self._request('GET', '/finops/reports')

    def finops_reports_summary(self):
        return self._request('GET', '/finops/reports/summary')

    def finops_reports_generate(self, report_type, period):
        return self._request('POST', '/finops/reports/generate', {'report_type': report_type, 'period': period})

    def finops_reports_get(self, report_id):
        return self._request('GET', f'/finops/reports/{report_id}')

    def finops_reports_dashboard(self, dashboard_type):
        return self._request('GET', f'/finops/reports/dashboard/{dashboard_type}')

    def finops_reports_allocations(self, team=None):
        path = '/finops/reports/allocations'
        if team:
            path += f'?team={team}'
        return self._request('GET', path)

    def finops_reports_create_allocation(self, tag_key, tag_value, cost_pct, team=None, project=None):
        return self._request('POST', '/finops/reports/allocations', {
            'tag_key': tag_key, 'tag_value': tag_value, 'cost_pct': cost_pct, 'team': team, 'project': project,
        })

    def finops_commitment_analyze(self):
        return self._request('POST', '/finops/commitment/analyze')

    def finops_commitment_coverage(self):
        return self._request('GET', '/finops/commitment/coverage-gaps')

    def finops_spot_launch(self, fleet_id, count=None):
        body = {}
        if count: body['count'] = count
        return self._request('POST', f'/finops/spot/fleets/{fleet_id}/launch', body)

    def finops_spot_interrupt(self, instance_id):
        return self._request('POST', f'/finops/spot/instances/{instance_id}/interrupt')

    def finops_spot_update(self, fleet_id, capacity):
        return self._request('PATCH', f'/finops/spot/fleets/{fleet_id}', {'target_capacity': capacity})

    def finops_anomaly_ingest(self, service, amount, region):
        return self._request('POST', '/finops/anomaly/ingest', {'service': service, 'amount': amount, 'region': region})

    def finops_budget_variance(self, budget_id):
        return self._request('GET', f'/finops/budget/{budget_id}/variance')

    def finops_rightsizing_register(self, name, resource_type, current_size, specs, monthly_cost, provider, region):
        return self._request('POST', '/finops/rightsizing/resources', {
            'name': name, 'resource_type': resource_type, 'current_size': current_size,
            'specs': specs, 'monthly_cost': monthly_cost, 'provider': provider, 'region': region,
        })

    def finops_rightsizing_analyze(self, resource_id):
        return self._request('POST', f'/finops/rightsizing/resources/{resource_id}/analyze')

    def finops_carbon_footprint(self, asset_id):
        return self._request('GET', f'/finops/carbon/assets/{asset_id}/footprint')

    def finops_carbon_tradeoff(self, asset_id):
        return self._request('GET', f'/finops/carbon/assets/{asset_id}/tradeoff')

    def finops_carbon_intensity(self, region):
        return self._request('GET', f'/finops/carbon/intensity/{region}')

    def finops_arbitrage_register(self, name, cpu_cores, memory_gb, storage_gb, data_transfer_gb, current_provider, current_cost):
        return self._request('POST', '/finops/arbitrage/workloads', {
            'name': name, 'cpu_cores': cpu_cores, 'memory_gb': memory_gb,
            'storage_gb': storage_gb, 'data_transfer_gb': data_transfer_gb,
            'current_provider': current_provider, 'current_cost': current_cost,
        })

    def finops_arbitrage_compare(self, workload_id):
        return self._request('GET', f'/finops/arbitrage/workloads/{workload_id}/compare')

    def finops_arbitrage_migrate(self, workload_id):
        return self._request('POST', f'/finops/arbitrage/workloads/{workload_id}/migrate')

    # === v4 Emerging Tech ===

    def blockchain_list_networks(self):
        return self._get('/api/v1/emerging-tech/blockchain/networks')

    def blockchain_create_network(self, name, consensus, chain_id):
        return self._post('/api/v1/emerging-tech/blockchain/networks', {'name': name, 'consensus': consensus, 'chain_id': chain_id})

    def blockchain_network_status(self, network_id):
        return self._get(f'/api/v1/emerging-tech/blockchain/networks/{network_id}')

    def blockchain_validators(self, network_id):
        return self._get(f'/api/v1/emerging-tech/blockchain/networks/{network_id}/validators')

    def storage_list_gateways(self):
        return self._get('/api/v1/emerging-tech/storage/gateways')

    def storage_create_gateway(self, name, provider):
        return self._post('/api/v1/emerging-tech/storage/gateways', {'name': name, 'provider': provider})

    def storage_pin_content(self, cid):
        return self._post('/api/v1/emerging-tech/storage/pin', {'cid': cid})

    def storage_gateway_status(self, gateway_id):
        return self._get(f'/api/v1/emerging-tech/storage/gateways/{gateway_id}')

    def quantum_list_keys(self):
        return self._get('/api/v1/emerging-tech/quantum/keys')

    def quantum_generate_key(self, algorithm):
        return self._post('/api/v1/emerging-tech/quantum/keys', {'algorithm': algorithm})

    def quantum_create_certificate(self, name, key_id):
        return self._post('/api/v1/emerging-tech/quantum/certificates', {'name': name, 'key_id': key_id})

    def quantum_encrypt(self, key_id, message):
        return self._post('/api/v1/emerging-tech/quantum/encrypt', {'key_id': key_id, 'message': message})

    def quantum_decrypt(self, key_id, ciphertext):
        return self._post('/api/v1/emerging-tech/quantum/decrypt', {'key_id': key_id, 'ciphertext': ciphertext})

    def contracts_list(self):
        return self._get('/api/v1/emerging-tech/contracts')

    def contracts_deploy(self, name, network, bytecode):
        return self._post('/api/v1/emerging-tech/contracts', {'name': name, 'network': network, 'bytecode': bytecode})

    def contracts_get(self, contract_id):
        return self._get(f'/api/v1/emerging-tech/contracts/{contract_id}')

    def contracts_events(self, contract_id):
        return self._get(f'/api/v1/emerging-tech/contracts/{contract_id}/events')

    def web3id_list(self):
        return self._get('/api/v1/emerging-tech/web3id/identities')

    def web3id_create(self, did):
        return self._post('/api/v1/emerging-tech/web3id/identities', {'did': did})

    def web3id_authenticate(self, identity_id):
        return self._post(f'/api/v1/emerging-tech/web3id/identities/{identity_id}/auth')

    def web3id_sessions(self):
        return self._get('/api/v1/emerging-tech/web3id/sessions')

    def confidential_list_enclaves(self):
        return self._get('/api/v1/emerging-tech/confidential/enclaves')

    def confidential_create_enclave(self, name, image, memory_mb):
        return self._post('/api/v1/emerging-tech/confidential/enclaves', {'name': name, 'image': image, 'memory_mb': memory_mb})

    def confidential_attest(self, enclave_id):
        return self._post(f'/api/v1/emerging-tech/confidential/enclaves/{enclave_id}/attest')

    def confidential_secrets(self, enclave_id):
        return self._get(f'/api/v1/emerging-tech/confidential/enclaves/{enclave_id}/secrets')

    def federated_list_projects(self):
        return self._get('/api/v1/emerging-tech/federated/projects')

    def federated_create_project(self, name, rounds, min_clients):
        return self._post('/api/v1/emerging-tech/federated/projects', {'name': name, 'rounds': rounds, 'min_clients': min_clients})

    def federated_project_status(self, project_id):
        return self._get(f'/api/v1/emerging-tech/federated/projects/{project_id}')

    def federated_rounds(self, project_id):
        return self._get(f'/api/v1/emerging-tech/federated/projects/{project_id}/rounds')

    def zkp_list(self):
        return self._get('/api/v1/emerging-tech/zkp/proofs')

    def zkp_generate(self, statement, witness):
        return self._post('/api/v1/emerging-tech/zkp/proofs', {'statement': statement, 'witness': witness})

    def zkp_verify(self, proof_id):
        return self._post(f'/api/v1/emerging-tech/zkp/proofs/{proof_id}/verify')

    def zkp_circuits(self):
        return self._get('/api/v1/emerging-tech/zkp/circuits')

    def dcn_list_tasks(self):
        return self._get('/api/v1/emerging-tech/dcn/tasks')

    def dcn_submit_task(self, name, requirements, input_data):
        return self._post('/api/v1/emerging-tech/dcn/tasks', {'name': name, 'requirements': requirements, 'input_data': input_data})

    def dcn_task_status(self, task_id):
        return self._get(f'/api/v1/emerging-tech/dcn/tasks/{task_id}')

    def dcn_workers(self):
        return self._get('/api/v1/emerging-tech/dcn/workers')
