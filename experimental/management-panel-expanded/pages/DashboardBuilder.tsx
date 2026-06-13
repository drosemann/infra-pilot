import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Save, Share2, Trash2, Plus, Star } from 'lucide-react';
import { apiClient } from '../lib/api';
import type { DashboardDefinition, DashboardPanel } from '../lib/types';
import { Canvas } from '../components/DashboardBuilder/Canvas';
import { PanelLibrary, type PanelTemplate } from '../components/DashboardBuilder/PanelLibrary';

export function DashboardBuilder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dashboards, setDashboards] = useState<DashboardDefinition[]>([]);
  const [current, setCurrent] = useState<DashboardDefinition | null>(null);
  const [panelData, setPanelData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const ensureCurrentDashboard = useCallback((dashboards: DashboardDefinition[], targetId?: string) => {
    if (targetId) {
      return dashboards.find(d => d.id === targetId) || null;
    }
    if (dashboards.length > 0) {
      navigate(`/dashboard-builder/${dashboards[0].id}`, { replace: true });
      return dashboards[0];
    }
    return null;
  }, [navigate]);

  const loadDashboards = useCallback(async () => {
    try {
      setLoading(true);
      const list = await apiClient.listDashboards();
      setDashboards(list);
      const target = ensureCurrentDashboard(list, id);
      setCurrent(target);
      if (target) fetchData(target);
    } catch {
      toast.error('Failed to load dashboards');
    } finally {
      setLoading(false);
    }
  }, [id, ensureCurrentDashboard]);

  useEffect(() => { loadDashboards(); }, [loadDashboards]);

  const fetchData = async (dashboard: DashboardDefinition) => {
    try {
      const data = await apiClient.getDashboardData(dashboard.id);
      setPanelData(data.panels || {});
    } catch {
      // Silent fail for data
    }
  };

  const handleSave = async () => {
    if (!current) return;
    setSaving(true);
    try {
      await apiClient.updateDashboard(current.id, current);
      toast.success('Dashboard saved');
    } catch {
      toast.error('Failed to save dashboard');
    } finally {
      setSaving(false);
    }
  };

  const handleCreate = async () => {
    try {
      const name = prompt('Dashboard name:');
      if (!name) return;
      const dashboard = await apiClient.createDashboard({ name, panels: [], layout: { columns: 12, rowHeight: 100 }, refreshInterval: 30, starred: false });
      toast.success('Dashboard created');
      navigate(`/dashboard-builder/${dashboard.id}`);
      loadDashboards();
    } catch {
      toast.error('Failed to create dashboard');
    }
  };

  const handleDelete = async () => {
    if (!current || !confirm('Delete this dashboard?')) return;
    try {
      await apiClient.deleteDashboard(current.id);
      toast.success('Dashboard deleted');
      navigate('/dashboard-builder');
      loadDashboards();
    } catch {
      toast.error('Failed to delete dashboard');
    }
  };

  const handleAddPanel = (template: PanelTemplate) => {
    if (!current) return;
    const newPanel: DashboardPanel = {
      id: crypto.randomUUID(),
      type: template.type,
      title: template.title,
      dataSource: { ...template.defaultDataSource },
      position: {
        x: (current.panels.length * 3) % 9,
        y: Math.floor(current.panels.length / 3) * 2,
        w: 3,
        h: 2,
      },
      config: {},
    };
    setCurrent({ ...current, panels: [...current.panels, newPanel] });
  };

  const handleUpdatePanel = (updated: DashboardPanel) => {
    if (!current) return;
    setCurrent({
      ...current,
      panels: current.panels.map(p => p.id === updated.id ? updated : p),
    });
  };

  const handleRemovePanel = (panelId: string) => {
    if (!current) return;
    setCurrent({
      ...current,
      panels: current.panels.filter(p => p.id !== panelId),
    });
  };

  const handleSelectDashboard = (dashboardId: string) => {
    navigate(`/dashboard-builder/${dashboardId}`);
    const target = dashboards.find(d => d.id === dashboardId) || null;
    setCurrent(target);
    if (target) fetchData(target);
  };

  if (loading) {
    return <div className="text-center py-12 text-slate-400">Loading...</div>;
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard Builder</h1>
          <p className="text-slate-400">Create and manage custom dashboards</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleCreate} className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm rounded-lg transition-colors border border-slate-700">
            <Plus className="w-4 h-4" /> New
          </button>
          <button onClick={handleSave} disabled={saving || !current} className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
            <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save'}
          </button>
          {current && (
            <button onClick={handleDelete} className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-red-900/50 text-slate-300 hover:text-red-400 text-sm rounded-lg transition-colors border border-slate-700">
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        <div className="w-48 flex-shrink-0 space-y-2">
          {dashboards.map(d => (
            <button
              key={d.id}
              onClick={() => handleSelectDashboard(d.id)}
              className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors text-left ${
                current?.id === d.id ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span className="flex-1 truncate">{d.name}</span>
              {d.starred && <Star className="w-3 h-3 text-amber-400" />}
            </button>
          ))}
          {dashboards.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-4">No dashboards yet</p>
          )}
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          {current ? (
            <div className="flex gap-4 flex-1 min-h-0">
              <div className="flex-1 min-h-0 overflow-hidden">
                <Canvas
                  panels={current.panels}
                  panelData={panelData}
                  onUpdatePanel={handleUpdatePanel}
                  onRemovePanel={handleRemovePanel}
                  onAddPanel={handleAddPanel}
                />
              </div>
              <div className="w-48 flex-shrink-0">
                <PanelLibrary onAddPanel={handleAddPanel} />
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-slate-900 border-2 border-dashed border-slate-700 rounded-lg">
              <div className="text-center">
                <p className="text-slate-400 mb-4">No dashboard selected</p>
                <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors">
                  Create your first dashboard
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardBuilder;
