import json, uuid, asyncio, random, logging, math, statistics
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter, deque
from enum import Enum

logger = logging.getLogger(__name__)


class ActionRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealingMode(Enum):
    AUTO = "auto_remediate"
    SUGGEST = "suggest"
    LOG = "log_only"


REMEDIATION_ACTIONS = [
    {"action": "restart_container", "category": "container", "risk": "low", "avg_success_rate": 0.85, "avg_resolution_seconds": 30, "description": "Restart the container while preserving data volumes"},
    {"action": "recreate_container", "category": "container", "risk": "medium", "avg_success_rate": 0.75, "avg_resolution_seconds": 60, "description": "Delete and recreate the container from image"},
    {"action": "scale_up", "category": "container", "risk": "low", "avg_success_rate": 0.90, "avg_resolution_seconds": 45, "description": "Increase container CPU/memory limits"},
    {"action": "scale_down", "category": "container", "risk": "low", "avg_success_rate": 0.90, "avg_resolution_seconds": 45, "description": "Decrease container replicas to reduce load"},
    {"action": "restart_service", "category": "system", "risk": "medium", "avg_success_rate": 0.80, "avg_resolution_seconds": 20, "description": "Restart the system service via systemd"},
    {"action": "increase_memory", "category": "container", "risk": "low", "avg_success_rate": 0.88, "avg_resolution_seconds": 15, "description": "Increase memory limit for the container"},
    {"action": "increase_cpu", "category": "container", "risk": "low", "avg_success_rate": 0.85, "avg_resolution_seconds": 15, "description": "Increase CPU limit for the container"},
    {"action": "rollback_deployment", "category": "kubernetes", "risk": "high", "avg_success_rate": 0.70, "avg_resolution_seconds": 120, "description": "Rollback Kubernetes deployment to previous version"},
    {"action": "restart_node", "category": "kubernetes", "risk": "high", "avg_success_rate": 0.65, "avg_resolution_seconds": 180, "description": "Cordon and restart the Kubernetes node"},
    {"action": "cleanup_disk", "category": "system", "risk": "low", "avg_success_rate": 0.95, "avg_resolution_seconds": 60, "description": "Remove old logs, cache, and temp files"},
    {"action": "restart_dns", "category": "network", "risk": "medium", "avg_success_rate": 0.80, "avg_resolution_seconds": 10, "description": "Restart DNS resolver service"},
    {"action": "failover_database", "category": "database", "risk": "high", "avg_success_rate": 0.75, "avg_resolution_seconds": 90, "description": "Failover database to standby replica"},
    {"action": "rebalance_connections", "category": "database", "risk": "medium", "avg_success_rate": 0.82, "avg_resolution_seconds": 30, "description": "Kill idle database connections and rebalance pool"},
    {"action": "clear_cache", "category": "system", "risk": "low", "avg_success_rate": 0.90, "avg_resolution_seconds": 5, "description": "Clear application/system caches"},
    {"action": "restart_proxy", "category": "network", "risk": "medium", "avg_success_rate": 0.85, "avg_resolution_seconds": 15, "description": "Restart reverse proxy/load balancer"},
    {"action": "renew_certificate", "category": "security", "risk": "low", "avg_success_rate": 0.95, "avg_resolution_seconds": 30, "description": "Trigger SSL certificate renewal"},
    {"action": "reschedule_pods", "category": "kubernetes", "risk": "medium", "avg_success_rate": 0.78, "avg_resolution_seconds": 60, "description": "Reschedule pods to different nodes"},
    {"action": "increase_disk_size", "category": "storage", "risk": "medium", "avg_success_rate": 0.85, "avg_resolution_seconds": 120, "description": "Expand persistent volume or disk size"},
    {"action": "restart_database", "category": "database", "risk": "high", "avg_success_rate": 0.60, "avg_resolution_seconds": 45, "description": "Restart database service"},
    {"action": "vacuum_database", "category": "database", "risk": "medium", "avg_success_rate": 0.80, "avg_resolution_seconds": 300, "description": "Run database vacuum/optimize"},
]

HEALING_PATTERNS = [
    {"pattern": "container_crash_loop", "symptoms": ["container.restart_count > 5", "container.status == crash_loop_back_off"],
     "recommended_action": "recreate_container", "avg_success_rate": 0.78, "detection_count": 0, "severity": "high",
     "description": "Container is in crash loop backoff state", "auto_heal": True, "cooldown_seconds": 120},
    {"pattern": "high_cpu_usage", "symptoms": ["container.cpu_percent > 85", "cpu.duration_seconds > 300"],
     "recommended_action": "scale_up", "avg_success_rate": 0.92, "detection_count": 0, "severity": "medium",
     "description": "Sustained high CPU usage detected", "auto_heal": True, "cooldown_seconds": 300},
    {"pattern": "memory_leak", "symptoms": ["container.memory_percent > 90", "memory.trend == increasing", "memory.duration_seconds > 600"],
     "recommended_action": "restart_container", "avg_success_rate": 0.82, "detection_count": 0, "severity": "high",
     "description": "Memory usage increasing over time indicating leak", "auto_heal": True, "cooldown_seconds": 600},
    {"pattern": "disk_full", "symptoms": ["host.disk_percent > 90", "host.disk_available_bytes < 1073741824"],
     "recommended_action": "cleanup_disk", "avg_success_rate": 0.95, "detection_count": 0, "severity": "critical",
     "description": "Disk space critically low", "auto_heal": True, "cooldown_seconds": 300},
    {"pattern": "service_unhealthy", "symptoms": ["container.health == unhealthy", "container.health_failures > 3"],
     "recommended_action": "restart_container", "avg_success_rate": 0.88, "detection_count": 0, "severity": "high",
     "description": "Health check failures detected", "auto_heal": True, "cooldown_seconds": 120},
    {"pattern": "dns_resolution_failure", "symptoms": ["network.dns_latency_ms > 5000", "network.dns_errors > 10"],
     "recommended_action": "restart_dns", "avg_success_rate": 0.80, "detection_count": 0, "severity": "medium",
     "description": "DNS resolution failures or high latency", "auto_heal": False, "cooldown_seconds": 60},
    {"pattern": "database_slow_queries", "symptoms": ["database.query_latency_p99_ms > 1000", "database.connection_usage_percent > 80"],
     "recommended_action": "rebalance_connections", "avg_success_rate": 0.82, "detection_count": 0, "severity": "medium",
     "description": "Database query latency or connection pool exhaustion", "auto_heal": False, "cooldown_seconds": 300},
    {"pattern": "oom_kill", "symptoms": ["container.oom_killed == true", "container.restart_count > 1"],
     "recommended_action": "increase_memory", "avg_success_rate": 0.85, "detection_count": 0, "severity": "critical",
     "description": "Container killed due to out of memory", "auto_heal": True, "cooldown_seconds": 600},
    {"pattern": "network_high_latency", "symptoms": ["network.latency_p99_ms > 2000", "network.packet_loss_percent > 1"],
     "recommended_action": "restart_proxy", "avg_success_rate": 0.75, "detection_count": 0, "severity": "medium",
     "description": "High network latency or packet loss", "auto_heal": False, "cooldown_seconds": 180},
    {"pattern": "certificate_expiring", "symptoms": ["ssl.days_until_expiry < 7", "ssl.days_until_expiry > 0"],
     "recommended_action": "renew_certificate", "avg_success_rate": 0.95, "detection_count": 0, "severity": "high",
     "description": "SSL certificate expiring within 7 days", "auto_heal": True, "cooldown_seconds": 86400},
    {"pattern": "application_error_rate", "symptoms": ["http.error_rate_percent > 5", "http.total_requests > 100"],
     "recommended_action": "restart_service", "avg_success_rate": 0.70, "detection_count": 0, "severity": "high",
     "description": "Elevated application error rate", "auto_heal": False, "cooldown_seconds": 120},
    {"pattern": "pod_pending", "symptoms": ["kubernetes.pod_status == Pending", "kubernetes.pod_pending_duration_minutes > 5"],
     "recommended_action": "reschedule_pods", "avg_success_rate": 0.78, "detection_count": 0, "severity": "medium",
     "description": "Pods stuck in Pending state", "auto_heal": False, "cooldown_seconds": 300},
    {"pattern": "connection_pool_exhaustion", "symptoms": ["database.connection_usage_percent > 95", "database.connection_errors > 5"],
     "recommended_action": "rebalance_connections", "avg_success_rate": 0.82, "detection_count": 0, "severity": "critical",
     "description": "Database connection pool exhausted", "auto_heal": True, "cooldown_seconds": 300},
]


class CooldownTracker:
    def __init__(self, default_cooldown: int = 300):
        self._cooldowns: Dict[str, datetime] = {}
        self._default_cooldown = default_cooldown

    def is_on_cooldown(self, key: str) -> bool:
        if key not in self._cooldowns:
            return False
        return datetime.utcnow() < self._cooldowns[key]

    def set_cooldown(self, key: str, seconds: int):
        self._cooldowns[key] = datetime.utcnow() + timedelta(seconds=seconds)

    def get_remaining(self, key: str) -> int:
        if key not in self._cooldowns:
            return 0
        remaining = (self._cooldowns[key] - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    def clear(self, key: str):
        self._cooldowns.pop(key, None)

    def clear_all(self):
        self._cooldowns.clear()


class AnomalyDetector:
    def __init__(self, window_size: int = 10, z_threshold: float = 2.0):
        self._windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self._z_threshold = z_threshold

    def add_observation(self, metric: str, value: float):
        self._windows[metric].append(value)

    def is_anomalous(self, metric: str, value: float) -> Tuple[bool, float]:
        window = self._windows.get(metric, deque())
        if len(window) < 5:
            self.add_observation(metric, value)
            return False, 0.0
        mean = statistics.mean(window)
        stdev = statistics.stdev(window) if len(window) > 1 else 1.0
        if stdev == 0:
            stdev = 1.0
        z_score = abs(value - mean) / stdev
        is_anom = z_score > self._z_threshold
        self.add_observation(metric, value)
        return is_anom, round(z_score, 2)

    def get_statistics(self, metric: str) -> Optional[Dict[str, float]]:
        window = self._windows.get(metric)
        if not window or len(window) < 2:
            return None
        return {
            "mean": round(statistics.mean(window), 2),
            "stdev": round(statistics.stdev(window), 2),
            "min": round(min(window), 2),
            "max": round(max(window), 2),
            "count": len(window),
        }


class QLearningAgent:
    def __init__(self, actions: List[Dict[str, Any]], learning_rate: float = 0.1,
                 discount_factor: float = 0.9, exploration_rate: float = 0.1,
                 exploration_decay: float = 0.995, min_exploration_rate: float = 0.01):
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.actions = [a["action"] for a in actions]
        self.action_details = {a["action"]: a for a in actions}
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.epsilon_decay = exploration_decay
        self.epsilon_min = min_exploration_rate
        self.state_history: List[Dict[str, Any]] = []
        self.total_episodes = 0

    def get_state_key(self, context: Dict[str, Any]) -> str:
        pattern = context.get("detected_pattern", "unknown")
        severity = context.get("severity", "medium")
        time_of_day = datetime.utcnow().hour
        hour_bucket = "business_hours" if 8 <= time_of_day < 18 else "after_hours" if time_of_day < 22 else "night"
        day_of_week = datetime.utcnow().weekday()
        day_bucket = "weekday" if day_of_week < 5 else "weekend"
        return f"{pattern}:{severity}:{hour_bucket}:{day_bucket}"

    def select_action(self, state_key: str, context: Dict[str, Any]) -> str:
        self.total_episodes += 1
        if random.random() < self.epsilon:
            chosen = random.choice(self.actions)
            logger.debug(f"Exploration: selected random action {chosen}")
            return chosen
        state_values = {a: self.q_table[state_key].get(a, 0.0) for a in self.actions}
        max_val = max(state_values.values()) if state_values else 0.0
        best_actions = [a for a, v in state_values.items() if v == max_val]
        chosen = random.choice(best_actions) if best_actions else random.choice(self.actions)
        logger.debug(f"Exploitation: selected {chosen} with Q-value {max_val:.3f}")
        return chosen

    def learn(self, state_key: str, action: str, reward: float, next_state_key: str):
        old_value = self.q_table[state_key].get(action, 0.0)
        next_max = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0.0
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        self.q_table[state_key][action] = round(new_value, 4)
        self.state_history.append({
            "state": state_key, "action": action, "reward": reward,
            "old_value": round(old_value, 4), "new_value": round(new_value, 4),
            "timestamp": datetime.utcnow().isoformat(),
        })

    def decay_exploration(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def get_learned_actions(self, top_k: int = 20) -> List[Dict[str, Any]]:
        learned = []
        for state, actions in self.q_table.items():
            for action, value in actions.items():
                if value > 0:
                    details = self.action_details.get(action, {})
                    learned.append({
                        "state": state, "action": action,
                        "q_value": round(value, 3),
                        "category": details.get("category", "unknown"),
                        "risk": details.get("risk", "unknown"),
                    })
        return sorted(learned, key=lambda x: x["q_value"], reverse=True)[:top_k]

    def get_state_action_count(self) -> int:
        return sum(len(actions) for actions in self.q_table.values())

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_states": len(self.q_table),
            "total_state_action_pairs": self.get_state_action_count(),
            "exploration_rate": round(self.epsilon, 3),
            "total_episodes": self.total_episodes,
            "learning_rate": self.lr,
            "discount_factor": self.gamma,
        }


class SelfHealingManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._remediation_history: List[Dict[str, Any]] = []
        self._patterns: Dict[str, Dict[str, Any]] = {p["pattern"]: p for p in HEALING_PATTERNS}
        self._actions: Dict[str, Dict[str, Any]] = {a["action"]: a for a in REMEDIATION_ACTIONS}
        self.agent = QLearningAgent(REMEDIATION_ACTIONS, config.get("learning_rate", 0.1), config.get("discount_factor", 0.9), config.get("exploration_rate", 0.1))
        self.cooldowns = CooldownTracker()
        self.anomaly_detector = AnomalyDetector()
        self._auto_remediation_enabled = config.get("auto_remediation_enabled", True)
        self._confidence_thresholds = config.get("confidence_thresholds", {"auto_remediate": 0.85, "suggest": 0.65, "log_only": 0.40})
        self._max_history = config.get("max_history", 10000)
        self._min_observations_for_detection = config.get("min_observations", 3)
        self._initialized = False
        self._last_retrain: Optional[datetime] = None
        self._total_remediations = 0
        self._successful_remediations = 0
        self._failed_remediations = 0

    async def initialize(self):
        self._initialized = True
        logger.info(f"SelfHealingManager initialized with {len(self._patterns)} patterns and {len(self._actions)} actions")

    async def close(self):
        self._remediation_history.clear()
        logger.info(f"SelfHealingManager closed. Total remediations: {self._total_remediations}")

    def detect_and_heal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self._auto_remediation_enabled:
            return {"action": None, "decision": "disabled", "reason": "Auto-remediation is disabled"}
        detected_pattern, confidence = self._detect_pattern(context)
        if not detected_pattern:
            return {"action": None, "decision": "no_match", "reason": "No pattern matched", "confidence": 0.0}
        pattern_info = self._patterns.get(detected_pattern, {})
        cooldown_key = f"{detected_pattern}:{context.get('container', context.get('host', 'unknown'))}"
        if self.cooldowns.is_on_cooldown(cooldown_key):
            remaining = self.cooldowns.get_remaining(cooldown_key)
            return {"action": None, "decision": "cooldown", "reason": f"On cooldown for {remaining}s", "pattern": detected_pattern, "confidence": confidence}
        state_key = self.agent.get_state_key({**context, "detected_pattern": detected_pattern, "severity": pattern_info.get("severity", "medium")})
        recommended = pattern_info.get("recommended_action")
        if recommended:
            chosen_action = recommended
        else:
            chosen_action = self.agent.select_action(state_key, context)
        action_info = self._actions.get(chosen_action, {})
        base_confidence = action_info.get("avg_success_rate", 0.5)
        pattern_confidence = pattern_info.get("avg_success_rate", 0.5)
        overall_confidence = round((base_confidence + pattern_confidence + confidence) / 3, 3)
        if overall_confidence >= self._confidence_thresholds.get("auto_remediate", 0.85):
            result = self._execute_remediation(chosen_action, context)
            self._record_remediation(detected_pattern, chosen_action, context, result, overall_confidence, "auto")
            self.cooldowns.set_cooldown(cooldown_key, pattern_info.get("cooldown_seconds", 300))
            return {"action": chosen_action, "decision": "auto_remediated", "pattern": detected_pattern, "confidence": overall_confidence, "result": result}
        elif overall_confidence >= self._confidence_thresholds.get("suggest", 0.65):
            return {"action": chosen_action, "decision": "suggested", "pattern": detected_pattern, "confidence": overall_confidence, "message": f"Suggested: {action_info.get('description', chosen_action)}"}
        else:
            self._record_remediation(detected_pattern, chosen_action, context, {"action": chosen_action, "success": None, "skipped": True}, overall_confidence, "logged")
            return {"action": chosen_action, "decision": "logged", "pattern": detected_pattern, "confidence": overall_confidence, "message": "Confidence too low for automatic action"}

    def _detect_pattern(self, context: Dict[str, Any]) -> Tuple[Optional[str], float]:
        best_match = None
        best_confidence = 0.0
        for pattern_id, pattern in self._patterns.items():
            symptom_count = len(pattern["symptoms"])
            if symptom_count == 0:
                continue
            match_count = 0
            for symptom in pattern["symptoms"]:
                if self._check_symptom(symptom, context):
                    match_count += 1
            match_ratio = match_count / symptom_count
            if match_ratio >= 0.6 and match_ratio > best_confidence:
                best_match = pattern_id
                best_confidence = match_ratio
        if best_match:
            pattern_ref = self._patterns[best_match]
            pattern_ref["detection_count"] = pattern_ref.get("detection_count", 0) + 1
            severity_modifier = {"critical": 0.1, "high": 0.05, "medium": 0.0, "low": -0.1}
            confidence = min(1.0, 0.5 + (best_confidence * 0.5) + severity_modifier.get(pattern_ref.get("severity", "medium"), 0.0))
            return best_match, round(confidence, 3)
        return None, 0.0

    def _check_symptom(self, symptom: str, context: Dict[str, Any]) -> bool:
        try:
            if " > " in symptom:
                metric, value = symptom.split(" > ", 1)
                actual = self._get_metric(context, metric.strip())
                if actual is None:
                    return False
                return float(actual) > float(value)
            elif " < " in symptom:
                metric, value = symptom.split(" < ", 1)
                actual = self._get_metric(context, metric.strip())
                if actual is None:
                    return False
                return float(actual) < float(value)
            elif " == " in symptom:
                metric, value = symptom.split(" == ", 1)
                actual = self._get_metric(context, metric.strip())
                if actual is None:
                    return False
                return str(actual).strip("'\"") == str(value).strip("'\"")
            elif " >= " in symptom:
                metric, value = symptom.split(" >= ", 1)
                actual = self._get_metric(context, metric.strip())
                if actual is None:
                    return False
                return float(actual) >= float(value)
            elif " <= " in symptom:
                metric, value = symptom.split(" <= ", 1)
                actual = self._get_metric(context, metric.strip())
                if actual is None:
                    return False
                return float(actual) <= float(value)
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Symptom check failed for '{symptom}': {e}")
            return False
        return False

    def _get_metric(self, context: Dict[str, Any], metric_path: str) -> Any:
        parts = metric_path.split(".")
        current: Any = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)) and part.isdigit():
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return current

    def _execute_remediation(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        action_info = self._actions.get(action, {})
        success_rate = action_info.get("avg_success_rate", 0.8)
        success = random.random() < success_rate
        resolution_time = action_info.get("avg_resolution_seconds", 30) * random.uniform(0.8, 1.2)
        risk = action_info.get("risk", "medium")
        result = {
            "action": action,
            "success": success,
            "risk": risk,
            "category": action_info.get("category", "unknown"),
            "resolution_seconds": round(resolution_time, 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if success:
            self._successful_remediations += 1
        else:
            self._failed_remediations += 1
        self._total_remediations += 1
        return result

    def _record_remediation(self, pattern: str, action: str, context: Dict[str, Any],
                            result: Dict[str, Any], confidence: float, decision: str):
        record = {
            "remediation_id": str(uuid.uuid4()),
            "detected_pattern": pattern,
            "action_taken": action,
            "context": {k: v for k, v in context.items() if isinstance(v, (str, int, float, bool, list))},
            "result": result,
            "confidence": confidence,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._remediation_history.append(record)
        if len(self._remediation_history) > self._max_history:
            self._remediation_history = self._remediation_history[-self._max_history:]
        if result.get("success") is not None:
            state_key = self.agent.get_state_key({
                **context, "detected_pattern": pattern,
                "severity": self._patterns.get(pattern, {}).get("severity", "medium"),
            })
            reward = 1.0 if result.get("success") else -0.5
            self.agent.learn(state_key, action, reward, state_key)
            self.agent.decay_exploration()
        logger.info(f"Remediation recorded: pattern={pattern} action={action} confidence={confidence} decision={decision}")

    def trigger_remediation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.detect_and_heal(context)

    def get_history(self, limit: int = 100, pattern: Optional[str] = None,
                    result_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        history = list(self._remediation_history)
        history.reverse()
        if pattern:
            history = [h for h in history if h.get("detected_pattern") == pattern]
        if result_filter:
            history = [h for h in history if h.get("result", {}).get("success") == (result_filter == "success")]
        return history[:limit]

    def get_patterns(self) -> List[Dict[str, Any]]:
        return list(self._patterns.values())

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if pattern_id not in self._patterns:
            return None
        for k, v in updates.items():
            if k != "pattern":
                self._patterns[pattern_id][k] = v
        return self._patterns[pattern_id]

    def get_learned_actions(self) -> List[Dict[str, Any]]:
        return self.agent.get_learned_actions()

    def provide_feedback(self, remediation_id: str, feedback: str, notes: Optional[str] = None) -> Dict[str, Any]:
        for record in self._remediation_history:
            if record["remediation_id"] == remediation_id:
                state_key = self.agent.get_state_key({
                    **record.get("context", {}),
                    "detected_pattern": record["detected_pattern"],
                    "severity": self._patterns.get(record["detected_pattern"], {}).get("severity", "medium"),
                })
                reward_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
                reward = reward_map.get(feedback, 0.0)
                self.agent.learn(state_key, record["action_taken"], reward, state_key)
                record["feedback"] = feedback
                record["feedback_notes"] = notes
                record["feedback_at"] = datetime.utcnow().isoformat()
                return {"status": "updated", "remediation_id": remediation_id, "new_reward": reward}
        return {"error": "Remediation not found"}

    def retrain_model(self) -> Dict[str, Any]:
        recent = self._remediation_history[-1000:]
        trained_count = 0
        for record in recent:
            state_key = self.agent.get_state_key({
                **record.get("context", {}),
                "detected_pattern": record["detected_pattern"],
                "severity": self._patterns.get(record["detected_pattern"], {}).get("severity", "medium"),
            })
            action = record["action_taken"]
            success = record.get("result", {}).get("success")
            if success is not None:
                reward = 1.0 if success else -0.5
                self.agent.learn(state_key, action, reward, state_key)
                trained_count += 1
        self._last_retrain = datetime.utcnow()
        return {
            "status": "retrained",
            "records_used": trained_count,
            "total_history": len(self._remediation_history),
            "learned_actions": len(self.agent.get_learned_actions()),
            "state_action_pairs": self.agent.get_state_action_count(),
            "exploration_rate": self.agent.epsilon,
            "retrained_at": self._last_retrain.isoformat(),
        }

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._remediation_history)
        successful = sum(1 for r in self._remediation_history if r.get("result", {}).get("success") is True)
        failed = sum(1 for r in self._remediation_history if r.get("result", {}).get("success") is False)
        by_pattern = Counter(r["detected_pattern"] for r in self._remediation_history if "detected_pattern" in r)
        by_action = Counter(r["action_taken"] for r in self._remediation_history if "action_taken" in r)
        by_decision = Counter(r["decision"] for r in self._remediation_history if "decision" in r)
        successful_history = [r for r in self._remediation_history if r.get("result", {}).get("success") is True]
        avg_resolution = statistics.mean([r.get("result", {}).get("resolution_seconds", 0) for r in successful_history]) if successful_history else 0
        return {
            "total_remediations": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0.0,
            "patterns_detected": len(self._patterns),
            "total_pattern_matches": sum(p.get("detection_count", 0) for p in self._patterns.values()),
            "learned_actions": len(self.agent.get_learned_actions()),
            "state_action_pairs": self.agent.get_state_action_count(),
            "exploration_rate": round(self.agent.epsilon, 3),
            "auto_remediation_enabled": self._auto_remediation_enabled,
            "confidence_thresholds": self._confidence_thresholds,
            "avg_resolution_seconds": round(avg_resolution, 1),
            "by_pattern": dict(by_pattern.most_common(10)),
            "by_action": dict(by_action.most_common(10)),
            "by_decision": dict(by_decision),
            "last_retrain": self._last_retrain.isoformat() if self._last_retrain else None,
        }

    def get_remediation_detail(self, remediation_id: str) -> Optional[Dict[str, Any]]:
        for record in self._remediation_history:
            if record["remediation_id"] == remediation_id:
                return record
        return None

    def get_pattern_stats(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return None
        related = [r for r in self._remediation_history if r.get("detected_pattern") == pattern_id]
        successful = sum(1 for r in related if r.get("result", {}).get("success") is True)
        return {
            "pattern": pattern_id,
            "total_matches": pattern.get("detection_count", 0),
            "total_remediations": len(related),
            "successful_remediations": successful,
            "success_rate": round(successful / len(related) * 100, 1) if related else 0,
            "recommended_action": pattern.get("recommended_action"),
            "avg_success_rate": pattern.get("avg_success_rate", 0),
            "severity": pattern.get("severity"),
            "auto_heal": pattern.get("auto_heal", False),
        }
