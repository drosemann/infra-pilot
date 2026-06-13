"""Edge ML Inference Cog - Deploy TFLite/ONNX models to edge nodes."""

import asyncio
import base64
import json
import logging
import struct
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ModelFormat(Enum):
    TFLITE = "tflite"
    ONNX = "onnx"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"


class InferenceHardware(Enum):
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"
    TPU = "tpu"


class ModelStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    ARCHIVED = "archived"


class EdgeModel:
    """Represents an ML model deployed to an edge device."""

    def __init__(self, model_id: str, name: str, model_format: ModelFormat,
                 device_id: str, version: str):
        self.model_id = model_id
        self.name = name
        self.model_format = model_format
        self.device_id = device_id
        self.version = version
        self.status = ModelStatus.PENDING
        self.hardware_target = InferenceHardware.CPU
        self.input_shape: list[int] = [1, 224, 224, 3]
        self.output_classes: list[str] = []
        self.threshold: float = 0.5
        self.preprocess_steps: list[str] = []
        self.postprocess_steps: list[str] = []
        self.model_size_bytes: int = 0
        self.quantized: bool = False
        self.accuracy_score: float = 0.0
        self.latency_ms: float = 0.0
        self.inference_count: int = 0
        self.last_inference: Optional[datetime] = None
        self.deployed_at: Optional[datetime] = None
        self.trigger: Optional[str] = None
        self.labels: dict[int, str] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "model_format": self.model_format.value,
            "device_id": self.device_id,
            "version": self.version,
            "status": self.status.value,
            "hardware_target": self.hardware_target.value,
            "input_shape": self.input_shape,
            "output_classes": self.output_classes,
            "threshold": self.threshold,
            "preprocess_steps": self.preprocess_steps,
            "postprocess_steps": self.postprocess_steps,
            "model_size_bytes": self.model_size_bytes,
            "quantized": self.quantized,
            "accuracy_score": self.accuracy_score,
            "latency_ms": self.latency_ms,
            "inference_count": self.inference_count,
            "last_inference": self.last_inference.isoformat() if self.last_inference else None,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "trigger": self.trigger,
            "labels": self.labels,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class InferenceResult:
    """Result of an ML inference operation."""

    def __init__(self, model_id: str, success: bool):
        self.model_id = model_id
        self.success = success
        self.predicted_class: Optional[str] = None
        self.confidence: float = 0.0
        self.all_scores: dict[str, float] = {}
        self.inference_time_ms: float = 0.0
        self.error_message: Optional[str] = None
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "success": self.success,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "all_scores": self.all_scores,
            "inference_time_ms": self.inference_time_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


class BatchInferenceJob:
    """Batch inference job for processing historical data."""

    def __init__(self, job_id: str, model_id: str, data_points: list[dict]):
        self.job_id = job_id
        self.model_id = model_id
        self.data_points = data_points
        self.results: list[InferenceResult] = []
        self.status = "pending"
        self.progress = 0.0
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "model_id": self.model_id,
            "data_points_count": len(self.data_points),
            "results_count": len(self.results),
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class EdgeMLInference:
    """Manager for edge ML model deployment and inference."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.models: dict[str, EdgeModel] = {}
        self.batch_jobs: dict[str, BatchInferenceJob] = {}
        self._seed_models()

    def _seed_models(self):
        demo_models = [
            ("model-001", "mobilenet-v2", ModelFormat.TFLITE, "dev-006", "2.0.0",
             InferenceHardware.NPU, [1, 224, 224, 3],
             ["background", "aeroplane", "bicycle", "bird", "board", "bottle", "bus",
              "car", "cat", "chair", "cow", "dining_table", "dog", "horse", "motorbike",
              "person", "potted_plant", "sheep", "sofa", "train", "tv_monitor"]),
            ("model-002", "anomaly-detector", ModelFormat.ONNX, "dev-001", "1.3.0",
             InferenceHardware.CPU, [1, 128],
             ["normal", "anomaly"]),
            ("model-003", "vibration-cnn", ModelFormat.TFLITE, "dev-002", "1.1.0",
             InferenceHardware.CPU, [1, 64, 3],
             ["normal", "imbalance", "misalignment", "bearing_fault"]),
            ("model-004", "defect-detector", ModelFormat.ONNX, "dev-007", "1.0.0",
             InferenceHardware.GPU, [1, 512, 512, 3],
             ["ok", "scratch", "dent", "crack", "discoloration"]),
            ("model-005", "keyword-spotter", ModelFormat.TFLITE, "dev-003", "2.1.0",
             InferenceHardware.NPU, [1, 49, 10],
             ["silence", "unknown", "yes", "no", "up", "down", "left", "right",
              "on", "off", "stop", "go"]),
        ]
        for mid, name, fmt, dev_id, ver, hw, inp_shape, classes in demo_models:
            model = EdgeModel(mid, name, fmt, dev_id, ver)
            model.status = ModelStatus.ACTIVE
            model.hardware_target = hw
            model.input_shape = inp_shape
            model.output_classes = classes
            model.model_size_bytes = hash(mid) % (50 * 1024 * 1024) + 1024 * 1024
            model.quantized = mid in ("model-001", "model-005")
            model.accuracy_score = round(0.85 + (hash(mid) % 1000) / 10000, 3)
            model.latency_ms = round(10 + (hash(mid) % 100), 1)
            model.inference_count = hash(mid) % 5000
            model.deployed_at = datetime.utcnow() - timedelta(days=hash(mid) % 30)
            model.labels = {i: cls for i, cls in enumerate(classes)}
            self.models[mid] = model

    async def initialize(self):
        logger.info("EdgeMLInference initialized with %d models", len(self.models))

    async def close(self):
        logger.info("EdgeMLInference closed")

    def deploy_model(self, name: str, model_format: ModelFormat,
                     device_id: str, version: str,
                     input_shape: list[int],
                     output_classes: list[str],
                     hardware_target: InferenceHardware = InferenceHardware.CPU,
                     threshold: float = 0.5,
                     quantized: bool = False) -> EdgeModel:
        model_id = f"model-{uuid.uuid4().hex[:8]}"
        model = EdgeModel(model_id, name, model_format, device_id, version)
        model.input_shape = input_shape
        model.output_classes = output_classes
        model.hardware_target = hardware_target
        model.threshold = threshold
        model.quantized = quantized
        self.models[model_id] = model
        asyncio.create_task(self._deploy_model_async(model))
        logger.info("Deploying model %s (%s v%s) to device %s", model_id, name, version, device_id)
        return model

    async def _deploy_model_async(self, model: EdgeModel):
        try:
            await asyncio.sleep(2)
            model.status = ModelStatus.ACTIVE
            model.deployed_at = datetime.utcnow()
            model.model_size_bytes = sum(len(c) for c in model.output_classes) * 1000
            model.latency_ms = 20.0 if model.quantized else 45.0
            model.accuracy_score = 0.95 if model.quantized else 0.97
            model.updated_at = datetime.utcnow()
            logger.info("Model %s deployed successfully", model.model_id)
        except Exception as e:
            model.status = ModelStatus.FAILED
            model.updated_at = datetime.utcnow()
            logger.error("Model %s deployment failed: %s", model.model_id, e)

    def get_model(self, model_id: str) -> Optional[EdgeModel]:
        return self.models.get(model_id)

    def list_models(self, device_id: Optional[str] = None,
                    status: Optional[str] = None,
                    model_format: Optional[str] = None) -> list[EdgeModel]:
        result = list(self.models.values())
        if device_id:
            result = [m for m in result if m.device_id == device_id]
        if status:
            result = [m for m in result if m.status.value == status]
        if model_format:
            result = [m for m in result if m.model_format.value == model_format]
        return result

    def delete_model(self, model_id: str) -> bool:
        if model_id in self.models:
            model = self.models[model_id]
            model.status = ModelStatus.ARCHIVED
            model.updated_at = datetime.utcnow()
            return True
        return False

    def run_inference(self, model_id: str,
                      input_data: Any) -> InferenceResult:
        model = self.models.get(model_id)
        if not model:
            return InferenceResult(model_id, False).with_error("Model not found")
        if model.status != ModelStatus.ACTIVE:
            return InferenceResult(model_id, False).with_error(f"Model status: {model.status.value}")
        result = InferenceResult(model_id, True)
        try:
            import random
            model.inference_count += 1
            model.last_inference = datetime.utcnow()
            time_ms = model.latency_ms * (0.8 + 0.4 * (hash(str(input_data)) % 100) / 100)
            result.inference_time_ms = round(time_ms, 1)
            predicted_idx = hash(str(input_data)) % len(model.output_classes)
            result.predicted_class = model.output_classes[predicted_idx]
            result.confidence = round(0.5 + 0.5 * (hash(str(input_data)) % 1000) / 1000, 4)
            result.all_scores = {
                cls: round(0.1 + 0.9 * (hash(cls + str(input_data)) % 1000) / 1000, 4)
                for cls in model.output_classes
            }
            result.all_scores[result.predicted_class] = result.confidence
        except Exception as e:
            return InferenceResult(model_id, False).with_error(str(e))
        return result

    def create_batch_job(self, model_id: str,
                          data_points: list[dict]) -> BatchInferenceJob:
        job_id = f"batch-{uuid.uuid4().hex[:8]}"
        job = BatchInferenceJob(job_id, model_id, data_points)
        self.batch_jobs[job_id] = job
        asyncio.create_task(self._process_batch_job(job))
        return job

    async def _process_batch_job(self, job: BatchInferenceJob):
        job.status = "processing"
        total = len(job.data_points)
        for i, data_point in enumerate(job.data_points):
            result = self.run_inference(job.model_id, data_point)
            job.results.append(result)
            job.progress = (i + 1) / total * 100
            await asyncio.sleep(0.01)
        job.status = "completed"
        job.completed_at = datetime.utcnow()

    def get_batch_job(self, job_id: str) -> Optional[BatchInferenceJob]:
        return self.batch_jobs.get(job_id)

    def get_models_summary(self) -> dict[str, Any]:
        total = len(self.models)
        active = sum(1 for m in self.models.values() if m.status == ModelStatus.ACTIVE)
        total_inferences = sum(m.inference_count for m in self.models.values())
        return {
            "total_models": total,
            "active_models": active,
            "total_inferences": total_inferences,
            "avg_accuracy": round(
                sum(m.accuracy_score for m in self.models.values() if m.accuracy_score > 0) / max(active, 1), 3
            ),
            "avg_latency_ms": round(
                sum(m.latency_ms for m in self.models.values()) / max(total, 1), 1
            ),
        }


class InferenceResult:
    """Result of an ML inference operation."""

    def __init__(self, model_id: str, success: bool):
        self.model_id = model_id
        self.success = success
        self.predicted_class: Optional[str] = None
        self.confidence: float = 0.0
        self.all_scores: dict[str, float] = {}
        self.inference_time_ms: float = 0.0
        self.error_message: Optional[str] = None
        self.timestamp = datetime.utcnow()

    def with_error(self, msg: str) -> "InferenceResult":
        self.success = False
        self.error_message = msg
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "success": self.success,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "all_scores": self.all_scores,
            "inference_time_ms": self.inference_time_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


class EdgeMLInferenceCog(commands.Cog):
    """Discord cog for edge ML model management and inference."""

    def __init__(self, bot):
        self.bot = bot
        self.ml = EdgeMLInference({})

    async def cog_load(self):
        await self.ml.initialize()

    async def cog_unload(self):
        await self.ml.close()

    @discord.app_commands.command(name="ml_models", description="List deployed ML models")
    async def ml_models(self, interaction: discord.Interaction,
                        device_id: Optional[str] = None):
        models = self.ml.list_models(device_id=device_id)
        embed = discord.Embed(title="Edge ML Models", color=discord.Color.blue())
        if not models:
            embed.description = "No models deployed."
        else:
            lines = []
            for m in models[:25]:
                status_emoji = {"active": "🟢", "deploying": "🟡", "failed": "🔴", "archived": "📦"}
                emoji = status_emoji.get(m.status.value, "⚪")
                lines.append(f"{emoji} **{m.name}** v{m.version} (`{m.model_id}`)")
                lines.append(f"   Format: {m.model_format.value} | HW: {m.hardware_target.value} | "
                           f"Acc: {m.accuracy_score:.1%} | Lat: {m.latency_ms}ms")
            embed.description = "\n".join(lines[:25])
        summary = self.ml.get_models_summary()
        embed.set_footer(text=f"Total: {summary['total_models']} | "
                            f"Active: {summary['active_models']} | "
                            f"Inferences: {summary['total_inferences']}")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ml_deploy", description="Deploy an ML model")
    async def ml_deploy(self, interaction: discord.Interaction,
                        name: str, model_format: str, device_id: str,
                        version: str, input_shape: str, output_classes: str):
        try:
            fmt = ModelFormat(model_format)
        except ValueError:
            await interaction.response.send_message(
                f"Invalid format. Choose: {', '.join(f.value for f in ModelFormat)}",
                ephemeral=True
            )
            return
        shape = [int(x.strip()) for x in input_shape.split(",")]
        classes = [c.strip() for c in output_classes.split(",")]
        model = self.ml.deploy_model(name, fmt, device_id, version, shape, classes)
        embed = discord.Embed(title="Model Deployed", color=discord.Color.green())
        embed.add_field(name="Name", value=model.name, inline=True)
        embed.add_field(name="ID", value=model.model_id, inline=True)
        embed.add_field(name="Version", value=model.version, inline=True)
        embed.add_field(name="Format", value=model.model_format.value, inline=True)
        embed.add_field(name="Device", value=model.device_id, inline=True)
        embed.add_field(name="Classes", value=str(len(model.output_classes)), inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ml_infer", description="Run inference on a model")
    async def ml_infer(self, interaction: discord.Interaction,
                       model_id: str, input_data: Optional[str] = None):
        result = self.ml.run_inference(model_id, input_data or "default")
        embed = discord.Embed(title="Inference Result", color=discord.Color.green() if result.success else discord.Color.red())
        if result.success:
            embed.add_field(name="Class", value=result.predicted_class, inline=True)
            embed.add_field(name="Confidence", value=f"{result.confidence:.2%}", inline=True)
            embed.add_field(name="Latency", value=f"{result.inference_time_ms}ms", inline=True)
            top5 = sorted(result.all_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            scores_str = "\n".join(f"{cls}: {score:.2%}" for cls, score in top5)
            embed.add_field(name="Top Scores", value=scores_str, inline=False)
        else:
            embed.add_field(name="Error", value=result.error_message, inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="ml_batch", description="Run batch inference")
    async def ml_batch(self, interaction: discord.Interaction,
                       model_id: str, count: int = 10):
        data_points = [{"id": i, "value": hash(f"data_{i}")} for i in range(min(count, 1000))]
        job = self.ml.create_batch_job(model_id, data_points)
        embed = discord.Embed(title="Batch Job Created", color=discord.Color.blue())
        embed.add_field(name="Job ID", value=job.job_id, inline=True)
        embed.add_field(name="Model", value=model_id, inline=True)
        embed.add_field(name="Data Points", value=str(len(data_points)), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(EdgeMLInferenceCog(bot))
