# Feature 40: Loyalty & Reward System

## Overview
Points-based system for referrals, uptime milestones, early payments, and community participation. Redeemable for discounts, free months, or priority support. Gamification with badges and levels.

## Components

### Integration Service: `marketplace/loyalty.py`
- `LoyaltyManager` - Core loyalty system
  - Points management (earn, spend, expire)
  - Referral tracking and rewards
  - Achievement/badge system
  - Level progression (with XP)
  - Reward catalog (discounts, service credits, merchandise)
  - Points-to-currency conversion
  - Periodic bonus events
  - Leaderboards and rankings

### Orchestrator Agent: `cogs/loyalty_manager.py`
- Discord commands:
  - `/loyalty points` - Check points balance
  - `/loyalty level` - Current level and progress
  - `/loyalty badges` - Earned badges
  - `/loyalty rewards` - Available rewards
  - `/loyalty redeem` - Redeem points for reward
  - `/loyalty referral` - Generate referral link
  - `/loyalty leaderboard` - Top users

### Management Panel: `pages/marketplace/LoyaltyPage.tsx`
- Points dashboard with history
- Achievement/badge showcase
- Level progression view
- Reward catalog with redemption
- Referral management
- Leaderboard
- Gamification settings (admin)

### CLI Commands
- `ipilot loyalty points`
- `ipilot loyalty history`
- `ipilot loyalty rewards`
- `ipilot loyalty redeem <reward_id>`

## API Endpoints
- `GET /api/marketplace/loyalty/points` - Get points balance
- `GET /api/marketplace/loyalty/history` - Points history
- `GET /api/marketplace/loyalty/level` - Current level
- `GET /api/marketplace/loyalty/badges` - Earned badges
- `GET /api/marketplace/loyalty/achievements` - All achievements
- `GET /api/marketplace/loyalty/rewards` - Reward catalog
- `POST /api/marketplace/loyalty/rewards/{id}/redeem` - Redeem reward
- `GET /api/marketplace/loyalty/referrals` - Referral links
- `POST /api/marketplace/loyalty/referrals` - Create referral
- `GET /api/marketplace/loyalty/leaderboard` - Top users
- `GET /api/marketplace/loyalty/settings` - System settings (admin)
- `PUT /api/marketplace/loyalty/settings` - Update settings (admin)
- `POST /api/marketplace/loyalty/events` - Create bonus event (admin)

## Data Models

### LoyaltyPoints
- user_id, balance, lifetime_earned, lifetime_spent
- points_expiring_soon (points expiring within 30 days)
- last_updated

### PointsTransaction
- id, user_id, amount, balance_after
- type (earn/spend/expire/adjust/bonus)
- source (referral/uptime/payment/badge/event)
- reference_id, reference_type
- description, created_at

### UserLevel
- user_id, level (1-100), current_xp, xp_to_next_level
- total_xp_earned, level_title
- benefits (list of level-specific perks)

### Achievement
- id, name, slug, description, icon_url
- category (referral/uptime/payment/community/social)
- points_reward, xp_reward
- criteria (JSON: {type: "referral_count", threshold: 10})
- is_hidden, is_secret

### Badge
- id, user_id, achievement_id
- title, description, icon_url, rarity (common/uncommon/rare/epic/legendary)
- earned_at, equipped

### Reward
- id, name, description, points_cost
- reward_type (discount/service_credit/feature_unlock/merchandise)
- value (discount_pct, credit_amount, feature_name)
- stock, max_per_user
- is_limited_time, expires_at

## Implementation Details
- Points earning rules engine
- Referral tracking via unique links/codes
- XP and level formula: xp_for_level(n) = 100 * n * (1 + n/10)
- Badge rarity color codes
- Points expiry after 12 months of inactivity
- Reward inventory management
- Achievement progress tracking
- Leaderboard refresh intervals
- Bonus event scheduling (double points weekends)
- Points-to-currency conversion rate configuration

## Testing
- Points earning and spending accuracy
- Level calculation formula
- Achievement trigger and detection
- Referral tracking uniqueness
- Reward redemption workflow
- Points expiry logic
- Leaderboard ranking correctness
- Bonus event point multiplication
