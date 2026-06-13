import pytest
from services.integration_service.src.compliance_v4.data_residency import (
    DataResidencyEnforcer, ResidencyStatus, DataClassification, GeoLocation,
)

@pytest.fixture
def enforcer(tmp_path):
    return DataResidencyEnforcer({"residency_data_file": str(tmp_path / "dr.json")})

def test_register_asset(enforcer):
    asset = enforcer.register_asset("db-primary", "database", "confidential",
                                     "US", "us-east-1", "admin@co.com")
    assert asset.name == "db-primary"
    assert asset.classification == DataClassification.CONFIDENTIAL
    assert asset.status == "active"

def test_register_asset_violation(enforcer):
    asset = enforcer.register_asset("db-eu", "database", "restricted",
                                     "EU", "us-east-1", "admin@co.com")
    assert asset.status == "violation"

def test_check_flow_allowed(enforcer):
    enforcer.register_asset("db", "database", "internal", "US", "us-east-1")
    flow = enforcer.check_flow("db", "us-west-2", "GDPR", "replication")
    assert flow.status == ResidencyStatus.COMPLIANT

def test_check_flow_restricted(enforcer):
    enforcer.register_asset("db", "database", "confidential", "US", "us-east-1")
    flow = enforcer.check_flow("db", "eu-central-1", "CCPA")
    assert flow.status in (ResidencyStatus.COMPLIANT, ResidencyStatus.VIOLATION)

def test_approve_flow(enforcer):
    enforcer.register_asset("db", "database", "internal", "US", "us-east-1")
    flow = enforcer.check_flow("db", "us-west-2", "GDPR")
    approved = enforcer.approve_flow(flow.flow_id, "admin")
    assert approved.status == ResidencyStatus.COMPLIANT

def test_move_asset(enforcer):
    asset = enforcer.register_asset("db", "database", "internal", "US", "us-east-1")
    moved = enforcer.move_asset(asset.asset_id, "us-west-2", "admin")
    assert moved.current_region == GeoLocation.US_WEST

def test_get_assets(enforcer):
    enforcer.register_asset("db1", "database", "internal", "US", "us-east-1")
    enforcer.register_asset("db2", "database", "confidential", "EU", "eu-west-1")
    assets = enforcer.get_assets()
    assert len(assets) == 2

def test_get_assets_by_classification(enforcer):
    enforcer.register_asset("db1", "database", "internal", "US", "us-east-1")
    enforcer.register_asset("db2", "database", "restricted", "EU", "eu-west-1")
    internal = enforcer.get_assets(classification="internal")
    assert len(internal) == 1

def test_get_flows(enforcer):
    enforcer.register_asset("db", "database", "internal", "US", "us-east-1")
    enforcer.check_flow("db", "us-west-2", "GDPR")
    flows = enforcer.get_flows()
    assert len(flows) == 1

def test_get_audit_trail(enforcer):
    enforcer.register_asset("db", "database", "internal", "US", "us-east-1")
    trail = enforcer.get_audit_trail()
    assert len(trail) >= 1

def test_get_summary(enforcer):
    enforcer.register_asset("db1", "database", "internal", "US", "us-east-1")
    enforcer.register_asset("db2", "database", "restricted", "EU", "eu-west-1")
    summary = enforcer.get_summary()
    assert summary["total_assets"] == 2

def test_get_compliance_report(enforcer):
    enforcer.register_asset("db", "database", "internal", "US", "us-east-1")
    report = enforcer.get_compliance_report("GDPR")
    assert report["framework"] == "GDPR"
    assert "assets_in_scope" in report

def test_get_compliance_report_unknown(enforcer):
    report = enforcer.get_compliance_report("UNKNOWN")
    assert "error" in report

def test_register_multiple_jurisdictions(enforcer):
    enforcer.register_asset("db-us", "database", "internal", "US", "us-east-1")
    enforcer.register_asset("db-eu", "database", "internal", "EU", "eu-west-1")
    enforcer.register_asset("db-apac", "database", "internal", "APAC", "ap-southeast-1")
    by_jurs = enforcer.get_summary()["by_jurisdiction"]
    assert len(by_jurs) == 3

def test_region_to_jurisdiction(enforcer):
    assert enforcer._region_to_jurisdiction(GeoLocation.US_EAST) == "US"
    assert enforcer._region_to_jurisdiction(GeoLocation.EU_WEST) == "EU"
    assert enforcer._region_to_jurisdiction(GeoLocation.SA_EAST) == "BR"
