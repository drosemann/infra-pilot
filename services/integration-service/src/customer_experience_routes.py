"""API routes for Customer Experience & Support Platform features (71-80)."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from aiohttp import web

from .customer_experience.health_scoring import HealthScoringService
from .customer_experience.ticketing import TicketingService
from .customer_experience.sentiment_analysis import SentimentAnalysisService
from .customer_experience.adoption_analytics import AdoptionAnalyticsService
from .customer_experience.onboarding_wizard import OnboardingWizardService
from .customer_experience.knowledge_base import KnowledgeBaseService
from .customer_experience.community_platform import CommunityPlatformService
from .customer_experience.communication_hub import CommunicationHubService
from .customer_experience.nps_surveys import NPSSurveyService
from .customer_experience.success_automation import SuccessAutomationService

logger = logging.getLogger(__name__)


class CustomerExperienceAPIRouter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_scoring = HealthScoringService()
        self.ticketing = TicketingService()
        self.sentiment = SentimentAnalysisService()
        self.adoption = AdoptionAnalyticsService()
        self.onboarding = OnboardingWizardService()
        self.knowledge_base = KnowledgeBaseService()
        self.community = CommunityPlatformService()
        self.communication = CommunicationHubService()
        self.nps = NPSSurveyService()
        self.success = SuccessAutomationService()

    def register_routes(self, app: web.Application):
        app.router.add_get("/api/v1/cx/health/profile", self.list_health_profiles)
        app.router.add_get("/api/v1/cx/health/profile/{customer_id}", self.get_health_profile)
        app.router.add_post("/api/v1/cx/health/compute/{customer_id}", self.compute_health)
        app.router.add_get("/api/v1/cx/health/history/{customer_id}", self.get_health_history)
        app.router.add_get("/api/v1/cx/health/stats", self.get_health_stats)
        app.router.add_get("/api/v1/cx/tickets", self.list_tickets)
        app.router.add_post("/api/v1/cx/tickets", self.create_ticket)
        app.router.add_get("/api/v1/cx/tickets/{ticket_id}", self.get_ticket)
        app.router.add_patch("/api/v1/cx/tickets/{ticket_id}/status", self.update_ticket_status)
        app.router.add_post("/api/v1/cx/tickets/{ticket_id}/comments", self.add_comment)
        app.router.add_post("/api/v1/cx/tickets/{ticket_id}/assign", self.assign_ticket)
        app.router.add_get("/api/v1/cx/tickets/stats", self.get_ticket_stats)
        app.router.add_get("/api/v1/cx/slas", self.list_slas)
        app.router.add_post("/api/v1/cx/slas", self.create_sla)
        app.router.add_get("/api/v1/cx/canned-responses", self.list_canned_responses)
        app.router.add_post("/api/v1/cx/canned-responses", self.create_canned_response)
        app.router.add_post("/api/v1/cx/sentiment/analyze", self.analyze_sentiment)
        app.router.add_get("/api/v1/cx/sentiment/profile/{customer_id}", self.get_sentiment_profile)
        app.router.add_get("/api/v1/cx/sentiment/interactions", self.list_sentiment_interactions)
        app.router.add_get("/api/v1/cx/sentiment/trends", self.get_sentiment_trends)
        app.router.add_get("/api/v1/cx/sentiment/alerts", self.get_sentiment_alerts)
        app.router.add_get("/api/v1/cx/adoption/summary/{customer_id}", self.get_adoption_summary)
        app.router.add_get("/api/v1/cx/adoption/features/{customer_id}", self.get_feature_adoption)
        app.router.add_post("/api/v1/cx/adoption/track", self.track_event)
        app.router.add_get("/api/v1/cx/adoption/recommendations/{customer_id}", self.get_adoption_recommendations)
        app.router.add_get("/api/v1/cx/adoption/stats", self.get_adoption_stats)
        app.router.add_post("/api/v1/cx/onboarding/start", self.start_onboarding)
        app.router.add_get("/api/v1/cx/onboarding/session/{customer_id}", self.get_onboarding_session)
        app.router.add_post("/api/v1/cx/onboarding/step", self.update_onboarding_step)
        app.router.add_get("/api/v1/cx/onboarding/stats", self.get_onboarding_stats)
        app.router.add_get("/api/v1/cx/kb/articles", self.list_articles)
        app.router.add_post("/api/v1/cx/kb/articles", self.create_article)
        app.router.add_get("/api/v1/cx/kb/articles/{article_id}", self.get_article)
        app.router.add_put("/api/v1/cx/kb/articles/{article_id}", self.update_article)
        app.router.add_get("/api/v1/cx/kb/search", self.search_articles)
        app.router.add_get("/api/v1/cx/kb/categories", self.list_categories)
        app.router.add_post("/api/v1/cx/kb/feedback", self.add_article_feedback)
        app.router.add_get("/api/v1/cx/community/posts", self.list_posts)
        app.router.add_post("/api/v1/cx/community/posts", self.create_post)
        app.router.add_get("/api/v1/cx/community/posts/{post_id}", self.get_post)
        app.router.add_post("/api/v1/cx/community/posts/{post_id}/vote", self.vote_post)
        app.router.add_post("/api/v1/cx/community/posts/{post_id}/comments", self.add_community_comment)
        app.router.add_get("/api/v1/cx/community/posts/{post_id}/comments", self.get_post_comments)
        app.router.add_get("/api/v1/cx/community/feature-requests", self.get_feature_requests)
        app.router.add_get("/api/v1/cx/community/categories", self.get_community_categories)
        app.router.add_get("/api/v1/cx/community/leaderboard", self.get_leaderboard)
        app.router.add_get("/api/v1/cx/community/stats", self.get_community_stats)
        app.router.add_post("/api/v1/cx/communication/send", self.send_notification)
        app.router.add_get("/api/v1/cx/communication/batches", self.list_batches)
        app.router.add_get("/api/v1/cx/communication/batch/{batch_id}", self.get_batch_stats)
        app.router.add_post("/api/v1/cx/communication/maintenance", self.schedule_maintenance)
        app.router.add_get("/api/v1/cx/communication/maintenance", self.list_maintenance)
        app.router.add_post("/api/v1/cx/communication/maintenance/{maintenance_id}/complete", self.complete_maintenance)
        app.router.add_get("/api/v1/cx/communication/templates", self.list_templates)
        app.router.add_post("/api/v1/cx/communication/templates", self.create_template)
        app.router.add_post("/api/v1/cx/nps/surveys", self.create_survey)
        app.router.add_get("/api/v1/cx/nps/surveys", self.get_surveys)
        app.router.add_get("/api/v1/cx/nps/surveys/{survey_id}", self.get_survey)
        app.router.add_post("/api/v1/cx/nps/send/{survey_id}", self.send_survey)
        app.router.add_post("/api/v1/cx/nps/respond/{response_id}", self.submit_response)
        app.router.add_get("/api/v1/cx/nps/score", self.get_nps_score)
        app.router.add_get("/api/v1/cx/nps/trend", self.get_nps_trend)
        app.router.add_get("/api/v1/cx/nps/detractors", self.get_detractor_feedback)
        app.router.add_get("/api/v1/cx/nps/stats", self.get_nps_stats)
        app.router.add_get("/api/v1/cx/success/plays", self.list_plays)
        app.router.add_post("/api/v1/cx/success/plays", self.create_play)
        app.router.add_patch("/api/v1/cx/success/plays/{play_id}/status", self.update_play_status)
        app.router.add_post("/api/v1/cx/success/trigger", self.evaluate_trigger)
        app.router.add_get("/api/v1/cx/success/executions", self.get_executions)
        app.router.add_get("/api/v1/cx/success/stats", self.get_success_stats)

    async def list_health_profiles(self, request: web.Request) -> web.Response:
        risk_level = request.query.get("risk_level")
        min_score = request.query.get("min_score")
        results = self.health_scoring.list_health_profiles(risk_level, float(min_score) if min_score else None)
        return web.json_response({"profiles": results, "total": len(results)})

    async def get_health_profile(self, request: web.Request) -> web.Response:
        profile = self.health_scoring.get_health_profile(request.match_info["customer_id"])
        if not profile:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(profile.to_dict())

    async def compute_health(self, request: web.Request) -> web.Response:
        data = await request.json()
        profile = self.health_scoring.compute_health_score(
            request.match_info["customer_id"],
            data.get("usage", {}), data.get("billing", {}), data.get("support", {}),
            data.get("uptime"), data.get("sentiment"), data.get("adoption"),
        )
        return web.json_response(profile.to_dict())

    async def get_health_history(self, request: web.Request) -> web.Response:
        days = int(request.query.get("days", 30))
        history = self.health_scoring.get_health_history(request.match_info["customer_id"], days)
        return web.json_response({"history": history})

    async def get_health_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.health_scoring.get_segment_summary())

    async def list_tickets(self, request: web.Request) -> web.Response:
        tickets, total = self.ticketing.list_tickets(
            status=request.query.get("status"), priority=request.query.get("priority"),
            customer_id=request.query.get("customer_id"), assigned_to=request.query.get("assigned_to"),
            team=request.query.get("team"), search=request.query.get("search"),
            limit=int(request.query.get("limit", 50)), offset=int(request.query.get("offset", 0)),
        )
        return web.json_response({"tickets": tickets, "total": total})

    async def create_ticket(self, request: web.Request) -> web.Response:
        data = await request.json()
        ticket = self.ticketing.create_ticket(
            data["subject"], data["description"], data["customer_id"],
            data.get("customer_name", ""), data.get("customer_email", ""),
            data.get("priority", "medium"), data.get("channel", "web"),
            data.get("category"), data.get("tags"), data.get("custom_fields"),
        )
        return web.json_response(ticket.to_dict(), status=201)

    async def get_ticket(self, request: web.Request) -> web.Response:
        ticket = self.ticketing.get_ticket(request.match_info["ticket_id"])
        if not ticket:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(ticket.to_dict())

    async def update_ticket_status(self, request: web.Request) -> web.Response:
        data = await request.json()
        ticket = self.ticketing.update_ticket_status(request.match_info["ticket_id"], data["status"], data.get("agent_id"))
        if not ticket:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(ticket.to_dict())

    async def add_comment(self, request: web.Request) -> web.Response:
        data = await request.json()
        comment = self.ticketing.add_comment(
            request.match_info["ticket_id"], data["author_id"], data.get("author_name", ""),
            data["body"], data.get("is_internal", False),
        )
        if not comment:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(comment.to_dict(), status=201)

    async def assign_ticket(self, request: web.Request) -> web.Response:
        data = await request.json()
        ticket = self.ticketing.assign_ticket(request.match_info["ticket_id"], data["agent_id"], data.get("team"))
        if not ticket:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(ticket.to_dict())

    async def get_ticket_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.ticketing.get_ticket_stats())

    async def list_slas(self, request: web.Request) -> web.Response:
        return web.json_response({"slas": self.ticketing.list_slas()})

    async def create_sla(self, request: web.Request) -> web.Response:
        data = await request.json()
        sla = self.ticketing.create_sla(data["name"], data["priority"], data["response_time"], data["resolution_time"], data.get("business_hours", True))
        return web.json_response(sla.to_dict(), status=201)

    async def list_canned_responses(self, request: web.Request) -> web.Response:
        return web.json_response({"responses": self.ticketing.list_canned_responses(request.query.get("category"))})

    async def create_canned_response(self, request: web.Request) -> web.Response:
        data = await request.json()
        cr = self.ticketing.create_canned_response(data["title"], data["body"], data["category"], data.get("tags"), data.get("created_by", ""))
        return web.json_response(cr.to_dict(), status=201)

    async def analyze_sentiment(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = self.sentiment.analyze_text(
            data["text"], data.get("source_type", "support_ticket"),
            data.get("source_id", ""), data.get("customer_id", ""),
            data.get("customer_name", ""), data.get("metadata"),
        )
        return web.json_response(result.to_dict())

    async def get_sentiment_profile(self, request: web.Request) -> web.Response:
        profile = self.sentiment.get_customer_profile(request.match_info["customer_id"])
        if not profile:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(profile.to_dict())

    async def list_sentiment_interactions(self, request: web.Request) -> web.Response:
        results = self.sentiment.list_interactions(
            customer_id=request.query.get("customer_id"),
            source_type=request.query.get("source_type"),
            min_score=float(request.query.get("min_score")) if request.query.get("min_score") else None,
            max_score=float(request.query.get("max_score")) if request.query.get("max_score") else None,
            escalated_only=request.query.get("escalated_only", "").lower() == "true",
            limit=int(request.query.get("limit", 50)),
        )
        return web.json_response({"interactions": results, "total": len(results)})

    async def get_sentiment_trends(self, request: web.Request) -> web.Response:
        trends = self.sentiment.get_sentiment_trends(
            request.query.get("period", "daily"), int(request.query.get("days", 30)),
        )
        return web.json_response({"trends": trends})

    async def get_sentiment_alerts(self, request: web.Request) -> web.Response:
        return web.json_response({"alerts": self.sentiment.get_alerts()})

    async def get_adoption_summary(self, request: web.Request) -> web.Response:
        summary = self.adoption.get_customer_adoption_summary(request.match_info["customer_id"])
        return web.json_response(summary)

    async def get_feature_adoption(self, request: web.Request) -> web.Response:
        features = self.adoption.get_feature_adoption(request.match_info["customer_id"], int(request.query.get("days", 30)))
        return web.json_response({"features": [f.to_dict() for f in features]})

    async def track_event(self, request: web.Request) -> web.Response:
        data = await request.json()
        event = self.adoption.track_event(
            data["event_type"], data["customer_id"], data["user_id"],
            data.get("feature_id"), data.get("feature_name"),
            data.get("metadata"), data.get("session_id"),
        )
        return web.json_response(event.to_dict(), status=201)

    async def get_adoption_recommendations(self, request: web.Request) -> web.Response:
        recs = self.adoption.get_adoption_recommendations(request.match_info["customer_id"])
        return web.json_response({"recommendations": recs})

    async def get_adoption_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.adoption.get_global_stats())

    async def start_onboarding(self, request: web.Request) -> web.Response:
        data = await request.json()
        session = self.onboarding.start_onboarding(data["customer_id"], data.get("customer_name", ""), data.get("product_tier", "standard"))
        return web.json_response(session.to_dict(), status=201)

    async def get_onboarding_session(self, request: web.Request) -> web.Response:
        session = self.onboarding.get_session(request.match_info["customer_id"])
        if not session:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(session.to_dict())

    async def update_onboarding_step(self, request: web.Request) -> web.Response:
        data = await request.json()
        step = self.onboarding.update_step(data["session_id"], data["step_id"], data["status"], data.get("metadata"))
        if not step:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(step.to_dict())

    async def get_onboarding_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.onboarding.get_onboarding_stats())

    async def list_articles(self, request: web.Request) -> web.Response:
        articles = self.knowledge_base.list_articles(
            category=request.query.get("category"), article_type=request.query.get("type"),
            status=request.query.get("status"), limit=int(request.query.get("limit", 50)),
        )
        return web.json_response({"articles": articles, "total": len(articles)})

    async def create_article(self, request: web.Request) -> web.Response:
        data = await request.json()
        article = self.knowledge_base.create_article(
            data["title"], data["content"], data["category"],
            data.get("article_type", "guide"), data.get("tags"),
            data.get("author", ""), data.get("language", "en"),
        )
        return web.json_response(article.to_dict(), status=201)

    async def get_article(self, request: web.Request) -> web.Response:
        article = self.knowledge_base.get_article(request.match_info["article_id"])
        if not article:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(article.to_dict())

    async def update_article(self, request: web.Request) -> web.Response:
        data = await request.json()
        article = self.knowledge_base.update_article(request.match_info["article_id"], data)
        if not article:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(article.to_dict())

    async def search_articles(self, request: web.Request) -> web.Response:
        query = request.query.get("q", "")
        if not query:
            return web.json_response({"results": []})
        results = self.knowledge_base.search(query, request.query.get("category"), int(request.query.get("limit", 20)))
        return web.json_response({"results": [r.to_dict() for r in results]})

    async def list_categories(self, request: web.Request) -> web.Response:
        return web.json_response({"categories": self.knowledge_base.list_categories()})

    async def add_article_feedback(self, request: web.Request) -> web.Response:
        data = await request.json()
        fb = self.knowledge_base.add_feedback(data["article_id"], data["helpful"], data.get("comment"), data.get("user_id"))
        if not fb:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(fb.to_dict(), status=201)

    async def list_posts(self, request: web.Request) -> web.Response:
        posts, total = self.community.list_posts(
            request.query.get("category_id"), request.query.get("post_type"),
            request.query.get("sort", "hot"),
            int(request.query.get("limit", 50)), int(request.query.get("offset", 0)),
        )
        return web.json_response({"posts": posts, "total": total})

    async def create_post(self, request: web.Request) -> web.Response:
        data = await request.json()
        post = self.community.create_post(
            data["title"], data["content"], data["category_id"],
            data.get("post_type", "discussion"), data.get("author_id", ""),
            data.get("author_name", ""), data.get("tags"),
        )
        return web.json_response(post.to_dict(), status=201)

    async def get_post(self, request: web.Request) -> web.Response:
        post = self.community.get_post(request.match_info["post_id"])
        if not post:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(post.to_dict())

    async def vote_post(self, request: web.Request) -> web.Response:
        data = await request.json()
        post = self.community.vote_post(request.match_info["post_id"], data["user_id"], data["vote_type"])
        if not post:
            return web.json_response({"error": "not found or self-vote"}, status=400)
        return web.json_response(post.to_dict())

    async def add_community_comment(self, request: web.Request) -> web.Response:
        data = await request.json()
        comment = self.community.add_comment(
            request.match_info["post_id"], data["author_id"], data.get("author_name", ""),
            data["body"], data.get("parent_comment_id"),
        )
        if not comment:
            return web.json_response({"error": "not found or locked"}, status=400)
        return web.json_response(comment.to_dict(), status=201)

    async def get_post_comments(self, request: web.Request) -> web.Response:
        comments = self.community.get_comments(request.match_info["post_id"])
        return web.json_response({"comments": comments})

    async def get_feature_requests(self, request: web.Request) -> web.Response:
        requests = self.community.get_feature_requests(request.query.get("sort", "votes"), int(request.query.get("limit", 50)))
        return web.json_response({"feature_requests": requests})

    async def get_community_categories(self, request: web.Request) -> web.Response:
        return web.json_response({"categories": self.community.get_categories()})

    async def get_leaderboard(self, request: web.Request) -> web.Response:
        return web.json_response({"leaderboard": self.community.get_leaderboard(int(request.query.get("limit", 20)))})

    async def get_community_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.community.get_stats())

    async def send_notification(self, request: web.Request) -> web.Response:
        data = await request.json()
        batch = self.communication.send_notification(
            data["type"], data.get("priority", "normal"), data["subject"],
            data["body"], data["channels"], data.get("target_segment", "all"),
            data.get("target_customer_ids"), data.get("template_id"),
            data.get("scheduled_at"), data.get("created_by", ""),
        )
        return web.json_response(batch.to_dict(), status=201)

    async def list_batches(self, request: web.Request) -> web.Response:
        return web.json_response({"batches": self.communication.list_batches(int(request.query.get("limit", 50)))})

    async def get_batch_stats(self, request: web.Request) -> web.Response:
        stats = self.communication.get_batch_stats(request.match_info["batch_id"])
        if not stats:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(stats)

    async def schedule_maintenance(self, request: web.Request) -> web.Response:
        data = await request.json()
        mw = self.communication.schedule_maintenance_notification(
            data["title"], data["description"], data["affected_services"],
            data["start_time"], data["end_time"], data["expected_downtime"],
            data.get("created_by", ""),
        )
        return web.json_response(mw.to_dict(), status=201)

    async def list_maintenance(self, request: web.Request) -> web.Response:
        return web.json_response({"maintenance_windows": self.communication.get_maintenance_windows(request.query.get("status"))})

    async def complete_maintenance(self, request: web.Request) -> web.Response:
        data = await request.json() or {}
        mw = self.communication.complete_maintenance(request.match_info["maintenance_id"], data.get("actual_downtime"), data.get("post_mortem"))
        if not mw:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(mw.to_dict())

    async def list_templates(self, request: web.Request) -> web.Response:
        return web.json_response({"templates": self.communication.list_templates(request.query.get("channel"))})

    async def create_template(self, request: web.Request) -> web.Response:
        data = await request.json()
        tpl = self.communication.create_template(data["name"], data["subject"], data["body"], data["channel"], data.get("category", "general"), data.get("variables"))
        return web.json_response(tpl.to_dict(), status=201)

    async def create_survey(self, request: web.Request) -> web.Response:
        data = await request.json()
        survey = self.nps.create_survey(data["title"], data["description"], data["survey_type"], data["trigger"], data["questions"], data.get("target_segment", "all"), data.get("frequency_days"))
        return web.json_response(survey.to_dict(), status=201)

    async def get_surveys(self, request: web.Request) -> web.Response:
        return web.json_response({"surveys": self.nps.get_surveys(request.query.get("trigger"), request.query.get("survey_type"))})

    async def get_survey(self, request: web.Request) -> web.Response:
        survey = self.nps.get_survey(request.match_info["survey_id"])
        if not survey:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(survey)

    async def send_survey(self, request: web.Request) -> web.Response:
        data = await request.json()
        resp = self.nps.send_survey(request.match_info["survey_id"], data["customer_id"], data.get("customer_name", ""))
        if not resp:
            return web.json_response({"error": "cannot send survey"}, status=400)
        return web.json_response(resp.to_dict(), status=201)

    async def submit_response(self, request: web.Request) -> web.Response:
        data = await request.json()
        resp = self.nps.submit_response(request.match_info["response_id"], data.get("answers", {}), data.get("comments"))
        if not resp:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(resp.to_dict())

    async def get_nps_score(self, request: web.Request) -> web.Response:
        return web.json_response(self.nps.get_nps_score())

    async def get_nps_trend(self, request: web.Request) -> web.Response:
        return web.json_response(self.nps.get_nps_trend(int(request.query.get("days", 90))))

    async def get_detractor_feedback(self, request: web.Request) -> web.Response:
        return web.json_response({"detractors": self.nps.get_detractor_feedback(int(request.query.get("limit", 50)))})

    async def get_nps_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.nps.get_stats())

    async def list_plays(self, request: web.Request) -> web.Response:
        return web.json_response({"plays": self.success.list_plays(request.query.get("trigger_event"), request.query.get("status"))})

    async def create_play(self, request: web.Request) -> web.Response:
        data = await request.json()
        play = self.success.create_play(data["name"], data["description"], data["trigger_event"], data["actions"], data.get("tags"), data.get("trigger_conditions"), data.get("cooldown_days", 30))
        return web.json_response(play.to_dict(), status=201)

    async def update_play_status(self, request: web.Request) -> web.Response:
        data = await request.json()
        play = self.success.update_play_status(request.match_info["play_id"], data["status"])
        if not play:
            return web.json_response({"error": "not found"}, status=404)
        return web.json_response(play.to_dict())

    async def evaluate_trigger(self, request: web.Request) -> web.Response:
        data = await request.json()
        executions = self.success.evaluate_trigger(data["event"], data["customer_id"], data.get("event_data"))
        return web.json_response({"executions": [e.to_dict() for e in executions]})

    async def get_executions(self, request: web.Request) -> web.Response:
        return web.json_response({"executions": self.success.get_executions(request.query.get("play_id"), request.query.get("customer_id"), int(request.query.get("limit", 50)))})

    async def get_success_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.success.get_stats())
