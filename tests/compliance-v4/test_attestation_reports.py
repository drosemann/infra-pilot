import pytest
from datetime import datetime, timedelta
from services.integration_service.src.compliance_v4.attestation_reports import (
    AttestationReportGenerator,
)

@pytest.fixture
def generator(tmp_path):
    return AttestationReportGenerator({"attestation_data_file": str(tmp_path / "att.json")})

def test_generate_report(generator):
    report = generator.generate_report(
        "SOC_2_TYPE_II", "SOC_2", "Test Corp",
        datetime.utcnow() - timedelta(days=365),
        datetime.utcnow(),
    )
    assert report.report_type == "SOC_2_TYPE_II"
    assert report.organization == "Test Corp"
    assert report.status == "generated"
    assert len(report.control_mappings) > 0

def test_generate_unknown_type(generator):
    with pytest.raises(ValueError):
        generator.generate_report("UNKNOWN", "SOC_2", "C", datetime.utcnow()-timedelta(days=1), datetime.utcnow())

def test_get_reports(generator):
    generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                               datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    reports = generator.get_reports()
    assert len(reports) == 1

def test_get_reports_by_framework(generator):
    generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                               datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    generator.generate_report("HIPAA", "HIPAA", "C",
                               datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    soc2 = generator.get_reports(framework="SOC_2")
    assert len(soc2) == 1
    hipaa = generator.get_reports(framework="HIPAA")
    assert len(hipaa) == 1

def test_get_report_templates(generator):
    templates = generator.get_report_templates()
    assert "SOC_2_TYPE_II" in templates
    assert "HIPAA" in templates

def test_export_to_pdf(generator, tmp_path):
    report = generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                                        datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    path = generator.export_to_pdf(report.report_id, output_path=str(tmp_path / "test_output.pdf"))
    assert path is not None

def test_get_statistics(generator):
    generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                               datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    stats = generator.get_statistics()
    assert stats["total_reports"] == 1

def test_compare_reports(generator):
    r1 = generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                                     datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    r2 = generator.generate_report("HIPAA", "HIPAA", "C",
                                     datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    comp = generator.compare_reports(r1.report_id, r2.report_id)
    assert "report_1" in comp
    assert "report_2" in comp

def test_generate_batch(generator):
    configs = [
        {"report_type": "SOC_2_TYPE_II", "framework": "SOC_2", "organization": "C1",
         "period_start": (datetime.utcnow()-timedelta(days=365)).isoformat(),
         "period_end": datetime.utcnow().isoformat()},
        {"report_type": "HIPAA", "framework": "HIPAA", "organization": "C2",
         "period_start": (datetime.utcnow()-timedelta(days=365)).isoformat(),
         "period_end": datetime.utcnow().isoformat()},
    ]
    reports = generator.generate_batch(configs)
    assert len(reports) == 2

def test_schedule_report(generator):
    sched = generator.schedule_report("SOC_2_TYPE_II", "SOC_2", "C", "0 0 * * 1")
    assert sched["status"] == "active"
    assert sched["cron"] == "0 0 * * 1"

def test_verify_signature(generator):
    report = generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                                        datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    result = generator.verify_signature(report.report_id)
    assert result["verified"] is True

def test_diff_reports(generator):
    r1 = generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                                     datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    r2 = generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                                     datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    diff = generator.diff_reports(r1.report_id, r2.report_id)
    assert "control_status_changes" in diff

def test_composite_report(generator):
    report = generator.composite_report(["SOC_2", "HIPAA"], "Test Corp",
                                          datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    assert "COMPOSITE" in report.report_type
    assert len(report.control_mappings) > 0

def test_approve_report(generator):
    report = generator.generate_report("SOC_2_TYPE_II", "SOC_2", "C",
                                        datetime.utcnow()-timedelta(days=365), datetime.utcnow())
    result = generator.approve_report(report.report_id, "auditor@example.com", "Approved")
    assert result["status"] == "approved"
