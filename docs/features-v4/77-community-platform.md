# Feature 77: Community Platform

## Overview
Built-in community platform with forums, feature voting, Q&A, and gamification (badges, reputation). Includes moderator tools and leaderboard.

## Components
- `community_platform.py` - Community forums, voting, gamification
- `cx_cogs.py` - CommunityPlatformCog Discord commands

## Data Models
- `Post` - Community post (discussion, question, feature_request)
- `Comment` - Post comments with threading
- `Category` - Post category
- `UserReputation` - Gamification points and badges

## API Endpoints
- `GET /api/v1/cx/community/posts` - List posts
- `POST /api/v1/cx/community/posts` - Create post
- `GET /api/v1/cx/community/posts/{id}` - Get post
- `POST /api/v1/cx/community/posts/{id}/vote` - Vote on post
- `POST /api/v1/cx/community/posts/{id}/comments` - Add comment
- `GET /api/v1/cx/community/posts/{id}/comments` - Get comments
- `GET /api/v1/cx/community/feature-requests` - Feature requests
- `GET /api/v1/cx/community/categories` - Categories
- `GET /api/v1/cx/community/leaderboard` - Leaderboard
- `GET /api/v1/cx/community/stats` - Statistics

## Metrics
- Active users, posts, votes, comments, reputation scores
