import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api.ts';
import type { RbacMe } from '../lib/types.ts';

export interface UseRbacState {
  /** Instance role of the current user, or null when unassigned/unloaded. */
  role: 'admin' | 'operator' | 'viewer' | null;
  loading: boolean;
  /** True when the user may administer instance settings (roles, templates init). */
  isAdmin: boolean;
}

/**
 * Fetch the current user's RBAC state (`GET /api/rbac/me`) once per mount.
 * The backend remains the source of truth: this hook only drives cosmetic
 * gating (nav visibility, disabled controls), never data access.
 */
export function useRbac(): UseRbacState {
  const [state, setState] = useState<UseRbacState>({
    role: null,
    loading: true,
    isAdmin: false,
  });

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getRbacMe()
      .then((me: RbacMe) => {
        if (cancelled) return;
        setState({ role: me.instanceRole, loading: false, isAdmin: me.instanceRole === 'admin' });
      })
      .catch(() => {
        // Fail closed cosmetically: no role, nothing elevated shown.
        if (!cancelled) setState({ role: null, loading: false, isAdmin: false });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
