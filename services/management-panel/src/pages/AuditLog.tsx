import { useEffect, useState } from 'react';

interface AuditEntry {
  id: string;
  timestamp: string;
  action: string;
  entity_type: string;
  entity: string;
  user: string;
}

export function AuditLog() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' });
      if (actionFilter) params.set('action', actionFilter);
      if (entityFilter) params.set('entity_type', entityFilter);
      if (dateFrom) params.set('from', dateFrom);
      if (dateTo) params.set('to', dateTo);
      const res = await fetch(`/api/audit-log?${params}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
        setTotalPages(data.total_pages || 1);
      }
    } catch (e) {
      console.error('Failed to fetch audit log', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEntries(); }, [page]);

  const handleFilter = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEntries();
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight text-white">Activity</h1>
          <p className="mt-2 text-white/55">Every administrative action, in order.</p>
        </div>
      </div>

      <form onSubmit={handleFilter} className="card flex flex-wrap gap-4 p-4">
        <div>
          <label className="mb-1 block text-xs text-white/45">Action</label>
          <select value={actionFilter} onChange={e => setActionFilter(e.target.value)} className="input-field w-auto text-sm">
            <option value="">All</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="login">Login</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-white/45">Entity Type</label>
          <select value={entityFilter} onChange={e => setEntityFilter(e.target.value)} className="input-field w-auto text-sm">
            <option value="">All</option>
            <option value="app">App</option>
            <option value="backup">Backup</option>
            <option value="user">User</option>
            <option value="setting">Setting</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-white/45">From</label>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input-field w-auto text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs text-white/45">To</label>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input-field w-auto text-sm" />
        </div>
        <div className="flex items-end gap-2">
          <button type="submit" className="primary-button">Apply</button>
          <button type="button" onClick={() => { setActionFilter(''); setEntityFilter(''); setDateFrom(''); setDateTo(''); setPage(1); fetchEntries(); }} className="secondary-button">Clear</button>
        </div>
      </form>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="px-4 py-3 text-left font-medium text-white/45">Timestamp</th>
              <th className="px-4 py-3 text-left font-medium text-white/45">Action</th>
              <th className="px-4 py-3 text-left font-medium text-white/45">Entity Type</th>
              <th className="px-4 py-3 text-left font-medium text-white/45">Entity</th>
              <th className="px-4 py-3 text-left font-medium text-white/45">User</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="py-8 text-center text-white/45">Loading...</td></tr>
            ) : entries.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-white/45">No audit entries found</td></tr>
            ) : entries.map(entry => (
              <tr key={entry.id} className="border-b border-white/5">
                <td className="px-4 py-3 text-white/60">{new Date(entry.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3"><span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/70">{entry.action}</span></td>
                <td className="px-4 py-3 text-white/60">{entry.entity_type}</td>
                <td className="px-4 py-3 font-medium text-white">{entry.entity}</td>
                <td className="px-4 py-3 text-white/60">{entry.user}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="secondary-button">Previous</button>
          <span className="text-sm text-white/45">Page {page} of {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="secondary-button">Next</button>
        </div>
      )}
    </div>
  );
}

export default AuditLog;
