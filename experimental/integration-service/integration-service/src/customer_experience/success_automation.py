"""Customer success automation with automated success plays and trigger-based workflows."""

import json
import logging
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TriggerEvent(str, Enum):
    USER_LOGIN = "user_login"
    USER_INACTIVE_7D = "user_inactive_7d"
    USER_INACTIVE_14D = "user_inactive_14d"
    USER_INACTIVE_30D = "user_inactive_30d"
    TICKET_CREATED = "ticket_created"
    TICKET_RESOLVED = "ticket_resolved"
    TICKET_ESCALATED = "ticket_escalated"
    NPS_DETRACTOR = "nps_detractor"
    NPS_PROMOTER = "nps_promoter"
    ONBOARDING_COMPLETE = "onboarding_complete"
    ONBOARDING_STALLED = "onboarding_stalled"
    FEATURE_ADOPTED = "feature_adopted"
    FEATURE_NOT_ADOPTED = "feature_not_adopted"
    BILLING_PAST_DUE = "billing_past_due"
    BILLING_UPGRADE = "billing_upgrade"
    BILLING_DOWNGRADE = "billing_downgrade"
    RENEWAL_UPCOMING = "renewal_upcoming"
    CONTRACT_EXPIRING = "contract_expiring"
    HEALTH_DECLINED = "health_declined"
    HEALTH_IMPROVED = "health_improved"
    MANUAL = "manual"


class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    SEND_IN_APP = "send_in_app"
    SEND_SLACK = "send_slack"
    CREATE_TASK = "create_task"
    ASSIGN_CSM = "assign_csm"
    UPDATE_TAG = "update_tag"
    TRIGGER_WEBHOOK = "trigger_webhook"
    UPDATE_SCORE = "update_score"
    SCHEDULE_SURVEY = "schedule_survey"
    SET_ATTRIBUTE = "set_attribute"


class PlayStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DRAFT = "draft"
    COMPLETED = "completed"


@dataclass
class PlayAction:
    action_id: str
    action_type: ActionType
    config: Dict[str, Any]
    order: int = 0
    delay_minutes: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuccessPlay:
    play_id: str
    name: str
    description: str
    trigger_event: TriggerEvent
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    cooldown_days: int = 30
    max_executions_per_customer: int = 5
    actions: List[PlayAction] = field(default_factory=list)
    status: PlayStatus = PlayStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_count: int = 0
    success_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlayExecution:
    execution_id: str
    play_id: str
    customer_id: str
    trigger_event: str
    status: str
    actions_completed: int = 0
    actions_total: int = 0
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


PLAY_TEMPLATES = [
    {
        "name": "Re-engagement - 7 Days Inactive",
        "description": "Send re-engagement email when user hasn't logged in for 7 days",
        "trigger_event": "user_inactive_7d",
        "actions": [
            {"action_type": "send_email", "config": {"template": "tpl-inactive-7d", "subject": "We miss you!", "body": "It's been a week since your last visit. Here's what's new..."}},
            {"action_type": "send_in_app", "config": {"title": "Welcome back!", "body": "Check out the latest features"}},
        ],
        "tags": ["re-engagement", "inactive"],
    },
    {
        "name": "NPS Detractor Follow-up",
        "description": "Immediate follow-up when customer gives detractor NPS score",
        "trigger_event": "nps_detractor",
        "actions": [
            {"action_type": "send_email", "config": {"template": "tpl-detractor-followup", "subject": "We want to make things right", "body": "We noticed your recent feedback and want to help..."}},
            {"action_type": "assign_csm", "config": {"priority": "high", "note": "NPS detractor - needs immediate attention"}},
            {"action_type": "create_task", "config": {"task_type": "csm_review", "priority": "high", "due_days": 2}},
        ],
        "tags": ["nps", "feedback", "retention"],
    },
    {
        "name": "Onboarding Stalled",
        "description": "Re-engage customer who stalled during onboarding",
        "trigger_event": "onboarding_stalled",
        "actions": [
            {"action_type": "send_email", "config": {"template": "tpl-onboarding-stalled", "subject": "Need help getting started?", "body": "We noticed you paused during onboarding. Let us help you..."}},
            {"action_type": "assign_csm", "config": {"priority": "medium", "note": "Onboarding stalled"}},
        ],
        "tags": ["onboarding", "activation"],
    },
    {
        "name": "NPS Promoter - Ask for Referral",
        "description": "Capitalize on positive sentiment by asking for referral",
        "trigger_event": "nps_promoter",
        "actions": [
            {"action_type": "send_email", "config": {"template": "tpl-promoter-referral", "subject": "Love to have you! Refer a friend", "body": "You're loving Infra Pilot! Share the love..."}},
            {"action_type": "send_in_app", "config": {"title": "Refer & Earn", "body": "Invite your friends and earn credits!"}},
        ],
        "tags": ["nps", "referral", "growth"],
    },
    {
        "name": "Feature Not Adopted",
        "description": "Educate customer about unadopted features",
        "trigger_event": "feature_not_adopted",
        "actions": [
            {"action_type": "send_email", "config": {"template": "tpl-feature-education", "subject": "Did you know?", "body": "You haven't tried {{feature_name}} yet. Here's how it can help..."}},
            {"action_type": "send_in_app", "config": {"title": "Try {{feature_name}}", "body": "Click here to learn more about this feature"}},
        ],
        "tags": ["adoption", "education"],
    },
    {
        "name": "Renewal Reminder",
        "description": "Proactive renewal outreach before contract expires",
        "trigger_event": "renewal_upcoming",
        "actions": [
            {"action_type": "send_email", "config": {"template": "tpl-renewal", "subject": "Your subscription is renewing soon", "body": "Your plan will renew in {{days}} days. Here's a summary of your usage..."}},
            {"action_type": "create_task", "config": {"task_type": "renewal_review", "priority": "normal", "due_days": 7}},
        ],
        "tags": ["renewal", "retention"],
    },
    {
        "name": "Health Declined - Alert CSM",
        "description": "Alert customer success manager when health score declines",
        "trigger_event": "health_declined",
        "actions": [
            {"action_type": "assign_csm", "config": {"priority": "urgent", "note": "Customer health score declining"}},
            {"action_type": "send_in_app", "config": {"title": "Health Alert", "body": "Customer health score is declining. Please review and take action."}},
            {"action_type": "create_task", "config": {"task_type": "health_review", "priority": "high", "due_days": 1}},
        ],
        "tags": ["health", "csm", "alert"],
    },
]


class SuccessAutomationService:
    def __init__(self, storage_path: str = "success_automation_data.json"):
        self.storage_path = storage_path
        self.plays: Dict[str, SuccessPlay] = {}
        self.executions: Dict[str, PlayExecution] = {}
        self.customer_state: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._init_default_plays()
        self._load_data()

    def _init_default_plays(self):
        for i, template in enumerate(PLAY_TEMPLATES):
            play_id = f"PLAY-{uuid.uuid4().hex[:6].upper()}"
            actions = []
            for j, a in enumerate(template["actions"]):
                actions.append(PlayAction(
                    action_id=f"act-{uuid.uuid4().hex[:6]}",
                    action_type=ActionType(a["action_type"]),
                    config=a["config"],
                    order=j + 1,
                ))
            play = SuccessPlay(
                play_id=play_id,
                name=template["name"],
                description=template["description"],
                trigger_event=TriggerEvent(template["trigger_event"]),
                actions=actions,
                status=PlayStatus.ACTIVE,
                tags=template.get("tags", []),
            )
            self.plays[play_id] = play

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for pdata in data.get("plays", []):
                        actions = [PlayAction(**a) for a in pdata.get("actions", [])]
                        pdata["actions"] = actions
                        self.plays[pdata["play_id"]] = SuccessPlay(**pdata)
                    for edata in data.get("executions", []):
                        self.executions[edata["execution_id"]] = PlayExecution(**edata)
                    self.customer_state = defaultdict(dict, data.get("customer_state", {}))
            except Exception as e:
                logger.warning(f"Failed to load success automation data: {e}")

    def _save_data(self):
        try:
            data = {
                "plays": [p.to_dict() for p in self.plays.values()],
                "executions": [e.to_dict() for e in self.executions.values()],
                "customer_state": dict(self.customer_state),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save success automation data: {e}")

    def create_play(
        self, name: str, description: str, trigger_event: str,
        actions: List[Dict[str, Any]], tags: Optional[List[str]] = None,
        trigger_conditions: Optional[Dict[str, Any]] = None,
        cooldown_days: int = 30,
    ) -> SuccessPlay:
        play_id = f"PLAY-{uuid.uuid4().hex[:6].upper()}"
        play_actions = []
        for i, a in enumerate(actions):
            play_actions.append(PlayAction(
                action_id=f"act-{uuid.uuid4().hex[:6]}",
                action_type=ActionType(a["action_type"]),
                config=a.get("config", {}),
                order=i + 1,
                delay_minutes=a.get("delay_minutes", 0),
                conditions=a.get("conditions", {}),
            ))
        play = SuccessPlay(
            play_id=play_id, name=name, description=description,
            trigger_event=TriggerEvent(trigger_event),
            trigger_conditions=trigger_conditions or {},
            cooldown_days=cooldown_days,
            actions=play_actions, tags=tags or [],
        )
        self.plays[play_id] = play
        self._save_data()
        return play

    def evaluate_trigger(self, event: str, customer_id: str, event_data: Optional[Dict[str, Any]] = None) -> List[PlayExecution]:
        triggered: List[PlayExecution] = []
        for play in self.plays.values():
            if play.status != PlayStatus.ACTIVE:
                continue
            if play.trigger_event.value != event:
                continue
            if self._is_throttled(play, customer_id):
                continue
            if play.trigger_conditions and not self._check_conditions(play.trigger_conditions, event_data or {}):
                continue
            execution = self._execute_play(play, customer_id, event, event_data)
            triggered.append(execution)
        return triggered

    def _is_throttled(self, play: SuccessPlay, customer_id: str) -> bool:
        recent = [
            e for e in self.executions.values()
            if e.play_id == play.play_id and e.customer_id == customer_id
        ]
        if len(recent) >= play.max_executions_per_customer:
            return True
        if recent and play.cooldown_days > 0:
            last = datetime.fromisoformat(recent[-1].started_at)
            if datetime.utcnow() - last < timedelta(days=play.cooldown_days):
                return True
        return False

    def _check_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        for key, value in conditions.items():
            if key in event_data:
                if isinstance(value, dict):
                    op = value.get("operator", "eq")
                    target = value.get("value")
                    actual = event_data[key]
                    if op == "eq" and actual != target:
                        return False
                    if op == "gt" and not (actual > target):
                        return False
                    if op == "lt" and not (actual < target):
                        return False
                    if op == "gte" and not (actual >= target):
                        return False
                    if op == "lte" and not (actual <= target):
                        return False
                    if op == "in" and actual not in target:
                        return False
                elif event_data.get(key) != value:
                    return False
        return True

    def _execute_play(self, play: SuccessPlay, customer_id: str, event: str, event_data: Optional[Dict[str, Any]]) -> PlayExecution:
        execution_id = f"EXEC-{uuid.uuid4().hex[:8].upper()}"
        execution = PlayExecution(
            execution_id=execution_id, play_id=play.play_id,
            customer_id=customer_id, trigger_event=event,
            status="running", actions_total=len(play.actions),
            metadata=event_data or {},
        )
        self.executions[execution_id] = execution
        play.execution_count += 1
        results = []
        for action in play.actions:
            try:
                result = self._perform_action(action, customer_id, event_data)
                results.append({"action_id": action.action_id, "status": "completed", "result": result})
                execution.actions_completed += 1
            except Exception as e:
                logger.error(f"Action {action.action_id} failed: {e}")
                results.append({"action_id": action.action_id, "status": "failed", "error": str(e)})
        execution.results = results
        execution.status = "completed"
        execution.completed_at = datetime.utcnow().isoformat()
        execution.error = None if all(r["status"] == "completed" for r in results) else "some_actions_failed"
        if execution.error is None:
            play.success_count += 1
        self._save_data()
        return execution

    def _perform_action(self, action: PlayAction, customer_id: str, event_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        config = action.config
        if action.action_type == ActionType.SEND_EMAIL:
            return self._send_email(customer_id, config)
        elif action.action_type == ActionType.SEND_IN_APP:
            return self._send_in_app(customer_id, config)
        elif action.action_type == ActionType.SEND_SLACK:
            return self._send_slack(customer_id, config)
        elif action.action_type == ActionType.CREATE_TASK:
            return self._create_task(customer_id, config)
        elif action.action_type == ActionType.ASSIGN_CSM:
            return self._assign_csm(customer_id, config)
        elif action.action_type == ActionType.TRIGGER_WEBHOOK:
            return {"webhook_triggered": True, "url": config.get("url", "")}
        elif action.action_type == ActionType.UPDATE_TAG:
            return {"tag_updated": config.get("tag", "")}
        elif action.action_type == ActionType.SCHEDULE_SURVEY:
            return {"survey_scheduled": config.get("survey_type", "")}
        return {"status": "not_implemented"}

    def _send_email(self, customer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Sending email to {customer_id}: {config.get('subject', '')}")
        return {"channel": "email", "subject": config.get("subject", ""), "status": "queued"}

    def _send_in_app(self, customer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Sending in-app notification to {customer_id}: {config.get('title', '')}")
        return {"channel": "in_app", "title": config.get("title", ""), "status": "sent"}

    def _send_slack(self, customer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Sending slack notification for {customer_id}: {config.get('message', '')}")
        return {"channel": "slack", "status": "queued"}

    def _create_task(self, customer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Creating task for {customer_id}: {config.get('task_type', '')}")
        return {"task_type": config.get("task_type", ""), "priority": config.get("priority", "normal"), "status": "created"}

    def _assign_csm(self, customer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Assigning CSM for {customer_id}: {config.get('note', '')}")
        return {"assignment": "csm_assigned", "priority": config.get("priority", "normal"), "note": config.get("note", "")}

    def get_play(self, play_id: str) -> Optional[SuccessPlay]:
        return self.plays.get(play_id)

    def update_play_status(self, play_id: str, status: str) -> Optional[SuccessPlay]:
        play = self.plays.get(play_id)
        if not play:
            return None
        play.status = PlayStatus(status)
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return play

    def list_plays(self, trigger_event: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.plays.values())
        if trigger_event:
            results = [p for p in results if p.trigger_event.value == trigger_event]
        if status:
            results = [p for p in results if p.status.value == status]
        return [p.to_dict() for p in results]

    def get_executions(self, play_id: Optional[str] = None, customer_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        results = list(self.executions.values())
        if play_id:
            results = [e for e in results if e.play_id == play_id]
        if customer_id:
            results = [e for e in results if e.customer_id == customer_id]
        results.sort(key=lambda e: e.started_at, reverse=True)
        return [e.to_dict() for e in results[:limit]]

    def update_customer_state(self, customer_id: str, state_updates: Dict[str, Any]):
        self.customer_state[customer_id].update(state_updates)
        self._save_data()

    def get_customer_state(self, customer_id: str) -> Dict[str, Any]:
        return dict(self.customer_state.get(customer_id, {}))

    def get_stats(self) -> Dict[str, Any]:
        total_plays = len(self.plays)
        active_plays = sum(1 for p in self.plays.values() if p.status == PlayStatus.ACTIVE)
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions.values() if e.error is None)
        return {
            "total_plays": total_plays,
            "active_plays": active_plays,
            "total_executions": total_executions,
            "successful_executions": successful,
            "success_rate": round(successful / max(total_executions, 1), 3),
            "trigger_events": list(TriggerEvent),
        }

    def get_play(self, play_id: str) -> Optional[Dict[str, Any]]:
        play = self.plays.get(play_id)
        return play.to_dict() if play else None

    def update_play(self, play_id: str, updates: Dict[str, Any]) -> bool:
        play = self.plays.get(play_id)
        if not play: return False
        if "name" in updates: play.name = updates["name"]
        if "description" in updates: play.description = updates["description"]
        if "trigger_event" in updates: play.trigger_event = TriggerEvent(updates["trigger_event"]) if isinstance(updates["trigger_event"], str) else updates["trigger_event"]
        if "actions" in updates: play.actions = updates["actions"]
        if "conditions" in updates: play.conditions = updates["conditions"]
        if "active" in updates: play.active = updates["active"]
        play.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def delete_play(self, play_id: str) -> bool:
        if play_id in self.plays:
            del self.plays[play_id]
            self._save_data()
            return True
        return False

    def activate_play(self, play_id: str) -> bool:
        play = self.plays.get(play_id)
        if not play: return False
        play.active = True
        self._save_data()
        return True

    def deactivate_play(self, play_id: str) -> bool:
        play = self.plays.get(play_id)
        if not play: return False
        play.active = False
        self._save_data()
        return True

    def clone_play(self, play_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        play = self.plays.get(play_id)
        if not play: return None
        new_id = str(uuid.uuid4())[:8]
        cloned = SuccessPlay(play_id=new_id, name=new_name, description=play.description, trigger_event=play.trigger_event, actions=[{"type": a["type"], "config": dict(a.get("config", {}))} for a in play.actions], conditions=[dict(c) for c in play.conditions], active=False)
        self.plays[new_id] = cloned
        self._save_data()
        return cloned.to_dict()

    def get_execution_log(self, play_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        executions = [e for e in self.execution_history if e.play_id == play_id]
        executions.sort(key=lambda e: e.executed_at, reverse=True)
        return [{"execution_id": e.execution_id, "trigger_event": e.trigger_event.value, "input_data": e.input_data, "result": e.result, "status": e.status, "executed_at": e.executed_at.isoformat(), "error": e.error} for e in executions[:limit]]

    def get_play_stats(self, play_id: str) -> Optional[Dict[str, Any]]:
        play = self.plays.get(play_id)
        if not play: return None
        executions = [e for e in self.execution_history if e.play_id == play_id]
        successful = sum(1 for e in executions if e.status == "success")
        failed = sum(1 for e in executions if e.status == "failed")
        return {"play_id": play_id, "name": play.name, "active": play.active, "total_executions": len(executions), "successful": successful, "failed": failed, "success_rate": round(successful / max(len(executions), 1) * 100, 1), "last_execution": executions[0].executed_at.isoformat() if executions else None}

    def search_plays(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [p.to_dict() for p in self.plays.values() if q in p.name.lower() or q in p.description.lower() or q in p.trigger_event.value]
        return results[:20]

    def test_play(self, play_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        play = self.plays.get(play_id)
        if not play: return {"error": "Play not found"}
        conditions_met = all(self._evaluate_condition(c, test_data) for c in play.conditions)
        if not conditions_met:
            return {"play_id": play_id, "conditions_met": False, "actions_executed": 0, "message": "Conditions not met"}
        executed = 0
        for action in play.actions:
            try:
                executed += 1
            except Exception:
                continue
        return {"play_id": play_id, "conditions_met": True, "actions_executed": executed, "estimated_actions": len(play.actions)}

    def get_trigger_summary(self) -> Dict[str, Any]:
        by_trigger = defaultdict(int)
        for e in self.execution_history:
            by_trigger[e.trigger_event.value] += 1
        return {"total_executions": len(self.execution_history), "by_trigger": dict(by_trigger), "active_plays": sum(1 for p in self.plays.values() if p.active), "inactive_plays": sum(1 for p in self.plays.values() if not p.active)}

    def get_failed_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        failed = [e for e in self.execution_history if e.status == "failed"]
        failed.sort(key=lambda e: e.executed_at, reverse=True)
        return [{"execution_id": e.execution_id, "play_id": e.play_id, "trigger_event": e.trigger_event.value, "error": e.error, "executed_at": e.executed_at.isoformat()} for e in failed[:limit]]

    def retry_failed(self, execution_id: str) -> bool:
        execution = next((e for e in self.execution_history if e.execution_id == execution_id and e.status == "failed"), None)
        if not execution: return False
        execution.status = "retried"
        new_exec = ExecutionRecord(execution_id=str(uuid.uuid4())[:8], play_id=execution.play_id, trigger_event=execution.trigger_event, input_data=execution.input_data, status="pending")
        self.execution_history.append(new_exec)
        self._save_data()
        return True

    def get_play_recommendations(self) -> List[Dict[str, Any]]:
        return [{"type": "underutilized", "message": "Some plays have zero executions", "count": sum(1 for p in self.plays.values() if not any(e.play_id == p.play_id for e in self.execution_history))},
                {"type": "high_failure", "message": "Plays with high failure rate", "count": sum(1 for p in self.plays.values() if self.get_play_stats(p.play_id) and self.get_play_stats(p.play_id)["failed"] > 5)}]

    def export_automation_report(self) -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(), "plays": [p.to_dict() for p in self.plays.values()], "execution_summary": self.get_summary(), "recent_executions": [e.to_dict() for e in self.execution_history[-50:]]}

    def add_play_action(self, play_id: str, action_type: str, config: Dict[str, Any], order: Optional[int] = None) -> Optional[PlayAction]:
        play = self.plays.get(play_id)
        if not play:
            return None
        action_id = f"act-{uuid.uuid4().hex[:6]}"
        action = PlayAction(action_id=action_id, action_type=ActionType(action_type), config=config, order=order or len(play.actions) + 1)
        play.actions.append(action)
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return action

    def remove_play_action(self, play_id: str, action_id: str) -> bool:
        play = self.plays.get(play_id)
        if not play:
            return False
        play.actions = [a for a in play.actions if a.action_id != action_id]
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def reorder_actions(self, play_id: str, action_ids: List[str]) -> bool:
        play = self.plays.get(play_id)
        if not play:
            return False
        action_map = {a.action_id: a for a in play.actions}
        reordered = []
        for aid in action_ids:
            if aid in action_map:
                action_map[aid].order = len(reordered) + 1
                reordered.append(action_map[aid])
        remaining = [a for a in play.actions if a.action_id not in action_ids]
        for a in remaining:
            a.order = len(reordered) + 1
            reordered.append(a)
        play.actions = reordered
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_play_analytics(self, play_id: str) -> Optional[Dict[str, Any]]:
        play = self.plays.get(play_id)
        if not play:
            return None
        executions = [e for e in self.executions.values() if e.play_id == play_id]
        completed = [e for e in executions if e.status == "completed"]
        failed = [e for e in executions if e.status == "failed"]
        avg_duration = 0
        if completed:
            durations = []
            for e in completed:
                if e.started_at and e.completed_at:
                    start = datetime.fromisoformat(e.started_at)
                    end = datetime.fromisoformat(e.completed_at)
                    durations.append((end - start).total_seconds())
            avg_duration = sum(durations) / len(durations) if durations else 0
        return {
            "play_id": play_id,
            "name": play.name,
            "status": play.status.value,
            "total_executions": len(executions),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": round(len(completed) / max(len(executions), 1), 3) if executions else 0,
            "avg_duration_seconds": round(avg_duration, 1),
            "trigger_event": play.trigger_event.value,
            "cooldown_days": play.cooldown_days,
            "tags": play.tags,
        }

    def get_trigger_performance(self, trigger_event: Optional[str] = None) -> List[Dict[str, Any]]:
        by_trigger = defaultdict(lambda: {"executions": 0, "success": 0, "failure": 0})
        for e in self.executions.values():
            key = e.trigger_event
            by_trigger[key]["executions"] += 1
            if e.error is None:
                by_trigger[key]["success"] += 1
            else:
                by_trigger[key]["failure"] += 1
        results = [{"trigger": k, **v, "success_rate": round(v["success"] / max(v["executions"], 1), 3)} for k, v in by_trigger.items()]
        if trigger_event:
            results = [r for r in results if r["trigger"] == trigger_event]
        results.sort(key=lambda r: r["executions"], reverse=True)
        return results

    def get_customer_plays(self, customer_id: str) -> List[Dict[str, Any]]:
        executions = [e for e in self.executions.values() if e.customer_id == customer_id]
        play_ids = set(e.play_id for e in executions)
        return [p.to_dict() for pid, p in self.plays.items() if pid in play_ids]

    def get_customer_executions(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        executions = [e for e in self.executions.values() if e.customer_id == customer_id]
        executions.sort(key=lambda e: e.started_at, reverse=True)
        return [e.to_dict() for e in executions[:limit]]

    def dry_run_play(self, play_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.test_play(play_id, test_data)

    def get_play_recommendations(self) -> List[Dict[str, Any]]:
        recs = []
        unused = [p for p in self.plays.values() if p.execution_count == 0 and p.status == PlayStatus.ACTIVE]
        if unused:
            recs.append({"type": "unused_plays", "count": len(unused), "message": f"{len(unused)} active plays have never executed", "play_ids": [p.play_id for p in unused]})
        high_failure = [p for p in self.plays.values() if p.execution_count > 0 and p.success_count / p.execution_count < 0.5]
        if high_failure:
            recs.append({"type": "high_failure", "count": len(high_failure), "message": f"{len(high_failure)} plays have >50% failure rate", "play_ids": [p.play_id for p in high_failure]})
        return recs

    def bulk_activate_plays(self, play_ids: List[str]) -> int:
        count = 0
        for pid in play_ids:
            play = self.plays.get(pid)
            if play and play.status != PlayStatus.ACTIVE:
                play.status = PlayStatus.ACTIVE
                play.updated_at = datetime.utcnow().isoformat()
                count += 1
        if count:
            self._save_data()
        return count

    def bulk_deactivate_plays(self, play_ids: List[str]) -> int:
        count = 0
        for pid in play_ids:
            play = self.plays.get(pid)
            if play and play.status == PlayStatus.ACTIVE:
                play.status = PlayStatus.PAUSED
                play.updated_at = datetime.utcnow().isoformat()
                count += 1
        if count:
            self._save_data()
        return count

    def get_execution_timeline(self, play_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        executions = [e for e in self.executions.values() if e.play_id == play_id]
        executions.sort(key=lambda e: e.started_at, reverse=True)
        return [{
            "execution_id": e.execution_id,
            "customer_id": e.customer_id,
            "trigger_event": e.trigger_event,
            "status": e.status,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
            "actions_completed": e.actions_completed,
            "actions_total": e.actions_total,
        } for e in executions[:limit]]

    def get_automation_summary(self) -> Dict[str, Any]:
        total_plays = len(self.plays)
        active = sum(1 for p in self.plays.values() if p.status == PlayStatus.ACTIVE)
        total_exec = len(self.executions)
        successful = sum(1 for e in self.executions.values() if e.error is None)
        unique_customers = len(set(e.customer_id for e in self.executions.values()))
        return {
            "total_plays": total_plays,
            "active_plays": active,
            "pct_active": round(active / max(total_plays, 1) * 100, 1),
            "total_executions": total_exec,
            "successful_executions": successful,
            "success_rate": round(successful / max(total_exec, 1), 3),
            "unique_customers_affected": unique_customers,
            "trigger_events_covered": len(set(p.trigger_event.value for p in self.plays.values())),
        }

    def search_executions(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for e in self.executions.values():
            if q in e.customer_id.lower() or q in e.play_id.lower() or q in e.trigger_event:
                results.append(e.to_dict())
        results.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return results[:limit]

    def get_execution_detail(self, execution_id: str) -> Optional[Dict[str, Any]]:
        e = self.executions.get(execution_id)
        return e.to_dict() if e else None

    def retry_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        execution = self.executions.get(execution_id)
        if not execution or execution.error is None:
            return None
        play = self.plays.get(execution.play_id)
        if not play:
            return None
        new_execution = self._execute_play(play, execution.customer_id, execution.trigger_event, execution.metadata)
        return new_execution.to_dict()

    def get_customer_automation_state(self, customer_id: str) -> Dict[str, Any]:
        return self.get_customer_state(customer_id)

    def update_customer_attribute(self, customer_id: str, key: str, value: Any) -> bool:
        self.customer_state[customer_id][key] = value
        self._save_data()
        return True

    def evaluate_all_triggers(self, event: str, event_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        triggered = 0
        results = []
        for play in self.plays.values():
            if play.status != PlayStatus.ACTIVE:
                continue
            if play.trigger_event.value != event:
                continue
            execution = self._execute_play(play, event_data.get("customer_id", "unknown") if event_data else "unknown", event, event_data)
            results.append(execution.to_dict())
            triggered += 1
        return {"trigger_event": event, "plays_triggered": triggered, "executions": results}

    def get_play_template(self, name: str) -> Optional[Dict[str, Any]]:
        for template in PLAY_TEMPLATES:
            if template["name"].lower() == name.lower():
                return dict(template)
        return None

    def create_play_from_template(self, template_name: str, customizations: Optional[Dict[str, Any]] = None) -> Optional[SuccessPlay]:
        template = self.get_play_template(template_name)
        if not template:
            return None
        actions = template["actions"]
        if customizations and "actions" in customizations:
            actions = customizations["actions"]
        return self.create_play(
            name=customizations.get("name", template["name"]) if customizations else template["name"],
            description=template["description"],
            trigger_event=template["trigger_event"],
            actions=actions,
            tags=template.get("tags", []),
        )

    def get_automation_audit_log(self, days: int = 7) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        changes = []
        for p in self.plays.values():
            if p.updated_at >= cutoff:
                changes.append({"play_id": p.play_id, "name": p.name, "action": "updated", "timestamp": p.updated_at})
            if p.created_at >= cutoff:
                changes.append({"play_id": p.play_id, "name": p.name, "action": "created", "timestamp": p.created_at})
        changes.sort(key=lambda c: c["timestamp"], reverse=True)
        return changes

    def enable_play(self, play_id: str) -> bool:
        play = self.plays.get(play_id)
        if not play:
            return False
        play.status = PlayStatus.ACTIVE
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def disable_play(self, play_id: str) -> bool:
        play = self.plays.get(play_id)
        if not play:
            return False
        play.status = PlayStatus.INACTIVE
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_execution_errors(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        errors = [e.to_dict() for e in self.executions.values() if e.error is not None and e.started_at >= cutoff]
        errors.sort(key=lambda e: e.get("started_at", ""), reverse=True)
        return errors[:limit]

    def bulk_enable_plays(self, play_ids: List[str]) -> Dict[str, Any]:
        succeeded = 0
        for pid in play_ids:
            if self.enable_play(pid):
                succeeded += 1
        return {"enabled": succeeded, "total": len(play_ids)}

    def bulk_disable_plays(self, play_ids: List[str]) -> Dict[str, Any]:
        succeeded = 0
        for pid in play_ids:
            if self.disable_play(pid):
                succeeded += 1
        return {"disabled": succeeded, "total": len(play_ids)}

    def get_play_statistics(self) -> Dict[str, Any]:
        total = len(self.plays)
        active = sum(1 for p in self.plays.values() if p.status == PlayStatus.ACTIVE)
        total_exec = len(self.executions)
        error_count = sum(1 for e in self.executions.values() if e.error is not None)
        return {
            "total_plays": total,
            "active_plays": active,
            "inactive": total - active,
            "total_executions": total_exec,
            "error_count": error_count,
            "error_rate": round(error_count / max(total_exec, 1), 3),
            "trigger_distribution": dict(Counter(p.trigger_event.value for p in self.plays.values())),
        }

    def get_customer_execution_history(self, customer_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        executions = [e.to_dict() for e in self.executions.values() if e.customer_id == customer_id]
        executions.sort(key=lambda e: e.get("started_at", ""), reverse=True)
        return executions[:limit]

    def get_play_executions(self, play_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        executions = [e.to_dict() for e in self.executions.values() if e.play_id == play_id]
        executions.sort(key=lambda e: e.get("started_at", ""), reverse=True)
        return executions[:limit]

    def retry_all_failed(self) -> Dict[str, Any]:
        failed = [e for e in self.executions.values() if e.error is not None]
        retried = 0
        for e in failed:
            play = self.plays.get(e.play_id)
            if play:
                new_execution = self._execute_play(play, e.customer_id, e.trigger_event, e.metadata)
                if new_execution:
                    retried += 1
        return {"retried": retried, "total_failed": len(failed)}

    def get_play_suggestions(self) -> List[Dict[str, Any]]:
        suggestions = []
        for template in PLAY_TEMPLATES:
            exists = any(p.name.lower() == template["name"].lower() for p in self.plays.values())
            if not exists:
                suggestions.append({"template_name": template["name"], "description": template["description"], "trigger_event": template["trigger_event"]})
        return suggestions

    def update_play_schedule(self, play_id: str, schedule: Dict[str, Any]) -> Optional[SuccessPlay]:
        play = self.plays.get(play_id)
        if not play:
            return None
        play.cooldown_days = schedule.get("cooldown_days", play.cooldown_days)
        play.max_executions = schedule.get("max_executions", play.max_executions)
        play.time_restriction = schedule.get("time_restriction", play.time_restriction)
        play.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return play

    def get_play_performance(self, play_id: str) -> Dict[str, Any]:
        play = self.plays.get(play_id)
        if not play:
            return {}
        executions = [e for e in self.executions.values() if e.play_id == play_id]
        total = len(executions)
        errors = sum(1 for e in executions if e.error is not None)
        avg_duration = sum(e.execution_time_ms for e in executions if e.execution_time_ms) / max(total - errors, 1) if total > errors else 0
        return {"play_id": play_id, "name": play.name, "total_executions": total, "errors": errors, "success_rate": round((total - errors) / max(total, 1), 3), "avg_execution_time_ms": round(avg_duration, 1)}

    def export_automation_config(self) -> Dict[str, Any]:
        return {"plays": [p.to_dict() for p in self.plays.values()], "templates": PLAY_TEMPLATES, "exported_at": datetime.utcnow().isoformat()}


class SuccessAutomationBatchProcessor:
    def __init__(self, service: SuccessAutomationService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_create_plays(self, plays_data: List[Dict[str, Any]]) -> List[SuccessPlay]:
        results = []
        for data in plays_data:
            try:
                play = self.service.create_play(
                    name=data["name"], description=data.get("description", ""),
                    trigger_event=data.get("trigger_event", "ticket_closed"),
                    conditions=data.get("conditions", {}),
                    actions=data.get("actions", []),
                    created_by=data.get("created_by", ""),
                )
                results.append(play)
                self.batch_log.append({"action": "create_play", "play_id": play.play_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "create_play", "name": data.get("name"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_executions(executions: List[PlayExecution], page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
    filtered = [e for e in executions if e.error is None] if status == "success" else ([e for e in executions if e.error is not None] if status == "error" else executions)
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [e.to_dict() for e in filtered[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_automation_efficiency(service: SuccessAutomationService) -> Dict[str, Any]:
    executions = list(service.executions.values())
    if not executions:
        return {"total": 0}
    successful = [e for e in executions if e.error is None]
    failed = [e for e in executions if e.error is not None]
    durations = [e.execution_time_ms for e in successful if e.execution_time_ms]
    return {
        "total_executions": len(executions),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": round(len(successful) / max(len(executions), 1), 3),
        "avg_duration_ms": round(sum(durations) / max(len(durations), 1), 1) if durations else 0,
    }


class SuccessAutomationAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


def validate_automation_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    return errors


def get_most_triggered_plays(service: SuccessAutomationService, limit: int = 10) -> List[Dict[str, Any]]:
    play_counts: Dict[str, int] = {}
    for e in service.executions.values():
        play_counts[e.play_id] = play_counts.get(e.play_id, 0) + 1
    sorted_plays = sorted(play_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    result = []
    for play_id, count in sorted_plays:
        play = service.plays.get(play_id)
        if play:
            result.append({"play_id": play_id, "name": play.name, "execution_count": count})
    return result


def merge_automation_customers(service: SuccessAutomationService, source: str, target: str) -> int:
    count = 0
    for e in service.executions.values():
        if e.customer_id == source:
            e.customer_id = target
            count += 1
    if count:
        service._save_data()
    return count

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
        return {"total_customers": 0, "active_users": 0, "nps_score": 0.0, "satisfaction_rate": 0.0}

    def validate_engagement(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class CXResult(BaseModel):
    success: bool = True
    operation: str = ""
    customer_id: Optional[str] = None
    interaction_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CXBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    campaign: str = Field(default="general")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    responded: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_response(self) -> None:
        self.responded += 1

    def complete(self) -> None:
        self.status = "completed"

class CustomerProfile(BaseModel):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    tier: str = Field(default="standard")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    total_spend: float = Field(default=0.0)
    interaction_count: int = Field(default=0)
    nps_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

class CustomerRepository:
    def __init__(self) -> None:
        self._customers: Dict[str, CustomerProfile] = {}

    def create(self, name: str, email: str, tier: str = "standard") -> CustomerProfile:
        customer = CustomerProfile(name=name, email=email, tier=tier)
        self._customers[customer.customer_id] = customer
        return customer

    def get(self, customer_id: str) -> Optional[CustomerProfile]:
        return self._customers.get(customer_id)

    def update_last_active(self, customer_id: str) -> bool:
        customer = self._customers.get(customer_id)
        if customer:
            customer.last_active = datetime.utcnow()
            customer.interaction_count += 1
            return True
        return False

    def get_by_tier(self, tier: str) -> List[CustomerProfile]:
        return [c for c in self._customers.values() if c.tier == tier]

    def get_at_risk(self, days_inactive: int = 30) -> List[CustomerProfile]:
        cutoff = datetime.utcnow() - timedelta(days=days_inactive)
        return [c for c in self._customers.values() if c.last_active and c.last_active < cutoff]

    def get_statistics(self) -> Dict[str, Any]:
        customers = list(self._customers.values())
        return {"total": len(customers), "avg_spend": round(sum(c.total_spend for c in customers) / max(len(customers), 1), 2),
                "by_tier": {t: sum(1 for c in customers if c.tier == t) for t in set(c.tier for c in customers)},
                "at_risk": len(self.get_at_risk())}

class NPSRecord(BaseModel):
    survey_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    score: int = Field(default=0, ge=0, le=10)
    comment: str = ""
    category: str = Field(default="general")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    def is_promoter(self) -> bool:
        return self.score >= 9

    def is_passive(self) -> bool:
        return 7 <= self.score <= 8

    def is_detractor(self) -> bool:
        return self.score <= 6

class NPSTracker:
    def __init__(self) -> None:
        self._surveys: List[NPSRecord] = []

    def record(self, customer_id: str, score: int, comment: str = "", category: str = "general") -> NPSRecord:
        survey = NPSRecord(customer_id=customer_id, score=score, comment=comment, category=category)
        self._surveys.append(survey)
        return survey

    def get_score(self) -> float:
        total = len(self._surveys)
        if total == 0:
            return 0.0
        promoters = sum(1 for s in self._surveys if s.is_promoter())
        detractors = sum(1 for s in self._surveys if s.is_detractor())
        return round((promoters - detractors) / total * 100, 1)

    def get_by_category(self, category: str) -> List[NPSRecord]:
        return [s for s in self._surveys if s.category == category]

    def get_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [s for s in self._surveys if s.submitted_at >= cutoff]
        return {"period_days": days, "surveys": len(recent),
                "score": round((sum(1 for s in recent if s.is_promoter()) - sum(1 for s in recent if s.is_detractor())) / max(len(recent), 1) * 100, 1),
                "promoters": sum(1 for s in recent if s.is_promoter()),
                "passives": sum(1 for s in recent if s.is_passive()),
                "detractors": sum(1 for s in recent if s.is_detractor())}

class TicketRecord(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    subject: str
    description: str = ""
    priority: str = Field(default="medium")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    satisfaction_score: Optional[int] = None

class TicketSystem:
    def __init__(self) -> None:
        self._tickets: Dict[str, TicketRecord] = {}

    def create(self, customer_id: str, subject: str, description: str = "", priority: str = "medium") -> TicketRecord:
        ticket = TicketRecord(customer_id=customer_id, subject=subject, description=description, priority=priority)
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def resolve(self, ticket_id: str, satisfaction: Optional[int] = None) -> bool:
        ticket = self._tickets.get(ticket_id)
        if ticket and ticket.status == "open":
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow()
            ticket.satisfaction_score = satisfaction
            return True
        return False

    def get_open(self) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.status == "open"]

    def get_by_priority(self, priority: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.priority == priority]

    def get_by_customer(self, customer_id: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.customer_id == customer_id]

    def get_statistics(self) -> Dict[str, Any]:
        tickets = list(self._tickets.values())
        open_tickets = self.get_open()
        resolved = [t for t in tickets if t.status == "resolved"]
        avg_resolution = 0.0
        if resolved:
            durations = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved if t.resolved_at]
            avg_resolution = round(sum(durations) / len(durations), 1) if durations else 0.0
        return {"total": len(tickets), "open": len(open_tickets), "resolved": len(resolved),
                "avg_resolution_hours": avg_resolution,
                "by_priority": {p: sum(1 for t in tickets if t.priority == p) for p in set(t.priority for t in tickets)},
                "avg_satisfaction": round(sum(t.satisfaction_score for t in resolved if t.satisfaction_score) / max(len([t for t in resolved if t.satisfaction_score]), 1), 1)}

class OnboardingStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    step_name: str
    status: str = Field(default="pending")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class OnboardingWorkflow:
    def __init__(self) -> None:
        self._steps: Dict[str, OnboardingStep] = {}

    def add_step(self, customer_id: str, step_name: str) -> OnboardingStep:
        step = OnboardingStep(customer_id=customer_id, step_name=step_name)
        self._steps[step.step_id] = step
        return step

    def start_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "pending":
            step.status = "in_progress"
            step.started_at = datetime.utcnow()
            return True
        return False

    def complete_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "in_progress":
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_minutes = int((step.completed_at - step.started_at).total_seconds() / 60) if step.started_at else 0
            return True
        return False

    def get_progress(self, customer_id: str) -> Dict[str, Any]:
        steps = [s for s in self._steps.values() if s.customer_id == customer_id]
        completed = sum(1 for s in steps if s.status == "completed")
        return {"customer_id": customer_id, "total_steps": len(steps),
                "completed": completed, "in_progress": sum(1 for s in steps if s.status == "in_progress"),
                "pending": sum(1 for s in steps if s.status == "pending"),
                "progress_pct": round(completed / max(len(steps), 1) * 100, 1)}
