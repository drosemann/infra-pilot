import { GitDeployManager } from '../components/GitDeployManager';
import { PageHeader } from '../components/PageHeader';

export const Deployments = () => {
  return (
    <div className="mx-auto max-w-5xl space-y-8 px-2 py-8">
      <PageHeader eyebrow="Ship">
        <h1 className="text-4xl font-semibold tracking-tight text-white">Releases</h1>
        <p className="mt-2 text-white/55">
          Connect Git repositories to containers. Pushes deploy through the
          GitOps webhook with per-deployment history.
        </p>
      </PageHeader>

      <GitDeployManager />
    </div>
  );
};

export default Deployments;
