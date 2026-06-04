"""Tests for Scorecards/DORA Metrics manager."""
import pytest
from services.integration_service.src.platform_engineering.scorecards import ScorecardsManager


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
        from services.integration_service.src.platform_engineering.scorecards import Scorecard
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
