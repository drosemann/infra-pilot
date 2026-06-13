"""Knowledge base and help center with searchable articles, videos, and FAQs."""

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
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ArticleType(str, Enum):
    GUIDE = "guide"
    TUTORIAL = "tutorial"
    FAQ = "faq"
    VIDEO = "video"
    REFERENCE = "reference"
    TROUBLESHOOTING = "troubleshooting"
    RELEASE_NOTE = "release_note"


@dataclass
class Article:
    article_id: str
    title: str
    slug: str
    content: str
    article_type: ArticleType
    status: ArticleStatus
    category: str
    tags: List[str] = field(default_factory=list)
    author: str = ""
    featured_image_url: Optional[str] = None
    video_url: Optional[str] = None
    estimated_read_minutes: int = 5
    related_article_ids: List[str] = field(default_factory=list)
    language: str = "en"
    version: int = 1
    view_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    published_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def helpfulness_score(self) -> float:
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return round(self.helpful_count / total, 3)


@dataclass
class ArticleFeedback:
    feedback_id: str
    article_id: str
    helpful: bool
    comment: Optional[str] = None
    user_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Category:
    category_id: str
    name: str
    slug: str
    description: str = ""
    icon: str = "📄"
    parent_category_id: Optional[str] = None
    order: int = 0
    article_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResult:
    article_id: str
    title: str
    excerpt: str
    category: str
    article_type: str
    score: float
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchEngine:
    def __init__(self):
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "was", "are",
            "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "shall", "can", "need", "dare", "ought", "used",
        }

    def tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
        return [t for t in tokens if t not in self.stop_words]

    def score_article(self, article: Article, query_tokens: Set[str]) -> Tuple[float, List[str]]:
        title_tokens = self.tokenize(article.title)
        content_tokens = self.tokenize(article.content)
        tag_tokens = [t.lower() for t in article.tags]
        category_tokens = self.tokenize(article.category)

        matched_terms = []
        score = 0.0

        for qt in query_tokens:
            if qt in title_tokens:
                score += 10.0
                matched_terms.append(qt)
            if qt in tag_tokens:
                score += 8.0
                if qt not in matched_terms:
                    matched_terms.append(qt)
            if qt in category_tokens:
                score += 5.0
                if qt not in matched_terms:
                    matched_terms.append(qt)
            content_count = content_tokens.count(qt)
            if content_count > 0:
                score += min(content_count * 0.5, 5.0)
                if qt not in matched_terms:
                    matched_terms.append(qt)

        words_in_query = len(query_tokens)
        if words_in_query > 0:
            score = score / words_in_query

        score *= 1 + (article.view_count / 1000) * 0.1
        if article.helpfulness_score() > 0.7:
            score *= 1.1

        return round(score, 2), matched_terms


class KnowledgeBaseService:
    def __init__(self, storage_path: str = "knowledge_base_data.json"):
        self.storage_path = storage_path
        self.articles: Dict[str, Article] = {}
        self.feedback: List[ArticleFeedback] = []
        self.categories: Dict[str, Category] = {}
        self.search_engine = SearchEngine()
        self._init_categories()
        self._init_default_articles()
        self._load_data()

    def _init_categories(self):
        cat_data = [
            ("cat-getting-started", "Getting Started", "getting-started", "Learn the basics and set up your account", "🚀", order=1),
            ("cat-deployment", "Deployment", "deployment", "Deploy and manage your applications", "📦", order=2),
            ("cat-monitoring", "Monitoring & Alerts", "monitoring", "Monitor performance and set up alerts", "📊", order=3),
            ("cat-backup", "Backup & Recovery", "backup", "Backup strategies and disaster recovery", "💾", order=4),
            ("cat-security", "Security", "security", "Security best practices and compliance", "🔒", order=5),
            ("cat-integration", "Integrations", "integrations", "Connect with your favorite tools", "🔗", order=6),
            ("cat-billing", "Billing & Account", "billing", "Manage billing, plans, and account settings", "💰", order=7),
            ("cat-troubleshooting", "Troubleshooting", "troubleshooting", "Common issues and solutions", "🔧", order=8),
            ("cat-advanced", "Advanced Topics", "advanced", "Deep dives and technical reference", "⚡", order=9),
        ]
        for cid, name, slug, desc, icon, order in cat_data:
            self.categories[cid] = Category(category_id=cid, name=name, slug=slug, description=desc, icon=icon, order=order)

    def _init_default_articles(self):
        defaults = [
            Article("art-quickstart", "Quick Start Guide", "quick-start-guide", "Welcome to Infra Pilot! This guide will help you get started with deploying your first application. Follow these steps:\n\n1. Create your account\n2. Set up your first server\n3. Deploy your application\n4. Configure monitoring\n5. Set up backups", ArticleType.GUIDE, ArticleStatus.PUBLISHED, "cat-getting-started", tags=["quickstart", "guide", "setup"], estimated_read_minutes=5, helpful_count=42, view_count=1520),
            Article("art-deploy-app", "How to Deploy an Application", "deploy-application", "Deploying your application with Infra Pilot is straightforward. Choose your deployment method:\n\n- **One-click deploy**: Use the dashboard to deploy from a Git repository\n- **CLI deploy**: Use the `ipilot deploy` command\n- **API deploy**: Use our REST API for automated deployments\n\nEnsure your Dockerfile or build configuration is ready.", ArticleType.TUTORIAL, ArticleStatus.PUBLISHED, "cat-deployment", tags=["deploy", "git", "ci-cd"], estimated_read_minutes=8, helpful_count=38, view_count=980),
            Article("art-monitoring-setup", "Setting Up Monitoring & Alerts", "monitoring-setup", "Configure comprehensive monitoring for your infrastructure:\n\n1. **Health Checks**: Set up HTTP, TCP, and ping checks\n2. **Metrics**: View CPU, memory, disk, and network metrics\n3. **Alerts**: Configure alert rules with multiple notification channels\n4. **Dashboards**: Create custom dashboards for key metrics", ArticleType.GUIDE, ArticleStatus.PUBLISHED, "cat-monitoring", tags=["monitoring", "alerts", "metrics"], estimated_read_minutes=6, helpful_count=31, view_count=750),
            Article("art-backup-strategy", "Backup Strategy Best Practices", "backup-strategy", "Implement a robust backup strategy:\n\n- Follow the 3-2-1 backup rule\n- Schedule automated backups\n- Test restores regularly\n- Use cross-region replication for critical data\n- Monitor backup success/failure", ArticleType.GUIDE, ArticleStatus.PUBLISHED, "cat-backup", tags=["backup", "recovery", "disaster-recovery"], estimated_read_minutes=7, helpful_count=27, view_count=620),
            Article("art-faq-general", "Frequently Asked Questions", "frequently-asked-questions", "**Q: How do I reset my password?**\nA: Go to Settings > Security and click Reset Password.\n\n**Q: What happens if I exceed my plan limits?**\nA: You'll receive a notification and can upgrade your plan.\n\n**Q: How do I cancel my subscription?**\nA: Go to Billing > Plans and click Cancel Subscription.", ArticleType.FAQ, ArticleStatus.PUBLISHED, "cat-billing", tags=["faq", "general", "account"], estimated_read_minutes=3, helpful_count=55, view_count=2100),
        ]
        for art in defaults:
            self.articles[art.article_id] = art

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for adata in data.get("articles", []):
                        article = Article(**adata)
                        self.articles[article.article_id] = article
                    for fdata in data.get("feedback", []):
                        self.feedback.append(ArticleFeedback(**fdata))
                    for cdata in data.get("categories", []):
                        cat = Category(**cdata)
                        self.categories[cat.category_id] = cat
            except Exception as e:
                logger.warning(f"Failed to load knowledge base data: {e}")

    def _save_data(self):
        try:
            data = {
                "articles": [a.to_dict() for a in self.articles.values()],
                "feedback": [f.to_dict() for f in self.feedback[-5000:]],
                "categories": [c.to_dict() for c in self.categories.values()],
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save knowledge base data: {e}")

    def create_article(
        self, title: str, content: str, category: str,
        article_type: str = "guide", tags: Optional[List[str]] = None,
        author: str = "", language: str = "en",
    ) -> Article:
        article_id = f"ART-{uuid.uuid4().hex[:8].upper()}"
        slug = title.lower().replace(" ", "-").replace("_", "-")
        slug = re.sub(r"[^a-z0-9-]", "", slug)[:80]
        article = Article(
            article_id=article_id,
            title=title,
            slug=slug,
            content=content,
            article_type=ArticleType(article_type),
            status=ArticleStatus.DRAFT,
            category=category,
            tags=tags or [],
            author=author,
            language=language,
        )
        self.articles[article_id] = article
        self._save_data()
        return article

    def publish_article(self, article_id: str) -> Optional[Article]:
        article = self.articles.get(article_id)
        if not article:
            return None
        article.status = ArticleStatus.PUBLISHED
        article.published_at = datetime.utcnow().isoformat()
        article.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return article

    def update_article(self, article_id: str, updates: Dict[str, Any]) -> Optional[Article]:
        article = self.articles.get(article_id)
        if not article:
            return None
        for key, value in updates.items():
            if hasattr(article, key) and key not in ("article_id", "created_at"):
                setattr(article, key, value)
        article.version += 1
        article.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return article

    def get_article(self, article_id: str) -> Optional[Article]:
        article = self.articles.get(article_id)
        if article:
            article.view_count += 1
            self._save_data()
        return article

    def search(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[SearchResult]:
        query_tokens = set(self.search_engine.tokenize(query))
        if not query_tokens:
            return []

        results = []
        for article in self.articles.values():
            if article.status != ArticleStatus.PUBLISHED:
                continue
            if category and article.category != category:
                continue
            score, matched = self.search_engine.score_article(article, query_tokens)
            if score > 0:
                excerpt = article.content[:200].replace("\n", " ")
                results.append(SearchResult(
                    article_id=article.article_id,
                    title=article.title,
                    excerpt=excerpt,
                    category=article.category,
                    article_type=article.article_type.value,
                    score=score,
                    matched_terms=matched,
                ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def add_feedback(self, article_id: str, helpful: bool, comment: Optional[str] = None, user_id: Optional[str] = None) -> Optional[ArticleFeedback]:
        article = self.articles.get(article_id)
        if not article:
            return None
        feedback = ArticleFeedback(
            feedback_id=f"FB-{uuid.uuid4().hex[:8].upper()}",
            article_id=article_id,
            helpful=helpful,
            comment=comment,
            user_id=user_id,
        )
        self.feedback.append(feedback)
        if helpful:
            article.helpful_count += 1
        else:
            article.not_helpful_count += 1
        self._save_data()
        return feedback

    def get_related_articles(self, article_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        article = self.articles.get(article_id)
        if not article:
            return []
        related = []
        for aid in article.related_article_ids:
            if aid in self.articles:
                rel = self.articles[aid]
                if rel.status == ArticleStatus.PUBLISHED:
                    related.append(self._article_summary(rel))
        if len(related) < limit:
            candidates = [a for a in self.articles.values() if a.article_id != article_id and a.status == ArticleStatus.PUBLISHED and a.category == article.category]
            for c in candidates:
                if c.article_id not in article.related_article_ids and len(related) < limit:
                    related.append(self._article_summary(c))
        return related[:limit]

    def _article_summary(self, article: Article) -> Dict[str, Any]:
        return {
            "article_id": article.article_id,
            "title": article.title,
            "slug": article.slug,
            "article_type": article.article_type.value,
            "category": article.category,
            "estimated_read_minutes": article.estimated_read_minutes,
            "helpfulness": article.helpfulness_score(),
        }

    def list_articles(
        self, category: Optional[str] = None, article_type: Optional[str] = None,
        status: Optional[str] = None, limit: int = 50,
    ) -> List[Dict[str, Any]]:
        results = list(self.articles.values())
        if category:
            results = [a for a in results if a.category == category]
        if article_type:
            results = [a for a in results if a.article_type.value == article_type]
        if status:
            results = [a for a in results if a.status.value == status]
        else:
            results = [a for a in results if a.status == ArticleStatus.PUBLISHED]
        results.sort(key=lambda a: a.view_count, reverse=True)
        summaries = []
        for a in results[:limit]:
            s = self._article_summary(a)
            s["view_count"] = a.view_count
            s["helpful_count"] = a.helpful_count
            s["tags"] = a.tags
            s["author"] = a.author
            s["updated_at"] = a.updated_at
            summaries.append(s)
        return summaries

    def list_categories(self) -> List[Dict[str, Any]]:
        categories = list(self.categories.values())
        categories.sort(key=lambda c: c.order)
        result = []
        for c in categories:
            c.article_count = sum(1 for a in self.articles.values() if a.category == c.category_id and a.status == ArticleStatus.PUBLISHED)
            result.append(c.to_dict())
        return result

    def get_popular_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        published = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        published.sort(key=lambda a: a.view_count, reverse=True)
        return [self._article_summary(a) for a in published[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        published = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        total_views = sum(a.view_count for a in self.articles.values())
        total_helpful = sum(a.helpful_count for a in self.articles.values())
        total_feedback = sum(a.helpful_count + a.not_helpful_count for a in self.articles.values())
        return {
            "total_articles": len(self.articles),
            "published_articles": len(published),
            "total_views": total_views,
            "total_feedback": total_feedback,
            "helpfulness_rate": round(total_helpful / max(total_feedback, 1), 3),
            "categories": len(self.categories),
        }

    def delete_article(self, article_id: str) -> bool:
        if article_id in self.articles:
            del self.articles[article_id]
            self._save_data()
            return True
        return False

    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [a.to_dict() for a in self.articles.values() if q in a.title.lower() or q in a.content.lower() or q in a.summary.lower() or any(q in t.lower() for t in a.tags)]
        results.sort(key=lambda x: x.get("helpful_votes", 0), reverse=True)
        return results[:limit]

    def get_article_stats(self, article_id: str) -> Optional[Dict[str, Any]]:
        a = self.articles.get(article_id)
        if not a:
            return None
        return {"article_id": article_id, "title": a.title, "view_count": a.view_count, "helpful_votes": len(a.helpful_votes), "not_helpful_votes": len(a.not_helpful_votes), "helpfulness_ratio": round(len(a.helpful_votes) / max(len(a.helpful_votes) + len(a.not_helpful_votes), 1), 3), "category": a.category.value if a.category else None, "tags": a.tags}

    def vote_helpful(self, article_id: str, user_id: str) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        if user_id not in a.helpful_votes:
            a.helpful_votes.append(user_id)
            if user_id in a.not_helpful_votes:
                a.not_helpful_votes.remove(user_id)
            self._save_data()
        return True

    def vote_not_helpful(self, article_id: str, user_id: str) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        if user_id not in a.not_helpful_votes:
            a.not_helpful_votes.append(user_id)
            if user_id in a.helpful_votes:
                a.helpful_votes.remove(user_id)
            self._save_data()
        return True

    def get_popular_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        ranked = sorted(self.articles.values(), key=lambda a: a.view_count, reverse=True)
        return [a.to_dict() for a in ranked[:limit]]

    def get_unhelpful_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        unhelpful = [a for a in self.articles.values() if len(a.not_helpful_votes) > len(a.helpful_votes)]
        unhelpful.sort(key=lambda a: len(a.not_helpful_votes), reverse=True)
        return [a.to_dict() for a in unhelpful[:limit]]

    def get_articles_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.articles.values() if tag.lower() in [t.lower() for t in a.tags]]

    def update_article(self, article_id: str, updates: Dict[str, Any]) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        if "title" in updates: a.title = updates["title"]
        if "content" in updates: a.content = updates["content"]
        if "summary" in updates: a.summary = updates["summary"]
        if "tags" in updates: a.tags = updates["tags"]
        if "category" in updates: a.category = ArticleCategory(updates["category"]) if isinstance(updates["category"], str) else updates["category"]
        a.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def bulk_import_articles(self, articles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        imported = 0
        errors = []
        for data in articles_data:
            try:
                aid = str(uuid.uuid4())[:8]
                cat = ArticleCategory(data.get("category", "general")) if isinstance(data.get("category"), str) else ArticleCategory.GENERAL
                article = Article(article_id=aid, title=data["title"], content=data["content"], summary=data.get("summary", ""), tags=data.get("tags", []), category=cat, author_id=data.get("author_id", "system"), author_name=data.get("author_name", "System"))
                self.articles[aid] = article
                imported += 1
            except Exception as e:
                errors.append({"data": data, "error": str(e)})
        self._save_data()
        return {"imported": imported, "errors": len(errors), "error_details": errors[:5]}

    def get_category_breakdown(self) -> Dict[str, int]:
        breakdown = defaultdict(int)
        for a in self.articles.values():
            breakdown[a.category.value] += 1
        return dict(breakdown)

    def get_suggested_articles(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        q = query.lower()
        scored = []
        for a in self.articles.values():
            score = 0
            if q in a.title.lower(): score += 10
            if q in a.tags: score += 5
            if q in a.content.lower(): score += 3
            if q in a.summary.lower(): score += 2
            if score > 0:
                scored.append((a, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [a.to_dict() for a, _ in scored[:limit]]

    def archive_article(self, article_id: str) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        a.status = "archived"
        self._save_data()
        return True

    def restore_article(self, article_id: str) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        a.status = "published"
        self._save_data()
        return True

    def get_draft_articles(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.articles.values() if a.status == "draft"]

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        total = len(self.articles)
        published = sum(1 for a in self.articles.values() if a.status == "published")
        total_views = sum(a.view_count for a in self.articles.values())
        total_helpful = sum(len(a.helpful_votes) for a in self.articles.values())
        return {"total_articles": total, "published": published, "drafts": sum(1 for a in self.articles.values() if a.status == "draft"), "archived": sum(1 for a in self.articles.values() if a.status == "archived"), "total_views": total_views, "total_helpful_votes": total_helpful}

    def get_article_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        for a in self.articles.values():
            if a.slug == slug and a.status == ArticleStatus.PUBLISHED:
                a.view_count += 1
                self._save_data()
                return a.to_dict()
        return None

    def get_articles_by_author(self, author: str) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.articles.values() if a.author == author and a.status == ArticleStatus.PUBLISHED]

    def get_articles_by_type(self, article_type: str) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.articles.values() if a.article_type.value == article_type and a.status == ArticleStatus.PUBLISHED]

    def get_related_content(self, article_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self.get_related_articles(article_id, limit)

    def vote_helpful(self, article_id: str) -> Dict[str, Any]:
        a = self.articles.get(article_id)
        if not a:
            return {"error": "Article not found"}
        a.helpful_count += 1
        self._save_data()
        return {"article_id": article_id, "helpful_count": a.helpful_count}

    def vote_not_helpful(self, article_id: str) -> Dict[str, Any]:
        a = self.articles.get(article_id)
        if not a:
            return {"error": "Article not found"}
        a.not_helpful_count += 1
        self._save_data()
        return {"article_id": article_id, "not_helpful_count": a.not_helpful_count}

    def get_helpfulness_report(self) -> Dict[str, Any]:
        articles = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        total = len(articles)
        high_helpfulness = sum(1 for a in articles if a.helpfulness_score() >= 0.8)
        low_helpfulness = sum(1 for a in articles if a.helpfulness_score() < 0.5 and (a.helpful_count + a.not_helpful_count) > 0)
        return {
            "total_articles": total,
            "high_helpfulness_count": high_helpfulness,
            "high_helpfulness_pct": round(high_helpfulness / max(total, 1) * 100, 1),
            "low_helpfulness_count": low_helpfulness,
            "low_helpfulness_pct": round(low_helpfulness / max(total, 1) * 100, 1),
            "needs_review": [a.to_dict() for a in articles if a.helpfulness_score() < 0.5 and (a.helpful_count + a.not_helpful_count) > 5][:10],
        }

    def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        results = self.search(query, limit=limit)
        return [r.title for r in results]

    def get_featured_articles(self, limit: int = 5) -> List[Dict[str, Any]]:
        published = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        scored = [(a, a.helpfulness_score() * 0.4 + a.view_count / 1000 * 0.3 + (1 if a.estimated_read_minutes < 10 else 0) * 0.3) for a in published]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [a.to_dict() for a, _ in scored[:limit]]

    def get_category_hierarchy(self) -> List[Dict[str, Any]]:
        categories = self.list_categories()
        for c in categories:
            children = [cat for cat in categories if cat.get("parent_category_id") == c.get("category_id")]
            c["children"] = children
        return [c for c in categories if not c.get("parent_category_id")]

    def get_article_templates(self, article_type: str = "guide") -> Dict[str, Any]:
        templates = {
            "guide": {"structure": ["Introduction", "Prerequisites", "Step-by-Step", "Verification", "Troubleshooting"]},
            "tutorial": {"structure": ["Overview", "Setup", "Implementation", "Testing", "Next Steps"]},
            "faq": {"structure": ["Question", "Answer", "Related Questions"]},
            "troubleshooting": {"structure": ["Symptoms", "Cause", "Solution", "Prevention"]},
        }
        return templates.get(article_type, templates["guide"])

    def get_content_gaps(self) -> List[Dict[str, Any]]:
        gaps = []
        for cat_id, category in self.categories.items():
            article_count = sum(1 for a in self.articles.values() if a.category == cat_id and a.status == ArticleStatus.PUBLISHED)
            if article_count < 3:
                gaps.append({
                    "category_id": cat_id,
                    "category_name": category.name,
                    "article_count": article_count,
                    "gap": 3 - article_count,
                    "suggestion": f"Create at least {3 - article_count} more article(s) in {category.name}",
                })
        return gaps

    def get_category_stats(self, category_id: str) -> Dict[str, Any]:
        cat = self.categories.get(category_id)
        if not cat:
            return {}
        articles = [a for a in self.articles.values() if a.category == category_id and a.status == ArticleStatus.PUBLISHED]
        return {
            "category_id": category_id,
            "name": cat.name,
            "article_count": len(articles),
            "total_views": sum(a.view_count for a in articles),
            "avg_helpfulness": round(sum(a.helpfulness_score() for a in articles) / max(len(articles), 1), 3),
            "top_articles": sorted([{"title": a.title, "views": a.view_count} for a in articles], key=lambda x: x["views"], reverse=True)[:5],
        }

    def duplicate_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        a = self.articles.get(article_id)
        if not a:
            return None
        new_id = f"ART-{uuid.uuid4().hex[:8].upper()}"
        new_article = Article(
            article_id=new_id, title=f"Copy of {a.title}", slug=f"copy-of-{a.slug}",
            content=a.content, article_type=a.article_type, status=ArticleStatus.DRAFT,
            category=a.category, tags=list(a.tags), author=a.author,
        )
        self.articles[new_id] = new_article
        self._save_data()
        return new_article.to_dict()

    def get_article_recommendations(self, customer_interests: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        scored = []
        for a in self.articles.values():
            if a.status != ArticleStatus.PUBLISHED:
                continue
            match_score = sum(3 for i in customer_interests if i.lower() in a.title.lower())
            match_score += sum(2 for i in customer_interests if any(i.lower() == t.lower() for t in a.tags))
            match_score += sum(1 for i in customer_interests if i.lower() in a.content.lower())
            if match_score > 0:
                scored.append((match_score, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a.to_dict() for _, a in scored[:limit]]

    def update_article_status(self, article_id: str, status: str) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        if status == "publish":
            self.publish_article(article_id)
        elif status == "archive":
            a.status = ArticleStatus.ARCHIVED
        elif status == "draft":
            a.status = ArticleStatus.DRAFT
        else:
            return False
        self._save_data()
        return True

    def batch_update_articles(self, article_ids: List[str], updates: Dict[str, Any]) -> int:
        count = 0
        for aid in article_ids:
            if self.update_article(aid, updates):
                count += 1
        return count

    def export_articles_json(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.articles.values()]

    def get_missing_translations(self) -> List[Dict[str, Any]]:
        primary = [a for a in self.articles.values() if a.language == "en"]
        missing = []
        for a in primary:
            has_translation = any(other.article_id.startswith(a.article_id) and other.language != "en" for other in self.articles.values())
            if not has_translation:
                missing.append({"article_id": a.article_id, "title": a.title, "languages_missing": ["es", "fr", "de", "ja"]})
        return missing[:20]

    def get_article_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        for a in self.articles.values():
            if a.slug == slug and a.status == ArticleStatus.PUBLISHED:
                return a.to_dict()
        return None

    def get_popular_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        published = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        published.sort(key=lambda a: a.view_count, reverse=True)
        return [a.to_dict() for a in published[:limit]]

    def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        published = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        published.sort(key=lambda a: a.created_at, reverse=True)
        return [a.to_dict() for a in published[:limit]]

    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for a in self.articles.values():
            if a.status != ArticleStatus.PUBLISHED:
                continue
            if q in a.title.lower() or q in a.content.lower() or any(q in t.lower() for t in a.tags):
                results.append(a.to_dict())
        results.sort(key=lambda r: r.get("view_count", 0), reverse=True)
        return results[:limit]

    def get_articles_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED and any(t.lower() == tag.lower() for t in a.tags)]

    def get_statistics(self) -> Dict[str, Any]:
        published = [a for a in self.articles.values() if a.status == ArticleStatus.PUBLISHED]
        drafts = [a for a in self.articles.values() if a.status == ArticleStatus.DRAFT]
        archived = [a for a in self.articles.values() if a.status == ArticleStatus.ARCHIVED]
        total_views = sum(a.view_count for a in published)
        total_helpful = sum(a.helpful_count for a in published)
        total_unhelpful = sum(a.unhelpful_count for a in published)
        return {
            "total_articles": len(self.articles),
            "published": len(published),
            "drafts": len(drafts),
            "archived": len(archived),
            "total_views": total_views,
            "helpfulness_rate": round(total_helpful / max(total_helpful + total_unhelpful, 1), 3),
            "categories": len(self.categories),
            "authors": len(set(a.author for a in self.articles.values())),
        }

    def get_weekly_report(self) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        new_articles = [a for a in self.articles.values() if a.created_at >= cutoff]
        recent_views = sum(a.view_count for a in self.articles.values() if a.updated_at >= cutoff)
        return {
            "new_articles": len(new_articles),
            "recent_views": recent_views,
            "articles_published": sum(1 for a in new_articles if a.status == ArticleStatus.PUBLISHED),
        }

    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent = [a for a in self.articles.values() if a.updated_at >= cutoff and a.status == ArticleStatus.PUBLISHED]
        tag_counts = Counter(tag for a in recent for tag in a.tags)
        return [{"topic": tag, "count": cnt, "articles": sum(1 for a in recent if tag in a.tags)} for tag, cnt in tag_counts.most_common(limit)]

    def merge_categories(self, source_id: str, target_id: str) -> bool:
        if source_id not in self.categories or target_id not in self.categories:
            return False
        for a in self.articles.values():
            if a.category == source_id:
                a.category = target_id
        del self.categories[source_id]
        self._save_data()
        return True

    def get_article_feedback(self, article_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        a = self.articles.get(article_id)
        if not a:
            return []
        return [{"feedback_id": f"FB-{i}", "rating": "helpful" if i % 2 == 0 else "unhelpful", "comment": f"Feedback on {a.title}"} for i in range(min(limit, a.helpful_count + a.unhelpful_count))]

    def set_article_featured(self, article_id: str, featured: bool = True) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        a.is_featured = featured
        a.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_unreviewed_articles(self) -> List[Dict[str, Any]]:
        unreviewed = [a.to_dict() for a in self.articles.values() if a.status == ArticleStatus.DRAFT or a.status == ArticleStatus.ARCHIVED]
        unreviewed.sort(key=lambda a: a.get("created_at", ""), reverse=True)
        return unreviewed

    def schedule_article_publish(self, article_id: str, publish_at: str) -> bool:
        a = self.articles.get(article_id)
        if not a:
            return False
        a.scheduled_publish_at = publish_at
        a.status = ArticleStatus.DRAFT
        self._save_data()
        return True

    def process_scheduled_publishes(self) -> int:
        now = datetime.utcnow().isoformat()
        published = 0
        for a in self.articles.values():
            if a.scheduled_publish_at and a.scheduled_publish_at <= now and a.status == ArticleStatus.DRAFT:
                self.publish_article(a.article_id)
                a.scheduled_publish_at = None
                published += 1
        return published


class KnowledgeBaseBatchProcessor:
    def __init__(self, service: KnowledgeBaseService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_create_articles(self, articles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        count = 0
        errors = []
        for data in articles_data:
            try:
                a = self.service.create_article(
                    title=data["title"], content=data["content"],
                    category=data.get("category", "general"),
                    author=data.get("author", ""), tags=data.get("tags", []),
                )
                count += 1
                self.batch_log.append({"action": "create_article", "article_id": a.article_id, "status": "success"})
            except Exception as e:
                errors.append({"title": data.get("title"), "error": str(e)})
                self.batch_log.append({"action": "create_article", "title": data.get("title"), "status": "error"})
        return {"created": count, "errors": len(errors), "error_details": errors[:5]}

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_articles(articles: List[Article], page: int = 1, page_size: int = 20, status: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    filtered = [a for a in articles if (not status or a.status.value == status) and (not category or a.category == category)]
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [a.to_dict() for a in filtered[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_knowledge_base_health(service: KnowledgeBaseService) -> Dict[str, Any]:
    articles = list(service.articles.values())
    published = [a for a in articles if a.status == ArticleStatus.PUBLISHED]
    avg_views = sum(a.view_count for a in published) / max(len(published), 1)
    helpfulness_ratios = []
    for a in published:
        total_fb = a.helpful_count + a.unhelpful_count
        if total_fb > 0:
            helpfulness_ratios.append(a.helpful_count / total_fb)
    avg_helpfulness = sum(helpfulness_ratios) / max(len(helpfulness_ratios), 1) if helpfulness_ratios else 0
    return {
        "total_articles": len(articles),
        "published": len(published),
        "avg_views": round(avg_views, 1),
        "avg_helpfulness": round(avg_helpfulness, 3),
        "coverage_gaps": len(service.categories) - len(set(a.category for a in published)),
    }


class KnowledgeBaseAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


def validate_kb_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if not config.get("storage_path"):
        errors.append("storage_path is required")
    return errors


def merge_knowledge_base_categories(service: KnowledgeBaseService, source: str, target: str) -> int:
    if source not in service.categories or target not in service.categories:
        return 0
    count = 0
    for a in service.articles.values():
        if a.category == source:
            a.category = target
            count += 1
    del service.categories[source]
    if count:
        service._save_data()
    return count


def get_article_recommendations(service: KnowledgeBaseService, search_tags: List[str], limit: int = 5) -> List[Dict[str, Any]]:
    scored = []
    for a in service.articles.values():
        if a.status != ArticleStatus.PUBLISHED:
            continue
        score = sum(3 for t in search_tags if t in a.tags)
        score += a.view_count * 0.01
        if score > 0:
            scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a.to_dict() for _, a in scored[:limit]]

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
