"""Tests for Developer Pulse manager."""
import pytest
from services.integration_service.src.platform_engineering.developer_pulse import DeveloperPulse


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
        from services.integration_service.src.platform_engineering.developer_pulse import PulseSurvey
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
