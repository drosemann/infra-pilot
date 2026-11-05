import { AccessLogViewer } from '../components/AccessLogViewer';
import { PageHeader } from '../components/PageHeader';

export const AccessLogs = () => {
  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader eyebrow="Review">
        <h1 className="text-4xl font-semibold tracking-tight text-white">Access Logs</h1>
        <p className="mt-2 text-white/55">SSH logins, console access, and authentication events.</p>
      </PageHeader>

      <div className="card p-4">
        <AccessLogViewer />
      </div>
    </div>
  );
};

export default AccessLogs;
