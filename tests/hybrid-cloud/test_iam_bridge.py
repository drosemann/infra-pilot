import pytest
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from iam_bridge import IAMBridge

@pytest.fixture
def iam():
    b = IAMBridge({})
    b.initialize()
    yield b
    b.close()

class TestIAMBridge:
    def test_list_mappings_empty(self, iam):
        assert iam.list_mappings() == []

    def test_create_mapping(self, iam):
        m = iam.create_mapping(source_role="Admin", source_provider="aws", target_role="Owner", target_provider="azure")
        assert m.id is not None
        assert m.active is True

    def test_sync_mappings(self, iam):
        iam.create_mapping("Admin", "aws", "Owner", "azure")
        result = iam.sync_all()
        assert result["status"] == "synced"
        assert result["count"] == 1

    def test_list_roles(self, iam):
        roles = iam.list_roles()
        assert len(roles) > 0

    def test_list_policies_empty(self, iam):
        assert iam.list_policies() == []

    def test_create_policy(self, iam):
        p = iam.create_policy(name="ReadOnlyAccess", statements=[{"effect": "Allow"}])
        assert p.id is not None
        assert p.name == "ReadOnlyAccess"

    def test_list_policies_after_create(self, iam):
        iam.create_policy("Policy1", [])
        assert len(iam.list_policies()) == 1
