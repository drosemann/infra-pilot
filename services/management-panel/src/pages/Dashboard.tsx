import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { apiClient } from "../lib/api";
import { DockerApp } from "../lib/types";
import { toast } from "sonner";
import { MetricCard } from "../components/MetricCard";
import { SystemOverview } from "../components/SystemOverview";
import { ResourceDistribution } from "../components/ResourceDistribution";
import { LiveLogs } from "../components/LiveLogs";
import { AppCard } from "../components/AppCard";

export const Dashboard = () => {
  const navigate = useNavigate();
  const [apps, setApps] = useState<DockerApp[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh twice a minute
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const appsData = await apiClient.listApps();
      setApps(appsData);
    } catch (error) {
      toast.error("Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApp = () => {
    navigate("/apps/new");
  };

  const runningApps = apps.filter((a) => a.status === "running").length;
  const attentionApps = apps.length - runningApps;

  return (
    <div className="mx-auto max-w-5xl space-y-12 px-2 py-8">
      <section>
        <p className="text-sm text-white/45">Overview</p>
        <h1 className="mt-2 max-w-2xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
          {apps.length === 0
            ? "Nothing deployed yet"
            : attentionApps === 0
              ? "All systems running"
              : `${attentionApps} ${attentionApps === 1 ? "app needs" : "apps need"} attention`}
        </h1>
        <p className="mt-3 max-w-xl text-base leading-7 text-white/55">
          {runningApps} of {apps.length}{" "}
          {apps.length === 1 ? "app" : "apps"} running.
        </p>
        <div className="mt-6">
          <button
            onClick={handleCreateApp}
            className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition-colors hover:bg-slate-200"
          >
            Deploy new app
          </button>
        </div>
      </section>

      <section>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <MetricCard label="Apps" value={apps.length} />
          <MetricCard label="Running" value={runningApps} />
          <MetricCard label="Needs attention" value={attentionApps} />
        </div>
      </section>

      {!loading && (
        <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 sm:p-6">
          <div className="mb-5">
            <h2 className="text-xl font-semibold tracking-tight text-white">
              Apps
            </h2>
          </div>

          {apps.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-white/15 bg-black/20 p-12 text-center">
              <p className="mb-4 text-white/55">No applications yet</p>
              <button
                onClick={handleCreateApp}
                className="rounded-full bg-white px-6 py-3 font-semibold text-black transition-colors hover:bg-slate-200"
              >
                Deploy new app
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {apps.map((app) => (
                <AppCard
                  key={app.id}
                  id={app.id}
                  name={app.name}
                  image={app.image}
                  status={app.status}
                  ports={app.ports}
                  onClick={() => navigate(`/apps/${app.id}`)}
                />
              ))}
            </div>
          )}
        </section>
      )}

      <section className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SystemOverview />
        </div>
        <div>
          <ResourceDistribution />
        </div>
      </section>

      <LiveLogs />
    </div>
  );
};
