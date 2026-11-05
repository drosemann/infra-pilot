import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { MaintenanceWindow, DockerApp } from '../lib/types';
import { toast } from 'sonner';

export const MaintenanceScheduler = () => {
  const [windows, setWindows] = useState<MaintenanceWindow[]>([]);
  const [apps, setApps] = useState<DockerApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    app_id: '',
    starts_at: '',
    ends_at: '',
  });

  useEffect(() => {
    Promise.all([loadWindows(), loadApps()]).finally(() => setLoading(false));
  }, []);

  const loadWindows = async () => {
    try {
      setWindows(await apiClient.getMaintenanceWindows());
    } catch {
      setWindows([]);
    }
  };

  const loadApps = async () => {
    try {
      setApps(await apiClient.listApps());
    } catch {
      setApps([]);
    }
  };

  const handleCreate = async () => {
    if (!form.title || !form.starts_at || !form.ends_at) {
      toast.error('Title, start and end times are required');
      return;
    }
    try {
      await apiClient.createMaintenanceWindow(form);
      toast.success('Maintenance window created');
      setShowForm(false);
      setForm({ title: '', description: '', app_id: '', starts_at: '', ends_at: '' });
      loadWindows();
    } catch {
      toast.error('Failed to create maintenance window');
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await apiClient.updateMaintenanceWindow(id, { status: 'cancelled' });
      toast.success('Maintenance window cancelled');
      loadWindows();
    } catch {
      toast.error('Failed to cancel maintenance window');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-500/10 text-blue-400';
      case 'active': return 'bg-green-500/10 text-green-400';
      case 'completed': return 'bg-white/5 text-white/50';
      case 'cancelled': return 'bg-red-500/10 text-red-400';
      default: return 'bg-white/5 text-white/50';
    }
  };

  if (loading) {
    return <div className="py-4 text-white/45">Loading maintenance windows…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-md font-semibold text-white">Maintenance Windows</h4>
        <button
          onClick={() => setShowForm(!showForm)}
          className="primary-button"
        >
          {showForm ? 'Cancel' : 'Schedule'}
        </button>
      </div>

      {showForm && (
        <div className="card space-y-3 p-4">
          <input
            type="text"
            placeholder="Window title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="input-field w-full text-sm"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="input-field w-full text-sm"
          />
          <select
            value={form.app_id}
            onChange={(e) => setForm({ ...form, app_id: e.target.value })}
            className="input-field w-full text-sm"
          >
            <option value="">All apps (global)</option>
            {apps.map((app) => (
              <option key={app.id} value={app.id}>{app.name}</option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs text-white/45">Start</label>
              <input
                type="datetime-local"
                value={form.starts_at}
                onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
                className="input-field w-full text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-white/45">End</label>
              <input
                type="datetime-local"
                value={form.ends_at}
                onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
                className="input-field w-full text-sm"
              />
            </div>
          </div>
          <button
            onClick={handleCreate}
            className="primary-button w-full"
          >
            Create Window
          </button>
        </div>
      )}

      <div className="space-y-2">
        {windows.length === 0 ? (
          <p className="text-sm text-white/45">No maintenance windows scheduled</p>
        ) : (
          windows.map((w) => (
            <div key={w.id} className="card flex items-center justify-between p-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">{w.title}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(w.status)}`}>
                    {w.status}
                  </span>
                </div>
                {w.description && (
                  <p className="mt-1 text-xs text-white/45">{w.description}</p>
                )}
                <p className="mt-1 text-xs text-white/40">
                  {new Date(w.starts_at).toLocaleString()} - {new Date(w.ends_at).toLocaleString()}
                </p>
              </div>
              {w.status === 'scheduled' && (
                <button
                  onClick={() => handleCancel(w.id)}
                  className="px-2 py-1 text-xs bg-red-600/20 text-red-400 hover:bg-red-600/40 rounded transition-colors"
                >
                  Cancel
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {windows.length > 0 && (
        <div className="card p-4">
          <p className="mb-3 text-sm text-white/45">Calendar View (Upcoming)</p>
          <div className="grid grid-cols-7 gap-1">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
              <div key={d} className="py-1 text-center text-xs text-white/35">{d}</div>
            ))}
            {Array.from({ length: 35 }, (_, i) => {
              const hasWindow = windows.some((w) => {
                const start = new Date(w.starts_at);
                const end = new Date(w.ends_at);
                const day = new Date();
                day.setDate(day.getDate() + (i - day.getDay() + 1));
                return start <= day && end >= day;
              });
              return (
                <div
                  key={i}
                  className={`text-center text-xs py-2 rounded ${
                    hasWindow ? 'bg-white text-black' : 'text-white/35'
                  }`}
                >
                  {new Date(new Date().getFullYear(), new Date().getMonth(), i - new Date().getDay() + 1).getDate()}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceScheduler;
