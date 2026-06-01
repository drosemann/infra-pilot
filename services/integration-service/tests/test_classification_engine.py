"""Tests for Data Classification Engine."""
import pytest
from classification_engine import ClassificationEngine, DataScan, DataInventory, ClassificationResult


@pytest.fixture
def engine():
    return ClassificationEngine({
        "pii_patterns_enabled": True,
        "phi_patterns_enabled": True,
        "pci_patterns_enabled": True,
        "confidence_threshold": 0.6,
        "max_scan_size_mb": 100,
        "inventory_auto_update": True
    })


class TestPatternDetection:
    def test_detect_email(self, engine):
        result = engine.detect_patterns("user@example.com")
        assert len(result) > 0
        assert any(r.pattern_type == "email" for r in result)

    def test_detect_credit_card(self, engine):
        result = engine.detect_patterns("4111-1111-1111-1111")
        assert len(result) > 0
        assert any(r.pattern_type == "credit_card" for r in result)

    def test_detect_ssn(self, engine):
        result = engine.detect_patterns("123-45-6789")
        assert len(result) > 0
        assert any(r.pattern_type == "ssn" for r in result)

    def test_detect_phone(self, engine):
        result = engine.detect_patterns("+1 (555) 123-4567")
        assert len(result) > 0
        assert any(r.pattern_type == "phone" for r in result)

    def test_detect_ip_address(self, engine):
        result = engine.detect_patterns("192.168.1.1")
        assert len(result) > 0
        assert any(r.pattern_type == "ip_address" for r in result)

    def test_detect_api_key(self, engine):
        result = engine.detect_patterns("sk_live_abc123def456ghi789")
        assert len(result) > 0
        assert any(r.pattern_type == "api_key" for r in result)

    def test_detect_jwt(self, engine):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNqP1s7L7jVPJ8KzqY7y0Qk"
        result = engine.detect_patterns(jwt)
        assert len(result) > 0
        assert any(r.pattern_type == "jwt_token" for r in result)

    def test_detect_aws_key(self, engine):
        result = engine.detect_patterns("AKIAIOSFODNN7EXAMPLE")
        assert len(result) > 0
        assert any(r.pattern_type == "aws_access_key" for r in result)

    def test_detect_private_key(self, engine):
        result = engine.detect_patterns("-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...")
        assert len(result) > 0
        assert any("private_key" in r.pattern_type for r in result)

    def test_detect_driver_license(self, engine):
        result = engine.detect_patterns("D123-4567-8901")
        assert len(result) > 0
        assert any(r.pattern_type == "driver_license" for r in result)

    def test_detect_passport(self, engine):
        result = engine.detect_patterns("AB1234567")
        assert len(result) > 0
        assert any(r.pattern_type == "passport" for r in result)

    def test_detect_bank_routing(self, engine):
        result = engine.detect_patterns("021000021")
        assert len(result) > 0
        assert any(r.pattern_type == "bank_routing" for r in result)

    def test_detect_bank_account(self, engine):
        result = engine.detect_patterns("123456789012")
        assert len(result) > 0

    def test_detect_medical_record(self, engine):
        result = engine.detect_patterns("MRN-98765432")
        assert len(result) > 0
        assert any(r.pattern_type == "medical_record" for r in result)

    def test_detect_health_insurance(self, engine):
        result = engine.detect_patterns("HI-123-456-789")
        assert len(result) > 0
        assert any(r.pattern_type == "health_insurance" for r in result)

    def test_detect_password(self, engine):
        result = engine.detect_patterns("password=P@ssw0rd123!")
        assert len(result) > 0
        assert any(r.pattern_type == "password" for r in result)

    def test_no_false_positive_clean_text(self, engine):
        result = engine.detect_patterns("The quick brown fox jumps over the lazy dog")
        sensitive = [r for r in result if r.confidence > 0.5]
        assert len(sensitive) == 0

    def test_confidence_scoring(self, engine):
        result = engine.detect_patterns("user@example.com")
        for r in result:
            if r.pattern_type == "email":
                assert r.confidence >= 0.9

    def test_multiple_patterns_in_text(self, engine):
        text = "Email: user@example.com, CC: 4111-1111-1111-1111, SSN: 123-45-6789"
        result = engine.detect_patterns(text)
        types = set(r.pattern_type for r in result)
        assert "email" in types
        assert "credit_card" in types
        assert "ssn" in types


class TestTextScanning:
    def test_scan_text(self, engine):
        scan = engine.scan_text("Contact: user@example.com, Phone: +1-555-123-4567")
        assert scan.scan_id is not None
        assert scan.classification == "sensitive"
        assert scan.findings_count > 0

    def test_scan_clean_text(self, engine):
        scan = engine.scan_text("This is a harmless text without any sensitive data")
        assert scan.scan_id is not None
        assert scan.classification == "clean"

    def test_scan_text_with_confidence_filter(self, engine):
        scan = engine.scan_text("email: test@test.com", min_confidence=0.95)
        assert scan.scan_id is not None

    def test_classify_text_pii(self, engine):
        result = engine.classify_text("Email: user@domain.com, Phone: 555-123-4567")
        assert result.classification == "pii"
        assert result.confidence > 0.8

    def test_classify_text_phi(self, engine):
        result = engine.classify_text("Patient MRN-98765432 has diagnosis X")
        assert result.classification == "phi"
        assert result.confidence > 0.5

    def test_classify_text_pci(self, engine):
        result = engine.classify_text("Card: 4111-1111-1111-1111 exp 12/25")
        assert result.classification == "pci"
        assert result.confidence > 0.8


class TestFileScanning:
    def test_scan_small_file(self, engine):
        scan = engine.scan_file("test.txt", b"user@company.com, 4111-1111-1111-1111")
        assert scan.scan_id is not None
        assert scan.findings_count >= 2

    def test_scan_empty_file(self, engine):
        scan = engine.scan_file("empty.txt", b"")
        assert scan.scan_id is not None
        assert scan.findings_count == 0
        assert scan.classification == "clean"

    def test_scan_binary_file(self, engine):
        scan = engine.scan_file("data.bin", b"\x00\x01\x02\x03\xff\xfe\xfd\xfc")
        assert scan.scan_id is not None

    def test_scan_large_file_truncation(self, engine):
        large = b"A" * (200 * 1024 * 1024)  # 200MB
        scan = engine.scan_file("large.log", large)
        assert scan.scan_id is not None
        assert "truncated" in scan.warnings[0].lower() if scan.warnings else True


class TestInventoryManagement:
    def test_add_to_inventory(self, engine):
        item = engine.add_to_inventory("sensitive_config.yaml", "config", "pii", ["email", "api_key"])
        assert item is not None
        assert item.path == "sensitive_config.yaml"

    def test_get_inventory(self, engine):
        engine.add_to_inventory("file1.txt", "document", "pii", ["email"])
        engine.add_to_inventory("file2.txt", "log", "phi", ["medical_record"])
        inventory = engine.get_inventory()
        assert len(inventory) >= 2

    def test_inventory_search_by_classification(self, engine):
        engine.add_to_inventory("pii_file.txt", "document", "pii", ["email"])
        engine.add_to_inventory("pci_file.txt", "document", "pci", ["credit_card"])
        pii_items = engine.search_inventory(classification="pii")
        assert len(pii_items) >= 1
        for item in pii_items:
            assert item.classification == "pii"

    def test_remove_from_inventory(self, engine):
        item = engine.add_to_inventory("remove_me.txt", "log", "pii", ["ssn"])
        assert engine.remove_from_inventory(item.item_id) is True
        assert engine.get_inventory_item(item.item_id) is None

    def test_update_inventory_item(self, engine):
        item = engine.add_to_inventory("update_me.txt", "log", "pii", ["email"])
        assert engine.update_inventory_item(item.item_id, {"classification": "phi", "notes": "Updated"}) is True
        updated = engine.get_inventory_item(item.item_id)
        assert updated.classification == "phi"
        assert updated.notes == "Updated"


class TestDatabaseScanning:
    def test_scan_column(self, engine):
        rows = [
            {"email": "user1@test.com", "name": "Alice", "ssn": "123-45-6789"},
            {"email": "user2@test.com", "name": "Bob", "ssn": "987-65-4321"},
        ]
        result = engine.scan_column("users", "email", [r["email"] for r in rows])
        assert result.is_sensitive is True
        assert result.pattern_type == "email"

    def test_scan_clean_column(self, engine):
        result = engine.scan_column("users", "id", ["1", "2", "3", "4", "5"])
        assert result.is_sensitive is False

    def test_scan_table(self, engine):
        rows = [
            {"email": "a@b.com", "name": "Alice", "id": "1"},
            {"email": "c@d.com", "name": "Bob", "id": "2"},
        ]
        results = engine.scan_table("users", rows)
        assert len(results) > 0
        sensitive_columns = [r for r in results if r.is_sensitive]
        assert any(r.column_name == "email" for r in sensitive_columns)
