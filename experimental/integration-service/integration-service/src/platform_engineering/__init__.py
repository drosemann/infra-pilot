"""Platform Engineering & Inner Source V4 Features."""

from .developer_portal import DeveloperPortalManager
from .golden_path_scaffolder import GoldenPathScaffolder
from .service_catalog import ServiceCatalogManager
from .scorecards import ScorecardsManager
from .template_registry import TemplateRegistryManager
from .tech_debt_tracker import TechDebtTracker
from .environment_orchestrator import EnvironmentOrchestrator
from .api_catalog import ApiCatalogManager
from .doc_generator import DocGenerator
from .developer_pulse import DeveloperPulseManager

__all__ = [
    "DeveloperPortalManager",
    "GoldenPathScaffolder",
    "ServiceCatalogManager",
    "ScorecardsManager",
    "TemplateRegistryManager",
    "TechDebtTracker",
    "EnvironmentOrchestrator",
    "ApiCatalogManager",
    "DocGenerator",
    "DeveloperPulseManager",
]



# -----------------------------------------------------------
# Batch import helper
# -----------------------------------------------------------
def get_all_managers():
    """Return a dict of all platform engineering managers keyed by short name."""
    return {
        "developer_portal": DeveloperPortalManager(),
        "golden_path_scaffolder": GoldenPathScaffolder(),
        "service_catalog": ServiceCatalogManager(),
        "scorecards": ScorecardsManager(),
        "template_registry": TemplateRegistryManager(),
        "tech_debt_tracker": TechDebtTracker(),
        "environment_orchestrator": EnvironmentOrchestrator(),
        "api_catalog": ApiCatalogManager(),
        "doc_generator": DocGenerator(),
        "developer_pulse": DeveloperPulseManager(),
    }


def init_default_data(managers: dict[str, object] | None = None) -> dict[str, int]:
    """Seed each domain with a small set of representative records.

    Returns a dict keyed by manager name whose values are the count of
    records created during seeding.
    """
    from datetime import datetime, timedelta

    if managers is None:
        managers = get_all_managers()

    counts: dict[str, int] = {}

    # Developer Portal  --  3 sample components
    portal = managers["developer_portal"]
    portal.register_component("sample-api", "api", "platform-lead", "REST gateway for internal services")
    portal.register_component("worker-svc", "service", "data-team", "Background job processor")
    portal.register_component("shared-lib", "library", "platform-lead", "Common utilities and helpers")
    counts["developer_portal"] = len(portal.components)

    # Golden Path Scaffolder  --  2 sample scaffolds
    scaff = managers["golden_path_scaffolder"]
    scaff.start_scaffold("microservice-fastapi", "new-billing-svc", "finops-team")
    scaff.start_scaffold("service-node-express", "webhook-relay", "platform-lead")
    counts["golden_path_scaffolder"] = len(scaff.instances)

    # Service Catalog  --  3 sample services
    catalog = managers["service_catalog"]
    catalog.register_service("catalog-api", "platform-lead", "python")
    catalog.register_service("event-store", "data-team", "go")
    catalog.register_service("frontend-gw", "web-team", "typescript")
    counts["service_catalog"] = len(catalog.services)

    # Scorecards  --  2 teams + 1 snapshot each
    sc = managers["scorecards"]
    t1 = sc.create_team("platform-team", "engineering")
    t2 = sc.create_team("data-team", "data")
    now = datetime.utcnow()
    sc.create_snapshot(t1.team_id, now - timedelta(days=7), now, 42, 14.5, 2, 3.0, 1, 50)
    sc.create_snapshot(t2.team_id, now - timedelta(days=7), now, 18, 36.0, 5, 18.0, 3, 30)
    counts["scorecards"] = len(sc.teams)

    # Template Registry  --  2 blueprints
    reg = managers["template_registry"]
    b1 = reg.create_blueprint("vpc-baseline", reg.BlueprintType.TERRAFORM, "networking-team")
    b1.add_version("1.0.0", "resource \"aws_vpc\" \"main\" {}", "networking-team", "initial release")
    b2 = reg.create_blueprint("k8s-cluster", reg.BlueprintType.HELM, "platform-lead")
    b2.add_version("0.1.0", "apiVersion: v1\nkind: Namespace", "platform-lead", "draft")
    counts["template_registry"] = len(reg.blueprints)

    # Tech Debt  --  4 sample items
    debt = managers["tech_debt_tracker"]
    debt.detect_debt("svc-001", debt.DebtCategory.OUTDATED_DEPENDENCIES, debt.DebtSeverity.HIGH, "requests v2.25 outdated")
    debt.detect_debt("svc-002", debt.DebtCategory.SECURITY_VULNERABILITIES, debt.DebtSeverity.CRITICAL, "CVE-2025-xyz in lodash")
    debt.detect_debt("svc-003", debt.DebtCategory.TEST_COVERAGE, debt.DebtSeverity.MEDIUM, "unit test coverage below 40%")
    debt.detect_debt("svc-001", debt.DebtCategory.DEPRECATED_APIS, debt.DebtSeverity.LOW, "/v1/users endpoint deprecated")
    counts["tech_debt_tracker"] = len(debt.items)

    # Environments  --  2 running envs
    env = managers["environment_orchestrator"]
    tmpl = env.create_template("default", "1 CPU / 1 GiB RAM baseline")
    env.provision_environment("pr-200-fix-auth", env.EnvironmentType.PR, tmpl.template_id, "user-service", "ci-bot", branch="fix/auth", pr_number=200)
    env.provision_environment("staging-ml", env.EnvironmentType.BRANCH, tmpl.template_id, "data-pipeline", "ml-bot", branch="ml/experiment")
    counts["environment_orchestrator"] = len(env.environments)

    # API Catalog  --  3 APIs
    api_cat = managers["api_catalog"]
    api_cat.register_api("User API v2", api_cat.ApiType.REST, "2.0.0", "platform-lead")
    api_cat.register_api("Payment Gateway", api_cat.ApiType.GRPC, "1.5.0", "finops-team")
    api_cat.register_api("Analytics Query", api_cat.ApiType.GRAPHQL, "0.9.0", "data-team")
    counts["api_catalog"] = len(api_cat.apis)

    # Doc Generator  --  2 docs + 2 ADRs
    docs = managers["doc_generator"]
    docs.generate_architecture_doc("user-service arch", "user-service", "microservice")
    docs.generate_system_context_diagram("payment-api", [{"name": "user-service", "relationship": "-->"}])
    docs.create_adr("Use PostgreSQL", "Need reliable relational store", "Adopt RDS PostgreSQL", "approved", "data", ["alice"])
    docs.create_adr("Migrate to gRPC", "Improve inter-service latency", "Adopt gRPC for new services", "proposed", "architecture", ["bob"])
    counts["doc_generator"] = len(docs.documents) + len(docs.adrs)

    # Developer Pulse  --  1 survey + 5 mock responses
    pulse = managers["developer_pulse"]
    s = pulse.create_survey("Q1 Platform NPS", pulse.SurveyType.NPS, "platform-lead")
    pulse.launch_survey(s.survey_id)
    for resp_id in ["user-a", "user-b", "user-c", "user-d", "user-e"]:
        pulse.submit_response(s.survey_id, resp_id, {"nps": 9 if resp_id in ("user-a", "user-b") else 7},
                              nps_score=9 if resp_id in ("user-a", "user-b") else 7)
    counts["developer_pulse"] = len(pulse.surveys) + len(pulse.responses)

    return counts
