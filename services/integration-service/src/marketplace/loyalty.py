import json
import logging
import os
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

RARITY_COLORS = {'common': '#9e9e9e', 'uncommon': '#4caf50', 'rare': '#2196f3', 'epic': '#9c27b0', 'legendary': '#ff9800'}

@dataclass
class LoyaltyPoints:
    user_id: str
    balance: int
    lifetime_earned: int
    lifetime_spent: int
    points_expiring_soon: int
    last_updated: str

@dataclass
class PointsTransaction:
    id: str
    user_id: str
    amount: int
    balance_after: int
    type: str
    source: str
    reference_id: str
    reference_type: str
    description: str
    created_at: str

@dataclass
class UserLevel:
    user_id: str
    level: int
    current_xp: int
    xp_to_next_level: int
    total_xp_earned: int
    level_title: str
    benefits: List[str]

@dataclass
class Achievement:
    id: str
    name: str
    slug: str
    description: str
    icon_url: str
    category: str
    points_reward: int
    xp_reward: int
    criteria: Dict[str, Any]
    is_hidden: bool
    is_secret: bool

@dataclass
class Badge:
    id: str
    user_id: str
    achievement_id: str
    title: str
    description: str
    icon_url: str
    rarity: str
    earned_at: str
    equipped: bool

@dataclass
class Reward:
    id: str
    name: str
    description: str
    points_cost: int
    reward_type: str
    value: str
    stock: int
    max_per_user: int
    is_limited_time: bool
    expires_at: str

class LoyaltyManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.points_file = os.path.join(self.data_path, 'loyalty_points.json')
        self.transactions_file = os.path.join(self.data_path, 'loyalty_transactions.json')
        self.levels_file = os.path.join(self.data_path, 'loyalty_levels.json')
        self.achievements_file = os.path.join(self.data_path, 'loyalty_achievements.json')
        self.badges_file = os.path.join(self.data_path, 'loyalty_badges.json')
        self.rewards_file = os.path.join(self.data_path, 'loyalty_rewards.json')
        self.points: Dict[str, LoyaltyPoints] = {}
        self.transactions: Dict[str, PointsTransaction] = {}
        self.levels: Dict[str, UserLevel] = {}
        self.achievements: Dict[str, Achievement] = {}
        self.badges: Dict[str, Badge] = {}
        self.rewards: Dict[str, Reward] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.points_file, 'points', LoyaltyPoints),
            (self.transactions_file, 'transactions', PointsTransaction),
            (self.levels_file, 'levels', UserLevel),
            (self.achievements_file, 'achievements', Achievement),
            (self.badges_file, 'badges', Badge),
            (self.rewards_file, 'rewards', Reward),
        ]:
            try:
                if os.path.exists(file_key):
                    with open(file_key, 'r') as f:
                        data = json.load(f)
                    storage = getattr(self, attr)
                    storage.clear()
                    for item in data:
                        storage[item['id'] if 'id' in item and attr not in ('points', 'levels') else (item['user_id'] if attr == 'points' or attr == 'levels' else item['id'])] = cls(**item)
            except Exception as e:
                logger.warning(f"Failed to load {attr}: {e}")

    def _save_data(self):
        for file_key, attr in [
            (self.points_file, 'points'),
            (self.transactions_file, 'transactions'),
            (self.levels_file, 'levels'),
            (self.achievements_file, 'achievements'),
            (self.badges_file, 'badges'),
            (self.rewards_file, 'rewards'),
        ]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("LoyaltyManager initialized")
        if not self.achievements:
            await self._seed_achievements()
        if not self.rewards:
            await self._seed_rewards()

    async def close(self):
        self._save_data()

    async def _seed_achievements(self):
        achievements = [
            {'name': 'First Steps', 'description': 'Create your first server', 'category': 'milestone', 'points_reward': 50, 'xp_reward': 100, 'criteria': {'type': 'server_count', 'threshold': 1}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Power User', 'description': 'Create 10 servers', 'category': 'milestone', 'points_reward': 200, 'xp_reward': 500, 'criteria': {'type': 'server_count', 'threshold': 10}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Cloud Baron', 'description': 'Create 50 servers', 'category': 'milestone', 'points_reward': 1000, 'xp_reward': 2500, 'criteria': {'type': 'server_count', 'threshold': 50}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Uptime Champion', 'description': 'Maintain 99.9% uptime for 30 days', 'category': 'reliability', 'points_reward': 300, 'xp_reward': 750, 'criteria': {'type': 'uptime', 'threshold': 99.9, 'days': 30}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Uptime Legend', 'description': 'Maintain 99.99% uptime for 90 days', 'category': 'reliability', 'points_reward': 1500, 'xp_reward': 5000, 'criteria': {'type': 'uptime', 'threshold': 99.99, 'days': 90}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Social Butterfly', 'description': 'Refer 5 friends', 'category': 'referral', 'points_reward': 500, 'xp_reward': 1000, 'criteria': {'type': 'referral_count', 'threshold': 5}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Super Referrer', 'description': 'Refer 20 friends', 'category': 'referral', 'points_reward': 2000, 'xp_reward': 5000, 'criteria': {'type': 'referral_count', 'threshold': 20}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Early Bird', 'description': 'Pay your first 3 invoices before due date', 'category': 'payment', 'points_reward': 150, 'xp_reward': 300, 'criteria': {'type': 'early_payment', 'threshold': 3}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Loyal Customer', 'description': 'Active subscription for 12 months', 'category': 'loyalty', 'points_reward': 1000, 'xp_reward': 3000, 'criteria': {'type': 'subscription_months', 'threshold': 12}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Bug Hunter', 'description': 'Report a valid bug', 'category': 'community', 'points_reward': 250, 'xp_reward': 500, 'criteria': {'type': 'bug_report', 'threshold': 1}, 'is_hidden': True, 'is_secret': False},
            {'name': 'Helpful Hand', 'description': 'Answer 10 questions in community forum', 'category': 'community', 'points_reward': 300, 'xp_reward': 600, 'criteria': {'type': 'forum_answers', 'threshold': 10}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Big Spender', 'description': 'Spend over $1000 in total', 'category': 'payment', 'points_reward': 750, 'xp_reward': 2000, 'criteria': {'type': 'total_spend', 'threshold': 1000}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Treasure Hunter', 'description': 'Find a secret achievement', 'category': 'special', 'points_reward': 500, 'xp_reward': 1000, 'criteria': {'type': 'secret', 'threshold': 1}, 'is_hidden': True, 'is_secret': True},
            {'name': 'Storage King', 'description': 'Use over 1TB of storage', 'category': 'milestone', 'points_reward': 400, 'xp_reward': 1000, 'criteria': {'type': 'storage_used', 'threshold': 1024}, 'is_hidden': False, 'is_secret': False},
            {'name': 'Network Mogul', 'description': 'Use over 10TB of bandwidth', 'category': 'milestone', 'points_reward': 500, 'xp_reward': 1200, 'criteria': {'type': 'bandwidth_used', 'threshold': 10240}, 'is_hidden': False, 'is_secret': False},
        ]
        for ach in achievements:
            aid = str(uuid.uuid4())
            slug = ach['name'].lower().replace(' ', '-')
            achievement = Achievement(id=aid, slug=slug, icon_url=f'https://cdn.infrapilot.com/badges/{slug}.png', **{k: v for k, v in ach.items() if k != 'name'})
            achievement.name = ach['name']
            self.achievements[aid] = achievement
        self._save_data()

    async def _seed_rewards(self):
        rewards = [
            {'name': '5% Discount Code', 'description': 'Get 5% off your next invoice', 'points_cost': 500, 'reward_type': 'discount', 'value': '5', 'stock': 1000, 'max_per_user': 3, 'is_limited_time': False, 'expires_at': ''},
            {'name': '10% Discount Code', 'description': 'Get 10% off your next invoice', 'points_cost': 1000, 'reward_type': 'discount', 'value': '10', 'stock': 500, 'max_per_user': 2, 'is_limited_time': False, 'expires_at': ''},
            {'name': '$10 Service Credit', 'description': '$10 credit applied to your account balance', 'points_cost': 2000, 'reward_type': 'service_credit', 'value': '10', 'stock': 200, 'max_per_user': 5, 'is_limited_time': False, 'expires_at': ''},
            {'name': '$25 Service Credit', 'description': '$25 credit applied to your account balance', 'points_cost': 4500, 'reward_type': 'service_credit', 'value': '25', 'stock': 100, 'max_per_user': 3, 'is_limited_time': False, 'expires_at': ''},
            {'name': '$50 Service Credit', 'description': '$50 credit applied to your account balance', 'points_cost': 8000, 'reward_type': 'service_credit', 'value': '50', 'stock': 50, 'max_per_user': 2, 'is_limited_time': False, 'expires_at': ''},
            {'name': 'Priority Support (1 Month)', 'description': 'One month of priority support access', 'points_cost': 3000, 'reward_type': 'feature_unlock', 'value': 'priority_support', 'stock': 100, 'max_per_user': 6, 'is_limited_time': False, 'expires_at': ''},
            {'name': 'Free Backup Upgrade (1 Month)', 'description': 'Double your backup retention for one month', 'points_cost': 1500, 'reward_type': 'feature_unlock', 'value': 'backup_upgrade', 'stock': 200, 'max_per_user': 6, 'is_limited_time': False, 'expires_at': ''},
            {'name': 'T-Shirt', 'description': 'Infra Pilot branded T-shirt', 'points_cost': 5000, 'reward_type': 'merchandise', 'value': 'tshirt', 'stock': 20, 'max_per_user': 1, 'is_limited_time': False, 'expires_at': ''},
            {'name': 'Free Month (Starter)', 'description': 'One free month on the Starter plan', 'points_cost': 3000, 'reward_type': 'service_credit', 'value': '9.99', 'stock': 50, 'max_per_user': 2, 'is_limited_time': False, 'expires_at': ''},
            {'name': 'Free Month (Pro)', 'description': 'One free month on the Pro plan', 'points_cost': 12000, 'reward_type': 'service_credit', 'value': '39.99', 'stock': 20, 'max_per_user': 1, 'is_limited_time': False, 'expires_at': ''},
        ]
        for rw in rewards:
            rid = str(uuid.uuid4())
            reward = Reward(id=rid, **rw)
            self.rewards[rid] = reward
        self._save_data()

    def _ensure_points(self, user_id: str) -> LoyaltyPoints:
        if user_id not in self.points:
            self.points[user_id] = LoyaltyPoints(user_id=user_id, balance=0, lifetime_earned=0, lifetime_spent=0, points_expiring_soon=0, last_updated=datetime.now().isoformat())
        return self.points[user_id]

    def _ensure_level(self, user_id: str) -> UserLevel:
        if user_id not in self.levels:
            level_titles = ['Newcomer', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Elite', 'Legend', 'Mythic', 'Transcendent']
            self.levels[user_id] = UserLevel(user_id=user_id, level=1, current_xp=0, xp_to_next_level=100, total_xp_earned=0, level_title='Newcomer', benefits=['Access to community forum'])
        return self.levels[user_id]

    def _xp_for_level(self, level: int) -> int:
        return int(100 * level * (1 + level / 10))

    async def get_points(self, user_id: str) -> Dict[str, Any]:
        pts = self._ensure_points(user_id)
        return asdict(pts)

    async def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(t) for t in sorted(self.transactions.values(), key=lambda x: x.created_at, reverse=True) if t.user_id == user_id]

    async def earn_points(self, user_id: str, amount: int, source: str, description: str = '', reference_id: str = '') -> PointsTransaction:
        pts = self._ensure_points(user_id)
        pts.balance += amount
        pts.lifetime_earned += amount
        pts.last_updated = datetime.now().isoformat()
        txn = PointsTransaction(
            id=str(uuid.uuid4()), user_id=user_id, amount=amount,
            balance_after=pts.balance, type='earn', source=source,
            reference_id=reference_id, reference_type='',
            description=description or f'Earned {amount} points from {source}',
            created_at=datetime.now().isoformat(),
        )
        self.transactions[txn.id] = txn
        await self._add_xp(user_id, amount)
        self._save_data()
        return txn

    async def spend_points(self, user_id: str, amount: int, description: str = '') -> Optional[PointsTransaction]:
        pts = self._ensure_points(user_id)
        if pts.balance < amount:
            return None
        pts.balance -= amount
        pts.lifetime_spent += amount
        pts.last_updated = datetime.now().isoformat()
        txn = PointsTransaction(
            id=str(uuid.uuid4()), user_id=user_id, amount=-amount,
            balance_after=pts.balance, type='spend', source='redemption',
            reference_id='', reference_type='',
            description=description or f'Spent {amount} points',
            created_at=datetime.now().isoformat(),
        )
        self.transactions[txn.id] = txn
        self._save_data()
        return txn

    async def _add_xp(self, user_id: str, xp: int):
        level = self._ensure_level(user_id)
        level.current_xp += xp
        level.total_xp_earned += xp
        while level.current_xp >= level.xp_to_next_level:
            level.current_xp -= level.xp_to_next_level
            level.level += 1
            level.xp_to_next_level = self._xp_for_level(level.level)
            level_titles = {1: 'Newcomer', 2: 'Bronze', 3: 'Silver', 4: 'Gold', 5: 'Platinum', 6: 'Diamond', 7: 'Elite', 8: 'Legend', 9: 'Mythic', 10: 'Transcendent'}
            level.level_title = level_titles.get(level.level, f'Level {level.level}')
            level.benefits = self._level_benefits(level.level)
        self._save_data()

    def _level_benefits(self, level: int) -> List[str]:
        benefits = ['Access to community forum']
        if level >= 2: benefits.append('Custom avatar')
        if level >= 3: benefits.append('Priority email support')
        if level >= 4: benefits.append('Early access to new features')
        if level >= 5: benefits.append('2x points on all purchases')
        if level >= 6: benefits.append('Monthly bonus points')
        if level >= 7: benefits.append('Direct line to support team')
        if level >= 8: benefits.append('Beta program access')
        if level >= 9: benefits.append('Name in product credits')
        if level >= 10: benefits.append('Lifetime free Starter plan')
        return benefits

    async def get_level(self, user_id: str) -> Dict[str, Any]:
        level = self._ensure_level(user_id)
        return asdict(level)

    async def get_badges(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(b) for b in self.badges.values() if b.user_id == user_id]

    async def get_achievements(self) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self.achievements.values()]

    async def check_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        new_achievements = []
        user_badge_achievement_ids = set(b.achievement_id for b in self.badges.values() if b.user_id == user_id)
        for ach in self.achievements.values():
            if ach.id in user_badge_achievement_ids:
                continue
            if ach.criteria.get('type') == 'server_count' and ach.criteria.get('threshold', 0) <= 5:
                badge = Badge(id=str(uuid.uuid4()), user_id=user_id, achievement_id=ach.id, title=ach.name, description=ach.description, icon_url=ach.icon_url, rarity=self._get_rarity(ach.points_reward), earned_at=datetime.now().isoformat(), equipped=False)
                self.badges[badge.id] = badge
                await self.earn_points(user_id, ach.points_reward, 'achievement', f'Achievement unlocked: {ach.name}')
                new_achievements.append(asdict(badge))
        self._save_data()
        return new_achievements

    def _get_rarity(self, points: int) -> str:
        if points >= 2000: return 'legendary'
        if points >= 1000: return 'epic'
        if points >= 500: return 'rare'
        if points >= 200: return 'uncommon'
        return 'common'

    async def get_rewards(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self.rewards.values() if r.stock > 0]

    async def redeem_reward(self, user_id: str, reward_id: str) -> Optional[Dict[str, Any]]:
        reward = self.rewards.get(reward_id)
        if not reward or reward.stock <= 0:
            return None
        user_redeemed = sum(1 for t in self.transactions.values() if t.user_id == user_id and t.type == 'spend' and reward.name in t.description)
        if user_redeemed >= reward.max_per_user:
            return None
        pts = self._ensure_points(user_id)
        if pts.balance < reward.points_cost:
            return None
        txn = await self.spend_points(user_id, reward.points_cost, f'Redeemed: {reward.name}')
        if not txn:
            return None
        reward.stock -= 1
        self._save_data()
        return {
            'transaction': asdict(txn),
            'reward': asdict(reward),
            'redemption_code': str(uuid.uuid4())[:12].upper(),
            'redeemed_at': datetime.now().isoformat(),
        }

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_users = sorted(self.points.values(), key=lambda p: p.lifetime_earned, reverse=True)[:limit]
        leaderboard = []
        for i, pts in enumerate(sorted_users):
            level = self.levels.get(pts.user_id)
            leaderboard.append({
                'rank': i + 1,
                'user_id': pts.user_id,
                'points': pts.balance,
                'lifetime_earned': pts.lifetime_earned,
                'level': level.level if level else 1,
                'level_title': level.level_title if level else 'Newcomer',
                'badge_count': sum(1 for b in self.badges.values() if b.user_id == pts.user_id),
            })
        return leaderboard

    async def create_referral(self, user_id: str) -> Dict[str, Any]:
        code = str(uuid.uuid4())[:8].upper()
        return {
            'user_id': user_id,
            'referral_code': code,
            'referral_url': f'https://infrapilot.com/signup?ref={code}',
            'points_per_referral': 200,
            'created_at': datetime.now().isoformat(),
        }

    async def get_settings(self) -> Dict[str, Any]:
        return {
            'points_per_dollar_spent': 10,
            'points_per_referral': 200,
            'points_for_signup': 100,
            'points_expiry_days': 365,
            'points_inactivity_days': 365,
            'referral_bonus_pct': 10,
            'leaderboard_update_hours': 24,
        }
