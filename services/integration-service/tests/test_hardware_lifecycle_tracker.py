"""Tests for Hardware Lifecycle Tracker."""

import pytest
from datetime import datetime
from hardware_lifecycle_tracker import (
    HardwareLifecycleTracker, HardwareAsset, MaintenanceRecord,
    AssetStatus, HardwareType, LifecycleStage
)


@pytest.fixture
def tracker():
    return HardwareLifecycleTracker({})


class TestHardwareAsset:
    def test_create(self):
        asset = HardwareAsset(
            "asset-001", HardwareType.SERVER, "Dell", "R740",
            "SN-12345", "2023-01-01"
        )
        assert asset.asset_id == "asset-001"
        assert asset.status == AssetStatus.ACTIVE
        assert asset.hardware_type == HardwareType.SERVER

    def test_to_dict(self):
        asset = HardwareAsset("a-001", HardwareType.SWITCH, " Cisco", "9300",
                               "SN-X", "2023-06-01")
        d = asset.to_dict()
        assert d["asset_id"] == "a-001"
        assert d["model"] == "9300"


class TestHardwareLifecycleTracker:
    def test_initialization(self, tracker):
        assert len(tracker.assets) > 0
        assert len(tracker.maintenance_records) > 0

    def test_register_asset(self, tracker):
        asset = tracker.register_asset(
            "asset-new", HardwareType.STORAGE, "Synology", "RS1221+",
            "SN-NEW", "2024-01-15", location="DC-1"
        )
        assert asset.asset_id == "asset-new"
        assert asset.location == "DC-1"

    def test_get_asset(self, tracker):
        aid = list(tracker.assets.keys())[0]
        assert tracker.get_asset(aid) is not None

    def test_get_asset_not_found(self, tracker):
        assert tracker.get_asset("nonexistent") is None

    def test_list_assets(self, tracker):
        assets = tracker.list_assets()
        assert len(assets) > 0

    def test_list_assets_by_status(self, tracker):
        active = tracker.list_assets(status=AssetStatus.ACTIVE)
        assert len(active) > 0

    def test_update_asset(self, tracker):
        aid = list(tracker.assets.keys())[0]
        updated = tracker.update_asset(aid, {"location": "DC-2"})
        assert updated is not None
        assert updated.location == "DC-2"

    def test_update_asset_not_found(self, tracker):
        assert tracker.update_asset("nonexistent", {}) is None

    def test_decommission_asset(self, tracker):
        aid = list(tracker.assets.keys())[0]
        assert tracker.decommission_asset(aid) is True
        assert tracker.get_asset(aid).status == AssetStatus.DECOMMISSIONED

    def test_decommission_asset_not_found(self, tracker):
        assert tracker.decommission_asset("nonexistent") is False

    def test_add_maintenance(self, tracker):
        aid = list(tracker.assets.keys())[0]
        record = tracker.add_maintenance(
            aid, "battery-replacement", "Scheduled battery swap",
            "tech-001"
        )
        assert record is not None
        assert record.record_id is not None
        assert record.maintenance_type == "battery-replacement"

    def test_add_maintenance_asset_not_found(self, tracker):
        assert tracker.add_maintenance("nonexistent", "type", "desc", "tech") is None

    def test_get_maintenance(self, tracker):
        rec = list(tracker.maintenance_records.values())[0]
        assert tracker.get_maintenance(rec.record_id) is not None

    def test_get_maintenance_not_found(self, tracker):
        assert tracker.get_maintenance("nonexistent") is None

    def test_list_maintenance(self, tracker):
        records = tracker.list_maintenance()
        assert len(records) > 0

    def test_list_maintenance_by_asset(self, tracker):
        rid = list(tracker.maintenance_records.keys())[0]
        rec = tracker.get_maintenance(rid)
        records = tracker.list_maintenance(asset_id=rec.asset_id)
        assert len(records) > 0

    def test_get_lifecycle_summary(self, tracker):
        summary = tracker.get_lifecycle_summary()
        assert "total_assets" in summary
        assert "active_assets" in summary
        assert "decommissioned_assets" in summary
        assert "maintenance_records" in summary
        assert "avg_age_years" in summary
        assert "upcoming_eol_count" in summary

    def test_get_asset_timeline(self, tracker):
        aid = list(tracker.assets.keys())[0]
        timeline = tracker.get_asset_timeline(aid)
        assert "asset_id" in timeline
        assert "events" in timeline

    def test_get_asset_timeline_not_found(self, tracker):
        assert tracker.get_asset_timeline("nonexistent") is None

    def test_get_warranty_status(self, tracker):
        aid = list(tracker.assets.keys())[0]
        status = tracker.get_warranty_status(aid)
        assert "asset_id" in status
        assert "under_warranty" in status

    def test_get_warranty_status_not_found(self, tracker):
        assert tracker.get_warranty_status("nonexistent") is None

    def test_asset_status_enum(self):
        assert AssetStatus.ACTIVE.value == "active"
        assert AssetStatus.INACTIVE.value == "inactive"
        assert AssetStatus.DECOMMISSIONED.value == "decommissioned"
        assert AssetStatus.RETIRED.value == "retired"

    def test_hardware_type_enum(self):
        assert HardwareType.SERVER.value == "server"
        assert HardwareType.SWITCH.value == "switch"
        assert HardwareType.ROUTER.value == "router"
        assert HardwareType.STORAGE.value == "storage"
        assert HardwareType.GPU.value == "gpu"
        assert HardwareType.NETWORK.value == "network"
