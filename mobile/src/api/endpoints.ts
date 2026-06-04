import { apiClient } from './client';
import {
  Server, UserProfile, ServerMetric, BackupJob, BackupStatusEntry,
  BillingInfo, Transaction, CostEstimate, LogEntry,
} from '../types';

export const endpoints = {
  auth: {
    login: (email: string, password: string) =>
      apiClient.post<{ token: string; user: UserProfile }>('/api/auth/login', { email, password }),
    register: (email: string, password: string, displayName: string) =>
      apiClient.post<{ token: string; user: UserProfile }>('/api/auth/register', {
        email,
        password,
        displayName,
      }),
    me: () => apiClient.get<UserProfile>('/api/user'),
  },

  servers: {
    list: () => apiClient.get<Server[]>('/api/apps'),
    get: (id: string) => apiClient.get<Server>(`/api/apps/${id}`),
    create: (data: Partial<Server>) => apiClient.post<Server>('/api/apps', data),
    update: (id: string, data: Partial<Server>) =>
      apiClient.patch<Server>(`/api/apps/${id}`, data),
    delete: (id: string) => apiClient.delete<void>(`/api/apps/${id}`),
    start: (id: string) => apiClient.post<Server>(`/api/apps/${id}/start`),
    stop: (id: string) => apiClient.post<Server>(`/api/apps/${id}/stop`),
    restart: (id: string) => apiClient.post<Server>(`/api/apps/${id}/restart`),
  },

  logs: {
    get: (appId: string, limit = 100, offset = 0) =>
      apiClient.get<LogEntry[]>(`/api/apps/${appId}/logs`, { limit, offset }),
    search: (
      appId: string,
      params: { query?: string; level?: string; from?: string; to?: string; page?: number; limit?: number }
    ) =>
      apiClient.get<{ logs: LogEntry[]; total: number; page: number }>(
        `/api/apps/${appId}/logs`,
        params
      ),
  },

  metrics: {
    get: (appId: string, range = '30m') =>
      apiClient.get<ServerMetric[]>(`/api/apps/${appId}/metrics`, { range }),
    aggregated: () => apiClient.get<any>('/api/metrics/aggregated'),
  },

  backups: {
    list: () => apiClient.get<BackupJob[]>('/api/backup-jobs'),
    create: (job: Partial<BackupJob>) => apiClient.post<BackupJob>('/api/backup-jobs', job),
    update: (id: string, updates: Partial<BackupJob>) =>
      apiClient.patch<BackupJob>(`/api/backup-jobs/${id}`, updates),
    delete: (id: string) => apiClient.delete<void>(`/api/backup-jobs/${id}`),
    status: (jobId: string) =>
      apiClient.get<BackupStatusEntry[]>(`/api/backup-jobs/${jobId}/status`),
  },

  billing: {
    balance: () => apiClient.get<BillingInfo>('/api/billing/balance'),
    topUp: (amount: number) => apiClient.post<BillingInfo>('/api/billing/topup', { amount }),
    transactions: () => apiClient.get<Transaction[]>('/api/billing/transactions'),
    costEstimate: (cpu: number, ram: number, storage: number) =>
      apiClient.get<CostEstimate>('/api/billing/cost-estimate', { cpu, ram, storage }),
    rates: () => apiClient.get<any>('/api/billing/rates'),
  },

  health: () => apiClient.get<{ status: string }>('/health'),

  // === v3 Identity & Access ===
  identity: {
    oidc: {
      clients: () => apiClient.get<any[]>('/api/v1/identity/oidc/clients'),
      register: (name: string, redirectUris: string[], type: string) =>
        apiClient.post<any>('/api/v1/identity/oidc/clients', { client_name: name, redirect_uris: redirectUris, client_type: type }),
      delete: (clientId: string) => apiClient.delete<void>(`/api/v1/identity/oidc/clients/${clientId}`),
      authorize: (clientId: string, redirectUri: string, scope: string) =>
        apiClient.get<any>('/api/v1/identity/oidc/authorize', { client_id: clientId, redirect_uri: redirectUri, scope }),
      token: (code: string, clientId: string, clientSecret: string) =>
        apiClient.post<any>('/api/v1/identity/oidc/token', { code, client_id: clientId, client_secret: clientSecret }),
      userinfo: () => apiClient.get<any>('/api/v1/identity/oidc/userinfo'),
      config: () => apiClient.get<any>('/api/v1/identity/oidc/.well-known/openid-configuration'),
    },
    webauthn: {
      credentials: (userId: string) => apiClient.get<any[]>(`/api/v1/identity/webauthn/credentials?user_id=${userId}`),
      register: (userId: string) => apiClient.post<any>('/api/v1/identity/webauthn/register', { user_id: userId }),
      login: (userId: string) => apiClient.post<any>('/api/v1/identity/webauthn/login', { user_id: userId }),
      remove: (credId: string) => apiClient.delete<void>(`/api/v1/identity/webauthn/credentials/${credId}`),
    },
    sessions: {
      list: (userId: string) => apiClient.get<any[]>(`/api/v1/identity/sessions?user_id=${userId}`),
      revoke: (sessionId: string) => apiClient.post<void>(`/api/v1/identity/sessions/${sessionId}/revoke`),
      activities: (sessionId: string) => apiClient.get<any[]>(`/api/v1/identity/sessions/${sessionId}/activities`),
    },
    pam: {
      requests: (params?: { user_id?: string; status?: string }) =>
        apiClient.get<any[]>('/api/v1/identity/pam/requests', params),
      create: (userId: string, resource: string, role: string, reason: string, duration?: number) =>
        apiClient.post<any>('/api/v1/identity/pam/requests', { user_id: userId, resource, role, reason, duration }),
      approve: (requestId: string, approverId: string) =>
        apiClient.post<any>(`/api/v1/identity/pam/requests/${requestId}/approve`, { approver_id: approverId }),
      deny: (requestId: string, approverId: string) =>
        apiClient.post<any>(`/api/v1/identity/pam/requests/${requestId}/deny`, { approver_id: approverId }),
      breakGlass: (userId: string, resource: string, reason: string) =>
        apiClient.post<any>('/api/v1/identity/pam/break-glass', { user_id: userId, resource, reason }),
    },
    breaches: {
      list: (status?: string) => apiClient.get<any[]>('/api/v1/identity/breaches', { status }),
      report: (description: string, affectedDataTypes: string[], affectedUsers: number) =>
        apiClient.post<any>('/api/v1/identity/breaches', { description, affected_data_types: affectedDataTypes, affected_users_count: affectedUsers }),
      get: (breachId: string) => apiClient.get<any>(`/api/v1/identity/breaches/${breachId}`),
      timeline: (breachId: string) => apiClient.get<any[]>(`/api/v1/identity/breaches/${breachId}/timeline`),
      notify: (breachId: string, type: string) =>
        apiClient.post<any>(`/api/v1/identity/breaches/${breachId}/notify`, { notification_type: type }),
    },
  },

  // === v3 Governance ===
  governance: {
    policies: {
      list: (category?: string) => apiClient.get<any[]>('/api/v1/governance/policies', { category }),
      create: (name: string, description: string, category: string, rules: any[]) =>
        apiClient.post<any>('/api/v1/governance/policies', { name, description, category, rules }),
      get: (policyId: string) => apiClient.get<any>(`/api/v1/governance/policies/${policyId}`),
      update: (policyId: string, data: any) => apiClient.patch<any>(`/api/v1/governance/policies/${policyId}`, data),
      delete: (policyId: string) => apiClient.delete<void>(`/api/v1/governance/policies/${policyId}`),
      evaluate: (resource: string, action: string, context: any) =>
        apiClient.post<any>('/api/v1/governance/policies/evaluate', { resource, action, context }),
    },
    compliance: {
      scan: (benchmark: string) => apiClient.post<any>('/api/v1/governance/compliance/scan', { benchmark }),
      getScan: (scanId: string) => apiClient.get<any>(`/api/v1/governance/compliance/scans/${scanId}`),
      history: () => apiClient.get<any[]>('/api/v1/governance/compliance/scans'),
      checks: (benchmark: string) => apiClient.get<any[]>(`/api/v1/governance/compliance/checks?benchmark=${benchmark}`),
      waivers: () => apiClient.get<any[]>('/api/v1/governance/compliance/waivers'),
      addWaiver: (checkId: string, reason: string) =>
        apiClient.post<any>('/api/v1/governance/compliance/waivers', { check_id: checkId, reason }),
      report: (scanId: string) => apiClient.get<any>(`/api/v1/governance/compliance/report/${scanId}`),
    },
    audit: {
      anomalies: (threshold?: number) => apiClient.get<any[]>(`/api/v1/governance/audit/anomalies${threshold ? `?threshold=${threshold}` : ''}`),
      trend: (userId: string) => apiClient.get<any>(`/api/v1/governance/audit/trend/${userId}`),
      summary: () => apiClient.get<any>('/api/v1/governance/audit/summary'),
      userReport: (userId: string) => apiClient.get<any>(`/api/v1/governance/audit/users/${userId}/report`),
    },
    classification: {
      scanText: (text: string) => apiClient.post<any>('/api/v1/governance/classify/scan', { text }),
      inventory: () => apiClient.get<any[]>('/api/v1/governance/classify/inventory'),
      addToInventory: (path: string, category: string, classification: string, patterns: string[]) =>
        apiClient.post<any>('/api/v1/governance/classify/inventory', { path, category, classification, patterns }),
      removeFromInventory: (itemId: string) => apiClient.delete<void>(`/api/v1/governance/classify/inventory/${itemId}`),
    },
    vendors: {
      list: () => apiClient.get<any[]>('/api/v1/governance/vendors'),
      register: (name: string, domain: string, category: string) =>
        apiClient.post<any>('/api/v1/governance/vendors', { name, domain, category }),
      get: (vendorId: string) => apiClient.get<any>(`/api/v1/governance/vendors/${vendorId}`),
      assessments: (vendorId: string) => apiClient.get<any[]>(`/api/v1/governance/vendors/${vendorId}/assessments`),
      createAssessment: (vendorId: string, questionnaireType: string) =>
        apiClient.post<any>(`/api/v1/governance/vendors/${vendorId}/assessments`, { questionnaire_type: questionnaireType }),
      findings: (vendorId: string) => apiClient.get<any[]>(`/api/v1/governance/vendors/${vendorId}/findings`),
      riskScore: (vendorId: string) => apiClient.get<any>(`/api/v1/governance/vendors/${vendorId}/risk-score`),
    },
  },

  // === v3 Orchestration ===
  orchestration: {
    workflows: {
      list: () => apiClient.get<any[]>('/api/v1/orchestration/workflows'),
      create: (name: string, description: string) =>
        apiClient.post<any>('/api/v1/orchestration/workflows', { name, description, nodes: [], edges: [] }),
      get: (workflowId: string) => apiClient.get<any>(`/api/v1/orchestration/workflows/${workflowId}`),
      execute: (workflowId: string) =>
        apiClient.post<any>(`/api/v1/orchestration/workflows/${workflowId}/execute`, { trigger_data: { source: 'mobile' } }),
      nodeTypes: () => apiClient.get<any[]>('/api/v1/orchestration/workflows/node-types'),
    },
    pipelines: {
      list: () => apiClient.get<any[]>('/api/v1/orchestration/pipelines'),
      create: (name: string, repoUrl: string, branch: string) =>
        apiClient.post<any>('/api/v1/orchestration/pipelines', { name, repo_url: repoUrl, branch }),
      run: (pipelineId: string) => apiClient.post<any>(`/api/v1/orchestration/pipelines/${pipelineId}/run`, { triggered_by: 'mobile' }),
      getRun: (runId: string) => apiClient.get<any>(`/api/v1/orchestration/pipelines/runs/${runId}`),
      approve: (runId: string) => apiClient.post<any>(`/api/v1/orchestration/pipelines/runs/${runId}/approve`),
      reject: (runId: string, reason: string) => apiClient.post<any>(`/api/v1/orchestration/pipelines/runs/${runId}/reject`, { reason }),
    },
    drift: {
      scan: () => apiClient.post<any>('/api/v1/orchestration/drift/scan'),
      scans: () => apiClient.get<any[]>('/api/v1/orchestration/drift/scans'),
      getScan: (scanId: string) => apiClient.get<any>(`/api/v1/orchestration/drift/scans/${scanId}`),
    },
    quotas: {
      list: () => apiClient.get<any[]>('/api/v1/orchestration/quotas'),
      check: (entityType: string, entityId: string, resources: any) =>
        apiClient.post<any>('/api/v1/orchestration/quotas/check', { entity_type: entityType, entity_id: entityId, resources }),
      requestIncrease: (entityType: string, entityId: string, newLimits: any, reason: string) =>
        apiClient.post<any>('/api/v1/orchestration/quotas/increase', { entity_type: entityType, entity_id: entityId, new_limits: newLimits, reason }),
    },
    remediation: {
      rules: () => apiClient.get<any[]>('/api/v1/orchestration/remediation/rules'),
      history: () => apiClient.get<any[]>('/api/v1/orchestration/remediation/history'),
      status: () => apiClient.get<any>('/api/v1/orchestration/remediation/status'),
    },
    maintenance: {
      windows: () => apiClient.get<any[]>('/api/v1/orchestration/maintenance/windows'),
      schedule: (name: string, startTime: string, endTime: string, systems: string[]) =>
        apiClient.post<any>('/api/v1/orchestration/maintenance/windows', { name, start_time: startTime, end_time: endTime, affected_systems: systems }),
      complete: (windowId: string, notes: string) =>
        apiClient.post<any>(`/api/v1/orchestration/maintenance/windows/${windowId}/complete`, { completion_notes: notes }),
      cancel: (windowId: string, reason: string) =>
        apiClient.post<any>(`/api/v1/orchestration/maintenance/windows/${windowId}/cancel`, { reason }),
    },
    runbooks: {
      templates: () => apiClient.get<any[]>('/api/v1/orchestration/runbook-templates'),
      get: (templateId: string) => apiClient.get<any>(`/api/v1/orchestration/runbook-templates/${templateId}`),
      instantiate: (templateId: string, variables: any) =>
        apiClient.post<any>(`/api/v1/orchestration/runbook-templates/${templateId}/instantiate`, { variables }),
      progress: (instanceId: string) => apiClient.get<any>(`/api/v1/orchestration/runbook-instances/${instanceId}/progress`),
    },
    chaos: {
      experiments: () => apiClient.get<any[]>('/api/v1/orchestration/chaos/experiments'),
      create: (name: string, target: any, faults: any[]) =>
        apiClient.post<any>('/api/v1/orchestration/chaos/experiments', { name, target, faults }),
      run: (experimentId: string) => apiClient.post<any>(`/api/v1/orchestration/chaos/experiments/${experimentId}/run`),
      stop: (experimentId: string) => apiClient.post<any>(`/api/v1/orchestration/chaos/experiments/${experimentId}/stop`),
      faultTypes: () => apiClient.get<any[]>('/api/v1/orchestration/chaos/fault-types'),
    },
    healing: {
      status: () => apiClient.get<any>('/api/v1/orchestration/healing/status'),
      history: () => apiClient.get<any[]>('/api/v1/orchestration/healing/history'),
      retrain: () => apiClient.post<any>('/api/v1/orchestration/healing/retrain'),
      remediate: (context: any) => apiClient.post<any>('/api/v1/orchestration/healing/remediate', { context }),
      patterns: () => apiClient.get<any[]>('/api/v1/orchestration/healing/patterns'),
    },
  },

  // === v3 Advanced Networking ===
  networking: {
    sdwan: {
      status: () => apiClient.get<any>('/api/v1/networking/sdwan/status'),
      apps: () => apiClient.get<any[]>('/api/v1/networking/sdwan/apps'),
      createApp: (data: any) => apiClient.post<any>('/api/v1/networking/sdwan/apps', data),
      deleteApp: (id: string) => apiClient.delete<void>(`/api/v1/networking/sdwan/apps/${id}`),
      toggleApp: (id: string) => apiClient.post<any>(`/api/v1/networking/sdwan/apps/${id}/toggle`),
      metrics: () => apiClient.get<any>('/api/v1/networking/sdwan/metrics'),
    },
    vpn: {
      configs: () => apiClient.get<any[]>('/api/v1/networking/vpn/configs'),
      createConfig: (data: any) => apiClient.post<any>('/api/v1/networking/vpn/configs', data),
      deleteConfig: (id: string) => apiClient.delete<void>(`/api/v1/networking/vpn/configs/${id}`),
      status: () => apiClient.get<any>('/api/v1/networking/vpn/status'),
    },
    dns: {
      zones: () => apiClient.get<any[]>('/api/v1/networking/dns/zones'),
      createZone: (data: any) => apiClient.post<any>('/api/v1/networking/dns/zones', data),
      deleteZone: (id: string) => apiClient.delete<void>(`/api/v1/networking/dns/zones/${id}`),
      records: (zoneId: string) => apiClient.get<any[]>(`/api/v1/networking/dns/zones/${zoneId}/records`),
      createRecord: (zoneId: string, data: any) => apiClient.post<any>(`/api/v1/networking/dns/zones/${zoneId}/records`, data),
      deleteRecord: (zoneId: string, recordId: string) => apiClient.delete<void>(`/api/v1/networking/dns/zones/${zoneId}/records/${recordId}`),
    },
    bgp: {
      sessions: () => apiClient.get<any[]>('/api/v1/networking/bgp/sessions'),
      createSession: (data: any) => apiClient.post<any>('/api/v1/networking/bgp/sessions', data),
      deleteSession: (id: string) => apiClient.delete<void>(`/api/v1/networking/bgp/sessions/${id}`),
      routes: () => apiClient.get<any[]>('/api/v1/networking/bgp/routes'),
    },
    proxy: {
      rules: () => apiClient.get<any[]>('/api/v1/networking/proxy/rules'),
      createRule: (data: any) => apiClient.post<any>('/api/v1/networking/proxy/rules', data),
      deleteRule: (id: string) => apiClient.delete<void>(`/api/v1/networking/proxy/rules/${id}`),
      toggleRule: (id: string) => apiClient.post<any>(`/api/v1/networking/proxy/rules/${id}/toggle`),
    },
    segments: {
      list: () => apiClient.get<any[]>('/api/v1/networking/segments'),
      create: (data: any) => apiClient.post<any>('/api/v1/networking/segments', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/networking/segments/${id}`),
    },
    captures: {
      list: () => apiClient.get<any[]>('/api/v1/networking/captures'),
      start: (data: any) => apiClient.post<any>('/api/v1/networking/captures', data),
      stop: (id: string) => apiClient.post<any>(`/api/v1/networking/captures/${id}/stop`),
      status: (id: string) => apiClient.get<any>(`/api/v1/networking/captures/${id}`),
      packets: (id: string) => apiClient.get<any[]>(`/api/v1/networking/captures/${id}/packets`),
    },
    dnsfilter: {
      status: () => apiClient.get<any>('/api/v1/networking/dnsfilter/status'),
      rules: () => apiClient.get<any[]>('/api/v1/networking/dnsfilter/rules'),
      createRule: (data: any) => apiClient.post<any>('/api/v1/networking/dnsfilter/rules', data),
      deleteRule: (id: string) => apiClient.delete<void>(`/api/v1/networking/dnsfilter/rules/${id}`),
      toggleRule: (id: string) => apiClient.post<any>(`/api/v1/networking/dnsfilter/rules/${id}/toggle`),
    },
    dhcp: {
      leases: () => apiClient.get<any[]>('/api/v1/networking/dhcp/leases'),
    },
    costs: {
      get: () => apiClient.get<any>('/api/v1/networking/costs'),
      setBudget: (data: any) => apiClient.post<any>('/api/v1/networking/costs/budget', data),
    },
    cellular: {
      networks: () => apiClient.get<any[]>('/api/v1/networking/cellular/networks'),
      register: (data: any) => apiClient.post<any>('/api/v1/networking/cellular/networks', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/networking/cellular/networks/${id}`),
      status: () => apiClient.get<any>('/api/v1/networking/cellular/status'),
      sims: () => apiClient.get<any[]>('/api/v1/networking/cellular/sims'),
      activateSim: (id: string) => apiClient.post<any>(`/api/v1/networking/cellular/sims/${id}/activate`),
      deactivateSim: (id: string) => apiClient.post<any>(`/api/v1/networking/cellular/sims/${id}/deactivate`),
    },
  },

  // === v4 Customer Experience ===
  customerExperience: {
    health: {
      profiles: (params?: any) => apiClient.get<any[]>('/api/v1/cx/health/profile', params),
      get: (customerId: string) => apiClient.get<any>(`/api/v1/cx/health/profile/${customerId}`),
      compute: (customerId: string, data: any) => apiClient.post<any>(`/api/v1/cx/health/compute/${customerId}`, data),
      history: (customerId: string, days?: number) => apiClient.get<any[]>(`/api/v1/cx/health/history/${customerId}`, { days }),
      stats: () => apiClient.get<any>('/api/v1/cx/health/stats'),
    },
    tickets: {
      list: (params?: any) => apiClient.get<any[]>('/api/v1/cx/tickets', params),
      create: (data: any) => apiClient.post<any>('/api/v1/cx/tickets', data),
      get: (id: string) => apiClient.get<any>(`/api/v1/cx/tickets/${id}`),
      updateStatus: (id: string, data: any) => apiClient.patch<any>(`/api/v1/cx/tickets/${id}/status`, data),
      addComment: (id: string, data: any) => apiClient.post<any>(`/api/v1/cx/tickets/${id}/comments`, data),
      assign: (id: string, data: any) => apiClient.post<any>(`/api/v1/cx/tickets/${id}/assign`, data),
      stats: () => apiClient.get<any>('/api/v1/cx/tickets/stats'),
      slas: {
        list: () => apiClient.get<any[]>('/api/v1/cx/slas'),
        create: (data: any) => apiClient.post<any>('/api/v1/cx/slas', data),
      },
      cannedResponses: {
        list: (category?: string) => apiClient.get<any[]>('/api/v1/cx/canned-responses', { category }),
        create: (data: any) => apiClient.post<any>('/api/v1/cx/canned-responses', data),
      },
    },
    sentiment: {
      analyze: (data: any) => apiClient.post<any>('/api/v1/cx/sentiment/analyze', data),
      profile: (customerId: string) => apiClient.get<any>(`/api/v1/cx/sentiment/profile/${customerId}`),
      interactions: (params?: any) => apiClient.get<any[]>('/api/v1/cx/sentiment/interactions', params),
      trends: (params?: any) => apiClient.get<any[]>('/api/v1/cx/sentiment/trends', params),
      alerts: () => apiClient.get<any[]>('/api/v1/cx/sentiment/alerts'),
    },
    adoption: {
      summary: (customerId: string) => apiClient.get<any>(`/api/v1/cx/adoption/summary/${customerId}`),
      features: (customerId: string, days?: number) => apiClient.get<any[]>(`/api/v1/cx/adoption/features/${customerId}`, { days }),
      track: (data: any) => apiClient.post<any>('/api/v1/cx/adoption/track', data),
      recommendations: (customerId: string) => apiClient.get<any[]>(`/api/v1/cx/adoption/recommendations/${customerId}`),
      stats: () => apiClient.get<any>('/api/v1/cx/adoption/stats'),
    },
    onboarding: {
      start: (data: any) => apiClient.post<any>('/api/v1/cx/onboarding/start', data),
      get: (customerId: string) => apiClient.get<any>(`/api/v1/cx/onboarding/session/${customerId}`),
      step: (data: any) => apiClient.post<any>('/api/v1/cx/onboarding/step', data),
      stats: () => apiClient.get<any>('/api/v1/cx/onboarding/stats'),
    },
    knowledgeBase: {
      articles: (params?: any) => apiClient.get<any[]>('/api/v1/cx/kb/articles', params),
      createArticle: (data: any) => apiClient.post<any>('/api/v1/cx/kb/articles', data),
      getArticle: (id: string) => apiClient.get<any>(`/api/v1/cx/kb/articles/${id}`),
      updateArticle: (id: string, data: any) => apiClient.put<any>(`/api/v1/cx/kb/articles/${id}`, data),
      search: (params: any) => apiClient.get<any[]>('/api/v1/cx/kb/search', params),
      categories: () => apiClient.get<any[]>('/api/v1/cx/kb/categories'),
      feedback: (data: any) => apiClient.post<any>('/api/v1/cx/kb/feedback', data),
    },
    community: {
      posts: (params?: any) => apiClient.get<any[]>('/api/v1/cx/community/posts', params),
      createPost: (data: any) => apiClient.post<any>('/api/v1/cx/community/posts', data),
      getPost: (id: string) => apiClient.get<any>(`/api/v1/cx/community/posts/${id}`),
      votePost: (id: string, data: any) => apiClient.post<any>(`/api/v1/cx/community/posts/${id}/vote`, data),
      addComment: (id: string, data: any) => apiClient.post<any>(`/api/v1/cx/community/posts/${id}/comments`, data),
      getComments: (id: string) => apiClient.get<any[]>(`/api/v1/cx/community/posts/${id}/comments`),
      featureRequests: (params?: any) => apiClient.get<any[]>('/api/v1/cx/community/feature-requests', params),
      categories: () => apiClient.get<any[]>('/api/v1/cx/community/categories'),
      leaderboard: (limit?: number) => apiClient.get<any[]>('/api/v1/cx/community/leaderboard', { limit }),
      stats: () => apiClient.get<any>('/api/v1/cx/community/stats'),
    },
    communication: {
      send: (data: any) => apiClient.post<any>('/api/v1/cx/communication/send', data),
      batches: (limit?: number) => apiClient.get<any[]>('/api/v1/cx/communication/batches', { limit }),
      batchStats: (id: string) => apiClient.get<any>(`/api/v1/cx/communication/batch/${id}`),
      scheduleMaintenance: (data: any) => apiClient.post<any>('/api/v1/cx/communication/maintenance', data),
      listMaintenance: (status?: string) => apiClient.get<any[]>('/api/v1/cx/communication/maintenance', { status }),
      completeMaintenance: (id: string, data: any) => apiClient.post<any>(`/api/v1/cx/communication/maintenance/${id}/complete`, data),
      templates: (channel?: string) => apiClient.get<any[]>('/api/v1/cx/communication/templates', { channel }),
      createTemplate: (data: any) => apiClient.post<any>('/api/v1/cx/communication/templates', data),
    },
    nps: {
      createSurvey: (data: any) => apiClient.post<any>('/api/v1/cx/nps/surveys', data),
      surveys: (params?: any) => apiClient.get<any[]>('/api/v1/cx/nps/surveys', params),
      getSurvey: (id: string) => apiClient.get<any>(`/api/v1/cx/nps/surveys/${id}`),
      send: (surveyId: string, data: any) => apiClient.post<any>(`/api/v1/cx/nps/send/${surveyId}`, data),
      respond: (responseId: string, data: any) => apiClient.post<any>(`/api/v1/cx/nps/respond/${responseId}`, data),
      score: () => apiClient.get<any>('/api/v1/cx/nps/score'),
      trend: (days?: number) => apiClient.get<any[]>('/api/v1/cx/nps/trend', { days }),
      detractors: (limit?: number) => apiClient.get<any[]>('/api/v1/cx/nps/detractors', { limit }),
      stats: () => apiClient.get<any>('/api/v1/cx/nps/stats'),
    },
    success: {
      plays: (params?: any) => apiClient.get<any[]>('/api/v1/cx/success/plays', params),
      createPlay: (data: any) => apiClient.post<any>('/api/v1/cx/success/plays', data),
      updateStatus: (id: string, data: any) => apiClient.patch<any>(`/api/v1/cx/success/plays/${id}/status`, data),
      trigger: (data: any) => apiClient.post<any>('/api/v1/cx/success/trigger', data),
      executions: (params?: any) => apiClient.get<any[]>('/api/v1/cx/success/executions', params),
      stats: () => apiClient.get<any>('/api/v1/cx/success/stats'),
    },
  },

  // === v3 Marketplace ===
  marketplace: {
    trades: {
      list: (params?: any) => apiClient.get<any[]>('/api/v1/marketplace/trades', params),
      create: (data: any) => apiClient.post<any>('/api/v1/marketplace/trades', data),
      accept: (id: string) => apiClient.post<any>(`/api/v1/marketplace/trades/${id}/accept`),
      cancel: (id: string) => apiClient.delete<void>(`/api/v1/marketplace/trades/${id}`),
    },
    apps: {
      list: (category?: string) => apiClient.get<any[]>('/api/v1/marketplace/apps', { category }),
      get: (id: string) => apiClient.get<any>(`/api/v1/marketplace/apps/${id}`),
      install: (id: string, targetServerId?: string) => apiClient.post<any>(`/api/v1/marketplace/apps/${id}/install`, { target_server_id: targetServerId }),
      installations: () => apiClient.get<any[]>('/api/v1/marketplace/apps/installations'),
    },
    ppu: {
      metrics: () => apiClient.get<any>('/api/v1/marketplace/ppu/metrics'),
      usage: () => apiClient.get<any[]>('/api/v1/marketplace/ppu/usage'),
      setBudget: (budget: number) => apiClient.post<any>('/api/v1/marketplace/ppu/budget', { monthly_budget: budget }),
    },
    resellers: {
      list: () => apiClient.get<any[]>('/api/v1/marketplace/resellers'),
      create: (data: any) => apiClient.post<any>('/api/v1/marketplace/resellers', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/marketplace/resellers/${id}`),
      analytics: (id: string) => apiClient.get<any>(`/api/v1/marketplace/resellers/${id}/analytics`),
    },
    whitelabel: {
      get: () => apiClient.get<any>('/api/v1/marketplace/whitelabel'),
      update: (data: any) => apiClient.put<any>('/api/v1/marketplace/whitelabel', data),
    },
    slas: {
      list: () => apiClient.get<any[]>('/api/v1/marketplace/slas'),
      create: (data: any) => apiClient.post<any>('/api/v1/marketplace/slas', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/marketplace/slas/${id}`),
      status: (id: string) => apiClient.get<any>(`/api/v1/marketplace/slas/${id}/status`),
    },
    credits: {
      list: () => apiClient.get<any[]>('/api/v1/marketplace/credits'),
      issue: (data: any) => apiClient.post<any>('/api/v1/marketplace/credits', data),
    },
    crypto: {
      wallets: () => apiClient.get<any[]>('/api/v1/marketplace/crypto/wallets'),
      createWallet: (data: any) => apiClient.post<any>('/api/v1/marketplace/crypto/wallets', data),
      transactions: () => apiClient.get<any[]>('/api/v1/marketplace/crypto/transactions'),
      rates: () => apiClient.get<any>('/api/v1/marketplace/crypto/rates'),
    },
    plans: {
      list: () => apiClient.get<any[]>('/api/v1/marketplace/plans'),
      create: (data: any) => apiClient.post<any>('/api/v1/marketplace/plans', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/marketplace/plans/${id}`),
      subscriptions: () => apiClient.get<any[]>('/api/v1/marketplace/plans/subscriptions'),
    },
    recommendations: {
      list: () => apiClient.get<any[]>('/api/v1/marketplace/recommendations'),
      summary: () => apiClient.get<any>('/api/v1/marketplace/recommendations/summary'),
      implement: (id: string) => apiClient.post<any>(`/api/v1/marketplace/recommendations/${id}/implement`),
      dismiss: (id: string) => apiClient.post<void>(`/api/v1/marketplace/recommendations/${id}/dismiss`),
    },
    tax: {
      rates: () => apiClient.get<any[]>('/api/v1/marketplace/tax/rates'),
      invoices: () => apiClient.get<any[]>('/api/v1/marketplace/tax/invoices'),
      generateInvoice: () => apiClient.post<any>('/api/v1/marketplace/tax/invoices/generate'),
      markPaid: (id: string) => apiClient.post<any>(`/api/v1/marketplace/tax/invoices/${id}/pay`),
      summary: () => apiClient.get<any>('/api/v1/marketplace/tax/summary'),
      fileReport: () => apiClient.post<any>('/api/v1/marketplace/tax/file'),
    },
  loyalty: {
      status: () => apiClient.get<any>('/api/v1/marketplace/loyalty/status'),
      badges: () => apiClient.get<any[]>('/api/v1/marketplace/loyalty/badges'),
      rewards: () => apiClient.get<any[]>('/api/v1/marketplace/loyalty/rewards'),
      redeem: (rewardId: string) => apiClient.post<any>(`/api/v1/marketplace/loyalty/rewards/${rewardId}/redeem`),
      leaderboard: () => apiClient.get<any[]>('/api/v1/marketplace/loyalty/leaderboard'),
    },
  },

  // === v4 Resiliency & Disaster Recovery ===
  resiliency: {
    dr: {
      plans: () => apiClient.get<any[]>('/api/v1/resiliency/dr/plans'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/dr/plans', data),
      get: (id: string) => apiClient.get<any>(`/api/v1/resiliency/dr/plans/${id}`),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/resiliency/dr/plans/${id}`),
      failover: (id: string, drill = false) => apiClient.post<any>(`/api/v1/resiliency/dr/plans/${id}/failover`, { is_drill: drill }),
      readiness: (id: string) => apiClient.post<any>(`/api/v1/resiliency/dr/plans/${id}/readiness`),
      compliance: () => apiClient.get<any>('/api/v1/resiliency/dr/compliance'),
    },
    activeActive: {
      regions: () => apiClient.get<any[]>('/api/v1/resiliency/active-active/regions'),
      register: (data: any) => apiClient.post<any>('/api/v1/resiliency/active-active/regions', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/resiliency/active-active/regions/${id}`),
      health: (id: string) => apiClient.post<any>(`/api/v1/resiliency/active-active/regions/${id}/health`),
      weight: (id: string, weight: number) => apiClient.post<any>(`/api/v1/resiliency/active-active/regions/${id}/weight`, { weight }),
      globalStatus: () => apiClient.get<any>('/api/v1/resiliency/active-active/global-status'),
    },
    backupSla: {
      list: () => apiClient.get<any[]>('/api/v1/resiliency/backup-sla'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/backup-sla', data),
      get: (id: string) => apiClient.get<any>(`/api/v1/resiliency/backup-sla/${id}`),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/resiliency/backup-sla/${id}`),
      verify: (id: string) => apiClient.post<any>(`/api/v1/resiliency/backup-sla/${id}/verify`),
      compliance: () => apiClient.get<any>('/api/v1/resiliency/backup-sla/compliance-report'),
    },
    chaos: {
      experiments: () => apiClient.get<any[]>('/api/v1/resiliency/chaos/experiments'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/chaos/experiments', data),
      approve: (id: string) => apiClient.post<any>(`/api/v1/resiliency/chaos/experiments/${id}/approve`),
      run: (id: string) => apiClient.post<any>(`/api/v1/resiliency/chaos/experiments/${id}/run`),
      results: () => apiClient.get<any[]>('/api/v1/resiliency/chaos/results'),
      dashboard: () => apiClient.get<any>('/api/v1/resiliency/chaos/dashboard'),
    },
    scoring: {
      score: (serviceId: string) => apiClient.post<any>(`/api/v1/resiliency/score/${serviceId}`, {}),
      get: (serviceId: string) => apiClient.get<any>(`/api/v1/resiliency/score/${serviceId}`),
      list: () => apiClient.get<any[]>('/api/v1/resiliency/scores'),
      orgSummary: () => apiClient.get<any>('/api/v1/resiliency/scores/org-summary'),
    },
    dependency: {
      simulations: () => apiClient.get<any[]>('/api/v1/resiliency/dependency/simulations'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/dependency/simulations', data),
      run: (id: string) => apiClient.post<any>(`/api/v1/resiliency/dependency/simulations/${id}/run`),
      results: () => apiClient.get<any[]>('/api/v1/resiliency/dependency/results'),
      failureTypes: () => apiClient.get<any[]>('/api/v1/resiliency/dependency/failure-types'),
    },
    runbooks: {
      list: () => apiClient.get<any[]>('/api/v1/resiliency/runbooks'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/runbooks', data),
      execute: (id: string) => apiClient.post<any>(`/api/v1/resiliency/runbooks/${id}/execute`, {}),
      executions: () => apiClient.get<any[]>('/api/v1/resiliency/runbooks/executions'),
      stepTypes: () => apiClient.get<any[]>('/api/v1/resiliency/runbooks/step-types'),
    },
    dataIntegrity: {
      verifications: () => apiClient.get<any[]>('/api/v1/resiliency/data-integrity/verifications'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/data-integrity/verifications', data),
      run: (id: string) => apiClient.post<any>(`/api/v1/resiliency/data-integrity/verifications/${id}/run`),
      summary: () => apiClient.get<any>('/api/v1/resiliency/data-integrity/summary'),
    },
    pipelines: {
      list: () => apiClient.get<any[]>('/api/v1/resiliency/pipelines'),
      create: (data: any) => apiClient.post<any>('/api/v1/resiliency/pipelines', data),
      trigger: (id: string) => apiClient.post<any>(`/api/v1/resiliency/pipelines/${id}/trigger`, {}),
      runs: () => apiClient.get<any[]>('/api/v1/resiliency/pipelines/runs'),
      summary: () => apiClient.get<any>('/api/v1/resiliency/pipelines/summary'),
    },
    dashboard: {
      show: () => apiClient.get<any>('/api/v1/resiliency/bc-dashboard'),
      snapshots: () => apiClient.get<any[]>('/api/v1/resiliency/bc-dashboard/snapshots'),
      report: () => apiClient.get<any>('/api/v1/resiliency/bc-dashboard/executive-report'),
    },
  },

  // === v4 Compliance Automation & Audit 2.0 ===
  complianceV4: {
    continuous: {
      list: () => apiClient.get<any[]>('/api/v1/compliance-v4/continuous/frameworks'),
      assess: (framework: string) => apiClient.post<any>(`/api/v1/compliance-v4/continuous/assess/${framework}`, {}),
      assessAll: () => apiClient.post<any>('/api/v1/compliance-v4/continuous/assess-all', {}),
      posture: (framework: string) => apiClient.get<any>(`/api/v1/compliance-v4/continuous/posture/${framework}`),
      summary: () => apiClient.get<any>('/api/v1/compliance-v4/continuous/summary'),
      alerts: () => apiClient.get<any[]>('/api/v1/compliance-v4/continuous/alerts'),
      trend: (framework: string, days?: number) => apiClient.get<any[]>(`/api/v1/compliance-v4/continuous/trend/${framework}`, { days }),
      drift: (framework: string) => apiClient.get<any[]>(`/api/v1/compliance-v4/continuous/drift/${framework}`),
      compare: () => apiClient.get<any>('/api/v1/compliance-v4/continuous/compare'),
      report: (framework: string) => apiClient.get<any>(`/api/v1/compliance-v4/continuous/report/${framework}`),
      batch: (frameworks: string[]) => apiClient.post<any>('/api/v1/compliance-v4/continuous/batch', { frameworks }),
      schedule: (intervalMinutes: number) => apiClient.post<any>('/api/v1/compliance-v4/continuous/schedule', { interval_minutes: intervalMinutes }),
      remediation: (framework: string) => apiClient.get<any[]>(`/api/v1/compliance-v4/continuous/remediation/${framework}`),
    },
    evidence: {
      list: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/evidence', params),
      collect: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/evidence/collect', data),
      get: (id: string) => apiClient.get<any>(`/api/v1/compliance-v4/evidence/${id}`),
      autoCollect: (controlId: string, framework: string) => apiClient.post<any>(`/api/v1/compliance-v4/evidence/auto-collect/${controlId}`, { framework }),
      packages: () => apiClient.get<any[]>('/api/v1/compliance-v4/evidence/packages'),
      createPackage: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/evidence/packages', data),
      finalizePackage: (id: string) => apiClient.post<any>(`/api/v1/compliance-v4/evidence/packages/${id}/finalize`, {}),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/evidence/stats'),
      search: (query: string) => apiClient.get<any[]>(`/api/v1/compliance-v4/evidence/search`, { query }),
      batchCollect: (items: any[]) => apiClient.post<any>('/api/v1/compliance-v4/evidence/batch-collect', { items }),
      validate: (id: string) => apiClient.get<any>(`/api/v1/compliance-v4/evidence/${id}/validate`),
    },
    cac: {
      controls: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/cac/controls', params),
      create: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/cac/controls', data),
      evaluate: (controlId: string, input: any) => apiClient.post<any>(`/api/v1/compliance-v4/cac/evaluate/${controlId}`, { input_data: input }),
      status: (controlId: string, status: string) => apiClient.patch<any>(`/api/v1/compliance-v4/cac/controls/${controlId}/status`, { status }),
      test: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/cac/test', data),
      templates: () => apiClient.get<any[]>('/api/v1/compliance-v4/cac/templates'),
      bulkEvaluate: (inputs: any[]) => apiClient.post<any>('/api/v1/compliance-v4/cac/bulk-evaluate', { inputs }),
      version: (controlId: string, rego: string, label?: string) => apiClient.post<any>(`/api/v1/compliance-v4/cac/controls/${controlId}/version`, { rego_expression: rego, version_label: label }),
      dryRun: (rego: string, input: any) => apiClient.post<any>('/api/v1/compliance-v4/cac/dry-run', { rego_expression: rego, input_data: input }),
      gap: (framework: string) => apiClient.get<any>(`/api/v1/compliance-v4/cac/gap/${framework}`),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/cac/stats'),
    },
    attest: {
      reports: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/attest/reports', params),
      generate: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/attest/reports', data),
      get: (id: string) => apiClient.get<any>(`/api/v1/compliance-v4/attest/reports/${id}`),
      export: (id: string) => apiClient.post<any>(`/api/v1/compliance-v4/attest/reports/${id}/export`, {}),
      templates: () => apiClient.get<any[]>('/api/v1/compliance-v4/attest/templates'),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/attest/stats'),
      compare: (id1: string, id2: string) => apiClient.get<any>(`/api/v1/compliance-v4/attest/compare/${id1}/${id2}`),
      batch: (configs: any[]) => apiClient.post<any>('/api/v1/compliance-v4/attest/batch', { configs }),
      schedule: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/attest/schedule', data),
      verify: (id: string) => apiClient.get<any>(`/api/v1/compliance-v4/attest/reports/${id}/verify`),
      composite: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/attest/composite', data),
    },
    vcom: {
      vendors: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/vcom/vendors', params),
      register: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/vcom/vendors', data),
      get: (id: string) => apiClient.get<any>(`/api/v1/compliance-v4/vcom/vendors/${id}`),
      assessments: (vendorId: string) => apiClient.get<any[]>(`/api/v1/compliance-v4/vcom/vendors/${vendorId}/assessments`),
      createAssessment: (vendorId: string) => apiClient.post<any>(`/api/v1/compliance-v4/vcom/vendors/${vendorId}/assessments`, {}),
      submitAssessment: (id: string, answers: any) => apiClient.post<any>(`/api/v1/compliance-v4/vcom/assessments/${id}/submit`, { answers }),
      reviewAssessment: (id: string, reviewer: string) => apiClient.post<any>(`/api/v1/compliance-v4/vcom/assessments/${id}/review`, { reviewer }),
      riskSummary: () => apiClient.get<any>('/api/v1/compliance-v4/vcom/risk-summary'),
      scorecard: (vendorId: string) => apiClient.get<any>(`/api/v1/compliance-v4/vcom/scorecard/${vendorId}`),
      discover: (domains: string[]) => apiClient.post<any>('/api/v1/compliance-v4/vcom/discover', { domains }),
      bulkAssess: (vendorIds: string[]) => apiClient.post<any>('/api/v1/compliance-v4/vcom/bulk-assess', { vendor_ids: vendorIds }),
      migrateTier: (vendorId: string, tier: string, reason?: string) => apiClient.post<any>(`/api/v1/compliance-v4/vcom/vendors/${vendorId}/migrate-tier`, { tier, reason }),
    },
    regintel: {
      changes: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/regintel/changes', params),
      detect: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/regintel/changes', data),
      impact: (changeId: string) => apiClient.get<any>(`/api/v1/compliance-v4/regintel/changes/${changeId}/impact`),
      sources: () => apiClient.get<any[]>('/api/v1/compliance-v4/regintel/sources'),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/regintel/stats'),
      batchDetect: (changes: any[]) => apiClient.post<any>('/api/v1/compliance-v4/regintel/batch-detect', { changes }),
      calendar: (year?: number) => apiClient.get<any[]>('/api/v1/compliance-v4/regintel/calendar', { year }),
      matrix: () => apiClient.get<any>('/api/v1/compliance-v4/regintel/impact-matrix'),
      sourceHealth: () => apiClient.get<any[]>('/api/v1/compliance-v4/regintel/source-health'),
    },
    auditMgmt: {
      rights: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/audit-mgmt/rights', params),
      registerRight: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/audit-mgmt/rights', data),
      schedules: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/audit-mgmt/schedules', params),
      schedule: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/audit-mgmt/schedules', data),
      updateStatus: (id: string, status: string) => apiClient.patch<any>(`/api/v1/compliance-v4/audit-mgmt/schedules/${id}/status`, { status }),
      upcoming: (days?: number) => apiClient.get<any[]>('/api/v1/compliance-v4/audit-mgmt/upcoming', { days }),
      overdue: () => apiClient.get<any[]>('/api/v1/compliance-v4/audit-mgmt/overdue'),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/audit-mgmt/stats'),
      collectEvidence: (scheduleId: string) => apiClient.post<any>(`/api/v1/compliance-v4/audit-mgmt/schedules/${scheduleId}/evidence`, {}),
      generateReport: (scheduleId: string, notes?: string) => apiClient.post<any>(`/api/v1/compliance-v4/audit-mgmt/schedules/${scheduleId}/report`, { notes }),
      workflow: (scheduleId: string, action: string) => apiClient.post<any>(`/api/v1/compliance-v4/audit-mgmt/schedules/${scheduleId}/workflow`, { action }),
      portalStatus: (customerId: string) => apiClient.get<any>(`/api/v1/compliance-v4/audit-mgmt/portal/${customerId}`),
    },
    dres: {
      assets: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/dres/assets', params),
      register: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/dres/assets', data),
      checkFlow: (assetId: string, targetRegion: string, framework: string) => apiClient.post<any>(`/api/v1/compliance-v4/dres/check-flow`, { asset_id: assetId, target_region: targetRegion, framework }),
      approveFlow: (flowId: string, approvedBy: string) => apiClient.post<any>(`/api/v1/compliance-v4/dres/flows/${flowId}/approve`, { approved_by: approvedBy }),
      move: (assetId: string, targetRegion: string) => apiClient.post<any>(`/api/v1/compliance-v4/dres/assets/${assetId}/move`, { target_region: targetRegion }),
      flows: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/dres/flows', params),
      auditTrail: (assetId?: string) => apiClient.get<any[]>('/api/v1/compliance-v4/dres/audit-trail', { asset_id: assetId }),
      summary: () => apiClient.get<any>('/api/v1/compliance-v4/dres/summary'),
      complianceReport: (framework: string) => apiClient.get<any>(`/api/v1/compliance-v4/dres/compliance-report/${framework}`),
    },
    train: {
      modules: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/train/modules', params),
      assign: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/train/assign', data),
      start: (assignmentId: string) => apiClient.post<any>(`/api/v1/compliance-v4/train/assignments/${assignmentId}/start`, {}),
      submit: (assignmentId: string, answers: any) => apiClient.post<any>(`/api/v1/compliance-v4/train/assignments/${assignmentId}/submit`, { answers }),
      assignments: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/train/assignments', params),
      certifications: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/train/certifications', params),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/train/stats'),
    },
    auditor: {
      engagements: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/auditor/engagements', params),
      createEngagement: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/auditor/engagements', data),
      sessions: () => apiClient.get<any[]>('/api/v1/compliance-v4/auditor/sessions'),
      createSession: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/auditor/sessions', data),
      accessEvidence: (sessionId: string, evidenceId: string) => apiClient.post<any>(`/api/v1/compliance-v4/auditor/access`, { session_id: sessionId, evidence_id: evidenceId }),
      evidenceByControl: (controlId: string) => apiClient.get<any[]>(`/api/v1/compliance-v4/auditor/evidence/control/${controlId}`),
      controlMapping: (framework: string) => apiClient.get<any>(`/api/v1/compliance-v4/auditor/evidence/mapping/${framework}`),
      findings: (params?: any) => apiClient.get<any[]>('/api/v1/compliance-v4/auditor/findings', params),
      createFinding: (data: any) => apiClient.post<any>('/api/v1/compliance-v4/auditor/findings', data),
      updateFinding: (id: string, status: string, notes?: string) => apiClient.patch<any>(`/api/v1/compliance-v4/auditor/findings/${id}`, { status, notes }),
      stats: () => apiClient.get<any>('/api/v1/compliance-v4/auditor/stats'),
      completeEngagement: (id: string, reportUrl?: string) => apiClient.post<any>(`/api/v1/compliance-v4/auditor/engagements/${id}/complete`, { report_url: reportUrl }),
    },
  },

  finops: {
    commitment: {
      list: () => apiClient.get<any[]>('/api/finops/commitment/recommendations'),
      summary: () => apiClient.get<any>('/api/finops/commitment/summary'),
      implement: (id: string) => apiClient.post<any>(`/api/finops/commitment/recommendations/${id}/implement`),
      commitments: () => apiClient.get<any[]>('/api/finops/commitment/commitments'),
      analyze: () => apiClient.post<any>('/api/finops/commitment/analyze'),
      coverage: () => apiClient.get<any[]>('/api/finops/commitment/coverage-gaps'),
    },
    spot: {
      list: () => apiClient.get<any[]>('/api/finops/spot/fleets'),
      create: (data: any) => apiClient.post<any>('/api/finops/spot/fleets', data),
      get: (id: string) => apiClient.get<any>(`/api/finops/spot/fleets/${id}`),
      update: (id: string, data: any) => apiClient.patch<any>(`/api/finops/spot/fleets/${id}`, data),
      instances: (id: string) => apiClient.get<any[]>(`/api/finops/spot/fleets/${id}/instances`),
      savings: () => apiClient.get<any>('/api/finops/spot/savings'),
      launch: (id: string, data: any) => apiClient.post<any>(`/api/finops/spot/fleets/${id}/launch`, data),
      interrupt: (id: string) => apiClient.post<any>(`/api/finops/spot/instances/${id}/interrupt`),
    },
    unitEconomics: {
      metrics: (customerId?: string, dimension?: string) => apiClient.get<any[]>('/api/finops/unit-economics/metrics', { customerId, dimension }),
      record: (data: any) => apiClient.post<any>('/api/finops/unit-economics/metrics', data),
      targets: () => apiClient.get<any[]>('/api/finops/unit-economics/targets'),
      setTarget: (data: any) => apiClient.post<any>('/api/finops/unit-economics/targets', data),
      violations: () => apiClient.get<any[]>('/api/finops/unit-economics/violations'),
      overview: () => apiClient.get<any>('/api/finops/unit-economics/overview'),
    },
    anomaly: {
      list: (severity?: string) => apiClient.get<any[]>('/api/finops/anomaly/detections', { severity }),
      summary: () => apiClient.get<any>('/api/finops/anomaly/summary'),
      investigate: (id: string) => apiClient.post<any>(`/api/finops/anomaly/detections/${id}/investigate`),
      resolve: (id: string) => apiClient.post<any>(`/api/finops/anomaly/detections/${id}/resolve`),
      profiles: () => apiClient.get<any[]>('/api/finops/anomaly/profiles'),
      createProfile: (data: any) => apiClient.post<any>('/api/finops/anomaly/profiles', data),
      ingest: (data: any) => apiClient.post<any>('/api/finops/anomaly/ingest', data),
    },
    budget: {
      list: () => apiClient.get<any[]>('/api/finops/budget'),
      create: (data: any) => apiClient.post<any>('/api/finops/budget', data),
      get: (id: string) => apiClient.get<any>(`/api/finops/budget/${id}`),
      spend: (id: string, data: any) => apiClient.post<any>(`/api/finops/budget/${id}/spend`, data),
      forecast: (id: string) => apiClient.get<any>(`/api/finops/budget/${id}/forecast`),
      scenario: (id: string, data: any) => apiClient.post<any>(`/api/finops/budget/${id}/scenario`, data),
      summary: () => apiClient.get<any>('/api/finops/budget/summary'),
      variance: (id: string) => apiClient.get<any>(`/api/finops/budget/${id}/variance`),
    },
    rightsizing: {
      list: () => apiClient.get<any[]>('/api/finops/rightsizing/recommendations'),
      summary: () => apiClient.get<any>('/api/finops/rightsizing/summary'),
      approve: (id: string) => apiClient.post<any>(`/api/finops/rightsizing/recommendations/${id}/approve`),
      implement: (id: string) => apiClient.post<any>(`/api/finops/rightsizing/recommendations/${id}/implement`),
      dismiss: (id: string) => apiClient.post<any>(`/api/finops/rightsizing/recommendations/${id}/dismiss`),
      register: (data: any) => apiClient.post<any>('/api/finops/rightsizing/resources', data),
      analyze: (id: string) => apiClient.post<any>(`/api/finops/rightsizing/resources/${id}/analyze`),
    },
    waste: {
      list: (category?: string, severity?: string) => apiClient.get<any[]>('/api/finops/waste/findings', { category, severity }),
      summary: () => apiClient.get<any>('/api/finops/waste/summary'),
      scan: () => apiClient.post<any>('/api/finops/waste/scan'),
      approve: (id: string) => apiClient.post<any>(`/api/finops/waste/findings/${id}/approve`),
      cleanup: (id: string) => apiClient.post<any>(`/api/finops/waste/findings/${id}/cleanup`),
      dismiss: (id: string) => apiClient.post<any>(`/api/finops/waste/findings/${id}/dismiss`),
    },
    carbon: {
      list: () => apiClient.get<any[]>('/api/finops/carbon/recommendations'),
      assets: () => apiClient.get<any[]>('/api/finops/carbon/assets'),
      register: (data: any) => apiClient.post<any>('/api/finops/carbon/assets', data),
      sustainability: () => apiClient.get<any>('/api/finops/carbon/sustainability-budget'),
      footprint: (id: string) => apiClient.get<any>(`/api/finops/carbon/assets/${id}/footprint`),
      tradeoff: (id: string) => apiClient.get<any>(`/api/finops/carbon/assets/${id}/tradeoff`),
      intensity: (region: string) => apiClient.get<any>(`/api/finops/carbon/intensity/${region}`),
    },
    arbitrage: {
      workloads: () => apiClient.get<any[]>('/api/finops/arbitrage/workloads'),
      comparisons: () => apiClient.get<any[]>('/api/finops/arbitrage/comparisons'),
      savings: () => apiClient.get<any>('/api/finops/arbitrage/savings'),
      register: (data: any) => apiClient.post<any>('/api/finops/arbitrage/workloads', data),
      compare: (id: string) => apiClient.get<any>(`/api/finops/arbitrage/workloads/${id}/compare`),
      migrate: (id: string) => apiClient.post<any>(`/api/finops/arbitrage/workloads/${id}/migrate`),
    },
    reporting: {
      list: () => apiClient.get<any[]>('/api/finops/reports'),
      generate: (data: any) => apiClient.post<any>('/api/finops/reports/generate', data),
      summary: () => apiClient.get<any>('/api/finops/reports/summary'),
      get: (id: string) => apiClient.get<any>(`/api/finops/reports/${id}`),
      dashboard: (type: string) => apiClient.get<any>(`/api/finops/reports/dashboard/${type}`),
      allocations: (team?: string) => apiClient.get<any[]>('/api/finops/reports/allocations', { team }),
      createAllocation: (data: any) => apiClient.post<any>('/api/finops/reports/allocations', data),
    },
  },

  // === v4 SOC ===
  soc: {
    soar: {
      playbooks: () => apiClient.get<any[]>('/api/soc/soar/playbooks'),
      playbook: (id: string) => apiClient.get<any>(`/api/soc/soar/playbooks/${id}`),
      createPlaybook: (data: any) => apiClient.post<any>('/api/soc/soar/playbooks', data),
      updatePlaybook: (id: string, data: any) => apiClient.put<any>(`/api/soc/soar/playbooks/${id}`, data),
      deletePlaybook: (id: string) => apiClient.delete<void>(`/api/soc/soar/playbooks/${id}`),
      execute: (id: string) => apiClient.post<any>(`/api/soc/soar/playbooks/${id}/execute`),
      cases: () => apiClient.get<any[]>('/api/soc/soar/cases'),
      connectors: () => apiClient.get<any[]>('/api/soc/soar/connectors'),
    },
    threatIntel: {
      iocs: () => apiClient.get<any[]>('/api/soc/ti/iocs'),
      addIoc: (data: any) => apiClient.post<any>('/api/soc/ti/iocs', data),
      deleteIoc: (id: string) => apiClient.delete<void>(`/api/soc/ti/iocs/${id}`),
      feeds: () => apiClient.get<any[]>('/api/soc/ti/feeds'),
      addFeed: (data: any) => apiClient.post<any>('/api/soc/ti/feeds', data),
      enrich: (data: any) => apiClient.post<any>('/api/soc/ti/enrich', data),
    },
    sase: {
      policies: () => apiClient.get<any[]>('/api/soc/sase/policies'),
      createPolicy: (data: any) => apiClient.post<any>('/api/soc/sase/policies', data),
      updatePolicy: (id: string, data: any) => apiClient.put<any>(`/api/soc/sase/policies/${id}`, data),
      deletePolicy: (id: string) => apiClient.delete<void>(`/api/soc/sase/policies/${id}`),
      branches: () => apiClient.get<any[]>('/api/soc/sase/branches'),
      ztnaApps: () => apiClient.get<any[]>('/api/soc/sase/ztna/apps'),
    },
    siem: {
      sources: () => apiClient.get<any[]>('/api/soc/siem/sources'),
      alerts: () => apiClient.get<any[]>('/api/soc/siem/alerts'),
      createRule: (data: any) => apiClient.post<any>('/api/soc/siem/rules', data),
      updateRule: (id: string, data: any) => apiClient.put<any>(`/api/soc/siem/rules/${id}`, data),
      deleteRule: (id: string) => apiClient.delete<void>(`/api/soc/siem/rules/${id}`),
      search: (query: string) => apiClient.post<any>('/api/soc/siem/search', { query }),
    },
    vulnerability: {
      findings: () => apiClient.get<any[]>('/api/soc/vuln/findings'),
      updateFinding: (id: string, data: any) => apiClient.put<any>(`/api/soc/vuln/findings/${id}`, data),
      scans: () => apiClient.get<any[]>('/api/soc/vuln/scans'),
      createScan: (data: any) => apiClient.post<any>('/api/soc/vuln/scans', data),
      runScan: (id: string) => apiClient.post<any>(`/api/soc/vuln/scans/${id}/run`),
      patches: () => apiClient.get<any[]>('/api/soc/vuln/patches'),
    },
    endpoint: {
      devices: () => apiClient.get<any[]>('/api/soc/endpoint/devices'),
      policies: () => apiClient.get<any[]>('/api/soc/endpoint/policies'),
      createPolicy: (data: any) => apiClient.post<any>('/api/soc/endpoint/policies', data),
      alerts: () => apiClient.get<any[]>('/api/soc/endpoint/alerts'),
      scanDevice: (id: string) => apiClient.post<any>(`/api/soc/endpoint/devices/${id}/scan`),
    },
    cloudSecurity: {
      cspm: () => apiClient.get<any[]>('/api/soc/cloud/cspm'),
      workloads: () => apiClient.get<any[]>('/api/soc/cloud/workloads'),
      scan: (data: any) => apiClient.post<any>('/api/soc/cloud/scan', data),
      iamRoles: () => apiClient.get<any[]>('/api/soc/cloud/iam/roles'),
    },
    iam: {
      users: () => apiClient.get<any[]>('/api/soc/iam/users'),
      createUser: (data: any) => apiClient.post<any>('/api/soc/iam/users', data),
      updateUser: (id: string, data: any) => apiClient.put<any>(`/api/soc/iam/users/${id}`, data),
      deleteUser: (id: string) => apiClient.delete<void>(`/api/soc/iam/users/${id}`),
      roles: () => apiClient.get<any[]>('/api/soc/iam/roles'),
      accessReviews: () => apiClient.get<any[]>('/api/soc/iam/access-reviews'),
      audit: () => apiClient.get<any[]>('/api/soc/iam/audit'),
    },
    compliance: {
      frameworks: () => apiClient.get<any[]>('/api/soc/compliance/frameworks'),
      controls: () => apiClient.get<any[]>('/api/soc/compliance/controls'),
      updateControl: (id: string, data: any) => apiClient.put<any>(`/api/soc/compliance/controls/${id}`, data),
      audits: () => apiClient.get<any[]>('/api/soc/compliance/audits'),
      remediations: () => apiClient.get<any[]>('/api/soc/compliance/remediations'),
    },
    analytics: {
      dashboards: () => apiClient.get<any[]>('/api/soc/analytics/dashboards'),
      createDashboard: (data: any) => apiClient.post<any>('/api/soc/analytics/dashboards', data),
      reports: () => apiClient.get<any[]>('/api/soc/analytics/reports'),
      generateReport: (data: any) => apiClient.post<any>('/api/soc/analytics/reports/generate', data),
      anomalies: () => apiClient.get<any[]>('/api/soc/analytics/anomalies'),
      metrics: () => apiClient.get<any[]>('/api/soc/analytics/metrics'),
    },
  },

  hybridCloud: {
    resources: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/resources'),
      get: (id: string) => apiClient.get<any>(`/api/v1/hybrid-cloud/resources/$`),
      create: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/resources', data),
      delete: (id: string) => apiClient.delete<void>(`/api/v1/hybrid-cloud/resources/$`),
    },
    bursting: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/bursting'),
      trigger: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/bursting', data),
    },
    arbitrage: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/arbitrage'),
      execute: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/arbitrage/execute', data),
    },
    costControl: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/cost-control'),
      summary: () => apiClient.get<any>('/api/v1/hybrid-cloud/cost-control/summary'),
    },
    networking: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/networking'),
      create: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/networking', data),
    },
    migration: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/migration'),
      start: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/migration', data),
    },
    iam: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/iam'),
      create: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/iam', data),
    },
    backup: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/backup'),
      create: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/backup', data),
    },
    registry: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/registry'),
      replicate: (data: any) => apiClient.post<any>('/api/v1/hybrid-cloud/registry/replicate', data),
    },
    costAllocation: {
      list: () => apiClient.get<any[]>('/api/v1/hybrid-cloud/cost-allocation'),
      summary: () => apiClient.get<any>('/api/v1/hybrid-cloud/cost-allocation/summary'),
    },
  },

  platformEngineering: {
    developerPortal: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/developer-portal'),
      register: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/developer-portal', data),
    },
    scaffold: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/scaffold'),
      generate: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/scaffold/generate', data),
    },
    serviceCatalog: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/service-catalog'),
      register: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/service-catalog', data),
    },
    scorecards: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/scorecards'),
      create: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/scorecards', data),
    },
    templateRegistry: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/template-registry'),
      create: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/template-registry', data),
    },
    techDebt: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/tech-debt'),
      report: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/tech-debt', data),
    },
    environments: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/environments'),
      create: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/environments', data),
    },
    apiCatalog: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/api-catalog'),
      register: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/api-catalog', data),
    },
    docGenerator: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/doc-generator'),
      generate: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/doc-generator', data),
    },
    developerPulse: {
      list: () => apiClient.get<any[]>('/api/v1/platform-engineering/developer-pulse'),
      create: (data: any) => apiClient.post<any>('/api/v1/platform-engineering/developer-pulse', data),
    },
  },

  dataPlatform: {
    lakehouse: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/lakehouse'),
      create: (data: any) => apiClient.post<any>('/api/v1/data-platform/lakehouse', data),
    },
    streaming: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/streaming'),
      create: (data: any) => apiClient.post<any>('/api/v1/data-platform/streaming', data),
    },
    quality: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/quality'),
      run: (data: any) => apiClient.post<any>('/api/v1/data-platform/quality/run', data),
    },
    analytics: {
      query: (query: string) => apiClient.post<any>('/api/v1/data-platform/analytics/query', { query }),
      workbench: () => apiClient.get<any[]>('/api/v1/data-platform/analytics/workbench'),
    },
    catalog: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/catalog'),
      register: (data: any) => apiClient.post<any>('/api/v1/data-platform/catalog', data),
    },
    dataMasking: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/data-masking'),
      apply: (data: any) => apiClient.post<any>('/api/v1/data-platform/data-masking', data),
    },
    selfService: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/self-service'),
      create: (data: any) => apiClient.post<any>('/api/v1/data-platform/self-service', data),
    },
    realtime: {
      dashboard: () => apiClient.get<any>('/api/v1/data-platform/realtime/dashboard'),
      metrics: () => apiClient.get<any[]>('/api/v1/data-platform/realtime/metrics'),
    },
    observability: {
      list: () => apiClient.get<any[]>('/api/v1/data-platform/observability'),
      alerts: () => apiClient.get<any[]>('/api/v1/data-platform/observability/alerts'),
    },
    embeddedAnalytics: {
      dashboards: () => apiClient.get<any[]>('/api/v1/data-platform/embedded-analytics'),
      create: (data: any) => apiClient.post<any>('/api/v1/data-platform/embedded-analytics', data),
    },
  },

  aiops: {
    rca: {
      analyze: (data: any) => apiClient.post<any>('/api/v1/aiops/rca/analyze', data),
      incidents: () => apiClient.get<any[]>('/api/v1/aiops/rca/incidents'),
      events: () => apiClient.get<any[]>('/api/v1/aiops/rca/events'),
    },
    remediation: {
      suggest: (data: any) => apiClient.post<any>('/api/v1/aiops/remediation/suggest', data),
      list: () => apiClient.get<any[]>('/api/v1/aiops/remediation'),
      approve: (id: string) => apiClient.post<any>(`/api/v1/aiops/remediation/approve`, { id }),
    },
    dem: {
      list: () => apiClient.get<any[]>('/api/v1/aiops/dem'),
      create: (data: any) => apiClient.post<any>('/api/v1/aiops/dem', data),
      check: (id: string) => apiClient.post<any>(`/api/v1/aiops/dem/check`, { id }),
    },
    alerts: {
      ingest: (data: any) => apiClient.post<any>('/api/v1/aiops/alerts/ingest', data),
      incidents: () => apiClient.get<any[]>('/api/v1/aiops/alerts/incidents'),
    },
    scaling: {
      predict: (id: string) => apiClient.get<any>(`/api/v1/aiops/scaling/predict`, { id }),
      policy: (data: any) => apiClient.post<any>('/api/v1/aiops/scaling/policy', data),
    },
    healthForecast: {
      services: () => apiClient.get<any[]>('/api/v1/aiops/health'),
      forecast: () => apiClient.get<any>('/api/v1/aiops/health/forecast'),
    },
    opsAssistant: {
      message: (msg: string) => apiClient.post<any>('/api/v1/aiops/assistant/message', { message: msg }),
      stats: () => apiClient.get<any>('/api/v1/aiops/assistant/stats'),
    },
    changeRisk: {
      analyze: (data: any) => apiClient.post<any>('/api/v1/aiops/change-risk/analyze', data),
      approve: (id: string) => apiClient.post<any>(`/api/v1/aiops/change-risk/approve`, { id }),
    },
    capacityPlanning: {
      recommend: () => apiClient.get<any>('/api/v1/aiops/capacity/recommend'),
      simulate: (data: any) => apiClient.post<any>('/api/v1/aiops/capacity/simulate', data),
    },
    opsChatbot: {
      message: (msg: string) => apiClient.post<any>('/api/v1/aiops/chatbot', { message: msg }),
      history: () => apiClient.get<any[]>('/api/v1/aiops/chatbot/history'),
    },
  },

  emergingTech: {
    blockchain: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/blockchain/networks'),
      create: (data: any) => apiClient.post<any>('/api/v1/emerging-tech/blockchain/networks', data),
      status: (id: string) => apiClient.get<any>(`/api/v1/emerging-tech/blockchain/networks/$`),
    },
    storage: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/storage/gateways'),
      create: (data: any) => apiClient.post<any>('/api/v1/emerging-tech/storage/gateways', data),
      pin: (cid: string) => apiClient.post<any>('/api/v1/emerging-tech/storage/pin', { cid }),
    },
    quantum: {
      keys: () => apiClient.get<any[]>('/api/v1/emerging-tech/quantum/keys'),
      generate: (algorithm: string) => apiClient.post<any>('/api/v1/emerging-tech/quantum/generate', { algorithm }),
      encrypt: (keyId: string, message: string) => apiClient.post<any>('/api/v1/emerging-tech/quantum/encrypt', { keyId, message }),
    },
    contracts: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/contracts'),
      deploy: (data: any) => apiClient.post<any>('/api/v1/emerging-tech/contracts', data),
      events: (id: string) => apiClient.get<any[]>(`/api/v1/emerging-tech/contracts/events`),
    },
    web3id: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/web3id/identities'),
      create: (did: string) => apiClient.post<any>('/api/v1/emerging-tech/web3id/create', { did }),
      auth: (id: string) => apiClient.post<any>(`/api/v1/emerging-tech/web3id/auth`, { id }),
    },
    confidential: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/confidential/enclaves'),
      create: (data: any) => apiClient.post<any>('/api/v1/emerging-tech/confidential/enclaves', data),
      attest: (id: string) => apiClient.post<any>(`/api/v1/emerging-tech/confidential/attest`, { id }),
    },
    federated: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/federated/projects'),
      create: (data: any) => apiClient.post<any>('/api/v1/emerging-tech/federated/projects', data),
      rounds: (id: string) => apiClient.get<any[]>(`/api/v1/emerging-tech/federated/rounds`),
    },
    zkp: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/zkp/proofs'),
      generate: (statement: string, witness: string) => apiClient.post<any>('/api/v1/emerging-tech/zkp/generate', { statement, witness }),
      verify: (id: string) => apiClient.post<any>(`/api/v1/emerging-tech/zkp/verify`, { id }),
    },
    dcn: {
      list: () => apiClient.get<any[]>('/api/v1/emerging-tech/dcn/tasks'),
      submit: (data: any) => apiClient.post<any>('/api/v1/emerging-tech/dcn/tasks', data),
      workers: () => apiClient.get<any[]>('/api/v1/emerging-tech/dcn/workers'),
    },
    aiops: {
      alertCorrelation: {
        correlate: (windowMinutes: number) => apiClient.post('/api/v1/aiops/alert-correlation/correlate', { windowMinutes }),
        sources: () => apiClient.get<any[]>('/api/v1/aiops/alert-correlation/sources'),
        suppress: (windowMinutes: number) => apiClient.post('/api/v1/aiops/alert-correlation/suppress', { windowMinutes }),
        stats: () => apiClient.get<any>('/api/v1/aiops/alert-correlation/stats'),
      },
      rca: {
        analyze: (incidentId: string) => apiClient.post<any>(`/api/v1/aiops/rca/analyze/${incidentId}`),
        impact: (eventId: string) => apiClient.get<any>(`/api/v1/aiops/rca/impact/${eventId}`),
        timeline: (hours: number) => apiClient.get<any[]>('/api/v1/aiops/rca/timeline', { params: { hours } }),
        patterns: () => apiClient.get<any[]>('/api/v1/aiops/rca/patterns'),
      },
      capacity: {
        recommendations: () => apiClient.get<any[]>('/api/v1/aiops/capacity/recommendations'),
        simulate: (scenario: string, peakPct: number) => apiClient.post('/api/v1/aiops/capacity/simulate', { scenario, peakPct }),
        forecast: () => apiClient.get<any>('/api/v1/aiops/capacity/forecast'),
        alerts: () => apiClient.get<any[]>('/api/v1/aiops/capacity/alerts'),
      },
      changeRisk: {
        analyze: (changeId: string) => apiClient.post<any>(`/api/v1/aiops/change-risk/analyze`, { changeId }),
        trend: (days: number) => apiClient.get<any[]>('/api/v1/aiops/change-risk/trend', { params: { days } }),
        ranking: () => apiClient.get<any[]>('/api/v1/aiops/change-risk/ranking'),
      },
      conversational: {
        sloHealth: () => apiClient.get<any>('/api/v1/aiops/conversational/slo-health'),
        feedback: (days: number) => apiClient.get<any>('/api/v1/aiops/conversational/feedback', { params: { days } }),
        popularCommands: () => apiClient.get<any[]>('/api/v1/aiops/conversational/popular-commands'),
      },
      digitalExperience: {
        monitors: () => apiClient.get<any[]>('/api/v1/aiops/digital-experience/monitors'),
        regression: (days: number) => apiClient.get<any[]>('/api/v1/aiops/digital-experience/regression', { params: { days } }),
        health: () => apiClient.get<any>('/api/v1/aiops/digital-experience/health'),
      },
      healthForecasting: {
        forecast: (hours: number) => apiClient.get<any>('/api/v1/aiops/health-forecasting/forecast', { params: { hours } }),
        alerts: (days: number) => apiClient.get<any[]>('/api/v1/aiops/health-forecasting/alerts', { params: { days } }),
        accuracy: (weeks: number) => apiClient.get<any>('/api/v1/aiops/health-forecasting/accuracy', { params: { weeks } }),
      },
      incidentRemediation: {
        remediate: (incidentId: string, action: string) => apiClient.post('/api/v1/aiops/incident-remediation/remediate', { incidentId, action }),
        analytics: (days: number) => apiClient.get<any>('/api/v1/aiops/incident-remediation/analytics', { params: { days } }),
        mttr: () => apiClient.get<any>('/api/v1/aiops/incident-remediation/mttr'),
      },
      opsChatbot: {
        chat: (message: string) => apiClient.post('/api/v1/aiops/ops-chatbot/chat', { message }),
        tasks: () => apiClient.get<any[]>('/api/v1/aiops/ops-chatbot/tasks'),
        priorities: () => apiClient.get<any[]>('/api/v1/aiops/ops-chatbot/priorities'),
      },
      predictiveScaling: {
        forecast: (resourceId: string, metric: string) => apiClient.get<any>('/api/v1/aiops/predictive-scaling/forecast', { params: { resourceId, metric } }),
        alerts: () => apiClient.get<any[]>('/api/v1/aiops/predictive-scaling/alerts'),
        recommendations: () => apiClient.get<any[]>('/api/v1/aiops/predictive-scaling/recommendations'),
      },
    },
  },
};
