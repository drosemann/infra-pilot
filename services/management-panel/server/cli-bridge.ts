/**
 * @file CLI Bridge for the Management Panel.
 * Invokes `ipilot` CLI commands via subprocess and returns parsed JSON,
 * avoiding duplication of business logic in Express route handlers.
 *
 * Usage: import { cli } from './cli-bridge.js';
 *   const servers = await cli('server list --output json');
 */

import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

/** @constant {string} */
const IPILOT_CMD = process.env.IPILOT_CMD || 'ipilot';
/** @constant {number} */
const CLI_TIMEOUT_MS = 30000;

/**
 * Result of a CLI command execution.
 */
export interface CliResult {
  success: boolean;
  data: any;
  error?: string;
}

/**
 * Split a command string on whitespace, honouring double quotes.
 * Avoids spawning a shell, so arguments cannot be shell-injected.
 */
export function splitArgs(command: string): string[] {
  const args: string[] = [];
  const re = /"([^"]*)"|(\S+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(command)) !== null) args.push(m[1] ?? m[2]);
  return args;
}

/**
 * Execute an ipilot CLI command and return parsed JSON.
 * The command string should NOT include --output json (it is added automatically).
 * Async: never blocks the Node event loop while the child runs.
 * @param command - The ipilot subcommand to run (e.g. 'server list')
 * @returns Parsed result with success flag
 */
export async function cli(command: string): Promise<CliResult> {
  if (!command || typeof command !== 'string') {
    return { success: false, data: null, error: 'Command must be a non-empty string' };
  }

  try {
    const { stdout } = await execFileAsync(IPILOT_CMD, [...splitArgs(command), '--output', 'json'], {
      encoding: 'utf-8',
      timeout: CLI_TIMEOUT_MS,
      windowsHide: true,
    });
    return { success: true, data: JSON.parse((stdout as string).trim()) };
  } catch (err: any) {
    const message = err.stderr?.toString() || err.message || String(err);
    if (err.stdout) {
      try {
        return { success: true, data: JSON.parse(err.stdout.toString().trim()) };
      } catch {
        // stdout is not valid JSON; fall through to error path
      }
    }
    return { success: false, data: null, error: message };
  }
}

/**
 * Convenience wrappers for common ipilot operations.
 */
export const ipilot = {
  server: {
    /** @returns {Promise<CliResult>} */
    list: () => cli('server list'),
    /** @param name @param type @param [memory] @returns {Promise<CliResult>} */
    create: (name: string, type: string, memory?: number) =>
      cli(`server create "${name}" --type "${type}"${memory ? ` --memory ${memory}` : ''}`),
    /** @param serverId @returns {Promise<CliResult>} */
    delete: (serverId: string) => cli(`server delete "${serverId}"`),
    /** @param serverId @returns {Promise<CliResult>} */
    status: (serverId: string) => cli(`server status "${serverId}"`),
  },
  backup: {
    /** @param [serverId] @returns {Promise<CliResult>} */
    list: (serverId?: string) => cli(`backup list${serverId ? ` "${serverId}"` : ''}`),
    /** @param serverId @returns {Promise<CliResult>} */
    create: (serverId: string) => cli(`backup create "${serverId}"`),
  },
  logs: {
    /** @param serverId @param [lines] @returns {Promise<CliResult>} */
    fetch: (serverId: string, lines?: number) =>
      cli(`logs fetch "${serverId}"${lines ? ` --lines ${lines}` : ''}`),
  },
  edge: {
    /** @returns {Promise<CliResult>} */
    list: () => cli('edge list'),
    /** @param name @param type @param hardwareId @returns {Promise<CliResult>} */
    register: (name: string, type: string, hardwareId: string) =>
      cli(`edge register "${name}" "${type}" "${hardwareId}"`),
    /** @param deviceId @returns {Promise<CliResult>} */
    status: (deviceId: string) => cli(`edge status "${deviceId}"`),
  },
  health: {
    /** @returns {Promise<CliResult>} */
    check: () => cli('health'),
  },
  config: {
    /** @param [key] @returns {Promise<CliResult>} */
    get: (key?: string) => cli(`config get${key ? ` ${key}` : ''}`),
    /** @param key @param value @returns {Promise<CliResult>} */
    set: (key: string, value: string) => cli(`config set ${key} "${value}"`),
  },
};
