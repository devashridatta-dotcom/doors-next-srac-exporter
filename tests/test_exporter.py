import json
import unittest
from pathlib import Path

from doors_srac_exporter.exporter import ValidationError, export_document, validate_document


ROOT = Path(__file__).resolve().parents[1]


class ExporterTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
        self.response = json.loads((ROOT / "fixtures" / "reportable-rest-response.json").read_text(encoding="utf-8"))

    def test_exports_a_valid_product_specific_assertion(self):
        document = export_document(self.config, self.response)
        validate_document(document)
        self.assertEqual(document["component"]["purl"], "pkg:generic/brake-control@1.4.0")
        assertion = document["assertions"][0]
        self.assertEqual(assertion["outcome"], "SAFETY_RELATED")
        self.assertEqual(assertion["classification"]["value"], "ASIL-B")
        self.assertEqual(assertion["source"]["configuration"], "Baseline-1.4")
        self.assertEqual(len(assertion["evidence"]), 2)

    def test_rejects_missing_component_digest(self):
        del self.config["component"]["digest"]
        with self.assertRaises(ValidationError):
            export_document(self.config, self.response)

    def test_rejects_missing_decision_status(self):
        del self.response["artifacts"][0]["attributes"]["decisionStatus"]
        with self.assertRaises(ValidationError):
            export_document(self.config, self.response)

