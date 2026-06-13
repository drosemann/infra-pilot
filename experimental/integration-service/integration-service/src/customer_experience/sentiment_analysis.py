"""NLP sentiment analysis on support conversations, surveys, and social mentions."""

import json
import logging
import math
import os
import re
import uuid
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SentimentLabel(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class SourceType(str, Enum):
    SUPPORT_TICKET = "support_ticket"
    SURVEY = "survey"
    SOCIAL_MEDIA = "social_media"
    CHAT = "chat"
    EMAIL = "email"
    REVIEW = "review"
    FEEDBACK = "feedback"


@dataclass
class SentimentResult:
    text: str
    label: SentimentLabel
    score: float
    confidence: float
    aspects: Dict[str, float] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    entities: List[Dict[str, str]] = field(default_factory=list)
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:200],
            "label": self.label.value,
            "score": self.score,
            "confidence": self.confidence,
            "aspects": self.aspects,
            "keywords": self.keywords,
            "entities": self.entities,
            "language": self.language,
        }


@dataclass
class AnalyzedInteraction:
    interaction_id: str
    source_type: SourceType
    source_id: str
    customer_id: str
    customer_name: str = ""
    sentiment: SentimentResult
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    escalated: bool = False
    escalation_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "sentiment": self.sentiment.to_dict(),
            "created_at": self.created_at,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "metadata": self.metadata,
        }


@dataclass
class SentimentTrend:
    period: str
    average_score: float
    total_interactions: int
    distribution: Dict[str, int]
    top_keywords: List[Tuple[str, int]]
    change_vs_previous: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CustomerSentimentProfile:
    customer_id: str
    customer_name: str
    overall_sentiment: float
    interaction_count: int
    last_interaction: Optional[str]
    trend: str
    risk_level: str
    recent_negative_count: int
    aspects: Dict[str, float] = field(default_factory=dict)
    top_keywords: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LexiconAnalyzer:
    POSITIVE_WORDS = {
        "great", "excellent", "amazing", "wonderful", "fantastic", "outstanding",
        "superb", "brilliant", "awesome", "love", "perfect", "best", "happy",
        "grateful", "thankful", "impressed", "pleased", "satisfied", "delighted",
        "helpful", "fast", "reliable", "easy", "intuitive", "seamless", "smooth",
        "responsive", "efficient", "incredible", "exceptional", "remarkable",
    }

    NEGATIVE_WORDS = {
        "terrible", "awful", "horrible", "worst", "hate", "frustrated", "frustrating",
        "disappointed", "disappointing", "useless", "broken", "slow", "unreliable",
        "complicated", "confusing", "difficult", "poor", "bad", "horrific",
        "nightmare", "unacceptable", "appalling", "dreadful", "pathetic",
        "annoying", "infuriating", "outrageous", "disgusting", "abysmal",
    }

    INTENSIFIERS = {"very", "extremely", "incredibly", "absolutely", "completely", "totally", "highly", "really", "so", "too"}

    NEGATORS = {"not", "no", "never", "neither", "nor", "none", "nothing", "nowhere", "hardly", "barely", "doesn't", "don't", "didn't", "won't", "wouldn't", "shouldn't", "couldn't", "isn't", "aren't", "wasn't", "weren't"}

    ASPECT_KEYWORDS = {
        "support": {"support", "agent", "team", "help", "response", "service", "representative"},
        "performance": {"performance", "speed", "fast", "slow", "lag", "response time", "latency", "slow"},
        "reliability": {"reliable", "uptime", "downtime", "stable", "crash", "bug", "error", "issue", "problem"},
        "usability": {"easy", "interface", "ui", "intuitive", "confusing", "complicated", "navigation", "design"},
        "pricing": {"price", "cost", "expensive", "cheap", "affordable", "billing", "subscription", "plan", "value"},
        "features": {"feature", "functionality", "capability", "option", "tool", "missing", "need", "want"},
    }

    def analyze(self, text: str) -> Tuple[float, Dict[str, float], List[str], float]:
        words = re.findall(r"\b[a-z']+\b", text.lower())
        if not words:
            return 0.5, {}, [], 0.5

        word_count = len(words)
        pos_count = 0
        neg_count = 0
        negated = False
        keyword_scores: List[Tuple[str, float]] = []
        aspect_scores: Dict[str, List[float]] = defaultdict(list)

        for i, word in enumerate(words):
            if word in self.NEGATORS:
                negated = True
                continue

            intensity = 1.0
            if i > 0 and words[i - 1] in self.INTENSIFIERS:
                intensity = 1.5
            if negated:
                intensity *= -1

            if word in self.POSITIVE_WORDS:
                keyword_scores.append((word, intensity * 2))
                for aspect, keywords in self.ASPECT_KEYWORDS.items():
                    if word in keywords:
                        aspect_scores[aspect].append(intensity * 2)
            elif word in self.NEGATIVE_WORDS:
                keyword_scores.append((word, -intensity * 2))
                for aspect, keywords in self.ASPECT_KEYWORDS.items():
                    if word in keywords:
                        aspect_scores[aspect].append(-intensity * 2)

            if word in (".", "!", "?"):
                negated = False

        total_score = sum(s for _, s in keyword_scores)
        max_possible = word_count * 2
        normalized = max(-1, min(1, total_score / max(max_possible, 1)))
        sentiment_score = (normalized + 1) / 2

        keywords = [w for w, _ in sorted(keyword_scores, key=lambda x: abs(x[1]), reverse=True)[:10]]

        aspect_scores_final = {}
        for aspect, scores in aspect_scores.items():
            if scores:
                aspect_scores_final[aspect] = round((sum(scores) / len(scores) + 1) / 2, 3)

        word_confidence = min(1, len(keyword_scores) / max(word_count * 0.1, 1))
        length_confidence = min(1, word_count / 50)
        confidence = round((word_confidence * 0.6 + length_confidence * 0.4), 3)

        return round(sentiment_score, 3), aspect_scores_final, keywords, confidence

    def classify(self, score: float) -> SentimentLabel:
        if score >= 0.8:
            return SentimentLabel.VERY_POSITIVE
        elif score >= 0.6:
            return SentimentLabel.POSITIVE
        elif score >= 0.4:
            return SentimentLabel.NEUTRAL
        elif score >= 0.2:
            return SentimentLabel.NEGATIVE
        return SentimentLabel.VERY_NEGATIVE


class SentimentAnalysisService:
    def __init__(self, storage_path: str = "sentiment_data.json"):
        self.storage_path = storage_path
        self.analyzer = LexiconAnalyzer()
        self.interactions: Dict[str, AnalyzedInteraction] = {}
        self.customer_profiles: Dict[str, CustomerSentimentProfile] = {}
        self.escalation_threshold = 0.3
        self.negative_count_threshold = 3
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for idata in data.get("interactions", []):
                        sa = SentimentResult(
                            text=idata["sentiment"]["text"],
                            label=SentimentLabel(idata["sentiment"]["label"]),
                            score=idata["sentiment"]["score"],
                            confidence=idata["sentiment"]["confidence"],
                            aspects=idata["sentiment"].get("aspects", {}),
                            keywords=idata["sentiment"].get("keywords", []),
                            entities=idata["sentiment"].get("entities", []),
                            language=idata["sentiment"].get("language", "en"),
                        )
                        interaction = AnalyzedInteraction(
                            interaction_id=idata["interaction_id"],
                            source_type=SourceType(idata["source_type"]),
                            source_id=idata["source_id"],
                            customer_id=idata["customer_id"],
                            customer_name=idata.get("customer_name", ""),
                            sentiment=sa,
                            created_at=idata.get("created_at", ""),
                            escalated=idata.get("escalated", False),
                            escalation_reason=idata.get("escalation_reason"),
                            metadata=idata.get("metadata", {}),
                        )
                        self.interactions[interaction.interaction_id] = interaction
                    for pdata in data.get("customer_profiles", []):
                        self.customer_profiles[pdata["customer_id"]] = CustomerSentimentProfile(**pdata)
            except Exception as e:
                logger.warning(f"Failed to load sentiment data: {e}")

    def _save_data(self):
        try:
            data = {
                "interactions": [i.to_dict() for i in self.interactions.values()],
                "customer_profiles": [p.to_dict() for p in self.customer_profiles.values()],
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sentiment data: {e}")

    def analyze_text(
        self,
        text: str,
        source_type: str = "support_ticket",
        source_id: str = "",
        customer_id: str = "",
        customer_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyzedInteraction:
        score, aspects, keywords, confidence = self.analyzer.analyze(text)
        label = self.analyzer.classify(score)

        sentiment = SentimentResult(
            text=text,
            label=label,
            score=score,
            confidence=confidence,
            aspects=aspects,
            keywords=keywords,
        )

        interaction_id = f"SA-{uuid.uuid4().hex[:8].upper()}"
        interaction = AnalyzedInteraction(
            interaction_id=interaction_id,
            source_type=SourceType(source_type),
            source_id=source_id,
            customer_id=customer_id,
            customer_name=customer_name,
            sentiment=sentiment,
            metadata=metadata or {},
        )

        if score < self.escalation_threshold:
            interaction.escalated = True
            interaction.escalation_reason = f"Very negative sentiment detected (score: {score})"
            logger.warning(f"Escalation triggered for customer {customer_id}: {interaction.escalation_reason}")

        self.interactions[interaction_id] = interaction
        self._update_customer_profile(customer_id, customer_name, interaction)
        self._save_data()
        return interaction

    def _update_customer_profile(self, customer_id: str, customer_name: str, interaction: AnalyzedInteraction):
        recent = self._get_customer_interactions(customer_id, days=30)
        if recent:
            avg_score = sum(i.sentiment.score for i in recent) / len(recent)
        else:
            avg_score = interaction.sentiment.score

        labels = [i.sentiment.label for i in recent]
        negative_count = sum(1 for l in labels if l in (SentimentLabel.NEGATIVE, SentimentLabel.VERY_NEGATIVE))

        scores_30d = recent[-14:] if len(recent) >= 14 else recent
        if len(scores_30d) >= 2:
            recent_avg = sum(i.sentiment.score for i in scores_30d[-7:]) / max(len(scores_30d[-7:]), 1)
            older_avg = sum(i.sentiment.score for i in scores_30d[:7]) / max(len(scores_30d[:7]), 1)
            trend = "improving" if recent_avg > older_avg + 0.05 else ("declining" if recent_avg < older_avg - 0.05 else "stable")
        else:
            trend = "stable"

        risk_level = "critical" if negative_count >= 5 else ("high" if negative_count >= 3 else ("medium" if negative_count >= 1 else "low"))

        aspects_agg: Dict[str, List[float]] = defaultdict(list)
        all_keywords: List[str] = []
        for i in recent:
            for aspect, score_val in i.sentiment.aspects.items():
                aspects_agg[aspect].append(score_val)
            all_keywords.extend(i.sentiment.keywords[:3])
        keyword_counts = Counter(all_keywords)

        self.customer_profiles[customer_id] = CustomerSentimentProfile(
            customer_id=customer_id,
            customer_name=customer_name,
            overall_sentiment=round(avg_score, 3),
            interaction_count=len(recent),
            last_interaction=interaction.created_at,
            trend=trend,
            risk_level=risk_level,
            recent_negative_count=negative_count,
            aspects={a: round(sum(v) / len(v), 3) for a, v in aspects_agg.items()},
            top_keywords=[kw for kw, _ in keyword_counts.most_common(10)],
        )

    def _get_customer_interactions(self, customer_id: str, days: Optional[int] = None) -> List[AnalyzedInteraction]:
        results = [i for i in self.interactions.values() if i.customer_id == customer_id]
        if days:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            results = [i for i in results if i.created_at >= cutoff]
        results.sort(key=lambda i: i.created_at, reverse=True)
        return results

    def get_customer_profile(self, customer_id: str) -> Optional[CustomerSentimentProfile]:
        return self.customer_profiles.get(customer_id)

    def list_interactions(
        self,
        customer_id: Optional[str] = None,
        source_type: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        escalated_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        results = list(self.interactions.values())
        if customer_id:
            results = [i for i in results if i.customer_id == customer_id]
        if source_type:
            results = [i for i in results if i.source_type.value == source_type]
        if min_score is not None:
            results = [i for i in results if i.sentiment.score >= min_score]
        if max_score is not None:
            results = [i for i in results if i.sentiment.score <= max_score]
        if escalated_only:
            results = [i for i in results if i.escalated]
        results.sort(key=lambda i: i.created_at, reverse=True)
        return [i.to_dict() for i in results[:limit]]

    def get_sentiment_trends(self, period: str = "daily", days: int = 30) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        interactions = [i for i in self.interactions.values() if i.created_at >= cutoff]
        if not interactions:
            return []

        buckets: Dict[str, List[float]] = defaultdict(list)
        for i in interactions:
            dt = datetime.fromisoformat(i.created_at)
            if period == "daily":
                key = dt.strftime("%Y-%m-%d")
            elif period == "weekly":
                key = dt.strftime("%Y-W%V")
            else:
                key = dt.strftime("%Y-%m")
            buckets[key].append(i.sentiment.score)

        trends = []
        sorted_keys = sorted(buckets.keys())
        prev_avg = None
        for key in sorted_keys:
            scores = buckets[key]
            avg = sum(scores) / len(scores)
            labels = [self.analyzer.classify(s).value for s in scores]
            dist = Counter(labels)
            change = round(avg - prev_avg, 3) if prev_avg is not None else None
            trends.append(SentimentTrend(
                period=key,
                average_score=round(avg, 3),
                total_interactions=len(scores),
                distribution=dict(dist),
                top_keywords=self._get_top_keywords_for_period(key),
                change_vs_previous=change,
            ).to_dict())
            prev_avg = avg

        return trends

    def _get_top_keywords_for_period(self, period_key: str) -> List[Tuple[str, int]]:
        all_kw: List[str] = []
        for i in self.interactions.values():
            dt = datetime.fromisoformat(i.created_at)
            if period_key in (dt.strftime("%Y-%m-%d"), dt.strftime("%Y-W%V"), dt.strftime("%Y-%m")):
                all_kw.extend(i.sentiment.keywords)
        return Counter(all_kw).most_common(10)

    def get_overview_stats(self) -> Dict[str, Any]:
        total = len(self.interactions)
        if not total:
            return {"total_interactions": 0, "average_sentiment": 0, "escalations": 0}
        avg_score = sum(i.sentiment.score for i in self.interactions.values()) / total
        escalations = sum(1 for i in self.interactions.values() if i.escalated)
        labels = [i.sentiment.label.value for i in self.interactions.values()]
        dist = Counter(labels)
        return {
            "total_interactions": total,
            "average_sentiment": round(avg_score, 3),
            "escalations": escalations,
            "escalation_rate": round(escalations / total, 3),
            "distribution": dict(dist),
            "customers_tracked": len(self.customer_profiles),
            "at_risk_customers": sum(1 for p in self.customer_profiles.values() if p.risk_level in ("high", "critical")),
        }

    def set_escalation_threshold(self, threshold: float):
        self.escalation_threshold = max(0, min(1, threshold))

    def get_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        for cid, profile in self.customer_profiles.items():
            if profile.risk_level in ("high", "critical"):
                alerts.append({
                    "customer_id": cid,
                    "customer_name": profile.customer_name,
                    "risk_level": profile.risk_level,
                    "overall_sentiment": profile.overall_sentiment,
                    "negative_interactions": profile.recent_negative_count,
                    "trend": profile.trend,
                    "message": f"Customer {profile.customer_name} sentiment at risk level: {profile.risk_level}",
                })
        return alerts

    def get_sentiment_trend(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        profile = self.profiles.get(customer_id)
        if not profile: return {"customer_id": customer_id, "error": "Not found"}
        recent_interactions = [i for i in profile.recent_interactions if i.timestamp >= cutoff]
        daily = defaultdict(list)
        for i in recent_interactions:
            day = i.timestamp.strftime("%Y-%m-%d")
            daily[day].append(i.sentiment_score)
        trend = {k: round(sum(v) / len(v), 2) for k, v in sorted(daily.items())}
        return {"customer_id": customer_id, "customer_name": profile.customer_name, "trend": trend, "overall": profile.overall_sentiment, "direction": profile.trend}

    def get_customer_feedback(self, customer_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        profile = self.profiles.get(customer_id)
        if not profile: return []
        interactions = sorted(profile.recent_interactions, key=lambda i: i.timestamp, reverse=True)
        return [{"interaction_id": i.interaction_id, "channel": i.channel, "sentiment_score": i.sentiment_score, "label": i.sentiment_label, "summary": i.summary, "timestamp": i.timestamp.isoformat()} for i in interactions[:limit]]

    def get_sentiment_distribution(self) -> Dict[str, int]:
        distribution = {"positive": 0, "neutral": 0, "negative": 0, "mixed": 0}
        for p in self.profiles.values():
            label = p.overall_sentiment
            if label in distribution:
                distribution[label] += 1
        return distribution

    def get_segment_sentiment(self) -> Dict[str, Any]:
        segments = defaultdict(lambda: {"scores": [], "count": 0})
        for p in self.profiles.values():
            seg = p.segment or "unknown"
            segments[seg]["scores"].append(p.overall_score)
            segments[seg]["count"] += 1
        return {seg: {"avg_score": round(sum(data["scores"]) / len(data["scores"]), 2), "count": data["count"], "distribution": {"positive": sum(1 for p in self.profiles.values() if (p.segment or "unknown") == seg and p.overall_sentiment == "positive"), "negative": sum(1 for p in self.profiles.values() if (p.segment or "unknown") == seg and p.overall_sentiment == "negative")}} for seg, data in segments.items()}

    def search_sentiment(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for p in self.profiles.values():
            if q in p.customer_name.lower() or q in p.customer_id.lower():
                results.append({"customer_id": p.customer_id, "customer_name": p.customer_name, "overall_sentiment": p.overall_sentiment, "overall_score": p.overall_score, "trend": p.trend})
        return results[:20]

    def batch_analyze(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        analyzed = 0
        for data in interactions:
            try:
                self.record_interaction(customer_id=data["customer_id"], channel=data.get("channel", "chat"), content=data.get("content", ""), sentiment_score=data.get("sentiment_score", 0.0), metadata=data.get("metadata", {}))
                analyzed += 1
            except Exception:
                continue
        return {"analyzed": analyzed, "total_provided": len(interactions)}

    def get_trend_forecast(self, customer_id: str, days_ahead: int = 7) -> Dict[str, Any]:
        profile = self.profiles.get(customer_id)
        if not profile: return {"error": "Customer not found"}
        recent = [i.sentiment_score for i in profile.recent_interactions[-30:]]
        if len(recent) < 3: return {"forecast": "insufficient_data", "scores": recent}
        avg = sum(recent) / len(recent)
        direction = 1 if recent[-1] > recent[0] else -1 if recent[-1] < recent[0] else 0
        forecast = [min(1.0, max(0.0, avg + direction * 0.05 * i)) for i in range(1, days_ahead + 1)]
        return {"customer_id": customer_id, "customer_name": profile.customer_name, "historical_avg": round(avg, 2), "forecast_scores": [round(s, 2) for s in forecast], "direction": "improving" if direction > 0 else "declining" if direction < 0 else "stable"}

    def get_top_positive_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        all_interactions = []
        for p in self.profiles.values():
            for i in p.recent_interactions:
                all_interactions.append({"customer_id": p.customer_id, "customer_name": p.customer_name, "score": i.sentiment_score, "summary": i.summary, "channel": i.channel, "timestamp": i.timestamp.isoformat()})
        all_interactions.sort(key=lambda x: x["score"], reverse=True)
        return all_interactions[:limit]

    def get_top_negative_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        all_interactions = []
        for p in self.profiles.values():
            for i in p.recent_interactions:
                all_interactions.append({"customer_id": p.customer_id, "customer_name": p.customer_name, "score": i.sentiment_score, "summary": i.summary, "channel": i.channel, "timestamp": i.timestamp.isoformat()})
        all_interactions.sort(key=lambda x: x["score"])
        return all_interactions[:limit]

    def export_sentiment_report(self) -> Dict[str, Any]:
        return {"generated_at": datetime.utcnow().isoformat(), "profiles": [p.to_dict() for p in self.profiles.values()], "distribution": self.get_sentiment_distribution(), "segment_sentiment": self.get_segment_sentiment(), "alerts": self.get_sentiment_alerts()}

    def reset_customer_sentiment(self, customer_id: str) -> bool:
        p = self.profiles.get(customer_id)
        if not p: return False
        p.overall_sentiment = "neutral"
        p.overall_score = 0.5
        p.risk_level = RiskLevel.LOW
        p.recent_interactions = []
        p.recent_negative_count = 0
        p.recent_positive_count = 0
        p.recent_neutral_count = 0
        p.trend = "stable"
        self._save_data()
        return True

    def analyze_batch(self, texts: List[str], source_type: str = "feedback", customer_id: str = "") -> List[AnalyzedInteraction]:
        results = []
        for text in texts:
            try:
                result = self.analyze_text(text, source_type=source_type, customer_id=customer_id)
                results.append(result)
            except Exception:
                continue
        return results

    def get_sentiment_summary(self, customer_id: str) -> Dict[str, Any]:
        profile = self.customer_profiles.get(customer_id)
        if not profile:
            return {"customer_id": customer_id, "error": "Profile not found"}
        return {
            "customer_id": customer_id,
            "overall_sentiment": profile.overall_sentiment,
            "trend": profile.trend,
            "risk_level": profile.risk_level,
            "interaction_count": profile.interaction_count,
            "recent_negative_count": profile.recent_negative_count,
            "aspects": profile.aspects,
            "top_keywords": profile.top_keywords,
        }

    def get_sentiment_by_channel(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [i for i in self.interactions.values() if i.created_at >= cutoff]
        by_channel = defaultdict(list)
        for i in recent:
            by_channel[i.source_type.value].append(i.sentiment.score)
        return {
            ch: {
                "avg_score": round(sum(scores) / len(scores), 3),
                "count": len(scores),
                "label": self.analyzer.classify(sum(scores) / len(scores)).value if scores else "neutral",
            }
            for ch, scores in by_channel.items()
        }

    def get_sentiment_alerts(self) -> List[Dict[str, Any]]:
        return self.get_alerts()

    def get_customer_interactions(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.list_interactions(customer_id=customer_id, limit=limit)

    def get_sentiment_forecast(self, customer_id: str, days_ahead: int = 7) -> Dict[str, Any]:
        return self.get_trend_forecast(customer_id, days_ahead)

    def get_positive_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.get_top_positive_interactions(limit)

    def get_negative_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.get_top_negative_interactions(limit)

    def export_sentiment_data(self) -> Dict[str, Any]:
        return self.export_sentiment_report()

    def get_sentiment_heatmap(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [i for i in self.interactions.values() if i.created_at >= cutoff]
        heatmap = defaultdict(lambda: defaultdict(list))
        for i in recent:
            day = i.created_at[:10]
            aspect = list(i.sentiment.aspects.keys()) or ["general"]
            for a in aspect:
                heatmap[day][a].append(i.sentiment.score)
        return {
            day: {
                aspect: round(sum(scores) / len(scores), 3)
                for aspect, scores in aspects.items()
            }
            for day, aspects in sorted(heatmap.items())
        }

    def get_keyword_trends(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [i for i in self.interactions.values() if i.created_at >= cutoff]
        keyword_freq = Counter()
        for i in recent:
            keyword_freq.update(i.sentiment.keywords)
        return {
            "top_keywords": [{"keyword": kw, "count": cnt} for kw, cnt in keyword_freq.most_common(20)],
            "total_interactions": len(recent),
        }

    def get_aspect_sentiment(self, customer_id: str) -> Dict[str, Any]:
        interactions = self._get_customer_interactions(customer_id, days=90)
        aspects = defaultdict(list)
        for i in interactions:
            for aspect, score in i.sentiment.aspects.items():
                aspects[aspect].append(score)
        return {
            customer_id: {
                aspect: {
                    "avg_score": round(sum(scores) / len(scores), 3),
                    "count": len(scores),
                    "label": self.analyzer.classify(sum(scores) / len(scores)).value,
                }
                for aspect, scores in aspects.items()
            }
        }

    def compare_sentiment(self, customer_ids: List[str]) -> Dict[str, Any]:
        comparison = {}
        for cid in customer_ids:
            profile = self.customer_profiles.get(cid)
            if profile:
                comparison[cid] = {
                    "overall_sentiment": profile.overall_sentiment,
                    "trend": profile.trend,
                    "risk_level": profile.risk_level,
                    "interaction_count": profile.interaction_count,
                }
        return comparison

    def get_sentiment_triggers(self) -> List[Dict[str, Any]]:
        triggers = []
        for i in self.interactions.values():
            if i.escalated:
                triggers.append({
                    "interaction_id": i.interaction_id,
                    "customer_id": i.customer_id,
                    "reason": i.escalation_reason,
                    "score": i.sentiment.score,
                    "created_at": i.created_at,
                })
        triggers.sort(key=lambda t: t["created_at"], reverse=True)
        return triggers[:20]

    def update_escalation_threshold(self, threshold: float) -> Dict[str, Any]:
        self.set_escalation_threshold(threshold)
        return {"threshold": self.escalation_threshold}

    def search_customer_sentiment(self, query: str) -> List[Dict[str, Any]]:
        return self.search_sentiment(query)

    def get_sentiment_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        profile = self.customer_profiles.get(customer_id)
        return profile.to_dict() if profile else None

    def get_interaction_detail(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        interaction = self.interactions.get(interaction_id)
        return interaction.to_dict() if interaction else None

    def get_customer_feedback_summary(self, customer_id: str) -> Dict[str, Any]:
        return self.get_customer_feedback(customer_id)

    def get_daily_sentiment(self, days: int = 7) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [i for i in self.interactions.values() if i.created_at >= cutoff]
        daily = defaultdict(list)
        for i in recent:
            day = i.created_at[:10]
            daily[day].append(i.sentiment.score)
        return {day: {"avg": round(sum(scores) / len(scores), 3), "count": len(scores)} for day, scores in sorted(daily.items())}

    def get_weekly_sentiment_report(self) -> Dict[str, Any]:
        overview = self.get_overview_stats()
        trends = self.get_sentiment_trends(period="weekly", days=30)
        return {
            "overview": overview,
            "weekly_trends": trends,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def delete_interaction(self, interaction_id: str) -> bool:
        if interaction_id in self.interactions:
            del self.interactions[interaction_id]
            self._save_data()
            return True
        return False

    def get_customer_risk_list(self, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for cid, profile in self.customer_profiles.items():
            if risk_level and profile.risk_level != risk_level:
                continue
            results.append(profile.to_dict())
        results.sort(key=lambda p: p.get("overall_sentiment", 0.5))
        return results[:50]

    def get_sentiment_breakdown(self, customer_id: str) -> Dict[str, Any]:
        interactions = self._get_customer_interactions(customer_id, days=90)
        by_channel = defaultdict(list)
        for i in interactions:
            by_channel[i.channel.value].append(i.sentiment.score)
        breakdown = {ch: {"avg_score": round(sum(scores) / len(scores), 3), "count": len(scores), "label": self.analyzer.classify(sum(scores) / len(scores)).value} for ch, scores in by_channel.items()}
        return {"customer_id": customer_id, "breakdown": breakdown, "total_interactions": len(interactions)}

    def get_sentiment_timeline(self, customer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        interactions = self._get_customer_interactions(customer_id, days)
        timeline = []
        for i in interactions:
            timeline.append({"date": i.created_at[:10], "score": i.sentiment.score, "channel": i.channel.value, "keywords": i.sentiment.keywords[:3]})
        timeline.sort(key=lambda t: t["date"])
        return timeline

    def get_negative_interactions(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        negative = [i.to_dict() for i in self.interactions.values() if i.created_at >= cutoff and i.sentiment.score < 0.4]
        negative.sort(key=lambda i: i.get("sentiment", {}).get("score", 0.5))
        return negative[:limit]

    def get_positive_interactions(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        positive = [i.to_dict() for i in self.interactions.values() if i.created_at >= cutoff and i.sentiment.score >= 0.7]
        positive.sort(key=lambda i: i.get("sentiment", {}).get("score", 0.5), reverse=True)
        return positive[:limit]

    def get_sentiment_alert_count(self) -> Dict[str, Any]:
        alerts = self.get_sentiment_triggers()
        return {"total_alerts": len(alerts), "high_priority": sum(1 for a in alerts if a.get("score", 0.5) < 0.3)}

    def export_sentiment_report(self, customer_id: str) -> Dict[str, Any]:
        return self.get_weekly_sentiment_report()

    def get_all_customer_profiles(self, limit: int = 100) -> List[Dict[str, Any]]:
        profiles = sorted(self.customer_profiles.values(), key=lambda p: p.overall_sentiment)
        return [p.to_dict() for p in profiles[:limit]]

    def update_profile_sentiment(self, customer_id: str, score: float, source: str = "manual") -> Optional[Dict[str, Any]]:
        profile = self.customer_profiles.get(customer_id)
        if not profile:
            return None
        interaction = self.record_interaction(customer_id=customer_id, channel=source, content=f"Manual sentiment update: {score}")
        if interaction:
            interaction.sentiment.score = score
            interaction.sentiment.label = self.analyzer.classify(score).value
            self._recalculate_profile(customer_id)
            self._save_data()
        return self.customer_profiles[customer_id].to_dict()

    def get_sentiment_milestones(self, customer_id: str) -> List[Dict[str, Any]]:
        profile = self.customer_profiles.get(customer_id)
        if not profile:
            return []
        milestones = []
        if profile.interaction_count >= 10:
            milestones.append({"name": "10 Interactions Reached", "achieved": True, "icon": "💬"})
        if profile.overall_sentiment >= 0.7:
            milestones.append({"name": "Positive Sentiment", "achieved": True, "icon": "😊"})
        if profile.overall_sentiment < 0.3 and profile.interaction_count >= 5:
            milestones.append({"name": "Needs Attention", "achieved": True, "icon": "warning"})
        return milestones


class SentimentBatchProcessor:
    def __init__(self, service: SentimentAnalysisService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_record_interactions(self, interactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        count = 0
        errors = []
        for data in interactions_data:
            try:
                interaction = self.service.record_interaction(
                    customer_id=data["customer_id"], channel=data.get("channel", "email"),
                    content=data.get("content", ""),
                )
                count += 1
                self.batch_log.append({"action": "record_interaction", "interaction_id": interaction.interaction_id, "status": "success"})
            except Exception as e:
                errors.append({"customer_id": data.get("customer_id"), "error": str(e)})
                self.batch_log.append({"action": "record_interaction", "customer_id": data.get("customer_id"), "status": "error"})
        return {"recorded": count, "errors": len(errors), "error_details": errors[:5]}

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_interactions(interactions: List[Interaction], page: int = 1, page_size: int = 20, channel: Optional[str] = None) -> Dict[str, Any]:
    filtered = [i for i in interactions if i.channel.value == channel] if channel else interactions
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [i.to_dict() for i in filtered[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_sentiment_summary(service: SentimentAnalysisService) -> Dict[str, Any]:
    profiles = list(service.customer_profiles.values())
    if not profiles:
        return {"total_profiles": 0}
    scores = [p.overall_sentiment for p in profiles]
    return {
        "total_profiles": len(profiles),
        "avg_sentiment": round(sum(scores) / len(scores), 3),
        "positive": sum(1 for p in profiles if p.overall_sentiment >= 0.7),
        "neutral": sum(1 for p in profiles if 0.4 <= p.overall_sentiment < 0.7),
        "negative": sum(1 for p in profiles if p.overall_sentiment < 0.4),
        "total_interactions": sum(p.interaction_count for p in profiles),
        "sentiment_trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "declining" if len(scores) > 1 and scores[-1] < scores[0] else "stable",
    }


def merge_sentiment_customers(service: SentimentAnalysisService, source: str, target: str) -> int:
    count = 0
    for i in service.interactions.values():
        if i.customer_id == source:
            i.customer_id = target
            count += 1
    source_profile = service.customer_profiles.pop(source, None)
    if source_profile and count:
        target_profile = service.customer_profiles.get(target)
        if target_profile:
            target_profile.overall_sentiment = (target_profile.overall_sentiment + source_profile.overall_sentiment) / 2
            target_profile.interaction_count += source_profile.interaction_count
        else:
            source_profile.customer_id = target
            service.customer_profiles[target] = source_profile
        if count:
            service._save_data()
    return count


class SentimentAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


def validate_sentiment_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    return errors


def get_top_complaint_themes(service: SentimentAnalysisService, days: int = 30) -> List[Dict[str, Any]]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    negative = [i for i in service.interactions.values() if i.created_at >= cutoff and i.sentiment.score < 0.4]
    keyword_counts: Dict[str, int] = {}
    for i in negative:
        for kw in i.sentiment.keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    return [{"theme": kw, "frequency": cnt} for kw, cnt in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

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
