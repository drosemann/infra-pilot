"""Internal Developer Portal — Backstage-inspired software catalog."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SoftwareComponent:
    def __init__(self, component_id: str, name: str, component_type: str, owner: str):
        self.component_id = component_id
        self.name = name
        self.component_type = component_type
        self.owner = owner
        self.description: str = ""
        self.lifecycle: str = "production"
        self.system: str = ""
        self.subsystem: str = ""
        self.tags: list[str] = []
        self.dependencies: list[str] = []
        self.depended_by: list[str] = []
        self.api_spec_url: str = ""
        self.docs_url: str = ""
        self.source_url: str = ""
        self.sla_tier: str = "t3"
        self.health_score: float = 100.0
        self.maturity_level: str = "level_1"
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "component_type": self.component_type,
            "owner": self.owner,
            "description": self.description,
            "lifecycle": self.lifecycle,
            "system": self.system,
            "subsystem": self.subsystem,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "depended_by": self.depended_by,
            "api_spec_url": self.api_spec_url,
            "docs_url": self.docs_url,
            "source_url": self.source_url,
            "sla_tier": self.sla_tier,
            "health_score": self.health_score,
            "maturity_level": self.maturity_level,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SoftwareComponent":
        c = cls(data["component_id"], data["name"], data["component_type"], data["owner"])
        c.description = data.get("description", "")
        c.lifecycle = data.get("lifecycle", "production")
        c.system = data.get("system", "")
        c.subsystem = data.get("subsystem", "")
        c.tags = data.get("tags", [])
        c.dependencies = data.get("dependencies", [])
        c.depended_by = data.get("depended_by", [])
        c.api_spec_url = data.get("api_spec_url", "")
        c.docs_url = data.get("docs_url", "")
        c.source_url = data.get("source_url", "")
        c.sla_tier = data.get("sla_tier", "t3")
        c.health_score = data.get("health_score", 100.0)
        c.maturity_level = data.get("maturity_level", "level_1")
        if data.get("created_at"):
            c.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            c.updated_at = datetime.fromisoformat(data["updated_at"])
        c.metadata = data.get("metadata", {})
        return c


class DependencyGraph:
    def __init__(self):
        self.nodes: dict[str, SoftwareComponent] = {}
        self.edges: list[dict[str, str]] = []

    def add_component(self, component: SoftwareComponent):
        self.nodes[component.component_id] = component

    def add_dependency(self, source_id: str, target_id: str):
        self.edges.append({"source": source_id, "target": target_id})
        if source_id in self.nodes and target_id in self.nodes:
            if target_id not in self.nodes[source_id].dependencies:
                self.nodes[source_id].dependencies.append(target_id)
            if source_id not in self.nodes[target_id].depended_by:
                self.nodes[target_id].depended_by.append(source_id)

    def get_impact_analysis(self, component_id: str) -> list[str]:
        affected = []
        queue = [component_id]
        visited = set()
        while queue:
            cid = queue.pop(0)
            if cid in visited:
                continue
            visited.add(cid)
            if cid in self.nodes:
                for dep_id in self.nodes[cid].depended_by:
                    if dep_id not in visited:
                        affected.append(dep_id)
                        queue.append(dep_id)
        return affected

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {cid: comp.to_dict() for cid, comp in self.nodes.items()},
            "edges": self.edges,
        }


MATURITY_MODEL = {
    "level_0": {"name": "Discovery", "score": 0, "requirements": []},
    "level_1": {"name": "Defined", "score": 20, "requirements": ["source_url", "owner"]},
    "level_2": {"name": "Managed", "score": 40, "requirements": ["source_url", "owner", "docs_url", "api_spec_url"]},
    "level_3": {"name": "Measured", "score": 60, "requirements": ["source_url", "owner", "docs_url", "api_spec_url", "tests_passing"]},
    "level_4": {"name": "Optimized", "score": 80, "requirements": ["source_url", "owner", "docs_url", "api_spec_url", "tests_passing", "monitoring", "on_call"]},
    "level_5": {"name": "Innovating", "score": 100, "requirements": ["source_url", "owner", "docs_url", "api_spec_url", "tests_passing", "monitoring", "on_call", "sla_defined", "dr_tested"]},
}


class DeveloperPortalManager:
    def __init__(self):
        self.components: dict[str, SoftwareComponent] = {}
        self.systems: dict[str, dict[str, Any]] = {}
        self.dependency_graph = DependencyGraph()

    def register_component(self, name: str, component_type: str, owner: str, description: str = "") -> SoftwareComponent:
        cid = str(uuid.uuid4())
        component = SoftwareComponent(cid, name, component_type, owner)
        component.description = description
        self.components[cid] = component
        self.dependency_graph.add_component(component)
        logger.info("Registered component %s (%s) owned by %s", name, component_type, owner)
        return component

    def get_component(self, component_id: str) -> Optional[SoftwareComponent]:
        return self.components.get(component_id)

    def update_component(self, component_id: str, updates: dict[str, Any]) -> Optional[SoftwareComponent]:
        comp = self.components.get(component_id)
        if not comp:
            return None
        for key, value in updates.items():
            if hasattr(comp, key):
                setattr(comp, key, value)
        comp.updated_at = datetime.utcnow()
        return comp

    def delete_component(self, component_id: str) -> bool:
        if component_id in self.components:
            del self.components[component_id]
            return True
        return False

    def list_components(self, owner: str = "", component_type: str = "", system: str = "") -> list[SoftwareComponent]:
        results = list(self.components.values())
        if owner:
            results = [c for c in results if c.owner == owner]
        if component_type:
            results = [c for c in results if c.component_type == component_type]
        if system:
            results = [c for c in results if c.system == system]
        return results

    def calculate_maturity(self, component_id: str) -> dict[str, Any]:
        comp = self.components.get(component_id)
        if not comp:
            return {"error": "Component not found"}
        current_level = "level_0"
        current_score = 0
        for lid, ldef in sorted(MATURITY_MODEL.items()):
            if all(comp.source_url if r == "source_url" else
                   comp.docs_url if r == "docs_url" else
                   comp.api_spec_url if r == "api_spec_url" else
                   comp.owner if r == "owner" else
                   comp.sla_tier if r == "sla_defined" else
                   comp.health_score > 50 if r == "tests_passing" else
                   comp.metadata.get("monitoring", False) if r == "monitoring" else
                   comp.metadata.get("on_call", False) if r == "on_call" else
                   comp.metadata.get("dr_tested", False) if r == "dr_tested" else False
                   for r in ldef["requirements"]):
                current_level = lid
                current_score = ldef["score"]
        return {
            "component_id": component_id,
            "level": current_level,
            "level_name": MATURITY_MODEL[current_level]["name"],
            "score": current_score,
            "next_level": self._next_level(current_level),
        }

    def _next_level(self, current: str) -> Optional[str]:
        levels = sorted(MATURITY_MODEL.keys())
        idx = levels.index(current)
        if idx + 1 < len(levels):
            lid = levels[idx + 1]
            return {"level": lid, "name": MATURITY_MODEL[lid]["name"], "score": MATURITY_MODEL[lid]["score"]}
        return None

    def get_dependency_graph(self) -> dict[str, Any]:
        return self.dependency_graph.to_dict()

    def get_impact_analysis(self, component_id: str) -> list[str]:
        return self.dependency_graph.get_impact_analysis(component_id)

    def create_system(self, name: str, description: str, domain: str) -> dict[str, Any]:
        sid = str(uuid.uuid4())
        system = {
            "system_id": sid,
            "name": name,
            "description": description,
            "domain": domain,
            "components": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        self.systems[sid] = system
        return system

    def add_component_to_system(self, system_id: str, component_id: str) -> bool:
        if system_id in self.systems and component_id in self.components:
            if component_id not in self.systems[system_id]["components"]:
                self.systems[system_id]["components"].append(component_id)
                self.components[component_id].system = self.systems[system_id]["name"]
            return True
        return False

    def get_catalog_summary(self) -> dict[str, Any]:
        total = len(self.components)
        by_type: dict[str, int] = {}
        by_owner: dict[str, int] = {}
        by_maturity: dict[str, int] = {}
        for comp in self.components.values():
            by_type[comp.component_type] = by_type.get(comp.component_type, 0) + 1
            by_owner[comp.owner] = by_owner.get(comp.owner, 0) + 1
            mat = self.calculate_maturity(comp.component_id)
            by_maturity[mat["level"]] = by_maturity.get(mat["level"], 0) + 1
        return {
            "total_components": total,
            "total_systems": len(self.systems),
            "by_type": by_type,
            "by_owner": by_owner,
            "by_maturity": by_maturity,
            "average_health": round(
                sum(c.health_score for c in self.components.values()) / total, 1
            ) if total > 0 else 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": {cid: c.to_dict() for cid, c in self.components.items()},
            "systems": self.systems,
            "dependency_graph": self.dependency_graph.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeveloperPortalManager":
        mgr = cls()
        for cid, cdata in data.get("components", {}).items():
            comp = SoftwareComponent.from_dict(cdata)
            mgr.components[cid] = comp
            mgr.dependency_graph.add_component(comp)
        for sid, sdata in data.get("systems", {}).items():
            mgr.systems[sid] = sdata
        for edge in data.get("dependency_graph", {}).get("edges", []):
            mgr.dependency_graph.add_dependency(edge["source"], edge["target"])
        return mgr

    def bulk_register_components(self, components_data: list[dict[str, Any]]) -> list[str]:
        ids = []
        for cd in components_data:
            comp = self.register_component(
                cd["name"], cd.get("component_type", "service"),
                cd["owner"], cd.get("description", ""),
            )
            if cd.get("tags"):
                comp.tags = cd["tags"]
            if cd.get("lifecycle"):
                comp.lifecycle = cd["lifecycle"]
            if cd.get("source_url"):
                comp.source_url = cd["source_url"]
            if cd.get("docs_url"):
                comp.docs_url = cd["docs_url"]
            if cd.get("dependencies"):
                for dep_id in cd["dependencies"]:
                    self.dependency_graph.add_dependency(comp.component_id, dep_id)
            ids.append(comp.component_id)
        return ids

    def search_components(self, query: str) -> list[SoftwareComponent]:
        q = query.lower()
        return [c for c in self.components.values()
                if q in c.name.lower() or q in c.description.lower() or q in c.owner.lower()
                or any(q in tag.lower() for tag in c.tags)]

    def health_check_all(self) -> list[dict[str, Any]]:
        results = []
        for cid, comp in self.components.items():
            checks = {
                "has_owner": bool(comp.owner),
                "has_source": bool(comp.source_url),
                "has_docs": bool(comp.docs_url),
                "has_api_spec": bool(comp.api_spec_url),
                "has_sla": bool(comp.sla_tier),
            }
            passed = sum(1 for v in checks.values() if v)
            results.append({
                "component_id": cid,
                "name": comp.name,
                "health_score": round(passed / len(checks) * 100, 1),
                "checks": checks,
            })
        return results

    def update_maturity_all(self) -> dict[str, Any]:
        results = {}
        for cid in self.components:
            results[cid] = self.calculate_maturity(cid)
        return results

    def get_system_components(self, system_id: str) -> list[SoftwareComponent]:
        system = self.systems.get(system_id)
        if not system:
            return []
        return [self.components[cid] for cid in system.get("components", []) if cid in self.components]

    def export_catalog(self) -> dict[str, Any]:
        return self.to_dict()

    def get_dependency_report(self) -> dict[str, Any]:
        all_deps = set()
        for comp in self.components.values():
            for dep in comp.dependencies:
                all_deps.add(dep)
        circular = []
        for comp_id in self.components:
            impacted = self.dependency_graph.get_impact_analysis(comp_id)
            if comp_id in impacted:
                circular.append(comp_id)
        return {
            "total_dependencies": len(all_deps),
            "total_components": len(self.components),
            "circular_dependencies": circular,
            "most_depended_on": sorted(
                [(cid, len(c.depended_by)) for cid, c in self.components.items()],
                key=lambda x: x[1], reverse=True,
            )[:10],
            "orphaned_components": [cid for cid, c in self.components.items() if not c.dependencies and not c.depended_by],
        }

    def get_components_by_maturity(self, level: str) -> list[SoftwareComponent]:
        return [c for cid, c in self.components.items() if self.calculate_maturity(cid).get("level") == level]

    def add_component_dependency(self, source_id: str, target_id: str) -> bool:
        if source_id in self.components and target_id in self.components:
            self.dependency_graph.add_dependency(source_id, target_id)
            return True
        return False

    def component_health_check(self, component_id: str) -> dict[str, Any]:
        comp = self.components.get(component_id)
        if not comp:
            return {"error": "Component not found"}
        checks = {"has_source": bool(comp.source_url), "has_docs": bool(comp.docs_url),
                  "has_api_spec": bool(comp.api_spec_url), "has_owner": bool(comp.owner),
                  "has_sla": bool(comp.sla_tier)}
        passed = sum(1 for v in checks.values() if v)
        return {"component_id": component_id, "name": comp.name,
                "health_score": round(passed / len(checks) * 100, 1), "checks": checks}

    def get_system_summary(self) -> dict[str, Any]:
        return {"total_systems": len(self.systems),
                "systems": [{"id": sid, "name": s["name"], "components": len(s["components"])}
                            for sid, s in self.systems.items()]}

    def export_components_by_owner(self, owner: str) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.components.values() if c.owner == owner]

    def get_dependency_chain_visualization(self, component_id: str) -> dict[str, Any]:
        comp = self.components.get(component_id)
        if not comp:
            return {"error": "Component not found"}
        nodes: list[dict[str, Any]] = [{"id": component_id, "name": comp.name, "type": "component"}]
        edges: list[dict[str, str]] = []
        visited = set()

        def traverse(cid: str, direction: str) -> None:
            if cid in visited:
                return
            visited.add(cid)
            comp_node = self.components.get(cid)
            if not comp_node:
                return
            if direction == "upstream":
                for dep_id in comp_node.dependencies:
                    dep = self.components.get(dep_id)
                    if dep:
                        nodes.append({"id": dep_id, "name": dep.name, "type": "component"})
                        edges.append({"from": cid, "to": dep_id})
                        traverse(dep_id, "upstream")
            elif direction == "downstream":
                for dep_id in comp_node.depended_by:
                    dep = self.components.get(dep_id)
                    if dep:
                        nodes.append({"id": dep_id, "name": dep.name, "type": "component"})
                        edges.append({"from": dep_id, "to": cid})
                        traverse(dep_id, "downstream")

        traverse(component_id, "upstream")
        visited.clear()
        traverse(component_id, "downstream")
        return {"root": component_id, "nodes": nodes, "edges": edges}

    def get_health_trend(self, component_id: str, days: int = 30) -> list[dict[str, Any]]:
        comp = self.components.get(component_id)
        if not comp:
            return []
        checks = self.component_health_check(component_id)
        return [{"date": datetime.utcnow().isoformat(), "health_score": checks.get("health_score", 0),
                 "checks_passed": sum(1 for v in checks.get("checks", {}).values() if v)}]

    def get_portal_scorecard(self, system_id: str = "") -> dict[str, Any]:
        comps = [c for c in self.components.values() if not system_id or c.system_id == system_id]
        if not comps:
            return {"error": "No components found"}
        scores = [self.calculate_maturity(cid) for cid, _ in [(c.component_id, c) for c in comps]]
        avg_maturity = round(sum(s.get("score", 0) for s in scores) / len(scores), 1) if scores else 0
        return {
            "system_id": system_id or "all", "component_count": len(comps),
            "avg_maturity_score": avg_maturity,
            "levels": {s.get("level", "unknown"): sum(1 for sc in scores if sc.get("level") == s.get("level"))
                       for s in scores},
            "health_summary": {
                "healthy": sum(1 for c in comps if self.component_health_check(c.component_id).get("health_score", 0) >= 80),
                "needs_attention": sum(1 for c in comps if 50 <= self.component_health_check(c.component_id).get("health_score", 0) < 80),
                "critical": sum(1 for c in comps if self.component_health_check(c.component_id).get("health_score", 0) < 50),
            }
        }

    def search_portal(self, query: str) -> dict[str, Any]:
        q = query.lower()
        comps = [c.to_dict() for c in self.components.values()
                 if q in c.name.lower() or q in (c.description or "").lower() or q in (c.owner or "").lower()]
        sys = [{"id": sid, "name": s["name"]} for sid, s in self.systems.items()
               if q in s["name"].lower()]
        return {"components": comps[:20], "systems": sys[:10], "total_matches": len(comps) + len(sys)}

    def add_system_tag(self, system_id: str, tag: str) -> bool:
        system = self.systems.get(system_id)
        if not system:
            return False
        if "tags" not in system:
            system["tags"] = []
        if tag not in system["tags"]:
            system["tags"].append(tag)
        return True

    def get_components_by_tag(self, tag: str) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.components.values() if tag in (c.metadata.get("tags", []))]

    def bulk_update_component_owner(self, component_ids: list[str], new_owner: str) -> int:
        count = 0
        for cid in component_ids:
            comp = self.components.get(cid)
            if comp:
                comp.owner = new_owner
                comp.updated_at = datetime.utcnow()
                count += 1
        return count

    def get_system_dependency_map(self, system_id: str) -> dict[str, Any]:
        system = self.systems.get(system_id)
        if not system:
            return {"error": "System not found"}
        comp_ids = system["components"]
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []
        for cid in comp_ids:
            comp = self.components.get(cid)
            if comp:
                nodes.append({"id": cid, "name": comp.name, "type": "component"})
                for dep_id in comp.dependencies:
                    if dep_id in comp_ids:
                        edges.append({"from": dep_id, "to": cid})
        return {"system_id": system_id, "system_name": system["name"], "nodes": nodes, "edges": edges}

    def calculate_system_maturity(self, system_id: str) -> dict[str, Any]:
        system = self.systems.get(system_id)
        if not system:
            return {"error": "System not found"}
        scores = [self.calculate_maturity(cid) for cid in system["components"] if cid in self.components]
        if not scores:
            return {"system_id": system_id, "score": 0, "level": "unknown"}
        avg = round(sum(s["score"] for s in scores) / len(scores), 1)
        level = "bronze" if avg < 40 else "silver" if avg < 70 else "gold" if avg < 90 else "platinum"
        return {"system_id": system_id, "system_name": system["name"], "score": avg,
                "level": level, "component_count": len(scores)}

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
        return {"total_items": 0, "avg_score": 0.0, "completion_rate": 0.0}

    def validate_operation(self) -> Dict[str, Any]:
        return {"valid": True, "checks_passed": 0, "checks_failed": 0}

class PlatformOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PlatformBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="parallel")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)

    def update_progress(self, pct: int) -> None:
        self.progress = min(pct, 100)
        if self.progress >= 100:
            self.status = "completed"

class PlatformMetrics(BaseModel):
    metric_name: str
    value: float
    unit: str = Field(default="count")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)

class MetricsCollector:
    def __init__(self) -> None:
        self._metrics: List[PlatformMetrics] = []

    def record(self, name: str, value: float, unit: str = "count", labels: Optional[Dict[str, str]] = None) -> None:
        self._metrics.append(PlatformMetrics(metric_name=name, value=value, unit=unit, labels=labels or {}))

    def query(self, name: str, since: Optional[datetime] = None) -> List[PlatformMetrics]:
        filtered = [m for m in self._metrics if m.metric_name == name]
        if since:
            filtered = [m for m in filtered if m.timestamp >= since]
        return filtered

    def aggregate(self, name: str, operation: str = "avg") -> float:
        values = [m.value for m in self._metrics if m.metric_name == name]
        if not values:
            return 0.0
        if operation == "avg":
            return round(sum(values) / len(values), 4)
        elif operation == "sum":
            return round(sum(values), 4)
        elif operation == "max":
            return round(max(values), 4)
        elif operation == "min":
            return round(min(values), 4)
        return 0.0

    def get_all_summary(self) -> Dict[str, Any]:
        names = set(m.metric_name for m in self._metrics)
        return {n: {"count": sum(1 for m in self._metrics if m.metric_name == n),
                     "avg": self.aggregate(n, "avg")} for n in names}

class ConfigManager:
    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        self._config: Dict[str, Any] = defaults or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def update(self, config: Dict[str, Any]) -> None:
        self._config.update(config)

    def export(self) -> Dict[str, Any]:
        return dict(self._config)

    def validate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        for key, rules in schema.items():
            value = self._config.get(key)
            if rules.get("required") and value is None:
                errors.append(f"Missing: {key}")
            if rules.get("type") and value is not None and not isinstance(value, rules["type"]):
                errors.append(f"Type mismatch: {key}")
        return {"valid": len(errors) == 0, "errors": errors}

class AuditTrail:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def log(self, user: str, action: str, resource: str, details: Optional[Dict[str, Any]] = None) -> None:
        self._entries.append({"user": user, "action": action, "resource": resource,
                               "details": details or {}, "timestamp": datetime.utcnow().isoformat()})

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    def search(self, user: Optional[str] = None, action: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._entries
        if user:
            results = [e for e in results if e["user"] == user]
        if action:
            results = [e for e in results if e["action"] == action]
        return results

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e["action"]] = counts.get(e["action"], 0) + 1
        return counts

class HealthChecker:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_fn) -> None:
        self._checks[name] = {"fn": check_fn, "last_result": None, "last_run": None}

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name, check in self._checks.items():
            try:
                result = await check["fn"]()
                check["last_result"] = result
                check["last_run"] = datetime.utcnow()
                results[name] = result
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results

    def get_status(self) -> Dict[str, Any]:
        return {name: {"last_result": c["last_result"], "last_run": c["last_run"].isoformat() if c["last_run"] else None}
                for name, c in self._checks.items()}
