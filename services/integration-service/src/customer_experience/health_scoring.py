"""Customer health scoring with composite score calculation and churn prediction."""

import json
import logging
import math
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HealthCategory(str, Enum):
    USAGE = "usage"
    BILLING = "billing"
    SUPPORT = "support"
    UPTIME = "uptime"
    SENTIMENT = "sentiment"
    ADOPTION = "adoption"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    HEALTHY = "healthy"


@dataclass
class ScoreComponent:
    category: HealthCategory
    score: float
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)
    trend: str = "stable"
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CustomerHealthProfile:
    customer_id: str
    composite_score: float
    components: List[ScoreComponent]
    risk_level: RiskLevel
    churn_probability: float
    trend: str
    last_updated: str
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "composite_score": self.composite_score,
            "components": [c.to_dict() for c in self.components],
            "risk_level": self.risk_level.value,
            "churn_probability": self.churn_probability,
            "trend": self.trend,
            "last_updated": self.last_updated,
            "alerts": self.alerts,
            "recommendations": self.recommendations,
        }


class HealthScoringService:
    def __init__(self, storage_path: str = "health_scores.json"):
        self.storage_path = storage_path
        self.profiles: Dict[str, CustomerHealthProfile] = {}
        self.history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.weights: Dict[str, float] = {
            "usage": 0.20,
            "billing": 0.20,
            "support": 0.20,
            "uptime": 0.15,
            "sentiment": 0.10,
            "adoption": 0.15,
        }
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for cid, pdata in data.get("profiles", {}).items():
                        comps = []
                        for c in pdata.get("components", []):
                            comps.append(ScoreComponent(
                                category=HealthCategory(c["category"]),
                                score=c["score"],
                                weight=c["weight"],
                                details=c.get("details", {}),
                                trend=c.get("trend", "stable"),
                                last_updated=c.get("last_updated", ""),
                            ))
                        self.profiles[cid] = CustomerHealthProfile(
                            customer_id=cid,
                            composite_score=pdata.get("composite_score", 0),
                            components=comps,
                            risk_level=RiskLevel(pdata.get("risk_level", "medium")),
                            churn_probability=pdata.get("churn_probability", 0),
                            trend=pdata.get("trend", "stable"),
                            last_updated=pdata.get("last_updated", ""),
                            alerts=pdata.get("alerts", []),
                            recommendations=pdata.get("recommendations", []),
                        )
                    self.history = defaultdict(list, data.get("history", {}))
            except Exception as e:
                logger.warning(f"Failed to load health scores: {e}")

    def _save_data(self):
        try:
            data = {
                "profiles": {cid: p.to_dict() for cid, p in self.profiles.items()},
                "history": dict(self.history),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health scores: {e}")

    def _calculate_risk_level(self, score: float) -> RiskLevel:
        if score >= 85:
            return RiskLevel.HEALTHY
        elif score >= 70:
            return RiskLevel.LOW
        elif score >= 50:
            return RiskLevel.MEDIUM
        elif score >= 30:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _calculate_churn_probability(self, score: float, trend: str) -> float:
        base = max(0, min(1, (85 - score) / 85))
        trend_modifier = {"declining": 0.15, "stable": 0, "improving": -0.10}
        return max(0, min(1, base + trend_modifier.get(trend, 0)))

    def _calculate_trend(self, customer_id: str, current_score: float) -> str:
        hist = self.history.get(customer_id, [])
        if len(hist) < 2:
            return "stable"
        recent = [h["composite_score"] for h in hist[-3:]]
        if len(recent) < 2:
            return "stable"
        avg_old = sum(recent[:-1]) / len(recent[:-1])
        if current_score > avg_old + 2:
            return "improving"
        elif current_score < avg_old - 2:
            return "declining"
        return "stable"

    def compute_usage_score(self, customer_id: str, usage_data: Dict[str, Any]) -> ScoreComponent:
        active_users = usage_data.get("active_users", 0)
        total_users = max(usage_data.get("total_users", 1), 1)
        login_frequency = usage_data.get("login_frequency", 0)
        sessions_per_week = usage_data.get("sessions_per_week", 0)
        feature_count = usage_data.get("features_used", 0)
        total_features = max(usage_data.get("total_features", 1), 1)
        engagement_ratio = active_users / total_users
        feature_adoption = feature_count / total_features
        login_score = min(1, login_frequency / 30)
        session_score = min(1, sessions_per_week / 10)
        score = round((
            engagement_ratio * 0.30 +
            feature_adoption * 0.30 +
            login_score * 0.20 +
            session_score * 0.20
        ) * 100, 1)
        details = {
            "active_users": active_users,
            "total_users": total_users,
            "engagement_ratio": round(engagement_ratio, 3),
            "feature_adoption": round(feature_adoption, 3),
            "login_frequency": login_frequency,
            "sessions_per_week": sessions_per_week,
        }
        return ScoreComponent(
            category=HealthCategory.USAGE,
            score=score,
            weight=self.weights["usage"],
            details=details,
        )

    def compute_billing_score(self, customer_id: str, billing_data: Dict[str, Any]) -> ScoreComponent:
        invoice_paid = billing_data.get("invoices_paid_on_time", 0)
        invoice_total = max(billing_data.get("invoices_total", 1), 1)
        payment_method_valid = billing_data.get("payment_method_valid", True)
        credit_remaining = billing_data.get("credit_remaining", 0)
        monthly_spend = billing_data.get("monthly_spend", 0)
        spend_trend = billing_data.get("spend_trend", "stable")
        payment_reliability = invoice_paid / invoice_total
        credit_score = min(1, credit_remaining / max(monthly_spend * 2, 1))
        trend_penalty = 0 if spend_trend == "growing" else (0.1 if spend_trend == "stable" else 0.2)
        score = round((
            payment_reliability * 0.40 +
            (1 if payment_method_valid else 0) * 0.25 +
            credit_score * 0.20 -
            trend_penalty
        ) * 100, 1)
        score = max(0, min(100, score))
        details = {
            "invoices_paid_on_time": invoice_paid,
            "invoices_total": invoice_total,
            "payment_reliability": round(payment_reliability, 3),
            "payment_method_valid": payment_method_valid,
            "credit_remaining": credit_remaining,
            "monthly_spend": monthly_spend,
            "spend_trend": spend_trend,
        }
        return ScoreComponent(
            category=HealthCategory.BILLING,
            score=score,
            weight=self.weights["billing"],
            details=details,
        )

    def compute_support_score(self, customer_id: str, support_data: Dict[str, Any]) -> ScoreComponent:
        tickets_open = support_data.get("open_tickets", 0)
        tickets_resolved = support_data.get("resolved_tickets", 0)
        tickets_total = max(support_data.get("total_tickets", 1), 1)
        avg_response_time = support_data.get("avg_response_time_hours", 0)
        avg_resolution_time = support_data.get("avg_resolution_time_hours", 0)
        satisfaction = support_data.get("satisfaction_score", 5)
        resolution_rate = tickets_resolved / tickets_total
        response_penalty = max(0, min(1, (avg_response_time - 1) / 48))
        resolution_penalty = max(0, min(1, (avg_resolution_time - 4) / 72))
        satisfaction_score = satisfaction / 5
        open_penalty = min(1, tickets_open / 10)
        score = round((
            resolution_rate * 0.25 +
            satisfaction_score * 0.30 +
            (1 - response_penalty) * 0.20 +
            (1 - resolution_penalty) * 0.15 -
            open_penalty * 0.10
        ) * 100, 1)
        score = max(0, min(100, score))
        details = {
            "open_tickets": tickets_open,
            "resolved_tickets": tickets_resolved,
            "total_tickets": tickets_total,
            "resolution_rate": round(resolution_rate, 3),
            "avg_response_time_hours": avg_response_time,
            "avg_resolution_time_hours": avg_resolution_time,
            "satisfaction_score": satisfaction,
        }
        return ScoreComponent(
            category=HealthCategory.SUPPORT,
            score=score,
            weight=self.weights["support"],
            details=details,
        )

    def compute_uptime_score(self, customer_id: str, uptime_data: Dict[str, Any]) -> ScoreComponent:
        uptime_pct = uptime_data.get("uptime_percentage", 99.9)
        incidents = uptime_data.get("incidents_last_30d", 0)
        total_incidents = uptime_data.get("total_incidents", 0)
        mttr_minutes = uptime_data.get("mttr_minutes", 30)
        sla_breaches = uptime_data.get("sla_breaches", 0)
        uptime_score = uptime_pct / 100
        incident_penalty = min(1, incidents * 0.05)
        mttr_penalty = max(0, min(1, (mttr_minutes - 5) / 120))
        breach_penalty = min(1, sla_breaches * 0.15)
        score = round((
            uptime_score * 0.40 +
            (1 - incident_penalty) * 0.25 +
            (1 - mttr_penalty) * 0.20 +
            (1 - breach_penalty) * 0.15
        ) * 100, 1)
        score = max(0, min(100, score))
        details = {
            "uptime_percentage": uptime_pct,
            "incidents_last_30d": incidents,
            "total_incidents": total_incidents,
            "mttr_minutes": mttr_minutes,
            "sla_breaches": sla_breaches,
        }
        return ScoreComponent(
            category=HealthCategory.UPTIME,
            score=score,
            weight=self.weights["uptime"],
            details=details,
        )

    def compute_sentiment_score(self, customer_id: str, sentiment_data: Dict[str, Any]) -> ScoreComponent:
        avg_sentiment = sentiment_data.get("average_sentiment", 0.5)
        negative_interactions = sentiment_data.get("negative_interactions", 0)
        total_interactions = max(sentiment_data.get("total_interactions", 1), 1)
        sentiment_trend = sentiment_data.get("sentiment_trend", "neutral")
        negative_ratio = negative_interactions / total_interactions
        trend_bonus = 0.05 if sentiment_trend == "improving" else (-0.05 if sentiment_trend == "declining" else 0)
        score = round((avg_sentiment * 0.60 + (1 - negative_ratio) * 0.30 + trend_bonus) * 100, 1)
        score = max(0, min(100, score))
        details = {
            "average_sentiment": avg_sentiment,
            "negative_interactions": negative_interactions,
            "total_interactions": total_interactions,
            "negative_ratio": round(negative_ratio, 3),
            "sentiment_trend": sentiment_trend,
        }
        return ScoreComponent(
            category=HealthCategory.SENTIMENT,
            score=score,
            weight=self.weights["sentiment"],
            details=details,
        )

    def compute_adoption_score(self, customer_id: str, adoption_data: Dict[str, Any]) -> ScoreComponent:
        features_adopted = adoption_data.get("features_adopted", 0)
        total_features = max(adoption_data.get("total_features", 1), 1)
        onboarding_complete = adoption_data.get("onboarding_complete", False)
        time_to_value_days = adoption_data.get("time_to_value_days", 30)
        power_users = adoption_data.get("power_users", 0)
        total_users = max(adoption_data.get("total_users", 1), 1)
        adoption_rate = features_adopted / total_features
        power_ratio = power_users / total_users
        ttv_score = max(0, min(1, 1 - (time_to_value_days / 90)))
        score = round((
            adoption_rate * 0.35 +
            (1 if onboarding_complete else 0.3) * 0.25 +
            ttv_score * 0.20 +
            power_ratio * 0.20
        ) * 100, 1)
        score = max(0, min(100, score))
        details = {
            "features_adopted": features_adopted,
            "total_features": total_features,
            "adoption_rate": round(adoption_rate, 3),
            "onboarding_complete": onboarding_complete,
            "time_to_value_days": time_to_value_days,
            "power_users": power_users,
            "power_ratio": round(power_ratio, 3),
        }
        return ScoreComponent(
            category=HealthCategory.ADOPTION,
            score=score,
            weight=self.weights["adoption"],
            details=details,
        )

    def compute_health_score(
        self,
        customer_id: str,
        usage_data: Dict[str, Any],
        billing_data: Dict[str, Any],
        support_data: Dict[str, Any],
        uptime_data: Optional[Dict[str, Any]] = None,
        sentiment_data: Optional[Dict[str, Any]] = None,
        adoption_data: Optional[Dict[str, Any]] = None,
    ) -> CustomerHealthProfile:
        components = []
        components.append(self.compute_usage_score(customer_id, usage_data))
        components.append(self.compute_billing_score(customer_id, billing_data))
        components.append(self.compute_support_score(customer_id, support_data))
        if uptime_data:
            components.append(self.compute_uptime_score(customer_id, uptime_data))
        if sentiment_data:
            components.append(self.compute_sentiment_score(customer_id, sentiment_data))
        if adoption_data:
            components.append(self.compute_adoption_score(customer_id, adoption_data))
        total_weight = sum(c.weight for c in components)
        composite = sum(c.score * c.weight for c in components) / total_weight if total_weight > 0 else 0
        composite = round(composite, 1)
        trend = self._calculate_trend(customer_id, composite)
        risk_level = self._calculate_risk_level(composite)
        churn_prob = self._calculate_churn_probability(composite, trend)

        if customer_id not in self.history:
            self.history[customer_id] = []
        self.history[customer_id].append({
            "composite_score": composite,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": risk_level.value,
        })
        if len(self.history[customer_id]) > 90:
            self.history[customer_id] = self.history[customer_id][-90:]

        alerts = []
        recommendations = []
        for comp in components:
            if comp.score < 40:
                alerts.append({
                    "type": "critical_score",
                    "category": comp.category.value,
                    "score": comp.score,
                    "message": f"{comp.category.value} score critically low ({comp.score})",
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif comp.score < 60:
                alerts.append({
                    "type": "warning_score",
                    "category": comp.category.value,
                    "score": comp.score,
                    "message": f"{comp.category.value} score below threshold ({comp.score})",
                    "timestamp": datetime.utcnow().isoformat(),
                })

        if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            recommendations.append("Schedule executive check-in call")
            recommendations.append("Review support ticket backlog and prioritize")
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("Escalate to customer success manager immediately")
            recommendations.append("Offer discount or service credit to retain")
        if churn_prob > 0.5:
            recommendations.append("Proactive outreach with personalized retention offer")

        profile = CustomerHealthProfile(
            customer_id=customer_id,
            composite_score=composite,
            components=components,
            risk_level=risk_level,
            churn_probability=round(churn_prob, 3),
            trend=trend,
            last_updated=datetime.utcnow().isoformat(),
            alerts=alerts,
            recommendations=recommendations,
        )
        self.profiles[customer_id] = profile
        self._save_data()
        return profile

    def get_health_profile(self, customer_id: str) -> Optional[CustomerHealthProfile]:
        return self.profiles.get(customer_id)

    def list_health_profiles(
        self, risk_level: Optional[str] = None, min_score: Optional[float] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        results = []
        for cid, profile in self.profiles.items():
            if risk_level and profile.risk_level.value != risk_level:
                continue
            if min_score is not None and profile.composite_score < min_score:
                continue
            results.append(profile.to_dict())
            if len(results) >= limit:
                break
        return results

    def get_health_history(self, customer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return [h for h in self.history.get(customer_id, []) if h["timestamp"] >= cutoff]

    def update_weights(self, new_weights: Dict[str, float]) -> Dict[str, float]:
        for key, value in new_weights.items():
            if key in self.weights:
                self.weights[key] = value
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            self.weights = {k: v / total for k, v in self.weights.items()}
        self._save_data()
        return dict(self.weights)

    def get_segment_summary(self) -> Dict[str, Any]:
        if not self.profiles:
            return {"total_customers": 0, "average_score": 0, "segments": {}}
        scores = [p.composite_score for p in self.profiles.values()]
        avg_score = sum(scores) / len(scores)
        segments = defaultdict(int)
        for p in self.profiles.values():
            segments[p.risk_level.value] += 1
        return {
            "total_customers": len(self.profiles),
            "average_score": round(avg_score, 1),
            "segments": dict(segments),
            "at_risk_count": sum(
                1 for p in self.profiles.values()
                if p.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
            ),
        }

    def get_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        p = self.profiles.get(customer_id)
        return p.to_dict() if p else None

    def update_profile(self, customer_id: str, updates: Dict[str, Any]) -> bool:
        p = self.profiles.get(customer_id)
        if not p:
            return False
        for key, val in updates.items():
            if hasattr(p, key):
                setattr(p, key, val)
        p.last_updated = datetime.utcnow()
        self._recalculate_risk(p)
        self._save_data()
        return True

    def _recalculate_risk(self, profile: CustomerProfile) -> None:
        total = profile.recent_negative_count + profile.recent_positive_count + profile.recent_neutral_count or 1
        neg_ratio = profile.recent_negative_count / total
        if neg_ratio > 0.4 and profile.recent_negative_count > 5:
            profile.risk_level = RiskLevel.CRITICAL
        elif neg_ratio > 0.25 and profile.recent_negative_count > 3:
            profile.risk_level = RiskLevel.HIGH
        elif neg_ratio > 0.15:
            profile.risk_level = RiskLevel.MEDIUM
        else:
            profile.risk_level = RiskLevel.LOW

    def get_risk_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        trend_data = defaultdict(int)
        for p in self.profiles.values():
            if p.last_updated >= cutoff:
                trend_data[p.risk_level.value] += 1
        return {"period_days": days, "breakdown": dict(trend_data), "total_profiles": len(self.profiles)}

    def get_health_distribution(self) -> Dict[str, Any]:
        buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for p in self.profiles.values():
            score = p.overall_health_score or p.calculate_health_score(self.events.get(p.customer_id, []), self.tickets.get(p.customer_id, []))
            if score <= 20: buckets["0-20"] += 1
            elif score <= 40: buckets["21-40"] += 1
            elif score <= 60: buckets["41-60"] += 1
            elif score <= 80: buckets["61-80"] += 1
            else: buckets["81-100"] += 1
        return {"buckets": buckets, "total": len(self.profiles)}

    def search_profiles(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [p.to_dict() for p in self.profiles.values() if q in p.customer_name.lower() or q in p.customer_id.lower()]
        return results[:20]

    def get_at_risk_profiles(self, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
        profiles = [p for p in self.profiles.values() if p.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)]
        if risk_level:
            profiles = [p for p in profiles if p.risk_level.value == risk_level]
        profiles.sort(key=lambda p: p.overall_health_score or 100)
        return [p.to_dict() for p in profiles[:30]]

    def batch_update_health(self, customer_ids: List[str], events_data: Dict[str, List], tickets_data: Dict[str, List]) -> int:
        count = 0
        for cid in customer_ids:
            p = self.profiles.get(cid)
            if p:
                p.calculate_health_score(events_data.get(cid, []), tickets_data.get(cid, []))
                self._recalculate_risk(p)
                count += 1
        self._save_data()
        return count

    def get_segment_summary(self) -> Dict[str, Any]:
        segments = {"healthy": 0, "attention_needed": 0, "at_risk": 0, "critical": 0}
        for p in self.profiles.values():
            if p.risk_level == RiskLevel.LOW:
                segments["healthy"] += 1
            elif p.risk_level == RiskLevel.MEDIUM:
                segments["attention_needed"] += 1
            elif p.risk_level == RiskLevel.HIGH:
                segments["at_risk"] += 1
            elif p.risk_level == RiskLevel.CRITICAL:
                segments["critical"] += 1
        return segments

    def get_health_changelog(self, customer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        p = self.profiles.get(customer_id)
        if not p:
            return []
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [s for s in p.score_history if s.get("timestamp") and datetime.fromisoformat(s["timestamp"]) >= cutoff]

    def compare_profiles(self, customer_ids: List[str]) -> Dict[str, Any]:
        profiles = {cid: self.profiles.get(cid) for cid in customer_ids}
        valid = {cid: p for cid, p in profiles.items() if p}
        return {cid: {"health_score": p.overall_health_score, "risk_level": p.risk_level.value, "nps_category": p.nps_category, "trend": p.trend, "last_updated": p.last_updated.isoformat()} for cid, p in valid.items()}

    def export_health_report(self) -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(), "profiles": [p.to_dict() for p in self.profiles.values()], "summary": self.get_summary(), "distribution": self.get_health_distribution()}

    def reset_profile(self, customer_id: str) -> bool:
        p = self.profiles.get(customer_id)
        if not p:
            return False
        p.overall_health_score = 50
        p.risk_level = RiskLevel.LOW
        p.score_history = []
        p.last_updated = datetime.utcnow()
        self._save_data()
        return True

    def get_health_alerts(self, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
        alerts = []
        for cid, p in self.profiles.items():
            if risk_level and p.risk_level.value != risk_level:
                continue
            for a in p.alerts:
                alerts.append({"customer_id": cid, **a})
        alerts.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
        return alerts[:50]

    def get_health_trend_chart(self, customer_id: str, days: int = 90) -> Dict[str, Any]:
        history = self.get_health_history(customer_id, days)
        return {
            "customer_id": customer_id,
            "data_points": [{"date": h["timestamp"][:10], "score": h["composite_score"]} for h in history],
            "trend": history[-1]["risk_level"] if history else "unknown",
        }

    def bulk_compute_health(self, customer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for data in customer_data:
            try:
                profile = self.compute_health_score(
                    data["customer_id"],
                    data.get("usage", {}),
                    data.get("billing", {}),
                    data.get("support", {}),
                    data.get("uptime"),
                    data.get("sentiment"),
                    data.get("adoption"),
                )
                results.append(profile.to_dict())
            except Exception as e:
                results.append({"customer_id": data.get("customer_id", "unknown"), "error": str(e)})
        return {"computed": len(results), "profiles": results}

    def get_health_summary(self, customer_id: str) -> Dict[str, Any]:
        profile = self.profiles.get(customer_id)
        if not profile:
            return {"customer_id": customer_id, "error": "Profile not found"}
        return {
            "customer_id": customer_id,
            "composite_score": profile.composite_score,
            "risk_level": profile.risk_level.value,
            "trend": profile.trend,
            "churn_probability": profile.churn_probability,
            "components": {c.category.value: {"score": c.score, "weight": c.weight, "trend": c.trend} for c in profile.components},
            "alerts": profile.alerts,
            "recommendations": profile.recommendations,
        }

    def compare_health_profiles(self, customer_ids: List[str]) -> List[Dict[str, Any]]:
        return [self.get_health_summary(cid) for cid in customer_ids if cid in self.profiles]

    def get_health_forecast(self, customer_id: str, days_ahead: int = 30) -> Dict[str, Any]:
        history = self.get_health_history(customer_id, 90)
        if len(history) < 3:
            return {"customer_id": customer_id, "forecast": "insufficient_data"}
        scores = [h["composite_score"] for h in history[-10:]]
        if len(scores) < 2:
            return {"customer_id": customer_id, "forecast": "insufficient_data"}
        slope = (scores[-1] - scores[0]) / max(len(scores), 1)
        forecast = [max(0, min(100, scores[-1] + slope * i)) for i in range(1, days_ahead + 1)]
        return {
            "customer_id": customer_id,
            "historical_scores": scores,
            "forecast_scores": [round(s, 1) for s in forecast],
            "direction": "improving" if slope > 0.5 else "declining" if slope < -0.5 else "stable",
        }

    def get_health_distribution_chart(self) -> Dict[str, Any]:
        buckets = {"healthy": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
        for p in self.profiles.values():
            buckets[p.risk_level.value] += 1
        return {
            "labels": list(buckets.keys()),
            "values": list(buckets.values()),
            "total": sum(buckets.values()),
        }

    def get_anomalous_profiles(self) -> List[Dict[str, Any]]:
        anomalous = []
        for cid, p in self.profiles.items():
            history = self.history.get(cid, [])
            if len(history) >= 3:
                recent = [h["composite_score"] for h in history[-3:]]
                if max(recent) - min(recent) > 30:
                    anomalous.append(p.to_dict())
        return anomalous[:20]

    def get_health_report(self, customer_id: str) -> Dict[str, Any]:
        profile = self.get_health_summary(customer_id)
        history = self.get_health_history(customer_id, 90)
        forecast = self.get_health_forecast(customer_id)
        return {
            "profile": profile,
            "history": history,
            "forecast": forecast,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_component_breakdown(self, customer_id: str) -> Dict[str, Any]:
        p = self.profiles.get(customer_id)
        if not p:
            return {}
        components = {}
        for c in p.components:
            components[c.category.value] = {
                "score": c.score,
                "weight": c.weight,
                "weighted_contribution": round(c.score * c.weight, 1),
                "trend": c.trend,
                "details": c.details,
            }
        return {
            "customer_id": customer_id,
            "components": components,
            "total_weighted": round(sum(c.score * c.weight for c in p.components), 1),
        }

    def get_health_changelog(self, customer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        return self.get_health_history(customer_id, days)

    def export_health_csv(self) -> str:
        lines = ["customer_id,composite_score,risk_level,churn_probability,trend,last_updated"]
        for p in self.profiles.values():
            lines.append(f"{p.customer_id},{p.composite_score},{p.risk_level.value},{p.churn_probability},{p.trend},{p.last_updated}")
        return "\n".join(lines)

    def get_at_risk_summary(self) -> Dict[str, Any]:
        at_risk = [p for p in self.profiles.values() if p.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
        return {
            "total_at_risk": len(at_risk),
            "pct_of_total": round(len(at_risk) / max(len(self.profiles), 1) * 100, 1),
            "avg_churn_probability": round(sum(p.churn_probability for p in at_risk) / max(len(at_risk), 1), 3) if at_risk else 0,
            "critical_count": sum(1 for p in at_risk if p.risk_level == RiskLevel.CRITICAL),
            "high_count": sum(1 for p in at_risk if p.risk_level == RiskLevel.HIGH),
        }

    def schedule_health_check(self, customer_id: str, days_from_now: int = 7) -> Dict[str, Any]:
        check_id = f"HC-{uuid.uuid4().hex[:6].upper()}"
        scheduled = (datetime.utcnow() + timedelta(days=days_from_now)).isoformat()
        return {
            "check_id": check_id,
            "customer_id": customer_id,
            "scheduled_at": scheduled,
            "type": "health_review",
            "status": "scheduled",
        }

    def get_health_score_history(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.history.get(customer_id, [])

    def recent_health_changes(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        changes = []
        for cid, hist in self.history.items():
            recent = [h for h in hist if h["timestamp"] >= cutoff]
            if recent:
                changes.append({"customer_id": cid, "changes": recent})
        return changes

    def get_health_summary_all(self) -> Dict[str, Any]:
        scores = [p.composite_score for p in self.profiles.values()]
        if not scores:
            return {}
        return {
            "total_profiles": len(self.profiles),
            "avg_score": round(sum(scores) / len(scores), 1),
            "median_score": sorted(scores)[len(scores) // 2] if scores else 0,
            "min_score": min(scores),
            "max_score": max(scores),
            "risk_distribution": dict(Counter(p.risk_level.value for p in self.profiles.values())),
            "trend_distribution": dict(Counter(p.trend for p in self.profiles.values())),
        }

    def get_health_scoring_trend(self, customer_id: str, days: int = 90) -> Dict[str, Any]:
        history = self.get_health_history(customer_id, days)
        if not history:
            return {"customer_id": customer_id, "trend": "insufficient_data"}
        scores = [h["composite_score"] for h in history]
        first_half = sum(scores[:len(scores)//2]) / max(len(scores)//2, 1)
        second_half = sum(scores[len(scores)//2:]) / max(len(scores) - len(scores)//2, 1)
        direction = "improving" if second_half > first_half else "declining" if second_half < first_half else "stable"
        return {
            "customer_id": customer_id,
            "direction": direction,
            "start_score": scores[0],
            "end_score": scores[-1],
            "change": round(scores[-1] - scores[0], 1),
            "volatility": round(max(scores) - min(scores), 1),
            "samples": len(scores),
        }

    def get_health_factors(self, customer_id: str) -> Dict[str, Any]:
        p = self.profiles.get(customer_id)
        if not p:
            return {}
        factors = []
        for c in p.components:
            if c.score < 40:
                factors.append({"component": c.category.value, "score": c.score, "impact": "negative", "action": "Immediate attention required"})
            elif c.score < 70:
                factors.append({"component": c.category.value, "score": c.score, "impact": "neutral", "action": "Monitor and improve"})
            else:
                factors.append({"component": c.category.value, "score": c.score, "impact": "positive", "action": "Maintain current trajectory"})
        return {"customer_id": customer_id, "factors": factors, "primary_concern": min(factors, key=lambda f: f["score"])["component"] if factors else None}

    def compare_profiles(self, customer_ids: List[str]) -> Dict[str, Any]:
        comparison = {}
        for cid in customer_ids:
            p = self.profiles.get(cid)
            if p:
                comparison[cid] = {"score": p.composite_score, "risk": p.risk_level.value, "churn": p.churn_probability, "trend": p.trend}
        return comparison

    def get_health_alerts(self, days: int = 7) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        alerts = []
        for cid, hist in self.history.items():
            recent = [h for h in hist if h["timestamp"] >= cutoff and h.get("composite_score", 100) < 40]
            for h in recent:
                alerts.append({"customer_id": cid, "score": h["composite_score"], "timestamp": h["timestamp"], "alert": "Critical health score drop"})
        alerts.sort(key=lambda a: a["timestamp"], reverse=True)
        return alerts[:50]

    def batch_update_health(self, customer_ids: List[str]) -> Dict[str, Any]:
        updated = 0
        for cid in customer_ids:
            p = self.profiles.get(cid)
            if p:
                self.update_health_score(cid)
                updated += 1
        return {"updated": updated, "total_requested": len(customer_ids)}

    def get_health_prediction(self, customer_id: str) -> Dict[str, Any]:
        hist = self.get_health_history(customer_id, 90)
        if len(hist) < 3:
            return {"customer_id": customer_id, "prediction": "insufficient_data"}
        scores = [h["composite_score"] for h in hist[-10:]]
        if len(scores) >= 2:
            slope = (scores[-1] - scores[0]) / len(scores)
            predicted = max(0, min(100, scores[-1] + slope * 30))
        else:
            predicted = scores[-1]
        return {"customer_id": customer_id, "current": scores[-1], "predicted_30d": round(predicted, 1), "direction": "improving" if predicted > scores[-1] else "declining" if predicted < scores[-1] else "stable"}

    def export_health_report(self, format: str = "json") -> Any:
        if format == "csv":
            return self.export_health_csv()
        return {"profiles": [p.to_dict() for p in self.profiles.values()], "generated_at": datetime.utcnow().isoformat()}


class HealthScoringBatchProcessor:
    def __init__(self, service: HealthScoringService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_update_scores(self, customer_ids: List[str]) -> Dict[str, Any]:
        updated = 0
        errors = []
        for cid in customer_ids:
            try:
                self.service.update_health_score(cid)
                updated += 1
                self.batch_log.append({"action": "update_score", "customer_id": cid, "status": "success"})
            except Exception as e:
                errors.append({"customer_id": cid, "error": str(e)})
                self.batch_log.append({"action": "update_score", "customer_id": cid, "status": "error"})
        return {"updated": updated, "errors": len(errors), "error_details": errors[:5]}

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_health_profiles(profiles: List[CustomerHealthProfile], page: int = 1, page_size: int = 20, risk_level: Optional[str] = None) -> Dict[str, Any]:
    filtered = [p for p in profiles if p.risk_level.value == risk_level] if risk_level else profiles
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [p.to_dict() for p in filtered[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_population_health_summary(service: HealthScoringService) -> Dict[str, Any]:
    profiles = list(service.profiles.values())
    if not profiles:
        return {"total_profiles": 0}
    scores = [p.composite_score for p in profiles]
    churns = [p.churn_probability for p in profiles]
    return {
        "total": len(profiles),
        "avg_score": round(sum(scores) / len(scores), 1),
        "avg_churn_probability": round(sum(churns) / len(churns), 3),
        "healthy": sum(1 for p in profiles if p.risk_level == RiskLevel.HEALTHY),
        "at_risk": sum(1 for p in profiles if p.risk_level == RiskLevel.AT_RISK),
        "critical": sum(1 for p in profiles if p.risk_level == RiskLevel.CRITICAL),
        "improving": sum(1 for p in profiles if p.trend == "improving"),
        "declining": sum(1 for p in profiles if p.trend == "declining"),
    }


class HealthAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


class HealthMetricsCollector:
    def __init__(self):
        self._counts: Dict[str, int] = {}

    def inc(self, name: str, n: int = 1):
        self._counts[name] = self._counts.get(name, 0) + n

    def get(self, name: str) -> int:
        return self._counts.get(name, 0)

    def snapshot(self) -> Dict[str, int]:
        return dict(self._counts)


def validate_health_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    thresholds = config.get("thresholds", {})
    if thresholds and not isinstance(thresholds, dict):
        errors.append("thresholds must be a dict")
    return errors


def merge_health_profiles(service: HealthScoringService, source_customer: str, target_customer: str) -> int:
    source = service.profiles.get(source_customer)
    target = service.profiles.get(target_customer)
    if not source:
        return 0
    if target:
        target.composite_score = max(source.composite_score, target.composite_score)
        target.churn_probability = max(source.churn_probability, target.churn_probability)
        for comp in source.components:
            existing = next((c for c in target.components if c.category == comp.category), None)
            if existing:
                existing.score = max(existing.score, comp.score)
            else:
                target.components.append(comp)
    else:
        source.customer_id = target_customer
        service.profiles[target_customer] = source
    del service.profiles[source_customer]
    if source_customer in service.history:
        service.history[target_customer] = service.history.pop(source_customer)
    service._save_data()
    return 1


def get_health_anomalies(service: HealthScoringService, threshold: float = 30.0) -> List[Dict[str, Any]]:
    anomalies = []
    for cid, profile in service.profiles.items():
        anomalies_found = []
        if profile.churn_probability > 0.7:
            anomalies_found.append("high_churn_risk")
        if profile.risk_level == RiskLevel.CRITICAL:
            anomalies_found.append("critical_health")
        if profile.trend == "declining" and profile.composite_score < 50:
            anomalies_found.append("declining_critical")
        if anomalies_found:
            anomalies.append({"customer_id": cid, "score": profile.composite_score, "anomalies": anomalies_found})
    return sorted(anomalies, key=lambda a: a["score"])

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
        return {"total_customers": 0, "active_users": 0, "nps_score": 0.0, "satisfaction_rate": 0.0}

    def validate_engagement(self) -> Dict[str, Any]:
        return {"valid": True, "checks": [], "timestamp": datetime.utcnow().isoformat()}

class CXResult(BaseModel):
    success: bool = True
    operation: str = ""
    customer_id: Optional[str] = None
    interaction_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CXBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[Dict[str, Any]] = Field(default_factory=list)
    campaign: str = Field(default="general")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    processed: int = Field(default=0)
    responded: int = Field(default=0)

    def record_processed(self) -> None:
        self.processed += 1

    def record_response(self) -> None:
        self.responded += 1

    def complete(self) -> None:
        self.status = "completed"

class CustomerProfile(BaseModel):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    tier: str = Field(default="standard")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    total_spend: float = Field(default=0.0)
    interaction_count: int = Field(default=0)
    nps_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

class CustomerRepository:
    def __init__(self) -> None:
        self._customers: Dict[str, CustomerProfile] = {}

    def create(self, name: str, email: str, tier: str = "standard") -> CustomerProfile:
        customer = CustomerProfile(name=name, email=email, tier=tier)
        self._customers[customer.customer_id] = customer
        return customer

    def get(self, customer_id: str) -> Optional[CustomerProfile]:
        return self._customers.get(customer_id)

    def update_last_active(self, customer_id: str) -> bool:
        customer = self._customers.get(customer_id)
        if customer:
            customer.last_active = datetime.utcnow()
            customer.interaction_count += 1
            return True
        return False

    def get_by_tier(self, tier: str) -> List[CustomerProfile]:
        return [c for c in self._customers.values() if c.tier == tier]

    def get_at_risk(self, days_inactive: int = 30) -> List[CustomerProfile]:
        cutoff = datetime.utcnow() - timedelta(days=days_inactive)
        return [c for c in self._customers.values() if c.last_active and c.last_active < cutoff]

    def get_statistics(self) -> Dict[str, Any]:
        customers = list(self._customers.values())
        return {"total": len(customers), "avg_spend": round(sum(c.total_spend for c in customers) / max(len(customers), 1), 2),
                "by_tier": {t: sum(1 for c in customers if c.tier == t) for t in set(c.tier for c in customers)},
                "at_risk": len(self.get_at_risk())}

class NPSRecord(BaseModel):
    survey_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    score: int = Field(default=0, ge=0, le=10)
    comment: str = ""
    category: str = Field(default="general")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    def is_promoter(self) -> bool:
        return self.score >= 9

    def is_passive(self) -> bool:
        return 7 <= self.score <= 8

    def is_detractor(self) -> bool:
        return self.score <= 6

class NPSTracker:
    def __init__(self) -> None:
        self._surveys: List[NPSRecord] = []

    def record(self, customer_id: str, score: int, comment: str = "", category: str = "general") -> NPSRecord:
        survey = NPSRecord(customer_id=customer_id, score=score, comment=comment, category=category)
        self._surveys.append(survey)
        return survey

    def get_score(self) -> float:
        total = len(self._surveys)
        if total == 0:
            return 0.0
        promoters = sum(1 for s in self._surveys if s.is_promoter())
        detractors = sum(1 for s in self._surveys if s.is_detractor())
        return round((promoters - detractors) / total * 100, 1)

    def get_by_category(self, category: str) -> List[NPSRecord]:
        return [s for s in self._surveys if s.category == category]

    def get_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [s for s in self._surveys if s.submitted_at >= cutoff]
        return {"period_days": days, "surveys": len(recent),
                "score": round((sum(1 for s in recent if s.is_promoter()) - sum(1 for s in recent if s.is_detractor())) / max(len(recent), 1) * 100, 1),
                "promoters": sum(1 for s in recent if s.is_promoter()),
                "passives": sum(1 for s in recent if s.is_passive()),
                "detractors": sum(1 for s in recent if s.is_detractor())}

class TicketRecord(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    subject: str
    description: str = ""
    priority: str = Field(default="medium")
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    satisfaction_score: Optional[int] = None

class TicketSystem:
    def __init__(self) -> None:
        self._tickets: Dict[str, TicketRecord] = {}

    def create(self, customer_id: str, subject: str, description: str = "", priority: str = "medium") -> TicketRecord:
        ticket = TicketRecord(customer_id=customer_id, subject=subject, description=description, priority=priority)
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def resolve(self, ticket_id: str, satisfaction: Optional[int] = None) -> bool:
        ticket = self._tickets.get(ticket_id)
        if ticket and ticket.status == "open":
            ticket.status = "resolved"
            ticket.resolved_at = datetime.utcnow()
            ticket.satisfaction_score = satisfaction
            return True
        return False

    def get_open(self) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.status == "open"]

    def get_by_priority(self, priority: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.priority == priority]

    def get_by_customer(self, customer_id: str) -> List[TicketRecord]:
        return [t for t in self._tickets.values() if t.customer_id == customer_id]

    def get_statistics(self) -> Dict[str, Any]:
        tickets = list(self._tickets.values())
        open_tickets = self.get_open()
        resolved = [t for t in tickets if t.status == "resolved"]
        avg_resolution = 0.0
        if resolved:
            durations = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved if t.resolved_at]
            avg_resolution = round(sum(durations) / len(durations), 1) if durations else 0.0
        return {"total": len(tickets), "open": len(open_tickets), "resolved": len(resolved),
                "avg_resolution_hours": avg_resolution,
                "by_priority": {p: sum(1 for t in tickets if t.priority == p) for p in set(t.priority for t in tickets)},
                "avg_satisfaction": round(sum(t.satisfaction_score for t in resolved if t.satisfaction_score) / max(len([t for t in resolved if t.satisfaction_score]), 1), 1)}

class OnboardingStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    step_name: str
    status: str = Field(default="pending")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class OnboardingWorkflow:
    def __init__(self) -> None:
        self._steps: Dict[str, OnboardingStep] = {}

    def add_step(self, customer_id: str, step_name: str) -> OnboardingStep:
        step = OnboardingStep(customer_id=customer_id, step_name=step_name)
        self._steps[step.step_id] = step
        return step

    def start_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "pending":
            step.status = "in_progress"
            step.started_at = datetime.utcnow()
            return True
        return False

    def complete_step(self, step_id: str) -> bool:
        step = self._steps.get(step_id)
        if step and step.status == "in_progress":
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.duration_minutes = int((step.completed_at - step.started_at).total_seconds() / 60) if step.started_at else 0
            return True
        return False

    def get_progress(self, customer_id: str) -> Dict[str, Any]:
        steps = [s for s in self._steps.values() if s.customer_id == customer_id]
        completed = sum(1 for s in steps if s.status == "completed")
        return {"customer_id": customer_id, "total_steps": len(steps),
                "completed": completed, "in_progress": sum(1 for s in steps if s.status == "in_progress"),
                "pending": sum(1 for s in steps if s.status == "pending"),
                "progress_pct": round(completed / max(len(steps), 1) * 100, 1)}
