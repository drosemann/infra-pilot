import pytest
import json
import sys
sys.path.insert(0, 'services/integration-service/src/hybrid_cloud')
from multi_cloud_broker import MultiCloudBroker, ResourceRequest, ResourceStatus

@pytest.fixture
def broker():
    b = MultiCloudBroker({"default_provider": "aws"})
    b.initialize()
    yield b
    b.close()

class TestMultiCloudBroker:
    def test_list_resources_empty(self, broker):
        assert broker.list_resources() == []

    def test_provision_and_list(self, broker):
        req = ResourceRequest(provider="aws", type="ec2", name="test-vm", region="us-east-1", count=1)
        r = broker.provision_resource(req)
        assert r.id is not None
        assert r.status == ResourceStatus.PROVISIONING
        assert len(broker.list_resources()) == 1

    def test_get_resource(self, broker):
        req = ResourceRequest(provider="aws", type="ec2", name="test-vm", region="us-east-1")
        r = broker.provision_resource(req)
        found = broker.get_resource(r.id)
        assert found.id == r.id

    def test_get_resource_not_found(self, broker):
        assert broker.get_resource("nonexistent") is None

    def test_delete_resource(self, broker):
        req = ResourceRequest(provider="aws", type="ec2", name="test-vm", region="us-east-1")
        r = broker.provision_resource(req)
        assert broker.delete_resource(r.id) is True
        assert broker.get_resource(r.id) is None

    def test_list_providers(self, broker):
        providers = broker.list_providers()
        assert len(providers) > 0
        assert any(p["id"] == "aws" for p in providers)

    def test_score_providers(self, broker):
        scores = broker.score_providers(vcpu=2, memory=4)
        assert len(scores) > 0
        assert all("overall" in s for s in scores)

    def test_failover_empty(self, broker):
        assert broker.failover(None) is None

    def test_resource_cost(self, broker):
        req = ResourceRequest(provider="aws", type="ec2", name="test", region="us-east-1")
        r = broker.provision_resource(req)
        cost = broker.get_resource_cost(r.id)
        assert cost > 0
