import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

from config import config
from integration import init_database_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("main")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.config = config


async def load_cogs():
    core_cogs = [
        "cogs.vps_commands",
        "cogs.vps_pricing",
        "cogs.vps_billing",
        "cogs.prepaid_billing",
        "cogs.monitoring",
        "cogs.bot_commands",
        "cogs.health_checks",
        "cogs.backup_manager",
        "cogs.resource_manager",
        "cogs.template_manager",
        "cogs.task_scheduler",
        "cogs.alert_manager",
        "cogs.cleanup",
        "cogs.database_manager",
        "cogs.modpack_installer",
        "cogs.update_manager",
    ]
    for cog in core_cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")


@bot.event
async def on_ready():
    logger.info(f"Bot ready. Logged in as {bot.user}")
    try:
        init_database_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
    await bot.tree.sync()
    logger.info("Commands synced")

    asyncio.create_task(start_webhook_server(bot))


async def start_webhook_server(bot):
    from aiohttp import web
    app = web.Application()

    async def health(request):
        return web.json_response({"status": "ok", "service": "orchestrator-agent"})

    app.router.add_get('/health', health)

    cog = bot.get_cog('GitDeployer')
    if cog:
        app.router.add_post('/webhook/github/{deploy_id}', cog.handle_webhook)
        app.router.add_post('/webhook/github', cog.handle_webhook)

    gitops_cog = bot.get_cog('GitOpsSync')
    if gitops_cog:
        app.router.add_post('/webhook/gitops', gitops_cog.handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('GITOPS_WEBHOOK_PORT', '8500'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f'Webhook server listening on port {port}')


if __name__ == "__main__":
    token_missing = not config.DISCORD_BOT_TOKEN or config.DISCORD_BOT_TOKEN == 'your_discord_bot_token_here'
    disabled = os.getenv('ORCHESTRATOR_AGENT_DISABLED', 'true').lower() == 'true'
    if token_missing or disabled:
        logger.warning('Discord bot disabled; starting health/webhook server only')

        async def run_health_only():
            await start_webhook_server(bot)
            await asyncio.Event().wait()

        asyncio.run(run_health_only())
        sys.exit(0)

    asyncio_loop = None
    try:
        asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(asyncio_loop)
        asyncio_loop.run_until_complete(load_cogs())
        bot.run(config.DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutting down")
    finally:
        if asyncio_loop:
            asyncio_loop.close()
