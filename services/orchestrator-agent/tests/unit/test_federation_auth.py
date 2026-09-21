"""Tests for the federation token middleware fail-closed behavior.

Regression coverage for the security pass: previously the middleware
allowed all requests when FEDERATION_API_TOKEN was not configured
(fail-open). In production it must refuse traffic instead.
"""

import os
import unittest
from types import SimpleNamespace

from aiohttp.test_utils import TestClient, TestServer
from webhook_server import build_webhook_app

BOT = SimpleNamespace(get_cog=lambda name: None)

# Ensure a clean baseline regardless of what other test modules set.
_ENV_VARS = (
    "FEDERATION_API_TOKEN",
    "NODE_ENV",
    "ENVIRONMENT",
    "ALLOW_INSECURE_FEDERATION",
)


class FederationTokenFailClosedTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.saved = {key: os.environ.get(key) for key in _ENV_VARS}
        for key in _ENV_VARS:
            os.environ.pop(key, None)
        self.app = await build_webhook_app(BOT)
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()
        self.addAsyncCleanup(self.client.close)

    async def asyncTearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    async def test_production_without_token_fails_closed(self):
        os.environ["NODE_ENV"] = "production"
        resp = await self.client.get("/api/v1/federation/status")
        self.assertEqual(resp.status, 503)
        body = await resp.json()
        self.assertEqual(body["error"], "auth not configured")

    async def test_production_without_token_rejects_rbac_mutations(self):
        os.environ["NODE_ENV"] = "production"
        resp = await self.client.post(
            "/api/v1/rbac/orgs", json={"name": "X", "owner_user_id": "u1"}
        )
        self.assertEqual(resp.status, 503)

    async def test_production_with_valid_token_allowed(self):
        os.environ["NODE_ENV"] = "production"
        os.environ["FEDERATION_API_TOKEN"] = "prod-secret"
        resp = await self.client.get(
            "/api/v1/federation/status",
            headers={"Authorization": "Bearer prod-secret"},
        )
        self.assertEqual(resp.status, 200)

    async def test_configured_token_is_trimmed_for_authentication(self):
        os.environ["NODE_ENV"] = "production"
        os.environ["FEDERATION_API_TOKEN"] = "  prod-secret\t"
        resp = await self.client.get(
            "/api/v1/federation/status",
            headers={"Authorization": "Bearer prod-secret"},
        )
        self.assertEqual(resp.status, 200)

    async def test_production_with_invalid_token_rejected(self):
        os.environ["NODE_ENV"] = "production"
        os.environ["FEDERATION_API_TOKEN"] = "prod-secret"
        resp = await self.client.get(
            "/api/v1/federation/status",
            headers={"Authorization": "Bearer wrong"},
        )
        self.assertEqual(resp.status, 401)

    async def test_development_without_token_allows_with_warning(self):
        os.environ["ALLOW_INSECURE_FEDERATION"] = "true"
        os.environ["NODE_ENV"] = "development"
        resp = await self.client.get("/api/v1/federation/status")
        self.assertEqual(resp.status, 200)

    async def test_blank_node_env_falls_back_to_environment(self):
        os.environ["ALLOW_INSECURE_FEDERATION"] = "true"
        os.environ["NODE_ENV"] = "   "
        os.environ["ENVIRONMENT"] = " Local "
        resp = await self.client.get("/api/v1/federation/status")
        self.assertEqual(resp.status, 200)

    async def test_insecure_bypass_rejected_outside_local_development(self):
        os.environ["ALLOW_INSECURE_FEDERATION"] = "true"
        for environment in ("", "staging", "test", "production", "unknown"):
            with self.subTest(environment=environment):
                os.environ["NODE_ENV"] = environment
                os.environ.pop("ENVIRONMENT", None)
                resp = await self.client.get("/api/v1/federation/status")
                self.assertEqual(resp.status, 503)

    async def test_whitespace_only_token_is_rejected(self):
        os.environ["FEDERATION_API_TOKEN"] = "   "
        resp = await self.client.get(
            "/api/v1/federation/status",
            headers={"Authorization": "Bearer    "},
        )
        self.assertEqual(resp.status, 503)

    async def test_development_without_token_without_flag_fails_closed(self):
        # Fail-closed even in development unless explicitly allowed
        resp = await self.client.get("/api/v1/federation/status")
        self.assertEqual(resp.status, 503)

    async def test_health_endpoint_never_requires_token(self):
        os.environ["NODE_ENV"] = "production"
        resp = await self.client.get("/health")
        self.assertEqual(resp.status, 200)


if __name__ == "__main__":
    unittest.main()
