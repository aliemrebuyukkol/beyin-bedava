import copy
import importlib.util
import json
from pathlib import Path
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_session", PROJECT / "tools/check_session.py")
SESSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SESSION)


class SessionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((PROJECT / "qa/synthetic-session.json").read_text())

    def test_small_synthetic_session_has_insufficient_coverage(self):
        result = SESSION.validate(self.document)
        self.assertEqual(result["coverage"], "synthetic_only")
        self.assertEqual(result["level_screens"], {"1": "insufficient"})

    def test_impossible_counts_are_rejected(self):
        for invalid in (True, -1, 40):
            with self.subTest(invalid=invalid):
                report = copy.deepcopy(self.document)
                report["levels"]["1"]["blocked"] = invalid
                with self.assertRaises(ValueError):
                    SESSION.validate(report)

    def test_p95_is_computed_and_validated(self):
        self.document["render_feedback"] = {"samples_ms": list(range(30)), "p95_ms": 28}
        self.assertEqual(SESSION.validate(self.document)["render_p95_ms"], 28)
        self.document["render_feedback"]["p95_ms"] = 29
        with self.assertRaises(ValueError):
            SESSION.validate(self.document)

    def test_large_blocked_share_requests_review(self):
        self.document["source"] = "observed_local"
        self.document["levels"]["1"].update(actions=40, blocked=20)
        result = SESSION.validate(self.document)
        self.assertEqual(result["level_screens"]["1"], "review_blocked_actions")
        self.assertEqual(result["coverage"], "single_local_session")


if __name__ == "__main__":
    unittest.main()
