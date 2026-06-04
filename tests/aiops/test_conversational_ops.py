"""Tests for Feature 57: Conversational Ops Assistant."""

import pytest
from services.integration_service.src.aiops.conversational_ops import ConversationalOpsAssistant


@pytest.fixture
def assistant():
    return ConversationalOpsAssistant({})


class TestConversationalOps:
    def test_status_check(self, assistant):
        result = assistant.process_message("session-1", "user-1", "What's the status of web-server?")
        assert result["intent"] == "status_check"
        assert result["success"] is True

    def test_restart_intent(self, assistant):
        result = assistant.process_message("session-2", "user-1", "restart nginx")
        assert result["intent"] == "restart"
        assert result["success"] is True

    def test_deploy_intent(self, assistant):
        result = assistant.process_message("session-3", "user-1", "deploy version 3.2 to staging")
        assert result["intent"] == "deploy"
        assert result["success"] is True

    def test_logs_intent(self, assistant):
        result = assistant.process_message("session-4", "user-1", "show logs for database")
        assert result["intent"] == "logs"

    def test_help_intent(self, assistant):
        result = assistant.process_message("session-5", "user-1", "help")
        assert result["intent"] == "help"

    def test_list_resources(self, assistant):
        result = assistant.process_message("session-6", "user-1", "list all servers")
        assert result["intent"] == "list_resources"

    def test_unknown_intent(self, assistant):
        result = assistant.process_message("session-7", "user-1", "xyzzy the magic word")
        assert result["intent"] == "unknown"
        assert result["success"] is False

    def test_session_management(self, assistant):
        result1 = assistant.process_message("sess-mgmt", "user-2", "status web")
        result2 = assistant.process_message("sess-mgmt", "user-2", "restart web")
        session = assistant.get_session("sess-mgmt")
        assert len(session["messages"]) >= 4

    def test_statistics(self, assistant):
        assistant.process_message("stats-sess", "user-3", "status app")
        assistant.process_message("stats-sess", "user-3", "restart app")
        stats = assistant.get_statistics()
        assert stats["total_messages"] >= 2

    def test_scale_intent(self, assistant):
        result = assistant.process_message("sess-scale", "user-1", "scale api-service to 5 replicas")
        assert result["intent"] == "scale"

    def test_metrics_intent(self, assistant):
        result = assistant.process_message("sess-metrics", "user-1", "show CPU for web-server")
        assert result["intent"] == "metrics"

    def test_backup_intent(self, assistant):
        result = assistant.process_message("sess-backup", "user-1", "create a backup of postgres")
        assert result["intent"] == "backup"
