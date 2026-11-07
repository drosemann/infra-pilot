import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { cli, splitArgs } from '../../server/cli-bridge.ts';

describe('cli-bridge', () => {
  it('splits quoted arguments without a shell', () => {
    assert.deepEqual(splitArgs('server create "my server" --type "a b"'), [
      'server',
      'create',
      'my server',
      '--type',
      'a b',
    ]);
  });

  it('rejects empty commands without spawning', async () => {
    const result = await cli('');
    assert.equal(result.success, false);
    assert.equal(result.data, null);
  });
});
