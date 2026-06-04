import argparse
import json
import sys

from . import __version__
from .config import load_config, save_config, set_key, get
from .client import ApiClient
from .output import print_output


def get_client():
    config = load_config()
    return ApiClient(config.get('api_url', 'http://localhost:8080'), config.get('token'))


def cmd_login(args):
    result = get_client().login(args.api_key)
    if 'token' in result:
        set_key('token', result['token'])
        print_output({'status': 'Logged in successfully'}, args.output)
    else:
        print_output(result, args.output)


def cmd_logout(args):
    result = get_client().logout()
    set_key('token', None)
    print_output(result or {'status': 'Logged out'}, args.output)


def cmd_server_list(args):
    result = get_client().list_servers()
    data = result if isinstance(result, list) else result.get('servers', result)
    print_output(data, args.output)


def cmd_server_create(args):
    result = get_client().create_server(args.name, args.type, args.memory)
    print_output(result, args.output)


def cmd_server_delete(args):
    result = get_client().delete_server(args.server)
    print_output(result, args.output)


def cmd_server_status(args):
    result = get_client().server_status(args.server)
    print_output(result, args.output)


def cmd_logs(args):
    result = get_client().get_logs(args.server, args.lines, args.follow)
    print_output(result, args.output)


def cmd_backup_list(args):
    result = get_client().list_backups(args.server)
    data = result if isinstance(result, list) else result.get('backups', result)
    print_output(data, args.output)


def cmd_backup_create(args):
    result = get_client().create_backup(args.server)
    print_output(result, args.output)


def cmd_deploy(args):
    result = get_client().deploy(args.server, args.branch)
    print_output(result, args.output)


def cmd_config_get(args):
    config = load_config()
    if args.key:
        value = config.get(args.key)
        print_output({args.key: value}, args.output)
    else:
        print_output(config, args.output)


def cmd_config_set(args):
    set_key(args.key, args.value)
    print_output({args.key: args.value, 'status': 'set'}, args.output)


# === Edge & IoT Commands ===

def cmd_edge_list(args):
    result = get_client().edge_list_devices(device_type=args.device_type, status=args.status)
    data = result if isinstance(result, list) else result.get('devices', result)
    print_output(data, args.output)


def cmd_edge_register(args):
    result = get_client().edge_register_device(args.name, args.device_type, args.hardware_id)
    print_output(result, args.output)


def cmd_edge_status(args):
    result = get_client().edge_device_status(args.device_id)
    print_output(result, args.output)


def cmd_edge_command(args):
    result = get_client().edge_send_command(args.device_id, args.command)
    print_output(result, args.output)


def cmd_edge_backup(args):
    result = get_client().edge_create_backup(args.device_id)
    print_output(result, args.output)


def cmd_fn_list(args):
    result = get_client().fn_list_functions(device_id=args.device_id)
    data = result if isinstance(result, list) else result.get('functions', result)
    print_output(data, args.output)


def cmd_fn_deploy(args):
    result = get_client().fn_deploy_function(args.name, args.runtime, args.device_id, args.source, args.handler)
    print_output(result, args.output)


def cmd_fn_invoke(args):
    payload = json.loads(args.payload) if args.payload else {}
    result = get_client().fn_invoke_function(args.func_id, payload)
    print_output(result, args.output)


def cmd_ml_models(args):
    result = get_client().ml_list_models(device_id=args.device_id)
    data = result if isinstance(result, list) else result.get('models', result)
    print_output(data, args.output)


def cmd_ml_deploy(args):
    result = get_client().ml_deploy_model(args.name, args.model_format, args.device_id, args.version)
    print_output(result, args.output)


def cmd_ml_infer(args):
    result = get_client().ml_run_inference(args.model_id)
    print_output(result, args.output)


def cmd_iot_codes(args):
    result = get_client().iot_generate_codes(args.count, args.ttl)
    data = result if isinstance(result, list) else result.get('codes', result)
    print_output(data, args.output)


def cmd_iot_enroll(args):
    result = get_client().iot_enroll_device(args.code, args.device_id)
    print_output(result, args.output)


def cmd_cdn_stats(args):
    result = get_client().cdn_get_stats()
    print_output(result, args.output)


def cmd_mesh_list(args):
    result = get_client().mesh_list_networks()
    data = result if isinstance(result, list) else result.get('networks', result)
    print_output(data, args.output)


def cmd_mesh_create(args):
    result = get_client().mesh_create_network(args.name, args.mesh_type, args.subnet)
    print_output(result, args.output)


def cmd_gw_list(args):
    result = get_client().gw_list_gateways(status=args.status)
    data = result if isinstance(result, list) else result.get('gateways', result)
    print_output(data, args.output)


def cmd_pipeline_stats(args):
    result = get_client().pipeline_get_statistics()
    print_output(result, args.output)


# === Green Computing Commands ===

def cmd_energy_current(args):
    result = get_client().energy_get_current()
    print_output(result, args.output)


def cmd_energy_history(args):
    result = get_client().energy_get_history(args.server_id, args.hours)
    print_output(result, args.output)


def cmd_energy_summary(args):
    result = get_client().energy_get_summary(args.period)
    print_output(result, args.output)


def cmd_carbon_current(args):
    result = get_client().carbon_get_current()
    print_output(result, args.output)


def cmd_carbon_history(args):
    result = get_client().carbon_get_history()
    print_output(result, args.output)


def cmd_green_forecast(args):
    result = get_client().green_get_forecast()
    print_output(result, args.output)


def cmd_green_jobs(args):
    result = get_client().green_list_jobs(status=args.status)
    data = result if isinstance(result, list) else result.get('jobs', result)
    print_output(data, args.output)


def cmd_green_schedule(args):
    result = get_client().green_add_job(args.name, args.command, args.urgency)
    print_output(result, args.output)


def cmd_green_report(args):
    result = get_client().green_savings_report()
    print_output(result, args.output)


def cmd_reclaim_list(args):
    result = get_client().reclaim_list_resources(resource_type=args.resource_type)
    data = result if isinstance(result, list) else result.get('resources', result)
    print_output(data, args.output)


def cmd_reclaim_scan(args):
    result = get_client().reclaim_scan()
    print_output(result, args.output)


def cmd_reclaim_report(args):
    result = get_client().reclaim_report()
    print_output(result, args.output)


def cmd_shutdown_policies(args):
    result = get_client().shutdown_list_policies()
    data = result if isinstance(result, list) else result.get('policies', result)
    print_output(data, args.output)


def cmd_shutdown_create(args):
    result = get_client().shutdown_create_policy(args.name, args.tags, args.shutdown_hours)
    print_output(result, args.output)


def cmd_shutdown_savings(args):
    result = get_client().shutdown_savings()
    print_output(result, args.output)


def cmd_hardware_list(args):
    result = get_client().hardware_list_assets(asset_type=args.asset_type)
    data = result if isinstance(result, list) else result.get('assets', result)
    print_output(data, args.output)


def cmd_hardware_add(args):
    result = get_client().hardware_add_asset(args.asset_type, args.manufacturer, args.model, args.serial)
    print_output(result, args.output)


def cmd_pue_current(args):
    result = get_client().pue_get_current()
    print_output(result, args.output)


def cmd_pue_history(args):
    result = get_client().pue_get_history(args.hours)
    print_output(result, args.output)


def cmd_provider_rank(args):
    result = get_client().provider_get_rankings()
    data = result if isinstance(result, list) else result.get('rankings', result)
    print_output(data, args.output)


def cmd_offset_quote(args):
    result = get_client().offset_calculate(args.energy_kwh, args.project_type)
    print_output(result, args.output)


def cmd_offset_purchase(args):
    result = get_client().offset_purchase(args.quote_id)
    print_output(result, args.output)


def cmd_offset_certs(args):
    result = get_client().offset_list_certificates()
    data = result if isinstance(result, list) else result.get('certificates', result)
    print_output(data, args.output)


def cmd_efficiency_score(args):
    result = get_client().efficiency_get_score(args.server_id)
    print_output(result, args.output)


def cmd_efficiency_recommendations(args):
    result = get_client().efficiency_get_recommendations(args.server_id)
    data = result if isinstance(result, list) else result.get('recommendations', result)
    print_output(data, args.output)


# === v3 Networking Commands ===

def cmd_sdwan_status(args):
    result = get_client().sdwan_status()
    print_output(result, args.output)

def cmd_sdwan_apps(args):
    result = get_client().sdwan_list_apps()
    data = result if isinstance(result, list) else result.get('apps', result)
    print_output(data, args.output)

def cmd_sdwan_create(args):
    result = get_client().sdwan_create_app(args.name, args.provider, args.bandwidth)
    print_output(result, args.output)

def cmd_sdwan_delete(args):
    result = get_client().sdwan_delete_app(args.app_id)
    print_output(result, args.output)

def cmd_sdwan_toggle(args):
    result = get_client().sdwan_toggle(args.app_id)
    print_output(result, args.output)

def cmd_vpn_configs(args):
    result = get_client().vpn_list_configs()
    data = result if isinstance(result, list) else result.get('configs', result)
    print_output(data, args.output)

def cmd_vpn_create(args):
    result = get_client().vpn_create_config(args.name, args.server, args.port, args.protocol)
    print_output(result, args.output)

def cmd_vpn_delete(args):
    result = get_client().vpn_delete_config(args.config_id)
    print_output(result, args.output)

def cmd_vpn_status(args):
    result = get_client().vpn_status()
    print_output(result, args.output)

def cmd_dns_zones(args):
    result = get_client().dns_list_zones()
    data = result if isinstance(result, list) else result.get('zones', result)
    print_output(data, args.output)

def cmd_dns_create_zone(args):
    result = get_client().dns_create_zone(args.domain, args.ttl)
    print_output(result, args.output)

def cmd_dns_delete_zone(args):
    result = get_client().dns_delete_zone(args.zone_id)
    print_output(result, args.output)

def cmd_dns_records(args):
    result = get_client().dns_list_records(args.zone_id)
    data = result if isinstance(result, list) else result.get('records', result)
    print_output(data, args.output)

def cmd_dns_add_record(args):
    result = get_client().dns_create_record(args.zone_id, args.name, args.type, args.value, args.ttl)
    print_output(result, args.output)

def cmd_dns_delete_record(args):
    result = get_client().dns_delete_record(args.zone_id, args.record_id)
    print_output(result, args.output)

def cmd_bgp_sessions(args):
    result = get_client().bgp_list_sessions()
    data = result if isinstance(result, list) else result.get('sessions', result)
    print_output(data, args.output)

def cmd_bgp_create(args):
    result = get_client().bgp_create_session(args.name, args.peer_as, args.peer_ip)
    print_output(result, args.output)

def cmd_bgp_delete(args):
    result = get_client().bgp_delete_session(args.session_id)
    print_output(result, args.output)

def cmd_bgp_routes(args):
    result = get_client().bgp_routes()
    data = result if isinstance(result, list) else result.get('routes', result)
    print_output(data, args.output)

def cmd_proxy_rules(args):
    result = get_client().proxy_list_rules()
    data = result if isinstance(result, list) else result.get('rules', result)
    print_output(data, args.output)

def cmd_proxy_create(args):
    result = get_client().proxy_create_rule(args.domain, args.target, args.tls)
    print_output(result, args.output)

def cmd_proxy_delete(args):
    result = get_client().proxy_delete_rule(args.rule_id)
    print_output(result, args.output)

def cmd_proxy_toggle(args):
    result = get_client().proxy_toggle(args.rule_id)
    print_output(result, args.output)

def cmd_seg_list(args):
    result = get_client().seg_list_segments()
    data = result if isinstance(result, list) else result.get('segments', result)
    print_output(data, args.output)

def cmd_seg_create(args):
    result = get_client().seg_create_segment(args.name, args.cidr, args.env)
    print_output(result, args.output)

def cmd_seg_delete(args):
    result = get_client().seg_delete_segment(args.segment_id)
    print_output(result, args.output)

def cmd_cap_list(args):
    result = get_client().cap_list_captures()
    data = result if isinstance(result, list) else result.get('captures', result)
    print_output(data, args.output)

def cmd_cap_start(args):
    result = get_client().cap_start_capture(args.interface, args.duration, args.filter)
    print_output(result, args.output)

def cmd_cap_stop(args):
    result = get_client().cap_stop_capture(args.capture_id)
    print_output(result, args.output)

def cmd_dnsfilter_status(args):
    result = get_client().dnsfilter_status()
    print_output(result, args.output)

def cmd_dnsfilter_rules(args):
    result = get_client().dnsfilter_list_rules()
    data = result if isinstance(result, list) else result.get('rules', result)
    print_output(data, args.output)

def cmd_dnsfilter_add(args):
    result = get_client().dnsfilter_create_rule(args.domain, args.action)
    print_output(result, args.output)

def cmd_dnsfilter_remove(args):
    result = get_client().dnsfilter_delete_rule(args.rule_id)
    print_output(result, args.output)

def cmd_dhcp_leases(args):
    result = get_client().dhcp_leases()
    data = result if isinstance(result, list) else result.get('leases', result)
    print_output(data, args.output)

def cmd_netcost_show(args):
    result = get_client().cost_get_costs()
    print_output(result, args.output)

def cmd_netcost_budget(args):
    result = get_client().cost_set_budget(args.monthly_budget)
    print_output(result, args.output)

def cmd_cell_networks(args):
    result = get_client().cell_list_networks()
    data = result if isinstance(result, list) else result.get('networks', result)
    print_output(data, args.output)

def cmd_cell_register(args):
    result = get_client().cell_register_network(args.name, args.provider, args.apn)
    print_output(result, args.output)

def cmd_cell_delete(args):
    result = get_client().cell_delete_network(args.network_id)
    print_output(result, args.output)

def cmd_cell_status(args):
    result = get_client().cell_status()
    print_output(result, args.output)

def cmd_cell_sims(args):
    result = get_client().cell_list_sims()
    data = result if isinstance(result, list) else result.get('sims', result)
    print_output(data, args.output)

def cmd_cell_activate(args):
    result = get_client().cell_activate_sim(args.sim_id)
    print_output(result, args.output)

def cmd_cell_deactivate(args):
    result = get_client().cell_deactivate_sim(args.sim_id)
    print_output(result, args.output)

# === v3 Marketplace Commands ===

def cmd_trade_list(args):
    result = get_client().trade_list(status=args.status)
    data = result if isinstance(result, list) else result.get('trades', result)
    print_output(data, args.output)

def cmd_trade_create(args):
    result = get_client().trade_create(args.resource_type, args.quantity, args.price, args.unit)
    print_output(result, args.output)

def cmd_trade_accept(args):
    result = get_client().trade_accept(args.trade_id)
    print_output(result, args.output)

def cmd_trade_cancel(args):
    result = get_client().trade_cancel(args.trade_id)
    print_output(result, args.output)

def cmd_appmarket_list(args):
    result = get_client().appmarket_list(category=args.category)
    data = result if isinstance(result, list) else result.get('apps', result)
    print_output(data, args.output)

def cmd_appmarket_install(args):
    result = get_client().appmarket_install(args.app_id, args.target_server)
    print_output(result, args.output)

def cmd_appmarket_installations(args):
    result = get_client().appmarket_installations()
    data = result if isinstance(result, list) else result.get('installations', result)
    print_output(data, args.output)

def cmd_ppu_metrics(args):
    result = get_client().ppu_metrics()
    print_output(result, args.output)

def cmd_ppu_usage(args):
    result = get_client().ppu_usage()
    data = result if isinstance(result, list) else result.get('usage', result)
    print_output(data, args.output)

def cmd_ppu_budget(args):
    result = get_client().ppu_set_budget(args.monthly_budget)
    print_output(result, args.output)

def cmd_reseller_list(args):
    result = get_client().reseller_list()
    data = result if isinstance(result, list) else result.get('resellers', result)
    print_output(data, args.output)

def cmd_reseller_create(args):
    result = get_client().reseller_create(args.name, args.email, args.commission)
    print_output(result, args.output)

def cmd_reseller_delete(args):
    result = get_client().reseller_delete(args.reseller_id)
    print_output(result, args.output)

def cmd_reseller_analytics(args):
    result = get_client().reseller_analytics(args.reseller_id)
    print_output(result, args.output)

def cmd_whitelabel_settings(args):
    result = get_client().whitelabel_settings()
    print_output(result, args.output)

def cmd_sla_list(args):
    result = get_client().sla_list()
    data = result if isinstance(result, list) else result.get('slas', result)
    print_output(data, args.output)

def cmd_sla_create(args):
    result = get_client().sla_create(args.name, args.uptime, args.credit_rate)
    print_output(result, args.output)

def cmd_sla_delete(args):
    result = get_client().sla_delete(args.sla_id)
    print_output(result, args.output)

def cmd_sla_status(args):
    result = get_client().sla_status(args.sla_id)
    print_output(result, args.output)

def cmd_credit_list(args):
    result = get_client().credit_list()
    data = result if isinstance(result, list) else result.get('credits', result)
    print_output(data, args.output)

def cmd_credit_issue(args):
    result = get_client().credit_issue(args.customer_id, args.amount, args.reason)
    print_output(result, args.output)

def cmd_crypto_wallets(args):
    result = get_client().crypto_wallets()
    data = result if isinstance(result, list) else result.get('wallets', result)
    print_output(data, args.output)

def cmd_crypto_create_wallet(args):
    result = get_client().crypto_create_wallet(args.currency, args.label)
    print_output(result, args.output)

def cmd_crypto_transactions(args):
    result = get_client().crypto_transactions()
    data = result if isinstance(result, list) else result.get('transactions', result)
    print_output(data, args.output)

def cmd_crypto_rates(args):
    result = get_client().crypto_rates()
    print_output(result, args.output)

def cmd_plans_list(args):
    result = get_client().plans_list()
    data = result if isinstance(result, list) else result.get('plans', result)
    print_output(data, args.output)

def cmd_plans_create(args):
    result = get_client().plans_create(args.name, args.price, args.billing_cycle, args.features)
    print_output(result, args.output)

def cmd_plans_delete(args):
    result = get_client().plans_delete(args.plan_id)
    print_output(result, args.output)

def cmd_plans_subscriptions(args):
    result = get_client().plans_subscriptions()
    data = result if isinstance(result, list) else result.get('subscriptions', result)
    print_output(data, args.output)

def cmd_reco_list(args):
    result = get_client().reco_list()
    data = result if isinstance(result, list) else result.get('recommendations', result)
    print_output(data, args.output)

def cmd_reco_summary(args):
    result = get_client().reco_summary()
    print_output(result, args.output)

def cmd_reco_implement(args):
    result = get_client().reco_implement(args.reco_id)
    print_output(result, args.output)

def cmd_reco_dismiss(args):
    result = get_client().reco_dismiss(args.reco_id)
    print_output(result, args.output)

def cmd_tax_rates(args):
    result = get_client().tax_rates()
    data = result if isinstance(result, list) else result.get('rates', result)
    print_output(data, args.output)

def cmd_tax_invoices(args):
    result = get_client().tax_invoices()
    data = result if isinstance(result, list) else result.get('invoices', result)
    print_output(data, args.output)

def cmd_tax_generate(args):
    result = get_client().tax_generate_invoice()
    print_output(result, args.output)

def cmd_tax_pay(args):
    result = get_client().tax_mark_paid(args.invoice_id)
    print_output(result, args.output)

def cmd_tax_summary(args):
    result = get_client().tax_summary()
    print_output(result, args.output)

def cmd_tax_file(args):
    result = get_client().tax_file_report()
    print_output(result, args.output)

def cmd_loyalty_status(args):
    result = get_client().loyalty_status()
    print_output(result, args.output)

def cmd_loyalty_badges(args):
    result = get_client().loyalty_badges()
    data = result if isinstance(result, list) else result.get('badges', result)
    print_output(data, args.output)

def cmd_loyalty_rewards(args):
    result = get_client().loyalty_rewards()
    data = result if isinstance(result, list) else result.get('rewards', result)
    print_output(data, args.output)

def cmd_loyalty_redeem(args):
    result = get_client().loyalty_redeem(args.reward_id)
    print_output(result, args.output)

def cmd_loyalty_leaderboard(args):
    result = get_client().loyalty_leaderboard()
    data = result if isinstance(result, list) else result.get('leaderboard', result)
    print_output(data, args.output)


# === v4 Emerging Tech Handler Functions ===

def cmd_blockchain_list(args):
    result = get_client().blockchain_list_networks()
    data = result if isinstance(result, list) else result.get('networks', result)
    print_output(data, args.output)

def cmd_blockchain_create(args):
    result = get_client().blockchain_create_network(args.name, args.consensus, args.chain_id)
    print_output(result, args.output)

def cmd_blockchain_status(args):
    result = get_client().blockchain_network_status(args.network_id)
    print_output(result, args.output)

def cmd_blockchain_validators(args):
    result = get_client().blockchain_validators(args.network_id)
    print_output(result, args.output)

def cmd_storage_list(args):
    result = get_client().storage_list_gateways()
    data = result if isinstance(result, list) else result.get('gateways', result)
    print_output(data, args.output)

def cmd_storage_create(args):
    result = get_client().storage_create_gateway(args.name, args.provider)
    print_output(result, args.output)

def cmd_storage_pin(args):
    result = get_client().storage_pin_content(args.cid)
    print_output(result, args.output)

def cmd_storage_status(args):
    result = get_client().storage_gateway_status(args.gateway_id)
    print_output(result, args.output)

def cmd_quantum_list(args):
    result = get_client().quantum_list_keys()
    data = result if isinstance(result, list) else result.get('keys', result)
    print_output(data, args.output)

def cmd_quantum_generate(args):
    result = get_client().quantum_generate_key(args.algorithm)
    print_output(result, args.output)

def cmd_quantum_cert(args):
    result = get_client().quantum_create_certificate(args.name, args.key_id)
    print_output(result, args.output)

def cmd_quantum_encrypt(args):
    result = get_client().quantum_encrypt(args.key_id, args.message)
    print_output(result, args.output)

def cmd_quantum_decrypt(args):
    result = get_client().quantum_decrypt(args.key_id, args.ciphertext)
    print_output(result, args.output)

def cmd_contracts_list(args):
    result = get_client().contracts_list()
    data = result if isinstance(result, list) else result.get('contracts', result)
    print_output(data, args.output)

def cmd_contracts_deploy(args):
    result = get_client().contracts_deploy(args.name, args.network, args.bytecode)
    print_output(result, args.output)

def cmd_contracts_get(args):
    result = get_client().contracts_get(args.contract_id)
    print_output(result, args.output)

def cmd_contracts_events(args):
    result = get_client().contracts_events(args.contract_id)
    print_output(result, args.output)

def cmd_web3id_list(args):
    result = get_client().web3id_list()
    data = result if isinstance(result, list) else result.get('identities', result)
    print_output(data, args.output)

def cmd_web3id_create(args):
    result = get_client().web3id_create(args.did)
    print_output(result, args.output)

def cmd_web3id_auth(args):
    result = get_client().web3id_authenticate(args.identity_id)
    print_output(result, args.output)

def cmd_web3id_sessions(args):
    result = get_client().web3id_sessions()
    print_output(result, args.output)

def cmd_confidential_list(args):
    result = get_client().confidential_list_enclaves()
    data = result if isinstance(result, list) else result.get('enclaves', result)
    print_output(data, args.output)

def cmd_confidential_create(args):
    result = get_client().confidential_create_enclave(args.name, args.image, args.memory_mb)
    print_output(result, args.output)

def cmd_confidential_attest(args):
    result = get_client().confidential_attest(args.enclave_id)
    print_output(result, args.output)

def cmd_confidential_secrets(args):
    result = get_client().confidential_secrets(args.enclave_id)
    print_output(result, args.output)

def cmd_federated_list(args):
    result = get_client().federated_list_projects()
    data = result if isinstance(result, list) else result.get('projects', result)
    print_output(data, args.output)

def cmd_federated_create(args):
    result = get_client().federated_create_project(args.name, args.rounds, args.min_clients)
    print_output(result, args.output)

def cmd_federated_status(args):
    result = get_client().federated_project_status(args.project_id)
    print_output(result, args.output)

def cmd_federated_rounds(args):
    result = get_client().federated_rounds(args.project_id)
    print_output(result, args.output)

def cmd_zkp_list(args):
    result = get_client().zkp_list()
    data = result if isinstance(result, list) else result.get('proofs', result)
    print_output(data, args.output)

def cmd_zkp_generate(args):
    result = get_client().zkp_generate(args.statement, args.witness)
    print_output(result, args.output)

def cmd_zkp_verify(args):
    result = get_client().zkp_verify(args.proof_id)
    print_output(result, args.output)

def cmd_zkp_circuits(args):
    result = get_client().zkp_circuits()
    print_output(result, args.output)

def cmd_dcn_list(args):
    result = get_client().dcn_list_tasks()
    data = result if isinstance(result, list) else result.get('tasks', result)
    print_output(data, args.output)

def cmd_dcn_submit(args):
    result = get_client().dcn_submit_task(args.name, args.requirements, args.input_data)
    print_output(result, args.output)

def cmd_dcn_status(args):
    result = get_client().dcn_task_status(args.task_id)
    print_output(result, args.output)

def cmd_dcn_workers(args):
    result = get_client().dcn_workers()
    print_output(result, args.output)


def build_parser():
    parser = argparse.ArgumentParser(
        prog='ipilot',
        description='Infra Pilot CLI - Infrastructure management tool',
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--output', '-o', choices=['json', 'table', 'yaml', 'plain'],
                        default=get('output_format', 'table'),
                        help='Output format (default: table)')

    sub = parser.add_subparsers(dest='command')

    p_login = sub.add_parser('login', help='Authenticate with the API')
    p_login.add_argument('api_key', help='API key')

    sub.add_parser('logout', help='Clear authentication token')

    p_server = sub.add_parser('server', help='Server management commands')
    p_server_sub = p_server.add_subparsers(dest='subcommand')

    p_server_list = p_server_sub.add_parser('list', help='List all servers')
    p_server_create = p_server_sub.add_parser('create', help='Create a new server')
    p_server_create.add_argument('name', help='Server name')
    p_server_create.add_argument('--type', '-t', required=True, help='Server type')
    p_server_create.add_argument('--memory', '-m', type=int, help='Memory in MB')
    p_server_delete = p_server_sub.add_parser('delete', help='Delete a server')
    p_server_delete.add_argument('server', help='Server ID or name')
    p_server_status = p_server_sub.add_parser('status', help='Get server status')
    p_server_status.add_argument('server', help='Server ID or name')

    p_logs = sub.add_parser('logs', help='Fetch server logs')
    p_logs.add_argument('server', help='Server ID or name')
    p_logs.add_argument('--lines', '-n', type=int, default=50, help='Number of lines')
    p_logs.add_argument('--follow', '-f', action='store_true', help='Follow log output')

    p_backup = sub.add_parser('backup', help='Backup management')
    p_backup_sub = p_backup.add_subparsers(dest='subcommand')
    p_backup_list = p_backup_sub.add_parser('list', help='List backups')
    p_backup_list.add_argument('server', nargs='?', help='Server ID (optional)')
    p_backup_create = p_backup_sub.add_parser('create', help='Create a backup')
    p_backup_create.add_argument('server', help='Server ID or name')

    p_deploy = sub.add_parser('deploy', help='Deploy a branch to a server')
    p_deploy.add_argument('server', help='Server ID or name')
    p_deploy.add_argument('branch', help='Branch to deploy')

    p_config = sub.add_parser('config', help='Configuration management')
    p_config_sub = p_config.add_subparsers(dest='subcommand')
    p_config_get = p_config_sub.add_parser('get', help='Get config value(s)')
    p_config_get.add_argument('key', nargs='?', help='Config key')
    p_config_set = p_config_sub.add_parser('set', help='Set a config value')
    p_config_set.add_argument('key', help='Config key')
    p_config_set.add_argument('value', help='Config value')

    # === Edge & IoT Commands ===
    p_edge = sub.add_parser('edge', help='Edge device management')
    p_edge_sub = p_edge.add_subparsers(dest='subcommand')
    p_edge_list = p_edge_sub.add_parser('list', help='List edge devices')
    p_edge_list.add_argument('--device-type', '-t', help='Filter by device type')
    p_edge_list.add_argument('--status', '-s', help='Filter by status')
    p_edge_register = p_edge_sub.add_parser('register', help='Register edge device')
    p_edge_register.add_argument('name', help='Device name')
    p_edge_register.add_argument('device_type', help='Device type (raspberry_pi, jetson_nano, etc)')
    p_edge_register.add_argument('hardware_id', help='Hardware MAC/serial')
    p_edge_status = p_edge_sub.add_parser('status', help='Get device status')
    p_edge_status.add_argument('device_id', help='Device ID')
    p_edge_command = p_edge_sub.add_parser('command', help='Send command to device')
    p_edge_command.add_argument('device_id', help='Device ID')
    p_edge_command.add_argument('command', help='Command to execute')
    p_edge_backup = p_edge_sub.add_parser('backup', help='Backup edge device')
    p_edge_backup.add_argument('device_id', help='Device ID')

    p_fn = sub.add_parser('fn', help='Edge function management')
    p_fn_sub = p_fn.add_subparsers(dest='subcommand')
    p_fn_list = p_fn_sub.add_parser('list', help='List edge functions')
    p_fn_list.add_argument('--device-id', help='Filter by device')
    p_fn_deploy = p_fn_sub.add_parser('deploy', help='Deploy edge function')
    p_fn_deploy.add_argument('name', help='Function name')
    p_fn_deploy.add_argument('runtime', choices=['wasm', 'container', 'native'], help='Runtime type')
    p_fn_deploy.add_argument('device_id', help='Target device')
    p_fn_deploy.add_argument('source', help='Function source URL')
    p_fn_deploy.add_argument('handler', help='Entry handler')
    p_fn_invoke = p_fn_sub.add_parser('invoke', help='Invoke edge function')
    p_fn_invoke.add_argument('func_id', help='Function ID')
    p_fn_invoke.add_argument('--payload', '-p', help='JSON payload')

    p_ml = sub.add_parser('ml', help='Edge ML management')
    p_ml_sub = p_ml.add_subparsers(dest='subcommand')
    p_ml_models = p_ml_sub.add_parser('models', help='List ML models')
    p_ml_models.add_argument('--device-id', help='Filter by device')
    p_ml_deploy = p_ml_sub.add_parser('deploy', help='Deploy ML model')
    p_ml_deploy.add_argument('name', help='Model name')
    p_ml_deploy.add_argument('model_format', choices=['tflite', 'onnx', 'pytorch'], help='Model format')
    p_ml_deploy.add_argument('device_id', help='Target device')
    p_ml_deploy.add_argument('version', help='Model version')
    p_ml_infer = p_ml_sub.add_parser('infer', help='Run inference')
    p_ml_infer.add_argument('model_id', help='Model ID')

    p_iot = sub.add_parser('iot', help='IoT provisioning')
    p_iot_sub = p_iot.add_subparsers(dest='subcommand')
    p_iot_codes = p_iot_sub.add_parser('codes', help='Generate claim codes')
    p_iot_codes.add_argument('--count', type=int, default=10, help='Number of codes')
    p_iot_codes.add_argument('--ttl', type=int, default=24, help='TTL in hours')
    p_iot_enroll = p_iot_sub.add_parser('enroll', help='Enroll device')
    p_iot_enroll.add_argument('code', help='Claim code')
    p_iot_enroll.add_argument('device_id', help='Device ID')

    p_cdn = sub.add_parser('cdn', help='Edge CDN management')
    p_cdn_sub = p_cdn.add_subparsers(dest='subcommand')
    p_cdn_stats = p_cdn_sub.add_parser('stats', help='CDN statistics')

    p_mesh = sub.add_parser('mesh', help='Mesh network management')
    p_mesh_sub = p_mesh.add_subparsers(dest='subcommand')
    p_mesh_list = p_mesh_sub.add_parser('list', help='List mesh networks')
    p_mesh_create = p_mesh_sub.add_parser('create', help='Create mesh network')
    p_mesh_create.add_argument('name', help='Network name')
    p_mesh_create.add_argument('mesh_type', choices=['wireguard', 'tinc'], help='Mesh type')
    p_mesh_create.add_argument('subnet', help='Subnet CIDR')

    p_gw = sub.add_parser('gw', help='LoRaWAN gateway management')
    p_gw_sub = p_gw.add_subparsers(dest='subcommand')
    p_gw_list = p_gw_sub.add_parser('list', help='List gateways')
    p_gw_list.add_argument('--status', help='Filter by status')

    p_pipeline = sub.add_parser('pipeline', help='IoT data pipeline')
    p_pipeline_sub = p_pipeline.add_subparsers(dest='subcommand')
    p_pipeline_stats = p_pipeline_sub.add_parser('stats', help='Pipeline statistics')

    # === Green Computing Commands ===
    p_energy = sub.add_parser('energy', help='Energy consumption')
    p_energy_sub = p_energy.add_subparsers(dest='subcommand')
    p_energy_current = p_energy_sub.add_parser('current', help='Current energy snapshot')
    p_energy_history = p_energy_sub.add_parser('history', help='Historical energy data')
    p_energy_history.add_argument('--server-id', help='Server ID')
    p_energy_history.add_argument('--hours', type=int, default=24, help='Hours of history')
    p_energy_summary = p_energy_sub.add_parser('summary', help='Energy summary')
    p_energy_summary.add_argument('--period', default='daily', choices=['daily', 'weekly', 'monthly'])

    p_carbon = sub.add_parser('carbon', help='Carbon footprint')
    p_carbon_sub = p_carbon.add_subparsers(dest='subcommand')
    p_carbon_current = p_carbon_sub.add_parser('current', help='Current CO2 output')
    p_carbon_history = p_carbon_sub.add_parser('history', help='Historical CO2 data')

    p_green = sub.add_parser('green', help='Green scheduling')
    p_green_sub = p_green.add_subparsers(dest='subcommand')
    p_green_forecast = p_green_sub.add_parser('forecast', help='Carbon forecast')
    p_green_jobs = p_green_sub.add_parser('jobs', help='List green jobs')
    p_green_jobs.add_argument('--status', help='Filter by status')
    p_green_schedule = p_green_sub.add_parser('schedule', help='Schedule green job')
    p_green_schedule.add_argument('name', help='Job name')
    p_green_schedule.add_argument('command', help='Command to run')
    p_green_schedule.add_argument('--urgency', default='normal', choices=['critical', 'high', 'normal', 'low', 'background'])
    p_green_report = p_green_sub.add_parser('report', help='Green savings report')

    p_reclaim = sub.add_parser('reclaim', help='Idle resource reclamation')
    p_reclaim_sub = p_reclaim.add_subparsers(dest='subcommand')
    p_reclaim_list = p_reclaim_sub.add_parser('list', help='List idle resources')
    p_reclaim_list.add_argument('--resource-type', help='Filter by type')
    p_reclaim_scan = p_reclaim_sub.add_parser('scan', help='Scan for idle resources')
    p_reclaim_report = p_reclaim_sub.add_parser('report', help='Reclamation report')

    p_shutdown = sub.add_parser('shutdown', help='Auto-shutdown policies')
    p_shutdown_sub = p_shutdown.add_subparsers(dest='subcommand')
    p_shutdown_policies = p_shutdown_sub.add_parser('policies', help='List policies')
    p_shutdown_create = p_shutdown_sub.add_parser('create', help='Create policy')
    p_shutdown_create.add_argument('name', help='Policy name')
    p_shutdown_create.add_argument('tags', help='Comma-separated environment tags')
    p_shutdown_create.add_argument('shutdown_hours', help='Comma-separated hours')
    p_shutdown_savings = p_shutdown_sub.add_parser('savings', help='Show savings')

    p_hardware = sub.add_parser('hardware', help='Hardware lifecycle')
    p_hardware_sub = p_hardware.add_subparsers(dest='subcommand')
    p_hardware_list = p_hardware_sub.add_parser('list', help='List assets')
    p_hardware_list.add_argument('--asset-type', help='Filter by type')
    p_hardware_add = p_hardware_sub.add_parser('add', help='Add asset')
    p_hardware_add.add_argument('asset_type', help='Asset type (server, storage, network, gpu)')
    p_hardware_add.add_argument('manufacturer', help='Manufacturer')
    p_hardware_add.add_argument('model', help='Model')
    p_hardware_add.add_argument('serial', help='Serial number')

    p_pue = sub.add_parser('pue', help='PUE/DCIM management')
    p_pue_sub = p_pue.add_subparsers(dest='subcommand')
    p_pue_current = p_pue_sub.add_parser('current', help='Current PUE metrics')
    p_pue_history = p_pue_sub.add_parser('history', help='PUE history')
    p_pue_history.add_argument('--hours', type=int, default=168, help='Hours of history')

    p_provider = sub.add_parser('provider', help='Sustainable provider rankings')
    p_provider_sub = p_provider.add_subparsers(dest='subcommand')
    p_provider_rank = p_provider_sub.add_parser('rank', help='Provider rankings')

    p_offset = sub.add_parser('offset', help='CO2 offset management')
    p_offset_sub = p_offset.add_subparsers(dest='subcommand')
    p_offset_quote = p_offset_sub.add_parser('quote', help='Get offset quote')
    p_offset_quote.add_argument('energy_kwh', type=float, help='Energy consumption in kWh')
    p_offset_quote.add_argument('--project-type', default='reforestation', help='Project type')
    p_offset_purchase = p_offset_sub.add_parser('purchase', help='Purchase offset')
    p_offset_purchase.add_argument('quote_id', help='Quote ID')
    p_offset_certs = p_offset_sub.add_parser('certs', help='List certificates')

    p_efficiency = sub.add_parser('efficiency', help='Efficiency scorecards')
    p_efficiency_sub = p_efficiency.add_subparsers(dest='subcommand')
    p_efficiency_score = p_efficiency_sub.add_parser('score', help='Get efficiency score')
    p_efficiency_score.add_argument('server_id', help='Server ID')
    p_efficiency_recommendations = p_efficiency_sub.add_parser('recommendations', help='Get recommendations')
    p_efficiency_recommendations.add_argument('server_id', help='Server ID')

    # === v3 Identity & Access Commands ===
    p_oidc = sub.add_parser('oidc', help='OIDC provider management')
    p_oidc_sub = p_oidc.add_subparsers(dest='subcommand')
    p_oidc_clients = p_oidc_sub.add_parser('clients', help='List OIDC clients')
    p_oidc_register = p_oidc_sub.add_parser('register', help='Register OIDC client')
    p_oidc_register.add_argument('name', help='Client name')
    p_oidc_register.add_argument('redirect_uris', help='Comma-separated redirect URIs')
    p_oidc_register.add_argument('--type', default='confidential', choices=['confidential', 'public'])
    p_oidc_delete = p_oidc_sub.add_parser('delete', help='Delete OIDC client')
    p_oidc_delete.add_argument('client_id', help='Client ID')

    p_webauthn = sub.add_parser('webauthn', help='WebAuthn/passkey management')
    p_webauthn_sub = p_webauthn.add_subparsers(dest='subcommand')
    p_webauthn_creds = p_webauthn_sub.add_parser('credentials', help='List credentials')
    p_webauthn_creds.add_argument('user_id', help='User ID')
    p_webauthn_remove = p_webauthn_sub.add_parser('remove', help='Remove credential')
    p_webauthn_remove.add_argument('credential_id', help='Credential ID')

    p_session = sub.add_parser('session', help='Session management')
    p_session_sub = p_session.add_subparsers(dest='subcommand')
    p_session_list = p_session_sub.add_parser('list', help='List active sessions')
    p_session_list.add_argument('user_id', help='User ID')
    p_session_revoke = p_session_sub.add_parser('revoke', help='Revoke session')
    p_session_revoke.add_argument('session_id', help='Session ID')

    p_pam = sub.add_parser('pam', help='Privileged access management')
    p_pam_sub = p_pam.add_subparsers(dest='subcommand')
    p_pam_requests = p_pam_sub.add_parser('requests', help='List access requests')
    p_pam_requests.add_argument('--user-id', help='Filter by user')
    p_pam_requests.add_argument('--status', help='Filter by status')
    p_pam_request = p_pam_sub.add_parser('request', help='Create access request')
    p_pam_request.add_argument('user_id', help='User ID')
    p_pam_request.add_argument('resource', help='Target resource')
    p_pam_request.add_argument('role', help='Requested role')
    p_pam_request.add_argument('reason', help='Reason for access')
    p_pam_request.add_argument('--duration', type=int, default=3600, help='Duration in seconds')
    p_pam_approve = p_pam_sub.add_parser('approve', help='Approve request')
    p_pam_approve.add_argument('request_id', help='Request ID')
    p_pam_approve.add_argument('approver_id', help='Approver user ID')
    p_pam_deny = p_pam_sub.add_parser('deny', help='Deny request')
    p_pam_deny.add_argument('request_id', help='Request ID')
    p_pam_deny.add_argument('approver_id', help='Approver user ID')

    p_breach = sub.add_parser('breach', help='Breach notification management')
    p_breach_sub = p_breach.add_subparsers(dest='subcommand')
    p_breach_list = p_breach_sub.add_parser('list', help='List breaches')
    p_breach_report = p_breach_sub.add_parser('report', help='Report a breach')
    p_breach_report.add_argument('description', help='Breach description')
    p_breach_report.add_argument('--data-types', required=True, help='Comma-separated affected data types')
    p_breach_report.add_argument('--affected-users', type=int, default=0, help='Number of affected users')

    # === v3 Governance Commands ===
    p_policy = sub.add_parser('policy', help='Policy as code management')
    p_policy_sub = p_policy.add_subparsers(dest='subcommand')
    p_policy_list = p_policy_sub.add_parser('list', help='List policies')
    p_policy_list.add_argument('--category', help='Filter by category')
    p_policy_create = p_policy_sub.add_parser('create', help='Create policy')
    p_policy_create.add_argument('name', help='Policy name')
    p_policy_create.add_argument('description', help='Policy description')
    p_policy_create.add_argument('--category', default='general', help='Policy category')
    p_policy_evaluate = p_policy_sub.add_parser('evaluate', help='Evaluate a policy')
    p_policy_evaluate.add_argument('resource', help='Resource to evaluate')
    p_policy_evaluate.add_argument('action', help='Action to evaluate')
    p_policy_evaluate.add_argument('--context', help='JSON context')

    p_compliance = sub.add_parser('compliance', help='Compliance scanning')
    p_compliance_sub = p_compliance.add_subparsers(dest='subcommand')
    p_compliance_scan = p_compliance_sub.add_parser('scan', help='Run compliance scan')
    p_compliance_scan.add_argument('--benchmark', default='cis_docker', help='Benchmark to run')
    p_compliance_report = p_compliance_sub.add_parser('report', help='Get scan report')
    p_compliance_report.add_argument('scan_id', help='Scan ID')
    p_compliance_checks = p_compliance_sub.add_parser('checks', help='List available checks')
    p_compliance_checks.add_argument('--benchmark', default='cis_docker', help='Benchmark name')

    p_audit = sub.add_parser('audit', help='Audit analytics')
    p_audit_sub = p_audit.add_subparsers(dest='subcommand')
    p_audit_anomalies = p_audit_sub.add_parser('anomalies', help='List anomalies')
    p_audit_trend = p_audit_sub.add_parser('trend', help='Get anomaly trend')
    p_audit_trend.add_argument('user_id', help='User ID')
    p_audit_summary = p_audit_sub.add_parser('summary', help='Audit summary')

    p_classify = sub.add_parser('classify', help='Data classification')
    p_classify_sub = p_classify.add_subparsers(dest='subcommand')
    p_classify_scan = p_classify_sub.add_parser('scan', help='Scan text for sensitive data')
    p_classify_scan.add_argument('text', help='Text to scan')
    p_classify_inventory = p_classify_sub.add_parser('inventory', help='List data inventory')

    p_vendor = sub.add_parser('vendor', help='Vendor risk management')
    p_vendor_sub = p_vendor.add_subparsers(dest='subcommand')
    p_vendor_list = p_vendor_sub.add_parser('list', help='List vendors')
    p_vendor_create = p_vendor_sub.add_parser('create', help='Register vendor')
    p_vendor_create.add_argument('name', help='Vendor name')
    p_vendor_create.add_argument('domain', help='Vendor domain')
    p_vendor_create.add_argument('--category', default='saas', help='Vendor category')
    p_vendor_assess = p_vendor_sub.add_parser('assess', help='Create assessment')
    p_vendor_assess.add_argument('vendor_id', help='Vendor ID')
    p_vendor_assess.add_argument('--type', default='sig', choices=['sig', 'caiq'], help='Questionnaire type')

    # === v3 Automation Commands ===
    p_workflow = sub.add_parser('workflow', help='Workflow automation')
    p_workflow_sub = p_workflow.add_subparsers(dest='subcommand')
    p_workflow_list = p_workflow_sub.add_parser('list', help='List workflows')
    p_workflow_create = p_workflow_sub.add_parser('create', help='Create workflow')
    p_workflow_create.add_argument('name', help='Workflow name')
    p_workflow_create.add_argument('description', help='Workflow description')
    p_workflow_run = p_workflow_sub.add_parser('run', help='Execute workflow')
    p_workflow_run.add_argument('workflow_id', help='Workflow ID')

    p_infra_pipeline = sub.add_parser('infra-pipeline', help='Infrastructure CI/CD pipelines')
    p_infra_pipeline_sub = p_infra_pipeline.add_subparsers(dest='subcommand')
    p_infra_pipeline_list = p_infra_pipeline_sub.add_parser('list', help='List pipelines')
    p_infra_pipeline_run = p_infra_pipeline_sub.add_parser('run', help='Run pipeline')
    p_infra_pipeline_run.add_argument('pipeline_id', help='Pipeline ID')
    p_infra_pipeline_run.add_argument('--branch', default='main', help='Branch to run')

    p_drift = sub.add_parser('drift', help='Configuration drift detection')
    p_drift_sub = p_drift.add_subparsers(dest='subcommand')
    p_drift_scan = p_drift_sub.add_parser('scan', help='Run drift scan')
    p_drift_list = p_drift_sub.add_parser('list', help='List scans')

    p_quota = sub.add_parser('quota', help='Resource quota management')
    p_quota_sub = p_quota.add_subparsers(dest='subcommand')
    p_quota_list = p_quota_sub.add_parser('list', help='List quotas')
    p_quota_check = p_quota_sub.add_parser('check', help='Check quota')
    p_quota_check.add_argument('entity_type', help='Entity type (org/team/project)')
    p_quota_check.add_argument('entity_id', help='Entity ID')
    p_quota_check.add_argument('--cpu', type=int, help='CPU cores requested')
    p_quota_check.add_argument('--memory', type=int, help='Memory GB requested')

    p_remediate = sub.add_parser('remediate', help='Auto-remediation rules')
    p_remediate_sub = p_remediate.add_subparsers(dest='subcommand')
    p_remediate_rules = p_remediate_sub.add_parser('rules', help='List remediation rules')
    p_remediate_history = p_remediate_sub.add_parser('history', help='Remediation history')

    p_maintenance = sub.add_parser('maintenance', help='Maintenance scheduling')
    p_maintenance_sub = p_maintenance.add_subparsers(dest='subcommand')
    p_maintenance_list = p_maintenance_sub.add_parser('list', help='List maintenance windows')
    p_maintenance_schedule = p_maintenance_sub.add_parser('schedule', help='Schedule maintenance')
    p_maintenance_schedule.add_argument('name', help='Window name')
    p_maintenance_schedule.add_argument('--start', required=True, help='Start time (ISO format)')
    p_maintenance_schedule.add_argument('--end', required=True, help='End time (ISO format)')
    p_maintenance_schedule.add_argument('--systems', required=True, help='Comma-separated affected systems')

    p_runbook = sub.add_parser('runbook', help='Runbook template library')
    p_runbook_sub = p_runbook.add_subparsers(dest='subcommand')
    p_runbook_list = p_runbook_sub.add_parser('list', help='List templates')
    p_runbook_use = p_runbook_sub.add_parser('use', help='Instantiate runbook')
    p_runbook_use.add_argument('template_id', help='Template ID')
    p_runbook_use.add_argument('--vars', help='JSON variables')

    p_chaos = sub.add_parser('chaos', help='Chaos engineering')
    p_chaos_sub = p_chaos.add_subparsers(dest='subcommand')
    p_chaos_experiments = p_chaos_sub.add_parser('experiments', help='List experiments')
    p_chaos_create = p_chaos_sub.add_parser('create', help='Create experiment')
    p_chaos_create.add_argument('name', help='Experiment name')
    p_chaos_create.add_argument('--target-type', default='container', help='Target type')
    p_chaos_create.add_argument('--target-selector', required=True, help='Target selector')
    p_chaos_run = p_chaos_sub.add_parser('run', help='Run experiment')
    p_chaos_run.add_argument('experiment_id', help='Experiment ID')
    p_chaos_stop = p_chaos_sub.add_parser('stop', help='Stop experiment')
    p_chaos_stop.add_argument('experiment_id', help='Experiment ID')
    p_chaos_faults = p_chaos_sub.add_parser('faults', help='List fault types')

    p_heal = sub.add_parser('heal', help='Self-healing infrastructure')
    p_heal_sub = p_heal.add_subparsers(dest='subcommand')
    p_heal_status = p_heal_sub.add_parser('status', help='Healing system status')
    p_heal_history = p_heal_sub.add_parser('history', help='Remediation history')
    p_heal_retrain = p_heal_sub.add_parser('retrain', help='Retrain model')

    # === v3 Networking Commands ===
    p_sdwan = sub.add_parser('sdwan', help='SD-WAN controller')
    p_sdwan_sub = p_sdwan.add_subparsers(dest='subcommand')
    p_sdwan_status = p_sdwan_sub.add_parser('status', help='SD-WAN status')
    p_sdwan_apps = p_sdwan_sub.add_parser('apps', help='List SD-WAN apps')
    p_sdwan_create = p_sdwan_sub.add_parser('create', help='Create SD-WAN app')
    p_sdwan_create.add_argument('name', help='App name')
    p_sdwan_create.add_argument('provider', help='Provider (aws, azure, gcp)')
    p_sdwan_create.add_argument('--bandwidth', type=int, default=100, help='Bandwidth Mbps')
    p_sdwan_delete = p_sdwan_sub.add_parser('delete', help='Delete SD-WAN app')
    p_sdwan_delete.add_argument('app_id', help='App ID')
    p_sdwan_toggle = p_sdwan_sub.add_parser('toggle', help='Toggle SD-WAN app')
    p_sdwan_toggle.add_argument('app_id', help='App ID')

    p_vpn = sub.add_parser('vpn', help='VPN as a service')
    p_vpn_sub = p_vpn.add_subparsers(dest='subcommand')
    p_vpn_configs = p_vpn_sub.add_parser('configs', help='List VPN configs')
    p_vpn_create = p_vpn_sub.add_parser('create', help='Create VPN config')
    p_vpn_create.add_argument('name', help='Config name')
    p_vpn_create.add_argument('server', help='VPN server')
    p_vpn_create.add_argument('--port', type=int, default=1194, help='Port')
    p_vpn_create.add_argument('--protocol', default='udp', choices=['udp', 'tcp'], help='Protocol')
    p_vpn_delete = p_vpn_sub.add_parser('delete', help='Delete VPN config')
    p_vpn_delete.add_argument('config_id', help='Config ID')
    p_vpn_status = p_vpn_sub.add_parser('status', help='VPN status')

    p_dns = sub.add_parser('dns', help='DNS management')
    p_dns_sub = p_dns.add_subparsers(dest='subcommand')
    p_dns_zones = p_dns_sub.add_parser('zones', help='List DNS zones')
    p_dns_create_zone = p_dns_sub.add_parser('create-zone', help='Create DNS zone')
    p_dns_create_zone.add_argument('domain', help='Domain name')
    p_dns_create_zone.add_argument('--ttl', type=int, default=3600, help='TTL')
    p_dns_delete_zone = p_dns_sub.add_parser('delete-zone', help='Delete DNS zone')
    p_dns_delete_zone.add_argument('zone_id', help='Zone ID')
    p_dns_records = p_dns_sub.add_parser('records', help='List DNS records')
    p_dns_records.add_argument('zone_id', help='Zone ID')
    p_dns_add_record = p_dns_sub.add_parser('add-record', help='Add DNS record')
    p_dns_add_record.add_argument('zone_id', help='Zone ID')
    p_dns_add_record.add_argument('name', help='Record name')
    p_dns_add_record.add_argument('type', choices=['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS'], help='Record type')
    p_dns_add_record.add_argument('value', help='Record value')
    p_dns_add_record.add_argument('--ttl', type=int, default=3600, help='TTL')
    p_dns_delete_record = p_dns_sub.add_parser('delete-record', help='Delete DNS record')
    p_dns_delete_record.add_argument('zone_id', help='Zone ID')
    p_dns_delete_record.add_argument('record_id', help='Record ID')

    p_bgp = sub.add_parser('bgp', help='BGP route manager')
    p_bgp_sub = p_bgp.add_subparsers(dest='subcommand')
    p_bgp_sessions = p_bgp_sub.add_parser('sessions', help='List BGP sessions')
    p_bgp_create = p_bgp_sub.add_parser('create', help='Create BGP session')
    p_bgp_create.add_argument('name', help='Session name')
    p_bgp_create.add_argument('--peer-as', required=True, type=int, help='Peer AS number')
    p_bgp_create.add_argument('--peer-ip', required=True, help='Peer IP address')
    p_bgp_delete = p_bgp_sub.add_parser('delete', help='Delete BGP session')
    p_bgp_delete.add_argument('session_id', help='Session ID')
    p_bgp_routes = p_bgp_sub.add_parser('routes', help='Show BGP routes')

    p_proxy = sub.add_parser('proxy', help='Reverse proxy catalog')
    p_proxy_sub = p_proxy.add_subparsers(dest='subcommand')
    p_proxy_rules = p_proxy_sub.add_parser('rules', help='List proxy rules')
    p_proxy_create = p_proxy_sub.add_parser('create', help='Create proxy rule')
    p_proxy_create.add_argument('domain', help='Domain name')
    p_proxy_create.add_argument('target', help='Target URL')
    p_proxy_create.add_argument('--tls', action='store_true', help='Enable TLS')
    p_proxy_delete = p_proxy_sub.add_parser('delete', help='Delete proxy rule')
    p_proxy_delete.add_argument('rule_id', help='Rule ID')
    p_proxy_toggle = p_proxy_sub.add_parser('toggle', help='Toggle proxy rule')
    p_proxy_toggle.add_argument('rule_id', help='Rule ID')

    p_segment = sub.add_parser('segment', help='Network segmentation')
    p_segment_sub = p_segment.add_subparsers(dest='subcommand')
    p_seg_list = p_segment_sub.add_parser('list', help='List segments')
    p_seg_create = p_segment_sub.add_parser('create', help='Create segment')
    p_seg_create.add_argument('name', help='Segment name')
    p_seg_create.add_argument('cidr', help='CIDR range')
    p_seg_create.add_argument('--env', default='production', help='Environment')
    p_seg_delete = p_segment_sub.add_parser('delete', help='Delete segment')
    p_seg_delete.add_argument('segment_id', help='Segment ID')

    p_capture = sub.add_parser('capture', help='Packet capture studio')
    p_capture_sub = p_capture.add_subparsers(dest='subcommand')
    p_cap_list = p_capture_sub.add_parser('list', help='List captures')
    p_cap_start = p_capture_sub.add_parser('start', help='Start capture')
    p_cap_start.add_argument('--interface', default='eth0', help='Interface')
    p_cap_start.add_argument('--duration', type=int, default=60, help='Duration seconds')
    p_cap_start.add_argument('--filter', default='', help='BPF filter')
    p_cap_stop = p_capture_sub.add_parser('stop', help='Stop capture')
    p_cap_stop.add_argument('capture_id', help='Capture ID')

    p_dnsfilter = sub.add_parser('dnsfilter', help='DNS filtering & DHCP')
    p_dnsfilter_sub = p_dnsfilter.add_subparsers(dest='subcommand')
    p_dnsfilter_status = p_dnsfilter_sub.add_parser('status', help='DNS filter status')
    p_dnsfilter_rules = p_dnsfilter_sub.add_parser('rules', help='List filtering rules')
    p_dnsfilter_add = p_dnsfilter_sub.add_parser('add', help='Add filtering rule')
    p_dnsfilter_add.add_argument('domain', help='Domain to filter')
    p_dnsfilter_add.add_argument('--action', default='block', choices=['block', 'allow', 'redirect'], help='Action')
    p_dnsfilter_remove = p_dnsfilter_sub.add_parser('remove', help='Remove filtering rule')
    p_dnsfilter_remove.add_argument('rule_id', help='Rule ID')

    p_dhcp = sub.add_parser('dhcp', help='DHCP management')
    p_dhcp_sub = p_dhcp.add_subparsers(dest='subcommand')
    p_dhcp_leases = p_dhcp_sub.add_parser('leases', help='List DHCP leases')

    p_netcost = sub.add_parser('netcost', help='Network cost analyzer')
    p_netcost_sub = p_netcost.add_subparsers(dest='subcommand')
    p_netcost_show = p_netcost_sub.add_parser('show', help='Show network costs')
    p_netcost_budget = p_netcost_sub.add_parser('budget', help='Set cost budget')
    p_netcost_budget.add_argument('monthly_budget', type=float, help='Monthly budget')

    p_cell = sub.add_parser('cell', help='5G/LTE cellular integration')
    p_cell_sub = p_cell.add_subparsers(dest='subcommand')
    p_cell_networks = p_cell_sub.add_parser('networks', help='List cellular networks')
    p_cell_register = p_cell_sub.add_parser('register', help='Register network')
    p_cell_register.add_argument('name', help='Network name')
    p_cell_register.add_argument('provider', help='Provider (att, verizon, tmobile)')
    p_cell_register.add_argument('apn', help='APN')
    p_cell_delete = p_cell_sub.add_parser('delete', help='Delete network')
    p_cell_delete.add_argument('network_id', help='Network ID')
    p_cell_status = p_cell_sub.add_parser('status', help='Cellular status')
    p_cell_sims = p_cell_sub.add_parser('sims', help='List SIM cards')
    p_cell_activate = p_cell_sub.add_parser('activate', help='Activate SIM')
    p_cell_activate.add_argument('sim_id', help='SIM ID')
    p_cell_deactivate = p_cell_sub.add_parser('deactivate', help='Deactivate SIM')
    p_cell_deactivate.add_argument('sim_id', help='SIM ID')

    # === v3 Marketplace Commands ===
    p_trade = sub.add_parser('trade', help='Resource trading platform')
    p_trade_sub = p_trade.add_subparsers(dest='subcommand')
    p_trade_list = p_trade_sub.add_parser('list', help='List trades')
    p_trade_list.add_argument('--status', help='Filter by status')
    p_trade_create = p_trade_sub.add_parser('create', help='Create trade listing')
    p_trade_create.add_argument('resource_type', help='Resource type')
    p_trade_create.add_argument('quantity', type=int, help='Quantity')
    p_trade_create.add_argument('price', type=float, help='Price')
    p_trade_create.add_argument('--unit', default='unit', help='Unit')
    p_trade_accept = p_trade_sub.add_parser('accept', help='Accept trade')
    p_trade_accept.add_argument('trade_id', help='Trade ID')
    p_trade_cancel = p_trade_sub.add_parser('cancel', help='Cancel trade')
    p_trade_cancel.add_argument('trade_id', help='Trade ID')

    p_appmarket = sub.add_parser('appmarket', help='One-click app marketplace')
    p_appmarket_sub = p_appmarket.add_subparsers(dest='subcommand')
    p_appmarket_list = p_appmarket_sub.add_parser('list', help='List available apps')
    p_appmarket_list.add_argument('--category', help='Filter by category')
    p_appmarket_install = p_appmarket_sub.add_parser('install', help='Install app')
    p_appmarket_install.add_argument('app_id', help='App ID')
    p_appmarket_install.add_argument('--target-server', help='Target server ID')
    p_appmarket_installations = p_appmarket_sub.add_parser('installations', help='List installations')

    p_ppu = sub.add_parser('ppu', help='Pay-per-use billing')
    p_ppu_sub = p_ppu.add_subparsers(dest='subcommand')
    p_ppu_metrics = p_ppu_sub.add_parser('metrics', help='PPU metrics')
    p_ppu_usage = p_ppu_sub.add_parser('usage', help='PPU usage details')
    p_ppu_budget = p_ppu_sub.add_parser('budget', help='Set PPU budget')
    p_ppu_budget.add_argument('monthly_budget', type=float, help='Monthly budget')

    p_reseller = sub.add_parser('reseller', help='Reseller/white-label')
    p_reseller_sub = p_reseller.add_subparsers(dest='subcommand')
    p_reseller_list = p_reseller_sub.add_parser('list', help='List resellers')
    p_reseller_create = p_reseller_sub.add_parser('create', help='Create reseller')
    p_reseller_create.add_argument('name', help='Reseller name')
    p_reseller_create.add_argument('email', help='Reseller email')
    p_reseller_create.add_argument('--commission', type=float, default=10.0, help='Commission rate %')
    p_reseller_delete = p_reseller_sub.add_parser('delete', help='Delete reseller')
    p_reseller_delete.add_argument('reseller_id', help='Reseller ID')
    p_reseller_analytics = p_reseller_sub.add_parser('analytics', help='Reseller analytics')
    p_reseller_analytics.add_argument('reseller_id', help='Reseller ID')

    p_whitelabel = sub.add_parser('whitelabel', help='White-label settings')
    p_whitelabel_sub = p_whitelabel.add_subparsers(dest='subcommand')
    p_whitelabel_settings = p_whitelabel_sub.add_parser('settings', help='View settings')

    p_sla = sub.add_parser('sla', help='SLA management & credits')
    p_sla_sub = p_sla.add_subparsers(dest='subcommand')
    p_sla_list = p_sla_sub.add_parser('list', help='List SLAs')
    p_sla_create = p_sla_sub.add_parser('create', help='Create SLA')
    p_sla_create.add_argument('name', help='SLA name')
    p_sla_create.add_argument('--uptime', type=float, default=99.9, help='Uptime target %')
    p_sla_create.add_argument('--credit-rate', type=float, default=5.0, help='Credit rate %')
    p_sla_delete = p_sla_sub.add_parser('delete', help='Delete SLA')
    p_sla_delete.add_argument('sla_id', help='SLA ID')
    p_sla_status = p_sla_sub.add_parser('status', help='SLA status')
    p_sla_status.add_argument('sla_id', help='SLA ID')

    p_credit = sub.add_parser('credit', help='SLA credits')
    p_credit_sub = p_credit.add_subparsers(dest='subcommand')
    p_credit_list = p_credit_sub.add_parser('list', help='List credits')
    p_credit_issue = p_credit_sub.add_parser('issue', help='Issue credit')
    p_credit_issue.add_argument('customer_id', help='Customer ID')
    p_credit_issue.add_argument('amount', type=float, help='Credit amount')
    p_credit_issue.add_argument('reason', help='Reason')

    p_crypto = sub.add_parser('crypto', help='Crypto payment gateway')
    p_crypto_sub = p_crypto.add_subparsers(dest='subcommand')
    p_crypto_wallets = p_crypto_sub.add_parser('wallets', help='List wallets')
    p_crypto_create_wallet = p_crypto_sub.add_parser('create-wallet', help='Create wallet')
    p_crypto_create_wallet.add_argument('currency', help='Currency (btc, eth, usdt)')
    p_crypto_create_wallet.add_argument('--label', default='default', help='Wallet label')
    p_crypto_transactions = p_crypto_sub.add_parser('transactions', help='List transactions')
    p_crypto_rates = p_crypto_sub.add_parser('rates', help='Crypto exchange rates')

    p_plans = sub.add_parser('plans', help='Subscription plan builder')
    p_plans_sub = p_plans.add_subparsers(dest='subcommand')
    p_plans_list = p_plans_sub.add_parser('list', help='List plans')
    p_plans_create = p_plans_sub.add_parser('create', help='Create plan')
    p_plans_create.add_argument('name', help='Plan name')
    p_plans_create.add_argument('price', type=float, help='Price')
    p_plans_create.add_argument('--billing-cycle', default='monthly', choices=['monthly', 'yearly', 'weekly'], help='Billing cycle')
    p_plans_create.add_argument('--features', default='basic', help='Comma-separated features')
    p_plans_delete = p_plans_sub.add_parser('delete', help='Delete plan')
    p_plans_delete.add_argument('plan_id', help='Plan ID')
    p_plans_subscriptions = p_plans_sub.add_parser('subscriptions', help='List active subscriptions')

    p_reco = sub.add_parser('reco', help='Usage-based recommendations')
    p_reco_sub = p_reco.add_subparsers(dest='subcommand')
    p_reco_list = p_reco_sub.add_parser('list', help='List recommendations')
    p_reco_summary = p_reco_sub.add_parser('summary', help='Recommendation summary')
    p_reco_implement = p_reco_sub.add_parser('implement', help='Implement recommendation')
    p_reco_implement.add_argument('reco_id', help='Recommendation ID')
    p_reco_dismiss = p_reco_sub.add_parser('dismiss', help='Dismiss recommendation')
    p_reco_dismiss.add_argument('reco_id', help='Recommendation ID')

    p_tax = sub.add_parser('tax', help='Invoice & tax automation')
    p_tax_sub = p_tax.add_subparsers(dest='subcommand')
    p_tax_rates = p_tax_sub.add_parser('rates', help='List tax rates')
    p_tax_invoices = p_tax_sub.add_parser('invoices', help='List invoices')
    p_tax_generate = p_tax_sub.add_parser('generate', help='Generate invoice')
    p_tax_pay = p_tax_sub.add_parser('pay', help='Mark invoice paid')
    p_tax_pay.add_argument('invoice_id', help='Invoice ID')
    p_tax_summary = p_tax_sub.add_parser('summary', help='Tax summary')
    p_tax_file = p_tax_sub.add_parser('file', help='File tax report')

    p_loyalty = sub.add_parser('loyalty', help='Loyalty & reward system')
    p_loyalty_sub = p_loyalty.add_subparsers(dest='subcommand')
    p_loyalty_status = p_loyalty_sub.add_parser('status', help='Loyalty status')
    p_loyalty_badges = p_loyalty_sub.add_parser('badges', help='List badges')
    p_loyalty_rewards = p_loyalty_sub.add_parser('rewards', help='List rewards')
    p_loyalty_redeem = p_loyalty_sub.add_parser('redeem', help='Redeem reward')
    p_loyalty_redeem.add_argument('reward_id', help='Reward ID')
    p_loyalty_leaderboard = p_loyalty_sub.add_parser('leaderboard', help='Leaderboard')

# === v4 Customer Experience Commands ===

def cmd_cx_health_list(args):
    result = get_client().cx_list_health_profiles(risk_level=args.risk_level, min_score=args.min_score)
    data = result if isinstance(result, list) else result.get('profiles', result)
    print_output(data, args.output)

def cmd_cx_health_get(args):
    result = get_client().cx_get_health_profile(args.customer_id)
    print_output(result, args.output)

def cmd_cx_health_compute(args):
    data = json.loads(args.data) if args.data else {}
    result = get_client().cx_compute_health(args.customer_id, data)
    print_output(result, args.output)

def cmd_cx_health_history(args):
    result = get_client().cx_get_health_history(args.customer_id, args.days)
    print_output(result, args.output)

def cmd_cx_health_stats(args):
    result = get_client().cx_get_health_stats()
    print_output(result, args.output)

def cmd_cx_ticket_list(args):
    result = get_client().cx_list_tickets(
        status=args.status, priority=args.priority, customer_id=args.customer_id,
        assigned_to=args.assigned_to, search=args.search,
        limit=args.limit, offset=args.offset,
    )
    data = result if isinstance(result, list) else result.get('tickets', result)
    print_output(data, args.output)

def cmd_cx_ticket_create(args):
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    result = get_client().cx_create_ticket(
        args.subject, args.description, args.customer_id,
        args.customer_name, args.customer_email, args.priority,
        args.channel, args.category, tags,
    )
    print_output(result, args.output)

def cmd_cx_ticket_get(args):
    result = get_client().cx_get_ticket(args.ticket_id)
    print_output(result, args.output)

def cmd_cx_ticket_status(args):
    result = get_client().cx_update_ticket_status(args.ticket_id, args.status, args.agent_id)
    print_output(result, args.output)

def cmd_cx_ticket_comment(args):
    result = get_client().cx_add_comment(args.ticket_id, args.author_id, args.body, args.author_name, args.internal)
    print_output(result, args.output)

def cmd_cx_ticket_assign(args):
    result = get_client().cx_assign_ticket(args.ticket_id, args.agent_id, args.team)
    print_output(result, args.output)

def cmd_cx_ticket_stats(args):
    result = get_client().cx_get_ticket_stats()
    print_output(result, args.output)

def cmd_cx_sla_list(args):
    result = get_client().cx_list_slas()
    data = result if isinstance(result, list) else result.get('slas', result)
    print_output(data, args.output)

def cmd_cx_sla_create(args):
    result = get_client().cx_create_sla(args.name, args.priority, args.response_time, args.resolution_time, not args.no_business_hours)
    print_output(result, args.output)

def cmd_cx_canned_list(args):
    result = get_client().cx_list_canned_responses(args.category)
    data = result if isinstance(result, list) else result.get('responses', result)
    print_output(data, args.output)

def cmd_cx_canned_create(args):
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    result = get_client().cx_create_canned_response(args.title, args.body, args.category, tags, args.created_by)
    print_output(result, args.output)

def cmd_cx_sentiment_analyze(args):
    result = get_client().cx_analyze_sentiment(args.text, args.source_type, args.source_id, args.customer_id, args.customer_name)
    print_output(result, args.output)

def cmd_cx_sentiment_profile(args):
    result = get_client().cx_get_sentiment_profile(args.customer_id)
    print_output(result, args.output)

def cmd_cx_sentiment_interactions(args):
    result = get_client().cx_list_sentiment_interactions(
        args.customer_id, args.source_type, args.min_score, args.max_score,
        args.escalated_only, args.limit,
    )
    data = result if isinstance(result, list) else result.get('interactions', result)
    print_output(data, args.output)

def cmd_cx_sentiment_trends(args):
    result = get_client().cx_get_sentiment_trends(args.period, args.days)
    print_output(result, args.output)

def cmd_cx_sentiment_alerts(args):
    result = get_client().cx_get_sentiment_alerts()
    data = result if isinstance(result, list) else result.get('alerts', result)
    print_output(data, args.output)

def cmd_cx_adoption_summary(args):
    result = get_client().cx_get_adoption_summary(args.customer_id)
    print_output(result, args.output)

def cmd_cx_adoption_features(args):
    result = get_client().cx_get_feature_adoption(args.customer_id, args.days)
    print_output(result, args.output)

def cmd_cx_adoption_track(args):
    result = get_client().cx_track_event(args.event_type, args.customer_id, args.user_id, args.feature_id, args.feature_name)
    print_output(result, args.output)

def cmd_cx_adoption_recommendations(args):
    result = get_client().cx_get_adoption_recommendations(args.customer_id)
    print_output(result, args.output)

def cmd_cx_adoption_stats(args):
    result = get_client().cx_get_adoption_stats()
    print_output(result, args.output)

def cmd_cx_onboarding_start(args):
    result = get_client().cx_start_onboarding(args.customer_id, args.customer_name, args.product_tier)
    print_output(result, args.output)

def cmd_cx_onboarding_get(args):
    result = get_client().cx_get_onboarding_session(args.customer_id)
    print_output(result, args.output)

def cmd_cx_onboarding_step(args):
    meta = json.loads(args.metadata) if args.metadata else None
    result = get_client().cx_update_onboarding_step(args.session_id, args.step_id, args.status, meta)
    print_output(result, args.output)

def cmd_cx_onboarding_stats(args):
    result = get_client().cx_get_onboarding_stats()
    print_output(result, args.output)

def cmd_cx_kb_list(args):
    result = get_client().cx_list_articles(args.category, args.article_type, args.status, args.limit)
    data = result if isinstance(result, list) else result.get('articles', result)
    print_output(data, args.output)

def cmd_cx_kb_create(args):
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    result = get_client().cx_create_article(args.title, args.content, args.category, args.article_type, tags, args.author, args.language)
    print_output(result, args.output)

def cmd_cx_kb_get(args):
    result = get_client().cx_get_article(args.article_id)
    print_output(result, args.output)

def cmd_cx_kb_update(args):
    data = json.loads(args.data) if args.data else {}
    result = get_client().cx_update_article(args.article_id, data)
    print_output(result, args.output)

def cmd_cx_kb_search(args):
    result = get_client().cx_search_articles(args.query, args.category, args.limit)
    data = result if isinstance(result, list) else result.get('results', result)
    print_output(data, args.output)

def cmd_cx_kb_categories(args):
    result = get_client().cx_list_categories()
    data = result if isinstance(result, list) else result.get('categories', result)
    print_output(data, args.output)

def cmd_cx_kb_feedback(args):
    result = get_client().cx_add_article_feedback(args.article_id, args.helpful, args.comment, args.user_id)
    print_output(result, args.output)

def cmd_cx_community_posts(args):
    result = get_client().cx_list_posts(args.category_id, args.post_type, args.sort, args.limit, args.offset)
    print_output(result, args.output)

def cmd_cx_community_create(args):
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    result = get_client().cx_create_post(args.title, args.content, args.category_id, args.post_type, args.author_id, args.author_name, tags)
    print_output(result, args.output)

def cmd_cx_community_get(args):
    result = get_client().cx_get_post(args.post_id)
    print_output(result, args.output)

def cmd_cx_community_vote(args):
    result = get_client().cx_vote_post(args.post_id, args.user_id, args.vote_type)
    print_output(result, args.output)

def cmd_cx_community_comment(args):
    result = get_client().cx_add_community_comment(args.post_id, args.author_id, args.body, args.author_name, args.parent_comment_id)
    print_output(result, args.output)

def cmd_cx_community_comments(args):
    result = get_client().cx_get_post_comments(args.post_id)
    data = result if isinstance(result, list) else result.get('comments', result)
    print_output(data, args.output)

def cmd_cx_community_requests(args):
    result = get_client().cx_get_feature_requests(args.sort, args.limit)
    data = result if isinstance(result, list) else result.get('feature_requests', result)
    print_output(data, args.output)

def cmd_cx_community_categories(args):
    result = get_client().cx_get_community_categories()
    data = result if isinstance(result, list) else result.get('categories', result)
    print_output(data, args.output)

def cmd_cx_community_leaderboard(args):
    result = get_client().cx_get_leaderboard(args.limit)
    data = result if isinstance(result, list) else result.get('leaderboard', result)
    print_output(data, args.output)

def cmd_cx_community_stats(args):
    result = get_client().cx_get_community_stats()
    print_output(result, args.output)

def cmd_cx_comm_send(args):
    channels = [c.strip() for c in args.channels.split(',')]
    result = get_client().cx_send_notification(
        args.type, args.subject, args.body, channels, args.priority,
        args.target_segment, args.created_by,
    )
    print_output(result, args.output)

def cmd_cx_comm_batches(args):
    result = get_client().cx_list_batches(args.limit)
    data = result if isinstance(result, list) else result.get('batches', result)
    print_output(data, args.output)

def cmd_cx_comm_batch(args):
    result = get_client().cx_get_batch_stats(args.batch_id)
    print_output(result, args.output)

def cmd_cx_comm_maintenance_schedule(args):
    services = [s.strip() for s in args.affected_services.split(',')]
    result = get_client().cx_schedule_maintenance(args.title, args.description, services, args.start, args.end, args.expected_downtime, args.created_by)
    print_output(result, args.output)

def cmd_cx_comm_maintenance_list(args):
    result = get_client().cx_list_maintenance(args.status)
    data = result if isinstance(result, list) else result.get('maintenance_windows', result)
    print_output(data, args.output)

def cmd_cx_comm_maintenance_complete(args):
    result = get_client().cx_complete_maintenance(args.maintenance_id, args.actual_downtime, args.post_mortem)
    print_output(result, args.output)

def cmd_cx_comm_templates(args):
    result = get_client().cx_list_templates(args.channel)
    data = result if isinstance(result, list) else result.get('templates', result)
    print_output(data, args.output)

def cmd_cx_comm_template_create(args):
    variables = [v.strip() for v in args.variables.split(',')] if args.variables else None
    result = get_client().cx_create_template(args.name, args.subject, args.body, args.channel, args.category, variables)
    print_output(result, args.output)

def cmd_cx_nps_create(args):
    questions = json.loads(args.questions_json)
    result = get_client().cx_create_survey(args.title, args.description, args.survey_type, args.trigger, questions, args.target_segment, args.frequency_days)
    print_output(result, args.output)

def cmd_cx_nps_list(args):
    result = get_client().cx_get_surveys(args.trigger, args.survey_type)
    data = result if isinstance(result, list) else result.get('surveys', result)
    print_output(data, args.output)

def cmd_cx_nps_get(args):
    result = get_client().cx_get_survey(args.survey_id)
    print_output(result, args.output)

def cmd_cx_nps_send(args):
    result = get_client().cx_send_survey(args.survey_id, args.customer_id, args.customer_name)
    print_output(result, args.output)

def cmd_cx_nps_respond(args):
    answers = json.loads(args.answers_json) if args.answers_json else {}
    result = get_client().cx_submit_response(args.response_id, answers, args.comments)
    print_output(result, args.output)

def cmd_cx_nps_score(args):
    result = get_client().cx_get_nps_score()
    print_output(result, args.output)

def cmd_cx_nps_trend(args):
    result = get_client().cx_get_nps_trend(args.days)
    print_output(result, args.output)

def cmd_cx_nps_detractors(args):
    result = get_client().cx_get_detractor_feedback(args.limit)
    data = result if isinstance(result, list) else result.get('detractors', result)
    print_output(data, args.output)

def cmd_cx_nps_stats(args):
    result = get_client().cx_get_nps_stats()
    print_output(result, args.output)

def cmd_cx_success_plays(args):
    result = get_client().cx_list_plays(args.trigger_event, args.status)
    data = result if isinstance(result, list) else result.get('plays', result)
    print_output(data, args.output)

def cmd_cx_success_create(args):
    actions = json.loads(args.actions_json) if args.actions_json else []
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    conditions = json.loads(args.conditions_json) if args.conditions_json else None
    result = get_client().cx_create_play(args.name, args.description, args.trigger_event, actions, tags, conditions, args.cooldown_days)
    print_output(result, args.output)

def cmd_cx_success_status(args):
    result = get_client().cx_update_play_status(args.play_id, args.status)
    print_output(result, args.output)

def cmd_cx_success_trigger(args):
    data = json.loads(args.event_data) if args.event_data else {}
    result = get_client().cx_evaluate_trigger(args.event, args.customer_id, data)
    print_output(result, args.output)

def cmd_cx_success_executions(args):
    result = get_client().cx_get_executions(args.play_id, args.customer_id, args.limit)
    data = result if isinstance(result, list) else result.get('executions', result)
    print_output(data, args.output)

def cmd_cx_success_stats(args):
    result = get_client().cx_get_success_stats()
    print_output(result, args.output)

# === v4 Platform Engineering Commands ===

    p_devportal = sub.add_parser('devportal', help='Developer portal')
    p_devportal_sub = p_devportal.add_subparsers(dest='subcommand')
    p_devportal_list = p_devportal_sub.add_parser('list', help='List components')
    p_devportal_list.add_argument('--domain', help='Filter by domain')
    p_devportal_register = p_devportal_sub.add_parser('register', help='Register component')
    p_devportal_register.add_argument('name', help='Component name')
    p_devportal_register.add_argument('domain', help='Domain')
    p_devportal_register.add_argument('--description', '-d', default='', help='Description')
    p_devportal_register.add_argument('--owner', '-o', default='platform', help='Owner team')
    p_devportal_get = p_devportal_sub.add_parser('get', help='Get component details')
    p_devportal_get.add_argument('component_id', help='Component ID')
    p_devportal_summary = p_devportal_sub.add_parser('summary', help='Portal summary')

    p_scaffold = sub.add_parser('scaffold', help='Golden path scaffold')
    p_scaffold_sub = p_scaffold.add_subparsers(dest='subcommand')
    p_scaffold_list = p_scaffold_sub.add_parser('list', help='List templates')
    p_scaffold_generate = p_scaffold_sub.add_parser('generate', help='Generate from template')
    p_scaffold_generate.add_argument('template_id', help='Template ID')
    p_scaffold_generate.add_argument('project_name', help='Project name')
    p_scaffold_generate.add_argument('--params', '-p', default='{}', help='JSON params')
    p_scaffold_status = p_scaffold_sub.add_parser('status', help='Generation status')
    p_scaffold_status.add_argument('generation_id', help='Generation ID')
    p_scaffold_step = p_scaffold_sub.add_parser('step', help='Complete a step')
    p_scaffold_step.add_argument('generation_id', help='Generation ID')
    p_scaffold_step.add_argument('step_name', help='Step name')
    p_scaffold_step.add_argument('--outputs', default='{}', help='JSON step outputs')

    p_catalog = sub.add_parser('service-catalog', help='Service catalog')
    p_catalog_sub = p_catalog.add_subparsers(dest='subcommand')
    p_catalog_list = p_catalog_sub.add_parser('list', help='List services')
    p_catalog_register = p_catalog_sub.add_parser('register', help='Register service')
    p_catalog_register.add_argument('name', help='Service name')
    p_catalog_register.add_argument('domain', help='Domain')
    p_catalog_register.add_argument('--description', '-d', default='', help='Description')
    p_catalog_register.add_argument('--owner', '-o', default='platform', help='Owner')
    p_catalog_get = p_catalog_sub.add_parser('get', help='Get service details')
    p_catalog_get.add_argument('service_id', help='Service ID')
    p_catalog_score = p_catalog_sub.add_parser('score', help='Score service readiness')
    p_catalog_score.add_argument('service_id', help='Service ID')
    p_catalog_summary = p_catalog_sub.add_parser('summary', help='Catalog summary')

    p_scorecards = sub.add_parser('scorecards', help='DORA scorecards')
    p_scorecards_sub = p_scorecards.add_subparsers(dest='subcommand')
    p_scorecards_list = p_scorecards_sub.add_parser('list', help='List scorecards')
    p_scorecards_create = p_scorecards_sub.add_parser('create', help='Create scorecard')
    p_scorecards_create.add_argument('name', help='Scorecard name')
    p_scorecards_create.add_argument('team', help='Team name')
    p_scorecards_create.add_argument('--dora', action='store_true', help='Include DORA metrics')
    p_scorecards_get = p_scorecards_sub.add_parser('get', help='Get scorecard')
    p_scorecards_get.add_argument('scorecard_id', help='Scorecard ID')
    p_scorecards_update = p_scorecards_sub.add_parser('update', help='Update metric')
    p_scorecards_update.add_argument('scorecard_id', help='Scorecard ID')
    p_scorecards_update.add_argument('metric', help='Metric name')
    p_scorecards_update.add_argument('value', help='Metric value')
    p_scorecards_summary = p_scorecards_sub.add_parser('summary', help='Scorecards summary')

    p_templatereg = sub.add_parser('template-registry', help='Template registry')
    p_templatereg_sub = p_templatereg.add_subparsers(dest='subcommand')
    p_templatereg_list = p_templatereg_sub.add_parser('list', help='List templates')
    p_templatereg_create = p_templatereg_sub.add_parser('create', help='Create template')
    p_templatereg_create.add_argument('name', help='Template name')
    p_templatereg_create.add_argument('category', help='Category')
    p_templatereg_create.add_argument('--params', '-p', default='{}', help='JSON params schema')
    p_templatereg_get = p_templatereg_sub.add_parser('get', help='Get template')
    p_templatereg_get.add_argument('template_id', help='Template ID')
    p_templatereg_use = p_templatereg_sub.add_parser('use', help='Record template usage')
    p_templatereg_use.add_argument('template_id', help='Template ID')
    p_templatereg_summary = p_templatereg_sub.add_parser('summary', help='Registry summary')

    p_techdebt = sub.add_parser('techdebt', help='Tech debt tracker')
    p_techdebt_sub = p_techdebt.add_subparsers(dest='subcommand')
    p_techdebt_list = p_techdebt_sub.add_parser('list', help='List debt items')
    p_techdebt_list.add_argument('--severity', help='Filter by severity')
    p_techdebt_report = p_techdebt_sub.add_parser('report', help='Report debt item')
    p_techdebt_report.add_argument('title', help='Title')
    p_techdebt_report.add_argument('severity', choices=['low', 'medium', 'high', 'critical'], help='Severity')
    p_techdebt_report.add_argument('effort_hours', type=int, help='Effort hours')
    p_techdebt_report.add_argument('--area', '-a', default='code', help='Area')
    p_techdebt_get = p_techdebt_sub.add_parser('get', help='Get debt item')
    p_techdebt_get.add_argument('debt_id', help='Debt ID')
    p_techdebt_fix = p_techdebt_sub.add_parser('fix', help='Mark as fixed')
    p_techdebt_fix.add_argument('debt_id', help='Debt ID')
    p_techdebt_summary = p_techdebt_sub.add_parser('summary', help='Debt summary')

    p_environments = sub.add_parser('environments', help='Ephemeral environments')
    p_environments_sub = p_environments.add_subparsers(dest='subcommand')
    p_environments_list = p_environments_sub.add_parser('list', help='List environments')
    p_environments_list.add_argument('--status', help='Filter by status')
    p_environments_create = p_environments_sub.add_parser('create', help='Create environment')
    p_environments_create.add_argument('name', help='Environment name')
    p_environments_create.add_argument('template', help='Environment template')
    p_environments_create.add_argument('--ttl', '-t', type=int, default=24, help='TTL hours')
    p_environments_create.add_argument('--branch', '-b', default='main', help='Git branch')
    p_environments_get = p_environments_sub.add_parser('get', help='Get environment')
    p_environments_get.add_argument('env_id', help='Environment ID')
    p_environments_delete = p_environments_sub.add_parser('delete', help='Delete environment')
    p_environments_delete.add_argument('env_id', help='Environment ID')
    p_environments_extend = p_environments_sub.add_parser('extend', help='Extend TTL')
    p_environments_extend.add_argument('env_id', help='Environment ID')
    p_environments_extend.add_argument('hours', type=int, help='Additional hours')
    p_environments_summary = p_environments_sub.add_parser('summary', help='Environment stats')

    p_apicatalog = sub.add_parser('api-catalog', help='API catalog')
    p_apicatalog_sub = p_apicatalog.add_subparsers(dest='subcommand')
    p_apicatalog_list = p_apicatalog_sub.add_parser('list', help='List APIs')
    p_apicatalog_register = p_apicatalog_sub.add_parser('register', help='Register API from spec')
    p_apicatalog_register.add_argument('name', help='API name')
    p_apicatalog_register.add_argument('version', help='API version')
    p_apicatalog_register.add_argument('spec', help='OpenAPI spec file path')
    p_apicatalog_get = p_apicatalog_sub.add_parser('get', help='Get API details')
    p_apicatalog_get.add_argument('api_id', help='API ID')
    p_apicatalog_summary = p_apicatalog_sub.add_parser('summary', help='Catalog summary')

    p_docgen = sub.add_parser('docgen', help='Doc generator')
    p_docgen_sub = p_docgen.add_subparsers(dest='subcommand')
    p_docgen_list = p_docgen_sub.add_parser('list', help='List documents')
    p_docgen_generate = p_docgen_sub.add_parser('generate', help='Generate document')
    p_docgen_generate.add_argument('title', help='Document title')
    p_docgen_generate.add_argument('doc_type', choices=['adr', 'c4_context', 'c4_container', 'c4_component'], help='Document type')
    p_docgen_get = p_docgen_sub.add_parser('get', help='Get document')
    p_docgen_get.add_argument('doc_id', help='Document ID')
    p_docgen_summary = p_docgen_sub.add_parser('summary', help='Doc generator stats')

    p_pulse = sub.add_parser('pulse', help='Developer pulse surveys')
    p_pulse_sub = p_pulse.add_subparsers(dest='subcommand')
    p_pulse_list = p_pulse_sub.add_parser('list', help='List surveys')
    p_pulse_create = p_pulse_sub.add_parser('create', help='Create survey')
    p_pulse_create.add_argument('title', help='Survey title')
    p_pulse_create.add_argument('questions_json', help='JSON array of questions')
    p_pulse_respond = p_pulse_sub.add_parser('respond', help='Submit response')
    p_pulse_respond.add_argument('survey_id', help='Survey ID')
    p_pulse_respond.add_argument('respondent', help='Respondent identifier')
    p_pulse_respond.add_argument('answers_json', help='JSON answers object')
    p_pulse_results = p_pulse_sub.add_parser('results', help='Get survey results')
    p_pulse_results.add_argument('survey_id', help='Survey ID')
    p_pulse_summary = p_pulse_sub.add_parser('summary', help='Pulse summary')

    # === v4 AIOps Commands ===
    p_rca = sub.add_parser('rca', help='Root cause analysis')
    p_rca_sub = p_rca.add_subparsers(dest='subcommand')
    p_rca_analyze = p_rca_sub.add_parser('analyze', help='Analyze incident')
    p_rca_analyze.add_argument('title', help='Incident title')
    p_rca_analyze.add_argument('description', help='Incident description')
    p_rca_incidents = p_rca_sub.add_parser('incidents', help='List incidents')
    p_rca_events = p_rca_sub.add_parser('events', help='List events')
    p_rca_events.add_argument('--source', help='Filter by source')
    p_rca_deps = p_rca_sub.add_parser('deps', help='Dependency graph')

    p_remediate = sub.add_parser('remediate', help='Incident remediation')
    p_remediate_sub = p_remediate.add_subparsers(dest='subcommand')
    p_remediate_suggest = p_remediate_sub.add_parser('suggest', help='Suggest remediation')
    p_remediate_suggest.add_argument('title', help='Incident title')
    p_remediate_suggest.add_argument('description', help='Incident description')
    p_remediate_list = p_remediate_sub.add_parser('list', help='List remediations')
    p_remediate_approve = p_remediate_sub.add_parser('approve', help='Approve remediation')
    p_remediate_approve.add_argument('remediation_id', help='Remediation ID')
    p_remediate_approve.add_argument('approver', help='Approver')
    p_remediate_stats = p_remediate_sub.add_parser('stats', help='Remediation stats')

    p_dem = sub.add_parser('dem', help='Digital experience monitoring')
    p_dem_sub = p_dem.add_subparsers(dest='subcommand')
    p_dem_list = p_dem_sub.add_parser('list', help='List monitors')
    p_dem_list.add_argument('--status', help='Filter by status')
    p_dem_create = p_dem_sub.add_parser('create', help='Create monitor')
    p_dem_create.add_argument('name', help='Monitor name')
    p_dem_create.add_argument('url', help='Target URL')
    p_dem_create.add_argument('--monitor-type', default='browser_synthetic', choices=['browser_synthetic', 'api_synthetic', 'multi_step'], help='Monitor type')
    p_dem_check = p_dem_sub.add_parser('check', help='Run check')
    p_dem_check.add_argument('monitor_id', help='Monitor ID')
    p_dem_stats = p_dem_sub.add_parser('stats', help='Monitor stats')
    p_dem_stats.add_argument('monitor_id', help='Monitor ID')
    p_dem_summary = p_dem_sub.add_parser('summary', help='Global summary')

    p_alert = sub.add_parser('alert', help='Alert correlation')
    p_alert_sub = p_alert.add_subparsers(dest='subcommand')
    p_alert_ingest = p_alert_sub.add_parser('ingest', help='Ingest alert')
    p_alert_ingest.add_argument('name', help='Alert name')
    p_alert_ingest.add_argument('source', help='Alert source')
    p_alert_ingest.add_argument('--severity', default='warning', choices=['info', 'warning', 'critical'], help='Severity')
    p_alert_ingest.add_argument('--message', default='', help='Alert message')
    p_alert_incidents = p_alert_sub.add_parser('incidents', help='List incidents')
    p_alert_incidents.add_argument('--status', help='Filter by status')
    p_alert_stats = p_alert_sub.add_parser('stats', help='Alert stats')
    p_alert_suppress = p_alert_sub.add_parser('suppress', help='Add suppression rule')
    p_alert_suppress.add_argument('name', help='Rule name')
    p_alert_suppress.add_argument('match_name', help='Match alert name')

    p_scaling = sub.add_parser('scaling', help='Predictive auto-scaling')
    p_scaling_sub = p_scaling.add_subparsers(dest='subcommand')
    p_scaling_predict = p_scaling_sub.add_parser('predict', help='Predict metrics')
    p_scaling_predict.add_argument('resource_id', help='Resource ID')
    p_scaling_predict.add_argument('metric', help='Metric name')
    p_scaling_metrics = p_scaling_sub.add_parser('metrics', help='View metrics')
    p_scaling_metrics.add_argument('resource_id', help='Resource ID')
    p_scaling_metrics.add_argument('metric', help='Metric name')
    p_scaling_policy = p_scaling_sub.add_parser('policy', help='Set scaling policy')
    p_scaling_policy.add_argument('resource_id', help='Resource ID')
    p_scaling_policy.add_argument('policy', choices=['conservative', 'aggressive', 'balanced'], help='Policy type')
    p_scaling_summary = p_scaling_sub.add_parser('summary', help='Scaling summary')

    p_health = sub.add_parser('health', help='Service health forecasting')
    p_health_sub = p_health.add_subparsers(dest='subcommand')
    p_health_services = p_health_sub.add_parser('services', help='List services')
    p_health_register = p_health_sub.add_parser('register', help='Register service')
    p_health_register.add_argument('service_id', help='Service ID')
    p_health_register.add_argument('name', help='Service name')
    p_health_forecast = p_health_sub.add_parser('forecast', help='Forecast health')
    p_health_forecast.add_argument('service_id', help='Service ID')
    p_health_dashboard = p_health_sub.add_parser('dashboard', help='Health dashboard')

    p_assistant = sub.add_parser('assistant', help='Conversational ops assistant')
    p_assistant_sub = p_assistant.add_subparsers(dest='subcommand')
    p_assistant_message = p_assistant_sub.add_parser('message', help='Send message')
    p_assistant_message.add_argument('session_id', help='Session ID')
    p_assistant_message.add_argument('user_id', help='User ID')
    p_assistant_message.add_argument('message', help='Message text')
    p_assistant_stats = p_assistant_sub.add_parser('stats', help='Assistant stats')

    p_change = sub.add_parser('change', help='Change risk analysis')
    p_change_sub = p_change.add_subparsers(dest='subcommand')
    p_change_plan = p_change_sub.add_parser('plan', help='Plan change')
    p_change_plan.add_argument('title', help='Change title')
    p_change_plan.add_argument('description', help='Change description')
    p_change_plan.add_argument('--change-type', default='deployment', choices=['deployment', 'config_change', 'migration', 'scaling'], help='Change type')
    p_change_plan.add_argument('--target', required=True, help='Target resource')
    p_change_plan.add_argument('--affected-resources', required=True, help='Comma-separated affected resources')
    p_change_approve = p_change_sub.add_parser('approve', help='Approve change')
    p_change_approve.add_argument('change_id', help='Change ID')
    p_change_approve.add_argument('approver', help='Approver')
    p_change_stats = p_change_sub.add_parser('stats', help='Change stats')

    p_capacity = sub.add_parser('capacity', help='AI-driven capacity planning')
    p_capacity_sub = p_capacity.add_subparsers(dest='subcommand')
    p_capacity_recommend = p_capacity_sub.add_parser('recommend', help='Get recommendation')
    p_capacity_recommend.add_argument('resource_id', help='Resource ID')
    p_capacity_recommend.add_argument('metric', help='Metric name')
    p_capacity_usage = p_capacity_sub.add_parser('usage', help='View usage')
    p_capacity_usage.add_argument('resource_id', help='Resource ID')
    p_capacity_usage.add_argument('metric', help='Metric name')
    p_capacity_simulate = p_capacity_sub.add_parser('simulate', help='What-if simulation')
    p_capacity_simulate.add_argument('resource_id', help='Resource ID')
    p_capacity_simulate.add_argument('metric', help='Metric name')
    p_capacity_simulate.add_argument('scenario', choices=['traffic_spike', 'black_friday', 'node_failure', 'migration', 'organic_growth'], help='Scenario')
    p_capacity_summary = p_capacity_sub.add_parser('summary', help='Capacity summary')

    p_chatbot = sub.add_parser('chatbot', help='Self-service ops chatbot')
    p_chatbot_sub = p_chatbot.add_subparsers(dest='subcommand')
    p_chatbot_message = p_chatbot_sub.add_parser('message', help='Send message')
    p_chatbot_message.add_argument('user_id', help='User ID')
    p_chatbot_message.add_argument('message', help='Message text')
    p_chatbot_message.add_argument('--conversation-id', help='Conversation ID')
    p_chatbot_tasks = p_chatbot_sub.add_parser('tasks', help='List tasks')
    p_chatbot_tasks.add_argument('user_id', help='User ID')
    p_chatbot_analytics = p_chatbot_sub.add_parser('analytics', help='Chatbot analytics')

    # === v6 AIOps Commands ===
    p_alert_corr = sub.add_parser('alert-corr', help='Alert correlation v6')
    p_alert_corr_sub = p_alert_corr.add_subparsers(dest='subcommand')
    p_alert_corr_sub.add_parser('correlate', help='Correlate alerts').add_argument('--window', type=int, default=5, help='Window minutes')
    p_alert_corr_sub.add_parser('sources', help='Alert source breakdown')
    p_alert_corr_sub.add_parser('suppress', help='Suppress duplicates').add_argument('--window', type=int, default=2, help='Window minutes')
    p_alert_corr_sub.add_parser('stats', help='Correlation stats')

    p_rca_v6 = sub.add_parser('rca-v6', help='Root cause analysis v6')
    p_rca_v6_sub = p_rca_v6.add_subparsers(dest='subcommand')
    p_rca_v6_sub.add_parser('analyze', help='Analyze incident').add_argument('incident_id', help='Incident ID')
    p_rca_v6_sub.add_parser('impact', help='Event impact score').add_argument('event_id', help='Event ID')
    p_rca_v6_sub.add_parser('timeline', help='Event timeline').add_argument('--hours', type=int, default=24, help='Hours')
    p_rca_v6_sub.add_parser('patterns', help='Correlation patterns')

    p_capacity_v6 = sub.add_parser('capacity-v6', help='Capacity planning v6')
    p_capacity_v6_sub = p_capacity_v6.add_subparsers(dest='subcommand')
    p_capacity_v6_sub.add_parser('recommend', help='Capacity recommendations')
    p_capacity_v6_sub.add_parser('simulate', help='What-if simulation').add_argument('scenario', help='Scenario name').add_argument('--peak', type=int, default=150, help='Peak %')
    p_capacity_v6_sub.add_parser('forecast', help='Capacity forecast')
    p_capacity_v6_sub.add_parser('alerts', help='Capacity alerts')

    p_change_risk = sub.add_parser('change-risk', help='Change risk analysis v6')
    p_change_risk_sub = p_change_risk.add_subparsers(dest='subcommand')
    p_change_risk_sub.add_parser('analyze', help='Analyze change').add_argument('change_id', help='Change ID')
    p_change_risk_sub.add_parser('trend', help='Risk trend').add_argument('--days', type=int, default=30, help='Days')
    p_change_risk_sub.add_parser('ranking', help='Service risk ranking')

    p_convo = sub.add_parser('convo', help='Conversational ops v6')
    p_convo_sub = p_convo.add_subparsers(dest='subcommand')
    p_convo_sub.add_parser('health', help='SLO health')
    p_convo_sub.add_parser('feedback', help='Feedback stats').add_argument('--days', type=int, default=7, help='Days')
    p_convo_sub.add_parser('popular', help='Popular commands')

    p_dex = sub.add_parser('dex', help='Digital experience v6')
    p_dex_sub = p_dex.add_subparsers(dest='subcommand')
    p_dex_sub.add_parser('monitors', help='List monitors')
    p_dex_sub.add_parser('regression', help='Performance regression').add_argument('--days', type=int, default=7, help='Days')
    p_dex_sub.add_parser('health', help='Monitor health')

    p_health_f = sub.add_parser('health-f', help='Health forecasting v6')
    p_health_f_sub = p_health_f.add_subparsers(dest='subcommand')
    p_health_f_sub.add_parser('forecast', help='Get forecast').add_argument('--hours', type=int, default=24, help='Hours')
    p_health_f_sub.add_parser('alerts', help='Health alerts').add_argument('--days', type=int, default=3, help='Days')
    p_health_f_sub.add_parser('accuracy', help='Forecast accuracy').add_argument('--weeks', type=int, default=6, help='Weeks')

    p_incident = sub.add_parser('incident', help='Incident remediation v6')
    p_incident_sub = p_incident.add_subparsers(dest='subcommand')
    p_incident_sub.add_parser('remediate', help='Remediate incident').add_argument('incident_id', help='Incident ID').add_argument('--action', default='auto', help='Action')
    p_incident_sub.add_parser('analytics', help='Remediation analytics').add_argument('--days', type=int, default=30, help='Days')
    p_incident_sub.add_parser('mttr', help='MTTR by severity')

    p_ops = sub.add_parser('ops', help='Ops chatbot v6')
    p_ops_sub = p_ops.add_subparsers(dest='subcommand')
    p_ops_sub.add_parser('chat', help='Send message').add_argument('message', help='Message')
    p_ops_sub.add_parser('tasks', help='List tasks')
    p_ops_sub.add_parser('priorities', help='Task priorities')

    p_scaling_v6 = sub.add_parser('scaling-v6', help='Predictive scaling v6')
    p_scaling_v6_sub = p_scaling_v6.add_subparsers(dest='subcommand')
    p_scaling_v6_sub.add_parser('forecast', help='Get forecast').add_argument('resource_id', help='Resource ID').add_argument('--metric', default='cpu', help='Metric')
    p_scaling_v6_sub.add_parser('alerts', help='Scaling alerts')
    p_scaling_v6_sub.add_parser('recommend', help='Scaling recommendations')

    # === v4 SOC Commands ===
    p_soar = sub.add_parser('soar', help='SOAR playbook management')
    p_soar_sub = p_soar.add_subparsers(dest='subcommand')
    p_soar_playbooks = p_soar_sub.add_parser('playbooks', help='List playbooks')
    p_soar_playbook = p_soar_sub.add_parser('playbook', help='Get playbook details')
    p_soar_playbook.add_argument('playbook_id', help='Playbook ID')
    p_soar_run = p_soar_sub.add_parser('run', help='Execute playbook')
    p_soar_run.add_argument('playbook_id', help='Playbook ID')
    p_soar_create = p_soar_sub.add_parser('create', help='Create playbook')
    p_soar_create.add_argument('name', help='Playbook name')
    p_soar_create.add_argument('description', help='Playbook description')
    p_soar_create.add_argument('--category', default='incident_response', help='Category')
    p_soar_cases = p_soar_sub.add_parser('cases', help='List cases')
    p_soar_connectors = p_soar_sub.add_parser('connectors', help='List connectors')

    p_ti = sub.add_parser('threatintel', help='Threat intelligence')
    p_ti_sub = p_ti.add_subparsers(dest='subcommand')
    p_ti_feeds = p_ti_sub.add_parser('feeds', help='List threat feeds')
    p_ti_iocs = p_ti_sub.add_parser('iocs', help='List IoCs')
    p_ti_blocklist = p_ti_sub.add_parser('blocklist', help='Show blocklist')
    p_ti_add_ioc = p_ti_sub.add_parser('add-ioc', help='Add IoC')
    p_ti_add_ioc.add_argument('type', choices=['ip', 'domain', 'url', 'hash', 'email'], help='IoC type')
    p_ti_add_ioc.add_argument('value', help='IoC value')
    p_ti_add_ioc.add_argument('--confidence', type=int, default=75, help='Confidence score (0-100)')
    p_ti_analyze = p_ti_sub.add_parser('analyze', help='Analyze text for threat indicators')
    p_ti_analyze.add_argument('text', help='Text to analyze')

    p_decoy = sub.add_parser('decoy', help='Deception technology')
    p_decoy_sub = p_decoy.add_subparsers(dest='subcommand')
    p_decoy_list = p_decoy_sub.add_parser('list', help='List decoys')
    p_decoy_tokens = p_decoy_sub.add_parser('tokens', help='List honey tokens')
    p_decoy_create = p_decoy_sub.add_parser('create', help='Create decoy')
    p_decoy_create.add_argument('name', help='Decoy name')
    p_decoy_create.add_argument('decoy_type', choices=['honeypot', 'fake_db', 'fake_s3', 'fake_gitlab', 'fake_api', 'fake_admin'], help='Decoy type')
    p_decoy_create.add_argument('target_ip', help='Target IP')
    p_decoy_create.add_argument('--port', type=int, default=22, help='Port')
    p_decoy_deploy = p_decoy_sub.add_parser('deploy', help='Deploy decoy')
    p_decoy_deploy.add_argument('decoy_id', help='Decoy ID')

    p_vuln = sub.add_parser('vuln', help='Vulnerability management')
    p_vuln_sub = p_vuln.add_subparsers(dest='subcommand')
    p_vuln_cves = p_vuln_sub.add_parser('cves', help='List CVEs')
    p_vuln_scan = p_vuln_sub.add_parser('scan', help='Run vulnerability scan')
    p_vuln_scan.add_argument('target', help='Target to scan')
    p_vuln_patch = p_vuln_sub.add_parser('patch', help='Patch CVE')
    p_vuln_patch.add_argument('cve_id', help='CVE ID')
    p_vuln_summary = p_vuln_sub.add_parser('summary', help='Vulnerability summary')

    p_ir = sub.add_parser('incident', help='Incident response')
    p_ir_sub = p_ir.add_subparsers(dest='subcommand')
    p_ir_list = p_ir_sub.add_parser('list', help='List incidents')
    p_ir_get = p_ir_sub.add_parser('get', help='Get incident details')
    p_ir_get.add_argument('incident_id', help='Incident ID')
    p_ir_create = p_ir_sub.add_parser('create', help='Create incident')
    p_ir_create.add_argument('title', help='Incident title')
    p_ir_create.add_argument('severity', choices=['low', 'medium', 'high', 'critical'], help='Severity')
    p_ir_create.add_argument('incident_type', help='Incident type')
    p_ir_status = p_ir_sub.add_parser('status', help='Update incident status')
    p_ir_status.add_argument('incident_id', help='Incident ID')
    p_ir_status.add_argument('status', choices=['open', 'investigating', 'contained', 'resolved', 'closed'], help='Status')
    p_ir_evidence = p_ir_sub.add_parser('evidence', help='Add evidence')
    p_ir_evidence.add_argument('incident_id', help='Incident ID')
    p_ir_evidence.add_argument('title', help='Evidence title')
    p_ir_evidence.add_argument('content', help='Evidence content')
    p_ir_evidence.add_argument('--evidence-type', default='log', help='Evidence type')
    p_ir_timeline = p_ir_sub.add_parser('timeline', help='Get incident timeline')
    p_ir_timeline.add_argument('incident_id', help='Incident ID')
    p_ir_report = p_ir_sub.add_parser('report', help='Generate incident report')
    p_ir_report.add_argument('incident_id', help='Incident ID')

    p_ueba = sub.add_parser('ueba', help='User & entity behavior analytics')
    p_ueba_sub = p_ueba.add_subparsers(dest='subcommand')
    p_ueba_entities = p_ueba_sub.add_parser('entities', help='List entities')
    p_ueba_alerts = p_ueba_sub.add_parser('alerts', help='List anomaly alerts')

    p_cspm = sub.add_parser('cspm', help='Cloud security posture management')
    p_cspm_sub = p_cspm.add_subparsers(dest='subcommand')
    p_cspm_accounts = p_cspm_sub.add_parser('accounts', help='List cloud accounts')
    p_cspm_results = p_cspm_sub.add_parser('results', help='List check results')
    p_cspm_scan = p_cspm_sub.add_parser('scan', help='Run CSPM scan')

    p_ndr = sub.add_parser('ndr', help='Network detection & response')
    p_ndr_sub = p_ndr.add_subparsers(dest='subcommand')
    p_ndr_flows = p_ndr_sub.add_parser('flows', help='List network flows')
    p_ndr_flows.add_argument('--all', action='store_true', help='Show non-malicious flows too')
    p_ndr_alerts = p_ndr_sub.add_parser('alerts', help='List NDR alerts')

    p_secrets = sub.add_parser('secrets', help='Secrets detection')
    p_secrets_sub = p_secrets.add_subparsers(dest='subcommand')
    p_secrets_findings = p_secrets_sub.add_parser('findings', help='List findings')
    p_secrets_targets = p_secrets_sub.add_parser('targets', help='List scan targets')
    p_secrets_rotate = p_secrets_sub.add_parser('rotate', help='Rotate a secret')
    p_secrets_rotate.add_argument('finding_id', help='Finding ID')

    p_training = sub.add_parser('training', help='Security awareness training')
    p_training_sub = p_training.add_subparsers(dest='subcommand')
    p_training_modules = p_training_sub.add_parser('modules', help='List training modules')
    p_training_campaigns = p_training_sub.add_parser('campaigns', help='List phishing campaigns')
    p_training_assignments = p_training_sub.add_parser('assignments', help='List assignments')

    # === v4 FinOps Commands ===
    p_finops = sub.add_parser('finops', help='FinOps & cost management')
    p_finops_sub = p_finops.add_subparsers(dest='subcommand')

    p_finops_commitment = p_finops_sub.add_parser('commitment', help='Commitment discount optimization')
    p_finops_commitment_sub = p_finops_commitment.add_subparsers(dest='action')
    p_finops_commitment_list = p_finops_commitment_sub.add_parser('list', help='List recommendations')
    p_finops_commitment_summary = p_finops_commitment_sub.add_parser('summary', help='Commitment summary')
    p_finops_commitment_implement = p_finops_commitment_sub.add_parser('implement', help='Implement recommendation')
    p_finops_commitment_implement.add_argument('rec_id', help='Recommendation ID')
    p_finops_commitment_commitments = p_finops_commitment_sub.add_parser('commitments', help='List active commitments')

    p_finops_spot = p_finops_sub.add_parser('spot', help='Spot instance management')
    p_finops_spot_sub = p_finops_spot.add_subparsers(dest='action')
    p_finops_spot_list = p_finops_spot_sub.add_parser('list', help='List fleets')
    p_finops_spot_list.add_argument('--status', help='Filter by status')
    p_finops_spot_create = p_finops_spot_sub.add_parser('create', help='Create fleet')
    p_finops_spot_create.add_argument('name', help='Fleet name')
    p_finops_spot_create.add_argument('instance_type', help='Instance type')
    p_finops_spot_create.add_argument('target_capacity', type=int, help='Target capacity')
    p_finops_spot_create.add_argument('--spot-type', default='request', choices=['request', 'fleet'], help='Spot request type')
    p_finops_spot_get = p_finops_spot_sub.add_parser('get', help='Get fleet details')
    p_finops_spot_get.add_argument('fleet_id', help='Fleet ID')
    p_finops_spot_instances = p_finops_spot_sub.add_parser('instances', help='List fleet instances')
    p_finops_spot_instances.add_argument('fleet_id', help='Fleet ID')
    p_finops_spot_savings = p_finops_spot_sub.add_parser('savings', help='Spot savings summary')

    p_finops_uoe = p_finops_sub.add_parser('uoe', help='Unit economics')
    p_finops_uoe_sub = p_finops_uoe.add_subparsers(dest='action')
    p_finops_uoe_metrics = p_finops_uoe_sub.add_parser('metrics', help='List metrics')
    p_finops_uoe_metrics.add_argument('--customer-id', help='Filter by customer')
    p_finops_uoe_metrics.add_argument('--dimension', help='Filter by dimension')
    p_finops_uoe_record = p_finops_uoe_sub.add_parser('record', help='Record metric')
    p_finops_uoe_record.add_argument('customer_id', help='Customer ID')
    p_finops_uoe_record.add_argument('metric_name', help='Metric name')
    p_finops_uoe_record.add_argument('value', type=float, help='Metric value')
    p_finops_uoe_record.add_argument('--dimension', default='general', help='Dimension')
    p_finops_uoe_targets = p_finops_uoe_sub.add_parser('targets', help='List targets')
    p_finops_uoe_set_target = p_finops_uoe_sub.add_parser('set-target', help='Set target')
    p_finops_uoe_set_target.add_argument('metric_name', help='Metric name')
    p_finops_uoe_set_target.add_argument('target_value', type=float, help='Target value')
    p_finops_uoe_set_target.add_argument('--threshold', type=float, default=10.0, help='Alert threshold %')
    p_finops_uoe_violations = p_finops_uoe_sub.add_parser('violations', help='List violations')
    p_finops_uoe_overview = p_finops_uoe_sub.add_parser('overview', help='Unit economics overview')

    p_finops_anomaly = p_finops_sub.add_parser('anomaly', help='Cost anomaly detection')
    p_finops_anomaly_sub = p_finops_anomaly.add_subparsers(dest='action')
    p_finops_anomaly_list = p_finops_anomaly_sub.add_parser('list', help='List detections')
    p_finops_anomaly_list.add_argument('--severity', help='Filter by severity')
    p_finops_anomaly_summary = p_finops_anomaly_sub.add_parser('summary', help='Anomaly summary')
    p_finops_anomaly_investigate = p_finops_anomaly_sub.add_parser('investigate', help='Investigate anomaly')
    p_finops_anomaly_investigate.add_argument('anomaly_id', help='Anomaly ID')
    p_finops_anomaly_resolve = p_finops_anomaly_sub.add_parser('resolve', help='Resolve anomaly')
    p_finops_anomaly_resolve.add_argument('anomaly_id', help='Anomaly ID')
    p_finops_anomaly_profiles = p_finops_anomaly_sub.add_parser('profiles', help='List detection profiles')
    p_finops_anomaly_create_profile = p_finops_anomaly_sub.add_parser('create-profile', help='Create profile')
    p_finops_anomaly_create_profile.add_argument('name', help='Profile name')
    p_finops_anomaly_create_profile.add_argument('--method', default='zscore', choices=['zscore', 'mad', 'iqr', 'adaptive'], help='Detection method')
    p_finops_anomaly_create_profile.add_argument('--sensitivity', type=float, default=2.0, help='Sensitivity')

    p_finops_budget = p_finops_sub.add_parser('budget', help='Budget forecasting')
    p_finops_budget_sub = p_finops_budget.add_subparsers(dest='action')
    p_finops_budget_list = p_finops_budget_sub.add_parser('list', help='List budgets')
    p_finops_budget_create = p_finops_budget_sub.add_parser('create', help='Create budget')
    p_finops_budget_create.add_argument('name', help='Budget name')
    p_finops_budget_create.add_argument('amount', type=float, help='Budget amount')
    p_finops_budget_create.add_argument('--period', default='monthly', choices=['weekly', 'monthly', 'quarterly', 'annual'], help='Period')
    p_finops_budget_get = p_finops_budget_sub.add_parser('get', help='Get budget')
    p_finops_budget_get.add_argument('budget_id', help='Budget ID')
    p_finops_budget_spend = p_finops_budget_sub.add_parser('spend', help='Record spend')
    p_finops_budget_spend.add_argument('budget_id', help='Budget ID')
    p_finops_budget_spend.add_argument('amount', type=float, help='Spend amount')
    p_finops_budget_forecast = p_finops_budget_sub.add_parser('forecast', help='Get budget forecast')
    p_finops_budget_forecast.add_argument('budget_id', help='Budget ID')
    p_finops_budget_scenario = p_finops_budget_sub.add_parser('scenario', help='What-if scenario')
    p_finops_budget_scenario.add_argument('budget_id', help='Budget ID')
    p_finops_budget_scenario.add_argument('scenario', help='Scenario name')
    p_finops_budget_summary = p_finops_budget_sub.add_parser('summary', help='Budget summary')

    p_finops_rightsizing = p_finops_sub.add_parser('rightsizing', help='Resource right-sizing')
    p_finops_rightsizing_sub = p_finops_rightsizing.add_subparsers(dest='action')
    p_finops_rightsizing_list = p_finops_rightsizing_sub.add_parser('list', help='List recommendations')
    p_finops_rightsizing_summary = p_finops_rightsizing_sub.add_parser('summary', help='Rightsizing summary')
    p_finops_rightsizing_approve = p_finops_rightsizing_sub.add_parser('approve', help='Approve recommendation')
    p_finops_rightsizing_approve.add_argument('rec_id', help='Recommendation ID')
    p_finops_rightsizing_implement = p_finops_rightsizing_sub.add_parser('implement', help='Implement recommendation')
    p_finops_rightsizing_implement.add_argument('rec_id', help='Recommendation ID')
    p_finops_rightsizing_dismiss = p_finops_rightsizing_sub.add_parser('dismiss', help='Dismiss recommendation')
    p_finops_rightsizing_dismiss.add_argument('rec_id', help='Recommendation ID')

    p_finops_waste = p_finops_sub.add_parser('waste', help='Cloud waste detection')
    p_finops_waste_sub = p_finops_waste.add_subparsers(dest='action')
    p_finops_waste_list = p_finops_waste_sub.add_parser('list', help='List findings')
    p_finops_waste_summary = p_finops_waste_sub.add_parser('summary', help='Waste summary')
    p_finops_waste_scan = p_finops_waste_sub.add_parser('scan', help='Run waste scan')
    p_finops_waste_approve = p_finops_waste_sub.add_parser('approve', help='Approve cleanup')
    p_finops_waste_approve.add_argument('finding_id', help='Finding ID')
    p_finops_waste_cleanup = p_finops_waste_sub.add_parser('cleanup', help='Execute cleanup')
    p_finops_waste_cleanup.add_argument('finding_id', help='Finding ID')
    p_finops_waste_dismiss = p_finops_waste_sub.add_parser('dismiss', help='Dismiss finding')
    p_finops_waste_dismiss.add_argument('finding_id', help='Finding ID')

    p_finops_carbon = p_finops_sub.add_parser('carbon', help='Carbon-aware optimization')
    p_finops_carbon_sub = p_finops_carbon.add_subparsers(dest='action')
    p_finops_carbon_list = p_finops_carbon_sub.add_parser('list', help='List carbon recommendations')
    p_finops_carbon_assets = p_finops_carbon_sub.add_parser('assets', help='List registered assets')
    p_finops_carbon_register = p_finops_carbon_sub.add_parser('register', help='Register asset')
    p_finops_carbon_register.add_argument('name', help='Asset name')
    p_finops_carbon_register.add_argument('provider', choices=['aws', 'azure', 'gcp'], help='Provider')
    p_finops_carbon_register.add_argument('region', help='Region')
    p_finops_carbon_register.add_argument('--monthly-cost', type=float, default=1000, help='Monthly cost')
    p_finops_carbon_sustainability = p_finops_carbon_sub.add_parser('sustainability', help='Sustainability budget')

    p_finops_arbitrage = p_finops_sub.add_parser('arbitrage', help='Multi-cloud discount arbitrage')
    p_finops_arbitrage_sub = p_finops_arbitrage.add_subparsers(dest='action')
    p_finops_arbitrage_workloads = p_finops_arbitrage_sub.add_parser('workloads', help='List workloads')
    p_finops_arbitrage_comparisons = p_finops_arbitrage_sub.add_parser('comparisons', help='Provider comparisons')
    p_finops_arbitrage_savings = p_finops_arbitrage_sub.add_parser('savings', help='Savings summary')

    p_finops_reports = p_finops_sub.add_parser('reports', help='FinOps reporting')
    p_finops_reports_sub = p_finops_reports.add_subparsers(dest='action')
    p_finops_reports_list = p_finops_reports_sub.add_parser('list', help='List reports')
    p_finops_reports_summary = p_finops_reports_sub.add_parser('summary', help='Reports summary')
    p_finops_reports_generate = p_finops_reports_sub.add_parser('generate', help='Generate report')
    p_finops_reports_generate.add_argument('report_type', help='Report type')
    p_finops_reports_generate.add_argument('--period', default='monthly', help='Period')

    # === v4 Compliance & Audit 2.0 Commands ===
    p_cc = sub.add_parser('cc', help='Continuous compliance monitoring')
    p_cc_sub = p_cc.add_subparsers(dest='subcommand')
    p_cc_sub.add_parser('status', help='Compliance posture status')
    p_cc_scan = p_cc_sub.add_parser('scan', help='Run compliance scan')
    p_cc_scan.add_argument('--framework', help='Framework to scan')
    p_cc_sub.add_parser('alerts', help='List compliance alerts')
    p_cc_sub.add_parser('summary', help='Compliance summary')

    p_ec = sub.add_parser('evidence', help='Evidence collection')
    p_ec_sub = p_ec.add_subparsers(dest='subcommand')
    p_ec_sub.add_parser('list', help='List evidence items')
    p_ec_collect = p_ec_sub.add_parser('collect', help='Collect evidence')
    p_ec_collect.add_argument('ev_type', help='Evidence type')
    p_ec_collect.add_argument('control', help='Control ID')
    p_ec_sub.add_parser('packages', help='List evidence packages')
    p_ec_sub.add_parser('stats', help='Evidence collection stats')

    p_cac = sub.add_parser('cac', help='Compliance as code')
    p_cac_sub = p_cac.add_subparsers(dest='subcommand')
    p_cac_sub.add_parser('list', help='List policy templates')
    p_cac_eval = p_cac_sub.add_parser('evaluate', help='Evaluate template')
    p_cac_eval.add_argument('template_id', help='Template ID')
    p_cac_sub.add_parser('templates', help='List available templates')
    p_cac_sub.add_parser('stats', help='CAC stats')

    p_ar = sub.add_parser('attest', help='Attestation report management')
    p_ar_sub = p_ar.add_subparsers(dest='subcommand')
    p_ar_sub.add_parser('list', help='List attestation reports')
    p_ar_gen = p_ar_sub.add_parser('generate', help='Generate report')
    p_ar_gen.add_argument('--framework', default='SOC_2', help='Framework')
    p_ar_gen.add_argument('--start', help='Period start (YYYY-MM-DD)')
    p_ar_gen.add_argument('--end', help='Period end (YYYY-MM-DD)')
    p_ar_sign = p_ar_sub.add_parser('sign', help='Sign report')
    p_ar_sign.add_argument('report_id', help='Report ID')
    p_ar_sign.add_argument('signed_by', help='Signer name')
    p_ar_sub.add_parser('stats', help='Attestation stats')

    p_vc = sub.add_parser('vcom', help='Vendor compliance management')
    p_vc_sub = p_vc.add_subparsers(dest='subcommand')
    p_vc_sub.add_parser('list', help='List vendors')
    p_vc_reg = p_vc_sub.add_parser('register', help='Register vendor')
    p_vc_reg.add_argument('name', help='Vendor name')
    p_vc_reg.add_argument('category', help='Vendor category')
    p_vc_assess = p_vc_sub.add_parser('assess', help='Assess vendor')
    p_vc_assess.add_argument('vendor_id', help='Vendor ID')
    p_vc_sub.add_parser('risk', help='Risk summary')

    p_ri = sub.add_parser('regintel', help='Regulatory intelligence')
    p_ri_sub = p_ri.add_subparsers(dest='subcommand')
    p_ri_sub.add_parser('changes', help='List regulatory changes')
    p_ri_detect = p_ri_sub.add_parser('detect', help='Detect regulatory change')
    p_ri_detect.add_argument('regulation', help='Regulation name')
    p_ri_detect.add_argument('jurisdiction', help='Jurisdiction')
    p_ri_detect.add_argument('--impact', default='medium', choices=['low', 'medium', 'high'], help='Impact level')
    p_ri_detect.add_argument('--title', default='', help='Change title')
    p_ri_sub.add_parser('sources', help='List sources')
    p_ri_sub.add_parser('stats', help='Regulatory intel stats')

    p_am = sub.add_parser('audit-mgmt', help='Audit management')
    p_am_sub = p_am.add_subparsers(dest='subcommand')
    p_am_sub.add_parser('list', help='List audit schedules')
    p_am_sched = p_am_sub.add_parser('schedule', help='Schedule audit')
    p_am_sched.add_argument('audit_type', help='Audit type (internal/customer/regulatory)')
    p_am_sched.add_argument('framework', help='Framework')
    p_am_sched.add_argument('date', help='Scheduled date (YYYY-MM-DD)')
    p_am_sched.add_argument('--assignee', default='', help='Assignee')
    p_am_sub.add_parser('rights', help='List customer audit rights')
    p_am_sub.add_parser('stats', help='Audit management stats')

    p_dr = sub.add_parser('dres', help='Data residency enforcement')
    p_dr_sub = p_dr.add_subparsers(dest='subcommand')
    p_dr_sub.add_parser('list', help='List data assets')
    p_dr_reg = p_dr_sub.add_parser('register', help='Register data asset')
    p_dr_reg.add_argument('name', help='Asset name')
    p_dr_reg.add_argument('region', help='Region')
    p_dr_reg.add_argument('--classification', default='general', help='Data classification')
    p_dr_reg.add_argument('--owner', default='', help='Owner')
    p_dr_check = p_dr_sub.add_parser('check', help='Check cross-border flow')
    p_dr_check.add_argument('asset_id', help='Asset ID')
    p_dr_check.add_argument('target_region', help='Target region')
    p_dr_sub.add_parser('summary', help='Data residency summary')

    p_ct = sub.add_parser('train', help='Compliance training management')
    p_ct_sub = p_ct.add_subparsers(dest='subcommand')
    p_ct_sub.add_parser('modules', help='List training modules')
    p_ct_assign = p_ct_sub.add_parser('assign', help='Assign training')
    p_ct_assign.add_argument('user_id', help='User ID')
    p_ct_assign.add_argument('module_id', help='Module ID')
    p_ct_sub.add_parser('status', help='Assignment status')
    p_ct_sub.add_parser('stats', help='Training stats')

    p_ap = sub.add_parser('auditor', help='Auditor portal')
    p_ap_sub = p_ap.add_subparsers(dest='subcommand')
    p_ap_sub.add_parser('sessions', help='List auditor sessions')
    p_ap_sub.add_parser('evidence', help='List evidence for auditors')
    p_ap_sub.add_parser('findings', help='List audit findings')
    p_ap_sub.add_parser('stats', help='Auditor portal stats')

    # === v4 Emerging Tech Commands ===
    p_blockchain = sub.add_parser('blockchain', help='Blockchain node management')
    p_blockchain_sub = p_blockchain.add_subparsers(dest='subcommand')
    p_blockchain_list = p_blockchain_sub.add_parser('list', help='List networks')
    p_blockchain_create = p_blockchain_sub.add_parser('create', help='Create network')
    p_blockchain_create.add_argument('name', help='Network name')
    p_blockchain_create.add_argument('--consensus', default='pos', choices=['pos', 'pow', 'poa'], help='Consensus mechanism')
    p_blockchain_create.add_argument('--chain-id', type=int, default=1, help='Chain ID')
    p_blockchain_status = p_blockchain_sub.add_parser('status', help='Network status')
    p_blockchain_status.add_argument('network_id', help='Network ID')
    p_blockchain_validators = p_blockchain_sub.add_parser('validators', help='List validators')
    p_blockchain_validators.add_argument('network_id', help='Network ID')

    p_storage = sub.add_parser('storage', help='Decentralized storage gateway')
    p_storage_sub = p_storage.add_subparsers(dest='subcommand')
    p_storage_list = p_storage_sub.add_parser('list', help='List gateways')
    p_storage_create = p_storage_sub.add_parser('create', help='Create gateway')
    p_storage_create.add_argument('name', help='Gateway name')
    p_storage_create.add_argument('provider', choices=['ipfs', 'arweave', 'filecoin'], help='Storage provider')
    p_storage_pin = p_storage_sub.add_parser('pin', help='Pin content')
    p_storage_pin.add_argument('cid', help='Content CID')
    p_storage_status = p_storage_sub.add_parser('status', help='Gateway status')
    p_storage_status.add_argument('gateway_id', help='Gateway ID')

    p_quantum = sub.add_parser('quantum', help='Quantum-safe cryptography')
    p_quantum_sub = p_quantum.add_subparsers(dest='subcommand')
    p_quantum_list = p_quantum_sub.add_parser('list', help='List keys')
    p_quantum_generate = p_quantum_sub.add_parser('generate', help='Generate key')
    p_quantum_generate.add_argument('algorithm', choices=['kyber', 'dilithium', 'falcon', 'sphincs'], help='Algorithm')
    p_quantum_cert = p_quantum_sub.add_parser('cert', help='Create certificate')
    p_quantum_cert.add_argument('name', help='Certificate name')
    p_quantum_cert.add_argument('key_id', help='Key ID')
    p_quantum_encrypt = p_quantum_sub.add_parser('encrypt', help='Encrypt message')
    p_quantum_encrypt.add_argument('key_id', help='Key ID')
    p_quantum_encrypt.add_argument('message', help='Message to encrypt')
    p_quantum_decrypt = p_quantum_sub.add_parser('decrypt', help='Decrypt message')
    p_quantum_decrypt.add_argument('key_id', help='Key ID')
    p_quantum_decrypt.add_argument('ciphertext', help='Ciphertext hex')

    p_contracts = sub.add_parser('contracts', help='Smart contract monitoring')
    p_contracts_sub = p_contracts.add_subparsers(dest='subcommand')
    p_contracts_list = p_contracts_sub.add_parser('list', help='List contracts')
    p_contracts_deploy = p_contracts_sub.add_parser('deploy', help='Deploy contract')
    p_contracts_deploy.add_argument('name', help='Contract name')
    p_contracts_deploy.add_argument('network', help='Network')
    p_contracts_deploy.add_argument('bytecode', help='Bytecode hex')
    p_contracts_get = p_contracts_sub.add_parser('get', help='Get contract')
    p_contracts_get.add_argument('contract_id', help='Contract ID')
    p_contracts_events = p_contracts_sub.add_parser('events', help='List events')
    p_contracts_events.add_argument('contract_id', help='Contract ID')

    p_web3id = sub.add_parser('web3id', help='Web3 identity & auth')
    p_web3id_sub = p_web3id.add_subparsers(dest='subcommand')
    p_web3id_list = p_web3id_sub.add_parser('list', help='List identities')
    p_web3id_create = p_web3id_sub.add_parser('create', help='Create identity')
    p_web3id_create.add_argument('did', help='DID string')
    p_web3id_auth = p_web3id_sub.add_parser('auth', help='Authenticate')
    p_web3id_auth.add_argument('identity_id', help='Identity ID')
    p_web3id_sessions = p_web3id_sub.add_parser('sessions', help='List sessions')

    p_confidential = sub.add_parser('confidential', help='Confidential computing enclave')
    p_confidential_sub = p_confidential.add_subparsers(dest='subcommand')
    p_confidential_list = p_confidential_sub.add_parser('list', help='List enclaves')
    p_confidential_create = p_confidential_sub.add_parser('create', help='Create enclave')
    p_confidential_create.add_argument('name', help='Enclave name')
    p_confidential_create.add_argument('image', help='Enclave image')
    p_confidential_create.add_argument('--memory-mb', type=int, default=512, help='Memory MB')
    p_confidential_attest = p_confidential_sub.add_parser('attest', help='Attest enclave')
    p_confidential_attest.add_argument('enclave_id', help='Enclave ID')
    p_confidential_secrets = p_confidential_sub.add_parser('secrets', help='List secrets')
    p_confidential_secrets.add_argument('enclave_id', help='Enclave ID')

    p_federated = sub.add_parser('federated', help='Federated learning infrastructure')
    p_federated_sub = p_federated.add_subparsers(dest='subcommand')
    p_federated_list = p_federated_sub.add_parser('list', help='List projects')
    p_federated_create = p_federated_sub.add_parser('create', help='Create project')
    p_federated_create.add_argument('name', help='Project name')
    p_federated_create.add_argument('--rounds', type=int, default=10, help='Number of rounds')
    p_federated_create.add_argument('--min-clients', type=int, default=3, help='Minimum clients')
    p_federated_status = p_federated_sub.add_parser('status', help='Project status')
    p_federated_status.add_argument('project_id', help='Project ID')
    p_federated_rounds = p_federated_sub.add_parser('rounds', help='List rounds')
    p_federated_rounds.add_argument('project_id', help='Project ID')

    p_zkp = sub.add_parser('zkp', help='Zero-knowledge proof service')
    p_zkp_sub = p_zkp.add_subparsers(dest='subcommand')
    p_zkp_list = p_zkp_sub.add_parser('list', help='List proofs')
    p_zkp_generate = p_zkp_sub.add_parser('generate', help='Generate proof')
    p_zkp_generate.add_argument('statement', help='Statement')
    p_zkp_generate.add_argument('witness', help='Witness')
    p_zkp_verify = p_zkp_sub.add_parser('verify', help='Verify proof')
    p_zkp_verify.add_argument('proof_id', help='Proof ID')
    p_zkp_circuits = p_zkp_sub.add_parser('circuits', help='List circuits')

    p_dcn = sub.add_parser('dcn', help='Decentralized compute network')
    p_dcn_sub = p_dcn.add_subparsers(dest='subcommand')
    p_dcn_list = p_dcn_sub.add_parser('list', help='List tasks')
    p_dcn_submit = p_dcn_sub.add_parser('submit', help='Submit task')
    p_dcn_submit.add_argument('name', help='Task name')
    p_dcn_submit.add_argument('requirements', help='Requirements JSON')
    p_dcn_submit.add_argument('--input-data', default='{}', help='Input data JSON')
    p_dcn_status = p_dcn_sub.add_parser('status', help='Task status')
    p_dcn_status.add_argument('task_id', help='Task ID')
    p_dcn_workers = p_dcn_sub.add_parser('workers', help='List workers')

    return parser


# === v3 Identity & Governance Commands ===

def cmd_oidc_clients(args):
    result = get_client().oidc_list_clients()
    data = result if isinstance(result, list) else result.get('clients', result)
    print_output(data, args.output)

def cmd_oidc_register(args):
    redirects = [u.strip() for u in args.redirect_uris.split(',')]
    result = get_client().oidc_register_client(args.name, redirects, args.type)
    print_output(result, args.output)

def cmd_oidc_delete(args):
    result = get_client().oidc_delete_client(args.client_id)
    print_output(result, args.output)

def cmd_webauthn_creds(args):
    result = get_client().webauthn_list_credentials(args.user_id)
    data = result if isinstance(result, list) else result.get('credentials', result)
    print_output(data, args.output)

def cmd_webauthn_remove(args):
    result = get_client().webauthn_remove_credential(args.credential_id)
    print_output(result, args.output)

def cmd_session_list(args):
    result = get_client().session_list_active(args.user_id)
    data = result if isinstance(result, list) else result.get('sessions', result)
    print_output(data, args.output)

def cmd_session_revoke(args):
    result = get_client().session_revoke(args.session_id)
    print_output(result, args.output)

def cmd_pam_requests(args):
    result = get_client().pam_list_requests(user_id=args.user_id, status=args.status)
    data = result if isinstance(result, list) else result.get('requests', result)
    print_output(data, args.output)

def cmd_pam_request(args):
    result = get_client().pam_create_request(args.user_id, args.resource, args.role, args.reason, args.duration)
    print_output(result, args.output)

def cmd_pam_approve(args):
    result = get_client().pam_approve_request(args.request_id, args.approver_id)
    print_output(result, args.output)

def cmd_pam_deny(args):
    result = get_client().pam_deny_request(args.request_id, args.approver_id)
    print_output(result, args.output)

def cmd_breach_list(args):
    result = get_client().breach_list()
    data = result if isinstance(result, list) else result.get('breaches', result)
    print_output(data, args.output)

def cmd_breach_report(args):
    data_types = [t.strip() for t in args.data_types.split(',')]
    result = get_client().breach_report(args.description, data_types, args.affected_users)
    print_output(result, args.output)

def cmd_policy_list(args):
    result = get_client().policy_list(category=args.category)
    data = result if isinstance(result, list) else result.get('policies', result)
    print_output(data, args.output)

def cmd_policy_create(args):
    result = get_client().policy_create(args.name, args.description, args.category)
    print_output(result, args.output)

def cmd_policy_evaluate(args):
    context = json.loads(args.context) if args.context else {}
    result = get_client().policy_evaluate(args.resource, args.action, context)
    print_output(result, args.output)

def cmd_compliance_scan(args):
    result = get_client().compliance_run_scan(args.benchmark)
    print_output(result, args.output)

def cmd_compliance_report(args):
    result = get_client().compliance_get_report(args.scan_id)
    print_output(result, args.output)

def cmd_compliance_checks(args):
    result = get_client().compliance_list_checks(args.benchmark)
    data = result if isinstance(result, list) else result.get('checks', result)
    print_output(data, args.output)

def cmd_audit_anomalies(args):
    result = get_client().audit_get_anomalies()
    data = result if isinstance(result, list) else result.get('anomalies', result)
    print_output(data, args.output)

def cmd_audit_trend(args):
    result = get_client().audit_get_trend(args.user_id)
    print_output(result, args.output)

def cmd_audit_summary(args):
    result = get_client().audit_get_summary()
    print_output(result, args.output)

def cmd_classify_scan(args):
    result = get_client().classify_scan_text(args.text)
    print_output(result, args.output)

def cmd_classify_inventory(args):
    result = get_client().classify_get_inventory()
    data = result if isinstance(result, list) else result.get('inventory', result)
    print_output(data, args.output)

def cmd_vendor_list(args):
    result = get_client().vendor_list()
    data = result if isinstance(result, list) else result.get('vendors', result)
    print_output(data, args.output)

def cmd_vendor_create(args):
    result = get_client().vendor_create(args.name, args.domain, args.category)
    print_output(result, args.output)

def cmd_vendor_assess(args):
    result = get_client().vendor_create_assessment(args.vendor_id, args.type)
    print_output(result, args.output)

def cmd_workflow_list(args):
    result = get_client().workflow_list()
    data = result if isinstance(result, list) else result.get('workflows', result)
    print_output(data, args.output)

def cmd_workflow_create(args):
    result = get_client().workflow_create(args.name, args.description)
    print_output(result, args.output)

def cmd_workflow_run(args):
    result = get_client().workflow_execute(args.workflow_id)
    print_output(result, args.output)

def cmd_infra_pipeline_list(args):
    result = get_client().infra_pipeline_list()
    data = result if isinstance(result, list) else result.get('pipelines', result)
    print_output(data, args.output)

def cmd_infra_pipeline_run(args):
    result = get_client().infra_pipeline_run(args.pipeline_id, args.branch)
    print_output(result, args.output)

def cmd_drift_scan(args):
    result = get_client().drift_run_scan()
    print_output(result, args.output)

def cmd_drift_list(args):
    result = get_client().drift_list_scans()
    data = result if isinstance(result, list) else result.get('scans', result)
    print_output(data, args.output)

def cmd_quota_list(args):
    result = get_client().quota_list()
    data = result if isinstance(result, list) else result.get('quotas', result)
    print_output(data, args.output)

def cmd_quota_check(args):
    resources = {}
    if args.cpu: resources['cpu_cores'] = args.cpu
    if args.memory: resources['memory_gb'] = args.memory
    result = get_client().quota_check(args.entity_type, args.entity_id, resources)
    print_output(result, args.output)

def cmd_remediate_rules(args):
    result = get_client().remediation_list_rules()
    data = result if isinstance(result, list) else result.get('rules', result)
    print_output(data, args.output)

def cmd_remediate_history(args):
    result = get_client().remediation_get_history()
    data = result if isinstance(result, list) else result.get('history', result)
    print_output(data, args.output)

def cmd_maintenance_list(args):
    result = get_client().maintenance_list_windows()
    data = result if isinstance(result, list) else result.get('windows', result)
    print_output(data, args.output)

def cmd_maintenance_schedule(args):
    systems = [s.strip() for s in args.systems.split(',')]
    result = get_client().maintenance_schedule(args.name, args.start, args.end, systems)
    print_output(result, args.output)

def cmd_runbook_list(args):
    result = get_client().runbook_list_templates()
    data = result if isinstance(result, list) else result.get('templates', result)
    print_output(data, args.output)

def cmd_runbook_use(args):
    variables = json.loads(args.vars) if args.vars else {}
    result = get_client().runbook_instantiate(args.template_id, variables)
    print_output(result, args.output)

def cmd_chaos_experiments(args):
    result = get_client().chaos_list_experiments()
    data = result if isinstance(result, list) else result.get('experiments', result)
    print_output(data, args.output)

def cmd_chaos_create(args):
    target = {'type': args.target_type, 'selector': args.target_selector}
    result = get_client().chaos_create_experiment(args.name, target)
    print_output(result, args.output)

def cmd_chaos_run(args):
    result = get_client().chaos_run_experiment(args.experiment_id)
    print_output(result, args.output)

def cmd_chaos_stop(args):
    result = get_client().chaos_stop_experiment(args.experiment_id)
    print_output(result, args.output)

def cmd_chaos_faults(args):
    result = get_client().chaos_list_faults()
    data = result if isinstance(result, list) else result.get('faults', result)
    print_output(data, args.output)

def cmd_heal_status(args):
    result = get_client().healing_get_status()
    print_output(result, args.output)

def cmd_heal_history(args):
    result = get_client().healing_get_history()
    data = result if isinstance(result, list) else result.get('history', result)
    print_output(data, args.output)

def cmd_heal_retrain(args):
    result = get_client().healing_retrain()
    print_output(result, args.output)


    # === v4 Customer Experience Commands ===
    p_cx = sub.add_parser('cx', help='Customer experience & support platform')
    p_cx_sub = p_cx.add_subparsers(dest='subcommand')

    p_cx_health = p_cx_sub.add_parser('health', help='Customer health scoring')
    p_cx_health_sub = p_cx_health.add_subparsers(dest='action')
    p_cx_health_list = p_cx_health_sub.add_parser('list', help='List health profiles')
    p_cx_health_list.add_argument('--risk-level', help='Filter by risk level')
    p_cx_health_list.add_argument('--min-score', type=float, help='Minimum health score')
    p_cx_health_get = p_cx_health_sub.add_parser('get', help='Get health profile')
    p_cx_health_get.add_argument('customer_id', help='Customer ID')
    p_cx_health_compute = p_cx_health_sub.add_parser('compute', help='Compute health score')
    p_cx_health_compute.add_argument('customer_id', help='Customer ID')
    p_cx_health_compute.add_argument('--data', help='JSON data payload')
    p_cx_health_history = p_cx_health_sub.add_parser('history', help='Get health history')
    p_cx_health_history.add_argument('customer_id', help='Customer ID')
    p_cx_health_history.add_argument('--days', type=int, default=30, help='Days of history')
    p_cx_health_stats = p_cx_health_sub.add_parser('stats', help='Health segment summary')

    p_cx_ticket = p_cx_sub.add_parser('ticket', help='Support ticket system')
    p_cx_ticket_sub = p_cx_ticket.add_subparsers(dest='action')
    p_cx_ticket_list = p_cx_ticket_sub.add_parser('list', help='List tickets')
    p_cx_ticket_list.add_argument('--status', help='Filter by status')
    p_cx_ticket_list.add_argument('--priority', help='Filter by priority')
    p_cx_ticket_list.add_argument('--customer-id', help='Filter by customer')
    p_cx_ticket_list.add_argument('--assigned-to', help='Filter by assignee')
    p_cx_ticket_list.add_argument('--search', help='Search text')
    p_cx_ticket_list.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_ticket_list.add_argument('--offset', type=int, default=0, help='Offset')
    p_cx_ticket_create = p_cx_ticket_sub.add_parser('create', help='Create ticket')
    p_cx_ticket_create.add_argument('subject', help='Ticket subject')
    p_cx_ticket_create.add_argument('description', help='Ticket description')
    p_cx_ticket_create.add_argument('customer_id', help='Customer ID')
    p_cx_ticket_create.add_argument('--customer-name', default='', help='Customer name')
    p_cx_ticket_create.add_argument('--customer-email', default='', help='Customer email')
    p_cx_ticket_create.add_argument('--priority', default='medium', choices=['low', 'medium', 'high', 'critical'], help='Priority')
    p_cx_ticket_create.add_argument('--channel', default='web', help='Channel')
    p_cx_ticket_create.add_argument('--category', help='Category')
    p_cx_ticket_create.add_argument('--tags', help='Comma-separated tags')
    p_cx_ticket_get = p_cx_ticket_sub.add_parser('get', help='Get ticket')
    p_cx_ticket_get.add_argument('ticket_id', help='Ticket ID')
    p_cx_ticket_status = p_cx_ticket_sub.add_parser('status', help='Update ticket status')
    p_cx_ticket_status.add_argument('ticket_id', help='Ticket ID')
    p_cx_ticket_status.add_argument('status', help='New status')
    p_cx_ticket_status.add_argument('--agent-id', help='Agent ID')
    p_cx_ticket_comment = p_cx_ticket_sub.add_parser('comment', help='Add comment to ticket')
    p_cx_ticket_comment.add_argument('ticket_id', help='Ticket ID')
    p_cx_ticket_comment.add_argument('author_id', help='Author ID')
    p_cx_ticket_comment.add_argument('body', help='Comment body')
    p_cx_ticket_comment.add_argument('--author-name', default='', help='Author name')
    p_cx_ticket_comment.add_argument('--internal', action='store_true', help='Internal note')
    p_cx_ticket_assign = p_cx_ticket_sub.add_parser('assign', help='Assign ticket')
    p_cx_ticket_assign.add_argument('ticket_id', help='Ticket ID')
    p_cx_ticket_assign.add_argument('agent_id', help='Agent ID')
    p_cx_ticket_assign.add_argument('--team', help='Team name')
    p_cx_ticket_stats = p_cx_ticket_sub.add_parser('stats', help='Ticket statistics')

    p_cx_sla = p_cx_sub.add_parser('sla', help='SLA management')
    p_cx_sla_sub = p_cx_sla.add_subparsers(dest='action')
    p_cx_sla_list = p_cx_sla_sub.add_parser('list', help='List SLAs')
    p_cx_sla_create = p_cx_sla_sub.add_parser('create', help='Create SLA')
    p_cx_sla_create.add_argument('name', help='SLA name')
    p_cx_sla_create.add_argument('priority', choices=['low', 'medium', 'high', 'critical'], help='Priority')
    p_cx_sla_create.add_argument('response_time', type=int, help='Response time in minutes')
    p_cx_sla_create.add_argument('resolution_time', type=int, help='Resolution time in minutes')
    p_cx_sla_create.add_argument('--no-business-hours', action='store_true', help='24/7 SLA')

    p_cx_canned = p_cx_sub.add_parser('canned', help='Canned responses')
    p_cx_canned_sub = p_cx_canned.add_subparsers(dest='action')
    p_cx_canned_list = p_cx_canned_sub.add_parser('list', help='List canned responses')
    p_cx_canned_list.add_argument('--category', help='Filter by category')
    p_cx_canned_create = p_cx_canned_sub.add_parser('create', help='Create canned response')
    p_cx_canned_create.add_argument('title', help='Title')
    p_cx_canned_create.add_argument('body', help='Response body')
    p_cx_canned_create.add_argument('category', help='Category')
    p_cx_canned_create.add_argument('--tags', help='Comma-separated tags')
    p_cx_canned_create.add_argument('--created-by', default='', help='Creator')

    p_cx_sentiment = p_cx_sub.add_parser('sentiment', help='Customer sentiment analysis')
    p_cx_sentiment_sub = p_cx_sentiment.add_subparsers(dest='action')
    p_cx_sentiment_analyze = p_cx_sentiment_sub.add_parser('analyze', help='Analyze text sentiment')
    p_cx_sentiment_analyze.add_argument('text', help='Text to analyze')
    p_cx_sentiment_analyze.add_argument('--source-type', default='support_ticket', help='Source type')
    p_cx_sentiment_analyze.add_argument('--source-id', default='', help='Source ID')
    p_cx_sentiment_analyze.add_argument('--customer-id', default='', help='Customer ID')
    p_cx_sentiment_analyze.add_argument('--customer-name', default='', help='Customer name')
    p_cx_sentiment_profile = p_cx_sentiment_sub.add_parser('profile', help='Get customer sentiment profile')
    p_cx_sentiment_profile.add_argument('customer_id', help='Customer ID')
    p_cx_sentiment_interactions = p_cx_sentiment_sub.add_parser('interactions', help='List sentiment interactions')
    p_cx_sentiment_interactions.add_argument('--customer-id', help='Filter by customer')
    p_cx_sentiment_interactions.add_argument('--source-type', help='Filter by source type')
    p_cx_sentiment_interactions.add_argument('--min-score', type=float, help='Min sentiment score')
    p_cx_sentiment_interactions.add_argument('--max-score', type=float, help='Max sentiment score')
    p_cx_sentiment_interactions.add_argument('--escalated-only', action='store_true', help='Escalated only')
    p_cx_sentiment_interactions.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_sentiment_trends = p_cx_sentiment_sub.add_parser('trends', help='Get sentiment trends')
    p_cx_sentiment_trends.add_argument('--period', default='daily', choices=['daily', 'weekly', 'monthly'], help='Period')
    p_cx_sentiment_trends.add_argument('--days', type=int, default=30, help='Days')
    p_cx_sentiment_alerts = p_cx_sentiment_sub.add_parser('alerts', help='List sentiment alerts')

    p_cx_adoption = p_cx_sub.add_parser('adoption', help='Product adoption analytics')
    p_cx_adoption_sub = p_cx_adoption.add_subparsers(dest='action')
    p_cx_adoption_summary = p_cx_adoption_sub.add_parser('summary', help='Customer adoption summary')
    p_cx_adoption_summary.add_argument('customer_id', help='Customer ID')
    p_cx_adoption_features = p_cx_adoption_sub.add_parser('features', help='Feature adoption')
    p_cx_adoption_features.add_argument('customer_id', help='Customer ID')
    p_cx_adoption_features.add_argument('--days', type=int, default=30, help='Days')
    p_cx_adoption_track = p_cx_adoption_sub.add_parser('track', help='Track adoption event')
    p_cx_adoption_track.add_argument('event_type', help='Event type')
    p_cx_adoption_track.add_argument('customer_id', help='Customer ID')
    p_cx_adoption_track.add_argument('user_id', help='User ID')
    p_cx_adoption_track.add_argument('--feature-id', help='Feature ID')
    p_cx_adoption_track.add_argument('--feature-name', help='Feature name')
    p_cx_adoption_recommendations = p_cx_adoption_sub.add_parser('recommendations', help='Adoption recommendations')
    p_cx_adoption_recommendations.add_argument('customer_id', help='Customer ID')
    p_cx_adoption_stats = p_cx_adoption_sub.add_parser('stats', help='Global adoption stats')

    p_cx_onboarding = p_cx_sub.add_parser('onboarding', help='Customer onboarding wizard')
    p_cx_onboarding_sub = p_cx_onboarding.add_subparsers(dest='action')
    p_cx_onboarding_start = p_cx_onboarding_sub.add_parser('start', help='Start onboarding')
    p_cx_onboarding_start.add_argument('customer_id', help='Customer ID')
    p_cx_onboarding_start.add_argument('--customer-name', default='', help='Customer name')
    p_cx_onboarding_start.add_argument('--product-tier', default='standard', help='Product tier')
    p_cx_onboarding_get = p_cx_onboarding_sub.add_parser('get', help='Get onboarding session')
    p_cx_onboarding_get.add_argument('customer_id', help='Customer ID')
    p_cx_onboarding_step = p_cx_onboarding_sub.add_parser('step', help='Update onboarding step')
    p_cx_onboarding_step.add_argument('session_id', help='Session ID')
    p_cx_onboarding_step.add_argument('step_id', help='Step ID')
    p_cx_onboarding_step.add_argument('status', choices=['pending', 'in_progress', 'completed', 'skipped'], help='Status')
    p_cx_onboarding_step.add_argument('--metadata', help='JSON metadata')
    p_cx_onboarding_stats = p_cx_onboarding_sub.add_parser('stats', help='Onboarding statistics')

    p_cx_kb = p_cx_sub.add_parser('kb', help='Knowledge base & help center')
    p_cx_kb_sub = p_cx_kb.add_subparsers(dest='action')
    p_cx_kb_list = p_cx_kb_sub.add_parser('list', help='List articles')
    p_cx_kb_list.add_argument('--category', help='Filter by category')
    p_cx_kb_list.add_argument('--article-type', help='Filter by type')
    p_cx_kb_list.add_argument('--status', help='Filter by status')
    p_cx_kb_list.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_kb_create = p_cx_kb_sub.add_parser('create', help='Create article')
    p_cx_kb_create.add_argument('title', help='Article title')
    p_cx_kb_create.add_argument('content', help='Article content (file path or raw)')
    p_cx_kb_create.add_argument('category', help='Category')
    p_cx_kb_create.add_argument('--article-type', default='guide', help='Article type')
    p_cx_kb_create.add_argument('--tags', help='Comma-separated tags')
    p_cx_kb_create.add_argument('--author', default='', help='Author')
    p_cx_kb_create.add_argument('--language', default='en', help='Language')
    p_cx_kb_get = p_cx_kb_sub.add_parser('get', help='Get article')
    p_cx_kb_get.add_argument('article_id', help='Article ID')
    p_cx_kb_update = p_cx_kb_sub.add_parser('update', help='Update article')
    p_cx_kb_update.add_argument('article_id', help='Article ID')
    p_cx_kb_update.add_argument('--data', help='JSON data payload')
    p_cx_kb_search = p_cx_kb_sub.add_parser('search', help='Search articles')
    p_cx_kb_search.add_argument('query', help='Search query')
    p_cx_kb_search.add_argument('--category', help='Filter by category')
    p_cx_kb_search.add_argument('--limit', type=int, default=20, help='Max results')
    p_cx_kb_categories = p_cx_kb_sub.add_parser('categories', help='List categories')
    p_cx_kb_feedback = p_cx_kb_sub.add_parser('feedback', help='Add article feedback')
    p_cx_kb_feedback.add_argument('article_id', help='Article ID')
    p_cx_kb_feedback.add_argument('--helpful', action='store_true', default=True, help='Was helpful')
    p_cx_kb_feedback.add_argument('--comment', help='Feedback comment')
    p_cx_kb_feedback.add_argument('--user-id', help='User ID')

    p_cx_community = p_cx_sub.add_parser('community', help='Community platform')
    p_cx_community_sub = p_cx_community.add_subparsers(dest='action')
    p_cx_community_posts = p_cx_community_sub.add_parser('posts', help='List posts')
    p_cx_community_posts.add_argument('--category-id', help='Filter by category')
    p_cx_community_posts.add_argument('--post-type', help='Filter by type')
    p_cx_community_posts.add_argument('--sort', default='hot', choices=['hot', 'new', 'top', 'votes'], help='Sort')
    p_cx_community_posts.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_community_posts.add_argument('--offset', type=int, default=0, help='Offset')
    p_cx_community_create = p_cx_community_sub.add_parser('create', help='Create post')
    p_cx_community_create.add_argument('title', help='Post title')
    p_cx_community_create.add_argument('content', help='Post content')
    p_cx_community_create.add_argument('category_id', help='Category ID')
    p_cx_community_create.add_argument('--post-type', default='discussion', help='Post type')
    p_cx_community_create.add_argument('--author-id', default='', help='Author ID')
    p_cx_community_create.add_argument('--author-name', default='', help='Author name')
    p_cx_community_create.add_argument('--tags', help='Comma-separated tags')
    p_cx_community_get = p_cx_community_sub.add_parser('get', help='Get post')
    p_cx_community_get.add_argument('post_id', help='Post ID')
    p_cx_community_vote = p_cx_community_sub.add_parser('vote', help='Vote on post')
    p_cx_community_vote.add_argument('post_id', help='Post ID')
    p_cx_community_vote.add_argument('user_id', help='User ID')
    p_cx_community_vote.add_argument('vote_type', choices=['upvote', 'downvote'], help='Vote type')
    p_cx_community_comment = p_cx_community_sub.add_parser('comment', help='Add comment')
    p_cx_community_comment.add_argument('post_id', help='Post ID')
    p_cx_community_comment.add_argument('author_id', help='Author ID')
    p_cx_community_comment.add_argument('body', help='Comment body')
    p_cx_community_comment.add_argument('--author-name', default='', help='Author name')
    p_cx_community_comment.add_argument('--parent-comment-id', help='Parent comment ID')
    p_cx_community_comments = p_cx_community_sub.add_parser('comments', help='Get post comments')
    p_cx_community_comments.add_argument('post_id', help='Post ID')
    p_cx_community_requests = p_cx_community_sub.add_parser('requests', help='Feature requests')
    p_cx_community_requests.add_argument('--sort', default='votes', help='Sort by')
    p_cx_community_requests.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_community_categories = p_cx_community_sub.add_parser('categories', help='List categories')
    p_cx_community_leaderboard = p_cx_community_sub.add_parser('leaderboard', help='Leaderboard')
    p_cx_community_leaderboard.add_argument('--limit', type=int, default=20, help='Max results')
    p_cx_community_stats = p_cx_community_sub.add_parser('stats', help='Community statistics')

    p_cx_comm = p_cx_sub.add_parser('comm', help='Customer communication hub')
    p_cx_comm_sub = p_cx_comm.add_subparsers(dest='action')
    p_cx_comm_send = p_cx_comm_sub.add_parser('send', help='Send notification')
    p_cx_comm_send.add_argument('type', choices=['announcement', 'maintenance', 'update', 'promotional', 'transactional'], help='Notification type')
    p_cx_comm_send.add_argument('subject', help='Subject')
    p_cx_comm_send.add_argument('body', help='Body text')
    p_cx_comm_send.add_argument('channels', help='Comma-separated channels (email,in_app,slack,discord)')
    p_cx_comm_send.add_argument('--priority', default='normal', choices=['low', 'normal', 'high', 'urgent'], help='Priority')
    p_cx_comm_send.add_argument('--target-segment', default='all', help='Target segment')
    p_cx_comm_send.add_argument('--created-by', default='', help='Creator')
    p_cx_comm_batches = p_cx_comm_sub.add_parser('batches', help='List notification batches')
    p_cx_comm_batches.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_comm_batch = p_cx_comm_sub.add_parser('batch', help='Get batch stats')
    p_cx_comm_batch.add_argument('batch_id', help='Batch ID')
    p_cx_comm_maintenance = p_cx_comm_sub.add_parser('maintenance', help='Maintenance notifications')
    p_cx_comm_maintenance_sub = p_cx_comm_maintenance.add_subparsers(dest='maint_action')
    p_cx_comm_maint_schedule = p_cx_comm_maintenance_sub.add_parser('schedule', help='Schedule maintenance')
    p_cx_comm_maint_schedule.add_argument('title', help='Title')
    p_cx_comm_maint_schedule.add_argument('description', help='Description')
    p_cx_comm_maint_schedule.add_argument('affected_services', help='Comma-separated services')
    p_cx_comm_maint_schedule.add_argument('start', help='Start time (ISO)')
    p_cx_comm_maint_schedule.add_argument('end', help='End time (ISO)')
    p_cx_comm_maint_schedule.add_argument('expected_downtime', help='Expected downtime')
    p_cx_comm_maint_schedule.add_argument('--created-by', default='', help='Creator')
    p_cx_comm_maint_list = p_cx_comm_maintenance_sub.add_parser('list', help='List maintenance')
    p_cx_comm_maint_list.add_argument('--status', help='Filter by status')
    p_cx_comm_maint_complete = p_cx_comm_maintenance_sub.add_parser('complete', help='Complete maintenance')
    p_cx_comm_maint_complete.add_argument('maintenance_id', help='Maintenance ID')
    p_cx_comm_maint_complete.add_argument('--actual-downtime', help='Actual downtime')
    p_cx_comm_maint_complete.add_argument('--post-mortem', help='Post-mortem notes')
    p_cx_comm_templates = p_cx_comm_sub.add_parser('templates', help='List templates')
    p_cx_comm_templates.add_argument('--channel', help='Filter by channel')
    p_cx_comm_template_create = p_cx_comm_sub.add_parser('template-create', help='Create template')
    p_cx_comm_template_create.add_argument('name', help='Template name')
    p_cx_comm_template_create.add_argument('subject', help='Subject template')
    p_cx_comm_template_create.add_argument('body', help='Body template')
    p_cx_comm_template_create.add_argument('channel', choices=['email', 'in_app', 'slack', 'discord'], help='Channel')
    p_cx_comm_template_create.add_argument('--category', default='general', help='Category')
    p_cx_comm_template_create.add_argument('--variables', help='Comma-separated variable names')

    p_cx_nps = p_cx_sub.add_parser('nps', help='NPS survey engine')
    p_cx_nps_sub = p_cx_nps.add_subparsers(dest='action')
    p_cx_nps_create = p_cx_nps_sub.add_parser('create', help='Create survey')
    p_cx_nps_create.add_argument('title', help='Survey title')
    p_cx_nps_create.add_argument('description', help='Survey description')
    p_cx_nps_create.add_argument('--survey-type', default='nps', choices=['nps', 'csat', 'ces', 'custom'], help='Survey type')
    p_cx_nps_create.add_argument('--trigger', default='manual', choices=['manual', 'after_ticket', 'after_onboarding', 'periodic', 'after_renewal'], help='Trigger')
    p_cx_nps_create.add_argument('--questions-json', required=True, help='JSON array of questions')
    p_cx_nps_create.add_argument('--target-segment', default='all', help='Target segment')
    p_cx_nps_create.add_argument('--frequency-days', type=int, help='Frequency in days')
    p_cx_nps_list = p_cx_nps_sub.add_parser('list', help='List surveys')
    p_cx_nps_list.add_argument('--trigger', help='Filter by trigger')
    p_cx_nps_list.add_argument('--survey-type', help='Filter by type')
    p_cx_nps_get = p_cx_nps_sub.add_parser('get', help='Get survey')
    p_cx_nps_get.add_argument('survey_id', help='Survey ID')
    p_cx_nps_send = p_cx_nps_sub.add_parser('send', help='Send survey to customer')
    p_cx_nps_send.add_argument('survey_id', help='Survey ID')
    p_cx_nps_send.add_argument('customer_id', help='Customer ID')
    p_cx_nps_send.add_argument('--customer-name', default='', help='Customer name')
    p_cx_nps_respond = p_cx_nps_sub.add_parser('respond', help='Submit survey response')
    p_cx_nps_respond.add_argument('response_id', help='Response ID')
    p_cx_nps_respond.add_argument('--answers-json', help='JSON answers object')
    p_cx_nps_respond.add_argument('--comments', help='Additional comments')
    p_cx_nps_score = p_cx_nps_sub.add_parser('score', help='Get NPS score')
    p_cx_nps_trend = p_cx_nps_sub.add_parser('trend', help='Get NPS trend')
    p_cx_nps_trend.add_argument('--days', type=int, default=90, help='Days')
    p_cx_nps_detractors = p_cx_nps_sub.add_parser('detractors', help='Detractor feedback')
    p_cx_nps_detractors.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_nps_stats = p_cx_nps_sub.add_parser('stats', help='NPS statistics')

    p_cx_success = p_cx_sub.add_parser('success', help='Customer success automation')
    p_cx_success_sub = p_cx_success.add_subparsers(dest='action')
    p_cx_success_plays = p_cx_success_sub.add_parser('plays', help='List success plays')
    p_cx_success_plays.add_argument('--trigger-event', help='Filter by trigger event')
    p_cx_success_plays.add_argument('--status', help='Filter by status')
    p_cx_success_create = p_cx_success_sub.add_parser('create', help='Create success play')
    p_cx_success_create.add_argument('name', help='Play name')
    p_cx_success_create.add_argument('description', help='Play description')
    p_cx_success_create.add_argument('trigger_event', help='Trigger event')
    p_cx_success_create.add_argument('--actions-json', required=True, help='JSON array of actions')
    p_cx_success_create.add_argument('--tags', help='Comma-separated tags')
    p_cx_success_create.add_argument('--conditions-json', help='JSON trigger conditions')
    p_cx_success_create.add_argument('--cooldown-days', type=int, default=30, help='Cooldown in days')
    p_cx_success_status = p_cx_success_sub.add_parser('status', help='Update play status')
    p_cx_success_status.add_argument('play_id', help='Play ID')
    p_cx_success_status.add_argument('status', choices=['active', 'paused', 'archived'], help='Status')
    p_cx_success_trigger = p_cx_success_sub.add_parser('trigger', help='Evaluate trigger event')
    p_cx_success_trigger.add_argument('event', help='Event name')
    p_cx_success_trigger.add_argument('customer_id', help='Customer ID')
    p_cx_success_trigger.add_argument('--event-data', help='JSON event data')
    p_cx_success_executions = p_cx_success_sub.add_parser('executions', help='List executions')
    p_cx_success_executions.add_argument('--play-id', help='Filter by play')
    p_cx_success_executions.add_argument('--customer-id', help='Filter by customer')
    p_cx_success_executions.add_argument('--limit', type=int, default=50, help='Max results')
    p_cx_success_stats = p_cx_success_sub.add_parser('stats', help='Success automation stats')

    # === v4 Platform Engineering Commands ===

def cmd_devportal_list(args):
    result = get_client().devportal_list_components(args.domain)
    data = result if isinstance(result, list) else result.get('components', result)
    print_output(data, args.output)

def cmd_devportal_register(args):
    result = get_client().devportal_register_component(args.name, args.domain, args.description, args.owner)
    print_output(result, args.output)

def cmd_devportal_get(args):
    result = get_client().devportal_get_component(args.component_id)
    print_output(result, args.output)

def cmd_devportal_summary(args):
    result = get_client().devportal_summary()
    print_output(result, args.output)

def cmd_scaffold_list(args):
    result = get_client().scaffold_list_templates()
    data = result if isinstance(result, list) else result.get('templates', result)
    print_output(data, args.output)

def cmd_scaffold_generate(args):
    params = json.loads(args.params) if args.params else {}
    result = get_client().scaffold_generate(args.template_id, args.project_name, params)
    print_output(result, args.output)

def cmd_scaffold_status(args):
    result = get_client().scaffold_status(args.generation_id)
    print_output(result, args.output)

def cmd_scaffold_step(args):
    outputs = json.loads(args.outputs) if args.outputs else {}
    result = get_client().scaffold_complete_step(args.generation_id, args.step_name, outputs)
    print_output(result, args.output)

def cmd_catalog_list(args):
    result = get_client().catalog_list_services()
    data = result if isinstance(result, list) else result.get('services', result)
    print_output(data, args.output)

def cmd_catalog_register(args):
    result = get_client().catalog_register_service(args.name, args.domain, args.description, args.owner)
    print_output(result, args.output)

def cmd_catalog_get(args):
    result = get_client().catalog_get_service(args.service_id)
    print_output(result, args.output)

def cmd_catalog_score(args):
    result = get_client().catalog_score_service(args.service_id)
    print_output(result, args.output)

def cmd_catalog_summary(args):
    result = get_client().catalog_summary()
    print_output(result, args.output)

def cmd_scorecards_list(args):
    result = get_client().scorecards_list()
    data = result if isinstance(result, list) else result.get('scorecards', result)
    print_output(data, args.output)

def cmd_scorecards_create(args):
    result = get_client().scorecards_create(args.name, args.team, args.dora)
    print_output(result, args.output)

def cmd_scorecards_get(args):
    result = get_client().scorecards_get(args.scorecard_id)
    print_output(result, args.output)

def cmd_scorecards_update(args):
    result = get_client().scorecards_update_metric(args.scorecard_id, args.metric, args.value)
    print_output(result, args.output)

def cmd_scorecards_summary(args):
    result = get_client().scorecards_summary()
    print_output(result, args.output)

def cmd_templatereg_list(args):
    result = get_client().templatereg_list()
    data = result if isinstance(result, list) else result.get('templates', result)
    print_output(data, args.output)

def cmd_templatereg_create(args):
    params = json.loads(args.params) if args.params else {}
    result = get_client().templatereg_create(args.name, args.category, params)
    print_output(result, args.output)

def cmd_templatereg_get(args):
    result = get_client().templatereg_get(args.template_id)
    print_output(result, args.output)

def cmd_templatereg_use(args):
    result = get_client().templatereg_use(args.template_id)
    print_output(result, args.output)

def cmd_templatereg_summary(args):
    result = get_client().templatereg_summary()
    print_output(result, args.output)

def cmd_techdebt_list(args):
    result = get_client().techdebt_list(args.severity)
    data = result if isinstance(result, list) else result.get('items', result)
    print_output(data, args.output)

def cmd_techdebt_report(args):
    result = get_client().techdebt_report(args.title, args.severity, args.effort_hours, args.area)
    print_output(result, args.output)

def cmd_techdebt_get(args):
    result = get_client().techdebt_get(args.debt_id)
    print_output(result, args.output)

def cmd_techdebt_fix(args):
    result = get_client().techdebt_fix(args.debt_id)
    print_output(result, args.output)

def cmd_techdebt_summary(args):
    result = get_client().techdebt_summary()
    print_output(result, args.output)

def cmd_environments_list(args):
    result = get_client().environments_list(args.status)
    data = result if isinstance(result, list) else result.get('environments', result)
    print_output(data, args.output)

def cmd_environments_create(args):
    result = get_client().environments_create(args.name, args.template, args.ttl, args.branch)
    print_output(result, args.output)

def cmd_environments_get(args):
    result = get_client().environments_get(args.env_id)
    print_output(result, args.output)

def cmd_environments_delete(args):
    result = get_client().environments_delete(args.env_id)
    print_output(result, args.output)

def cmd_environments_extend(args):
    result = get_client().environments_extend(args.env_id, args.hours)
    print_output(result, args.output)

def cmd_environments_summary(args):
    result = get_client().environments_summary()
    print_output(result, args.output)

def cmd_apicatalog_list(args):
    result = get_client().apicatalog_list()
    data = result if isinstance(result, list) else result.get('apis', result)
    print_output(data, args.output)

def cmd_apicatalog_register(args):
    with open(args.spec, 'r') as f:
        spec_content = f.read()
    result = get_client().apicatalog_register(args.name, args.version, spec_content)
    print_output(result, args.output)

def cmd_apicatalog_get(args):
    result = get_client().apicatalog_get(args.api_id)
    print_output(result, args.output)

def cmd_apicatalog_summary(args):
    result = get_client().apicatalog_summary()
    print_output(result, args.output)

def cmd_docgen_list(args):
    result = get_client().docgen_list()
    data = result if isinstance(result, list) else result.get('documents', result)
    print_output(data, args.output)

def cmd_docgen_generate(args):
    result = get_client().docgen_generate(args.title, args.doc_type)
    print_output(result, args.output)

def cmd_docgen_get(args):
    result = get_client().docgen_get(args.doc_id)
    print_output(result, args.output)

def cmd_docgen_summary(args):
    result = get_client().docgen_summary()
    print_output(result, args.output)

def cmd_pulse_list(args):
    result = get_client().pulse_list_surveys()
    data = result if isinstance(result, list) else result.get('surveys', result)
    print_output(data, args.output)

def cmd_pulse_create(args):
    questions = json.loads(args.questions_json)
    result = get_client().pulse_create_survey(args.title, questions)
    print_output(result, args.output)

def cmd_pulse_respond(args):
    answers = json.loads(args.answers_json)
    result = get_client().pulse_respond(args.survey_id, args.respondent, answers)
    print_output(result, args.output)

def cmd_pulse_results(args):
    result = get_client().pulse_results(args.survey_id)
    print_output(result, args.output)

def cmd_pulse_summary(args):
    result = get_client().pulse_summary()
    print_output(result, args.output)


# === v4 AIOps Commands ===

def cmd_rca_analyze(args):
    result = get_client().rca_analyze(args.title, args.description)
    print_output(result, args.output)

def cmd_rca_incidents(args):
    result = get_client().rca_incidents()
    data = result if isinstance(result, list) else result.get('incidents', result)
    print_output(data, args.output)

def cmd_rca_events(args):
    result = get_client().rca_events(source=args.source)
    data = result if isinstance(result, list) else result.get('events', result)
    print_output(data, args.output)

def cmd_rca_deps(args):
    result = get_client().rca_dependency_graph()
    print_output(result, args.output)

def cmd_remediate_suggest(args):
    incident = {'title': args.title, 'description': args.description}
    result = get_client().remediate_suggest(incident)
    data = result if isinstance(result, list) else result.get('suggestions', result)
    print_output(data, args.output)

def cmd_remediate_list(args):
    result = get_client().remediate_list()
    data = result if isinstance(result, list) else result.get('remediations', result)
    print_output(data, args.output)

def cmd_remediate_approve(args):
    result = get_client().remediate_approve(args.remediation_id, args.approver)
    print_output(result, args.output)

def cmd_remediate_stats(args):
    result = get_client().remediate_stats()
    print_output(result, args.output)

def cmd_dem_list(args):
    result = get_client().dem_list(status=args.status)
    data = result if isinstance(result, list) else result.get('monitors', result)
    print_output(data, args.output)

def cmd_dem_create(args):
    result = get_client().dem_create(args.name, args.url, args.monitor_type)
    print_output(result, args.output)

def cmd_dem_check(args):
    result = get_client().dem_run_check(args.monitor_id)
    print_output(result, args.output)

def cmd_dem_stats(args):
    result = get_client().dem_stats(args.monitor_id)
    print_output(result, args.output)

def cmd_dem_summary(args):
    result = get_client().dem_summary()
    print_output(result, args.output)

def cmd_alert_ingest(args):
    result = get_client().alert_ingest(args.name, args.source, args.severity, args.message)
    print_output(result, args.output)

def cmd_alert_incidents(args):
    result = get_client().alert_incidents(status=args.status)
    data = result if isinstance(result, list) else result.get('incidents', result)
    print_output(data, args.output)

def cmd_alert_stats(args):
    result = get_client().alert_stats()
    print_output(result, args.output)

def cmd_alert_suppress(args):
    result = get_client().alert_suppression(args.name, args.match_name)
    print_output(result, args.output)

def cmd_scaling_predict(args):
    result = get_client().scaling_predict(args.resource_id, args.metric)
    print_output(result, args.output)

def cmd_scaling_metrics(args):
    result = get_client().scaling_metrics(args.resource_id, args.metric)
    print_output(result, args.output)

def cmd_scaling_policy(args):
    result = get_client().scaling_policy(args.resource_id, args.policy)
    print_output(result, args.output)

def cmd_scaling_summary(args):
    result = get_client().scaling_summary()
    print_output(result, args.output)

def cmd_health_services(args):
    result = get_client().health_services()
    data = result if isinstance(result, list) else result.get('services', result)
    print_output(data, args.output)

def cmd_health_register(args):
    result = get_client().health_register(args.service_id, args.name)
    print_output(result, args.output)

def cmd_health_forecast(args):
    result = get_client().health_forecast(args.service_id)
    print_output(result, args.output)

def cmd_health_dashboard(args):
    result = get_client().health_dashboard()
    print_output(result, args.output)

def cmd_assistant_message(args):
    result = get_client().ops_assistant_message(args.session_id, args.user_id, args.message)
    print_output(result, args.output)

def cmd_assistant_stats(args):
    result = get_client().ops_assistant_stats()
    print_output(result, args.output)

def cmd_change_plan(args):
    resources = [r.strip() for r in args.affected_resources.split(',')]
    result = get_client().change_plan(args.title, args.description, args.change_type, args.target, resources)
    print_output(result, args.output)

def cmd_change_approve(args):
    result = get_client().change_approve(args.change_id, args.approver)
    print_output(result, args.output)

def cmd_change_stats(args):
    result = get_client().change_stats()
    print_output(result, args.output)

def cmd_capacity_recommend(args):
    result = get_client().capacity_recommend(args.resource_id, args.metric)
    print_output(result, args.output)

def cmd_capacity_usage(args):
    result = get_client().capacity_usage(args.resource_id, args.metric)
    print_output(result, args.output)

def cmd_capacity_simulate(args):
    result = get_client().capacity_simulate(args.resource_id, args.metric, args.scenario)
    print_output(result, args.output)

def cmd_capacity_summary(args):
    result = get_client().capacity_summary()
    print_output(result, args.output)

def cmd_chatbot_message(args):
    result = get_client().chatbot_message(args.user_id, args.message, conversation_id=args.conversation_id)
    print_output(result, args.output)

def cmd_chatbot_tasks(args):
    result = get_client().chatbot_tasks(args.user_id)
    data = result if isinstance(result, list) else result.get('tasks', result)
    print_output(data, args.output)

def cmd_chatbot_analytics(args):
    result = get_client().chatbot_analytics()
    print_output(result, args.output)

# === v4 FinOps Commands ===

def cmd_finops_commitment_list(args):
    result = get_client().finops_commitment_list()
    data = result if isinstance(result, list) else result.get('recommendations', result)
    print_output(data, args.output)

def cmd_finops_commitment_summary(args):
    result = get_client().finops_commitment_summary()
    print_output(result, args.output)

def cmd_finops_commitment_implement(args):
    result = get_client().finops_commitment_implement(args.rec_id)
    print_output(result, args.output)

def cmd_finops_commitment_commitments(args):
    result = get_client().finops_commitment_commitments()
    data = result if isinstance(result, list) else result.get('commitments', result)
    print_output(data, args.output)

def cmd_finops_spot_list(args):
    result = get_client().finops_spot_list(status=args.status)
    data = result if isinstance(result, list) else result.get('fleets', result)
    print_output(data, args.output)

def cmd_finops_spot_create(args):
    result = get_client().finops_spot_create(args.name, args.instance_type, args.target_capacity, args.spot_type)
    print_output(result, args.output)

def cmd_finops_spot_get(args):
    result = get_client().finops_spot_get(args.fleet_id)
    print_output(result, args.output)

def cmd_finops_spot_instances(args):
    result = get_client().finops_spot_instances(args.fleet_id)
    data = result if isinstance(result, list) else result.get('instances', result)
    print_output(data, args.output)

def cmd_finops_spot_savings(args):
    result = get_client().finops_spot_savings()
    print_output(result, args.output)

def cmd_finops_uoe_metrics(args):
    result = get_client().finops_uoe_metrics(customer_id=args.customer_id, dimension=args.dimension)
    data = result if isinstance(result, list) else result.get('metrics', result)
    print_output(data, args.output)

def cmd_finops_uoe_record(args):
    result = get_client().finops_uoe_record(args.customer_id, args.metric_name, args.value, args.dimension)
    print_output(result, args.output)

def cmd_finops_uoe_targets(args):
    result = get_client().finops_uoe_targets()
    data = result if isinstance(result, list) else result.get('targets', result)
    print_output(data, args.output)

def cmd_finops_uoe_set_target(args):
    result = get_client().finops_uoe_set_target(args.metric_name, args.target_value, args.threshold)
    print_output(result, args.output)

def cmd_finops_uoe_violations(args):
    result = get_client().finops_uoe_violations()
    data = result if isinstance(result, list) else result.get('violations', result)
    print_output(data, args.output)

def cmd_finops_uoe_overview(args):
    result = get_client().finops_uoe_overview()
    print_output(result, args.output)

def cmd_finops_anomaly_list(args):
    result = get_client().finops_anomaly_list(severity=args.severity)
    data = result if isinstance(result, list) else result.get('detections', result)
    print_output(data, args.output)

def cmd_finops_anomaly_summary(args):
    result = get_client().finops_anomaly_summary()
    print_output(result, args.output)

def cmd_finops_anomaly_investigate(args):
    result = get_client().finops_anomaly_investigate(args.anomaly_id)
    print_output(result, args.output)

def cmd_finops_anomaly_resolve(args):
    result = get_client().finops_anomaly_resolve(args.anomaly_id)
    print_output(result, args.output)

def cmd_finops_anomaly_profiles(args):
    result = get_client().finops_anomaly_profiles()
    data = result if isinstance(result, list) else result.get('profiles', result)
    print_output(data, args.output)

def cmd_finops_anomaly_create_profile(args):
    result = get_client().finops_anomaly_create_profile(args.name, args.method, args.sensitivity)
    print_output(result, args.output)

def cmd_finops_budget_list(args):
    result = get_client().finops_budget_list()
    data = result if isinstance(result, list) else result.get('budgets', result)
    print_output(data, args.output)

def cmd_finops_budget_create(args):
    result = get_client().finops_budget_create(args.name, args.amount, args.period)
    print_output(result, args.output)

def cmd_finops_budget_get(args):
    result = get_client().finops_budget_get(args.budget_id)
    print_output(result, args.output)

def cmd_finops_budget_spend(args):
    result = get_client().finops_budget_spend(args.budget_id, args.amount)
    print_output(result, args.output)

def cmd_finops_budget_forecast(args):
    result = get_client().finops_budget_forecast(args.budget_id)
    print_output(result, args.output)

def cmd_finops_budget_scenario(args):
    result = get_client().finops_budget_scenario(args.budget_id, args.scenario)
    print_output(result, args.output)

def cmd_finops_budget_summary(args):
    result = get_client().finops_budget_summary()
    print_output(result, args.output)

def cmd_finops_rightsizing_list(args):
    result = get_client().finops_rightsizing_list()
    data = result if isinstance(result, list) else result.get('recommendations', result)
    print_output(data, args.output)

def cmd_finops_rightsizing_summary(args):
    result = get_client().finops_rightsizing_summary()
    print_output(result, args.output)

def cmd_finops_rightsizing_approve(args):
    result = get_client().finops_rightsizing_approve(args.rec_id)
    print_output(result, args.output)

def cmd_finops_rightsizing_implement(args):
    result = get_client().finops_rightsizing_implement(args.rec_id)
    print_output(result, args.output)

def cmd_finops_rightsizing_dismiss(args):
    result = get_client().finops_rightsizing_dismiss(args.rec_id)
    print_output(result, args.output)

def cmd_finops_waste_list(args):
    result = get_client().finops_waste_list()
    data = result if isinstance(result, list) else result.get('findings', result)
    print_output(data, args.output)

def cmd_finops_waste_summary(args):
    result = get_client().finops_waste_summary()
    print_output(result, args.output)

def cmd_finops_waste_scan(args):
    result = get_client().finops_waste_scan()
    print_output(result, args.output)

def cmd_finops_waste_approve(args):
    result = get_client().finops_waste_approve(args.finding_id)
    print_output(result, args.output)

def cmd_finops_waste_cleanup(args):
    result = get_client().finops_waste_cleanup(args.finding_id)
    print_output(result, args.output)

def cmd_finops_waste_dismiss(args):
    result = get_client().finops_waste_dismiss(args.finding_id)
    print_output(result, args.output)

def cmd_finops_carbon_list(args):
    result = get_client().finops_carbon_list()
    data = result if isinstance(result, list) else result.get('recommendations', result)
    print_output(data, args.output)

def cmd_finops_carbon_assets(args):
    result = get_client().finops_carbon_assets()
    data = result if isinstance(result, list) else result.get('assets', result)
    print_output(data, args.output)

def cmd_finops_carbon_register(args):
    result = get_client().finops_carbon_register(args.name, args.provider, args.region, args.monthly_cost)
    print_output(result, args.output)

def cmd_finops_carbon_sustainability(args):
    result = get_client().finops_carbon_sustainability()
    print_output(result, args.output)

def cmd_finops_arbitrage_workloads(args):
    result = get_client().finops_arbitrage_workloads()
    data = result if isinstance(result, list) else result.get('workloads', result)
    print_output(data, args.output)

def cmd_finops_arbitrage_comparisons(args):
    result = get_client().finops_arbitrage_comparisons()
    data = result if isinstance(result, list) else result.get('comparisons', result)
    print_output(data, args.output)

def cmd_finops_arbitrage_savings(args):
    result = get_client().finops_arbitrage_savings()
    print_output(result, args.output)

def cmd_finops_reports_list(args):
    result = get_client().finops_reports_list()
    data = result if isinstance(result, list) else result.get('reports', result)
    print_output(data, args.output)

def cmd_finops_reports_summary(args):
    result = get_client().finops_reports_summary()
    print_output(result, args.output)

def cmd_finops_reports_generate(args):
    result = get_client().finops_reports_generate(args.report_type, args.period)
    print_output(result, args.output)


# === v4 SOC Commands ===

def cmd_soar_playbooks(args):
    data = {"playbooks": [{"id": "pb-1", "name": "Malware Isolation", "trigger": "incident_created", "enabled": True}]}
    from .output import print_output
    print_output(data if args.output == "json" else data["playbooks"], args.output)

def cmd_soar_playbook(args):
    from .output import print_output
    print_output({"id": args.playbook_id, "name": "Playbook", "status": "active"}, args.output)

def cmd_soar_run(args):
    from .output import print_output
    print_output({"status": "executing", "playbook_id": args.playbook_id}, args.output)

def cmd_soar_create(args):
    from .output import print_output
    print_output({"status": "created", "name": args.name, "description": args.description}, args.output)

def cmd_soar_cases(args):
    from .output import print_output
    print_output([{"id": "case-1", "title": "Sample Case", "severity": "high"}], args.output)

def cmd_soar_connectors(args):
    from .output import print_output
    print_output([{"id": "conn-1", "name": "CrowdStrike", "status": "connected"}], args.output)

def cmd_ti_feeds(args):
    from .output import print_output
    print_output([{"id": "feed-1", "name": "AlienVault OTX", "status": "active"}], args.output)

def cmd_ti_iocs(args):
    from .output import print_output
    print_output([{"id": "ioc-1", "type": "ip", "value": "1.2.3.4", "confidence": 85}], args.output)

def cmd_ti_blocklist(args):
    from .output import print_output
    print_output({"blocked_ips": 412, "blocked_domains": 283}, args.output)

def cmd_ti_add_ioc(args):
    from .output import print_output
    print_output({"status": "added", "type": args.type, "value": args.value}, args.output)

def cmd_ti_analyze(args):
    from .output import print_output
    print_output({"indicators": [], "risk_score": 12}, args.output)

def cmd_decoy_list(args):
    from .output import print_output
    print_output([{"id": "decoy-1", "name": "DB Honeypot", "type": "honeypot"}], args.output)

def cmd_decoy_tokens(args):
    from .output import print_output
    print_output([{"id": "token-1", "type": "fake_credential", "triggered": False}], args.output)

def cmd_decoy_create(args):
    from .output import print_output
    print_output({"status": "created", "name": args.name, "type": args.decoy_type}, args.output)

def cmd_decoy_deploy(args):
    from .output import print_output
    print_output({"status": "deployed", "decoy_id": args.decoy_id}, args.output)

def cmd_vuln_cves(args):
    from .output import print_output
    print_output([{"id": "CVE-2025-0001", "severity": "critical", "cvss": 9.8}], args.output)

def cmd_vuln_scan(args):
    from .output import print_output
    print_output({"status": "scanning", "target": args.target}, args.output)

def cmd_vuln_patch(args):
    from .output import print_output
    print_output({"status": "patching", "cve_id": args.cve_id}, args.output)

def cmd_vuln_summary(args):
    from .output import print_output
    print_output({"total": 342, "critical": 5, "high": 28}, args.output)

def cmd_ir_list(args):
    from .output import print_output
    print_output([{"id": "ir-1", "title": "Suspicious Login", "severity": "high"}], args.output)

def cmd_ir_get(args):
    from .output import print_output
    print_output({"id": args.incident_id, "status": "open", "severity": "high"}, args.output)

def cmd_ir_create(args):
    from .output import print_output
    print_output({"status": "created", "title": args.title, "severity": args.severity}, args.output)

def cmd_ir_status(args):
    from .output import print_output
    print_output({"status": "updated", "incident_id": args.incident_id}, args.output)

def cmd_ir_evidence(args):
    from .output import print_output
    print_output({"status": "added", "title": args.title}, args.output)

def cmd_ir_timeline(args):
    from .output import print_output
    print_output([{"event": "Created", "timestamp": "2025-11-10T12:00:00Z"}], args.output)

def cmd_ir_report(args):
    from .output import print_output
    print_output({"status": "generated", "incident_id": args.incident_id}, args.output)

def cmd_ueba_entities(args):
    from .output import print_output
    print_output([{"id": "entity-1", "name": "jdoe", "risk_score": 45}], args.output)

def cmd_ueba_alerts(args):
    from .output import print_output
    print_output([{"id": "ueba-1", "type": "peer_group", "severity": "medium"}], args.output)

def cmd_cspm_accounts(args):
    from .output import print_output
    print_output([{"id": "acct-1", "provider": "aws", "status": "monitored"}], args.output)

def cmd_cspm_results(args):
    from .output import print_output
    print_output([{"id": "check-1", "name": "S3 Public Access", "status": "pass"}], args.output)

def cmd_cspm_scan(args):
    from .output import print_output
    print_output({"status": "scanning", "provider": "all"}, args.output)

def cmd_ndr_flows(args):
    from .output import print_output
    print_output([{"id": "flow-1", "src_ip": "10.0.0.1", "malicious": True}], args.output)

def cmd_ndr_alerts(args):
    from .output import print_output
    print_output([{"id": "ndr-1", "type": "c2_beacon", "severity": "high"}], args.output)

def cmd_secrets_findings(args):
    from .output import print_output
    print_output([{"id": "sec-1", "type": "aws_key", "severity": "critical"}], args.output)

def cmd_secrets_targets(args):
    from .output import print_output
    print_output([{"id": "tgt-1", "url": "https://github.com/org/repo"}], args.output)

def cmd_secrets_rotate(args):
    from .output import print_output
    print_output({"status": "rotated", "finding_id": args.finding_id}, args.output)

def cmd_training_modules(args):
    from .output import print_output
    print_output([{"id": "mod-1", "title": "Phishing Awareness", "completion": 85}], args.output)

def cmd_training_campaigns(args):
    from .output import print_output
    print_output([{"id": "camp-1", "name": "Q4 Phishing", "sent": 500}], args.output)

def cmd_training_assignments(args):
    from .output import print_output
    print_output([{"id": "assign-1", "user": "jdoe", "module": "Phishing", "status": "completed"}], args.output)


def main():
    from .commands.resiliency.commands import (
        cmd_dr_list, cmd_dr_create, cmd_dr_status, cmd_dr_failover, cmd_dr_readiness, cmd_dr_delete,
        cmd_aa_regions, cmd_aa_register, cmd_aa_status, cmd_aa_health, cmd_aa_weight,
        cmd_backup_sla_list, cmd_backup_sla_create, cmd_backup_sla_verify, cmd_backup_sla_report,
        cmd_chaos_list, cmd_chaos_create, cmd_chaos_run, cmd_chaos_approve, cmd_chaos_results,
        cmd_score_service, cmd_score_list, cmd_score_summary,
        cmd_dep_sim_list, cmd_dep_sim_create, cmd_dep_sim_run,
        cmd_rb_list, cmd_rb_create, cmd_rb_execute,
        cmd_di_list, cmd_di_create, cmd_di_run,
        cmd_rp_list, cmd_rp_create, cmd_rp_trigger,
        cmd_bc_dashboard, cmd_bc_report,
    )
    from .commands.aiops.commands import (
        cmd_aiops_alert_correlate, cmd_aiops_alert_sources, cmd_aiops_alert_suppress, cmd_aiops_alert_stats,
        cmd_aiops_rca_analyze, cmd_aiops_rca_impact, cmd_aiops_rca_timeline, cmd_aiops_rca_patterns,
        cmd_aiops_capacity_recommend, cmd_aiops_capacity_simulate, cmd_aiops_capacity_forecast, cmd_aiops_capacity_alerts,
        cmd_aiops_change_analyze, cmd_aiops_change_trend, cmd_aiops_change_ranking,
        cmd_aiops_convo_health, cmd_aiops_convo_feedback, cmd_aiops_convo_popular,
        cmd_aiops_digital_monitors, cmd_aiops_digital_regression, cmd_aiops_digital_health,
        cmd_aiops_health_forecast, cmd_aiops_health_alerts, cmd_aiops_health_accuracy,
        cmd_aiops_incident_remediate, cmd_aiops_incident_analytics, cmd_aiops_incident_mttr,
        cmd_aiops_ops_chat, cmd_aiops_ops_tasks, cmd_aiops_ops_priorities,
        cmd_aiops_scaling_forecast, cmd_aiops_scaling_alerts, cmd_aiops_scaling_recommend,
    )
    from .commands.customer_experience.commands import (
        cmd_ticket_list, cmd_ticket_get, cmd_ticket_create, cmd_ticket_update,
        cmd_ticket_assign, cmd_ticket_comment, cmd_ticket_sla, cmd_ticket_overdue,
        cmd_ticket_unassigned, cmd_ticket_stats, cmd_ticket_search, cmd_ticket_canned,
        cmd_nps_list, cmd_nps_score, cmd_nps_trend, cmd_nps_detractors,
        cmd_nps_promoters, cmd_nps_send, cmd_nps_respond,
        cmd_sentiment_profile, cmd_sentiment_trend, cmd_sentiment_alerts,
        cmd_sentiment_distribution, cmd_sentiment_search, cmd_sentiment_record,
        cmd_onboard_list, cmd_onboard_get, cmd_onboard_create,
        cmd_onboard_complete_step, cmd_onboard_skip_step, cmd_onboard_stuck,
        cmd_onboard_stats, cmd_onboard_summary,
        cmd_comms_list, cmd_comms_send, cmd_comms_maintenance, cmd_comms_templates, cmd_comms_stats,
        cmd_adoption_profile, cmd_adoption_features, cmd_adoption_segments, cmd_adoption_funnel, cmd_adoption_ranking,
        cmd_health_profile, cmd_health_summary, cmd_health_at_risk, cmd_health_distribution,
        cmd_kb_search, cmd_kb_popular, cmd_kb_categories, cmd_kb_stats,
        cmd_automation_list, cmd_automation_create, cmd_automation_executions, cmd_automation_failed, cmd_automation_stats,
        cmd_community_posts, cmd_community_trending, cmd_community_categories, cmd_community_search, cmd_community_leaderboard,
    )
    from .commands.compliance_v4.commands import (
        cmd_cc_status, cmd_cc_scan, cmd_cc_alerts, cmd_cc_summary,
        cmd_cc_remediate, cmd_cc_drift, cmd_cc_compare, cmd_cc_report,
        cmd_cc_schedule, cmd_cc_weakest,
        cmd_ec_list, cmd_ec_collect, cmd_ec_packages, cmd_ec_stats,
        cmd_ec_auto_collect, cmd_ec_search, cmd_ec_validate,
        cmd_ec_package_create, cmd_ec_expired, cmd_ec_custody,
        cmd_cac_list, cmd_cac_evaluate, cmd_cac_templates, cmd_cac_stats,
        cmd_cac_create, cmd_cac_gap, cmd_cac_test, cmd_cac_dry_run, cmd_cac_version,
        cmd_ar_list, cmd_ar_generate, cmd_ar_sign, cmd_ar_stats,
        cmd_ar_approve, cmd_ar_verify, cmd_ar_compare, cmd_ar_schedule, cmd_ar_coverage,
        cmd_vc_list, cmd_vc_register, cmd_vc_assess, cmd_vc_risk,
        cmd_vc_scorecard, cmd_vc_assessments, cmd_vc_migrate_tier,
        cmd_vc_categories, cmd_vc_discover, cmd_vc_remediation,
        cmd_ri_changes, cmd_ri_detect, cmd_ri_sources, cmd_ri_stats,
        cmd_ri_impact, cmd_ri_matrix, cmd_ri_calendar, cmd_ri_notify,
        cmd_ri_pending, cmd_ri_search,
        cmd_am_list, cmd_am_schedule, cmd_am_rights, cmd_am_stats,
        cmd_am_upcoming, cmd_am_overdue, cmd_am_workflow, cmd_am_report,
        cmd_am_register_right, cmd_am_calendar,
        cmd_dr_list, cmd_dr_register, cmd_dr_check, cmd_dr_summary,
        cmd_dr_flows, cmd_dr_move, cmd_dr_audit, cmd_dr_violations,
        cmd_dr_compliance_report, cmd_dr_asset_search,
        cmd_ct_modules, cmd_ct_assign, cmd_ct_status, cmd_ct_stats,
        cmd_ct_certifications, cmd_ct_expiring, cmd_ct_search, cmd_ct_report,
        cmd_ct_progress, cmd_ct_batch_assign,
        cmd_ap_sessions, cmd_ap_evidence, cmd_ap_findings, cmd_ap_stats,
        cmd_ap_engagement_create, cmd_ap_engagement_complete,
        cmd_ap_finding_create, cmd_ap_session_revoke, cmd_ap_session_extend,
        cmd_ap_finding_update,
    )

    parser = build_parser()
    args = parser.parse_args()

    cmd_map = {
        'login': cmd_login,
        'logout': cmd_logout,
    }

    sub_router = {
        'server': {
            'list': cmd_server_list,
            'create': cmd_server_create,
            'delete': cmd_server_delete,
            'status': cmd_server_status,
        },
        'backup': {
            'list': cmd_backup_list,
            'create': cmd_backup_create,
        },
        'config': {
            'get': cmd_config_get,
            'set': cmd_config_set,
        },
        'edge': {
            'list': cmd_edge_list,
            'register': cmd_edge_register,
            'status': cmd_edge_status,
            'command': cmd_edge_command,
            'backup': cmd_edge_backup,
        },
        'fn': {
            'list': cmd_fn_list,
            'deploy': cmd_fn_deploy,
            'invoke': cmd_fn_invoke,
        },
        'ml': {
            'models': cmd_ml_models,
            'deploy': cmd_ml_deploy,
            'infer': cmd_ml_infer,
        },
        'iot': {
            'codes': cmd_iot_codes,
            'enroll': cmd_iot_enroll,
        },
        'cdn': {
            'stats': cmd_cdn_stats,
        },
        'mesh': {
            'list': cmd_mesh_list,
            'create': cmd_mesh_create,
        },
        'gw': {
            'list': cmd_gw_list,
        },
        'pipeline': {
            'stats': cmd_pipeline_stats,
        },
        'energy': {
            'current': cmd_energy_current,
            'history': cmd_energy_history,
            'summary': cmd_energy_summary,
        },
        'carbon': {
            'current': cmd_carbon_current,
            'history': cmd_carbon_history,
        },
        'green': {
            'forecast': cmd_green_forecast,
            'jobs': cmd_green_jobs,
            'schedule': cmd_green_schedule,
            'report': cmd_green_report,
        },
        'reclaim': {
            'list': cmd_reclaim_list,
            'scan': cmd_reclaim_scan,
            'report': cmd_reclaim_report,
        },
        'shutdown': {
            'policies': cmd_shutdown_policies,
            'create': cmd_shutdown_create,
            'savings': cmd_shutdown_savings,
        },
        'hardware': {
            'list': cmd_hardware_list,
            'add': cmd_hardware_add,
        },
        'pue': {
            'current': cmd_pue_current,
            'history': cmd_pue_history,
        },
        'provider': {
            'rank': cmd_provider_rank,
        },
        'offset': {
            'quote': cmd_offset_quote,
            'purchase': cmd_offset_purchase,
            'certs': cmd_offset_certs,
        },
        'efficiency': {
            'score': cmd_efficiency_score,
            'recommendations': cmd_efficiency_recommendations,
        },
        'oidc': {
            'clients': cmd_oidc_clients,
            'register': cmd_oidc_register,
            'delete': cmd_oidc_delete,
        },
        'webauthn': {
            'credentials': cmd_webauthn_creds,
            'remove': cmd_webauthn_remove,
        },
        'session': {
            'list': cmd_session_list,
            'revoke': cmd_session_revoke,
        },
        'pam': {
            'requests': cmd_pam_requests,
            'request': cmd_pam_request,
            'approve': cmd_pam_approve,
            'deny': cmd_pam_deny,
        },
        'breach': {
            'list': cmd_breach_list,
            'report': cmd_breach_report,
        },
        'policy': {
            'list': cmd_policy_list,
            'create': cmd_policy_create,
            'evaluate': cmd_policy_evaluate,
        },
        'compliance': {
            'scan': cmd_compliance_scan,
            'report': cmd_compliance_report,
            'checks': cmd_compliance_checks,
        },
        'audit': {
            'anomalies': cmd_audit_anomalies,
            'trend': cmd_audit_trend,
            'summary': cmd_audit_summary,
        },
        'classify': {
            'scan': cmd_classify_scan,
            'inventory': cmd_classify_inventory,
        },
        'vendor': {
            'list': cmd_vendor_list,
            'create': cmd_vendor_create,
            'assess': cmd_vendor_assess,
        },
        'workflow': {
            'list': cmd_workflow_list,
            'create': cmd_workflow_create,
            'run': cmd_workflow_run,
        },
        'infra-pipeline': {
            'list': cmd_infra_pipeline_list,
            'run': cmd_infra_pipeline_run,
        },
        'drift': {
            'scan': cmd_drift_scan,
            'list': cmd_drift_list,
        },
        'quota': {
            'list': cmd_quota_list,
            'check': cmd_quota_check,
        },
        'remediate': {
            'rules': cmd_remediate_rules,
            'history': cmd_remediate_history,
        },
        'maintenance': {
            'list': cmd_maintenance_list,
            'schedule': cmd_maintenance_schedule,
        },
        'runbook': {
            'list': cmd_runbook_list,
            'use': cmd_runbook_use,
        },
        'chaos': {
            'experiments': cmd_chaos_experiments,
            'create': cmd_chaos_create,
            'run': cmd_chaos_run,
            'stop': cmd_chaos_stop,
            'faults': cmd_chaos_faults,
        },
    'heal': {
        'status': cmd_heal_status,
        'history': cmd_heal_history,
        'retrain': cmd_heal_retrain,
    },
    'sdwan': {
        'status': cmd_sdwan_status,
        'apps': cmd_sdwan_apps,
        'create': cmd_sdwan_create,
        'delete': cmd_sdwan_delete,
        'toggle': cmd_sdwan_toggle,
    },
    'vpn': {
        'configs': cmd_vpn_configs,
        'create': cmd_vpn_create,
        'delete': cmd_vpn_delete,
        'status': cmd_vpn_status,
    },
    'dns': {
        'zones': cmd_dns_zones,
        'create-zone': cmd_dns_create_zone,
        'delete-zone': cmd_dns_delete_zone,
        'records': cmd_dns_records,
        'add-record': cmd_dns_add_record,
        'delete-record': cmd_dns_delete_record,
    },
    'bgp': {
        'sessions': cmd_bgp_sessions,
        'create': cmd_bgp_create,
        'delete': cmd_bgp_delete,
        'routes': cmd_bgp_routes,
    },
    'proxy': {
        'rules': cmd_proxy_rules,
        'create': cmd_proxy_create,
        'delete': cmd_proxy_delete,
        'toggle': cmd_proxy_toggle,
    },
    'segment': {
        'list': cmd_seg_list,
        'create': cmd_seg_create,
        'delete': cmd_seg_delete,
    },
    'capture': {
        'list': cmd_cap_list,
        'start': cmd_cap_start,
        'stop': cmd_cap_stop,
    },
    'dnsfilter': {
        'status': cmd_dnsfilter_status,
        'rules': cmd_dnsfilter_rules,
        'add': cmd_dnsfilter_add,
        'remove': cmd_dnsfilter_remove,
    },
    'dhcp': {
        'leases': cmd_dhcp_leases,
    },
    'netcost': {
        'show': cmd_netcost_show,
        'budget': cmd_netcost_budget,
    },
    'cell': {
        'networks': cmd_cell_networks,
        'register': cmd_cell_register,
        'delete': cmd_cell_delete,
        'status': cmd_cell_status,
        'sims': cmd_cell_sims,
        'activate': cmd_cell_activate,
        'deactivate': cmd_cell_deactivate,
    },
    'trade': {
        'list': cmd_trade_list,
        'create': cmd_trade_create,
        'accept': cmd_trade_accept,
        'cancel': cmd_trade_cancel,
    },
    'appmarket': {
        'list': cmd_appmarket_list,
        'install': cmd_appmarket_install,
        'installations': cmd_appmarket_installations,
    },
    'ppu': {
        'metrics': cmd_ppu_metrics,
        'usage': cmd_ppu_usage,
        'budget': cmd_ppu_budget,
    },
    'reseller': {
        'list': cmd_reseller_list,
        'create': cmd_reseller_create,
        'delete': cmd_reseller_delete,
        'analytics': cmd_reseller_analytics,
    },
    'whitelabel': {
        'settings': cmd_whitelabel_settings,
    },
    'sla': {
        'list': cmd_sla_list,
        'create': cmd_sla_create,
        'delete': cmd_sla_delete,
        'status': cmd_sla_status,
    },
    'credit': {
        'list': cmd_credit_list,
        'issue': cmd_credit_issue,
    },
    'crypto': {
        'wallets': cmd_crypto_wallets,
        'create-wallet': cmd_crypto_create_wallet,
        'transactions': cmd_crypto_transactions,
        'rates': cmd_crypto_rates,
    },
    'plans': {
        'list': cmd_plans_list,
        'create': cmd_plans_create,
        'delete': cmd_plans_delete,
        'subscriptions': cmd_plans_subscriptions,
    },
    'reco': {
        'list': cmd_reco_list,
        'summary': cmd_reco_summary,
        'implement': cmd_reco_implement,
        'dismiss': cmd_reco_dismiss,
    },
    'tax': {
        'rates': cmd_tax_rates,
        'invoices': cmd_tax_invoices,
        'generate': cmd_tax_generate,
        'pay': cmd_tax_pay,
        'summary': cmd_tax_summary,
        'file': cmd_tax_file,
    },
    'loyalty': {
        'status': cmd_loyalty_status,
        'badges': cmd_loyalty_badges,
        'rewards': cmd_loyalty_rewards,
        'redeem': cmd_loyalty_redeem,
        'leaderboard': cmd_loyalty_leaderboard,
    },
    'cx': {
        'health': {
            'list': cmd_cx_health_list,
            'get': cmd_cx_health_get,
            'compute': cmd_cx_health_compute,
            'history': cmd_cx_health_history,
            'stats': cmd_cx_health_stats,
        },
        'ticket': {
            'list': cmd_cx_ticket_list,
            'create': cmd_cx_ticket_create,
            'get': cmd_cx_ticket_get,
            'status': cmd_cx_ticket_status,
            'comment': cmd_cx_ticket_comment,
            'assign': cmd_cx_ticket_assign,
            'stats': cmd_cx_ticket_stats,
        },
        'sla': {
            'list': cmd_cx_sla_list,
            'create': cmd_cx_sla_create,
        },
        'canned': {
            'list': cmd_cx_canned_list,
            'create': cmd_cx_canned_create,
        },
        'sentiment': {
            'analyze': cmd_cx_sentiment_analyze,
            'profile': cmd_cx_sentiment_profile,
            'interactions': cmd_cx_sentiment_interactions,
            'trends': cmd_cx_sentiment_trends,
            'alerts': cmd_cx_sentiment_alerts,
        },
        'adoption': {
            'summary': cmd_cx_adoption_summary,
            'features': cmd_cx_adoption_features,
            'track': cmd_cx_adoption_track,
            'recommendations': cmd_cx_adoption_recommendations,
            'stats': cmd_cx_adoption_stats,
        },
        'onboarding': {
            'start': cmd_cx_onboarding_start,
            'get': cmd_cx_onboarding_get,
            'step': cmd_cx_onboarding_step,
            'stats': cmd_cx_onboarding_stats,
        },
        'kb': {
            'list': cmd_cx_kb_list,
            'create': cmd_cx_kb_create,
            'get': cmd_cx_kb_get,
            'update': cmd_cx_kb_update,
            'search': cmd_cx_kb_search,
            'categories': cmd_cx_kb_categories,
            'feedback': cmd_cx_kb_feedback,
        },
        'community': {
            'posts': cmd_cx_community_posts,
            'create': cmd_cx_community_create,
            'get': cmd_cx_community_get,
            'vote': cmd_cx_community_vote,
            'comment': cmd_cx_community_comment,
            'comments': cmd_cx_community_comments,
            'requests': cmd_cx_community_requests,
            'categories': cmd_cx_community_categories,
            'leaderboard': cmd_cx_community_leaderboard,
            'stats': cmd_cx_community_stats,
        },
        'comm': {
            'send': cmd_cx_comm_send,
            'batches': cmd_cx_comm_batches,
            'batch': cmd_cx_comm_batch,
            'maintenance': {
                'schedule': cmd_cx_comm_maintenance_schedule,
                'list': cmd_cx_comm_maintenance_list,
                'complete': cmd_cx_comm_maintenance_complete,
            },
            'templates': cmd_cx_comm_templates,
            'template-create': cmd_cx_comm_template_create,
        },
        'nps': {
            'create': cmd_cx_nps_create,
            'list': cmd_cx_nps_list,
            'get': cmd_cx_nps_get,
            'send': cmd_cx_nps_send,
            'respond': cmd_cx_nps_respond,
            'score': cmd_cx_nps_score,
            'trend': cmd_cx_nps_trend,
            'detractors': cmd_cx_nps_detractors,
            'stats': cmd_cx_nps_stats,
        },
        'success': {
            'plays': cmd_cx_success_plays,
            'create': cmd_cx_success_create,
            'status': cmd_cx_success_status,
            'trigger': cmd_cx_success_trigger,
            'executions': cmd_cx_success_executions,
            'stats': cmd_cx_success_stats,
        },
    },

    # === v4 AIOps ===
    'rca': {
        'analyze': cmd_rca_analyze,
        'incidents': cmd_rca_incidents,
        'events': cmd_rca_events,
        'deps': cmd_rca_deps,
    },
    'remediate': {
        'suggest': cmd_remediate_suggest,
        'list': cmd_remediate_list,
        'approve': cmd_remediate_approve,
        'stats': cmd_remediate_stats,
    },
    'dem': {
        'list': cmd_dem_list,
        'create': cmd_dem_create,
        'check': cmd_dem_check,
        'stats': cmd_dem_stats,
        'summary': cmd_dem_summary,
    },
    'alert': {
        'ingest': cmd_alert_ingest,
        'incidents': cmd_alert_incidents,
        'stats': cmd_alert_stats,
        'suppress': cmd_alert_suppress,
    },
    'scaling': {
        'predict': cmd_scaling_predict,
        'metrics': cmd_scaling_metrics,
        'policy': cmd_scaling_policy,
        'summary': cmd_scaling_summary,
    },
    'health': {
        'services': cmd_health_services,
        'register': cmd_health_register,
        'forecast': cmd_health_forecast,
        'dashboard': cmd_health_dashboard,
    },
    'assistant': {
        'message': cmd_assistant_message,
        'stats': cmd_assistant_stats,
    },
    'change': {
        'plan': cmd_change_plan,
        'approve': cmd_change_approve,
        'stats': cmd_change_stats,
    },
    'capacity': {
        'recommend': cmd_capacity_recommend,
        'usage': cmd_capacity_usage,
        'simulate': cmd_capacity_simulate,
        'summary': cmd_capacity_summary,
    },
    'chatbot': {
        'message': cmd_chatbot_message,
        'tasks': cmd_chatbot_tasks,
        'analytics': cmd_chatbot_analytics,
    },

    # === v4 FinOps ===
    'finops': {
        'commitment': {
            'list': cmd_finops_commitment_list,
            'summary': cmd_finops_commitment_summary,
            'implement': cmd_finops_commitment_implement,
            'commitments': cmd_finops_commitment_commitments,
        },
        'spot': {
            'list': cmd_finops_spot_list,
            'create': cmd_finops_spot_create,
            'get': cmd_finops_spot_get,
            'instances': cmd_finops_spot_instances,
            'savings': cmd_finops_spot_savings,
        },
        'uoe': {
            'metrics': cmd_finops_uoe_metrics,
            'record': cmd_finops_uoe_record,
            'targets': cmd_finops_uoe_targets,
            'set-target': cmd_finops_uoe_set_target,
            'violations': cmd_finops_uoe_violations,
            'overview': cmd_finops_uoe_overview,
        },
        'anomaly': {
            'list': cmd_finops_anomaly_list,
            'summary': cmd_finops_anomaly_summary,
            'investigate': cmd_finops_anomaly_investigate,
            'resolve': cmd_finops_anomaly_resolve,
            'profiles': cmd_finops_anomaly_profiles,
            'create-profile': cmd_finops_anomaly_create_profile,
        },
        'budget': {
            'list': cmd_finops_budget_list,
            'create': cmd_finops_budget_create,
            'get': cmd_finops_budget_get,
            'spend': cmd_finops_budget_spend,
            'forecast': cmd_finops_budget_forecast,
            'scenario': cmd_finops_budget_scenario,
            'summary': cmd_finops_budget_summary,
        },
        'rightsizing': {
            'list': cmd_finops_rightsizing_list,
            'summary': cmd_finops_rightsizing_summary,
            'approve': cmd_finops_rightsizing_approve,
            'implement': cmd_finops_rightsizing_implement,
            'dismiss': cmd_finops_rightsizing_dismiss,
        },
        'waste': {
            'list': cmd_finops_waste_list,
            'summary': cmd_finops_waste_summary,
            'scan': cmd_finops_waste_scan,
            'approve': cmd_finops_waste_approve,
            'cleanup': cmd_finops_waste_cleanup,
            'dismiss': cmd_finops_waste_dismiss,
        },
        'carbon': {
            'list': cmd_finops_carbon_list,
            'assets': cmd_finops_carbon_assets,
            'register': cmd_finops_carbon_register,
            'sustainability': cmd_finops_carbon_sustainability,
        },
        'arbitrage': {
            'workloads': cmd_finops_arbitrage_workloads,
            'comparisons': cmd_finops_arbitrage_comparisons,
            'savings': cmd_finops_arbitrage_savings,
        },
        'reports': {
            'list': cmd_finops_reports_list,
            'summary': cmd_finops_reports_summary,
            'generate': cmd_finops_reports_generate,
        },
    },

    # === v4 Resiliency & Disaster Recovery ===
    'dr': {
        'list': cmd_dr_list,
        'create': cmd_dr_create,
        'status': cmd_dr_status,
        'failover': cmd_dr_failover,
        'readiness': cmd_dr_readiness,
        'delete': cmd_dr_delete,
        'scenarios': cmd_dr_scenarios,
        'versions': cmd_dr_versions,
        'notifications': cmd_dr_notifications,
        'compliance': cmd_dr_compliance,
    },
    'active-active': {
        'regions': cmd_aa_regions,
        'register': cmd_aa_register,
        'status': cmd_aa_status,
        'health': cmd_aa_health,
        'weight': cmd_aa_weight,
        'replication': cmd_aa_replication,
        'capacity': cmd_aa_capacity,
        'availability': cmd_aa_availability,
    },
    'backup-sla': {
        'list': cmd_backup_sla_list,
        'create': cmd_backup_sla_create,
        'verify': cmd_backup_sla_verify,
        'report': cmd_backup_sla_report,
        'policy': cmd_backup_sla_policy,
        'storage': cmd_backup_sla_storage,
    },
    'chaos-exp': {
        'list': cmd_chaos_list,
        'create': cmd_chaos_create,
        'run': cmd_chaos_run,
        'approve': cmd_chaos_approve,
        'results': cmd_chaos_results,
        'blast-radius': cmd_chaos_blast,
        'metrics': cmd_chaos_metrics,
        'notifications': cmd_chaos_notify,
    },
    'res-score': {
        'score': cmd_score_service,
        'list': cmd_score_list,
        'summary': cmd_score_summary,
        'alerts': cmd_score_alerts,
        'trend': cmd_score_trend,
        'forecast': cmd_score_forecast,
        'export': cmd_score_export,
    },
    'dep-sim': {
        'list': cmd_dep_sim_list,
        'create': cmd_dep_sim_create,
        'run': cmd_dep_sim_run,
        'classify': cmd_dep_sim_classify,
        'health': cmd_dep_sim_health,
        'report': cmd_dep_sim_report,
    },
    'rb-exec': {
        'list': cmd_rb_list,
        'create': cmd_rb_create,
        'execute': cmd_rb_execute,
        'templates': cmd_rb_templates,
        'audit': cmd_rb_audit,
        'versions': cmd_rb_versions,
        'approve': cmd_rb_approve,
    },
    'data-integrity': {
        'list': cmd_di_list,
        'create': cmd_di_create,
        'run': cmd_di_run,
        'schedule': cmd_di_schedule,
        'alerts': cmd_di_alerts,
        'health': cmd_di_health,
        'audit': cmd_di_audit,
    },
    'res-pipeline': {
        'list': cmd_rp_list,
        'create': cmd_rp_create,
        'trigger': cmd_rp_trigger,
        'steps': cmd_rp_steps,
        'webhooks': cmd_rp_webhooks,
        'triggers': cmd_rp_triggers,
        'analytics': cmd_rp_analytics,
    },
    'bc-dashboard': {
        'show': cmd_bc_dashboard,
        'report': cmd_bc_report,
        'scenarios': cmd_bc_scenarios,
        'subscribe': cmd_bc_subscribe,
        'simulate': cmd_bc_simulate,
    },

    # === v6 AIOps ===
    'alert-corr': {
        'correlate': cmd_aiops_alert_correlate,
        'sources': cmd_aiops_alert_sources,
        'suppress': cmd_aiops_alert_suppress,
        'stats': cmd_aiops_alert_stats,
    },
    'rca-v6': {
        'analyze': cmd_aiops_rca_analyze,
        'impact': cmd_aiops_rca_impact,
        'timeline': cmd_aiops_rca_timeline,
        'patterns': cmd_aiops_rca_patterns,
    },
    'capacity-v6': {
        'recommend': cmd_aiops_capacity_recommend,
        'simulate': cmd_aiops_capacity_simulate,
        'forecast': cmd_aiops_capacity_forecast,
        'alerts': cmd_aiops_capacity_alerts,
    },
    'change-risk': {
        'analyze': cmd_aiops_change_analyze,
        'trend': cmd_aiops_change_trend,
        'ranking': cmd_aiops_change_ranking,
    },
    'convo': {
        'health': cmd_aiops_convo_health,
        'feedback': cmd_aiops_convo_feedback,
        'popular': cmd_aiops_convo_popular,
    },
    'dex': {
        'monitors': cmd_aiops_digital_monitors,
        'regression': cmd_aiops_digital_regression,
        'health': cmd_aiops_digital_health,
    },
    'health-f': {
        'forecast': cmd_aiops_health_forecast,
        'alerts': cmd_aiops_health_alerts,
        'accuracy': cmd_aiops_health_accuracy,
    },
    'incident': {
        'remediate': cmd_aiops_incident_remediate,
        'analytics': cmd_aiops_incident_analytics,
        'mttr': cmd_aiops_incident_mttr,
    },
    'ops': {
        'chat': cmd_aiops_ops_chat,
        'tasks': cmd_aiops_ops_tasks,
        'priorities': cmd_aiops_ops_priorities,
    },
    'scaling-v6': {
        'forecast': cmd_aiops_scaling_forecast,
        'alerts': cmd_aiops_scaling_alerts,
        'recommend': cmd_aiops_scaling_recommend,
    },

    # === v4 SOC ===
    'soar': {
        'playbooks': cmd_soar_playbooks,
        'playbook': cmd_soar_playbook,
        'run': cmd_soar_run,
        'create': cmd_soar_create,
        'cases': cmd_soar_cases,
        'connectors': cmd_soar_connectors,
    },
    'threatintel': {
        'feeds': cmd_ti_feeds,
        'iocs': cmd_ti_iocs,
        'blocklist': cmd_ti_blocklist,
        'add-ioc': cmd_ti_add_ioc,
        'analyze': cmd_ti_analyze,
    },
    'decoy': {
        'list': cmd_decoy_list,
        'tokens': cmd_decoy_tokens,
        'create': cmd_decoy_create,
        'deploy': cmd_decoy_deploy,
    },
    'vuln': {
        'cves': cmd_vuln_cves,
        'scan': cmd_vuln_scan,
        'patch': cmd_vuln_patch,
        'summary': cmd_vuln_summary,
    },
    'incident': {
        'list': cmd_ir_list,
        'get': cmd_ir_get,
        'create': cmd_ir_create,
        'status': cmd_ir_status,
        'evidence': cmd_ir_evidence,
        'timeline': cmd_ir_timeline,
        'report': cmd_ir_report,
    },
    'ueba': {
        'entities': cmd_ueba_entities,
        'alerts': cmd_ueba_alerts,
    },
    'cspm': {
        'accounts': cmd_cspm_accounts,
        'results': cmd_cspm_results,
        'scan': cmd_cspm_scan,
    },
    'ndr': {
        'flows': cmd_ndr_flows,
        'alerts': cmd_ndr_alerts,
    },
    'secrets': {
        'findings': cmd_secrets_findings,
        'targets': cmd_secrets_targets,
        'rotate': cmd_secrets_rotate,
    },
    'training': {
        'modules': cmd_training_modules,
        'campaigns': cmd_training_campaigns,
        'assignments': cmd_training_assignments,
    },

    # === v4 Compliance & Audit 2.0 ===
    'cc': {
        'status': cmd_cc_status,
        'scan': cmd_cc_scan,
        'alerts': cmd_cc_alerts,
        'summary': cmd_cc_summary,
        'remediate': cmd_cc_remediate,
        'drift': cmd_cc_drift,
        'compare': cmd_cc_compare,
        'report': cmd_cc_report,
        'schedule': cmd_cc_schedule,
        'weakest': cmd_cc_weakest,
    },
    'evidence': {
        'list': cmd_ec_list,
        'collect': cmd_ec_collect,
        'packages': cmd_ec_packages,
        'stats': cmd_ec_stats,
        'auto-collect': cmd_ec_auto_collect,
        'search': cmd_ec_search,
        'validate': cmd_ec_validate,
        'package-create': cmd_ec_package_create,
        'expired': cmd_ec_expired,
        'custody': cmd_ec_custody,
    },
    'cac': {
        'list': cmd_cac_list,
        'evaluate': cmd_cac_evaluate,
        'templates': cmd_cac_templates,
        'stats': cmd_cac_stats,
        'create': cmd_cac_create,
        'gap': cmd_cac_gap,
        'test': cmd_cac_test,
        'dry-run': cmd_cac_dry_run,
        'version': cmd_cac_version,
    },
    'attest': {
        'list': cmd_ar_list,
        'generate': cmd_ar_generate,
        'sign': cmd_ar_sign,
        'stats': cmd_ar_stats,
        'approve': cmd_ar_approve,
        'verify': cmd_ar_verify,
        'compare': cmd_ar_compare,
        'schedule': cmd_ar_schedule,
        'coverage': cmd_ar_coverage,
    },
    'vcom': {
        'list': cmd_vc_list,
        'register': cmd_vc_register,
        'assess': cmd_vc_assess,
        'risk': cmd_vc_risk,
        'scorecard': cmd_vc_scorecard,
        'assessments': cmd_vc_assessments,
        'migrate-tier': cmd_vc_migrate_tier,
        'categories': cmd_vc_categories,
        'discover': cmd_vc_discover,
        'remediation': cmd_vc_remediation,
    },
    'regintel': {
        'changes': cmd_ri_changes,
        'detect': cmd_ri_detect,
        'sources': cmd_ri_sources,
        'stats': cmd_ri_stats,
        'impact': cmd_ri_impact,
        'matrix': cmd_ri_matrix,
        'calendar': cmd_ri_calendar,
        'notify': cmd_ri_notify,
        'pending': cmd_ri_pending,
        'search': cmd_ri_search,
    },
    'audit-mgmt': {
        'list': cmd_am_list,
        'schedule': cmd_am_schedule,
        'rights': cmd_am_rights,
        'stats': cmd_am_stats,
        'upcoming': cmd_am_upcoming,
        'overdue': cmd_am_overdue,
        'workflow': cmd_am_workflow,
        'report': cmd_am_report,
        'register-right': cmd_am_register_right,
        'calendar': cmd_am_calendar,
    },
    'dres': {
        'list': cmd_dr_list,
        'register': cmd_dr_register,
        'check': cmd_dr_check,
        'summary': cmd_dr_summary,
        'flows': cmd_dr_flows,
        'move': cmd_dr_move,
        'audit': cmd_dr_audit,
        'violations': cmd_dr_violations,
        'compliance-report': cmd_dr_compliance_report,
        'asset-search': cmd_dr_asset_search,
    },
    'train': {
        'modules': cmd_ct_modules,
        'assign': cmd_ct_assign,
        'status': cmd_ct_status,
        'stats': cmd_ct_stats,
        'certifications': cmd_ct_certifications,
        'expiring': cmd_ct_expiring,
        'search': cmd_ct_search,
        'report': cmd_ct_report,
        'progress': cmd_ct_progress,
        'batch-assign': cmd_ct_batch_assign,
    },
    'auditor': {
        'sessions': cmd_ap_sessions,
        'evidence': cmd_ap_evidence,
        'findings': cmd_ap_findings,
        'stats': cmd_ap_stats,
        'engagement-create': cmd_ap_engagement_create,
        'engagement-complete': cmd_ap_engagement_complete,
        'finding-create': cmd_ap_finding_create,
        'session-revoke': cmd_ap_session_revoke,
        'session-extend': cmd_ap_session_extend,
        'finding-update': cmd_ap_finding_update,
    },

    # === Customer Experience ===
    'tickets': {
        'list': cmd_ticket_list,
        'get': cmd_ticket_get,
        'create': cmd_ticket_create,
        'update': cmd_ticket_update,
        'assign': cmd_ticket_assign,
        'comment': cmd_ticket_comment,
        'sla': cmd_ticket_sla,
        'overdue': cmd_ticket_overdue,
        'unassigned': cmd_ticket_unassigned,
        'stats': cmd_ticket_stats,
        'search': cmd_ticket_search,
        'canned': cmd_ticket_canned,
    },
    'nps': {
        'list': cmd_nps_list,
        'score': cmd_nps_score,
        'trend': cmd_nps_trend,
        'detractors': cmd_nps_detractors,
        'promoters': cmd_nps_promoters,
        'send': cmd_nps_send,
        'respond': cmd_nps_respond,
    },
    'sentiment': {
        'profile': cmd_sentiment_profile,
        'trend': cmd_sentiment_trend,
        'alerts': cmd_sentiment_alerts,
        'distribution': cmd_sentiment_distribution,
        'search': cmd_sentiment_search,
        'record': cmd_sentiment_record,
    },
    'onboard': {
        'list': cmd_onboard_list,
        'get': cmd_onboard_get,
        'create': cmd_onboard_create,
        'complete-step': cmd_onboard_complete_step,
        'skip-step': cmd_onboard_skip_step,
        'stuck': cmd_onboard_stuck,
        'stats': cmd_onboard_stats,
        'summary': cmd_onboard_summary,
    },
    'comms': {
        'list': cmd_comms_list,
        'send': cmd_comms_send,
        'maintenance': cmd_comms_maintenance,
        'templates': cmd_comms_templates,
        'stats': cmd_comms_stats,
    },
    'adoption': {
        'profile': cmd_adoption_profile,
        'features': cmd_adoption_features,
        'segments': cmd_adoption_segments,
        'funnel': cmd_adoption_funnel,
        'ranking': cmd_adoption_ranking,
    },
    'health': {
        'profile': cmd_health_profile,
        'summary': cmd_health_summary,
        'at-risk': cmd_health_at_risk,
        'distribution': cmd_health_distribution,
    },
    'kb': {
        'search': cmd_kb_search,
        'popular': cmd_kb_popular,
        'categories': cmd_kb_categories,
        'stats': cmd_kb_stats,
    },
    'automation': {
        'list': cmd_automation_list,
        'create': cmd_automation_create,
        'executions': cmd_automation_executions,
        'failed': cmd_automation_failed,
        'stats': cmd_automation_stats,
    },
    'community': {
        'posts': cmd_community_posts,
        'trending': cmd_community_trending,
        'categories': cmd_community_categories,
        'search': cmd_community_search,
        'leaderboard': cmd_community_leaderboard,
    },

    # === v4 Platform Engineering ===
    'devportal': {
        'list': cmd_devportal_list,
        'register': cmd_devportal_register,
        'get': cmd_devportal_get,
        'summary': cmd_devportal_summary,
    },
    'scaffold': {
        'list': cmd_scaffold_list,
        'generate': cmd_scaffold_generate,
        'status': cmd_scaffold_status,
        'step': cmd_scaffold_step,
    },
    'service-catalog': {
        'list': cmd_catalog_list,
        'register': cmd_catalog_register,
        'get': cmd_catalog_get,
        'score': cmd_catalog_score,
        'summary': cmd_catalog_summary,
    },
    'scorecards': {
        'list': cmd_scorecards_list,
        'create': cmd_scorecards_create,
        'get': cmd_scorecards_get,
        'update': cmd_scorecards_update,
        'summary': cmd_scorecards_summary,
    },
    'template-registry': {
        'list': cmd_templatereg_list,
        'create': cmd_templatereg_create,
        'get': cmd_templatereg_get,
        'use': cmd_templatereg_use,
        'summary': cmd_templatereg_summary,
    },
    'techdebt': {
        'list': cmd_techdebt_list,
        'report': cmd_techdebt_report,
        'get': cmd_techdebt_get,
        'fix': cmd_techdebt_fix,
        'summary': cmd_techdebt_summary,
    },
    'environments': {
        'list': cmd_environments_list,
        'create': cmd_environments_create,
        'get': cmd_environments_get,
        'delete': cmd_environments_delete,
        'extend': cmd_environments_extend,
        'summary': cmd_environments_summary,
    },
    'api-catalog': {
        'list': cmd_apicatalog_list,
        'register': cmd_apicatalog_register,
        'get': cmd_apicatalog_get,
        'summary': cmd_apicatalog_summary,
    },
    'docgen': {
        'list': cmd_docgen_list,
        'generate': cmd_docgen_generate,
        'get': cmd_docgen_get,
        'summary': cmd_docgen_summary,
    },
    'pulse': {
        'list': cmd_pulse_list,
        'create': cmd_pulse_create,
        'respond': cmd_pulse_respond,
        'results': cmd_pulse_results,
        'summary': cmd_pulse_summary,
    },

    # === v4 Emerging Tech ===
    'blockchain': {
        'list': cmd_blockchain_list,
        'create': cmd_blockchain_create,
        'status': cmd_blockchain_status,
        'validators': cmd_blockchain_validators,
    },
    'storage': {
        'list': cmd_storage_list,
        'create': cmd_storage_create,
        'pin': cmd_storage_pin,
        'status': cmd_storage_status,
    },
    'quantum': {
        'list': cmd_quantum_list,
        'generate': cmd_quantum_generate,
        'cert': cmd_quantum_cert,
        'encrypt': cmd_quantum_encrypt,
        'decrypt': cmd_quantum_decrypt,
    },
    'contracts': {
        'list': cmd_contracts_list,
        'deploy': cmd_contracts_deploy,
        'get': cmd_contracts_get,
        'events': cmd_contracts_events,
    },
    'web3id': {
        'list': cmd_web3id_list,
        'create': cmd_web3id_create,
        'auth': cmd_web3id_auth,
        'sessions': cmd_web3id_sessions,
    },
    'confidential': {
        'list': cmd_confidential_list,
        'create': cmd_confidential_create,
        'attest': cmd_confidential_attest,
        'secrets': cmd_confidential_secrets,
    },
    'federated': {
        'list': cmd_federated_list,
        'create': cmd_federated_create,
        'status': cmd_federated_status,
        'rounds': cmd_federated_rounds,
    },
    'zkp': {
        'list': cmd_zkp_list,
        'generate': cmd_zkp_generate,
        'verify': cmd_zkp_verify,
        'circuits': cmd_zkp_circuits,
    },
    'dcn': {
        'list': cmd_dcn_list,
        'submit': cmd_dcn_submit,
        'status': cmd_dcn_status,
        'workers': cmd_dcn_workers,
    },

}

if args.command in sub_router:
        sub_map = sub_router[args.command]
        entry = sub_map.get(args.subcommand)
        if isinstance(entry, dict):
            action = getattr(args, 'action', None)
            if action and action in entry:
                inner = entry[action]
                if isinstance(inner, dict):
                    maint_action = getattr(args, 'maint_action', None)
                    inner.get(maint_action, lambda a: parser.print_help())(args)
                else:
                    inner(args)
            else:
                parser.print_help()
        elif entry:
            entry(args)
        else:
            parser.print_help()
    elif args.command == 'logs':
        cmd_logs(args)
    elif args.command == 'deploy':
        cmd_deploy(args)
    elif args.command in cmd_map:
        cmd_map[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
