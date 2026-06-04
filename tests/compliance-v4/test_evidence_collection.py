import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.evidence_collection import (
    EvidenceCollector, EvidenceItem, EvidencePackage,
)

@pytest.fixture
def collector(tmp_path):
    return EvidenceCollector({"evidence_data_dir": str(tmp_path)})

def test_collect_evidence(collector):
    ev = collector.collect_evidence("SOC2-CC1", "SOC_2", "config_snapshot",
                                     "Test evidence", "terraform", '{"key": "val"}')
    assert ev.control_id == "SOC2-CC1"
    assert ev.framework == "SOC_2"
    assert ev.status == "active"
    assert ev.content_hash is not None

def test_auto_collect(collector):
    items = collector.auto_collect_for_control("SOC2-CC1", "SOC_2")
    assert len(items) > 0

def test_create_package(collector):
    collector.collect_evidence("CTRL-1", "SOC_2", "scan", "desc", "src", "data")
    pkg = collector.create_package("Test Pkg", "SOC_2", ["CTRL-1"],
                                    datetime.utcnow() - timedelta(days=30),
                                    datetime.utcnow())
    assert pkg.status == "draft"
    assert pkg.framework == "SOC_2"

def test_finalize_package(collector):
    collector.collect_evidence("CTRL-1", "SOC_2", "scan", "desc", "src", "data")
    pkg = collector.create_package("Pkg", "SOC_2", ["CTRL-1"],
                                    datetime.utcnow() - timedelta(days=30),
                                    datetime.utcnow())
    finalized = collector.finalize_package(pkg.package_id)
    assert finalized.status == "finalized"

def test_get_evidence_by_id(collector):
    ev = collector.collect_evidence("CTRL-1", "SOC_2", "scan", "desc", "src", "data")
    results = collector.get_evidence(evidence_id=ev.evidence_id)
    assert len(results) == 1
    assert results[0].evidence_id == ev.evidence_id

def test_get_evidence_by_control(collector):
    collector.collect_evidence("CTRL-1", "SOC_2", "scan", "desc", "src", "data")
    results = collector.get_evidence(control_id="CTRL-1")
    assert len(results) >= 1

def test_get_statistics(collector):
    stats = collector.get_statistics()
    assert "total_evidence" in stats
    assert "by_type" in stats

def test_batch_collect(collector):
    items = collector.batch_collect([
        {"control_id": "C1", "framework": "SOC_2", "evidence_type": "scan",
         "description": "d1", "source": "batch", "content": "{}"},
        {"control_id": "C2", "framework": "HIPAA", "evidence_type": "log",
         "description": "d2", "source": "batch", "content": "{}"},
    ])
    assert len(items) == 2

def test_set_retention_policy(collector):
    policy = collector.set_retention_policy("certification", 730)
    assert policy["evidence_type"] == "certification"
    assert policy["retention_days"] == 730

def test_check_expired_evidence(collector):
    ev = collector.collect_evidence("CTRL-1", "SOC_2", "certification",
                                     "test", "src", "data")
    ev.expires_at = datetime.utcnow() - timedelta(days=1)
    expired = collector.check_expired_evidence()
    assert len(expired) >= 1
    assert ev.status == "expired"

def test_bulk_update_status(collector):
    ev1 = collector.collect_evidence("C1", "SOC_2", "scan", "d1", "s1", "{}")
    ev2 = collector.collect_evidence("C2", "SOC_2", "scan", "d2", "s2", "{}")
    count = collector.bulk_update_status([ev1.evidence_id, ev2.evidence_id], "archived")
    assert count == 2

def test_search_evidence(collector):
    collector.collect_evidence("CTRL-1", "SOC_2", "scan", "encryption check", "aws", "{}")
    results = collector.search_evidence("encryption")
    assert len(results) >= 1

def test_chain_of_custody(collector):
    ev = collector.collect_evidence("CTRL-1", "SOC_2", "scan", "test", "src", "data")
    chain = collector.get_chain_of_custody(ev.evidence_id)
    assert len(chain) >= 1
    assert chain[0]["event"] == "collected"

def test_validate_evidence(collector):
    ev = collector.collect_evidence("CTRL-1", "SOC_2", "scan", "test", "src", "data")
    result = collector.validate_evidence(ev.evidence_id)
    assert result["valid"] is True

def test_export_import_package(collector, tmp_path):
    collector.collect_evidence("CTRL-1", "SOC_2", "scan", "desc", "src", "data")
    pkg = collector.create_package("Pkg", "SOC_2", ["CTRL-1"],
                                    datetime.utcnow() - timedelta(days=30),
                                    datetime.utcnow())
    path = collector.export_package(pkg.package_id)
    assert path is not None

    imported = collector.import_package(path)
    assert imported is not None
    assert imported.framework == "SOC_2"
