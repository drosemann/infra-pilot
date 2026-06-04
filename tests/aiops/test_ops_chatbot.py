"""Tests for Feature 60: Self-Service Operations Chatbot."""

import pytest
from services.integration_service.src.aiops.ops_chatbot import OpsChatbot


@pytest.fixture
def chatbot():
    return OpsChatbot({})


class TestOpsChatbot:
    def test_restart_service(self, chatbot):
        result = chatbot.process_message("user-1", "restart nginx")
        assert result["type"] == "success"
        assert "restarting" in result["text"].lower()

    def test_check_logs(self, chatbot):
        result = chatbot.process_message("user-1", "logs api-server")
        assert result["type"] == "success"
        assert "logs" in result["text"].lower()

    def test_run_backup(self, chatbot):
        result = chatbot.process_message("user-1", "backup postgres")
        assert result["type"] == "success"
        assert "backup" in result["text"].lower()

    def test_check_status(self, chatbot):
        result = chatbot.process_message("user-1", "status web-server")
        assert result["type"] == "success"

    def test_list_services(self, chatbot):
        result = chatbot.process_message("user-1", "list services")
        assert result["type"] == "success"
        assert "services" in result["text"].lower()

    def test_scale_service(self, chatbot):
        result = chatbot.process_message("user-1", "scale api-service 5")
        assert result["type"] == "success"

    def test_deploy_version(self, chatbot):
        result = chatbot.process_message("user-1", "deploy v3.2 staging")
        assert result["type"] == "success"

    def test_clear_cache(self, chatbot):
        result = chatbot.process_message("user-1", "clear cache cdn")
        assert result["type"] == "success"

    def test_run_diagnostic(self, chatbot):
        result = chatbot.process_message("user-1", "diagnostic database")
        assert result["type"] == "success"

    def test_show_metrics(self, chatbot):
        result = chatbot.process_message("user-1", "metrics gateway")
        assert result["type"] == "success"

    def test_unknown_command(self, chatbot):
        result = chatbot.process_message("user-1", "do something weird and crazy")
        assert result["type"] == "error"

    def test_conversation_tracking(self, chatbot):
        r1 = chatbot.process_message("user-2", "status nginx")
        conv_id = r1["conversation_id"]
        r2 = chatbot.process_message("user-2", "restart nginx", conversation_id=conv_id)
        conv = chatbot.get_conversation(conv_id)
        assert len(conv["messages"]) >= 4

    def test_task_history(self, chatbot):
        chatbot.process_message("user-3", "restart web")
        chatbot.process_message("user-3", "logs web")
        tasks = chatbot.list_tasks(user_id="user-3")
        assert len(tasks) >= 2

    def test_analytics(self, chatbot):
        chatbot.process_message("user-analytics", "status app")
        chatbot.process_message("user-analytics", "restart app")
        chatbot.process_message("user-analytics", "logs app")
        analytics = chatbot.get_analytics()
        assert analytics["total_messages"] >= 3
