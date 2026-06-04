import { apiClient } from '../client';

export const platformEngineeringEndpoints = {
  // Developer Portal (feature 11)
  portal: {
    listComponents: (domain?: string) =>
      apiClient.get<any[]>('/api/v4/platform-engineering/portal/components', { domain }),
    registerComponent: (name: string, domain: string, description?: string, owner?: string) =>
      apiClient.post<any>('/api/v4/platform-engineering/portal/components', { name, domain, description, owner }),
    getComponent: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/portal/components/${id}`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/portal/summary'),
  },

  // Golden Path Scaffolder (feature 12)
  scaffold: {
    listTemplates: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/scaffold/templates'),
    generate: (templateId: string, projectName: string, params?: any) =>
      apiClient.post<any>(`/api/v4/platform-engineering/scaffold/templates/${templateId}/generate`, { project_name: projectName, params }),
    status: (generationId: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/scaffold/generations/${generationId}`),
    completeStep: (generationId: string, stepName: string, outputs?: any) =>
      apiClient.post<any>(`/api/v4/platform-engineering/scaffold/generations/${generationId}/steps/${stepName}/complete`, { outputs }),
  },

  // Service Catalog (feature 13)
  catalog: {
    listServices: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/catalog/services'),
    registerService: (name: string, domain: string, description?: string, owner?: string) =>
      apiClient.post<any>('/api/v4/platform-engineering/catalog/services', { name, domain, description, owner }),
    getService: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/catalog/services/${id}`),
    scoreService: (id: string) =>
      apiClient.post<any>(`/api/v4/platform-engineering/catalog/services/${id}/score`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/catalog/summary'),
  },

  // Scorecards & DORA Metrics (feature 14)
  scorecards: {
    list: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/scorecards'),
    create: (name: string, team: string, includeDora?: boolean) =>
      apiClient.post<any>('/api/v4/platform-engineering/scorecards', { name, team, include_dora: includeDora }),
    get: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/scorecards/${id}`),
    updateMetric: (id: string, metric: string, value: string) =>
      apiClient.patch<any>(`/api/v4/platform-engineering/scorecards/${id}/metrics/${metric}`, { value }),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/scorecards/summary'),
  },

  // Template Registry (feature 15)
  templateRegistry: {
    list: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/templates'),
    create: (name: string, category: string, paramsSchema?: any) =>
      apiClient.post<any>('/api/v4/platform-engineering/templates', { name, category, params_schema: paramsSchema }),
    get: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/templates/${id}`),
    use: (id: string) =>
      apiClient.post<any>(`/api/v4/platform-engineering/templates/${id}/use`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/templates/summary'),
  },

  // Tech Debt Tracker (feature 16)
  techDebt: {
    list: (severity?: string) =>
      apiClient.get<any[]>('/api/v4/platform-engineering/tech-debt', { severity }),
    report: (title: string, severity: string, effortHours: number, area?: string) =>
      apiClient.post<any>('/api/v4/platform-engineering/tech-debt', { title, severity, effort_hours: effortHours, area }),
    get: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/tech-debt/${id}`),
    fix: (id: string) =>
      apiClient.post<any>(`/api/v4/platform-engineering/tech-debt/${id}/fix`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/tech-debt/summary'),
  },

  // Environment Orchestrator (feature 17)
  environments: {
    list: (status?: string) =>
      apiClient.get<any[]>('/api/v4/platform-engineering/environments', { status }),
    create: (name: string, template: string, ttl?: number, branch?: string) =>
      apiClient.post<any>('/api/v4/platform-engineering/environments', { name, template, ttl_hours: ttl, branch }),
    get: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/environments/${id}`),
    delete: (id: string) =>
      apiClient.delete<void>(`/api/v4/platform-engineering/environments/${id}`),
    extend: (id: string, hours: number) =>
      apiClient.post<any>(`/api/v4/platform-engineering/environments/${id}/extend`, { additional_hours: hours }),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/environments/summary'),
  },

  // API Catalog (feature 18)
  apiCatalog: {
    list: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/api-catalog'),
    register: (name: string, version: string, spec: string) =>
      apiClient.post<any>('/api/v4/platform-engineering/api-catalog', { name, version, spec }),
    get: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/api-catalog/${id}`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/api-catalog/summary'),
  },

  // Doc Generator (feature 19)
  docGenerator: {
    list: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/docs'),
    generate: (title: string, docType: string) =>
      apiClient.post<any>('/api/v4/platform-engineering/docs', { title, doc_type: docType }),
    get: (id: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/docs/${id}`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/docs/summary'),
  },

  // Developer Pulse (feature 20)
  developerPulse: {
    listSurveys: () =>
      apiClient.get<any[]>('/api/v4/platform-engineering/pulse/surveys'),
    createSurvey: (title: string, questions: any[]) =>
      apiClient.post<any>('/api/v4/platform-engineering/pulse/surveys', { title, questions }),
    respond: (surveyId: string, respondent: string, answers: any) =>
      apiClient.post<any>(`/api/v4/platform-engineering/pulse/surveys/${surveyId}/respond`, { respondent, answers }),
    results: (surveyId: string) =>
      apiClient.get<any>(`/api/v4/platform-engineering/pulse/surveys/${surveyId}/results`),
    summary: () =>
      apiClient.get<any>('/api/v4/platform-engineering/pulse/summary'),
  },
};
