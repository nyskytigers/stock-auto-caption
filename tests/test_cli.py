import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from stock_metadata.cli import main, run_batch

ROOT = Path(__file__).resolve().parents[1]
VALUES = {"caption": "White ceramic mug", "keywords": ["mug", "white", "ceramic"]}


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.images = self.root / "images with spaces"
        self.images.mkdir()
        self.image = self.images / "test.JPG"
        self.image.write_bytes(b"supplied-metadata mode deliberately does not decode images")
        self.meta = self.root / "meta.json"
        self.meta.write_text(json.dumps({"test.JPG": VALUES}), encoding="utf-8")
        self.out = self.root / "new.csv"

    def args(self):
        return ["--input-dir", str(self.images), "--marketplace", "adobe", "--output", str(self.out), "--metadata-json", str(self.meta)]

    def test_cli_subprocess_and_unchanged_original(self):
        before = hashlib.sha256(self.image.read_bytes()).digest()
        result = subprocess.run([sys.executable, "-m", "stock_metadata", *self.args()], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(hashlib.sha256(self.image.read_bytes()).digest(), before)
        self.assertIn("test.JPG", self.out.read_text())

    def test_partial_batch(self):
        (self.images / "missing.png").write_bytes(b"x")
        self.assertEqual(main(self.args()), 1)
        self.assertTrue(self.out.exists())

    def test_existing_output(self):
        self.out.write_text("keep")
        self.assertEqual(main(self.args()), 2)
        self.assertEqual(self.out.read_text(), "keep")

    def test_output_in_source(self):
        self.out = self.images / "export.csv"
        self.assertEqual(main(self.args()), 2)
        self.assertFalse(self.out.exists())

    def test_all_invalid(self):
        self.meta.write_text("{}")
        self.assertEqual(main(self.args()), 2)
        self.assertFalse(self.out.exists())

    def test_malformed_json(self):
        self.meta.write_text("{")
        self.assertEqual(main(self.args()), 2)

    def test_filename_override_rejected(self):
        rows, errors = run_batch(self.images, "adobe", metadata={"test.JPG": dict(VALUES, filename="other.jpg")})
        self.assertEqual(rows, [])
        self.assertIn("override", errors[0]["error"])

    def test_backend_failure_recovery(self):
        (self.images / "second.png").write_bytes(b"x")
        from unittest.mock import patch
        from stock_metadata import Metadata
        def process(source, backend, filename):
            if filename == "second.png":
                raise RuntimeError("model failure")
            return Metadata(filename, **VALUES)
        with patch("stock_metadata.cli.process_image", side_effect=process):
            rows, errors = run_batch(self.images, "adobe", backend=object())
        self.assertEqual([r.filename for r in rows], ["test.JPG"])
        self.assertEqual(errors[0]["filename"], "second.png")

    def test_symlink_rejected(self):
        link = self.images / "linked.jpg"
        try:
            link.symlink_to(self.image)
        except OSError:
            self.skipTest("symlink privilege unavailable")
        rows, errors = run_batch(self.images, "adobe", metadata={"test.JPG": VALUES, "linked.jpg": VALUES})
        self.assertEqual(len(rows), 1)
        self.assertIn("symlink", errors[0]["error"])

    def test_requires_explicit_backend(self):
        self.assertEqual(main(self.args()[:-2]), 2)
