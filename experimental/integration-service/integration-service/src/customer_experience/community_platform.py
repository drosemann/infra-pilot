"""Community platform with forums, feature voting, Q&A, and gamification."""

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


class PostType(str, Enum):
    DISCUSSION = "discussion"
    QUESTION = "question"
    FEATURE_REQUEST = "feature_request"
    ANNOUNCEMENT = "announcement"
    TUTORIAL = "tutorial"
    SHOWCASE = "showcase"


class PostStatus(str, Enum):
    PUBLISHED = "published"
    HIDDEN = "hidden"
    PINNED = "pinned"
    LOCKED = "locked"
    ARCHIVED = "archived"


class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class BadgeType(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class ForumCategory:
    category_id: str
    name: str
    slug: str
    description: str = ""
    icon: str = "💬"
    color: str = "#6366f1"
    post_count: int = 0
    thread_count: int = 0
    order: int = 0
    moderators: List[str] = field(default_factory=list)
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommunityPost:
    post_id: str
    title: str
    content: str
    post_type: PostType
    status: PostStatus
    category_id: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    view_count: int = 0
    tags: List[str] = field(default_factory=list)
    is_answered: bool = False
    accepted_answer_id: Optional[str] = None
    feature_votes: int = 0
    feature_status: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    pinned_until: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def score(self) -> int:
        return self.upvotes - self.downvotes

    def hotness(self) -> float:
        score = self.score()
        hours_since_creation = (datetime.utcnow() - datetime.fromisoformat(self.created_at)).total_seconds() / 3600
        return (score - 1) / pow(max(hours_since_creation + 2, 1), 1.5)


@dataclass
class Comment:
    comment_id: str
    post_id: str
    parent_comment_id: Optional[str] = None
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    body: str
    upvotes: int = 0
    downvotes: int = 0
    is_answer: bool = False
    is_accepted_answer: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    edited: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserReputation:
    user_id: str
    username: str
    reputation: int = 0
    badges: List[Dict[str, Any]] = field(default_factory=list)
    post_count: int = 0
    comment_count: int = 0
    upvotes_received: int = 0
    accepted_answers: int = 0
    feature_requests_made: int = 0
    level: int = 1
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def calculate_level(self) -> int:
        thresholds = [0, 50, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        for level, threshold in enumerate(thresholds):
            if self.reputation < threshold:
                return level
        return len(thresholds)


class CommunityPlatformService:
    def __init__(self, storage_path: str = "community_data.json"):
        self.storage_path = storage_path
        self.posts: Dict[str, CommunityPost] = {}
        self.comments: Dict[str, Comment] = {}
        self.categories: Dict[str, ForumCategory] = {}
        self.reputations: Dict[str, UserReputation] = {}
        self._init_categories()
        self._load_data()

    def _init_categories(self):
        cat_data = [
            ("cat-general", "General Discussion", "general-discussion", "Chat about anything related to the platform", "💬", "#6366f1", 1),
            ("cat-feature-requests", "Feature Requests", "feature-requests", "Suggest and vote on new features", "💡", "#f59e0b", 2),
            ("cat-help", "Help & Support", "help-support", "Get help from the community", "🆘", "#10b981", 3),
            ("cat-showcase", "Showcase", "showcase", "Share what you've built with Infra Pilot", "🌟", "#ec4899", 4),
            ("cat-tutorials", "Tutorials & Guides", "tutorials-guides", "Community-contributed tutorials", "📚", "#8b5cf6", 5),
            ("cat-announcements", "Announcements", "announcements", "Official product updates and news", "📢", "#ef4444", 6),
            ("cat-feedback", "Feedback", "feedback", "Share your thoughts on the platform", "💭", "#06b6d4", 7),
        ]
        for cid, name, slug, desc, icon, color, order in cat_data:
            self.categories[cid] = ForumCategory(category_id=cid, name=name, slug=slug, description=desc, icon=icon, color=color, order=order)

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for pdata in data.get("posts", []):
                        post = CommunityPost(**pdata)
                        self.posts[post.post_id] = post
                    for cdata in data.get("comments", []):
                        comment = Comment(**cdata)
                        self.comments[comment.comment_id] = comment
                    for cdata in data.get("categories", []):
                        cat = ForumCategory(**cdata)
                        self.categories[cat.category_id] = cat
                    for rdata in data.get("reputations", []):
                        rep = UserReputation(**rdata)
                        self.reputations[rep.user_id] = rep
            except Exception as e:
                logger.warning(f"Failed to load community data: {e}")

    def _save_data(self):
        try:
            data = {
                "posts": [p.to_dict() for p in self.posts.values()],
                "comments": [c.to_dict() for c in self.comments.values()],
                "categories": [c.to_dict() for c in self.categories.values()],
                "reputations": [r.to_dict() for r in self.reputations.values()],
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save community data: {e}")

    def _get_or_create_reputation(self, user_id: str, username: str = "") -> UserReputation:
        if user_id not in self.reputations:
            self.reputations[user_id] = UserReputation(user_id=user_id, username=username or f"User-{user_id[:6]}")
        return self.reputations[user_id]

    def _update_reputation(self, user_id: str, delta: int, username: str = ""):
        rep = self._get_or_create_reputation(user_id, username)
        rep.reputation = max(0, rep.reputation + delta)
        rep.last_active_at = datetime.utcnow().isoformat()
        new_level = rep.calculate_level()
        if new_level > rep.level:
            logger.info(f"User {user_id} leveled up to {new_level}")
        rep.level = new_level
        self._check_badges(rep)
        self._save_data()

    def _check_badges(self, rep: UserReputation):
        badge_defs = [
            (BadgeType.BRONZE, "First Post", lambda r: r.post_count >= 1),
            (BadgeType.BRONZE, "First Upvote", lambda r: r.upvotes_received >= 1),
            (BadgeType.SILVER, "Popular Contributor", lambda r: r.upvotes_received >= 25),
            (BadgeType.SILVER, "Answered", lambda r: r.accepted_answers >= 5),
            (BadgeType.GOLD, "Top Contributor", lambda r: r.upvotes_received >= 100),
            (BadgeType.GOLD, "Expert", lambda r: r.accepted_answers >= 25),
            (BadgeType.PLATINUM, "Legend", lambda r: r.reputation >= 10000),
            (BadgeType.BRONZE, "Feature Advocate", lambda r: r.feature_requests_made >= 3),
        ]
        existing = {b["name"] for b in rep.badges}
        for btype, name, condition in badge_defs:
            if name not in existing and condition(rep):
                rep.badges.append({
                    "type": btype.value,
                    "name": name,
                    "awarded_at": datetime.utcnow().isoformat(),
                })

    def create_post(
        self, title: str, content: str, category_id: str,
        post_type: str = "discussion", author_id: str = "", author_name: str = "",
        tags: Optional[List[str]] = None,
    ) -> CommunityPost:
        post_id = f"PST-{uuid.uuid4().hex[:8].upper()}"
        post = CommunityPost(
            post_id=post_id, title=title, content=content,
            post_type=PostType(post_type), status=PostStatus.PUBLISHED,
            category_id=category_id, author_id=author_id,
            author_name=author_name, tags=tags or [],
            feature_votes=1 if post_type == "feature_request" else 0,
        )
        self.posts[post_id] = post
        if category_id in self.categories:
            self.categories[category_id].post_count += 1
            self.categories[category_id].thread_count += 1
        rep = self._get_or_create_reputation(author_id, author_name)
        rep.post_count += 1
        if post.post_type == PostType.FEATURE_REQUEST:
            rep.feature_requests_made += 1
        self._update_reputation(author_id, 10, author_name)
        self._save_data()
        return post

    def get_post(self, post_id: str) -> Optional[CommunityPost]:
        post = self.posts.get(post_id)
        if post:
            post.view_count += 1
            self._save_data()
        return post

    def add_comment(
        self, post_id: str, author_id: str, author_name: str,
        body: str, parent_comment_id: Optional[str] = None,
    ) -> Optional[Comment]:
        post = self.posts.get(post_id)
        if not post or post.status in (PostStatus.LOCKED, PostStatus.ARCHIVED):
            return None
        comment_id = f"CMT-{uuid.uuid4().hex[:8].upper()}"
        comment = Comment(
            comment_id=comment_id, post_id=post_id,
            parent_comment_id=parent_comment_id,
            author_id=author_id, author_name=author_name, body=body,
        )
        self.comments[comment_id] = comment
        post.comment_count += 1
        post.last_activity_at = datetime.utcnow().isoformat()
        rep = self._get_or_create_reputation(author_id, author_name)
        rep.comment_count += 1
        self._update_reputation(author_id, 2, author_name)
        self._save_data()
        return comment

    def vote_post(self, post_id: str, user_id: str, vote_type: str) -> Optional[CommunityPost]:
        post = self.posts.get(post_id)
        if not post or post.author_id == user_id:
            return None
        if vote_type == "upvote":
            post.upvotes += 1
            if post.post_type == PostType.FEATURE_REQUEST:
                post.feature_votes += 1
            self._update_reputation(post.author_id, 5)
        else:
            post.downvotes += 1
            self._update_reputation(post.author_id, -2)
        self._save_data()
        return post

    def vote_comment(self, comment_id: str, user_id: str, vote_type: str) -> Optional[Comment]:
        comment = self.comments.get(comment_id)
        if not comment or comment.author_id == user_id:
            return None
        if vote_type == "upvote":
            comment.upvotes += 1
            self._update_reputation(comment.author_id, 3)
        else:
            comment.downvotes += 1
            self._update_reputation(comment.author_id, -1)
        self._save_data()
        return comment

    def mark_accepted_answer(self, post_id: str, comment_id: str) -> Optional[Dict[str, Any]]:
        post = self.posts.get(post_id)
        comment = self.comments.get(comment_id)
        if not post or not comment or comment.post_id != post_id:
            return None
        post.is_answered = True
        post.accepted_answer_id = comment_id
        comment.is_accepted_answer = True
        self._update_reputation(comment.author_id, 25)
        self._save_data()
        return {"post_id": post_id, "comment_id": comment_id}

    def list_posts(
        self, category_id: Optional[str] = None, post_type: Optional[str] = None,
        sort: str = "hot", limit: int = 50, offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        results = list(self.posts.values())
        if category_id:
            results = [p for p in results if p.category_id == category_id]
        if post_type:
            results = [p for p in results if p.post_type.value == post_type]
        results = [p for p in results if p.status in (PostStatus.PUBLISHED, PostStatus.PINNED)]

        if sort == "new":
            results.sort(key=lambda p: p.created_at, reverse=True)
        elif sort == "top":
            results.sort(key=lambda p: p.score(), reverse=True)
        elif sort == "featured":
            results.sort(key=lambda p: (p.status == PostStatus.PINNED, p.hotness()), reverse=True)
        else:
            results.sort(key=lambda p: (p.status == PostStatus.PINNED, p.hotness()), reverse=True)

        pinned = [p for p in results if p.status == PostStatus.PINNED]
        regular = [p for p in results if p.status != PostStatus.PINNED]
        sorted_posts = pinned + regular
        total = len(sorted_posts)
        page = sorted_posts[offset:offset + limit]
        return [p.to_dict() for p in page], total

    def get_comments(self, post_id: str) -> List[Dict[str, Any]]:
        comments = [c for c in self.comments.values() if c.post_id == post_id]
        comments.sort(key=lambda c: (-1 if c.is_accepted_answer else 0, -c.upvotes, c.created_at))
        return [c.to_dict() for c in comments]

    def get_feature_requests(self, sort: str = "votes", limit: int = 50) -> List[Dict[str, Any]]:
        requests = [p for p in self.posts.values() if p.post_type == PostType.FEATURE_REQUEST and p.status == PostStatus.PUBLISHED]
        if sort == "votes":
            requests.sort(key=lambda p: p.feature_votes, reverse=True)
        elif sort == "new":
            requests.sort(key=lambda p: p.created_at, reverse=True)
        elif sort == "status":
            status_order = {"planned": 0, "in_progress": 1, "completed": 2, "under_review": 3, None: 4}
            requests.sort(key=lambda p: (status_order.get(p.feature_status, 4), -p.feature_votes))
        return [p.to_dict() for p in requests[:limit]]

    def update_feature_status(self, post_id: str, status: str) -> Optional[CommunityPost]:
        post = self.posts.get(post_id)
        if not post or post.post_type != PostType.FEATURE_REQUEST:
            return None
        post.feature_status = status
        post.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return post

    def get_user_reputation(self, user_id: str) -> Optional[UserReputation]:
        return self.reputations.get(user_id)

    def get_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        users = list(self.reputations.values())
        users.sort(key=lambda u: u.reputation, reverse=True)
        result = []
        for i, u in enumerate(users[:limit]):
            result.append({
                "rank": i + 1,
                "user_id": u.user_id,
                "username": u.username,
                "reputation": u.reputation,
                "level": u.level,
                "badges": u.badges,
                "post_count": u.post_count,
                "accepted_answers": u.accepted_answers,
            })
        return result

    def get_stats(self) -> Dict[str, Any]:
        total_posts = len(self.posts)
        total_comments = len(self.comments)
        total_feature_requests = sum(1 for p in self.posts.values() if p.post_type == PostType.FEATURE_REQUEST)
        total_users = len(self.reputations)
        return {
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_feature_requests": total_feature_requests,
            "total_users": total_users,
            "total_categories": len(self.categories),
            "popular_categories": [
                {"name": c.name, "post_count": c.post_count}
                for c in sorted(self.categories.values(), key=lambda x: x.post_count, reverse=True)[:5]
            ],
        }

    def get_categories(self) -> List[Dict[str, Any]]:
        cats = sorted(self.categories.values(), key=lambda c: c.order)
        return [c.to_dict() for c in cats]

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        post = self.posts.get(post_id)
        return post.to_dict() if post else None

    def update_post(self, post_id: str, content: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        if content:
            post.content = content
        if tags is not None:
            post.tags = tags
        post.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def delete_post(self, post_id: str) -> bool:
        if post_id in self.posts:
            del self.posts[post_id]
            self._save_data()
            return True
        return False

    def add_comment(self, post_id: str, author_id: str, author_name: str, content: str) -> Optional[Dict[str, Any]]:
        post = self.posts.get(post_id)
        if not post:
            return None
        comment = Comment(comment_id=str(uuid.uuid4())[:8], post_id=post_id, author_id=author_id, author_name=author_name, content=content)
        post.comments.append(comment)
        post.comment_count = len(post.comments)
        post.updated_at = datetime.utcnow()
        self._save_data()
        return comment.to_dict()

    def like_post(self, post_id: str, user_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        if user_id not in post.likes:
            post.likes.append(user_id)
            post.like_count = len(post.likes)
            self._save_data()
        return True

    def unlike_post(self, post_id: str, user_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        if user_id in post.likes:
            post.likes.remove(user_id)
            post.like_count = len(post.likes)
            self._save_data()
        return True

    def get_trending_posts(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [p for p in self.posts.values() if p.created_at >= cutoff]
        scored = [(p, p.like_count * 3 + p.comment_count * 2 + p.view_count) for p in recent]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p.to_dict() for p, _ in scored[:limit]]

    def get_user_contributions(self, author_id: str) -> Dict[str, Any]:
        posts = [p.to_dict() for p in self.posts.values() if p.author_id == author_id]
        comments = []
        for p in self.posts.values():
            for c in p.comments:
                if c.author_id == author_id:
                    comments.append(c.to_dict())
        return {"posts": len(posts), "comments": len(comments), "total_likes": sum(p.get("like_count", 0) for p in posts), "total_views": sum(p.get("view_count", 0) for p in posts)}

    def search_posts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = [p.to_dict() for p in self.posts.values() if q in p.title.lower() or q in p.content.lower() or any(q in t.lower() for t in p.tags)]
        results.sort(key=lambda x: x.get("like_count", 0), reverse=True)
        return results[:limit]

    def create_category(self, name: str, description: str = "", order: int = 0) -> Dict[str, Any]:
        cid = str(uuid.uuid4())[:8]
        cat = Category(category_id=cid, name=name, description=description, order=order)
        self.categories[cid] = cat
        self._save_data()
        return cat.to_dict()

    def update_category(self, category_id: str, name: Optional[str] = None, description: Optional[str] = None, order: Optional[int] = None) -> bool:
        cat = self.categories.get(category_id)
        if not cat:
            return False
        if name:
            cat.name = name
        if description is not None:
            cat.description = description
        if order is not None:
            cat.order = order
        self._save_data()
        return True

    def delete_category(self, category_id: str) -> bool:
        if category_id in self.categories:
            del self.categories[category_id]
            self._save_data()
            return True
        return False

    def get_community_summary(self) -> Dict[str, Any]:
        total_posts = len(self.posts)
        total_comments = sum(p.comment_count for p in self.posts.values())
        total_likes = sum(p.like_count for p in self.posts.values())
        unique_authors = len(set(p.author_id for p in self.posts.values()))
        top_category = max(self.categories.values(), key=lambda c: c.post_count, default=None)
        return {"total_posts": total_posts, "total_comments": total_comments, "total_likes": total_likes, "unique_authors": unique_authors, "categories": len(self.categories), "top_category": top_category.name if top_category else None}

    def get_author_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        authors = defaultdict(lambda: {"posts": 0, "comments": 0, "likes": 0, "views": 0})
        for p in self.posts.values():
            authors[p.author_id]["posts"] += 1
            authors[p.author_id]["likes"] += p.like_count
            authors[p.author_id]["views"] += p.view_count
            for c in p.comments:
                authors[c.author_id]["comments"] += 1
        ranked = [{"author_id": aid, **stats} for aid, stats in authors.items()]
        ranked.sort(key=lambda x: x["posts"] + x["comments"], reverse=True)
        return ranked[:limit]

    def flag_post(self, post_id: str, reason: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.flagged = True
        if reason not in post.metadata.get("flags", []):
            post.metadata.setdefault("flags", []).append(reason)
        self._save_data()
        return True

    def moderate_post(self, post_id: str, action: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        if action == "approve":
            post.flagged = False
        elif action == "hide":
            post.visibility = "hidden"
        elif action == "show":
            post.visibility = "public"
        else:
            return False
        self._save_data()
        return True

    def pin_post(self, post_id: str, duration_hours: Optional[int] = None) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.status = PostStatus.PINNED
        if duration_hours:
            post.pinned_until = (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat()
        self._save_data()
        return True

    def unpin_post(self, post_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.status = PostStatus.PUBLISHED
        post.pinned_until = None
        self._save_data()
        return True

    def lock_post(self, post_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.status = PostStatus.LOCKED
        self._save_data()
        return True

    def archive_post(self, post_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.status = PostStatus.ARCHIVED
        self._save_data()
        return True

    def get_similar_posts(self, post_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        post = self.posts.get(post_id)
        if not post:
            return []
        post_tags = set(t.lower() for t in post.tags)
        scored = []
        for p in self.posts.values():
            if p.post_id == post_id or p.status != PostStatus.PUBLISHED:
                continue
            tag_overlap = len(post_tags & set(t.lower() for t in p.tags))
            same_category = 1 if p.category_id == post.category_id else 0
            score = tag_overlap * 3 + same_category * 2
            if score > 0:
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p.to_dict() for _, p in scored[:limit]]

    def get_daily_active_users(self, days: int = 7) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        daily = defaultdict(set)
        for p in self.posts.values():
            if p.created_at >= cutoff:
                daily[p.created_at[:10]].add(p.author_id)
        for c in self.comments.values():
            if c.created_at >= cutoff:
                daily[c.created_at[:10]].add(c.author_id)
        return {day: len(users) for day, users in sorted(daily.items())}

    def get_post_engagement(self, post_id: str) -> Dict[str, Any]:
        post = self.posts.get(post_id)
        if not post:
            return {}
        comments = [c for c in self.comments.values() if c.post_id == post_id]
        total_votes = post.upvotes + post.downvotes
        return {
            "post_id": post_id,
            "views": post.view_count,
            "upvotes": post.upvotes,
            "downvotes": post.downvotes,
            "net_score": post.score(),
            "comments": len(comments),
            "engagement_score": post.view_count + post.upvotes * 3 + len(comments) * 2,
            "hotness": post.hotness(),
        }

    def search_tags(self, tag: str) -> List[Dict[str, Any]]:
        tag_lower = tag.lower()
        results = [p.to_dict() for p in self.posts.values() if any(tag_lower == t.lower() for t in p.tags)]
        results.sort(key=lambda x: x.get("upvotes", 0), reverse=True)
        return results[:20]

    def get_user_activity_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        activity = []
        for p in self.posts.values():
            if p.author_id == user_id:
                activity.append({"type": "post", "id": p.post_id, "title": p.title, "timestamp": p.created_at})
        for c in self.comments.values():
            if c.author_id == user_id:
                post = self.posts.get(c.post_id)
                activity.append({"type": "comment", "id": c.comment_id, "post_title": post.title if post else "", "timestamp": c.created_at})
        activity.sort(key=lambda a: a["timestamp"], reverse=True)
        return activity[:limit]

    def get_category_stats(self, category_id: str) -> Dict[str, Any]:
        cat = self.categories.get(category_id)
        if not cat:
            return {}
        posts = [p for p in self.posts.values() if p.category_id == category_id and p.status == PostStatus.PUBLISHED]
        total_views = sum(p.view_count for p in posts)
        total_upvotes = sum(p.upvotes for p in posts)
        return {
            "category_id": category_id,
            "name": cat.name,
            "total_posts": len(posts),
            "total_views": total_views,
            "total_upvotes": total_upvotes,
            "top_contributors": self._get_top_contributors(category_id),
        }

    def _get_top_contributors(self, category_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        author_scores = defaultdict(int)
        for p in self.posts.values():
            if p.category_id == category_id:
                author_scores[p.author_id] += p.upvotes * 2 + p.view_count // 10
        ranked = sorted(author_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"author_id": aid, "score": score} for aid, score in ranked[:limit]]

    def get_feature_request_roadmap(self) -> Dict[str, Any]:
        requests = [p for p in self.posts.values() if p.post_type == PostType.FEATURE_REQUEST and p.status == PostStatus.PUBLISHED]
        by_status = defaultdict(list)
        for r in requests:
            by_status[r.feature_status or "under_review"].append(r.to_dict())
        for status_list in by_status.values():
            status_list.sort(key=lambda x: x.get("feature_votes", 0), reverse=True)
        return dict(by_status)

    def upvote_post(self, post_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self.vote_post(post_id, user_id, "upvote").to_dict() if self.vote_post(post_id, user_id, "upvote") else None

    def downvote_post(self, post_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self.vote_post(post_id, user_id, "downvote").to_dict() if self.vote_post(post_id, user_id, "downvote") else None

    def get_popular_categories(self) -> List[Dict[str, Any]]:
        cats = list(self.categories.values())
        cats.sort(key=lambda c: c.post_count, reverse=True)
        return [c.to_dict() for c in cats[:10]]

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        activity = []
        for p in list(self.posts.values())[:limit]:
            activity.append({"type": "post", "id": p.post_id, "title": p.title, "author": p.author_name, "timestamp": p.created_at, "category": p.category_id})
        for c in list(self.comments.values())[:limit]:
            post = self.posts.get(c.post_id)
            activity.append({"type": "comment", "id": c.comment_id, "post_title": post.title if post else "", "author": c.author_name, "timestamp": c.created_at})
        activity.sort(key=lambda a: a["timestamp"], reverse=True)
        return activity[:limit]

    def get_moderation_queue(self) -> List[Dict[str, Any]]:
        flagged = [p.to_dict() for p in self.posts.values() if p.flagged]
        flagged.sort(key=lambda p: p.get("created_at", ""))
        return flagged[:50]

    def approve_post(self, post_id: str) -> bool:
        return self.moderate_post(post_id, "approve")

    def hide_post(self, post_id: str) -> bool:
        return self.moderate_post(post_id, "hide")

    def get_badge_leaderboard(self, badge_name: str) -> List[Dict[str, Any]]:
        users = []
        for uid, rep in self.reputations.items():
            for b in rep.badges:
                if b["name"] == badge_name:
                    users.append({"user_id": uid, "username": rep.username, "reputation": rep.reputation})
        users.sort(key=lambda u: u["reputation"], reverse=True)
        return users[:20]

    def award_badge(self, user_id: str, badge_type: str, badge_name: str) -> bool:
        rep = self.reputations.get(user_id)
        if not rep:
            return False
        existing = {b["name"] for b in rep.badges}
        if badge_name not in existing:
            rep.badges.append({"type": badge_type, "name": badge_name, "awarded_at": datetime.utcnow().isoformat()})
            self._save_data()
        return True

    def get_unanswered_questions(self, limit: int = 20) -> List[Dict[str, Any]]:
        questions = [p.to_dict() for p in self.posts.values() if p.post_type == PostType.QUESTION and not p.is_answered and p.status == PostStatus.PUBLISHED]
        questions.sort(key=lambda q: q.get("upvotes", 0), reverse=True)
        return questions[:limit]

    def get_answered_questions(self, limit: int = 20) -> List[Dict[str, Any]]:
        answered = [p.to_dict() for p in self.posts.values() if p.post_type == PostType.QUESTION and p.is_answered and p.status == PostStatus.PUBLISHED]
        answered.sort(key=lambda q: q.get("upvotes", 0), reverse=True)
        return answered[:limit]

    def get_post_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        for p in self.posts.values():
            if p.slug == slug and p.status == PostStatus.PUBLISHED:
                return p.to_dict()
        return None

    def get_related_posts(self, post_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        post = self.posts.get(post_id)
        if not post:
            return []
        scored = []
        for p in self.posts.values():
            if p.post_id == post_id or p.status != PostStatus.PUBLISHED:
                continue
            score = 0
            if p.category_id == post.category_id:
                score += 5
            common_tags = set(p.tags) & set(post.tags)
            score += len(common_tags) * 3
            if p.author_id == post.author_id:
                score += 1
            if score > 0:
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p.to_dict() for _, p in scored[:limit]]

    def get_weekly_summary(self) -> Dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        new_posts = [p for p in self.posts.values() if p.created_at >= cutoff]
        new_comments = [c for c in self.comments.values() if c.created_at >= cutoff]
        total_votes = sum(p.upvotes + p.downvotes for p in new_posts)
        return {
            "new_posts": len(new_posts),
            "new_comments": len(new_comments),
            "total_votes": total_votes,
            "top_post": max(new_posts, key=lambda p: p.upvotes).to_dict() if new_posts else None,
            "most_active_category": Counter(p.category_id for p in new_posts).most_common(1)[0][0] if new_posts else None,
        }

    def search_posts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for p in self.posts.values():
            if p.status != PostStatus.PUBLISHED:
                continue
            if q in p.title.lower() or q in p.content.lower() or any(q in t.lower() for t in p.tags):
                results.append(p.to_dict())
        results.sort(key=lambda r: r.get("upvotes", 0), reverse=True)
        return results[:limit]

    def get_post_comments(self, post_id: str, sort: str = "recent") -> List[Dict[str, Any]]:
        comments = [c.to_dict() for c in self.comments.values() if c.post_id == post_id and c.status == "active"]
        if sort == "recent":
            comments.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        elif sort == "votes":
            comments.sort(key=lambda c: c.get("upvotes", 0), reverse=True)
        elif sort == "oldest":
            comments.sort(key=lambda c: c.get("created_at", ""))
        return comments

    def delete_post(self, post_id: str) -> bool:
        if post_id not in self.posts:
            return False
        self.posts[post_id].status = PostStatus.ARCHIVED
        self.posts[post_id].updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def pin_post(self, post_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        for p in self.posts.values():
            p.is_pinned = False
        post.is_pinned = True
        post.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def unpin_post(self, post_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.is_pinned = False
        post.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def get_pinned_posts(self) -> List[Dict[str, Any]]:
        pinned = [p.to_dict() for p in self.posts.values() if p.is_pinned and p.status == PostStatus.PUBLISHED]
        pinned.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return pinned

    def get_user_reputation(self, user_id: str) -> Optional[Dict[str, Any]]:
        rep = self.reputations.get(user_id)
        return rep.to_dict() if rep else None

    def add_reputation(self, user_id: str, username: str, points: int = 1) -> Dict[str, Any]:
        if user_id in self.reputations:
            self.reputations[user_id].reputation += points
        else:
            self.reputations[user_id] = UserReputation(user_id=user_id, username=username, reputation=points)
        self._save_data()
        return self.reputations[user_id].to_dict()

    def get_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        users = sorted(self.reputations.values(), key=lambda u: u.reputation, reverse=True)
        return [{"rank": i + 1, **u.to_dict()} for i, u in enumerate(users[:limit])]

    def save_comment_draft(self, post_id: str, author_id: str, content: str) -> Dict[str, Any]:
        draft_id = f"DRAFT-{uuid.uuid4().hex[:6].upper()}"
        return {"draft_id": draft_id, "post_id": post_id, "author_id": author_id, "content": content, "saved_at": datetime.utcnow().isoformat()}

    def flag_post(self, post_id: str, reason: str, flagged_by: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.flagged = True
        post.flag_reason = reason
        post.flagged_by = flagged_by
        post.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True

    def unflag_post(self, post_id: str) -> bool:
        post = self.posts.get(post_id)
        if not post:
            return False
        post.flagged = False
        post.flag_reason = None
        post.flagged_by = None
        post.updated_at = datetime.utcnow().isoformat()
        self._save_data()
        return True


class CommunityBatchProcessor:
    def __init__(self, service: CommunityPlatformService):
        self.service = service
        self.batch_log: List[Dict[str, Any]] = []

    def batch_create_posts(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        count = 0
        errors = []
        for data in posts_data:
            try:
                post = self.service.create_post(
                    title=data["title"], content=data["content"],
                    author_id=data["author_id"], author_name=data.get("author_name", ""),
                    category_id=data.get("category_id"), tags=data.get("tags", []),
                    post_type=data.get("post_type", "discussion"),
                )
                count += 1
                self.batch_log.append({"action": "create_post", "post_id": post.post_id, "status": "success"})
            except Exception as e:
                errors.append({"data": data, "error": str(e)})
                self.batch_log.append({"action": "create_post", "title": data.get("title"), "status": "error"})
        return {"created": count, "errors": len(errors), "error_details": errors[:5]}

    def get_batch_log(self) -> List[Dict[str, Any]]:
        return self.batch_log[-100:]


def paginate_posts(posts: List[Post], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    total = len(posts)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": [p.to_dict() for p in posts[start:end]],
        "page": page, "page_size": page_size, "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total, "has_prev": page > 1,
    }


def compute_community_health(service: CommunityPlatformService) -> Dict[str, Any]:
    active_users = set()
    for p in service.posts.values():
        active_users.add(p.author_id)
    for c in service.comments.values():
        active_users.add(c.author_id)
    total_posts = len(service.posts)
    published = sum(1 for p in service.posts.values() if p.status == PostStatus.PUBLISHED)
    total_votes = sum(p.upvotes + p.downvotes for p in service.posts.values())
    return {
        "total_users": len(service.reputations),
        "active_users_30d": len(active_users),
        "total_posts": total_posts,
        "published_posts": published,
        "total_comments": len(service.comments),
        "total_votes": total_votes,
        "engagement_rate": round(total_votes / max(published, 1), 2),
        "posts_per_user": round(total_posts / max(len(active_users), 1), 2),
    }


def merge_community_users(service: CommunityPlatformService, source_user: str, target_user: str) -> int:
    count = 0
    for p in service.posts.values():
        if p.author_id == source_user:
            p.author_id = target_user
            count += 1
    for c in service.comments.values():
        if c.author_id == source_user:
            c.author_id = target_user
            count += 1
    if source_user in service.reputations:
        target_rep = service.reputations.get(target_user)
        if target_rep:
            target_rep.reputation += service.reputations[source_user].reputation
        else:
            service.reputations[target_user] = service.reputations[source_user]
            service.reputations[target_user].user_id = target_user
        del service.reputations[source_user]
        count += 1
    if count:
        service._save_data()
    return count


class CommunityAuditLogger:
    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def log(self, action: str, detail: str = "") -> Dict[str, Any]:
        entry = {"action": action, "detail": detail, "ts": datetime.utcnow().isoformat(), "id": uuid.uuid4().hex[:8]}
        self._log.append(entry)
        return entry

    def tail(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._log[-n:]


def validate_community_config(config: Dict[str, Any]) -> List[str]:
    errors = []
    if "storage_path" not in config:
        errors.append("storage_path is required")
    max_posts = config.get("max_posts_per_user")
    if max_posts is not None and max_posts < 1:
        errors.append("max_posts_per_user must be >= 1")
    return errors


def get_trending_topics(service: CommunityPlatformService, days: int = 7) -> List[Dict[str, Any]]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    recent = [p for p in service.posts.values() if p.created_at >= cutoff and p.status == PostStatus.PUBLISHED]
    tag_counts: Dict[str, int] = {}
    for p in recent:
        for t in p.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"tag": tag, "count": count, "trend": "hot" if count > 5 else "rising"} for tag, count in sorted_tags[:10]]

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
