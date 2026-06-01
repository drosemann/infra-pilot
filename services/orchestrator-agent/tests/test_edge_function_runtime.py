"""Tests for Edge Function Runtime."""

import pytest
from datetime import datetime
from cogs.edge_function_runtime import (
    EdgeFunctionRuntime, EdgeFunction, FunctionRuntime, FunctionStatus,
    OfflineQueueItem
)


@pytest.fixture
def runtime():
    return EdgeFunctionRuntime({})


class TestEdgeFunction:
    def test_create_function(self):
        func = EdgeFunction("f-001", "test-func", FunctionRuntime.WASM,
                           "dev-001", "wasm://test.wasm", "process")
        assert func.func_id == "f-001"
        assert func.name == "test-func"
        assert func.status == FunctionStatus.PENDING

    def test_to_dict(self, runtime):
        func = runtime.list_functions()[0]
        d = func.to_dict()
        assert d["func_id"] is not None
        assert d["name"] is not None
        assert "status" in d
        assert "runtime" in d


class TestEdgeFunctionRuntime:
    def test_initialization(self, runtime):
        assert len(runtime.functions) > 0

    def test_deploy_function(self, runtime):
        func = runtime.deploy_function("new-func", FunctionRuntime.WASM,
                                       "dev-001", "wasm://new.wasm", "handler")
        assert func.func_id is not None
        assert func.name == "new-func"
        assert func.status == FunctionStatus.DEPLOYING

    def test_get_function(self, runtime):
        func_id = list(runtime.functions.keys())[0]
        assert runtime.get_function(func_id) is not None

    def test_get_function_not_found(self, runtime):
        assert runtime.get_function("nonexistent") is None

    def test_list_functions(self, runtime):
        funcs = runtime.list_functions()
        assert len(funcs) > 0

    def test_list_functions_by_device(self, runtime):
        first_func = list(runtime.functions.values())[0]
        filtered = runtime.list_functions(device_id=first_func.device_id)
        assert all(f.device_id == first_func.device_id for f in filtered)

    def test_list_functions_by_status(self, runtime):
        filtered = runtime.list_functions(status="running")
        assert all(f.status.value == "running" for f in filtered)

    def test_update_function(self, runtime):
        func_id = list(runtime.functions.keys())[0]
        updated = runtime.update_function(func_id, {"version": "2.0.0"})
        assert updated is not None
        assert updated.version == "2.0.0"

    def test_update_function_not_found(self, runtime):
        assert runtime.update_function("nonexistent", {}) is None

    def test_delete_function(self, runtime):
        func_id = list(runtime.functions.keys())[0]
        assert runtime.delete_function(func_id) is True
        assert runtime.get_function(func_id) is None

    def test_delete_function_not_found(self, runtime):
        assert runtime.delete_function("nonexistent") is False

    def test_add_trigger(self, runtime):
        func_id = list(runtime.functions.keys())[0]
        assert runtime.add_trigger(func_id, "timer", {"interval_seconds": 60}) is True

    def test_add_trigger_not_found(self, runtime):
        assert runtime.add_trigger("nonexistent", "timer", {}) is False

    def test_invoke_function(self, runtime):
        func_id = list(runtime.functions.keys())[0]
        result = runtime.invoke_function(func_id, {"test": "data"})
        assert result["success"] is True or result.get("queued") is True

    def test_invoke_function_not_found(self, runtime):
        result = runtime.invoke_function("nonexistent", {})
        assert result["success"] is False

    def test_get_offline_queue(self, runtime):
        queue = runtime.get_offline_queue()
        assert isinstance(queue, list)

    def test_create_function_chain(self, runtime):
        func_ids = list(runtime.functions.keys())[:3]
        if len(func_ids) >= 2:
            results = runtime.create_function_chain(func_ids[:2])
            assert len(results) == 2

    def test_get_functions_summary(self, runtime):
        summary = runtime.get_functions_summary()
        assert "total" in summary
        assert "running" in summary
        assert "total_invocations" in summary
        assert "queue_depth" in summary

    def test_deploy_with_custom_limits(self, runtime):
        func = runtime.deploy_function("limited", FunctionRuntime.CONTAINER,
                                       "dev-001", "docker://img", "main",
                                       resource_limits={"memory_mb": 256})
        assert func.resource_limits["memory_mb"] == 256

    def test_deploy_with_environment(self, runtime):
        func = runtime.deploy_function("env-func", FunctionRuntime.NATIVE,
                                       "dev-001", "python://script", "run",
                                       environment={"DEBUG": "true"})
        assert func.environment["DEBUG"] == "true"

    def test_deploy_with_triggers(self, runtime):
        func = runtime.deploy_function("trig-func", FunctionRuntime.WASM,
                                       "dev-001", "wasm://f", "h")
        runtime.add_trigger(func.func_id, "timer", {"interval_seconds": 30})
        runtime.add_trigger(func.func_id, "http", {"path": "/webhook"})
        assert len(func.triggers) == 2

    def test_process_offline_queue(self, runtime):
        device_ids = set(f.device_id for f in runtime.functions.values())
        if device_ids:
            runtime.process_offline_queue(list(device_ids)[0])


class TestOfflineQueueItem:
    def test_create_item(self):
        item = OfflineQueueItem("q-001", "f-001", {"data": 1}, "manual")
        assert item.queue_id == "q-001"
        assert item.status == "queued"
        assert item.retry_count == 0
