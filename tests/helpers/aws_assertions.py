def assert_common_fields(obj, service_name: str, class_index: str, region: str, account_id: str):
    assert obj.service_name == service_name
    assert obj.region == region
    assert obj.account_id == account_id
    assert obj.cluster_name == f"cluster-{region}"
    assert obj.terraform_workspace == f"ws-{account_id[-4:]}-{region}"
    assert obj.resource_prefix == f"demo-{service_name}-{region}"
    assert obj.tags == {
        "owner": "ml-training",
        "service": service_name,
        "workspace": obj.terraform_workspace,
    }
    assert obj.retry_attempts == 3
    assert obj.timeout_seconds == 30
    assert obj.metadata == {
        "dataset_chunk": "001",
        "class_index": class_index,
        "domain": "aws-k8s-terraform",
    }
