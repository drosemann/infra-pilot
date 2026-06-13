import { promises as fs } from 'fs';
import path from 'path';

const ACTIVITY_FILE = path.resolve(process.cwd(), 'data', 'activity-feed.json');

export type ActivityEventType =
  | 'app:create' | 'app:update' | 'app:delete'
  | 'app:start' | 'app:stop' | 'app:restart'
  | 'backup:create' | 'backup:update' | 'backup:delete'
  | 'config:update' | 'deployment' | 'alert'
  | 'maintenance' | 'user:login' | 'user:logout'
  | 'database:create' | 'database:delete'
  | 'knowledge_base:create' | 'knowledge_base:update' | 'knowledge_base:delete';

export interface ActivityEvent {
  id: string;
  type: ActivityEventType;
  userId: string;
  userName?: string;
  description: string;
  metadata?: Record<string, any>;
  timestamp: string;
  severity: 'info' | 'warning' | 'error';
}

async function ensureFile() {
  await fs.mkdir(path.dirname(ACTIVITY_FILE), { recursive: true });
  try {
    await fs.access(ACTIVITY_FILE);
  } catch {
    await fs.writeFile(ACTIVITY_FILE, '[]', 'utf-8');
  }
}

async function readEvents(): Promise<ActivityEvent[]> {
  await ensureFile();
  try {
    const raw = await fs.readFile(ACTIVITY_FILE, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function writeEvents(events: ActivityEvent[]): Promise<void> {
  await ensureFile();
  await fs.writeFile(ACTIVITY_FILE, JSON.stringify(events, null, 2), 'utf-8');
}

export async function addEvent(event: Omit<ActivityEvent, 'id' | 'timestamp'>): Promise<ActivityEvent> {
  const events = await readEvents();
  const newEvent: ActivityEvent = {
    ...event,
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
  };
  events.unshift(newEvent);
  const maxEvents = 5000;
  if (events.length > maxEvents) {
    events.splice(maxEvents);
  }
  await writeEvents(events);
  return newEvent;
}

export async function getEvents(params: {
  limit?: number;
  offset?: number;
  type?: string;
  userId?: string;
  from?: string;
  to?: string;
}): Promise<{ events: ActivityEvent[]; total: number }> {
  let all = await readEvents();

  if (params.type) {
    all = all.filter(e => e.type === params.type);
  }
  if (params.userId) {
    all = all.filter(e => e.userId === params.userId);
  }
  if (params.from) {
    const from = new Date(params.from).getTime();
    all = all.filter(e => new Date(e.timestamp).getTime() >= from);
  }
  if (params.to) {
    const to = new Date(params.to).getTime();
    all = all.filter(e => new Date(e.timestamp).getTime() <= to);
  }

  const total = all.length;
  const limit = params.limit || 50;
  const offset = params.offset || 0;
  const events = all.slice(offset, offset + limit);

  return { events, total };
}

export async function getEvent(id: string): Promise<ActivityEvent | null> {
  const events = await readEvents();
  return events.find(e => e.id === id) || null;
}

export async function exportEvents(params: {
  format?: 'csv' | 'json';
  type?: string;
  userId?: string;
  from?: string;
  to?: string;
}): Promise<string> {
  const { events } = await getEvents({
    ...params,
    limit: 10000,
    offset: 0,
  });

  if (params.format === 'csv') {
    const header = 'id,type,userId,userName,description,severity,timestamp';
    const rows = events.map(e =>
      `"${e.id}","${e.type}","${e.userId}","${e.userName || ''}","${e.description.replace(/"/g, '""')}","${e.severity}","${e.timestamp}"`
    );
    return [header, ...rows].join('\n');
  }

  return JSON.stringify(events, null, 2);
}
