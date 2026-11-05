import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../lib/api';

interface LogEntry {
  id: string;
  timestamp: string;
  app: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
  status?: 'success' | 'failed';
}

interface LiveLogsProps {
  logs?: LogEntry[];
  isLive?: boolean;
  maxHeight?: string;
  appId?: string;
}

const LOG_LEVELS = ['ALL', 'INFO', 'WARN', 'ERROR', 'DEBUG'] as const;

function highlightText(text: string, query: string) {
  if (!query) return text;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase()
      ? `<mark class="bg-yellow-500/30 text-yellow-200 rounded px-0.5">${part}</mark>`
      : part
  ).join('');
}

export const LiveLogs = ({
  logs = [],
  isLive = true,
  maxHeight = 'max-h-96',
  appId,
}: LiveLogsProps) => {
  const [isPaused, setIsPaused] = useState(false);
  const [displayLogs, setDisplayLogs] = useState(logs);
  const [mode, setMode] = useState<'live' | 'search'>('live');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [searchResults, setSearchResults] = useState<LogEntry[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setDisplayLogs(logs);
  }, [logs]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const performSearch = useCallback(async (page = 1) => {
    if (!appId) return;
    setLoading(true);
    try {
      const result = await apiClient.searchLogs(appId, {
        query: debouncedSearch || undefined,
        level: levelFilter === 'ALL' ? undefined : levelFilter,
        from: fromDate || undefined,
        to: toDate || undefined,
        page,
        limit: 50,
      });
      setSearchResults(result.logs);
      setTotalResults(result.total);
      setCurrentPage(page);
    } catch {
      setSearchResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  }, [appId, debouncedSearch, levelFilter, fromDate, toDate]);

  useEffect(() => {
    if (mode === 'search') {
      performSearch(1);
    }
  }, [mode, performSearch]);

  const getLevelBackground = (level: string) => {
    switch (level) {
      case 'INFO':
        return 'bg-blue-500/10 text-blue-400';
      case 'WARN':
        return 'bg-yellow-500/10 text-yellow-400';
      case 'ERROR':
        return 'bg-red-500/10 text-red-400';
      case 'DEBUG':
        return 'bg-gray-500/10 text-gray-400';
      default:
        return 'bg-slate-500/10 text-white/45';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const currentLogs = mode === 'search' ? searchResults : displayLogs;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-semibold tracking-tight text-white">Logs</h3>
          {mode === 'live' && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-sm">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Live
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode(mode === 'live' ? 'search' : 'live')}
            className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
              mode === 'search'
                ? 'primary-button'
                : 'secondary-button'
            }`}
          >
            {mode === 'live' ? 'ðŸ” Search' : 'ðŸ”´ Live'}
          </button>
          {mode === 'live' && (
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                isPaused
                  ? 'primary-button'
                  : 'secondary-button'
              }`}
            >
              {isPaused ? 'â–¶ Resume' : 'â¸ Pause'}
            </button>
          )}
          {mode === 'live' && (
            <button onClick={() => setDisplayLogs([])} className="secondary-button">
              ðŸ—‘ Clear
            </button>
          )}
        </div>
      </div>

      {/* Search / Filter Bar */}
      {mode === 'search' && (
        <div className="card flex flex-wrap items-center gap-3 p-3">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field min-w-[200px] flex-1 text-sm"
          />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="input-field text-sm"
          >
            {LOG_LEVELS.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="input-field text-sm"
          />
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="input-field text-sm"
          />
          <button
            onClick={() => performSearch(1)}
            className="primary-button"
          >
            Search
          </button>
          {totalResults > 0 && (
            <span className="text-sm text-white/45">
              Showing {searchResults.length} of {totalResults} results
            </span>
          )}
        </div>
      )}

      {/* Logs Container */}
      <div className={`${maxHeight} card overflow-y-auto`}>
        {loading ? (
          <div className="flex items-center justify-center py-8 text-white/45">
            Searching logs...
          </div>
        ) : currentLogs.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-white/45">
            No results
          </div>
        ) : (
          <div className="font-mono text-xs">
            {currentLogs.map((log, idx) => (
              <div
                key={log.id || idx}
                className="flex items-start gap-3 border-b border-white/5 px-4 py-2"
              >
                <span className="flex-shrink-0 text-white/35 w-20">
                  {log.id}
                </span>
                <span className="flex-shrink-0 text-white/35 w-32">
                  {formatTime(log.timestamp)}
                </span>
                <span
                  className={`${getLevelBackground(log.level)} px-2 py-0.5 rounded text-xs font-semibold flex-shrink-0 w-16`}
                >
                  {log.level}
                </span>
                <span className="text-blue-400 flex-shrink-0 w-24">{log.app}:</span>
                <span
                  className="flex-1 text-white/70"
                  dangerouslySetInnerHTML={{
                    __html: mode === 'search' && debouncedSearch
                      ? highlightText(log.message, debouncedSearch)
                      : log.message,
                  }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {mode === 'search' && totalResults > 50 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={currentPage <= 1}
            onClick={() => performSearch(currentPage - 1)}
            className="secondary-button"
          >
            Previous
          </button>
          <span className="text-sm text-white/45">
            Page {currentPage} of {Math.ceil(totalResults / 50)}
          </span>
          <button
            disabled={currentPage >= Math.ceil(totalResults / 50)}
            onClick={() => performSearch(currentPage + 1)}
            className="secondary-button"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
