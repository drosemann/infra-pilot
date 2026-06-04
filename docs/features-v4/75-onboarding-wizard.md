# Feature 75: Customer Onboarding Wizard

## Overview
Step-by-step guided onboarding system with progress tracking, product tours, video walkthroughs, milestone celebrations, and task checklists.

## Components
- `onboarding_wizard.py` - Step-by-step onboarding orchestration
- `cx_cogs.py` - OnboardingWizardCog Discord commands

## Data Models
- `OnboardingSession` - Customer onboarding state with progress
- `OnboardingStep` - Individual step with status and metadata

## API Endpoints
- `POST /api/v1/cx/onboarding/start` - Start onboarding
- `GET /api/v1/cx/onboarding/session/{customer_id}` - Get session
- `POST /api/v1/cx/onboarding/step` - Update step
- `GET /api/v1/cx/onboarding/stats` - Onboarding statistics

## Metrics
- Onboarding completion rate, average time to onboard, step drop-off
