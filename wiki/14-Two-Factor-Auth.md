# Two-Factor Authentication (TOTP + backup codes)

Infra Pilot uses TOTP (RFC 6238, 6 digits, 30-second step,
SHA-1) for the second login factor, plus single-use backup
codes for recovery. Tested with common auth apps (see below).

## Compatible auth apps (tested pattern)

Any standard TOTP app works — verified against the
`otpauth://totp/` URI + 6-digit flow:

| App | Platform | Notes |
| --- | -------- | ----- |
| Google Authenticator | Android / iOS | Scan QR or enter setup key |
| Microsoft Authenticator | Android / iOS | Same flow, cloud backup optional |
| Authy | Android / iOS / Desktop | Multi-device sync |
| 1Password | All | TOTP inside password item |
| Bitwarden | All | Authenticator field / mobile app |
| Aegis Authenticator | Android | Encrypted vault, FOSS |
| andOTP | Android | Encrypted backup, FOSS |

Contract: `secret` is Base32, `uri` is
`otpauth://totp/InfraPilot:<user>?secret=...&issuer=InfraPilot`,
codes are `^\d{6}$`, one code valid per 30 s window
(+/- 1 step clock skew on the backend).

## Setup flow (Settings page)

1. Open Settings → Two-Factor Authentication →
   Enable Two-Factor Authentication.
2. `POST /api/auth/2fa/setup` (authenticated) returns
   `{ secret, uri, qr_code_url }`.
3. Scan the QR code **or** enter the manual setup key.
4. Enter the current 6-digit code from the app.
   `POST /api/auth/2fa/verify-setup` confirms it.
5. Save the backup codes shown next
   (`GET /api/auth/2fa/backup-codes`). Each code works once.
   Copy or download them, store offline, then Finish.

Tips:

- If the code just rolled over, wait for the next 30 s code.
- The setup input accepts digits only, `inputMode="numeric"`,
  `autocomplete="one-time-code"` for mobile autofill.
- Time drift breaks TOTP: keep the phone clock automatic.

## Login flow

1. Normal login returns a temporary token when 2FA is active.
2. Enter the 6-digit app code:
   `POST /api/auth/2fa/verify`
   `{ temp_token, totp_code }` → `{ token }` (session).
3. No device at hand? Use a backup code instead:
   `POST /api/auth/2fa/verify-backup`
   `{ temp_token, backup_code }` → `{ token }`.
   The code is consumed on use.

Both verify endpoints are public by design (pre-auth login
step) and guarded by `loginLimiter` (rate limiting).
Setup / verify-setup / disable / backup-codes require an
authenticated session (`verifyAuth`).

## Backup codes

- Shown once after setup; fetch again via
  `GET /api/auth/2fa/backup-codes` (authenticated).
- Single-use, treat like passwords (offline store, no screenshots
  in cloud galleries).
- Lost device **and** lost codes = admin recovery via panel
  database / support process (see [08-Security](./08-Security.md)).

## Disable

Settings → active 2FA → confirm password → Disable.
`POST /api/auth/2fa/disable` (authenticated).
Disabling requires the account password, not just a session.

## Troubleshooting

| Problem | Fix |
| ------- | --- |
| Code always rejected | Phone clock off — enable automatic time; try the next 30 s code |
| QR won't scan | Enter the manual setup key (Base32) instead |
| Lost device, have codes | Login → use backup code via verify-backup |
| Lost device + codes | Contact admin; do not open a public issue with secrets |
| `502 Integration service unavailable` | Integration service (`:9000`) not running — start it / check `INTEGRATION_SERVICE_URL` |
| Repeated `429` | Rate limiter tripped — wait, then retry once per code window |

## Test coverage

- `services/management-panel/tests/unit/two-factor-auth-flow.test.ts`:
  setup → verify → verify-backup → disable → backup codes,
  error paths, and the 6-digit TOTP contract.
- `services/management-panel/tests/integration/api.test.ts`:
  setup/verify-setup/disable/backup-codes require auth (`401`
  without token); verify/verify-backup stay public pre-auth
  (never `404`/`401`, rate-limited).
- Manual checklist before release: set up with two different
  apps (e.g. Google Authenticator + Bitwarden), log in with a
  TOTP code, log in with a backup code, disable with password.
