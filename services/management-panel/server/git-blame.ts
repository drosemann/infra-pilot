/**
 * Blame-aware GitOps for the management panel.
 * Pure helpers (unit-tested): parse `git blame --line-porcelain`, locate
 * `- name:` server entries in an ipilot YAML config, and annotate each
 * resource with its last author, change date, and ownership risk flags.
 * The Express route in index.ts shells out to git; everything else lives here.
 */

export interface BlameLine {
  commit: string;
  author: string;
  authorTime: number;
}

export interface ResourceSpan {
  name: string;
  /** 1-based inclusive first line of the resource block. */
  start: number;
  /** 1-based inclusive last line of the resource block. */
  end: number;
}

export interface BlameAnnotation extends ResourceSpan {
  lastAuthor: string;
  /** Short (7-char) commit sha, or 'uncommitted'. */
  lastCommit: string;
  /** ISO date of the last change, 'uncommitted', or '-' when unknown. */
  lastChanged: string;
  authors: string[];
  /** Subset of 'uncommitted' | 'stale' | 'many-hands' | 'unknown'. */
  risk: string[];
}

export const ZERO_COMMIT = '0'.repeat(40);

function isHex(value: string): boolean {
  return value.length === 40 && /^[0-9a-f]+$/.test(value);
}

/** Parse `git blame --line-porcelain` into 1-based line attributions. */
export function parseBlamePorcelain(output: string): Map<number, BlameLine> {
  const blame = new Map<number, BlameLine>();
  let commit = '';
  let author = '';
  let authorTime = 0;
  let lineno = 0;
  for (const raw of output.split('\n')) {
    const line = raw.endsWith('\r') ? raw.slice(0, -1) : raw;
    if (line.startsWith('\t')) {
      lineno += 1;
      blame.set(lineno, { commit, author: author || 'unknown', authorTime });
    } else if (line.startsWith('author ')) {
      author = line.slice('author '.length);
    } else if (line.startsWith('author-time ')) {
      const parsed = Number.parseInt(line.slice('author-time '.length), 10);
      authorTime = Number.isNaN(parsed) ? 0 : parsed;
    } else {
      const head = line.split(/\s+/)[0] || '';
      if (isHex(head)) {
        commit = head;
        author = '';
        authorTime = 0;
      }
    }
  }
  return blame;
}

/**
 * Find `- name:` items under `servers:` as (name, start, end) spans.
 * Lines are 1-based and inclusive. Only the first `servers:` block is
 * tracked; leaving its indent level closes the block.
 */
export function resourceSpans(text: string): ResourceSpan[] {
  const lines = text.split('\n');
  if (lines.at(-1) === '') lines.pop();
  const spans: ResourceSpan[] = [];
  let serversIndent: number | null = null;
  let itemIndent: number | null = null;
  let pendingName = '';
  let pendingStart = 0;
  const closePending = (end: number) => {
    if (pendingName) spans.push({ name: pendingName, start: pendingStart, end });
    pendingName = '';
  };
  for (const [i, raw] of lines.entries()) {
    const idx = i + 1;
    const stripped = raw.trim();
    if (!stripped || stripped.startsWith('#')) continue;
    const indent = raw.length - raw.trimStart().length;
    if (serversIndent === null) {
      if (/^servers\s*:/.test(stripped)) {
        serversIndent = indent;
        if (/^servers\s*:\s*\[\s*\]/.test(stripped)) break;
      }
      continue;
    }
    const isItem = /^-(?:\s|$)/.test(stripped);
    if (indent < serversIndent || (indent === serversIndent && !isItem)) {
      closePending(idx - 1);
      break;
    }
    if (isItem && itemIndent === null) itemIndent = indent;
    let nameLine: string;
    if (isItem && indent === itemIndent) {
      closePending(idx - 1);
      pendingStart = idx;
      nameLine = stripped.slice(1).trim();
    } else if (itemIndent !== null && indent === itemIndent + 2) {
      nameLine = stripped;
    } else {
      continue;
    }
    const match = /^name\s*:\s*(.*)/.exec(nameLine);
    if (match && !pendingName) {
      const value = match[1].trim();
      if (value.startsWith("'") || value.startsWith('"')) {
        const end = value.indexOf(value[0], 1);
        pendingName = end === -1 ? value : value.slice(1, end);
      } else {
        pendingName = value.split(/\s+#/, 1)[0].trim();
      }
    }
  }
  closePending(lines.length);
  return spans;
}

/** Attribute each resource span to authors and flag risky ownership. */
export function annotateResources(
  spans: ResourceSpan[],
  blame: Map<number, BlameLine>,
  staleDays = 180,
  nowMs: number = Date.now(),
): BlameAnnotation[] {
  const nowSec = Math.floor(nowMs / 1000);
  const staleAfter = staleDays * 86400;
  return spans.map((span) => {
    const nums: number[] = [];
    for (let n = span.start; n <= span.end; n += 1) {
      if (blame.has(n)) nums.push(n);
    }
    if (nums.length === 0) {
      return { ...span, lastAuthor: 'unknown', lastCommit: '-', lastChanged: '-', authors: [], risk: ['unknown'] };
    }
    const authors = [...new Set(nums.map((n) => (blame.get(n) as BlameLine).author))].sort();
    const recency = (n: number) => {
      const entry = blame.get(n) as BlameLine;
      return entry.commit === ZERO_COMMIT ? nowSec : entry.authorTime;
    };
    let newestNum = nums[0];
    for (const n of nums) {
      if (recency(n) > recency(newestNum)) newestNum = n;
    }
    const newest = blame.get(newestNum) as BlameLine;
    const risk: string[] = [];
    if (nums.some((n) => (blame.get(n) as BlameLine).commit === ZERO_COMMIT)) {
      risk.push('uncommitted');
    } else if (recency(newestNum) < nowSec - staleAfter) {
      risk.push('stale');
    }
    if (authors.length > 3) risk.push('many-hands');
    return {
      ...span,
      lastAuthor: newest.author,
      lastCommit: newest.commit === ZERO_COMMIT ? 'uncommitted' : newest.commit.slice(0, 7),
      lastChanged:
        newest.commit === ZERO_COMMIT
          ? 'uncommitted'
          : new Date(newest.authorTime * 1000).toISOString().slice(0, 10),
      authors,
      risk,
    };
  });
}
