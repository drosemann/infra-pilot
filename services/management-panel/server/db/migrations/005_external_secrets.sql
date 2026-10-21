-- ============================================================================
-- Phase 9: External secrets (server/secrets-external.ts)
-- ============================================================================
-- Optional per-secret external mode: a row with `external_ref` set holds
-- ONLY the Vault/AWS/Azure reference (e.g. vault://apps/app-1/db#password);
-- `value` is stored empty and versions are not written (no plaintext
-- duplication). Resolution happens at read time through the orchestrator
-- secrets API (POST /api/v1/secrets/get) with the panel's federation-token
-- credential and a short-lived in-process cache only.

ALTER TABLE secrets ADD COLUMN IF NOT EXISTS external_ref TEXT;
