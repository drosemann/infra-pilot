import { useState } from 'react';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { PageHeader } from '../components/PageHeader';

export const Reports = () => {
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getReports(startDate, endDate);
      setReportData(data);
    } catch {
      toast.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'csv') => {
    setExporting(true);
    try {
      const blob = await apiClient.exportReport(format, startDate, endDate);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch {
      toast.error('Failed to export report');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader eyebrow="Analyze">
        <h1 className="text-4xl font-semibold tracking-tight text-white">Reports</h1>
        <p className="mt-2 text-white/55">Resource usage and incidents, exportable.</p>
      </PageHeader>

      <div className="card p-6">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-white/45">Start date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="input-field text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-white/45">End date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="input-field text-sm"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="primary-button"
          >
            {loading ? 'Generating…' : 'Generate'}
          </button>
          {reportData && (
            <>
              <button
                onClick={() => handleExport('csv')}
                disabled={exporting}
                className="secondary-button"
              >
                {exporting ? 'Exporting…' : 'Export CSV'}
              </button>
              <button
                onClick={() => handleExport('pdf')}
                disabled={exporting}
                className="secondary-button"
              >
                {exporting ? 'Exporting…' : 'Export PDF'}
              </button>
            </>
          )}
        </div>
      </div>

      {reportData && (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="card p-4 text-center">
              <p className="text-2xl font-semibold text-white">{(reportData.metrics || []).length}</p>
              <p className="mt-1 text-xs text-white/45">Metric data points</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-semibold text-white">{(reportData.backups || []).filter((b: any) => b.status === 'success').length}</p>
              <p className="mt-1 text-xs text-white/45">Successful backups</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-semibold text-white">{(reportData.alerts || []).length}</p>
              <p className="mt-1 text-xs text-white/45">Alerts triggered</p>
            </div>
          </div>

          {reportData.metrics && reportData.metrics.length > 0 && (
            <div className="card p-4">
              <h3 className="mb-3 font-semibold text-white">Recent metrics</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-left text-white/45">
                      <th className="pb-2 pr-4 font-medium">App</th>
                      <th className="pb-2 pr-4 font-medium">CPU</th>
                      <th className="pb-2 pr-4 font-medium">Memory</th>
                      <th className="pb-2 pr-4 font-medium">TPS</th>
                      <th className="pb-2 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.metrics.slice(0, 20).map((m: any) => (
                      <tr key={m.id} className="border-b border-white/5">
                        <td className="py-2 pr-4 text-white/60">{m.app_id?.slice(0, 8)}</td>
                        <td className="py-2 pr-4 text-white">{m.cpu_percent}%</td>
                        <td className="py-2 pr-4 text-white">{m.memory_used_mb}MB</td>
                        <td className="py-2 pr-4 text-white">{m.tps}</td>
                        <td className="py-2 text-white/45">{new Date(m.recorded_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {reportData.alerts && reportData.alerts.length > 0 && (
            <div className="card p-4">
              <h3 className="mb-3 font-semibold text-white">Alert summary</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-left text-white/45">
                      <th className="pb-2 pr-4 font-medium">Type</th>
                      <th className="pb-2 pr-4 font-medium">Value</th>
                      <th className="pb-2 pr-4 font-medium">Threshold</th>
                      <th className="pb-2 font-medium">Triggered</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.alerts.slice(0, 20).map((a: any) => (
                      <tr key={a.id} className="border-b border-white/5">
                        <td className="py-2 pr-4 text-white/60">{a.metric_type}</td>
                        <td className="py-2 pr-4 text-white">{a.metric_value}</td>
                        <td className="py-2 pr-4 text-white">{a.threshold}</td>
                        <td className="py-2 text-white/45">{new Date(a.triggered_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Reports;
