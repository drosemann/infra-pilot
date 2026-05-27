# architecture planner

## description

helps design and plan software architecture, including system design, component relationships, technology stack decisions, and scalability considerations. provides structured architectural guidance for projects of any size.

## usage

describe your project requirements, constraints, and goals. include information about expected scale, performance requirements, team size, and any existing systems. works for both new projects and architectural refactoring.

## prompt

```markdown
Help me design the software architecture for the following project:

**Project Overview:**
[Describe what the system should do and its main purpose]

**Requirements:**
- **Functional Requirements:**
  - [Core features and capabilities needed]
  - [User interactions and workflows]
  - [Data processing requirements]

- **Non-Functional Requirements:**
  - **Scale**: [Expected users, data volume, transaction volume]
  - **Performance**: [Response time, throughput requirements]
  - **Availability**: [Uptime requirements, disaster recovery needs]
  - **Security**: [Authentication, authorization, data protection needs]

**Constraints:**
- **Budget**: [Budget limitations or cost considerations]
- **Team**: [Team size, skill levels, experience with technologies]
- **Timeline**: [Development timeline and milestones]
- **Technology**: [Required technologies, existing systems to integrate]
- **Compliance**: [Regulatory or industry standards to follow]

**Current State:** [Existing systems, legacy code, or starting from scratch]

Please provide:

1. **High-Level Architecture**
   - System overview and major components
   - Architecture pattern recommendation (MVC, microservices, etc.)
   - Data flow and component interactions

2. **Technology Stack Recommendations**
   - Backend technologies and frameworks
   - Database choices and rationale
   - Frontend technologies
   - Infrastructure and deployment options

3. **Detailed Component Design**
   - Core services/modules breakdown
   - API design considerations
   - Data models and relationships

4. **Scalability Strategy**
   - How to handle growth
   - Performance optimization points
   - Caching strategies

5. **Security Architecture**
   - Authentication and authorization approach
   - Data protection measures
   - Security best practices

6. **Implementation Roadmap**
   - Development phases and priorities
   - MVP scope and incremental features
   - Risk mitigation strategies
```

## example input

```markdown
**Project Overview:**
A real-time collaboration platform for remote teams, similar to Slack but with integrated video calls, file sharing, and project management features.

**Requirements:**
- **Functional Requirements:**
  - Real-time messaging and channels
  - Video/audio calling for up to 50 participants
  - File upload and sharing (up to 100MB per file)
  - Task management and project boards
  - User authentication and team management

- **Non-Functional Requirements:**
  - **Scale**: 10,000 concurrent users, 100,000 total users
  - **Performance**: <200ms message delivery, <3s file upload
  - **Availability**: 99.9% uptime
  - **Security**: Enterprise-grade security, GDPR compliance

**Constraints:**
- **Budget**: $50k initial development budget
- **Team**: 5 full-stack developers, 1 DevOps engineer
- **Timeline**: 6 months to MVP, 12 months to full feature set
- **Technology**: Team has experience with React, Node.js, PostgreSQL
```

## example output

```markdown
# Collaboration Platform Architecture Design

## High-Level Architecture

### Architecture Pattern: Microservices with Event-Driven Communication
```

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   web client    │    │  mobile client  │    │  desktop app    │
│    (react)      │    │   (react native)│    │   (electron)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     api gateway           │
                    │   (authentication +       │
                    │    load balancing)        │
                    └─────────────┬─────────────┘
                                  │
    ┌─────────────┬───────────────┼───────────────┬─────────────┐
    │             │               │               │             │
┌───▼───┐    ┌───▼───┐       ┌───▼───┐      ┌───▼───┐    ┌───▼───┐
│message│    │ user  │       │ file  │      │video  │    │project│
│service│    │service│       │service│      │service│    │service│
└───┬───┘    └───┬───┘       └───┬───┘      └───┬───┘    └───┬───┘
    │            │               │              │            │
    └────────────┼───────────────┼──────────────┼────────────┘
                 │               │              │
            ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
            │postgresql│     │   s3    │    │  redis  │
            │(primary) │     │(files)  │    │(cache)  │
            └─────────┘     └─────────┘    └─────────┘

```

## technology stack recommendations

### backend
- language: node.js with typescript (team familiarity)
- framework: express.js with fastify for high-performance services
- real-time: socket.io for websocket connections
- message queue: redis for pub/sub and job queues
- video: webrtc with kurento media server for large calls

### database
- primary: postgresql for structured data (users, teams, projects)
- cache: redis for sessions, real-time data, and message caching
- file storage: aws s3 or minio for file uploads
- search: elasticsearch for message search functionality

### frontend
- framework: react with typescript
- state management: redux toolkit for complex state
- real-time: socket.io client
- ui library: material-ui or ant design for rapid development

### infrastructure
- containerization: docker with docker compose for development
- orchestration: kubernetes for production (or start with simple vps)
- ci/cd: github actions
- monitoring: prometheus + grafana

## detailed component design

### 1. message service
```typescript
interface MessageService {
  sendMessage(channelId: string, message: MessagePayload): Promise<void>
  getChannelHistory(channelId: string, limit: number): Promise<Message[]>
  subscribeToChannel(channelId: string, userId: string): void
}
```

- real-time message delivery via socket.io
- message persistence in postgresql
- redis for message caching and pub/sub

### 2. user service

```typescript
interface UserService {
  authenticate(credentials: LoginCredentials): Promise<AuthResult>
  createUser(userData: CreateUserRequest): Promise<User>
  updateUserStatus(userId: string, status: UserStatus): Promise<void>
}
```

- jwt-based authentication
- user management and team assignments
- integration with external oauth providers

### 3. file service

- secure file upload with virus scanning
- progressive upload for large files
- automatic thumbnail generation for images
- cdn integration for fast delivery

### 4. video service

- webrtc peer-to-peer for small calls (<5 people)
- selective forwarding unit (sfu) for larger calls
- recording capabilities with cloud storage
- screen sharing support

## scalability strategy

### phase 1 (mvp): monolithic start

- single node.js application
- postgresql primary database
- redis for caching
- supports up to 1,000 concurrent users

### phase 2 (growth): service separation

- extract message service for independent scaling
- add read replicas for database
- implement horizontal scaling for video services
- cdn for static assets

### phase 3 (scale): full microservices

- complete service decomposition
- database sharding by team/organization
- multi-region deployment
- advanced caching strategies

## security architecture

### authentication & authorization

```
User → API Gateway → JWT Validation → Service Authorization
```

- jwt tokens with short expiry (15 minutes)
- refresh token rotation
- role-based access control (rbac)
- rate limiting per user/ip

### data protection

- end-to-end encryption for sensitive messages
- at-rest encryption for database and files
- https everywhere with hsts headers
- input validation and sanitization

## implementation roadmap

### phase 1 (months 1-2): core mvp

goal: basic messaging and user management

- user authentication and team creation
- real-time messaging in channels
- basic file sharing
- simple web client

mvp features:

- login/signup
- create teams and channels
- send/receive messages
- upload/download files

### phase 2 (months 3-4): enhanced features

- video calling (up to 10 participants)
- message search
- mobile-responsive design
- basic project management features

### phase 3 (months 5-6): production ready

- advanced video features (screen sharing, recording)
- full project management integration
- admin dashboard
- comprehensive security features

### risk mitigation

• technical risks:
   - start with proven technologies
   - build comprehensive testing early
   - plan for database migration strategies

• scalability risks:
   - design with microservices in mind from day 1
   - use feature flags for gradual rollouts
   - monitor performance metrics continuously

• security risks:
   - regular security audits
   - implement logging and monitoring
   - have incident response plan ready

## success metrics

- message delivery latency <200ms
- 99.9% uptime
- support 10,000 concurrent users
- file upload success rate >99%
- video call quality metrics

```

## variations

• enterprise architecture: focus on enterprise patterns and governance
• microservices design: deep dive into service decomposition
• cloud-native: emphasize cloud services and serverless architectures
• legacy migration: focus on modernizing existing systems

## tips

• be specific about scale and performance requirements
• include budget and timeline constraints for realistic recommendations
• mention team expertise to align technology choices
• consider starting simple and evolving the architecture over time
• always include security and compliance considerations

## related prompts

• `code-review.md` - for reviewing architectural decisions in code
• `documentation-generator.md` - for creating architecture documentation
• `test-case-generator.md` - for testing architectural components

## tags

`architecture` `system-design` `scalability` `technology-stack` `development` `planning`
