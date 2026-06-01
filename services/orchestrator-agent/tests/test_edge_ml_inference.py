"""Tests for Edge ML Inference."""

import pytest
from cogs.edge_ml_inference import (
    EdgeMLInference, EdgeModel, ModelFormat, InferenceHardware,
    ModelStatus, InferenceResult, BatchInferenceJob
)


@pytest.fixture
def ml():
    return EdgeMLInference({})


class TestEdgeModel:
    def test_create_model(self):
        model = EdgeModel("m-001", "test-model", ModelFormat.TFLITE, "dev-001", "1.0")
        assert model.model_id == "m-001"
        assert model.status == ModelStatus.PENDING

    def test_to_dict(self, ml):
        model = list(ml.models.values())[0]
        d = model.to_dict()
        assert d["model_id"] is not None
        assert d["name"] is not None


class TestEdgeMLInference:
    def test_initialization(self, ml):
        assert len(ml.models) > 0

    def test_deploy_model(self, ml):
        model = ml.deploy_model("new-model", ModelFormat.ONNX, "dev-001", "1.0",
                                [1, 3, 224, 224], ["cat", "dog"])
        assert model.model_id is not None
        assert model.status == ModelStatus.PENDING

    def test_get_model(self, ml):
        mid = list(ml.models.keys())[0]
        assert ml.get_model(mid) is not None

    def test_get_model_not_found(self, ml):
        assert ml.get_model("nonexistent") is None

    def test_list_models(self, ml):
        models = ml.list_models()
        assert len(models) > 0

    def test_list_models_by_device(self, ml):
        first = list(ml.models.values())[0]
        filtered = ml.list_models(device_id=first.device_id)
        assert all(m.device_id == first.device_id for m in filtered)

    def test_delete_model(self, ml):
        mid = list(ml.models.keys())[0]
        assert ml.delete_model(mid) is True
        assert ml.get_model(mid).status == ModelStatus.ARCHIVED

    def test_run_inference(self, ml):
        mid = list(ml.models.keys())[0]
        result = ml.run_inference(mid, "test_input")
        assert result.success is True
        assert result.predicted_class is not None
        assert result.confidence > 0

    def test_run_inference_not_found(self, ml):
        result = ml.run_inference("nonexistent", "data")
        assert result.success is False

    def test_create_batch_job(self, ml):
        mid = list(ml.models.keys())[0]
        data = [{"id": i} for i in range(5)]
        job = ml.create_batch_job(mid, data)
        assert job.job_id is not None
        assert len(job.data_points) == 5

    def test_get_batch_job(self, ml):
        mid = list(ml.models.keys())[0]
        job = ml.create_batch_job(mid, [{"id": 1}])
        assert ml.get_batch_job(job.job_id) is not None

    def test_get_batch_job_not_found(self, ml):
        assert ml.get_batch_job("nonexistent") is None

    def test_get_models_summary(self, ml):
        summary = ml.get_models_summary()
        assert "total_models" in summary
        assert "active_models" in summary
        assert "total_inferences" in summary

    def test_inference_with_threshold(self, ml):
        model = ml.deploy_model("thresh-model", ModelFormat.TFLITE, "dev-001", "1.0",
                                [1, 10], ["a", "b"], threshold=0.9)
        result = ml.run_inference(model.model_id, "test")
        assert result.success is True

    def test_quantized_model(self, ml):
        model = ml.deploy_model("quant-model", ModelFormat.TFLITE, "dev-001", "1.0",
                                [1, 10], ["x", "y"], quantized=True)
        assert model.quantized is True

    def test_models_with_hardware(self, ml):
        models = ml.list_models()
        hw_types = set(m.hardware_target.value for m in models)
        assert len(hw_types) > 0


class TestInferenceResult:
    def test_result_creation(self):
        result = InferenceResult("m-001", True)
        assert result.success is True
        assert result.model_id == "m-001"

    def test_result_with_error(self):
        result = InferenceResult("m-001", False)
        result = result.with_error("Model not found")
        assert result.success is False
        assert result.error_message == "Model not found"

    def test_result_to_dict(self):
        result = InferenceResult("m-001", True)
        result.predicted_class = "cat"
        result.confidence = 0.95
        result.inference_time_ms = 45.0
        d = result.to_dict()
        assert d["predicted_class"] == "cat"
        assert d["confidence"] == 0.95
