const spec: Record<string, any> = {
  openapi: '3.1.0',
  info: {
    title: 'Infra Pilot Management Panel API',
    version: '1.0.0',
    description: 'API for managing Docker apps, backups, alerts, and server infrastructure.',
  },
  servers: [{ url: '/api', description: 'API base' }],
  components: {
    securitySchemes: {
      bearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' },
    },
    schemas: {
      Error: { type: 'object', properties: { error: { type: 'string' } } },
      App: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          name: { type: 'string' },
          image: { type: 'string' },
          status: { type: 'string', enum: ['running', 'stopped', 'restarting', 'error'] },
          container_id: { type: 'string' },
          ports: { type: 'array' },
          environment_vars: { type: 'object' },
          volumes: { type: 'array' },
          memory_limit: { type: 'string' },
          cpu_shares: { type: 'integer' },
          description: { type: 'string' },
          created_at: { type: 'string', format: 'date-time' },
          updated_at: { type: 'string', format: 'date-time' },
        },
      },
      SetupStatus: {
        type: 'object',
        properties: {
          initialized: { type: 'boolean' },
          mode: { type: 'string', enum: ['personal', 'business'] },
        },
      },
      BackupJob: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          app_id: { type: 'string', format: 'uuid' },
          name: { type: 'string' },
          schedule_type: { type: 'string', enum: ['manual', 'hourly', 'daily', 'weekly'] },
          retention_count: { type: 'integer' },
          status: { type: 'string' },
          created_at: { type: 'string', format: 'date-time' },
        },
      },
      AlertConfig: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          metric_type: { type: 'string' },
          operator: { type: 'string', enum: ['gt', 'lt', 'gte', 'lte', 'eq'] },
          threshold: { type: 'number' },
          enabled: { type: 'boolean' },
          created_at: { type: 'string', format: 'date-time' },
        },
      },
      MaintenanceWindow: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          title: { type: 'string' },
          description: { type: 'string' },
          app_id: { type: 'string', format: 'uuid' },
          starts_at: { type: 'string', format: 'date-time' },
          ends_at: { type: 'string', format: 'date-time' },
          status: { type: 'string' },
        },
      },
      AuditLog: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          action: { type: 'string' },
          entity_type: { type: 'string' },
          entity_id: { type: 'string' },
          old_value: { type: 'object' },
          new_value: { type: 'object' },
          ip_address: { type: 'string' },
          created_at: { type: 'string', format: 'date-time' },
        },
      },
      NotificationChannel: {
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          name: { type: 'string' },
          type: { type: 'string', enum: ['email', 'webhook', 'telegram'] },
          config: { type: 'object' },
          enabled: { type: 'boolean' },
          created_at: { type: 'string', format: 'date-time' },
        },
      },
      HealthCheck: {
        type: 'object',
        properties: {
          id: { type: 'integer' },
          app_id: { type: 'string', format: 'uuid' },
          status: { type: 'string', enum: ['healthy', 'degraded', 'down', 'unknown'] },
          response_time_ms: { type: 'number' },
          checked_at: { type: 'string', format: 'date-time' },
        },
      },
      SearchResult: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          name: { type: 'string' },
          type: { type: 'string', enum: ['app', 'audit', 'backup'] },
        },
      },
      RbacInstanceRole: {
        type: 'object',
        description: 'Instance-level role assignment',
        properties: {
          userId: { type: 'string', format: 'uuid' },
          role: { type: 'string', enum: ['admin', 'operator', 'viewer'] },
          grantedBy: { type: 'string', format: 'uuid', nullable: true },
          createdAt: { type: 'string', format: 'date-time' },
          updatedAt: { type: 'string', format: 'date-time' },
        },
      },
      RbacMe: {
        type: 'object',
        description: 'Caller authorization state used by frontend route guards',
        properties: {
          userId: { type: 'string', format: 'uuid' },
          instanceRole: { type: 'string', enum: ['admin', 'operator', 'viewer'], nullable: true },
          organizations: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                id: { type: 'string', format: 'uuid', nullable: true },
                role: { type: 'string' },
              },
            },
          },
        },
      },
      RbacDenial: {
        type: 'object',
        description: '403 response body emitted by the RBAC middleware',
        properties: {
          error: { type: 'string', enum: ['Forbidden'] },
          code: { type: 'string', enum: ['rbac_denied'] },
          resourceType: { type: 'string' },
          action: { type: 'string' },
          reason: { type: 'string', enum: ['app', 'assignment', 'instance'] },
        },
      },
    },
  },
  paths: {
    '/ws-token': {
      post: {
        summary: 'Mint a short-lived WebSocket handshake ticket',
        description: 'Returns a single-use, short-lived ticket that authenticates a WebSocket connection to the realtime gateway. The ticket is bound to the caller and optionally scoped to a single app. Every per-app action is still re-authorized by the gateway.',
        tags: ['WebSocket'],
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: false,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  appId: { type: 'string', description: 'Optional app to scope the ticket to' },
                },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Ticket minted',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    ticket: { type: 'string' },
                    expiresIn: { type: 'integer', description: 'Lifetime in seconds' },
                    appScope: { type: 'string', nullable: true },
                  },
                },
              },
            },
          },
          '400': { description: 'Invalid appId', content: { 'application/json': { schema: { $ref: '#/components/schemas/Error' } } } },
          '401': { description: 'Unauthorized' },
          '403': { description: 'No access to the requested app', content: { 'application/json': { schema: { $ref: '#/components/schemas/Error' } } } },
        },
      },
    },
    '/ws-token/revoke': {
      post: {
        summary: 'Revoke a WebSocket ticket (or all of the user\'s tickets)',
        description: 'Revokes one ticket by value, or every ticket for the caller when `all` is true. Live sessions authenticated with a revoked ticket are closed.',
        tags: ['WebSocket'],
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  ticket: { type: 'string', description: 'The ticket to revoke' },
                  all: { type: 'boolean', description: 'Revoke every ticket for the caller' },
                },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Revocation result',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    revoked: { type: 'boolean' },
                    scope: { type: 'string', enum: ['ticket', 'all'] },
                    sessionsClosed: { type: 'integer' },
                  },
                },
              },
            },
          },
          '400': { description: 'Missing or invalid ticket', content: { 'application/json': { schema: { $ref: '#/components/schemas/Error' } } } },
          '401': { description: 'Unauthorized' },
          '403': { description: 'Ticket belongs to another user', content: { 'application/json': { schema: { $ref: '#/components/schemas/Error' } } } },
        },
      },
    },
    '/setup/status': {
      get: {
        summary: 'Check setup initialization status',
        tags: ['Setup'],
        responses: { '200': { description: 'Setup status', content: { 'application/json': { schema: { $ref: '#/components/schemas/SetupStatus' } } } } },
      },
    },
    '/setup/init': {
      post: {
        summary: 'Initialize the panel (create admin user & select mode)',
        tags: ['Setup'],
        requestBody: { required: true, content: { 'application/json': { schema: { type: 'object', required: ['email', 'password', 'mode'], properties: { email: { type: 'string', format: 'email' }, password: { type: 'string', minLength: 6 }, displayName: { type: 'string' }, mode: { type: 'string', enum: ['personal', 'business'] } } } } } },
        responses: { '200': { description: 'Setup complete' }, '400': { description: 'Invalid parameters', content: { 'application/json': { schema: { $ref: '#/components/schemas/Error' } } } } },
      },
    },
    '/presets': {
      get: { summary: 'List server presets', tags: ['Apps'], security: [{ bearerAuth: [] }], responses: { '200': { description: 'Server presets' } } },
    },
    '/apps': {
      get: {
        summary: 'List all apps for current user',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'List of apps', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/App' } } } } } },
      },
      post: {
        summary: 'Create a new Docker app',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        requestBody: { required: true, content: { 'application/json': { schema: { type: 'object', required: ['name', 'image'], properties: { name: { type: 'string' }, image: { type: 'string' }, ports: { type: 'array' }, environmentVars: { type: 'object' }, volumes: { type: 'array' }, memoryLimit: { type: 'string' }, cpuShares: { type: 'integer' }, description: { type: 'string' } } } } } },
        responses: { '201': { description: 'App created', content: { 'application/json': { schema: { $ref: '#/components/schemas/App' } } } }, '400': { description: 'Validation error', content: { 'application/json': { schema: { $ref: '#/components/schemas/Error' } } } } },
      },
    },
    '/apps/{appId}': {
      get: {
        summary: 'Get app details',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'App details', content: { 'application/json': { schema: { $ref: '#/components/schemas/App' } } } }, '404': { description: 'App not found' } },
      },
      patch: {
        summary: 'Update app settings',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'App updated', content: { 'application/json': { schema: { $ref: '#/components/schemas/App' } } } }, '404': { description: 'App not found' } },
      },
      delete: {
        summary: 'Delete an app',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'App deleted' }, '404': { description: 'App not found' } },
      },
    },
    '/apps/{appId}/start': {
      post: {
        summary: 'Start a container',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Container started' }, '404': { description: 'App not found' } },
      },
    },
    '/apps/{appId}/stop': {
      post: {
        summary: 'Stop a container',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Container stopped' }, '404': { description: 'App not found' } },
      },
    },
    '/apps/{appId}/restart': {
      post: {
        summary: 'Restart a container',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Container restarted' }, '404': { description: 'App not found' } },
      },
    },
    '/apps/{appId}/logs': {
      get: {
        summary: 'Stream paginated logs for an app',
        tags: ['Apps'],
        security: [{ bearerAuth: [] }],
        parameters: [
          { name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } },
          { name: 'limit', in: 'query', schema: { type: 'integer', default: 50 } },
          { name: 'offset', in: 'query', schema: { type: 'integer', default: 0 } },
        ],
        responses: { '200': { description: 'Log entries' } },
      },
    },
    '/apps/{appId}/metrics': {
      get: {
        summary: 'Server metrics for an app',
        tags: ['Metrics'],
        security: [{ bearerAuth: [] }],
        parameters: [
          { name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } },
          { name: 'range', in: 'query', schema: { type: 'string', default: '30m' } },
        ],
        responses: { '200': { description: 'Metrics data' } },
      },
    },
    '/apps/{appId}/config-versions': {
      get: {
        summary: 'Config version history',
        tags: ['Config'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Config versions' } },
      },
      post: {
        summary: 'Create config version snapshot',
        tags: ['Config'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '201': { description: 'Version created' } },
      },
    },
    '/apps/{appId}/config-versions/{version}/rollback': {
      post: {
        summary: 'Rollback to a specific config version',
        tags: ['Config'],
        security: [{ bearerAuth: [] }],
        parameters: [
          { name: 'appId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } },
          { name: 'version', in: 'path', required: true, schema: { type: 'integer' } },
        ],
        responses: { '200': { description: 'Rollback applied' } },
      },
    },
    '/metrics/aggregated': {
      get: {
        summary: 'Aggregated metrics across all apps',
        tags: ['Metrics'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Aggregated metrics' } },
      },
    },
    '/logs/access': {
      get: {
        summary: 'Access logs',
        tags: ['Logs'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Access log entries' } },
      },
    },
    '/maintenance-windows': {
      get: {
        summary: 'List maintenance windows',
        tags: ['Maintenance'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Maintenance windows', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/MaintenanceWindow' } } } } } },
      },
      post: {
        summary: 'Create maintenance window',
        tags: ['Maintenance'],
        security: [{ bearerAuth: [] }],
        responses: { '201': { description: 'Maintenance window created' } },
      },
    },
    '/maintenance-windows/{id}': {
      patch: {
        summary: 'Update maintenance window',
        tags: ['Maintenance'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Maintenance window updated' }, '404': { description: 'Not found' } },
      },
    },
    '/backup-jobs': {
      get: {
        summary: 'List backup jobs',
        tags: ['Backups'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Backup jobs', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/BackupJob' } } } } } },
      },
      post: {
        summary: 'Create a backup job',
        tags: ['Backups'],
        security: [{ bearerAuth: [] }],
        responses: { '201': { description: 'Backup job created' } },
      },
    },
    '/backup-jobs/{id}': {
      patch: {
        summary: 'Update a backup job',
        tags: ['Backups'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Backup job updated' }, '404': { description: 'Not found' } },
      },
      delete: {
        summary: 'Delete a backup job',
        tags: ['Backups'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Backup job deleted' }, '404': { description: 'Not found' } },
      },
    },
    '/backup-jobs/{jobId}/status': {
      get: {
        summary: 'Backup status history',
        tags: ['Backups'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'jobId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Backup status entries' } },
      },
    },
    '/backup-artifacts': {
      get: {
        summary: 'Read-only list of db-backup.sh artifacts',
        tags: ['Backups'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Backup artifacts with last success timestamp' } },
      },
    },
    '/alert-configs': {
      get: {
        summary: 'List alert configurations',
        tags: ['Alerts'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Alert configs', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/AlertConfig' } } } } } },
      },
      post: {
        summary: 'Create alert configuration',
        tags: ['Alerts'],
        security: [{ bearerAuth: [] }],
        responses: { '201': { description: 'Alert config created' } },
      },
    },
    '/alert-configs/{id}': {
      patch: {
        summary: 'Update alert configuration',
        tags: ['Alerts'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Alert config updated' }, '404': { description: 'Not found' } },
      },
      delete: {
        summary: 'Delete alert configuration',
        tags: ['Alerts'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Alert config deleted' } },
      },
    },
    '/alert-history': {
      get: {
        summary: 'Alert history',
        tags: ['Alerts'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Alert history entries' } },
      },
    },
    '/alert-history/{id}/acknowledge': {
      post: {
        summary: 'Acknowledge an alert',
        tags: ['Alerts'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'integer' } }],
        responses: { '200': { description: 'Alert acknowledged' } },
      },
    },
    '/health-checks': {
      get: {
        summary: 'Health check results',
        tags: ['Health'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'app_id', in: 'query', schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Health check entries', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/HealthCheck' } } } } } },
      },
    },
    '/reports': {
      get: {
        summary: 'Generate reports',
        tags: ['Reports'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Report data' } },
      },
    },
    '/reports/export': {
      get: {
        summary: 'Export report (CSV or PDF)',
        tags: ['Reports'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'format', in: 'query', schema: { type: 'string', enum: ['csv', 'pdf'] } }],
        responses: { '200': { description: 'Exported file' } },
      },
    },
    '/user': {
      get: { summary: 'Get current user info', tags: ['User'], security: [{ bearerAuth: [] }], responses: { '200': { description: 'User profile' } } },
    },
    '/config/mode': {
      get: { summary: 'Get current mode', tags: ['Config'], security: [{ bearerAuth: [] }], responses: { '200': { description: 'Current mode' } } },
    },
    '/health': {
      get: { summary: 'Health check', tags: ['Health'], responses: { '200': { description: 'Server health status' } } },
    },
    '/demo/flag': {
      get: { summary: 'Demo feature flag', tags: ['Demo'], responses: { '200': { description: 'Demo flag status' } } },
    },
    '/customers': {
      get: { summary: 'List customers (Business Mode)', tags: ['Customers'], security: [{ bearerAuth: [] }], responses: { '200': { description: 'Customers list' } } },
      post: { summary: 'Create customer (Business Mode)', tags: ['Customers'], security: [{ bearerAuth: [] }], responses: { '201': { description: 'Customer created' } } },
    },
    '/customers/{customerId}': {
      patch: { summary: 'Update customer', tags: ['Customers'], security: [{ bearerAuth: [] }], parameters: [{ name: 'customerId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }], responses: { '200': { description: 'Customer updated' } } },
      delete: { summary: 'Delete customer', tags: ['Customers'], security: [{ bearerAuth: [] }], parameters: [{ name: 'customerId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }], responses: { '200': { description: 'Customer deleted' } } },
    },
    '/seed-demo': {
      post: { summary: 'Seed demo data', tags: ['Demo'], security: [{ bearerAuth: [] }], responses: { '200': { description: 'Demo data seeded' } } },
    },
    '/search': {
      get: {
        summary: 'Global search across apps, audit logs, and backups',
        tags: ['Search'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'q', in: 'query', required: true, schema: { type: 'string', minLength: 2 } }],
        responses: { '200': { description: 'Search results', content: { 'application/json': { schema: { type: 'object', properties: { results: { type: 'array', items: { $ref: '#/components/schemas/SearchResult' } } } } } } }, '400': { description: 'Query too short' } },
      },
    },
    '/audit-log': {
      get: {
        summary: 'Paginated audit log entries',
        tags: ['Audit'],
        security: [{ bearerAuth: [] }],
        parameters: [
          { name: 'user_id', in: 'query', schema: { type: 'string', format: 'uuid' } },
          { name: 'entity_type', in: 'query', schema: { type: 'string' } },
          { name: 'action', in: 'query', schema: { type: 'string' } },
          { name: 'start_date', in: 'query', schema: { type: 'string', format: 'date-time' } },
          { name: 'end_date', in: 'query', schema: { type: 'string', format: 'date-time' } },
          { name: 'limit', in: 'query', schema: { type: 'integer', default: 50 } },
          { name: 'offset', in: 'query', schema: { type: 'integer', default: 0 } },
        ],
        responses: { '200': { description: 'Audit log entries', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/AuditLog' } } } } } },
      },
    },
    '/notification-channels': {
      get: {
        summary: 'List notification channels',
        tags: ['Notifications'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Notification channels', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/NotificationChannel' } } } } } },
      },
      post: {
        summary: 'Create notification channel',
        tags: ['Notifications'],
        security: [{ bearerAuth: [] }],
        requestBody: { required: true, content: { 'application/json': { schema: { type: 'object', required: ['name', 'type', 'config'], properties: { name: { type: 'string' }, type: { type: 'string', enum: ['email', 'webhook', 'telegram'] }, config: { type: 'object' } } } } } },
        responses: { '201': { description: 'Channel created' } },
      },
    },
    '/notification-channels/{id}': {
      patch: {
        summary: 'Update notification channel',
        tags: ['Notifications'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Channel updated' }, '404': { description: 'Not found' } },
      },
      delete: {
        summary: 'Delete notification channel',
        tags: ['Notifications'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Channel deleted' } },
      },
    },
    '/notification-channels/{id}/test': {
      post: {
        summary: 'Send test notification',
        tags: ['Notifications'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: { '200': { description: 'Test notification sent' } },
      },
    },
    '/rbac/me': {
      get: {
        summary: 'Get the caller\'s authorization state',
        description: 'Returns the caller\'s instance role, app assignments, and organization memberships. Powers frontend route guards.',
        tags: ['RBAC'],
        security: [{ bearerAuth: [] }],
        responses: {
          '200': { description: 'Authorization state', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacMe' } } } },
          '401': { description: 'Unauthorized' },
        },
      },
    },
    '/rbac/instance-roles': {
      get: {
        summary: 'List instance-level role assignments',
        tags: ['RBAC'],
        security: [{ bearerAuth: [] }],
        responses: {
          '200': {
            description: 'Assignments',
            content: { 'application/json': { schema: { type: 'object', properties: { roles: { type: 'array', items: { $ref: '#/components/schemas/RbacInstanceRole' } } } } } },
          },
          '401': { description: 'Unauthorized' },
          '403': { description: 'Forbidden', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacDenial' } } } },
        },
      },
      post: {
        summary: 'Grant or change an instance role',
        description: 'Requires instance admin. Audited. Refuses to demote the last instance admin.',
        tags: ['RBAC'],
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['userId', 'role'],
                properties: {
                  userId: { type: 'string', format: 'uuid' },
                  role: { type: 'string', enum: ['admin', 'operator', 'viewer'] },
                },
              },
            },
          },
        },
        responses: {
          '201': { description: 'Assignment written', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacInstanceRole' } } } },
          '400': { description: 'Invalid body' },
          '403': { description: 'Forbidden', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacDenial' } } } },
          '409': { description: 'Demotion would remove the last instance admin' },
        },
      },
    },
    '/rbac/instance-roles/{userId}': {
      delete: {
        summary: 'Revoke an instance role',
        description: 'Requires instance admin. Audited. Refuses to revoke the last instance admin.',
        tags: ['RBAC'],
        security: [{ bearerAuth: [] }],
        parameters: [{ name: 'userId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        responses: {
          '200': { description: 'Revoked' },
          '403': { description: 'Forbidden', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacDenial' } } } },
          '404': { description: 'Assignment not found' },
          '409': { description: 'Revocation would remove the last instance admin' },
        },
      },
    },
    '/sso/providers': {
      get: {
        summary: 'List configured SSO providers',
        description: 'Returns enabled booleans only. Providers are enabled when their OIDC env configuration (client id + secret) is present. GitHub is listed but never enabled: its OAuth2 flow has no id_token and cannot run the OIDC path.',
        tags: ['SSO'],
        responses: {
          '200': {
            description: 'Provider flags',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    providers: {
                      type: 'array',
                      items: {
                        type: 'object',
                        properties: {
                          id: { type: 'string', enum: ['google', 'microsoft', 'oidc', 'github'] },
                          name: { type: 'string' },
                          enabled: { type: 'boolean' },
                        },
                      },
                    },
                    saml: {
                      type: 'object',
                      properties: {
                        enabled: { type: 'boolean' },
                        note: { type: 'string' },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    '/sso/login/{providerId}': {
      get: {
        summary: 'Start the OIDC authorization-code flow (browser redirect)',
        description: '302 redirect to the identity provider with PKCE (S256), state, and nonce. The state is single-use and expires after ten minutes.',
        tags: ['SSO'],
        parameters: [{ name: 'providerId', in: 'path', required: true, schema: { type: 'string', enum: ['google', 'microsoft', 'oidc'] } }],
        responses: {
          '302': { description: 'Redirect to the IdP' },
          '404': { description: 'Unknown provider' },
          '502': { description: 'OIDC discovery failed' },
          '503': { description: 'Provider not configured' },
        },
      },
    },
    '/sso/callback/{providerId}': {
      get: {
        summary: 'OIDC callback (browser redirect from the IdP)',
        description: 'Validates state, exchanges the code (PKCE), verifies the id_token (RS256/JWKS, iss/aud/exp/nonce), provisions or links the identity, and redirects to the SPA with a panel-session token in the URL fragment plus the ip_session cookie.',
        tags: ['SSO'],
        parameters: [{ name: 'providerId', in: 'path', required: true, schema: { type: 'string' } }],
        responses: {
          '302': { description: 'Redirect to the SPA on success or failure reason' },
        },
      },
    },
    '/sso/session': {
      get: {
        summary: 'Describe the current authentication context',
        tags: ['SSO'],
        security: [{ bearerAuth: [] }],
        responses: {
          '200': {
            description: 'Authentication method in use',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    user: { type: 'string', format: 'uuid', nullable: true },
                    method: { type: 'string', enum: ['sso-session', 'none', 'jwt', 'api-key'] },
                    provider: { type: 'string', nullable: true },
                    expiresAt: { type: 'string', format: 'date-time', nullable: true },
                  },
                },
              },
            },
          },
        },
      },
    },
    '/sso/logout': {
      post: {
        summary: 'Revoke the current SSO panel session and clear the cookie',
        tags: ['SSO'],
        security: [{ bearerAuth: [] }],
        responses: { '200': { description: 'Logged out' } },
      },
    },
    '/sso/group-roles': {
      get: {
        summary: 'List group to instance-role mappings (admin)',
        tags: ['SSO'],
        security: [{ bearerAuth: [] }],
        responses: {
          '200': {
            description: 'Mappings',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    mappings: {
                      type: 'array',
                      items: {
                        type: 'object',
                        properties: {
                          id: { type: 'string', format: 'uuid' },
                          provider: { type: 'string', enum: ['google', 'microsoft', 'oidc'] },
                          group_name: { type: 'string' },
                          role: { type: 'string', enum: ['admin', 'operator', 'viewer'] },
                          created_at: { type: 'string', format: 'date-time' },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          '403': { description: 'Forbidden', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacDenial' } } } },
        },
      },
      put: {
        summary: 'Upsert a group to instance-role mapping (admin)',
        description: 'Body: { provider, group, role }. Applied at next SSO login; only takes effect for users without an admin-set instance role. Audited.',
        tags: ['SSO'],
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['provider', 'group', 'role'],
                properties: {
                  provider: { type: 'string', enum: ['google', 'microsoft', 'oidc'] },
                  group: { type: 'string' },
                  role: { type: 'string', enum: ['admin', 'operator', 'viewer'] },
                },
              },
            },
          },
        },
        responses: {
          '201': { description: 'Mapping saved' },
          '400': { description: 'Invalid body' },
          '403': { description: 'Forbidden', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacDenial' } } } },
        },
      },
      delete: {
        summary: 'Remove a group to instance-role mapping (admin)',
        description: 'Body: { provider, group }. Audited.',
        tags: ['SSO'],
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['provider', 'group'],
                properties: {
                  provider: { type: 'string', enum: ['google', 'microsoft', 'oidc'] },
                  group: { type: 'string' },
                },
              },
            },
          },
        },
        responses: {
          '200': { description: 'Mapping removed' },
          '404': { description: 'Mapping not found' },
          '403': { description: 'Forbidden', content: { 'application/json': { schema: { $ref: '#/components/schemas/RbacDenial' } } } },
        },
      },
    },
  },
};

export default spec;
