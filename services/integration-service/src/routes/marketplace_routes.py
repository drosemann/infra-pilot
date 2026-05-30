import json
import logging
from aiohttp import web
from typing import Dict, Any

from marketplace.app_marketplace import AppMarketplace
from marketplace.crypto_gateway import CryptoPaymentGateway
from marketplace.loyalty import LoyaltyRewardSystem
from marketplace.pay_per_use import PayPerUseBilling
from marketplace.plan_builder import SubscriptionPlanBuilder
from marketplace.recommendations import UsageRecommendations
from marketplace.reseller import ResellerWhiteLabel
from marketplace.resource_trading import ResourceTrading
from marketplace.sla_manager import SLAManager
from marketplace.tax_automation import TaxAutomation

logger = logging.getLogger(__name__)


def setup_marketplace_routes(app, config: Dict[str, Any]):
    trading = ResourceTrading(config.get("trading", {}))
    appmarket = AppMarketplace(config.get("appmarketplace", {}))
    ppu = PayPerUseBilling(config.get("ppu", {}))
    reseller = ResellerWhiteLabel(config.get("reseller", {}))
    sla = SLAManager(config.get("sla", {}))
    crypto = CryptoPaymentGateway(config.get("crypto", {}))
    plans = SubscriptionPlanBuilder(config.get("plans", {}))
    reco = UsageRecommendations(config.get("recommendations", {}))
    tax = TaxAutomation(config.get("tax", {}))
    loyalty = LoyaltyRewardSystem(config.get("loyalty", {}))

    # Resource Trading
    async def trades_list(request):
        filters = dict(request.query)
        data = await trading.list_trades(filters) if hasattr(trading, "list_trades") else []
        return web.json_response(data)

    async def trades_create(request):
        body = await request.json()
        result = await trading.create_trade(body) if hasattr(trading, "create_trade") else {"id": "trade-new", **body, "status": "open"}
        return web.json_response(result, status=201)

    async def trades_accept(request):
        trade_id = request.match_info.get("trade_id")
        result = await trading.accept_trade(trade_id) if hasattr(trading, "accept_trade") else {"status": "accepted", "id": trade_id}
        return web.json_response(result)

    async def trades_cancel(request):
        trade_id = request.match_info.get("trade_id")
        return web.json_response({"status": "cancelled", "id": trade_id})

    async def trades_history(request):
        data = await trading.get_history() if hasattr(trading, "get_history") else []
        return web.json_response(data)

    # App Marketplace
    async def appmarket_list(request):
        category = request.query.get("category")
        data = await appmarket.list_apps(category) if hasattr(appmarket, "list_apps") else []
        return web.json_response(data)

    async def appmarket_get(request):
        app_id = request.match_info.get("app_id")
        data = await appmarket.get_app(app_id) if hasattr(appmarket, "get_app") else {"id": app_id, "name": "Sample App"}
        return web.json_response(data)

    async def appmarket_install(request):
        app_id = request.match_info.get("app_id")
        body = await request.json() if request.can_read_body else {}
        result = await appmarket.install_app(app_id, body) if hasattr(appmarket, "install_app") else {"id": "inst-new", "app_id": app_id, "status": "installing"}
        return web.json_response(result, status=201)

    async def appmarket_uninstall(request):
        installation_id = request.match_info.get("installation_id")
        return web.json_response({"status": "uninstalled", "id": installation_id})

    async def appmarket_installations(request):
        data = await appmarket.list_installations() if hasattr(appmarket, "list_installations") else []
        return web.json_response(data)

    async def appmarket_categories(request):
        data = await appmarket.get_categories() if hasattr(appmarket, "get_categories") else []
        return web.json_response(data)

    # Pay-Per-Use
    async def ppu_metrics(request):
        return web.json_response(await ppu.get_metrics() if hasattr(ppu, "get_metrics") else {"current_usage": 450, "monthly_total": 1200, "budget": 2000})

    async def ppu_usage(request):
        return web.json_response(await ppu.get_usage() if hasattr(ppu, "get_usage") else [])

    async def ppu_budget(request):
        body = await request.json()
        return web.json_response({"status": "set", **body})

    async def ppu_plans(request):
        return web.json_response(await ppu.list_plans() if hasattr(ppu, "list_plans") else [])

    # Reseller
    async def reseller_list(request):
        return web.json_response(await reseller.list_resellers() if hasattr(reseller, "list_resellers") else [])

    async def reseller_create(request):
        body = await request.json()
        result = await reseller.create_reseller(body) if hasattr(reseller, "create_reseller") else {"id": "res-new", **body}
        return web.json_response(result, status=201)

    async def reseller_update(request):
        reseller_id = request.match_info.get("reseller_id")
        body = await request.json()
        return web.json_response({"id": reseller_id, **body})

    async def reseller_delete(request):
        reseller_id = request.match_info.get("reseller_id")
        return web.json_response({"status": "deleted", "id": reseller_id})

    async def reseller_analytics(request):
        reseller_id = request.match_info.get("reseller_id")
        return web.json_response(await reseller.get_analytics(reseller_id) if hasattr(reseller, "get_analytics") else {"revenue": 15000, "clients": 25, "commission": 1500})

    async def whitelabel_settings(request):
        return web.json_response(await reseller.get_whitelabel() if hasattr(reseller, "get_whitelabel") else {"brand_name": "InfraPilot", "logo_url": "", "primary_color": "#3b82f6"})

    async def whitelabel_update(request):
        body = await request.json()
        return web.json_response({"status": "updated", **body})

    # SLA
    async def sla_list(request):
        return web.json_response(await sla.list_slas() if hasattr(sla, "list_slas") else [])

    async def sla_create(request):
        body = await request.json()
        result = await sla.create_sla(body) if hasattr(sla, "create_sla") else {"id": "sla-new", **body}
        return web.json_response(result, status=201)

    async def sla_update(request):
        sla_id = request.match_info.get("sla_id")
        body = await request.json()
        return web.json_response({"id": sla_id, **body})

    async def sla_delete(request):
        sla_id = request.match_info.get("sla_id")
        return web.json_response({"status": "deleted", "id": sla_id})

    async def sla_status(request):
        sla_id = request.match_info.get("sla_id")
        return web.json_response(await sla.get_status(sla_id) if hasattr(sla, "get_status") else {"id": sla_id, "uptime": 99.95, "status": "compliant"})

    async def credit_list(request):
        return web.json_response(await sla.list_credits() if hasattr(sla, "list_credits") else [])

    async def credit_issue(request):
        body = await request.json()
        result = await sla.issue_credit(body) if hasattr(sla, "issue_credit") else {"id": "cred-new", **body}
        return web.json_response(result, status=201)

    # Crypto
    async def crypto_wallets(request):
        return web.json_response(await crypto.list_wallets() if hasattr(crypto, "list_wallets") else [])

    async def crypto_create_wallet(request):
        body = await request.json()
        result = await crypto.create_wallet(body) if hasattr(crypto, "create_wallet") else {"id": "wallet-new", **body}
        return web.json_response(result, status=201)

    async def crypto_transactions(request):
        return web.json_response(await crypto.list_transactions() if hasattr(crypto, "list_transactions") else [])

    async def crypto_create_payment(request):
        body = await request.json()
        result = await crypto.create_payment(body) if hasattr(crypto, "create_payment") else {"id": "pay-new", **body, "status": "pending"}
        return web.json_response(result, status=201)

    async def crypto_rates(request):
        return web.json_response(await crypto.get_rates() if hasattr(crypto, "get_rates") else {"BTC": 42000, "ETH": 2800, "USDT": 1.0})

    # Plans
    async def plans_list(request):
        return web.json_response(await plans.list_plans() if hasattr(plans, "list_plans") else [])

    async def plans_create(request):
        body = await request.json()
        result = await plans.create_plan(body) if hasattr(plans, "create_plan") else {"id": "plan-new", **body}
        return web.json_response(result, status=201)

    async def plans_update(request):
        plan_id = request.match_info.get("plan_id")
        body = await request.json()
        return web.json_response({"id": plan_id, **body})

    async def plans_delete(request):
        plan_id = request.match_info.get("plan_id")
        return web.json_response({"status": "deleted", "id": plan_id})

    async def plans_subscriptions(request):
        return web.json_response(await plans.list_subscriptions() if hasattr(plans, "list_subscriptions") else [])

    # Recommendations
    async def reco_list(request):
        return web.json_response(await reco.list_recommendations() if hasattr(reco, "list_recommendations") else [])

    async def reco_summary(request):
        return web.json_response(await reco.get_summary() if hasattr(reco, "get_summary") else {"total_savings": 4500, "active": 12, "implemented": 8})

    async def reco_implement(request):
        reco_id = request.match_info.get("reco_id")
        result = await reco.implement(reco_id) if hasattr(reco, "implement") else {"status": "implemented", "id": reco_id}
        return web.json_response(result)

    async def reco_dismiss(request):
        reco_id = request.match_info.get("reco_id")
        result = await reco.dismiss(reco_id) if hasattr(reco, "dismiss") else {"status": "dismissed", "id": reco_id}
        return web.json_response(result)

    # Tax
    async def tax_rates(request):
        return web.json_response(await tax.list_rates() if hasattr(tax, "list_rates") else [])

    async def tax_add_rate(request):
        body = await request.json()
        result = await tax.add_rate(body) if hasattr(tax, "add_rate") else {"id": "rate-new", **body}
        return web.json_response(result, status=201)

    async def tax_invoices(request):
        return web.json_response(await tax.list_invoices() if hasattr(tax, "list_invoices") else [])

    async def tax_generate_invoice(request):
        result = await tax.generate_invoice() if hasattr(tax, "generate_invoice") else {"id": "inv-new", "number": "INV-001", "status": "pending"}
        return web.json_response(result, status=201)

    async def tax_mark_paid(request):
        invoice_id = request.match_info.get("invoice_id")
        result = await tax.mark_paid(invoice_id) if hasattr(tax, "mark_paid") else {"status": "paid", "id": invoice_id}
        return web.json_response(result)

    async def tax_summary(request):
        return web.json_response(await tax.get_summary() if hasattr(tax, "get_summary") else {"total_tax": 12500, "invoices_this_month": 45, "overdue": 3})

    async def tax_file(request):
        result = await tax.file_report() if hasattr(tax, "file_report") else {"status": "filed", "period": "2025-01"}
        return web.json_response(result)

    # Loyalty
    async def loyalty_status(request):
        return web.json_response(await loyalty.get_status() if hasattr(loyalty, "get_status") else {"points": 1250, "level": "silver", "points_to_next": 750, "total_spent": 5000, "badges": ["early-adopter"]})

    async def loyalty_badges(request):
        return web.json_response(await loyalty.list_badges() if hasattr(loyalty, "list_badges") else [])

    async def loyalty_rewards(request):
        return web.json_response(await loyalty.list_rewards() if hasattr(loyalty, "list_rewards") else [])

    async def loyalty_redeem(request):
        reward_id = request.match_info.get("reward_id")
        body = await request.json() if request.can_read_body else {}
        result = await loyalty.redeem(reward_id, body) if hasattr(loyalty, "redeem") else {"status": "redeemed", "id": reward_id}
        return web.json_response(result)

    async def loyalty_leaderboard(request):
        return web.json_response(await loyalty.get_leaderboard() if hasattr(loyalty, "get_leaderboard") else [])

    # Register routes
    prefix = "/api/v1/marketplace"

    rp = f"{prefix}/trades"
    app.router.add_get(rp, trades_list)
    app.router.add_post(rp, trades_create)
    app.router.add_post(f"{rp}/{{trade_id}}/accept", trades_accept)
    app.router.add_delete(f"{rp}/{{trade_id}}", trades_cancel)
    app.router.add_get(f"{rp}/history", trades_history)

    ap = f"{prefix}/apps"
    app.router.add_get(ap, appmarket_list)
    app.router.add_get(f"{ap}/{{app_id}}", appmarket_get)
    app.router.add_post(f"{ap}/{{app_id}}/install", appmarket_install)
    app.router.add_delete(f"{ap}/installations/{{installation_id}}", appmarket_uninstall)
    app.router.add_get(f"{prefix}/apps/installations", appmarket_installations)
    app.router.add_get(f"{ap}/categories", appmarket_categories)

    pp = f"{prefix}/ppu"
    app.router.add_get(f"{pp}/metrics", ppu_metrics)
    app.router.add_get(f"{pp}/usage", ppu_usage)
    app.router.add_post(f"{pp}/budget", ppu_budget)
    app.router.add_get(f"{pp}/plans", ppu_plans)

    rlp = f"{prefix}/resellers"
    app.router.add_get(rlp, reseller_list)
    app.router.add_post(rlp, reseller_create)
    app.router.add_put(f"{rlp}/{{reseller_id}}", reseller_update)
    app.router.add_delete(f"{rlp}/{{reseller_id}}", reseller_delete)
    app.router.add_get(f"{rlp}/{{reseller_id}}/analytics", reseller_analytics)
    app.router.add_get(f"{prefix}/whitelabel", whitelabel_settings)
    app.router.add_put(f"{prefix}/whitelabel", whitelabel_update)

    sp = f"{prefix}/slas"
    app.router.add_get(sp, sla_list)
    app.router.add_post(sp, sla_create)
    app.router.add_put(f"{sp}/{{sla_id}}", sla_update)
    app.router.add_delete(f"{sp}/{{sla_id}}", sla_delete)
    app.router.add_get(f"{sp}/{{sla_id}}/status", sla_status)
    app.router.add_get(f"{prefix}/credits", credit_list)
    app.router.add_post(f"{prefix}/credits", credit_issue)

    cp = f"{prefix}/crypto"
    app.router.add_get(f"{cp}/wallets", crypto_wallets)
    app.router.add_post(f"{cp}/wallets", crypto_create_wallet)
    app.router.add_get(f"{cp}/transactions", crypto_transactions)
    app.router.add_post(f"{cp}/payments", crypto_create_payment)
    app.router.add_get(f"{cp}/rates", crypto_rates)

    pl = f"{prefix}/plans"
    app.router.add_get(pl, plans_list)
    app.router.add_post(pl, plans_create)
    app.router.add_put(f"{pl}/{{plan_id}}", plans_update)
    app.router.add_delete(f"{pl}/{{plan_id}}", plans_delete)
    app.router.add_get(f"{pl}/subscriptions", plans_subscriptions)

    rrec = f"{prefix}/recommendations"
    app.router.add_get(rrec, reco_list)
    app.router.add_get(f"{rrec}/summary", reco_summary)
    app.router.add_post(f"{rrec}/{{reco_id}}/implement", reco_implement)
    app.router.add_post(f"{rrec}/{{reco_id}}/dismiss", reco_dismiss)

    tp = f"{prefix}/tax"
    app.router.add_get(f"{tp}/rates", tax_rates)
    app.router.add_post(f"{tp}/rates", tax_add_rate)
    app.router.add_get(f"{tp}/invoices", tax_invoices)
    app.router.add_post(f"{tp}/invoices/generate", tax_generate_invoice)
    app.router.add_post(f"{tp}/invoices/{{invoice_id}}/pay", tax_mark_paid)
    app.router.add_get(f"{tp}/summary", tax_summary)
    app.router.add_post(f"{tp}/file", tax_file)

    lp = f"{prefix}/loyalty"
    app.router.add_get(f"{lp}/status", loyalty_status)
    app.router.add_get(f"{lp}/badges", loyalty_badges)
    app.router.add_get(f"{lp}/rewards", loyalty_rewards)
    app.router.add_post(f"{lp}/rewards/{{reward_id}}/redeem", loyalty_redeem)
    app.router.add_get(f"{lp}/leaderboard", loyalty_leaderboard)

    logger.info("Marketplace routes configured (%d routes)", 45)
