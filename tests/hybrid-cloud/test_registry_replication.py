import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from registry_replication import RegistryReplication

@pytest.fixture
def reg():
    r = RegistryReplication({})
    r.initialize()
    yield r
    r.close()

class TestRegistryReplication:
    def test_list_images_empty(self, reg):
        assert reg.list_images() == []

    def test_register_image(self, reg):
        img = reg.register_image(name="nginx", registry="docker_hub", repository="library/nginx")
        assert img.id is not None
        assert img.vulnerability_count == 0

    def test_scan_image(self, reg):
        img = reg.register_image("nginx", "docker_hub", "library/nginx")
        result = reg.scan_image(img.id)
        assert "vulnerability_count" in result

    def test_scan_nonexistent(self, reg):
        result = reg.scan_image("nonexistent")
        assert result.get("error") == "Not found"

    def test_replicate_image(self, reg):
        img = reg.register_image("nginx", "docker_hub", "library/nginx")
        result = reg.replicate_image(img.id)
        assert result["status"] == "replicating"
        assert "targets" in result

    def test_replicate_nonexistent(self, reg):
        result = reg.replicate_image("nonexistent")
        assert result.get("error") == "Not found"

    def test_list_rules_empty(self, reg):
        assert reg.list_rules() == []

    def test_create_rule(self, reg):
        rule = reg.create_rule(source_registry="docker_hub", target_registries=["aws_ecr"], image_pattern="*")
        assert rule.id is not None

    def test_list_registries(self, reg):
        registries = reg.list_registries()
        assert len(registries) > 0
