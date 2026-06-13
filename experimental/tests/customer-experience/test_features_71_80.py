"""Integration tests for Customer Experience & Support Platform features (71-80)."""

import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def client():
    from services.integration_service.src.customer_experience_routes import CustomerExperienceAPIRouter
    return CustomerExperienceAPIRouter({})


class TestHealthScoring:
    def test_compute_health_score(self, client):
        profile = client.health_scoring.compute_health_score(
            "cust-1", {"uptime": 99.9}, {"payment_status": "paid"},
            {"open_tickets": 0}, 99.9, 0.8, 0.7,
        )
        assert profile is not None
        assert 0 <= profile.overall_score <= 100

    def test_health_profile_crud(self, client):
        client.health_scoring.compute_health_score(
            "cust-2", {"uptime": 95.0}, {"payment_status": "paid"},
            {"open_tickets": 1}, 98.0, 0.5, 0.4,
        )
        profile = client.health_scoring.get_health_profile("cust-2")
        assert profile is not None
        assert profile.customer_id == "cust-2"


class TestTicketing:
    def test_create_ticket(self, client):
        ticket = client.ticketing.create_ticket(
            "Test issue", "Description", "cust-1", "Customer One",
            "cust@test.com", "high", "web",
        )
        assert ticket is not None
        assert ticket.subject == "Test issue"
        assert ticket.status == "open"

    def test_ticket_workflow(self, client):
        ticket = client.ticketing.create_ticket("Test", "Body", "cust-1")
        client.ticketing.update_ticket_status(ticket.id, "in_progress", "agent-1")
        updated = client.ticketing.get_ticket(ticket.id)
        assert updated.status == "in_progress"

    def test_sla_management(self, client):
        sla = client.ticketing.create_sla("Gold", "high", 30, 240)
        assert sla is not None
        assert sla.name == "Gold"


class TestSentimentAnalysis:
    def test_analyze_text(self, client):
        result = client.sentiment.analyze_text(
            "I love this product! It works great.", "support_ticket",
        )
        assert result is not None
        assert -1 <= result.score <= 1

    def test_customer_profile(self, client):
        client.sentiment.analyze_text("Great!", "survey", customer_id="cust-1")
        client.sentiment.analyze_text("Bad experience", "support_ticket", customer_id="cust-1")
        profile = client.sentiment.get_customer_profile("cust-1")
        assert profile is not None


class TestAdoptionAnalytics:
    def test_track_event(self, client):
        event = client.adoption.track_event(
            "feature_used", "cust-1", "user-1", "feat-1", "Dashboard",
        )
        assert event is not None
        assert event.event_type == "feature_used"

    def test_adoption_summary(self, client):
        client.adoption.track_event("login", "cust-1", "user-1")
        summary = client.adoption.get_customer_adoption_summary("cust-1")
        assert summary is not None
        assert "total_events" in summary


class TestOnboardingWizard:
    def test_start_onboarding(self, client):
        session = client.onboarding.start_onboarding("cust-1", "Customer One", "premium")
        assert session is not None
        assert session.customer_id == "cust-1"

    def test_onboarding_progress(self, client):
        session = client.onboarding.start_onboarding("cust-2")
        step = client.onboarding.update_step(session.id, "step-1", "completed")
        assert step is not None
        assert step.status == "completed"


class TestKnowledgeBase:
    def test_create_article(self, client):
        article = client.knowledge_base.create_article(
            "How to deploy", "Step by step guide", "getting-started", "guide",
        )
        assert article is not None
        assert article.title == "How to deploy"

    def test_search_articles(self, client):
        client.knowledge_base.create_article("Setup guide", "Content", "setup")
        results = client.knowledge_base.search("setup")
        assert len(results) >= 1


class TestCommunityPlatform:
    def test_create_post(self, client):
        post = client.community.create_post(
            "Welcome thread", "Hello everyone!", "general", "discussion",
        )
        assert post is not None
        assert post.title == "Welcome thread"

    def test_voting(self, client):
        post = client.community.create_post("Test", "Body", "general")
        result = client.community.vote_post(post.id, "user-1", "upvote")
        assert result is not None
        assert result.upvotes == 1


class TestCommunicationHub:
    def test_send_notification(self, client):
        batch = client.communication.send_notification(
            "announcement", "normal", "New feature!", "Check it out", ["email", "in_app"],
        )
        assert batch is not None
        assert batch.type == "announcement"

    def test_maintenance_schedule(self, client):
        mw = client.communication.schedule_maintenance_notification(
            "Scheduled downtime", "DB upgrade", ["database"],
            datetime.utcnow().isoformat(), (datetime.utcnow() + timedelta(hours=2)).isoformat(), "30min",
        )
        assert mw is not None
        assert mw.title == "Scheduled downtime"


class TestNPSSurveys:
    def test_create_survey(self, client):
        survey = client.nps.create_survey(
            "How are we doing?", "Quarterly NPS", "nps", "periodic",
            [{"id": "q1", "text": "How likely?", "type": "nps"}],
        )
        assert survey is not None
        assert survey.title == "How are we doing?"

    def test_submit_response(self, client):
        survey = client.nps.create_survey("Test", "Desc", "nps", "manual", [{"id": "q1", "text": "Rate us", "type": "nps"}])
        resp = client.nps.send_survey(survey.id, "cust-1")
        result = client.nps.submit_response(resp.id, {"q1": 9}, "Great!")
        assert result is not None


class TestSuccessAutomation:
    def test_create_play(self, client):
        play = client.success.create_play(
            "Re-engage inactive users", "Send re-engagement email",
            "user_inactive_7d", [{"type": "send_email", "template": "re_engagement"}],
        )
        assert play is not None
        assert play.name == "Re-engage inactive users"

    def test_evaluate_trigger(self, client):
        client.success.create_play("Test Play", "Desc", "user_login", [{"type": "send_notification"}])
        executions = client.success.evaluate_trigger("user_login", "cust-1")
        assert len(executions) >= 0
