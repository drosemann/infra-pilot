import { GitDeployManager } from '../components/GitDeployManager';
import { PageHeader } from '../components/PageHeader';

export const Deployments = () => {
  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Ship">
        <h1 className="text-3xl font-bold text-white mb-2">Deployments</h1>
        <p className="text-slate-400">
          Connect Git repositories to containers. Pushes deploy through the
          GitOps webhook with per-deployment history and enable/disable control.
        </p>
      </PageHeader>

      <GitDeployManager />
    </div>
  );
};

export default Deployments;
