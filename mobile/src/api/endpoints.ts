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
};
