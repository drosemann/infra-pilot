"""Edge Function Runtime Cog - Lightweight WASM/container runtime for edge nodes."""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Callable

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class FunctionRuntime(Enum):
    WASM = "wasm"
    CONTAINER = "container"
    NATIVE = "native"


class FunctionStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"


class TriggerType(Enum):
    TIMER = "timer"
    MQTT = "mqtt"
    HTTP = "http"
    FILE = "file"
    WEBHOOK = "webhook"


class EdgeFunction:
    """Represents a deployed edge function."""

    def __init__(self, func_id: str, name: str, runtime: FunctionRuntime,
                 device_id: str, source: str, handler: str):
        self.func_id = func_id
        self.name = name
        self.runtime = runtime
        self.device_id = device_id
        self.source = source
        self.handler = handler
        self.version = "1.0.0"
        self.status = FunctionStatus.PENDING
        self.triggers: list[dict[str, Any]] = []
        self.environment: dict[str, str] = {}
        self.resource_limits: dict[str, Any] = {
            "cpu_shares": 256,
            "memory_mb": 128,
            "timeout_seconds": 30,
        }
        self.offline_queue_enabled: bool = True
        self.retry_on_failure: bool = True
        self.max_retries: int = 3
        self.invocation_count: int = 0
        self.last_invocation: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "func_id": self.func_id,
            "name": self.name,
            "runtime": self.runtime.value,
            "device_id": self.device_id,
            "source": self.source,
            "handler": self.handler,
            "version": self.version,
            "status": self.status.value,
            "triggers": self.triggers,
            "environment": dict(self.environment),
            "resource_limits": self.resource_limits,
            "offline_queue_enabled": self.offline_queue_enabled,
            "retry_on_failure": self.retry_on_failure,
            "max_retries": self.max_retries,
            "invocation_count": self.invocation_count,
            "last_invocation": self.last_invocation.isoformat() if self.last_invocation else None,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class OfflineQueueItem:
    """Represents an item in the offline queue for sync-on-reconnect."""

    def __init__(self, queue_id: str, func_id: str, payload: dict[str, Any],
                 trigger_type: str):
        self.queue_id = queue_id
        self.func_id = func_id
        self.payload = payload
        self.trigger_type = trigger_type
        self.status = "queued"
        self.created_at = datetime.utcnow()
        self.retry_count = 0
        self.last_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "func_id": self.func_id,
            "payload": self.payload,
            "trigger_type": self.trigger_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "last_error": self.last_error,
        }


class EdgeFunctionRuntime:
    """Manager for edge function deployment and execution."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.functions: dict[str, EdgeFunction] = {}
        self.offline_queue: list[OfflineQueueItem] = []
        self._function_tasks: dict[str, asyncio.Task] = {}
        self._timer_tasks: dict[str, asyncio.Task] = {}
        self._seed_functions()

    def _seed_functions(self):
        demo_funcs = [
            ("func-001", "sensor-filter", FunctionRuntime.WASM, "dev-001",
             "wasm://functions/sensor-filter.wasm", "process"),
            ("func-002", "temp-converter", FunctionRuntime.WASM, "dev-002",
             "wasm://functions/temp-converter.wasm", "convert"),
            ("func-003", "data-aggregator", FunctionRuntime.NATIVE, "dev-003",
             "python://functions/aggregator.py", "aggregate"),
            ("func-004", "alert-generator", FunctionRuntime.CONTAINER, "dev-004",
             "docker://functions/alert-gen:latest", "main"),
            ("func-005", "image-classifier", FunctionRuntime.WASM, "dev-006",
             "wasm://functions/classifier.wasm", "classify"),
        ]
        for fid, name, runtime, dev_id, src, handler in demo_funcs:
            func = EdgeFunction(fid, name, runtime, dev_id, src, handler)
            func.status = FunctionStatus.RUNNING
            func.invocation_count = hash(fid) % 1000
            func.triggers = [{"type": "timer", "config": {"cron": "*/5 * * * *"}}]
            self.functions[fid] = func

    async def initialize(self):
        logger.info("EdgeFunctionRuntime initialized with %d functions", len(self.functions))

    async def close(self):
        for task in self._function_tasks.values():
            task.cancel()
        for task in self._timer_tasks.values():
            task.cancel()
        logger.info("EdgeFunctionRuntime closed")

    def deploy_function(self, name: str, runtime: FunctionRuntime,
                        device_id: str, source: str, handler: str,
                        resource_limits: Optional[dict] = None,
                        environment: Optional[dict[str, str]] = None) -> EdgeFunction:
        func_id = f"func-{uuid.uuid4().hex[:8]}"
        func = EdgeFunction(func_id, name, runtime, device_id, source, handler)
        func.status = FunctionStatus.DEPLOYING
        if resource_limits:
            func.resource_limits.update(resource_limits)
        if environment:
            func.environment.update(environment)
        self.functions[func_id] = func
        asyncio.create_task(self._finalize_deployment(func))
        logger.info("Deploying function %s (%s) to device %s", func_id, name, device_id)
        return func

    async def _finalize_deployment(self, func: EdgeFunction):
        try:
            await asyncio.sleep(1)
            func.status = FunctionStatus.RUNNING
            func.updated_at = datetime.utcnow()
            logger.info("Function %s deployed successfully", func.func_id)
        except Exception as e:
            func.status = FunctionStatus.FAILED
            func.last_error = str(e)

    def get_function(self, func_id: str) -> Optional[EdgeFunction]:
        return self.functions.get(func_id)

    def list_functions(self, device_id: Optional[str] = None,
                       status: Optional[str] = None,
                       runtime: Optional[str] = None) -> list[EdgeFunction]:
        result = list(self.functions.values())
        if device_id:
            result = [f for f in result if f.device_id == device_id]
        if status:
            result = [f for f in result if f.status.value == status]
        if runtime:
            result = [f for f in result if f.runtime.value == runtime]
        return result

    def update_function(self, func_id: str, updates: dict[str, Any]) -> Optional[EdgeFunction]:
        func = self.functions.get(func_id)
        if not func:
            return None
        if "version" in updates:
            func.version = updates["version"]
        if "environment" in updates:
            func.environment.update(updates["environment"])
        if "resource_limits" in updates:
            func.resource_limits.update(updates["resource_limits"])
        if "triggers" in updates:
            func.triggers = updates["triggers"]
        func.updated_at = datetime.utcnow()
        return func

    def delete_function(self, func_id: str) -> bool:
        if func_id in self.functions:
            del self.functions[func_id]
            if func_id in self._function_tasks:
                self._function_tasks[func_id].cancel()
                del self._function_tasks[func_id]
            return True
        return False

    def add_trigger(self, func_id: str, trigger_type: str,
                    config: dict[str, Any]) -> bool:
        func = self.functions.get(func_id)
        if not func:
            return False
        func.triggers.append({"type": trigger_type, "config": config})
        func.updated_at = datetime.utcnow()
        if trigger_type == "timer":
            self._schedule_timer(func, config)
        return True

    def _schedule_timer(self, func: EdgeFunction, config: dict[str, Any]):
        interval = config.get("interval_seconds", 60)

        async def timer_loop():
            while True:
                await asyncio.sleep(interval)
                await self._invoke_function(func, {"trigger": "timer", "time": datetime.utcnow().isoformat()})

        task = asyncio.create_task(timer_loop())
        self._timer_tasks[func.func_id] = task

    async def _invoke_function(self, func: EdgeFunction, payload: dict[str, Any]) -> dict[str, Any]:
        func.invocation_count += 1
        func.last_invocation = datetime.utcnow()
        func.last_error = None

        try:
            await asyncio.sleep(0.1)
            result = {
                "success": True,
                "func_id": func.func_id,
                "name": func.name,
                "result": {"processed": True, "payload_size": len(json.dumps(payload))},
                "execution_time_ms": 50,
                "timestamp": datetime.utcnow().isoformat(),
            }
            return result
        except Exception as e:
            func.last_error = str(e)
            if func.retry_on_failure and func.max_retries > 0:
                self._queue_for_retry(func, payload)
            return {"success": False, "error": str(e), "func_id": func.func_id}

    def _queue_for_retry(self, func: EdgeFunction, payload: dict[str, Any]):
        item = OfflineQueueItem(
            f"q-{uuid.uuid4().hex[:8]}", func.func_id, payload, "retry"
        )
        self.offline_queue.append(item)

    def invoke_function(self, func_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        func = self.functions.get(func_id)
        if not func:
            return {"success": False, "error": "Function not found"}
        if func.status != FunctionStatus.RUNNING:
            if func.offline_queue_enabled:
                item = OfflineQueueItem(
                    f"q-{uuid.uuid4().hex[:8]}", func_id, payload, "manual"
                )
                self.offline_queue.append(item)
                return {"success": True, "queued": True, "queue_id": item.queue_id}
            return {"success": False, "error": f"Function status: {func.status.value}"}
        return asyncio.run_coroutine_threadsafe(
            self._invoke_function(func, payload), asyncio.get_event_loop()
        ).result()

    def get_offline_queue(self, func_id: Optional[str] = None) -> list[OfflineQueueItem]:
        if func_id:
            return [item for item in self.offline_queue if item.func_id == func_id]
        return list(self.offline_queue)

    def process_offline_queue(self, device_id: str):
        queued = [item for item in self.offline_queue
                  if item.func_id in self.functions
                  and self.functions[item.func_id].device_id == device_id
                  and item.status == "queued"]
        for item in queued:
            func = self.functions[item.func_id]
            if func.status == FunctionStatus.RUNNING:
                asyncio.create_task(self._process_queue_item(item, func))

    async def _process_queue_item(self, item: OfflineQueueItem, func: EdgeFunction):
        item.status = "processing"
        result = await self._invoke_function(func, item.payload)
        if result.get("success"):
            item.status = "completed"
        else:
            item.retry_count += 1
            if item.retry_count >= func.max_retries:
                item.status = "failed"
            else:
                item.status = "queued"

    def create_function_chain(self, func_ids: list[str]) -> list[dict[str, Any]]:
        chain_results = []
        previous_result = None
        for func_id in func_ids:
            payload = {"previous_result": previous_result} if previous_result else {}
            result = self.invoke_function(func_id, payload)
            chain_results.append(result)
            if result.get("success") and "result" in result:
                previous_result = result["result"]
            elif not result.get("success"):
                break
        return chain_results

    def get_functions_summary(self) -> dict[str, Any]:
        total = len(self.functions)
        running = sum(1 for f in self.functions.values() if f.status == FunctionStatus.RUNNING)
        return {
            "total": total,
            "running": running,
            "pending": sum(1 for f in self.functions.values() if f.status == FunctionStatus.PENDING),
            "failed": sum(1 for f in self.functions.values() if f.status == FunctionStatus.FAILED),
            "total_invocations": sum(f.invocation_count for f in self.functions.values()),
            "queue_depth": len(self.offline_queue),
        }


class EdgeFunctionRuntimeCog(commands.Cog):
    """Discord cog for edge function runtime management."""

    def __init__(self, bot):
        self.bot = bot
        config = getattr(bot, "config", {})
        self.runtime = EdgeFunctionRuntime({})

    async def cog_load(self):
        await self.runtime.initialize()

    async def cog_unload(self):
        await self.runtime.close()

    @discord.app_commands.command(name="fn_list", description="List edge functions")
    async def fn_list(self, interaction: discord.Interaction,
                      device_id: Optional[str] = None):
        functions = self.runtime.list_functions(device_id=device_id)
        embed = discord.Embed(title="Edge Functions", color=discord.Color.blue())
        if not functions:
            embed.description = "No functions deployed."
        else:
            lines = []
            for f in functions[:25]:
                status_emoji = {"running": "🟢", "deploying": "🟡",
                                "failed": "🔴", "stopped": "⏹️", "pending": "🟣"}
                emoji = status_emoji.get(f.status.value, "⚪")
                lines.append(f"{emoji} **{f.name}** (`{f.func_id}`)")
                lines.append(f"   Runtime: {f.runtime.value} | Device: {f.device_id} | "
                           f"Invocations: {f.invocation_count}")
            embed.description = "\n".join(lines[:25])
        summary = self.runtime.get_functions_summary()
        embed.set_footer(text=f"Total: {summary['total']} | "
                            f"Running: {summary['running']} | "
                            f"Queue: {summary['queue_depth']}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="fn_deploy", description="Deploy an edge function")
    async def fn_deploy(self, interaction: discord.Interaction,
                        name: str, runtime: str, device_id: str,
                        source: str, handler: str):
        try:
            rt = FunctionRuntime(runtime)
        except ValueError:
            await interaction.response.send_message(
                f"Invalid runtime. Choose from: {', '.join(r.value for r in FunctionRuntime)}",
                ephemeral=True
            )
            return
        func = self.runtime.deploy_function(name, rt, device_id, source, handler)
        embed = discord.Embed(title="Function Deployed", color=discord.Color.green())
        embed.add_field(name="Name", value=func.name, inline=True)
        embed.add_field(name="ID", value=func.func_id, inline=True)
        embed.add_field(name="Runtime", value=func.runtime.value, inline=True)
        embed.add_field(name="Device", value=func.device_id, inline=True)
        embed.add_field(name="Source", value=func.source[:50], inline=True)
        embed.add_field(name="Handler", value=func.handler, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="fn_invoke", description="Invoke an edge function")
    async def fn_invoke(self, interaction: discord.Interaction,
                        func_id: str, payload: Optional[str] = None):
        payload_data = json.loads(payload) if payload else {}
        result = self.runtime.invoke_function(func_id, payload_data)
        embed = discord.Embed(title="Function Invocation", color=discord.Color.blue())
        if result.get("success"):
            embed.color = discord.Color.green()
            embed.add_field(name="Result", value=str(result.get("result", {})), inline=False)
        else:
            embed.color = discord.Color.red()
            embed.add_field(name="Error", value=result.get("error", "Unknown"), inline=False)
        if result.get("queued"):
            embed.add_field(name="Queued", value=f"Queue ID: {result['queue_id']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="fn_delete", description="Delete an edge function")
    async def fn_delete(self, interaction: discord.Interaction, func_id: str):
        if self.runtime.delete_function(func_id):
            await interaction.response.send_message(f"Function {func_id} deleted.")
        else:
            await interaction.response.send_message("Function not found.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(EdgeFunctionRuntimeCog(bot))
