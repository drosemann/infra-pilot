"""Product adoption analytics with feature usage tracking and onboarding funnel analysis."""

import json
import logging
import math
import os
import uuid
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    FEATURE_USED = "feature_used"
    PAGE_VIEW = "page_view"
    ONBOARDING_STEP = "onboarding_step"
    API_CALL = "api_call"
    LOGIN = "login"
    SETTING_CHANGED = "setting_changed"
    INTEGRATION_ADDED = "integration_added"
    REPORT_RUN = "report_run"
    EXPORT = "export"


@dataclass
class FeatureDefinition:
    feature_id: str
    name: str
    category: str
    description: str = ""
    is_core: bool = False
    depends_on: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    released_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UsageEvent:
    event_id: str
    event_type: EventType
    customer_id: str
    user_id: str
    feature_id: Optional[str] = None
    feature_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: Optional[str] = None
    ip_address: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureAdoption:
    feature_id: str
    feature_name: str
    total_users: int
    active_users_7d: int
    active_users_30d: int
    adoption_rate: float
    usage_frequency: Dict[str, int]
    avg_time_in_feature_seconds: float
    trend: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingFunnel:
    stage: str
    total_entered: int
    total_completed: int
    conversion_rate: float
    drop_off_count: int
    avg_time_in_stage_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdoptionAnalyticsService:
    def __init__(self, storage_path: str = "adoption_data.json"):
        self.storage_path = storage_path
        self.features: Dict[str, FeatureDefinition] = {}
        self.events: List[UsageEvent] = []
        self.onboarding_funnels: Dict[str, List[OnboardingFunnel]] = defaultdict(list)
        self._init_default_features()
        self._load_data()

    def _init_default_features(self):
        defaults = [
            FeatureDefinition("f-dashboard", "Dashboard Overview", "core", is_core=True),
            FeatureDefinition("f-server-mgmt", "Server Management", "core", is_core=True),
            FeatureDefinition("f-backup", "Backup & Restore", "data"),
            FeatureDefinition("f-monitoring", "Monitoring & Alerts", "observability"),
            FeatureDefinition("f-analytics", "Analytics & Reports", "analytics"),
            FeatureDefinition("f-billing", "Billing & Invoicing", "finance"),
            FeatureDefinition("f-team", "Team Management", "collaboration"),
            FeatureDefinition("f-api", "API Access", "developer"),
            FeatureDefinition("f-webhook", "Webhooks", "integration"),
            FeatureDefinition("f-iam", "Identity & Access", "security"),
            FeatureDefinition("f-logs", "Log Management", "observability"),
            FeatureDefinition("f-notifications", "Notifications", "core"),
            FeatureDefinition("f-health", "Health Checks", "monitoring"),
            FeatureDefinition("f-automation", "Automation Workflows", "automation"),
            FeatureDefinition("f-kubernetes", "Kubernetes Management", "orchestration"),
            FeatureDefinition("f-edge", "Edge Computing", "advanced"),
            FeatureDefinition("f-green", "Green Computing", "sustainability"),
            FeatureDefinition("f-marketplace", "Marketplace", "ecosystem"),
        ]
        for f in defaults:
            self.features[f.feature_id] = f

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for fdata in data.get("features", []):
                        feat = FeatureDefinition(**fdata)
                        self.features[feat.feature_id] = feat
                    for edata in data.get("events", []):
                        self.events.append(UsageEvent(**edata))
                    for cid, funnel_data in data.get("onboarding_funnels", {}).items():
                        self.onboarding_funnels[cid] = [OnboardingFunnel(**s) for s in funnel_data]
            except Exception as e:
                logger.warning(f"Failed to load adoption data: {e}")

    def _save_data(self):
        try:
            data = {
                "features": [f.to_dict() for f in self.features.values()],
                "events": [e.to_dict() for e in self.events[-10000:]],
                "onboarding_funnels": {cid: [s.to_dict() for s in stages] for cid, stages in self.onboarding_funnels.items()},
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save adoption data: {e}")

    def track_event(
        self,
        event_type: str,
        customer_id: str,
        user_id: str,
        feature_id: Optional[str] = None,
        feature_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> UsageEvent:
        event = UsageEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:12].upper()}",
            event_type=EventType(event_type),
            customer_id=customer_id,
            user_id=user_id,
            feature_id=feature_id,
            feature_name=feature_name,
            metadata=metadata or {},
            session_id=session_id or uuid.uuid4().hex[:12],
        )
        self.events.append(event)
        if len(self.events) > 50000:
            self.events = self.events[-50000:]
        self._save_data()
        return event

    def register_feature(
        self, name: str, category: str, description: str = "",
        is_core: bool = False, depends_on: Optional[List[str]] = None,
    ) -> FeatureDefinition:
        feature_id = name.lower().replace(" ", "-").replace("_", "-")
        if feature_id in self.features:
            return self.features[feature_id]
        feat = FeatureDefinition(
            feature_id=feature_id, name=name, category=category,
            description=description, is_core=is_core,
            depends_on=depends_on or [],
        )
        self.features[feature_id] = feat
        self._save_data()
        return feat

    def get_feature_adoption(
        self, customer_id: str, days: int = 30
    ) -> List[FeatureAdoption]:
        cutoff_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
        cutoff_30d = (datetime.utcnow() - timedelta(days=days)).isoformat()
        customer_events = [e for e in self.events if e.customer_id == customer_id and e.timestamp >= cutoff_30d]

        users_30d = set(e.user_id for e in customer_events)
        total_users = len(users_30d) or 1

        results = []
        for fid, feature in self.features.items():
            feature_events = [e for e in customer_events if e.feature_id == fid]
            if not feature_events:
                continue

            users_with_feature = set(e.user_id for e in feature_events)
            users_7d = set(
                e.user_id for e in feature_events
                if e.timestamp >= cutoff_7d
            )
            frequency = Counter(e.user_id for e in feature_events)
            frequency_buckets = {
                "daily": sum(1 for v in frequency.values() if v >= 7),
                "weekly": sum(1 for v in frequency.values() if 2 <= v < 7),
                "monthly": sum(1 for v in frequency.values() if v < 2),
            }
            times = []
            for e in feature_events:
                if "duration_seconds" in e.metadata:
                    times.append(e.metadata["duration_seconds"])
            avg_time = sum(times) / len(times) if times else 0

            adoption_rate = len(users_with_feature) / total_users
            prev_events = self._get_previous_period_events(customer_id, days)
            prev_users = set(e.user_id for e in prev_events if e.feature_id == fid)
            trend = "growing" if len(users_with_feature) > len(prev_users) else ("declining" if len(users_with_feature) < len(prev_users) else "stable")

            results.append(FeatureAdoption(
                feature_id=fid,
                feature_name=feature.name,
                total_users=len(users_with_feature),
                active_users_7d=len(users_7d),
                active_users_30d=len(users_with_feature),
                adoption_rate=round(adoption_rate, 3),
                usage_frequency=frequency_buckets,
                avg_time_in_feature_seconds=round(avg_time, 1),
                trend=trend,
            ))

        results.sort(key=lambda r: r.adoption_rate, reverse=True)
        return results

    def _get_previous_period_events(self, customer_id: str, days: int) -> List[UsageEvent]:
        end = (datetime.utcnow() - timedelta(days=days)).isoformat()
        start = (datetime.utcnow() - timedelta(days=days * 2)).isoformat()
        return [e for e in self.events if e.customer_id == customer_id and start <= e.timestamp < end]

    def get_customer_adoption_summary(self, customer_id: str) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        customer_events = [e for e in self.events if e.customer_id == customer_id and e.timestamp >= cutoff]

        feature_events = [e for e in customer_events if e.event_type == EventType.FEATURE_USED]
        login_events = [e for e in customer_events if e.event_type == EventType.LOGIN]
        api_events = [e for e in customer_events if e.event_type == EventType.API_CALL]

        users = set(e.user_id for e in customer_events)
        features_used = set(e.feature_id for e in feature_events if e.feature_id)

        return {
            "customer_id": customer_id,
            "total_events_30d": len(customer_events),
            "active_users_30d": len(users),
            "features_used_30d": len(features_used),
            "total_features": len(self.features),
            "adoption_rate": round(len(features_used) / max(len(self.features), 1), 3),
            "login_count_30d": len(login_events),
            "api_call_count_30d": len(api_events),
            "most_used_features": self._get_top_features(customer_events, 5),
            "last_active": max((e.timestamp for e in customer_events), default=""),
        }

    def _get_top_features(self, events: List[UsageEvent], n: int = 5) -> List[Dict[str, Any]]:
        feature_counts = Counter(e.feature_name or e.feature_id for e in events if e.feature_id)
        return [
            {"name": name, "count": count}
            for name, count in feature_counts.most_common(n)
        ]

    def get_onboarding_funnel(self, customer_id: str) -> List[OnboardingFunnel]:
        return self.onboarding_funnels.get(customer_id, [])

    def record_onboarding_step(
        self, customer_id: str, stage: str, completed: bool,
        time_in_stage_seconds: float = 0,
    ) -> OnboardingFunnel:
        if customer_id not in self.onboarding_funnels:
            funnel_stages = [
                OnboardingFunnel(stage="account_created", total_entered=0, total_completed=0, conversion_rate=0, drop_off_count=0, avg_time_in_stage_seconds=0),
                OnboardingFunnel(stage="profile_setup", total_entered=0, total_completed=0, conversion_rate=0, drop_off_count=0, avg_time_in_stage_seconds=0),
                OnboardingFunnel(stage="first_resource", total_entered=0, total_completed=0, conversion_rate=0, drop_off_count=0, avg_time_in_stage_seconds=0),
                OnboardingFunnel(stage="invite_team", total_entered=0, total_completed=0, conversion_rate=0, drop_off_count=0, avg_time_in_stage_seconds=0),
                OnboardingFunnel(stage="first_deploy", total_entered=0, total_completed=0, conversion_rate=0, drop_off_count=0, avg_time_in_stage_seconds=0),
            ]
            self.onboarding_funnels[customer_id] = funnel_stages

        for s in self.onboarding_funnels[customer_id]:
            if s.stage == stage:
                s.total_entered += 1
                if completed:
                    s.total_completed += 1
                s.drop_off_count = s.total_entered - s.total_completed
                s.conversion_rate = round(s.total_completed / max(s.total_entered, 1), 3)
                if s.total_completed > 0:
                    s.avg_time_in_stage_seconds = (
                        (s.avg_time_in_stage_seconds * (s.total_completed - 1) + time_in_stage_seconds) / s.total_completed
                    )
                break

        self._update_funnel_conversions(customer_id)
        self._save_data()
        return self.onboarding_funnels[customer_id][-1]

    def _update_funnel_conversions(self, customer_id: str):
        stages = self.onboarding_funnels.get(customer_id, [])
        if not stages:
            return
        for i in range(1, len(stages)):
            stages[i].total_entered = stages[i - 1].total_completed
            stages[i].conversion_rate = round(
                stages[i].total_completed / max(stages[i].total_entered, 1), 3
            )

    def get_adoption_recommendations(self, customer_id: str) -> List[Dict[str, Any]]:
        recommendations = []
        features = self.get_feature_adoption(customer_id)
        summary = self.get_customer_adoption_summary(customer_id)

        for feat in features:
            if feat.adoption_rate < 0.2:
                recommendations.append({
                    "type": "low_adoption",
                    "feature_id": feat.feature_id,
                    "feature_name": feat.feature_name,
                    "message": f"Feature '{feat.feature_name}' has very low adoption ({feat.adoption_rate:.0%})",
                    "suggestion": "Consider sending a tutorial or highlighting in onboarding",
                    "priority": "high",
                })
            elif feat.adoption_rate < 0.5:
                recommendations.append({
                    "type": "moderate_adoption",
                    "feature_id": feat.feature_id,
                    "feature_name": feat.feature_name,
                    "message": f"Feature '{feat.feature_name}' adoption is moderate ({feat.adoption_rate:.0%})",
                    "suggestion": "Send tips and use cases to increase engagement",
                    "priority": "medium",
                })
            if feat.trend == "declining":
                recommendations.append({
                    "type": "declining_usage",
                    "feature_id": feat.feature_id,
                    "feature_name": feat.feature_name,
                    "message": f"Feature '{feat.feature_name}' usage is declining",
                    "suggestion": "Investigate and reach out to understand user needs",
                    "priority": "medium",
                })

        if summary.get("features_used_30d", 0) < 3:
            recommendations.append({
                "type": "low_engagement",
                "message": "Customer is using very few features",
                "suggestion": "Schedule a walkthrough session to demonstrate value",
                "priority": "high",
            })

        if summary.get("login_count_30d", 0) < 5:
            recommendations.append({
                "type": "infrequent_logins",
                "message": "Customer logs in infrequently",
                "suggestion": "Send re-engagement email with latest updates",
                "priority": "medium",
            })

        return recommendations

    def get_all_features(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.features.values() if f.active]

    def get_global_stats(self) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        customers = set(e.customer_id for e in recent_events)
        users = set(e.user_id for e in recent_events)
        feature_events = [e for e in recent_events if e.event_type == EventType.FEATURE_USED]
        features_used = set(e.feature_id for e in feature_events if e.feature_id)
        return {
            "total_events_30d": len(recent_events),
            "active_customers_30d": len(customers),
            "active_users_30d": len(users),
            "features_used_30d": len(features_used),
            "total_features": len(self.features),
            "avg_events_per_customer": round(len(recent_events) / max(len(customers), 1), 1),
        }

    def get_feature_trend(self, feature_id: str, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        events = [e for e in self.events if e.feature_id == feature_id and e.timestamp >= cutoff]
        total = len(events)
        unique_users = len(set(e.customer_id for e in events))
        weekly = defaultdict(int)
        for e in events:
            week = e.timestamp.isocalendar()[1]
            weekly[week] += 1
        trend = "stable"
        if len(weekly) >= 2:
            weeks = sorted(weekly.items())
            if weeks[-1][1] > weeks[-2][1] * 1.2:
                trend = "increasing"
            elif weeks[-1][1] < weeks[-2][1] * 0.8:
                trend = "decreasing"
        return {"feature_id": feature_id, "total_events": total, "unique_users": unique_users, "weekly_breakdown": dict(weekly), "trend": trend, "days_analyzed": days}

    def get_onboarding_funnel(self) -> Dict[str, Any]:
        steps = ["signup", "profile_complete", "first_login", "first_integration", "first_report"]
        funnel = {}
        for step in steps:
            count = len(set(e.customer_id for e in self.events if e.event_type.value == step))
            funnel[step] = count
        conversions = []
        for i in range(len(steps) - 1):
            prev_count = funnel[steps[i]]
            curr_count = funnel[steps[i + 1]]
            rate = round(curr_count / max(prev_count, 1) * 100, 1)
            conversions.append({"from": steps[i], "to": steps[i + 1], "rate": rate})
        return {"steps": funnel, "conversions": conversions}

    def get_customer_journey(self, customer_id: str) -> List[Dict[str, Any]]:
        events = [e for e in self.events if e.customer_id == customer_id]
        events.sort(key=lambda e: e.timestamp)
        return [{"event_type": e.event_type.value, "feature_id": e.feature_id, "timestamp": e.timestamp.isoformat(), "metadata": e.metadata} for e in events]

    def get_adoption_score(self, customer_id: str) -> Dict[str, Any]:
        events = [e for e in self.events if e.customer_id == customer_id]
        if not events:
            return {"customer_id": customer_id, "score": 0, "features_adopted": 0, "days_active": 0}
        features_adopted = len(set(e.feature_id for e in events if e.event_type == EventType.FEATURE_USED))
        days_active = len(set(e.timestamp.date() for e in events))
        recency = (datetime.utcnow() - max(e.timestamp for e in events)).days
        score = min(100, int((features_adopted * 10) + (days_active * 2) - (recency * 5)))
        return {"customer_id": customer_id, "score": max(0, score), "features_adopted": features_adopted, "days_active": days_active, "recency_days": recency}

    def get_segment_analytics(self) -> Dict[str, Any]:
        segments = defaultdict(list)
        for cid in set(e.customer_id for e in self.events):
            score = self.get_adoption_score(cid)
            segment = "power" if score["score"] >= 70 else "regular" if score["score"] >= 40 else "at_risk" if score["score"] >= 20 else "dormant"
            segments[segment].append(cid)
        return {k: {"count": len(v), "pct": round(len(v) / max(sum(len(s) for s in segments.values()), 1) * 100, 1)} for k, v in segments.items()}

    def export_adoption_report(self, format: str = "json") -> Dict[str, Any]:
        features = [f.to_dict() for f in self.features.values()]
        trends = [self.get_feature_trend(fid) for fid in self.features]
        return {"features": features, "trends": trends, "generated_at": datetime.utcnow().isoformat(), "format": format}

    def batch_import_events(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        count = 0
        errors = []
        for data in events_data:
            try:
                event = FeatureEvent(customer_id=data["customer_id"], feature_id=data.get("feature_id"), event_type=EventType(data.get("event_type", "feature_used")), metadata=data.get("metadata", {}))
                self.events.append(event)
                count += 1
            except Exception as e:
                errors.append({"data": data, "error": str(e)})
        self._save_data()
        return {"imported": count, "errors": len(errors), "error_details": errors[:5]}

    def get_feature_comparison(self, feature_ids: List[str]) -> List[Dict[str, Any]]:
        return [self.get_feature_trend(fid) for fid in feature_ids if fid in self.features]

    def get_weekly_active_users(self, weeks: int = 4) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(weeks=weeks)
        weekly = defaultdict(set)
        for e in self.events:
            if e.timestamp >= cutoff:
                week = e.timestamp.isocalendar()[1]
                weekly[week].add(e.customer_id)
        return {f"week_{k}": len(v) for k, v in sorted(weekly.items())}

    def get_feature_discovery_path(self, feature_id: str) -> List[Dict[str, Any]]:
        events = [e for e in self.events if e.feature_id == feature_id and e.event_type == EventType.FEATURE_USED]
        first_uses = {}
        for e in events:
            if e.customer_id not in first_uses or e.timestamp < first_uses[e.customer_id]:
                first_uses[e.customer_id] = e.timestamp
        return [{"customer_id": cid, "first_used": ts.isoformat()} for cid, ts in sorted(first_uses.items(), key=lambda x: x[1])[:20]]

    def get_engagement_metrics(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        daily = [e for e in self.events if e.timestamp >= now - timedelta(hours=24)]
        weekly = [e for e in self.events if e.timestamp >= now - timedelta(days=7)]
        monthly = [e for e in self.events if e.timestamp >= now - timedelta(days=30)]
        return {"daily_events": len(daily), "weekly_events": len(weekly), "monthly_events": len(monthly), "daily_active_customers": len(set(e.customer_id for e in daily)), "weekly_active_customers": len(set(e.customer_id for e in weekly)), "monthly_active_customers": len(set(e.customer_id for e in monthly))}

    def get_power_users(self, threshold: int = 50) -> List[Dict[str, Any]]:
        scores = []
        for cid in set(e.customer_id for e in self.events):
            score = self.get_adoption_score(cid)
            if score["score"] >= threshold:
                scores.append(score)
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:20]

    def merge_features(self, feature_ids: List[str], target_name: str) -> Optional[str]:
        if len(feature_ids) < 2:
            return None
        target_id = str(uuid.uuid4())[:8]
        merged = FeatureDefinition(feature_id=target_id, name=target_name, category=self.features[feature_ids[0]].category if feature_ids[0] in self.features else "general")
        self.features[target_id] = merged
        for fid in feature_ids:
            if fid in self.features:
                for e in self.events:
                    if e.feature_id == fid:
                        e.feature_id = target_id
                del self.features[fid]
        self._save_data()
        return target_id

    def get_feature_ranking(self) -> List[Dict[str, Any]]:
        ranking = []
        for fid, feature in self.features.items():
            events = [e for e in self.events if e.feature_id == fid]
            unique_users = len(set(e.customer_id for e in events))
            recent = sum(1 for e in events if e.timestamp >= datetime.utcnow() - timedelta(days=7))
            ranking.append({"feature_id": fid, "name": feature.name, "total_events": len(events), "unique_users": unique_users, "recent_events_7d": recent, "engagement_score": round((unique_users * 0.6 + recent * 0.4), 1)})
        ranking.sort(key=lambda x: x["engagement_score"], reverse=True)
        return ranking[:30]

    def delete_customer_data(self, customer_id: str) -> bool:
        before = len(self.events)
        self.events = [e for e in self.events if e.customer_id != customer_id]
        removed = before - len(self.events)
        if removed > 0:
            self._save_data()
        return removed > 0

    def get_event_schema(self) -> List[Dict[str, str]]:
        return [{"field": "customer_id", "type": "string", "required": True, "description": "Unique customer identifier"},
                {"field": "feature_id", "type": "string", "required": False, "description": "Feature or page identifier"},
                {"field": "event_type", "type": "enum", "values": [e.value for e in EventType], "required": True, "description": "Type of event"},
                {"field": "metadata", "type": "object", "required": False, "description": "Additional event context"},
                {"field": "timestamp", "type": "datetime", "required": False, "description": "Event time (defaults to now)"}]

    def get_customer_retention(self, days: int = 90) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        active = set(e.customer_id for e in self.events if e.timestamp >= cutoff)
        all_customers = set(e.customer_id for e in self.events)
        retention_rate = round(len(active) / max(len(all_customers), 1) * 100, 1)
        return {"retention_rate": retention_rate, "active_customers": len(active), "total_customers": len(all_customers), "period_days": days}

    def get_feature_adoption_by_segment(self, segment_key: str) -> Dict[str, Any]:
        segments = self.get_segment_analytics()
        result = {}
        for seg_name, seg_data in segments.items():
            result[seg_name] = {"feature_breakdown": {}, "total_in_segment": seg_data["count"]}
        for e in self.events:
            score = self.get_adoption_score(e.customer_id)
            seg = "power" if score["score"] >= 70 else "regular" if score["score"] >= 40 else "at_risk" if score["score"] >= 20 else "dormant"
            if e.feature_id not in result[seg]["feature_breakdown"]:
                result[seg]["feature_breakdown"][e.feature_id] = 0
            result[seg]["feature_breakdown"][e.feature_id] += 1
        return result

    def get_user_cohorts(self) -> Dict[str, Any]:
        cohorts = defaultdict(lambda: {"users": set(), "events": 0})
        for e in self.events:
            week = datetime.fromisoformat(e.timestamp).strftime("%Y-W%V")
            cohorts[week]["users"].add(e.customer_id)
            cohorts[week]["events"] += 1
        return {k: {"unique_users": len(v["users"]), "total_events": v["events"]} for k, v in sorted(cohorts.items())}

    def get_feature_stickiness(self, feature_id: str, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        events = [e for e in self.events if e.feature_id == feature_id and e.timestamp >= cutoff]
        daily_users = defaultdict(set)
        for e in events:
            day = e.timestamp[:10]
            daily_users[day].add(e.customer_id)
        dau_values = [len(v) for v in daily_users.values()]
        return {
            "feature_id": feature_id,
            "daily_active_users": dict(sorted((k, len(v)) for k, v in daily_users.items())),
            "avg_dau": round(sum(dau_values) / max(len(dau_values), 1), 1),
            "peak_dau": max(dau_values) if dau_values else 0,
            "stickiness": round(len(set(e.customer_id for e in events)) / max(len(set(e.customer_id for e in self.events if e.timestamp >= cutoff)), 1), 3),
        }

    def get_adoption_gap_analysis(self) -> List[Dict[str, Any]]:
        gaps = []
        all_customers = set(e.customer_id for e in self.events)
        for fid, feature in self.features.items():
            users = set(e.customer_id for e in self.events if e.feature_id == fid)
            non_users = all_customers - users
            if non_users:
                gaps.append({
                    "feature_id": fid,
                    "feature_name": feature.name,
                    "total_customers": len(all_customers),
                    "adopted": len(users),
                    "adoption_gap": len(non_users),
                    "gap_pct": round(len(non_users) / max(len(all_customers), 1) * 100, 1),
                })
        gaps.sort(key=lambda g: g["gap_pct"], reverse=True)
        return gaps

    def get_time_to_adoption(self, feature_id: str) -> Dict[str, Any]:
        first_events = {}
        for e in self.events:
            if e.feature_id == feature_id:
                if e.customer_id not in first_events or e.timestamp < first_events[e.customer_id]:
                    first_events[e.customer_id] = e.timestamp
        first_event_times = [datetime.fromisoformat(ts) for ts in first_events.values()]
        first_registrations = {}
        for e in self.events:
            if e.event_type == EventType.LOGIN and e.customer_id in first_events:
                if e.customer_id not in first_registrations or e.timestamp < first_registrations[e.customer_id]:
                    first_registrations[e.customer_id] = e.timestamp
        time_deltas = []
        for cid, first_use in first_events.items():
            if cid in first_registrations:
                delta = (datetime.fromisoformat(first_use) - datetime.fromisoformat(first_registrations[cid])).days
                time_deltas.append(delta)
        return {
            "feature_id": feature_id,
            "total_adopters": len(first_events),
            "avg_days_to_adoption": round(sum(time_deltas) / max(len(time_deltas), 1), 1) if time_deltas else None,
            "median_days_to_adoption": sorted(time_deltas)[len(time_deltas) // 2] if time_deltas else None,
            "min_days": min(time_deltas) if time_deltas else None,
            "max_days": max(time_deltas) if time_deltas else None,
        }

    def get_feature_correlation_matrix(self) -> Dict[str, Any]:
        feature_ids = list(self.features.keys())[:15]
        matrix = {}
        for f1 in feature_ids:
            matrix[f1] = {}
            users_f1 = set(e.customer_id for e in self.events if e.feature_id == f1)
            for f2 in feature_ids:
                if f1 == f2:
                    matrix[f1][f2] = 1.0
                    continue
                users_f2 = set(e.customer_id for e in self.events if e.feature_id == f2)
                intersection = users_f1 & users_f2
                union = users_f1 | users_f2
                jaccard = len(intersection) / max(len(union), 1)
                matrix[f1][f2] = round(jaccard, 3)
        return {"features": feature_ids, "correlation_matrix": matrix}

    def predict_churn_risk(self, customer_id: str) -> Dict[str, Any]:
        cutoff_30 = (datetime.utcnow() - timedelta(days=30)).isoformat()
        cutoff_60 = (datetime.utcnow() - timedelta(days=60)).isoformat()
        events_30 = [e for e in self.events if e.customer_id == customer_id and e.timestamp >= cutoff_30]
        events_60 = [e for e in self.events if e.customer_id == customer_id and e.timestamp >= cutoff_60]
        login_30 = sum(1 for e in events_30 if e.event_type == EventType.LOGIN)
        feature_30 = len(set(e.feature_id for e in events_30 if e.feature_id))
        decay = 0
        if events_60 and events_30:
            decay = 1 - (len(events_30) / max(len(events_60), 1))
        risk_score = 0
        if login_30 < 3:
            risk_score += 30
        if feature_30 < 2:
            risk_score += 25
        if decay > 0.5:
            risk_score += 25
        if len(events_30) < 5:
            risk_score += 20
        return {
            "customer_id": customer_id,
            "risk_score": min(100, risk_score),
            "risk_level": "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low",
            "login_frequency_30d": login_30,
            "features_used_30d": feature_30,
            "event_decay_rate": round(decay, 2),
            "recommendation": "Immediate outreach required" if risk_score >= 60 else "Monitor closely" if risk_score >= 30 else "On track",
        }

    def get_adoption_forecast(self, feature_id: str, days_ahead: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
        events = [e for e in self.events if e.feature_id == feature_id and e.timestamp >= cutoff]
        weekly_counts = defaultdict(int)
        weekly_unique = defaultdict(set)
        for e in events:
            week = datetime.fromisoformat(e.timestamp).strftime("%Y-W%V")
            weekly_counts[week] += 1
            weekly_unique[week].add(e.customer_id)
        recent_weeks = sorted(weekly_counts.keys())[-8:]
        counts = [weekly_counts[w] for w in recent_weeks]
        users = [len(weekly_unique[w]) for w in recent_weeks]
        if len(counts) < 2:
            return {"feature_id": feature_id, "forecast": "insufficient_data"}
        avg_growth = (counts[-1] - counts[0]) / max(len(counts), 1) if counts else 0
        forecast_counts = [max(0, int(counts[-1] + avg_growth * i)) for i in range(1, days_ahead // 7 + 1)]
        forecast_users = [max(0, int(users[-1] + (users[-1] - users[0]) / max(len(users), 1) * i)) for i in range(1, days_ahead // 7 + 1)]
        return {
            "feature_id": feature_id,
            "current_weekly_events": counts[-1] if counts else 0,
            "current_weekly_users": users[-1] if users else 0,
            "trend": "growing" if avg_growth > 0 else "declining" if avg_growth < 0 else "stable",
            "forecast_weeks": days_ahead // 7,
            "forecast_events": forecast_counts,
            "forecast_users": forecast_users,
        }

    def get_onboarding_bottlenecks(self) -> List[Dict[str, Any]]:
        bottlenecks = []
        for cid, stages in self.onboarding_funnels.items():
            for stage in stages:
                if stage.conversion_rate < 0.5:
                    bottlenecks.append({
                        "customer_id": cid,
                        "stage": stage.stage,
                        "conversion_rate": stage.conversion_rate,
                        "entered": stage.total_entered,
                        "completed": stage.total_completed,
                        "drop_off": stage.drop_off_count,
                        "avg_time_seconds": stage.avg_time_in_stage_seconds,
                    })
            break
        if not bottlenecks:
            for cid, stages in self.onboarding_funnels.items():
                for stage in stages:
                    if stage.conversion_rate < 0.7:
                        bottlenecks.append({
                            "customer_id": cid,
                            "stage": stage.stage,
                            "conversion_rate": stage.conversion_rate,
                        })
                break
        return bottlenecks

    def get_adoption_heatmap(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [e for e in self.events if e.timestamp >= cutoff]
        heatmap = defaultdict(lambda: defaultdict(int))
        for e in recent:
            day = e.timestamp[:10]
            hour = str(datetime.fromisoformat(e.timestamp).hour)
            heatmap[day][hour] += 1
        return {day: dict(hours) for day, hours in sorted(heatmap.items())}

    def get_adoption_summary(self, customer_id: str) -> Dict[str, Any]:
        summary = self.get_customer_adoption_summary(customer_id)
        score = self.get_adoption_score(customer_id)
        recommendations = self.get_adoption_recommendations(customer_id)
        return {
            "customer_id": customer_id,
            "adoption_summary": summary,
            "adoption_score": score,
            "recommendations": recommendations,
            "features": [f.to_dict() for f in self.features.values() if f.active],
        }

    def delete_customer_events(self, customer_id: str) -> int:
        before = len(self.events)
        self.events = [e for e in self.events if e.customer_id != customer_id]
        removed = before - len(self.events)
        if removed:
            self._save_data()
        return removed

    def get_event_stream(self, customer_id: str, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        events = [e for e in self.events if e.customer_id == customer_id]
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in events[:limit]]

    def get_active_users_chart(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [e for e in self.events if e.timestamp >= cutoff]
        daily = defaultdict(set)
        for e in recent:
            daily[e.timestamp[:10]].add(e.customer_id)
        return {"labels": sorted(daily.keys()), "values": [len(daily[d]) for d in sorted(daily.keys())]}

    def get_feature_usage_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        feature_counts = Counter(e.feature_id for e in self.events if e.feature_id)
        ranking = []
        for fid, count in feature_counts.most_common(limit):
            feature = self.features.get(fid)
            ranking.append({"feature_id": fid, "name": feature.name if feature else fid, "event_count": count})
        return ranking

    def get_adoption_funnel(self, feature_ids: List[str]) -> Dict[str, Any]:
        funnel = {}
        all_users = set(e.customer_id for e in self.events)
        funnel["total_users"] = len(all_users)
        exposed = len(all_users)
        for fid in feature_ids:
            users = set(e.customer_id for e in self.events if e.feature_id == fid)
            funnel[fid] = {"users": len(users), "conversion": round(len(users) / max(exposed, 1), 3)}
            exposed = len(users)
        return funnel

    def get_session_replay(self, customer_id: str, session_id: str) -> List[Dict[str, Any]]:
        events = [e for e in self.events if e.customer_id == customer_id and e.session_id == session_id]
        events.sort(key=lambda e: e.timestamp)
        return [{"event_type": e.event_type.value, "feature_id": e.feature_id, "timestamp": e.timestamp, "metadata": e.metadata} for e in events]

    def get_customer_events_summary(self, customer_id: str) -> Dict[str, Any]:
        events = [e for e in self.events if e.customer_id == customer_id]
        if not events:
            return {"customer_id": customer_id, "total_events": 0}
        by_type = Counter(e.event_type.value for e in events)
        by_feature = Counter(e.feature_id for e in events if e.feature_id)
        return {
            "customer_id": customer_id,
            "total_events": len(events),
            "unique_features": len(set(e.feature_id for e in events if e.feature_id)),
            "by_event_type": dict(by_type),
            "top_features": [{"id": fid, "count": cnt} for fid, cnt in by_feature.most_common(5)],
            "first_event": min(e.timestamp for e in events),
            "last_event": max(e.timestamp for e in events),
        }

    def get_feature_discovery(self, feature_id: str) -> List[Dict[str, Any]]:
        return self.get_feature_discovery_path(feature_id)

    def get_weekly_active_chart(self, weeks: int = 12) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(weeks=weeks)
        weekly = defaultdict(set)
        for e in self.events:
            ts = datetime.fromisoformat(e.timestamp) if isinstance(e.timestamp, str) else e.timestamp
            if ts >= cutoff:
                week_key = ts.strftime("%Y-W%V")
                weekly[week_key].add(e.customer_id)
        sorted_weeks = sorted(weekly.keys())
        return {"labels": sorted_weeks, "values": [len(weekly[w]) for w in sorted_weeks]}

    def get_onboarding_funnel_analysis(self) -> Dict[str, Any]:
        return self.get_onboarding_funnel()

    def get_user_journey_map(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.get_customer_journey(customer_id)

    def get_adoption_trends(self, feature_id: str, days: int = 90) -> Dict[str, Any]:
        return self.get_feature_trend(feature_id, days)

    def get_retention_cohorts(self) -> Dict[str, Any]:
        cohorts = defaultdict(lambda: {"total": set(), "active": set()})
        for e in self.events:
            ts = datetime.fromisoformat(e.timestamp) if isinstance(e.timestamp, str) else e.timestamp
            cohort = ts.strftime("%Y-%m")
            cohorts[cohort]["total"].add(e.customer_id)
            if ts >= datetime.utcnow() - timedelta(days=30):
                cohorts[cohort]["active"].add(e.customer_id)
        return {k: {"total": len(v["total"]), "active": len(v["active"]), "retention": round(len(v["active"]) / max(len(v["total"]), 1), 3)} for k, v in sorted(cohorts.items())}

    def export_all_events(self, format: str = "json") -> Dict[str, Any]:
        return self.export_adoption_report(format)

    def get_user_segments(self) -> Dict[str, Any]:
        cutoff_30 = (datetime.utcnow() - timedelta(days=30)).isoformat()
        cutoff_7 = (datetime.utcnow() - timedelta(days=7)).isoformat()
        all_customers = set(e.customer_id for e in self.events)
        active_30 = set(e.customer_id for e in self.events if e.timestamp >= cutoff_30)
        active_7 = set(e.customer_id for e in self.events if e.timestamp >= cutoff_7)
        return {
            "total_customers": len(all_customers),
            "active_30d": len(active_30),
            "active_7d": len(active_7),
            "dormant": len(all_customers - active_30),
            "new_last_30d": len(active_30 - active_7),
            "power_users": len(set(e.customer_id for e in self.events if e.timestamp >= cutoff_7 and len([ev for ev in self.events if ev.customer_id == e.customer_id and ev.timestamp >= cutoff_7]) >= 10)),
        }

    def get_event_statistics(self) -> Dict[str, Any]:
        if not self.events:
            return {"total_events": 0}
        return {
            "total_events": len(self.events),
            "unique_customers": len(set(e.customer_id for e in self.events)),
            "unique_features": len(set(e.feature_id for e in self.events if e.feature_id)),
            "unique_sessions": len(set(e.session_id for e in self.events if e.session_id)),
            "event_types": dict(Counter(e.event_type.value for e in self.events)),
            "avg_events_per_customer": round(len(self.events) / max(len(set(e.customer_id for e in self.events)), 1), 1),
        }

    def get_adoption_rate_change(self, feature_id: str, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        now = datetime.utcnow().isoformat()
        first_half = [e for e in self.events if e.feature_id == feature_id and cutoff <= e.timestamp < (datetime.fromisoformat(cutoff) + timedelta(days=days//2)).isoformat()]
        second_half = [e for e in self.events if e.feature_id == feature_id and (datetime.fromisoformat(cutoff) + timedelta(days=days//2)).isoformat() <= e.timestamp <= now]
        return {
            "feature_id": feature_id,
            "first_half_users": len(set(e.customer_id for e in first_half)),
            "second_half_users": len(set(e.customer_id for e in second_half)),
            "change": len(set(e.customer_id for e in second_half)) - len(set(e.customer_id for e in first_half)),
            "first_half_events": len(first_half),
            "second_half_events": len(second_half),
        }

    def get_feature_discovery_path(self, feature_id: str) -> List[Dict[str, Any]]:
        events = [e for e in self.events if e.feature_id == feature_id]
        paths = defaultdict(int)
        for e in events:
            prev_event = None
            sorted_events = sorted([ev for ev in self.events if ev.session_id == e.session_id and ev.timestamp < e.timestamp], key=lambda x: x.timestamp)
            if sorted_events:
                prev_event = sorted_events[-1].feature_id or sorted_events[-1].event_type.value
            else:
                prev_event = "direct_entry"
            paths[prev_event] += 1
        sorted_paths = sorted(paths.items(), key=lambda x: x[1], reverse=True)
        return [{"from": key, "count": val, "pct": round(val / max(len(events), 1) * 100, 1)} for key, val in sorted_paths[:10]]

    def get_customer_activation_score(self, customer_id: str) -> Dict[str, Any]:
        events = [e for e in self.events if e.customer_id == customer_id]
        if not events:
            return {"customer_id": customer_id, "activation_score": 0, "activated": False}
        used_features = len(set(e.feature_id for e in events if e.feature_id))
        total_sessions = len(set(e.session_id for e in events if e.session_id))
        event_count = len(events)
        days_active = len(set(e.timestamp[:10] for e in events))
        score = min(100, (used_features * 10) + (total_sessions * 5) + (days_active * 3) + min(event_count, 50))
        return {"customer_id": customer_id, "activation_score": score, "activated": score >= 50, "used_features": used_features, "total_sessions": total_sessions, "days_active": days_active}

    def get_adoption_forecast_all(self, days_ahead: int = 30) -> Dict[str, Any]:
        forecasts = {}
        for feature in self.features.values():
            if feature.active:
                forecasts[feature.feature_id] = self.get_adoption_forecast(feature.feature_id, days_ahead)
        return {"forecasts": forecasts, "generated_at": datetime.utcnow().isoformat()}

    def get_feature_timeline(self, feature_id: str, days: int = 90) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        events = [e for e in self.events if e.feature_id == feature_id and e.timestamp >= cutoff]
        daily = defaultdict(int)
        for e in events:
            daily[e.timestamp[:10]] += 1
        sorted_days = sorted(daily.keys())
        return {"feature_id": feature_id, "labels": sorted_days, "values": [daily[d] for d in sorted_days], "total_events": len(events)}

    def get_adoption_gaps_summary(self) -> Dict[str, Any]:
        gaps = []
        all_customers = set(e.customer_id for e in self.events)
        if not all_customers:
            return {"gaps": []}
        for feature in self.features.values():
            if not feature.active:
                continue
            users = set(e.customer_id for e in self.events if e.feature_id == feature.feature_id)
            gap = len(all_customers - users)
            gap_pct = round(gap / len(all_customers) * 100, 1)
            if gap_pct > 30:
                gaps.append({"feature_id": feature.feature_id, "feature_name": feature.name, "total_users": len(users), "non_users": gap, "gap_pct": gap_pct})
        gaps.sort(key=lambda g: g["gap_pct"], reverse=True)
        return {"gaps": gaps, "total_customers": len(all_customers)}


class AdoptionAnalyticsBatchProcessor:
    def __init__(self, service: AdoptionAnalyticsService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_import_events(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.service.batch_import_events(events_data)

    def batch_register_features(self, features_data: List[Dict[str, Any]]) -> List[FeatureDefinition]:
        results = []
        for data in features_data:
            try:
                feat = self.service.register_feature(
                    name=data["name"], category=data.get("category", "general"),
                    description=data.get("description", ""),
                    is_core=data.get("is_core", False),
                    depends_on=data.get("depends_on"),
                )
                results.append(feat)
                self.batch_log.append({"action": "register_feature", "feature_id": feat.feature_id, "status": "success"})
            except Exception as e:
                self.batch_log.append({"action": "register_feature", "name": data.get("name"), "status": "error", "error": str(e)})
        return results

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]

    def clear_batch_log(self):
        self.batch_log = []


@dataclass
class AdoptionStateTransition:
    from_state: str
    to_state: str
    trigger: str
    customer_id: str
    timestamp: str = ""
    actor: str = "system"


_adoption_state_history: Dict[str, List[AdoptionStateTransition]] = {}


def record_adoption_state_transition(customer_id: str, trigger: str, actor: str = "system") -> AdoptionStateTransition:
    from_state = "active"
    transition = AdoptionStateTransition(from_state=from_state, to_state=from_state, trigger=trigger, customer_id=customer_id, actor=actor)
    _adoption_state_history.setdefault(customer_id, []).append(transition)
    return transition


def get_adoption_state_history(customer_id: str) -> List[AdoptionStateTransition]:
    return _adoption_state_history.get(customer_id, [])


async def paginate_features(page: int = 1, page_size: int = 20, category: Optional[str] = None) -> Dict[str, Any]:
    # Placeholder — works with any service instance
    return {"items": [], "page": page, "page_size": page_size, "total": 0, "total_pages": 0}


def export_adoption_analytics_data(service: AdoptionAnalyticsService, format: str = "json") -> Dict[str, Any]:
    export_id = f"aa_export_{uuid.uuid4().hex[:8]}"
    return {
        "export_id": export_id,
        "exported_at": datetime.utcnow().isoformat(),
        "global_stats": service.get_global_stats(),
        "segment_analytics": service.get_segment_analytics(),
        "event_statistics": service.get_event_statistics(),
        "format": format,
    }


def merge_customer_adoption_data(service: AdoptionAnalyticsService, source_customer: str, target_customer: str) -> int:
    events = [e for e in service.events if e.customer_id == source_customer]
    for e in events:
        e.customer_id = target_customer
    if events:
        service._save_data()
    return len(events)


def compute_customer_lifetime_value(service: AdoptionAnalyticsService, customer_id: str) -> Dict[str, Any]:
    events = [e for e in service.events if e.customer_id == customer_id]
    if not events:
        return {"customer_id": customer_id, "ltv_score": 0, "confidence": "low"}
    days_active = len(set(e.timestamp[:10] for e in events))
    features_used = len(set(e.feature_id for e in events if e.feature_id))
    event_velocity = len(events) / max(days_active, 1)
    ltv = min(100, int((features_used * 8) + (days_active * 3) + (event_velocity * 5)))
    return {
        "customer_id": customer_id,
        "ltv_score": ltv,
        "days_active": days_active,
        "features_used": features_used,
        "event_velocity": round(event_velocity, 2),
        "confidence": "high" if days_active > 30 else "medium" if days_active > 7 else "low",
    }


def get_underperforming_features(service: AdoptionAnalyticsService, threshold: float = 0.3) -> List[Dict[str, Any]]:
    underperforming = []
    for fid, feature in service.features.items():
        events = [e for e in service.events if e.feature_id == fid]
        unique_users = len(set(e.customer_id for e in events))
        all_customers = len(set(e.customer_id for e in service.events))
        adoption = unique_users / max(all_customers, 1)
        if adoption < threshold:
            underperforming.append({
                "feature_id": fid, "name": feature.name,
                "adoption_rate": round(adoption, 3), "unique_users": unique_users,
                "total_customers": all_customers,
            })
    return sorted(underperforming, key=lambda x: x["adoption_rate"])

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
