# Feature 88: IAM Security

## Overview
Enterprise identity and access management with least-privilege enforcement, access reviews, MFA, and audit logging.

## Components
- **Users**: 245 identities (218 active) with SSO/MFA
- **Roles**: 68 roles (12 custom) with policy attachments
- **Access Reviews**: Automated certification campaigns
- **Audit**: Comprehensive audit logging with anomaly detection

## Data Models
- User: id, username, email, status, mfa_enabled, roles
- Role: id, name, type, policies, overprivileged
- AccessReview: id, name, status, due_date, reviewer
- AuditEvent: id, user_id, action, resource, timestamp, ip

## API Endpoints
- GET /api/soc/iam/users - List users
- GET /api/soc/iam/users/:id - Get user details
- POST /api/soc/iam/users - Create user
- PUT /api/soc/iam/users/:id - Update user
- DELETE /api/soc/iam/users/:id - Delete user
- GET /api/soc/iam/roles - List roles
- GET /api/soc/iam/access-reviews - List reviews
- POST /api/soc/iam/access-reviews/:id/execute - Run review
- GET /api/soc/iam/audit - Get audit log

## Metrics
- Users: 245 (218 active)
- MFA Adoption: 98.8%
- Roles: 68 (5 overprivileged)
- Access Reviews: 3 pending
- Events (30d): 3,124
- Offboarding Compliance: 99.5%

## Discord Commands
- /iamsec - View IAM security summary
- /iamsec users - List users
- /iamsec roles - List roles
- /iamsec access - List access reviews
- /iamsec audit - View audit log
- /iamsec stats - View statistics
