"""Documentation Generator — Auto-generate architecture docs from live infrastructure."""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DocFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    ADOC = "asciidoc"
    MINTLIFY = "mintlify"


class DocType(str, Enum):
    ARCHITECTURE = "architecture"
    ADR = "adr"
    SYSTEM_CONTEXT = "system_context"
    CONTAINER_DIAGRAM = "container_diagram"
    COMPONENT_DIAGRAM = "component_diagram"
    DEPLOYMENT_DIAGRAM = "deployment_diagram"
    API_REFERENCE = "api_reference"
    RUNBOOK = "runbook"
    SLIDE = "slide"


class ArchitectureDecisionRecord:
    def __init__(self, adr_id: str, title: str, context: str, decision: str, status: str = "proposed"):
        self.adr_id = adr_id
        self.title = title
        self.context = context
        self.decision = decision
        self.status = status
        self.consequences: str = ""
        self.alternatives: list[str] = []
        self.pros: list[str] = []
        self.cons: list[str] = []
        self.domain: str = ""
        self.authors: list[str] = []
        self.approvers: list[str] = []
        self.tags: list[str] = []
        self.supersedes: list[str] = []
        self.superseded_by: str = ""
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "adr_id": self.adr_id,
            "title": self.title,
            "context": self.context,
            "decision": self.decision,
            "status": self.status,
            "consequences": self.consequences,
            "alternatives": self.alternatives,
            "pros": self.pros,
            "cons": self.cons,
            "domain": self.domain,
            "authors": self.authors,
            "approvers": self.approvers,
            "tags": self.tags,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArchitectureDecisionRecord":
        adr = cls(data["adr_id"], data["title"], data["context"], data["decision"], data.get("status", "proposed"))
        adr.consequences = data.get("consequences", "")
        adr.alternatives = data.get("alternatives", [])
        adr.pros = data.get("pros", [])
        adr.cons = data.get("cons", [])
        adr.domain = data.get("domain", "")
        adr.authors = data.get("authors", [])
        adr.approvers = data.get("approvers", [])
        adr.tags = data.get("tags", [])
        adr.supersedes = data.get("supersedes", [])
        adr.superseded_by = data.get("superseded_by", "")
        if data.get("created_at"):
            adr.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            adr.updated_at = datetime.fromisoformat(data["updated_at"])
        return adr


class GeneratedDocument:
    def __init__(self, doc_id: str, title: str, doc_type: DocType, format: DocFormat, service_id: str):
        self.doc_id = doc_id
        self.title = title
        self.doc_type = doc_type
        self.format = format
        self.service_id = service_id
        self.content: str = ""
        self.template_used: str = ""
        self.author: str = "auto-generator"
        self.tags: list[str] = []
        self.source_infrastructure: dict[str, Any] = {}
        self.diagram_svg: str = ""
        self.word_count: int = 0
        self.version: int = 1
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "doc_type": self.doc_type.value,
            "format": self.format.value,
            "service_id": self.service_id,
            "content_length": len(self.content),
            "template_used": self.template_used,
            "author": self.author,
            "tags": self.tags,
            "source_infrastructure": self.source_infrastructure,
            "has_diagram": bool(self.diagram_svg),
            "word_count": self.word_count,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedDocument":
        doc = cls(
            data["doc_id"], data["title"],
            DocType(data["doc_type"]),
            DocFormat(data["format"]),
            data["service_id"],
        )
        doc.content = data.get("content", "")
        doc.template_used = data.get("template_used", "")
        doc.author = data.get("author", "auto-generator")
        doc.tags = data.get("tags", [])
        doc.source_infrastructure = data.get("source_infrastructure", {})
        doc.diagram_svg = data.get("diagram_svg", "")
        doc.word_count = data.get("word_count", 0)
        doc.version = data.get("version", 1)
        if data.get("created_at"):
            doc.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            doc.updated_at = datetime.fromisoformat(data["updated_at"])
        return doc


ARCHITECTURE_TEMPLATES = {
    "microservice": {
        "name": "Microservice Architecture",
        "sections": ["Overview", "System Context", "Service Boundaries", "API Design", "Data Flow", "Deployment", "Monitoring", "ADR References"],
    },
    "event_driven": {
        "name": "Event-Driven Architecture",
        "sections": ["Overview", "Event Taxonomy", "Producers", "Consumers", "Event Schemas", "Stream Topology", "Error Handling", "Observability"],
    },
    "layered": {
        "name": "Layered Architecture",
        "sections": ["Overview", "Presentation Layer", "Business Logic Layer", "Data Access Layer", "Integration Layer", "Cross-Cutting Concerns"],
    },
}


class DocGenerator:
    def __init__(self):
        self.documents: dict[str, GeneratedDocument] = {}
        self.adrs: dict[str, ArchitectureDecisionRecord] = {}
        self.templates: dict[str, Any] = dict(ARCHITECTURE_TEMPLATES)

    def generate_architecture_doc(self, title: str, service_id: str, template_name: str = "microservice",
                                   format: DocFormat = DocFormat.MARKDOWN,
                                   source_infra: dict[str, Any] = None) -> GeneratedDocument:
        doc_id = str(uuid.uuid4())
        doc = GeneratedDocument(doc_id, title, DocType.ARCHITECTURE, format, service_id)
        doc.template_used = template_name
        doc.source_infrastructure = source_infra or {}
        tmpl = self.templates.get(template_name, self.templates.get("microservice"))
        content_parts = [f"# {title}\n", f"_Auto-generated: {datetime.utcnow().isoformat()}_\n", ""]
        if source_infra:
            content_parts.append("## Source Infrastructure\n")
            content_parts.append("```json\n")
            content_parts.append(json.dumps(source_infra, indent=2))
            content_parts.append("\n```\n")
        if tmpl:
            content_parts.append(f"\n## Architecture Template: {tmpl['name']}\n")
            for section in tmpl["sections"]:
                content_parts.append(f"\n### {section}\n")
                content_parts.append(f"_This section auto-generated from {service_id}_\n")
        content_parts.append(f"\n## System Context\n")
        content_parts.append(f"Service `{service_id}` deployed in the infrastructure.\n")
        content_parts.append(f"\n## Dependencies\n")
        content_parts.append("- Infrastructure components scanned at generation time\n")
        content_parts.append("\n## Deployment\n")
        content_parts.append("- Generated from live infrastructure state\n")
        doc.content = "\n".join(content_parts)
        doc.word_count = len(doc.content.split())
        self.documents[doc_id] = doc
        logger.info("Generated architecture document %s for service %s", doc_id, service_id)
        return doc

    def generate_system_context_diagram(self, service_id: str, dependencies: list[dict[str, Any]]) -> GeneratedDocument:
        doc_id = str(uuid.uuid4())
        doc = GeneratedDocument(doc_id, f"System Context - {service_id}", DocType.SYSTEM_CONTEXT, DocFormat.MARKDOWN, service_id)
        lines = [f"# System Context Diagram: {service_id}\n", ""]
        lines.append("```mermaid")
        lines.append("graph TD")
        lines.append(f"    {service_id.replace('-', '_')}[{service_id}]")
        for dep in dependencies:
            dep_id = dep.get("id", dep.get("name", "unknown")).replace("-", "_")
            dep_rel = dep.get("relationship", "-->")
            lines.append(f"    {service_id.replace('-', '_')} {dep_rel} {dep_id}[{dep.get('name', dep.get('id', 'unknown'))}]")
        lines.append("```")
        doc.content = "\n".join(lines)
        doc.source_infrastructure = {"dependencies": dependencies}
        doc.word_count = len(doc.content.split())
        self.documents[doc_id] = doc
        return doc

    def create_adr(self, title: str, context: str, decision: str, status: str = "proposed",
                    domain: str = "", authors: list[str] = None) -> ArchitectureDecisionRecord:
        adr_id = str(uuid.uuid4())
        adr = ArchitectureDecisionRecord(adr_id, title, context, decision, status)
        adr.domain = domain
        adr.authors = authors or []
        self.adrs[adr_id] = adr
        logger.info("Created ADR: %s [%s]", title, status)
        return adr

    def update_adr_status(self, adr_id: str, status: str) -> Optional[ArchitectureDecisionRecord]:
        adr = self.adrs.get(adr_id)
        if not adr:
            return None
        adr.status = status
        adr.updated_at = datetime.utcnow()
        return adr

    def list_adrs(self, domain: str = "", status: str = "") -> list[ArchitectureDecisionRecord]:
        results = list(self.adrs.values())
        if domain:
            results = [a for a in results if a.domain == domain]
        if status:
            results = [a for a in results if a.status == status]
        return sorted(results, key=lambda a: a.created_at, reverse=True)

    def get_document(self, doc_id: str) -> Optional[GeneratedDocument]:
        return self.documents.get(doc_id)

    def list_documents(self, service_id: str = "", doc_type: str = "") -> list[GeneratedDocument]:
        results = list(self.documents.values())
        if service_id:
            results = [d for d in results if d.service_id == service_id]
        if doc_type:
            results = [d for d in results if d.doc_type.value == doc_type]
        return sorted(results, key=lambda d: d.created_at, reverse=True)

    def render_adr_to_markdown(self, adr_id: str) -> Optional[str]:
        adr = self.adrs.get(adr_id)
        if not adr:
            return None
        lines = [
            f"# ADR-{adr.adr_id[:8]}: {adr.title}",
            "",
            f"**Status:** {adr.status}",
            f"**Domain:** {adr.domain}" if adr.domain else "",
            f"**Authors:** {', '.join(adr.authors)}" if adr.authors else "",
            f"**Created:** {adr.created_at.isoformat()}",
            "",
            "## Context",
            "",
            adr.context,
            "",
            "## Decision",
            "",
            adr.decision,
            "",
            "## Consequences",
            "",
            adr.consequences or "_None documented_",
            "",
        ]
        if adr.alternatives:
            lines.extend(["## Alternatives Considered", ""])
            for alt in adr.alternatives:
                lines.append(f"- {alt}")
            lines.append("")
        if adr.pros:
            lines.extend(["## Pros", ""])
            for p in adr.pros:
                lines.append(f"- {p}")
            lines.append("")
        if adr.cons:
            lines.extend(["## Cons", ""])
            for c in adr.cons:
                lines.append(f"- {c}")
            lines.append("")
        return "\n".join(lines)

    def get_docs_summary(self) -> dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "total_adrs": len(self.adrs),
            "by_type": {
                dt.value: len([d for d in self.documents.values() if d.doc_type.value == dt.value])
                for dt in DocType
            },
            "by_format": {
                df.value: len([d for d in self.documents.values() if d.format.value == df.value])
                for df in DocFormat
            },
            "adr_statuses": {
                s: len([a for a in self.adrs.values() if a.status == s])
                for s in set(a.status for a in self.adrs.values())
            } if self.adrs else {},
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": {did: d.to_dict() for did, d in self.documents.items()},
            "adrs": {aid: a.to_dict() for aid, a in self.adrs.items()},
            "templates": self.templates,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocGenerator":
        gen = cls()
        for did, ddata in data.get("documents", {}).items():
            gen.documents[did] = GeneratedDocument.from_dict(ddata)
        for aid, adata in data.get("adrs", {}).items():
            gen.adrs[aid] = ArchitectureDecisionRecord.from_dict(adata)
        gen.templates = data.get("templates", dict(ARCHITECTURE_TEMPLATES))
        return gen

    def register_template(self, name: str, sections: list[str], description: str = "") -> bool:
        if name in self.templates:
            return False
        self.templates[name] = {"name": description or name, "sections": sections}
        return True

    def batch_generate_docs(self, requests: list[dict[str, Any]]) -> list[GeneratedDocument]:
        docs = []
        for req in requests:
            doc = self.generate_architecture_doc(
                req["title"], req["service_id"],
                template_name=req.get("template", "microservice"),
                format=DocFormat(req.get("format", "markdown")),
                source_infra=req.get("source_infra"),
            )
            doc.author = req.get("author", "auto-generator")
            doc.tags = req.get("tags", [])
            docs.append(doc)
        return docs

    def get_document_version(self, doc_id: str) -> Optional[GeneratedDocument]:
        return self.documents.get(doc_id)

    def increment_version(self, doc_id: str, new_content: str) -> Optional[GeneratedDocument]:
        doc = self.documents.get(doc_id)
        if not doc:
            return None
        doc.version += 1
        doc.content = new_content
        doc.word_count = len(new_content.split())
        doc.updated_at = datetime.utcnow()
        return doc

    def search_documents(self, query: str) -> list[GeneratedDocument]:
        q = query.lower()
        return [d for d in self.documents.values()
                if q in d.title.lower() or q in d.service_id.lower() or q in d.content.lower()[:500]]

    def get_adr_by_domain(self, domain: str) -> list[ArchitectureDecisionRecord]:
        return [a for a in self.adrs.values() if a.domain == domain]

    def generate_runbook(self, service_id: str, steps: list[dict[str, Any]], format: DocFormat = DocFormat.MARKDOWN) -> GeneratedDocument:
        doc_id = str(uuid.uuid4())
        doc = GeneratedDocument(doc_id, f"Runbook - {service_id}", DocType.RUNBOOK, format, service_id)
        lines = [f"# Runbook: {service_id}", "", "## Incident Response Steps", ""]
        for i, step in enumerate(steps, 1):
            lines.append(f"### Step {i}: {step.get('title', f'Step {i}')}")
            lines.append("")
            lines.append(step.get("description", ""))
            if step.get("command"):
                lines.append("")
                lines.append(f"```bash\n{step['command']}\n```")
            lines.append("")
        doc.content = "\n".join(lines)
        doc.word_count = len(doc.content.split())
        self.documents[doc_id] = doc
        return doc

    def export_adrs(self, domain: str = "") -> list[dict[str, Any]]:
        adrs = self.list_adrs(domain=domain) if domain else list(self.adrs.values())
        return [a.to_dict() for a in adrs]

    def export_docs(self, service_id: str = "") -> list[dict[str, Any]]:
        docs = self.list_documents(service_id=service_id) if service_id else list(self.documents.values())
        return [d.to_dict() for d in docs]

    def get_adr_statistics(self) -> dict[str, Any]:
        total = len(self.adrs)
        by_status: dict[str, int] = {}
        for a in self.adrs.values():
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {"total_adrs": total, "by_status": by_status,
                "approved": by_status.get("approved", 0),
                "proposed": by_status.get("proposed", 0),
                "superseded": by_status.get("superseded", 0)}

    def bulk_create_adrs(self, adr_defs: list[dict[str, Any]]) -> list[str]:
        ids = []
        for ad in adr_defs:
            adr = self.create_adr(ad["title"], ad["context"], ad["decision"],
                                   ad.get("status", "proposed"), ad.get("domain", ""), ad.get("authors"))
            ids.append(adr.adr_id)
        return ids

    def start_review(self, adr_id: str, reviewers: list[str]) -> dict[str, Any] | None:
        adr = self.adrs.get(adr_id)
        if not adr:
            return None
        review_id = str(uuid.uuid4())
        review = {
            "review_id": review_id, "adr_id": adr_id, "reviewers": reviewers,
            "status": "pending", "comments": [], "created_at": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "_reviews"):
            self._reviews: dict[str, list[dict[str, Any]]] = {}
        if adr_id not in self._reviews:
            self._reviews[adr_id] = []
        self._reviews[adr_id].append(review)
        adr.status = "in_review"
        return review

    def submit_review_comment(self, review_id: str, reviewer: str, comment: str, decision: str = "comment") -> bool:
        for reviews in getattr(self, "_reviews", {}).values():
            for r in reviews:
                if r["review_id"] == review_id:
                    r["comments"].append({
                        "reviewer": reviewer, "comment": comment,
                        "decision": decision, "timestamp": datetime.utcnow().isoformat(),
                    })
                    return True
        return False

    def approve_review(self, review_id: str, reviewer: str) -> bool:
        return self.submit_review_comment(review_id, reviewer, "Approved", "approved")

    def reject_review(self, review_id: str, reviewer: str, reason: str) -> bool:
        return self.submit_review_comment(review_id, reviewer, f"Rejected: {reason}", "rejected")

    def get_adr_reviews(self, adr_id: str) -> list[dict[str, Any]]:
        return list(getattr(self, "_reviews", {}).get(adr_id, []))

    def cross_reference_docs(self, source_id: str, target_id: str, ref_type: str = "related") -> bool:
        if source_id not in self.documents and source_id not in self.adrs:
            return False
        if target_id not in self.documents and target_id not in self.adrs:
            return False
        if not hasattr(self, "_cross_refs"):
            self._cross_refs: list[dict[str, Any]] = []
        self._cross_refs.append({
            "source_id": source_id, "target_id": target_id,
            "ref_type": ref_type, "created_at": datetime.utcnow().isoformat(),
        })
        return True

    def get_document_links(self, doc_id: str) -> list[dict[str, Any]]:
        return [r for r in getattr(self, "_cross_refs", [])
                if r["source_id"] == doc_id or r["target_id"] == doc_id]

    def set_doc_template(self, template_name: str, template_content: str) -> dict[str, Any]:
        tmpl_id = str(uuid.uuid4())
        tmpl = {
            "template_id": tmpl_id, "name": template_name,
            "content": template_content, "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
        }
        if not hasattr(self, "_doc_templates"):
            self._doc_templates: dict[str, dict[str, Any]] = {}
        self._doc_templates[tmpl_id] = tmpl
        return tmpl

    def get_doc_templates(self) -> list[dict[str, Any]]:
        return list(getattr(self, "_doc_templates", {}).values())

    def generate_from_template(self, template_id: str, service_id: str, params: dict[str, Any]) -> str | None:
        tmpl = getattr(self, "_doc_templates", {}).get(template_id)
        if not tmpl:
            return None
        content = tmpl["content"]
        for key, value in params.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        doc = self.create_document(service_id, tmpl["name"], content, "system")
        return doc.document_id

    def search_docs(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        results = []
        for d in self.documents.values():
            if q in d.title.lower() or q in d.content.lower():
                results.append(d.to_dict())
        for a in self.adrs.values():
            if q in a.title.lower() or q in a.decision.lower() or q in a.context.lower():
                results.append(a.to_dict())
        return results

    def get_content_statistics(self) -> dict[str, Any]:
        total_docs = len(self.documents)
        total_adrs = len(self.adrs)
        total_words = sum(d.word_count or 0 for d in self.documents.values())
        total_words += sum(a.word_count or 0 for a in self.adrs.values())
        return {
            "total_documents": total_docs, "total_adrs": total_adrs,
            "total_words": total_words, "avg_words_per_doc": round(total_words / max(total_docs + total_adrs, 1), 0),
        }

    def version_doc_template(self, template_id: str, new_content: str) -> dict[str, Any] | None:
        tmpl = getattr(self, "_doc_templates", {}).get(template_id)
        if not tmpl:
            return None
        ver = float(tmpl["version"]) + 1.0
        tmpl["previous_versions"] = tmpl.get("previous_versions", []) + [{"version": tmpl["version"], "content": tmpl["content"]}]
        tmpl["content"] = new_content
        tmpl["version"] = f"{ver:.1f}"
        tmpl["updated_at"] = datetime.utcnow().isoformat()
        return tmpl

    def bulk_generate_docs(self, service_id: str, template_ids: list[str], params: dict[str, Any]) -> list[str]:
        ids = []
        for tid in template_ids:
            doc_id = self.generate_from_template(tid, service_id, params)
            if doc_id:
                ids.append(doc_id)
        return ids

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
