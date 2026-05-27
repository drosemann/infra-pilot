# security policy

## reporting security vulnerabilities

do not open public issues for security vulnerabilities!

if you discover a security vulnerability in infra pilot, please report it responsibly by emailing the maintainers directly instead of using the public issue tracker.

### reporting process

• email the maintainers with details of the vulnerability
• include:
  • description of the vulnerability
  • affected component(s) and version(s)
  • steps to reproduce (if applicable)
  • potential impact
  • suggested fix (if you have one)
• do not include:
  • full exploit code in the initial report
  • unnecessary details that could aid malicious actors
  • information about other vulnerabilities

### response

• we will acknowledge receipt of your report within 48 hours
• we'll work on a fix / mitigation with you as necessary
• we'll provide a timeline for a patch release
• we request that you refrain from publicly disclosing the vulnerability until we've had a reasonable time to prepare and deliver a fix

### security best practices

#### for users

• keep software updated - always use the latest stable release
• use secrets management - never hardcode credentials; use environment variables or secret vaults
• enable ssl/tls - use https in production
• restrict access - use firewalls, vpns, and proper authentication
• monitor logs - regularly review application and infrastructure logs
• backup data - maintain regular backups and test recovery procedures

#### for developers

• validate input - always validate and sanitize user input
• parameterize queries - use parameterized statements / orms to prevent sql injection
• use strong auth - implement strong authentication and authorization mechanisms
• secure credentials - never commit secrets; use environment variables
• encrypt sensitive data - use tls for transport, encryption at rest for stored data
• dependency updates - keep dependencies up to date and monitor for vulnerabilities
• code review - use peer review before merging changes
• security testing - include security checks in ci/cd pipelines

### known security measures

• input validation: all api inputs are validated and sanitized
• authentication: jwt-based authentication with secure token handling
• authorization: role-based access control (rbac) for operations
• secrets: environment variable-based secret management
• dependencies: regular vulnerability scanning with `safety` and `npm audit`
• ci/cd: security checks in github actions workflows

### vulnerability scanning

we use the following tools to identify and prevent vulnerabilities:

• python: `bandit`, `safety`
• javascript: `npm audit`, eslint security plugins
• java: maven plugins for dependency checking
• docker: image scanning with `trivy` or similar

### supported versions

security updates are provided for:

• current release: all patches and minor updates
• previous major version: critical security fixes only
• older versions: no support

### disclosure timeline

we follow responsible disclosure practices:

• day 0: vulnerability reported
• day 1-2: vulnerability confirmed and assessed
• day 3-7: fix developed and tested
• day 7-14: patch released (depending on severity)
• day 14: public disclosure of the fixed vulnerability (after release)

thank you for helping us keep infra pilot secure!
