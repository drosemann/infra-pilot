import crypto from 'crypto';

export interface ChangeRequestEntry {
  id: string;
  userId: string;
  userName: string;
  appId: string;
  action: string;
  reason: string;
  details: string;
  status: 'pending' | 'approved' | 'rejected' | 'emergency';
  reviewerId?: string;
  reviewerName?: string;
  rejectReason?: string;
  createdAt: string;
  reviewedAt?: string;
  expiresAt: string;
  isBreakGlass: boolean;
}

const DEFAULT_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const BREAK_GLASS_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

// Destructive action patterns requiring approval
const DESTRUCTIVE_ACTIONS = [
  'delete', 'destroy', 'remove', 'stop', 'restart', 'reboot',
  'reset', 'wipe', 'purge', 'drop', 'truncate',
  'shutdown', 'terminate', 'rm', 'kill',
];

const DESTRUCTIVE_PATTERNS = [
  /delete/i, /drop\s+table/i, /truncate/i, /rm\s+-rf/i,
  /destroy/i, /shutdown/i, /format/i, /wipe/i,
  /purge/i, /terminate/i, /stop\s+--force/i,
];

interface PolicyResult {
  requiresApproval: boolean;
  reason?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  autoApprovalPossible: boolean;
}

export function evaluatePolicy(action: string, details: string, appId: string): PolicyResult {
  const combined = `${action} ${details}`;

  // Check for critical destructive patterns
  for (const pattern of DESTRUCTIVE_PATTERNS) {
    if (pattern.test(combined)) {
      return {
        requiresApproval: true,
        reason: `Action matches destructive pattern: "${pattern.source}"`,
        severity: 'critical',
        autoApprovalPossible: false,
      };
    }
  }

  // Check for known destructive actions
  const actionLower = action.toLowerCase();
  for (const destructive of DESTRUCTIVE_ACTIONS) {
    if (actionLower.includes(destructive)) {
      return {
        requiresApproval: true,
        reason: `Action "${action}" is classified as destructive`,
        severity: 'high',
        autoApprovalPossible: false,
      };
    }
  }

  // Production apps (by naming convention) always require approval
  if (appId.includes('prod') || appId.includes('production') || appId.includes('live')) {
    return {
      requiresApproval: true,
      reason: 'Production apps require change approval',
      severity: 'high',
      autoApprovalPossible: true,
    };
  }

  // Default: non-destructive actions on non-production pass through
  return {
    requiresApproval: false,
    severity: 'low',
    autoApprovalPossible: true,
  };
}

// In-memory store for change requests
const changeRequests: Map<string, ChangeRequestEntry> = new Map();

export function createChangeRequest(
  userId: string,
  userName: string,
  appId: string,
  action: string,
  reason: string,
  details: string,
  isBreakGlass: boolean = false,
): ChangeRequestEntry {
  const policy = evaluatePolicy(action, details, appId);
  const timeoutMs = isBreakGlass ? BREAK_GLASS_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;

  const request: ChangeRequestEntry = {
    id: crypto.randomUUID(),
    userId,
    userName,
    appId,
    action,
    reason,
    details,
    status: isBreakGlass ? 'emergency' : 'pending',
    createdAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + timeoutMs).toISOString(),
    isBreakGlass,
  };

  changeRequests.set(request.id, request);
  return request;
}

export function listChangeRequests(filter?: { status?: string; userId?: string; appId?: string }): ChangeRequestEntry[] {
  let requests = Array.from(changeRequests.values());

  // Remove expired requests
  const now = Date.now();
  requests = requests.filter(r => new Date(r.expiresAt).getTime() > now);

  if (filter?.status) {
    requests = requests.filter(r => r.status === filter.status);
  }
  if (filter?.userId) {
    requests = requests.filter(r => r.userId === filter.userId);
  }
  if (filter?.appId) {
    requests = requests.filter(r => r.appId === filter.appId);
  }

  return requests.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
}

export function getChangeRequest(id: string): ChangeRequestEntry | undefined {
  return changeRequests.get(id);
}

export function approveChangeRequest(id: string, reviewerId: string, reviewerName: string): ChangeRequestEntry | null {
  const request = changeRequests.get(id);
  if (!request) return null;
  if (request.status !== 'pending') return null;

  request.status = 'approved';
  request.reviewerId = reviewerId;
  request.reviewerName = reviewerName;
  request.reviewedAt = new Date().toISOString();
  return request;
}

export function rejectChangeRequest(id: string, reviewerId: string, reviewerName: string, reason: string): ChangeRequestEntry | null {
  const request = changeRequests.get(id);
  if (!request) return null;
  if (request.status !== 'pending') return null;

  request.status = 'rejected';
  request.reviewerId = reviewerId;
  request.reviewerName = reviewerName;
  request.rejectReason = reason;
  request.reviewedAt = new Date().toISOString();
  return request;
}

export function clearExpiredRequests(): void {
  const now = Date.now();
  for (const [id, request] of changeRequests) {
    if (new Date(request.expiresAt).getTime() < now) {
      changeRequests.delete(id);
    }
  }
}

export function clearAllRequests(): void {
  changeRequests.clear();
}
