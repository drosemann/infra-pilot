"""API route definitions for Platform Engineering (V4 Category 2, features 11-20)."""

from .developer_portal import DeveloperPortalManager
from .golden_path_scaffolder import GoldenPathScaffolder
from .service_catalog import ServiceCatalogManager
from .scorecards import ScorecardsManager
from .template_registry import TemplateRegistry
from .tech_debt_tracker import TechDebtTracker
from .environment_orchestrator import EnvironmentOrchestrator
from .api_catalog import ApiCatalog
from .doc_generator import DocGenerator
from .developer_pulse import DeveloperPulse


def register_routes(app):
    portal = DeveloperPortalManager()
    scaffold = GoldenPathScaffolder()
    catalog = ServiceCatalogManager()
    scorecards = ScorecardsManager()
    templates = TemplateRegistry()
    techdebt = TechDebtTracker()
    environments = EnvironmentOrchestrator()
    apis = ApiCatalog()
    docs = DocGenerator()
    pulse = DeveloperPulse()

    # Developer Portal
    @app.route('/api/v4/platform-engineering/portal/components', methods=['GET'])
    def list_components():
        from flask import request, jsonify
        domain = request.args.get('domain')
        components = portal.list_components(domain=domain)
        return jsonify([c.to_dict() for c in components])

    @app.route('/api/v4/platform-engineering/portal/components', methods=['POST'])
    def register_component():
        from flask import request, jsonify
        data = request.get_json()
        c = portal.register_component(data['name'], data['domain'], data.get('description', ''), data.get('owner', ''))
        return jsonify(c.to_dict()), 201

    @app.route('/api/v4/platform-engineering/portal/components/<component_id>', methods=['GET'])
    def get_component(component_id):
        from flask import jsonify
        c = portal.get_component(component_id)
        if c:
            return jsonify(c.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/portal/summary', methods=['GET'])
    def portal_summary():
        from flask import jsonify
        return jsonify(portal.get_summary())

    # Scaffolder
    @app.route('/api/v4/platform-engineering/scaffold/templates', methods=['GET'])
    def list_scaffold_templates():
        from flask import jsonify
        return jsonify([t.to_dict() for t in scaffold.list_templates()])

    @app.route('/api/v4/platform-engineering/scaffold/templates/<template_id>/generate', methods=['POST'])
    def scaffold_generate(template_id):
        from flask import request, jsonify
        data = request.get_json()
        gen = scaffold.generate_project(template_id, data.get('project_name'), data.get('params', {}))
        if gen:
            return jsonify(gen.to_dict()), 201
        return jsonify({'error': 'template not found'}), 404

    @app.route('/api/v4/platform-engineering/scaffold/generations/<generation_id>', methods=['GET'])
    def scaffold_status(generation_id):
        from flask import jsonify
        gen = scaffold.get_generation_status(generation_id)
        if gen:
            return jsonify(gen.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/scaffold/generations/<generation_id>/steps/<step_name>/complete', methods=['POST'])
    def scaffold_complete_step(generation_id, step_name):
        from flask import request, jsonify
        data = request.get_json() or {}
        result = scaffold.complete_step(generation_id, step_name, data.get('outputs', {}))
        if result:
            return jsonify({'status': 'completed', 'step': step_name})
        return jsonify({'error': 'generation or step not found'}), 404

    # Service Catalog
    @app.route('/api/v4/platform-engineering/catalog/services', methods=['GET'])
    def list_catalog_services():
        from flask import jsonify
        return jsonify([s.to_dict() for s in catalog.list_services()])

    @app.route('/api/v4/platform-engineering/catalog/services', methods=['POST'])
    def register_catalog_service():
        from flask import request, jsonify
        data = request.get_json()
        s = catalog.register_service(data['name'], data['domain'], data.get('description', ''), data.get('owner', ''))
        return jsonify(s.to_dict()), 201

    @app.route('/api/v4/platform-engineering/catalog/services/<service_id>', methods=['GET'])
    def get_catalog_service(service_id):
        from flask import jsonify
        s = catalog.get_service(service_id)
        if s:
            return jsonify(s.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/catalog/services/<service_id>/score', methods=['POST'])
    def score_catalog_service(service_id):
        from flask import jsonify
        score = catalog.score_service(service_id)
        return jsonify(score)

    @app.route('/api/v4/platform-engineering/catalog/summary', methods=['GET'])
    def catalog_summary():
        from flask import jsonify
        return jsonify(catalog.get_summary())

    # Scorecards
    @app.route('/api/v4/platform-engineering/scorecards', methods=['GET'])
    def list_scorecards():
        from flask import jsonify
        return jsonify([s.to_dict() for s in scorecards.list_scorecards()])

    @app.route('/api/v4/platform-engineering/scorecards', methods=['POST'])
    def create_scorecard():
        from flask import request, jsonify
        data = request.get_json()
        s = scorecards.create_scorecard(data['name'], data.get('team', ''))
        return jsonify(s.to_dict()), 201

    @app.route('/api/v4/platform-engineering/scorecards/<scorecard_id>', methods=['GET'])
    def get_scorecard(scorecard_id):
        from flask import jsonify
        s = scorecards.get_scorecard(scorecard_id)
        if s:
            return jsonify(s.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/scorecards/<scorecard_id>/metrics/<metric>', methods=['PATCH'])
    def update_scorecard_metric(scorecard_id, metric):
        from flask import request, jsonify
        data = request.get_json()
        scorecards.update_metric(scorecard_id, metric, data.get('value'))
        return jsonify({'status': 'updated'})

    @app.route('/api/v4/platform-engineering/scorecards/summary', methods=['GET'])
    def scorecards_summary():
        from flask import jsonify
        return jsonify(scorecards.get_summary())

    # Template Registry
    @app.route('/api/v4/platform-engineering/templates', methods=['GET'])
    def list_templates():
        from flask import jsonify
        return jsonify([t.to_dict() for t in templates.list_templates()])

    @app.route('/api/v4/platform-engineering/templates', methods=['POST'])
    def create_template():
        from flask import request, jsonify
        data = request.get_json()
        t = templates.create_template(data['name'], data.get('category', 'general'), data.get('params_schema', {}))
        return jsonify(t.to_dict()), 201

    @app.route('/api/v4/platform-engineering/templates/<template_id>', methods=['GET'])
    def get_template(template_id):
        from flask import jsonify
        t = templates.get_template(template_id)
        if t:
            return jsonify(t.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/templates/<template_id>/use', methods=['POST'])
    def use_template(template_id):
        from flask import jsonify
        t = templates.use_template(template_id)
        if t:
            return jsonify({'usage_count': t.usage_count})
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/templates/summary', methods=['GET'])
    def templates_summary():
        from flask import jsonify
        return jsonify(templates.get_summary())

    # Tech Debt
    @app.route('/api/v4/platform-engineering/tech-debt', methods=['GET'])
    def list_techdebt():
        from flask import request, jsonify
        severity = request.args.get('severity')
        return jsonify([d.to_dict() for d in techdebt.list_items(severity=severity)])

    @app.route('/api/v4/platform-engineering/tech-debt', methods=['POST'])
    def report_techdebt():
        from flask import request, jsonify
        data = request.get_json()
        d = techdebt.report_item(data['title'], data['severity'], data.get('effort_hours', 1), data.get('area', 'code'))
        return jsonify(d.to_dict()), 201

    @app.route('/api/v4/platform-engineering/tech-debt/<debt_id>', methods=['GET'])
    def get_techdebt(debt_id):
        from flask import jsonify
        d = techdebt.get_item(debt_id)
        if d:
            return jsonify(d.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/tech-debt/<debt_id>/fix', methods=['POST'])
    def fix_techdebt(debt_id):
        from flask import jsonify
        d = techdebt.fix_item(debt_id)
        if d:
            return jsonify({'remediated': d.remediated})
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/tech-debt/summary', methods=['GET'])
    def techdebt_summary():
        from flask import jsonify
        return jsonify(techdebt.get_summary())

    # Environments
    @app.route('/api/v4/platform-engineering/environments', methods=['GET'])
    def list_environments():
        from flask import request, jsonify
        status = request.args.get('status')
        return jsonify([e.to_dict() for e in environments.list_environments(status=status)])

    @app.route('/api/v4/platform-engineering/environments', methods=['POST'])
    def create_environment():
        from flask import request, jsonify
        data = request.get_json()
        e = environments.create_environment(data['name'], data.get('template', 'default'), data.get('ttl_hours', 24), data.get('branch', 'main'))
        return jsonify(e.to_dict()), 201

    @app.route('/api/v4/platform-engineering/environments/<env_id>', methods=['GET'])
    def get_environment(env_id):
        from flask import jsonify
        e = environments.get_environment(env_id)
        if e:
            return jsonify(e.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/environments/<env_id>', methods=['DELETE'])
    def delete_environment(env_id):
        from flask import jsonify
        environments.delete_environment(env_id)
        return jsonify({'status': 'deleted'})

    @app.route('/api/v4/platform-engineering/environments/<env_id>/extend', methods=['POST'])
    def extend_environment(env_id):
        from flask import request, jsonify
        data = request.get_json()
        environments.extend_ttl(env_id, data.get('additional_hours', 1))
        e = environments.get_environment(env_id)
        if e:
            return jsonify({'ttl_hours': e.ttl_hours})
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/environments/summary', methods=['GET'])
    def environments_summary():
        from flask import jsonify
        return jsonify(environments.get_summary())

    # API Catalog
    @app.route('/api/v4/platform-engineering/api-catalog', methods=['GET'])
    def list_apis():
        from flask import jsonify
        return jsonify([a.to_dict() for a in apis.list_apis()])

    @app.route('/api/v4/platform-engineering/api-catalog', methods=['POST'])
    def register_api():
        from flask import request, jsonify
        data = request.get_json()
        a = apis.register_api(data['name'], data.get('version', '1.0'), data.get('spec', '{}'))
        return jsonify(a.to_dict()), 201

    @app.route('/api/v4/platform-engineering/api-catalog/<api_id>', methods=['GET'])
    def get_api(api_id):
        from flask import jsonify
        a = apis.get_api(api_id)
        if a:
            return jsonify(a.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/api-catalog/summary', methods=['GET'])
    def api_catalog_summary():
        from flask import jsonify
        return jsonify(apis.get_summary())

    # Doc Generator
    @app.route('/api/v4/platform-engineering/docs', methods=['GET'])
    def list_docs():
        from flask import jsonify
        return jsonify([d.to_dict() for d in docs.list_documents()])

    @app.route('/api/v4/platform-engineering/docs', methods=['POST'])
    def generate_doc():
        from flask import request, jsonify
        data = request.get_json()
        d = docs.generate_document(data['title'], data.get('doc_type', 'adr'))
        return jsonify(d.to_dict()), 201

    @app.route('/api/v4/platform-engineering/docs/<doc_id>', methods=['GET'])
    def get_doc(doc_id):
        from flask import jsonify
        d = docs.get_document(doc_id)
        if d:
            return jsonify(d.to_dict())
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/v4/platform-engineering/docs/summary', methods=['GET'])
    def docs_summary():
        from flask import jsonify
        return jsonify(docs.get_summary())

    # Developer Pulse
    @app.route('/api/v4/platform-engineering/pulse/surveys', methods=['GET'])
    def list_surveys():
        from flask import jsonify
        return jsonify([s.to_dict() for s in pulse.list_surveys()])

    @app.route('/api/v4/platform-engineering/pulse/surveys', methods=['POST'])
    def create_survey():
        from flask import request, jsonify
        data = request.get_json()
        s = pulse.create_survey(data['title'], data.get('questions', []))
        return jsonify(s.to_dict()), 201

    @app.route('/api/v4/platform-engineering/pulse/surveys/<survey_id>/respond', methods=['POST'])
    def respond_survey(survey_id):
        from flask import request, jsonify
        data = request.get_json()
        r = pulse.submit_response(survey_id, data.get('respondent', 'anonymous'), data.get('answers', {}))
        if r:
            return jsonify({'status': 'recorded', 'response_id': r.id})
        return jsonify({'error': 'survey not found'}), 404

    @app.route('/api/v4/platform-engineering/pulse/surveys/<survey_id>/results', methods=['GET'])
    def survey_results(survey_id):
        from flask import jsonify
        results = pulse.get_survey_results(survey_id)
        return jsonify(results)

    @app.route('/api/v4/platform-engineering/pulse/summary', methods=['GET'])
    def pulse_summary():
        from flask import jsonify
        return jsonify(pulse.get_summary())

    # ── Search routes ──────────────────────────────────────────────
    @app.route('/api/v4/platform-engineering/search', methods=['GET'])
    def platform_search():
        from flask import request, jsonify
        q = request.args.get('q', '')
        if not q:
            return jsonify({"error": "query required"}), 400
        results = {"components": [], "services": [], "blueprints": [], "apis": [], "docs": []}
        for c in portal.components.values():
            if q.lower() in c.name.lower() or q.lower() in c.owner.lower():
                results["components"].append(c.to_dict())
        for s_obj in catalog.services.values():
            if q.lower() in s_obj.name.lower():
                results["services"].append(s_obj.to_dict())
        for bp in templates.blueprints.values():
            if q.lower() in bp.name.lower():
                results["blueprints"].append(bp.to_dict())
        for a_obj in apis.apis.values():
            if q.lower() in a_obj.name.lower():
                results["apis"].append(a_obj.to_dict())
        for d_obj in docs.documents.values():
            if q.lower() in d_obj.title.lower():
                results["docs"].append(d_obj.to_dict())
        return jsonify({k: v for k, v in results.items() if v})

    # ── Health routes ──────────────────────────────────────────────
    @app.route('/api/v4/platform-engineering/health', methods=['GET'])
    def platform_health():
        from flask import jsonify
        checks = {
            "developer_portal": len(portal.components) > 0,
            "golden_path_scaffolder": len(scaffold.instances) > 0,
            "service_catalog": len(catalog.services) > 0,
            "scorecards": len(scorecards.teams) > 0,
            "template_registry": len(templates.blueprints) > 0,
            "tech_debt_tracker": len(techdebt.items) > 0,
            "environment_orchestrator": len(environments.environments) > 0,
            "api_catalog": len(apis.apis) > 0,
            "doc_generator": len(docs.documents) > 0,
            "developer_pulse": len(pulse.surveys) > 0,
        }
        healthy = sum(1 for v in checks.values() if v)
        return jsonify({"status": "healthy" if healthy == len(checks) else "degraded",
                        "healthy_modules": healthy,
                        "total_modules": len(checks),
                        "checks": checks})

    # ── Export / Import ────────────────────────────────────────────
    @app.route('/api/v4/platform-engineering/export', methods=['GET'])
    def platform_export():
        from flask import jsonify
        return jsonify({
            "developer_portal": portal.to_dict(),
            "golden_path_scaffolder": scaffold.to_dict(),
            "service_catalog": catalog.to_dict(),
            "scorecards": scorecards.to_dict(),
            "template_registry": templates.to_dict(),
            "tech_debt_tracker": techdebt.to_dict(),
            "environment_orchestrator": environments.to_dict(),
            "api_catalog": apis.to_dict(),
            "doc_generator": docs.to_dict(),
            "developer_pulse": pulse.to_dict(),
        })

    @app.route('/api/v4/platform-engineering/import', methods=['POST'])
    def platform_import():
        from flask import request, jsonify
        data = request.get_json() or {}
        imported = {}
        if "developer_portal" in data:
            portal.from_dict(data["developer_portal"])
            imported["developer_portal"] = len(portal.components)
        if "service_catalog" in data:
            catalog.from_dict(data["service_catalog"])
            imported["service_catalog"] = len(catalog.services)
        if "scorecards" in data:
            scorecards.from_dict(data["scorecards"])
            imported["scorecards"] = len(scorecards.teams)
        if "template_registry" in data:
            templates.from_dict(data["template_registry"])
            imported["template_registry"] = len(templates.blueprints)
        if "tech_debt_tracker" in data:
            techdebt.from_dict(data["tech_debt_tracker"])
            imported["tech_debt_tracker"] = len(techdebt.items)
        if "environment_orchestrator" in data:
            environments.from_dict(data["environment_orchestrator"])
            imported["environment_orchestrator"] = len(environments.environments)
        if "api_catalog" in data:
            apis.from_dict(data["api_catalog"])
            imported["api_catalog"] = len(apis.apis)
        if "doc_generator" in data:
            docs.from_dict(data["doc_generator"])
            imported["doc_generator"] = len(docs.documents)
        if "developer_pulse" in data:
            pulse.from_dict(data["developer_pulse"])
            imported["developer_pulse"] = len(pulse.surveys)
        return jsonify({"imported": imported}), 201

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
