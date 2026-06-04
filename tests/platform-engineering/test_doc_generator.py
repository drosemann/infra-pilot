"""Tests for Doc Generator manager."""
import pytest
from services.integration_service.src.platform_engineering.doc_generator import DocGenerator


class TestDocGenerator:
    def setup_method(self):
        self.mgr = DocGenerator()

    def test_generate_document(self):
        d = self.mgr.generate_document("Architecture Overview", "c4_context")
        assert d.id is not None
        assert d.title == "Architecture Overview"
        assert d.doc_type == "c4_context"

    def test_get_document(self):
        d = self.mgr.generate_document("System Design", "c4_container")
        found = self.mgr.get_document(d.id)
        assert found.id == d.id

    def test_list_documents(self):
        self.mgr.generate_document("Doc A", "adr")
        self.mgr.generate_document("Doc B", "c4_context")
        assert len(self.mgr.list_documents()) == 2

    def test_document_has_content(self):
        d = self.mgr.generate_document("My Doc", "c4_context")
        assert len(d.content) > 0

    def test_get_summary(self):
        self.mgr.generate_document("D1", "adr")
        self.mgr.generate_document("D2", "c4_context")
        s = self.mgr.get_summary()
        assert s["total_documents"] == 2

    def test_to_dict_from_dict(self):
        d = self.mgr.generate_document("roundtrip", "adr")
        d2 = d.to_dict()
        from services.integration_service.src.platform_engineering.doc_generator import Documentation
        restored = Documentation.from_dict(d2)
        assert restored.title == "roundtrip"
        assert restored.doc_type == "adr"

    def test_empty_summary(self):
        s = self.mgr.get_summary()
        assert s["total_documents"] == 0

    def test_adr_proposed_by_default(self):
        d = self.mgr.generate_document("ADR Decision", "adr")
        assert d.status == "proposed"

    def test_start_and_approve_review(self):
        adr = self.mgr.generate_document("Review ADR", "adr")
        review = self.mgr.start_review(adr.id, ["reviewer1", "reviewer2"])
        assert review is not None
        approved = self.mgr.approve_review(review["review_id"], "reviewer1")
        assert approved

    def test_reject_review(self):
        adr = self.mgr.generate_document("Reject ADR", "adr")
        review = self.mgr.start_review(adr.id, ["reviewer"])
        rejected = self.mgr.reject_review(review["review_id"], "reviewer", "Missing details")
        assert rejected

    def test_cross_reference(self):
        d1 = self.mgr.generate_document("Doc A", "adr")
        d2 = self.mgr.generate_document("Doc B", "documentation")
        result = self.mgr.cross_reference_docs(d1.id, d2.id, "related")
        assert result

    def test_doc_template_crud(self):
        tmpl = self.mgr.set_doc_template("Arch Template", "## {{title}}\n{{body}}")
        assert tmpl["name"] == "Arch Template"
        templates = self.mgr.get_doc_templates()
        assert len(templates) >= 1

    def test_generate_from_template(self):
        tmpl = self.mgr.set_doc_template("Service Doc", "# {{service_name}}\nOwner: {{owner}}")
        doc_id = self.mgr.generate_from_template(tmpl["template_id"], "svc-1", {"service_name": "MySvc", "owner": "team"})
        assert doc_id is not None

    def test_search_docs(self):
        self.mgr.generate_document("Searchable Doc", "adr")
        results = self.mgr.search_docs("Searchable")
        assert len(results) >= 1

    def test_get_content_statistics(self):
        self.mgr.generate_document("Stats Doc", "documentation")
        stats = self.mgr.get_content_statistics()
        assert stats["total_documents"] >= 1

    def test_version_doc_template(self):
        tmpl = self.mgr.set_doc_template("Versioned Template", "v1 content")
        updated = self.mgr.version_doc_template(tmpl["template_id"], "v2 content")
        assert updated["version"] == "2.0"

    def test_bulk_generate_docs(self):
        tmpl = self.mgr.set_doc_template("Bulk Template", "{{name}}")
        ids = self.mgr.bulk_generate_docs("svc-bulk", [tmpl["template_id"]], {"name": "test"})
        assert len(ids) >= 1
