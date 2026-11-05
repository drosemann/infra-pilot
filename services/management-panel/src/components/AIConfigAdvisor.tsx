import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';

interface Suggestion {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: string;
  title: string;
  description: string;
  recommendation: string;
  file?: string;
  autoFixable: boolean;
  fixCommand?: string;
}

interface AdviceResult {
  appId: string;
  analyzedAt: string;
  total: number;
  critical: number;
  warning: number;
  info: number;
  suggestions: Suggestion[];
}

interface AIConfigAdvisorProps {
  appId: string;
}

export const AIConfigAdvisor = ({ appId }: AIConfigAdvisorProps) => {
  const [result, setResult] = useState<AdviceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [applying, setApplying] = useState<string | null>(null);

  useEffect(() => {
    loadAdvice();
  }, [appId]);

  const loadAdvice = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getConfigAdvice(appId);
      setResult(data);
    } catch {
      toast.error('Failed to load config advice');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleApply = async (suggestionId: string) => {
    setApplying(suggestionId);
    try {
      await apiClient.applyConfigAdvice(appId, suggestionId);
      toast.success('Suggestion applied');
    } catch {
      toast.error('Failed to apply suggestion');
    } finally {
      setApplying(null);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500/30 bg-red-500/5';
      case 'warning': return 'border-yellow-500/30 bg-yellow-500/5';
      case 'info': return 'border-blue-500/30 bg-blue-500/5';
      default: return 'border-white/10 bg-white/[0.04]';
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'warning': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'info': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default: return 'bg-white/5 text-white/45 border-white/10';
    }
  };

  if (loading) {
    return <div className="text-white/45 py-4">Analyzing configuration...</div>;
  }

  if (!result) {
    return (
      <div className="text-center py-8">
        <p className="text-white/45">Unable to analyze configuration</p>
        <button onClick={loadAdvice} className="primary-button mt-4">
          Retry Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">AI Config Advisor</h3>
        <button onClick={loadAdvice} className="px-3 py-1.5 text-xs bg-white/10 hover:bg-white/20 text-white/60 rounded transition-colors">
          Re-analyze
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-white">{result.total}</p>
          <p className="text-xs text-white/45">Total</p>
        </div>
        <div className="bg-white/[0.04] border border-red-500/30 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-red-400">{result.critical}</p>
          <p className="text-xs text-white/45">Critical</p>
        </div>
        <div className="bg-white/[0.04] border border-yellow-500/30 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-yellow-400">{result.warning}</p>
          <p className="text-xs text-white/45">Warnings</p>
        </div>
        <div className="bg-white/[0.04] border border-blue-500/30 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-blue-400">{result.info}</p>
          <p className="text-xs text-white/45">Info</p>
        </div>
      </div>

      {result.suggestions.length === 0 ? (
        <div className="card p-6 text-center">
          <p className="text-green-400 text-lg font-semibold">No issues found!</p>
          <p className="text-white/45 text-sm mt-1">Your configuration follows best practices.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {result.suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className={`border rounded-lg ${getSeverityColor(suggestion.severity)}`}
            >
              <button
                onClick={() => toggleExpand(suggestion.id)}
                className="w-full flex items-center justify-between p-3 text-left"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`px-2 py-0.5 text-xs rounded border ${getSeverityBadge(suggestion.severity)} capitalize shrink-0`}>
                    {suggestion.severity}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-white/10 rounded text-white/60 shrink-0">{suggestion.category}</span>
                  <span className="text-sm text-white truncate">{suggestion.title}</span>
                </div>
                <svg className={`w-4 h-4 text-white/45 shrink-0 transition-transform ${expanded.has(suggestion.id) ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {expanded.has(suggestion.id) && (
                <div className="px-3 pb-3 space-y-3">
                  <p className="text-sm text-white/60">{suggestion.description}</p>
                  <div className="bg-black/30 rounded p-2">
                    <p className="text-xs text-white/45 mb-1">Recommendation:</p>
                    <p className="text-sm text-blue-300">{suggestion.recommendation}</p>
                  </div>
                  {suggestion.file && (
                    <p className="text-xs text-white/40">Affected file: {suggestion.file}</p>
                  )}
                  {suggestion.autoFixable && (
                    <button
                      onClick={() => handleApply(suggestion.id)}
                      disabled={applying === suggestion.id}
                      className="px-3 py-1.5 text-xs bg-green-600 hover:bg-green-700 disabled:bg-white/10 text-white rounded transition-colors"
                    >
                      {applying === suggestion.id ? 'Applying...' : 'Apply Fix'}
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-white/40 text-right">
        Analyzed at {new Date(result.analyzedAt).toLocaleString()}
      </p>
    </div>
  );
};
