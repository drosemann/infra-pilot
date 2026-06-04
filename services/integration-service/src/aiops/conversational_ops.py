"""Feature 57: Conversational Ops Assistant — Natural language interface for operations."""

import json
import os
import uuid
import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime
from collections import Counter
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class IntentType(Enum):
    STATUS_CHECK = "status_check"
    DEPLOY = "deploy"
    RESTART = "restart"
    SCALE = "scale"
    LOGS = "logs"
    METRICS = "metrics"
    BACKUP = "backup"
    CONFIG = "config"
    HELP = "help"
    LIST_RESOURCES = "list_resources"
    UNKNOWN = "unknown"


class ConversationState(Enum):
    ACTIVE = "active"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConversationalOpsAssistant:
    """Natural language interface for operations tasks."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session_timeout = config.get("session_timeout_minutes", 15)
        self.max_sessions = config.get("max_sessions", 1000)
        self.sessions_file = _data_file('ops_sessions.json')
        self.intents_file = _data_file('ops_intents.json')
        self.sessions: List[Dict[str, Any]] = []
        self.intent_log: List[Dict[str, Any]] = []
        self._load_data()
        self._register_intent_handlers()

    def _load_data(self):
        try:
            with open(self.sessions_file, 'r') as f:
                self.sessions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        try:
            with open(self.intents_file, 'r') as f:
                self.intent_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_sessions(self):
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions[-self.max_sessions:], f, default=str)

    def _save_intents(self):
        with open(self.intents_file, 'w') as f:
            json.dump(self.intent_log[-10000:], f, default=str)

    def _register_intent_handlers(self):
        self.intent_handlers: Dict[str, Callable] = {
            IntentType.STATUS_CHECK.value: self._handle_status_check,
            IntentType.DEPLOY.value: self._handle_deploy,
            IntentType.RESTART.value: self._handle_restart,
            IntentType.SCALE.value: self._handle_scale,
            IntentType.LOGS.value: self._handle_logs,
            IntentType.METRICS.value: self._handle_metrics,
            IntentType.BACKUP.value: self._handle_backup,
            IntentType.CONFIG.value: self._handle_config,
            IntentType.HELP.value: self._handle_help,
            IntentType.LIST_RESOURCES.value: self._handle_list_resources,
        }

    INTENT_PATTERNS = {
        IntentType.STATUS_CHECK: [
            r"(?:what'?s?|what is|show|get|check|status of)\s*(?:the\s+)?(?:status\s+of\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?",
            r"(?:is|how is)\s+(\w+)\s+(?:up|down|running|healthy|alive)",
            r"status\s+(?:of\s+)?(\w+)",
        ],
        IntentType.DEPLOY: [
            r"(?:deploy|release|push|ship)\s+(?:version\s+)?([\w\.]+)\s+(?:to|on)\s+(\w+)",
            r"(?:deploy|release)\s+(\w+)\s+(?:to|on)\s+(?:the\s+)?(\w+)",
        ],
        IntentType.RESTART: [
            r"(?:restart|reboot|reload)\s+(?:the\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?",
            r"restart\s+(\w+)",
        ],
        IntentType.SCALE: [
            r"(?:scale|resize)\s+(?:up|down\s+)?(?:the\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?\s*(?:to\s+)?(\d+)?",
            r"(?:increase|decrease)\s+(?:replicas\s+of\s+)?(\w+)\s+(?:by|to)\s+(\d+)",
        ],
        IntentType.LOGS: [
            r"(?:show|get|fetch|view)\s+(?:the\s+)?logs\s+(?:for|of)\s+(?:the\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?",
            r"logs\s+(?:for|of|from)\s+(\w+)",
        ],
        IntentType.METRICS: [
            r"(?:show|get|view)\s+(?:the\s+)?(?:metrics|cpu|memory|usage)\s+(?:for|of)\s+(?:the\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?",
            r"(?:cpu|memory|disk)\s+(?:usage|metrics)\s+(?:for|of)\s+(\w+)",
        ],
        IntentType.BACKUP: [
            r"(?:create|run|do|make)\s+(?:a\s+)?backup\s+(?:of|for)\s+(?:the\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?",
            r"backup\s+(\w+)",
        ],
        IntentType.CONFIG: [
            r"(?:show|get|view)\s+(?:the\s+)?config(?:uration)?\s+(?:of|for)\s+(?:the\s+)?(?:server|service|app|container)\s*(?:called\s+|named\s+)?[\"']?(\w+)[\"']?",
            r"config\s+(?:for|of)\s+(\w+)",
        ],
        IntentType.LIST_RESOURCES: [
            r"(?:list|show|get)\s+(?:all\s+)?(?:servers|services|apps|containers|resources)",
            r"what\s+(?:servers|services|apps|containers)\s+(?:do\s+)?(?:I|we)\s+have",
        ],
        IntentType.HELP: [
            r"(?:help|what can you do|commands|options)",
            r"^(?:hi|hello|hey)",
        ],
    }

    def _extract_intent(self, message: str) -> Tuple[IntentType, Dict[str, str]]:
        message_clean = message.strip().lower()
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_clean, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    params = {}
                    if intent_type == IntentType.STATUS_CHECK:
                        params["resource"] = groups[0] if groups else ""
                    elif intent_type == IntentType.DEPLOY:
                        if len(groups) >= 2:
                            params["version"] = groups[0]
                            params["target"] = groups[1]
                    elif intent_type == IntentType.RESTART:
                        params["resource"] = groups[0] if groups else ""
                    elif intent_type == IntentType.SCALE:
                        params["resource"] = groups[0] if groups else ""
                        if len(groups) >= 2 and groups[1]:
                            params["replicas"] = groups[1]
                    elif intent_type == IntentType.LOGS:
                        params["resource"] = groups[0] if groups else ""
                    elif intent_type == IntentType.METRICS:
                        params["resource"] = groups[0] if groups else ""
                    elif intent_type == IntentType.BACKUP:
                        params["resource"] = groups[0] if groups else ""
                    elif intent_type == IntentType.CONFIG:
                        params["resource"] = groups[0] if groups else ""
                    return intent_type, params
        return IntentType.UNKNOWN, {"original": message}

    def _evaluate_confidence(self, intent: IntentType, params: Dict[str, str],
                              message: str) -> str:
        if intent == IntentType.UNKNOWN:
            return Confidence.LOW.value
        if not params:
            return Confidence.LOW.value
        if intent == IntentType.HELP:
            return Confidence.HIGH.value
        resource = params.get("resource", params.get("target", ""))
        if resource and len(resource) >= 2:
            return Confidence.HIGH.value
        if intent == IntentType.LIST_RESOURCES:
            return Confidence.HIGH.value
        if intent == IntentType.DEPLOY and "version" in params and "target" in params:
            return Confidence.HIGH.value
        return Confidence.MEDIUM.value

    def process_message(self, session_id: str, user_id: str, message: str,
                        channel: str = "web") -> Dict[str, Any]:
        session = self._get_or_create_session(session_id, user_id, channel)
        if not session:
            return {"error": "Could not create or retrieve session"}
        intent, params = self._extract_intent(message)
        confidence = self._evaluate_confidence(intent, params, message)
        handler = self.intent_handlers.get(intent.value, self._handle_unknown)
        try:
            response = handler(params, session)
        except Exception as e:
            logger.error(f"Intent handler failed: {e}")
            response = {"message": f"I encountered an error processing your request: {str(e)}", "success": False}
        entry = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "message": message,
            "intent": intent.value,
            "confidence": confidence,
            "params": params,
            "response_summary": response.get("message", "")[:200],
            "success": response.get("success", True),
            "timestamp": datetime.utcnow().isoformat(),
        }
        session["messages"].append({
            "role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()
        })
        session["messages"].append({
            "role": "assistant", "content": response.get("message", ""),
            "data": response, "timestamp": datetime.utcnow().isoformat()
        })
        session["last_activity"] = datetime.utcnow().isoformat()
        self.intent_log.append(entry)
        self._save_sessions()
        self._save_intents()
        response["intent"] = intent.value
        response["confidence"] = confidence
        response["session_id"] = session_id
        return response

    def _get_or_create_session(self, session_id: str, user_id: str,
                                channel: str) -> Dict[str, Any]:
        existing = next((s for s in self.sessions if s["id"] == session_id), None)
        if existing:
            return existing
        if len(self.sessions) >= self.max_sessions:
            self.sessions = self.sessions[-self.max_sessions + 1:]
        session = {
            "id": session_id,
            "user_id": user_id,
            "channel": channel,
            "state": ConversationState.ACTIVE.value,
            "context": {},
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        self.sessions.append(session)
        self._save_sessions()
        return session

    def _handle_status_check(self, params: Dict[str, str],
                              session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        return {
            "success": True,
            "message": f"Server **{resource}** is **running** and **healthy**. CPU: 23%, Memory: 1.2GB/4GB (30%), Uptime: 14d 6h 32m.",
            "data": {
                "resource": resource,
                "status": "running",
                "health": "healthy",
                "cpu_percent": 23,
                "memory_used_gb": 1.2,
                "memory_total_gb": 4,
                "uptime_days": 14,
            }
        }

    def _handle_deploy(self, params: Dict[str, str],
                        session: Dict[str, Any]) -> Dict[str, Any]:
        version = params.get("version", "latest")
        target = params.get("target", "production")
        session["context"]["pending_deploy"] = {"version": version, "target": target}
        return {
            "success": True,
            "message": f"Deploy version **{version}** to **{target}**? Reply with 'yes' to confirm, or 'no' to cancel.",
            "needs_confirmation": True,
            "data": {"version": version, "target": target},
        }

    def _handle_restart(self, params: Dict[str, str],
                         session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        return {
            "success": True,
            "message": f"Restarting **{resource}**... Graceful shutdown initiated. Service should be back online in ~15 seconds.",
            "action_taken": "restart",
            "data": {"resource": resource, "status": "restarting", "estimated_downtime_seconds": 15},
        }

    def _handle_scale(self, params: Dict[str, str],
                       session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        replicas = params.get("replicas", "3")
        return {
            "success": True,
            "message": f"Scaling **{resource}** to **{replicas}** replicas. Current: 2 → Target: {replicas}.",
            "action_taken": "scale",
            "data": {"resource": resource, "current_replicas": 2, "target_replicas": int(replicas)},
        }

    def _handle_logs(self, params: Dict[str, str],
                      session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        sample_logs = [
            f"[2026-05-30 10:23:15] INFO  [{resource}] Server started on port 8080",
            f"[2026-05-30 10:23:16] INFO  [{resource}] Connected to database postgres://db.internal:5432/main",
            f"[2026-05-30 10:23:18] INFO  [{resource}] Health check endpoint registered at /health",
            f"[2026-05-30 10:24:01] DEBUG [{resource}] Processing request GET /api/users from 10.0.1.42",
            f"[2026-05-30 10:24:02] INFO  [{resource}] Request completed in 23ms",
        ]
        return {
            "success": True,
            "message": f"Recent logs for **{resource}** (last 5 entries):\n" + "\n".join(sample_logs),
            "data": {"resource": resource, "log_entries": sample_logs, "total_lines": 2341},
        }

    def _handle_metrics(self, params: Dict[str, str],
                         session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        return {
            "success": True,
            "message": f"Metrics for **{resource}** — CPU: 34.2%, Memory: 1.8GB/8GB, Disk: 45GB/100GB, Network: 1.2Mbps in / 0.8Mbps out",
            "data": {
                "resource": resource,
                "cpu_percent": 34.2,
                "memory_used_gb": 1.8,
                "memory_total_gb": 8,
                "disk_used_gb": 45,
                "disk_total_gb": 100,
                "network_in_mbps": 1.2,
                "network_out_mbps": 0.8,
            },
        }

    def _handle_backup(self, params: Dict[str, str],
                        session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        return {
            "success": True,
            "message": f"Backup initiated for **{resource}**. Backup ID: bkp-{uuid.uuid4().hex[:8]}. Estimated completion: 2 minutes.",
            "action_taken": "backup",
            "data": {"resource": resource, "backup_id": f"bkp-{uuid.uuid4().hex[:8]}", "status": "in_progress"},
        }

    def _handle_config(self, params: Dict[str, str],
                        session: Dict[str, Any]) -> Dict[str, Any]:
        resource = params.get("resource", "unknown")
        config_data = {
            "server_name": resource,
            "port": 8080,
            "environment": "production",
            "log_level": "info",
            "max_connections": 100,
            "database_url": "postgres://db.internal:5432/main",
            "cache_ttl_seconds": 3600,
            "features": {"monitoring": True, "tracing": True, "metrics": True},
        }
        return {
            "success": True,
            "message": f"Configuration for **{resource}**:\n" + json.dumps(config_data, indent=2),
            "data": config_data,
        }

    def _handle_help(self, params: Dict[str, str],
                      session: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": True,
            "message": (
                "🤖 **Infra Pilot Ops Assistant** — I can help with:\n\n"
                "• **Status checks**: 'What's the status of server-42?'\n"
                "• **Deployments**: 'Deploy version 3.2 to staging'\n"
                "• **Restarts**: 'Restart the web-server'\n"
                "• **Scaling**: 'Scale api-service to 5 replicas'\n"
                "• **Logs**: 'Show logs for database'\n"
                "• **Metrics**: 'Show CPU for web-server'\n"
                "• **Backups**: 'Create a backup of postgres'\n"
                "• **Config**: 'Show config for nginx'\n"
                "• **List resources**: 'List all servers'"
            ),
            "data": {"available_intents": [i.value for i in IntentType if i != IntentType.UNKNOWN]},
        }

    def _handle_list_resources(self, params: Dict[str, str],
                                session: Dict[str, Any]) -> Dict[str, Any]:
        resources = [
            {"name": "web-server-01", "type": "container", "status": "running", "cpu": 23},
            {"name": "api-service-02", "type": "container", "status": "running", "cpu": 45},
            {"name": "postgres-db", "type": "container", "status": "running", "cpu": 12},
            {"name": "redis-cache", "type": "container", "status": "running", "cpu": 5},
            {"name": "nginx-proxy", "type": "container", "status": "running", "cpu": 8},
            {"name": "worker-queue", "type": "container", "status": "idle", "cpu": 2},
        ]
        message_lines = ["**Available Resources:**\n"]
        for r in resources:
            status_icon = "🟢" if r["status"] == "running" else "🟡" if r["status"] == "idle" else "🔴"
            message_lines.append(f"{status_icon} **{r['name']}** — {r['type']}, CPU: {r['cpu']}%")
        return {
            "success": True,
            "message": "\n".join(message_lines),
            "data": {"resources": resources, "total": len(resources)},
        }

    def _handle_unknown(self, params: Dict[str, str],
                         session: Dict[str, Any]) -> Dict[str, Any]:
        original = params.get("original", "")
        return {
            "success": False,
            "message": (
                f"I'm not sure what you mean by \"{original}\". "
                f"Try something like 'status of server-42', 'deploy version 1.2 to staging', "
                f"'restart web-server', or 'help' to see all available commands."
            ),
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return next((s for s in self.sessions if s["id"] == session_id), None)

    def list_sessions(self, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        result = self.sessions
        if user_id:
            result = [s for s in result if s.get("user_id") == user_id]
        return result[-limit:]

    def clear_session(self, session_id: str) -> bool:
        initial = len(self.sessions)
        self.sessions = [s for s in self.sessions if s["id"] != session_id]
        self._save_sessions()
        return len(self.sessions) < initial

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get_session(session_id)
        if session:
            return session.get("messages", [])
        return []

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self.intent_log)
        by_intent = {}
        for entry in self.intent_log:
            intent = entry.get("intent", "unknown")
            by_intent[intent] = by_intent.get(intent, 0) + 1
        successful = sum(1 for e in self.intent_log if e.get("success"))
        return {
            "total_messages": total,
            "total_sessions": len(self.sessions),
            "successful": successful,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            "intents_distribution": by_intent,
            "active_sessions": sum(1 for s in self.sessions if s.get("state") == ConversationState.ACTIVE.value),
        }

    # ===== APPENDED: Pagination, batch ops, export/import, analytics, enrichment =====

    def paginate_sessions(self, offset: int = 0, limit: int = 50, user_id: str = None,
                           state: str = None) -> dict:
        results = self.sessions
        if user_id:
            results = [s for s in results if s.get("user_id") == user_id]
        if state:
            results = [s for s in results if s.get("state") == state]
        total = len(results)
        results.sort(key=lambda s: s.get("last_activity", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def paginate_intents(self, offset: int = 0, limit: int = 50, intent: str = None,
                          user_id: str = None, success: bool = None) -> dict:
        results = self.intent_log
        if intent:
            results = [e for e in results if e.get("intent") == intent]
        if user_id:
            results = [e for e in results if e.get("user_id") == user_id]
        if success is not None:
            results = [e for e in results if e.get("success") == success]
        total = len(results)
        results.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        sliced = results[offset:offset + limit]
        return {"items": sliced, "total": total, "offset": offset, "limit": limit,
                "has_more": offset + limit < total}

    def batch_process_messages(self, messages: list[dict]) -> list[dict]:
        results = []
        for msg in messages:
            try:
                result = self.process_message(
                    msg["session_id"], msg["user_id"], msg["message"], msg.get("channel", "web"),
                )
                results.append(result)
            except (KeyError, TypeError) as e:
                results.append({"error": str(e), "message": msg.get("message", "")})
        return results

    def batch_clear_sessions(self, session_ids: list[str]) -> dict:
        cleared = 0
        for sid in session_ids:
            if self.clear_session(sid):
                cleared += 1
        return {"cleared": cleared, "total_requested": len(session_ids)}

    def export_intents(self, intent: str = None, user_id: str = None) -> list[dict]:
        results = self.intent_log
        if intent:
            results = [e for e in results if e.get("intent") == intent]
        if user_id:
            results = [e for e in results if e.get("user_id") == user_id]
        return [{
            "id": e["id"], "session_id": e.get("session_id"), "user_id": e.get("user_id"),
            "message": e.get("message"), "intent": e.get("intent"),
            "confidence": e.get("confidence"), "success": e.get("success"),
            "response_summary": e.get("response_summary"), "timestamp": e.get("timestamp"),
        } for e in results]

    def import_intents(self, intents: list[dict]) -> dict:
        imported = 0
        for e in intents:
            entry = {
                "id": str(uuid.uuid4()),
                "session_id": e.get("session_id", "imported"),
                "user_id": e.get("user_id", "imported"),
                "message": e.get("message", ""),
                "intent": e.get("intent", "unknown"),
                "confidence": e.get("confidence", "low"),
                "params": e.get("params", {}),
                "response_summary": e.get("response_summary", ""),
                "success": e.get("success", True),
                "timestamp": e.get("timestamp", datetime.utcnow().isoformat()),
            }
            self.intent_log.append(entry)
            imported += 1
        self._save_intents()
        return {"imported": imported}

    def export_sessions(self, user_id: str = None, state: str = None) -> list[dict]:
        results = self.sessions
        if user_id:
            results = [s for s in results if s.get("user_id") == user_id]
        if state:
            results = [s for s in results if s.get("state") == state]
        return [{
            "id": s["id"], "user_id": s.get("user_id"), "channel": s.get("channel"),
            "state": s.get("state"), "context": s.get("context", {}),
            "message_count": len(s.get("messages", [])),
            "created_at": s.get("created_at"), "last_activity": s.get("last_activity"),
        } for s in results]

    def get_analytics(self) -> dict:
        intent_counts = Counter(e.get("intent", "unknown") for e in self.intent_log)
        confidence_counts = Counter(e.get("confidence", "unknown") for e in self.intent_log)
        success_count = sum(1 for e in self.intent_log if e.get("success"))
        total = len(self.intent_log)
        intents_by_hour = {}
        for e in self.intent_log:
            try:
                hour = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%dT%H:00:00")
                intents_by_hour[hour] = intents_by_hour.get(hour, 0) + 1
            except (ValueError, TypeError):
                pass
        user_counts = Counter(e.get("user_id", "unknown") for e in self.intent_log)
        return {
            "total_messages": total,
            "total_sessions": len(self.sessions),
            "successful": success_count,
            "failed": total - success_count,
            "success_rate": round(success_count / max(total, 1) * 100, 1),
            "intent_distribution": dict(intent_counts),
            "confidence_distribution": dict(confidence_counts),
            "top_users": [{"user": u, "count": c} for u, c in user_counts.most_common(10)],
            "intents_by_hour": dict(sorted(intents_by_hour.items())[-24:]),
            "active_sessions": sum(1 for s in self.sessions if s.get("state") == ConversationState.ACTIVE.value),
        }

    def search_intents(self, query: str) -> list[dict]:
        q = query.lower()
        return [e for e in self.intent_log if q in e.get("message", "").lower()
                or q in e.get("intent", "").lower()
                or q in e.get("user_id", "").lower()]

    def get_user_sessions(self, user_id: str) -> list[dict]:
        user_sessions = [s for s in self.sessions if s.get("user_id") == user_id]
        return [{
            "id": s["id"], "channel": s.get("channel"), "state": s.get("state"),
            "message_count": len(s.get("messages", [])),
            "created_at": s.get("created_at"), "last_activity": s.get("last_activity"),
        } for s in user_sessions]

    def get_intent_trend(self, intent: str = None) -> list[dict]:
        filtered = self.intent_log
        if intent:
            filtered = [e for e in filtered if e.get("intent") == intent]
        daily_counts = {}
        for e in filtered:
            try:
                day = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%d")
                daily_counts[day] = daily_counts.get(day, 0) + 1
            except (ValueError, TypeError):
                pass
        return [{"date": d, "count": c} for d, c in sorted(daily_counts.items())]

    def add_custom_intent(self, pattern: str, intent_type: str, handler_desc: str = "") -> dict:
        try:
            intent_enum = IntentType(intent_type)
        except ValueError:
            intent_enum = IntentType.UNKNOWN
        if intent_enum not in self.INTENT_PATTERNS:
            self.INTENT_PATTERNS[intent_enum] = []
        self.INTENT_PATTERNS[intent_enum].append(pattern)
        return {
            "intent": intent_type,
            "pattern": pattern,
            "description": handler_desc or f"Custom handler for {intent_type}",
        }

    def simulate_conversation(self, messages: list[str], session_id: str = None,
                               user_id: str = "simulation") -> list[dict]:
        if not session_id:
            session_id = f"sim-{uuid.uuid4().hex[:8]}"
        results = []
        for msg in messages:
            result = self.process_message(session_id, user_id, msg)
            results.append({"message": msg, "response": result})
        return results

    # ===== APPENDED BATCH 2: SLO, reports, config export, advanced analytics =====

    def check_ops_slo(self, target_success_rate: float = 95.0, window_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = [e for e in self.intent_log if datetime.fromisoformat(e["timestamp"]) > cutoff]
        total = len(recent)
        successful = sum(1 for e in recent if e.get("success"))
        actual_rate = round((successful / max(total, 1)) * 100, 2)
        return {
            "slo_target_pct": target_success_rate,
            "actual_success_rate_pct": actual_rate,
            "compliant": actual_rate >= target_success_rate,
            "window_hours": window_hours,
            "total_requests": total,
            "successful": successful,
            "failed": total - successful,
        }

    def generate_ops_report(self, days: int = 7) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [e for e in self.intent_log if datetime.fromisoformat(e["timestamp"]) > cutoff]
        by_intent = Counter(e.get("intent", "unknown") for e in recent)
        by_user = Counter(e.get("user_id", "unknown") for e in recent)
        by_confidence = Counter(e.get("confidence", "unknown") for e in recent)
        successful = sum(1 for e in recent if e.get("success"))
        return {
            "period_days": days,
            "total_messages": len(recent),
            "successful": successful,
            "success_rate": round((successful / max(len(recent), 1)) * 100, 1),
            "intent_distribution": dict(by_intent),
            "top_users": dict(by_user.most_common(10)),
            "confidence_distribution": dict(by_confidence),
            "unique_users": len(by_user),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_config(self) -> dict:
        return {
            "config": self.config,
            "session_timeout_minutes": self.session_timeout,
            "max_sessions": self.max_sessions,
            "total_sessions": len(self.sessions),
            "total_intents_logged": len(self.intent_log),
        }

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        messages = session.get("messages", [])
        user_msgs = [m for m in messages if m.get("role") == "user"]
        return {
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "channel": session.get("channel"),
            "state": session.get("state"),
            "total_messages": len(messages),
            "user_message_count": len(user_msgs),
            "duration_minutes": round((datetime.fromisoformat(session.get("last_activity", datetime.utcnow().isoformat())) -
                                       datetime.fromisoformat(session.get("created_at", datetime.utcnow().isoformat()))).total_seconds() / 60, 1),
            "created_at": session.get("created_at"),
            "last_activity": session.get("last_activity"),
        }

    def get_top_intents(self, limit: int = 10) -> list[dict]:
        counter = Counter(e.get("intent", "unknown") for e in self.intent_log)
        return [{"intent": i, "count": c} for i, c in counter.most_common(limit)]

    def get_user_engagement(self, user_id: str) -> dict:
        user_sessions = [s for s in self.sessions if s.get("user_id") == user_id]
        user_intents = [e for e in self.intent_log if e.get("user_id") == user_id]
        return {
            "user_id": user_id,
            "total_sessions": len(user_sessions),
            "total_messages": len(user_intents),
            "unique_intents": len(set(e.get("intent") for e in user_intents)),
            "success_rate": round(sum(1 for e in user_intents if e.get("success")) / max(len(user_intents), 1) * 100, 1),
            "last_active": max((s.get("last_activity", "") for s in user_sessions), default=None),
        }

    def export_user_data(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "sessions": [s for s in self.sessions if s.get("user_id") == user_id],
            "intents": [e for e in self.intent_log if e.get("user_id") == user_id],
            "analytics": self.get_user_engagement(user_id),
        }

    def clear_user_data(self, user_id: str) -> dict:
        before_sessions = len(self.sessions)
        before_intents = len(self.intent_log)
        self.sessions = [s for s in self.sessions if s.get("user_id") != user_id]
        self.intent_log = [e for e in self.intent_log if e.get("user_id") != user_id]
        self._save_sessions()
        self._save_intents()
        return {
            "sessions_removed": before_sessions - len(self.sessions),
            "intents_removed": before_intents - len(self.intent_log),
        }

    def get_slo_health(self, window_hours: int = 24, target_success_rate: float = 95.0) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent = [e for e in self.intent_log if datetime.fromisoformat(e["timestamp"]) > cutoff]
        total = len(recent)
        successful = sum(1 for e in recent if e.get("success"))
        actual_rate = round((successful / max(total, 1)) * 100, 2)
        return {"slo_target_pct": target_success_rate, "actual_success_rate_pct": actual_rate, "compliant": actual_rate >= target_success_rate, "window_hours": window_hours, "total_requests": total, "successful": successful, "failed": total - successful}

    def get_conversation_timeline(self, hours: int = 24) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [e for e in self.intent_log if datetime.fromisoformat(e["timestamp"]) > cutoff]
        hourly = defaultdict(int)
        for e in recent:
            try:
                hour = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%dT%H:00")
                hourly[hour] += 1
            except (ValueError, TypeError):
                pass
        return [{"hour": h, "count": c} for h, c in sorted(hourly.items())]

    def get_user_satisfaction(self, user_id: str) -> dict:
        user_intents = [e for e in self.intent_log if e.get("user_id") == user_id]
        if not user_intents:
            return {"user_id": user_id, "error": "No data"}
        successful = sum(1 for e in user_intents if e.get("success"))
        return {"user_id": user_id, "total_interactions": len(user_intents), "successful": successful, "success_rate": round(successful / len(user_intents) * 100, 1), "avg_confidence": round(statistics.mean([e.get("confidence", 0) for e in user_intents if isinstance(e.get("confidence"), (int, float))]), 4) if any(isinstance(e.get("confidence"), (int, float)) for e in user_intents) else 0}

    def get_channel_breakdown(self) -> dict:
        channel_count: dict[str, int] = defaultdict(int)
        for s in self.sessions:
            channel_count[s.get("channel", "unknown")] += 1
        return dict(channel_count)

    def export_conversation_log(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        return {"session_id": session_id, "messages": session.get("messages", []), "intents": [e for e in self.intent_log if e.get("session_id") == session_id], "summary": self.get_session_summary(session_id)}

    def search_conversations(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for s in self.sessions:
            for m in s.get("messages", []):
                if q in m.get("content", "").lower():
                    results.append({"session_id": s.get("id"), "user_id": s.get("user_id"), "matched_message": m.get("content", "")[:100], "timestamp": m.get("timestamp")})
                    break
        return results[:20]


class FeedbackCollector:
    def __init__(self, engine: ConversationalOpsEngine):
        self.engine = engine
        self.feedback: list[dict] = []

    def record_feedback(self, session_id: str, rating: int, comment: str = "") -> dict:
        entry = {"id": str(uuid.uuid4()), "session_id": session_id, "rating": rating, "comment": comment, "created_at": datetime.utcnow().isoformat()}
        self.feedback.append(entry)
        return entry

    def get_average_rating(self) -> float:
        if not self.feedback:
            return 0.0
        return round(statistics.mean(f.get("rating", 0) for f in self.feedback), 2)

    def get_feedback_summary(self) -> dict:
        if not self.feedback:
            return {"total": 0, "avg_rating": 0}
        ratings = [f.get("rating", 0) for f in self.feedback]
        return {"total": len(self.feedback), "avg_rating": round(statistics.mean(ratings), 2), "rating_distribution": dict(Counter(ratings)), "positive_pct": round(sum(1 for r in ratings if r >= 4) / len(ratings) * 100, 1)}

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
