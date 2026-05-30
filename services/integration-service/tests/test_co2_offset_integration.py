"""Tests for CO2 Offset Integration."""

import pytest
from datetime import datetime
from co2_offset_integration import (
    CO2OffsetIntegration, CarbonOffset, OffsetProject,
    OffsetProvider, OffsetStatus, ProjectType, VerificationStandard
)


@pytest.fixture
def co2():
    return CO2OffsetIntegration({})


class TestCarbonOffset:
    def test_create(self):
        offset = CarbonOffset(
            "off-001", 10.0, "provider-1",
            OffsetStatus.PURCHASED
        )
        assert offset.offset_id == "off-001"
        assert offset.tonnes_co2 == 10.0
        assert offset.status == OffsetStatus.PURCHASED

    def test_to_dict(self):
        offset = CarbonOffset("off-001", 5.0, "prov-1", OffsetStatus.PENDING)
        d = offset.to_dict()
        assert d["offset_id"] == "off-001"
        assert d["tonnes_co2"] == 5.0


class TestOffsetProject:
    def test_create(self):
        project = OffsetProject(
            "proj-001", "Reforestation Amazon",
            ProjectType.REFORESTATION, "Brazil"
        )
        assert project.project_id == "proj-001"
        assert project.type == ProjectType.REFORESTATION

    def test_to_dict(self):
        project = OffsetProject("p-001", "Solar Farm", ProjectType.RENEWABLE, "Spain")
        d = project.to_dict()
        assert d["name"] == "Solar Farm"
        assert d["type"] == "renewable_energy"


class TestCO2OffsetIntegration:
    def test_initialization(self, co2):
        assert len(co2.offsets) > 0
        assert len(co2.projects) > 0
        assert len(co2.providers) > 0

    def test_purchase_offset(self, co2):
        offset = co2.purchase_offset(25.0, "provider-1")
        assert offset is not None
        assert offset.tonnes_co2 == 25.0
        assert offset.status == OffsetStatus.PURCHASED

    def test_get_offset(self, co2):
        oid = list(co2.offsets.keys())[0]
        assert co2.get_offset(oid) is not None

    def test_get_offset_not_found(self, co2):
        assert co2.get_offset("nonexistent") is None

    def test_list_offsets(self, co2):
        offsets = co2.list_offsets()
        assert len(offsets) > 0

    def test_list_offsets_by_status(self, co2):
        purchased = co2.list_offsets(status=OffsetStatus.PURCHASED)
        assert len(purchased) > 0

    def test_register_project(self, co2):
        project = co2.register_project(
            "proj-new", "Wind Farm", ProjectType.RENEWABLE, "Denmark",
            VerificationStandard.VCS, capacity_tonnes_year=50000
        )
        assert project.project_id == "proj-new"
        assert project.verification == VerificationStandard.VCS

    def test_get_project(self, co2):
        pid = list(co2.projects.keys())[0]
        assert co2.get_project(pid) is not None

    def test_get_project_not_found(self, co2):
        assert co2.get_project("nonexistent") is None

    def test_list_projects(self, co2):
        projects = co2.list_projects()
        assert len(projects) > 0

    def test_register_provider(self, co2):
        provider = co2.register_provider(
            "prov-new", "Green Offset Inc",
            verification_standards=[VerificationStandard.GOLD_STANDARD]
        )
        assert provider.provider_id == "prov-new"
        assert provider.name == "Green Offset Inc"

    def test_get_provider(self, co2):
        pid = list(co2.providers.keys())[0]
        assert co2.get_provider(pid) is not None

    def test_get_provider_not_found(self, co2):
        assert co2.get_provider("nonexistent") is None

    def test_list_providers(self, co2):
        providers = co2.list_providers()
        assert len(providers) > 0

    def test_get_total_offset(self, co2):
        total = co2.get_total_offset()
        assert "total_tonnes_co2" in total
        assert "total_purchased" in total
        assert "total_retired" in total
        assert "total_pending" in total

    def test_get_portfolio_summary(self, co2):
        summary = co2.get_portfolio_summary()
        assert "total_tonnes_offset" in summary
        assert "active_projects" in summary
        assert "providers" in summary
        assert "carbon_neutral_status" in summary

    def test_get_project_by_type(self, co2):
        projects = co2.get_project_by_type(ProjectType.REFORESTATION)
        assert len(projects) >= 0

    def test_retire_offset(self, co2):
        oid = list(co2.offsets.keys())[0]
        assert co2.retire_offset(oid) is True
        assert co2.get_offset(oid).status == OffsetStatus.RETIRED

    def test_retire_offset_not_found(self, co2):
        assert co2.retire_offset("nonexistent") is False

    def test_get_carbon_neutrality_status(self, co2):
        status = co2.get_carbon_neutrality_status()
        assert "is_carbon_neutral" in status
        assert "total_emissions_tonnes" in status
        assert "total_offsets_tonnes" in status
        assert "net_tonnes" in status

    def test_get_impact_report(self, co2):
        report = co2.get_impact_report()
        assert "total_tonnes_offset" in report
        assert "trees_equivalent" in report
        assert "cars_equivalent" in report
        assert "projects_supported" in report

    def test_offset_status_enum(self):
        assert OffsetStatus.PENDING.value == "pending"
        assert OffsetStatus.PURCHASED.value == "purchased"
        assert OffsetStatus.RETIRED.value == "retired"

    def test_project_type_enum(self):
        assert ProjectType.REFORESTATION.value == "reforestation"
        assert ProjectType.RENEWABLE.value == "renewable_energy"
        assert ProjectType.METHANE.value == "methane_capture"
        assert ProjectType.DIRECT_AIR_CAPTURE.value == "direct_air_capture"
