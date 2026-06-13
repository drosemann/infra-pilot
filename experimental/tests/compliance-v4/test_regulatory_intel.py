import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.regulatory_intel import (
    RegulatoryIntelligenceEngine, ImpactLevel,
)

@pytest.fixture
def engine(tmp_path):
    eng = RegulatoryIntelligenceEngine({"regulatory_data_file": str(tmp_path / "ri.json")})
    eng.changes = []
    return eng

def test_detect_change(engine):
    change = engine.detect_change(
        "New Regulation", "government", "new_regulation",
        "Description", "GDPR", "EU", "critical",
        action_required=True,
    )
    assert change.title == "New Regulation"
    assert change.impact_level == ImpactLevel.CRITICAL
    assert change.status == "new"

def test_get_changes(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "high")
    changes = engine.get_changes()
    assert len(changes) == 1

def test_get_changes_by_regulation(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "high")
    engine.detect_change("C2", "government", "amendment", "D2", "PCI DSS", "Global", "medium")
    gdpr = engine.get_changes(regulation="gdpr")
    assert len(gdpr) == 1

def test_get_changes_by_impact(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "critical")
    engine.detect_change("C2", "government", "amendment", "D2", "PCI DSS", "Global", "low")
    critical = engine.get_changes(impact_level="critical")
    assert len(critical) == 1

def test_get_sources(engine):
    sources = engine.get_sources()
    assert len(sources) > 0

def test_get_impact_analysis(engine):
    c = engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "critical",
                              affected_controls=["C1"], affected_frameworks=["GDPR"])
    analysis = engine.get_impact_analysis(c.change_id)
    assert "impact_summary" in analysis
    assert "recommended_actions" in analysis

def test_get_statistics(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "high")
    engine.detect_change("C2", "government", "amendment", "D2", "PCI DSS", "Global", "critical")
    stats = engine.get_statistics()
    assert stats["total_changes"] == 2

def test_mark_reviewed(engine):
    c = engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "medium")
    engine.mark_reviewed(c.change_id)
    assert c.status == "reviewed"

def test_batch_detect(engine):
    changes = [
        {"title": "B1", "source": "government", "change_type": "new_regulation",
         "description": "D1", "regulation": "GDPR", "jurisdiction": "EU", "impact_level": "high"},
        {"title": "B2", "source": "industry_body", "change_type": "amendment",
         "description": "D2", "regulation": "PCI DSS", "jurisdiction": "Global", "impact_level": "critical"},
    ]
    detected = engine.batch_detect(changes)
    assert len(detected) == 2

def test_get_calendar(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "high",
                          effective_date=datetime.utcnow() + timedelta(days=30))
    events = engine.get_calendar()
    assert len(events) >= 1

def test_impact_matrix(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "critical",
                          affected_frameworks=["GDPR"])
    matrix = engine.impact_matrix()
    assert "matrix" in matrix
    assert "most_impacted" in matrix

def test_source_health(engine):
    engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "high")
    health = engine.source_health()
    assert len(health) > 0

def test_route_notification(engine):
    c = engine.detect_change("C1", "government", "new_regulation", "D1", "GDPR", "EU", "critical")
    notif = engine.route_notification(c.change_id, ["email", "slack"])
    assert notif["status"] == "sent"
    assert "email" in notif["channels"]

def test_sync_calendar(engine):
    result = engine.sync_calendar()
    assert result["sync_status"] == "completed"
