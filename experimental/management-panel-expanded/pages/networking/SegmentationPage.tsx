import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface NetworkSegment { id: string; name: string; cidr: string; segment_type: string; device_count: number; compliance_status: string; vlan_id: number; acl_rules: string[] }
interface TopologyNode { id: string; segment_id: string; label: string; node_type: string; ip_address: string }
interface TopologyEdge { id: string; source: string; target: string; label: string; allowed: boolean }

export const SegmentationPage = () => {
  const [segments, setSegments] = useState<NetworkSegment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [complianceDetail, setComplianceDetail] = useState<any>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/api/networking/segments');
      setSegments(Array.isArray(data) ? data : data?.segments || []);
    } catch { toast.error('Failed to load segments'); }
    finally { setLoading(false); }
  };

  const handleCompliance = async (id: string) => {
    try {
      const data = await apiClient.get(`/api/networking/segments/${id}/compliance`);
      setComplianceDetail(data);
    } catch { toast.error('Failed to check compliance'); }
  };

  const segmentTypes = [...new Set(segments.map(s => s.segment_type))];

  if (loading) return <div className="text-slate-400 p-8">Loading segments...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Network Segmentation Designer</h1>
          <p className="text-slate-400">Design and manage network segments with compliance checks</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {segmentTypes.map(t => (
          <button key={t} onClick={() => setSelectedSegment(null)} className={`px-3 py-1.5 text-xs rounded-lg border capitalize ${selectedSegment === null ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>{t}</button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {segments.map(seg => (
          <div key={seg.id} className={`bg-slate-900 border rounded-lg p-5 cursor-pointer transition-colors ${selectedSegment === seg.id ? 'border-blue-500' : 'border-slate-800 hover:border-slate-700'}`} onClick={() => { setSelectedSegment(seg.id); handleCompliance(seg.id); }}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-white">{seg.name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded ${seg.compliance_status === 'compliant' ? 'bg-green-600 text-white' : seg.compliance_status === 'non-compliant' ? 'bg-red-600 text-white' : 'bg-yellow-600 text-white'}`}>{seg.compliance_status}</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-slate-400">CIDR</span><p className="text-white font-mono text-xs">{seg.cidr}</p></div>
              <div><span className="text-slate-400">Type</span><p className="text-white capitalize">{seg.segment_type}</p></div>
              <div><span className="text-slate-400">VLAN ID</span><p className="text-white">{seg.vlan_id}</p></div>
              <div><span className="text-slate-400">Devices</span><p className="text-white">{seg.device_count}</p></div>
            </div>
            {seg.acl_rules && seg.acl_rules.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-800">
                <span className="text-xs text-slate-400">ACL Rules ({seg.acl_rules.length})</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {seg.acl_rules.slice(0, 3).map((r, i) => (
                    <span key={i} className="text-xs bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-mono">{r}</span>
                  ))}
                  {seg.acl_rules.length > 3 && <span className="text-xs text-slate-500">+{seg.acl_rules.length - 3} more</span>}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {complianceDetail && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <h3 className="text-lg font-semibold text-white mb-3">Compliance Details</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
            <div><span className="text-slate-400">Status</span><p className="text-white capitalize">{complianceDetail.status}</p></div>
            <div><span className="text-slate-400">Checks Passed</span><p className="text-white">{complianceDetail.checks_passed}</p></div>
            <div><span className="text-slate-400">Checks Failed</span><p className="text-white">{complianceDetail.checks_failed}</p></div>
            <div><span className="text-slate-400">Last Checked</span><p className="text-white">{complianceDetail.last_checked || 'N/A'}</p></div>
          </div>
          {complianceDetail.findings && complianceDetail.findings.length > 0 && (
            <div>
              <span className="text-sm text-slate-400">Findings</span>
              <ul className="list-disc list-inside text-sm text-slate-300 mt-1">
                {complianceDetail.findings.map((f: string, i: number) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {segments.length === 0 && <p className="text-slate-500 text-center py-8">No segments configured.</p>}
    </div>
  );
};

export default SegmentationPage;
