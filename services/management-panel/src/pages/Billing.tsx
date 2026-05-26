import { BillingDashboard } from '../components/BillingDashboard';

export const BillingPage = () => {
  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Billing</h1>
          <p className="text-slate-400">Manage your prepaid balance and view billing details</p>
        </div>
      </div>
      <BillingDashboard />
    </div>
  );
};

export default BillingPage;
