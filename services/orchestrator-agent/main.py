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
    cog_list = [
        "cogs.vps_commands",
        "cogs.vps_pricing",
        "cogs.vps_billing",
        "cogs.monitoring",
        "cogs.bot_commands",
    ]
    new_cogs = [
        "cogs.health_checks",
        "cogs.auto_scaling",
        "cogs.backup_manager",
        "cogs.cost_prediction",
        "cogs.performance_optimizer",
        "cogs.resource_manager",
        "cogs.network_monitor",
        "cogs.template_manager",
        "cogs.server_migration",
        "cogs.clone_system",
        "cogs.snapshot_system",
        "cogs.alert_manager",
        "cogs.benchmark",
        "cogs.recovery",
        "cogs.troubleshoot",
        "cogs.security_audit",
        "cogs.update_manager",
        "cogs.cleanup",
        "cogs.quota_manager",
        "cogs.load_balancer",
        "cogs.dns_manager",
        "cogs.ssl_manager",
        "cogs.cost_optimizer",
        "cogs.traffic_analysis",
    ]
    for cog in cog_list + new_cogs:
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


if __name__ == "__main__":
    if not config.DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set")
        sys.exit(1)

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
