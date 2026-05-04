from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import modules.aws_extended_001 as aws001


def _assert_common_fields(obj, service_name: str, class_index: str, region: str, account_id: str):
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


@pytest.mark.parametrize(
    "service_cls, service_name, class_index, region, account_id",
    [
        (aws001.AWSEC2Service001, "ec2", "001", "eu-central-1", "123456789012"),
        (aws001.AWSS3Service002, "s3", "002", "us-west-2", "210987654321"),
        (aws001.AWSRDSService003, "rds", "003", "ap-southeast-1", "555544443333"),
        (aws001.AWSLambdaService004, "lambda", "004", "eu-west-1", "111122223333"),
        (aws001.AWSECSService005, "ecs", "005", "sa-east-1", "444455556666"),
        (aws001.AWSEKSService006, "eks", "006", "ca-central-1", "777788889999"),
        (aws001.AWSDynamoDBService007, "dynamodb", "007", "us-east-2", "101010101010"),
        (aws001.AWSCloudWatchService008, "cloudwatch", "008", "eu-north-1", "202020202020"),
        (aws001.AWSIAMService009, "iam", "009", "ap-northeast-1", "303030303030"),
        (aws001.AWSVPCService010, "vpc", "010", "af-south-1", "404040404040"),
        (aws001.AWSRoute53Service011, "route53", "011", "me-south-1", "505050505050"),
        (aws001.AWSSNSService012, "sns", "012", "eu-south-1", "606060606060"),
    ],
    ids=[
        "ec2-eu-central-1",
        "s3-us-west-2",
        "rds-ap-southeast-1",
        "lambda-eu-west-1",
        "ecs-sa-east-1",
        "eks-ca-central-1",
        "dynamodb-us-east-2",
        "cloudwatch-eu-north-1",
        "iam-ap-northeast-1",
        "vpc-af-south-1",
        "route53-me-south-1",
        "sns-eu-south-1",
    ],
)
def test_given_service_when_initialized_then_applies_expected_defaults(
    service_cls,
    service_name,
    class_index,
    region,
    account_id,
):
    service = service_cls(region=region, account_id=account_id)
    _assert_common_fields(service, service_name, class_index, region, account_id)
