import { EventEmitter } from 'events';

export interface BatchJob {
  batchId: string;
  action: string;
  userId: string;
  itemIds: string[];
  params: any;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'rolled_back';
  progress: Record<string, { status: string; progress: number }>;
  results: Record<string, any>;
  errors: Record<string, string>;
  timestamp: string;
}

class BulkOperationEngine extends EventEmitter {
  private jobs: Map<string, BatchJob> = new Map();
  private history: BatchJob[] = [];

  async execute(action: string, userId: string, itemIds: string[], params: any): Promise<BatchJob> {
    const batchId = crypto.randomUUID();
    const progress: Record<string, { status: string; progress: number }> = {};
    itemIds.forEach((id) => {
      progress[id] = { status: 'pending', progress: 0 };
    });

    const job: BatchJob = {
      batchId,
      action,
      userId,
      itemIds,
      params,
      status: 'running',
      progress,
      results: {},
      errors: {},
      timestamp: new Date().toISOString(),
    };

    this.jobs.set(batchId, job);
    this.emit('job:start', job);

    // Simulate processing each item
    for (const id of itemIds) {
      try {
        job.progress[id] = { status: 'processing', progress: 50 };
        this.emit('progress', job);

        // Simulate work
        await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1000));

        job.results[id] = { success: true, action };
        job.progress[id] = { status: 'completed', progress: 100 };
      } catch (err: any) {
        job.errors[id] = err.message || 'Unknown error';
        job.progress[id] = { status: 'failed', progress: 0 };
      }
      this.emit('progress', job);
    }

    const hasErrors = Object.keys(job.errors).length > 0;
    job.status = hasErrors ? 'failed' : 'completed';
    this.emit('job:complete', job);

    this.history.unshift(job);
    if (this.history.length > 50) this.history.pop();

    return job;
  }

  async getStatus(batchId: string): Promise<BatchJob | undefined> {
    return this.jobs.get(batchId);
  }

  async undo(batchId: string): Promise<boolean> {
    const job = this.jobs.get(batchId);
    if (!job || job.status === 'rolled_back') return false;

    // Simulate rollback
    for (const id of job.itemIds) {
      if (job.results[id]) {
        await new Promise((resolve) => setTimeout(resolve, 200));
        job.progress[id] = { status: 'rolled_back', progress: 0 };
      }
    }

    job.status = 'rolled_back';
    this.emit('job:rollback', job);
    return true;
  }

  getHistory(): BatchJob[] {
    return this.history;
  }
}

export const bulkEngine = new BulkOperationEngine();
