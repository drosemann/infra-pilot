import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api.ts';
import { useRbac } from '../hooks/useRbac.ts';
import type { InstanceRoleAssignment } from '../lib/types.ts';

const ROLE_OPTIONS: Array<'admin' | 'operator' | 'viewer'> = ['admin', 'operator', 'viewer'];

/**
 * Instance-level roles page. Lists every instance role assignment and lets
 * instance admins grant, change, or revoke them. The backend keeps being the
 * source of truth — 403 responses simply surface as errors.
 */
export function RolesManagement() {
  const { isAdmin, loading: rbacLoading } = useRbac();
  const [roles, setRoles] = useState<InstanceRoleAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newUserId, setNewUserId] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'operator' | 'viewer'>('operator');
  const [busy, setBusy] = useState(false);

  const fetchRoles = async () => {
    setLoading(true);
    setError(null);
    try {
      setRoles(await apiClient.getInstanceRoles());
    } catch (e: any) {
      setError(e?.response?.data?.error || 'Failed to load instance roles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserId.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.setInstanceRole(newUserId.trim(), newRole);
      setNewUserId('');
      await fetchRoles();
    } catch (e2: any) {
      setError(e2?.response?.data?.error || `HTTP ${e2?.response?.status || ''}`.trim() || 'Failed to grant role');
    } finally {
      setBusy(false);
    }
  };

  const handleChange = async (userId: string, role: 'admin' | 'operator' | 'viewer') => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.setInstanceRole(userId, role);
      await fetchRoles();
    } catch (e: any) {
      setError(e?.response?.data?.error || 'Failed to update role');
    } finally {
      setBusy(false);
    }
  };

  const handleRevoke = async (userId: string) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.deleteInstanceRole(userId);
      await fetchRoles();
    } catch (e: any) {
      setError(e?.response?.data?.error || 'Failed to revoke role');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-6 space-y-6" aria-labelledby="roles-heading">
      <div>
        <h1 id="roles-heading" className="text-2xl font-bold text-slate-100">Access Roles</h1>
        <p className="text-slate-400 mt-1">
          Instance-level roles. App owners and per-app assignments are managed on each app's
          Members page.
        </p>
      </div>

      {error && (
        <div role="alert" className="px-4 py-3 rounded bg-red-900/40 border border-red-700 text-red-200">
          {error}
        </div>
      )}

      {isAdmin && (
        <form onSubmit={handleGrant} className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label htmlFor="rbac-user-id" className="text-sm text-slate-300">User ID</label>
            <input
              id="rbac-user-id"
              value={newUserId}
              onChange={(e) => setNewUserId(e.target.value)}
              placeholder="Supabase user UUID"
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100 w-72"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="rbac-role" className="text-sm text-slate-300">Role</label>
            <select
              id="rbac-role"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as 'admin' | 'operator' | 'viewer')}
              className="px-3 py-2 rounded bg-slate-800 border border-slate-700 text-slate-100"
            >
              {ROLE_OPTIONS.map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={busy || !newUserId.trim()}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white"
          >
            Grant Role
          </button>
        </form>
      )}

      {loading || rbacLoading ? (
        <p className="text-slate-400">Loading...</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th scope="col" className="py-2 pr-4">User ID</th>
                <th scope="col" className="py-2 pr-4">Role</th>
                <th scope="col" className="py-2 pr-4">Updated</th>
                {isAdmin && <th scope="col" className="py-2">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {roles.map((assignment) => (
                <tr key={assignment.userId} className="border-b border-slate-800">
                  <td className="py-2 pr-4 font-mono text-slate-200">{assignment.userId}</td>
                  <td className="py-2 pr-4">
                    {isAdmin ? (
                      <select
                        aria-label={`Role for ${assignment.userId}`}
                        value={assignment.role}
                        onChange={(e) => handleChange(assignment.userId, e.target.value as 'admin' | 'operator' | 'viewer')}
                        disabled={busy}
                        className="px-2 py-1 rounded bg-slate-800 border border-slate-700 text-slate-100"
                      >
                        {ROLE_OPTIONS.map((role) => (
                          <option key={role} value={role}>{role}</option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-slate-200">{assignment.role}</span>
                    )}
                  </td>
                  <td className="py-2 pr-4 text-slate-400">
                    {assignment.updatedAt ? new Date(assignment.updatedAt).toLocaleString() : '—'}
                  </td>
                  {isAdmin && (
                    <td className="py-2">
                      <button
                        onClick={() => handleRevoke(assignment.userId)}
                        disabled={busy}
                        className="px-3 py-1 rounded bg-red-900/60 hover:bg-red-800 disabled:opacity-50 text-red-100"
                      >
                        Revoke
                      </button>
                    </td>
                  )}
                </tr>
              ))}
              {roles.length === 0 && (
                <tr>
                  <td colSpan={isAdmin ? 4 : 3} className="py-4 text-slate-400">
                    No instance roles assigned yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default RolesManagement;
