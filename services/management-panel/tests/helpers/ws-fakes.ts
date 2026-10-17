/**
 * Test doubles for the WebSocket gateway.
 *
 * `FakeSocket` implements the gateway's `SocketLike` surface (sent frames are
 * captured as parsed objects), and `FakeChild` implements `ChildProcessLike`
 * for Docker log/metrics streams. `makeSpawnQueue` returns a `SpawnFn` that
 * hands out queued children, recording every invocation.
 */
import { EventEmitter } from 'node:events';
import type { IncomingMessage } from 'node:http';
import type { ChildProcessLike, SocketLike, SpawnFn } from '../../server/ws/index.ts';

export class FakeSocket implements SocketLike {
  readyState = 1;
  bufferedAmount = 0;
  sent: any[] = [];
  closed = false;
  closeCode: number | undefined;
  closeReason: string | undefined;
  terminated = false;
  pings = 0;
  private readonly emitter = new EventEmitter();

  send(data: string): void {
    this.sent.push(JSON.parse(data));
  }

  close(code?: number, reason?: string): void {
    if (this.closed) return;
    this.closed = true;
    this.closeCode = code;
    this.closeReason = reason;
    this.readyState = 3;
    this.emitter.emit('close');
  }

  terminate(): void {
    this.terminated = true;
    this.readyState = 3;
    this.emitter.emit('close');
  }

  ping(): void {
    this.pings += 1;
  }

  on(event: string, listener: (...args: any[]) => void): this {
    this.emitter.on(event, listener);
    return this;
  }

  /** Test helper: deliver an inbound frame to the gateway. */
  receive(message: unknown): void {
    this.emitter.emit('message', Buffer.from(JSON.stringify(message)));
  }

  /** Test helper: deliver a raw (possibly invalid) frame. */
  receiveRaw(data: string): void {
    this.emitter.emit('message', Buffer.from(data));
  }

  /** Test helper: simulate a protocol-level pong. */
  pong(): void {
    this.emitter.emit('pong');
  }

  /** Test helper: simulate a client disconnect. */
  disconnect(): void {
    this.emitter.emit('close');
  }

  /** Test helper: all messages of a given type. */
  messagesOfType(type: string): any[] {
    return this.sent.filter((message) => message.type === type);
  }

  /** Test helper: the most recent message of a given type. */
  lastOfType(type: string): any | undefined {
    return this.messagesOfType(type).at(-1);
  }
}

export class FakeChild implements ChildProcessLike {
  stdout = new EventEmitter();
  stderr = new EventEmitter();
  killed = false;
  private readonly emitter = new EventEmitter();

  on(event: string, listener: (...args: any[]) => void): this {
    this.emitter.on(event, listener);
    return this;
  }

  kill(_signal?: NodeJS.Signals): boolean {
    this.killed = true;
    return true;
  }

  /** Test helper: emit stdout data, then close successfully. */
  emitStdout(data: string): void {
    this.stdout.emit('data', Buffer.from(data));
  }

  emitStderr(data: string): void {
    this.stderr.emit('data', Buffer.from(data));
  }

  emitClose(code = 0): void {
    this.emitter.emit('close', code);
  }

  emitError(message = 'spawn failed'): void {
    this.emitter.emit('error', new Error(message));
  }
}

export interface SpawnQueue {
  spawnFn: SpawnFn;
  children: FakeChild[];
  calls: Array<{ command: string; args: string[] }>;
}

/** Build a `SpawnFn` that returns a fresh `FakeChild` per call. */
export function makeSpawnQueue(): SpawnQueue {
  const children: FakeChild[] = [];
  const calls: Array<{ command: string; args: string[] }> = [];
  const spawnFn: SpawnFn = (command, args) => {
    calls.push({ command, args });
    const child = new FakeChild();
    children.push(child);
    return child;
  };
  return { spawnFn, children, calls };
}

/** Build a minimal fake `IncomingMessage` for `handleConnection`. */
export function makeRequest(url: string, ip = '127.0.0.1'): IncomingMessage {
  return {
    url,
    headers: {},
    socket: { remoteAddress: ip },
  } as unknown as IncomingMessage;
}

/** Await one microtask turn plus timers, letting queued promises settle. */
export function flush(times = 5): Promise<void> {
  let chain = Promise.resolve();
  for (let i = 0; i < times; i += 1) chain = chain.then(() => undefined);
  return chain;
}

/** Wait until `predicate` is true or the timeout elapses. */
export async function waitFor(
  predicate: () => boolean,
  timeoutMs = 2000,
  intervalMs = 5,
): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return true;
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return predicate();
}
