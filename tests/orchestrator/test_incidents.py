"""Unit tests for the Incident & On-Call module (Ideen #69, #17, #75, #81).

Pure-logic tests against a temporary JSON store; the aiohttp handlers are
thin wrappers over the same functions and covered via the OpenAPI contract
test (route/spec parity).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "orchestrator-agent"))

import incidents


class IncidentTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        tmp.close()
        self.store = tmp.name
        self._env = dict(os.environ)
        os.environ["INCIDENTS_STORE"] = self.store
        os.environ["INCIDENTS_ESCALATION"] = "alice|bob;carol"
        os.environ["INCIDENTS_ESCALATE_AFTER_S"] = "3600"
        os.environ.pop("INCIDENTS_QUIET_HOURS", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        try:
            os.unlink(self.store)
        except OSError:
            pass

    def test_create_assigns_duty_owner(self):
        inc = incidents.create_incident("payments", "critical", "checkout 500s")
        self.assertTrue(inc["id"].startswith("inc-"))
        self.assertEqual(inc["status"], "open")
        self.assertEqual(inc["owner"], "alice")
        self.assertEqual(inc["escalation_level"], 0)

    def test_create_validates_input(self):
        with self.assertRaises(ValueError):
            incidents.create_incident("", "critical", "x")
        with self.assertRaises(ValueError):
            incidents.create_incident("svc", "critical", "  ")
        with self.assertRaises(ValueError):
            incidents.create_incident("svc", "cosmic", "x")

    def test_status_flow_and_timeline(self):
        inc = incidents.create_incident("svc", "high", "t", reporter="r")
        incidents.add_note(inc["id"], "looking", actor="alice")
        incidents.set_status(inc["id"], "acknowledged", actor="alice")
        got = incidents.get_incident(inc["id"])
        self.assertEqual(got["status"], "acknowledged")
        self.assertTrue(got["acknowledged_at"])
        kinds = [e["kind"] for e in got["timeline"]]
        self.assertEqual(kinds, ["created", "assigned", "note", "status"])

    def test_resolve_requires_note(self):
        inc = incidents.create_incident("svc", "low", "t")
        with self.assertRaises(ValueError):
            incidents.set_status(inc["id"], "resolved")
        incidents.set_status(inc["id"], "resolved", note="fixed", actor="a")
        self.assertEqual(incidents.get_incident(inc["id"])["status"], "resolved")
        with self.assertRaises(ValueError):
            incidents.add_note(inc["id"], "late note")

    def test_escalation_advances_rota(self):
        inc = incidents.create_incident("svc", "critical", "t")
        result = incidents.escalate(inc["id"], actor="alice")
        self.assertTrue(result["escalated"])
        self.assertEqual(result["incident"]["owner"], "carol")
        self.assertEqual(result["incident"]["escalation_level"], 1)
        # Highest level: no-op, still returns a result.
        again = incidents.escalate(inc["id"])
        self.assertFalse(again["escalated"])

    def test_escalation_deferred_in_quiet_hours(self):
        os.environ["INCIDENTS_QUIET_HOURS"] = "00:00-23:59"  # always quiet
        inc = incidents.create_incident("svc", "critical", "t")
        result = incidents.escalate(inc["id"])
        self.assertFalse(result["escalated"])
        self.assertIn("quiet", result["reason"])
        self.assertEqual(result["incident"]["owner"], "alice")
        forced = incidents.escalate(inc["id"], force=True)
        self.assertTrue(forced["escalated"])
        self.assertEqual(forced["incident"]["owner"], "carol")

    def test_manual_assign_is_audited(self):
        inc = incidents.create_incident("svc", "medium", "t")
        incidents.assign(inc["id"], "dave", actor="alice")
        got = incidents.get_incident(inc["id"])
        self.assertEqual(got["owner"], "dave")
        self.assertTrue(any(e["kind"] == "assigned" and "dave" in e["detail"]
                            for e in got["timeline"]))

    def test_list_filters_and_order(self):
        a = incidents.create_incident("svc-a", "low", "first")
        incidents.create_incident("svc-b", "low", "second")
        incidents.set_status(a["id"], "acknowledged")
        self.assertEqual([i["service"] for i in incidents.list_incidents()],
                         ["svc-b", "svc-a"])
        self.assertEqual(len(incidents.list_incidents(status="acknowledged")), 1)
        self.assertEqual(len(incidents.list_incidents(service="svc-b")), 1)

    def test_postmortem_draft_is_marked_unreviewed(self):
        inc = incidents.create_incident("svc", "high", "t", runbook="rb-1")
        incidents.add_note(inc["id"], "n1", actor="a")
        incidents.set_status(inc["id"], "resolved", note="done", actor="a")
        draft = incidents.postmortem_draft(inc["id"])
        self.assertTrue(draft["draft"])
        self.assertIn("ENTWURF", draft["markdown"])
        self.assertIn("unreviewed", draft["markdown"])
        self.assertIn("rb-1", draft["markdown"])
        self.assertIn("n1", draft["markdown"])
        self.assertIsNone(incidents.postmortem_draft("inc-nope"))

    def test_escalation_due_respects_deadline(self):
        inc = incidents.create_incident("svc", "high", "t")
        self.assertFalse(incidents.escalation_due(inc))
        old = dict(inc)
        old["updated_at"] = "2000-01-01T00:00:00+00:00"
        self.assertTrue(incidents.escalation_due(old))
        resolved = dict(old, status="resolved")
        self.assertFalse(incidents.escalation_due(resolved))


if __name__ == "__main__":
    unittest.main()
