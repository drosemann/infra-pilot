# Feature 97: VCS Integration Manager

## Overview
Version control system integration for GitHub and GitLab with webhook processing, commit status updates, PR comments, and deployment tracking.

## Capabilities
- Webhook processing for push, PR, issue events
- Commit status creation (pending/success/failure/error)
- Pull request comments with AI review summaries
- Deployment tracking and environment mapping
- App token generation for CI/CD pipelines
- Multi-repository management

## Backend API
- `POST /api/v1/vcs/webhook` - receive webhook event
- `POST /api/v1/vcs/commit-status` - create commit status
- `POST /api/v1/vcs/pr-comment` - add PR comment
- `POST /api/v1/vcs/deployment` - track deployment
- `GET /api/v1/vcs/repos` - list configured repos
- `POST /api/v1/vcs/repos` - add repository
