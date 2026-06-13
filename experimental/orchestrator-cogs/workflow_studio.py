import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    LOGIC = "logic"
    INTEGRATION = "integration"
    TRANSFORM = "transform"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    ARCHIVED = "archived"


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


TRIGGER_NODES = [
    {"type": "webhook_trigger", "name": "Webhook Trigger", "category": "triggers",
     "description": "Starts workflow on HTTP webhook call", "config_schema": {
         "properties": {
             "path": {"type": "string", "description": "Webhook path"},
             "method": {"type": "string", "enum": ["POST", "PUT", "PATCH"]},
             "secret": {"type": "string", "description": "Optional secret for verification"},
         },
         "required": ["path", "method"],
     }},
    {"type": "schedule_trigger", "name": "Schedule Trigger", "category": "triggers",
     "description": "Starts workflow on cron schedule", "config_schema": {
         "properties": {
             "cron": {"type": "string", "description": "Cron expression"},
             "timezone": {"type": "string", "default": "UTC"},
         },
         "required": ["cron"],
     }},
    {"type": "event_trigger", "name": "Event Trigger", "category": "triggers",
     "description": "Starts workflow on system event", "config_schema": {
         "properties": {
             "event_type": {"type": "string", "description": "Event type to match"},
             "filters": {"type": "object", "description": "Event attribute filters"},
         },
         "required": ["event_type"],
     }},
]

ACTION_NODES = [
    {"type": "http_request", "name": "HTTP Request", "category": "actions",
     "description": "Make HTTP request", "config_schema": {
         "properties": {
             "url": {"type": "string"}, "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
             "headers": {"type": "object"}, "body": {"type": "object"},
             "timeout": {"type": "integer", "default": 30},
         }, "required": ["url", "method"],
     }},
    {"type": "ssh_command", "name": "SSH Command", "category": "actions",
     "description": "Execute command via SSH", "config_schema": {
         "properties": {
             "host": {"type": "string"}, "command": {"type": "string"},
             "port": {"type": "integer", "default": 22},
             "timeout": {"type": "integer", "default": 60},
         }, "required": ["host", "command"],
     }},
    {"type": "docker_action", "name": "Docker Action", "category": "actions",
     "description": "Perform Docker container action", "config_schema": {
         "properties": {
             "action": {"type": "string", "enum": ["start", "stop", "restart", "recreate", "exec"]},
             "container": {"type": "string"}, "command": {"type": "string"},
         }, "required": ["action", "container"],
     }},
    {"type": "discord_notify", "name": "Discord Notification", "category": "actions",
     "description": "Send Discord message", "config_schema": {
         "properties": {
             "channel": {"type": "string"}, "message": {"type": "string"},
             "embed": {"type": "object"},
         }, "required": ["channel", "message"],
     }},
    {"type": "email_action", "name": "Send Email", "category": "actions",
     "description": "Send email notification", "config_schema": {
         "properties": {
             "to": {"type": "array", "items": {"type": "string"}},
             "subject": {"type": "string"}, "body": {"type": "string"},
         }, "required": ["to", "subject", "body"],
     }},
    {"type": "script_action", "name": "Run Script", "category": "actions",
     "description": "Execute custom script", "config_schema": {
         "properties": {
             "language": {"type": "string", "enum": ["python", "bash", "powershell"]},
             "script": {"type": "string"}, "env": {"type": "object"},
         }, "required": ["language", "script"],
     }},
]

LOGIC_NODES = [
    {"type": "condition", "name": "Condition", "category": "logic",
     "description": "Branch based on condition", "config_schema": {
         "properties": {
             "expression": {"type": "string", "description": "JSONPath or template expression"},
             "operator": {"type": "string", "enum": ["eq", "neq", "gt", "gte", "lt", "lte", "contains", "regex"]},
             "value": {"type": "string"},
         }, "required": ["expression", "operator", "value"],
     }},
    {"type": "switch", "name": "Switch", "category": "logic",
     "description": "Multi-branch switch", "config_schema": {
         "properties": {
             "expression": {"type": "string"},
             "cases": {"type": "array", "items": {"type": "object"}},
         }, "required": ["expression", "cases"],
     }},
    {"type": "delay", "name": "Delay", "category": "logic",
     "description": "Wait before proceeding", "config_schema": {
         "properties": {
             "duration_seconds": {"type": "integer", "minimum": 1, "maximum": 86400},
         }, "required": ["duration_seconds"],
     }},
    {"type": "loop", "name": "Loop", "category": "logic",
     "description": "Iterate over items", "config_schema": {
         "properties": {
             "iterable_expression": {"type": "string"},
             "max_iterations": {"type": "integer", "default": 100},
         }, "required": ["iterable_expression"],
     }},
]


class WorkflowNode:
    def __init__(self, node_id: str, node_type: str, config: Dict[str, Any], name: str = ""):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
        self.name = name or node_type

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.node_id, "type": self.node_type, "name": self.name, "config": self.config}


class WorkflowEdge:
    def __init__(self, edge_id: str, source: str, target: str, label: str = ""):
        self.edge_id = edge_id
        self.source = source
        self.target = target
        self.label = label

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.edge_id, "source": self.source, "target": self.target, "label": self.label}


class Workflow:
    def __init__(self, workflow_id: str, name: str, description: str,
                 nodes: List[WorkflowNode], edges: List[WorkflowEdge],
                 tags: Optional[List[str]] = None):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.nodes = {n.node_id: n for n in nodes}
        self.edges = edges
        self.tags = tags or []
        self.status = WorkflowStatus.DRAFT
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version = 1
        self.execution_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "tags": self.tags,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "execution_count": self.execution_count,
        }


class WorkflowExecution:
    def __init__(self, execution_id: str, workflow_id: str, trigger_data: Dict[str, Any]):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.trigger_data = trigger_data
        self.status = ExecutionStatus.PENDING
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.node_results: Dict[str, Dict[str, Any]] = {}
        self.error: Optional[str] = None
        self.context: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "node_results": {k: {"status": v.get("status"), "duration_ms": v.get("duration_ms")}
                             for k, v in self.node_results.items()},
            "error": self.error,
        }


class WorkflowManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._workflows: Dict[str, Workflow] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._node_registry: Dict[str, Dict] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._register_default_nodes()
        self._initialized = True
        logger.info("WorkflowManager initialized")

    async def close(self) -> None:
        self._workflows.clear()
        self._executions.clear()
        logger.info("WorkflowManager closed")

    def _register_default_nodes(self) -> None:
        for node_list in [TRIGGER_NODES, ACTION_NODES, LOGIC_NODES]:
            for node_def in node_list:
                self._node_registry[node_def["type"]] = node_def

    def get_node_types(self, category: Optional[str] = None) -> List[Dict]:
        if category:
            return [n for n in self._node_registry.values() if n.get("category") == category]
        return list(self._node_registry.values())

    def create_workflow(self, name: str, description: str,
                        nodes: Optional[List[Dict]] = None,
                        edges: Optional[List[Dict]] = None,
                        tags: Optional[List[str]] = None) -> Workflow:
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            nodes=[WorkflowNode(**n) for n in (nodes or [])],
            edges=[WorkflowEdge(**e) for e in (edges or [])],
            tags=tags,
        )
        self._workflows[workflow_id] = workflow
        logger.info(f"Workflow {workflow_id} created: {name}")
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Workflow]:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        if "name" in updates:
            workflow.name = updates["name"]
        if "description" in updates:
            workflow.description = updates["description"]
        if "tags" in updates:
            workflow.tags = updates["tags"]
        if "nodes" in updates:
            workflow.nodes = {n["id"]: WorkflowNode(**n) for n in updates["nodes"]}
        if "edges" in updates:
            workflow.edges = [WorkflowEdge(**e) for e in updates["edges"]]
        if "status" in updates:
            workflow.status = WorkflowStatus(updates["status"])
        workflow.version += 1
        workflow.updated_at = datetime.utcnow()
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id not in self._workflows:
            return False
        del self._workflows[workflow_id]
        return True

    def list_workflows(self, status: Optional[str] = None, tag: Optional[str] = None) -> List[Dict]:
        workflows = list(self._workflows.values())
        if status:
            workflows = [w for w in workflows if w.status.value == status]
        if tag:
            workflows = [w for w in workflows if tag in w.tags]
        return [w.to_dict() for w in sorted(workflows, key=lambda w: w.updated_at, reverse=True)]

    async def execute_workflow(self, workflow_id: str, trigger_data: Dict[str, Any]) -> WorkflowExecution:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow is {workflow.status.value}, must be active")

        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(execution_id, workflow_id, trigger_data)
        execution.status = ExecutionStatus.RUNNING
        self._executions[execution_id] = execution
        workflow.execution_count += 1

        logger.info(f"Executing workflow {workflow_id} (execution {execution_id})")

        try:
            start_nodes = self._find_start_nodes(workflow)
            await self._execute_nodes(workflow, execution, start_nodes, trigger_data)
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Workflow execution {execution_id} failed: {e}")

        return execution

    def _find_start_nodes(self, workflow: Workflow) -> List[WorkflowNode]:
        target_ids = {e.target for e in workflow.edges}
        return [n for n in workflow.nodes.values() if n.node_id not in target_ids]

    async def _execute_nodes(self, workflow: Workflow, execution: WorkflowExecution,
                              nodes: List[WorkflowNode], context: Dict[str, Any]) -> None:
        for node in nodes:
            start_time = datetime.utcnow()
            result = await self._execute_node(node, context)
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            execution.node_results[node.node_id] = {
                "status": "completed" if result.get("success") else "failed",
                "duration_ms": duration,
                "output": result.get("output"),
            }

            next_nodes = self._get_next_nodes(workflow, node.node_id)
            if next_nodes:
                await self._execute_nodes(workflow, execution, next_nodes, result.get("output", {}))

    def _get_next_nodes(self, workflow: Workflow, node_id: str) -> List[WorkflowNode]:
        next_ids = [e.target for e in workflow.edges if e.source == node_id]
        return [workflow.nodes[nid] for nid in next_ids if nid in workflow.nodes]

    async def _execute_node(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        if node.node_type == "delay":
            duration = node.config.get("duration_seconds", 1)
            await asyncio.sleep(duration)
            return {"success": True, "output": {"waited_seconds": duration}}
        if node.node_type == "condition":
            expr = node.config.get("expression", "")
            operator = node.config.get("operator", "eq")
            value = node.config.get("value", "")
            actual = self._resolve_expression(expr, context)
            passed = self._evaluate_condition(actual, operator, value)
            return {"success": True, "output": {"condition_met": passed, "actual_value": actual}}
        return {"success": True, "output": {"node_type": node.node_type, "config": node.config, "handled": False}}

    def _resolve_expression(self, expression: str, context: Dict[str, Any]) -> Any:
        if expression.startswith("{{") and expression.endswith("}}"):
            path = expression[2:-2].strip()
            parts = path.split(".")
            current = context
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part, None)
                elif isinstance(current, list) and part.isdigit():
                    try:
                        current = current[int(part)]
                    except (IndexError, ValueError):
                        return None
                else:
                    return None
            return current
        return expression

    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "neq":
                return actual != expected
            elif operator == "gt":
                return float(actual) > float(expected)
            elif operator == "gte":
                return float(actual) >= float(expected)
            elif operator == "lt":
                return float(actual) < float(expected)
            elif operator == "lte":
                return float(actual) <= float(expected)
            elif operator == "contains":
                return expected in actual if isinstance(actual, (str, list)) else False
            elif operator == "regex":
                import re
                return bool(re.match(str(expected), str(actual))) if actual else False
        except (ValueError, TypeError):
            return False
        return False

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        return self._executions.get(execution_id)

    def get_workflow_executions(self, workflow_id: str, limit: int = 50) -> List[Dict]:
        executions = [e for e in self._executions.values() if e.workflow_id == workflow_id]
        executions.sort(key=lambda e: e.started_at, reverse=True)
        return [e.to_dict() for e in executions[:limit]]

    def cancel_execution(self, execution_id: str) -> bool:
        execution = self._executions.get(execution_id)
        if not execution or execution.status not in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            return False
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        return True

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._workflows)
        active = sum(1 for w in self._workflows.values() if w.status == WorkflowStatus.ACTIVE)
        total_execs = len(self._executions)
        completed = sum(1 for e in self._executions.values() if e.status == ExecutionStatus.COMPLETED)
        failed = sum(1 for e in self._executions.values() if e.status == ExecutionStatus.FAILED)
        return {
            "total_workflows": total,
            "active_workflows": active,
            "total_executions": total_execs,
            "completed_executions": completed,
            "failed_executions": failed,
            "avg_nodes_per_workflow": round(
                sum(len(w.nodes) for w in self._workflows.values()) / total, 1
            ) if total > 0 else 0,
        }
