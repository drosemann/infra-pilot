import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  annotateResources,
  parseBlamePorcelain,
  resourceSpans,
  ZERO_COMMIT,
  type BlameLine,
} from '../../server/git-blame.ts';

const SHA_A = 'a'.repeat(40);
const SHA_B = 'b'.repeat(40);

const PORCELAIN = [
  `${SHA_A} 1 1 2`,
  'author Alice',
  'author-time 1700000000',
  'committer Alice',
  '\t- name: web',
  '\t  type: standard',
  `${SHA_B} 3 3 1`,
  'author Bob',
  'author-time not-a-number',
  '\t- name: db',
  `${ZERO_COMMIT} 4 4 1`,
  'author Alice',
  'author-time 0',
  '\t  memory: big',
].join('\n');

const CONFIG = [
  '# ipilot config',
  'spec:',
  '  servers:',
  '    - name: web',
  '      type: standard',
  "    - name: 'db'",
  '      type: standard',
  '  backups: []',
  '',
].join('\n');

describe('git-blame porcelain parsing', () => {
  it('attributes lines to commit, author, and time', () => {
    const blame = parseBlamePorcelain(PORCELAIN);
    assert.deepEqual(blame.get(1), { commit: SHA_A, author: 'Alice', authorTime: 1700000000 });
    assert.equal(blame.get(2)?.commit, SHA_A);
    assert.equal(blame.get(3)?.author, 'Bob');
  });

  it('falls back to zero time and unknown author', () => {
    const blame = parseBlamePorcelain(PORCELAIN);
    assert.equal(blame.get(3)?.authorTime, 0);
    const bare = parseBlamePorcelain(`${SHA_A} 1 1 1\n\t- name: web\n`);
    assert.equal(bare.get(1)?.author, 'unknown');
  });
});

describe('git-blame resource spans', () => {
  it('finds server entries and closes the block on a sibling key', () => {
    assert.deepEqual(resourceSpans(CONFIG), [
      { name: 'web', start: 4, end: 5 },
      { name: 'db', start: 6, end: 8 },
    ]);
  });

  it('returns no spans without a servers block', () => {
    assert.deepEqual(resourceSpans('spec:\n  backups: []\n'), []);
    assert.deepEqual(resourceSpans(''), []);
    assert.deepEqual(resourceSpans('spec:\n  servers: []\n  backups: []\n'), []);
  });
});

function line(commit: string, author: string, authorTime: number): BlameLine {
  return { commit, author, authorTime };
}

describe('git-blame annotation', () => {
  it('flags uncommitted lines and many hands on the newest line', () => {
    const nowMs = new Date('2024-06-01T00:00:00Z').getTime();
    const blame = new Map([
      [1, line(SHA_A, 'Alice', 1700000000)],
      [2, line(ZERO_COMMIT, 'Zed', 0)],
      [3, line(SHA_B, 'Bob', 1700000001)],
      [4, line(SHA_A, 'Cara', 1700000002)],
      [5, line(SHA_A, 'Dan', 1700000003)],
    ]);
    const [item] = annotateResources([{ name: 'web', start: 1, end: 5 }], blame, 180, nowMs);
    assert.equal(item.lastAuthor, 'Zed');
    assert.equal(item.lastChanged, 'uncommitted');
    assert.equal(item.lastCommit, 'uncommitted');
    assert.deepEqual(item.authors, ['Alice', 'Bob', 'Cara', 'Dan', 'Zed']);
    assert.deepEqual(item.risk, ['uncommitted', 'many-hands']);
  });

  it('flags stale authorship', () => {
    const nowMs = new Date('2024-06-01T00:00:00Z').getTime();
    const blame = new Map([[1, line(SHA_A, 'Alice', 1000000000)]]);
    const [item] = annotateResources([{ name: 'web', start: 1, end: 1 }], blame, 180, nowMs);
    assert.equal(item.lastChanged, '2001-09-09');
    assert.equal(item.lastCommit, SHA_A.slice(0, 7));
    assert.deepEqual(item.risk, ['stale']);
  });

  it('leaves fresh single-author resources clean', () => {
    const nowMs = new Date('2024-06-01T00:00:00Z').getTime();
    const fresh = Math.floor(nowMs / 1000) - 10;
    const blame = new Map([[1, line(SHA_A, 'Alice', fresh)]]);
    const [item] = annotateResources([{ name: 'web', start: 1, end: 1 }], blame, 180, nowMs);
    assert.deepEqual(item.risk, []);
  });

  it('marks spans without blame lines unknown', () => {
    const [item] = annotateResources([{ name: 'web', start: 1, end: 2 }], new Map());
    assert.equal(item.lastAuthor, 'unknown');
    assert.deepEqual(item.risk, ['unknown']);
  });
});
