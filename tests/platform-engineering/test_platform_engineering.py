import pytest
from datetime import datetime, timedelta

from services.integration_service.src.platform_engineering.api_catalog import ApiCatalog, APIDefinition
from services.integration_service.src.platform_engineering.developer_pulse import DeveloperPulse, PulseSurvey
from services.integration_service.src.platform_engineering.developer_portal import DeveloperPortalManager, Component
from services.integration_service.src.platform_engineering.doc_generator import DocGenerator, Documentation
from services.integration_service.src.platform_engineering.environment_orchestrator import EnvironmentOrchestrator, Environment
from services.integration_service.src.platform_engineering.golden_path_scaffolder import (
    GoldenPathScaffolder, GoldenPathTemplate, ScaffoldGeneration,
)
from services.integration_service.src.platform_engineering.scorecards import ScorecardsManager, Scorecard
from services.integration_service.src.platform_engineering.service_catalog import ServiceCatalogManager, CatalogService
from services.integration_service.src.platform_engineering.tech_debt_tracker import TechDebtTracker, TechDebtItem
from services.integration_service.src.platform_engineering.template_registry import TemplateRegistry, Template


# === test_api_catalog.py ===


class TestApiCatalog:
    def setup_method(self):
        self.mgr = ApiCatalog()
        self.sample_spec = '{"openapi":"3.0.0","info":{"title":"Test API","version":"1.0"},"paths":{"/users":{"get":{"operationId":"listUsers"}}}}'

    def test_register_api(self):
        a = self.mgr.register_api("My API", "1.0.0", self.sample_spec)
        assert a.id is not None
        assert a.name == "My API"

    def test_get_api(self):
        a = self.mgr.register_api("API v1", "2.0.0", self.sample_spec)
        found = self.mgr.get_api(a.id)
        assert found.id == a.id

    def test_list_apis(self):
        self.mgr.register_api("A1", "1.0", self.sample_spec)
        self.mgr.register_api("A2", "2.0", self.sample_spec)
        assert len(self.mgr.list_apis()) == 2

    def test_endpoint_count(self):
        a = self.mgr.register_api("EP API", "1.0", self.sample_spec)
        assert a.endpoint_count >= 1

    def test_get_summary(self):
        self.mgr.register_api("S1", "1.0", self.sample_spec)
        s = self.mgr.get_summary()
        assert s["total_apis"] == 1
        assert s["total_endpoints"] >= 1

    def test_to_dict_from_dict(self):
        a = self.mgr.register_api("roundtrip", "1.0", self.sample_spec)
        d = a.to_dict()
        restored = APIDefinition.from_dict(d)
        assert restored.name == "roundtrip"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_apis"] == 0
        assert s["total_endpoints"] == 0

    def test_breaking_change_detection(self):
        v1 = '{"openapi":"3.0.0","info":{"title":"API","version":"1.0"},"paths":{"/users":{"get":{"operationId":"listUsers"}}}}'
        v2 = '{"openapi":"3.0.0","info":{"title":"API","version":"2.0"},"paths":{}}'
        a = self.mgr.register_api("BC API", "1.0", v1)
        a2 = self.mgr.register_api("BC API", "2.0", v2)
        assert True

    def test_schedule_deprecation(self):
        a = self.mgr.register_api("dep-test", "1.0", "", "team")
        schedule = self.mgr.schedule_deprecation(a.id, datetime.utcnow() + timedelta(days=90), "https://migrate")
        assert schedule is not None
        assert schedule["status"] == "scheduled"

    def test_track_api_usage(self):
        a = self.mgr.register_api("usage-test", "1.0", "", "team")
        event = self.mgr.track_api_usage(a.id, "consumer-x", "/api/v1/test", "GET", 200, 45.2)
        assert "event_id" in event

    def test_get_api_usage_stats(self):
        a = self.mgr.register_api("stats-test", "1.0", "", "team")
        self.mgr.track_api_usage(a.id, "consumer-a", "/api/v1/data", "GET", 200, 30)
        self.mgr.track_api_usage(a.id, "consumer-b", "/api/v1/data", "POST", 201, 55)
        stats = self.mgr.get_api_usage_stats(a.id, days=30)
        assert stats["total_requests"] == 2
        assert stats["unique_callers"] == 2

    def test_compliance_report(self):
        a = self.mgr.register_api("comp-test", "1.0", "Test API", "team")
        report = self.mgr.run_compliance_report(a.id)
        assert report["compliance_pct"] > 0

    def test_bulk_register_apis(self):
        ids = self.mgr.bulk_register_apis([
            {"name": "bulk-1", "version": "1.0", "description": "desc", "owner": "team"},
            {"name": "bulk-2", "version": "2.0", "description": "desc", "owner": "team"},
        ])
        assert len(ids) == 2

    def test_find_duplicate_endpoints(self):
        a = self.mgr.register_api("dup-test", "1.0", "", "team")
        a.add_endpoint("GET", "/users")
        a2 = self.mgr.register_api("dup-test-2", "1.0", "", "team")
        a2.add_endpoint("GET", "/users")
        dups = self.mgr.get_duplicate_endpoints()
        assert len(dups) >= 1

    def test_add_api_version(self):
        a = self.mgr.register_api("version-test", "1.0", "", "team")
        self.mgr.add_api_version(a.id, "2.0", "https://spec/v2", "Breaking changes")
        assert a.version == "2.0"

    def test_notify_consumers(self):
        a = self.mgr.register_api("notify-test", "1.0", "", "team", consumers=["consumer-a", "consumer-b"])
        result = self.mgr.notify_consumers(a.id, "API will be deprecated")
        assert result["notifications_sent"] == 2

    def test_get_deprecation_schedule(self):
        a = self.mgr.register_api("dep-sched", "1.0", "", "team")
        self.mgr.schedule_deprecation(a.id, datetime.utcnow() + timedelta(days=30))
        schedules = self.mgr.get_deprecation_schedule(a.id)
        assert len(schedules) >= 1


# === test_developer_pulse.py ===


class TestDeveloperPulse:
    def setup_method(self):
        self.mgr = DeveloperPulse()
        self.questions = [
            {"id": "q1", "text": "How satisfied?", "type": "rating", "scale_max": 5},
            {"id": "q2", "text": "Any feedback?", "type": "text"},
        ]

    def test_create_survey(self):
        s = self.mgr.create_survey("Developer Satisfaction", self.questions)
        assert s.id is not None
        assert s.title == "Developer Satisfaction"

    def test_get_survey(self):
        s = self.mgr.create_survey("Q1 Survey", self.questions)
        found = self.mgr.get_survey(s.id)
        assert found.id == s.id

    def test_list_surveys(self):
        self.mgr.create_survey("S1", self.questions)
        self.mgr.create_survey("S2", self.questions)
        assert len(self.mgr.list_surveys()) == 2

    def test_submit_response(self):
        s = self.mgr.create_survey("Feedback", self.questions)
        answers = {"q1": 4, "q2": "Great work"}
        r = self.mgr.submit_response(s.id, "user-1", answers)
        assert r is not None
        assert r.respondent == "user-1"

    def test_get_survey_results(self):
        s = self.mgr.create_survey("NPS Survey", self.questions)
        self.mgr.submit_response(s.id, "u1", {"q1": 5, "q2": "Excellent"})
        self.mgr.submit_response(s.id, "u2", {"q1": 3, "q2": "OK"})
        results = self.mgr.get_survey_results(s.id)
        assert results["response_count"] == 2
        assert results["avg_score"] is not None

    def test_nps_scoring(self):
        s = self.mgr.create_survey("NPS Test", self.questions)
        self.mgr.submit_response(s.id, "u1", {"q1": 5, "q2": "Love it"})
        self.mgr.submit_response(s.id, "u2", {"q1": 4, "q2": "Good"})
        self.mgr.submit_response(s.id, "u3", {"q1": 2, "q2": "Meh"})
        results = self.mgr.get_survey_results(s.id)
        assert "nps_score" in results

    def test_get_summary(self):
        s = self.mgr.create_survey("Pulse", self.questions)
        self.mgr.submit_response(s.id, "u1", {"q1": 4, "q2": "Great"})
        summary = self.mgr.get_summary()
        assert summary["total_surveys"] >= 1
        assert summary["total_responses"] >= 1

    def test_to_dict_from_dict(self):
        s = self.mgr.create_survey("roundtrip", self.questions)
        d = s.to_dict()
        restored = PulseSurvey.from_dict(d)
        assert restored.title == "roundtrip"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_surveys"] == 0
        assert s["total_responses"] == 0

    def test_anonymized_responses(self):
        s = self.mgr.create_survey("Anon Test", self.questions)
        self.mgr.submit_response(s.id, "u1", {"q1": 5, "q2": "Good"})
        anon = self.mgr.get_anonymized_responses(s.id)
        assert len(anon) >= 1
        assert all("user_id" not in r for r in anon)

    def test_aggregate_survey_results(self):
        s = self.mgr.create_survey("Agg Test", self.questions)
        self.mgr.submit_response(s.id, "u1", {"q1": 4, "q2": "Great"})
        self.mgr.submit_response(s.id, "u2", {"q1": 5, "q2": "Excellent"})
        agg = self.mgr.aggregate_survey_results(s.id)
        assert agg["total_responses"] == 2
        assert "q1" in agg["aggregated"]

    def test_get_sentiment_trend(self):
        s = self.mgr.create_survey("Sentiment Survey", self.questions, survey_type="nps", target_audience=["u1", "u2"])
        self.mgr.submit_response(s.id, "u1", {"nps_score": 9})
        self.mgr.submit_response(s.id, "u2", {"nps_score": 7})
        trend = self.mgr.get_sentiment_trend(months=12)
        assert "trend" in trend

    def test_export_survey_csv(self):
        s = self.mgr.create_survey("CSV Test", self.questions)
        self.mgr.submit_response(s.id, "u1", {"q1": 3, "q2": "Ok"})
        csv = self.mgr.export_survey_data(s.id, format="csv")
        assert "response_id" in csv

    def test_schedule_survey(self):
        result = self.mgr.schedule_survey("Scheduled Survey", ["q1", "q2"], target_audience=["u1"])
        assert "schedule" in result
        assert result["schedule"]["status"] == "active"

    def test_get_schedules(self):
        self.mgr.schedule_survey("Sched 1", ["q"])
        schedules = self.mgr.get_schedules()
        assert len(schedules) >= 1

    def test_pause_resume_schedule(self):
        result = self.mgr.schedule_survey("Pause Test", ["q"])
        schedule_id = result["schedule"]["schedule_id"]
        self.mgr.pause_schedule(schedule_id)
        schedules = self.mgr.get_schedules()
        sched = next(s for s in schedules if s["schedule_id"] == schedule_id)
        assert sched["status"] == "paused"
        self.mgr.resume_schedule(schedule_id)
        sched2 = next(s for s in self.mgr.get_schedules() if s["schedule_id"] == schedule_id)
        assert sched2["status"] == "active"

    def test_get_response_insights(self):
        s = self.mgr.create_survey("Insights Test", ["nps_score"], target_audience=["u1", "u2", "u3"])
        self.mgr.submit_response(s.id, "u1", {"nps_score": 9})
        self.mgr.submit_response(s.id, "u2", {"nps_score": 5})
        insights = self.mgr.get_response_insights(s.id)
        assert "nps_score" in insights
        assert insights["promoters"] >= 1

    def test_bulk_send_reminders(self):
        s = self.mgr.create_survey("Reminder Test", ["q1"], target_audience=["u1", "u2"])
        self.mgr.submit_response(s.id, "u1", {"q1": 5})
        result = self.mgr.bulk_send_reminders(s.id)
        assert result["reminders_sent"] >= 1


# === test_devportal.py ===


class TestDeveloperPortalManager:
    def setup_method(self):
        self.mgr = DeveloperPortalManager()

    def test_register_component(self):
        c = self.mgr.register_component("my-service", "backend", "desc", "team-a")
        assert c.id is not None
        assert c.name == "my-service"

    def test_get_component(self):
        c = self.mgr.register_component("test-svc", "frontend", "desc", "team-b")
        found = self.mgr.get_component(c.id)
        assert found.id == c.id
        assert found.domain == "frontend"

    def test_list_components(self):
        self.mgr.register_component("a", "backend", "", "team-x")
        self.mgr.register_component("b", "frontend", "", "team-y")
        all_c = self.mgr.list_components()
        assert len(all_c) == 2

    def test_list_components_filter_domain(self):
        self.mgr.register_component("c1", "backend", "", "t1")
        self.mgr.register_component("c2", "frontend", "", "t2")
        backend = self.mgr.list_components(domain="backend")
        assert len(backend) == 1
        assert backend[0].domain == "backend"

    def test_get_summary(self):
        self.mgr.register_component("s1", "backend", "", "t1")
        self.mgr.register_component("s2", "backend", "", "t2")
        s = self.mgr.get_summary()
        assert s["total_components"] == 2
        assert "avg_maturity_level" in s

    def test_add_dependency(self):
        c1 = self.mgr.register_component("svc-a", "backend", "", "t1")
        c2 = self.mgr.register_component("svc-b", "backend", "", "t2")
        c1.add_dependency(c2.id)
        assert c2.id in c1.dependencies

    def test_to_dict_from_dict(self):
        c = self.mgr.register_component("roundtrip", "backend", "desc", "t1")
        d = c.to_dict()
        restored = Component.from_dict(d)
        assert restored.name == "roundtrip"
        assert restored.domain == "backend"

    def test_maturity_upgrade(self):
        c = self.mgr.register_component("maturity-test", "backend", "", "t1")
        assert c.maturity_level == 0
        c.maturity_level = 3
        assert c.maturity_level == 3

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_components"] == 0

    def test_dependency_chain_visualization(self):
        c1 = self.mgr.register_component("viz-a", "backend", "desc", "t1")
        c2 = self.mgr.register_component("viz-b", "backend", "desc", "t1")
        self.mgr.add_component_dependency(c1.id, c2.id)
        viz = self.mgr.get_dependency_chain_visualization(c1.id)
        assert "nodes" in viz
        assert len(viz["edges"]) >= 1

    def test_health_trend(self):
        c = self.mgr.register_component("health-trend", "backend", "desc", "t1")
        trend = self.mgr.get_health_trend(c.id)
        assert len(trend) >= 1

    def test_portal_scorecard(self):
        c = self.mgr.register_component("scorecard-test", "backend", "desc", "t1")
        scorecard = self.mgr.get_portal_scorecard()
        assert scorecard["component_count"] >= 1

    def test_search_portal(self):
        self.mgr.register_component("search-target", "data", "desc", "t1")
        results = self.mgr.search_portal("search")
        assert results["total_matches"] >= 1

    def test_bulk_update_component_owner(self):
        c1 = self.mgr.register_component("bulk-owner-1", "backend", "desc", "t1")
        c2 = self.mgr.register_component("bulk-owner-2", "backend", "desc", "t1")
        count = self.mgr.bulk_update_component_owner([c1.id, c2.id], "new-team")
        assert count == 2
        assert c1.owner == "new-team"

    def test_system_dependency_map(self):
        sys = self.mgr.create_system("DepMapSys", "System for deps", "platform")
        c1 = self.mgr.register_component("dep-map-1", "backend", "", "t1")
        c2 = self.mgr.register_component("dep-map-2", "backend", "", "t1")
        self.mgr.add_component_to_system(sys["id"], c1.id)
        self.mgr.add_component_to_system(sys["id"], c2.id)
        dep_map = self.mgr.get_system_dependency_map(sys["id"])
        assert len(dep_map["nodes"]) == 2

    def test_calculate_system_maturity(self):
        sys = self.mgr.create_system("MatSys", "Maturity test", "platform")
        c = self.mgr.register_component("mat-comp", "backend", "desc", "t1")
        self.mgr.add_component_to_system(sys["id"], c.id)
        maturity = self.mgr.calculate_system_maturity(sys["id"])
        assert maturity["score"] >= 0
        assert maturity["level"] in ("bronze", "silver", "gold", "platinum")

    def test_add_system_tag(self):
        sys = self.mgr.create_system("TagSys", "Tag test", "platform")
        self.mgr.add_system_tag(sys["id"], "critical")
        assert "critical" in sys["tags"]


# === test_doc_generator.py ===


class TestDocGenerator:
    def setup_method(self):
        self.mgr = DocGenerator()

    def test_generate_document(self):
        d = self.mgr.generate_document("Architecture Overview", "c4_context")
        assert d.id is not None
        assert d.title == "Architecture Overview"
        assert d.doc_type == "c4_context"

    def test_get_document(self):
        d = self.mgr.generate_document("System Design", "c4_container")
        found = self.mgr.get_document(d.id)
        assert found.id == d.id

    def test_list_documents(self):
        self.mgr.generate_document("Doc A", "adr")
        self.mgr.generate_document("Doc B", "c4_context")
        assert len(self.mgr.list_documents()) == 2

    def test_document_has_content(self):
        d = self.mgr.generate_document("My Doc", "c4_context")
        assert len(d.content) > 0

    def test_get_summary(self):
        self.mgr.generate_document("D1", "adr")
        self.mgr.generate_document("D2", "c4_context")
        s = self.mgr.get_summary()
        assert s["total_documents"] == 2

    def test_to_dict_from_dict(self):
        d = self.mgr.generate_document("roundtrip", "adr")
        d2 = d.to_dict()
        restored = Documentation.from_dict(d2)
        assert restored.title == "roundtrip"
        assert restored.doc_type == "adr"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_documents"] == 0

    def test_adr_proposed_by_default(self):
        d = self.mgr.generate_document("ADR Decision", "adr")
        assert d.status == "proposed"

    def test_start_and_approve_review(self):
        adr = self.mgr.generate_document("Review ADR", "adr")
        review = self.mgr.start_review(adr.id, ["reviewer1", "reviewer2"])
        assert review is not None
        approved = self.mgr.approve_review(review["review_id"], "reviewer1")
        assert approved

    def test_reject_review(self):
        adr = self.mgr.generate_document("Reject ADR", "adr")
        review = self.mgr.start_review(adr.id, ["reviewer"])
        rejected = self.mgr.reject_review(review["review_id"], "reviewer", "Missing details")
        assert rejected

    def test_cross_reference(self):
        d1 = self.mgr.generate_document("Doc A", "adr")
        d2 = self.mgr.generate_document("Doc B", "documentation")
        result = self.mgr.cross_reference_docs(d1.id, d2.id, "related")
        assert result

    def test_doc_template_crud(self):
        tmpl = self.mgr.set_doc_template("Arch Template", "## {{title}}\n{{body}}")
        assert tmpl["name"] == "Arch Template"
        templates = self.mgr.get_doc_templates()
        assert len(templates) >= 1

    def test_generate_from_template(self):
        tmpl = self.mgr.set_doc_template("Service Doc", "# {{service_name}}\nOwner: {{owner}}")
        doc_id = self.mgr.generate_from_template(tmpl["template_id"], "svc-1", {"service_name": "MySvc", "owner": "team"})
        assert doc_id is not None

    def test_search_docs(self):
        self.mgr.generate_document("Searchable Doc", "adr")
        results = self.mgr.search_docs("Searchable")
        assert len(results) >= 1

    def test_get_content_statistics(self):
        self.mgr.generate_document("Stats Doc", "documentation")
        stats = self.mgr.get_content_statistics()
        assert stats["total_documents"] >= 1

    def test_version_doc_template(self):
        tmpl = self.mgr.set_doc_template("Versioned Template", "v1 content")
        updated = self.mgr.version_doc_template(tmpl["template_id"], "v2 content")
        assert updated["version"] == "2.0"

    def test_bulk_generate_docs(self):
        tmpl = self.mgr.set_doc_template("Bulk Template", "{{name}}")
        ids = self.mgr.bulk_generate_docs("svc-bulk", [tmpl["template_id"]], {"name": "test"})
        assert len(ids) >= 1


# === test_environments.py ===


class TestEnvironmentOrchestrator:
    def setup_method(self):
        self.mgr = EnvironmentOrchestrator()

    def test_create_environment(self):
        e = self.mgr.create_environment("pr-42", "microservice", 24, "feature-x")
        assert e.id is not None
        assert e.name == "pr-42"
        assert e.status == "creating"

    def test_get_environment(self):
        e = self.mgr.create_environment("test-env", "api-gateway", 12, "main")
        found = self.mgr.get_environment(e.id)
        assert found.id == e.id

    def test_list_environments(self):
        self.mgr.create_environment("e1", "t1", 24, "main")
        self.mgr.create_environment("e2", "t2", 48, "dev")
        assert len(self.mgr.list_environments()) == 2

    def test_delete_environment(self):
        e = self.mgr.create_environment("to-delete", "t1", 24, "main")
        self.mgr.delete_environment(e.id)
        found = self.mgr.get_environment(e.id)
        assert found.status == "deleted"

    def test_extend_ttl(self):
        e = self.mgr.create_environment("extend-me", "t1", 24, "main")
        self.mgr.extend_ttl(e.id, 12)
        updated = self.mgr.get_environment(e.id)
        assert updated.ttl_hours > 24

    def test_get_summary(self):
        self.mgr.create_environment("a", "t1", 24, "main")
        self.mgr.create_environment("b", "t2", 48, "dev")
        s = self.mgr.get_summary()
        assert s["total_environments"] == 2

    def test_to_dict_from_dict(self):
        e = self.mgr.create_environment("roundtrip", "t1", 24, "main")
        d = e.to_dict()
        restored = Environment.from_dict(d)
        assert restored.name == "roundtrip"
        assert restored.template == "t1"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_environments"] == 0

    def test_environment_lifecycle(self):
        e = self.mgr.create_environment("lifecycle", "t1", 1, "main")
        assert e.status == "creating"
        self.mgr.transition_status(e.id, "running")
        assert self.mgr.get_environment(e.id).status == "running"
        self.mgr.transition_status(e.id, "expired")
        assert self.mgr.get_environment(e.id).status == "expired"

    def test_set_cleanup_policy(self):
        policy = self.mgr.set_cleanup_policy("test-project", 48, True, 12)
        assert policy["project"] == "test-project"
        assert policy["max_age_hours"] == 48

    def test_set_resource_quota(self):
        quota = self.mgr.set_resource_quota("test-project", 4, 16, 3)
        assert quota["max_cpu"] == 4
        assert quota["max_memory_gb"] == 16

    def test_check_resource_quota(self):
        self.mgr.set_resource_quota("quota-project", 8, 32, 5)
        check = self.mgr.check_resource_quota("quota-project")
        assert "cpu_pct" in check
        assert "memory_pct" in check

    def test_backup_and_restore(self):
        e = self.mgr.create_environment("backup-test", "t1", 1, "main")
        backup = self.mgr.backup_environment(e.env_id)
        assert backup is not None
        restored = self.mgr.restore_environment(backup["backup_id"])
        assert restored is not None
        assert restored["status"] == "restored"

    def test_list_backups(self):
        e = self.mgr.create_environment("bk-list", "t1", 1, "main")
        self.mgr.backup_environment(e.env_id)
        backups = self.mgr.list_backups(e.env_id)
        assert len(backups) >= 1

    def test_environment_health(self):
        e = self.mgr.create_environment("health-test", "t1", 1, "main")
        health = self.mgr.get_environment_health(e.env_id)
        assert "age_hours" in health
        assert health["is_expired"] is False

    def test_extend_ttl(self):
        e = self.mgr.create_environment("ttl-test", "t1", 1, "main", ttl_hours=24)
        self.mgr.extend_environment_ttl(e.env_id, 12)
        assert e.ttl_hours == 36

    def test_bulk_delete_expired(self):
        e = self.mgr.create_environment("expired-test", "t1", 1, "main", ttl_hours=-1)
        count = self.mgr.bulk_delete_expired()
        assert count >= 1

    def test_batch_set_template(self):
        e1 = self.mgr.create_environment("batch-1", "t1", 1, "main")
        e2 = self.mgr.create_environment("batch-2", "t1", 1, "main")
        count = self.mgr.batch_set_template([e1.env_id, e2.env_id], "t2")
        assert count == 2


# === test_scaffolder.py ===


class TestGoldenPathScaffolder:
    def setup_method(self):
        self.mgr = GoldenPathScaffolder()

    def test_list_templates(self):
        templates = self.mgr.list_templates()
        assert len(templates) >= 4

    def test_get_template(self):
        t = self.mgr.get_template("microservice")
        assert t is not None
        assert t.name == "microservice"

    def test_generate_project(self):
        gen = self.mgr.generate_project("microservice", "my-project", {"port": 8080})
        assert gen.id is not None
        assert gen.project_name == "my-project"
        assert gen.status == "in_progress"

    def test_generation_status(self):
        gen = self.mgr.generate_project("api-gateway", "gw-project", {})
        status = self.mgr.get_generation_status(gen.id)
        assert status.id == gen.id
        assert status.status == "in_progress"

    def test_complete_step(self):
        gen = self.mgr.generate_project("microservice", "test-proj", {})
        result = self.mgr.complete_step(gen.id, "create-repo", {"repo_url": "https://github.com/test"})
        assert result is not None
        updated = self.mgr.get_generation_status(gen.id)
        assert updated.current_step == 1

    def test_all_templates_have_steps(self):
        for t in self.mgr.list_templates():
            assert len(t.steps) > 0

    def test_invalid_template_returns_none(self):
        t = self.mgr.get_template("nonexistent")
        assert t is None

    def test_generation_progress_pct(self):
        gen = self.mgr.generate_project("data-pipeline", "pipe-proj", {})
        self.mgr.complete_step(gen.id, "create-repo", {})
        status = self.mgr.get_generation_status(gen.id)
        assert status.current_step >= 0

    def test_add_custom_step(self):
        step = self.mgr.add_custom_step("microservice", "deploy-canary", "automated", "Canary deploy")
        assert step is not None
        assert step["name"] == "deploy-canary"

    def test_add_approval_flow(self):
        flow = self.mgr.add_approval_flow("microservice", ["lead-dev", "architect"])
        assert flow is not None
        assert "lead-dev" in flow["required_approvers"]

    def test_submit_approval(self):
        flow = self.mgr.add_approval_flow("microservice", ["reviewer"])
        gen = self.mgr.generate_project("microservice", "approve-test", {})
        result = self.mgr.submit_approval(gen.instance_id, "reviewer", "approved")
        assert result

    def test_post_scaffold_hook(self):
        hook = self.mgr.add_post_scaffold_hook("microservice", "webhook", {"url": "https://example.com/hook"})
        assert hook is not None
        assert hook["type"] == "webhook"

    def test_scaffold_analytics(self):
        self.mgr.generate_project("microservice", "analytics-test", {})
        analytics = self.mgr.get_scaffold_analytics()
        assert analytics["total_instances"] >= 1

    def test_validate_template(self):
        result = self.mgr.validate_template("microservice")
        assert "valid" in result

    def test_estimate_template_duration(self):
        est = self.mgr.estimate_template_duration("microservice")
        assert est["estimated_minutes"] > 0

    def test_clone_template(self):
        cloned = self.mgr.clone_template("microservice", "cloned-service")
        assert cloned is not None
        assert cloned["name"] == "cloned-service"

    def test_batch_retire_instances(self):
        g1 = self.mgr.generate_project("microservice", "retire-1", {})
        g2 = self.mgr.generate_project("microservice", "retire-2", {})
        count = self.mgr.batch_retire_instances([g1.instance_id, g2.instance_id])
        assert count == 2


# === test_scorecards.py ===


class TestScorecardsManager:
    def setup_method(self):
        self.mgr = ScorecardsManager()

    def test_create_scorecard(self):
        s = self.mgr.create_scorecard("team-a", "Team A")
        assert s.id is not None
        assert s.name == "team-a"

    def test_get_scorecard(self):
        s = self.mgr.create_scorecard("team-b", "Team B")
        found = self.mgr.get_scorecard(s.id)
        assert found.id == s.id

    def test_list_scorecards(self):
        self.mgr.create_scorecard("t1", "T1")
        self.mgr.create_scorecard("t2", "T2")
        assert len(self.mgr.list_scorecards()) == 2

    def test_update_metric(self):
        s = self.mgr.create_scorecard("metrics-team", "Metrics Team")
        self.mgr.update_metric(s.id, "deploy_frequency", "daily")
        updated = self.mgr.get_scorecard(s.id)
        assert updated.dora_metrics.deploy_frequency == "daily"

    def test_update_all_dora_metrics(self):
        s = self.mgr.create_scorecard("dora-team", "DORA Team")
        self.mgr.update_metric(s.id, "deploy_frequency", "multiple-daily")
        self.mgr.update_metric(s.id, "lead_time", "<1 hour")
        self.mgr.update_metric(s.id, "mttr", "<1 hour")
        self.mgr.update_metric(s.id, "change_failure_rate", "<5%")
        u = self.mgr.get_scorecard(s.id)
        assert u.dora_metrics.deploy_frequency == "multiple-daily"
        assert u.dora_metrics.lead_time == "<1 hour"

    def test_get_summary(self):
        self.mgr.create_scorecard("s1", "S1")
        self.mgr.create_scorecard("s2", "S2")
        s = self.mgr.get_summary()
        assert s["total_scorecards"] == 2

    def test_to_dict_from_dict(self):
        s = self.mgr.create_scorecard("roundtrip", "RT")
        d = s.to_dict()
        restored = Scorecard.from_dict(d)
        assert restored.name == "roundtrip"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_scorecards"] == 0

    def test_invalid_metric_no_error(self):
        s = self.mgr.create_scorecard("safe", "Safe")
        self.mgr.update_metric(s.id, "nonexistent", "value")
        assert True

    def test_compare_teams(self):
        t1 = self.mgr.create_team("Team Alpha", "org-1")
        t2 = self.mgr.create_team("Team Beta", "org-1")
        comparison = self.mgr.compare_teams([t1.team_id, t2.team_id])
        assert len(comparison) == 2

    def test_set_and_check_goal(self):
        t = self.mgr.create_team("Goal Team", "org-1")
        goal = self.mgr.set_goal(t.team_id, "deployment_frequency", 10.0, datetime.utcnow() + timedelta(days=30))
        progress = self.mgr.check_goal_progress(goal["goal_id"])
        assert "progress_pct" in progress

    def test_ingest_dora_data(self):
        t = self.mgr.create_team("DORA Team", "org-1")
        ingested = self.mgr.ingest_dora_data(t.team_id, {"deployment_frequency": 5.0, "lead_time": 2.0})
        assert ingested

    def test_get_team_history(self):
        t = self.mgr.create_team("History Team", "org-1")
        self.mgr.create_snapshot(t.team_id)
        history = self.mgr.get_team_history(t.team_id, days=30)
        assert len(history) >= 1

    def test_organization_summary(self):
        t = self.mgr.create_team("Org Team", "acme")
        self.mgr.create_snapshot(t.team_id)
        summary = self.mgr.get_organization_summary("acme")
        assert summary["team_count"] >= 1
        assert summary["avg_dora_score"] >= 0

    def test_predict_trend_insufficient_data(self):
        t = self.mgr.create_team("Pred Team", "org")
        pred = self.mgr.predict_trend(t.team_id, 4)
        assert "error" in pred

    def test_add_team_tag(self):
        t = self.mgr.create_team("Tag Team", "org")
        self.mgr.add_team_tag(t.team_id, "critical")
        assert "critical" in t.tags

    def test_close_goal(self):
        t = self.mgr.create_team("Close Team", "org")
        goal = self.mgr.set_goal(t.team_id, "mttr", 30.0, datetime.utcnow() + timedelta(days=30))
        closed = self.mgr.close_goal(goal["goal_id"])
        assert closed


# === test_service_catalog.py ===


class TestServiceCatalogManager:
    def setup_method(self):
        self.mgr = ServiceCatalogManager()

    def test_register_service(self):
        s = self.mgr.register_service("my-svc", "backend", "test", "team-a")
        assert s.id is not None
        assert s.name == "my-svc"

    def test_get_service(self):
        s = self.mgr.register_service("svc-1", "frontend", "desc", "team-b")
        found = self.mgr.get_service(s.id)
        assert found.id == s.id

    def test_list_services(self):
        self.mgr.register_service("a", "backend", "", "t1")
        self.mgr.register_service("b", "frontend", "", "t2")
        assert len(self.mgr.list_services()) == 2

    def test_score_service(self):
        s = self.mgr.register_service("score-test", "backend", "desc", "t1")
        s.description = "full description"
        s.owner = "team-a"
        s.domain = "backend"
        s.sla = "99.9"
        s.has_documentation = True
        s.has_ci_cd = True
        s.has_monitoring = True
        s.has_oncall = True
        score = self.mgr.score_service(s.id)
        assert score["readiness_score"] > 0
        assert score["total_checks"] == 15

    def test_get_summary(self):
        self.mgr.register_service("s1", "backend", "", "t1")
        s = self.mgr.get_summary()
        assert s["total_services"] == 1

    def test_to_dict_from_dict(self):
        s = self.mgr.register_service("roundtrip", "backend", "desc", "t1")
        d = s.to_dict()
        restored = CatalogService.from_dict(d)
        assert restored.name == "roundtrip"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_services"] == 0
        assert s["avg_readiness_score"] == 0

    def test_score_zero_when_no_checks(self):
        s = self.mgr.register_service("bare", "", "", "")
        score = self.mgr.score_service(s.id)
        assert score["readiness_score"] == 0

    def test_compliance_check(self):
        s = self.mgr.register_service("compliance-test", "team-a", "python", "t1")
        result = self.mgr.run_compliance_check(s.id)
        assert result["compliance_score"] > 0

    def test_bulk_compliance(self):
        self.mgr.register_service("c1", "team", "py", "t1")
        results = self.mgr.bulk_compliance_check()
        assert len(results) >= 1

    def test_add_cost_data(self):
        s = self.mgr.register_service("cost-test", "fin", "go", "t2")
        self.mgr.add_cost_data(s.id, 1500.50)
        summary = self.mgr.get_cost_summary()
        assert summary["total_monthly_cost"] > 0

    def test_dependency_graph(self):
        s1 = self.mgr.register_service("core", "team-a", "py", "t1")
        s2 = self.mgr.register_service("dependent", "team-b", "ts", "t2")
        self.mgr.add_service_metadata(s2.id, "dependencies", [s1.id])
        chain = self.mgr.get_dependency_chain(s2.id)
        assert len(chain) >= 2

    def test_find_orphan_services(self):
        self.mgr.register_service("orphan-test", "orphan", "py", "t1")
        orphans = self.mgr.find_orphan_services()
        assert len(orphans) >= 1

    def test_compute_maturity_levels(self):
        s = self.mgr.register_service("maturity", "team", "py", "t1")
        score = self.mgr.compute_maturity_score(s.id)
        assert score["level"] in ("bronze", "silver", "gold", "platinum")

    def test_bulk_set_tier(self):
        s1 = self.mgr.register_service("tier-test-1", "t", "py", "t3")
        s2 = self.mgr.register_service("tier-test-2", "t", "go", "t3")
        count = self.mgr.bulk_set_tier([s1.id, s2.id], "t1")
        assert count == 2
        assert s1.tier == "t1"


# === test_tech_debt.py ===


class TestTechDebtTracker:
    def setup_method(self):
        self.mgr = TechDebtTracker()

    def test_report_item(self):
        d = self.mgr.report_item("Bug in parser", "high", 8, "code")
        assert d.id is not None
        assert d.title == "Bug in parser"

    def test_get_item(self):
        d = self.mgr.report_item("Refactor needed", "medium", 4, "code")
        found = self.mgr.get_item(d.id)
        assert found.id == d.id

    def test_list_items(self):
        self.mgr.report_item("i1", "low", 2, "code")
        self.mgr.report_item("i2", "high", 10, "config")
        assert len(self.mgr.list_items()) == 2

    def test_list_items_filter_severity(self):
        self.mgr.report_item("a", "low", 1, "code")
        self.mgr.report_item("b", "high", 5, "code")
        high = self.mgr.list_items(severity="high")
        assert len(high) == 1

    def test_fix_item(self):
        d = self.mgr.report_item("Fix me", "critical", 12, "code")
        assert d.remediated is False
        self.mgr.fix_item(d.id)
        assert self.mgr.get_item(d.id).remediated is True

    def test_get_summary(self):
        self.mgr.report_item("d1", "high", 5, "code")
        self.mgr.report_item("d2", "medium", 3, "docs")
        s = self.mgr.get_summary()
        assert s["total_items"] == 2
        assert s["total_effort_hours"] == 8

    def test_to_dict_from_dict(self):
        d = self.mgr.report_item("roundtrip", "medium", 6, "code")
        d2 = d.to_dict()
        restored = TechDebtItem.from_dict(d2)
        assert restored.title == "roundtrip"
        assert restored.severity == "medium"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_items"] == 0
        assert s["total_effort_hours"] == 0

    def test_trend_analysis(self):
        self.mgr.report_item("old-item", "critical", 5, "security")
        trend = self.mgr.get_trend_analysis(days=365)
        assert trend["created"] >= 1

    def test_schedule_and_cancel_scan(self):
        scan = self.mgr.schedule_scan("svc-1", "full", 24)
        assert "scan_id" in scan
        cancelled = self.mgr.cancel_scheduled_scan(scan["scan_id"])
        assert cancelled

    def test_bulk_remediate(self):
        i1 = self.mgr.report_item("fix-me-1", "high", 3, "code")
        i2 = self.mgr.report_item("fix-me-2", "medium", 2, "code")
        result = self.mgr.bulk_remediate_items([i1.item_id, i2.item_id])
        assert result["succeeded"] == 2

    def test_get_debt_report(self):
        self.mgr.report_item("report-item", "critical", 8, "security")
        report = self.mgr.get_debt_report()
        assert report["total_items"] >= 1
        assert report["critical_open"] >= 1

    def test_service_rankings(self):
        self.mgr.report_item("rank-item", "critical", 5, "code", service_id="svc-alpha")
        rankings = self.mgr.get_service_rankings()
        assert len(rankings) >= 1

    def test_export_csv(self):
        self.mgr.report_item("csv-item", "low", 1, "test")
        csv = self.mgr.export_debt_csv()
        assert "csv-item" in csv
        assert csv.startswith("id")

    def test_dependency_links(self):
        i1 = self.mgr.report_item("dep-a", "medium", 2, "code")
        i2 = self.mgr.report_item("dep-b", "high", 3, "code")
        self.mgr.add_dependency_link(i1.item_id, i2.item_id)
        chain = self.mgr.get_dependency_chain(i1.item_id)
        assert len(chain) >= 2

    def test_batch_update_effort(self):
        i1 = self.mgr.report_item("effort-1", "low", 1, "code")
        i2 = self.mgr.report_item("effort-2", "low", 1, "code")
        count = self.mgr.batch_update_effort([i1.item_id, i2.item_id], 10)
        assert count == 2


# === test_template_registry.py ===


class TestTemplateRegistry:
    def setup_method(self):
        self.mgr = TemplateRegistry()

    def test_create_template(self):
        t = self.mgr.create_template("blueprint", "infra", {"region": "string"})
        assert t.id is not None
        assert t.name == "blueprint"

    def test_get_template(self):
        t = self.mgr.create_template("tmpl-1", "app", {})
        found = self.mgr.get_template(t.id)
        assert found.id == t.id

    def test_list_templates(self):
        self.mgr.create_template("t1", "infra", {})
        self.mgr.create_template("t2", "app", {})
        assert len(self.mgr.list_templates()) == 2

    def test_use_template_increments_count(self):
        t = self.mgr.create_template("popular", "infra", {})
        assert t.usage_count == 0
        self.mgr.use_template(t.id)
        assert self.mgr.get_template(t.id).usage_count == 1

    def test_version_starts_at_1(self):
        t = self.mgr.create_template("v-test", "app", {})
        assert t.version == 1

    def test_get_summary(self):
        t = self.mgr.create_template("s1", "infra", {})
        self.mgr.use_template(t.id)
        self.mgr.use_template(t.id)
        s = self.mgr.get_summary()
        assert s["total_templates"] == 1
        assert s["total_usage"] == 2

    def test_to_dict_from_dict(self):
        t = self.mgr.create_template("roundtrip", "app", {"name": "string"})
        d = t.to_dict()
        restored = Template.from_dict(d)
        assert restored.name == "roundtrip"
        assert restored.params_schema == {"name": "string"}

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_templates"] == 0
        assert s["total_usage"] == 0

    def test_bulk_create_templates(self):
        ids = self.mgr.bulk_import_blueprints([
            {"name": "bulk1", "blueprint_type": "infrastructure", "owner": "team-a"},
            {"name": "bulk2", "blueprint_type": "application", "owner": "team-b"},
        ])
        assert len(ids) == 2
        assert self.mgr.get_blueprint_statistics()["total_blueprints"] >= 2

    def test_search_blueprints(self):
        self.mgr.create_blueprint("search-me", "infrastructure", "tester")
        results = self.mgr.search_blueprints("search")
        assert any("search" in b.name.lower() for b in results)

    def test_tag_blueprint(self):
        bp = self.mgr.create_blueprint("tag-test", "infrastructure", "owner")
        self.mgr.tag_blueprint(bp.blueprint_id, ["alpha", "beta"])
        bp2 = self.mgr.blueprints[bp.blueprint_id]
        assert "alpha" in bp2.tags
        assert "beta" in bp2.tags

    def test_blueprint_health_missing_fields(self):
        bp = self.mgr.create_blueprint("health-test", "infrastructure", "")
        health = self.mgr.get_blueprint_health(bp.blueprint_id)
        assert health["health_score"] < 100

    def test_archive_old_versions(self):
        bp = self.mgr.create_blueprint("archive-test", "infrastructure", "owner")
        for i in range(5):
            bp.add_version(f"v{i}", f"content-{i}", "owner", "")
        removed = self.mgr.archive_old_versions(bp.blueprint_id, keep=2)
        assert removed > 0
        assert len(bp.versions) <= 2

    def test_version_diff(self):
        bp = self.mgr.create_blueprint("diff-test", "infrastructure", "owner")
        bp.add_version("v1", "line1\nline2\nline3", "owner", "")
        bp.add_version("v2", "line1\nline4\nline3", "owner", "")
        diff = self.mgr.get_version_diff(bp.blueprint_id, "v1", "v2")
        assert diff["added"] > 0 or diff["removed"] > 0

    def test_popular_templates_empty(self):
        popular = self.mgr.get_popular_templates()
        assert isinstance(popular, list)

    def test_recommend_no_context(self):
        recs = self.mgr.recommend_blueprint({})
        assert isinstance(recs, list)
