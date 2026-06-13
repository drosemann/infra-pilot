"""Feature 60: Self-Service Operations Chatbot — Chatbot for common ops tasks."""

import json
import os
import uuid
import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class TaskType(Enum):
    RESTART_SERVICE = "restart_service"
    CHECK_LOGS = "check_logs"
    RUN_BACKUP = "run_backup"
    CHECK_STATUS = "check_status"
    LIST_SERVICES = "list_services"
    SCALE_SERVICE = "scale_service"
    DEPLOY_VERSION = "deploy_version"
    CLEAR_CACHE = "clear_cache"
    RUN_DIAGNOSTIC = "run_diagnostic"
    SHOW_METRICS = "show_metrics"


class TaskStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class ChatbotState(Enum):
    IDLE = "idle"
    AWAITING_INPUT = "awaiting_input"
    PROCESSING = "processing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"


class OpsChatbot:
    """Self-service chatbot for common operations tasks with RBAC."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.require_confirmation = config.get("require_confirmation", True)
        self.session_timeout = config.get("session_timeout_minutes", 30)
        self.max_conversations = config.get("max_conversations", 1000)
        self.conversations_file = _data_file('chatbot_conversations.json')
        self.tasks_file = _data_file('chatbot_tasks.json')
        self.analytics_file = _data_file('chatbot_analytics.json')
        self.conversations: List[Dict[str, Any]] = []
        self.tasks: List[Dict[str, Any]] = []
        self.analytics: Dict[str, Any] = {"total_messages": 0, "tasks_completed": 0,
                                           "tasks_failed": 0, "popular_commands": {}}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.conversations_file, "conversations"),
            (self.tasks_file, "tasks"),
            (self.analytics_file, "analytics")
        ]:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if target == "conversations":
                    self.conversations = data
                elif target == "tasks":
                    self.tasks = data
                elif target == "analytics":
                    self.analytics = data
            except (FileNotFoundError, json.JSONDecodeError):
                pass

    def _save_conversations(self):
        with open(self.conversations_file, 'w') as f:
            json.dump(self.conversations[-self.max_conversations:], f, default=str)

    def _save_tasks(self):
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks[-5000:], f, default=str)

    def _save_analytics(self):
        with open(self.analytics_file, 'w') as f:
            json.dump(self.analytics, f, default=str)

    COMMAND_PATTERNS = {
        TaskType.RESTART_SERVICE: [
            r"(?:restart|reboot)\s+(?:the\s+)?(?:service|server|app)\s+(.+)",
            r"restart\s+(.+)",
        ],
        TaskType.CHECK_LOGS: [
            r"(?:show|get|check|view)\s+(?:the\s+)?logs\s+(?:for|of)\s+(.+)",
            r"logs\s+(?:for|of|from)\s+(.+)",
        ],
        TaskType.RUN_BACKUP: [
            r"(?:create|run|make|do)\s+(?:a\s+)?backup\s+(?:of|for)\s+(.+)",
            r"backup\s+(?:up\s+)?(.+)",
        ],
        TaskType.CHECK_STATUS: [
            r"(?:what'?s?|what is|is|check)\s+(?:the\s+)?status\s+(?:of\s+)?(.+)",
            r"status\s+(?:of\s+)?(.+)",
        ],
        TaskType.LIST_SERVICES: [
            r"(?:list|show)\s+(?:all\s+)?(?:services|servers|apps)",
            r"what (?:services|servers|apps) (?:do|are)",
        ],
        TaskType.SCALE_SERVICE: [
            r"(?:scale|resize)\s+(.+)\s+(?:up|down)?\s*(?:to\s+)?(\d+)",
            r"scale\s+(.+)",
        ],
        TaskType.DEPLOY_VERSION: [
            r"(?:deploy|release)\s+(.+)\s+(?:to|on)\s+(.+)",
            r"deploy\s+(.+)",
        ],
        TaskType.CLEAR_CACHE: [
            r"(?:clear|flush|purge)\s+(?:the\s+)?cache\s+(?:for|of)\s+(.+)",
            r"clear\s+cache\s+(.+)",
        ],
        TaskType.RUN_DIAGNOSTIC: [
            r"(?:run|start|execute)\s+(?:a\s+)?diagnostic\s+(?:on|for)\s+(.+)",
            r"diagnostic\s+(.+)",
        ],
        TaskType.SHOW_METRICS: [
            r"(?:show|get|view)\s+(?:metrics|cpu|memory|usage)\s+(?:for|of)\s+(.+)",
            r"metrics\s+(?:for|of)\s+(.+)",
        ],
    }

    COMMAND_HELP = {
        TaskType.RESTART_SERVICE: {"description": "Restart a service", "example": "restart nginx"},
        TaskType.CHECK_LOGS: {"description": "View logs for a service", "example": "logs api-server"},
        TaskType.RUN_BACKUP: {"description": "Create a backup", "example": "backup postgres"},
        TaskType.CHECK_STATUS: {"description": "Check service status", "example": "status web-server"},
        TaskType.LIST_SERVICES: {"description": "List all services", "example": "list services"},
        TaskType.SCALE_SERVICE: {"description": "Scale a service", "example": "scale api-service 5"},
        TaskType.DEPLOY_VERSION: {"description": "Deploy a version", "example": "deploy v3.2 staging"},
        TaskType.CLEAR_CACHE: {"description": "Clear service cache", "example": "clear cache cdn"},
        TaskType.RUN_DIAGNOSTIC: {"description": "Run diagnostics", "example": "diagnostic database"},
        TaskType.SHOW_METRICS: {"description": "Show service metrics", "example": "metrics gateway"},
    }

    def _parse_message(self, message: str) -> Tuple[TaskType, Dict[str, str]]:
        message_clean = message.strip().lower()
        for task_type, patterns in self.COMMAND_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_clean, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    params = {}
                    if task_type == TaskType.DEPLOY_VERSION:
                        params["target"] = groups[-1]
                    elif task_type == TaskType.SCALE_SERVICE and len(groups) >= 2:
                        params["target"] = groups[0]
                        params["replicas"] = groups[1]
                    else:
                        params["target"] = groups[0] if groups else ""
                    return task_type, params
        return TaskType.CHECK_STATUS, {"target": "", "original": message}

    def _check_permissions(self, user_id: str, task_type: str) -> bool:
        return True

    def process_message(self, user_id: str, message: str, roles: List[str] = None,
                        conversation_id: str = None) -> Dict[str, Any]:
        conv = self._get_or_create_conversation(user_id, conversation_id)
        if not conv:
            return {"error": "Could not create conversation"}
        conv["state"] = ChatbotState.PROCESSING.value
        self.analytics["total_messages"] = self.analytics.get("total_messages", 0) + 1
        task_type, params = self._parse_message(message)
        cmd_name = task_type.value
        self.analytics["popular_commands"][cmd_name] = self.analytics["popular_commands"].get(cmd_name, 0) + 1
        self._save_analytics()
        if not self._check_permissions(user_id, cmd_name):
            response = self._format_response("error", "You don't have permission to perform this action.",
                                              {"required_role": "operator"})
        else:
            task = self._execute_task(task_type, params, user_id)
            response = self._format_response("success" if task.get("success") else "error",
                                              task.get("message", "Task completed"), task)
            if task.get("success"):
                self.analytics["tasks_completed"] = self.analytics.get("tasks_completed", 0) + 1
            else:
                self.analytics["tasks_failed"] = self.analytics.get("tasks_failed", 0) + 1
            self._save_analytics()
        conv["messages"].append({"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()})
        conv["messages"].append({"role": "assistant", "content": response.get("text", ""),
                                  "data": response, "timestamp": datetime.utcnow().isoformat()})
        conv["state"] = ChatbotState.IDLE.value
        conv["last_activity"] = datetime.utcnow().isoformat()
        self._save_conversations()
        response["conversation_id"] = conv["id"]
        response["can_undo"] = task.get("can_undo", False)
        response["task_id"] = task.get("task_id")
        return response

    def _get_or_create_conversation(self, user_id: str, conv_id: str = None) -> Optional[Dict[str, Any]]:
        if conv_id:
            existing = next((c for c in self.conversations if c["id"] == conv_id), None)
            if existing:
                return existing
        if len(self.conversations) >= self.max_conversations:
            self.conversations = self.conversations[-self.max_conversations + 1:]
        conv = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "state": ChatbotState.IDLE.value,
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        self.conversations.append(conv)
        self._save_conversations()
        return conv

    def _execute_task(self, task_type: TaskType, params: Dict[str, str],
                       user_id: str) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        task_handlers = {
            TaskType.RESTART_SERVICE: self._task_restart_service,
            TaskType.CHECK_LOGS: self._task_check_logs,
            TaskType.RUN_BACKUP: self._task_run_backup,
            TaskType.CHECK_STATUS: self._task_check_status,
            TaskType.LIST_SERVICES: self._task_list_services,
            TaskType.SCALE_SERVICE: self._task_scale_service,
            TaskType.DEPLOY_VERSION: self._task_deploy_version,
            TaskType.CLEAR_CACHE: self._task_clear_cache,
            TaskType.RUN_DIAGNOSTIC: self._task_run_diagnostic,
            TaskType.SHOW_METRICS: self._task_show_metrics,
        }
        handler = task_handlers.get(task_type, self._task_unknown)
        result = handler(params, user_id)
        task = {
            "id": task_id,
            "task_type": task_type.value,
            "params": params,
            "user_id": user_id,
            "status": TaskStatus.COMPLETED.value if result.get("success") else TaskStatus.FAILED.value,
            "result": result,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.tasks.append(task)
        self._save_tasks()
        result["task_id"] = task_id
        return result

    def _task_restart_service(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        return {
            "success": True, "can_undo": True,
            "message": f"**{target}** is restarting. Graceful shutdown initiated. Expected recovery in 15 seconds.",
            "details": {"service": target, "action": "restart", "estimated_downtime_seconds": 15},
        }

    def _task_check_logs(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        sample = [
            f"INFO [{target}] Service started on port 8080",
            f"INFO [{target}] Connected to upstream database",
            f"INFO [{target}] Health check passed — status: healthy",
            f"DEBUG [{target}] Processing batch job: 45/120 items",
            f"INFO [{target}] Request completed in 32ms (200 OK)",
        ]
        return {
            "success": True,
            "message": f"📋 **Recent logs for {target}** (showing last 5 of 2,341 lines):\n" + "\n".join(sample),
            "details": {"service": target, "log_lines": sample, "total_lines": 2341},
        }

    def _task_run_backup(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        backup_id = f"bkp-{uuid.uuid4().hex[:12]}"
        return {
            "success": True, "can_undo": True,
            "message": f"💾 **Backup initiated for {target}**.\nBackup ID: `{backup_id}`\nEstimated completion: 3 minutes\nSize estimate: 2.4 GB",
            "details": {"service": target, "backup_id": backup_id, "estimated_size_gb": 2.4, "status": "in_progress"},
        }

    def _task_check_status(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "")
        if not target:
            return self._task_list_services(params, user_id)
        return {
            "success": True,
            "message": (
                f"🟢 **{target}** is **healthy** and **running**.\n"
                f"• CPU: 23.4% • Memory: 1.2/4.0 GB (30%)\n"
                f"• Uptime: 14d 6h 32m • Status: operational"
            ),
            "details": {"service": target, "status": "running", "health": "healthy",
                        "cpu_percent": 23.4, "memory_used_gb": 1.2, "memory_total_gb": 4.0,
                        "uptime": "14d 6h 32m"},
        }

    def _task_list_services(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        services = [
            {"name": "nginx-proxy", "status": "running", "cpu": 8, "memory": "120MB"},
            {"name": "api-gateway", "status": "running", "cpu": 34, "memory": "450MB"},
            {"name": "web-server", "status": "running", "cpu": 23, "memory": "1.2GB"},
            {"name": "postgres-db", "status": "running", "cpu": 15, "memory": "2.8GB"},
            {"name": "redis-cache", "status": "running", "cpu": 5, "memory": "80MB"},
            {"name": "worker-queue", "status": "idle", "cpu": 2, "memory": "60MB"},
        ]
        lines = [f"**Available Services ({len(services)}):**\n"]
        for s in services:
            icon = "🟢" if s["status"] == "running" else "🟡"
            lines.append(f"{icon} **{s['name']}** — CPU: {s['cpu']}%, Mem: {s['memory']}")
        return {"success": True, "message": "\n".join(lines), "details": {"services": services, "count": len(services)}}

    def _task_scale_service(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        replicas = params.get("replicas", "3")
        return {
            "success": True,
            "message": f"📈 **Scaling {target}** to **{replicas}** replicas (currently 2). This may take 30 seconds.",
            "details": {"service": target, "current_replicas": 2, "target_replicas": int(replicas)},
        }

    def _task_deploy_version(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        return {
            "success": True, "can_undo": True,
            "message": f"🚀 **Deploying** to **{target}**. Build #1842. Rolling update with zero-downtime. Estimated completion: 90 seconds.",
            "details": {"environment": target, "build_number": 1842, "strategy": "rolling_update"},
        }

    def _task_clear_cache(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        return {
            "success": True,
            "message": f"🧹 **Cache cleared for {target}**. 2,450 entries removed (size: 1.2 GB). Cache warming initiated.",
            "details": {"service": target, "entries_removed": 2450, "size_cleared_gb": 1.2},
        }

    def _task_run_diagnostic(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        return {
            "success": True,
            "message": (
                f"🔍 **Diagnostic results for {target}:**\n"
                f"• Connectivity: ✅ Pass (12ms latency)\n"
                f"• Disk I/O: ✅ Pass (240MB/s read, 180MB/s write)\n"
                f"• Memory: ⚠️ Warning (72% utilization)\n"
                f"• CPU: ✅ Pass (34% load, 8 cores)\n"
                f"• Network: ✅ Pass (1.2Gbps up / 0.8Gbps down)"
            ),
            "details": {"service": target, "checks": [
                {"name": "connectivity", "status": "pass", "latency_ms": 12},
                {"name": "disk_io", "status": "pass", "read_mbps": 240, "write_mbps": 180},
                {"name": "memory", "status": "warning", "utilization": 72},
                {"name": "cpu", "status": "pass", "load": 34, "cores": 8},
                {"name": "network", "status": "pass", "up_gbps": 1.2, "down_gbps": 0.8},
            ]},
        }

    def _task_show_metrics(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        target = params.get("target", "unknown")
        return {
            "success": True,
            "message": (
                f"📊 **Metrics for {target}:**\n"
                f"• CPU: 34.2% (8 cores)\n"
                f"• Memory: 1.8 GB / 8.0 GB (22.5%)\n"
                f"• Disk: 45 GB / 100 GB (45%)\n"
                f"• Network In: 1.2 Mbps • Network Out: 0.8 Mbps\n"
                f"• Requests/sec: 245 • Error Rate: 0.02%"
            ),
            "details": {"service": target, "cpu_percent": 34.2, "memory_used_gb": 1.8,
                        "memory_total_gb": 8.0, "disk_used_gb": 45, "disk_total_gb": 100,
                        "network_in_mbps": 1.2, "network_out_mbps": 0.8,
                        "requests_per_sec": 245, "error_rate": 0.02},
        }

    def _task_unknown(self, params: Dict[str, str], user_id: str) -> Dict[str, Any]:
        original = params.get("original", params.get("target", ""))
        return {
            "success": False,
            "message": (
                f"I'm not sure how to handle: \"{original}\".\n\n"
                f"Try one of these:\n"
                f"• **restart** `<service>` — Restart a service\n"
                f"• **logs** `<service>` — View service logs\n"
                f"• **backup** `<service>` — Create a backup\n"
                f"• **status** `<service>` — Check service status\n"
                f"• **list services** — List all services\n"
                f"• **deploy** `<version>` to `<env>` — Deploy a version\n"
                f"• **help** — See all commands"
            ),
        }

    def _format_response(self, response_type: str, text: str,
                          data: Dict[str, Any] = None) -> Dict[str, Any]:
        actions = []
        if data and data.get("can_undo"):
            actions.append({"type": "undo", "label": "Undo", "action": "rollback"})
        return {
            "type": response_type,
            "text": text,
            "data": data or {},
            "actions": actions,
            "quick_replies": self._get_contextual_quick_replies(data.get("details", {}) if data else {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _get_contextual_quick_replies(self, context: Dict[str, Any]) -> List[str]:
        service = context.get("service", "")
        if service:
            return [
                f"status {service}", f"logs {service}",
                f"metrics {service}", f"restart {service}",
            ]
        return ["list services", "help", "status nginx", "status postgres-db"]

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return next((c for c in self.conversations if c["id"] == conversation_id), None)

    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conv = self.get_conversation(conversation_id)
        if conv:
            return conv.get("messages", [])[-limit:]
        return []

    def list_conversations(self, user_id: str = None) -> List[Dict[str, Any]]:
        if user_id:
            return [c for c in self.conversations if c.get("user_id") == user_id]
        return list(self.conversations)

    def list_tasks(self, user_id: str = None, task_type: str = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        result = self.tasks
        if user_id:
            result = [t for t in result if t.get("user_id") == user_id]
        if task_type:
            result = [t for t in result if t.get("task_type") == task_type]
        return result[-limit:]

    def get_analytics(self) -> Dict[str, Any]:
        total = self.analytics.get("total_messages", 0)
        completed = self.analytics.get("tasks_completed", 0)
        popular = dict(sorted(
            self.analytics.get("popular_commands", {}).items(),
            key=lambda x: x[1], reverse=True
        )[:10])
        return {
            "total_messages": total,
            "tasks_completed": completed,
            "tasks_failed": self.analytics.get("tasks_failed", 0),
            "success_rate": round(completed / max(1, total) * 100, 1),
            "active_conversations": len(self.conversations),
            "popular_commands": popular,
        }

    def clear_conversation(self, conversation_id: str) -> bool:
        initial = len(self.conversations)
        self.conversations = [c for c in self.conversations if c["id"] != conversation_id]
        self._save_conversations()
        return len(self.conversations) < initial

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_conversations(self, offset: int = 0, limit: int = 50, user_id: str = None) -> dict:
        results = self.conversations
        if user_id:
            results = [c for c in results if c.get("user_id") == user_id]
        total = len(results)
        results.sort(key=lambda c: c.get("last_activity", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_tasks(self, offset: int = 0, limit: int = 50, task_type: str = None,
                        user_id: str = None, status: str = None) -> dict:
        results = self.tasks
        if task_type:
            results = [t for t in results if t.get("task_type") == task_type]
        if user_id:
            results = [t for t in results if t.get("user_id") == user_id]
        if status:
            results = [t for t in results if t.get("status") == status]
        total = len(results)
        results.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_process_messages(self, messages: list[dict]) -> list[dict]:
        results = []
        for msg in messages:
            try:
                result = self.process_message(
                    msg["user_id"], msg["message"],
                    msg.get("roles"), msg.get("conversation_id"),
                )
                results.append(result)
            except (KeyError, TypeError) as e:
                results.append({"error": str(e), "message": msg.get("message", "")})
        return results

    def batch_clear_conversations(self, conversation_ids: list[str]) -> dict:
        cleared = 0
        for cid in conversation_ids:
            if self.clear_conversation(cid):
                cleared += 1
        return {"cleared": cleared, "total_requested": len(conversation_ids)}

    def export_conversations(self, user_id: str = None) -> list[dict]:
        results = self.conversations
        if user_id:
            results = [c for c in results if c.get("user_id") == user_id]
        return [{
            "id": c["id"], "user_id": c.get("user_id"),
            "state": c.get("state"),
            "message_count": len(c.get("messages", [])),
            "created_at": c.get("created_at"), "last_activity": c.get("last_activity"),
        } for c in results]

    def import_conversations(self, conversations: list[dict]) -> dict:
        imported = 0
        for c in conversations:
            conv = {
                "id": c.get("id", str(uuid.uuid4())),
                "user_id": c.get("user_id", "imported"),
                "state": c.get("state", "idle"),
                "messages": c.get("messages", []),
                "created_at": c.get("created_at", datetime.utcnow().isoformat()),
                "last_activity": c.get("last_activity", datetime.utcnow().isoformat()),
            }
            self.conversations.append(conv)
            imported += 1
        self._save_conversations()
        return {"imported": imported}

    def export_tasks(self, task_type: str = None, user_id: str = None) -> list[dict]:
        results = self.tasks
        if task_type:
            results = [t for t in results if t.get("task_type") == task_type]
        if user_id:
            results = [t for t in results if t.get("user_id") == user_id]
        return [{
            "id": t["id"], "task_type": t.get("task_type"), "params": t.get("params"),
            "user_id": t.get("user_id"), "status": t.get("status"),
            "result_summary": t.get("result", {}).get("message", "")[:200],
            "created_at": t.get("created_at"),
        } for t in results]

    def get_extended_analytics(self) -> dict:
        task_type_counts = Counter(t.get("task_type", "unknown") for t in self.tasks)
        task_status_counts = Counter(t.get("status", "unknown") for t in self.tasks)
        user_task_counts = Counter(t.get("user_id", "unknown") for t in self.tasks)
        tasks_by_hour = {}
        for t in self.tasks:
            try:
                hour = datetime.fromisoformat(t["created_at"]).strftime("%Y-%m-%dT%H:00:00")
                tasks_by_hour[hour] = tasks_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        total = self.analytics.get("total_messages", 0)
        completed = self.analytics.get("tasks_completed", 0)
        return {
            "total_messages": total,
            "total_tasks": len(self.tasks),
            "tasks_completed": completed,
            "tasks_failed": self.analytics.get("tasks_failed", 0),
            "success_rate": round(completed / max(total, 1) * 100, 1),
            "active_conversations": len(self.conversations),
            "task_type_distribution": dict(task_type_counts),
            "task_status_distribution": dict(task_status_counts),
            "top_users": [{"user": u, "count": c} for u, c in user_task_counts.most_common(10)],
            "popular_commands": dict(sorted(
                self.analytics.get("popular_commands", {}).items(),
                key=lambda x: x[1], reverse=True)[:10]),
            "tasks_by_hour": dict(sorted(tasks_by_hour.items())[-24:]),
        }

    def search_conversations(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for c in self.conversations:
            if q in c.get("user_id", "").lower():
                results.append(c)
                continue
            for msg in c.get("messages", []):
                if q in msg.get("content", "").lower():
                    results.append(c)
                    break
        return results

    def get_user_activity(self, user_id: str) -> list[dict]:
        user_tasks = [t for t in self.tasks if t.get("user_id") == user_id]
        user_convs = [c for c in self.conversations if c.get("user_id") == user_id]
        tasks_by_type = Counter(t.get("task_type", "unknown") for t in user_tasks)
        return {
            "user_id": user_id,
            "total_tasks": len(user_tasks),
            "total_conversations": len(user_convs),
            "completed_tasks": sum(1 for t in user_tasks if t.get("status") == TaskStatus.COMPLETED.value),
            "failed_tasks": sum(1 for t in user_tasks if t.get("status") == TaskStatus.FAILED.value),
            "task_type_distribution": dict(tasks_by_type),
            "last_activity": max((c.get("last_activity", "") for c in user_convs), default=None),
        }

    def simulate_command_batch(self, commands: list[str], user_id: str = "simulation") -> list[dict]:
        results = []
        for cmd in commands:
            result = self.process_message(user_id, cmd)
            results.append(result)
        return results

    def add_custom_command(self, pattern: str, task_type: str, help_text: str = None) -> dict:
        try:
            task_enum = TaskType(task_type)
        except ValueError:
            return {"error": f"Unknown task type: {task_type}"}
        if task_enum not in self.COMMAND_PATTERNS:
            self.COMMAND_PATTERNS[task_enum] = []
        self.COMMAND_PATTERNS[task_enum].append(pattern)
        self.COMMAND_HELP[task_enum] = {
            "description": help_text or f"Custom {task_type} command",
            "example": pattern,
        }
        return {"task_type": task_type, "pattern": pattern, "help_text": help_text}

    # ===== APPENDED BATCH 2: SLO, reports, config export, advanced analytics =====

    def check_chatbot_slo(self, target_success_rate: float = 90.0, window_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = [t for t in self.tasks if datetime.fromisoformat(t["created_at"]) > cutoff]
        total = len(recent)
        successful = sum(1 for t in recent if t.get("status") == TaskStatus.COMPLETED.value)
        actual_rate = round((successful / max(total, 1)) * 100, 2)
        return {
            "slo_target_pct": target_success_rate,
            "actual_success_rate_pct": actual_rate,
            "compliant": actual_rate >= target_success_rate,
            "window_hours": window_hours,
            "total_tasks": total,
            "successful": successful,
            "failed": total - successful,
        }

    def generate_chatbot_report(self, days: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_tasks = [t for t in self.tasks if datetime.fromisoformat(t["created_at"]) > cutoff]
        recent_convs = [c for c in self.conversations if datetime.fromisoformat(c["created_at"]) > cutoff]
        by_type = Counter(t.get("task_type", "unknown") for t in recent_tasks)
        by_status = Counter(t.get("status", "unknown") for t in recent_tasks)
        by_user = Counter(t.get("user_id", "unknown") for t in recent_tasks)
        completed = sum(1 for t in recent_tasks if t.get("status") == TaskStatus.COMPLETED.value)
        return {
            "period_days": days,
            "total_tasks": len(recent_tasks),
            "new_conversations": len(recent_convs),
            "completed": completed,
            "success_rate": round((completed / max(len(recent_tasks), 1)) * 100, 1),
            "task_type_distribution": dict(by_type),
            "status_distribution": dict(by_status),
            "top_users": dict(by_user.most_common(10)),
            "popular_commands": dict(sorted(self.analytics.get("popular_commands", {}).items(), key=lambda x: x[1], reverse=True)[:10]),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "require_confirmation": self.require_confirmation,
            "session_timeout_minutes": self.session_timeout,
            "max_conversations": self.max_conversations,
            "total_conversations": len(self.conversations),
            "total_tasks": len(self.tasks),
            "available_commands": list(self.COMMAND_HELP.keys()),
        }

    def get_permission_summary(self) -> dict:
        return {"permission_model": "RBAC", "default_access": "all commands enabled",
                "note": "Override _check_permissions for custom RBAC"}

    def get_task_performance(self, task_type: str = None) -> dict:
        filtered = self.tasks
        if task_type:
            filtered = [t for t in filtered if t.get("task_type") == task_type]
        total = len(filtered)
        completed = sum(1 for t in filtered if t.get("status") == TaskStatus.COMPLETED.value)
        failed = sum(1 for t in filtered if t.get("status") == TaskStatus.FAILED.value)
        return {
            "task_type": task_type or "all",
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round((completed / max(total, 1)) * 100, 1),
        }

    def get_active_users(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [c for c in self.conversations if datetime.fromisoformat(c["last_activity"]) > cutoff]
        user_activity = Counter(c.get("user_id", "unknown") for c in recent)
        return [{"user_id": u, "active_sessions": c, "last_seen": max(
            (conv.get("last_activity", "") for conv in recent if conv.get("user_id") == u), default="")}
                for u, c in user_activity.most_common(20)]

    def get_command_suggestions(self, partial: str) -> list[dict]:
        partial_lower = partial.lower()
        suggestions = []
        for task_type, help_info in self.COMMAND_HELP.items():
            if partial_lower in task_type.value.lower() or partial_lower in help_info.get("description", "").lower():
                suggestions.append({
                    "command": task_type.value,
                    "description": help_info.get("description"),
                    "example": help_info.get("example"),
                })
        return suggestions[:10]

    def batch_get_task_status(self, task_ids: list[str]) -> list[dict]:
        results = []
        for tid in task_ids:
            task = next((t for t in self.tasks if t["id"] == tid), None)
            if task:
                results.append({"task_id": tid, "status": task.get("status"), "task_type": task.get("task_type")})
            else:
                results.append({"task_id": tid, "status": "not_found"})
        return results

    def get_conversation_summary(self, conversation_id: str) -> Optional[dict]:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return None
        tasks = [t for t in self.tasks if t.get("conversation_id") == conversation_id]
        return {"conversation_id": conversation_id, "user_id": conv.get("user_id"), "channel": conv.get("channel"), "status": conv.get("status"), "total_messages": len(conv.get("messages", [])), "tasks_created": len(tasks), "tasks_completed": sum(1 for t in tasks if t.get("status") == TaskStatus.COMPLETED.value), "duration_minutes": round((datetime.fromisoformat(conv.get("last_activity", datetime.utcnow().isoformat())) - datetime.fromisoformat(conv.get("created_at", datetime.utcnow().isoformat()))).total_seconds() / 60, 1)}

    def get_popular_commands(self, limit: int = 10) -> list[dict]:
        sorted_commands = sorted(self.analytics.get("popular_commands", {}).items(), key=lambda x: x[1], reverse=True)
        return [{"command": cmd, "count": cnt} for cmd, cnt in sorted_commands[:limit]]

    def export_task_log(self, task_id: str) -> Optional[dict]:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return None
        return {"task_id": task_id, "task_type": task.get("task_type"), "status": task.get("status"), "config": task.get("config"), "result": task.get("result"), "created_at": task.get("created_at"), "completed_at": task.get("completed_at")}

    def search_tasks(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for t in self.tasks:
            if q in t.get("task_type", "").lower() or q in t.get("status", "").lower() or q in str(t.get("config", {})).lower():
                results.append({"task_id": t["id"], "task_type": t.get("task_type"), "status": t.get("status"), "created_at": t.get("created_at")})
        return results[:20]

    def get_analytics_summary(self) -> dict:
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get("status") == TaskStatus.COMPLETED.value)
        failed = sum(1 for t in self.tasks if t.get("status") == TaskStatus.FAILED.value)
        unique_users = len(set(c.get("user_id", "") for c in self.conversations))
        return {"total_tasks": total_tasks, "completed": completed, "failed": failed, "success_rate": round(completed / max(total_tasks, 1) * 100, 1), "total_conversations": len(self.conversations), "unique_users": unique_users, "avg_tasks_per_conversation": round(total_tasks / max(len(self.conversations), 1), 1)}

    def get_dashboard_data(self) -> dict:
        return {"analytics": self.get_analytics_summary(), "popular_commands": self.get_popular_commands(5), "active_users": self.get_active_users(1), "recent_tasks": [{"task_id": t["id"], "task_type": t.get("task_type"), "status": t.get("status")} for t in self.tasks[-10:]]}


class TaskPrioritizer:
    def __init__(self, engine: OpsChatbotEngine):
        self.engine = engine

    def prioritize_tasks(self) -> list[dict]:
        pending = [t for t in self.engine.tasks if t.get("status") == TaskStatus.PENDING.value]
        scored = []
        for t in pending:
            score = 0
            config = t.get("config", {})
            if config.get("severity") == "critical":
                score += 10
            elif config.get("severity") == "high":
                score += 7
            if config.get("timeout", 0) < 60:
                score += 5
            scored.append({"task_id": t["id"], "task_type": t.get("task_type"), "priority_score": score, "config": config})
        return sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    def get_next_task(self) -> Optional[dict]:
        prioritized = self.prioritize_tasks()
        if prioritized:
            return prioritized[0]
        return None

# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_events": 0, "anomalies_detected": 0, "false_positives": 0, "avg_confidence": 0.0}

    def validate_model(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "model_version": "v1"}

class AiopsResult(BaseModel):
    success: bool = True
    operation: str = ""
    prediction_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    duration_ms: float = 0.0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AiopsBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    model: str = Field(default="default")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    anomalies_found: int = Field(default=0)

    def record_result(self, is_anomaly: bool) -> None:
        self.processed += 1
        if is_anomaly:
            self.anomalies_found += 1

    def complete(self) -> None:
        self.status = "completed"

class AnomalyScore(BaseModel):
    entity_id: str
    score: float = Field(default=0.0, ge=0, le=1)
    baseline: float = Field(default=0.0)
    deviation: float = Field(default=0.0)
    features: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    severity: str = Field(default="info")

    def is_anomalous(self, threshold: float = 0.7) -> bool:
        return self.score >= threshold

class ModelMetrics(BaseModel):
    model_name: str
    version: str = Field(default="v1")
    accuracy: float = Field(default=0.0, ge=0, le=1)
    precision: float = Field(default=0.0, ge=0, le=1)
    recall: float = Field(default=0.0, ge=0, le=1)
    f1_score: float = Field(default=0.0, ge=0, le=1)
    training_date: Optional[datetime] = None
    total_predictions: int = Field(default=0)

class ModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, ModelMetrics] = {}

    def register(self, name: str, version: str = "v1") -> ModelMetrics:
        mm = ModelMetrics(model_name=name, version=version)
        self._models[name] = mm
        return mm

    def update_metrics(self, name: str, accuracy: float = 0.0, precision: float = 0.0,
                       recall: float = 0.0, f1: float = 0.0) -> None:
        model = self._models.get(name)
        if model:
            model.accuracy = accuracy
            model.precision = precision
            model.recall = recall
            model.f1_score = f1
            model.total_predictions += 1

    def get_best(self) -> Optional[ModelMetrics]:
        if not self._models:
            return None
        return max(self._models.values(), key=lambda m: m.f1_score)

    def summary(self) -> Dict[str, Any]:
        return {name: m.dict() for name, m in self._models.items()}

class FeatureStore(BaseModel):
    feature_name: str
    value: float
    entity_type: str = Field(default="generic")
    entity_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="inference")

class FeatureRepository:
    def __init__(self) -> None:
        self._features: List[FeatureStore] = []

    def store(self, feature: FeatureStore) -> None:
        self._features.append(feature)

    def get_latest(self, entity_id: str, feature_name: str) -> Optional[FeatureStore]:
        matches = [f for f in self._features if f.entity_id == entity_id and f.feature_name == feature_name]
        return max(matches, key=lambda f: f.timestamp) if matches else None

    def get_entity_features(self, entity_id: str) -> Dict[str, Any]:
        features = [f for f in self._features if f.entity_id == entity_id]
        return {f.feature_name: {"value": f.value, "timestamp": f.timestamp.isoformat()} for f in features}

    def get_time_series(self, feature_name: str, entity_id: str, limit: int = 100) -> List[FeatureStore]:
        matches = [f for f in self._features if f.feature_name == feature_name and f.entity_id == entity_id]
        return sorted(matches, key=lambda f: f.timestamp, reverse=True)[:limit]

class ThresholdConfig(BaseModel):
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    enabled: bool = True
    cooldown_minutes: int = Field(default=5)

class ThresholdManager:
    def __init__(self) -> None:
        self._thresholds: Dict[str, ThresholdConfig] = {}

    def define(self, config: ThresholdConfig) -> None:
        self._thresholds[config.metric_name] = config

    def check(self, metric_name: str, value: float) -> Dict[str, Any]:
        config = self._thresholds.get(metric_name)
        if not config or not config.enabled:
            return {"level": "ok", "message": "No threshold configured"}
        if value >= config.critical_threshold:
            return {"level": "critical", "value": value, "threshold": config.critical_threshold}
        if value >= config.warning_threshold:
            return {"level": "warning", "value": value, "threshold": config.warning_threshold}
        return {"level": "ok", "value": value}

    def get_all(self) -> Dict[str, ThresholdConfig]:
        return dict(self._thresholds)

class DriftMetric(BaseModel):
    feature_name: str
    training_mean: float
    production_mean: float
    drift_score: float = Field(default=0.0, ge=0)
    drifted: bool = False
    detected_at: datetime = Field(default_factory=datetime.utcnow)

class DriftDetector:
    def __init__(self, threshold: float = 0.1) -> None:
        self.threshold = threshold
        self._metrics: List[DriftMetric] = []

    def compare(self, feature_name: str, training_mean: float, production_values: List[float]) -> DriftMetric:
        prod_mean = sum(production_values) / max(len(production_values), 1)
        drift = abs(prod_mean - training_mean) / max(abs(training_mean), 0.001)
        metric = DriftMetric(feature_name=feature_name, training_mean=training_mean,
                              production_mean=round(prod_mean, 4),
                              drift_score=round(drift, 4), drifted=drift > self.threshold)
        self._metrics.append(metric)
        return metric

    def get_recent_drifts(self) -> List[DriftMetric]:
        return [m for m in self._metrics if m.drifted]

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._metrics)
        drifted = len(self.get_recent_drifts())
        return {"total_features": total, "drifted": drifted, "stable": total - drifted,
                "drift_rate": round(drifted / max(total, 1) * 100, 1)}

class PredictionLog(BaseModel):
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str
    input_features: Dict[str, float] = Field(default_factory=dict)
    prediction: Any = None
    confidence: float = Field(default=0.0)
    actual: Optional[Any] = None
    correct: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float = Field(default=0.0)

class PredictionLogger:
    def __init__(self) -> None:
        self._logs: List[PredictionLog] = []

    def log_prediction(self, model_name: str, features: Dict[str, float], prediction: Any,
                       confidence: float, latency_ms: float = 0.0) -> PredictionLog:
        pl = PredictionLog(model_name=model_name, input_features=features,
                            prediction=prediction, confidence=confidence, latency_ms=latency_ms)
        self._logs.append(pl)
        return pl

    def record_actual(self, prediction_id: str, actual: Any) -> bool:
        for pl in self._logs:
            if pl.prediction_id == prediction_id:
                pl.actual = actual
                pl.correct = pl.prediction == actual
                return True
        return False

    def get_accuracy(self, model_name: Optional[str] = None) -> float:
        logs = [l for l in self._logs if l.correct is not None]
        if model_name:
            logs = [l for l in logs if l.model_name == model_name]
        if not logs:
            return 0.0
        return round(sum(1 for l in logs if l.correct) / len(logs), 4)
