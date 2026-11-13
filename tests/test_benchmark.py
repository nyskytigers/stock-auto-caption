"""Synthetic in-memory unit fixtures, NOT a manually labeled quality benchmark."""
import copy
import json
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from stock_metadata.benchmark import (plan, digest, report, markdown, assessment_template,
                                       validate_manifest, export_reviewed, main, run)
from stock_metadata.candidates import keyword_candidates


def fixture(count=1):
    manifest = plan()
    rows = []
    for item in manifest["items"][:count]:
        item.update(status="labeled", filename=item["id"] + ".png", sha256="a" * 64)
        item["rights"] = {"basis": "user_owned", "evidence": "UNIT TEST ONLY"}
        item["labels"].update(annotator="unit fixture", labeled_at="test", objects=["cup", "table"])
        item["platform_fields"] = {"shutterstock": {"categories": ["Objects"]}}
        rows.append({"id": item["id"], "filename": item["filename"], "source_sha256": item["sha256"],
                     "caption": "Cup on a table", "keywords": ["cup", "Cup", "table"], "source_unchanged": True})
    raw = {"schema_version": 1, "dataset_sha256": digest(manifest), "records": rows}
    review = assessment_template(raw)
    return manifest, raw, review


def complete(assessment, row):
    values = {"filename": row["filename"], "caption": "Cup on a table", "keywords": ["cup", "table"]}
    assessment.update(status="complete", reviewer="unit fixture", reviewed_at="test",
                      caption_exhaustive=True, objects_checked=True,
                      caption_claims=[{"text": "cup", "verdict": "supported"}, {"text": "red", "verdict": "unsupported"}],
                      missing_objects=["table"], keyword_judgments=["relevant", "relevant", "uncertain"],
                      review_seconds=12, edit_operations=2, unresolved=[],
                      checks={k: True for k in assessment["checks"]}, reviewed_metadata=values,
                      approved_marketplace="adobe", approved_metadata_sha256=digest(values))


class BenchmarkTests(unittest.TestCase):
    def test_plan_has_24_pending_slots_not_results(self):
        data = validate_manifest(plan())
        self.assertEqual(len(data["items"]), 24)
        self.assertEqual(sum(i["kind"] == "photograph" for i in data["items"]), 12)
        self.assertTrue(all(i["status"] == "pending" for i in data["items"]))

    def test_empty_report_uses_null_not_fabricated_zero(self):
        manifest, raw, review = fixture(0)
        result = report(manifest, raw, review)
        self.assertEqual(result["status"], "NOT TESTED")
        self.assertTrue(all(v is None for v in result["metrics"].values()))
        self.assertIn("NOT TESTED", markdown(result))
        root = Path(__file__).resolve().parents[1] / "docs/benchmark"
        load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
        checked = report(load("manifest.json"), load("raw-empty.json"), load("review-empty.json"))
        self.assertEqual(checked, load("reports/not-tested.json"))
        self.assertEqual(markdown(checked), (root / "reports/not-tested.md").read_text(encoding="utf-8"))

    def test_human_metrics_and_denominators(self):
        manifest, raw, review = fixture()
        complete(review["assessments"][0], raw["records"][0])
        result = report(manifest, raw, review)
        self.assertEqual(result["metrics"]["caption_supported_claim_rate"], .5)
        self.assertEqual(result["metrics"]["hallucinated_claim_rate"], .5)
        self.assertEqual(result["metrics"]["uncertain_claim_rate"], 0)
        self.assertEqual(result["metrics"]["missing_object_rate"], .5)
        self.assertEqual(result["metrics"]["keyword_relevance_rate"], 2/3)
        self.assertEqual(result["metrics"]["raw_duplicate_rate"], 1/3)
        self.assertEqual(result["metrics"]["mean_review_seconds"], 12)
        self.assertEqual(result["status"], "NOT TESTED")  # partial coverage

    def test_raw_review_binding(self):
        manifest, raw, review = fixture()
        raw["records"][0]["caption"] = "Changed"
        with self.assertRaisesRegex(ValueError, "binding"):
            report(manifest, raw, review)

    def test_no_approval_and_partial_review_block_export(self):
        manifest, raw, review = fixture()
        with self.assertRaises(ValueError):
            export_reviewed(manifest, raw, review, "adobe")
        complete(review["assessments"][0], raw["records"][0])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            export_reviewed(manifest, raw, review, "adobe")

    def test_full_review_gate_and_invalidation(self):
        manifest, raw, review = fixture(24)
        for a, r in zip(review["assessments"], raw["records"]):
            complete(a, r)
        self.assertIn(b"Filename,Title", export_reviewed(manifest, raw, review, "adobe"))
        review["assessments"][0]["reviewed_metadata"]["caption"] = "Edited after approval"
        with self.assertRaisesRegex(ValueError, "digest"):
            export_reviewed(manifest, raw, review, "adobe")

    def test_invalid_fields_still_block_human_approved_export(self):
        manifest, raw, review = fixture(24)
        for a, r in zip(review["assessments"], raw["records"]):
            complete(a, r)
        a = review["assessments"][0]
        a["reviewed_metadata"]["caption"] = "x" * 71
        a["approved_metadata_sha256"] = digest(a["reviewed_metadata"])
        with self.assertRaises(ValueError):
            export_reviewed(manifest, raw, review, "adobe")

    def test_rights_required(self):
        manifest, raw, review = fixture()
        manifest["items"][0]["rights"]["basis"] = None
        with self.assertRaisesRegex(ValueError, "rights"):
            validate_manifest(manifest)

    def test_incomplete_annotation_not_scored(self):
        manifest, raw, review = fixture()
        complete(review["assessments"][0], raw["records"][0])
        review["assessments"][0]["caption_exhaustive"] = False
        with self.assertRaises(ValueError):
            report(manifest, raw, review)

    def test_candidates_are_not_padded_or_approved(self):
        result = keyword_candidates(["Cup", "cup"], ["cup", "wooden table"])
        self.assertEqual([r["keyword"] for r in result], ["Cup", "wooden table"])
        self.assertTrue(all(r["review_required"] for r in result))
        self.assertEqual(keyword_candidates([]), [])

    def test_cli_new_output_only(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan"
            self.assertEqual(main(["plan", "--output", str(path)]), 0)
            self.assertEqual(main(["plan", "--output", str(path)]), 2)
            self.assertEqual(len(json.loads((path / "manifest.json").read_text())["items"]), 24)

    def test_nonfinite_effort_is_not_scored(self):
        manifest, raw, review = fixture()
        complete(review["assessments"][0], raw["records"][0])
        review["assessments"][0]["review_seconds"] = float("nan")
        with self.assertRaises(ValueError):
            report(manifest, raw, review)

    def test_local_backend_preserves_raw_decoder_text(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch
        from stock_metadata.backends import LocalBackend
        backend = object.__new__(LocalBackend)
        backend.processor = MagicMock()
        backend.processor.return_value = {}
        backend.processor.decode.return_value = "  NASA  cup\n"
        backend.model = MagicMock()
        backend.model.generate.return_value = [[1]]
        image = MagicMock()
        with patch.dict("sys.modules", {"torch": SimpleNamespace(inference_mode=nullcontext)}):
            self.assertEqual(backend.generate_raw_caption(image), "  NASA  cup\n")
            self.assertEqual(backend.generate_caption(image), "NASA cup")

    def test_unresolved_and_wrong_marketplace_block_export(self):
        manifest, raw, review = fixture(24)
        for a, r in zip(review["assessments"], raw["records"]):
            complete(a, r)
        review["assessments"][0]["unresolved"] = ["location not verified"]
        with self.assertRaises(ValueError):
            export_reviewed(manifest, raw, review, "adobe")
        review["assessments"][0]["unresolved"] = []
        with self.assertRaises(ValueError):
            export_reviewed(manifest, raw, review, "shutterstock")

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow not installed")
    def test_raw_inference_is_separate_and_source_is_immutable(self):
        from PIL import Image
        class Keywords:
            def extract_keywords(self, caption, **options):
                return [("Cup", .9), ("cup", .8)]
        class Backend:
            kw_model = Keywords()
            def generate_caption(self, image):
                return "Raw cup caption"
        manifest, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temp:
            item = manifest["items"][0]
            path = Path(temp) / item["filename"]
            Image.new("RGB", (10, 10)).save(path)
            item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            result = run(manifest, temp, Backend())
            row = result["records"][0]
            self.assertEqual(row["keywords"], ["Cup", "cup"])
            self.assertEqual(row["keyword_scores"], [.9, .8])
            self.assertEqual(row["caption"], "Raw cup caption")
            self.assertTrue(row["source_unchanged"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            item["sha256"] = "b" * 64
            self.assertIn("hash differs", run(manifest, temp, Backend())["records"][0]["error"])
