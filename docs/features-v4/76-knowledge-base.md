# Feature 76: Knowledge Base & Help Center

## Overview
Searchable help center with articles, videos, FAQs. Features article feedback, related article suggestions, and multi-language support.

## Components
- `knowledge_base.py` - Knowledge base service with search
- `cx_cogs.py` - KnowledgeBaseCog Discord commands

## Data Models
- `Article` - Knowledge base article with content, category, tags
- `Category` - Article category
- `ArticleFeedback` - User feedback on articles

## API Endpoints
- `GET /api/v1/cx/kb/articles` - List articles
- `POST /api/v1/cx/kb/articles` - Create article
- `GET /api/v1/cx/kb/articles/{id}` - Get article
- `PUT /api/v1/cx/kb/articles/{id}` - Update article
- `GET /api/v1/cx/kb/search` - Search articles
- `GET /api/v1/cx/kb/categories` - List categories
- `POST /api/v1/cx/kb/feedback` - Add article feedback

## Metrics
- Article views, helpfulness rate, search success rate
