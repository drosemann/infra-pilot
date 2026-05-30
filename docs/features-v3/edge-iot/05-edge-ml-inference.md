# Feature 5: Edge ML Inference

## Overview
Deploy TensorFlow Lite (TFLite) and ONNX models to edge nodes. Support camera feed analysis, vibration monitoring, predictive maintenance, and other ML workloads at the edge.

## Capabilities
- TFLite model deployment and execution
- ONNX Runtime for cross-framework models
- Model format conversion (TF, PyTorch → TFLite/ONNX)
- Camera feed capture and image classification
- Vibration/accelerometer data analysis
- Predictive maintenance alerts
- Model versioning with A/B testing
- Batch inference for historical data
- Inference result streaming to cloud
- Model quantization for resource-constrained devices

## Supported Models

| Model Type | Use Case | Format | Accelerator |
|-----------|----------|--------|-------------|
| Image Classification | Object detection, quality inspection | TFLite | GPU, NPU (Coral) |
| Time Series | Vibration analysis, predictive maint | ONNX | CPU |
| Anomaly Detection | Security, intrusion detection | TFLite | CPU, GPU |
| NLP | Keyword spotting, command recognition | TFLite | CPU, NPU |
| Audio | Sound classification, leak detection | ONNX | CPU |

## Inference Pipeline

```
Edge Device
  ├── Model Registry (local cache)
  │   ├── models/
  │   │   ├── mobilenet_v2.tflite
  │   │   ├── anomaly_detector.onnx  
  │   │   └── vibration_cnn.tflite
  │   └── manifests/
  │       └── model_manifest.json
  │
  ├── Inference Engine
  │   ├── TFLite Interpreter (C++/Python)
  │   ├── ONNX Runtime (C++/Python)
  │   ├── Preprocessing pipeline
  │   └── Postprocessing pipeline
  │
  ├── Data Sources
  │   ├── Camera (USB, CSI, IP)
  │   ├── Sensors (I2C, SPI, GPIO)
  │   ├── Audio (USB mic, I2S)
  │   └── Files (CSV, JSON, images)
  │
  └── Result Handlers
      ├── Local storage (SQLite)
      ├── MQTT publish
      ├── Alert trigger
      └── Cloud sync
```

## Model Management

```python
# Deploy model to edge node
edge_client.deploy_model(
    node_id="node-042",
    model_name="defect_detector",
    model_file="models/defect_detector_v2.tflite",
    model_type="tflite",
    input_shape=[1, 224, 224, 3],
    output_classes=["ok", "scratch", "dent", "crack"],
    threshold=0.85,
    preprocess_steps=["resize(224,224)", "normalize(0,1)"],
    trigger="camera:camera1"
)

# Run inference and get results
result = edge_client.run_inference(
    node_id="node-042",
    model_name="defect_detector",
    input_data=image_bytes
)
# {"class": "scratch", "confidence": 0.92, "inference_time_ms": 45}
```

## Implementation
- Primary service: Orchestrator Agent (cog)
- Module: `services/orchestrator-agent/cogs/edge_ml_inference.py`
- Test with mock TFLite models
- CLI commands for model deployment
