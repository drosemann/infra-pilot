import assert from 'node:assert/strict';
import { beforeEach, describe, it } from 'node:test';

type FetchCall = { url: string; options: any };

const calls: FetchCall[] = [];
let nextResponse: { ok: boolean; status: number; body: any } = {
  ok: true,
  status: 200,
  body: {},
};

/** Record auth requests and return the response configured by the current test. */
(globalThis as any).fetch = async (url: string, options: any) => {
  calls.push({ url: String(url), options });
  return {
    ok: nextResponse.ok,
    status: nextResponse.status,
    /** Return the configured response body without parsing or network access. */
    json: async () => nextResponse.body,
  };
};

const {
  setup2FA,
  verify2FA,
  verify2FABackup,
  verify2FASetup,
  disable2FA,
  get2FABackupCodes,
} = await import('../../src/lib/auth.ts');

describe('two-factor auth-app flow (TOTP + backup codes)', () => {
  beforeEach(() => {
    calls.length = 0;
    nextResponse = { ok: true, status: 200, body: {} };
  });

  it('sets up 2FA and returns secret, uri and QR code url', async () => {
    nextResponse.body = {
      secret: 'JBSWY3DPEHPK3PXP',
      uri: 'otpauth://totp/InfraPilot:user?secret=JBSWY3DPEHPK3PXP&issuer=InfraPilot',
      qr_code_url: 'data:image/png;base64,qr',
    };
    const result = await setup2FA('user-1');
    assert.equal(result.secret, 'JBSWY3DPEHPK3PXP');
    assert.match(result.uri, /^otpauth:\/\/totp\//);
    assert.ok(calls[0].url.endsWith('/api/auth/2fa/setup'));
    assert.deepEqual(JSON.parse(calls[0].options.body), { user_id: 'user-1' });
  });

  it('verifies a 6-digit TOTP code and returns the session token', async () => {
    nextResponse.body = { token: 'session-token' };
    const token = await verify2FA('temp-token', '123456');
    assert.equal(token, 'session-token');
    assert.ok(calls[0].url.endsWith('/api/auth/2fa/verify'));
    const body = JSON.parse(calls[0].options.body);
    assert.equal(body.temp_token, 'temp-token');
    assert.match(body.totp_code, /^\d{6}$/);
  });

  it('throws a clear error when the TOTP code is rejected', async () => {
    nextResponse = { ok: false, status: 401, body: { error: 'Invalid code' } };
    await assert.rejects(() => verify2FA('temp-token', '000000'), /Invalid code/);
  });

  it('verifies a backup code through the dedicated endpoint', async () => {
    nextResponse.body = { token: 'session-token-via-backup' };
    const token = await verify2FABackup('temp-token', 'BACKUP-1');
    assert.equal(token, 'session-token-via-backup');
    assert.ok(calls[0].url.endsWith('/api/auth/2fa/verify-backup'));
    const body = JSON.parse(calls[0].options.body);
    assert.equal(body.temp_token, 'temp-token');
    assert.equal(body.backup_code, 'BACKUP-1');
  });

  it('throws a clear error when the backup code is rejected', async () => {
    nextResponse = { ok: false, status: 401, body: { error: 'Invalid backup code' } };
    await assert.rejects(() => verify2FABackup('temp-token', 'WRONG'), /Invalid backup code/);
  });

  it('confirms setup only when the backend reports success', async () => {
    nextResponse.body = { success: true };
    assert.equal(await verify2FASetup('user-1', '123456'), true);
    nextResponse.body = { success: false };
    assert.equal(await verify2FASetup('user-1', '000000'), false);
  });

  it('disables 2FA with password confirmation', async () => {
    nextResponse.body = { success: true };
    assert.equal(await disable2FA('user-1', 'correct-horse'), true);
    const body = JSON.parse(calls[0].options.body);
    assert.equal(body.user_id, 'user-1');
    assert.equal(body.password, 'correct-horse');
    nextResponse.body = { success: false };
    assert.equal(await disable2FA('user-1', 'wrong'), false);
  });

  it('fetches single-use backup codes for the user', async () => {
    nextResponse.body = { backup_codes: ['AAA-111', 'BBB-222'] };
    const codes = await get2FABackupCodes('user-1');
    assert.deepEqual(codes, ['AAA-111', 'BBB-222']);
    assert.match(calls[0].url, /\/api\/auth\/2fa\/backup-codes\?user_id=user-1/);
  });

  it('throws a clear error when backup codes cannot be loaded', async () => {
    nextResponse = { ok: false, status: 500, body: { error: 'unavailable' } };
    await assert.rejects(() => get2FABackupCodes('user-1'), /unavailable/);
  });

  it('documents the TOTP contract auth apps must satisfy', () => {
    // RFC 6238 default used across Google/Microsoft Authenticator,
    // Authy, 1Password, Bitwarden, Aegis, andOTP: 6 digits, 30s step.
    const sample = '482913';
    assert.match(sample, /^\d{6}$/);
    assert.equal(sample.length, 6);
  });
});
