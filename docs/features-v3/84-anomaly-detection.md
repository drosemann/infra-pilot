# Feature 84: Time-Series Anomaly Detection Engine

## Overview
Multi-method anomaly detection engine for infrastructure metrics. Supports statistical and ML-based techniques with adaptive thresholds.

## Detection Methods
- Z-score: flags points beyond N standard deviations
- Modified Z-score (MAD): robust to outliers in baseline
- IQR: Tukey's fences method
- STL Decomposition: seasonal-trend residual analysis
- CUSUM: cumulative sum change detection
- Adaptive Threshold: dynamically adjusts to recent patterns

## Configuration
- Detection method selection per metric
- Sensitivity parameters per method
- Seasonality period (for STL)
- Alert cooldown to prevent flooding
- Per-metric thresholds and profiles

## Backend API
- `POST /api/v1/anomaly/detect` - run detection on data
- `GET /api/v1/anomaly/profiles` - list configured profiles
- `POST /api/v1/anomaly/profiles` - create profile
- `GET /api/v1/anomaly/history` - anomaly event history
