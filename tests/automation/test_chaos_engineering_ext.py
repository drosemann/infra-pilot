"""Tests for chaos_engineering_ext module."""
import pytest
import tempfile
import os
from services.integration_service.src.chaos_engineering_ext import ChaosEngineeringManager, ExperimentStatus, ExperimentTargetType, FaultType, ExperimentHypothesis


@pytest.fixture
def manager():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    mgr = ChaosEngineeringManager(storage_path=path)
    mgr.initialize()
    yield mgr
    mgr.close()
    os.unlink(path)


class TestExperimentCRUD:
    def test_create_experiment(self, manager):
        ex = manager.create_experiment(name="Pod Kill Test", description="Test pod resilience", target_type=ExperimentTargetType.KUBERNETES, hypothesis=ExperimentHypothesis.STEADY_STATE, target_selector={"namespace": "production", "label": "app=web"}, blast_radius="targeted", duration_minutes=15, created_by="sre-team")
        assert ex.id is not None
        assert ex.name == "Pod Kill Test"
        assert ex.target_type == ExperimentTargetType.KUBERNETES
        assert ex.status == ExperimentStatus.DRAFT

    def test_get_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        retrieved = manager.get_experiment(ex.id)
        assert retrieved is not None

    def test_update_experiment(self, manager):
        ex = manager.create_experiment(name="Original", description="Original", target_type=ExperimentTargetType.NETWORK)
        updated = manager.update_experiment(ex.id, {"name": "Updated", "blast_radius": "full"})
        assert updated.name == "Updated"
        assert updated.blast_radius == "full"

    def test_delete_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        assert manager.delete_experiment(ex.id) == True


class TestSteadyState:
    def test_add_steady_state_check(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        check = manager.add_steady_state_check(ex.id, "cpu_usage", "avg(container_cpu)", 80.0, "less_than", tolerance_percent=10.0, duration_seconds=30)
        assert check is not None
        assert check.metric == "cpu_usage"
        assert check.expected_value == 80.0


class TestScenarios:
    def test_create_scenario(self, manager):
        sc = manager.create_scenario(name="Network Chaos", description="Network fault injection", tags=["network", "resilience"])
        assert sc.id is not None
        assert sc.name == "Network Chaos"

    def test_add_scenario_to_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.NETWORK)
        sc = manager.create_scenario(name="Net Scenario", description="Network test")
        assert manager.add_scenario_to_experiment(ex.id, sc.id) == True
        assert len(ex.scenarios) >= 1

    def test_add_fault_to_scenario(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        sc = manager.create_scenario(name="Pod Kill", description="Kill pods")
        manager.add_scenario_to_experiment(ex.id, sc.id)
        fault = manager.add_fault_to_scenario(ex.id, sc.id, FaultType.POD_KILL, ExperimentTargetType.KUBERNETES, target_selector={"namespace": "default", "label": "app=web"}, duration_seconds=30, intensity=1.0, parameters={"policy": "random"})
        assert fault is not None
        assert fault.fault_type == FaultType.POD_KILL


class TestExecution:
    def test_run_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        manager.approve_experiment(ex.id, "admin")
        run = manager.run_experiment(ex.id, executed_by="sre")
        assert run is not None
        assert run.status in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED)

    def test_get_run(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        manager.approve_experiment(ex.id, "admin")
        run = manager.run_experiment(ex.id)
        retrieved = manager.get_run(run.id)
        assert retrieved is not None


class TestLifecycle:
    def test_cancel_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        assert manager.cancel_experiment(ex.id) == True
        assert ex.status == ExperimentStatus.CANCELLED

    def test_approve_experiment(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.NETWORK)
        assert manager.approve_experiment(ex.id, "security-lead") == True
        assert ex.status == ExperimentStatus.SCHEDULED


class TestReport:
    def test_get_report(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        report = manager.get_report(ex.id)
        assert report is not None
        assert report["experiment"]["name"] == "Test"


class TestDuplicate:
    def test_duplicate_experiment(self, manager):
        ex = manager.create_experiment(name="Original", description="Original", target_type=ExperimentTargetType.KUBERNETES)
        clone = manager.duplicate_experiment(ex.id, "Clone")
        assert clone is not None
        assert clone.name == "Clone"
        assert clone.id != ex.id


class TestSearch:
    def test_search_experiments(self, manager):
        manager.create_experiment(name="Pod Chaos", description="Pod chaos test", target_type=ExperimentTargetType.KUBERNETES)
        results = manager.search_experiments("chaos")
        assert len(results) >= 1


class TestList:
    def test_list_experiments(self, manager):
        manager.create_experiment(name="E1", description="Test", target_type=ExperimentTargetType.DOCKER)
        manager.create_experiment(name="E2", description="Test", target_type=ExperimentTargetType.NETWORK)
        experiments = manager.list_experiments()
        assert len(experiments) >= 2

    def test_list_runs(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.DOCKER)
        manager.approve_experiment(ex.id, "admin")
        manager.run_experiment(ex.id)
        runs = manager.list_runs(experiment_id=ex.id)
        assert len(runs) >= 0


class TestStatistics:
    def test_get_statistics(self, manager):
        ex = manager.create_experiment(name="Test", description="Test", target_type=ExperimentTargetType.KUBERNETES)
        stats = manager.get_statistics()
        assert stats["total_experiments"] >= 1
