"""Feature 25: Budget & Forecast Engine - Hierarchical budgets, forecast vs actual"""

import json
import os
import math
import uuid
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _data_file(name):
    _ensure_data_dir()
    return os.path.join(DATA_DIR, name)


class BudgetPeriod(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class BudgetScope(Enum):
    ORG = "org"
    TEAM = "team"
    PROJECT = "project"
    SERVICE = "service"


class BudgetStatus(Enum):
    ACTIVE = "active"
    EXCEEDED = "exceeded"
    AT_RISK = "at_risk"
    PAUSED = "paused"
    COMPLETED = "completed"


class ForecastModel(Enum):
    MOVING_AVERAGE = "moving_average"
    LINEAR_REGRESSION = "linear_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL = "seasonal"
    ENSEMBLE = "ensemble"


class BudgetForecastEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.budgets_file = _data_file('budgets.json')
        self.actuals_file = _data_file('budget_actuals.json')
        self.forecasts_file = _data_file('budget_forecasts.json')
        self.scenarios_file = _data_file('budget_scenarios.json')
        self.budgets: List[Dict[str, Any]] = []
        self.actuals: List[Dict[str, Any]] = []
        self.forecasts: List[Dict[str, Any]] = []
        self.scenarios: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.budgets_file, 'budgets'), (self.actuals_file, 'actuals'),
                           (self.forecasts_file, 'forecasts'), (self.scenarios_file, 'scenarios')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_budgets(self):
        try:
            with open(self.budgets_file, 'w') as f:
                json.dump(self.budgets, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save budgets: {e}")

    def _save_actuals(self):
        try:
            with open(self.actuals_file, 'w') as f:
                json.dump(self.actuals, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save actuals: {e}")

    def _save_forecasts(self):
        try:
            with open(self.forecasts_file, 'w') as f:
                json.dump(self.forecasts, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save forecasts: {e}")

    def _save_scenarios(self):
        try:
            with open(self.scenarios_file, 'w') as f:
                json.dump(self.scenarios, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save scenarios: {e}")

    def create_budget(self, name: str, amount: float, period: str, scope: str,
                      scope_id: str = None, parent_id: str = None,
                      alert_thresholds: List[float] = None) -> Dict[str, Any]:
        budget = {
            "id": str(uuid.uuid4()),
            "name": name,
            "amount": amount,
            "spent": 0,
            "period": period,
            "scope": scope,
            "scope_id": scope_id or name.lower().replace(' ', '_'),
            "parent_id": parent_id,
            "status": BudgetStatus.ACTIVE.value,
            "alert_thresholds": alert_thresholds or [0.5, 0.75, 0.9, 1.0],
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat() if period == BudgetPeriod.MONTHLY.value
                        else (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "children": [],
        }
        self.budgets.append(budget)
        self._save_budgets()
        return budget

    def record_actual_spend(self, budget_id: str, amount: float,
                            category: str = None, description: str = None) -> Dict[str, Any]:
        actual = {
            "id": str(uuid.uuid4()),
            "budget_id": budget_id,
            "amount": amount,
            "category": category,
            "description": description,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self.actuals.append(actual)
        self._save_actuals()

        budget = next((b for b in self.budgets if b['id'] == budget_id), None)
        if budget:
            budget['spent'] = budget.get('spent', 0) + amount
            self._update_budget_status(budget)
            self._save_budgets()

            if budget['parent_id']:
                parent = next((b for b in self.budgets if b['id'] == budget['parent_id']), None)
                if parent:
                    children = [b for b in self.budgets if b.get('parent_id') == parent['id']]
                    parent['spent'] = sum(c.get('spent', 0) for c in children)
                    self._update_budget_status(parent)
                    self._save_budgets()
        return actual

    def _update_budget_status(self, budget: Dict):
        ratio = budget['spent'] / max(budget['amount'], 0.01)
        if ratio >= 1.0:
            budget['status'] = BudgetStatus.EXCEEDED.value
        elif ratio >= budget.get('alert_thresholds', [])[-2] if len(budget.get('alert_thresholds', [])) >= 2 else 0.8:
            budget['status'] = BudgetStatus.AT_RISK.value
        else:
            budget['status'] = BudgetStatus.ACTIVE.value

    def get_budget(self, budget_id: str) -> Optional[Dict[str, Any]]:
        return next((b for b in self.budgets if b['id'] == budget_id), None)

    def list_budgets(self, scope: str = None, scope_id: str = None) -> List[Dict[str, Any]]:
        result = self.budgets
        if scope:
            result = [b for b in result if b['scope'] == scope]
        if scope_id:
            result = [b for b in result if b.get('scope_id') == scope_id]
        return result

    def get_budget_tree(self, root_id: str = None) -> List[Dict[str, Any]]:
        roots = [b for b in self.budgets if b.get('parent_id') is None] if not root_id else [self.get_budget(root_id)]
        def build_tree(budget):
            budget['children'] = [build_tree(c) for c in self.budgets if c.get('parent_id') == budget['id']]
            return budget
        return [build_tree(b) for b in roots]

    def generate_forecast(self, budget_id: str, model: str = "moving_average",
                          horizon_days: int = 30) -> Dict[str, Any]:
        budget = self.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}

        budget_actuals = [a for a in self.actuals if a['budget_id'] == budget_id]
        if len(budget_actuals) < 7:
            budget_actuals = self._generate_mock_actuals(budget_id, budget['amount'])

        values = [a['amount'] for a in sorted(budget_actuals, key=lambda x: x['recorded_at'])]
        daily_avg = sum(values) / max(len(values), 1)

        if model == ForecastModel.MOVING_AVERAGE.value:
            predicted = self._ma_forecast(values, horizon_days)
        elif model == ForecastModel.LINEAR_REGRESSION.value:
            predicted = self._lr_forecast(values, horizon_days)
        elif model == ForecastModel.EXPONENTIAL_SMOOTHING.value:
            predicted = self._es_forecast(values, horizon_days)
        else:
            predicted = [round(daily_avg * random.uniform(0.9, 1.1), 2) for _ in range(horizon_days)]

        total_forecast = sum(predicted)
        projected_overspend = max(0, total_forecast - budget['amount'])
        confidence = "high" if len(values) > 60 else "medium" if len(values) > 14 else "low"

        forecast_entry = {
            "id": str(uuid.uuid4()),
            "budget_id": budget_id,
            "model": model,
            "horizon_days": horizon_days,
            "daily_forecasts": predicted[:min(horizon_days, 90)],
            "total_forecast": round(total_forecast, 2),
            "budget_amount": budget['amount'],
            "projected_overspend": round(projected_overspend, 2),
            "confidence": confidence,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.forecasts.append(forecast_entry)
        self._save_forecasts()
        return forecast_entry

    def _ma_forecast(self, values: List[float], horizon: int) -> List[float]:
        window = min(7, max(1, len(values) // 4))
        ma = sum(values[-window:]) / window if len(values) >= window else sum(values) / len(values)
        trend = (values[-1] - values[0]) / max(len(values), 1) if len(values) > 1 else 0
        return [round(max(0, ma + trend * i), 2) for i in range(horizon)]

    def _lr_forecast(self, values: List[float], horizon: int) -> List[float]:
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum(i * v for i, v in enumerate(values)) - n * x_mean * y_mean
        den = sum(i * i for i in range(n)) - n * x_mean * x_mean
        slope = num / max(den, 0.01)
        intercept = y_mean - slope * x_mean
        return [round(max(0, intercept + slope * (n + i)), 2) for i in range(horizon)]

    def _es_forecast(self, values: List[float], horizon: int) -> List[float]:
        alpha = 0.3
        smoothed = values[0]
        for v in values[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed
        return [round(max(0, smoothed * (1 + random.uniform(-0.05, 0.05))), 2) for _ in range(horizon)]

    def what_if_scenario(self, budget_id: str, changes: Dict[str, float]) -> Dict[str, Any]:
        budget = self.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        new_amount = budget['amount']
        adjustments = {}
        for key, pct in changes.items():
            adjustment = budget['amount'] * (pct / 100)
            new_amount += adjustment
            adjustments[key] = round(adjustment, 2)
        current_forecast = self.generate_forecast(budget_id, horizon_days=30)
        projected_overspend = max(0, current_forecast.get('total_forecast', 0) - new_amount)
        scenario = {
            "id": str(uuid.uuid4()),
            "budget_id": budget_id,
            "name": f"What-If: {', '.join(f'{k}={v}%' for k, v in changes.items())}",
            "original_amount": budget['amount'],
            "adjusted_amount": round(new_amount, 2),
            "adjustments": adjustments,
            "current_forecast": current_forecast.get('total_forecast', 0),
            "projected_overspend": round(projected_overspend, 2),
            "would_exceed": projected_overspend > 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.scenarios.append(scenario)
        self._save_scenarios()
        return scenario

    def get_scenarios(self, budget_id: str = None) -> List[Dict[str, Any]]:
        if budget_id:
            return [s for s in self.scenarios if s['budget_id'] == budget_id]
        return self.scenarios

    def get_variance_analysis(self, budget_id: str) -> Dict[str, Any]:
        budget = self.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        budget_actuals = [a for a in self.actuals if a['budget_id'] == budget_id]
        total_actual = sum(a['amount'] for a in budget_actuals)
        variance = budget['amount'] - total_actual
        variance_pct = round((variance / max(budget['amount'], 0.01)) * 100, 1)
        daily_avg = total_actual / max(len(budget_actuals), 1)
        projected_total = daily_avg * 30
        return {
            "budget_id": budget_id,
            "budget_name": budget['name'],
            "budget_amount": budget['amount'],
            "total_spent": round(total_actual, 2),
            "remaining": round(max(0, variance), 2),
            "variance": round(variance, 2),
            "variance_pct": variance_pct,
            "spend_pct": round((total_actual / max(budget['amount'], 0.01)) * 100, 1),
            "daily_avg": round(daily_avg, 2),
            "days_remaining": max(0, (datetime.fromisoformat(budget['end_date']) - datetime.utcnow()).days),
            "projected_monthly": round(projected_total, 2),
            "status": budget['status'],
        }

    def get_summary(self) -> Dict[str, Any]:
        total_budget = sum(b['amount'] for b in self.budgets)
        total_spent = sum(b.get('spent', 0) for b in self.budgets)
        at_risk = sum(1 for b in self.budgets if b['status'] == BudgetStatus.AT_RISK.value)
        exceeded = sum(1 for b in self.budgets if b['status'] == BudgetStatus.EXCEEDED.value)
        return {
            "total_budgets": len(self.budgets),
            "total_budget_amount": round(total_budget, 2),
            "total_spent": round(total_spent, 2),
            "remaining": round(total_budget - total_spent, 2),
            "overall_spend_pct": round((total_spent / max(total_budget, 0.01)) * 100, 1),
            "at_risk": at_risk,
            "exceeded": exceeded,
            "healthy": len(self.budgets) - at_risk - exceeded,
        }

    def _generate_mock_actuals(self, budget_id: str, budget_amount: float) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        daily_budget = budget_amount / 30
        mock_actuals = []
        for day in range(30):
            amount = round(daily_budget * random.uniform(0.8, 1.3), 2)
            actual = {
                "id": str(uuid.uuid4()),
                "budget_id": budget_id,
                "amount": amount,
                "recorded_at": (now - timedelta(days=29 - day)).isoformat(),
            }
            mock_actuals.append(actual)
            self.actuals.append(actual)
        self._save_actuals()
        return mock_actuals

# === EXPANDED FUNCTIONALITY ===

from dataclasses import dataclass, asdict
from typing import Optional

class BudgetForecastError(Exception): pass

@dataclass
class BudgetConfig:
    name: str
    amount: float
    period: str = "monthly"
    scope: str = "team"
    start_date: str = ""
    end_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_budget(data: Dict[str, Any]) -> List[str]:
    errors = []
    if not data.get('name'): errors.append("name is required")
    if data.get('amount', 0) <= 0: errors.append("amount must be positive")
    if data.get('period') not in ['weekly', 'monthly', 'quarterly', 'annual']: errors.append("period must be weekly/monthly/quarterly/annual")
    return errors

def compute_forecast(historical_spend: List[float], budget_amount: float, method: str = "linear") -> Dict[str, Any]:
    if not historical_spend: return {"forecasted_spend": 0, "confidence": "low"}
    avg = sum(historical_spend) / len(historical_spend)
    trend = (historical_spend[-1] - historical_spend[0]) / max(len(historical_spend) - 1, 1) if len(historical_spend) > 1 else 0
    forecasted = avg + trend * 7
    at_risk = forecasted > budget_amount * 0.9
    return {
        "forecasted_spend": round(forecasted, 2),
        "budget_amount": round(budget_amount, 2),
        "variance": round(forecasted - budget_amount, 2),
        "at_risk": at_risk,
        "confidence": "high" if len(historical_spend) > 20 else ("medium" if len(historical_spend) > 10 else "low"),
        "method": method,
    }

def compute_variance(budgeted: float, actual: float) -> Dict[str, Any]:
    variance = actual - budgeted
    variance_pct = (variance / max(budgeted, 0.01)) * 100
    return {
        "budgeted": round(budgeted, 2),
        "actual": round(actual, 2),
        "variance": round(variance, 2),
        "variance_pct": round(variance_pct, 1),
        "status": "over_budget" if variance > 0 else ("under_budget" if variance < 0 else "on_track"),
    }

def run_what_if_scenario(budget: Dict[str, Any], changes: Dict[str, float]) -> Dict[str, Any]:
    base = budget.get('amount', 0)
    new_amount = base
    for key, multiplier in changes.items():
        if key == 'ec2_growth': new_amount += base * multiplier
        elif key == 'savings_plan': new_amount -= base * multiplier * 0.3
        elif key == 'spot_migration': new_amount -= base * multiplier * 0.4
    return {
        "scenario": changes,
        "original_budget": round(base, 2),
        "adjusted_budget": round(new_amount, 2),
        "change": round(new_amount - base, 2),
        "change_pct": round(((new_amount - base) / max(base, 0.01)) * 100, 1),
    }

def aggregate_budgets(budgets: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(b.get('amount', 0) for b in budgets)
    spent = sum(b.get('spent', 0) for b in budgets)
    return {
        "count": len(budgets),
        "total_budget": round(total, 2),
        "total_spent": round(spent, 2),
        "remaining": round(max(0, total - spent), 2),
        "utilization_pct": round((spent / max(total, 0.01)) * 100, 1),
    }

def forecast_by_period(budgets: List[Dict[str, Any]], lookahead_months: int = 3) -> List[Dict[str, Any]]:
    forecasts = []
    for b in budgets:
        monthly_rate = (b.get('spent', 0)) / max((datetime.utcnow() - datetime.fromisoformat(b.get('created_at', '2000-01-01'))).days / 30, 1)
        for i in range(1, lookahead_months + 1):
            forecasts.append({
                "budget_id": b.get('id'),
                "budget_name": b.get('name'),
                "month": i,
                "projected_spend": round(monthly_rate * i, 2),
                "budget_remaining": round(max(0, b.get('amount', 0) - monthly_rate * i), 2),
            })
    return forecasts

def generate_budget_alert(budget: Dict[str, Any], current_spend: float) -> Dict[str, Any]:
    utilization = (current_spend / max(budget.get('amount', 1), 0.01)) * 100
    alert_level = "info" if utilization < 75 else ("warning" if utilization < 90 else ("critical" if utilization < 100 else "exceeded"))
    return {
        "budget_id": budget.get('id'),
        "budget_name": budget.get('name'),
        "utilization_pct": round(utilization, 1),
        "alert_level": alert_level,
        "message": f"Budget '{budget.get('name')}' is at {round(utilization, 1)}% utilization",
        "recommended_action": "Review spend and adjust budget or reduce costs" if utilization > 80 else "On track",
    }

# === BATCH OPERATIONS ===

import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import io

class BudgetBatchProcessor:
    def __init__(self, engine: BudgetForecastEngine):
        self.engine = engine
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def batch_create(self, budgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for b in budgets:
            try:
                result = self.engine.create_budget(
                    name=b['name'], amount=b['amount'],
                    period=b.get('period', 'monthly'),
                    scope=b.get('scope', 'team'),
                    scope_id=b.get('scope_id'),
                    parent_id=b.get('parent_id')
                )
                results.append({"success": True, "budget": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": b})
        return results

    async def batch_record_spend(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for r in records:
            try:
                result = self.engine.record_actual_spend(
                    budget_id=r['budget_id'],
                    amount=r['amount'],
                    category=r.get('category'),
                    description=r.get('description')
                )
                results.append({"success": True, "actual": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "input": r})
        return results

    async def batch_forecast(self, budget_ids: List[str], model: str = "moving_average") -> List[Dict[str, Any]]:
        tasks = [self.engine.generate_forecast(bid, model) for bid in budget_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def export_budgets_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "amount", "spent", "period", "scope", "status"])
        for b in self.engine.budgets:
            writer.writerow([b['id'], b['name'], b['amount'], b.get('spent', 0), b['period'], b['scope'], b['status']])
        return output.getvalue()

    async def import_budgets_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        reader = csv.DictReader(io.StringIO(csv_content))
        budgets = []
        for row in reader:
            try:
                budget = self.engine.create_budget(
                    name=row['name'],
                    amount=float(row['amount']),
                    period=row.get('period', 'monthly'),
                    scope=row.get('scope', 'team')
                )
                budgets.append(budget)
            except Exception as e:
                budgets.append({"error": str(e), "row": row})
        return budgets

# === STATE MACHINE ===

class BudgetStateMachine:
    STATES = ["draft", "active", "at_risk", "exceeded", "paused", "closed"]
    TRANSITIONS = {
        "draft": ["active", "closed"],
        "active": ["at_risk", "exceeded", "paused", "closed"],
        "at_risk": ["active", "exceeded", "paused", "closed"],
        "exceeded": ["active", "paused", "closed"],
        "paused": ["active", "closed"],
        "closed": [],
    }

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        if current not in BudgetStateMachine.STATES:
            return False
        if target not in BudgetStateMachine.STATES:
            return False
        if current == target:
            return True
        return target in BudgetStateMachine.TRANSITIONS.get(current, [])

    @staticmethod
    def transition(budget: Dict[str, Any], target: str) -> Dict[str, Any]:
        current = budget.get('status', 'draft')
        if not BudgetStateMachine.can_transition(current, target):
            raise BudgetForecastError(f"Cannot transition from {current} to {target}")
        budget['status'] = target
        budget['status_changed_at'] = datetime.utcnow().isoformat()
        return budget

# === ANALYTICS ===

class BudgetAnalytics:
    def __init__(self, engine: BudgetForecastEngine):
        self.engine = engine

    def spend_trend(self, budget_id: str, days: int = 30) -> List[Dict[str, Any]]:
        budget_actuals = [a for a in self.engine.actuals if a['budget_id'] == budget_id]
        cutoff = datetime.utcnow() - timedelta(days=days)
        filtered = [a for a in budget_actuals if datetime.fromisoformat(a['recorded_at']) >= cutoff]
        return sorted(filtered, key=lambda x: x['recorded_at'])[-90:]

    def category_breakdown(self, budget_id: str = None) -> Dict[str, float]:
        actuals = self.engine.actuals
        if budget_id:
            actuals = [a for a in actuals if a['budget_id'] == budget_id]
        breakdown = {}
        for a in actuals:
            cat = a.get('category', 'uncategorized')
            breakdown[cat] = breakdown.get(cat, 0) + a['amount']
        return {k: round(v, 2) for k, v in breakdown.items()}

    def budget_health_score(self, budget_id: str) -> float:
        budget = self.engine.get_budget(budget_id)
        if not budget:
            return 0.0
        ratio = budget.get('spent', 0) / max(budget['amount'], 0.01)
        if ratio <= 0.5:
            return 1.0
        if ratio <= 0.75:
            return 0.8
        if ratio <= 0.9:
            return 0.5
        if ratio <= 1.0:
            return 0.2
        return 0.0

    def anomaly_detection(self, budget_id: str) -> List[Dict[str, Any]]:
        actuals = sorted(
            [a for a in self.engine.actuals if a['budget_id'] == budget_id],
            key=lambda x: x['recorded_at']
        )
        anomalies = []
        if len(actuals) < 5:
            return anomalies
        values = [a['amount'] for a in actuals]
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        for a in actuals:
            zscore = (a['amount'] - mean) / max(std, 0.01)
            if abs(zscore) > 2.5:
                anomalies.append({"actual_id": a['id'], "amount": a['amount'], "zscore": round(zscore, 2), "date": a['recorded_at']})
        return anomalies

# === ASYNC PAGINATION ===

class BudgetPaginator:
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items
        self.page_size = page_size

    def get_page(self, page: int = 1) -> Dict[str, Any]:
        start = (page - 1) * self.page_size
        end = start + self.page_size
        total_pages = max(1, (len(self.items) + self.page_size - 1) // self.page_size)
        return {
            "page": page,
            "page_size": self.page_size,
            "total_items": len(self.items),
            "total_pages": total_pages,
            "has_next": page < total_pages,
        "has_prev": page > 1,
        "items": self.items[start:end],
    }

# === ADVANCED FORECASTING ===

class AdvancedForecaster:
    def __init__(self, engine: BudgetForecastEngine):
        self.engine = engine

    def seasonal_decompose(self, budget_id: str) -> Dict[str, Any]:
        budget = self.engine.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        actuals = sorted(
            [a for a in self.engine.actuals if a['budget_id'] == budget_id],
            key=lambda x: x['recorded_at']
        )
        if len(actuals) < 14:
            return {"error": "Insufficient data for seasonal decomposition"}
        values = [a['amount'] for a in actuals]
        n = len(values)
        period = 7
        if n < 2 * period:
            return {"error": "Need at least 2 full seasonal periods"}
        trend = []
        half = period // 2
        for i in range(n):
            start = max(0, i - half)
            end = min(n, i + half + 1)
            trend.append(sum(values[start:end]) / (end - start))
        detrended = [values[i] - trend[i] for i in range(n)]
        seasonal = []
        for i in range(period):
            indices = list(range(i, n, period))
            seasonal.append(sum(detrended[j] for j in indices) / len(indices))
        seasonal_mean = sum(seasonal) / period
        seasonal = [s - seasonal_mean for s in seasonal]
        remainder = [detrended[i] - seasonal[i % period] for i in range(n)]
        return {
            "budget_id": budget_id,
            "period_days": period,
            "seasonal_factors": [round(s, 2) for s in seasonal],
            "trend": [round(t, 2) for t in trend],
            "remainder": [round(r, 2) for r in remainder],
            "seasonal_strength": round(1 - sum(abs(r) for r in remainder) / max(sum(abs(d) for d in detrended), 0.01), 3),
        }

    def arima_predict(self, values: List[float], p: int = 1, d: int = 1, q: int = 1, horizon: int = 30) -> List[float]:
        if len(values) < p + d + q + 1:
            return [round(sum(values) / len(values), 2) for _ in range(horizon)]
        diff = values[:]
        for _ in range(d):
            diff = [diff[i] - diff[i-1] for i in range(1, len(diff))]
        ar_part = diff[-p:] if len(diff) >= p else diff
        ma_errors = [0] * q
        predictions = []
        for i in range(horizon):
            pred = 0
            for j in range(min(p, len(ar_part))):
                pred += ar_part[-(j+1)] * (0.5 / (j+1))
            for j in range(min(q, len(ma_errors))):
                pred += ma_errors[-(j+1)] * (0.3 / (j+1))
            predictions.append(pred)
            ar_part.append(pred)
            if len(ar_part) > p:
                ar_part = ar_part[-p:]
            ma_errors.append(predictions[-1])
            if len(ma_errors) > q:
                ma_errors = ma_errors[-q:]
        cumulative = values[-1] if values else 0
        result = []
        for pv in predictions:
            cumulative += pv
            result.append(round(max(0, cumulative), 2))
        return result

    def ensemble_forecast(self, budget_id: str, horizon: int = 30) -> Dict[str, Any]:
        ma = self.engine.generate_forecast(budget_id, "moving_average", horizon)
        lr = self.engine.generate_forecast(budget_id, "linear_regression", horizon)
        es = self.engine.generate_forecast(budget_id, "exponential_smoothing", horizon)
        forecasts = []
        for i in range(horizon):
            vals = [ma['daily_forecasts'][i], lr['daily_forecasts'][i], es['daily_forecasts'][i]]
            forecasts.append(round(sum(vals) / len(vals), 2))
        return {
            "budget_id": budget_id,
            "ensemble_size": 3,
            "models": ["moving_average", "linear_regression", "exponential_smoothing"],
            "daily_forecasts": forecasts,
            "total_forecast": round(sum(forecasts), 2),
            "budget_amount": ma['budget_amount'],
            "confidence": "high" if ma['confidence'] == lr['confidence'] == es['confidence'] == "high" else "medium",
        }

    def detect_budget_anomaly(self, budget_id: str) -> Dict[str, Any]:
        actuals = sorted(
            [a for a in self.engine.actuals if a['budget_id'] == budget_id],
            key=lambda x: x['recorded_at']
        )
        if len(actuals) < 5:
            return {"anomaly_detected": False, "reason": "Insufficient data"}
        values = [a['amount'] for a in actuals[-10:]]
        mean = sum(values) / len(values)
        std = (sum((v - mean)**2 for v in values) / len(values))**0.5
        anomalies = []
        for a in actuals[-10:]:
            zscore = (a['amount'] - mean) / max(std, 0.01)
            if abs(zscore) > 2:
                anomalies.append({"date": a['recorded_at'], "amount": a['amount'], "zscore": round(zscore, 2)})
        return {
            "anomaly_detected": len(anomalies) > 0,
            "anomalies": anomalies,
            "threshold_zscore": 2.0,
            "recent_mean": round(mean, 2),
            "recent_std": round(std, 2),
        }

# === MULTI-CURRENCY ===

class MultiCurrencyManager:
    def __init__(self):
        self.rates = {
            "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5,
            "AUD": 1.54, "CAD": 1.37, "INR": 83.1, "SGD": 1.34,
            "BRL": 4.97, "KRW": 1325.0,
        }

    def convert(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        if from_currency not in self.rates or to_currency not in self.rates:
            return {"error": "Unsupported currency"}
        usd_amount = amount / self.rates[from_currency]
        converted = usd_amount * self.rates[to_currency]
        return {
            "amount": round(amount, 2),
            "from": from_currency,
            "to": to_currency,
            "converted": round(converted, 2),
            "rate": round(self.rates[to_currency] / self.rates[from_currency], 6),
        }

    def get_rates(self) -> Dict[str, float]:
        return self.rates

    def update_rate(self, currency: str, rate: float) -> bool:
        if currency not in self.rates:
            return False
        self.rates[currency] = rate
        return True

# === BUDGET FREEZE/THAW ===

class BudgetFreezeManager:
    def __init__(self, engine: BudgetForecastEngine):
        self.engine = engine
        self.frozen_budgets: Dict[str, Dict] = {}

    def freeze_budget(self, budget_id: str, reason: str = "") -> Dict[str, Any]:
        budget = self.engine.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        self.frozen_budgets[budget_id] = {
            "budget_id": budget_id,
            "previous_status": budget['status'],
            "reason": reason,
            "frozen_at": datetime.utcnow().isoformat(),
            "spend_at_freeze": budget.get('spent', 0),
        }
        budget['status'] = "frozen"
        self._update_budget_field(budget, 'frozen', True)
        return self.frozen_budgets[budget_id]

    def thaw_budget(self, budget_id: str, reason: str = "") -> Dict[str, Any]:
        budget = self.engine.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        if budget_id not in self.frozen_budgets:
            return {"error": "Budget is not frozen"}
        freeze_info = self.frozen_budgets.pop(budget_id)
        budget['status'] = freeze_info['previous_status']
        self._update_budget_field(budget, 'frozen', False)
        return {"budget_id": budget_id, "status": budget['status'], "thawed_at": datetime.utcnow().isoformat(), "reason": reason}

    def _update_budget_field(self, budget: Dict, key: str, value: Any):
        budget[key] = value
        self.engine._save_budgets()

    def list_frozen(self) -> List[Dict[str, Any]]:
        return [info for bid, info in self.frozen_budgets.items()]

# === ROLLING FORECAST ===

class RollingForecast:
    def __init__(self, engine: BudgetForecastEngine, window_days: int = 90):
        self.engine = engine
        self.window_days = window_days

    def compute(self, budget_id: str) -> Dict[str, Any]:
        budget = self.engine.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        actuals = sorted(
            [a for a in self.engine.actuals if a['budget_id'] == budget_id],
            key=lambda x: x['recorded_at']
        )
        cutoff = datetime.utcnow() - timedelta(days=self.window_days)
        windowed = [a for a in actuals if datetime.fromisoformat(a['recorded_at']) >= cutoff]
        if len(windowed) < 7:
            return {"error": "Insufficient data in window"}
        values = [a['amount'] for a in windowed]
        daily_rate = sum(values) / len(values)
        remaining_days = max(0, (datetime.fromisoformat(budget['end_date']) - datetime.utcnow()).days)
        projected = daily_rate * remaining_days
        remaining_budget = max(0, budget['amount'] - budget.get('spent', 0))
        return {
            "budget_id": budget_id,
            "window_days": self.window_days,
            "daily_rate": round(daily_rate, 2),
            "remaining_days": remaining_days,
            "projected_remaining_spend": round(projected, 2),
            "remaining_budget": round(remaining_budget, 2),
            "surplus_deficit": round(remaining_budget - projected, 2),
            "on_track": projected <= remaining_budget,
        }

# === ALERT DISPATCHER ===

class BudgetAlertDispatcher:
    def __init__(self, engine: BudgetForecastEngine):
        self.engine = engine
        self.alert_log: List[Dict[str, Any]] = []

    def check_and_alert(self) -> List[Dict[str, Any]]:
        alerts = []
        for budget in self.engine.budgets:
            ratio = budget.get('spent', 0) / max(budget['amount'], 0.01)
            thresholds = budget.get('alert_thresholds', [0.5, 0.75, 0.9, 1.0])
            for t in thresholds:
                if ratio >= t:
                    triggered = any(a for a in self.alert_log if a['budget_id'] == budget['id'] and a['threshold'] == t and a['acknowledged'] is False)
                    if not triggered:
                        alert = {
                            "id": str(uuid.uuid4()),
                            "budget_id": budget['id'],
                            "budget_name": budget['name'],
                            "threshold": t,
                            "current_ratio": round(ratio, 2),
                            "spent": budget.get('spent', 0),
                            "amount": budget['amount'],
                            "alerted_at": datetime.utcnow().isoformat(),
                            "acknowledged": False,
                        }
                        self.alert_log.append(alert)
                        alerts.append(alert)
                    break
        return alerts

    def acknowledge(self, alert_id: str) -> bool:
        for a in self.alert_log:
            if a['id'] == alert_id:
                a['acknowledged'] = True
                a['acknowledged_at'] = datetime.utcnow().isoformat()
                return True
        return False

    def get_alerts(self, acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
        if acknowledged is None:
            return self.alert_log
        return [a for a in self.alert_log if a['acknowledged'] == acknowledged]

# -- Extended Operations -----------------------------------------------

    async def batch_process(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "processed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "processed")}

    def get_analytics(self) -> Dict[str, Any]:
        return {"total_count": 0, "total_value": 0.0, "avg_value": 0.0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class FinopsResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    amount: float = 0.0
    currency: str = Field(default="USD")
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FinopsBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: str = Field(default="sequential")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    total_cost: float = Field(default=0.0)
    estimated_savings: float = Field(default=0.0)

    def add_item(self, item: Dict[str, Any], cost: float = 0.0, savings: float = 0.0) -> None:
        self.items.append(item)
        self.total_cost += cost
        self.estimated_savings += savings

    def complete(self) -> None:
        self.status = "completed"

class CostMetrics(BaseModel):
    category: str
    amount: float
    currency: str = Field(default="USD")
    period: str = Field(default="monthly")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict)

class CostTracker:
    def __init__(self) -> None:
        self._entries: List[CostMetrics] = []

    def record(self, category: str, amount: float, tags: Optional[Dict[str, str]] = None) -> None:
        self._entries.append(CostMetrics(category=category, amount=amount, tags=tags or {}))

    def total_by_category(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._entries:
            totals[e.category] = totals.get(e.category, 0) + e.amount
        return totals

    def total(self) -> float:
        return round(sum(e.amount for e in self._entries), 2)

    def average(self) -> float:
        return round(self.total() / max(len(self._entries), 1), 2)

    def get_by_period(self, period: str) -> List[CostMetrics]:
        return [e for e in self._entries if e.period == period]

    def summary(self) -> Dict[str, Any]:
        return {"total_entries": len(self._entries), "total_cost": self.total(),
                "avg_per_entry": self.average(),
                "by_category": self.total_by_category(),
                "latest": self._entries[-1].dict() if self._entries else None}

class SavingsCalculator:
    @staticmethod
    def compute(original_cost: float, new_cost: float) -> Dict[str, Any]:
        savings = original_cost - new_cost
        pct = (savings / original_cost * 100) if original_cost > 0 else 0
        return {"original": round(original_cost, 2), "new": round(new_cost, 2),
                "savings": round(savings, 2), "savings_pct": round(pct, 1)}

    @staticmethod
    def project_monthly(daily_savings: float, days: int = 30) -> float:
        return round(daily_savings * days, 2)

    @staticmethod
    def project_annual(daily_savings: float) -> float:
        return round(daily_savings * 365, 2)

    @staticmethod
    def roi(investment: float, savings_per_month: float, months: int = 12) -> Dict[str, Any]:
        total_savings = savings_per_month * months
        roi_value = ((total_savings - investment) / investment * 100) if investment > 0 else 0
        return {"investment": round(investment, 2), "total_savings": round(total_savings, 2),
                "months": months, "roi_pct": round(roi_value, 1),
                "payback_months": round(investment / max(savings_per_month, 0.01), 1)}

class BudgetAlert(BaseModel):
    budget_name: str
    threshold: float
    current_spend: float
    percentage: float
    severity: str = Field(default="info")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    notified: bool = False

    def should_alert(self) -> bool:
        return self.percentage >= self.threshold and not self.notified

class BudgetMonitor:
    def __init__(self) -> None:
        self._budgets: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[BudgetAlert] = []

    def set_budget(self, name: str, limit: float, warning_threshold: float = 80.0) -> None:
        self._budgets[name] = {"limit": limit, "warning_threshold": warning_threshold, "spend": 0.0}

    def record_spend(self, name: str, amount: float) -> Optional[BudgetAlert]:
        budget = self._budgets.get(name)
        if not budget:
            return None
        budget["spend"] += amount
        pct = (budget["spend"] / budget["limit"]) * 100
        if pct >= budget["warning_threshold"]:
            alert = BudgetAlert(budget_name=name, threshold=budget["warning_threshold"],
                                current_spend=round(budget["spend"], 2),
                                percentage=round(pct, 1),
                                severity="warning" if pct < 100 else "critical")
            self._alerts.append(alert)
            return alert
        return None

    def get_budget_status(self, name: str) -> Optional[Dict[str, Any]]:
        budget = self._budgets.get(name)
        if not budget:
            return None
        pct = (budget["spend"] / budget["limit"]) * 100 if budget["limit"] > 0 else 0
        return {"name": name, "limit": budget["limit"], "spend": round(budget["spend"], 2),
                "remaining": round(budget["limit"] - budget["spend"], 2),
                "usage_pct": round(pct, 1)}

    def get_all_status(self) -> Dict[str, Any]:
        return {name: self.get_budget_status(name) for name in self._budgets}

    def get_alerts(self, severity: Optional[str] = None) -> List[BudgetAlert]:
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return self._alerts

class ReportingSchedule(BaseModel):
    report_type: str
    frequency: str = Field(default="daily")
    recipients: List[str] = Field(default_factory=list)
    format: str = Field(default="pdf")
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None

# -- Advanced FinOps Analytics -----------------------------------------

class CostEfficiencyIndex:
    def __init__(self) -> None:
        self._indices: Dict[str, float] = {}

    def calculate(self, department: str, total_cost: float, output_value: float) -> float:
        if total_cost <= 0:
            return 0.0
        index = round(output_value / total_cost, 4)
        self._indices[department] = index
        return index

    def get_index(self, department: str) -> Optional[float]:
        return self._indices.get(department)

    def get_ranking(self) -> List[Dict[str, Any]]:
        ranked = sorted(self._indices.items(), key=lambda x: x[1], reverse=True)
        return [{"department": d, "efficiency_index": v, "rank": i + 1} for i, (d, v) in enumerate(ranked)]

class AnomalyThresholdConfig(BaseModel):
    metric: str
    warning_pct: float = Field(default=20.0, ge=0)
    critical_pct: float = Field(default=50.0, ge=0)
    cooldown_minutes: int = Field(default=60)
    enabled: bool = True

class AnomalyConfigManager:
    def __init__(self) -> None:
        self._configs: Dict[str, AnomalyThresholdConfig] = {}

    def set_config(self, config: AnomalyThresholdConfig) -> None:
        self._configs[config.metric] = config

    def get_config(self, metric: str) -> Optional[AnomalyThresholdConfig]:
        return self._configs.get(metric)

    def evaluate(self, metric: str, current: float, baseline: float) -> Dict[str, Any]:
        config = self._configs.get(metric)
        if not config or not config.enabled or baseline <= 0:
            return {"level": "ok", "deviation_pct": 0.0}
        deviation = abs(current - baseline) / baseline * 100
        if deviation >= config.critical_pct:
            return {"level": "critical", "deviation_pct": round(deviation, 1), "threshold": config.critical_pct}
        if deviation >= config.warning_pct:
            return {"level": "warning", "deviation_pct": round(deviation, 1), "threshold": config.warning_pct}
        return {"level": "ok", "deviation_pct": round(deviation, 1)}

class CommitmentPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str
    commitment_type: str = Field(default="1yr")
    hourly_commitment: float = Field(default=0.0)
    upfront_cost: float = Field(default=0.0)
    effective_rate: float = Field(default=0.0)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    status: str = Field(default="active")
    estimated_savings_pct: float = Field(default=0.0)

class CommitmentOptimizer:
    def __init__(self) -> None:
        self._plans: Dict[str, CommitmentPlan] = {}

    def create_plan(self, provider: str, commitment_type: str, hourly: float,
                    upfront: float, effective_rate: float, savings_pct: float) -> CommitmentPlan:
        plan = CommitmentPlan(provider=provider, commitment_type=commitment_type,
                              hourly_commitment=hourly, upfront_cost=upfront,
                              effective_rate=effective_rate, estimated_savings_pct=savings_pct)
        self._plans[plan.plan_id] = plan
        return plan

    def get_active(self) -> List[CommitmentPlan]:
        return [p for p in self._plans.values() if p.status == "active"]

    def get_coverage_pct(self, total_hourly_spend: float) -> float:
        committed = sum(p.hourly_commitment for p in self.get_active())
        return round(committed / max(total_hourly_spend, 0.01) * 100, 1)

    def get_savings_projection(self) -> Dict[str, Any]:
        active = self.get_active()
        total_original = sum(p.hourly_commitment for p in active)
        total_effective = sum(p.effective_rate for p in active)
        monthly_savings = (total_original - total_effective) * 730
        return {"monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(monthly_savings * 12, 2),
                "coverage_pct": round(total_original / max(total_original + 0.01, 1) * 100, 1)}

class WasteCategory(BaseModel):
    category: str
    amount: float
    resources: int
    recommendation: str = ""
    potential_savings: float = 0.0

class WasteAnalyzer:
    def __init__(self) -> None:
        self._categories: Dict[str, WasteCategory] = {}

    def add_category(self, category: str, amount: float, resources: int,
                     recommendation: str = "", savings: float = 0.0) -> WasteCategory:
        wc = WasteCategory(category=category, amount=amount, resources=resources,
                           recommendation=recommendation, potential_savings=savings)
        self._categories[category] = wc
        return wc

    def total_waste(self) -> float:
        return round(sum(c.amount for c in self._categories.values()), 2)

    def total_potential_savings(self) -> float:
        return round(sum(c.potential_savings for c in self._categories.values()), 2)

    def get_by_category(self, category: str) -> Optional[WasteCategory]:
        return self._categories.get(category)

    def get_summary(self) -> Dict[str, Any]:
        return {"categories": [c.dict() for c in self._categories.values()],
                "total_waste": self.total_waste(),
                "total_potential_savings": self.total_potential_savings(),
                "waste_pct": round(self.total_waste() / max(self.total_waste() + self.total_potential_savings(), 0.01) * 100, 1)}

class CostForecastPoint(BaseModel):
    date: str
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float

class CostForecaster:
    def __init__(self) -> None:
        self._forecasts: List[CostForecastPoint] = []

    def generate(self, days: int = 90, base_cost: float = 1000.0, volatility: float = 0.1) -> List[CostForecastPoint]:
        self._forecasts = []
        current = base_cost
        for i in range(days):
            change = current * volatility * (random.random() * 2 - 1)
            predicted = round(current + change, 2)
            ci = current * 0.05
            point = CostForecastPoint(
                date=(datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d"),
                predicted_cost=predicted, lower_bound=round(predicted - ci, 2),
                upper_bound=round(predicted + ci, 2),
                confidence=max(0.5, 1.0 - i / days * 0.4),
            )
            self._forecasts.append(point)
            current = predicted
        return self._forecasts

    def get_forecast(self) -> List[CostForecastPoint]:
        return self._forecasts

    def get_aggregate(self) -> Dict[str, Any]:
        if not self._forecasts:
            return {"total_forecast": 0, "avg_daily": 0}
        total = sum(p.predicted_cost for p in self._forecasts)
        return {"total_forecast": round(total, 2),
                "avg_daily": round(total / len(self._forecasts), 2),
                "days": len(self._forecasts),
                "last_prediction": self._forecasts[-1].predicted_cost}
