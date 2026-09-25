"""P2 observability tests: security rejections are counted and exposed."""

import os
import unittest
from types import SimpleNamespace

from aiohttp.test_utils import TestClient, TestServer

import webhook_server
from webhook_server import build_webhook_app

BOT = SimpleNamespace(get_cog=lambda name: None)

_ENV_VARS = (
    "FEDERATION_API_TOKEN",
    "GITOPS_WEBHOOK_TOKEN",
    "GITHUB_WEBHOOK_SECRET",
    "NODE_ENV",
    "ENVIRONMENT",
    "ALLOW_INSECURE_FEDERATION",
)


class AuthObservabilityTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.saved = {key: os.environ.get(key) for key in _ENV_VARS}
        for key in _ENV_VARS:
            os.environ.pop(key, None)
        webhook_server.reset_auth_failure_counters()
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
        webhook_server.reset_auth_failure_counters()

    async def test_federation_401_is_counted(self):
        os.environ["FEDERATION_API_TOKEN"] = "secret"
        resp = await self.client.get(
            "/api/v1/federation/status",
            headers={"Authorization": "Bearer wrong"},
        )
        self.assertEqual(resp.status, 401)
        self.assertEqual(webhook_server._auth_failure_counters["federation_401"], 1)

    async def test_federation_503_is_counted(self):
        os.environ["NODE_ENV"] = "production"
        resp = await self.client.get("/api/v1/federation/status")
        self.assertEqual(resp.status, 503)
        self.assertEqual(webhook_server._auth_failure_counters["federation_503"], 1)

    async def test_webhook_401_is_counted(self):
        os.environ["GITOPS_WEBHOOK_TOKEN"] = "token"
        resp = await self.client.post(
            "/webhook/gitops",
            headers={"X-Timestamp": "1", "X-Signature-256": "sha256=bad"},
            json={"manifest": "x"},
        )
        self.assertEqual(resp.status, 401)
        self.assertGreaterEqual(
            webhook_server._auth_failure_counters["webhook_401"], 1
        )

    async def test_metrics_exposes_counters(self):
        os.environ["FEDERATION_API_TOKEN"] = "secret"
        await self.client.get(
            "/api/v1/federation/status",
            headers={"Authorization": "Bearer wrong"},
        )
        resp = await self.client.get("/metrics")
        self.assertEqual(resp.status, 200)
        text = await resp.text()
        self.assertIn("orchestrator_auth_failures_total", text)
        self.assertIn('outcome="federation_401"', text)


if __name__ == "__main__":
    unittest.main()
