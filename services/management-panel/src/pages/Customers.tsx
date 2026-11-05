import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { Customer } from '../lib/types';
import { useConfig } from '../lib/types';
import { toast } from 'sonner';
import { PageHeader } from '../components/PageHeader';

export const Customers = () => {
  const { mode } = useConfig();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [editing, setEditing] = useState<{ id: string; name: string; email?: string } | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [seedModalOpen, setSeedModalOpen] = useState(false);
  const [seedInProgress, setSeedInProgress] = useState(false);

  useEffect(() => {
    if (mode === 'business') {
      loadCustomers();
    } else {
      setLoading(false);
    }
  }, [mode]);

  const loadCustomers = async () => {
    try {
      const data = await apiClient.getCustomers();
      setCustomers(data);
    } catch {
      // ignore errors in MVP UI
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    try {
      const c = await apiClient.createCustomer({ name, email } as Partial<Customer>);
      setCustomers((prev) => [c, ...prev]);
      setName('');
      setEmail('');
      toast.success('Customer created');
    } catch {
      toast.error('Failed to create customer');
    }
  };

  if (mode === 'personal') {
    return (
      <div className="mx-auto max-w-5xl px-2 py-8">
        <div className="card border-red-500/20 p-5">
          <p className="text-white/70">Customers are only available in Business Mode.</p>
        </div>
      </div>
    );
  }

  const openEditModal = (c: Customer) => {
    setEditing({ id: c.id, name: c.name, email: c.email });
    setShowModal(true);
  };

  // Feature flag: enable Seed Demo only in environments where it's intended
  const DEMO_FEATURE_ENABLED = (() => {
    try {
      return (import.meta && (import.meta as any).env && (import.meta as any).env.VITE_DEMO_FEATURE_ENABLED === 'true');
    } catch {
      return false;
    }
  })();

  const handleSeedDemo = async () => {
    try {
      setSeedInProgress(true);
      const res = await apiClient.seedDemo();
      const seededCustomers = res?.customersSeeded ?? 0;
      const seededApps = res?.appsSeeded ?? 0;
      toast.success(`Seeded ${seededCustomers} customers and ${seededApps} apps`);
      await loadCustomers();
    } catch {
      toast.error('Seed Demo failed');
    } finally {
      setSeedInProgress(false);
      setSeedModalOpen(false);
    }
  };

  const handleEditSubmit = async () => {
    if (!editing?.id) return;
    try {
      const { id, name, email } = editing;
      await apiClient.updateCustomer(id, { name, email });
      setCustomers((arr) => arr.map((x) => (x.id === id ? { ...x, name, email } : x)));
      setShowModal(false);
      setEditing(null);
      toast.success('Customer updated');
    } catch {
      toast.error('Failed to update customer');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this customer?')) return;
    try {
      await apiClient.deleteCustomer(id);
      setCustomers((arr) => arr.filter((c) => c.id !== id));
      toast.success('Customer deleted');
    } catch {
      toast.error('Failed to delete customer');
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-2 py-8">
      <PageHeader
        eyebrow="Manage"
        actions={
          DEMO_FEATURE_ENABLED ? (
            <button onClick={() => setSeedModalOpen(true)} className="secondary-button" title="Seed demo data">
              Seed Demo
            </button>
          ) : undefined
        }
      >
        <h1 className="text-4xl font-semibold tracking-tight text-white">Customers</h1>
        <p className="mt-2 text-white/55">{customers.length} {customers.length === 1 ? 'customer' : 'customers'}.</p>
      </PageHeader>

      <form onSubmit={handleCreate} className="flex flex-wrap gap-2" aria-label="Create customer">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" className="input-field flex-1" />
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="input-field flex-1" />
        <button type="submit" className="primary-button">Add</button>
      </form>

      {loading ? (
        <p className="text-white/45">Loading customersâ€¦</p>
      ) : customers.length === 0 ? (
        <div className="card p-12 text-center">
          <p className="text-white/55">No customers yet. Add the first one above.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {customers.map((c) => (
            <div key={c.id} className="card flex items-center justify-between gap-4 p-4">
              <div className="min-w-0">
                <p className="truncate font-medium text-white">{c.name}</p>
                <p className="truncate text-sm text-white/45">{c.email ?? 'No email'}</p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="hidden text-xs text-white/35 sm:block">
                  {c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}
                </span>
                <button className="text-sm text-white/60 hover:text-white" onClick={() => openEditModal(c)}>
                  Edit
                </button>
                <button className="text-sm text-red-400/80 hover:text-red-400" onClick={() => handleDelete(c.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="glass-sheet w-full max-w-md p-6">
            <h3 className="mb-4 text-lg font-semibold text-white">Edit Customer</h3>
            <div className="mb-4 grid gap-2">
              <input className="input-field w-full" value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} placeholder="Name" />
              <input className="input-field w-full" value={editing.email ?? ''} onChange={(e) => setEditing({ ...editing, email: e.target.value })} placeholder="Email" />
            </div>
            <div className="flex justify-end gap-2">
              <button className="secondary-button" onClick={() => { setShowModal(false); setEditing(null); }}>Cancel</button>
              <button className="primary-button" onClick={handleEditSubmit}>Save</button>
            </div>
          </div>
        </div>
      )}

      {seedModalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
          <div className="glass-sheet w-full max-w-md p-6">
            <h3 className="mb-2 text-lg font-semibold text-white">Seed Demo Data</h3>
            <p className="mb-4 text-sm text-white/55">
              This will seed sample customers and apps for a quick local demo. Safe and idempotent.
            </p>
            <div className="flex justify-end gap-2">
              <button className="secondary-button" onClick={() => setSeedModalOpen(false)} disabled={seedInProgress}>
                Cancel
              </button>
              <button className="primary-button" onClick={handleSeedDemo} disabled={seedInProgress}>
                {seedInProgress ? 'Seedingâ€¦' : 'Seed Demo'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;
