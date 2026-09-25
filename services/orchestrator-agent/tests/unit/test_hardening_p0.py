"""P0 hardening regression tests: manifest strict validation, spawn
validation, bounded bodies and wired rate limiting."""

import os
import unittest
from types import SimpleNamespace

import pytest
from aiohttp.test_utils import TestClient, TestServer
from manifest.schema import InfraFile

BOT = SimpleNamespace(get_cog=lambda name: None)


def _manifest(**overrides):
    instance = {
        "name": "web-01",
        "provider": "docker",
        "image": "nginx:1.25",
        "cpu": 1.0,
        "memory_mb": 512,
        "storage_gb": 10,
    }
    instance.update(overrides)
    return {
        "api_version": "v1",
        "kind": "InfraFile",
        "metadata": {"name": "test"},
        "spec": {"instances": [instance]},
    }


class StrictManifestTest(unittest.TestCase):
    def test_valid_manifest_passes_strict(self):
        InfraFile.from_dict(_manifest()).validate(strict=True)

    def test_privileged_host_port_rejected_in_strict(self):
        infra = InfraFile.from_dict(_manifest(ports={"80/tcp": "80"}))
        with pytest.raises(ValueError):
            infra.validate(strict=True)

    def test_privileged_host_port_allowed_lenient(self):
        # from_dict stays lenient; only the API path enforces strict.
        infra = InfraFile.from_dict(_manifest(ports={"80/tcp": "80"}))
        infra.validate(strict=False)

    def test_denied_env_rejected(self):
        infra = InfraFile.from_dict(_manifest(env={"LD_PRELOAD": "/tmp/x.so"}))
        with pytest.raises(ValueError):
            infra.validate(strict=True)

    def test_bad_image_rejected(self):
        infra = InfraFile.from_dict(_manifest(image="evil; rm -rf /"))
        with pytest.raises(ValueError):
            infra.validate(strict=True)

    def test_oversized_manifest_rejected(self):
        env = {f"VAR_{i}": "x" for i in range(200)}
        infra = InfraFile.from_dict(_manifest(env=env))
        with pytest.raises(ValueError):
            infra.validate(strict=True)


class SpawnValidationTest(unittest.TestCase):
    def test_spawn_validators_accept_fixture(self):
        import vps_manager as vm

        cfg = SimpleNamespace(
            cpu_limit=1.5,
            memory_limit=512,
            storage_limit=20,
            image="ubuntu:22.04",
            ports={"22/tcp": "2222"},
            env_vars={"TOKEN": "redacted"},
        )
        vm._validate_spawn_config(cfg)

    def test_spawn_rejects_privileged_host_port(self):
        import vps_manager as vm

        cfg = SimpleNamespace(
            cpu_limit=1.0,
            memory_limit=512,
            storage_limit=10,
            image="nginx:1.25",
            ports={"80/tcp": "80"},
            env_vars={},
        )
        with pytest.raises(ValueError):
            vm._validate_spawn_config(cfg)

    def test_spawn_rejects_denied_env(self):
        import vps_manager as vm

        cfg = SimpleNamespace(
            cpu_limit=1.0,
            memory_limit=512,
            storage_limit=10,
            image="nginx:1.25",
            ports={},
            env_vars={"DOCKER_HOST": "tcp://evil:2375"},
        )
        with pytest.raises(ValueError):
            vm._validate_spawn_config(cfg)

    def test_spawn_rejects_bad_image(self):
        import vps_manager as vm

        cfg = SimpleNamespace(
            cpu_limit=1.0,
            memory_limit=512,
            storage_limit=10,
            image="evil image;curl",
            ports={},
            env_vars={},
        )
        with pytest.raises(ValueError):
            vm._validate_spawn_config(cfg)


class BoundedBodyAndRateLimitTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.saved = {
            k: os.environ.get(k)
            for k in ("FEDERATION_API_TOKEN", "GITOPS_WEBHOOK_TOKEN")
        }
        os.environ["FEDERATION_API_TOKEN"] = "test-federation-token"
        os.environ["GITOPS_WEBHOOK_TOKEN"] = "test-gitops-token"
        from webhook_server import build_webhook_app

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

    async def test_oversized_content_length_rejected(self):
        resp = await self.client.post(
            "/api/v1/deployments",
            headers={
                "Authorization": "Bearer test-federation-token",
                "Content-Length": str(10 * 1024 * 1024),
            },
            data='{"manifest": {}}',
        )
        self.assertIn(resp.status, (400, 413))

    async def test_strict_manifest_rejects_privileged_port_via_api(self):
        resp = await self.client.post(
            "/api/v1/deployments",
            headers={"Authorization": "Bearer test-federation-token"},
            json={
                "manifest": _manifest(ports={"80/tcp": "80"}),
                "as_platform_admin": True,
            },
        )
        self.assertEqual(resp.status, 400)

    async def test_rate_limit_trips_on_webhook(self):
        # Webhook rule allows 60 POSTs/min per IP; 70 rapid calls must trip it.
        statuses = set()
        for _ in range(70):
            resp = await self.client.post(
                "/webhook/gitops",
                headers={"X-Timestamp": "1", "X-Signature-256": "sha256=bad"},
                json={"manifest": "x"},
            )
            statuses.add(resp.status)
        self.assertIn(429, statuses)


if __name__ == "__main__":
    unittest.main()
