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


def main():
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
}

if args.command in sub_router:
        sub_map = sub_router[args.command]
        sub_map.get(args.subcommand, lambda a: parser.print_help())(args)
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
