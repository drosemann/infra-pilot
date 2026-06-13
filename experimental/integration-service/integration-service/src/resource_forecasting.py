"""Feature 85: Resource Forecasting Engine - Prophet/ARIMA-based capacity planning"""

import json
import os
import math
import uuid
import asyncio
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class ForecastHorizon(Enum):
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


class ForecastModel(Enum):
    PROPHET = "prophet"
    ARIMA = "arima"
    HOLT_WINTERS = "holt_winters"
    LINEAR_REGRESSION = "linear_regression"
    MOVING_AVERAGE = "moving_average"
    ENSEMBLE = "ensemble"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_NAIVE = "seasonal_naive"
    THETA = "theta"


class ResourceForecastingEngine:
    """Resource forecasting engine for capacity planning using multiple models"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_horizon_days = config.get("default_horizon_days", 30)
        self.seasonality_period = config.get("seasonality_period", 24)
        self.confidence_level = config.get("confidence_level", 0.95)
        self.min_training_points = config.get("min_training_points", 14)

        self.forecasts_file = _data_file('forecast_results.json')
        self.models_file = _data_file('forecast_models.json')
        self.accuracy_file = _data_file('forecast_accuracy.json')

        self.forecast_results: Dict[str, Dict[str, Any]] = {}
        self.models: Dict[str, Dict[str, Any]] = {}
        self.accuracy_metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._load_data()

    def _load_data(self):
        for filepath, target in [
            (self.forecasts_file, "forecasts"),
            (self.models_file, "models"),
            (self.accuracy_file, "accuracy")
        ]:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if target == "forecasts":
                        self.forecast_results = {k: v for k, v in data.items()}
                    elif target == "models":
                        self.models = data
                    elif target == "accuracy":
                        self.accuracy_metrics = {k: v for k, v in data.items()}
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    def _save_forecasts(self):
        try:
            with open(self.forecasts_file, 'w') as f:
                json.dump(self.forecast_results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save forecasts: {e}")

    def _save_models(self):
        try:
            with open(self.models_file, 'w') as f:
                json.dump(self.models, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def _save_accuracy(self):
        try:
            with open(self.accuracy_file, 'w') as f:
                json.dump(self.accuracy_metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save accuracy: {e}")

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _z_critical(self, confidence: float) -> float:
        if confidence >= 0.99:
            return 2.576
        elif confidence >= 0.95:
            return 1.960
        elif confidence >= 0.90:
            return 1.645
        elif confidence >= 0.85:
            return 1.440
        return 1.960

    def _linear_regression_forecast(self, values: List[float], steps: int) -> Tuple[List[float], List[float], List[float]]:
        n = len(values)
        if n < 3:
            return ([values[-1]] * steps, [0] * steps, [0] * steps)
        x = list(range(n))
        x_sum = sum(x)
        y_sum = sum(values)
        x2_sum = sum(xi ** 2 for xi in x)
        xy_sum = sum(xi * yi for xi, yi in zip(x, values))
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum ** 2) if (n * x2_sum - x_sum ** 2) != 0 else 0
        intercept = (y_sum - slope * x_sum) / n if n > 0 else 0
        residuals = [values[i] - (slope * i + intercept) for i in range(n)]
        residual_std = statistics.pstdev(residuals) if len(residuals) > 1 else 0
        z = self._z_critical(self.confidence_level)
        forecasts = []
        lower_bounds = []
        upper_bounds = []
        for i in range(1, steps + 1):
            pred = slope * (n + i - 1) + intercept
            forecasts.append(pred)
            interval = z * residual_std * math.sqrt(1 + 1 / n + (n + i - 1 - x_sum / n) ** 2 / (x2_sum - x_sum ** 2 / n)) if residual_std > 0 else 0
            lower_bounds.append(pred - interval)
            upper_bounds.append(pred + interval)
        return (forecasts, lower_bounds, upper_bounds)

    def _moving_average_forecast(self, values: List[float], steps: int, window: int = 7) -> Tuple[List[float], List[float], List[float]]:
        if len(values) < window:
            window = max(2, len(values))
        recent = values[-window:]
        ma = statistics.mean(recent)
        std = statistics.pstdev(recent) if len(recent) > 1 else 0
        z = self._z_critical(self.confidence_level)
        forecasts = [ma] * steps
        interval = z * std * math.sqrt(1 + 1 / window) if std > 0 else 0
        lower_bounds = [ma - interval] * steps
        upper_bounds = [ma + interval] * steps
        return (forecasts, lower_bounds, upper_bounds)

    def _holt_winters_forecast(self, values: List[float], steps: int,
                                 period: int = 24) -> Tuple[List[float], List[float], List[float]]:
        n = len(values)
        if n < period * 2:
            return self._linear_regression_forecast(values, steps)

        alpha = 0.3
        beta = 0.1
        gamma = 0.1

        level = [values[0]]
        trend = [values[1] - values[0]] if n > 1 else [0]
        seasonal = [values[i] - values[0] for i in range(min(period, n))]

        for i in range(1, n):
            if i < period:
                new_level = alpha * values[i] + (1 - alpha) * (level[-1] + trend[-1])
                new_trend = beta * (new_level - level[-1]) + (1 - beta) * trend[-1]
                level.append(new_level)
                trend.append(new_trend)
            else:
                s_idx = i % period
                new_level = alpha * (values[i] - seasonal[s_idx]) + (1 - alpha) * (level[-1] + trend[-1])
                new_trend = beta * (new_level - level[-1]) + (1 - beta) * trend[-1]
                seasonal[s_idx] = gamma * (values[i] - new_level) + (1 - gamma) * seasonal[s_idx]
                level.append(new_level)
                trend.append(new_trend)

        forecasts = []
        lower_bounds = []
        upper_bounds = []
        residuals = [values[i] - level[i] for i in range(n)]
        residual_std = statistics.pstdev(residuals) if len(residuals) > 1 else 0
        z = self._z_critical(self.confidence_level)

        for i in range(steps):
            s_idx = (n + i) % period
            pred = level[-1] + (i + 1) * trend[-1] + (seasonal[s_idx] if s_idx < len(seasonal) else 0)
            forecasts.append(pred)
            interval = z * residual_std * math.sqrt(i + 1) if residual_std > 0 else 0
            lower_bounds.append(pred - interval)
            upper_bounds.append(pred + interval)

        return (forecasts, lower_bounds, upper_bounds)

    def _exponential_smoothing_forecast(self, values: List[float], steps: int,
                                          alpha: float = 0.3) -> Tuple[List[float], List[float], List[float]]:
        if not values:
            return ([], [], [])
        smoothed = [values[0]]
        for v in values[1:]:
            smoothed.append(alpha * v + (1 - alpha) * smoothed[-1])
        last_smooth = smoothed[-1]
        residuals = [values[i] - smoothed[i] for i in range(len(values))]
        residual_std = statistics.pstdev(residuals) if len(residuals) > 1 else 0
        z = self._z_critical(self.confidence_level)
        forecasts = [last_smooth] * steps
        interval = z * residual_std if residual_std > 0 else 0
        lower_bounds = [last_smooth - interval] * steps
        upper_bounds = [last_smooth + interval] * steps
        return (forecasts, lower_bounds, upper_bounds)

    def _seasonal_naive_forecast(self, values: List[float], steps: int,
                                   period: int = 24) -> Tuple[List[float], List[float], List[float]]:
        if len(values) < period:
            return self._moving_average_forecast(values, steps)
        forecasts = []
        lower_bounds = []
        upper_bounds = []
        z = self._z_critical(self.confidence_level)
        residuals = [values[i] - values[i - period] for i in range(period, len(values))]
        residual_std = statistics.pstdev(residuals) if len(residuals) > 1 else 0
        for i in range(steps):
            idx = len(values) - period + (i % period)
            pred = values[idx] if idx < len(values) else values[-period + (i % period)]
            forecasts.append(pred)
            interval = z * residual_std if residual_std > 0 else 0
            lower_bounds.append(pred - interval)
            upper_bounds.append(pred + interval)
        return (forecasts, lower_bounds, upper_bounds)

    def _theta_forecast(self, values: List[float], steps: int) -> Tuple[List[float], List[float], List[float]]:
        theta = 2.0
        n = len(values)
        if n < 3:
            return self._moving_average_forecast(values, steps)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        slope_num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        slope_den = sum((xi - x_mean) ** 2 for xi in x)
        slope = slope_num / slope_den if slope_den != 0 else 0
        intercept = y_mean - slope * x_mean
        theta_line = [intercept + slope * xi for xi in x]
        theta_values = [theta * vi - (theta - 1) * tl for vi, tl in zip(values, theta_line)]
        theta_mean = statistics.mean(theta_values)
        forecasts = []
        lower_bounds = []
        upper_bounds = []
        residuals = [values[i] - (intercept + slope * x[i]) for i in range(n)]
        residual_std = statistics.pstdev(residuals) if len(residuals) > 1 else 0
        z = self._z_critical(self.confidence_level)
        for i in range(1, steps + 1):
            pred = (intercept + slope * (n + i - 1)) / theta + (1 - 1 / theta) * theta_mean
            forecasts.append(pred)
            interval = z * residual_std * math.sqrt(i / n) if residual_std > 0 else 0
            lower_bounds.append(pred - interval)
            upper_bounds.append(pred + interval)
        return (forecasts, lower_bounds, upper_bounds)

    def _ensemble_forecast(self, values: List[float], steps: int) -> Tuple[List[float], List[float], List[float]]:
        methods = [
            self._linear_regression_forecast,
            self._moving_average_forecast,
            self._holt_winters_forecast,
            self._exponential_smoothing_forecast,
            self._seasonal_naive_forecast,
            self._theta_forecast
        ]
        all_forecasts = []
        all_lower = []
        all_upper = []
        for method in methods:
            try:
                f, l, u = method(values, steps)
                all_forecasts.append(f)
                all_lower.append(l)
                all_upper.append(u)
            except Exception as e:
                logger.warning(f"Ensemble method failed: {e}")
        if not all_forecasts:
            return self._moving_average_forecast(values, steps)
        avg_forecasts = [statistics.mean([f[i] for f in all_forecasts]) for i in range(steps)]
        avg_lower = [statistics.mean([l[i] for l in all_lower]) for i in range(steps)]
        avg_upper = [statistics.mean([u[i] for u in all_upper]) for i in range(steps)]
        return (avg_forecasts, avg_lower, avg_upper)

    async def generate_forecast(self, resource_id: str, historical_values: List[float],
                                  horizon_days: Optional[int] = None,
                                  model_type: str = ForecastModel.ENSEMBLE.value,
                                  seasonality_period: Optional[int] = None,
                                  granularity: str = "daily") -> Dict[str, Any]:
        horizon = horizon_days or self.default_horizon_days
        period = seasonality_period or self.seasonality_period

        if len(historical_values) < self.min_training_points:
            return {
                "resource_id": resource_id,
                "status": "error",
                "error": f"Need at least {self.min_training_points} data points, got {len(historical_values)}"
            }

        steps = horizon

        model_map = {
            ForecastModel.LINEAR_REGRESSION.value: self._linear_regression_forecast,
            ForecastModel.MOVING_AVERAGE.value: self._moving_average_forecast,
            ForecastModel.HOLT_WINTERS.value: self._holt_winters_forecast,
            ForecastModel.EXPONENTIAL_SMOOTHING.value: self._exponential_smoothing_forecast,
            ForecastModel.SEASONAL_NAIVE.value: self._seasonal_naive_forecast,
            ForecastModel.THETA.value: self._theta_forecast,
            ForecastModel.ENSEMBLE.value: self._ensemble_forecast,
        }

        if ForecastModel.PROPHET.value in model_type:
            try:
                forecasts, lower, upper = await self._prophet_forecast(historical_values, steps, period)
            except Exception as e:
                logger.warning(f"Prophet failed, falling back to ensemble: {e}")
                forecasts, lower, upper = self._ensemble_forecast(historical_values, steps)
        elif ForecastModel.ARIMA.value in model_type:
            try:
                forecasts, lower, upper = self._arima_forecast(historical_values, steps)
            except Exception as e:
                logger.warning(f"ARIMA failed, falling back to ensemble: {e}")
                forecasts, lower, upper = self._ensemble_forecast(historical_values, steps)
        elif model_type in model_map:
            forecasts, lower, upper = model_map[model_type](historical_values, steps)
        else:
            forecasts, lower, upper = self._ensemble_forecast(historical_values, steps)

        now = datetime.utcnow()
        forecast_points = []
        for i in range(steps):
            ts = (now + timedelta(days=i)).isoformat() + "Z" if granularity == "daily" else \
                 (now + timedelta(hours=i)).isoformat() + "Z"
            forecast_points.append({
                "timestamp": ts,
                "forecast": round(forecasts[i], 4) if i < len(forecasts) else 0,
                "lower_bound": round(lower[i], 4) if i < len(lower) else 0,
                "upper_bound": round(upper[i], 4) if i < len(upper) else 0
            })

        result = {
            "id": self._generate_id(),
            "resource_id": resource_id,
            "model_type": model_type,
            "generated_at": self._now(),
            "horizon_days": horizon,
            "granularity": granularity,
            "training_points": len(historical_values),
            "forecast": forecast_points,
            "summary": {
                "min_forecast": round(min(forecasts), 4) if forecasts else 0,
                "max_forecast": round(max(forecasts), 4) if forecasts else 0,
                "mean_forecast": round(statistics.mean(forecasts), 4) if forecasts else 0,
                "last_historical": historical_values[-1] if historical_values else 0,
                "p50_forecast": round(statistics.median(forecasts), 4) if forecasts else 0,
                "p95_forecast": round(sorted(forecasts)[int(len(forecasts) * 0.95)] if len(forecasts) > 1 else forecasts[0], 4) if forecasts else 0,
                "trend_direction": "up" if forecasts[-1] > forecasts[0] if len(forecasts) > 1 else "flat" else "flat" if len(forecasts) > 1 else "flat",
                "confidence_interval_width": round(statistics.mean([u - l for u, l in zip(upper, lower)]), 4) if upper and lower else 0
            },
            "metadata": {
                "seasonality_period": period,
                "confidence_level": self.confidence_level
            }
        }

        self.forecast_results[resource_id] = result
        self._save_forecasts()
        return result

    async def _prophet_forecast(self, values: List[float], steps: int,
                                  period: int = 24) -> Tuple[List[float], List[float], List[float]]:
        try:
            from prophet import Prophet
            import pandas as pd
            df = pd.DataFrame({
                "ds": pd.date_range(end=pd.Timestamp.now(), periods=len(values), freq="H" if period <= 24 else "D"),
                "y": values
            })
            model = Prophet(
                seasonality_mode="multiplicative",
                weekly_seasonality=True,
                daily_seasonality=(period <= 24),
                yearly_seasonality=False
            )
            model.fit(df)
            future = model.make_future_dataframe(periods=steps, freq="H" if period <= 24 else "D")
            forecast = model.predict(future)
            preds = forecast["yhat"].tail(steps).tolist()
            lower = forecast["yhat_lower"].tail(steps).tolist()
            upper = forecast["yhat_upper"].tail(steps).tolist()
            return (preds, lower, upper)
        except ImportError:
            logger.warning("Prophet not available, using Holt-Winters as fallback")
            return self._holt_winters_forecast(values, steps, period)

    def _arima_forecast(self, values: List[float], steps: int) -> Tuple[List[float], List[float], List[float]]:
        try:
            from statsmodels.tsa.arima.model import ARIMA
            model = ARIMA(values, order=(2, 1, 2))
            fitted = model.fit()
            result = fitted.forecast(steps=steps)
            preds = result.tolist() if hasattr(result, 'tolist') else list(result)
            conf_int = fitted.get_forecast(steps=steps).conf_int(alpha=0.05)
            lower = conf_int.iloc[:, 0].tolist()
            upper = conf_int.iloc[:, 1].tolist()
            return (preds, lower, upper)
        except ImportError:
            logger.warning("statsmodels not available, using Holt-Winters as fallback")
            return self._holt_winters_forecast(values, steps)
        except Exception as e:
            logger.warning(f"ARIMA failed: {e}, using Holt-Winters fallback")
            return self._holt_winters_forecast(values, steps)

    async def what_if_scenario(self, resource_id: str, base_values: List[float],
                                 scenario_name: str,
                                 adjustment_factor: float = 1.1,
                                 horizon_days: Optional[int] = None) -> Dict[str, Any]:
        adjusted_values = [v * adjustment_factor for v in base_values]
        base_forecast = await self.generate_forecast(
            f"{resource_id}_base", base_values, horizon_days
        )
        scenario_forecast = await self.generate_forecast(
            f"{resource_id}_{scenario_name}", adjusted_values, horizon_days
        )
        return {
            "scenario_name": scenario_name,
            "adjustment_factor": adjustment_factor,
            "base_forecast": base_forecast,
            "scenario_forecast": scenario_forecast,
            "differential": {
                "base_final": base_forecast["forecast"][-1] if base_forecast.get("forecast") else 0,
                "scenario_final": scenario_forecast["forecast"][-1] if scenario_forecast.get("forecast") else 0,
                "absolute_difference": (
                    (scenario_forecast["forecast"][-1] if scenario_forecast.get("forecast") else 0) -
                    (base_forecast["forecast"][-1] if base_forecast.get("forecast") else 0)
                ),
                "percentage_change": (
                    ((scenario_forecast["forecast"][-1] if scenario_forecast.get("forecast") else 0) /
                     (base_forecast["forecast"][-1] if base_forecast.get("forecast") else 1) - 1) * 100
                    if base_forecast.get("forecast") and base_forecast["forecast"][-1] != 0 else 0
                )
            }
        }

    async def calculate_accuracy(self, resource_id: str, actuals: List[float],
                                   predictions: List[float]) -> Dict[str, Any]:
        if not actuals or not predictions or len(actuals) != len(predictions):
            return {"error": "Actuals and predictions must be non-empty and same length"}

        n = len(actuals)
        errors = [a - p for a, p in zip(actuals, predictions)]
        abs_errors = [abs(e) for e in errors]
        pct_errors = [abs(e) / a * 100 if a != 0 else 0 for e, a in zip(errors, actuals)]

        mae = statistics.mean(abs_errors)
        mse = statistics.mean([e ** 2 for e in errors])
        rmse = math.sqrt(mse)
        mape = statistics.mean(pct_errors)
        smape = statistics.mean([
            abs(a - p) / ((abs(a) + abs(p)) / 2) * 100 if (abs(a) + abs(p)) > 0 else 0
            for a, p in zip(actuals, predictions)
        ])

        actual_mean = statistics.mean(actuals)
        ss_res = sum((a - p) ** 2 for a, p in zip(actuals, predictions))
        ss_tot = sum((a - actual_mean) ** 2 for a in actuals)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        accuracy_entry = {
            "resource_id": resource_id,
            "n": n,
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 4),
            "smape": round(smape, 4),
            "r2": round(r2, 4),
            "calculated_at": self._now()
        }

        self.accuracy_metrics.setdefault(resource_id, []).append(accuracy_entry)
        self._save_accuracy()
        return accuracy_entry

    async def get_forecast(self, resource_id: str) -> Optional[Dict[str, Any]]:
        return self.forecast_results.get(resource_id)

    async def list_models(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in self.models.items()]

    async def train_model(self, resource_id: str, values: List[float],
                           model_type: str = ForecastModel.ENSEMBLE.value) -> Dict[str, Any]:
        if len(values) < self.min_training_points:
            raise ValueError(f"Need at least {self.min_training_points} training points")
        model_id = self._generate_id()
        mean = statistics.mean(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0
        model = {
            "id": model_id,
            "resource_id": resource_id,
            "model_type": model_type,
            "trained_at": self._now(),
            "training_points": len(values),
            "statistics": {
                "mean": round(mean, 4),
                "std": round(std, 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "trend": round((values[-1] - values[0]) / len(values), 4) if len(values) > 1 else 0
            }
        }
        self.models[resource_id] = model
        self._save_models()
        return model

    async def get_accuracy(self, resource_id: str) -> List[Dict[str, Any]]:
        return list(reversed(self.accuracy_metrics.get(resource_id, [])))

    async def set_forecast_alert(self, resource_id: str, threshold: float,
                                   direction: str = "above") -> Dict[str, Any]:
        return {
            "resource_id": resource_id,
            "threshold": threshold,
            "direction": direction,
            "enabled": True,
            "created_at": self._now(),
            "alert_id": self._generate_id()
        }

    async def initialize(self):
        logger.info("ResourceForecastingEngine initialized with %d forecasts, %d models",
                     len(self.forecast_results), len(self.models))

    async def close(self):
        self._save_forecasts()
        self._save_models()
        self._save_accuracy()
        logger.info("ResourceForecastingEngine closed")
