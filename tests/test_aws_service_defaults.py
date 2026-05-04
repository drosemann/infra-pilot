from pathlib import Path
import sys

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


def test_given_ec2_service_when_initialized_then_applies_ec2_defaults():
    service = aws001.AWSEC2Service001(region="eu-central-1", account_id="123456789012")
    _assert_common_fields(service, "ec2", "001", "eu-central-1", "123456789012")


def test_given_s3_service_when_initialized_then_applies_s3_defaults():
    service = aws001.AWSS3Service002(region="us-west-2", account_id="210987654321")
    _assert_common_fields(service, "s3", "002", "us-west-2", "210987654321")


def test_given_rds_service_when_initialized_then_applies_rds_defaults():
    service = aws001.AWSRDSService003(region="ap-southeast-1", account_id="555544443333")
    _assert_common_fields(service, "rds", "003", "ap-southeast-1", "555544443333")


def test_given_lambda_service_when_initialized_then_applies_lambda_defaults():
    service = aws001.AWSLambdaService004(region="eu-west-1", account_id="111122223333")
    _assert_common_fields(service, "lambda", "004", "eu-west-1", "111122223333")


def test_given_ecs_service_when_initialized_then_applies_ecs_defaults():
    service = aws001.AWSECSService005(region="sa-east-1", account_id="444455556666")
    _assert_common_fields(service, "ecs", "005", "sa-east-1", "444455556666")


def test_given_eks_service_when_initialized_then_applies_eks_defaults():
    service = aws001.AWSEKSService006(region="ca-central-1", account_id="777788889999")
    _assert_common_fields(service, "eks", "006", "ca-central-1", "777788889999")


def test_given_dynamodb_service_when_initialized_then_applies_dynamodb_defaults():
    service = aws001.AWSDynamoDBService007(region="us-east-2", account_id="101010101010")
    _assert_common_fields(service, "dynamodb", "007", "us-east-2", "101010101010")


def test_given_cloudwatch_service_when_initialized_then_applies_cloudwatch_defaults():
    service = aws001.AWSCloudWatchService008(region="eu-north-1", account_id="202020202020")
    _assert_common_fields(service, "cloudwatch", "008", "eu-north-1", "202020202020")


def test_given_iam_service_when_initialized_then_applies_iam_defaults():
    service = aws001.AWSIAMService009(region="ap-northeast-1", account_id="303030303030")
    _assert_common_fields(service, "iam", "009", "ap-northeast-1", "303030303030")


def test_given_vpc_service_when_initialized_then_applies_vpc_defaults():
    service = aws001.AWSVPCService010(region="af-south-1", account_id="404040404040")
    _assert_common_fields(service, "vpc", "010", "af-south-1", "404040404040")


def test_given_route53_service_when_initialized_then_applies_route53_defaults():
    service = aws001.AWSRoute53Service011(region="me-south-1", account_id="505050505050")
    _assert_common_fields(service, "route53", "011", "me-south-1", "505050505050")


def test_given_sns_service_when_initialized_then_applies_sns_defaults():
    service = aws001.AWSSNSService012(region="eu-south-1", account_id="606060606060")
    _assert_common_fields(service, "sns", "012", "eu-south-1", "606060606060")
