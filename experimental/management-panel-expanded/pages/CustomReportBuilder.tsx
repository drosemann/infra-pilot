import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../lib/api';
import type { ReportDesign, ReportWidgetConfig, ReportWidgetType, ReportSchedule, ReportDelivery, ReportTemplate, DeliveryChannel, ReportScheduleFrequency } from '../lib/types';

const WIDGET_DEFS: Array<{ type: ReportWidgetType; label: string; icon: string; defaultW: number; defaultH: number }> = [
  { type: 'line-chart', label: 'Line Chart', icon: '📈', defaultW: 4, defaultH: 3 },
  { type: 'bar-chart', label: 'Bar Chart', icon: '📊', defaultW: 4, defaultH: 3 },
  { type: 'pie-chart', label: 'Pie Chart', icon: '🥧', defaultW: 3, defaultH: 3 },
  { type: 'area-chart', label: 'Area Chart', icon: '📉', defaultW: 4, defaultH: 3 },
  { type: 'data-table', label: 'Data Table', icon: '📋', defaultW: 4, defaultH: 3 },
  { type: 'metric-card', label: 'Metric Card', icon: '🔢', defaultW: 2, defaultH: 2 },
  { type: 'text-block', label: 'Text Block', icon: '📝', defaultW: 3, defaultH: 2 },
  { type: 'image-block', label: 'Image Block', icon: '🖼️', defaultW: 3, defaultH: 3 },
  { type: 'status-indicator', label: 'Status', icon: '🟢', defaultW: 2, defaultH: 1 },
];

const CHANNEL_DEFS: Array<{ channel: DeliveryChannel; label: string; icon: string }> = [
  { channel: 'email', label: 'Email', icon: '📧' },
  { channel: 'slack', label: 'Slack', icon: '💬' },
  { channel: 'discord', label: 'Discord', icon: '🔊' },
  { channel: 'webhook', label: 'Webhook', icon: '🔗' },
  { channel: 'pdf', label: 'PDF Export', icon: '📄' },
];

const FREQ_OPTIONS: Array<{ value: ReportScheduleFrequency; label: string }> = [
  { value: 'one-time', label: 'One Time' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'custom', label: 'Custom (Cron)' },
];

function generateId(): string { return crypto.randomUUID(); }

function WidgetPreview({ widget }: { widget: ReportWidgetConfig }) {
  const def = WIDGET_DEFS.find(d => d.type === widget.type);
  return (
    <div className="bg-slate-700/50 rounded-lg p-3 h-full flex flex-col">
      <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
        <span>{def?.icon}</span>
        <span>{def?.label}</span>
      </div>
      <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
        {widget.type === 'metric-card' ? (
          <div className="text-center">
            <div className="text-2xl font-bold text-white">--</div>
            <div className="text-xs text-slate-400">{widget.title}</div>
          </div>
        ) : widget.type === 'status-indicator' ? (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-xs text-white">{widget.title}</span>
          </div>
        ) : widget.type === 'text-block' ? (
          <div className="text-xs text-slate-400 italic">Text content...</div>
        ) : widget.type === 'image-block' ? (
          <div className="text-xs text-slate-500">[Image placeholder]</div>
        ) : (
          <div className="text-xs text-slate-500">[Chart: {widget.title}]</div>
        )}
      </div>
    </div>
  );
}

interface ScheduleFormProps {
  designId: string;
  onSaved: () => void;
  onCancel: () => void;
}

function ScheduleForm({ designId, onSaved, onCancel }: ScheduleFormProps) {
  const [frequency, setFrequency] = useState<ReportScheduleFrequency>('daily');
  const [time, setTime] = useState('08:00');
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const [channels, setChannels] = useState<DeliveryChannel[]>(['email']);
  const [recipientStr, setRecipientStr] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [format, setFormat] = useState<'csv' | 'excel' | 'pdf'>('pdf');
  const [dayOfWeek, setDayOfWeek] = useState(1);
  const [dayOfMonth, setDayOfMonth] = useState(1);
  const [cronExpr, setCronExpr] = useState('0 8 * * *');
  const [saving, setSaving] = useState(false);

  const toggleChannel = (ch: DeliveryChannel) => {
    setChannels(prev => prev.includes(ch) ? prev.filter(c => c !== ch) : [...prev, ch]);
  };

  const handleSave = async () => {
    if (channels.length === 0) { toast.error('Select at least one delivery channel'); return; }
    setSaving(true);
    try {
      await apiClient.createReportSchedule({
        design_id: designId,
        frequency,
        time,
        timezone,
        channels,
        recipients: recipientStr.split(',').map(s => s.trim()).filter(Boolean),
        webhook_url: webhookUrl || undefined,
        format,
        day_of_week: frequency === 'weekly' ? dayOfWeek : undefined,
        day_of_month: frequency === 'monthly' ? dayOfMonth : undefined,
        cron_expression: frequency === 'custom' ? cronExpr : undefined,
        enabled: true,
      });
      toast.success('Schedule created');
      onSaved();
    } catch { toast.error('Failed to create schedule'); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Frequency</label>
          <select value={frequency} onChange={e => setFrequency(e.target.value as ReportScheduleFrequency)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
            {FREQ_OPTIONS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Time</label>
          <input type="time" value={time} onChange={e => setTime(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
        </div>
        {frequency === 'weekly' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Day of Week</label>
            <select value={dayOfWeek} onChange={e => setDayOfWeek(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d, i) => <option key={i} value={i}>{d}</option>)}
            </select>
          </div>
        )}
        {frequency === 'monthly' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Day of Month</label>
            <input type="number" min={1} max={31} value={dayOfMonth} onChange={e => setDayOfMonth(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
          </div>
        )}
        {frequency === 'custom' && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">Cron Expression</label>
            <input type="text" value={cronExpr} onChange={e => setCronExpr(e.target.value)}
              placeholder="0 8 * * *"
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
          </div>
        )}
        <div>
          <label className="block text-xs text-slate-400 mb-1">Timezone</label>
          <select value={timezone} onChange={e => setTimezone(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
            {Intl.supportedValuesOf('timeZone').map(tz => <option key={tz} value={tz}>{tz}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Export Format</label>
          <select value={format} onChange={e => setFormat(e.target.value as any)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
            <option value="csv">CSV</option>
            <option value="excel">Excel</option>
            <option value="pdf">PDF</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1">Delivery Channels</label>
        <div className="flex flex-wrap gap-2">
          {CHANNEL_DEFS.map(cd => (
            <button key={cd.channel} onClick={() => toggleChannel(cd.channel)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${channels.includes(cd.channel) ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-400 hover:text-white'}`}>
              {cd.icon} {cd.label}
            </button>
          ))}
        </div>
      </div>

      {channels.includes('email') && (
        <div>
          <label className="block text-xs text-slate-400 mb-1">Email Recipients (comma-separated)</label>
          <input type="text" value={recipientStr} onChange={e => setRecipientStr(e.target.value)}
            placeholder="admin@example.com, team@example.com"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
        </div>
      )}

      {channels.includes('slack') && (
        <div>
          <label className="block text-xs text-slate-400 mb-1">Slack Webhook URLs (comma-separated)</label>
          <input type="text" value={recipientStr} onChange={e => setRecipientStr(e.target.value)}
            placeholder="https://hooks.slack.com/services/..."
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
        </div>
      )}

      {channels.includes('webhook') && (
        <div>
          <label className="block text-xs text-slate-400 mb-1">Custom Webhook URL</label>
          <input type="url" value={webhookUrl} onChange={e => setWebhookUrl(e.target.value)}
            placeholder="https://hooks.example.com/report"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
        </div>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <button onClick={onCancel}
          className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">Cancel</button>
        <button onClick={handleSave} disabled={saving}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
          {saving ? 'Saving...' : 'Create Schedule'}
        </button>
      </div>
    </div>
  );
}

export default function CustomReportBuilder() {
  const [designs, setDesigns] = useState<ReportDesign[]>([]);
  const [current, setCurrent] = useState<ReportDesign | null>(null);
  const [schedules, setSchedules] = useState<ReportSchedule[]>([]);
  const [deliveries, setDeliveries] = useState<ReportDelivery[]>([]);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [showTemplateLib, setShowTemplateLib] = useState(false);
  const [activeTab, setActiveTab] = useState<'designer' | 'schedules' | 'deliveries'>('designer');
  const [designName, setDesignName] = useState('Untitled Report');
  const [designDesc, setDesignDesc] = useState('');
  const [widgets, setWidgets] = useState<ReportWidgetConfig[]>([]);
  const [draggedType, setDraggedType] = useState<ReportWidgetType | null>(null);
  const [editingWidget, setEditingWidget] = useState<ReportWidgetConfig | null>(null);
  const dragCounter = useRef(0);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [d, scheds, dels, tmpls] = await Promise.all([
        apiClient.listReportDesigns(),
        apiClient.listReportSchedules(),
        apiClient.listReportDeliveries(),
        apiClient.getReportTemplates(),
      ]);
      setDesigns(d);
      setSchedules(scheds);
      setDeliveries(dels);
      setTemplates(tmpls);
      if (d.length > 0 && !current) {
        setCurrent(d[0]);
        setDesignName(d[0].name);
        setDesignDesc(d[0].description);
        setWidgets(d[0].widgets);
      }
    } catch { toast.error('Failed to load report data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const selectDesign = (design: ReportDesign) => {
    setCurrent(design);
    setDesignName(design.name);
    setDesignDesc(design.description);
    setWidgets(design.widgets);
    setActiveTab('designer');
  };

  // Drag and drop
  const handleDragStart = (e: React.DragEvent, type: ReportWidgetType) => {
    e.dataTransfer.setData('text/plain', type);
    setDraggedType(type);
  };

  const handleCanvasDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleCanvasDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const type = e.dataTransfer.getData('text/plain') as ReportWidgetType;
    if (!type) return;
    const def = WIDGET_DEFS.find(d => d.type === type);
    if (!def) return;
    const newWidget: ReportWidgetConfig = {
      type,
      title: def.label,
      dataSource: { type: 'metrics', period: '1h' },
      position: { x: 0, y: widgets.length, w: def.defaultW, h: def.defaultH },
      config: {},
    };
    setWidgets(prev => [...prev, newWidget]);
    setDraggedType(null);
  };

  const removeWidget = (idx: number) => {
    setWidgets(prev => prev.filter((_, i) => i !== idx));
  };

  const updateWidget = (idx: number, updates: Partial<ReportWidgetConfig>) => {
    setWidgets(prev => prev.map((w, i) => i === idx ? { ...w, ...updates } : w));
  };

  // Apply template
  const applyTemplate = (tmpl: ReportTemplate) => {
    setDesignName(tmpl.name);
    setDesignDesc(tmpl.description);
    setWidgets(tmpl.widgets.map(w => ({ ...w, position: { ...w.position } })));
    setShowTemplateLib(false);
    toast.success(`Template "${tmpl.name}" applied`);
  };

  // Save design
  const handleSave = async () => {
    if (!current) {
      // Create new
      try {
        setSaving(true);
        const created = await apiClient.createReportDesign({
          name: designName,
          description: designDesc,
          widgets,
          layout: { columns: 12, rowHeight: 80 },
        });
        setCurrent(created);
        toast.success('Report design created');
        loadData();
      } catch { toast.error('Failed to create design'); }
      finally { setSaving(false); }
    } else {
      try {
        setSaving(true);
        await apiClient.updateReportDesign(current.id, {
          name: designName,
          description: designDesc,
          widgets,
          layout: { columns: 12, rowHeight: 80 },
        });
        toast.success('Report design saved');
        loadData();
      } catch { toast.error('Failed to save design'); }
      finally { setSaving(false); }
    }
  };

  const handleCreateNew = () => {
    setCurrent(null);
    setDesignName('Untitled Report');
    setDesignDesc('');
    setWidgets([]);
  };

  const handleDeleteDesign = async () => {
    if (!current || !confirm(`Delete "${current.name}"?`)) return;
    try {
      await apiClient.deleteReportDesign(current.id);
      toast.success('Design deleted');
      setCurrent(null);
      setDesignName('Untitled Report');
      setDesignDesc('');
      setWidgets([]);
      loadData();
    } catch { toast.error('Failed to delete design'); }
  };

  const handleGenerateNow = async (channel?: DeliveryChannel) => {
    if (!current) { toast.error('Save design first'); return; }
    try {
      const chs = channel ? [channel] : ['pdf' as DeliveryChannel];
      await apiClient.generateReportNow(current.id, chs);
      toast.success('Report generation started');
      loadData();
    } catch { toast.error('Failed to generate report'); }
  };

  const handleDeleteSchedule = async (id: string) => {
    if (!confirm('Delete this schedule?')) return;
    try {
      await apiClient.deleteReportSchedule(id);
      toast.success('Schedule deleted');
      loadData();
    } catch { toast.error('Failed to delete schedule'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Custom Report Builder</h1>
          <p className="text-slate-400">Design, schedule, and deliver custom reports</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Report Designs</p>
          <p className="text-2xl font-bold text-blue-400">{designs.length}</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Active Schedules</p>
          <p className="text-2xl font-bold text-green-400">{schedules.filter(s => s.enabled).length}</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Deliveries Today</p>
          <p className="text-2xl font-bold text-yellow-400">
            {deliveries.filter(d => new Date(d.delivered_at).toDateString() === new Date().toDateString()).length}
          </p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Templates</p>
          <p className="text-2xl font-bold text-purple-400">{templates.length}</p>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <button onClick={handleCreateNew}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors">
          + New Design
        </button>
        {current && (
          <>
            <div className="flex-1" />
            <button onClick={() => setShowTemplateLib(true)}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded transition-colors">
              📚 Templates
            </button>
            <button onClick={() => setShowScheduleForm(true)}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded transition-colors">
              🕐 Schedule
            </button>
            <button onClick={() => handleGenerateNow()}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded transition-colors">
              ▶ Generate Now
            </button>
            <button onClick={handleDeleteDesign}
              className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 text-sm font-medium rounded transition-colors">
              🗑 Delete
            </button>
          </>
        )}
      </div>

      {/* Design Selector */}
      {designs.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {designs.map(d => (
            <button key={d.id} onClick={() => selectDesign(d)}
              className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${current?.id === d.id ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:text-white'}`}>
              {d.name}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading...</div>
      ) : (
        <div className="space-y-4">
          {/* Tab bar */}
          {current && (
            <div className="flex bg-slate-800 rounded-lg p-1 w-fit">
              {(['designer', 'schedules', 'deliveries'] as const).map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`px-4 py-1.5 text-sm rounded-md transition-colors ${activeTab === tab ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                  {tab === 'designer' ? 'Designer' : tab === 'schedules' ? 'Schedules' : 'Deliveries'}
                </button>
              ))}
            </div>
          )}

          {/* Designer Tab */}
          {activeTab === 'designer' && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              {/* Widget Palette */}
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-white mb-3">Widgets</h3>
                <div className="space-y-2">
                  {WIDGET_DEFS.map(def => (
                    <div key={def.type}
                      draggable
                      onDragStart={e => handleDragStart(e, def.type)}
                      className="flex items-center gap-3 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg cursor-grab active:cursor-grabbing transition-colors text-sm text-slate-300">
                      <span>{def.icon}</span>
                      <span>{def.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Canvas */}
              <div className="lg:col-span-3">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  {/* Design metadata */}
                  <div className="flex gap-3 mb-4">
                    <input type="text" value={designName} onChange={e => setDesignName(e.target.value)}
                      placeholder="Report name"
                      className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
                    <input type="text" value={designDesc} onChange={e => setDesignDesc(e.target.value)}
                      placeholder="Description (optional)"
                      className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
                    <button onClick={handleSave} disabled={saving}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
                      {saving ? 'Saving...' : current ? 'Save' : 'Create'}
                    </button>
                  </div>

                  {/* Drop zone */}
                  <div
                    onDragOver={handleCanvasDragOver}
                    onDrop={handleCanvasDrop}
                    className="min-h-[400px] border-2 border-dashed border-slate-700 rounded-lg p-4 transition-colors hover:border-slate-500"
                  >
                    {widgets.length === 0 ? (
                      <div className="flex flex-col items-center justify-center h-[400px] text-slate-500">
                        <p className="text-lg mb-2">Drag widgets here</p>
                        <p className="text-xs">or click a template to get started</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-12 gap-3 auto-rows-[80px]">
                        {widgets.map((w, i) => (
                          <div key={i}
                            className="col-span-12 group relative"
                            style={{ gridColumn: `span ${Math.min(w.position.w || 4, 12)}`, gridRow: `span ${w.position.h || 3}` }}
                          >
                            <WidgetPreview widget={w} />
                            <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => setEditingWidget(w)}
                                className="p-1 bg-slate-600 hover:bg-slate-500 rounded text-xs text-white">✏️</button>
                              <button onClick={() => removeWidget(i)}
                                className="p-1 bg-red-600/60 hover:bg-red-600 rounded text-xs text-white">✕</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Schedules Tab */}
          {activeTab === 'schedules' && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Delivery Schedules</h3>
                <button onClick={() => setShowScheduleForm(true)}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors">
                  + New Schedule
                </button>
              </div>

              {showScheduleForm && current && (
                <div className="mb-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                  <h4 className="text-sm font-semibold text-white mb-3">New Schedule for "{current.name}"</h4>
                  <ScheduleForm designId={current.id} onSaved={() => { setShowScheduleForm(false); loadData(); }} onCancel={() => setShowScheduleForm(false)} />
                </div>
              )}

              {schedules.length === 0 ? (
                <div className="text-center py-8 text-slate-500">No schedules yet</div>
              ) : (
                <div className="space-y-3">
                  {schedules.map(s => (
                    <div key={s.id} className="flex items-center justify-between bg-slate-700/50 rounded-lg px-4 py-3">
                      <div className="flex items-center gap-4">
                        <div className={`w-2 h-2 rounded-full ${s.enabled ? 'bg-green-500' : 'bg-slate-500'}`} />
                        <div>
                          <p className="text-sm text-white font-medium capitalize">{s.frequency.replace('-', ' ')}</p>
                          <p className="text-xs text-slate-400">
                            {s.time} {s.timezone} | {s.channels.join(', ')} | {s.format.toUpperCase()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {s.next_run && <span className="text-xs text-slate-400">Next: {new Date(s.next_run).toLocaleDateString()}</span>}
                        <button onClick={() => handleDeleteSchedule(s.id)}
                          className="text-red-400 hover:text-red-300 text-xs">Delete</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Deliveries Tab */}
          {activeTab === 'deliveries' && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Delivery History</h3>
              {deliveries.length === 0 ? (
                <div className="text-center py-8 text-slate-500">No deliveries yet</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-400 border-b border-slate-700">
                        <th className="pb-2 pr-4">Status</th>
                        <th className="pb-2 pr-4">Channels</th>
                        <th className="pb-2 pr-4">Recipients</th>
                        <th className="pb-2">Delivered At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deliveries.map(d => (
                        <tr key={d.id} className="border-b border-slate-800">
                          <td className="py-2 pr-4">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${d.status === 'sent' ? 'bg-green-600/20 text-green-400' : d.status === 'failed' ? 'bg-red-600/20 text-red-400' : 'bg-yellow-600/20 text-yellow-400'}`}>
                              {d.status}
                            </span>
                          </td>
                          <td className="py-2 pr-4 text-slate-300">{d.channels.join(', ')}</td>
                          <td className="py-2 pr-4 text-white">{d.recipient_count}</td>
                          <td className="py-2 text-slate-400">{new Date(d.delivered_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Widget Editor Modal */}
      {editingWidget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setEditingWidget(null)}>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">Edit Widget</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Title</label>
                <input type="text" value={editingWidget.title}
                  onChange={e => setEditingWidget({ ...editingWidget, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Data Source</label>
                <select value={editingWidget.dataSource.type}
                  onChange={e => setEditingWidget({ ...editingWidget, dataSource: { ...editingWidget.dataSource, type: e.target.value } })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
                  <option value="metrics">Metrics</option>
                  <option value="logs">Logs</option>
                  <option value="alerts">Alerts</option>
                  <option value="backups">Backups</option>
                  <option value="apps">Apps</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Period</label>
                <select value={editingWidget.dataSource.period || '1h'}
                  onChange={e => setEditingWidget({ ...editingWidget, dataSource: { ...editingWidget.dataSource, period: e.target.value } })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500">
                  <option value="15m">15 min</option>
                  <option value="1h">1 hour</option>
                  <option value="6h">6 hours</option>
                  <option value="24h">24 hours</option>
                  <option value="7d">7 days</option>
                  <option value="30d">30 days</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Width (cols)</label>
                  <input type="number" min={1} max={12} value={editingWidget.position.w}
                    onChange={e => setEditingWidget({ ...editingWidget, position: { ...editingWidget.position, w: Number(e.target.value) } })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Height (rows)</label>
                  <input type="number" min={1} max={12} value={editingWidget.position.h}
                    onChange={e => setEditingWidget({ ...editingWidget, position: { ...editingWidget.position, h: Number(e.target.value) } })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-white outline-none focus:border-blue-500" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setEditingWidget(null)}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">Cancel</button>
              <button onClick={() => {
                const idx = widgets.findIndex(w => w === editingWidget);
                if (idx >= 0) updateWidget(idx, editingWidget);
                setEditingWidget(null);
              }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors">Apply</button>
            </div>
          </div>
        </div>
      )}

      {/* Template Library Modal */}
      {showTemplateLib && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowTemplateLib(false)}>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-3xl mx-4 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">Report Templates</h3>
            {templates.length === 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { name: 'Weekly Performance Summary', desc: 'CPU, memory, disk, and network metrics for the week', cat: 'performance', widgets: 5 },
                  { name: 'Error Analysis Report', desc: 'Error rates, top error sources, and trends', cat: 'errors', widgets: 4 },
                  { name: 'Resource Usage Overview', desc: 'Resource consumption across all services', cat: 'resources', widgets: 4 },
                  { name: 'Security Audit Report', desc: 'Access logs, auth attempts, and security events', cat: 'security', widgets: 3 },
                  { name: 'Deployment Activity', desc: 'Recent deployments, rollbacks, and changes', cat: 'operations', widgets: 3 },
                  { name: 'Backup Status Report', desc: 'Backup success rates, sizes, and retention', cat: 'backups', widgets: 4 },
                ].map((tmpl, i) => (
                  <div key={i} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 hover:border-blue-500 transition-colors cursor-pointer"
                    onClick={() => {
                      applyTemplate({
                        id: `template-${i}`,
                        name: tmpl.name,
                        description: tmpl.desc,
                        category: tmpl.cat,
                        widgets: Array.from({ length: tmpl.widgets }, (_, wi) => ({
                          type: (['line-chart', 'bar-chart', 'metric-card', 'data-table', 'status-indicator'] as ReportWidgetType[])[wi % 5],
                          title: `${tmpl.name} - Widget ${wi + 1}`,
                          dataSource: { type: 'metrics', period: '24h' },
                          position: { x: 0, y: wi, w: wi === 0 ? 6 : 3, h: 2 },
                          config: {},
                        })),
                        layout: { columns: 12, rowHeight: 80 },
                      });
                    }}>
                    <p className="text-sm font-semibold text-white">{tmpl.name}</p>
                    <p className="text-xs text-slate-400 mt-1">{tmpl.desc}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-slate-500 bg-slate-600 px-2 py-0.5 rounded capitalize">{tmpl.cat}</span>
                      <span className="text-xs text-slate-500">{tmpl.widgets} widgets</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {templates.map(tmpl => (
                  <div key={tmpl.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 hover:border-blue-500 transition-colors cursor-pointer"
                    onClick={() => applyTemplate(tmpl)}>
                    <p className="text-sm font-semibold text-white">{tmpl.name}</p>
                    <p className="text-xs text-slate-400 mt-1">{tmpl.description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-slate-500 bg-slate-600 px-2 py-0.5 rounded capitalize">{tmpl.category}</span>
                      <span className="text-xs text-slate-500">{tmpl.widgets.length} widgets</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="flex justify-end mt-4">
              <button onClick={() => setShowTemplateLib(false)}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}