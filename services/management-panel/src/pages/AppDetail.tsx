import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { apiClient } from '../lib/api';
import { DockerApp } from '../lib/types';
import { toast } from 'sonner';
import { GitDeployManager } from '../components/GitDeployManager';
import { DatabaseManager } from '../components/DatabaseManager';
import { ModpackBrowser } from '../components/ModpackBrowser';
import { ConfigEditor } from '../components/ConfigEditor';
import { ConfigVersionControl } from '../components/ConfigVersionControl';
import { LiveLogs } from '../components/LiveLogs';
import AlertConfig from '../components/AlertConfig';
import { ServerOperationsHub } from '../components/ServerOperationsHub';
import { PageHeader } from '../components/PageHeader';

type Tab = 'overview' | 'logs' | 'config' | 'deploy' | 'advanced';

const TABS: Tab[] = ['overview', 'logs', 'config', 'deploy', 'advanced'];

export const AppDetail = () => {
  const navigate = useNavigate();
  const { appId } = useParams();
  const [app, setApp] = useState<DockerApp | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [logs, setLogs] = useState<Array<any>>([]);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (appId) {
      loadApp();
    }
  }, [appId]);

  useEffect(() => {
    if (activeTab === 'logs') {
      loadLogs();
      const interval = setInterval(loadLogs, 30000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  const loadApp = async () => {
    try {
      const data = await apiClient.getApp(appId!);
      setApp(data);
    } catch (error) {
      toast.error('Failed to load app');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadLogs = async () => {
    if (!appId) return;
    try {
      const data = await apiClient.getLogs(appId, 50, 0);
      setLogs(data);
    } catch (error) {
      // Silently fail on logs load
    }
  };

  const runAction = async (fn: () => Promise<DockerApp | void>, success: string, failure: string, after?: () => void) => {
    setActionLoading(true);
    try {
      const updated = await fn();
      if (updated) setApp(updated as DockerApp);
      toast.success(success);
      after?.();
    } catch (error) {
      toast.error(failure);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = () => {
    if (!window.confirm('Are you sure you want to delete this app?')) return;
    runAction(() => apiClient.deleteApp(appId!), 'App deleted', 'Failed to delete app', () => navigate('/dashboard'));
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-2 py-16 text-center">
        <p className="text-white/45">Loading…</p>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-2 py-16 text-center">
        <p className="text-white/55">App not found</p>
        <button onClick={() => navigate('/dashboard')} className="secondary-button">
          Back to Overview
        </button>
      </div>
    );
  }

  const statusDot =
    app.status === 'running' ? 'bg-emerald-400'
    : app.status === 'error' ? 'bg-red-400'
    : app.status === 'restarting' ? 'bg-amber-400 animate-pulse'
    : 'bg-white/30';

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader
        eyebrow="Apps"
        actions={
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-white/55 transition-colors hover:text-white"
          >
            ← Back
          </button>
        }
      >
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-4xl font-semibold tracking-tight text-white">{app.name}</h1>
          <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-3 py-1 text-xs text-white/70">
            <span className={`h-2 w-2 rounded-full ${statusDot}`} />
            {app.status}
          </span>
        </div>
        <p className="mt-2 font-mono text-sm text-white/45">{app.image}</p>
        {app.description && (
          <p className="mt-2 max-w-2xl text-white/55">{app.description}</p>
        )}
      </PageHeader>

      {/* One primary action */}
      <div className="flex flex-wrap items-center gap-3">
        {app.status === 'running' ? (
          <>
            <button
              onClick={() => runAction(() => apiClient.restartApp(appId!), 'App restarting', 'Failed to restart app')}
              disabled={actionLoading}
              className="primary-button"
            >
              Restart
            </button>
            <button
              onClick={() => runAction(() => apiClient.stopApp(appId!), 'App stopped', 'Failed to stop app')}
              disabled={actionLoading}
              className="secondary-button"
            >
              Stop
            </button>
          </>
        ) : (
          <button
            onClick={() => runAction(() => apiClient.startApp(appId!), 'App started', 'Failed to start app')}
            disabled={actionLoading}
            className="primary-button"
          >
            Start
          </button>
        )}
        <button
          onClick={() => navigate(`/apps/${app.id}/edit`)}
          disabled={actionLoading}
          className="secondary-button"
        >
          Edit
        </button>
      </div>

      {/* Tabs */}
      <div>
        <div className="flex gap-1 border-b border-white/10">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'border-b-2 border-white text-white'
                  : 'text-white/45 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="mt-6">
          {activeTab === 'overview' && (
            <div className="card space-y-3 p-6">
              <h3 className="font-semibold text-white">Details</h3>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-white/45">Container ID</dt>
                  <dd className="font-mono text-white">{app.container_id || 'Not assigned'}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-white/45">Created</dt>
                  <dd className="text-white">{new Date(app.created_at).toLocaleString()}</dd>
                </div>
                {app.started_at && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-white/45">Started</dt>
                    <dd className="text-white">{new Date(app.started_at).toLocaleString()}</dd>
                  </div>
                )}
                {app.memory_limit && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-white/45">Memory limit</dt>
                    <dd className="text-white">{app.memory_limit}</dd>
                  </div>
                )}
                {app.ports && app.ports.length > 0 && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-white/45">Ports</dt>
                    <dd className="font-mono text-white">
                      {app.ports.map((p) => `${p.hostPort}:${p.containerPort}`).join(', ')}
                    </dd>
                  </div>
                )}
                {app.environment_vars && Object.keys(app.environment_vars).length > 0 && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-white/45">Environment</dt>
                    <dd className="font-mono text-xs text-white">
                      {Object.entries(app.environment_vars).map(([k, v]) => (
                        <div key={k}>{k}={String(v)}</div>
                      ))}
                    </dd>
                  </div>
                )}
                {app.volumes && app.volumes.length > 0 && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-white/45">Volumes</dt>
                    <dd className="font-mono text-xs text-white">
                      {app.volumes.map((vol, idx) => (
                        <div key={idx}>{vol.hostPath} → {vol.containerPath}</div>
                      ))}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {activeTab === 'logs' && (
            <LiveLogs
              appId={appId}
              logs={logs.map((log, idx) => ({
                id: String(log.id ?? idx),
                timestamp: log.created_at || log.timestamp || new Date().toISOString(),
                app: app.name,
                level: (log.level || 'INFO').toUpperCase(),
                message: log.message || String(log),
              }))}
            />
          )}

          {activeTab === 'config' && appId && (
            <div className="space-y-6">
              <ConfigEditor appId={appId} />
              <ConfigVersionControl appId={appId} />
            </div>
          )}

          {activeTab === 'deploy' && (
            <GitDeployManager />
          )}

          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <ServerOperationsHub app={app} onCloned={(clone) => navigate(`/apps/${clone.id}`)} />
              {appId && <DatabaseManager appId={appId} />}
              {appId && <ModpackBrowser appId={appId} />}
              <div className="card p-4"><AlertConfig /></div>
              <div className="card border-red-500/20 p-5">
                <h3 className="font-semibold text-white">Danger zone</h3>
                <p className="mt-1 text-sm text-white/45">Deleting removes the container and its configuration.</p>
                <button
                  onClick={handleDelete}
                  disabled={actionLoading}
                  className="secondary-button mt-4"
                >
                  Delete this app
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
